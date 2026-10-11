"""Offline commands retain unavailable containment and unknown fixture evidence."""

import json
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import pytest
from typer.testing import CliRunner

from model_learner.adapters.codex import capture_codex_stream
from model_learner.benchmark import (
    finalize_benchmark,
    prepare_benchmark,
    snapshot_candidate,
)
from model_learner.cli import app
from model_learner.domain.models import ExecutionConfiguration, Observation, utc_now
from model_learner.storage.database import Database, Repository


@pytest.mark.parametrize(
    "status,exit_code", [("validated", 0), ("unavailable", 1), ("failed", 1)]
)
def test_offline_probe_cli_retains_status_and_real_gate(monkeypatch, status, exit_code):
    @dataclass(frozen=True)
    class Receipt:
        status: str
        real_execution_ready: bool = False

    monkeypatch.setattr(
        "model_learner.benchmark.offline.probe_offline_isolation",
        lambda **kwargs: Receipt(status),
    )
    result = CliRunner().invoke(app, ["benchmark", "offline-isolation-probe"])
    assert result.exit_code == exit_code
    assert json.loads(result.output) == {
        "status": status,
        "real_execution_ready": False,
    }


@pytest.mark.parametrize("verified", [False, True])
def test_evidence_cli_round_trip_fixture(tmp_path, verified):
    protected = tmp_path / "protected"
    protected.mkdir()
    (protected / "source.txt").write_text("public synthetic source\n")
    parent = tmp_path / "tasks"
    parent.mkdir()
    prepared = prepare_benchmark(
        parent=parent,
        protected_repository=protected,
        task_id="clamp",
        configuration=ExecutionConfiguration(
            provider="fixture",
            model="fixture-model",
            harness="synthetic",
            harness_version="1",
            configuration_version="1",
        ),
        isolation_mechanism="public fixture; no agent",
        execution_origin="fixture",
    )
    started = utc_now()
    capture = None
    if verified:
        source = Path(__file__).parents[1] / "fixtures/benchmark/clamp_solution.py"
        (prepared.workspace / "solution.py").write_bytes(source.read_bytes())
        capture = prepared.control / "capture.jsonl"
        with capture.open("x") as stream:
            capture_codex_stream(
                ['{"type":"thread.started","thread_id":"synthetic"}'],
                stream,
                source_version="fixture-v1",
            )
    ended = utc_now()
    completed = None
    if verified:
        snapshot_candidate(prepared.root)
        completed = subprocess.run(
            [sys.executable, "-I", str(prepared.control / "acceptance.py")],
            cwd=prepared.control,
            env={},
            capture_output=True,
            timeout=15,
            check=False,
        )
        assert completed.returncode == 0
    finalize_benchmark(
        prepared.root,
        started_at=started,
        ended_at=ended,
        capture=capture,
        test_completed=True if verified else None,
        test_exit_code=completed.returncode if completed else None,
        test_generated_at=utc_now() if verified else None,
        isolation_confirmed=True,
    )
    runner = CliRunner()
    exported = runner.invoke(app, ["benchmark", "evidence-export", str(prepared.root)])
    assert exported.exit_code == 0, exported.output
    evidence_path = tmp_path / "evidence.json"
    saved = runner.invoke(
        app,
        [
            "benchmark",
            "evidence-export",
            str(prepared.root),
            "--output",
            str(evidence_path),
        ],
    )
    assert saved.exit_code == 0, saved.output
    before = evidence_path.read_bytes()
    refused = runner.invoke(
        app,
        [
            "benchmark",
            "evidence-export",
            str(prepared.root),
            "--output",
            str(evidence_path),
        ],
    )
    assert refused.exit_code != 0
    assert evidence_path.read_bytes() == before
    database = Database(tmp_path / "imported.sqlite3")
    database.initialize()
    arguments = [
        "benchmark",
        "evidence-import",
        str(evidence_path),
        "--root",
        str(prepared.root),
        "--database",
        str(database.path),
    ]
    first = runner.invoke(app, arguments)
    second = runner.invoke(app, arguments)
    assert first.exit_code == second.exit_code == 0, (first.output, second.output)
    row = json.loads(first.output)
    assert row == json.loads(second.output)
    assert row["source_kind"] == "benchmark"
    assert row["dataset"]["dataset_id"].endswith(":fixture")
    assert row["outcome_status"] == ("success" if verified else "unknown")
    assert row["eligible_for_configuration_learning"] is verified
    assert row["cost_usd"] is None
    assert (
        len(Repository(database).list_records(Observation, source_kind="benchmark"))
        == 1
    )

    evidence_path.write_text('{"version":"fabricated"}')
    rejected = runner.invoke(app, arguments)
    assert rejected.exit_code != 0
    assert (
        len(Repository(database).list_records(Observation, source_kind="benchmark"))
        == 1
    )


def test_evidence_export_rejects_naive_historical_cutoff(tmp_path):
    result = CliRunner().invoke(
        app,
        [
            "benchmark",
            "evidence-export",
            str(tmp_path),
            "--historical-cutoff",
            "2026-10-11T12:00:00",
        ],
    )
    assert result.exit_code != 0
    assert "time must include a timezone" in result.output
