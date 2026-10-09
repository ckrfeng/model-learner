# Repository instructions

Model Learner is a local-first system for learning AI-model utility from observed
execution data and verified outcomes. Follow `MODEL_LEARNER_PLAN.md` as the primary
design reference; `STATUS.md` records actual implementation and test evidence.

- Read `STATUS.md` and the relevant plan section before making milestone changes.
- Implement only the explicitly requested milestone or submilestone. Stop when it
  is complete; do not proceed to another milestone without user instruction.
- Inspect existing code, preserve working behavior, and avoid unrelated rewrites
  or speculative placeholder implementations.
- Prioritize correctness, modularity, and testability. Keep dependencies and
  complexity minimal, and create components only when the milestone needs them.
- Do not silently change architectural decisions. Explain a proposed deviation
  and obtain approval before changing the plan's core semantics.
- Keep observation, inference, and decision separate. Unknown is not failure;
  completion is not verification; unknown cost is not zero. Keep real, simulated,
  and benchmark data distinct.
- Run relevant tests and Ruff checks, report actual results, fix in-scope failures,
  and update `STATUS.md` with delivered behavior, blockers, and the next milestone.
- Keep secrets, private transcripts, and unsanitized data out of Git. Do not install
  global hooks, push, merge, or publish without explicit user authorization.

Development checks: `uv run pytest`, `uv run ruff check .`, and
`uv run ruff format --check .`. Install the development environment with `uv sync`.
