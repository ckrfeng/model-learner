"""Explicit run/session relations preserve task identity and imported evidence."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest

from model_learner.domain.models import (
    AcceptanceSpec,
    Run,
    RunSessionLink,
    Session,
    Task,
    TaskSessionLink,
)
from model_learner.storage.database import Database, Repository, StorageError
from model_learner.storage.migrations import MIGRATIONS


def test_upgrade_existing_ledger_and_explicit_run_association(tmp_path: Path) -> None:
    db = Database(tmp_path / "ledger.sqlite")
    with db.connection() as connection:
        connection.execute(
            "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY)"
        )
        for version, migration in enumerate(MIGRATIONS[:2], start=1):
            connection.executescript(migration)
            connection.execute("INSERT INTO schema_migrations VALUES (?)", (version,))
    db.initialize()
    repo = Repository(db)
    task = repo.create_task(
        Task(
            description="Declared",
            acceptance_spec=AcceptanceSpec(identifier="digest", version="1"),
        )
    )
    session = repo.create_session(Session(source="codex", native_session_id="native"))
    run = repo.create_run(Run(task_id=task.task_id))
    link = RunSessionLink(run_id=run.run_id, session_id=session.session_id)
    assert repo.list_sessions_for_run(run.run_id) == []
    with pytest.raises(StorageError, match="first be explicitly linked"):
        repo.associate_run_session(link)
    repo.associate_session(
        TaskSessionLink(task_id=task.task_id, session_id=session.session_id)
    )
    assert repo.associate_run_session(link) == link
    replay = RunSessionLink(
        run_id=run.run_id,
        session_id=session.session_id,
        associated_at=datetime(2030, 1, 1, tzinfo=UTC),
    )
    assert repo.associate_run_session(replay) == link
    assert repo.list_run_session_links(run.run_id) == [link]
    assert repo.list_sessions_for_run(run.run_id) == [session]
    assert task.task_id != session.session_id != run.run_id
    with pytest.raises(StorageError, match="unknown"):
        repo.associate_run_session(
            RunSessionLink(run_id=uuid4(), session_id=session.session_id)
        )


def test_link_to_other_task_does_not_authorize_run_link(tmp_path: Path) -> None:
    db = Database(tmp_path / "ledger.sqlite")
    db.initialize()
    repo = Repository(db)
    spec = AcceptanceSpec(identifier="digest", version="1")
    first = repo.create_task(Task(description="First", acceptance_spec=spec))
    second = repo.create_task(Task(description="Second", acceptance_spec=spec))
    session = repo.create_session(Session(source="codex"))
    repo.associate_session(
        TaskSessionLink(task_id=first.task_id, session_id=session.session_id)
    )
    run = repo.create_run(Run(task_id=second.task_id))
    with pytest.raises(StorageError, match="first be explicitly linked"):
        repo.associate_run_session(
            RunSessionLink(run_id=run.run_id, session_id=session.session_id)
        )
    assert repo.list_sessions_for_run(run.run_id) == []


def test_overlap_rejected_on_initial_and_additional_session_links(
    tmp_path: Path,
) -> None:
    db = Database(tmp_path / "ledger.sqlite")
    db.initialize()
    repo = Repository(db)
    spec = AcceptanceSpec(identifier="digest", version="1")
    task = repo.create_task(Task(description="First", acceptance_spec=spec))
    other_task = repo.create_task(Task(description="Second", acceptance_spec=spec))
    session = repo.create_session(Session(source="codex.exec"))
    for declared in (task, other_task):
        repo.associate_session(
            TaskSessionLink(task_id=declared.task_id, session_id=session.session_id)
        )
    start = datetime(2026, 1, 1, tzinfo=UTC)
    end = datetime(2026, 1, 2, tzinfo=UTC)
    first = repo.create_run(Run(task_id=task.task_id, started_at=start, ended_at=end))
    link = RunSessionLink(run_id=first.run_id, session_id=session.session_id)
    repo.associate_run_session(link)
    assert repo.associate_run_session(link) == link
    for second_start, second_end in (
        (start, end),
        (end, datetime(2026, 1, 3, tzinfo=UTC)),
    ):
        second = Run(
            task_id=other_task.task_id, started_at=second_start, ended_at=second_end
        )
        with pytest.raises(StorageError, match="overlap"):
            repo.validate_run_session_bounds(second, session.session_id)
        repo.create_run(second)
        with pytest.raises(StorageError, match="overlap"):
            repo.associate_run_session(
                RunSessionLink(run_id=second.run_id, session_id=session.session_id)
            )
        assert repo.list_sessions_for_run(second.run_id) == []
    disjoint = repo.create_run(
        Run(
            task_id=other_task.task_id,
            started_at=datetime(2026, 1, 3, tzinfo=UTC),
            ended_at=datetime(2026, 1, 4, tzinfo=UTC),
        )
    )
    repo.associate_run_session(
        RunSessionLink(run_id=disjoint.run_id, session_id=session.session_id)
    )
    assert repo.list_sessions_for_run(disjoint.run_id) == [session]


def test_concurrent_overlapping_associations_are_serialized(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor
    from threading import Barrier

    db = Database(tmp_path / "ledger.sqlite")
    db.initialize()
    repo = Repository(db)
    task = repo.create_task(
        Task(
            description="One execution",
            acceptance_spec=AcceptanceSpec(identifier="digest", version="1"),
        )
    )
    session = repo.create_session(Session(source="codex.exec"))
    repo.associate_session(
        TaskSessionLink(task_id=task.task_id, session_id=session.session_id)
    )
    runs = [
        repo.create_run(
            Run(
                task_id=task.task_id,
                started_at=datetime(2026, 1, 1, tzinfo=UTC),
                ended_at=datetime(2026, 1, 2, tzinfo=UTC),
            )
        )
        for _ in range(2)
    ]
    ready = Barrier(2)

    def associate(run: Run) -> str:
        ready.wait(timeout=5)
        try:
            repo.associate_run_session(
                RunSessionLink(run_id=run.run_id, session_id=session.session_id)
            )
            return "accepted"
        except StorageError as error:
            assert "overlap" in str(error)
            return "rejected"

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(associate, runs))
    assert sorted(results) == ["accepted", "rejected"]
    assert sum(len(repo.list_run_session_links(run.run_id)) for run in runs) == 1
