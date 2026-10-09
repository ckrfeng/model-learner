# Model Learner

Model Learner is a local-first system intended to estimate AI-model utility from
observed execution data and verified outcomes. It will preserve evidence,
uncertainty, and missing values while keeping observation, inference, and advice
separate.

M0 provides the Python package and development environment. The CLI currently
supports help and version output. Follow
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

## Development checks

```sh
uv run pytest
uv run ruff check .
uv run ruff format --check .
```

To format code, run `uv run ruff format .`. Implementation lives under
`src/model_learner/`; tests live under `tests/unit/` and `tests/integration/`.
Develop one milestone at a time according to [AGENTS.md](AGENTS.md).
