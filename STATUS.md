# Model Learner status

Current milestone: M0 — Project Foundation (COMPLETE; awaiting user review)
Last accepted milestone: none; implementation awaits user review.
Updated: 2026-10-09

## Completed milestones

- M0-A: repository and environment assessment.
- M0-B: project foundation implemented and acceptance checks passed.

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
- No domain contracts, database, collection, simulation, learning, routing, hooks,
  or TUI have been implemented.

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

Tests cover imports/version metadata, help, version, no arguments, invalid options,
unsupported commands, and the installed executable from an unrelated directory.
Help/version invocations create no files in that directory. Diff review found only
M0 foundation changes; no master-plan edits or later milestone implementations.

For this session, `.tools/bin` was prepended to `PATH`, `UV_CACHE_DIR` was set to
`$PWD/.uv-cache`, and `UV_PYTHON` selected Codex's bundled Python 3.12.14 during
setup. The resulting `.venv` is ready for local use. These environment overrides
are local validation setup and are not required on a machine with uv/Python ready.

## Decisions

- Use the plan's `src/model_learner/` layout and Typer/Rich CLI.
- Package version comes from `src/model_learner/__init__.py`; Hatchling derives
  distribution metadata from the same value.
- Add only dependencies needed for M0. Pydantic and later components are deferred.
- Pin the development interpreter to Python 3.12; package metadata allows 3.12+.

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

## Next recommended milestone

- M1 is NOT STARTED. Begin with M1-A: Pydantic v2 domain contracts and versioned
  validation for events, tasks, runs, attempts, verification, assessments, and
  observations, preserving provenance, explicit dataset source, time fields,
  unknown/censored outcomes, and nullable resource costs.
- Then M1-B adds SQLite migrations/repositories, append-only evidence, stable IDs
  and deduplication, validated JSONL round trips, and the small storage CLI. Test
  invalid records, idempotent imports, missing values, and dataset separation.
- Await user review of M0 and explicit instruction before starting M1. Review the
  foundational diff and listed checks; no commit, push, or publication was made.
