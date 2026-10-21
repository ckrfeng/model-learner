# W4A first discriminating task preparation

**PARTIAL — offline components validated; no launch authorization.** Prepared on
2026-10-20/21. No measured agent, additional model, subagent, paid inference, network
probe, install, historical private ledger read, staging, commit or push occurred.
All outcomes below describe synthetic software checks, not model performance.

W3 gate: initial branch `main`, HEAD and cached `origin/main` both
`386d54686009eb21ca5c200294c906f58f2b7793`; clean worktree/index, no existing edits.
The preceding source/test commit is `98d568a01ca9de10f3bb6bb678c9dc372b72f32b`.
Both exact W3 path groups and content are present. The coordinator's supplied
attestation says both commits and the push used GitHub Desktop. Local Git confirms
the commits and cached remote equality; no network fetch independently checked
GitHub. The existing executable local privacy hook remains configured.

## Prepared task and frozen contract

The selected source is a freshly constructed algorithmic problem: **Transactional
Dependency Graph Planner**. No unrelated repository or downloaded benchmark is
needed. Medium-to-hard is a pre-outcome assessment of interacting graph invariants,
transactional updates, lexicographic ordering, rollback and scale, not a learned
feature or retrospective outcome label. Graph algorithms are familiar; contamination
cannot be ruled out. One constructed task cannot establish broad model superiority.

The complete candidate-facing specification and deliberately incomplete source are
[`TASK.md`](../tests/fixtures/w4a/TASK.md) and
[`planner.py`](../tests/fixtures/w4a/planner.py). There are no planted unrelated
bugs. Implement only one standard-library source file. API: `GraphError(ValueError)`;
`Planner()`; four node/dependency edit methods; atomic `apply(list[tuple])`;
`nodes()`, `dependencies()`, `order()` returning detached sorted tuples. Names are
strict ASCII identifiers. Dependency direction is `(task, prerequisite)`.
Acyclicity is checked at batch end; intermediate multi-node cycles may resolve,
but malformed operations, unknown endpoints and self-adds reject immediately.
Any error rolls back all edits. Removing a node removes incident edges. Adds are
idempotent; absent-edge removals require existing endpoints. Instance state is local.

The manifest at [`experiments/w4a_preparation.json`](experiments/w4a_preparation.json)
freezes starting hashes, proposed configuration identities, reserved Task identity,
all 15 required JUnit case identities, protected component hashes and policy state.
The Task ID is a proposal only; no live Task/Run/Attempt has been created.
Changes to this frozen contract require a versioned re-review before forecasting.

Independent acceptance has explicit API/edge/compound/failure cases, all 64
three-node directed graphs, 24 seeds × 100 transactional batches, instance/input
isolation, deterministic replay and metamorphic checks. A separate immutable
small-state oracle enumerates permutations; it does not import the reference.
The trusted reference uses copied state and heap-based Kahn ordering. Analytic
anchors include the 25 labeled three-node DAGs. These are separately implemented
by the same preparation executor; no independent person/model review is claimed.

Performance uses an 8,000-node chain, a 2,000-node/24,000-edge DAG and 20 reversible
updates, with three fresh trials: median <=10 CPU seconds, each <=20 CPU seconds.
A 30-second per-trial wall timeout is an infrastructure failure, not a binary
failure label. All three reference trials must be <=2 CPU seconds on the eventual
isolated runtime before cohort freeze. Current host trials meet that threshold;
future runtime calibration is still required. No post-outcome threshold changes.

## Private package and verification

Only new files created in `.model-learner/w4a-preparation-v1/` were inspected.
Existing ignored private evidence was not opened. The package contains:

- `protected/`: `reference.py`, `oracle.py`, `test_acceptance.py`, `test_oracle.py`,
  `test_preparation_controls.py`, `verify_preparation.py`.
- `protected_manifest.json`: exact protected/start hashes and required test IDs.
- `workspaces/{luna-low,sol-low,sol-high}/`: identical `TASK.md` and `planner.py`.
- `probe/`: seven newly authored public synthetic canaries, never real credentials,
  private ledgers or source data.
- `reports/`: reference/starter JUnit, receipts, performance measurements, protected
  and focused regression reports, isolation and same-user read-control results.
- `inventory.json`: exact relative file inventory and digests (excluding itself).

The protected directory is ignored and mode 0700. That is accidental-exposure
hygiene only: a same-user process can still read it. It is **not proven protected
from a measured agent**. Hidden files never enter the two-file starting snapshots.
Do not give a candidate this checkout, its parent, the private package, forecasts,
reports, another arm's workspace, credentials or the original project.

Offline verification commands, from the repository root, with unique report names:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  .model-learner/w4a-preparation-v1/protected/verify_preparation.py \
  reference --report-name reference-review
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  .model-learner/w4a-preparation-v1/protected/verify_preparation.py \
  starter --report-name starter-review
W4A_CANDIDATE="$PWD/.model-learner/w4a-preparation-v1/protected/reference.py" \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv/bin/python -B -m pytest -q -c /dev/null \
  --rootdir=.model-learner/w4a-preparation-v1/protected -p no:cacheprovider \
  .model-learner/w4a-preparation-v1/protected
```

The minimal runner accepts ONLY the known reference and starter, verifies every
frozen input, refuses report overwrite, records actual completion/exit and hashes,
and requires exactly all test identities without skips. It does not launch agents
or write learner records. It runs known preparation code in-process with tests;
**it must not be extended to arbitrary submissions without verified isolation**.
It is not an adversarial code sandbox or a hard process-tree resource controller.
An initial runner diagnostic incorrectly classified the failing starter as a wall
timeout because traceback source contained the timeout literal. This was repaired
to inspect the actual JUnit failure message; both initial and corrected local
reports are retained. Final starter result is complete failure, as expected.

For future submissions, the operator must stop the agent and all descendants,
collect only a regular bounded `planner.py` without links, freeze it, and execute
trusted acceptance against that exact file in a separately validated environment.
Candidate code must also be denied access to tests, oracle and receipt writers
(e.g. a restricted worker behind a trusted test driver); mounting hidden tests
read-only alongside hostile Python is insufficient. This backend is missing.
Bind the final file SHA-256, test-source hash, required IDs, JUnit SHA-256, actual
UTC report time, completion and exit code to the Task/Run/Attempt/acceptance version.
Reuse existing `JUnitReportBinding`, `verify_junit`, assessment and receipt contracts;
retain incomplete reports as indeterminate. Never accept the agent's own report.

## Models, commands and containment

Permitted local evidence: `codex --version`, `codex exec --help`, selected fields
of the local model metadata cache, and the installed app's declared model options.
Harness: `codex-cli 0.163.0-alpha.10.2`; Python: 3.12.14 on macOS arm64.
CLI help emitted a PATH-alias permission warning; no inference was performed.

| Arm | Provider / requested ID | Effort | Local metadata | Advertised context |
| --- | --- | --- | --- | --- |
| luna-low | openai / gpt-6-luna | low | Listed, effort supported | 272,000 |
| sol-low | openai / gpt-6.1-sol | low | Listed, effort supported | 500,000 |
| sol-high | openai / gpt-6.1-sol | high | Listed, effort supported | 500,000 |

Cache time/client version and canonical configuration IDs are in the manifest.
These are local support findings, not authenticated entitlement or successful
backend availability. Effective revision is null for all arms. Context windows
are advertised capacities, not enforceable total-token ceilings. No substitutions.

Exact **proposed inner argv**, also stored per arm in the manifest:

```sh
codex exec --ignore-user-config -c 'approval_policy="never"' --ignore-rules \
  --strict-config --ephemeral --json --skip-git-repo-check --sandbox workspace-write \
  --model gpt-6-luna -c 'model_reasoning_effort="low"' --cd /candidate/luna-low -
codex exec --ignore-user-config -c 'approval_policy="never"' --ignore-rules \
  --strict-config --ephemeral --json --skip-git-repo-check --sandbox workspace-write \
  --model gpt-6.1-sol -c 'model_reasoning_effort="low"' --cd /candidate/sol-low -
codex exec --ignore-user-config -c 'approval_policy="never"' --ignore-rules \
  --strict-config --ephemeral --json --skip-git-repo-check --sandbox workspace-write \
  --model gpt-6.1-sol -c 'model_reasoning_effort="high"' --cd /candidate/sol-high -
```

Stdin must be the frozen TASK.md bytes. These commands were **not run** and are
**not a complete or safe launch command**. `/candidate/...` is a proposed isolated
mount, not a current host path. Fresh sessions, empty candidate-visible home,
no project/user skills or integrations, and controller-only auth/transport remain
to be implemented and verified. Model transport requires an approved broker;
"no networking" applies to agent tools, not pretending remote inference is offline.
Ignoring config does not isolate credentials. These flags do not supply read
containment, a 600-second watchdog, integration denial or process-tree limits.

Actual non-agent probes reused existing `probe_macos_containment()`:
`sandbox_bootstrap_unavailable`, exit 71; allowed reads/writes never began, all
outside/symlink/descendant denial results unknown. A separate same-user control
read all seven synthetic canaries from the candidate folder, proving directory
separation alone insufficient. No sensitive canary targets were opened.
The existing offline diagnostic reports `image_approval_required`; no Docker
image/container/network probe was launched. `require_supported_real_containment()`
still refuses collection unconditionally. No guard was weakened. There is no
launch authorization or prepared launch wrapper.

## Resource and forecast policy

Propose exactly three invocations, one per listed arm, sequentially, one active
agent and one candidate attempt each; no extra workers, automatic retries, repairs
or replacement of missing runs. Proposed arm order is luna-low, sol-low, sol-high;
this tiny fixed order is confounded with time and cannot support causal ranking.

| Resource | Proposal | Actual enforceability now |
| --- | --- | --- |
| Wall stop | 600 seconds/arm, 1,800 cohort seconds | Missing validated external agent/process-tree watchdog. |
| Tokens / money | No invented numeric cap | Installed exec interface offers no demonstrated hard token/dollar cap. |
| Subscription | Existing ChatGPT allowance only, if separately approved | No measured usage authorized; allowance consumption is not guaranteed zero cost. |
| New spend | No purchased credits, API billing or vendor service | No purchase or inference performed; future transport/account mode must be verified. |
| Local CPU/tests | Existing local interpreter and test tools | Used offline; reference timings measured. Agent CPU/RAM/PID/disk caps remain unvalidated. |
| Verifier | 30-second trial wall timer, 120-second preparation subprocess timeout | Exercised only on trusted fixtures; no adversarial process-tree guarantee. |

If the user requires a numeric token or dollar maximum, these proposed arms cannot
launch through the currently demonstrated interface. A wall stop does not bound
in-flight billing, token production or provider-side cancellation lag. Stop the
cohort on containment, identity, integrity, allowance or infrastructure ambiguity;
record unknown/censored outcomes without retrying.

No execution-specific forecasts have been issued. Future dataset proposal:
`source_kind=benchmark`, ID `w4a-constructed-dag`, version `1`. Its constructed origin
must remain distinct from ordinary personal work; today's preparation fixtures are
simulated. Historical Experiment 4 aggregates and all private histories are excluded.
No approved prior observations exist here: expected cold start is Beta(1,1), mean
0.5, 95% interval [0.025, 0.975], zero evidence for every policy and arm. These are
policy illustrations, not frozen execution forecasts or evidence of equal ability.

Before any execution freeze task, all configuration snapshots/families, source
universe/dataset, acceptance/tests, resource target, cohort/order and one UTC cutoff.
Freeze all 18 arm × predictor entries together and preserve an external digest;
no arm may start until every entry exists. Use existing pure `forecast` for A/B/C,
`BetaBernoulli.fit` for global/per-arm and empty inputs for the fixed prior. All
share Beta(1,1), the same eligible universe/cutoff/acceptance/budget, and whole-target-
Task exclusion. The baseline estimator does NOT itself exclude the target Task:
filter it explicitly before fitting. Per-arm preserves exact configuration;
B/C families keep all three model/effort combinations separate. Unknown labels,
identity or revision remain unknown; invalid membership abstains.

For admitted evidence require verified binary labels, one independently attributed
complete run, unique stable keys, correct target/budget/dataset, and all decision,
record, label and first-receipt availability gates. Score frozen predictions before
learning; first-arm outcomes cannot affect any sibling forecast. A/B/C use existing
selection rules; global pools admitted arms intentionally. Report Brier/log loss
and missingness descriptively; with one task no calibration or superiority claim.

**Additional integration gap:** W2 receipt reconstruction and the normal observation
builder resolve `real` data. The existing benchmark exporter has its own containment
and fixture contracts and marks any non-null resource budget ineligible because
budget measurements are unsupported. W4A proposes `max_duration_seconds=600`, not
silently nulling a real budget to gain eligibility. This new task's benchmark
receipt/budget path has NOT been integrated. Preserve independent results as
unscored/ineligible until a separately approved adapter/measurement contract exists.
Do not relabel benchmark rows as real or mutate estimators/schemas to bypass this.

## Validation and operator decision

Final results: 15/15 reference acceptance tests; starter 0/15 (all expected complete
failures); 26/26 protected tests (15 acceptance, three oracle, eight preparation
controls); nine public manifest/policy checks. Final required IDs and file hashes
match; three starting workspaces match byte-for-byte. The protected controls reject
tampered source/test/oracle, arbitrary runner input and missing/skipped/malformed
reports. Final regression/Ruff/privacy results and exact commands are in STATUS.
All ignored results, including initial diagnostics, remain available locally.

**Single approval packet:** accept the task/contract and three proposed arms as the
preparation baseline, then authorize a bounded offline containment and benchmark
receipt/budget integration increment. It must demonstrate read/write/network,
credential, cross-arm and verifier isolation, descendant termination and the
600-second watchdog on the actual runtime before asking to consume allowance.
This is the smallest next decision; it is not W4B launch approval. After those
checks, separately approve these exact arms/task, three allowance-consuming runs,
1,800 seconds of process exposure and the uncapped token/monetary risk (or require
another interface that enforces numeric ceilings). Re-freeze any affected identities
and forecasts. Opening this package performs nothing; W4B/W5 have not begun.

Proposed GitHub Desktop groups; coordinator alone reviews/stages/guards/commits:

1. `test: prepare transactional graph pilot contract and checks` — fixture TASK.md,
   fixture planner.py, public manifest, `tests/unit/test_w4a_preparation.py`.
2. `docs: record W4A preparation evidence and launch blockers` — this document,
   `STATUS.md`.

No private file belongs in either group. The staged privacy guard remains mandatory
for the coordinator after staging. There are no production, schema, algorithm,
dependency, Git-policy or historical evidence changes.
