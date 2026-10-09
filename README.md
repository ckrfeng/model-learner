# Model Learner

Model Learner is a local-first system intended to estimate AI-model utility from
observed execution data and verified outcomes. It will preserve evidence,
uncertainty, and missing values while keeping observation, inference, and advice
separate.

M1 adds versioned evidence contracts and a local SQLite ledger. It does not yet
collect real agent telemetry, verify outcomes automatically, learn model utility,
or route execution. Follow
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

## Development checks

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

To format code, run `uv run ruff format .`. Implementation lives under
`src/model_learner/`; tests live under `tests/unit/` and `tests/integration/`.
Develop one milestone at a time according to [AGENTS.md](AGENTS.md).
