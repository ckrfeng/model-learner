"""Explicit task/run/session boundaries and declared execution segments."""

from datetime import datetime
from uuid import UUID

from model_learner.domain.models import (
    Attempt,
    ExecutionConfiguration,
    Run,
    RunSessionLink,
    RunState,
    Session,
    Task,
    TaskSessionLink,
)
from model_learner.storage.database import Repository, StorageError


def create_bounded_run(
    repository: Repository,
    *,
    task_id: UUID,
    session_id: UUID,
    started_at: datetime,
    ended_at: datetime,
    state: RunState = RunState.FINISHED,
    final_artifact_fingerprint: str | None = None,
) -> Run:
    """Declare one bounded execution; completion never implies verification.

    Boundaries are user declarations. Native event records remain untouched and
    receipt timestamps are not promoted into native execution timestamps.
    """
    task = repository.get(Task, task_id)
    if task is None:
        raise StorageError("unknown task")
    if repository.get(Session, session_id) is None:
        raise StorageError("unknown session")
    if final_artifact_fingerprint is not None:
        from model_learner.verification import validate_fingerprint

        validate_fingerprint(final_artifact_fingerprint)
    run = Run(
        task_id=task_id,
        started_at=started_at,
        ended_at=ended_at,
        state=state,
        resource_budget=task.resource_budget,
        metadata={
            "boundary_source": "human_declaration",
            "final_artifact_fingerprint": final_artifact_fingerprint,
        },
    )
    repository.validate_run_session_bounds(run, session_id)
    if session_id not in {
        item.session_id for item in repository.list_sessions_for_task(task_id)
    }:
        repository.associate_session(
            TaskSessionLink(task_id=task_id, session_id=session_id)
        )
    repository.create_run(run)
    repository.associate_run_session(
        RunSessionLink(run_id=run.run_id, session_id=session_id)
    )
    return run


def declare_attempt(
    repository: Repository,
    *,
    run_id: UUID,
    configuration: ExecutionConfiguration,
    started_at: datetime,
    ended_at: datetime,
    declaration_source: str = "human",
) -> Attempt:
    """Declare a configuration segment without asserting emitted model telemetry."""
    run = repository.get(Run, run_id)
    if run is None:
        raise StorageError("unknown run")
    if not declaration_source.strip():
        raise ValueError("declaration_source must be nonempty")
    attempt = Attempt(
        run_id=run_id,
        configuration=configuration,
        started_at=started_at,
        ended_at=ended_at,
        metadata={
            "configuration_provenance": "human_declaration",
            "declaration_source": declaration_source,
            "boundary_source": "human_declaration",
        },
    )
    if run.started_at is None or run.ended_at is None:
        raise ValueError("attempt declaration requires a bounded run")
    if started_at < run.started_at or ended_at > run.ended_at:
        raise ValueError("attempt boundaries must be inside the run")
    for existing in repository.list_records(Attempt):
        if existing.run_id != run_id:
            continue
        if existing.started_at is None or existing.ended_at is None:
            raise ValueError("existing attempt has unknown boundaries")
        if started_at < existing.ended_at and ended_at > existing.started_at:
            raise ValueError("attempt segments must not overlap")
    return repository.create_attempt(attempt)
