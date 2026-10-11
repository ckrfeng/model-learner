# Model Learner status

Current work: requested Workstreams A/B — coding-task verification and
execution-state analysis (COMPLETE; stopped after independent review).
Last user-confirmed work: historical assessment resolution and drift investigation
complete.
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

## Requested Workstreams A/B/C — 2026-10-10

The coordinator read the plan, AGENTS.md, prior status and implementation. The
build-order file remains absent. Three Codex subagents had separate ownership:
new run/verification/observation modules and tests; simulation/learning stress
modules and tests; and Desktop feasibility research. The coordinator owned shared
contracts/migrations/storage, CLI integration, integration tests, README and this
status. The research agent independently reviewed the final implementation.
The master plan, dependencies and lockfile are unchanged.

### Workstream A — delivered and real integration exercised

- Added the additive `RunSessionLink` contract and migration 3 (`run_sessions`).
  Existing version-1/2 contracts and primary records remain readable. Associations
  require the session to be explicitly linked to the run's task. Imported events
  are never rewritten to attach a run.
- Explicit bounded runs retain declared state, receipt-time range, final artifact
  fingerprint and boundary provenance. Attempts retain exact configuration
  snapshots, contiguous boundaries and human declaration source; no inferred task
  classification or fabricated native model telemetry is used.
- Added a deterministic **read-only SHA-256 file verifier**. The expected digest is
  declared with the task; the final artifact snapshot is declared with the run.
  Verification retains artifact reference/fingerprint, acceptance version, result,
  verifier version, observation time, criterion and observed provenance. It reads
  bytes without retaining them and checks for file changes while hashing. It never
  executes an arbitrary verifier command or launches an agent.
- Completed execution remains separate from assessment. Evidence-free assessment
  yields unknown; explicit human labels remain unverified. Matching final evidence
  yields verified success/failure against this exact bytes-only criterion.
  Wrong/stale artifact/spec, contradictory result, foreign evidence, invalid times
  and branching supersession are rejected. Assessments remain append-only.
- Real observation building retains task/run/outcome/attempt/evidence links,
  dataset identity, acceptance/budget, label availability and eligibility reasons.
  It requires actual captured Codex CLI events in the selected receipt-time range.
  Mixed, incomplete or contradicted attribution, unknown/unverified labels, and
  unknown/exceeded declared budgets stay ineligible. Unknown resources stay null.
  Rebuilding the same derivation is idempotent. Quality reports explicitly count
  assessment derivations, with dataset and missingness denominators.
- Added `task create --expected-sha256`, `run create/attach-session/attempt/show`,
  `verify file`, `outcome assess/human`, and `observations build/quality`. Existing
  source-filtered JSONL export serves real observations. Usage and semantics are
  documented in `README.md` and `docs/TASK_VERIFICATION.md`.
- Independent review reproduced two defects: repeating the same captured run
  counted it twice, and concurrent association could bypass overlap validation.
  Inclusive overlapping bounds for the same session are now rejected (including
  different tasks and additional session links). Preflight avoids ordinary phantom
  runs, and `BEGIN IMMEDIATE` serializes the association check and write. Regression
  tests cover repeat, shared endpoints, disjoint ranges and competing writers.

**Actual real workflow:** An operator-only validation script under ignored
`.model-learner/verification-smoke/` declared an exact sanitized reply digest
**before** running installed `codex-cli 0.162.0-alpha.17.2` on macOS arm64.
The explicit invocation used `exec --json --ephemeral --ignore-user-config
--ignore-rules --skip-git-repo-check --sandbox read-only`, an isolated temporary
working directory, `--model gpt-6.1-sol`, low reasoning, and `--output-last-message`.
It requested a fixed reply without tools or file changes. The operator launches
this test; the shipped Model Learner APIs/CLI remain observers. Based on the
previous demonstrated outer-sandbox failure, this bounded validation received
execution approval outside that outer sandbox while retaining Codex's own
read-only sandbox. No native stderr or raw prompts/messages were retained.

The CLI exited 0 and the streaming capture retained four metadata-only events,
with zero diagnostics. First import inserted four; replay inserted zero and
recognized four duplicates. A distinct task/run/session and explicitly declared
configuration segment were linked. Finished execution first produced unknown,
unverified, ineligible assessment. The predeclared exact reply bytes then passed
verification; an appended assessment produced success/verified and an eligible
real observation. Rebuild returned the same observation ID. JSONL exported both
real derivations (unknown and assessed, in explicitly distinct cohorts), and
fitting only the assessed dataset counted **one** label. Cost and latency remained
null; configuration provenance was the operator's explicit command declaration,
not an emitted native model/version. Native model version remains unknown.
This validates the real capture-to-verification path for a fixed reply; it does
not establish coding-task utility or native Desktop capture.

### Workstream B — delivered with actual multi-seed evidence

- Added pure `run_stress_suite()` and eight reproducible scenarios: balanced,
  homogeneous, sparse, imbalanced, drift, missing, delayed-pending and delayed-mature.
  Each seed/scenario has an explicit simulated dataset and complete configuration.
  The existing Beta(1,1) estimator and seeded generation behavior are preserved.
- Reports retain per-seed counts/cutoffs/exclusions, calibration bins and ECE,
  Brier/log loss, evaluator-only truth errors and interval coverage/width,
  assignment-weighted and represented-cell macro coverage, all 12 cell predictions,
  across-seed variation, and paired global/per-arm/unpooled comparisons.
  Undefined metrics remain null. Repeated cell predictions are not represented as
  independent coverage trials, and Monte Carlo SE is not real-world confidence.
- Added `learn stress` with repeated `--seed`/`--scenario`, count, frozen split,
  calibration bins and exclusive optional JSON output. It never writes ledger rows.
  `docs/STATISTICAL_EVALUATION.md` records complete reproduction and actual results.
- Actual reference experiment: seeds 0–19, 1,000 observations per seed/scenario
  (sparse capped at 48), 60% training split, ten calibration bins. Balanced unpooled
  mean Brier was **0.197198** and latent 95%-interval coverage **0.968000**.
  Homogeneous global Brier **0.211467** beat unpooled **0.216226**. Sparse scenarios
  had 4–8 prior-only cells per seed; imbalance had 1–6 despite 600 training labels.
  Under a sharp 0.9→0.2 drift at the split, unpooled Brier was **0.630445**, coverage
  **0.000000**, and mean interval width **0.168369**: concrete overconfidence.
  Global marginal ECE **0.005608** in heterogeneous balanced data masked conditional
  coverage **0.233375**. Missing/delayed scenarios reduced evidence without recoding
  unknown as failure or admitting future labels. No complex ML was introduced.

### Workstream C — feasibility assessed, no adapter

- `docs/CODEX_DESKTOP_FEASIBILITY.md` records official documented interfaces,
  coverage, reliability, privacy and integration difficulty. The research agent
  used the OpenAI Docs skill, public CLI help and generated installed-version
  protocol schemas; it did not access private transcripts or app databases.
- App-server read-only stored-thread APIs, prospective OTel and lifecycle hooks
  are candidates. Public historical schemas have optional timing/configuration
  and lack complete historical per-turn model/usage. The default public daemon
  control socket was absent (`daemon version` exited 1). Desktop visibility,
  passive connectivity and delivery fidelity therefore remain unvalidated.
- No Desktop adapter, daemon, hook, telemetry setting or control integration was
  installed. Continue supporting explicit CLI capture. The report proposes a
  narrow sanitized public-transport feasibility spike as future work only.

### Actual verification and independent review

Existing local Python 3.12.14 / uv 0.12.24 / Ruff 0.16.10 environment, repository
local tool/cache paths; no dependency installation was needed.

| Command / check | Actual result |
| --- | --- |
| Pre-change `uv run pytest` | Exit 0; **105 passed in 1.45s**. |
| A owned tests / lint / format | **32 passed in 0.69s**; lint passed; 5 files formatted. |
| B learning/storage tests / lint / format | **66 passed in 2.85s**; lint and format passed. |
| Final coordinator `uv run pytest` | Exit 0; **164 passed in 4.94s**. |
| Final coordinator `uv run ruff check .` | Exit 0; `All checks passed!` |
| Final coordinator `uv run ruff format --check .` | Exit 0; **51 files already formatted**. |
| Installed CLI `--help` and `learn stress --help` | Exit 0; new workflow/stress commands and flags present. |
| Real operator-run CLI workflow | Exit 0; four events, safe replay, unknown then verified, eligible real export, one learner label. |
| Independent final suite | **164 passed in 4.72s**; lint and formatting passed. |
| Independent association/task/CLI regressions | **29 passed**; duplicate and concurrent overlap repros resolved. |
| `git diff --check` | Exit 0; no whitespace errors. |

The independent reviewer found no remaining blocking implementation issue within
these workstreams after the regression-tested fixes. Real validation completed
subsequently with the result above. Fixtures remain sanitized/synthetic and real
validation artifacts remain ignored; they are never claimed as Git fixtures.

**Remaining limits:** Digest verification proves exact bytes of one regular file,
not general correctness; a copy of identical bytes satisfies that criterion.
Configuration/boundary declarations are trusted explicit user assertions; native
metadata remains separate. Multi-operation run creation can leave a harmless
unlinked run after exceptional I/O/concurrent failures; the builder rejects it.
The learner still needs explicit resolution when a cohort contains multiple
assessment derivations for one run; this smoke intentionally selected distinct
cohorts for unknown and assessed rows. Simulation uses independent Bernoulli
trials, completely-at-random missingness, independent assignment and simple step
drift; correlated retries, confounding and biased delayed outcomes remain untested.
No synthetic result establishes real calibration. Desktop capture remains
unvalidated; the fixed-reply CLI smoke establishes neither Desktop nor coding-task
performance.

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

## Historical assessment resolution and drift investigation — 2026-10-10

The coordinator inspected the plan, repository instructions, status, code and
tests before editing. Two implementation subagents had non-overlapping ownership:
observation derivation/resolution and its tests/docs; recent-window inference,
drift evaluation, additive gradual simulation and its tests/docs. The coordinator
owned repository integrity checks, CLI integration, frozen evaluation inputs,
integration tests, package exports, README and this status. A third subagent
performed independent read-only statistical and data-integrity review. Domain
contracts, migrations, dependencies, lockfile and the master plan are unchanged.

### Assessment resolution delivered

- Added pure `resolve_assessment` and persisted-cohort
  `resolve_observation_revisions`, plus read-only evidence-checked
  `resolve_real_observations`. A cutoff includes only available assessment
  revisions and evidence. One complete unbranched visible chain selects its head;
  equal timestamps resolve by lineage. Missing/unavailable or foreign parents,
  backwards edges, cycles, branches, multiple roots and conflicting identities
  fail closed with deterministic diagnostics. Future branches cannot invalidate
  earlier state. Original outcome/evidence/observation rows remain append-only.
- Preserved unknown and censored heads without fallback to older binary labels.
  Exact proof/target/evidence/attribution/resource-budget checks still determine
  learning eligibility. At most one observation per run is returned; stable
  identities and deduplication prevent revisions or replay becoming extra trials.
- Refactored the existing builder into read-only derivation plus the compatible
  idempotent persistence wrapper. Historical learning requires a unique matching
  builder derivation recorded by the cutoff. Its immutable attempt IDs reconstruct
  the earlier declaration set, preserving explicit task-group overrides and
  excluding later declarations. Missing or malformed proof fails closed. Without
  proof, the assessment remains visible but configuration/attribution availability
  is unknown and learning is ineligible.
- Existing task/run session association timestamps and capture observation/ingest
  times are checked independently. Added read-only task/session link access.
  Repository outcome insertion now validates parent identity/run/time and evidence
  time and atomically checks branching with insertion, covering JSONL imports and
  competing writers without a migration.
- Added `observations resolve`. Real `learn predict` resolves the selected cohort
  at its cutoff; real `learn eval` independently resolves training and scoring
  snapshots, so a later censored/revised assessment cannot change frozen training.
  Pure estimator APIs retain explicit resolved-row input and conflict rejection.
  See `docs/ASSESSMENT_RESOLUTION.md` for APIs and limits.

**Historical limits:** Availability follows trusted declared timestamps. Run and
Attempt lack declaration receipts; Verification lacks ingestion receipts. A
persisted derivation proves availability only within those existing contracts,
not actual SQLite insertion time. Without a recorded proof, complete historical
attribution cannot be reconstructed. Snapshots expose these limitations. No
backdated unknown knowledge is promoted to a verified learning observation.

### Drift investigation delivered

- Independently reproduced the original frozen 20-seed stress results. Unpooled
  coverage was balanced **0.968000**, homogeneous **0.945250**, sparse **0.970000**,
  imbalanced **0.949750**, missing **0.961000**, delayed-pending **0.953672** and
  delayed-mature **0.957750**. The sharp split **0.9 to 0.2** drift alone had
  **0.000000** coverage in that suite. Stationary coverage is compatible with the
  stated assumptions in these tested scenarios, not a real-world guarantee.
- Audited the coverage metric and information flow. It checks whether an interval
  contains evaluator-only latent success probability, not whether it contains a
  future binary outcome. A stationary fixed-parameter posterior cannot promise
  current-time coverage after drift. Frozen pre-change training cannot adapt.
  Truth is evaluator-only; training checks decision, record and label cutoffs.
- Added explicit `RecentWindowBetaBernoulli`: fixed Beta prior with labels from
  `[cutoff - window_duration, cutoff)`, using decision age, never arrival age.
  The existing full-history estimator remains the default. No exponentially
  weighted method was added; another uncertain interval convention was unnecessary
  to test the requested simple baseline.
- Added `run_drift_suite` and `learn drift`: block-prequential full-history versus
  fixed 120/300-step windows, 50-step refits, seeds **0–19**, **1,000** decisions
  per seed/scenario and ten calibration bins. Seven scenarios cover heterogeneous
  and homogeneous stationary conditions, abrupt and gradual drift, 85% independent
  missing labels, 98:1:1 assignments and delayed verification. Additive gradual
  simulation preserves existing default fingerprints and seeded prefixes.
- Reports retain per-seed Brier, calibration bins/ECE, empirical current-p coverage,
  widths, assignment-weighted and represented-cell macro coverage, cell sample
  counts, tail metrics, paired differences and adaptation censoring. Adaptation
  requires three consecutive blocks with probability MAE at most 0.1 after drift
  ends. Recovery time has refit-step resolution, retrospective certification and
  survivor-only means; unrecovered seeds are explicitly censored.

| Scenario | Full-history Brier / ECE / coverage | Recent 120 Brier / ECE / coverage |
| --- | --- | --- |
| Stationary heterogeneous | 0.194192 / 0.035466 / 0.965833 | 0.207131 / 0.068866 / 0.959667 |
| Stationary homogeneous | 0.214616 / 0.045822 / 0.954583 | 0.227774 / 0.104458 / 0.959083 |
| Abrupt drift | 0.369329 / 0.440229 / 0.000000 | 0.221218 / 0.165865 / 0.808667 |
| Gradual drift | 0.351974 / 0.379013 / 0.103417 | 0.210493 / 0.120210 / 0.876833 |
| Sparse labels with drift | 0.352703 / 0.412883 / 0.234833 | 0.243423 / 0.241188 / 0.940833 |
| Imbalanced assignments with drift | 0.371025 / 0.442353 / 0.015750 | 0.219452 / 0.151061 / 0.767333 |
| Delayed verification with drift | 0.456481 / 0.528721 / 0.000000 | 0.250000 / 0.300500 / 1.000000 |

Abrupt recovery: full history **0/20**; recent 120 **16/20**, mean **281.25**
steps among recovered seeds; recent 300 **20/20**, mean **300** steps. Last-quarter
abrupt coverage was **0.000000 / 0.972333 / 0.952000**, respectively. Delayed
verification takes 150 steps, longer than the 120-step window: it has **zero**
usable labels, prior-only predictions, and **0/20** recovery. Its 100% coverage is
the broad prior, not useful adaptation or validated nonstationary uncertainty.

Sample-size sensitivity also ran 20 seeds at **240** decisions with fixed
120/300 windows and 50-step refits, then proportionate **29/72** windows and
12-step refits. At 240, a 300-step window equals full history. The fixed 120
abrupt Brier was **0.362787**, versus **0.401582** full history; shorter
proportionate windows gave **0.224872 / 0.253312**, versus **0.356845** full
history. Smaller cells increase prior influence and noise; calibration and
recovery depend on window, cadence, delay and evidence count. These are designed
comparisons, not tuning on held-out outcomes. Full results/reproduction are in
`docs/DRIFT_INVESTIGATION.md` and sanitized `docs/experiments/drift_reference.json`.

**Statistical limits:** Coverage under drift is empirical descriptive coverage,
with no nominal Bayesian claim. Repeated forecasts/cells/blocks are dependent;
independent simulation seeds define replication. ECE is a noisy bin-dependent
diagnostic. Verification missingness/delay are independent of outcomes here.
Real calibration, informative delays, confounding and correlated retries remain
unvalidated. Recent windows improve these drift scenarios but worsen stationary
scores; the experiments do not justify replacing the existing estimator.

### Actual checks and independent review

Existing macOS arm64 Python 3.12.14 / uv 0.12.24 / Ruff 0.16.10 environment;
repository-local tool/cache paths, no dependencies installed.

| Check | Actual result |
| --- | --- |
| Pre-change `uv run pytest` | **164 passed in 4.98s**. |
| Assessment agent relevant tests | **64 passed**; owned lint/format passed. |
| Drift agent recent/drift/simulation/stress tests | **60 passed in 4.39s**; owned lint/format passed. |
| Coordinator final `uv run pytest` | **232 passed in 8.53s**. |
| Coordinator `uv run ruff check .` | `All checks passed!` |
| Coordinator `uv run ruff format --check .` | **61 files already formatted**. |
| Installed CLI resolve/drift help | Exit 0; documented options present. |
| Independent full suite | **232 passed in 7.90s**; lint/format and whitespace passed. |
| Independent statistical verification | Reproduced original 20-seed stress table; checked final 20-seed aggregates against per-seed values; independently reproduced seeds 0/1 for all seven 1,000-decision scenarios. |

Regression tests include historical reconstruction, equal-time chains, corrupted
graphs, conflicting identities/proofs, delayed evidence, future revisions/events/
associations, attribution availability, exact prior attribution after later
declarations, group overrides, unknown/censoring, duplicate learning, concurrent
revision insertion, separate historical train/score states, window boundaries,
late old labels, truth isolation and chronological prediction freezing.
Independent review found no remaining blocking code or statistical issue. No
new real capture was required or attempted; these checks exercise ledger
reconstruction and explicitly synthetic evaluation. The system remains
observational and predictive. No routing, switching, embeddings, fine-tuning,
TUI, cloud sync, Desktop capture or Governor was implemented. No commit, push,
merge, publication or global hook installation was performed. Stop here.

## Coding-task verification and execution-state analysis — 2026-10-10

The coordinator read the plan, repository instructions, status and existing
contracts before implementing the requested two workstreams. Two implementation
subagents used separate ownership: verification modules/JUnit tests and fixtures,
versus execution-analysis modules/tests and controlled examples. The coordinator
owns CLI integration, the observation determinate-evidence guard, CLI integration
tests, README and status. A third agent completed independent read-only review.
Domain contracts, storage/migrations, dependencies, lockfile and master plan are
unchanged. One pre-existing Python code block in the drift documentation received
only the formatting required by the installed Ruff checker.

### Coding verification

- Added bounded, read-only pytest/JUnit XML parsing with per-test identities and
  pass/failure/error/skipped status, separate counts, report hash/reference,
  parser/verifier versions and provenance. Failure messages, stack traces,
  commands and captured outputs are omitted from evidence metadata.
- Acceptance predeclares required test identities. An external binding receipt
  declares task/run, exact acceptance specification, tested artifact SHA-256,
  report SHA-256, generation time, completion and process exit. Association,
  artifact bytes, report digest and result/count consistency are rechecked before
  assessment and observation derivation. The existing file verifier is preserved.
- Missing/malformed/unsupported/contradictory reports, missing required tests,
  skipped tests, unknown completion or unsuitable process exit remain
  indeterminate. Finished execution alone remains unknown. Determinate evidence
  can produce a separately appended verified assessment; indeterminate evidence
  cannot become an eligible binary learning label, including imported claims.
- Added `task create --required-test` and `verify junit ... --artifact ...
  --binding-file ...`. No test process, command or agent is launched by these
  APIs/commands. Sanitized pytest-style fixtures cover passes, failures, errors,
  skips and partial/inconsistent reports. See `docs/JUNIT_VERIFICATION.md`.

### Execution analysis

- Added a pure read-only extractor returning multiple explicit checkpoint
  projections from existing Codex capture events. Both observation and ingestion
  times must be available. Counts, tool lifecycle/status/exit observations,
  per-field token coverage and source evidence IDs remain separate from versioned
  heuristic states. Unsupported observations and unavailable data stay explicit.
- Distinct failed items can establish repeated failures of a tool category or
  named MCP tool. Commands/arguments are redacted; identical-operation retries,
  root causes, loops and stalls cannot be established from these observations.
  Completion/zero exit do not imply tests passed or task success. Unknown native
  duration, cost and verified task success remain null.
- Explicitly scoped run mode accepts validated JUnit evidence with declared
  association/artifact availability and optional evidence availability receipts.
  It compares test status/count changes only for unambiguous report ordering;
  different test sets or incomplete reports cannot establish aggregate progress.
  The current ledger binds reports to one final artifact and observes verification
  after run end. This compares repeated reports of that snapshot; it does not
  reconstruct test progression across intermediate coding edits.
- Added `session analyze ... --checkpoint ...` with repeatable checkpoints for
  event-only inspection. Python run/evidence mode requires explicit receipts.
  Tests and controlled examples cover missingness, replay, future visibility,
  malformed/unsupported events, repeated failures, report binding and changes.
  See `docs/EXECUTION_ANALYSIS.md`.

**Limits:** XML support is a bounded documented JUnit dialect, not all vendor
extensions. Report bindings and receipt timestamps are trusted operator
declarations, not cryptographic attestation of execution. Snapshot hashing covers
one regular file, not repository dependencies/environment. Verification has no
ingestion timestamp in the existing ledger; an explicit analyzer receipt is
preferable, otherwise trusted `observed_at` availability is disclosed. Metadata-only
CLI captures do not contain structured test results. Desktop capture remains
unsupported. These changes do not establish coding-agent performance calibration.

### Checks and independent review

Existing macOS arm64 Python 3.12.14 / uv 0.12.24 / Ruff 0.16.10 environment,
repository-local tool/cache paths; no new dependencies were installed.

| Check | Actual result |
| --- | --- |
| Baseline `uv run pytest` | **232 passed in 9.41s**. |
| A final relevant tests | **103 passed in 2.31s**; owned lint and formatting passed. |
| B final owned unit/integration tests | **38 passed in 0.19s**; owned lint and formatting passed. |
| Coordinator CLI integration tests | **5 passed in 0.62s**. |
| Coordinator full `uv run pytest --junitxml=<ignored path>` | **346 passed in 10.04s**. |
| Coordinator `uv run ruff check .` | `All checks passed!` |
| Coordinator `uv run ruff format --check .` | **75 files already formatted**. |
| Independent full `uv run pytest` | **346 passed in 9.85s**. |
| Independent Ruff lint/format and `git diff --check` | Passed; **75 files already formatted**. |
| Fresh selected pytest report | **1 passed in 0.13s**; actual XML parsed, bound to an unchanged tested module, persisted and assessed as pass/success/verified. |

The full generated pytest XML was **10,537,007 bytes**, exceeding the **10,485,760
byte** parser limit because a security-test parameter embeds a large byte fixture
in its case name. Parsing returned `report_too_large`, without passing evidence.
A fresh bounded report for the predeclared `test_summary_rejects_forged_counts`
then validated the real pytest producer format through parsing, digest binding,
ledger persistence and assessment. These were actual operator-run project checks,
not a coding-agent execution or coding-utility claim. The XML/receipts/validation
ledger remain under ignored `.model-learner/`; no learning observations were made.

Independent review prompted regression-tested fixes for raw private binding
values in CLI errors, acceptance targets unavailable at historical checkpoints,
optional completion-field omission, malformed XML hierarchy/case state, ambiguous
equal-time report comparisons, conflicting/incomplete projections, and dual
acceptance verifier declarations. Wrong task/run/spec/artifact/report associations,
missing/skipped/partial results, delayed receipts and replay are covered. The
reviewer found **no remaining blocking issue** in the requested scope after the
final fixes and complete checks.

No routing, automatic switching, Governor, neural network, CPU fine-tuning, TUI,
agent control, unrestricted command execution, migration or next milestone was
implemented. No commit, push, merge, publication or global hook installation was
performed. Stop after these two workstreams.

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
  The requested increment now adds a narrow read-only file digest verifier and
  evidence-linked real task-observation builder plus bound JUnit report verification.
  Arbitrary test command execution and whole-repository artifact verification remain
  unsupported.
- JSONL imports enforce record schemas and relationships but are intentionally
  limited to primary records; task/session links are managed through the explicit
  attach commands rather than exported as a standalone record stream. The new
  run/session links likewise require explicit reconstruction on ledger transfer.
- SQLite is appropriate for the local-first, single-machine milestone but does
  not make multiple concurrent writers parallel; short transactions and a busy
  timeout reduce contention only.
- Decision/policy records, automatic project discovery, intervention-state learning,
  and cache-cost attribution remain unimplemented. The new learner estimates a
  selected binary acceptance target; it does not claim full expected utility,
  causal model superiority, or effects of interventions/budgets.
- Simulator outcomes are independent; missingness is completely at random.
  Correlated retries, outcome-dependent missingness, and selection confounding
  are not modeled. Real CLI fitting now resolves conflicting assessment histories
  at the requested cutoff; pure estimator callers must pass resolved rows.
  Simulation calibration does not establish real calibration.
- The initial numerical interval implementation supports shapes at least 0.5,
  posterior shape sum at most 100,000, and interval mass in [0.5, 0.999]. The
  default Beta(1,1) permits at most 99,998 verified trials per cell. Unsupported
  inputs fail explicitly; larger-scale numerical methods are deferred.
- Receipt-time capture is affected by upstream buffering and is not execution
  duration. The native CLI stream lacks complete event IDs; independently
  recapturing a stream is not globally deduplicated. Replay requires retaining
  the same capture identity and machine ID. Metadata/raw-retention policy and
  emitter-version enrichment cannot rewrite already persisted events.

## Next recommended increment (not started)

- The requested coding-verification and execution-analysis workstreams are
  delivered, independently reviewed, and checked. No next milestone is authorized.
- Intermediate artifact snapshots and complete declaration/evidence ingestion
  receipts would require separately scoped contracts. No new schema is introduced
  here; no subsequent milestone has started.
- Complete receipt-time reconstruction beyond trusted declared timestamps would
  require a separately scoped declaration/ingestion availability contract. No
  schema change has been made for that future work.
- Further statistical work could examine informative verification delays,
  correlated retries and selection confounding. The recent-window experiment
  does not justify replacing full history as the default estimator.
- Desktop capture requires a separately scoped, sanitized public-transport spike.
  A suitable passive connection to this running Desktop instance is unvalidated.
- No recommendation, routing, model switching, fine-tuning, TUI, cloud sync,
  runtime intervention control, or AI Governor was implemented. No commit, push,
  merge, publication, or global hook installation was made. Stop at the requested
  workstreams; await user direction.
