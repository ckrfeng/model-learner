# Model Learner status

Current work: parallel first slices — local observation and probabilistic learning
(COMPLETE; stopped for user review).
Last accepted milestone: M1.1 — Contract Hardening (user confirmed M0/M1/M1.1).
Updated: 2026-10-10

## Completed milestones

- M0-A: repository and environment assessment.
- M0-B: project foundation implemented and acceptance checks passed.
- M1-A: typed, versioned domain contracts implemented.
- M1-B: SQLite persistence, JSONL validation, and storage CLI implemented.
- M1.1: evidence-safe observation, attribution, dataset, schema-version, and
  optional project-context contracts implemented.

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
- At the M1.1 checkpoint, no agent hooks, provider integration, automated
  verification, simulator, learner, routing, or TUI had been implemented. The
  parallel slices below now add CLI observation and reference learning.
- M1.1 adds an additive second SQLite migration. New records use schema version
  2; known M1 schema version 1 records remain readable but legacy observations
  cannot be marked learning-eligible. Unknown schema versions are rejected.
- Learning observations now identify their real/simulated/benchmark dataset and
  version, have deterministic stable keys for idempotent persistence, record
  decision and label-availability times separately, and retain target acceptance
  specifications, evidence IDs, attribution status, and eligibility.
- Real version-2 observations require a task, run, outcome, acceptance
  specification, outcome/verification status, and a matching attempt for a
  single-configuration attribution. Repository checks ensure all links, evidence,
  acceptance specification, configuration, and labels agree with ledger records.
- `censored` is distinct from `unknown`; censored outcomes require a reason and
  neither censored nor unknown observations can be learning-eligible. Mixed or
  incomplete attribution is retained but cannot be eligible for
  configuration-level learning.
- Execution configurations now have a deterministic snapshot ID plus optional
  configuration and harness versions. Optional manually declared `Project` and
  `ProjectTaskLink` records group tasks without changing task identity or adding
  project discovery.

## Parallel first slices delivered

The user explicitly authorized the first useful local-observation and learning
slices together. Two implementation subagents used one initially clean checkout
with strictly separate ownership: `adapters/` and Codex fixtures/tests versus
`simulate/`, `learn/`, and statistical tests. The coordinator owns CLI integration,
CLI integration tests, README, and this status. An independent third subagent
reviewed data integrity, privacy, numerical validity, and temporal leakage.
`MODEL_LEARNER_BUILD_ORDER.txt` is absent. Domain contracts, migrations, dependency
manifest, lockfile, and master plan are unchanged.

- **Local observation (M3-A/B and narrow M3-C slice):** a versioned read-only
  adapter consumes the documented `codex exec --json` stream. A small stream
  wrapper creates `codex-exec-capture/v1` receipt-time envelopes; it never launches
  or controls Codex. Session/event records use the existing M1.1 ledger, retain
  native thread/item identities, observed provenance, source/emitter/adapter
  versions, and redaction/missingness metadata. Tool lifecycles, completed/failed
  turns, per-field token usage coverage, and emitted configuration fields can be
  rebuilt from retained metadata. Completion creates no outcomes or learner rows.
- Capture retains a metadata projection of native observations by default;
  prompts, reasoning, commands, arguments, and outputs are omitted. Full private
  payload retention is an explicit local `--retain-raw` opt-in. Capture files are
  created exclusively; ingestion diagnostics describe rejected rows without
  reproducing private contents. Replay is idempotent; conflicting capture replay
  is rejected rather than counted as another event.
- **Probabilistic learning (M2-A/B reference slice):** seeded, reproducible
  synthetic observations cover three generic configuration arms and four task
  groups, configurable probabilities, assignment imbalance, independent missing
  labels/resources, delayed labels, resource distributions, and step drift.
  Simulator probabilities and realized truth live in a separate evaluator-only
  artifact; they never become Observation features or ledger rows.
- A pure Beta-Bernoulli estimator uses a fixed Beta(1,1) default prior and exact
  configuration snapshots. It selects one source/dataset/version and acceptance
  target/budget, counts only eligible verified binary outcomes available at the
  cutoff, excludes missing/unverified/mixed/legacy records, deduplicates reimports,
  and rejects conflicting observations for one experimental unit. Outputs include
  successes/failures, posterior mean/variance, 95% equal-tail credible intervals,
  exclusions, and descriptive resources with known/missing denominators.
- Frozen chronological evaluation compares global, per-configuration, and
  unpooled references with Brier score, log loss, calibration bins, separate
  simulator-truth probability errors, and assignment-weighted/grouped interval
  coverage/width. Empty denominators produce null metrics, not zero scores.
  Training and evaluation cutoffs apply to record and label availability.
- CLI commands now include `capture codex`, `import codex`, `sessions`,
  `session show`, `sim generate`, `learn predict`, and `learn eval`. Dataset,
  acceptance version, budget, configuration, and timestamps are explicit. The
  README and `docs/CODEX_OBSERVATION.md` / `docs/PROBABILISTIC_LEARNING.md` document
  usage, assumptions, source assessment, and limitations.

### Real local validation

Tested on macOS arm64 using installed **codex-cli 0.162.0-alpha.17.2**. A bounded
CLI smoke session used `exec --json --ephemeral --ignore-user-config
--ignore-rules --sandbox read-only` with a sanitized instruction to emit a fixed
reply without tools or file changes. Initial filesystem-sandbox attempts exited
1 before JSON events; a coordinator check identified `Operation not permitted`
without displaying native stderr. An authorized execution outside the outer
filesystem sandbox, retaining Codex's own read-only agent sandbox, exited 0.
Four actual JSON events were captured as metadata-only observations: first import
inserted four events and one session, replay inserted none and recognized four
duplicates, with no diagnostics. Private source messages/stderr were not retained.
The safe capture and test ledger stay under ignored `.model-learner/`.

For this smoke test, native stdout was buffered before envelope creation. Receipt
timestamps therefore describe receipt of that buffer, never native execution
times or durations. Normal pipe capture records stream receipt as data arrives;
upstream buffering still affects timing. Native timestamps, model settings not
emitted by the CLI, monetary cost, and verified task success remain unknown.
Existing desktop rollout records were assessed structurally only; their private
format is not implemented as a supported source. This is a validated **CLI**
slice, not passive capture of the current desktop development session.

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
| `uv run pytest` | Exit 0; **29 passed in 0.52s**. M1.1 coverage includes M1-to-M1.1 migration, schema-version rejection and legacy reading, evidence-linked real observations, unknown/censored labels, mixed-attribution rejection, observation deduplication, temporal validity, dataset filtering, configuration identity, and optional project/task links. |
| `uv run ruff check .` | Exit 0; `All checks passed!` |
| `uv run ruff format --check .` | Exit 0; `16 files already formatted`. |
| `git diff --check` | Exit 0; no whitespace errors. |

M0 tests cover imports/version metadata, help, version, no arguments, invalid
options, unsupported commands, and the installed executable from an unrelated
directory. Help/version invocations create no files in that directory. The M1
tests above add domain, storage, JSONL, and CLI coverage; no master-plan edits or
later milestone implementations were made.

For this session, `.tools/bin` was prepended to `PATH`, `UV_CACHE_DIR` was set to
`$PWD/.uv-cache`, and `UV_PYTHON` selected Codex's bundled Python 3.12.14 during
setup. The resulting `.venv` is ready for local use. These environment overrides
are local validation setup and are not required on a machine with uv/Python ready.

### Parallel-slice checks — 2026-10-10

Used the existing Python 3.12.14 / uv 0.12.24 / Ruff 0.16.10 environment with
repository-local tool/cache paths. No new dependencies were required.

| Command / check | Actual result |
| --- | --- |
| Pre-change `uv run pytest` | Exit 0; **29 passed in 0.56s**. |
| Observation subagent's owned tests | Exit 0; **24 passed in 0.43s**; owned Ruff lint/format checks passed. |
| Learning subagent's owned tests | Exit 0; **47 passed in 0.45s**; owned Ruff lint/format checks passed. |
| Final coordinator `uv run pytest` | Exit 0; **105 passed in 1.62s**. |
| Final coordinator `uv run ruff check .` | Exit 0; `All checks passed!` |
| Final coordinator `uv run ruff format --check .` | Exit 0; `38 files already formatted`. |
| `uv run model-learner --help` | Exit 0; includes capture/import/session inspection and sim/learn commands. |
| Installed CLI, actual metadata-only smoke capture in a fresh final ledger | First import: one session, four events; replay: zero new sessions/events, four duplicates; both had no diagnostics. `sessions` and `session show` returned four timeline events with native time/cost/latency unknown and verification unknown. |
| `git diff --check` | Exit 0; no whitespace errors. |

Coordinator integration coverage exercises capture privacy, diagnostic exit codes,
exclusive capture destinations, import/replay/timeline, arbitrary valid manual
event metadata, simulation persistence/deduplication, explicit scenario overrides,
target/dataset filtering, prediction, held-out evaluation, timezone rejection,
and prior-only empty datasets. Existing M1.1 tests continue passing unchanged.
The obsolete CLI test treating `learn` as unsupported now checks the still
unsupported `recommend` command instead.

Independent review identified and prompted regression-tested fixes for modified
capture replay (including native thread/version changes), phantom sessions after
rejected replay, malformed thread-boundary attribution, and unsupported ledger
payload inspection. Statistical review prompted explicit numeric-domain limits
and complete target/budget reporting. No contract or migration alteration was
needed. The two implementation slices remain independently testable.
Final independent review confirmed **105 tests passed**, clean Ruff/formatting,
and no unresolved blockers within the requested slice.

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
- Treat schema version 1 as a legacy read format and schema version 2 as the
  current M1.1 contract. Future schema versions require an explicit supported
  parser or upcaster; they are not accepted optimistically.
- Preserve project context as an explicit optional relationship. It is a manual
  grouping only and is not task identity, task difficulty, automatic discovery,
  or global activity tracking.

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
- The real-agent importer supports explicitly selected Codex CLI streams only;
  existing desktop sessions and passive desktop capture remain unsupported.
  No automatic verifier or verified real task-observation builder was added.
- JSONL imports enforce record schemas and relationships but are intentionally
  limited to primary records; task/session links are managed through the explicit
  attach command rather than exported as a standalone record stream.
- SQLite is appropriate for the local-first, single-machine milestone but does
  not make multiple concurrent writers parallel; short transactions and a busy
  timeout reduce contention only.
- Decision/policy records, automatic project discovery, execution-state inference,
  and cache-cost attribution remain unimplemented. The new learner estimates a
  selected binary acceptance target; it does not claim full expected utility,
  causal model superiority, or effects of interventions/budgets.
- Simulator outcomes are independent; missingness is completely at random.
  Correlated retries, outcome-dependent missingness, and selection confounding
  are not modeled. Conflicting assessment revisions require explicit resolution
  before fitting. Simulation calibration does not establish real calibration.
- The initial numerical interval implementation supports shapes at least 0.5,
  posterior shape sum at most 100,000, and interval mass in [0.5, 0.999]. The
  default Beta(1,1) permits at most 99,998 verified trials per cell. Unsupported
  inputs fail explicitly; larger-scale numerical methods are deferred.
- Receipt-time capture is affected by upstream buffering and is not execution
  duration. The native CLI stream lacks complete event IDs; independently
  recapturing a stream is not globally deduplicated. Replay requires retaining
  the same capture identity and machine ID. Metadata/raw-retention policy and
  emitter-version enrichment cannot rewrite already persisted events.

## Next recommended tasks (not started)

- Review these two slices before expanding scope. For observation, investigate a
  documented read-only export/interface for existing desktop sessions, then add
  only the narrow supported source needed to capture development activity.
- Begin M4's explicit bounded task/run association and independently sourced
  acceptance evidence so real captures can produce eligible learning records.
- Exercise the existing simulator/evaluator across multiple seeds, missingness,
  imbalance, and drift scenarios before considering a more complex estimator.
- No recommendation, routing, fine-tuning, runtime intervention learning, TUI,
  or AI Governor controls were implemented. Stop at this first useful slice.
  No commit, push, merge, publication, or global hook installation was made.
