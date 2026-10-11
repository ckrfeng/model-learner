"""Controlled adapter -> ledger -> JUnit evidence -> read-only checkpoints."""

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path

from model_learner.adapters.codex import read_codex_capture
from model_learner.domain import (
    AcceptanceSpec,
    Event,
    Outcome,
    Run,
    RunSessionLink,
    RunState,
    Task,
    TaskSessionLink,
    Verification,
)
from model_learner.execution import extract_execution_checkpoints
from model_learner.storage.database import Database, Repository
from model_learner.verification import file_sha256
from model_learner.verification.junit import (
    JUnitReportBinding,
    junit_criterion,
    verify_junit,
)

FIXTURES = Path(__file__).parents[1] / "fixtures/execution"
START = datetime(2026, 10, 10, 12, tzinfo=UTC)


def at(seconds):
    return START + timedelta(seconds=seconds)


def test_controlled_history_retains_checkpoint_failures_completion_and_unknowns():
    batch = read_codex_capture(
        FIXTURES / "controlled_capture.jsonl", machine_id="controlled-machine"
    )
    assert not batch.diagnostics
    events = [
        event.model_copy(
            update={"ingested_at": event.observed_at + timedelta(seconds=1)}
        )
        for event in batch.events
    ]
    checkpoints = extract_execution_checkpoints(
        events,
        session_id=batch.sessions[0].session_id,
        checkpoints=[at(4), at(7), at(10)],
    )
    assert [result.facts.event_count for result in checkpoints] == [3, 6, 9]
    assert [result.facts.failed_tool_items for result in checkpoints] == [0, 3, 3]
    assert checkpoints[0].facts.tool_items[0].failed is None
    repeated = checkpoints[1].facts.repeated_failures
    assert len(repeated) == 1
    assert repeated[0].server == "controlled-service"
    assert repeated[0].tool == "lookup"
    assert repeated[0].failed_items == 2
    assert repeated[0].same_operation_retry is None
    assert checkpoints[2].facts.tool_items_with_unknown_failure == 1
    assert checkpoints[2].execution_state.state == "completed_turn_observed"
    assert checkpoints[2].test_state.state == "unknown"
    assert checkpoints[2].facts.token_usage["input_tokens"] == 30


def test_persisted_junit_reports_only_change_features_after_available_receipts(
    tmp_path,
):
    database = Database(tmp_path / "ledger.sqlite3")
    database.initialize()
    repo = Repository(database)
    batch = read_codex_capture(
        FIXTURES / "controlled_capture.jsonl", machine_id="controlled-machine"
    )
    session = repo.create_session(batch.sessions[0])
    for event in batch.events:
        repo.add_event(
            event.model_copy(
                update={"ingested_at": event.observed_at + timedelta(seconds=1)}
            )
        )
    task = repo.create_task(
        Task(
            description="Controlled validation and serialization checks",
            acceptance_spec=AcceptanceSpec(
                identifier="controlled-coding-checks", version="1"
            ),
            created_at=START,
            metadata={
                "junit_verifier": junit_criterion(
                    required_test_ids=[
                        "controlled.test_feature::test_validation",
                        "controlled.test_feature::test_serialization",
                    ]
                )
            },
        )
    )
    artifact = tmp_path / "controlled_artifact.py"
    artifact.write_text("# Controlled synthetic artifact snapshot\n")
    fingerprint = f"sha256:{file_sha256(artifact)}"
    run = repo.create_run(
        Run(
            task_id=task.task_id,
            state=RunState.FINISHED,
            started_at=START,
            ended_at=at(10),
            metadata={"final_artifact_fingerprint": fingerprint},
        )
    )
    repo.associate_session(
        TaskSessionLink(
            task_id=task.task_id, session_id=session.session_id, associated_at=START
        )
    )
    repo.associate_run_session(
        RunSessionLink(
            run_id=run.run_id, session_id=session.session_id, associated_at=START
        )
    )
    evidence = []
    for filename, second, exit_code in (
        ("report_failed.xml", 20, 1),
        ("report_passed.xml", 30, 0),
    ):
        report = FIXTURES / filename
        evidence.append(
            verify_junit(
                repo,
                run_id=run.run_id,
                report=report,
                artifact=artifact,
                observed_at=at(second),
                binding=JUnitReportBinding(
                    task_id=task.task_id,
                    run_id=run.run_id,
                    acceptance_spec=task.acceptance_spec,
                    artifact_fingerprint=fingerprint,
                    report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
                    report_generated_at=at(second - 1),
                    source="pytest-junit",
                    execution_completed=True,
                    command_exit_code=exit_code,
                ),
            )
        )
    events_before = repo.list_records(Event)
    evidence_before = repo.list_records(Verification)
    before, failure, still_failure, passing = extract_execution_checkpoints(
        events_before,
        session_id=session.session_id,
        checkpoints=[at(15), at(25), at(35), at(40)],
        task=task,
        run=run,
        association_available_at=START,
        artifact_available_at=at(10),
        verifications=evidence_before,
        evidence_available_at={
            evidence[0].verification_id: at(21),
            evidence[1].verification_id: at(40),
        },
    )
    assert before.execution_state.state == "completed_turn_observed"
    assert before.test_state.state == "unknown"
    assert failure.test_state.state == "failing_report_observed"
    assert still_failure == failure.model_copy(update={"checkpoint": at(35)})
    assert passing.test_state.state == "passing_report_observed"
    assert passing.test_results[-1].counts == {
        "tests": 2,
        "passed": 2,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
    }
    assert passing.test_changes[0].failure_count_delta == -1
    assert passing.verified_task_success is None
    assert repo.list_records(Event) == events_before
    assert repo.list_records(Verification) == evidence_before
    assert not repo.list_records(Outcome)
    serialized = passing.model_dump_json()
    assert "Synthetic assertion mismatch" not in serialized
    assert 'time="0.014"' not in serialized
