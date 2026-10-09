# Model Learner — Master Development and Implementation Plan

**Repository:** `model-learner`  
**Python import package:** `model_learner`  
**CLI:** `model-learner`  
**Status:** Design document; milestones are **not** implemented merely because they appear here.  
**Plan revision:** 2026-10-09 (v1)

> **Mission:** Build a local-first, CLI/TUI-oriented system that learns the expected *verified utility* of AI-agent execution configurations from observed task outcomes. It should eventually recommend models and interventions, but it must first capture honest evidence, preserve uncertainty, and work on one local machine.

---

## 0. How to use this file with Codex

This is a **long-lived specification and milestone checklist**, not an instruction to implement everything at once.

1. Place this file at the root of the existing GitHub repository's local checkout (or a new local directory named `model-learner`).
2. Open **that directory** in the Codex desktop app, IDE extension, or Codex CLI. Ensure Codex's selected workspace is the correct local checkout, not an unrelated remote/cloud environment.
3. Start with the **First Codex prompt: repository assessment** in §13. It deliberately requests **no edits**. Review the findings.
4. Use the **M0 implementation prompt** in §13. Then review the diff, run tests yourself, and commit/PR only when satisfied.
5. For each subsequent milestone, ask Codex to implement **only the next numbered milestone or submilestone**. Do not ask it to build the entire plan.
6. Codex must keep `STATUS.md` updated with completed work, real test outputs, decisions, blockers, and the next unstarted milestone. The human decides whether to move forward.
7. A short repository-root `AGENTS.md` should be created or refined in M0; it references this plan but avoids copying the entire plan into instructions automatically loaded for every task.
8. If the repo already contains code, **audit and integrate**; do not wipe it or replace it with a downloaded scaffold.

**Recommended cycle:** `plan one milestone -> implement -> run automated tests -> inspect real behavior -> review git diff -> commit -> start next milestone`.

Use Codex Plan mode for uncertain or cross-cutting changes, then a separate implementation turn. No autonomous milestone chaining; an implementation turn ends after its requested scope.

### Human checkpoint after *every* implementation

- Inspect `git diff --stat` and `git diff`; confirm no unrelated modifications.
- Check `STATUS.md` for what was **actually** implemented versus proposed.
- Run the exact listed commands locally (or inspect trustworthy executed command output).
- Ask for an independent code review of that diff if the change affects data integrity, statistical validity, hooks, or database migrations.
- If tests fail, fix the **same** milestone. Do not move on to the next one.
- Commit a small, coherent change; a new branch/PR per major milestone is ideal for GitHub work.

---

## 1. Product definition and scope

### 1.1 What the first product does

On one developer machine, for one supported local agent at a time, the first working version must:

1. **Observe** available local session/tool/model metadata without changing the agent's behavior.
2. **Inspect** the captured timeline from a CLI.
3. **Link** a native session or portion of a session to an explicitly defined task/run.
4. **Assess** a task with a specified acceptance criterion (automated verifier or human label).
5. **Report** which evidence supports outcomes, what telemetry is missing, and resource usage where known.
6. **Learn** simple probabilistic configuration-level performance estimates from eligible observations and state their uncertainty.
7. Later, **recommend** configurations *advisably*, without controlling agents.

The principal outcome question is:

> For a declared task/acceptance criterion and specified resource budget, what is the predicted probability that a given model + settings + harness will satisfy the criterion, at what total resource cost, and with what uncertainty?

### 1.2 Explicitly out of scope for the local first release

- Browser-based ChatGPT/Claude conversations, phone activity, and hosted cloud-agent sessions.
- GitHub as a cloud-agent outcome ingestion pipeline, cloud CI polling, multi-machine synchronization, and cross-account identity management.
- Running a model locally (local-first storage does **not** require local inference).
- Subscription quota scraping or pretending token usage equals a subscription's monetary spending.
- Autonomous task dispatch, remote execution, automatic model upgrades, automated retries, or an API gateway.
- A hosted service, web dashboard, team features, accounts, billing, and marketing website.
- The separate Research Delta Engine and company-wide Pantheon branding architecture.

Keep extensibility for later, but **do not implement these now**.

### 1.3 What makes the project useful rather than another monitor

The important distinction is **outcome-grounded comparisons and learning**, not collecting tokens or displaying an agent timeline. The first recorder/importer is enabling infrastructure and should be narrow.

Maintain a strict separation:

- **Observation:** facts from a source (tool exited with code 1, verifier produced a report).
- **Inference:** heuristic/statistical conclusion (possible stall, estimated difficulty).
- **Decision:** advice/action selected by the learner or future governor.

An inferred “root cause found” cannot be silently treated as verified truth.

---

## 2. Design decisions (baseline)

| Decision | Initial choice | Reason | Reconsider when |
|---|---|---|---|
| Repository | `model-learner` | Current repo name; company/product names can change independently | Explicit branding decision |
| Language | Python 3.12+ | Fast iteration for telemetry, CLI, statistics | Actual performance bottleneck |
| Dependency tool | `uv` | Reproducible development and CLI entry point | Existing repo already has an established alternative |
| CLI | Typer + Rich | Nested commands, readable tables | A compelling existing CLI pattern conflicts |
| Validation | Pydantic v2 | Versioned schemas and strict validation | Specific measured overhead |
| Storage | SQLite (`sqlite3`) | Local-first, transactions, easy inspection | Proven multi-process scaling problem |
| Testing | pytest | Unit, integration, CLI tests | Existing repo convention differs |
| Style | Ruff | Lightweight lint/format checks | Existing repo convention differs |
| TUI | Textual, **later** | Reuse domain/report APIs, avoid a UI-led architecture | After basic CLI analytics work |
| Collection | External/native read-only source where possible; one adapter first | Reuse telemetry rather than recreating it | Missing essential data |
| Background daemon | **Not initially** | Import-on-demand or light hook should suffice | Proven need for real-time ingestion/concurrency |
| ML v0 | Transparent Bayesian baseline | Auditability, sparse-data uncertainty | After evaluation |
| Model switching | **Not initially** | No credible evidence/policy yet | After shadow-mode evaluation |

**Do not blindly commit a dependency list** if this repository already has compatible tooling. M0 should audit first.

### 2.1 GitHub/repo workflow

- Work in Git from the beginning. If remote `origin` already exists, **do not replace it**.
- Keep `main` stable. Prefer `milestone/m0-foundation`, `milestone/m1-contract`, etc. (or Codex worktrees) for significant work.
- Use one reviewed PR/commit per milestone, not one giant generated change.
- Do not push, merge, publish packages, or install global hooks without the user's explicit approval.
- `.gitignore`: databases, sockets, native/raw conversation transcripts, credentials, local configuration, spools, caches, and private logs. Only sanitized fixtures and synthetic datasets belong in Git.
- Keep a lockfile if using `uv`. No networked services or API keys required for early milestones.

---

## 3. Architecture and boundaries

### 3.1 Logical components (not necessarily separate processes)

```text
One local AI agent (Codex / Claude Code / Pi / other)
             |
    supported native telemetry or hook
             |
     narrow source importer/adapter
             |
    observed event/session ledger (SQLite)
             |
    explicit task and run association
             +------------> verifier / human assessment
             |                         |
             +-------------------------+
                         |
                 observation builder
                         |
                 outcome/quality ledger
                         |
          descriptive reports + simulated data path
                         |
           probabilistic model utility learner
                         |
              policy/recommendation layer
                         |
             future separate AI Governor
```

Do not merge the governor, learner, UI, and collector into a single procedural module. But do not split into independent services prematurely: one Python package and a small CLI are sufficient.

### 3.2 Suggested eventual repository layout

Only create directories/files when a milestone needs them.

```text
model-learner/
  MODEL_LEARNER_PLAN.md        # this document, primary technical roadmap
  AGENTS.md                    # small durable instructions, created/refined in M0
  STATUS.md                    # live progress, created in M0
  README.md
  pyproject.toml
  uv.lock
  .gitignore
  src/model_learner/
    __init__.py
    cli.py
    domain/                   # typed models and eligibility contracts
    storage/                  # SQLite migrations and repositories
    ingest/                   # one adapter at a time
    runs/                     # explicit session->task/run association
    verification/             # verifier results and human assessments
    observations/             # immutable training/evaluation exports
    simulate/                 # known-truth synthetic generator
    learning/                 # pure estimators/calibration
    policy/                   # prediction -> user preferences -> advice
    reporting/                # summaries + diagnostics
    tui/                      # optional late-stage Textual UI
  tests/
    unit/
    integration/
    fixtures/                 # synthetic or sanitized only
  docs/
    decisions/                # short ADRs for major deviations
```

### 3.3 CLI design (target commands, not yet implemented)

```text
model-learner init
model-learner status
model-learner sessions
model-learner session show <session-id>
model-learner events --session <session-id>
model-learner import <path> --source <adapter> [--dry-run]
model-learner task create ...
model-learner run attach-session <run-id> <session-id> ...
model-learner verify ...
model-learner outcome record ...
model-learner observations export --source real|simulated ...
model-learner sim generate --seed 1 --count 1000 ...
model-learner learn predict --group <group> ...
model-learner learn eval ...
model-learner models
model-learner recommend ...        # advisory only, later
model-learner tui                  # optional later
```

Exact flags/subcommands should be finalized as they are implemented and documented in `--help`. Avoid silently changing them in later stages.

---

## 4. Data contracts and correctness rules

### 4.1 Identity hierarchy — do not confuse these

- **Native session:** an agent's own session/thread identity. One session may contain multiple tasks; a task can span multiple sessions.
- **Task:** the user's declared objective plus an acceptance specification.
- **Run:** one bounded execution of a task against a starting state and budget; may reference one or more native sessions or bounded segments.
- **Attempt/segment:** a contiguous model/configuration/strategy segment *within* a run, when observable with reliable boundaries.
- **Verification:** test, build, benchmark, or other evidence with a defined target and artifact snapshot.
- **Outcome assessment:** label with evidence and source, possibly revised later.
- **Observation:** a carefully defined learning record derived from an eligible run or experimental attempt.
- **Decision:** an advisory routing choice made at a particular time from a particular state, with candidates and selection mechanism.

Do **not** equate `native_session_id == task_id` or one failed test invocation with one failed task.

### 4.2 Minimal versioned records

The schema may evolve; preserve these semantics even if field names vary.

**Event**
- `event_id`, `schema_version`, `observed_at`, `ingested_at`, `source`, `source_version`
- `machine_id` (locally generated), `capture_method` (e.g. telemetry_import, hook, manual)
- `native_session_id`, `native_event_id` (nullable), `event_type`
- `provenance`: `observed | inferred | decided`
- normalized payload, optional raw/redacted payload, ingestion adapter version
- A stable event identity on reimport; idempotent inserts; event data not edited in place

**Task**
- `task_id`, description/reference, creation time, workspace identifier
- acceptance specification with identifier/version and optional resource budget
- task group (initially an explicit coarse label, not learned embeddings)

**Run**
- `run_id`, `task_id`, starting state/artifact fingerprint, harness
- start/end, linkage to native sessions/segments, budget/stop reason
- state: running, finished, abandoned, unknown (none implies success)

**Attempt/segment**
- `attempt_id`, `run_id`, provider, model ID + version if known, reasoning level, harness, strategy
- start/end boundaries, usage and latency with coverage and source
- Mixed-model runs are **excluded from single-configuration success-rate estimates** until an explicit attribution method exists

**Verification evidence**
- `verification_id`, run/task, acceptance-spec version, verifier type + version
- artifact reference/fingerprint, timestamp, pass/fail/indeterminate, report pointer
- `human accepted` and `automated checks passed` are distinct evidence categories

**Outcome assessment**
- `assessment_id`, run, assessor/source, observed success/failure/unknown/censored, recorded time
- assessment/evidence linkage, revision/supersession chain; never silently overwrite history

**Observation for learning**
- `observation_id`, `source_kind` (`real | simulated | benchmark`), task group
- exact action/configuration, task/run association, available-at-decision-time features
- target definition, eligible success label or missing/censored state
- cost/latency (nullable) and measurement basis; evidence ids; timestamp
- Do not let simulated or benchmark rows enter the user's personal-success summaries by default

**Decision (later)**
- candidate action set, model/policy versions, features available at decision time
- actual choice, reason, timestamp, and **known selection probability** if genuinely randomized
- For historical manual choices, probability is `null`/unknown—not an invented value

### 4.3 No false equivalences

- `unknown` **is not** `failed`.
- `tool exit code 0` **is not** “task solved.”
- `agent said finished` **is not** verified.
- `tests passed` means “the named tests passed on the named snapshot,” not universal correctness.
- `git commit merged` **is not** by itself proof that all requirements were satisfied (future data source).
- `zero-dollar estimate due to missing pricing` **is not** free execution.
- `a failure and retry inside a run` **are not** independent task observations.
- `model B completed a handoff` **is not** evidence that B could have solved the original task from scratch.
- `historical model A vs B difference` **is not** a causal estimate if the assignments were confounded.

### 4.4 Privacy and reliability

- By default, keep only the metadata necessary for the declared task; do not silently collect entire prompts, transcripts, source files, secrets, or tool-output blobs.
- If retaining full native payloads is needed for future reconstruction, make that **explicit opt-in**, with redaction and local retention policy. Keep sufficient normalized metadata to rebuild supported views.
- Never check raw private event/transcript files into Git.
- Future hooks must fail open, be bounded and quick, and avoid blocking the agent. Stable IDs survive spool/replay; a hook's success exit does not guarantee negligible latency.
- Use SQLite WAL if useful, but remember **writers are still serialized**; use short transactions, retry/busy timeout, and reliable duplicate detection.
- Preserve time of observation and time of assessment separately to avoid leaking later knowledge into earlier decisions.

---

## 5. Learning and evaluation design

### 5.1 Separate the prediction engine from the policy

The learner estimates independent quantities:

- probability of satisfying a defined acceptance criterion within a defined budget
- expected end-to-end cost (including failed attempts), with unknown pricing labeled
- latency distribution and resource consumption
- expected human interventions / retry burden (later)
- uncertainty and evidence counts/coverage

The policy combines predictions with user-specified preferences and constraints. There is **no permanent universal “best model”**.

### 5.2 Baselines before sophisticated modeling

First implement a **pure fixed-prior Beta-Bernoulli** reference estimator, e.g. for task group `g` and execution arm `a`:

```text
p(a,g) | data ~ Beta(alpha0 + successes, beta0 + failures)
```

Choose and document the fixed prior. Show posterior summaries and intervals for eligible verified labels, not a falsely precise confidence percentage. Estimate cost/latency descriptively with missingness counts initially.

Next build hierarchical/partially pooled estimates (arm across task groups, then sensible broader information sharing). Avoid overconfident plug-in empirical-Bayes intervals. Keep the numerical estimator independent of SQLite and UI.

### 5.3 Simulation and evaluation

A **seeded simulator** emits observations from known conditional success probabilities, cost/latency distributions, and configurable assignment policies. It supports:

- balanced and highly imbalanced assignment
- sparse and common task groups
- group heterogeneity
- drift/model changes at time T
- delayed verification / unknown outcomes
- correlated retries or runs, where applicable

Ground truth remains available **only to the evaluator**, never as an input feature to the estimator. A real dataset and a simulator may share a schema, but must be strictly separated by `source_kind`.

Evaluation outputs: Brier score, log loss, calibration table/plot data, grouped uncertainty coverage/width where justified, error versus known simulator truth, and comparison with global/per-arm/unpooled baselines. Use **time-ordered** validation for chronological outcomes. Check for future-label leakage.

Do **not** require that pooling beat the unpooled baseline on *every* small random sample; study aggregate performance across seeds and both favorable/unfavorable pooling scenarios. Do not mistake simulation-based calibration for proof of real-world calibration.

### 5.4 Data starvation and selection bias

A personal user's data will be sparse. Initial confidence should often be low. Use partial pooling and explicit effective sample counts rather than pretending there are dozens of nearly identical verified tasks.

Harder tasks tend to be routed to stronger models; raw success rates across models are confounded. Shadow recommendations are observational predictions; they cannot establish that an unselected model would have succeeded or saved money. Genuine exploration can come later, with action probabilities recorded at the time of choice.

Model identity and harness must be recorded as separate dimensions, including provider, version where identifiable, and reasoning level. Report drift cautiously: it may reflect changes in tasks, harnesses, environments, or model behavior.

---

## 6. Milestones — build and verify ONE at a time

**Milestone state begins as NOT STARTED.** Codex updates `STATUS.md` after working, but does not mark the next milestone as done without acceptance tests.

### M0 — Repository assessment and development foundation

**Goal:** Know what exists and establish a safe, reproducible local workspace.

**M0-A (no edits):** Codex inspects Git status, directory layout, Python environment, existing tests/code, repository remote, and any previously generated starter. Propose which files are reusable and conflicting. Produce a brief gap/risks report. **Do not overwrite existing work**.

**M0-B (after review):** If absent, add `pyproject.toml`, `src/model_learner/` with Typer entry point, pytest/Ruff dev tooling, a clean `.gitignore`, `README.md`, short `AGENTS.md`, and `STATUS.md`. Existing equivalent files should be preserved/refined rather than replaced. `model-learner --help` should work; do not implement features yet.

**Tests/acceptance:**
- `uv sync` (or audited existing setup) succeeds.
- `uv run model-learner --help`, `uv run pytest`, and `uv run ruff check .` succeed.
- `git diff` contains only scoped foundational changes; no secrets, personal data, or large generated artifacts.
- `STATUS.md` specifies the next stage and exact test outcomes.

**Stop:** Do not add database schema, external integrations, a TUI, or learner logic in M0.

### M1 — Canonical contracts and persistent outcome/event storage

**Goal:** Define data semantics early so real and simulated sources can converge safely.

**M1-A:** Typed domain models and versioned input validation for Event, Task, Run, Attempt/Segment, Verification, Assessment, and learning Observation. Start with fields actually needed by M2–M4; optional future fields can be deferred. Require explicit `source_kind`, evidence provenance, time fields, and nullable usage costs.

**M1-B:** SQLite migrations and repositories for append-only events, assessments, task/run associations, and deduplicated observations. Maintain human labels separately from reconstructible derived views. Add JSONL import/export validation and a small CLI for `model-learner init`, validation, and record inspection.

**Tests/acceptance:**
- Duplicate event import is idempotent and retains a stable ID.
- Unknown/censored labels, incomplete attribution, missing costs, and mixed execution are representable—not silently recoded.
- Bad timestamps/schema versions/evidence associations fail validation with clear messages.
- A read/export/reimport round trip keeps identifiers and labels unchanged.
- Real, simulated, and benchmark data never silently mix in summaries.

**Stop:** No real provider integration or statistical routing here.

### M2 — Simulator + simple learner reference

**Goal:** Be able to test the statistical code before substantial real data arrives.

**M2-A:** Build a deterministic, seeded synthetic generator with 3 generic model arms × 4 task groups and configurable probabilities, total-cost distributions, imbalance, drift, and missing outcomes. Keep simulator ground truth in evaluator-only structures.

**M2-B:** Pure Beta-Bernoulli fixed-prior baseline, descriptive resource metrics, and CLI (`sim generate`, `learn predict`, `learn eval`) operating only on explicitly selected datasets. Include time-ordered evaluation and global, per-arm, and unpooled reference metrics.

**Tests/acceptance:**
- Identical seed/config produces identical generated records.
- Analytic posterior checks pass on tiny hand-worked examples.
- Zero-data and very sparse groups display appropriately broad uncertainty.
- Synthetic ground truth is inaccessible in learner inputs; no train/test leakage.
- Calibration/evaluation commands explain denominators and missingness.

**Stop:** No recommendation policy, adaptive routing, or complicated hierarchical learner yet.

### M3 — Local capture from ONE agent

**Goal:** Record one real local AI-agent workflow with honest fidelity.

**M3-A: feasibility spike (no integration code until reviewed):** Check current, documented telemetry/export sources available on this machine (Codex's local supported interface, Claude Code hooks/OTel, or an existing collector such as hcli). Choose **one** integration based on actual available fields and installation friction. Validate session identity, timestamps, tool events, token/model availability, and privacy behavior. Codex must not assume the Codex desktop app exposes the same events as Codex CLI. Do not install global hooks without user permission.

**M3-B:** Implement a versioned, read-only importer/adapter with a sanitized recorded fixture and idempotent ingestion. Prefer importing/exporting a supported format over inventing a new always-on daemon. If a hook is truly necessary, keep it bounded/fail-open and test spool/replay identities.

**M3-C:** CLI session listing and observed/inferred timeline, explicit unknowns for unavailable fields. Derive summaries from retained events and verify rebuild idempotence for supported fields.

**Tests/acceptance:**
- At least one **real, user-approved local** agent session can be captured/imported and inspected with `model-learner sessions` and `model-learner session show ...`.
- Confirm representative actual events versus the displayed timeline; no fabricated model/token/tool-count fields.
- Running the same import twice does not double-count events.
- Missing native event types do not crash ingestion; malformed events produce diagnostics.
- No raw private transcripts committed. The agent still works normally with collection disabled.

**Stop:** No second agent adapter, cross-machine sync, or forced background process.

### M4 — Link sessions to tasks and assess outcomes

**Goal:** Produce the first trustworthy, real, evidence-linked success/failure observation.

**M4-A:** Task creation with explicit acceptance criteria, bounded run creation, and link to a specific native session or range. Manual association is acceptable; do not infer a task boundary from every prompt or session automatically.

**M4-B:** One automated verification adapter (for example, a named test command/report against an artifact fingerprint) and explicit human assessment. Log command exit/report, verifier version, artifact state, when verified, and source. Do not execute arbitrary verifier commands without user approval.

**M4-C:** Observation eligibility rules and a data-quality report: verified, partially verified, human assessed, unassessed, censored, mixed-model, unknown pricing. Support later assessment revision without rewriting the original evidence.

**Tests/acceptance:**
- A local captured run can be linked to a declared task, assessed, and exported as an eligible **real** observation.
- A completed-but-unverified run remains unknown; two failed internal test cycles do not become two failed tasks.
- Verification for the wrong artifact or outdated acceptance spec is flagged rather than silently accepted.
- Mixed-model handoffs do not count as clean single-model success samples.

**Stop:** This milestone ends at accurate outcomes, not “predict a best model.”

### M5 — Historical reports and useful CLI

**Goal:** Make the local workflow worthwhile before recommending anything.

**Deliverables:** Session/run history, event timeline, task/outcome links, per-arm assessed outcome counts, cost/latency coverage, test/retry/intervention summaries where observable, and basic data-quality breakdowns. Optionally export to JSON/CSV for personal analysis.

**Tests/acceptance:** Small known fixtures yield exactly correct counts and denominators; unknown labels, costs, harnesses, and model IDs never disappear silently. Reports default to real observations and clearly identify all filters.

**Stop:** Do not display counterfactual “savings” or certainty labels without evidence.

### M6 — Sparse-data learning with pooling and evaluation

**Goal:** Improve estimates beyond the fixed-prior baseline without overclaiming.

**M6-A:** Implement a small, auditable hierarchical/partial-pooling model across task groups and configurations, with posterior uncertainty and numerical/unit checks. Workspace-specific adjustments only after the data supports them. Document what is pooled and what remains independent (especially harness/model versions).

**M6-B:** Multi-seed synthetic stress tests (sparse, heterogeneous, drift, selection bias), a frozen benchmark adapter if available, and time-ordered held-out evaluation on actual data when there is enough. Compare to global, per-model, and unpooled baselines.

**Tests/acceptance:** Posterior summaries are reproducible; simulated known-probability behavior is documented; pooled estimates help in appropriate scenarios and reveal failure under inappropriate pooling. Calibration claims include sample size and method. No false guarantee of 90% coverage in all settings.

### M7 — Advisory recommendation + shadow mode

**Goal:** Turn predictive distributions into explainable *advice*, not autonomous action.

**Deliverables:** Separate utility policy (quality-first, cost-sensitive, balanced); explicit budgets/constraints; candidate estimates with intervals, sample counts, missing data, and reasons; a command to record what would have been selected without altering the actual run. The user's actual selection remains primary.

**Tests/acceptance:** Equal outcome predictions with different costs lead to the expected cheaper choice under cost-sensitive policy; higher quality can dominate under a quality-first policy; unsupported actions may be rejected rather than guessed. Shadow-mode reports do not claim unobserved counterfactual results. Historical human choices have **unknown** propensities.

### M8 — Small terminal UI (optional after M5; no new semantics)

**Goal:** Thin keyboard-driven view of the same reports and timeline as CLI.

**Deliverables:** Runs list, current/recent sessions, detail/timeline, evidence and completeness indicators, and a model comparison view. Textual is optional; the CLI remains complete without a TUI.

**Tests/acceptance:** UI displays the same counts/filters as CLI; no alternative business logic in UI; behaves acceptably when storage is empty or fields are unknown.

### M9 — Runtime difficulty, intervention intelligence, and Governor boundary (later)

**Goal:** Extend from initial model selection to updated predictions based on observed progress/struggle.

**Deliverables:** Runtime features with provenance, failure-cycle/stall signals, an explicit **checkpoint state** for learning interventions, and prediction of the additional utility of continue/retry/fresh-context/escalate/ask-human under a budget. Start advisory-only, then optional Pi integration under explicit permission.

**Tests/acceptance:** Runtime features use only data available at the checkpoint; no leakage from final outcomes; only interventions with meaningful attribution enter intervention-level comparisons. Changing a model during a run does not retroactively credit the new model for all earlier work.

**Future M10+:** Separate AI Governor (quota-aware scheduler, control permissions, automation, cross-machine workers). Its job is to act on Model Learner estimates; **do not implement it inside the first learner release**.

---

## 7. First useful local end-to-end demo

After **M0–M4**, a human should be able to:

1. Install the package locally (`uv sync` and/or development CLI installation).
2. Run one supported local coding agent normally (without special paid APIs).
3. Import/capture the session with its actual supported metadata.
4. List sessions and inspect the event timeline and missing-data flags.
5. Create a task with a declared acceptance criterion and link it to the session/run.
6. Run or attach a verifier result for an exact artifact snapshot, or label human acceptance distinctly.
7. Show the assessed outcome; export one eligible `source_kind=real` observation.
8. Reimport the same session without duplicate counting; rebuild supported summaries from the retained ledger without losing human assessments.

**Example output (illustrative only; no fabricated success or token counts):**

```text
$ model-learner run show latest
Task: parser regression / run_...
Harness: <recorded harness>
Model: <observed model or unknown>
Elapsed: <observed duration>
Tool calls: <observed count or unavailable>
Pricing: unknown (provider cost not available)
Verification: tests passed against artifact <fingerprint>
Outcome: verified against acceptance spec v1
Data quality: token usage unavailable; model version unknown
```

A milestone is not “complete” if the happy path works only on a hand-crafted fixture while the promised real-agent path has not been exercised. Label such work **code-complete, integration-pending**.

---

## 8. Test strategy and gates

**Unit tests** for versioned schemas, idempotence, provenance, labeling, pure estimators, and policies.

**Integration tests** for SQLite migrations, read-only imports, rebuilding derived state, CLI outputs and exit codes, verifier attachment, and local data privacy.

**Statistical tests** for known analytic cases, reproducibility, simulation-based stress testing, missing-label behavior, and time-ordered evaluation.

**Manual tests** for one real local session per supported adapter version and CLI readability; record tested agent version, platform, sample origin, and observed limitations in `STATUS.md`.

Suggested command baseline (adjust to actual project conventions after M0):

```bash
uv sync
uv run pytest
uv run ruff check .
uv run model-learner --help
```

No invented green checks: Codex must report the actual command and output summary (or explicitly say it could not run it). If tests fail or a dependency cannot install, identify the limitation and keep milestone status blocked/incomplete.

**PR checklist:**

- [ ] Only requested milestone/submilestone changed.
- [ ] Tests for success, failure, empty state, and unknown/missing fields.
- [ ] No unsanitized local data/secrets in Git.
- [ ] No change to unrelated public interfaces without an explicit decision.
- [ ] CLI `--help` and README updated for commands that exist.
- [ ] Actual test results recorded in `STATUS.md`.
- [ ] Review of `git diff` and rollback path.
- [ ] User has approved moving to next milestone.

---

## 9. `AGENTS.md` guidance Codex should create in M0

Keep `AGENTS.md` short (roughly the following). **Do not** paste this entire plan into AGENTS.md:

```markdown
# Repository instructions for Codex

This repository is Model Learner, a local-first CLI system for outcome-verified
AI-agent utility estimation. `MODEL_LEARNER_PLAN.md` is the technical roadmap;
`STATUS.md` records what is actually implemented and tested.

- Implement only the explicitly requested milestone/submilestone from the plan.
- Check `STATUS.md` and the relevant plan section before making milestone changes.
- Inspect existing code before editing; preserve current working behavior and avoid
  unrelated rewrites or speculative future features.
- Keep observations, inferences, and decisions distinct. Missing != failure;
  completed != verified; cost unknown != zero.
- Keep real, simulated, and benchmark datasets separated.
- Test the requested change, report actual commands/results, and record blockers.
- Update `STATUS.md` after an implementation; stop at the requested gate.
- Never silently install global hooks, publish/push/merge, or include user secrets,
  private transcripts, or unsanitized fixtures in Git.
- Prefer simple, local implementations; no service/cloud/UI without an approved need.
```

Codex may tailor this based on the existing repository, but should keep it concise and not add burdensome instructions that apply to unrelated trivial edits.

---

## 10. `STATUS.md` template and decision log

M0 creates this file and subsequent milestones update it. This is **state**, not a wish list.

```markdown
# Model Learner status

Current milestone: M0 (NOT STARTED)
Last accepted milestone: none

## Completed
- None yet.

## In progress
- None.

## Test evidence
- No tests run yet.

## Decisions
- Repository CLI name is `model-learner`.
- Local single-machine scope for v1.

## Known limitations / blockers
- None recorded yet.

## Next user-approved step
- Await M0 repository assessment.
```

When a milestone finishes, replace placeholders with files changed, actual commands/run output, manual test observations, outstanding defects, and next unstarted stage. If Codex recommends a design deviation, document it under `docs/decisions/ADR-xxxx-*.md` (only for important decisions), state benefits/costs, and request approval before changing the plan's core semantics.

---

## 11. Risks and mitigations

| Risk | Mitigation |
|---|---|
| Data starvation | Transparent low-confidence estimates; hierarchical pooling; synthetic testing **separate** from user metrics |
| Verification missing | Extremely cheap explicit acceptance/unknown labeling; do not force success/failure |
| Label bias | Show verification coverage by configuration and group; automatic sources are not inherently unbiased |
| Selection bias | Do not claim causal superiority without controlled comparisons; record true assignment propensities when known |
| Model churn | Versioned model and harness IDs, report drift, keep model-version priors appropriately weak |
| Native telemetry changes | Adapter versioning, preserved/sanitized fixtures, unknown fields stay unknown |
| Privacy | Metadata-first, opt-in raw payloads, .gitignore, local retention, no external transmissions |
| SQLite concurrency | Short transactions, busy handling, import dedup, spool only if truly required |
| Fake progress estimates | Report evidence trajectory rather than invented completion percentage |
| Scope creep | One milestone per Codex task, explicit non-goals and tests, no automatic stage advancement |
| Brand changes | Keep repo/package name as currently agreed; postpone rebranding until explicitly requested |

---

## 12. GitHub milestones and issue structure (optional)

The repo is useful because the implementation will be iterative. If using GitHub Issues, one issue per milestone/submilestone is enough:

```text
M0-A  Audit existing repository       [planning, no-code]
M0-B  Local development foundation    [foundation]
M1-A  Domain/observation contracts    [data]
M1-B  SQLite storage + CLI            [data]
M2-A  Known-truth simulator           [learning]
M2-B  Reference learner + evaluation [learning]
M3-A  Local source feasibility spike  [integration, no-code]
M3-B  Local importer                  [integration]
M3-C  Session inspection             [integration]
M4-A  Task/run association            [verification]
M4-B  Verifier + human labels         [verification]
M4-C  Eligibility / data health       [verification]
M5    Historical reporting            [reporting]
M6-A  Hierarchical learner            [learning]
M6-B  Stress test / benchmark         [evaluation]
M7    Advisory recommendations        [policy]
M8    TUI                             [interface]
M9    Runtime intervention learning   [later]
```

Avoid mirroring the entire plan into dozens of speculative issues now. Create the next handful, implement, and refine as real constraints appear.

---

## 13. Copy/paste Codex prompts

### Prompt 1 — FIRST, repository assessment (**NO CODE CHANGES**)

```text
You are working in the local `model-learner` repository. Read
MODEL_LEARNER_PLAN.md, especially §§0–4 and milestone M0.

First inspect this actual working tree (including git status, git remote,
existing Python package, tests, docs, and any current code). Do not assume
it is empty, and do not overwrite working code or import a scaffold blindly.

This turn is READ-ONLY. Do not edit files, install packages, create a branch,
modify hooks, or run commands with side effects.

Report:
1. What exists and what already works, with file paths.
2. Differences between current repo and the plan.
3. The smallest safe M0 implementation changes.
4. Any design decisions or risks needing approval.
5. Exact acceptance tests and commands you propose for M0.

Stop after this assessment. Do NOT implement M0 or later milestones.
```

### Prompt 2 — M0 implementation (after reviewing assessment)

```text
Read MODEL_LEARNER_PLAN.md milestone M0 and your earlier repository
assessment. Implement only M0-B, preserving any existing working project
structure. Create/refine a short AGENTS.md and STATUS.md as specified.

Do not start database schemas, simulation, collectors, statistical learning,
TUI, or automatic routing. Do not change global hooks or remote Git settings.

Run the specified tests/checks, fix failures that are within M0 scope, show
the exact results, and summarize files changed. Update STATUS.md accurately.
Stop after M0; wait for my review before proceeding.
```

### Prompt 3 — Template for implementing **one later milestone**

```text
Implement ONLY [MILESTONE ID AND SUBSECTION] from MODEL_LEARNER_PLAN.md.
First read STATUS.md, relevant plan section, and the code paths that this
milestone touches. Do not implement the next milestone.

Before edits, state a small file-by-file approach and any deviations needed.
Then implement with meaningful unit/integration tests, run the project's
actual verification commands, and fix in-scope failures.

Update STATUS.md with:
- files changed / behavior delivered
- command/test results (or why they could not run)
- known limitations and unresolved issues
- what should be reviewed manually
- the next unstarted milestone

Preserve data provenance and unknown values. Keep changes narrow; do not
install global hooks, access private transcripts, or alter cloud resources
without explicit permission. Finish with a concise review summary and STOP.
```

Replace `[MILESTONE ID AND SUBSECTION]` with, for example, `M1-A — domain contracts` or `M3-A — local telemetry feasibility spike`. **Do not use this template to ask for M1–M9 at once.**

### Prompt 4 — independent test/review pass (separate Codex conversation)

```text
Review the current git diff against MODEL_LEARNER_PLAN.md for milestone
[MILESTONE]. Be a skeptical reviewer. Do NOT edit files yet.

Check requirement coverage, edge cases, privacy, schema/version compatibility,
unknown/verified semantics, data leakage and statistical validity as relevant.
Inspect tests and identify any unsupported 'passed' claims.

Report severity-ranked issues with concrete paths/lines, tests missing, and
whether the milestone is safe to accept. Do not review unrelated future
milestones and do not propose a full rewrite.
```

### Prompt 5 — fix an incomplete milestone

```text
Fix ONLY the issues discovered in milestone [MILESTONE], as listed below.
Do not expand scope or start the next milestone.

[PASTE FAILING TEST OUTPUT OR REVIEW FINDINGS]

Reproduce each relevant failure, make the minimal corrective edit, rerun the
relevant test and full relevant suite, and update STATUS.md with actual results.
Show the diff summary and STOP for review.
```

### Prompt 6 — resume after days or a new Codex chat

```text
Read STATUS.md and the relevant sections of MODEL_LEARNER_PLAN.md, then
inspect git status and recent commits. Tell me what is actually complete,
what is blocked, and the smallest next milestone. Do not implement anything
until I select the next milestone.
```

---

## 14. Next action and definition of first success

**Right now:** copy `MODEL_LEARNER_PLAN.md` into the repo root, open the **local folder** with Codex, and send **Prompt 1**. Assess before coding. Follow with M0 only after reviewing its assessment.

**First engineering success:** development commands run reproducibly and the project can validate/store/reload typed records without inventing missing results.

**First product success:** M0–M4 real local run -> captured evidence -> explicit task -> verified or honestly unknown outcome -> exported observation. This is the first endpoint that tests whether the conceptual product is real.

**First learning success:** the simple baseline is calibrated against its own stated simulator assumptions and evaluated honestly on held-out observations; sparse real-world outputs surface limitations instead of confidently choosing a model.

Do not evaluate this project by the amount of code Codex produces. Evaluate it by passing tests, accurate provenance, a working local demonstration, and increasingly useful predictions.

---

## 15. References and existing design materials

These are references, not implementation dependencies and not proof that every linked project currently works with your installed agent version.

- Codex's official multi-milestone planning approach: <https://developers.openai.com/blog/run-long-horizon-tasks-with-codex>
- Official AGENTS.md/ExecPlan guidance: <https://developers.openai.com/cookbook/articles/codex_exec_plans>
- Coding-agent AGENTS.md prompting details: <https://developers.openai.com/cookbook/examples/gpt-5/codex_prompting_guide>
- Local telemetry collector candidate: <https://github.com/justinmaks/hedge-local>
- Outcome/workflow comparator: <https://github.com/o11y-dev/reflect>
- Candidate future routing harness: <https://pi.dev/docs/latest/virtual-models>
- SQLite WAL concurrency: <https://sqlite.org/wal.html>

If there are older `routelearn_*` notes in the repo, treat them as historical input and reconcile them with this plan; the active repo and CLI naming is **`model-learner`**. Do not silently rename the project based on past naming brainstorms.
