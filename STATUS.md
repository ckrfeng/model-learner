# Model Learner status

Current milestone: M1 — Data Contracts and Local Persistence (COMPLETE; awaiting user review)
Last accepted milestone: M0 — Project Foundation.
Updated: 2026-10-09

## Completed milestones

- M0-A: repository and environment assessment.
- M0-B: project foundation implemented and acceptance checks passed.
- M1-A: typed, versioned domain contracts implemented.
- M1-B: SQLite persistence, JSONL validation, and storage CLI implemented.

## Implementation status

- Repository assessment: existing plan and minimal README, no implementation or
  development tooling; existing Git remote preserved.
- Python 3.12+ package under `src/model_learner/`, with an installed `model-learner`
  console entry point. Help and version output work; no arguments display help
  with exit code 2, and unsupported input is rejected with exit code 2.
- uv-managed editable installation and lockfile; pytest and Ruff in the default
  development group. README documents installation and development checks.
- Created `.gitignore`, `.python-version`, `pyproject.toml`, `uv.lock`, `AGENTS.md`,
  `STATUS.md`, `src/model_learner/__init__.py`, `src/model_learner/cli.py`,
  `tests/unit/test_package.py`, and `tests/integration/test_cli.py`.
  Updated the existing `README.md`; the master plan is unchanged.
- Domain contracts now cover tasks, native sessions, explicit task/session links,
  runs, attempts, execution configurations, events, verifications, outcomes, and
  future observations. Every record has a schema version. Timestamps must be
  timezone-aware, unknown telemetry remains nullable, and invalid values fail
  Pydantic validation.
- Task identity is distinct from session identity. Associations are stored only in
  `task_sessions`; registering a session does not attach it to a task or imply a
  complete task. Runs are bounded executions of a task; attempts are the
  configuration-bearing segments inside runs.
- Execution configuration records provider, model, optional model version,
  optional reasoning level, optional harness, and metadata. Missing provider,
  model, usage, latency, and cost are represented as `null`, never zero.
- Outcomes separately record `success`, `failure`, `abandoned`, or `unknown` and
  `verified`, `partially_verified`, or `unverified`. Verification evidence has its
  own provenance and identifiers. An `agent_report` outcome itself is always
  unverified; a separate independently sourced assessment can cite verification.
- SQLite uses numbered, forward-only migrations, foreign keys, WAL mode, a busy
  timeout, canonical JSON rows, and short transactions. Events use a stable key
  and idempotent insert behavior; outcomes remain append-only. Evidence linked to
  a different task or run is rejected.
- Added JSONL validation/import/export for primary records. Observation queries
  require an explicit `real`, `simulated`, or `benchmark` source kind so future
  summaries cannot silently mix datasets.
- Added `model-learner init`, `task create`, `task list`, `session register`,
  `task attach-session`, and `records show` CLI operations, plus JSONL record
  import/export/validation commands. README documents the M1 local ledger flow.
- Pydantic v2 is a runtime dependency; `uv.lock` was updated accordingly.
- No agent hooks, real provider integrations, automated verification, simulator,
  learner, routing, or TUI have been implemented.

## Test evidence

Executed on macOS arm64 with Python 3.12.14, uv 0.12.24, pytest 9.1.1,
Typer 0.27.3, Rich 14.3.4, and Ruff 0.16.10 on 2026-10-09.

| Command / check | Actual result |
| --- | --- |
| `uv sync` | Exit 0; resolved 14 packages, installed 13 including the editable project. |
| `uv run pytest` | Exit 0; **8 passed in 0.20s**. |
| `uv run ruff check .` | Exit 0; `All checks passed!` |
| `uv run ruff format --check .` | Exit 0; `8 files already formatted`. |
| `uv run model-learner --help` | Exit 0; readable help with `--help` and `--version`. |
| `uv run model-learner --version` | Exit 0; `model-learner 0.1.0`. |
| `uv sync --locked --offline` | Exit 0; lockfile accepted, 13 packages checked. |
| `uv build --offline` | Exit 0; source distribution and wheel built. |
| Archive inspection | Wheel contains only the two package modules and distribution metadata, with the correct console entry point. Source distribution excludes local tools, virtual environment, caches, OS files, and private runtime data. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `uv sync --locked` | Exit 0; installed Pydantic v2 and its locked dependencies into the local virtual environment. |
| `uv run pytest` | Exit 0; **21 passed in 0.41s**. Covers schema validation, invalid timestamps/outcomes, null measurements, migrations, task/session links, evidence integrity, event idempotence, JSONL round-trip, source-kind separation, and M1 CLI operations. |
| `uv run ruff check .` | Exit 0; `All checks passed!` |
| `uv run ruff format --check .` | Exit 0; `16 files already formatted`. |
| `uv run model-learner --help` | Exit 0; lists `init`, `task`, `session`, and `records` commands. |

M0 tests cover imports/version metadata, help, version, no arguments, invalid
options, unsupported commands, and the installed executable from an unrelated
directory. Help/version invocations create no files in that directory. The M1
tests above add domain, storage, JSONL, and CLI coverage; no master-plan edits or
later milestone implementations were made.

For this session, `.tools/bin` was prepended to `PATH`, `UV_CACHE_DIR` was set to
`$PWD/.uv-cache`, and `UV_PYTHON` selected Codex's bundled Python 3.12.14 during
setup. The resulting `.venv` is ready for local use. These environment overrides
are local validation setup and are not required on a machine with uv/Python ready.

## Decisions

- Use the plan's `src/model_learner/` layout and Typer/Rich CLI.
- Package version comes from `src/model_learner/__init__.py`; Hatchling derives
  distribution metadata from the same value.
- M0 added only foundation dependencies; M1 adds Pydantic and defers later components.
- Pin the development interpreter to Python 3.12; package metadata allows 3.12+.
- Use Pydantic v2 for strict, versioned contracts and the standard-library
  `sqlite3` module for local persistence; preserve each canonical record as JSON
  alongside indexed relationship columns.
- Make the M1 database migration-only: upgrades are forward-only and no downgrade
  path is supplied yet. The first migration creates the complete M1 ledger.

## Known issues / blockers

- No known M0 implementation defects or unresolved blockers.
- uv is installed in the ignored `.tools/bin/`, rather than the default shell PATH.
  From this checkout, use `export PATH="$PWD/.tools/bin:$PATH"` before uv commands,
  or install uv normally as described in the README. Python 3.12.14 is available
  through the existing `.venv`; the system `python3` remains 3.9.6.
- Initial sandboxed dependency download failed due to restricted network access;
  the authorized network retry succeeded. Locked offline sync now works locally.
- uv build warned that the repository-local cache might enter distributions;
  archive inspection confirmed it is excluded by `.gitignore`.
- Other operating systems and Python versions have not been tested.
- The pre-existing tracked `.DS_Store` was left unchanged. `.gitignore` prevents
  adding new OS metadata but does not remove files already tracked by Git.
- M1 does not have a real-agent importer or verifier. CLI persistence is for
  explicitly supplied local records, and no command claims an agent report is an
  independently verified outcome.
- JSONL imports enforce record schemas and relationships but are intentionally
  limited to primary records; task/session links are managed through the explicit
  attach command rather than exported as a standalone record stream.
- SQLite is appropriate for the local-first, single-machine milestone but does
  not make multiple concurrent writers parallel; short transactions and a busy
  timeout reduce contention only.

## Next recommended milestone

- M2 is NOT STARTED. The next milestone is M2-A: a deterministic seeded
  simulator with explicitly separate known-truth evaluator data. Do not begin it
  without a new user instruction.
- Review the M1 diff and checks before committing. No commit, push, merge, or
  publication was made.
