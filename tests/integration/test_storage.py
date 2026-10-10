"""Exercise SQLite migrations, relationship integrity, and JSONL persistence."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    AttributionStatus,
    DatasetReference,
    DataSourceKind,
    Event,
    ExecutionConfiguration,
    Observation,
    Outcome,
    OutcomeStatus,
    Project,
    ProjectTaskLink,
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


def dataset(kind: DataSourceKind, identifier: str = "test-data") -> DatasetReference:
    return DatasetReference(
        source_kind=kind,
        dataset_id=identifier,
        dataset_version="1",
    )


def real_observation(
    repo: Repository,
    *,
    status: OutcomeStatus = OutcomeStatus.SUCCESS,
    eligible: bool = True,
) -> Observation:
    declared_task = repo.create_task(make_task())
    run = repo.create_run(Run(task_id=declared_task.task_id))
    attempt = repo.create_attempt(
        Attempt(
            run_id=run.run_id,
            configuration=ExecutionConfiguration(provider="example", model="model-a"),
        )
    )
    evidence = ()
    verification_status = VerificationStatus.UNVERIFIED
    if status in (OutcomeStatus.SUCCESS, OutcomeStatus.FAILURE):
        verification = repo.add_verification(
            Verification(
                run_id=run.run_id,
                acceptance_spec=declared_task.acceptance_spec,
                verifier_type="pytest",
                result=(
                    VerificationResult.PASS
                    if status is OutcomeStatus.SUCCESS
                    else VerificationResult.FAIL
                ),
            )
        )
        evidence = (verification.verification_id,)
        verification_status = VerificationStatus.VERIFIED
    outcome = repo.add_outcome(
        Outcome(
            run_id=run.run_id,
            status=status,
            verification_status=verification_status,
            assessment_source="automated_verifier",
            evidence_ids=evidence,
            censor_reason="verification unavailable"
            if status is OutcomeStatus.CENSORED
            else None,
        )
    )
    decision_at = datetime(2026, 10, 9, tzinfo=UTC)
    label_available_at = (
        datetime(2026, 10, 10, tzinfo=UTC)
        if status in (OutcomeStatus.SUCCESS, OutcomeStatus.FAILURE)
        else None
    )
    return Observation(
        source_kind=DataSourceKind.REAL,
        dataset=dataset(DataSourceKind.REAL, "local-ledger"),
        task_group="maintenance",
        configuration=attempt.configuration,
        task_id=declared_task.task_id,
        run_id=run.run_id,
        attempt_id=attempt.attempt_id,
        outcome_id=outcome.outcome_id,
        outcome_status=outcome.status,
        verification_status=outcome.verification_status,
        evidence_ids=outcome.evidence_ids,
        acceptance_spec=declared_task.acceptance_spec,
        attribution_status=AttributionStatus.SINGLE_CONFIGURATION,
        eligible_for_configuration_learning=eligible,
        decision_at=decision_at,
        label_available_at=label_available_at,
        recorded_at=datetime(2026, 10, 11, tzinfo=UTC),
    )


def test_migrations_are_versioned_and_idempotent(tmp_path: Path) -> None:
    database = Database(tmp_path / "learner.sqlite3")
    database.initialize()
    database.initialize()

    with database.connection() as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS count FROM schema_migrations"
        ).fetchone()
    assert count["count"] == len(MIGRATIONS)


def test_migrations_upgrade_an_m1_database(tmp_path: Path) -> None:
    database = Database(tmp_path / "learner.sqlite3")
    with database.connection() as connection:
        connection.execute(
            "CREATE TABLE schema_migrations "
            "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL "
            "DEFAULT CURRENT_TIMESTAMP)"
        )
        connection.executescript(MIGRATIONS[0])
        connection.execute("INSERT INTO schema_migrations(version) VALUES (1)")

    database.initialize()

    with database.connection() as connection:
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(observations)").fetchall()
        }
    assert {"stable_key", "dataset_id", "dataset_version"} <= columns


def test_task_session_relationship_is_explicit(tmp_path: Path) -> None:
    repo = repository(tmp_path / "learner.sqlite3")
    declared_task = repo.create_task(make_task())
    session = repo.create_session(Session(source="codex", native_session_id="thread-1"))

    assert repo.list_sessions_for_task(declared_task.task_id) == []
    repo.associate_session(
        TaskSessionLink(task_id=declared_task.task_id, session_id=session.session_id)
    )
    assert repo.list_sessions_for_task(declared_task.task_id) == [session]


def test_project_task_relationship_is_optional_and_explicit(tmp_path: Path) -> None:
    repo = repository(tmp_path / "learner.sqlite3")
    declared_task = repo.create_task(make_task())
    project = repo.create_project(Project(name="model-learner"))

    assert repo.list_projects_for_task(declared_task.task_id) == []
    repo.associate_task_project(
        ProjectTaskLink(project_id=project.project_id, task_id=declared_task.task_id)
    )
    assert repo.list_projects_for_task(declared_task.task_id) == [project]


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
    simulated = repo.add_observation(
        Observation(
            source_kind=DataSourceKind.SIMULATED,
            dataset=dataset(DataSourceKind.SIMULATED, "sim-a"),
            source_record_id="sim-row-1",
            task_group="maintenance",
            configuration=ExecutionConfiguration(provider="example", model="model-a"),
        )
    )
    benchmark = repo.add_observation(
        Observation(
            source_kind=DataSourceKind.BENCHMARK,
            dataset=dataset(DataSourceKind.BENCHMARK, "benchmark-a"),
            source_record_id="benchmark-row-1",
            task_group="maintenance",
            configuration=ExecutionConfiguration(provider="example", model="model-a"),
        )
    )

    with pytest.raises(ValueError, match="explicit source_kind"):
        repo.list_records(Observation)
    assert repo.list_records(Observation, source_kind="simulated") == [simulated]
    assert repo.list_records(Observation, source_kind="benchmark") == [benchmark]
    assert repo.list_observations("simulated", dataset_id="sim-a") == [simulated]


def test_real_observation_requires_matching_evidence_and_deduplicates(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path / "learner.sqlite3")
    observation = real_observation(repo)

    first = repo.add_observation(observation)
    second = repo.add_observation(
        observation.model_copy(update={"observation_id": uuid4()})
    )

    assert first.observation_id == observation.observation_id
    assert second.observation_id == observation.observation_id
    assert repo.list_observations("real", dataset_id="local-ledger") == [first]

    mismatched = observation.model_copy(update={"evidence_ids": ()})
    with pytest.raises(StorageError, match="evidence_ids"):
        repo.add_observation(mismatched)


def test_unknown_and_censored_real_observations_remain_ineligible(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path / "learner.sqlite3")
    unknown = real_observation(repo, status=OutcomeStatus.UNKNOWN, eligible=False)
    censored = real_observation(repo, status=OutcomeStatus.CENSORED, eligible=False)

    assert repo.add_observation(unknown).outcome_status is OutcomeStatus.UNKNOWN
    assert repo.add_observation(censored).outcome_status is OutcomeStatus.CENSORED
