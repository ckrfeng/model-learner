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

## Permanent repository privacy policy

- Never commit raw conversation contents, imported session histories, private
  annotations, local execution databases, credential files, private evaluation
  reports, local model weights or caches. Keep sensitive artifacts under ignored
  `.model-learner/` or the explicit private directories in `.gitignore`.
- Public `docs/` contains implementation guidance and sanitized aggregate evidence.
  Private research, original messages, worksheets and per-conversation evaluation
  artifacts belong in ignored local storage, even when formatted as Markdown.
- Committed tests must use sanitized synthetic fixtures with documented provenance.
  The existing metadata-only smoke derivative remains explicitly distinct from
  simulated fixtures. Recognized conversation/session fixtures require reviewed
  exact digests in `scripts/privacy_fixture_allowlist.json`; never add real private
  data to this policy. Digest exceptions do not exempt secrets or prohibited paths.
- Before every commit, review staged paths and changes locally without copying
  private values to output, then run `python3 scripts/privacy_guard.py --staged`.
  It validates all index blobs, including force-added ignored files. Never bypass
  the guard, skip the hook, or weaken its policy without explicit user authorization.
- Activate only the repository-local hook as documented in
  `docs/REPOSITORY_PRIVACY.md`. Do not change global Git configuration. CI privacy
  checks require GitHub rules to be enforced; they do not clean earlier history.
- Report suspected exposures using file identifiers and categories only. Do not
  print credentials, private transcripts or unsanitized findings. Do not fetch
  remote history, rotate credentials, delete user data, rewrite history or push
  without the required user authorization.
