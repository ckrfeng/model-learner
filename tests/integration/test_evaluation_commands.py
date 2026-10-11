"""Evaluation CLI integration with public fixtures only; never run paid agents."""

import json
from datetime import timedelta
from pathlib import Path

from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.domain.models import utc_now

runner = CliRunner()


def call(arguments: list[str]) -> dict | list:
    result = runner.invoke(app, arguments)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def test_benchmark_cli_operator_flow_preserves_unknown(
    tmp_path: Path, monkeypatch
) -> None:
    protected = tmp_path / "protected"
    protected.mkdir()
    (protected / "source.py").write_text("public source\n")
    disposable = tmp_path / "disposable"
    disposable.mkdir()
    monkeypatch.setattr(
        "model_learner.commands.benchmark.PROTECTED_REPOSITORY", protected
    )
    config = tmp_path / "config.json"
    config.write_text('{"provider":"fixture","model":"public-fixture"}')
    tasks = call(["benchmark", "tasks"])
    assert {task["task_id"] for task in tasks} == {"clamp", "duration"}
    prepared = call(
        [
            "benchmark",
            "prepare",
            "clamp",
            "--parent",
            str(disposable),
            "--configuration-file",
            str(config),
            "--isolation-mechanism",
            "controlled fixture without agent execution",
            "--execution-origin",
            "fixture",
        ]
    )
    root = prepared["root"]
    assert call(["benchmark", "show", root])["benchmark_id"] == prepared["benchmark_id"]
    started = utc_now()
    ended = utc_now()
    result = call(
        [
            "benchmark",
            "finalize",
            root,
            "--started-at",
            started.isoformat(),
            "--ended-at",
            ended.isoformat(),
            "--state",
            "abandoned",
            "--isolation-confirmed",
        ]
    )
    assert result["outcome"]["status"] == "unknown"
    assert result["verification"] is None
    assert result["execution_origin"] == "fixture"
    assert result["dataset"]["source_kind"] == "benchmark"
    assert result["telemetry_events"] == 0
    assert (protected / "source.py").read_text() == "public source\n"
    call(["benchmark", "cleanup", root])
    assert not Path(root).exists()


def test_benchmark_cli_rejects_repository_workspace_and_private_config(
    tmp_path: Path, monkeypatch
) -> None:
    protected = tmp_path / "protected"
    protected.mkdir()
    monkeypatch.setattr(
        "model_learner.commands.benchmark.PROTECTED_REPOSITORY", protected
    )
    config = tmp_path / "config.json"
    config.write_text('{"model":"fixture"}')
    args = [
        "benchmark",
        "prepare",
        "clamp",
        "--parent",
        str(protected),
        "--configuration-file",
        str(config),
        "--isolation-mechanism",
        "fixture",
    ]
    rejected = runner.invoke(app, args)
    assert rejected.exit_code == 2
    assert list(protected.iterdir()) == []
    config.write_text('{"schema_version":"PRIVATE_SENTINEL"}')
    rejected = runner.invoke(app, args)
    assert rejected.exit_code == 2
    assert "PRIVATE_SENTINEL" not in rejected.output


def test_task_state_cli_fixture_round_trip_and_empty_scores(tmp_path: Path) -> None:
    source = tmp_path / "examples.json"
    call(["sim", "state-fixture", str(source), "--seed", "2", "--count", "8"])
    examples = json.loads(source.read_text())
    row = examples[0]["observation"]
    train = utc_now() - timedelta(days=1)
    report = call(
        [
            "learn",
            "state-eval",
            "--input-file",
            str(source),
            "--source-kind",
            "simulated",
            "--dataset-id",
            row["dataset"]["dataset_id"],
            "--dataset-version",
            "1",
            "--acceptance-id",
            row["acceptance_spec"]["identifier"],
            "--acceptance-version",
            "1",
            "--train-until",
            train.isoformat(),
            "--evaluation-at",
            utc_now().isoformat(),
            "--bootstrap-replicates",
            "100",
        ]
    )
    assert len(report["variants"]) == 6
    assert all(v["status"] == "insufficient_data" for v in report["variants"])
    assert all(v["brier_score"] is None for v in report["variants"])
    original = source.read_bytes()
    rejected = runner.invoke(app, ["sim", "state-fixture", str(source)])
    assert rejected.exit_code == 2
    assert source.read_bytes() == original


def test_task_state_cli_validation_does_not_echo_payload(tmp_path: Path) -> None:
    source = tmp_path / "invalid.json"
    source.write_text('[{"private":"PRIVATE_SENTINEL"}]')
    result = runner.invoke(
        app,
        [
            "learn",
            "state-eval",
            "--input-file",
            str(source),
            "--source-kind",
            "simulated",
            "--dataset-id",
            "fixture",
            "--dataset-version",
            "1",
            "--acceptance-id",
            "tests",
            "--acceptance-version",
            "1",
            "--train-until",
            "2026-01-01T00:00:00Z",
            "--evaluation-at",
            "2026-01-02T00:00:00Z",
        ],
    )
    assert result.exit_code == 2
    assert "invalid task-state input" in result.output
    assert "PRIVATE_SENTINEL" not in result.output
