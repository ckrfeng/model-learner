"""SQLite persistence that preserves canonical model JSON and evidence history."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
from typing import Any, TypeVar
from uuid import UUID

from pydantic import BaseModel

from model_learner.domain.models import (
    Attempt,
    Event,
    Observation,
    Outcome,
    Project,
    ProjectTaskLink,
    Run,
    Session,
    Task,
    TaskSessionLink,
    Verification,
)
from model_learner.storage.migrations import MIGRATIONS

Record = TypeVar("Record", bound=BaseModel)


class StorageError(RuntimeError):
    """Raised when a record cannot be persisted without breaking relationships."""


class Database:
    """An SQLite database with numbered, forward-only migrations."""

    def __init__(self, path: Path | str) -> None:
        self.path = Path(path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        connection.execute("PRAGMA journal_mode = WAL")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create the database (including parents) and apply outstanding migrations."""
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connection() as connection:
            connection.execute(
                "CREATE TABLE IF NOT EXISTS schema_migrations "
                "(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL "
                "DEFAULT CURRENT_TIMESTAMP)"
            )
            applied = {
                row["version"]
                for row in connection.execute("SELECT version FROM schema_migrations")
            }
            for version, migration in enumerate(MIGRATIONS, start=1):
                if version not in applied:
                    connection.executescript(migration)
                    connection.execute(
                        "INSERT INTO schema_migrations(version) VALUES (?)", (version,)
                    )

    @property
    def is_initialized(self) -> bool:
        if not self.path.exists():
            return False
        with self.connection() as connection:
            row = connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name = 'schema_migrations'"
            ).fetchone()
        return row is not None


class Repository:
    """Relationship-aware persistence for immutable evidence records."""

    def __init__(self, database: Database) -> None:
        if not database.is_initialized:
            raise StorageError(f"database is not initialized: {database.path}")
        self.database = database

    @staticmethod
    def _json(record: BaseModel) -> str:
        return json.dumps(
            record.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        )

    @staticmethod
    def _identifier(value: UUID | str) -> str:
        return str(value)

    @staticmethod
    def _exists(
        connection: sqlite3.Connection, table: str, column: str, value: UUID | str
    ) -> bool:
        row = connection.execute(
            f"SELECT 1 FROM {table} WHERE {column} = ?", (str(value),)
        ).fetchone()
        return row is not None

    def _require(
        self, connection: sqlite3.Connection, table: str, column: str, value: UUID | str
    ) -> None:
        if not self._exists(connection, table, column, value):
            raise StorageError(f"unknown {table[:-1]}: {value}")

    def _insert(self, table: str, columns: dict[str, Any]) -> None:
        names = ", ".join(columns)
        placeholders = ", ".join("?" for _ in columns)
        with self.database.connection() as connection:
            try:
                connection.execute(
                    f"INSERT INTO {table} ({names}) VALUES ({placeholders})",
                    tuple(columns.values()),
                )
            except sqlite3.IntegrityError as error:
                raise StorageError(str(error)) from error

    def create_task(self, task: Task) -> Task:
        self._insert(
            "tasks",
            {
                "task_id": self._identifier(task.task_id),
                "created_at": task.created_at.isoformat(),
                "data": self._json(task),
            },
        )
        return task

    def create_project(self, project: Project) -> Project:
        self._insert(
            "projects",
            {
                "project_id": self._identifier(project.project_id),
                "created_at": project.created_at.isoformat(),
                "data": self._json(project),
            },
        )
        return project

    def associate_task_project(self, link: ProjectTaskLink) -> ProjectTaskLink:
        with self.database.connection() as connection:
            self._require(connection, "projects", "project_id", link.project_id)
            self._require(connection, "tasks", "task_id", link.task_id)
            try:
                connection.execute(
                    "INSERT INTO project_tasks "
                    "(project_id, task_id, associated_at, relationship, data) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        str(link.project_id),
                        str(link.task_id),
                        link.associated_at.isoformat(),
                        link.relationship,
                        self._json(link),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise StorageError("project and task are already associated") from error
        return link

    def create_session(self, session: Session) -> Session:
        self._insert(
            "sessions",
            {
                "session_id": self._identifier(session.session_id),
                "source": session.source,
                "native_session_id": session.native_session_id,
                "data": self._json(session),
            },
        )
        return session

    def associate_session(self, link: TaskSessionLink) -> TaskSessionLink:
        with self.database.connection() as connection:
            self._require(connection, "tasks", "task_id", link.task_id)
            self._require(connection, "sessions", "session_id", link.session_id)
            try:
                connection.execute(
                    "INSERT INTO task_sessions "
                    "(task_id, session_id, associated_at, relationship, data) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        str(link.task_id),
                        str(link.session_id),
                        link.associated_at.isoformat(),
                        link.relationship,
                        self._json(link),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise StorageError("task and session are already associated") from error
        return link

    def create_run(self, run: Run) -> Run:
        with self.database.connection() as connection:
            self._require(connection, "tasks", "task_id", run.task_id)
            try:
                connection.execute(
                    "INSERT INTO runs (run_id, task_id, state, started_at, data) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        str(run.run_id),
                        str(run.task_id),
                        run.state.value,
                        run.started_at.isoformat() if run.started_at else None,
                        self._json(run),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise StorageError(str(error)) from error
        return run

    def create_attempt(self, attempt: Attempt) -> Attempt:
        with self.database.connection() as connection:
            self._require(connection, "runs", "run_id", attempt.run_id)
            try:
                connection.execute(
                    "INSERT INTO attempts (attempt_id, run_id, started_at, data) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        str(attempt.attempt_id),
                        str(attempt.run_id),
                        attempt.started_at.isoformat() if attempt.started_at else None,
                        self._json(attempt),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise StorageError(str(error)) from error
        return attempt

    def add_event(self, event: Event) -> Event:
        """Insert an event once, returning the first canonical row on re-import."""
        with self.database.connection() as connection:
            if event.session_id is not None:
                self._require(connection, "sessions", "session_id", event.session_id)
            if event.run_id is not None:
                self._require(connection, "runs", "run_id", event.run_id)
            connection.execute(
                "INSERT INTO events (event_id, stable_key, session_id, run_id, "
                "observed_at, ingested_at, data) "
                "VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT(stable_key) DO NOTHING",
                (
                    str(event.event_id),
                    event.stable_key,
                    str(event.session_id) if event.session_id else None,
                    str(event.run_id) if event.run_id else None,
                    event.observed_at.isoformat(),
                    event.ingested_at.isoformat(),
                    self._json(event),
                ),
            )
            row = connection.execute(
                "SELECT data FROM events WHERE stable_key = ?", (event.stable_key,)
            ).fetchone()
        if row is None:  # pragma: no cover - defensive SQLite contract guard
            raise StorageError("event insertion did not return a persisted row")
        return Event.model_validate_json(row["data"])

    def add_verification(self, verification: Verification) -> Verification:
        with self.database.connection() as connection:
            if verification.task_id is not None:
                self._require(connection, "tasks", "task_id", verification.task_id)
            if verification.run_id is not None:
                self._require(connection, "runs", "run_id", verification.run_id)
                run = connection.execute(
                    "SELECT task_id FROM runs WHERE run_id = ?",
                    (str(verification.run_id),),
                ).fetchone()
                if verification.task_id is not None and run["task_id"] != str(
                    verification.task_id
                ):
                    raise StorageError("verification task_id does not match its run")
            try:
                connection.execute(
                    "INSERT INTO verifications "
                    "(verification_id, task_id, run_id, observed_at, data) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        str(verification.verification_id),
                        str(verification.task_id) if verification.task_id else None,
                        str(verification.run_id) if verification.run_id else None,
                        verification.observed_at.isoformat(),
                        self._json(verification),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise StorageError(str(error)) from error
        return verification

    def add_outcome(self, outcome: Outcome) -> Outcome:
        with self.database.connection() as connection:
            self._require(connection, "runs", "run_id", outcome.run_id)
            run = connection.execute(
                "SELECT task_id FROM runs WHERE run_id = ?", (str(outcome.run_id),)
            ).fetchone()
            for evidence_id in outcome.evidence_ids:
                evidence = connection.execute(
                    "SELECT task_id, run_id, data FROM verifications "
                    "WHERE verification_id = ?",
                    (str(evidence_id),),
                ).fetchone()
                if evidence is None:
                    raise StorageError(f"unknown verification evidence: {evidence_id}")
                if evidence["task_id"] not in (None, run["task_id"]):
                    raise StorageError("outcome evidence belongs to a different task")
                if evidence["run_id"] not in (None, str(outcome.run_id)):
                    raise StorageError("outcome evidence belongs to a different run")
                verification = Verification.model_validate_json(evidence["data"])
                task_row = connection.execute(
                    "SELECT data FROM tasks WHERE task_id = ?", (run["task_id"],)
                ).fetchone()
                task = Task.model_validate_json(task_row["data"])
                if verification.acceptance_spec != task.acceptance_spec:
                    raise StorageError(
                        "outcome evidence acceptance_spec does not match its task"
                    )
            try:
                connection.execute(
                    "INSERT INTO outcomes (outcome_id, run_id, recorded_at, data) "
                    "VALUES (?, ?, ?, ?)",
                    (
                        str(outcome.outcome_id),
                        str(outcome.run_id),
                        outcome.recorded_at.isoformat(),
                        self._json(outcome),
                    ),
                )
            except sqlite3.IntegrityError as error:
                raise StorageError(str(error)) from error
        return outcome

    def add_observation(self, observation: Observation) -> Observation:
        """Insert one canonical learning record, checking real evidence links."""
        with self.database.connection() as connection:
            if (
                observation.source_kind.value == "real"
                and observation.schema_version == 2
            ):
                self._validate_real_observation(connection, observation)
            dataset = observation.dataset
            connection.execute(
                "INSERT INTO observations "
                "(observation_id, stable_key, source_kind, dataset_id, "
                "dataset_version, "
                "task_group, recorded_at, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?) "
                "ON CONFLICT(stable_key) DO NOTHING",
                (
                    str(observation.observation_id),
                    observation.stable_key,
                    observation.source_kind.value,
                    dataset.dataset_id if dataset else None,
                    dataset.dataset_version if dataset else None,
                    observation.task_group,
                    observation.recorded_at.isoformat(),
                    self._json(observation),
                ),
            )
            row = connection.execute(
                "SELECT data FROM observations WHERE stable_key = ?",
                (observation.stable_key,),
            ).fetchone()
        if row is None:  # pragma: no cover - defensive SQLite contract guard
            raise StorageError("observation insertion did not return a persisted row")
        return Observation.model_validate_json(row["data"])

    def _validate_real_observation(
        self, connection: sqlite3.Connection, observation: Observation
    ) -> None:
        """Ensure a real learner row cannot outlive or contradict its evidence."""
        assert observation.task_id is not None
        assert observation.run_id is not None
        assert observation.outcome_id is not None
        assert observation.acceptance_spec is not None
        self._require(connection, "tasks", "task_id", observation.task_id)
        self._require(connection, "runs", "run_id", observation.run_id)
        run = connection.execute(
            "SELECT task_id FROM runs WHERE run_id = ?", (str(observation.run_id),)
        ).fetchone()
        if run["task_id"] != str(observation.task_id):
            raise StorageError("observation task_id does not match its run")
        task_row = connection.execute(
            "SELECT data FROM tasks WHERE task_id = ?", (str(observation.task_id),)
        ).fetchone()
        task = Task.model_validate_json(task_row["data"])
        if observation.acceptance_spec != task.acceptance_spec:
            raise StorageError("observation acceptance_spec does not match its task")
        outcome_row = connection.execute(
            "SELECT data FROM outcomes WHERE outcome_id = ?",
            (str(observation.outcome_id),),
        ).fetchone()
        if outcome_row is None:
            raise StorageError(f"unknown outcome: {observation.outcome_id}")
        outcome = Outcome.model_validate_json(outcome_row["data"])
        if outcome.run_id != observation.run_id:
            raise StorageError("observation outcome belongs to a different run")
        if observation.outcome_status != outcome.status:
            raise StorageError("observation outcome_status does not match its outcome")
        if observation.verification_status != outcome.verification_status:
            raise StorageError(
                "observation verification_status does not match its outcome"
            )
        if observation.evidence_ids != outcome.evidence_ids:
            raise StorageError("observation evidence_ids do not match its outcome")
        if observation.attempt_id is not None:
            attempt_row = connection.execute(
                "SELECT data FROM attempts WHERE attempt_id = ?",
                (str(observation.attempt_id),),
            ).fetchone()
            if attempt_row is None:
                raise StorageError(f"unknown attempt: {observation.attempt_id}")
            attempt = Attempt.model_validate_json(attempt_row["data"])
            if attempt.run_id != observation.run_id:
                raise StorageError("observation attempt belongs to a different run")
            if (
                attempt.configuration.configuration_id
                != observation.configuration.configuration_id
            ):
                raise StorageError(
                    "observation configuration does not match its attempt"
                )
        if observation.eligible_for_configuration_learning:
            if observation.verification_status.value != "verified":
                raise StorageError(
                    "eligible real observations require verified outcomes"
                )
            if not observation.evidence_ids:
                raise StorageError("eligible real observations require evidence")

    def get(self, record_type: type[Record], identifier: UUID | str) -> Record | None:
        table, column = _record_table(record_type)
        with self.database.connection() as connection:
            row = connection.execute(
                f"SELECT data FROM {table} WHERE {column} = ?", (str(identifier),)
            ).fetchone()
        return record_type.model_validate_json(row["data"]) if row else None

    def list_tasks(self) -> list[Task]:
        return self._list(Task, "ORDER BY created_at")

    def list_sessions_for_task(self, task_id: UUID | str) -> list[Session]:
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT sessions.data FROM sessions JOIN task_sessions "
                "ON sessions.session_id = task_sessions.session_id "
                "WHERE task_sessions.task_id = ? ORDER BY task_sessions.associated_at",
                (str(task_id),),
            ).fetchall()
        return [Session.model_validate_json(row["data"]) for row in rows]

    def list_projects_for_task(self, task_id: UUID | str) -> list[Project]:
        with self.database.connection() as connection:
            rows = connection.execute(
                "SELECT projects.data FROM projects JOIN project_tasks "
                "ON projects.project_id = project_tasks.project_id "
                "WHERE project_tasks.task_id = ? ORDER BY project_tasks.associated_at",
                (str(task_id),),
            ).fetchall()
        return [Project.model_validate_json(row["data"]) for row in rows]

    def list_observations(
        self, source_kind: str, *, dataset_id: str | None = None
    ) -> list[Observation]:
        """Require an explicit source kind so datasets are never implicitly mixed."""
        with self.database.connection() as connection:
            if dataset_id is None:
                rows = connection.execute(
                    "SELECT data FROM observations WHERE source_kind = ? "
                    "ORDER BY recorded_at",
                    (source_kind,),
                ).fetchall()
            else:
                rows = connection.execute(
                    "SELECT data FROM observations WHERE source_kind = ? "
                    "AND dataset_id = ? ORDER BY recorded_at",
                    (source_kind, dataset_id),
                ).fetchall()
        return [Observation.model_validate_json(row["data"]) for row in rows]

    def list_records(
        self,
        record_type: type[Record],
        *,
        source_kind: str | None = None,
        dataset_id: str | None = None,
    ) -> list[Record]:
        """List one record type without combining source datasets."""
        if record_type is Observation:
            if source_kind is None:
                raise ValueError("observation listing requires an explicit source_kind")
            return self.list_observations(source_kind, dataset_id=dataset_id)  # type: ignore[return-value]
        return self._list(record_type)

    def import_record(self, record: BaseModel) -> BaseModel:
        """Persist a validated JSONL record through normal integrity checks."""
        writers = {
            Task: self.create_task,
            Project: self.create_project,
            Session: self.create_session,
            Run: self.create_run,
            Attempt: self.create_attempt,
            Event: self.add_event,
            Verification: self.add_verification,
            Outcome: self.add_outcome,
            Observation: self.add_observation,
        }
        try:
            return writers[type(record)](record)  # type: ignore[arg-type]
        except KeyError as error:
            raise ValueError(
                f"unsupported record type: {type(record).__name__}"
            ) from error

    def _list(self, record_type: type[Record], order_by: str = "") -> list[Record]:
        table, _ = _record_table(record_type)
        with self.database.connection() as connection:
            rows = connection.execute(f"SELECT data FROM {table} {order_by}").fetchall()
        return [record_type.model_validate_json(row["data"]) for row in rows]


def _record_table(record_type: type[BaseModel]) -> tuple[str, str]:
    tables: dict[type[BaseModel], tuple[str, str]] = {
        Task: ("tasks", "task_id"),
        Project: ("projects", "project_id"),
        Session: ("sessions", "session_id"),
        Run: ("runs", "run_id"),
        Attempt: ("attempts", "attempt_id"),
        Event: ("events", "event_id"),
        Verification: ("verifications", "verification_id"),
        Outcome: ("outcomes", "outcome_id"),
        Observation: ("observations", "observation_id"),
    }
    try:
        return tables[record_type]
    except KeyError as error:
        raise ValueError(f"unsupported record type: {record_type.__name__}") from error
