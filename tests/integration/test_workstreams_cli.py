"""Reviewable task verification and multi-seed evaluation through installed commands."""

import hashlib
import json
from pathlib import Path

from typer.testing import CliRunner

from model_learner.cli import app

runner = CliRunner()


def call(args: list[str]) -> dict | list:
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def setup_run(
    tmp_path: Path, *, expected: bytes = b"accepted\n"
) -> tuple[list[str], dict, dict, Path]:
    db = ["--database", str(tmp_path / "ledger.sqlite")]
    result = runner.invoke(app, ["init", *db])
    assert result.exit_code == 0
    task = call(
        [
            "task",
            "create",
            "Produce declared exact artifact",
            "--acceptance-id",
            "exact-file",
            "--acceptance-version",
            "1",
            "--acceptance-description",
            "Artifact matches predeclared SHA-256",
            "--expected-sha256",
            hashlib.sha256(expected).hexdigest(),
            "--task-group",
            "manual",
            *db,
        ]
    )
    fixture = Path(__file__).parents[1] / "fixtures/codex/exec_capture.jsonl"
    captured = tmp_path / "capture.jsonl"
    rows = [json.loads(line) for line in fixture.read_text().splitlines()]
    for row in rows:
        row["captured_at"] = "2026-01-01T00:00:30Z"
    captured.write_text("\n".join(json.dumps(row) for row in rows) + "\n")
    call(["import", "codex", str(captured), "--machine-id", "cli-test", *db])
    session = call(["sessions", *db])[0]
    artifact = tmp_path / "artifact.txt"
    artifact.write_bytes(b"accepted\n")
    run = call(
        [
            "run",
            "create",
            task["task_id"],
            "--session-id",
            session["session_id"],
            "--started-at",
            "2026-01-01T00:00:00Z",
            "--ended-at",
            "2026-01-01T00:01:00Z",
            "--artifact",
            str(artifact),
            *db,
        ]
    )
    config = tmp_path / "configuration.json"
    config.write_text(json.dumps({"model": "sanitized-example", "harness": "codex"}))
    call(
        [
            "run",
            "attempt",
            run["run_id"],
            "--configuration-file",
            str(config),
            "--started-at",
            "2026-01-01T00:00:00Z",
            "--ended-at",
            "2026-01-01T00:01:00Z",
            *db,
        ]
    )
    return db, task, run, artifact


def test_completed_unknown_then_verified_real_export(tmp_path: Path) -> None:
    db, task, run, artifact = setup_run(tmp_path)
    unknown = call(["outcome", "assess", run["run_id"], *db])
    assert unknown["status"] == "unknown"
    assert unknown["verification_status"] == "unverified"
    row_args = [
        "observations",
        "build",
        run["run_id"],
        "--dataset-id",
        "cli-real",
        "--dataset-version",
        "1",
        *db,
    ]
    unknown_row = call([*row_args, "--outcome-id", unknown["outcome_id"]])
    assert not unknown_row["eligible_for_configuration_learning"]
    assert unknown_row["label_available_at"] is None
    evidence = call(["verify", "file", run["run_id"], str(artifact), *db])
    assert evidence["result"] == "pass"
    assert evidence["metadata"]["content_retained"] is False
    outcome = call(
        [
            "outcome",
            "assess",
            run["run_id"],
            "--verification-id",
            evidence["verification_id"],
            "--supersedes",
            unknown["outcome_id"],
            *db,
        ]
    )
    assert outcome["status"] == "success"
    assert outcome["verification_status"] == "verified"
    row = call([*row_args, "--outcome-id", outcome["outcome_id"]])
    assert row["source_kind"] == "real"
    assert row["task_id"] == task["task_id"]
    assert row["eligible_for_configuration_learning"]
    assert row["cost_usd"] is None
    assert (
        call([*row_args, "--outcome-id", outcome["outcome_id"]])["observation_id"]
        == row["observation_id"]
    )
    shown = call(["run", "show", run["run_id"], *db])
    assert shown["run"]["state"] == "finished"
    assert len(shown["outcomes"]) == 2
    assert len(shown["session_links"]) == 1
    destination = tmp_path / "real.jsonl"
    result = runner.invoke(
        app,
        [
            "records",
            "export",
            "observation",
            str(destination),
            "--source-kind",
            "real",
            *db,
        ],
    )
    assert result.exit_code == 0
    assert len(destination.read_text().splitlines()) == 2
    quality = call(
        [
            "observations",
            "quality",
            "--dataset-id",
            "cli-real",
            "--dataset-version",
            "1",
            *db,
        ]
    )
    assert quality["dataset"]["source_kind"] == "real"


def test_fail_evidence_and_changed_snapshot_rejection(tmp_path: Path) -> None:
    db, _, run, artifact = setup_run(tmp_path, expected=b"different expectation")
    evidence = call(["verify", "file", run["run_id"], str(artifact), *db])
    assert evidence["result"] == "fail"
    outcome = call(
        [
            "outcome",
            "assess",
            run["run_id"],
            "--verification-id",
            evidence["verification_id"],
            *db,
        ]
    )
    assert outcome["status"] == "failure"
    assert outcome["verification_status"] == "verified"
    artifact.write_text("different snapshot")
    result = runner.invoke(app, ["verify", "file", run["run_id"], str(artifact), *db])
    assert result.exit_code == 2
    assert "fingerprint" in result.output
    assert len(call(["run", "show", run["run_id"], *db])["verifications"]) == 1


def test_invalid_run_declaration_has_no_side_effects(tmp_path: Path) -> None:
    db, task, run, _ = setup_run(tmp_path)
    session_id = call(["run", "show", run["run_id"], *db])["session_links"][0][
        "session_id"
    ]
    result = runner.invoke(
        app,
        [
            "run",
            "create",
            task["task_id"],
            "--session-id",
            session_id,
            "--started-at",
            "2026-01-01T00:00:00",
            "--ended-at",
            "2026-01-01T00:01:00Z",
            *db,
        ],
    )
    assert result.exit_code == 2
    assert "timezone" in result.output
    human = call(["outcome", "human", run["run_id"], "--status", "success", *db])
    assert human["assessment_source"] == "human_assessment"
    assert human["verification_status"] == "unverified"
    row = call(
        [
            "observations",
            "build",
            run["run_id"],
            "--outcome-id",
            human["outcome_id"],
            "--dataset-id",
            "human",
            "--dataset-version",
            "1",
            *db,
        ]
    )
    assert not row["eligible_for_configuration_learning"]


def test_stress_cli_reproducible_report_and_safe_destination(tmp_path: Path) -> None:
    args = [
        "learn",
        "stress",
        "--seed",
        "7",
        "--seed",
        "9",
        "--count",
        "24",
        "--scenario",
        "sparse",
        "--scenario",
        "drift",
    ]
    first = call(args)
    assert first == call(args)
    assert first["seeds"] == [7, 9]
    assert [s["name"] for s in first["scenarios"]] == ["sparse", "drift"]
    assert len(first["scenarios"][0]["runs"]) == 2
    output = tmp_path / "report.json"
    call([*args, "--output", str(output)])
    assert json.loads(output.read_text()) == first
    repeated = runner.invoke(app, [*args, "--output", str(output)])
    assert repeated.exit_code == 2
    assert json.loads(output.read_text()) == first
    invalid = runner.invoke(
        app, ["learn", "stress", "--seed", "1", "--seed", "1", "--count", "2"]
    )
    assert invalid.exit_code == 2
    assert "distinct" in invalid.output
    invalid = runner.invoke(
        app, ["learn", "stress", "--scenario", "not-real", "--count", "2"]
    )
    assert invalid.exit_code == 2
