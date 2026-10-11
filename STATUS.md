# Model Learner status

Current work: first longitudinal task-state increment implemented and evaluated.
Multi-checkpoint projections distinguish observed evidence, deterministic changes,
explicit author hypotheses and unknowns. Seven synthetic trajectories exercise
the implementation; no real longitudinal predictive improvement is established.
The earlier 40-query human-review batch still has no genuine human labels or
accepted reviews. Real coding-agent benchmark execution remains disabled.
Last user-confirmed work: audit execution evidence, implement longitudinal state,
construct and evaluate a small inspectable dataset with existing CPU representations,
and propose minimal privacy-preserving real-data requirements. This requested
increment is complete; the proposed data pilot and next milestone are not started.
Updated: 2026-10-11

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

## Real coding-task and task-state predictive evaluation — 2026-10-10

The coordinator read the plan, repository instructions, status and existing
implementation before assigning two separate implementation subagents. A owns
the new `benchmark/` package, public task fixtures, benchmark tests and operator
documentation. B owns `learn/task_state.py`, predictive tests, controlled evidence
and methods documentation. The coordinator owns CLI integration, four CLI tests,
README and this status. A third, independent reviewer examined statistical
validity, data integrity, privacy and isolation. Existing domain contracts,
storage migrations, dependencies, lockfile and master plan are unchanged.

### Workstream A: operator-controlled real coding-task harness

- Two predefined public single-module tasks (`clamp`, `duration`) have versioned
  objectives and independent acceptance tests. Preparation predeclares exact
  configuration, task/acceptance, starting fixture and benchmark dataset before
  an agent runs. New disposable roots and all control/results/ledger files are
  outside the protected repository; resolved overlapping paths, symlinks and
  non-regular inputs are rejected.
- Agent execution is exclusively operator-controlled. No API/CLI command launches
  an agent, paid API or arbitrary test command. Operators must supply OS/container
  containment with no repository mount, protect control files, stop/reap the agent
  and its descendants, then separately run the provided acceptance controller.
  Source-tree fingerprints detect protected source changes; they do not replace
  or attest OS containment. Exact inventory exclusions and resource/process
  boundaries are documented in `docs/CODING_TASK_EVALUATION.md`.
- A stopped-run snapshot freezes one candidate module with digest and timing
  checks. The trusted acceptance controller evaluates each test through a separate
  Python worker, independently compares primitive values/errors and creates JUnit.
  Candidate code never imports into the controller. Existing bound JUnit
  verification and append-only assessments are reused; agent completion and
  self-report supply no acceptance label.
- Metadata-only Codex capture preserves source/version, events, receipt times,
  token coverage and native model/provider observations without prompts/outputs.
  Exact operator configuration attribution is retained, with emitted conflicts
  explicit. Unknown costs remain unknown. Missing/partial/malformed/skipped
  evidence, missing telemetry and incomplete executions remain visible; incomplete
  or unverifiable outcomes are unknown. No learning observation is manufactured.
- Public coding tasks always use `source_kind=benchmark`. Dataset IDs end in
  `:real` or `:fixture` to separate real agent runs from controlled fixture checks.
  Finalization validates in a private staging ledger and can retry rejected
  evidence without leaving a partial canonical run. A lock prevents parallel
  finalizers; final publication is not multi-file crash-atomic.
- Added `benchmark tasks`, `prepare`, `show`, `snapshot`, `finalize`, `cleanup`.
  Fixture acceptance covers named tests only. No real coding-agent performance
  run was attempted; the harness is code-complete and fixture-validated, with
  operator-controlled real integration pending.

### Workstream B: frozen task-state predictive evaluation

- Compares A (initial task group/exact configuration), B (A plus simple observed
  event/tool/turn/token metrics and missingness), C (B plus observed failure,
  repeated-failure and failure/unknown-fraction state), and C minus each of the
  three feature groups. Every variant uses identical chronological fit/score
  cutoffs, selected rows and fixed checkpoint horizon. This experiment does not
  replace the existing Beta-Bernoulli learner.
- Initial configuration/association and feature availability receipts are explicit.
  Non-simulated checkpoint facts are rebuilt from retained observed/ingested
  events with run/session/horizon bounds; mismatches and foreign-run leakage are
  rejected. Final JUnit/test state, terminal execution state, final resources and
  outcomes are excluded from predictors. Labels already known at checkpoint are
  excluded. Training-only category vocabulary/scaling, unavailable-future filtering
  before identity conflicts and disjoint task clusters prevent tested leakage.
- Fixed L2 logistic reference has predeclared settings. Reports include Brier,
  calibration bins, label/task counts, exclusion reasons, paired task-cluster
  bootstrap intervals and feature-group ablations. Sparse/single-class cohorts
  return `insufficient_data` and null scores. Intervals condition on the fitted
  model, omit training uncertainty and cross-task time dependence, and ablations
  are exploratory. Selected/missing labels can remain nonrepresentative.
- Added `sim state-fixture`, `learn state-eval`, `learn state-experiment`.
  Portable real/benchmark inputs require prior independently verified,
  historically resolved labels and prospective availability receipts; JSON
  validation is not evidence attestation. See `docs/TASK_STATE_EVALUATION.md`.

Actual controlled CLI experiment: seeds **0–4**, **400 independent tasks per seed**,
60% chronological training prefix, 30-second checkpoint, 300 paired bootstrap
replicates. Eligible training counts per seed were **222, 228, 231, 231, 229**;
scored counts were **153, 150, 151, 154, 153**. Equal-seed mean Brier scores:

| Controlled scenario | A | B | C | B minus C |
| --- | --- | --- | --- | --- |
| Deliberate state signal | 0.249377 | 0.249568 | 0.133440 | 0.116128 |
| Null state signal | 0.251462 | 0.251353 | 0.251842 | -0.000489 |

All five state-signal paired intervals were positive; every null-signal interval
included zero. The favorable fixture shows use of a deliberately generated signal;
the null fixture provides no evidence of improvement. This establishes neither
real-task predictive improvement nor real calibration. Per-seed calibration,
scores, counts, conditional intervals and ablations are retained in the public
`tests/fixtures/task_state/controlled_reference.json`; no private data is included.

### Actual checks and independent review

Existing macOS arm64 Python 3.12.14 / uv 0.12.24 / Ruff 0.16.10 environment;
repository-local tool/cache paths, no new dependencies or paid executions.

| Check | Actual result |
| --- | --- |
| Baseline `uv run pytest` | **346 passed in 14.06s**. |
| A owned unit/integration tests | **24 passed in 2.92s**; owned lint/format passed. |
| B final owned unit/integration tests | **23 passed in 8.22s**; owned lint/format passed. |
| Coordinator CLI integration tests | **4 passed in 0.51s**. |
| Coordinator final `uv run pytest` | **397 passed in 21.39s**. |
| Coordinator `uv run ruff check .` | `All checks passed!` |
| Coordinator `uv run ruff format --check .` | **91 files already formatted**. |
| Independent final full suite | **397 passed in 21.56s**; lint/format and whitespace passed. |
| Actual CLI controlled experiment | Five seeds, two scenarios, six variants per seed; results above. |
| Independent numerical reproduction | All **60 per-seed variant Brier scores** recomputed directly from saved predictions and regenerated labels; agreement within **1e-14**. |

Review prompted fixes for candidate monkeypatching of evaluator builtins,
retry-safe finalization after verifier rejection, captured/configuration conflicts,
origin-specific datasets, candidate/report timing, foreign-run checkpoint
events and consistent synthetic event/tool/turn/usage projections. Regression
tests cover these along with repository/control/candidate
tampering, symlink/path rejection, failure/unknown evidence, capture privacy,
future records/labels, delayed labels, task retries, preprocessing and empty data.
The reviewer found no remaining blocking issue in the requested scope.

No automatic routing, Governor, neural fine-tuning, cloud synchronization,
subsequent milestone, commit, push, merge, publication or global hook installation
was implemented. Stop after these two workstreams.

## Real benchmark safety and controlled pilot preparation — 2026-10-10

The coordinator read the requested design, repository instructions, status and
evaluation documents and inspected the implementation before changes. Two
implementation/research subagents had separate ownership: A owns the containment
audit, diagnostic probe, benchmark safety gates and safety documentation; B owns
the synthetic task catalog, pure pilot preregistration, acceptance fixtures and
operator experiment protocol. The coordinator owns CLI integration, README,
integration tests and this status. A separate read-only reviewer checked the
final implementation and protocol, including the final host-access demonstration.
The master plan, estimator, domain contracts, migrations and dependencies remain
unchanged. No paid coding-agent execution was launched.

### Safety findings and delivered boundary

- The existing harness enforced path separation, immutable snapshots, hashes and
  operator declarations, but no OS containment. Python `-I` and a separate worker
  interpreter do not prevent submitted code from reading or writing host files.
  Source fingerprints detect changes after the fact; they cannot prevent them.
- A controlled local candidate read and overwrote synthetic files outside its
  task directory while passing all six `clamp` acceptance checks. This actual
  harmless test demonstrates the current worker's host access; no private files
  or real Model Learner source were read or modified by that candidate.
- Added `benchmark isolation-probe`: a fixed, five-second macOS diagnostic creates
  disposable synthetic workspace/private/source canaries, checks permitted access
  and attempts forbidden reads/writes, symlink reads and child-process reads.
  It accepts no arbitrary program or private path. Bootstrap failure is reported
  as unavailable with unknown denial results; it cannot masquerade as successful
  confinement. Even a passing diagnostic has `real_execution_ready=false`.
- Real benchmark finalization now refuses collection before creating a lock,
  staging ledger or result: there is no supported, verified containment backend.
  Neither an isolation string, the existing confirmation flag nor a passing
  diagnostic enables it. Preparation, inspection, snapshots and disposal remain
  available; controlled public fixture finalization continues working. Manifest
  origin/dataset consistency checks prevent a single-field origin relabeling.
- The minimal proposed real boundary is a fresh, clean VM with no host shares or
  integration, no agent-readable secrets, a bounded external provider relay and
  a separate credential-free acceptance environment. Required resource limits,
  harmless canary validation and operator receipts are documented. This setup is
  a protocol requirement, not an implemented or validated agent runner.

### Pilot preparation

- Twelve public synthetic single-module Python tasks have versioned independent
  acceptance tests and controlled solution fixtures. Existing `clamp`/`duration`
  behavior is preserved; ten tasks add arithmetic, parsing, sequences and graphs.
  Named tests establish only their stated acceptance criterion.
- `benchmark pilot-plan` accepts two declared configuration files and a fixed
  seed, emits 24 paired runs with balanced arm order, an 8-family training /
  4-family held-out split, and hashes of matching initial source and task text.
  Each run requires a fresh disposable root. It launches no execution and writes
  no evidence or ledger rows. The primary checkpoint is 30 seconds; 10/60 seconds
  are diagnostic only; the agent wall limit is 120 seconds.
- The operator protocol predeclares configuration identities, initial-state
  checks, time/event availability, allowed A/B/C feature groups, independent
  verification, cost/latency provenance and missingness. Hidden acceptance data,
  final outcomes, final resource totals and future telemetry are excluded from
  checkpoint features. A/B/C share the same cohort and cutoffs.
- Current benchmark finalization creates associations and imports telemetry after
  execution. The real observation builder cannot export benchmark observations,
  and each fixture has a separate exact acceptance target. Prospective checkpoint
  export and pooled suite evaluation therefore remain blocked; receipts must not
  be backdated and targets must not be fabricated. The existing predictive floors
  remain 30 training labels, 20 scored labels, five task clusters per partition,
  and both training classes. This 24-run pilot must report `insufficient_data`;
  it cannot establish real predictive improvement.

### Actual checks and independent review

Executed on macOS 26.6.2 arm64 with Python 3.12.14, uv 0.13.0 and Ruff 0.16.10.
The default external uv cache was unwritable; using
`UV_CACHE_DIR="$PWD/.uv-cache"` resolved that environment issue. No dependencies
were added or installed.

| Check | Actual result |
| --- | --- |
| Baseline coordinator `uv run pytest` | **397 passed in 20.69s**. |
| Baseline Ruff lint / format | Passed; **91 files** formatted. |
| A owned benchmark checks | **32 passed in 1.63s**; owned Ruff lint/format passed. |
| B owned pilot checks | **51 passed in 10.29s**; owned Ruff lint/format passed. |
| Coordinator diagnostic/pilot CLI tests | **5 passed** across readiness, paired preparation and private-diagnostic checks. |
| First expanded full suite | **460 passed, 1 failed in 29.23s**: an original CLI test assumed exactly two task IDs. The scoped catalog assertion was updated and its four-test file passed. |
| Final coordinator `uv run pytest` | **462 passed in 34.22s**. |
| Final coordinator `uv run ruff check .` | `All checks passed!` |
| Final coordinator `uv run ruff format --check .` | **102 files already formatted**. |
| Final `git diff --check` | Passed. |
| Independent full suite before final canary demonstration | **461 passed in 32.81s**; Ruff lint/format and whitespace passed. |
| Final synthetic host-access demonstration | Coordinator **1 passed in 0.40s**; independently **1 passed in 0.46s**. Outside synthetic read/write succeeded while all six acceptance checks passed. |
| Actual nested and elevated restrictive macOS canary probes | Both `unavailable`, `sandbox_bootstrap_unavailable`; no successful positive controls or demonstrated denial; outside canaries unchanged. |
| Elevated permissive macOS profile diagnostic | `/usr/bin/true` exited **0**; establishes profile application availability only. Fixed restrictive shell startup diagnostics exited **134** before output. |
| Benchmark CLI help | Passed; includes `isolation-probe` and `pilot-plan`. |

Independent review prompted clarification that +10/+60 are diagnostic horizons,
while +30 is primary. Final review found no remaining actionable defect in this
preparation scope; its final lint, **102-file** format and whitespace checks passed.
The actual restrictive containment profile is unvalidated, and the proposed
VM/relay/candidate transport was not executed. These are real-experiment blockers,
not passing isolation claims. Ready now: operator configuration preregistration,
disposable staging, all-task controlled acceptance rehearsal and recording
protocols in `docs/BENCHMARK_SAFETY.md` / `docs/REAL_EVALUATION_PILOT.md`.

The requested audit/probe attempts and pilot preparation are complete. No real
coding-agent execution, routing, Governor, fine-tuning, cloud synchronization,
web GUI, subsequent milestone, commit, push, merge or publication was performed.

## Offline isolation experiment and benchmark evidence pipeline — 2026-10-11

Read the requested design, repository instructions, status, safety and pilot
documents and inspected the current benchmark implementation. Two implementation
subagents had non-overlapping ownership: A owns `benchmark/offline.py`, its
unit/integration tests and `docs/OFFLINE_BENCHMARK_ISOLATION.md`; B owns
`benchmark/evidence.py`, its unit/integration tests and `docs/BENCHMARK_EVIDENCE.md`.
The coordinator owns CLI integration, pipeline CLI tests, README, updates to the
existing safety/pilot documentation and this status. A separate read-only reviewer
checked security, evidence integrity, statistical semantics and actual containment.
The master plan, domain contracts, migrations, estimator, dependencies and lockfile
remain unchanged. The existing real-execution gate remains unconditional.

### Actual isolated offline experiment

- Existing Docker Desktop **4.94.0 (241994)** / Engine **29.8.2** on macOS
  **26.6.2 arm64**, Linux **7.0.14-linuxkit**, cgroup v2 was available. No system
  software, image, global security setting or daemon was installed/started.
- The fixed probe requires an explicitly approved, locally cached immutable public
  `docker/welcome-to-docker` image. Only
  `sha256:c4d56c24da4f009ecf8352146b43497fe78953edb4c679b841732beb97e588b0`
  is supported in this experiment; absent/unapproved images fail closed without
  pulling. An unspecified image returns `unavailable/image_approval_required`.
- Each fresh container has **zero host mounts**, an unprivileged user, read-only
  root, all capabilities dropped, no-new-privileges, private process/cgroup
  boundary, IPC disabled and **network none**. Host home, credentials, repository,
  hidden tests and runtime sockets are never mounted. The controller uses an empty
  Docker client configuration and minimal environment; actual policy is inspected
  before starting. Only synthetic canaries are probed.
- Limits: **1 CPU, 128 MiB memory with no additional swap, 16 processes, 1 MiB
  task tmpfs, 15-second enclosing deadline, 64 KiB transport/log cap, 1 KiB
  artifact cap and 64 file descriptors**. CPU/memory values were read back from
  effective kernel cgroups, not load-stressed. Actual process creation and task
  storage overflow were refused. A second disposable boundary deliberately hit
  the watchdog with a sleeping descendant; whole-container removal was confirmed.
- Actual worker workspace positive controls passed. Outside synthetic
  repository/source/credential/hidden-test/runtime reads and writes, symlink,
  traversal and child-process reads were denied. Exact network-tool-mode loopback
  positive controls passed before external/host/metadata connections were denied.
  Host canaries were unchanged. No real credentials or source were read by workers.
- Coordinator and independent reviewer each observed
  **`validated/fixed_offline_probes_passed`, all 33 checks true**, zero host mounts,
  fixed-artifact hash
  `b91b66771b6ab7ce8f906c171c351e0f729ec21205db88ed835be3d56e47b048`, and policy
  fingerprint `2fb1b75be291c30610dc7b50e6ef92e1c9c8a17d473dc686fd5064fb68b73061`.
  The reviewer independently found no remaining probe containers. Ordinary
  enclosing-sandbox daemon access returned unavailable; scoped outer-sandbox
  approval permitted only this fixed harmless diagnostic, without broadening
  worker permissions. Every receipt retained **`real_execution_ready=false`**.
- Paused Docker `cp` could not see the task tmpfs and was rejected. Independent
  extraction instead uses a controller-requested stream from the pinned tar tool
  after the fixed worker has finished writing, followed by bounded in-memory
  regular-file validation, exact expected-byte comparison, pause and destruction.
  **Hostile artifact freeze-before-read is not validated.** This synthetic probe
  is not a general candidate runner, independent acceptance transport or paid
  agent execution backend. Cleanup has bounded additional control grace; an
  unavailable/hung daemon or unconfirmed destruction fails closed.

### Offline evidence handoff

- Added source-revalidated `benchmark-evidence/v1` export/import using the existing
  `Observation` contract. It preserves benchmark/task/run/attempt/assessment IDs,
  exact operator configuration and harness provenance, fixture family/version/hash,
  origin-specific datasets, acceptance target and artifact/report bindings.
- Retained native metadata-only events preserve IDs, adapter/emitter versions,
  original observation/ingestion times and safe redaction/missingness metadata.
  Raw transcripts, commands/outputs, candidate/report bodies, hidden case IDs and
  arbitrary native metadata are excluded. Arbitrary configuration metadata is
  rejected rather than hashed into a hidden-label channel or silently rewritten.
- Independent visible verification remains in the audit even for interrupted
  runs whose unknown assessment cites no evidence. Labels use only selected
  assessment-linked independent verification; agent self-report never labels a
  run. Unknown/censored/incomplete outcomes, attribution/configuration conflicts
  and nullable resources remain explicit. Blank or missing required configuration
  dimensions prevent eligibility. No unknown price becomes zero.
- Historical export resolves the visible assessment head and excludes future
  labels, verification, event ingestion and unavailable associations. Export/import
  availability stays actual; no timestamps or scope declarations are backdated.
  Requested checkpoints retain missing-session/unavailable-input reasons. **All
  checkpoint projections remain `eligible_for_task_state=false`** because this
  finalization path has no prospective initial/configuration/scope collector.
- Import requires the retained trusted benchmark root, rederives the whole bundle,
  checks current artifact/report bytes and uses an atomic replay-check/insertion
  transaction. Reimport returns one unchanged observation. An exclusive optional
  output file refuses overwriting prior evidence. No export/import executes code.
- Eligible `:fixture` rows support **algorithm rehearsal only**, not model utility
  measurement. An actual handwritten public clamp candidate passed the existing
  independent acceptance/finalization workflow, then exported/imported twice as
  one eligible fixture observation. The unknown CLI fixture stayed ineligible.
  Synthetic receipt fixtures separately exercised exact-target learner consumption,
  historical revisions, leakage rejection and interrupted verification retention.
- Exact targets and family dependence remain explicit; no suite target, pooling,
  changed estimator or lowered sufficiency floor was introduced. Multiple benchmark
  revisions in one learner input still fail closed as conflicting trials; select
  one immutable revision per evaluation snapshot. This does not add benchmark
  history resolution to the real-only CLI or establish predictive improvement.

### Review and checks

Commands use the existing `.tools/bin/uv` and repository-local `UV_CACHE_DIR`.
Independent review prompted fixes for arbitrary image selection, network-mode
false positives, actual PID/watchdog tests, bounded regular-file checks, missing
checkpoint coverage, interrupted verification retention, configuration metadata
and blank identity dimensions. No remaining actionable issue was found in the
requested synthetic experiment/evidence scope; the real blockers remain below.

| Check | Actual result |
| --- | --- |
| Baseline coordinator `uv run pytest` | **462 passed in 28.63s**. |
| Baseline Ruff lint/format | Passed; **102 files** formatted. |
| A unit/ordinary integration | **16 passed, 1 opt-in runtime test skipped**. |
| A actual opt-in Docker integration | **2 passed in 1.85s** with scoped approval. |
| B final owned tests | **19 passed in 0.67s**; owned lint/format passed. |
| Coordinator pipeline CLI integration | **6 passed in 0.70s**, including actual public fixture acceptance and refusal to overwrite export. |
| Intermediate full regression before A integration file landed | **502 passed in 29.50s**. |
| Coordinator actual Docker CLI | Exit **0**; all **33 checks true**, real readiness **false**. |
| Independent actual Docker replay and cleanup inventory | All **33 checks true**; no remaining probe containers. |
| Final coordinator `uv run pytest` | **503 passed, 1 opt-in test skipped in 30.70s**. The skipped actual test was separately executed successfully by A; coordinator/reviewer also ran the actual probe. |
| Final coordinator `uv run ruff check .` | `All checks passed!` |
| Final coordinator `uv run ruff format --check .` | **111 files already formatted**. |
| Final coordinator `git diff --check` | Passed. |
| Independent final focused evidence/offline/CLI checks | **26 passed, 1 opt-in test skipped in 1.34s**; lint/format/whitespace passed. |

No real or paid agents, production orchestration, routing, Governor, fine-tuning,
cloud synchronization, next milestone, commit, push, merge, publication, global
hook or system security change was performed. Stop after the requested offline
experiment and evidence pipeline.

## Secure execution boundary and CPU task representation — 2026-10-11

Read AGENTS.md, the master plan, status, and current benchmark/execution-state
modules. Two subagents had separate implementation ownership: A owns new
`benchmark/secure.py`, its security tests and `docs/SECURE_BENCHMARK_BOUNDARY.md`;
B owns new `representation/`, its evaluation tests/public fixtures and
`docs/CPU_TASK_REPRESENTATION.md`. The coordinator owns representation CLI commands,
CLI tests, README and this status. Each subagent independently reviews the other's
work read-only. The existing offline isolation and evidence-export workstreams
remain complete. Domain contracts, migrations, probabilistic learner, master plan,
dependencies and lockfile are unchanged.

### A — controller components delivered; real execution blocked

- Added a bounded, bytes-only single-file archive parser and immutable candidate
  object. It accepts only regular `solution.py` bytes, rejects traversal, links,
  device/FIFO/sparse/metadata entries, excess size, duplicate entries and hidden
  trailing data, and never imports or executes candidate source.
- Exclusive freezing pins directory descriptors, refuses symlink parents and
  existing outputs, and validation rechecks bounded current regular-file bytes,
  stable identity and metadata. This is controller-side freezing after transport;
  it does **not** prove hostile writers stopped before transport. Operator-owned
  control directories must remain inaccessible to workers.
- Public fixture envelopes and primitive function requests contain only public
  task inputs. Expected answers, case identities, control/report paths and signing
  material remain controller-side. Responses have size/type/field/request-ID
  checks. Wrong numeric answers fail comparison; missing/malformed evidence emits
  no validation receipt.
- Per-run ephemeral HMAC receipts bind benchmark/task/run, exact fixture and
  configuration snapshot, nonce, candidate/transport hashes and the controller's
  complete ordered comparison transcript. Tamper, foreign controller/run, wrong
  purpose, response replay, duplicate import and repeat finalization are rejected.
  Receipt authentication is in-process only; keys are not persisted or exported.
- Every receipt is `offline_synthetic_controller_only` with
  `real_execution_ready=false`, `runtime_freeze_verified=false` or
  `candidate_execution_attested=false`. They cannot create verified observations
  or satisfy the unchanged unconditional real-finalization gate.
- Actual integration launches only fixed harmless Python workers with an empty
  environment. Public synthetic credential environment canaries are absent; six
  clamp comparisons pass against an opaque non-Python candidate marker, and
  replay to another request is refused. Hostile tests supply only bytes/files;
  no hostile candidate code is executed on the host.

No acceptable exact-agent credential relay or hostile runtime artifact transport
was established. A separate credential-free candidate execution boundary also
remains unimplemented. The fixed Docker probe cannot attest these mechanisms.
One safe real coding-agent benchmark execution therefore remains **blocked**;
no real/paid agent was launched and containment requirements were preserved.

### B — optional local CPU prototype

- New independent representation inputs carry a public/sanitized initial task
  description, SHA-256, availability time, task identity and dependence family.
  The prototype collects no raw transcripts, writes no ledger rows and changes
  neither the probabilistic learner nor agent behavior.
- A uses existing task-group/exact-configuration features; B adds deterministic
  checkpoint metrics, failures, repeated failures and unknown/missing fractions;
  C adds an optional frozen pretrained CPU representation. Final tests, terminal
  states, final resources, outcomes and arbitrary metadata never enter features.
- Frozen chronological cohorts retain exact source/dataset/target/budget selection,
  visible labels and input availability. Task, family and exact description reuse
  cannot cross training/scoring partitions. Non-simulated checkpoint facts require
  retained bounded events; future records, unknown labels and insufficient cohorts
  remain explicit exclusions. Training-only feature vocabulary/scaling and a fixed
  logistic reference use no held-out fitting or fine-tuning.
- A/B/C share scored units. Reports include Brier scores, calibration bins,
  family-cluster paired bootstrap intervals, task/family counts, exclusions,
  reproducibility bindings and component timing/memory measurements. Floors stay
  30 training labels, 20 scored labels, five families per partition and both
  training classes. These floors do not guarantee precision.
- Added `sim representation-fixture` and `learn representation-eval`. Semantic
  loading requires an explicit existing three-file MiniLM safetensors bundle,
  expected bundle hash and full revision identity. Loading uses a bounded private
  snapshot, explicit architecture/tokenizer and CPU inference only; no download,
  remote inference, automatic model selection or software installation occurs.
  Unavailable semantic loading preserves A/B results and null C metrics.
- The current repository environment lacks `torch`, `transformers` and
  `safetensors`, and no local model was supplied. The optional pretrained adapter
  is **integration-pending**. C scores, actual model load/inference overhead and
  actual semantic memory remain unavailable; no semantic improvement is claimed.

Coordinator controlled evaluation: seeds 0–4, 150 simulated tasks per seed,
60% chronological training prefix, fixed +30-second checkpoint, 300 paired family
bootstrap draws. Training labels: **80, 89, 88, 87, 86**; scored labels:
**58, 58, 58, 57, 57**. Every partition has six families. Equal-seed means:

| Controlled scenario | A Brier | B Brier | A minus B | C |
| --- | --- | --- | --- | --- |
| Deliberate state signal | 0.256719 | 0.122489 | 0.134229 | unavailable |
| Null state signal | 0.254266 | 0.258117 | -0.003851 | unavailable |

All five state-signal conditional intervals were positive. In the null scenario,
two intervals excluded zero in opposite directions; six clusters provide limited
uncertainty evidence. These constructed held-out comparisons are algorithm
rehearsal only. They establish neither real predictive improvement nor benefit
from semantic embeddings.

Actual installed CLI rehearsal in a fresh process used seed 1 / 150 public
synthetic tasks: 89 training and 58 scored labels, A/B evaluated and C
`semantic_unavailable`. A feature extraction averaged **0.286 microseconds** and
reference prediction **1.36 microseconds** per checkpoint; B measured
**2.52 / 2.57 microseconds**, respectively. Reference fits took **0.0266 / 0.0682
seconds**. The feature Python-object census was **64,156 / 425,482 bytes** for
147 rows; this excludes other objects and runtime memory. Whole-process lifetime
peak RSS after the run was **52,822,016 bytes**, not incremental component RAM.
These are one wall-clock sample, excluding input parsing/cohort validation, and
are not stable performance guarantees. The semantic FP32 parameter estimate is
**90,800,000 bytes** (rounded 22.7M parameters), excluding runtime, activations
and feature objects; actual semantic memory/inference measurements remain null.

### Checks and independent review

Existing Python 3.12.14 / repository-local uv environment; commands use
`UV_CACHE_DIR="$PWD/.uv-cache"` and `--no-sync` to prevent dependency installation.
No global configuration, software installation, paid execution or subsequent
milestone was performed.

| Check | Actual result |
| --- | --- |
| Pre-change `uv run --no-sync pytest` | **503 passed, 1 opt-in runtime test skipped in 34.16s**. |
| Pre-change Ruff lint/format | Passed; **111 files already formatted**. |
| A final owned unit/integration tests | **40 passed in 0.42s**; owned lint/format passed. |
| Coordinator representation CLI tests | **4 passed in 0.67s**; includes unavailable model and sanitized invalid input. |
| B final owned unit/integration tests | **19 passed in 3.15s**; owned lint/format passed. |
| First combined coordinator suite | **564 passed, 1 opt-in runtime test skipped in 32.89s**. |
| Combined Ruff lint/format and whitespace | Passed; **123 files already formatted**. |
| Actual installed representation CLI rehearsal | Exit **0**; 150 public synthetic inputs, A/B evaluated, C unavailable; measured overhead above. |
| Independent A security review/checks by B | **40 passed in 0.36s**; no actionable defect in synthetic scope; real credential/runtime blockers confirmed. |
| Final combined coordinator `uv run --no-sync pytest` | **566 passed, 1 opt-in runtime test skipped in 34.05s**. |
| Final coordinator Ruff lint/format and whitespace | Passed; **125 files already formatted**; `git diff --check` passed. |
| Independent final B evaluation and parent CLI checks by A | **23 passed in 3.74s**; owned lint/format and whitespace passed. |
| Independent numerical reproduction by A | All **10 stored reports** matched exactly for cohort digests, counts, metrics/calibration/intervals, comparisons and methods; C remained unavailable. |

Independent security and evaluation reviews found no remaining actionable defect
within the delivered offline scope. Review prompted fixes for bounded hostile
integer/error responses, archive metadata prechecks, frozen-file identity/size
checks, exact configuration snapshot identity, task versus family denominators,
incomplete pretrained weight rejection and native future-ingestion/fact tests.
Actual runtime/credential mechanisms and pretrained model compatibility remain
unvalidated blockers, not passing claims. The pre-existing `.DS_Store` modification
was preserved. No AI Governor, automatic switching, fine-tuning, software install,
paid agent, commit, push, merge or publication was performed. Stop after these
two workstreams; await user direction.

## Pretrained CPU semantic C evaluation — 2026-10-11

The user confirmed no existing model was configured, accepted the previous A/B
work, requested completion of C and approved `minishlab/potion-base-8M` weights.
After compatibility inspection, the user separately approved installing pinned
CPU dependencies in the repository's optional environment. Read the repository
instructions, relevant learning/evaluation plan, prior status and C implementation.
One implementation subagent owns only `representation/potion.py` and its guard/
actual-model tests; a separate read-only subagent independently reviews model
provenance, CPU/privacy, evaluation and reproduction. The coordinator owns narrow
semantic dimension/metadata support, explicit CLI selection, optional dependencies,
the fixed experiment reproducer, integration tests, reports and documentation.

### Identity, compatibility and delivered behavior

- The original C loader is a strict 384-dimensional MiniLM BERT adapter. Potion is
  a 256-dimensional pretrained Model2Vec static embedding model, so it is not a
  direct drop-in. A separate narrow adapter retains the text-to-vector interface;
  the evaluator now validates either supported dimension. A/B input features,
  cohorts, numerical fitting, cutoffs, bootstrap policy and old reference artifact
  are unchanged. The explicitly preferred lightweight model was retained.
- Confirmed public identity, MIT license, 256-dimensional configuration and file
  sizes **before downloading**. Model revision is
  **`bf8b056651a2c21b8d2565580b8569da283cab23`**. Three files total **30,920,628 bytes**;
  the F32 table is **29,528 × 256**, **30,236,672 bytes** / 7,559,168 parameters.
  Weights match published upstream SHA-256
  `f65d0f325faadc1e121c319e2faa41170d3fa07d8c89abd48ca5358d9a223de2`.
  Approved bundle SHA-256 is
  `930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2`.
- Downloaded public unauthenticated revision-pinned `config.json`,
  `model.safetensors` and `tokenizer.json`, checking exact upstream identities and
  size. Weights/download receipts are in ignored `.model-learner/models/`; Git
  exclusion was checked. No private description/transcript was downloaded/uploaded.
- Added optional `semantic` dependency **`model2vec==0.9.0`**, with all dependencies
  locked in `uv.lock`. Actual core CPU packages: NumPy **2.5.4**, safetensors
  **0.8.0**, tokenizers **0.23.3**. Installation changed only the approved local
  project environment; no global configuration or software was changed.
- The local loader copies bounded no-follow regular files into a private snapshot
  and checks the supplied bundle hash plus fixed approved file identities before
  constructing the audited static model from NumPy arrays/local tokenizer. No Hub
  loading helper, model-supplied code, pickle, GPU or remote inference is used.
  Weights are read-only; incomplete/incompatible matrices and tokenizer IDs fail.
  Missing/bad explicit Potion loads remain unavailable and cannot fall back to
  another model; reports identify the requested Potion backend correctly.
- Inference uses only bounded public/sanitized descriptions, max 4096 characters,
  256 tokens, batch size one, no multiprocessing, mean token pooling and L2
  normalization. The runtime first truncates characters to
  `256 * median_token_length`, then tokens. Unknown tokens are removed; no-known-
  token text produces a zero vector. No fine-tuning, switching or private collection.
- `learn representation-eval --model-id minishlab/potion-base-8M` requires explicit
  local model path, full approved revision and bundle hash. The previous optional
  MiniLM default remains intact. `representation.potion_experiment` reproduces
  only the same fixed ten public simulated cohorts in fresh subprocesses, refuses
  output overwrite and fails if original A/B metrics/cohort hashes change.

### Actual held-out predictive evidence

New `tests/fixtures/representation/potion_reference.json` retains all ten
pretrained reports (state/null scenarios × seeds 0–4), without description text,
model weights or per-run predictions. Data/settings match the prior reference:
150 simulated tasks per seed, 60% chronological fit, **2026-01-01 04:30 / 07:30
UTC** cutoffs, +30-second checkpoint, 300 paired family-bootstrap draws. Training
counts remain **80, 89, 88, 87, 86**; scored counts **58, 58, 58, 57, 57**; six
training/six held-out families. All A/B scores, intervals, calibration, paired
comparisons, counts and cohort hashes match the original artifact exactly.

| Scenario | Mean A Brier | Mean B Brier | Mean C Brier | Mean B minus C |
| --- | --- | --- | --- | --- |
| Deliberate state signal | 0.256719 | 0.122489 | 0.122641 | -0.000152 |
| Null state signal | 0.254266 | 0.258117 | 0.258446 | -0.000329 |

Positive B minus C means C improves. All five state-signal paired 95% intervals
include zero. Null seed 4 has a positive interval **[0.000056, 0.000736]**;
the other four include zero. Full per-seed C Brier intervals, paired differences
and calibration bins are in the artifact and methods document. There is
**no consistent semantic improvement**. Intervals condition on fixed fits with
only six scored families and no multiplicity correction; seed means are
descriptive, not pooled confidence intervals.

The existing invented descriptions are independent of outcomes and struggling
state, so these fixtures contain no designed semantic outcome signal. This is
real pretrained **CPU inference on synthetic evaluation data**, not evidence of
real-world task understanding or model utility. A null/negative result on these
fixtures cannot show that embeddings are useless on real tasks.

### Actual loading, inference and memory measurements

Ten fresh Python 3.12.14/macOS arm64 workers use a minimal environment, requested
single-thread CPU limits, disabled tokenizer parallelism/multiprocessing and
socket connection guards before loading/inference. All reported **zero network
connection attempts**. OS caches were not cleared. Serial latency measures five
passes over the same scored public descriptions after evaluation warmup.

| Component | Actual result |
| --- | --- |
| Fresh-process model loading, including imports/snapshot/hash checks/construction | **0.167–0.264 s**, mean **0.192 s**. |
| First-description warmup | Mean **3.83 ms**, separate from loading and steady inference. |
| Embedding throughput | Mean **52.97 microseconds/description** over selected rows. |
| Warm serial description latency | Worker medians **58.33–59.88 microseconds**, p95 **62.04–65.71 microseconds**; 285–290 samples per worker. |
| Fixed C reference prediction | Mean **25.83 microseconds/checkpoint**, separate from embedding. |
| Fixed C reference fitting | Mean **0.603 s**; not encoder fine-tuning or inference. |
| Actual F32 embedding-table memory | **30,236,672 bytes**; excludes tokenizer/runtime. |
| Whole fresh-process peak RSS | **139,575,296–140,345,344 bytes**, including load/features/fits and latency measurements. |

Embedding latency includes output conversion/validation but excludes C feature
dictionary assembly, B feature extraction, cohort parsing and reference prediction.
Peak RSS is a process lifetime high-water mark, not incremental model RAM. C
feature-object census averages **4,055,355 bytes**; object census and timing are
descriptive measurements, not guaranteed worst-case resource requirements. These
short public descriptions do not establish long-input latency. All actual phase
measurements/runtime/model identities are retained; no semantic measurement is null.

### Checks and independent review

Use the approved optional environment (`uv sync --locked --extra semantic`).
Actual-model tests opt in with `MODEL_LEARNER_TEST_POTION_PATH` pointing to the
approved ignored bundle; tests never discover/download weights automatically.
Checks use repository-local cache/tools and `uv run --no-sync` to preserve it.

| Check | Actual result |
| --- | --- |
| Adapter owned actual/protocol checks | **31 passed in 0.47s**, including approved pretrained inference with sockets blocked. |
| Coordinator focused representation/Potion/CLI checks | **57 passed in 5.28s**. |
| Coordinator full suite with actual-model opt-in | **600 passed, 1 skipped in 37.06s**. Sole skip is unchanged offline Docker runtime opt-in. |
| Coordinator Ruff lint/format and whitespace | Passed; **129 files already formatted**; `git diff --check` passed. |
| Independent full suite with actual-model opt-in | **600 passed, 1 skipped in 37.65s**; lint/format/whitespace passed. |
| Independent canonical numerical reproduction | All **ten reports** match exactly for complete A/B/C score/calibration/interval results, paired comparisons, cohort hashes, counts, exclusions and methods. |
| Independent privacy/leakage/replay checks | Actual CPU load/encode succeeds with sockets disabled; exact embedding replay; input reversal and held-out label changes preserve predictions. |
| Protected baseline/boundary diff check | Original A/B reference, feature inputs, benchmark and execution modules unchanged. |
| Actual installed Potion CLI rehearsal | Exit **0**; seed 1 has 89 training / 58 scored rows, all A/B/C evaluated and C Brier **0.057289**. |

Review found and prompted fixes for unavailable-model identity/estimates and a
protocol-test compatibility regression, plus a formatting issue; focused/full
checks pass after repair. Guard tests cover bad revision/hash/file identity,
unsafe files/paths, incomplete matrices and bounded text/output. Independent
final documentation review confirms measured results and limitations, with no
remaining blocking finding. Historical dependency wording and repository-local
tool instructions were clarified. The pre-existing `.DS_Store` modification was
preserved.

No real coding agent, cloud/paid inference, Governor, automatic switching,
fine-tuning, benchmark boundary change, commit, push, merge or publication was
performed. Stop after C; no additional milestone is authorized.

## Semantic task understanding and relevance evaluation — 2026-10-11

Read the user request, AGENTS.md, current STATUS, relevant observation/identity,
privacy and evaluation plan sections, existing CPU encoder, representation and
task-state evaluators, documentation and tests before implementation. The main
agent owns architecture, CLI integration, README and this status. Non-overlapping
subagents own retrieval plus unit tests and dataset/evaluation/reproducer plus
their tests/docs. A third read-only reviewer independently checks labels,
leakage, false associations, privacy, performance and numerical reproduction.
The pre-existing `.DS_Store`, `pyproject.toml` and `uv.lock` changes are preserved.
No dependency, domain schema, master plan, learner or benchmark boundary changes
were needed for this increment.

### Delivered subset and limits

- `understanding/retrieval.py`: bounded in-memory description retrieval with
  deterministic token Jaccard, candidate-only TF-IDF and optional frozen Potion
  cosine. Explicit public/sanitized/declared input provenance, max 4096 characters
  per description and 10,000 candidate tasks; no transcript discovery or retention.
  Scores are inferred relatedness, never calibrated continuation/success
  probabilities. Zero/unknown representations remain unknown. Finite vectors,
  dimensions, deterministic ties and self exclusion are checked.
- `understanding/evaluation.py`, `experiment.py` and
  `tests/fixtures/understanding/`: authored relevance dataset, frozen SHA-256
  manifest, metrics and actual three-worker-per-backend reference measurements.
  Labels are technical judgments written by a separate evaluation agent before
  any encoder invocation, independently inspected by the reviewer; they are not
  derived from the encoder. They lack independent external human adjudication.
  Text is newly constructed and reviewable, with no third-party/private content
  or asserted external license. No outcome-success labels exist in this dataset.
- `model-learner task similar TASK_ID`: optional read-only shortlist command,
  TF-IDF default; `--backend text` or explicitly pinned local `--backend potion`.
  Returns distinct task IDs, similarity scores, explanation, provenance and
  exclusion/unknown counts without description text. Candidate creation
  declarations cannot be later than the query's declaration; this is not an
  attestation of historical ingestion availability. Model absence/bad pins return
  `semantic_unavailable` and no fallback suggestions. Other commands still work.
- Similarity never creates associations or changes task identities. Explicit
  task/session/run links remain authoritative. Shared sessions and equivalent
  descriptions do not establish continuation; integration tests retain distinct
  tasks with identical descriptions and a shared session. No continuation
  classifier is delivered or assigned classification metrics.
- This intentionally chooses the smallest reliably evaluable subset: related-task
  retrieval. Characteristic/ambiguity/dependency inference and evolving-scope or
  implementation-to-debugging detection remain unimplemented. Scope-diverged
  descriptions are hard retrieval negatives, not a longitudinal evolution test.
  No sanitized execution-summary collector or semantic utility features are added.

### Frozen relevance evidence

Dataset `authored-semantic-retrieval-v1`, frozen content SHA-256
`75a4208dea16b4aec6c6d3cfa59d5e29f67f2c028a70823f49cf56baf9b4000d`.
Development: four queries, two families/projects, twelve candidates. Locked test:
twelve queries, six families/projects, thirty-six candidates, two relevant tasks
per query. Family, project and query rewrite groups are disjoint between splits;
TF-IDF fits only the candidate corpus of the selected split. Query-to-historical
same-family matches are intended retrieval targets, not supervised training.
No thresholds or parameters are chosen from the locked test. Labels, family and
project annotations do not reach the retrieval index. Full known rankings use
fixed deterministic ties; unknown representations receive no retrieval credit.

| Locked-test method | Precision@1 | Precision@3 | Recall@3 | MRR | nDCG@3 |
| --- | --- | --- | --- | --- | --- |
| Token Jaccard | 0.250000 | 0.277778 | 0.416667 | 0.439316 | 0.352191 |
| TF-IDF | 0.250000 | 0.277778 | 0.416667 | 0.452649 | 0.358881 |
| Pinned Potion | 0.333333 | 0.416667 | 0.625000 | 0.574537 | 0.525548 |

Potion recovers fifteen of twenty-four relevant top-three slots versus ten for
either lexical baseline. Top-one relevant results improve only from three to
four of twelve; eight Potion first suggestions remain irrelevant. All six
original wording-trap queries choose their high-overlap wrong-objective distractor
first for every backend. Potion improves paraphrased duplicate-payment retrieval
(two relevant top-three results versus zero lexical), but confuses paraphrased
authentication concurrency with an unrelated payment regression test, and still
ranks changed-scope descriptions too highly. Scores require human review.

Two correlated rewrites per family and one repeated candidate structure make
this a small purposive six-family experiment. Means are descriptive; no population
confidence interval, significance claim, real-task accuracy or success-prediction
claim is warranted. The measured improvement supports only optional shortlist
exploration. It does not justify semantic decisions, automatic grouping or
feeding embeddings into the Bayesian estimator. Earlier synthetic outcome
prediction remains unchanged and has no consistent semantic gain.
The reviewer found two mixed-relevance text-baseline cutoff ties where frozen
task-ID ordering favors the positive label; TF-IDF/Potion have no such top-one or
top-three boundary ties. Potion's gain against TF-IDF is unaffected. A future
dataset should use opaque IDs. Potion's Recall@3 improves in four of six families
and worsens in the keyboard and query-plan families.

### Actual CPU measurements

Three fresh workers for each backend, Python 3.12.14/macOS arm64, requested
single-thread limits, tokenizer parallelism disabled, socket connections blocked
before loading. Every worker reports zero connection attempts. OS caches were
not cleared. Five warm serial passes measure twelve test queries against the
same thirty-six candidates; timings are descriptive, not large-ledger estimates.

| Component | Measured range across workers |
| --- | --- |
| Potion model loading, runtime imports/snapshot/hash/construction | 0.178–0.264 seconds |
| Potion warm single-description median encoding | 62.50–68.29 microseconds |
| Potion warm query median, including encode/score/sort | 0.4397–0.4636 milliseconds |
| Text warm query median | 0.0388–0.0436 milliseconds |
| TF-IDF warm query median | 0.0427–0.0435 milliseconds |
| Potion embedding table alone | 30,236,672 bytes |
| Whole Potion worker peak RSS | 132,202,496–132,235,264 bytes |
| Whole lexical worker peak RSS | 38,502,400–38,600,704 bytes |

Whole-process peak RSS is a lifetime high-water mark, not incremental model RAM.
Index construction/model loading are excluded from warm query time and reported
separately in the artifact. These short descriptions and tiny indexes do not
establish worst-case CPU/latency. Overhead buys a narrow top-three relevance gain,
but poor top-one precision and insufficient data favor keeping TF-IDF default.
Fine-tuning is not justified by this evidence; acquire independently human-reviewed
labels and a larger project/family-disjoint test first.

### Validation and next step

- Pre-change full suite: **598 passed, 3 skipped in 35.84s** (model/Docker opt-ins
  absent in this initial check).
- Retrieval owner's focused checks: **42 passed in 0.15s**, Ruff lint/format and
  whitespace passed.
- Coordinator final registered CLI focused tests with sockets blocked:
  **6 passed in 0.65s**, including malformed-ledger privacy diagnostics.
- Evaluation owner's focused actual-model checks: **22 passed in 0.38s**;
  owned Ruff lint/format passed.
- Independent reviewer exactly reproduced all three backends' development/test
  stored top-three similarity scores, relevant-target ranks, per-query/family
  metrics and provenance with socket connections blocked; zero attempts. Timing
  fields are intentionally not compared.
- Coordinator final `uv run pytest`: **670 passed, 1 skipped in 38.73s**.
  The unchanged Docker integration opt-in is the sole skip. Actual pinned model
  tests are enabled via the explicit `MODEL_LEARNER_TEST_POTION_PATH`.
- Coordinator `uv run ruff check .`: **All checks passed!**
- Coordinator `uv run ruff format --check .`: **139 files already formatted**.
- Final `git diff --check`: passed. Checks use the repository-local uv/cache and
  `UV_NO_SYNC=1` to preserve the installed approved optional semantic runtime.
- Independent reviewer full actual-model run before the final added metric test:
  **669 passed, 1 skipped in 38.20s**, lint/format/whitespace passed. The
  coordinator's final run above includes that additional test.

Independent review found no remaining blocking defect in the delivered scope.
It prompted pre-encoding provenance corrections, disclosure of text tie-order
sensitivity, precise reported-ranking wording and updating status resource ranges
to the final stored artifact. External human adjudication, diverse negative
objectives and no-relevant-history cases remain evaluation limitations.

See `docs/SEMANTIC_TASK_EVALUATION.md` for provenance, reproducer, per-capability
limitations and error analysis. The next recommended increment is larger
independently human-adjudicated retrieval data with diverse real-world objectives,
plus explicit success criteria and changing-scope labels before extending task
understanding. No fine-tuning, routing, paid agent execution, web GUI, remote
inference, model downloads, Governor or utility-estimator integration was performed.
Stop after this requested increment; the recommended next increment is not started.

## Task annotation workflow and evaluation protocol — 2026-10-11

Delivered only the requested preparation/evaluation increment. The original
retrieval v1 fixture and its reference results remain frozen. No new retrieval
accuracy, task-classification accuracy or model-utility improvement is claimed.

- `understanding/annotations.py` defines strict `task-annotations/v1` local
  artifacts with task-description snapshots, optional caller-declared canonical
  task UUIDs, source SHA-256/locators/authorship, split/project/family/lineage,
  timezone-aware availability and separately sourced observed facts. Facts retain
  their own real/simulated/benchmark origin; judgments always remain inferred.
- Complete per-query candidate judgments separately record similarity,
  continuation, scope and apparent-difficulty changes, rationales, evidence
  references and hard negatives. Query-level no-match is yes/no/unknown; yes
  requires every candidate explicitly irrelevant in that frozen corpus. Unknown
  judgments remain unknown. Distinct explicit canonical task IDs cannot be
  overridden by a continuation label, and annotations never create ledger links.
- Human author identity and independent reviewer identity/kind/time are explicit
  caller attestations. Accept/reject reviews bind to descriptions, provenance and
  labels by content hash. Self-review (including case/whitespace variants), stale
  reviews, agent-only labels/reviews, missing annotations and unresolved rejection
  block freezing. Relabeling invalidates current reviews; exclusive revision files
  retain prior decisions and a parent-content digest. Identities are not authenticated.
- Split checks reject shared projects, families, lineages, canonical task IDs,
  normalized description copies and exact source records across train/development/
  test, including a source used as a description in one split and a fact in another.
  Facts cannot postdate their snapshot; historical candidates cannot postdate the
  query. Unknown correlations and source-locator aliases still require human audit.
- Freeze locks data and a prospective backend/k/strict score threshold/selection
  note plus Potion revision/hash where applicable. Evaluation requires the frozen
  human-reviewed artifact before model loading. Only descriptions enter retrieval;
  TF-IDF fits candidate text only, and labels/groups/facts enter reporting afterward.
- `understanding/annotation_evaluation.py` reports per-query/family and aggregate
  TP/FP/FN/TN, precision, known-target recall, pairwise false-positive rate,
  hard-negative errors, no-match false acceptance, coverage and abstention. Unknown
  labels are excluded from confusion denominators and counted separately; unknown
  representations are separate operational abstentions. No-match recall and other
  empty denominators are null. Precision@k retains the requested slot denominator.
  Continuation/scope/difficulty have label coverage only, with no classifier or
  fabricated predictions. The protocol documents their future independent tests.
- `commands/annotations.py` and CLI registration provide `annotation prepare`,
  `show`, `label`, `review`, `freeze` and `evaluate`, all using explicitly supplied
  local files, exclusive output creation and privacy-safe malformed-input errors.
  No ledger access, transcript collection, network inference or automatic fallback.
- `tests/fixtures/understanding/annotations/` contains 18 snapshots and nine
  complete **agent-authored draft proposals**, with three independent example
  cohorts. Three historical descriptions reuse frozen sanitized v1 text; one
  context fact reuses the simulated controlled execution fixture. Source hashes
  are verified in tests. UUIDs/checkpoints are hypothetical benchmark context,
  not real ledger records. These public exposed examples are workflow rehearsals,
  not a fresh held-out human-reviewed accuracy dataset.
- `docs/TASK_ANNOTATIONS.md`, the root README and a pointer in the original
  semantic-evaluation doc explain collection, independent review, rejection,
  versioning, leakage checks, development-only policy selection, exact metric
  denominators and limitations. Existing TF-IDF/Potion code and learner semantics
  are unchanged; no security boundary or database migration was modified.

### Actual validation and independent review

macOS arm64 / Python 3.12.14. Used the existing `.tools/bin/uv` and repository-local
`UV_CACHE_DIR=$PWD/.uv-cache`; the default global cache is outside sandbox writes.
No packages, model weights or paid agents were provisioned for this increment.

| Check | Actual result |
| --- | --- |
| Initial full `uv run pytest` during implementation | **720 passed, 5 skipped in 32.10s** before the final source-overlap/fixture/model tests; optional model path absent. |
| Focused annotation unit + CLI checks after review fix | **56 passed in 1.38s**; independent reviewer separately reproduced **56 passed in 1.63s** before two further encoder tests. |
| Final full `uv run pytest` with `MODEL_LEARNER_TEST_POTION_PATH` set to the existing approved `potion-base-8M-bf8b056651a2c21b8d2565580b8569da283cab23` local bundle | **728 passed, 1 skipped in 33.33s**. Includes all 58 new annotation tests and actual pinned local Potion evaluation, with socket connections denied in the new model test. The remaining skip is the existing explicitly enabled Docker offline isolation check. |
| `uv run ruff check .` | **All checks passed!** |
| `uv run ruff format --check .` | **146 files already formatted** |
| `git diff --check` | Exit 0; no whitespace errors. |
| `uv run model-learner annotation --help` | Exit 0; all six operations displayed. |

Independent subagent implementation review inspected contracts, evaluator, CLI,
tests, provenance and claims. It found one P2 split-leakage gap: description and
fact source origins used separate namespaces. Fixed by checking both against the
same source-location namespace, with a cross-role regression. Reviewer verified
the correction and found no remaining semantic/provenance/privacy/metric blockers.
Its final formatting observation was corrected and the final checks above passed.
This is independent code review, **not independent human annotation review**.
The documentation reviewer authored the protocol prose but did not implement the
schema, evaluator or CLI. Implementation/CLI and example-authoring subagents had
separate file ownership.

The workflow and protocol are complete. Actual realistic human label collection,
adjudication and prospectively unexposed test cohorts remain pending and must occur
before substantive task-understanding accuracy claims. Hidden cohort aliases,
honest human attestations and no test-driven policy selection require operator
discipline. Retrieval evaluation remains separate from model-utility prediction.
No fine-tuning, larger model download, paid agent, routing, security-boundary
change, web GUI, commit, push, merge or publication occurred. Stop here.

## First independent human semantic-review batch prepared — 2026-10-11

Read AGENTS.md, the master plan, status, annotation protocol, original semantic
evaluation documentation, annotation CLI/contracts/evaluator and workflow tests.
This is data preparation and review guidance, not a feature milestone. No
implementation blocker was found, and no source code, dependency, schema,
database, model, or frozen prior experiment was changed. Pre-existing tracked
`.DS_Store`, `pyproject.toml`, and `uv.lock` modifications were preserved.

- Prepared ignored local `.model-learner/annotations/semantic-human-review-v1/`:
  source material, `seed.json`, CLI-created `collection-000.json`, a neutral query
  inventory, 40 blank forms in the existing query-judgment format, and local
  inspection/author/reviewer/revision directories. The collection identity is
  `semantic-human-review-v1`, schema `task-annotations/v1`, source kind `benchmark`.
- 40 newly agent-authored realistic technical queries and 32 historical snapshots
  cover eight project/family cohorts. Development has 10 queries and 8 candidates;
  test has 30 queries and 24 candidates. Complete per-query labeling requires
  **800 pair judgments**. Project/family/lineage groups are disjoint between splits;
  correlated variants stay together. IDs are neutral and order is shuffled.
- Material includes related/independent work, wording traps, different-wording
  technical equivalents, shared-capability/different-objective comparisons,
  explicit continuations, absent identity declarations, changed objectives under
  retained task identity, unrelated tasks, and intended no-history cases. These
  construction intentions are not judgments: actual relevance/no-match counts
  await exhaustive human assessment against the full split candidate pool.
- All descriptions, UUIDs and availability checkpoints are hypothetical benchmark
  context. No real history, private transcripts, execution facts, or outcomes were
  collected. Source locators refer to inspectable `authored_descriptions.json`,
  SHA-256 `2cede15f28ac8f193d7eb1a73a87efab24ba90fc7d515c9be073b6e0a908188b`.
  No prior retrieval fixture text/labels were reused. All data stays local/ignored.
- Zero annotations, zero reviews, no selected protocol/freeze, and no scores,
  rankings, or evaluation reports. Forms have unknown dimensions and empty
  rationales, intentionally failing submission until completed by a human.
- `docs/HUMAN_REVIEW_BATCH.md` provides chronological exact commands to inspect,
  author labels, independently accept/reject, correct, re-review, freeze, and
  later evaluate. It separates objective similarity, shared capability context
  in the existing rationale, and explicit identity/continuation. No capability
  label field or second annotation system was introduced. Two distinct actual
  humans must review source material without score exposure; software/agent
  review cannot substitute for human annotation review.
- The guide proposes a prospective fixed k=3, strict score >0 comparison for
  TF-IDF and the existing pinned Potion bundle, with separate frozen artifacts
  before held-out evaluation. This is not a calibrated rejection policy. Freeze
  and evaluation commands are provided for the operator, **not executed** here.

### Actual preparation checks

Existing macOS/Python 3.12.14 environment; `.tools/bin/uv`, repository-local
`UV_CACHE_DIR`, and `--no-sync` preserve installed dependencies. No installation
or model download occurred. Existing tests use separate fixtures, not labels for
this batch.

| Check | Actual result |
| --- | --- |
| `uv run --no-sync model-learner annotation prepare ... --dataset-id semantic-human-review-v1` | Exit 0; exclusively created pending `collection-000.json` with parent seed digest. |
| `uv run --no-sync model-learner annotation show ... --query-id q-93b477` | Exit 0; one query and all 24 test candidates, with no labels or model scores. |
| Local structural/source audit | Passed: exact counts, all source hashes/locators, complete candidate forms, checkpoints, split validation, and parent digest; all 40 unchanged blank forms reject submission. Human-review completeness gate rejects the pending collection. No frozen artifact/report exists. |
| `uv run --no-sync pytest tests/unit/test_task_annotations.py tests/unit/test_semantic_evaluation.py tests/integration/test_annotations_cli.py` | **78 passed, 2 skipped in 1.77s**. Skips are existing explicit local-model opt-ins; no actual-model test was enabled for this data-only activity. |
| `uv run --no-sync ruff check .` | **All checks passed!** |
| `uv run --no-sync ruff format --check .` | **147 files already formatted** |
| `git check-ignore` for seed/collection | Both files ignored under `.model-learner/`. |
| `git diff --check` | Passed. |

Batch preparation is complete. Manual source/context audit, genuine human labeling
and independent acceptance are still required before finalizing or evaluating.
The evidence will remain a small constructed benchmark even after human review;
it does not establish population accuracy on real task history, continuation
prediction, shared-capability classification, or model utility. No new models,
fine-tuning, routing, Governor, subagent, commit, push, merge or publication.
Stop here; the next action belongs to the human annotator and independent reviewer.

## First longitudinal task-state understanding — 2026-10-11

Read the plan, repository instructions, existing status, task-state/semantic/
annotation documentation and relevant code before implementation. A review
subagent independently audited evidence and later reviewed provenance, temporal
leakage, feature correctness, unsupported semantic inference, privacy and evaluation.
A separate implementation subagent owned only the synthetic evaluator, fixture
and its tests; the coordinator owned projections, CLI, integration and documentation.
No core architecture change or new database migration was needed. The pre-existing
working-tree changes to `.DS_Store`, `pyproject.toml` and `uv.lock` were preserved;
this increment did not alter them or add dependencies.

### Evidence audit and delivered behavior

- The real checked-in Codex derivative has four metadata-only buffered smoke
  events, without tools, code edits, semantic text or verified coding outcomes.
  Rich execution/JUnit/predictive/retrieval fixtures are explicitly synthetic.
- Safe aggregate inspection of ignored local ledgers found one genuine verified
  fixed-reply smoke observation plus its earlier unknown derivation, and a
  separate operator-run JUnit producer validation without execution events or
  learning observations. Smoke task/association availability follows captured
  events and cannot be backdated. There are **zero suitable real longitudinal
  coding trajectories** for this evaluation, not zero verified records anywhere.
  The audit read no description, raw payload or private transcript contents.
- `execution.longitudinal` reuses the existing checkpoint extractor and domain
  contracts. Identity/objective is separate from evolving state. Observed event
  receipts and retained tool/test evidence, derived counts/deltas/failure groups,
  inferred author phase/progress/scope/difficulty hypotheses and unknowns remain
  explicit. The nested existing execution projection retains compatibility;
  new `derived` fields give computed counts their proper epistemic classification.
- Optional `CheckpointSummary` takes explicitly submitted bounded public/sanitized
  text, SHA-256, actor/source declaration, observation/availability times and
  optional already visible evidence IDs. Text alone is not parsed into semantic
  claims. Actor identity/privacy are self-attested, not authenticated or attested
  by a digest. Unknown fields/tied latest reports remain unknown.
- Future events/summaries, delayed ingestion, scope/declaration receipts, run
  bounds, references and conflicts are checked at each cutoff. Raw payloads and
  arbitrary metadata do not enter outputs or embeddings. Completed turns,
  successful tools and reported completion never verify task success. No progress
  percentages, native execution times, unknown costs or identical retry causes
  are manufactured. Final-artifact JUnit visibility reuses existing checks;
  intermediate-artifact progression remains unsupported.
- `TrajectoryInput` is an explicit portable input over existing records, not a
  ledger schema or automatic collection mechanism. `task trajectory INPUT.json`
  makes state/changes inspectable; `learn trajectory-eval FIXTURE.json` compares
  the synthetic variants, with optional explicitly pinned local Potion. Reports
  use exclusive destinations and private invalid-input excerpts are omitted.

### Evaluation actually established

`tests/fixtures/longitudinal/` contains seven agent-authored **simulated** scenarios,
fourteen checkpoints, a digest manifest and an actual pinned local CPU reference.
The cases cover normal reported progression, unsuccessful tool actions, declared
complexity growth, implementation-to-debugging, reported completion without
verification, missing evidence and no observed change. They include no fabricated
verification/outcome records, human labels or accepted reviews.

| Variant / check | Actual result and interpretation |
| --- | --- |
| A initial only | Seven abstentions about subsequent change; appropriate lack of evolving evidence. |
| B metadata only | 6/7 status and 3/7 full dimension agreement with authored rules; zero semantic transitions established. |
| B including explicit reports | 7/7 status and dimension agreement; four cases obtain semantic hypothesis changes from author declarations. This is software rule agreement, not human-reviewed semantic accuracy. |
| C with existing Potion | Actual pinned CPU cosine diagnostics computed; identical classifications to B **by construction**, with no semantic threshold/classifier. No additional recognition or predictive benefit demonstrated. |
| Unsupported-inference checks | 154 implementation invariant checks, zero violations; not a population inference-error rate. |
| Downstream independently verified outcomes | `insufficient_data`, zero eligible outcomes in this longitudinal dataset and null scores. No outcome model fitted and no real-world improvement claimed. |

The Potion model/revision/bundle pins are unchanged. The actual-model test denies
socket connections and reproduces reference cosines within 1e-12. Missing weights
stay unavailable; no model download, alternative model, training or cloud inference.
The old outcome evaluators remain intact. A future outcome experiment must choose
one prospective checkpoint horizon per run, resolve labels historically and split
independent lineages; fourteen checkpoints here are not fourteen outcome trials.

### Validation and independent review

Used the existing local uv/Python environment with `.tools/bin` on PATH and
repository-local `UV_CACHE_DIR`. Full validation explicitly set
`MODEL_LEARNER_TEST_POTION_PATH` to the already approved local bundle.

| Executed check | Actual result |
| --- | --- |
| Final `uv run pytest` | **770 passed, 1 skipped in 38.37s**; skipped existing opt-in Docker offline isolation test. |
| `uv run ruff check .` | Exit 0; all checks passed. |
| `uv run ruff format --check .` | Exit 0; 155 files already formatted. |
| `git diff --check` | Exit 0; no whitespace errors. |
| Independent focused suite, actual pinned Potion | **42 passed in 0.63s**; no skips, sockets denied in actual-model test. |
| Actual installed `learn trajectory-eval` with full Potion pins and new `/tmp` output | Exit 0; A/B/metadata-only/C results, 154 checks / zero violations and `insufficient_data` reproduced. |

Review found a semantic-input visibility bypass in an early evaluator version:
its separate text filter omitted reference/run-bound/ambiguity eligibility.
Fixed by using the same projected states for objectives and summaries; encoder-spy
regressions cover delayed scope/description, late event references, pre-run text,
future text and tied summaries. Final independent review found no unresolved
privacy, provenance, temporal, feature or evaluation blockers. Software subagent
review does not count as human annotation/adjudication.

### Minimum evidence needed next

`docs/LONGITUDINAL_TASK_STATE.md` provides the concrete proposal: a manual opt-in
pilot on 5–10 independently scoped, already occurring local trajectories to study
evidence usability. Record a sanitized initial objective/target/configuration and
association receipts prospectively; submit brief sanitized checkpoint sidecars
about activity, attempted mechanism, obstacle, progress evidence and scope change;
keep author hypotheses separate from facts and store private sidecars in ignored
local storage. Later acquire distinct genuine human trajectory labels/review and
independently verified outcome/label-availability receipts. Intermediate-artifact
test evolution requires a separately scoped contract, not relaxed final-verifier
semantics. Enough independent prospective outcomes are needed before prediction.

The next recommended increment is **manual prospective summary collection and
evidence-usability review**. This proposal is not started. No raw transcript
collection, hooks, paid agents, benchmark-security bypass, retrieval expansion,
model switching, routing, Governor, GUI, commit, push, merge or publication.
Stopped after the requested implementation/evaluation.

## Known issues / blockers

- Real benchmark collection is fail-closed pending a supported, validated
  agent backend, credential relay, hostile artifact freezing/extraction, separate
  candidate-only acceptance transport and exact-runtime run-bound validation
  receipts. The validated fixed offline shell probe and new synthetic controller
  receipts do not attest these real-agent boundaries.
- Actual Potion CPU semantic C evaluation is complete on synthetic cohorts, with
  no consistent improvement. Real-world semantic predictive benefit remains
  unestablished. The optional original MiniLM backend is still integration-pending;
  its model/torch/transformers were not provisioned or validated here.
- The pilot is prepared for operator review and controlled fixture rehearsal.
  Manually authorizing payment does not resolve containment or predictive export
  limitations; no real experiment has been authorized or run here.

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

- First longitudinal state reconstruction and synthetic A/B/C rule evaluation are
  complete. Next: an explicitly authorized manual prospective sanitized-summary
  pilot and independent evidence-usability review, as specified above and in
  `docs/LONGITUDINAL_TASK_STATE.md`. No pilot or next implementation is started.
  The earlier retrieval human-review batch remains pending; it need not expand
  before demonstrating utility. Earlier recommendations below are historical.
- The local 40-query human-review batch is prepared; the annotation workflow and
  protocol remain complete. The next evidence step is genuine independent human
  labeling/adjudication of that batch, then retrieval/no-match/abstention
  measurement under a prospectively frozen policy. No next implementation increment,
  semantic classifier, fine-tuning or utility integration is authorized or started.
  Earlier checkpoint entries below are historical.
- The fixed offline isolation experiment and benchmark evidence pipeline are
  delivered. The requested secure controller components and CPU representation
  prototype are also delivered for their offline scope; await new user direction.
  A real pilot still requires the exact agent/credential/artifact/independent
  acceptance boundary plus prospective checkpoint collection. The requested
  pretrained Potion C evaluation is complete; optional MiniLM validation was not
  requested. No real run, further installation or next milestone is authorized.
- The requested coding-verification, execution-analysis, coding-task evaluation
  and task-state evaluation workstreams are delivered and checked. No next
  milestone is authorized. Real benchmark executions remain operator-controlled
  and were not launched; real predictive improvement remains unestablished.
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
