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
)
