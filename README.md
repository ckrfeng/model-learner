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

`model-learner benchmark tasks` lists small public coding exercises.
`benchmark prepare` stages a fresh disposable workspace outside this repository,
predeclares the configuration and acceptance target, and preserves operator
control files separately. The operator supplies OS containment, runs any agent,
captures telemetry, stops the agent, and invokes the trusted acceptance runner.
`benchmark snapshot`, `finalize`, and `cleanup` manage the frozen artifact,
independent JUnit evidence, incomplete outcomes, and disposal. These commands
never launch paid agent executions. Public tasks are recorded as benchmark data,
with actual agent executions distinguished from fixture checks. Follow the
[operator run procedure and isolation boundaries](docs/CODING_TASK_EVALUATION.md).

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

## Development checks

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

To format code, run `uv run ruff format .`. Implementation lives under
`src/model_learner/`; tests live under `tests/unit/` and `tests/integration/`.
Develop one milestone at a time according to [AGENTS.md](AGENTS.md).
