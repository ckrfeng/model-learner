# Model Learner status

Current work: experiment 2 complete after explicit user approval. One ordinary
Codex CLI execution fixed ShortcutLens DataLoader seed validation. All 172 frozen
required checks passed (60 independent acceptance cases, 112 initial regressions),
with zero failures/errors/skips. Candidate and applied-code scoped regressions each
passed 129 cases; Ruff passed. The verified two-file patch is applied; unrelated
concurrent project work was preserved. Capture/import retained 18 events with no
diagnostics; replay added zero. One real single-configuration verified-success
observation is eligible and consumed by the existing learner with no exclusions.
Prior-only mean 0.5 [0.025, 0.975] became 0.667 [0.158, 0.987] after one label;
this establishes workflow operation, not predictive accuracy. Operator wall time
was 31.64 seconds; native latency, dollar cost and effective native configuration
remain unknown. Relevant Model Learner checks: 95 passed; Ruff/format clean.
No new Model Learner infrastructure, semantic changes, additional agents, training,
commit or publication. Stopped after this one experiment; no further run authorized.

Prior work: first supervised real CSV coding experiment complete after explicit
user approval. One Codex CLI invocation requested gpt-6.1-sol with low reasoning,
produced a standalone standard-library CSV comparison script, and exited 0.
Metadata capture exited 0; import stored 11 events and one session without
diagnostics. All 18 independent acceptance tests, frozen before execution, passed
on the exact final script snapshot without failures/errors/skips or source changes.
Bound JUnit evidence produced one verified-success assessment and one eligible
single-configuration real observation. Existing reference learner consumption
selected one eligible success with no exclusions. Capture replay added zero events.
Operator agent wall time was 123.44 seconds; native latency, dollar cost and native
configuration/version confirmation remain unknown. Full repository checks:
931 passed, 7 existing skips; Ruff and formatting clean. Private experiment files
remain ignored. No production implementation, semantic analyzer, new trained model,
Governor, commit or publication changes. Stopped after this one experiment; no
additional run or milestone is authorized.

Prior work: real execution/outcome readiness assessment complete. Existing
capture, task/run/attempt, JUnit verification, assessment resolution and learning
contracts support a minimal prospective 5–10-run ordinary Codex CLI collection
pilot without new infrastructure. Read-only inventory/resolution establishes one
eligible real fixed-reply smoke run and zero eligible real coding runs. With user
approval, the three selected project artifacts passed fresh independent checks;
passing current checks does not establish historical configuration/attempt binding.
Sanitized assessment and exact operator sequence: docs/REAL_DATA_READINESS.md.
Private reports, snapshots and receipts remain ignored. No production code,
training, semantic integration, routing or Governor changes. Stopped after the
assessment/recommendation; prospective collection is unstarted.

Prior work: bounded local CPU semantic-extraction comparison complete.
Qwen2.5-1.5B-Instruct Q4_K_M was downloaded with explicit approval and evaluated
with a frozen zero-shot prompt/schema on 15 consumed diagnostic and 16 fresh
prediction-blind simulated checkpoints. It did not improve extraction: holdout
positive-obligation alignment is 3/25 precision and 3/31 recall, versus frozen
rules 10/16 and 10/31, structural parsing 12/13 and 12/31. Known objectives are
0/15, 0/15 and 4/15 respectively; all have 0/9 earlier-link recovery.
Only 4/33 local-model holdout events satisfy message-local evidence validation;
all 31 model generations are schema-valid, illustrating why JSON validity is
insufficient. Median holdout inference is 4.98 seconds and peak runtime RSS about
2.2 GiB. These are AI-reference agreement findings, not human-verified accuracy.
No production analyzer, estimator, dependency or routing change. Sanitized report
is docs/LOCAL_TASK_STATE_COMPARISON.md; private evidence and independent final
review remain ignored. Stopped after comparison/recommendation. No further model
or milestone started.

Prior work: authorized comparison of frozen predictions with independent
AI-authored Work annotations complete. All 15 exposed user messages and 150
reference fields validated; inputs and analyzer hashes remain unchanged. Private
report separates semantic agreement, missing/incomplete predictions, unsupported
fields, contextual matching and annotation policy. Typed positive-obligation
agreement is 21/24 normalized predicted units and 21/84 reference obligations;
alternate positive evidence covers 32/84. Current core-action objective agreement
is 3/15; topic compatibility is separately 8/15. These are post-hoc AI-reference
agreement measurements, not human-adjudicated accuracy or generalization.
No analyzer execution, implementation, training or outcome integration occurred.
Validation and independent methodology review are recorded at the end. Stop after
the comparison report; human adjudication and any further experiment are unstarted.

Prior work: blind human-adjudication worksheet preparation complete, with all
15 exposed user messages and 150 blank annotation cells. No human labels were
filled. The later comparison was separately authorized by the user and uses
independent AI annotations; genuine human adjudication remains pending.

Prior work: selected-conversation coverage recovery and projected evaluation
complete. All 15 exposed user messages across the same four selections now have
predictions (3/3, 4/4, 4/4, 4/4); original full-text results remain separate and
unchanged. A prediction-frozen all-user-prefix policy omits assistant text into a
separate message-local report view. The analyzer, rules and default importer
limits are unchanged. Approved diagnostic transport reads used a separate 256-KiB
allowance; non-message payloads caused the two original wire failures, and earlier
assistant prose caused the research clause failure. Objectives still remain unknown
for two selections; omission loses one user-to-assistant candidate edge. No human
labels or independent outcomes inspected; semantic accuracy remains unmeasured.
Checks: 870 passed, 7 existing opt-in skips; Ruff and formatting clean.
Independent review is recorded below. Stop after evaluation and recommendations;
human adjudication and outcome integration remain unstarted.

Prior focused semantic task-state generalization evaluation is complete.
The baseline and original diagnostic
results are frozen. Prediction-blind independently agent-authored synthetic
holdouts expose substantial failures: opening objectives 5/11 on the first 12
cases; typed requirement precision 13/18 and recall 13/23. Two bounded corrections
recognize progressive objective verbs and flag multiple candidate change targets.
On eight untouched cases the revision and baseline have identical recognition
results: opening objectives 3/7, typed requirement precision 5/6 and recall 5/10.
A separately untouched requirement-reinstatement case also shows no improvement.
No false verified claims occur; reference-policy artifacts are documented.
The user-supplied scheduling sentence reproduces an objective-rule morphology
defect with intact text and is fixed in a synthetic bridge regression. The private
original was not reread. No real outcome/predictive benefit is established.
Do not integrate these semantic hypotheses as trusted utility features yet.
Full checks passed: 865 tests, 7 existing opt-in skips, clean Ruff and formatting.
Independent final code/evaluation review found no blockers. Stopped after
evaluation and recommendations.
The standalone importer and prior longitudinal/retrieval increments remain intact.
The earlier 40-query human-review batch still has no genuine human labels or
accepted reviews. Real coding-agent benchmark execution remains disabled.
Last requested work: diagnose coverage for the same four selected conversations,
freeze separate evidence views, evaluate the unchanged analyzer, report limitations
and recommend whether to human-adjudicate. No later milestone is started.
Updated: 2026-10-13

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

## Selected Desktop and Work conversation feasibility — 2026-10-11

Read the master plan, AGENTS.md, status, existing observation/domain/association
code, deterministic execution and longitudinal projections, task retrieval,
annotations and optional local CPU encoder. Investigated Codex Desktop and ChatGPT
Work Local separately using official documentation, exposed desktop tool contracts,
public CLI help and freshly generated installed-version protocol schemas.

- `docs/CONVERSATION_INGESTION_FEASIBILITY.md` records source-by-source access,
  text/event/model/time/usage coverage, storage distinctions, account-export gaps,
  shared identity semantics, privacy, a bounded validation proposal and adapter
  tests. The prior Desktop report now points to this selected-history assessment.
- The exposed desktop `read_thread` reader supports an exact thread/chat ID and
  older-turn cursors. Its contract describes summaries and truncated optional
  outputs; complete raw messages/events and historical measurements are not
  established. This tool is available to an agent session, not a demonstrated
  callable interface for the standalone Model Learner CLI.
- Public Codex app-server supports stored reads without resuming. Installed
  `Thread` exposes optional model/effort explicitly described as current/latest
  settings, optional native project and source-origin fields, and a separate
  session-tree ID. `Turn` has nullable times/duration but no usage field. Message
  item variants lack per-message timestamps. Experimental history pagination
  needs version/capability checks; stored items cannot invent original lifecycles.
- Installed CLI remains `0.162.0-alpha.17.2`; help and fresh public schema
  generation exited 0. Schemas are outside Git under
  `/private/tmp/model-learner-history-protocol-20261011`. The read-only public
  daemon-version query exited 1 because its default control socket was absent.
  This blocks that endpoint only; it does not prove no desktop reader exists.
- Work Local can have a Codex-backed local task; ChatGPT-backed conversations with
  local execution are distinct. Official docs describe local-only Work history
  and cloud coordination with local execution. Product surface, backend, execution
  and transcript storage must stay separate. No selected Work backend was tested;
  public standalone Work-history access and account-export coverage remain
  unestablished. The Responses Conversations API is not established as an export
  interface for existing desktop chats.
- Existing Session/task/run/project links preserve the required identity
  separation. The report proposes a source-aware ordered snapshot with missingness,
  privacy and actual receipt times. Existing reviewed-text retrieval and explicit
  summaries can be reused. Execution analysis and the real observation builder
  currently require the exact Codex CLI source; relabeling snapshots as CLI events
  would fabricate provenance. No source-neutral projection was implemented.
- Only optional pinned existing Potion CPU relatedness is proposed. Embeddings
  cannot establish reasoning, progress, continuation or task identity; reported
  semantic hypotheses remain distinct from independently verified outcomes.
- No histories were enumerated, no thread/chat was read, and no private database,
  rollout, authentication token, intercepted traffic or scraped UI was accessed.
  No account export was requested, no daemon started, no global setting changed,
  and no agent execution, adapter, model download, routing or Governor added.

### Actual investigation checks

Existing repository-local uv/cache and `--no-sync` preserved installed dependencies.
No new tests were written for documentation-only changes.

| Executed check | Actual result |
| --- | --- |
| `uv run --no-sync pytest -q` with ten selected observation/domain/workflow/execution/retrieval/annotation/longitudinal test files | **183 passed, 2 skipped in 1.11s**; optional model opt-ins were not enabled. |
| `uv run --no-sync ruff check .` | Exit 0; all checks passed. |
| `uv run --no-sync ruff format --check .` | Exit 0; 155 files already formatted. |
| Documentation diff `git diff --check` | Exit 0; no whitespace errors. |

These are existing regression and schema/help checks, not real Desktop or Work
history validation. Full suite and actual-model integration were not rerun for
this documentation-only assessment. The pre-existing `.DS_Store` change remains.

Next permitted step only after selection/approval: read one exact, non-sensitive
existing conversation per source through the built-in reader, initially one turn,
at most ten turns and 64 KiB retained text each, outputs/attachments excluded.
Preserve identity, ordering basis, source provenance, optional times and missing
fields in ignored local storage. Reader access can place returned text in the
assistant context/tool history; local inference alone cannot make that read
device-only. Standalone app-server validation additionally needs an existing
supported endpoint. No automatic history discovery or speculative integration.
Stop after this feasibility report; controlled validation and implementation
remain unstarted.

## Selected conversation identifier discovery — 2026-10-11

The user supplied two non-sensitive test descriptions but no IDs/links. Inspected
exposed tool definitions, official desktop command/app-server documentation and
the already generated public `ThreadListParams` / `ThreadListResponse` schemas.
Updated `docs/CONVERSATION_INGESTION_FEASIBILITY.md` with the discovery boundary.

- Desktop `list_threads` has no title/source filter, can return generated summaries
  and always includes every pinned chat. It does not meet targeted metadata-only
  discovery limits; it was not called.
- App-server title filtering is documented, but installed responses include a
  required preview usually containing the first user message, with no suppression
  parameter. Selected Desktop connectivity remains unvalidated; `appServer` alone
  cannot distinguish Codex and Work. No RPC or endpoint probe was performed.
- Official **Copy chat deep link** (`Cmd+Option+L` on macOS) provides a manual route
  to a local technical thread ID. The user can copy each selected test's link and
  label its product/mode. No UI/clipboard inspection, history enumeration, private
  database/credential access, conversation read or shared-snapshot creation occurred.
- Both selected access tests, actual returned-field coverage, standalone Python
  connectivity and automatic local ingestion remain **unvalidated**. No adapter,
  model, routing, Governor or application setting change was implemented.

Next step: await the two user-supplied deep links, confirm each selected source and
identity, disclose the exact reader/context exposure and request explicit approval
per conversation. Only then read one turn with outputs disabled; expansion remains
bounded by ten turns and 64 KiB retained text per approved conversation. Stop after
validation/reporting; no adapter implementation is authorized.

Checks used the existing environment with `.tools/bin` on PATH, repository-local
`UV_CACHE_DIR` and `--no-sync`; no dependency changes or new tests were needed.

| Executed check | Actual result |
| --- | --- |
| `uv run --no-sync pytest -q` | **764 passed, 7 skipped in 33.61s**; optional integration opt-ins were not enabled. |
| `uv run --no-sync ruff check .` | Exit 0; all checks passed. |
| `uv run --no-sync ruff format --check .` | Exit 0; 156 files already formatted. |
| `git diff --check` | Exit 0; no whitespace errors. |

These regression checks do not validate selected conversation access. Only this
status and the feasibility documentation changed; the pre-existing `.DS_Store`
modification was preserved. No commit, push, merge or publication was performed.

## Controlled selected-conversation validation: pre-read transport stage — 2026-10-11

The user supplied exact local deep links for the Work scheduling-algorithms test
and Codex CSV-parser test. They confirmed both surfaces use the unified ChatGPT
macOS application with a mode selector. Shared UI/link scheme, local execution,
project working directories and guessed `~/Documents/Codex/` / `~/.codex/` paths
are not evidence of a shared backend or selected transcript storage.

- Requested explicit approval separately for each agent-mediated read, identifying
  `mcp__codex_app__read_thread`, model-context/tool-history exposure and the exact
  initial/maximum scope. No read approval is inferred from a supplied link.
- Installed public help/version checks succeeded. The read-only daemon-version
  query again found the documented default control socket absent (exit 1).
- A standalone ordinary Python subprocess invoked the installed supported
  `codex app-server proxy` with empty input and a ten-second timeout: child exit 1,
  zero stdout bytes, missing default socket. No conversation RPC was sent.
- Public stored-history protocol candidates exist, but selected access and source
  coverage remain unverified. Full `thread/read` lacks a turn limit; paginated
  request schemas lack output/attachment suppression. No daemon, alternate socket,
  private history/config/authentication access or application setting change.

At this stage the feasibility document recorded these transport facts and distinguished them
from successful independent Python conversation access. Both selected-content
validations remain pending their approvals. No native IDs, raw messages or
adapter implementation were added to tracked files.

Next permitted work: after each separate approval, read that selected ID with one
turn and outputs disabled; examine returned coverage and expand only within the
approved ten-turn/64-KiB limit. Report each source independently and stop without
implementing an adapter. Standalone automatic ingestion remains unestablished.

Documentation follow-up checks: `uv run --no-sync ruff check .` passed;
`uv run --no-sync ruff format --check .` reported 156 files already formatted;
`git diff --check` passed. No new Python test was needed or run for these
documentation-only changes. Prior regression evidence is recorded above and is
not evidence of either selected-content read. The pre-existing `.DS_Store` change
was preserved; no commit, push, merge or publication.

## Controlled selected-conversation validation: completed — 2026-10-11

The user explicitly approved both exact-ID agent reads separately with context
exposure disclosed. Used `mcp__codex_app__read_thread`, one turn per request,
`includeOutputs=false`, per-item text cap 3,000 characters, only each selected
conversation's cursors. No attachments, tool outputs, unrelated enumeration,
source execution/resumption, private database/authentication access, settings
change or adapter implementation. Returned text entered model context/tool history;
no transcripts or snapshot payloads were written to workspace files.

- **Codex CSV-parser sample:** three unique turns across three pages, all returned
  IDs matching the approved selection. Reader reports `kind=codex`, `hostId=local`.
  Three user and three assistant message items, plus one separate empty reasoning
  summary. Expected requirement progression is preserved; implementation remains
  unverified. Cumulative serialized retained responses: **5,396 UTF-8 bytes**.
- **Work Local scheduling sample:** three unique turns across three pages, stable
  matching selected ID. Reader also reports `kind=codex`, `hostId=local`, despite
  its user-declared Work product surface. Three user and three assistant message
  items preserve the expected narrowing/incomplete research progression. Cumulative
  serialized retained responses: **4,415 UTF-8 bytes**.
- Explicit `newest_first` pagination, native turn/item IDs, user-before-assistant
  item ordering and increasing start times after reversing the pages establish
  ordering within returned material. Both final pages have `hasMore=false` and
  `nextCursor=null`; this does not prove complete original history.
- Thread creation/update and turn start/completion/duration/status fields returned.
  No per-message timestamps, model/provider/effort, token usage or cost fields.
  No tool-call items exposed; zero original tool activity cannot be inferred.
  No content-truncation marker; longest text items are 460 / 159 characters,
  below the cap. Source lossless fidelity and omitted details remain unknown.
- The first Work request's byte-count wrapper failed before retaining/displaying
  its response; repeated the same one-turn request, without expansion. Four Work
  reader calls versus three Codex calls; retained scope is three turns each.
- Message-bearing user/assistant items were returned rather than merely generated
  retrieval summaries. Exact verbatim equivalence was not independently compared
  with the UI. Reader backend classification and local host do not locate transcript
  storage or establish device-only data. Returned cwd is project context.
- Independent Python history access remains **unvalidated**: the ordinary Python
  proxy probe in the preceding stage failed at an absent default endpoint before
  conversation RPC. Public App Server stored-read/pagination protocols are
  candidates, but neither selected ID was read through that transport. No general
  standalone interface for the agent-only desktop reader was established.

The updated feasibility report contains separate per-source coverage and smallest
integration conclusions. A bounded selected-snapshot projection is supported by
agent-returned evidence but still requires an agent. No autonomous ingestion adapter
is justified until supported endpoint reachability, selected-source mapping and
content exclusions are validated. Do not implement the handoff as a substitute for
the user's ordinary local Python application requirement.

Stopped after controlled validation/reporting. No next implementation milestone is
authorized; native IDs, working paths and transcripts were omitted from tracked
documentation. Current checks: `uv run --no-sync ruff check .` passed;
`uv run --no-sync ruff format --check .` passed (156 files formatted), and
`git diff --check` passed. No Python behavior changed; the prior full regression
suite (764 passed, 7 skipped) was not repeated. Actual integration evidence here
is the selected reader responses and the failed ordinary Python proxy probe,
not repository test success. No new tests, dependency changes, commit, push,
merge or publication; the pre-existing `.DS_Store` change was preserved.

## Independent Python stdio history experiment — 2026-10-11

The user explicitly approved temporary App Server startup and exact-ID reads for
the same two non-sensitive tests before any server process was launched. Read the
official App Server documentation, current status, relevant M3 plan boundary and
previously generated public parameter schemas. No runtime/package was installed.

Exact child command used the already installed executable:

```text
/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex app-server --listen stdio://
```

An ordinary **Python 3.9.6** standard-library client used subprocess stdin/stdout
JSONL, `initialize`/`initialized` with experimental pagination opt-in, then both
exact-ID `thread/read(includeTurns=false)` requests before any turn requests.
The protocol allowlist contained only those handshake methods and
`thread/turns/list`. No frontier-model retrieval or inference operation was sent.

| Actual check | Codex CSV-parser test | Work Local scheduling test |
| --- | --- | --- |
| Selected metadata access | Success; returned ID equals selected ID | Success; returned ID equals selected ID |
| Returned originator | `Codex Desktop` | `codex_work_desktop` |
| Other source/history fields | `source=vscode`, `threadSource=user`, `historyMode=paginated`, status `notLoaded` | Same |
| Server-limited turns | `limit=1`, `sortDirection=desc`, `itemsView=notLoaded`; three unique turns after cursor expansion | Same |
| Comparison with agent reader | Latest turn ID and all three start/completion/duration tuples match | Same |
| End/order | Final cursor null; reversing pages yields increasing start times | Same |
| Model metadata | `gpt-6.1-sol`, provider `openai`, effort `high`; current/latest thread settings only | Same |
| Returned/excluded content | Thread preview received privately; all turn items omitted server-side | Same |
| Measurements | Thread/turn times present; token/usage fields absent | Same |
| Response bytes in expanded run | 2,705 | 2,725 |

First successful run retrieved metadata plus one turn scaffold per source. The
second successful bounded run expanded to three turn scaffolds each, always one
turn per page. Cumulative response accounting across both runs: **4,390 bytes**
Codex / **4,430 bytes** Work, below 64 KiB each and only three unique turns each.
All returned items arrays were empty with `itemsView=notLoaded`. No attachment,
tool-output, message-item body or full-history request was issued. Nonempty thread
preview establishes limited text availability, not complete original messages.
No explicit truncation field; source/preview completeness and fidelity remain
unknown. No per-turn historical model attribution or token/cost recovery claim.

The outer execution sandbox blocked startup before handshake (`Operation not
permitted`; two startup/diagnostic attempts exited 1 without conversation RPC).
Scoped execution-sandbox escalation allowed the same approved protocol test.
Both successful temporary servers terminated on stdin EOF with exit **0**.
This corrects the earlier endpoint limit: an absent daemon proxy socket does not
prevent independent stdio access. No internal socket discovery was performed.

Private responses stayed inside Python memory; only sanitized coverage/error
facts reached terminal output/model context. No private response/log/transcript
file, native conversation ID or working/history path was added to Git or report
fixtures. The one-off probe outside Git was removed. No private database,
credential or undocumented rollout inspected; no unrelated conversation listed;
no resume/start, model turn, tool execution, mutation method or application setting
change. Read-only RPC behavior was validated, not zero incidental server startup
filesystem writes. Native path fields were not followed.

The updated feasibility report now justifies a narrow selected-ID standalone
**metadata/turn-record adapter** over this temporary stdio transport for these
samples. It preserves separate product provenance/originator and unknown historical
fields; it creates no automatic task/run links or verified outcomes. A standalone
message-text adapter still needs a supported selective-content boundary or a
separately approved scope: the inspected pagination parameters lack attachment/
tool-output filters, so summary/full item retrieval was not tested. Evidence for
this Codex-backed Work record does not establish every Work backend/storage path.

No adapter was implemented. Stop after this experiment/report; no next milestone,
new model, routing or Governor work is authorized. Documentation-only checks:
`uv run --no-sync ruff check .` passed; `uv run --no-sync ruff format --check .`
passed (156 files formatted); `git diff --check` passed. No production Python
behavior changed, so pytest was not repeated and no new test fixture was added.
The actual integration evidence is the independent subprocess result and its
bounded identity/time comparison, not repository regression tests. The pre-existing
`.DS_Store` change was preserved. No commit, push, merge or publication.

## Selective standalone text validation — 2026-10-11

The user explicitly approved **one full-view turn per selected test** after the
schema/documentation findings, with a stop for approval before implementing the
importer. Installed schema generation succeeded for CLI 0.162.0-alpha.17.2.
`summary` is a display summary; `full` includes every available persisted turn
item. Neither turn pagination nor item pagination has a message-only, attachment
or tool-output filter. Client exclusion occurs after the server returns content.

The temporary standard-library Python 3.9.6 client used the same stdio transport
and allowlist (`initialize`, `initialized`, `thread/read`, `thread/turns/list`).
After handshake it requested metadata without turns, then one latest full turn
per selection, with `limit=1` and descending order. No cursor expansion, item-list
RPC, unrelated enumeration or control method was sent. One notification was
ignored privately; server-initiated requests were prohibited. Scoped execution-
sandbox escalation was used for the approved process. Probe and temporary server
both exited **0**; server shutdown completed on stdin EOF.

| Actual sanitized coverage | Codex test | Work Local test |
| --- | --- | --- |
| Identity/source | Selected ID matched; originator `Codex Desktop` | Selected ID matched; originator `codex_work_desktop` |
| Runtime/history | `source=vscode`, `threadSource=user`, paginated | Same |
| Turn/item scope | One turn, confirmed full view, older cursor remains | Same |
| Messages/order | One user then one assistant, source ordinals 0/1, unique IDs | Same |
| User / assistant text bytes | 117 / 460 | 135 / 144 |
| Extracted text retained in memory | 577 bytes | 279 bytes |
| Metadata plus turn response bytes | 2,625 | 2,327 |
| Turn start/end/duration | Populated | Populated |
| Message timestamps | Absent / unknown | Absent / unknown |
| Other items / non-text user parts | Zero / zero in this turn | Zero / zero in this turn |
| Explicit truncation marker | None exposed | None exposed |

All four text fields were nonempty and survived local JSON round-trip comparison
without normalization or clipping. This validates extraction, not original-source
fidelity. The original test-message baseline is unavailable for independent
equality checks. Codex's 460-character assistant field matches the earlier reported
maximum length only; that does not establish text equality. Latest user strings
do not equal the first-message-style thread previews, as expected for later turns.
No source-completeness claim follows from full persisted view or missing markers.

Responses, previews, text and native errors stayed inside Python memory; only
coverage facts reached terminal/model context. No body/transcript file, fixture,
native ID or returned private path was added to Git. The temporary probe was
removed after use. One turn and under 64 KiB per selection stayed within the
ten-turn / 64-KiB ceilings. No inference/execution, task/run association, outcome
or learning record was created. Zero other items here does not imply server-side
exclusion elsewhere.

One-turn standalone user/assistant text access is supported for both samples.
Three-turn standalone text history, independent verbatim fidelity, historical
model/usage/cost attribution and other Work backends remain unvalidated. No
importer implemented; user approval is required before Phase 2 and bounded Phase 3
validation. Documentation-only checks: `uv run --no-sync ruff check .` passed;
`uv run --no-sync ruff format --check .` passed (156 files formatted);
`git diff --check` passed. Used the existing repository-local uv/cache paths.
No production Python changed, so pytest was not repeated. Full tests, sanitized
fixtures and independent importer review remain Phase 3 work after approval.
The pre-existing `.DS_Store` change was preserved. No commit, push or publication.

## Minimal standalone conversation importer — 2026-10-11

The user approved this narrow implementation and bounded three-turn validation
after the one-turn full-view probes. Read the repository instructions, M3 plan,
prior status/feasibility and existing observation/session/storage/CLI boundaries.
Used the current checkout; the pre-existing `.DS_Store` change was preserved.

### Delivered behavior

- New `adapters/app_server.py`: standard-library JSONL subprocess transport, exact
  selected UUID, experimental handshake, existing read-only allowlist, no server
  request responses or control operations. Default turn view is `notLoaded`;
  explicit full reads are bounded to ten one-turn pages and 64 KiB total response
  bytes, with timeouts and shutdown. Native response/error/notification bodies are
  never printed. No global discovery, private format parsing or model inference.
- New `adapters/conversations.py`: the two validated originators map to separate
  declared product sources over backend `codex`. Only the observed paginated
  `vscode`/`user` format is accepted. Native conversation identity includes source,
  backend, product and machine scope; canonical task identity stays separate.
  Existing Session/Event contracts hold `codex-conversation-snapshot/v1` snapshots,
  with ordered turns/messages, IDs, original timestamp units, explicit exclusions,
  truncation/missingness and retrieval receipt times. Unknown message times,
  configuration, usage and cost remain null; current thread model fields are dropped.
- Metadata retention is default. Preview/title/path/opaque extras and non-message
  bodies are excluded; full reads discard reasoning/attachments/tool results after
  server retrieval. Only explicit `retain_text` / `--retain-text` stores user and
  assistant text parts. `--read-text` reads text into memory without storing it.
  Storage must be under the workspace's ignored, untracked `.model-learner/`, with
  private directory/database permissions and no symlink paths.
- `Repository.add_session_snapshot` atomically creates a session and immutable
  snapshot. Retained-fact identity excludes receipt time and opaque transport
  cursors; identical fresh replay preserves the first receipt. Changed retained
  facts/view/retention policy append an explicit new snapshot version, with
  collision checks and rollback on failure. Native tools are not manufactured as
  execution lifecycle events. No migration, dependency or lockfile change.
- `import conversation` accepts one selected UUID, source and stable machine ID;
  `session show` reports conversation snapshot coverage and unknowns. README
  documents the exact command and privacy choices. This source remains excluded
  from existing Codex CLI execution projections and real learning builders.
  No task/run/project associations, verified outcomes or observations are generated.

### Actual three-turn validation

Used Python 3.12.14 and Codex CLI 0.162.0-alpha.17.2. Two independent full-view reads
per selection fetched three one-turn pages each, with null final cursors. Every
temporary server exited **0**, as did the validation wrapper. Scoped execution-
sandbox escalation covered the approved processes; private replies stayed inside
Python memory. Only sanitized coverage was emitted; the temporary script was
removed. Metadata snapshots were retained in a private ignored local ledger.

| Coverage | Codex test | Work Local test |
| --- | --- | --- |
| Identities/originators | Validated | Validated |
| Exposed turns/messages | Three unique turns / six unique messages | Same |
| Native ordering | User before assistant in each source-ordered turn | Same |
| Native times | Start/end/duration populated, starts increasing | Same |
| User/assistant bytes by turn | 159/234, 96/464, 117/460 | 159/105, 120/78, 135/144 |
| In-memory text per read | 1,530 bytes | 741 bytes |
| Wire bytes across both reads | 11,712 including handshake/notifications | 9,856 including handshake/notifications |
| Fresh-read text equality | Exact for all six fields | Same |
| Latest-turn lengths vs prior probe | Match | Match |
| First user equals thread preview | No; preview is not an exact baseline | Same |
| Excluded non-message counts by turn | 0 / 1 / 0 | 0 / 0 / 0 |
| Non-text user parts | Zero exposed | Zero exposed |
| Explicit turn truncation marker | None exposed / unknown fidelity | Same |
| First metadata import / replay | One snapshot / zero new snapshots | Same |

The ledger contains exactly two sessions and two metadata snapshots, all message
text/raw fields null. No recovered live string appears in retained canonical event
JSON or SQLite bytes. No task/run/verification/outcome/real-learning row exists.
No live text was stored. This validates client storage, not zero incidental server
startup writes or unknown source/cloud copies. Native paths were not followed.

Complete exposed three-turn history and repeatable text are validated for these
two samples. Original UI equality remains unverified without independent originals;
preview comparison failed. Codex's middle assistant field is 464 bytes in full view,
while the earlier agent reader reported a 460-character maximum; interface coverage
does not resolve original fidelity. Message timestamps, historical configurations,
usage/cost, hidden history/branches and other Work backends remain unestablished.

### Checks and independent review

Added authored sanitized three-turn fixture/fake stdio peer and unit/integration
tests for both sources, exact Unicode/multiline/whitespace text, privacy omission,
opt-in storage, native ordering, null time/resource fields, truncation, bounds,
malformed data/errors, controlled CLI diagnostics, private paths, transactions,
snapshot versioning, fresh replay and learning isolation.

An independent subagent reviewed the implementation and ran **41 focused tests**.
Both review findings were fixed: untrusted type rejection and cursor-independent
snapshot identity. A further independent varying-cursor regression check passed
(**1 passed**); final review reported **no remaining actionable findings**. The
reviewer accessed no live conversation or existing private storage.

| Command | Actual result |
| --- | --- |
| `uv run pytest` | **805 passed, 7 skipped in 48.43s**; optional host/model checks remained disabled. |
| `uv run ruff check .` | Passed; all checks passed. |
| `uv run ruff format --check .` | Passed; 162 files already formatted. |
| `git diff --check` | Passed. |

Used existing repository-local uv/cache paths; no installation was needed. No
global scanning, automatic grouping, routing, Governor, new CPU model, fine-tuning,
cloud inference, commit, push, merge or publication. Stop after the importer.

## CPU conversation semantic task-state demonstration — 2026-10-11

Read the repository instructions, master-plan observation/inference/privacy and
baseline/evaluation semantics, prior status and conversation feasibility evidence.
Reused the current checkout, existing environment and completed importer; preserved
the pre-existing `.DS_Store` change. No dependency, schema, storage, importer or
core architectural change was needed.

### Delivered behavior

- `understanding/conversation_state.py` is a pure CPU, in-memory analyzer over
  opted-in ordered user/assistant messages. Each message checkpoint retains its
  objective hypothesis, positive requirement/revision evidence, removal overlays,
  actor-attributed decision/reversal evidence, issue/progress/completion reports,
  ambiguity and missingness. Exact message character spans support interpretations;
  lexical target links are review candidates, not logical entailment or confidence.
- Original requirement/decision evidence remains alongside removals and revisions.
  The schema explicitly calls these evidence lists, not active resolved requirements.
  Partial list edits/pronouns and implicit scope/task changes remain limitations.
  Reported obstacles are historical statements; later progress does not prove
  independent resolution. Assistant proposals cannot impose user requirements.
- Independent full/partial acceptance sidecars remain outside prose. Completion
  claims never produce verification. Checks must match the exact checkpoint and
  inferred revision with a named artifact/acceptance target. Partial-only checks
  remain visible with unknown completion; contradictions/indeterminate checks stay
  unknown. A failed check is not a failed task. Passes never carry forward to later
  messages. Sidecars are explicit caller attestations, not authenticated verifiers
  or new ledger outcome/observation records.
- Inputs are bounded to 64 KiB text, 128 messages and 256 non-code clauses. Evidence
  and timeline construction use only each available prefix. Real, simulated,
  benchmark and unknown source declarations remain distinct; the live bridge is
  real and authored evaluation/demo inputs are simulated.
- `task conversation-state --text-opt-in` accepts stdin JSON or one exact selected
  live UUID with declared source/machine and the existing executable. No discovery,
  ingestion, file output or automatic persistence. Default stdout omits text/check
  identifiers; separate `--emit-text` authorizes display. Invalid-input diagnostics
  omit private content. Full-view source reads have the existing non-message
  retrieval exclusion and unknown original-fidelity limits.
- `understanding/conversation_evaluation.py` and `learn conversation-state-eval`
  compare a weak keyword baseline, contextual English rules and a dependency-free
  unigram/bigram/role multinomial NB classifier with fixed smoothing/abstention.
  Training uses only separate authored training examples. No embeddings-only
  requirement understanding, optional model load, cloud inference or routing.
- `docs/CONVERSATION_TASK_STATE.md`, README and authored simulated fixtures provide
  executable examples, timelines, evaluation/reference reports and limitations.
  The synthetic end-to-end demo covers a genuine streaming-to-buffered reversal
  and a synthetic independent acceptance check. It is not real verified evidence.

### Actual selected demonstrations

The existing exact-ID importer performed bounded full reads of the two approved
samples. The ordinary sandbox initialization failed as before; reviewed escalation
allowed the bounded existing read-only subprocess. It sent only the existing
handshake/history allowlist. Both again exposed three turns and six ordered
user/assistant messages; temporary servers exited 0. Live transcript strings and
derived state stayed in Python memory. Sanitized signal/count summaries were
printed; no native identifiers, excerpts, real transcript fixtures or semantic
snapshots were retained. Existing private metadata storage was not ingested into
or modified by the analysis code.

- **CSV:** initial parser objective and ordinary comma-field requirement recognized;
  quoted-comma support added at turn 2 and multiline quoted-field support at turn 3.
  One user issue report is recognized. Six uncertainty entries remain after turn 3.
  The final analysis took about **0.47 ms**, excluding retrieval, on 1,530 bytes.
- **Work Local:** the initial objective wording is **not recognized**. A constraint
  is extracted; FIFO exclusion is recognized but its initial target is unresolved.
  The last turn identifies remaining round-robin/shortest-job scope and user plus
  assistant incompletion reports. Seven uncertainty entries remain after turn 3.
  The final analysis took about **1.49 ms**, excluding retrieval, on 741 bytes.
- Both have zero independent check inputs and verification stays **unknown** at
  every checkpoint. No explicit progress report, decision or completion claim is
  recognized under these cues; that does not establish absence of real progress.
  Original UI fidelity, hidden history and original message times remain unknown.
  Warm timing observations and these two examples do not establish generalization.

### Evaluation actually established

`tests/fixtures/conversation_state/evaluation.json` has **52 training examples** and
**23 separate varied evaluation conversations / 54 manually specified intent
labels**, plus expected final-state signatures. Cases cover additions, removals,
revisions, genuine decision reversals, task switches, failed attempts, unresolved
work, independent full/partial verification, completion claims,
negation, planned progress, ambiguity and unresolved references. Labels were
manually specified by the implementing agent, not independently by human annotators.

| Variant | Intent accuracy | Macro F1 on present labels | Matching final signatures |
| --- | --- | --- | --- |
| Keyword baseline | 40/54 (74.1%) | 0.502 | 14/23 |
| Contextual rules — selected | 51/54 (94.4%) | 0.925 | 20/23 |
| Naive Bayes | 36/54 (66.7%) | 0.599 | 9/23 |

The first rule run scored 48/54; fixture/demo inspection exposed a quotation cue
mistaking quoted fields for indirect claims, missing objective phrasing and a
constraint mistaken for objective. Those defects were corrected. Independent
review found an example that repeated a choice instead of reversing it; corrected
SQLite-to-PostgreSQL/streaming-to-buffered examples and regenerated the reference.
Intent/final-state labels and NB training/features/margin were unchanged. This is
therefore a **diagnostic regression set**, not an untouched held-out evaluation.
No statistical improvement or generalized semantic understanding is established.

The rules still miss an implicit accessibility requirement, an implicit task switch
and ambiguous short approval. NB adds false scope changes, planned-progress and
indirect-success errors. The report includes per-case errors, confusion/category
counts, per-field agreement, dataset digest and actual CPU timing. Final signatures
measure evidence message positions and selected state fields, not fully normalized
logical requirements, link-target accuracy, all intermediate states or real success.
The reproducible checked-in reference excludes volatile elapsed fields.

### Checks and independent review

Used existing Python 3.12.14 / uv environment with repository-local cache and
`UV_NO_SYNC=1` to preserve installed optional capabilities. No model runtime was
needed; existing optional model/host checks remained disabled.

| Executed check | Actual result |
| --- | --- |
| `uv run pytest` | **840 passed, 7 skipped in 48.47s**. Existing optional model/host checks skipped. |
| Final focused unit/CLI suite after review fixture correction | **35 passed in 0.65s**. |
| Independent final focused suite | **35 passed in 0.56s**. |
| `uv run ruff check .` | Passed; all checks passed. |
| `uv run ruff format --check .` | Passed; 169 files already formatted. |
| `git diff --check` | Passed. |
| Installed CPU demo/evaluation commands | Exit 0; authored simulated timeline and references reproduced. |

Coverage includes source attribution, scope overlays/links, negation, conditional
and quoted ambiguity, fenced-code exclusion, input bounds, future/prefix isolation,
verification invalidation/conflicts/partial coverage, content-free errors, default
redaction, explicit display, no retained files, existing fake-stdio bridge, actual
synthetic demo, no network fitting and exact evaluation reference reproduction.
Independent review requested changes to stale/partial verification visibility,
input clause bounds, fixture validation and true reversal coverage; all were fixed.
Final independent review reports **no remaining actionable findings** and accessed
no private conversations or ignored storage. Software review is not human labeling.

The next evidence step would be separately authorized genuine independent human
labels and an untouched, more diverse evaluation, plus better objective/reference
resolution if requested. None is started. The existing pending human-review batch
and earlier prospective-summary pilot remain untouched. No ingestion expansion,
model routing, Governor, paid agent, cloud inference, commit, push, merge or
publication. Stopped after the requested demonstration and evaluation.

## Known issues / blockers

- Independent synthetic holdouts expose substantial semantic objective/change/
  decision failures. The bounded fixes show no broad recognition gain on untouched
  examples. Trusted semantic utility integration remains unsupported; eligible
  paired real conversation-prefix/outcome data is not demonstrated.
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
- The execution-event importer supports explicitly selected Codex CLI streams only;
  passive desktop capture remains unsupported.
  Bounded selected agent-mediated reads of both Desktop and Work Local tests are
  now validated. Independent stdio selected thread/turn metadata access is also
  validated. The standalone selected-ID importer now validates all three exposed
  turns and six user/assistant messages for each approved sample. Metadata-only
  live storage and fresh replay are checked. Original UI verbatim fidelity, hidden
  history completeness, historical measurements and other backends remain unverified.
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

- Latest request: private selected-real-conversation reports are produced, with
  explicit incomplete evaluation due to existing importer/analyzer bounds. Next
  unstarted step requires separate direction for a supported bounded strategy
  covering rejected text reads and the unsupported final prefix, followed by
  human adjudication. Independent outcome integration remains unstarted. No
  limits, rules, models or estimators were changed.

- Latest request: frozen semantic baseline and independent holdout evaluation,
  scheduling root cause, bounded corrections and untouched reevaluation are
  complete. Full checks and independent review passed. Next recommendation:
  human-adjudicated prospective prefixes, conservative reported-signal validation,
  and independent outcomes with checkpoint/attempt receipts before any predictive
  comparison or trusted utility integration. Await separate instruction; no next
  milestone is started. Earlier recommendations are historical.

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

## Focused conversation task-state holdout evaluation — 2026-10-12

Read MODEL_LEARNER_PLAN.md, AGENTS.md, STATUS.md and the conversation task-state
methodology/implementation before edits. Kept observation, inference and outcomes
separate; no estimator, ingestion, contract, migration, dependency, routing or
Governor change. The pre-existing `.DS_Store` change remains untouched.

### Frozen baseline and independent reference labeling

- Archived original rules/state logic, diagnostic evaluator, dataset and reference
  in `tests/fixtures/conversation_state/frozen_v1/`, with SHA-256 manifest, runtime
  and NB/default-rule configuration. Before any rule edits, original keyword/rule/
  NB results reproduced exactly: **40/54, 51/54, 36/54**, final states
  **14/23, 20/23, 9/23**. Archive replay tests bind its evaluator imports to archived
  rules, avoiding mutable-production imports. Existing diagnostic files unchanged.
- Confirmed original evaluation leakage: shared agent/cue authorship, inspected
  examples and fixture corrections during development; final-state scores omitted
  intermediate states, logical scope and target links. This was not a holdout.
- A separate agent with no inherited conversation context authored/froze labels
  without implementation, previous examples or predictions: **12 scenarios /
  63 messages / 85 events**. A different independent agent audited the scorer,
  freeze, metric semantics and reported artifacts. No human annotation is claimed.
- Frozen baseline ran on the first set before implementation changed. Only then
  two bounded corrections were made and revision hash frozen. The blind author
  independently produced **8 untouched scenarios / 38 messages / 46 events**;
  both archived and revised rules were evaluated. A later **1 untouched scenario /
  6 messages / 8 events** closes explicit removal/reinstatement coverage. Neither
  earlier set nor its labels was modified. No later rule tuning occurred.
- `understanding/conversation_holdout.py` is a small pure synthetic scoring/replay
  module, runnable with `python -m`; it adds no CLI infrastructure or persistence.
  Scores span-aligned events, intermediate objective/verification state, all target
  candidate edges, completion, uncertainty and subtype-tolerant supplemental
  recognition. Invalid references fail; missing denominators are null.

### Actual results and failures

| Measurement | Frozen first 12 | Frozen untouched 8 | Revised untouched 8 |
| --- | --- | --- | --- |
| Explicit opening objectives | **5/11** | **3/7** | **3/7** |
| Objective checkpoint agreement | **27/63** | **14/38** | **14/38** |
| Typed requirement precision / recall | **13/18 / 13/23** | **5/6 / 5/10** | **5/6 / 5/10** |
| Subtype-tolerant requirement detection | **15/18 / 15/23** | **5/6 / 5/10** | **5/6 / 5/10** |
| Typed decision precision / recall | **2/6 / 2/8** | **0/2 / 0/3** | **0/2 / 0/3** |
| Decision reversal recall | **1/2** | **0/1** | **0/1** |
| Typed change false positives / misses | **9 / 18** | **3 / 10** | **3 / 10** |
| Task-switch recall | **0/2** | **0/2** | **0/2** |
| Semantic target precision / recall | **3/8 / 3/7** | **null / 0/4** | **null / 0/4** |
| Source-span / actor integrity | **81/81** | **47/47** | **47/47** |
| Completion recall / false claims | **7/10 / 0** | **4/5 / 0** | **4/5 / 0** |
| Verification checkpoint agreement | **62/63** | **38/38** | **38/38** |
| False verified claims | **0** | **0** | **0** |
| Required uncertainty coverage | **1/2** | **2/2** | **2/2** |

The first-set revision improves required uncertainty from **1/2 to 2/2**, while
recognition metrics remain unchanged. This is diagnostic, after inspection.
All untouched eight-case metrics are identical across versions: **no broad
recognition gain demonstrated**. The additional reinstatement case also has
identical results: opening objective **0/1**, typed requirements **1/2 precision /
1/3 recall**, subtype-tolerant edits **2/2 precision / 2/3 recall**; the actual
reinstatement is missed. No false completion/verification claims; **6/6**
verification checkpoints agree. Small curated sets are not a real population
estimate, and dependent checkpoints are not independent accuracy trials.

Concrete failures include missing “Help me organize …”, treating “could use …” as
a decision, merging “Now make …” into old scope, missing failed-attempt and
unresolved paraphrases, over-abstaining on indirect requests and ordinary “example”
wording, missing natural changed decisions, and unresolved concurrent-task identity.
Evidence boundaries are intact, but that does not establish semantic correctness.

Scoring artifacts are preserved/documented in
`docs/CONVERSATION_TASK_STATE_HOLDOUT.md`: one first-set reference expects
verification to persist after a thanks, contrary to the exact-checkpoint contract;
latest-paraphrase objective provenance differs from initial-source retention;
addition/revision subtypes are arguable in two cases; same-span reversal/choice
labels duplicate two decision regions. Supplemental decision-region detection is
**2/6 precision / 2/6 recall**. Strict ambiguous-act agreement is **0/6 precision /
0/1 recall** in the first set and **0/2 / 0/1** in the untouched eight, but assistant
clarification questions and unparsed-user uncertainty are separate policy issues.
No labels were corrected against predictions. No verification semantics changed.

Independent scorer review found one emitted ordinary-decision edge omitted from
target precision. The original `holdout_v1_baseline.json` remains preserved;
`holdout_v1_baseline_audited.json` counts all edges and exact matched target
identity (**3/8**, not initial **3/7** precision), with unchanged model predictions.
Freeze manifests distinguish the original and audited scorer digests. Reviewed
revised/post/supplement reports and all synthetic references are retained separately.

### Scheduling investigation and narrow improvements

Used only the supplied scheduling sentence, not the private original. Frozen rules
preserve the entire **92-character** clause, classify it `other`, and consequently
leave objective unknown. `research` is recognized but `researching` is absent under
a word-boundary regex; there is no threshold in that path. Synthetic importer
bridge evidence preserves the same text exactly. The reference objective is
explicit. This isolates an extraction defect for intact input; original source
fidelity/missing text cannot be fully excluded without an approved fresh read.

Added progressive forms of existing objective verbs and explicit uncertainty when
more than one lexical candidate could be a removal/revision/reversal target.
Retained original evidence and candidate links; selected no target and added no
logical scope solver. Question/conditional/assistant guards remain tested. Known
supplied wording now establishes an objective with verification unknown. No
conversation-specific algorithm rule or broader cue fitting was introduced.

### Integration assessment and stopping point

- Useful future candidates: actor-separated reported obstacle/progress/scope
  signals, objective availability and coverage/uncertainty masks, with exact source
  spans for audit. They remain inferred reports. Active scope, automatic task
  identity, definitive links, semantic difficulty and inferred success are too
  unreliable. Missing data stays null plus an explicit reason/mask; a recognized
  count of zero is not proof of zero real events. Final outcome/checks must not
  leak into earlier predictors.
- Associate prospective prefixes with explicit Task/Run/Attempt, acceptance
  version and availability receipts. Source turn order is not an execution attempt
  boundary; current conversation segments create no ledger associations. Exclude
  ambiguous multiple-task or mixed-configuration attribution.
- Existing synthetic outcomes and `learn.task_state` can exercise plumbing and
  controlled ablation, not establish real semantic benefit. Recorded prior audit
  has one verified fixed-reply smoke observation and no suitable real longitudinal
  coding trajectories; selected conversations have no independently verified
  outcomes or run associations. No new private datastore or historical conversation
  enumeration occurred. Sufficient eligible paired real prefix/outcome data is
  **not demonstrated**, so no predictive model was fitted or gain claimed.
- Next recommendation, **unstarted**: human-adjudicate a small explicit prospective
  selection, resolve label policy, verify a conservative reported-signal subset on
  another frozen semantic set, and collect independent artifacts/outcomes with
  checkpoint/attempt receipts. With adequate paired labels, use the existing
  chronological metadata-versus-semantic-subset comparison and identical cohort/
  cutoffs; default floors are 30 training and 20 scored labels, five task clusters
  per split and both training classes, not a power guarantee. No larger neural
  network is justified yet. Stop after this evaluation/recommendation.

### Actual checks and review

Existing macOS arm64 Python **3.12.14**, Pydantic **2.14.0**, uv-managed environment;
used repository-local `UV_CACHE_DIR` and `uv run --no-sync` to preserve installed
optional capabilities. No installation, model download, cloud or paid execution.

| Executed check | Actual result |
| --- | --- |
| Frozen original diagnostic execution before implementation edits | Exact equality with original reference; baseline results above. |
| Focused new scorer tests before corrections | **7 passed in 0.13s**. |
| Focused scorer/analyzer/CLI suite after corrections | **57 passed in 1.06s**. |
| Final new holdout regression suite | **25 passed in 0.13s**. |
| `uv run --no-sync pytest` | **865 passed, 7 skipped in 50.49s**. Existing model/host opt-in tests skipped. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 174 files already formatted. |
| `git diff --check` | Passed; no whitespace errors. |
| Independent initial scorer/freeze audit | Reproduced baseline/reference and hashes; focused **37 passed**. Target-edge issue corrected, other artifacts documented. |
| Independent final code/evaluation review | **60 focused tests passed in 0.91s**, whole-repo Ruff/format/diff clean; source/dataset/scorer freezes and all six audited reports reproduced. No actionable blockers. Reviewer did not rerun the full suite. |

Changes are limited to the two source corrections, focused synthetic evaluator,
freeze/holdout/report artifacts, meaningful regression tests, this status and
linked evaluation documentation. Existing observation/probabilistic estimators
remain unchanged. No commit, push, merge, publication or later milestone started.

## First selected real-conversation evaluation reports — 2026-10-12

Read AGENTS.md, the existing status, M3/M4 plan semantics and the conversation
importer/task-state/holdout documentation. Used the current checkout, preserving
the pre-existing `.DS_Store` modification. Read only the four user-selected IDs
through the supported standalone `AppServerClient` / `read_conversation`; no
history enumeration, desktop reader fallback, private storage parsing or project
artifact/test-result access. Selected identifiers, titles, message excerpts and
semantic snapshots remain exclusively in ignored private local storage.

### Freeze and privacy

- Saved the current production analyzer and importer source copies, SHA-256
  digests, Git/runtime versions, default rule configuration and source selection
  before analysis. The original historical baseline archive is not substituted
  for the current analyzer. No source, classifier, limit, dependency or model edit.
- Processed opted-in extracted user/assistant text in Python memory. Full item
  retrieval receives other content before local exclusion; non-message bodies
  never reach semantic inference. No raw response, full transcript, preview,
  attachment body, tool result or unnecessary assistant prose was persisted.
- Saved immutable predictions, input/prediction hashes and version bindings before
  rendering or reviewing reports. No selected reference labels or independent
  project verification results were inspected before or after freezing. Only
  supporting semantic/uncertainty excerpts and source metadata are retained.
- Private artifacts include four source-specific prediction/coverage reports,
  aggregate coverage and transition summary, human-interpretation queue,
  limitations and a file-hash manifest under `.model-learner/`. Directories/files
  have private permissions and every artifact is Git-ignored. Nothing is committed.

### Actual coverage and incomplete evaluation

The rows below are anonymized selection positions, not invented task identities.

| Selection | Successful source coverage | Semantic coverage / gate |
| --- | --- | --- |
| Codex A | Metadata-only: 3 native turns, cursor exhausted; message count unknown | Full-view read rejected after 67,887 wire bytes crossed 65,536; no predictions. Metadata fallback: 3,874 bytes. |
| Codex B | Metadata-only: 4 native turns, cursor exhausted; message count unknown | Full-view read rejected after 69,123 wire bytes crossed 65,536; no predictions. Metadata fallback: 4,078 bytes. |
| Codex C | 4 native turns, 12 messages, 4 user messages; 35,482 wire bytes / 6,372 extracted text bytes | All 12 messages and 4 user turns analyzed. |
| Work Local D | 4 native turns, 11 messages, 4 user messages; 52,058 wire bytes / 20,417 extracted text bytes | First 9 messages / 3 user turns analyzed; fourth user's prefix has 261 clauses, full input 297, above 256. |

Every successful read validates the selected product originator and Codex backend,
preserves reversed descending turn pages and original item order, and exhausts
exposed cursors. This does not prove complete original history, hidden branches or
UI fidelity. Source truncation flags remain null/not emitted; application-bound
rejections are reported separately. Message timestamps, historical model/settings,
tokens and cost remain unknown. Native thread/turn time fields are retained as
source history metadata; retrieval receipts are not execution timestamps.
Non-message item counts for the two full-view successful reads are 19 and 17;
their bodies were excluded. Such counts are not reconstructed tool telemetry.

The initial sandboxed server exited 1 before any selected read. Scoped execution
permission enabled the same bounded process; successful temporary servers exited
0. A private report-writing mapping error interrupted the batch after one source's
predictions were saved. It was repaired, and the repeated selected read confirmed
identical input/predictions without replacing that original freeze. The Work
source was reread only to capture coverage and freeze admissible original prefixes
after its full analysis failed. No message/clause clipping or summarization was
used to evade the bounds; later checkpoints are explicitly unavailable.

### Reported transitions and interpretation limits

- The completely analyzed source never establishes an objective: it recognizes
  3 added-requirement facts, 4 decision facts, 2 failure reports, 5 progress reports
  and 7 completion claims. Two completion claims are user-attributed and five
  assistant-attributed. Its final positive evidence includes the two user decisions,
  for 5 requirement evidence entries; these are not normalized active requirements.
- The partial Work source establishes an initial objective and retains it through
  the analyzed prefix. It recognizes 2 removals, 1 addition, 1 revision, 7 decisions,
  1 unresolved report, 2 progress reports and 3 assistant completion claims.
  Two scope edits have unresolved target links. The fourth user turn has no state
  prediction and is not silently assigned the earlier scope.
- Neither analyzed source recognizes a decision reversal or task switch. This is
  a detection count, not proof of absence. Unparsed/ambiguous statements, missing
  objectives, candidate targets, proposed versus accepted assistant choices, and
  instruction/status-example versus event-report distinctions require human review.
- All **21 available message checkpoints** have `verification=unknown` and zero
  independent check inputs. Assistant statements about tests/completion never
  become verified outcomes. User-reported status is not independent verification.
- Per-user-turn reports distinguish request-prefix state from subsequent assistant
  response state, preserving cumulative evidence and exact message/character spans.
  Blocked sources expose only native-turn coverage slots; no user turns, objectives
  or semantic zeros are fabricated from metadata. No human labels, accuracy scores,
  causal claims or real predictive benefit are established.

### Actual checks and stopping point

Existing Python 3.12.14 / uv-managed environment; used repository-local uv/cache
paths and `--no-sync`. No installation, paid execution, network inference or model
download. Model Learner's own regression tests are separate from independent tests
of the selected projects and do not supply semantic inputs or project outcomes.

| Executed check | Actual result |
| --- | --- |
| `uv run --no-sync pytest` | **865 passed, 7 skipped in 46.49s**; existing opt-in host/model checks skipped. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 174 files already formatted. |
| Private artifact integrity/privacy check | Passed: manifest and prediction hashes, unchanged source hashes, private permissions, Git ignore, source-role/turn/span references, no raw text in prediction/metadata snapshots and unknown verification. |

Reports are produced; full requested semantic evaluation remains incomplete under
the supported bounds. Next unstarted step: separate direction for a supported
bounded strategy covering both rejected text reads and the final Work prefix,
then human adjudication. No rules/models were tuned, no estimators connected,
and no Task/Run/Attempt associations, execution telemetry or historical model
attribution were invented. No outcome integration, commit, push, merge, publication
or subsequent milestone. Stop after these reports.


## Selected-input coverage recovery — 2026-10-12

Read repository instructions/status, relevant M3/M4 provenance semantics,
conversation task-state/holdout/importer documentation and prior selected-report
metadata. Preserved the pre-existing `.DS_Store` modification and prior STATUS
content. Implemented only input selection/coverage reporting in
`understanding/conversation_projection.py`, five regressions reusing existing
fixtures, and `docs/CONVERSATION_INPUT_PROJECTION.md`. No new semantic evaluation
conversation or reference label. Production analyzer/importer/transport source
hashes exactly match the original private evaluation freeze.

### Privacy and deterministic freeze

Requested and received explicit approval for one bounded reread of only the same
four IDs: temporary read-only App Server, ten one-turn pages, at most 256 KiB
cumulative transport per source. The diagnostic runner loads unchanged transport
code in an isolated module namespace with the approved byte allowance; production
64-KiB default and importer extracted-text bounds stay unchanged. No discovery,
related conversation, datastore, project artifact or independent outcome access.
Full-item responses are received before local non-message exclusion; only numeric
item-type/count/byte statistics survive. No private text/raw response/excerpt is
printed or retained. Native source mapping and text-free predictions are private
under ignored `.model-learner/projected-real-evaluation-20261012/`, with 0700/0600
permissions and exclusive artifact writes. Original artifacts remain immutable.

Policy/helper/runner hashes and original manifest digest froze before the read or
prediction evaluation. Each source's predictions/hash/input digest froze before
comparison to old predictions. No human labels or independent project checks were
inspected before or after freeze. No classifier tuning, new model, estimator,
Governor, canonical task association, outcome inference or verified claim.

### Actual diagnosis and recovered coverage

| Original selection | User messages / UTF-8 bytes / clauses | Assistant messages / bytes / clauses | Actual wire bytes | Projected user checkpoints |
| --- | --- | --- | --- | --- |
| Codex A | 3 / 1,326 / 30 | 9 / 3,247 / 48 | 93,795 | 3/3 |
| Codex B | 4 / 1,272 / 28 | 10 / 4,366 / 62 | 110,337 | 4/4 |
| Codex C | 4 / 1,791 / 44 | 8 / 4,581 / 59 | 35,482 | 4/4 |
| Work Local D | 4 / 1,578 / 37 | 7 / 18,839 / 260 | 52,058 | 4/4 |

All temporary servers exited 0 and exposed pagination exhausted. That does not
prove complete original history or UI fidelity; truncation markers were not
emitted. No text, clause, message-count or per-message-character limit was reached
in any projected user prefix or any of 34 separate whole-assistant-message reads.
No arbitrary truncation, summarization or omitted user requirements/decisions.

A/B exceeded original transport bounds because command/file-change items dominate
wire input. Compact reserialized command/file item bytes were 53,899/27,203 for A
and 64,876/29,698 for B; whole extracted message text was only 4,573/5,638 bytes.
Documented per-item metrics distinguish reserialized sizes from exact wire bytes.
All source message IDs are unique, bridge strings equal source-part newline joins,
and joining expansion is zero in all four sources. No parsing duplication,
normalization or lexical expansion. Source-authored repetition is not excluded.

D's fourth user text is 246 bytes/6 clauses; the prior full prefix already has 255
clauses and rises to 261. Three earlier assistant messages contribute 15,808 bytes
and 218 clauses. All four user messages together have 37 clauses, recovering the
fourth checkpoint without processing those explanations as task-intent input.
The original complete full-input total is 297 clauses. Short clause distributions
are recorded, and no clause splitting rule was modified.

### Predictions and limits

- Frozen policy: every unchanged user message in source order, every full user
  prefix, original native IDs/item ordinals/turns/full-message evidence-span mapping.
  Checkpoints list included users, omitted assistants, bounds and available versus
  unavailable fields. Assistant reports are analyzed separately per whole message,
  with no cumulative execution state. Independent evidence stays null/unavailable.
- Final user intent counts (add/revise/remove; decision/reversal): A 10/1/0 and 1/0;
  B 3/0/0 and 2/0; C 3/0/0 and 2/0; D 3/1/2 and 2/0. Objectives are recognized
  only for B/D. A/C remain unknown; many clauses remain other/ambiguous. No detected
  reversal/task switch is a recognition count, not proof of absence.
- Separate assistant reported progress/completion counts: A 2/4, B 5/5, C 4/5,
  D 4/3. Test results have no dedicated field in this frozen analyzer; these reports
  never become independent execution checks or outcomes. All 49 analyzed
  user-prefix/assistant-message endpoints have verification unknown.
- User-clause classifications agree with original frozen predictions on 44/44
  shared C clauses and 31/31 shared D clauses. This is reproducibility, not accuracy.
  A/B have no original semantic baseline; D's fourth user is newly covered.
- C loses one candidate user-decision link to an omitted assistant decision.
  D's overlapping user candidate links are unchanged, but one removal and one
  revision target remain unresolved. Original full-text predictions stay separate;
  no projected output is relabeled as the historical baseline.
- Short approvals, implicit requirements/objectives, instruction/status-example
  versus event reports, proposed versus accepted assistant decisions, lexical
  targets and cross-message context need human adjudication. Missing independent
  checks, execution histories, historical settings/cost, source fidelity and task/
  run associations remain unknown. No semantic accuracy score is supported.

Recommendation: useful enough for human-adjudicated semantic review of the same
selected sources with both views and original references. Freeze the adjudication
policy before reviewing. Not ready as trusted success/utility features. Human
adjudication, outcome integration and all later milestones remain unstarted.

### Actual checks and independent review

Existing Python 3.12.14 environment; repository-local uv cache and `--no-sync`.
No installs, cloud inference or model downloads.

| Executed check | Actual result |
| --- | --- |
| Focused projection/analyzer/importer tests | 57 passed in 0.20s. |
| `uv run --no-sync pytest` | 870 passed, 7 existing opt-in skips in 51.54s. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 177 files already formatted. |
| `git diff --check` | Passed. |
| Freeze/private artifact integrity | Source hashes, original manifest, prediction digests, exact source mappings, no retained message text, unknown verification and ignored private permissions checked. |
| Independent code/report review | No actionable defects; 5 projection tests and Ruff lint/format passed. Numeric totals and omission/baseline qualifications reviewed. One turn-number wording correction applied. Reviewer read no private artifacts/labels/outcomes and did not rerun the full suite. |

Stop after this evaluation and recommendations. No commit, push, merge,
publication or later milestone started.

## Blind human-adjudication worksheet — 2026-10-12

Phase 1 only. Read repository instructions and the requested conversation-state,
holdout and input-projection documentation. Existing approved evaluation data
omitted full original message text, so requested and received explicit permission
to reread only the same four selections: at most ten one-turn pages and 256 KiB
cumulative transport per conversation, retaining user text only in ignored local
storage. The initial sandboxed attempt failed with a content-free diagnostic;
the scoped approved run succeeded and all four temporary servers exited 0.

Created one Markdown worksheet under ignored `.model-learner/annotations/`.
It contains 3, 4, 4 and 4 unchanged user messages, native message/evidence IDs,
conversation IDs and original turn/message/item positions. All ten annotation
fields per message are blank; multiple entries and earlier requirement/decision
references are supported. No predictions, reference labels or AI interpretations
are included. No assistant prose, tool body, preview or raw response was retained.
Original text is the unchanged source-part newline join. Chronological ordering
uses native turn-start metadata across conversations and preserves source order
within each conversation. Exact message timestamps, hidden history and original
UI fidelity remain unknown and are described in the worksheet.

The one-off preparation script reused the existing read-only importer and an
isolated transport module with the explicitly approved 256-KiB allowance. No
production source or default was edited, and the semantic analyzer was never
loaded or run. Frozen evaluation/prediction artifacts were not opened; metadata-
only inode/size/mtime/mode checks confirmed both existing artifact trees stayed
unchanged. No labeling, prediction comparison, tuning, training or outcome
integration occurred. Private output directory/file permissions are 0700/0600.
The temporary preparation script was removed after validation.

| Check | Actual result |
| --- | --- |
| Bounded selected-source reads | All four completed within the approved bounds; exposed cursors exhausted. |
| Worksheet structural/text verification | 15 distinct native message IDs, exact rendered text round-trips, 150 blank annotation fields, source order preserved; user text byte totals match the documented source totals. |
| Privacy and unchanged-artifact checks | Output Git-ignored, private permissions confirmed, no private contents printed; existing evaluation artifact metadata unchanged. |
| Preparation-script Ruff | Passed after formatting and correcting long lines; collector was not rerun. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 177 files already formatted. |

No pytest run: this task changes only a private worksheet and this status note;
relevant validation is the source/text/order/blinding verification above. No
implementation milestone started. Stop with the worksheet ready. Genuine human
annotation is pending; Phase 2 comparison requires separate user authorization.

## Frozen prediction / independent AI-reference comparison — 2026-10-12

The user separately authorized comparison against completed independent Work
annotations. Read AGENTS, status and conversation task-state/holdout/projection
documentation; used only existing private artifacts and the earlier blank source
worksheet. No conversation retrieval, analyzer import/execution, implementation,
rule tuning, training, model download or outcome/utility/Governor integration.
The AI annotations remain explicitly distinct from human-adjudicated truth.

Delivered a detailed private report, reproducible matching ledger, input/hash
inventory, validation evidence and independent methodology review under ignored
`.model-learner/`. No private text, annotations, native IDs or per-conversation
interpretations were added to tracked files. Both original result sets retain
their bytes, size and modification timestamps. The prediction manifest's 20
entries, original source hashes and projection hash validate unchanged. Native
message IDs, source positions, complete user-prefix order and unchanged worksheet
text align for 15/15 messages; all 150 reference cells are populated. All 139
unique new user-fact spans validate. Local freeze receipts predate the annotation
file; blindness is supported by attestations, not an authenticated audit of when
annotation began. Assistant context and independent execution evidence remain
unavailable.

Measurements use explicit post-hoc atomization, semantic equivalence and disclosed
same-message contextual matching. They separate new events from cumulative state,
incomplete/missing predictions from incorrect events, unsupported representations
from misses, and annotation-policy overlap from distinct changes. They do not
collapse 150 cells into one accuracy score:

- Current core-action objective agreement: **3/15**; broader topic compatibility
  separately **8/15**.
- Typed positive-obligation alignment: **21/24** normalized predicted semantic
  units and **21/84** reference obligations. Raw fragment alignment is **21/25**;
  the extra unit is an adjacent duplicate fragment, not a semantic false positive.
  Alternative positive evidence covers **32/84** obligations.
- Choice-content alignment: **6/8** predicted units and **6/28** reference choices;
  explicit reversal recall **0/2**, with precision unavailable at **0/0**.
- Narrow supported-operation scope-change alignment: **2/3** predicted changes
  and **2/5** reference transitions. The broader reference revision policy is not
  directly comparable; unsupported reinstatement has no semantic precision/recall.
- Native-message attribution of matched obligations: **32/32**, distinct from
  semantic target-link agreement. The one emitted user scope-target candidate is
  unsupported (**0/1**). Source traceability is not semantic correctness.
- Nominal field mappings: **135/150**, including partial mappings; descriptive
  nonempty field presence **49/150**. Neither is accuracy. Full active-scope,
  unresolved-work inventory and semantic uncertainty agreement are unavailable.

The report documents every message's substantive disagreements and evidence,
five ranked human-review priorities, representation limits and a minimal next
experiment. Rules can support an inspectable evidence-review subset; they do not
reliably resolve task scope, temporal changes or speech acts. Recommended next
step, unstarted: human adjudication/policy freeze, then a separately authorized
bounded local semantic-extractor comparison with this baseline unchanged. New
blind cases are needed for any subsequent generalization claim. No predictive
utility improvement is claimed and no semantic features enter outcome estimators.

| Executed check | Actual result |
| --- | --- |
| Read-only comparison artifact validation | Passed: unchanged inputs/source hashes, 15 native IDs, 150 cells, 139 facts, turn ordering, metric sums, table structure, private permissions and Git ignore. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 177 files already formatted. |
| Explicit private report-script Ruff checks | Passed; four scripts lint-clean and formatted. Initial local script formatting/lint issues were repaired without changing either input set. |
| `git diff --check` | Passed. |
| Independent methodology/ledger/report review | Accepted after distinguishing duplicate fragments, unsupported reinstatement and topic versus objective agreement; numeric sums, source mappings and hashes independently checked. No remaining substantive blockers. |

No pytest run: there is no implementation change, and this task explicitly forbids
rerunning the analyzer. Artifact validation is the relevant test and invokes no
analyzer code. Pre-existing working-tree changes are preserved. No commit, push,
merge or publication. Stop after the private comparison report; no next experiment
or milestone started.


## Git repository privacy/security audit — 2026-10-13

Completed the explicitly requested audit and safe preventive implementation only.
Read the repository instructions/status/plan privacy sections, README, ignore rules
and existing benchmark/observation privacy guidance. Initial state: main, 233
tracked files, zero staged changes and one modified Finder metadata file. Locally
available history: 28 refs, 25 reachable commits, 233 historical paths, 339 unique
blobs, 343 path/blob/mode combinations and 7,312,448 bytes. Every reachable blob
and commit metadata was locally scanned without emitting secret or transcript
contents. No historical-only deleted paths, special index modes or LFS pointers.
No high-confidence credentials or raw private transcripts confirmed. Broad
conversation/credential-canary matches were resolved through fixture provenance
and source context; existing real sanitized smoke metadata remains distinct from
simulated fixtures.

Two findings: tracked `.DS_Store` in two historical versions, and one identifying
absolute home-path reference in public developer documentation. Both are reachable
from cached origin history; live GitHub exposure/public visibility was not checked.
Finder metadata is removed from the index only; its modified local bytes, size and
mtime are unchanged. The public documentation prefix is now portable. Earlier
copies remain in Git history. No rotation indicated by the detected findings;
optional historical cleanup needs separate approval and human metadata-risk review.

Delivered strengthened ignores, a standard-library actual-index/committed-tree
privacy guard, 17 exact reviewed fixture digests, executable versioned pre-commit
hook, push/PR GitHub CI workflow, permanent AGENTS policy, developer instructions
and sanitized report in `docs/REPOSITORY_PRIVACY.md`. Local hooksPath is activated
as `.githooks`; no global Git settings changed. Hook/CI failures propagate nonzero.
Tests run only harmless synthetic fixtures in isolated temporary repositories.
They demonstrate path/content rejection, force-add protection, real staged bytes,
index policy provenance, safe source/docs/fixtures, nonleaking diagnostics, local
preservation, unusual names, hook and committed-tree enforcement, fail-closed
special/large/invalid entries, and replacement-object resistance.

| Executed check | Actual result |
| --- | --- |
| Local object/history inventory and content scan | 25 commits / 339 unique blobs inspected; no detected credentials; two sanitized hygiene/privacy findings. No fetch or external scanning. |
| `uv run --no-sync pytest` | 927 passed, 7 existing opt-in skips in 90.74 s. Collected before the final two guard regressions; final affected tests rerun below. Includes concurrently present unrelated experiment tests. |
| Final `uv run --no-sync pytest tests/integration/test_privacy_guard.py -q` | 55 passed in 10.28 s. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 188 files already formatted. |
| `git diff --check` and `git diff --cached --check` | Passed. |
| Scoped proposed index and tree, isolated temporary index/object store | 238 entries inspected, zero rejections in both modes; no implementation files staged in the actual checkout. |
| Actual index / hook state | Only `.DS_Store` deletion staged; hook active. Until reviewed policy is staged, guard rejects 17 existing session-format fixtures as expected. |
| Independent security review and recheck | Reproduced replacement-ref bypass; fixed every Git reader and added index/tree regression. Proposed-tree source-field false positive corrected with structural JSON parsing and acceptance regression. Final independent 55-test/Ruff recheck passed; no remaining blockers. |

Existing environment/cache used; no dependency installations or AI calls. The
initial uv invocation could not access its default out-of-workspace cache; reran
successfully with the existing repository-local `.uv-cache`. A non-UTF-8 filename
creation test hit a local filesystem restriction; its final test exercises Git's
index directly, without weakening filename handling. No private datasets deleted,
private data staged for testing, fetch, history rewrite, commit, push, merge or
GitHub setting changes. Unrelated concurrently appearing experiment files are
preserved and excluded from the recommended security commit.

Limits: heuristic detection cannot prove arbitrary prose/encoded secrets are
public; exact fixture exemptions require provenance review. Local hooks can be
bypassed; CI needs enforced GitHub rules and protected policy/workflow reviews.
CI checks final trees, not earlier intermediate commits or external copies. Only
locally reachable history and cached origin refs were audited; unfetched/deleted
remote refs, forks/releases and unreachable/reflog-only objects remain uninspected.
Stop after the audit; await approval before committing/pushing or any historical
remediation. Next development experiment/milestone remains separately authorized.


## Bounded local CPU semantic-extraction comparison — 2026-10-13

Completed only the explicitly authorized experiment. Read AGENTS/status/master
plan (especially observation/inference/verification boundaries), requested
conversation-state/holdout/projection documentation and the prior private
AI-reference comparison. The initial checkout's Finder modification and later
concurrent repository privacy-audit changes were preserved; this task did not
create their hook, CI, privacy guard or staged Finder deletion.

Delivered isolated experimental code under `experiments/local_task_state/`, a
compact evidence-bearing schema, one frozen zero-shot prompt, deterministic
structural parsing and a read-only frozen-analyzer adapter. The common schema
separates requested actions, obligations/constraints, choices/reversals, changes,
reinstatement, reports, conditionals, earlier references and uncertainty. Exact
original quotes, message identities, roles/turns and half-open source spans are
validated. Targets stay nullable; no candidate link is promoted into accepted
active scope or independent verification. Production source remains unchanged:
analyzer SHA-256 `9f90a466de5e0bc0957277a453afb304491213fccb1ca517d7c1ca992978319b`.

Investigated Qwen2.5-1.5B-Instruct, Qwen3-1.7B and SmolLM2-1.7B using primary
model/runtime documentation. Explicit user approval permitted only the selected
official Qwen2.5 Q4_K_M weights: 1,117,320,736 bytes, Apache-2.0, publisher hash
verified. Local official llama.cpp b11580 ARM64 runtime uses CPU only (device
none, zero GPU layers, no KV offload), six threads, one slot, no prompt cache,
8,192-token context and bounded output. Runtime/weights remain ignored; project
dependencies and lockfile unchanged. No cloud/paid inference or fine-tuning.

The 15 original real user checkpoints remain consumed diagnostics. A separate
prediction-blind AI author created four fresh simulated topics, 16 checkpoints,
56 events and nine earlier links. Original and synthetic sources/references,
prompt, schema, extractors, runtime configuration and initial scorer froze before
prediction generation. An independent pre-output-inspection review required
scorer integrity fixes (unique coverage, nonnegative indices, match reasons) and
a request-only positive-obligation denominator amendment; original scorer/freeze
were retained. Original-denominator sensitivities are disclosed. No prediction-
informed prompt/rule tuning or reference relabeling. A distinct final reviewer
checked all input receipts, validations, metrics and semantic matching ledgers;
one B uncertainty match was corrected. Original private comparison/input bytes
and the independent synthetic labels remain unchanged.

| Audited finding | Frozen rules A | Structural B | Local model C |
| --- | --- | --- | --- |
| Fresh holdout objectives / known objectives | 1/16; 0/15 | 5/16; 4/15 | 1/16; 0/15 |
| Holdout positive-obligation precision / recall | 10/16; 10/31 | 12/13; 12/31 | 3/25; 3/31 |
| Holdout earlier-link recovery | 0/9 | 0/9 | 0/9 |
| Holdout valid local event citations | 56/56 | 24/24 | 4/33 |
| Holdout false failure / completion events | 3 / 0 | 0 / 0 | 0 / 0 |
| Diagnostic objectives | 3/15 | 8/15 | 0/15 |
| Diagnostic positive-obligation precision / recall | 23/30; 23/84 | 35/43; 35/84 | 2/30; 2/84 |
| Diagnostic canonical scope-target recovery | 0/6 | 1/6 | 0/6 |
| Diagnostic valid local event citations | 139/139 | 95/95 | 4/32 |

These are common-schema, one-to-one AI-reference matches. Old post-hoc typed
21/24 and 21/84/overlay32/84 measurements remain historical and unchanged; they
are not directly interchangeable with the new scorer. Invalid C events remain
in precision denominators, with raw outputs retained. They usually repeat earlier
messages or confuse message ordinals with exact-quote occurrences. All C
objectives are null. Zero false status claims coexists with missing all three
holdout failures and both completion claims. Verification is null by contract at
all 93 candidate checkpoints; this is a safeguard, not semantic accuracy evidence.

C holdout median/p95 is 4.98/14.53 s (16 trials), diagnostics 9.07/14.17 s (15).
Runtime lifetime peak RSS is 2,344,894,464 and 2,353,102,848 bytes respectively;
fresh-process loads 7.11 and 1.55 s. macOS getrusage measures the sole runtime
child separately from the driver (~1.1 GiB transient hashing peak). Every prompt
cache count is zero, every generation ends normally, and none is truncated.
Initial sandbox startup failed to bind loopback without producing predictions;
scoped approved execution succeeded and both measured servers exited zero.
Repository checks overlapped early holdout inference, so timings are observational
rather than idle-machine benchmarks. Post-run runner/scorer hardening preserves
the actually executed versions and changes no saved prediction.

The sanitized report and design are `docs/LOCAL_TASK_STATE_COMPARISON.md` and
`docs/LOCAL_TASK_STATE_EXPERIMENT.md`. All private source/diagnostic annotations,
raw results, comparison ledgers, model/runtime, freeze/version receipts, resource
logs and independent final review stay in ignored local storage. Public fixtures
are independently authored simulated material, never copied private conversations.
The new permanent privacy instructions were read when concurrent changes appeared.

| Executed check | Actual result |
| --- | --- |
| Final `uv run --no-sync pytest` | 931 passed, 7 existing opt-in skips in 56.00 s; includes concurrent privacy-guard tests. |
| Final focused experiment tests | 6 passed in 0.08 s after all reporting/hardening changes; independent reviewer rerun: 6 passed in 0.11 s. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 189 files already formatted. |
| `git diff --check` | Passed. |
| Private input/output/artifact validation | Passed: 93 identical-prefix receipts, every saved extraction/metric reproduced, 31 cache-zero stopped generations, prior comparison manifest and source/reference/prompt freezes unchanged. |
| Independent semantic/code/methodology review | Accepted with denominator/context sensitivities, partial objective/reference-population limits, and one B uncertainty correction; no extractor/label tuning. |

Recommendation: C fails the semantic improvement screen despite practical CPU
resources. Keep production and trusted estimators unchanged. Structure/evidence
parsing can support human review, but a local-inference/state-update hybrid remains
unproven. Any later candidate/prompt experiment needs separate authorization and
fresh prediction-blind, preferably human-adjudicated cases. No next milestone,
model download, commit, push, merge, publication or outcome integration started.

## Real execution/outcome readiness assessment — 2026-10-13

Read AGENTS, STATUS, relevant plan identity/provenance/learning and M3/M4/M6
sections, existing observation/verification/learning documentation and implementation.
Delivered only the sanitized assessment in docs/REAL_DATA_READINESS.md and this
status update; no runtime or schema changes. Preserved the pre-existing untracked
experiment source file without reading or modifying it.

### Actual evidence and privacy scope

- Six existing local SQLite ledgers were queried read-only for aggregate counts;
  the eligible smoke cohort was revalidated through read-only repository assessment
  resolution. **One eligible real fixed-reply execution; zero eligible real coding
  executions**. An unknown smoke derivation is the same run, not another trial.
  The separate actual JUnit producer-validation assessment has no learner rows and
  is not a coding-agent execution. Counts are scoped to inspected local evidence.
- User explicitly approved the three selected chat reads, local project inspection
  and verification. Returned views expose 3/4/4 turns with timestamps, but no
  configuration/usage fields. Turns/tool activity do not create attempts; no
  historical task/run/configuration attribution or native timing was invented.
- Independently authored synthetic probes executed outside the producing chats on
  byte-identical private copies: **JSONL Validator 3/3**, **Markdown Indexer 4/4**,
  **Job Status Selection 3/3** passed. Separately rerun existing agent-authored
  suites: **27**, **22**, **8** passed respectively. All processes exited zero.
  Job-selection probes include all 24 interleavings of the offset-aware fixture.
  Markdown's current final scope is JSONL plus exclusions, distinct from its
  earlier CSV request; acceptance versions must not be retroactively merged.
- Original artifacts and tested copies remained unchanged under before/after
  content manifests. Private JUnit XML, report/artifact/test-source hashes,
  process timestamps/exit/completion receipts, copied code, and bounded chat
  metadata are retained under ignored `.model-learner/real-data-readiness-20261013/`.
  No transcript or project source is copied into public documentation/fixtures.
  Fresh checks establish current named-check results, not historical acceptance,
  agent execution outcomes, universal correctness or independent trial counts.
  No new ledger observations/associations/assessments were created.

### Recommendation, blockers and next user-directed step

Use the existing ordinary operator-run CLI capture/JUnit workflow for the next
5–10 genuine coding executions. Create the task and freeze trusted acceptance
before execution; retain actual launch/configuration/starting-state receipts;
import capture; explicitly declare bounded run/attempt coverage; freeze and
independently check the final artifact; import JUnit binding evidence; assess,
build and resolve real observations. Keep unknown cost/native times/model versions
null and manual settings labeled declarations. No collector or infrastructure
layer is needed for this collection pilot.

Historical project eligibility remains blocked by supported execution capture,
known configuration/segment attribution and per-execution artifact/acceptance/report
bindings. Passing final code today cannot repair those omissions. Desktop-only
collection would need separately authorized execution-observation support. The
separate benchmark real-execution containment gate remains unchanged; the ordinary
observation path does not bypass it.

Existing estimators can consume correctly eligible coding rows under exact dataset,
acceptance/version, budget and configuration selectors. Unrelated acceptance
criteria cannot be pooled by renaming them; ordinary new tasks may yield only one
row per target. Five to ten rows test collection coverage, not predictive benefit.
Future semantic comparison needs frozen pre-outcome inputs and independent labels,
comparable targets, prospective availability receipts, chronological/task-family
holdout and adequate sample size; current task-state floors remain 30 training,
20 scored, five task clusters per partition and both training classes. After-close
CLI associations alone cannot satisfy initial checkpoint availability. No semantic
state is integrated and no models were trained.

Next unstarted step: user selects the first five upcoming tasks and explicit
configuration, then follows the documented operator sequence for one execution
before repeating it. Stop at the collection/quality report; training/evaluation
expansion remains separately directed. No paid agent launch, commit, push, merge,
publication, new model, routing, Governor or next milestone was performed.

### Actual checks

- Initial `uv run --no-sync` invocations could not access the default external uv
  cache; retried successfully with repository-local `UV_CACHE_DIR=.uv-cache`.
  No installation or escalation was needed.
- `UV_CACHE_DIR=.uv-cache uv run --no-sync pytest`: **931 passed, 7 existing opt-in
  skips in 60.53s**. These repository tests are distinct from project acceptance.
- `UV_CACHE_DIR=.uv-cache uv run --no-sync ruff check .`: passed.
- `UV_CACHE_DIR=.uv-cache uv run --no-sync ruff format --check .`: passed,
  **189 files already formatted**.
- Private project check driver: three existing suites and the fresh **10-test**
  independent pytest/JUnit suite passed, zero failures/errors/skips; original and
  copy integrity checks passed. Checks are post-hoc and do not run a coding agent.
- `git diff --check`: passed; private receipt/XML paths confirmed Git-ignored.

## First supervised real CSV coding experiment — 2026-10-13

After reading AGENTS, status, readiness guidance and relevant plan contracts, the
operator prepared one ordinary supervised CLI coding task. This uses the existing
real observation workflow documented in docs/REAL_DATA_READINESS.md; the separate
benchmark controller and its blocked containment gate are unchanged.

- Independently authored 18 synthetic black-box acceptance tests before execution.
  Froze the CLI interface, JSON schema, exact comparison behavior, CSV quoting,
  validation/error behavior and dependency constraint. Required pytest/JUnit
  identities, test/criteria digests, configuration, prompt, launch arguments and
  starting-state manifest were recorded before approval. A constant-output negative
  control failed 15 checks; all 18 report identities matched the task declaration.
- Actual unpaid local Codex sandbox canary allowed working-directory writes and
  denied writes to acceptance source, the control directory and neighboring
  temporary storage. The agent's working directory was separate from this
  repository. This demonstrates the selected write boundary, not a VM or complete
  host-read isolation. Agent tool networking, escalation, web/apps/plugins/hooks
  and additional agents were disabled; provider access used existing ChatGPT auth.
- The user explicitly approved one execution and subsequent verification/audit.
  Executed exactly one fresh ephemeral Codex CLI invocation requesting OpenAI
  gpt-6.1-sol, low reasoning, CLI 0.162.0-alpha.17.2. Agent and live metadata capture
  each exited 0, with no timeout. Operator agent-process wall time: 123.44 seconds.
  Receipt timestamps and operator wall measurements are not native latency.
- Capture/import retained 11 supported events for one session, one completed turn
  and three observed tool items, with zero import diagnostics. Native cumulative
  usage: 91,335 input tokens, including 60,416 cached input; 6,587 output tokens,
  including 199 reasoning output. Subsets are not added to their parent totals.
  Model/provider/reasoning/version were not emitted by the stream: requested
  settings are explicitly operator declarations, not observed native configuration.
- Stopped the agent and copied its sole standalone module to an exact private
  snapshot before independent testing. Original/snapshot digests agree; starting
  instructions, frozen acceptance/configuration/command files and final code remain
  unchanged. Executed the frozen suite under a local filesystem/network sandbox:
  **18 passed in 0.99s**, exit 0, zero failures/errors/skips. No candidate repair or
  second coding-agent invocation followed the independent result.
- Used existing `run create`, `run attempt`, `verify junit`, `outcome assess` and
  `observations build`. An actual operator receipt binds task/run, acceptance
  version, final artifact/report digests, report generation time, completion and
  exit status. The persisted outcome is **success / verified**, with one matching
  verification; the real observation has **single_configuration** attribution,
  eligibility true and no exclusions.
- `observations quality` and historical `observations resolve` confirm one eligible
  real execution in this new private dataset. Existing `learn predict` consumed
  exactly one selected eligible success, zero failures and zero exclusions. This
  exercises the existing fixed-prior reference; it creates no new trained model
  or model weights and establishes no predictive accuracy or model superiority.
- Replay inserted zero events and recognized all 11 duplicates. Final ledger audit:
  one Task, Run, Attempt, Session, Verification, Outcome and Observation; 11 Events.
  Dollar cost and canonical attempt/observation latency remain null. Native usage
  is retained on captured events; the existing attempt convenience CLI does not
  fabricate resource measurements from the stream or operator clock.
- Private tests, configuration, command/launch receipts, metadata capture, snapshot,
  XML/binding, ledger, returned CLI records and compact experiment result remain
  under ignored `.model-learner/first-real-csv-20261013/`. Public status contains only
  sanitized behavior and aggregate evidence. Preserved the pre-existing untracked
  experiment file without reading or modifying it.

Validation: relevant capture/JUnit tests **80 passed**; full repository tests
**931 passed, 7 existing opt-in skips in 58.60s**; Ruff and formatting clean;
`git diff --check` clean. No production code, dependencies, semantic analyzer,
benchmark infrastructure, new model training, AI Governor, commit, push, merge,
publication or global hook changes. The requested single experiment is complete.
Next step remains unstarted and requires separate user direction; do not run
another task or expand evaluation automatically.

## Experiment 2: ShortcutLens seed-validation preparation — 2026-10-16

The user selected one real project maintenance task and authorized preparation
only. Installed Python 3.13.9 / PyTorch 2.14.1 CPU Generator probes accept the
tested Python-integer endpoints -2**63 and 2**64-1 and reject adjacent values.
ShortcutLens's existing nonnegative policy is preserved. Direct NumPy Integral
inputs fail at the Torch boundary and require normalization. With a synthetic
source, both oversized Torch-bound seeds load data, render 12 images and write
a temporary manifest before raising ValueError. No real dataset was accessed.

Prepared a byte-identical temporary working copy and initial manifest of 30
project/instruction files from a clean original repository. Independently authored
60 synthetic acceptance cases and copied the 112 existing regression cases outside
the agent's writable workspace. Baseline: 160 passed, 12 failed, no errors/skips;
all failures are the selected seed defects. Required JUnit identities are declared
in the existing Task ledger. The existing pre-execution predictor selected zero
labels for this new real target and returned Beta(1,1): probability 0.5, 95%
credible interval [0.025, 0.975]. Prior CSV acceptance is not pooled.

Requested configuration: OpenAI gpt-6.1-sol / low reasoning, existing Codex CLI
0.162.0-alpha.17.2 and ChatGPT authentication. Effective native settings and model
version remain unknown until emitted. The existing metadata-only capture pipeline
is prepared with one-off operator supervision, a 600-second safety stop and no
automatic second invocation. Local no-model sandbox canaries confirm working-copy
writes allowed, protected/original/environment/neighbor writes denied and tool
network denied. Web/apps/plugins/hooks/additional agents are disabled.

The strict agent sandbox produces an OpenMP temporary-registration warning that
affects three existing empty-stderr import checks. This is disclosed in the prompt;
source/test changes or warning suppression to hide it are prohibited. The separate
trusted verification sandbox permits standard temporary files while keeping the
final snapshot and frozen tests read-only. Its preflight reproduces exactly the
same 12 seed failures, with no extra failures and no changed acceptance tests.

Private tests, source snapshots, manifests, declared settings, prediction, command
scripts and receipts remain under ignored local experiment storage. Relevant
Model Learner capture/JUnit checks: **95 passed in 1.43s**; Ruff lint/format clean
(190 files). No ShortcutLens source changes, production infrastructure, semantic
analyzer change, dependency installation, model call, additional agent, commit or
publication occurred. Launch count is zero. Next step is explicit user approval
of this single prepared execution; final verification, outcome, observation and
learner consumption remain unstarted.

## Experiment 2: approved execution, verification and learner consumption

After explicit approval, executed exactly one prepared ephemeral Codex CLI
invocation requesting OpenAI gpt-6.1-sol / low reasoning. The supervisor checked
frozen preparation and starting-file hashes before launch. Agent and metadata
capture both exited 0, with no timeout; operator pipeline wall time was 31.64
seconds. No second invocation or coordinator repair followed independent results.

- The helper now rejects oversized Torch-bound seeds before source/manifest access
  and converts valid Integral scalars to Python integers at the Torch boundary.
  Default behavior, negative-seed policy and large NumPy-only seeds are preserved.
- Froze a canonical final archive and per-file manifest with the agent stopped.
  Independent verification passed all **172 required cases**, no failures, errors
  or skips, with exact JUnit identity agreement. Frozen inputs and final source
  remained unchanged. The 60 independent cases use synthetic verification inputs;
  the coding execution and observation are real, not simulated or benchmark data.
- The final candidate's repository suite, including 17 agent-added cases, passed
  **129 tests**. Ruff passed. Applied only the two verified task files after
  checking their initial hashes. Device work committed after preparation and new
  unrelated training files were preserved. Earlier global clean/head guards
  aborted before writing; scoped transfer and post-apply checks succeeded.
  Retained scoped regressions against the applied code passed **129 tests**;
  unrelated new training tests were not executed as part of this experiment.
- Capture/import stored **18 events**, one session and one completed turn, with
  six observed tool items and no diagnostics. Replay inserted zero events and
  recognized 18 duplicates. Native turn usage emitted 124,382 input tokens,
  including 98,688 cached, and 1,721 output tokens, including 47 reasoning.
  Subsets are not added to parent totals. Model/provider/reasoning/version were
  absent from the stream; configuration remains an operator declaration.
- Existing run/attempt, bound JUnit verifier, outcome assessor and observation
  builder produced **success / verified**, single-configuration attribution,
  eligibility true and no exclusions. Report/artifact digests and actual process
  receipts bind the required checks to the exact final archive. Cost and canonical
  observation latency remain null; operator wall time is not native latency.
- Existing quality/resolution/prediction commands selected one eligible success,
  zero failures and no exclusions. Baseline was Beta(1,1), mean 0.5 and 95%
  interval [0.025, 0.975]; after recording it is Beta(2,1), mean 0.667 and interval
  [0.158, 0.987]. The resolver's deterministic snapshot UUID/cutoff differ from
  the persisted row identity/time; every other field, including stable key, run,
  outcome, evidence, configuration and eligibility, matches. The ledger contains
  only one observation. No cross-target pooling or predictive-accuracy claim.

Private evidence and result report remain in ignored experiment storage. Ledger
audit: one Task, Run, Attempt, Session, Verification, Outcome and Observation;
18 Events. Final relevant capture/JUnit tests **95 passed in 1.41s**; Ruff lint
passed and formatting reports 190 files formatted. No Model Learner production
code, semantic analyzer, dependency, benchmark controller, extra coding agent,
training, commit, push or publication changes. The selected task and experiment
are complete. No additional run or milestone is started or authorized.
