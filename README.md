# Model Learner

Model Learner observes AI-agent activity and learns configuration-level success
probabilities from verified outcomes. It preserves evidence, uncertainty, and
missing values while keeping observation and inference separate. Agent control
belongs to the future AI Governor.

The first parallel slices add Codex CLI event capture/import and a seeded
simulator with a Beta-Bernoulli learner and held-out evaluation. The existing
versioned contracts and SQLite ledger are unchanged. Follow
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
files. See [Codex source assessment and limitations](docs/CODEX_OBSERVATION.md).

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

## Development checks

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

To format code, run `uv run ruff format .`. Implementation lives under
`src/model_learner/`; tests live under `tests/unit/` and `tests/integration/`.
Develop one milestone at a time according to [AGENTS.md](AGENTS.md).
