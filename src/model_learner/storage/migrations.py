"""Ordered, forward-only SQLite migrations."""

MIGRATIONS: tuple[str, ...] = (
    """
    CREATE TABLE tasks (
        task_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        data TEXT NOT NULL
    );
    CREATE TABLE sessions (
        session_id TEXT PRIMARY KEY,
        source TEXT NOT NULL,
        native_session_id TEXT,
        data TEXT NOT NULL
    );
    CREATE TABLE task_sessions (
        task_id TEXT NOT NULL REFERENCES tasks(task_id),
        session_id TEXT NOT NULL REFERENCES sessions(session_id),
        associated_at TEXT NOT NULL,
        relationship TEXT NOT NULL,
        data TEXT NOT NULL,
        PRIMARY KEY (task_id, session_id)
    );
    CREATE TABLE runs (
        run_id TEXT PRIMARY KEY,
        task_id TEXT NOT NULL REFERENCES tasks(task_id),
        state TEXT NOT NULL,
        started_at TEXT,
        data TEXT NOT NULL
    );
    CREATE TABLE attempts (
        attempt_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        started_at TEXT,
        data TEXT NOT NULL
    );
    CREATE TABLE events (
        event_id TEXT PRIMARY KEY,
        stable_key TEXT NOT NULL UNIQUE,
        session_id TEXT REFERENCES sessions(session_id),
        run_id TEXT REFERENCES runs(run_id),
        observed_at TEXT NOT NULL,
        ingested_at TEXT NOT NULL,
        data TEXT NOT NULL
    );
    CREATE TABLE verifications (
        verification_id TEXT PRIMARY KEY,
        task_id TEXT REFERENCES tasks(task_id),
        run_id TEXT REFERENCES runs(run_id),
        observed_at TEXT NOT NULL,
        data TEXT NOT NULL
    );
    CREATE TABLE outcomes (
        outcome_id TEXT PRIMARY KEY,
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        recorded_at TEXT NOT NULL,
        data TEXT NOT NULL
    );
    CREATE TABLE observations (
        observation_id TEXT PRIMARY KEY,
        source_kind TEXT NOT NULL,
        task_group TEXT NOT NULL,
        recorded_at TEXT NOT NULL,
        data TEXT NOT NULL
    );
    CREATE INDEX runs_task_id_idx ON runs(task_id);
    CREATE INDEX attempts_run_id_idx ON attempts(run_id);
    CREATE INDEX events_session_id_idx ON events(session_id);
    CREATE INDEX events_run_id_idx ON events(run_id);
    CREATE INDEX verifications_run_id_idx ON verifications(run_id);
    CREATE INDEX outcomes_run_id_idx ON outcomes(run_id);
    CREATE INDEX observations_source_kind_idx ON observations(source_kind);
    """,
    """
    CREATE TABLE projects (
        project_id TEXT PRIMARY KEY,
        created_at TEXT NOT NULL,
        data TEXT NOT NULL
    );
    CREATE TABLE project_tasks (
        project_id TEXT NOT NULL REFERENCES projects(project_id),
        task_id TEXT NOT NULL REFERENCES tasks(task_id),
        associated_at TEXT NOT NULL,
        relationship TEXT NOT NULL,
        data TEXT NOT NULL,
        PRIMARY KEY (project_id, task_id)
    );
    ALTER TABLE observations ADD COLUMN stable_key TEXT;
    ALTER TABLE observations ADD COLUMN dataset_id TEXT;
    ALTER TABLE observations ADD COLUMN dataset_version TEXT;
    CREATE UNIQUE INDEX observations_stable_key_idx ON observations(stable_key);
    CREATE INDEX observations_dataset_idx
        ON observations(source_kind, dataset_id, dataset_version);
    CREATE INDEX project_tasks_task_id_idx ON project_tasks(task_id);
    """,
    """
    CREATE TABLE run_sessions (
        run_id TEXT NOT NULL REFERENCES runs(run_id),
        session_id TEXT NOT NULL REFERENCES sessions(session_id),
        associated_at TEXT NOT NULL,
        data TEXT NOT NULL,
        PRIMARY KEY (run_id, session_id)
    );
    CREATE INDEX run_sessions_session_id_idx ON run_sessions(session_id);
    """,
)
