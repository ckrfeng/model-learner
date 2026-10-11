"""All persistence paths serialize and validate append-only revision edges."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta
from pathlib import Path
from threading import Barrier
from uuid import uuid4

import pytest

from model_learner.domain.models import AcceptanceSpec, Outcome, Run, Task, Verification
from model_learner.storage.database import Database, Repository, StorageError
from model_learner.storage.jsonl import JsonlValidationError, import_jsonl

TIME = datetime(2026, 1, 1, tzinfo=UTC)


def ledger(tmp_path: Path) -> tuple[Repository, Run]:
    database = Database(tmp_path / "ledger.sqlite")
    database.initialize()
    repository = Repository(database)
    task = repository.create_task(
        Task(
            description="Synthetic",
            acceptance_spec=AcceptanceSpec(identifier="x", version="1"),
        )
    )
    return repository, repository.create_run(Run(task_id=task.task_id))


def assessment(run: Run, **values) -> Outcome:
    return Outcome(
        **(
            dict(
                run_id=run.run_id,
                status="unknown",
                verification_status="unverified",
                assessment_source="fixture",
                recorded_at=TIME,
            )
            | values
        )
    )


@pytest.mark.parametrize("invalid", ["missing", "foreign", "backwards", "self"])
def test_invalid_revision_edge_rejected(tmp_path: Path, invalid: str) -> None:
    repository, run = ledger(tmp_path)
    parent_run = (
        repository.create_run(Run(task_id=run.task_id)) if invalid == "foreign" else run
    )
    parent = repository.add_outcome(assessment(parent_run))
    identifier = uuid4()
    revision = assessment(
        run,
        outcome_id=identifier,
        supersedes_outcome_id=(
            identifier
            if invalid == "self"
            else uuid4()
            if invalid == "missing"
            else parent.outcome_id
        ),
        recorded_at=TIME - timedelta(seconds=1) if invalid == "backwards" else TIME,
    )
    with pytest.raises(StorageError):
        repository.add_outcome(revision)
    assert repository.list_records(Outcome) == [parent]


def test_equal_time_revision_valid_and_branching_import_rejected(
    tmp_path: Path,
) -> None:
    repository, run = ledger(tmp_path)
    parent = repository.add_outcome(assessment(run))
    child = repository.add_outcome(
        assessment(run, supersedes_outcome_id=parent.outcome_id)
    )
    branch = assessment(run, supersedes_outcome_id=parent.outcome_id)
    source = tmp_path / "branch.jsonl"
    source.write_text(
        json.dumps({"record_type": "outcome", "record": branch.model_dump(mode="json")})
        + "\n"
    )
    with pytest.raises(JsonlValidationError, match="already has a revision"):
        import_jsonl(repository, source)
    assert repository.list_records(Outcome) == [parent, child]


def test_competing_revisions_cannot_branch(tmp_path: Path) -> None:
    repository, run = ledger(tmp_path)
    parent = repository.add_outcome(assessment(run))
    barrier = Barrier(2)

    def append(_: int) -> str:
        barrier.wait(timeout=5)
        try:
            repository.add_outcome(
                assessment(run, supersedes_outcome_id=parent.outcome_id)
            )
            return "accepted"
        except StorageError as error:
            assert "already has a revision" in str(error)
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(append, range(2))) == ["accepted", "rejected"]
    assert len(repository.list_records(Outcome)) == 2


def test_future_verification_cannot_support_backdated_assessment(
    tmp_path: Path,
) -> None:
    repository, run = ledger(tmp_path)
    task = repository.get(Task, run.task_id)
    evidence = repository.add_verification(
        Verification(
            run_id=run.run_id,
            acceptance_spec=task.acceptance_spec,
            verifier_type="fixture",
            result="pass",
            observed_at=TIME + timedelta(seconds=1),
        )
    )
    with pytest.raises(StorageError, match="predates"):
        repository.add_outcome(
            assessment(
                run,
                status="success",
                verification_status="verified",
                evidence_ids=(evidence.verification_id,),
            )
        )
    assert repository.list_records(Outcome) == []
