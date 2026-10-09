"""Exercise SQLite migrations, relationship integrity, and JSONL persistence."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    DataSourceKind,
    Event,
    ExecutionConfiguration,
    Observation,
    Outcome,
    OutcomeStatus,
    Provenance,
    Run,
    Session,
    Task,
    TaskSessionLink,
    Verification,
    VerificationResult,
    VerificationStatus,
)
from model_learner.storage.database import Database, Repository, StorageError
from model_learner.storage.jsonl import export_jsonl, import_jsonl, validate_jsonl
from model_learner.storage.migrations import MIGRATIONS


def make_task() -> Task:
    return Task(
        description="Repair parser regression",
        acceptance_spec=AcceptanceSpec(identifier="pytest", version="1"),
    )


def repository(path: Path) -> Repository:
    database = Database(path)
    database.initialize()
    return Repository(database)


def test_migrations_are_versioned_and_idempotent(tmp_path: Path) -> None:
    database = Database(tmp_path / "learner.sqlite3")
    database.initialize()
    database.initialize()

    with database.connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM schema_migrations"
        ).fetchone()
    assert count["count"] == len(MIGRATIONS)


def test_task_session_relationship_is_explicit(tmp_path: Path) -> None:
    repo = repository(tmp_path / "learner.sqlite3")
    declared_task = repo.create_task(make_task())
    session = repo.create_session(Session(source="codex", native_session_id="thread-1"))

    assert repo.list_sessions_for_task(declared_task.task_id) == []
    repo.associate_session(
        TaskSessionLink(task_id=declared_task.task_id, session_id=session.session_id)
    )
    assert repo.list_sessions_for_task(declared_task.task_id) == [session]


def test_records_preserve_null_measurements_and_event_deduplication(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path / "learner.sqlite3")
    declared_task = repo.create_task(make_task())
    run = repo.create_run(Run(task_id=declared_task.task_id))
    attempt = repo.create_attempt(
        Attempt(
            run_id=run.run_id,
            configuration=ExecutionConfiguration(provider="openai", model="example"),
        )
    )
    timestamp = datetime(2026, 10, 9, tzinfo=UTC)
    event = Event(
        observed_at=timestamp,
        source="fixture",
        source_version="1",
        machine_id="test-machine",
        capture_method="import",
        native_session_id="thread-1",
        run_id=run.run_id,
        event_type="tool_finished",
        provenance=Provenance.OBSERVED,
    )

    first = repo.add_event(event)
    second = repo.add_event(event.model_copy(update={"event_id": uuid4()}))

    assert attempt.cost_usd is None
    assert attempt.input_tokens is None
    assert first.event_id == event.event_id
    assert second.event_id == event.event_id


def test_outcome_evidence_must_belong_to_its_run_or_task(tmp_path: Path) -> None:
    repo = repository(tmp_path / "learner.sqlite3")
    first_task = repo.create_task(make_task())
    second_task = repo.create_task(make_task())
    first_run = repo.create_run(Run(task_id=first_task.task_id))
    second_run = repo.create_run(Run(task_id=second_task.task_id))
    evidence = repo.add_verification(
        Verification(
            run_id=second_run.run_id,
            acceptance_spec=second_task.acceptance_spec,
            verifier_type="pytest",
            result=VerificationResult.PASS,
        )
    )
    outcome = Outcome(
        run_id=first_run.run_id,
        status=OutcomeStatus.SUCCESS,
        verification_status=VerificationStatus.VERIFIED,
        assessment_source="automated_verifier",
        evidence_ids=(evidence.verification_id,),
    )

    with pytest.raises(StorageError, match="different (task|run)"):
        repo.add_outcome(outcome)


def test_jsonl_round_trip_keeps_identifiers_and_labels(tmp_path: Path) -> None:
    source = repository(tmp_path / "source.sqlite3")
    declared_task = source.create_task(make_task())
    export_path = tmp_path / "tasks.jsonl"

    assert export_jsonl(source, Task, export_path) == 1
    assert validate_jsonl(export_path) == 1

    destination = repository(tmp_path / "destination.sqlite3")
    assert import_jsonl(destination, export_path) == 1
    restored = destination.get(Task, declared_task.task_id)

    assert restored == declared_task


def test_observation_queries_require_an_explicit_source_kind(tmp_path: Path) -> None:
    repo = repository(tmp_path / "learner.sqlite3")
    real = repo.add_observation(
        Observation(
            source_kind=DataSourceKind.REAL,
            task_group="maintenance",
            configuration=ExecutionConfiguration(provider="example", model="model-a"),
        )
    )
    repo.add_observation(
        Observation(
            source_kind=DataSourceKind.SIMULATED,
            task_group="maintenance",
            configuration=ExecutionConfiguration(provider="example", model="model-a"),
        )
    )

    with pytest.raises(ValueError, match="explicit source_kind"):
        repo.list_records(Observation)
    assert repo.list_records(Observation, source_kind="real") == [real]
