# Model Learner

Model Learner observes AI-agent activity and learns configuration-level success
probabilities from verified outcomes. It preserves evidence, uncertainty, and
missing values while keeping observation and inference separate. Agent control
belongs to the future AI Governor.

The local workflow includes Codex CLI capture/import, explicit task/run
association, read-only file and JUnit verification, checkpoint analysis, real
observation building, and a seeded simulator with a Beta-Bernoulli learner and
multi-seed evaluation. Follow
[MODEL_LEARNER_PLAN.md](MODEL_LEARNER_PLAN.md) for the design and
[STATUS.md](STATUS.md) for implemented milestones and test results.

## Local installation

Install [uv](https://docs.astral.sh/uv/getting-started/installation/), then run from
this checkout:

```sh
uv sync
uv run model-learner --help
uv run model-learner --version
```

The project requires Python 3.12 or newer. `.python-version` selects Python 3.12
for development; uv can download it if needed. `uv sync` uses `uv.lock`, creates
`.venv`, installs the package in editable mode, and includes development tools.
Activate the environment with `source .venv/bin/activate` to use `model-learner`
directly.

## Local ledger

Initialize an ignored local database, then create tasks and register sessions
separately. A session is associated with a task only when you explicitly attach
it; that link does not claim task completion.

```sh
model-learner init --database .model-learner/model-learner.sqlite3
model-learner task create "Repair parser regression" \
  --acceptance-id pytest --acceptance-version 1
model-learner session register --source codex --native-session-id native-thread-1
model-learner task list
model-learner records show task <task-id>
```

The default database path is `.model-learner/model-learner.sqlite3`. JSONL
records can be checked, imported, and exported through `model-learner records`.
Use `model-learner records --help` for the exact commands. Measurements that are
not supplied remain `null`; they are not converted to zero.

## Selected conversation import

The read-only standalone importer supports the validated Codex-backed Codex
Desktop and Work Local history formats. Select an exact conversation UUID and
declare its product source and stable local machine identity:

```bash
model-learner init
model-learner import conversation <conversation-uuid> \
  --product-source codex_desktop --machine-id <local-machine-id>
# Work Local: --product-source chatgpt_work_local
model-learner sessions
model-learner session show <returned-local-session-id>
```

The installed `codex` executable must be on PATH; alternatively provide
`--codex-executable /absolute/path/to/codex`. The importer launches a temporary
`codex app-server --listen stdio://` process and sends only the documented
handshake, exact-ID metadata read and bounded turn pagination. It never resumes,
executes, modifies or scans conversations.

Defaults omit turn items server-side and store only metadata in the workspace's
Git-ignored `.model-learner/` database. The metadata endpoint can still return a
preview, which is discarded in memory. `--read-text` explicitly retrieves full
items, extracts user/assistant text in memory, and persists only message metadata.
Full view has **no server-side filter for reasoning, attachments or tool outputs**;
those bodies are discarded locally after retrieval. `--retain-text` is a separate
local storage opt-in that implies a full text read and retains only message text
parts, never raw responses or other item bodies. CLI import reports never print
message text. Inspecting an opted-in snapshot with `session show` or `records show`
does display its retained text.

Each import is limited to ten one-turn pages and 64 KiB of response bytes/text.
Snapshots preserve source page/item order, native identities, timestamps and
missingness. Reimporting identical retained facts creates no duplicates; changed
retained facts or retention/view choices append a distinct immutable snapshot.
Opaque pagination tokens stay in memory. Partial bounded history is marked;
exhausted pagination establishes only the exposed history, not lossless original
coverage. Message timestamps, historical configurations, usage, cost and
verification remain unknown. Conversations never automatically create task links
or learning labels. Other backends and source formats fail closed. See the
[feasibility and actual validation report](docs/CONVERSATION_INGESTION_FEASIBILITY.md).

## Codex observation

Capture the documented `codex exec --json` stream through a metadata-only
receipt-time envelope. Model Learner consumes the stream; the user runs Codex.

```sh
mkdir -p .model-learner
codex --version
codex exec --json "Your task" | model-learner capture codex \
  .model-learner/capture.jsonl --source-version <installed-codex-version>
model-learner import codex .model-learner/capture.jsonl \
  --machine-id local-machine
model-learner sessions
model-learner session show <session-id>
```

Reimporting an unchanged capture is idempotent. Native timestamps, unreported
model settings, and prices remain unknown; receipt times describe collection,
including any buffering, rather than execution duration. Completed turns create
no task outcomes or training labels. Default capture omits messages, reasoning,
commands, tool arguments, and outputs. `--retain-raw` explicitly opts into private
local payload retention; keep those files out of Git. Diagnostics return exit
code 1 with valid-record counts, since valid records may still have been imported.

This adapter supports the CLI stream. It does not ingest existing desktop session
files. See [Codex source assessment and limitations](docs/CODEX_OBSERVATION.md)
and [Desktop feasibility findings](docs/CODEX_DESKTOP_FEASIBILITY.md).

## Tasks and verification

Declare an objective, acceptance version, and expected file SHA-256 before the
execution. This first verifier checks exact bytes only; it does not establish
general code correctness. Associate the captured session with explicit run
bounds and declare configuration segments with their manual provenance.

```sh
model-learner task create "Produce the agreed artifact" \
  --acceptance-id exact-file --acceptance-version 1 \
  --acceptance-description "Artifact matches the agreed SHA-256" \
  --expected-sha256 <64-lowercase-hex-digest> --task-group artifact
model-learner run create <task-id> --session-id <session-id> \
  --started-at <ISO-time-with-timezone> --ended-at <ISO-time-with-timezone> \
  --artifact <final-file>
model-learner run attempt <run-id> --configuration-file <configuration.json> \
  --started-at <ISO-time-with-timezone> --ended-at <ISO-time-with-timezone>
model-learner verify file <run-id> <final-file>
model-learner outcome assess <run-id> --verification-id <verification-id>
model-learner observations build <run-id> --outcome-id <outcome-id> \
  --dataset-id local-tasks --dataset-version 1
model-learner observations quality --dataset-id local-tasks --dataset-version 1
model-learner records export observation .model-learner/real-observations.jsonl \
  --source-kind real
```

`configuration.json` uses the existing ExecutionConfiguration contract, for
example `{"provider":"openai","model":"<actual-model>","harness":"codex"}`.
Declare only settings you know; missing settings remain null. Run bounds select
captured receipt-time events, not native timing or execution duration. Commands
never launch an agent or an arbitrary verifier command. `run show` presents
execution state, evidence and assessments separately. `outcome assess` without
evidence records unknown; `outcome human` records an unverified human assessment.
Revisions use `--supersedes` and preserve original evidence. Mixed configuration,
incomplete capture/attribution, and unassessed outcomes are retained with
exclusions. See [workflow semantics and limitations](docs/TASK_VERIFICATION.md).

For coding tasks, declare the required JUnit test identities before execution.
Run pytest yourself and retain its XML report plus an independent binding receipt
for the exact task, run, acceptance version and tested artifact snapshot:

```sh
model-learner task create "Repair parser regression" \
  --acceptance-id parser-tests --acceptance-version 1 \
  --required-test 'tests.test_parser::test_regression'
model-learner verify junit <run-id> <report.xml> \
  --artifact <tested-file> --binding-file <binding.json>
model-learner outcome assess <run-id> --verification-id <verification-id>
```

Missing, incomplete or contradictory evidence cannot establish success. Reports
retain counts and test identities/statuses without failure messages or outputs.
The binding receipt is a trusted external declaration, not an agent completion
claim or cryptographic proof of execution. Current artifact hashing covers one
regular file; it does not establish a whole repository snapshot. See
[JUnit report bindings and limits](docs/JUNIT_VERIFICATION.md).

Inspect execution features at multiple explicit checkpoints without changing
agent behavior or creating outcome labels:

```sh
model-learner session analyze <session-id> \
  --checkpoint <ISO-time-with-timezone> --checkpoint <later-ISO-time-with-timezone>
```

Only events observed and ingested by each checkpoint contribute. Tool failures
and turn completion are separate from test results and verified task outcomes.
Default Codex capture omits commands/outputs, so identical-command retries and
test counts are unknown from those events. The Python analyzer accepts explicitly
bound structured verification for test-result changes; the session CLI analyzes
events only. Report comparisons currently require the same declared final
artifact; intermediate snapshots across code edits are unsupported. See
[observable execution features](docs/EXECUTION_ANALYSIS.md).

## Coding-task and task-state evaluation

Multi-checkpoint inspection and the evidence audit are documented in
[Longitudinal task state](docs/LONGITUDINAL_TASK_STATE.md). Use
`model-learner task trajectory INPUT.json` for an explicitly supplied local
trajectory and `model-learner learn trajectory-eval FIXTURE.json` for the seven
synthetic state-change checks. Summary declarations remain hypotheses; these
checks establish no real predictive improvement.

`model-learner benchmark tasks` lists small public synthetic coding exercises.
`benchmark prepare` stages a fresh disposable workspace outside this repository,
predeclares the configuration and acceptance target, and preserves operator
control files separately. Disposable paths and integrity checks provide no OS
containment. Real-run finalization is blocked until a supported, validated
execution boundary exists; an operator confirmation alone cannot enable it.
`benchmark snapshot`, `finalize`, and `cleanup` manage the frozen artifact,
independent JUnit evidence, incomplete outcomes, and disposal. These commands
never launch paid agent executions. Public tasks are recorded as benchmark data,
with actual agent executions distinguished from fixture checks. Follow the
[operator run procedure and isolation boundaries](docs/CODING_TASK_EVALUATION.md).

The [real evaluation pilot protocol](docs/REAL_EVALUATION_PILOT.md) predeclares
12 tasks, two configurations, prospective checkpoints, independent acceptance,
resource limits and missing-data reporting. It prepares a manually controlled
experiment; no paid executions have run. Containment readiness and the benchmark
handoff into predictive evaluation remain explicit gates. This small pilot cannot
establish predictive improvement under the existing evidence thresholds.

```sh
model-learner benchmark isolation-probe
model-learner benchmark pilot-plan \
  --configuration-a /private/tmp/arm-a.json \
  --configuration-b /private/tmp/arm-b.json --seed 1
```

The probe uses synthetic canaries and reports unavailable containment explicitly.
Even a passing probe does not authorize an agent run. `pilot-plan` emits a frozen
schedule from operator-supplied configurations without starting any execution.

`benchmark offline-isolation-probe` investigates an existing Docker Desktop Linux
runtime using a fixed synthetic worker, no host mounts, no network and bounded
resources. It never installs software, pulls an image or enables real execution.
An unavailable daemon or compatible local image remains an explicit blocker.
See [offline isolation experiment](docs/OFFLINE_BENCHMARK_ISOLATION.md).

`benchmark evidence-export ROOT` exports finalized benchmark evidence, and
`benchmark evidence-import FILE --root ROOT --database DATABASE` revalidates that
evidence against its trusted source before importing an observation idempotently.
The destination database must already be initialized. Repeat `--checkpoint
<aware-ISO-time>` to audit checkpoint coverage; use `--historical-cutoff
<aware-ISO-time>` for historical evidence selection. Fixture origins, exact
acceptance targets, native evidence and unknown outcomes remain explicit.
Post-run ingestion does not create historically available predictor inputs.
See [benchmark evidence export](docs/BENCHMARK_EVIDENCE.md).

The task-state experiment compares initial task/configuration information (A),
initial information plus simple execution metrics (B), and those inputs plus
evolving failure-state features (C). All variants and feature-group ablations
share chronological cutoffs and held-out tasks. Reports include Brier scores,
calibration bins, sample sizes, paired uncertainty and insufficient-data results.
Final acceptance reports and task outcomes never enter predictive features.

```sh
model-learner learn state-experiment --seeds 5 --count 400
model-learner sim state-fixture /tmp/task-state-examples.json --seed 1 --count 400
model-learner learn state-eval --help
```

Controlled state-signal and null-signal scenarios establish fixture behavior.
They do not establish predictive improvement on real coding tasks. The portable
input format requires explicit feature availability and independently resolved
labels; real observations need prior ledger validation. See
[methods, leakage controls and limitations](docs/TASK_STATE_EVALUATION.md).

The [secure benchmark controller primitives](docs/SECURE_BENCHMARK_BOUNDARY.md)
add bounded hostile archive parsing, immutable candidate bytes, credential-free
public envelopes, primitive acceptance messages, and authenticated per-run
synthetic receipts. They never execute submitted source. The supported real-agent
credential mechanism and OS freeze/acceptance transport remain unvalidated;
real execution stays disabled.

An optional [CPU task representation prototype](docs/CPU_TASK_REPRESENTATION.md)
compares existing initial features (A), those features plus deterministic
execution metrics/state (B), and B plus pretrained semantic embeddings (C).
This separate experiment uses public or explicitly sanitized initial descriptions,
chronological cutoffs, and held-out task families. It leaves the probabilistic
learner unchanged and writes no ledger records.

```sh
model-learner sim representation-fixture /tmp/public-representation.json
model-learner learn representation-eval --help
```

Semantic inference requires an explicitly supplied local, hash-pinned CPU model
bundle and an existing compatible runtime. The prototype never downloads models
or installs dependencies. Without a model, C scores and inference measurements
remain unavailable; A/B still run. Synthetic held-out results are algorithm
rehearsal and cannot establish real coding-task improvement.

Actual pretrained CPU C evaluation is now validated with the explicitly selected
`minishlab/potion-base-8M` model. Install its optional runtime with
`uv sync --locked --extra semantic`; model loading requires the approved local
revision/hash pins and never downloads automatically. The same frozen synthetic
cohorts show no consistent improvement over B. See the
[measured results, uncertainty and reproduction](docs/CPU_TASK_REPRESENTATION.md#completed-pretrained-potion-c-evaluation--2026-10-11).

Optional [task-description retrieval](docs/SEMANTIC_TASK_EVALUATION.md) now compares
token matching, TF-IDF and the same frozen local Potion encoder against authored
relevance judgments. On twelve queries from six task families, Potion retrieved
15 of 24 relevant query/candidate matches in the top three versus 10 for either
lexical baseline. Its top result was relevant on only 4 of 12 queries. These are small,
constructed examples with agent-authored labels, not evidence of real-world
accuracy or agent success prediction.

```sh
model-learner task similar TASK_ID --database .model-learner/model-learner.sqlite3
model-learner task similar TASK_ID --backend potion \
  --model-path /absolute/path/to/approved/potion-bundle \
  --model-revision bf8b056651a2c21b8d2565580b8569da283cab23 \
  --model-sha256 930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2
```

TF-IDF is the default and requires no embedding runtime. The optional Potion
backend requires the existing local bundle and pinned runtime; unavailable
embeddings yield an explicit status with no automatic fallback. The command
uses only declared descriptions of tasks created no later than the query task,
omits text from output, and returns IDs, inferred similarity scores and provenance.
Descriptions are limited to 4096 characters; unsupported historical descriptions
are counted as exclusions. The index supports up to 10,000 candidates. Creation
times are declarations, not independently verified historical availability.
Scores are relatedness suggestions, not probabilities of continuation or success.
Task identities, explicit links and the Bayesian estimator remain unchanged.

The [task annotation workflow](docs/TASK_ANNOTATIONS.md) collects similarity,
continuation, no-match, scope and apparent-difficulty judgments in versioned local
files. Use `model-learner annotation prepare`, `show`, `label`, `review`, `freeze`
and `evaluate` to collect labels, record independent human review and measure
retrieval precision, recall, false positives and abstention with a frozen policy.
Annotations never create task relationships. The
[example seed](tests/fixtures/understanding/annotations/README.md) and proposals
are agent-authored drafts awaiting actual human labeling and review; they supply
no new accuracy evidence or model-utility prediction claim.

## Simulation and reference learning

Generate observations in an explicitly simulated dataset. Known probabilities
are optionally saved in a separate evaluator-only JSON file.

```sh
model-learner sim generate --seed 7 --count 1000 \
  --dataset-id demo --truth-output .model-learner/demo-truth.json
model-learner learn predict --source-kind simulated \
  --dataset-id demo --dataset-version 1 \
  --acceptance-id simulated-binary-success --acceptance-version 1 \
  --cutoff 2026-01-01T08:20:00Z \
  --group group-a --configuration-id <id-from-generation-output>
model-learner learn eval --source-kind simulated \
  --dataset-id demo --dataset-version 1 \
  --acceptance-id simulated-binary-success --acceptance-version 1 \
  --train-until 2026-01-01T08:20:00Z \
  --evaluation-at 2026-01-02T00:00:00Z \
  --truth-file .model-learner/demo-truth.json
```

Predictions include a fixed Beta(1,1) prior, verified label counts, 95% equal-tail
credible intervals, and resource missingness. No labels yield probability 0.5
with a broad prior interval. Only records and labels available by the cutoff
train the estimator. Evaluation compares global, per-configuration, and unpooled
references using time-ordered holdout, Brier score, log loss, calibration bins,
and known-truth errors. Synthetic calibration does not establish real-world
calibration.

Use `sim generate --config-file` for missingness, assignment imbalance,
probabilities, drift, and resource distributions; explicit CLI options override
the scenario. Prediction accepts `--configuration-file` for an unseen arm.
Both learning commands select an exact acceptance version and optional
`--budget-file`; a missing budget selects only observations with no declared
budget. See [statistical assumptions and limits](docs/PROBABILISTIC_LEARNING.md).

Run the reference stress suite without writing any ledger rows:

```sh
model-learner learn stress --seed 7 --seed 9 --count 1000 \
  --output .model-learner/stress-report.json
```

The eight scenarios cover heterogeneity, homogeneous pooling, sparse groups,
imbalanced selection, drift, missing labels, and pending/mature delayed labels.
Reports preserve per-seed denominators, calibration bins, latent-probability
interval coverage, rare-cell diagnostics and paired baseline comparisons.
The stationary estimator fails under abrupt drift; see
[actual stress results and limits](docs/STATISTICAL_EVALUATION.md).

Resolve append-only real assessments at a historical cutoff without changing
the ledger:

```sh
model-learner observations resolve --dataset-id local-tasks --dataset-version 1 \
  --cutoff <ISO-time-with-timezone>
```

The resolver selects one complete revision chain per run and reports conflicts
explicitly. Unknown and censored heads supersede earlier binary labels. Real
`learn predict` resolves the selected cohort at its cutoff; real `learn eval`
resolves training and scoring separately, preserving earlier training knowledge.
Learning requires a matching derivation recorded by that time. Declared timestamps
are trusted; some record types lack ingestion receipts. See
[historical reconstruction and availability limits](docs/ASSESSMENT_RESOLUTION.md).

Compare the existing full-history estimator with explicit recent decision-age
windows, using chronological refits across independent simulation seeds:

```sh
model-learner learn drift --count 1000 --window-steps 120 --window-steps 300 \
  --output .model-learner/drift-report.json
```

The default experiment uses seeds 0–19 and stationary, abrupt, gradual, sparse,
imbalanced and delayed-verification scenarios. Reports include Brier scores,
calibration bins, empirical latent-probability interval coverage, cell sample
counts and adaptation with unrecovered seeds marked censored. Windows measure
decision age; delayed old labels do not become recent evidence. Full history
remains the default learner. See [drift investigation](docs/DRIFT_INVESTIGATION.md)
for reproduction, sample-size sensitivity and the stationary/adaptation tradeoff.

## Optional offline task-intent research

The [J1 fictional evaluation](docs/J1_OFFLINE_INTENT.md) freezes two task-intent
questions, 24 fictional descriptions and a deterministic baseline. Its executable
example uses only local mocked responses and preserves learner/advisory results.
The adapter follows supplied official OpenRouter Decisions examples offline.
Live use remains blocked pending provider-filter and resource enforcement evidence;
labels await independent human review. No live request,
credential access or model download is needed or enabled.

```sh
.venv/bin/python -B scripts/intent_example.py
```

## Development checks

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

To format code, run `uv run ruff format .`. Implementation lives under
`src/model_learner/`; tests live under `tests/unit/` and `tests/integration/`.
Develop one milestone at a time according to [AGENTS.md](AGENTS.md).

Activate the repository-local privacy hook once per checkout:

```sh
git config --local core.hooksPath .githooks
python3 scripts/privacy_guard.py --staged
```

Review staged changes and run the guard before every commit. The hook checks the
actual index, including ignored files added with `-f`; CI checks the committed
tree. Keep private messages, annotations, reports, databases and models under
ignored `.model-learner/`. See [the privacy policy, limitations and audit](docs/REPOSITORY_PRIVACY.md).

### CPU conversation task-state demonstration

Process explicitly opted-in text in memory and inspect an evidence-linked evolving
scope/progress timeline. No transcript or semantic state is automatically retained.
The default output omits text; `--emit-text` authorizes evidence display in stdout.

```sh
uv run model-learner task conversation-state --text-opt-in --emit-text \
  < tests/fixtures/conversation_state/demo.json
uv run model-learner learn conversation-state-eval \
  tests/fixtures/conversation_state/evaluation.json
```

The demo and evaluation are authored simulated inputs. Independent scoped checks
are distinct from assistant success claims. See
[the semantic demonstration](docs/CONVERSATION_TASK_STATE.md) for selected live
case results, CPU baselines, evaluation errors and limitations.
