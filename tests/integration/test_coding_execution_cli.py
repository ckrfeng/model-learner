"""Operator-supplied reports and metadata checkpoints through the CLI."""

import hashlib
import json
from datetime import timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.domain.models import utc_now

runner = CliRunner()


def call(args: list[str]) -> dict | list:
    result = runner.invoke(app, args)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def setup_report(tmp_path: Path, *, completed: bool | None = True):
    database = ["--database", str(tmp_path / "ledger.sqlite")]
    assert runner.invoke(app, ["init", *database]).exit_code == 0
    task = call(
        [
            "task",
            "create",
            "Repair parser regression",
            "--acceptance-id",
            "parser-tests",
            "--acceptance-version",
            "1",
            "--required-test",
            "tests.test_parser::test_regression",
            *database,
        ]
    )
    session = call(["session", "register", "--source", "codex.exec", *database])
    artifact = tmp_path / "parser.py"
    artifact.write_text("def parse(value):\n    return value.strip()\n")
    now = utc_now()
    run = call(
        [
            "run",
            "create",
            task["task_id"],
            "--session-id",
            session["session_id"],
            "--started-at",
            (now - timedelta(minutes=2)).isoformat(),
            "--ended-at",
            (now - timedelta(minutes=1)).isoformat(),
            "--artifact",
            str(artifact),
            *database,
        ]
    )
    report = tmp_path / "pytest.xml"
    report.write_text(
        '<testsuites><testsuite name="pytest" tests="1" failures="0" '
        'errors="0" skipped="0"><testcase classname="tests.test_parser" '
        'name="test_regression" time="0.002"/></testsuite></testsuites>'
    )
    binding = tmp_path / "binding.json"
    binding.write_text(
        json.dumps(
            {
                "task_id": task["task_id"],
                "run_id": run["run_id"],
                "acceptance_spec": task["acceptance_spec"],
                "artifact_fingerprint": run["metadata"]["final_artifact_fingerprint"],
                "report_sha256": hashlib.sha256(report.read_bytes()).hexdigest(),
                "report_generated_at": now.isoformat(),
                "source": "pytest-junit",
                "execution_completed": completed,
                "command_exit_code": 0,
            }
        )
    )
    return database, task, run, artifact, report, binding


@pytest.mark.parametrize(
    "completed,expected", [(True, "pass"), (None, "indeterminate")]
)
def test_junit_cli_separates_finished_and_verified(
    tmp_path: Path, completed: bool | None, expected: str
) -> None:
    database, _, run, artifact, report, binding = setup_report(
        tmp_path, completed=completed
    )
    unknown = call(["outcome", "assess", run["run_id"], *database])
    assert unknown["status"] == "unknown"
    assert unknown["verification_status"] == "unverified"
    evidence = call(
        [
            "verify",
            "junit",
            run["run_id"],
            str(report),
            "--artifact",
            str(artifact),
            "--binding-file",
            str(binding),
            *database,
        ]
    )
    assert evidence["result"] == expected
    assessed = call(
        [
            "outcome",
            "assess",
            run["run_id"],
            "--verification-id",
            evidence["verification_id"],
            "--supersedes",
            unknown["outcome_id"],
            *database,
        ]
    )
    assert assessed["status"] == ("success" if completed else "unknown")
    assert assessed["verification_status"] == (
        "verified" if completed else "unverified"
    )
    view = call(["run", "show", run["run_id"], *database])
    assert view["run"]["state"] == "finished"
    assert len(view["verifications"]) == 1
    assert len(view["outcomes"]) == 2


def test_junit_cli_rejects_wrong_snapshot_and_mixed_criteria(tmp_path: Path) -> None:
    database, _, run, artifact, report, binding = setup_report(tmp_path)
    artifact.write_text("changed after test execution\n")
    result = runner.invoke(
        app,
        [
            "verify",
            "junit",
            run["run_id"],
            str(report),
            "--artifact",
            str(artifact),
            "--binding-file",
            str(binding),
            *database,
        ],
    )
    assert result.exit_code == 2
    assert call(["run", "show", run["run_id"], *database])["verifications"] == []
    result = runner.invoke(
        app,
        [
            "task",
            "create",
            "Conflicting criteria",
            "--acceptance-id",
            "tests",
            "--acceptance-version",
            "1",
            "--required-test",
            "test::one",
            "--expected-sha256",
            "a" * 64,
            *database,
        ],
    )
    assert result.exit_code == 2
    assert len(call(["task", "list", *database])) == 1


def test_session_analysis_cli_filters_events_unavailable_at_checkpoint(
    tmp_path: Path,
) -> None:
    database = ["--database", str(tmp_path / "ledger.sqlite")]
    assert runner.invoke(app, ["init", *database]).exit_code == 0
    fixture = Path(__file__).parents[1] / "fixtures/codex/exec_capture.jsonl"
    call(["import", "codex", str(fixture), "--machine-id", "cli-example", *database])
    session = call(["sessions", *database])[0]
    snapshots = call(
        [
            "session",
            "analyze",
            session["session_id"],
            "--checkpoint",
            "2026-01-01T00:00:00Z",
            "--checkpoint",
            "2100-01-01T00:00:00Z",
            *database,
        ]
    )
    assert len(snapshots) == 2
    assert snapshots[0]["facts"]["event_count"] == 0
    assert snapshots[0]["execution_state"]["state"] == "unknown"
    assert snapshots[1]["facts"]["event_count"] == len(fixture.read_text().splitlines())
    for snapshot in snapshots:
        assert snapshot["facts"]["provenance"] == "observed"
        assert snapshot["execution_state"]["provenance"] == "inferred"
        assert snapshot["test_results"] == []
        assert snapshot["verified_task_success"] is None
    # Neither analysis nor turn completion creates task-result evidence.
    view = call(["session", "show", session["session_id"], *database])
    assert view["summary"]["verification"] == "unknown"
    assert call(["task", "list", *database]) == []
    invalid = runner.invoke(
        app,
        [
            "session",
            "analyze",
            session["session_id"],
            "--checkpoint",
            "2026-01-01",
            *database,
        ],
    )
    assert invalid.exit_code == 2


def test_invalid_binding_diagnostics_do_not_echo_private_input(tmp_path: Path) -> None:
    database, _, run, artifact, report, binding = setup_report(tmp_path)
    binding.write_text('{"command":"PRIVATE_SECRET_SENTINEL"}')
    result = runner.invoke(
        app,
        [
            "verify",
            "junit",
            run["run_id"],
            str(report),
            "--artifact",
            str(artifact),
            "--binding-file",
            str(binding),
            *database,
        ],
    )
    assert result.exit_code == 2
    assert "invalid JUnit binding receipt" in result.output
    assert "PRIVATE_SECRET_SENTINEL" not in result.output
    assert call(["run", "show", run["run_id"], *database])["verifications"] == []
