"""Resolved real cohorts remain one trial, with separate historical train state."""

import hashlib
import json
from datetime import timedelta
from pathlib import Path

from typer.testing import CliRunner

from model_learner.adapters.codex import ingest_codex_capture
from model_learner.cli import app
from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    Event,
    ExecutionConfiguration,
    Outcome,
    Run,
    Session,
    Task,
    TaskSessionLink,
    utc_now,
)
from model_learner.observations import build_real_observation
from model_learner.runs import create_bounded_run, declare_attempt
from model_learner.storage.database import Database, Repository
from model_learner.verification import (
    assess_human,
    assess_run,
    digest_criterion,
    verify_file,
)

runner = CliRunner()
DATASET = DatasetReference(
    source_kind="real", dataset_id="history", dataset_version="1"
)


def workflow(tmp_path: Path):
    database = Database(tmp_path / "ledger.sqlite")
    database.initialize()
    repo = Repository(database)
    fixture = Path(__file__).parents[1] / "fixtures/codex/exec_capture.jsonl"
    ingest_codex_capture(repo, fixture, machine_id="fixture")
    session = repo.list_records(Session)[0]
    artifact = tmp_path / "artifact"
    artifact.write_bytes(b"synthetic exact bytes")
    events = repo.list_records(Event)
    start = min(event.observed_at for event in events)
    end = max(event.observed_at for event in events) + timedelta(seconds=1)
    task = repo.create_task(
        Task(
            description="Synthetic resolver fixture",
            task_group="fixture",
            acceptance_spec=AcceptanceSpec(identifier="exact", version="1"),
            metadata={
                "file_digest_verifier": digest_criterion(
                    hashlib.sha256(artifact.read_bytes()).hexdigest()
                )
            },
        )
    )
    repo.associate_session(
        TaskSessionLink(task_id=task.task_id, session_id=session.session_id)
    )
    run = create_bounded_run(
        repo,
        task_id=task.task_id,
        session_id=session.session_id,
        started_at=start,
        ended_at=end,
        final_artifact_fingerprint="sha256:"
        + hashlib.sha256(artifact.read_bytes()).hexdigest(),
    )
    config = ExecutionConfiguration(
        provider="fixture", model="fixture-arm", harness="fixture"
    )
    declare_attempt(
        repo, run_id=run.run_id, configuration=config, started_at=start, ended_at=end
    )
    return repo, run, artifact, config, utc_now() + timedelta(minutes=1)


def call(args):
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def row(repo: Repository, run: Run, outcome: Outcome, time):
    return build_real_observation(
        repo,
        run_id=run.run_id,
        outcome_id=outcome.outcome_id,
        dataset=DATASET,
        recorded_at=time,
    )


def test_cli_resolves_unknown_verified_censored_without_duplicates(tmp_path: Path):
    repo, run, artifact, config, base = workflow(tmp_path)
    unknown = assess_run(repo, run_id=run.run_id, recorded_at=base)
    row(repo, run, unknown, base)
    evidence = verify_file(
        repo,
        run_id=run.run_id,
        artifact=artifact,
        observed_at=base + timedelta(seconds=1),
    )
    verified = assess_run(
        repo,
        run_id=run.run_id,
        verification_id=evidence.verification_id,
        supersedes_outcome_id=unknown.outcome_id,
        recorded_at=base + timedelta(seconds=2),
    )
    row(repo, run, verified, base + timedelta(seconds=3))
    censored = assess_human(
        repo,
        run_id=run.run_id,
        status="censored",
        censor_reason="withdrawn",
        supersedes_outcome_id=verified.outcome_id,
        recorded_at=base + timedelta(seconds=10),
    )
    row(repo, run, censored, base + timedelta(seconds=11))
    args = [
        "--dataset-id",
        DATASET.dataset_id,
        "--dataset-version",
        "1",
        "--database",
        str(repo.database.path),
    ]
    for seconds, status, count in [
        (0, "unknown", 0),
        (4, "success", 1),
        (12, "censored", 0),
    ]:
        cutoff = (base + timedelta(seconds=seconds)).isoformat()
        snapshot = call(["observations", "resolve", "--cutoff", cutoff, *args])
        assert len(snapshot["observations"]) == 1
        assert snapshot["observations"][0]["outcome_status"] == status
        prediction = call(
            [
                "learn",
                "predict",
                "--source-kind",
                "real",
                "--acceptance-id",
                "exact",
                "--acceptance-version",
                "1",
                "--configuration-id",
                config.configuration_id,
                "--group",
                "fixture",
                "--cutoff",
                cutoff,
                *args,
            ]
        )
        assert prediction["training"]["eligible_label_count"] == count
        assert prediction["prediction"]["successes"] == count
    evaluation = call(
        [
            "learn",
            "eval",
            "--source-kind",
            "real",
            "--acceptance-id",
            "exact",
            "--acceptance-version",
            "1",
            "--train-until",
            (base + timedelta(seconds=4)).isoformat(),
            "--evaluation-at",
            (base + timedelta(seconds=12)).isoformat(),
            *args,
        ]
    )
    assert evaluation["training"]["eligible_label_count"] == 1
    assert evaluation["held_out_count"] == 0
    assert len(repo.list_records(Outcome)) == 3
    assert len(repo.list_observations("real")) == 3


def test_drift_cli_report_and_exclusive_output(tmp_path: Path):
    output = tmp_path / "report.json"
    args = [
        "learn",
        "drift",
        "--seed",
        "2",
        "--count",
        "24",
        "--window-steps",
        "8",
        "--refit-steps",
        "8",
        "--output",
        str(output),
    ]
    summary = call(args)
    assert summary["seeds"] == [2]
    report = json.loads(output.read_text())
    assert report["window_steps"] == [8]
    assert {s["name"] for s in report["scenarios"]} >= {
        "stationary",
        "abrupt",
        "gradual",
        "sparse",
        "imbalanced",
        "delayed",
    }
    assert all(len(s["baselines"]) == 2 for s in report["scenarios"])
    original = output.read_bytes()
    assert runner.invoke(app, args).exit_code == 2
    assert output.read_bytes() == original
