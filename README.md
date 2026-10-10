# Model Learner

Model Learner observes AI-agent activity and learns configuration-level success
probabilities from verified outcomes. It preserves evidence, uncertainty, and
missing values while keeping observation and inference separate. Agent control
belongs to the future AI Governor.

The local workflow includes Codex CLI capture/import, explicit task/run
association, read-only file verification, real observation building, and a
seeded simulator with a Beta-Bernoulli learner and multi-seed evaluation. Follow
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

## Development checks

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

To format code, run `uv run ruff format .`. Implementation lives under
`src/model_learner/`; tests live under `tests/unit/` and `tests/integration/`.
Develop one milestone at a time according to [AGENTS.md](AGENTS.md).
