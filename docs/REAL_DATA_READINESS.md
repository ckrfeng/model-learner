# Real execution/outcome readiness — 2026-10-13

The smallest practical path is to collect the next **5–10 explicitly bounded,
operator-run Codex CLI coding executions**, using the existing ledger, metadata
capture, JUnit importer and outcome builder. No new collector, learner, routing
layer or semantic integration is needed for this collection pilot.

There is **one eligible real observation and zero eligible real coding
observations** in the inspected local ledgers. The eligible record is the existing
fixed-reply smoke execution, not a coding-quality sample. Today’s independent
checks pass on all three selected project artifacts, but cannot recover their
historical execution attribution. Prior semantic comparison results and production
semantics remain unchanged. No models were trained during this assessment.

## Existing capabilities and gaps

Read AGENTS, STATUS, master-plan sections 4/5 and M3/M4/M6, and the observation,
verification, resolution, execution-analysis and evaluation documentation; checked
the corresponding implementation. Some early documents describe limits before
later increments: JUnit support and historical assessment resolution now exist.

| Capability | Working behavior | Practical limit |
| --- | --- | --- |
| Identity and persistence | Versioned Task, Run, Attempt, Session, explicit associations; SQLite and validated JSONL import/export; nullable telemetry | Sessions and chat turns do not establish task or attempt identity. Some declaration/verification receipt times are absent. |
| Execution observation | `capture codex`, `import codex`, `sessions`, `session show`; metadata projection, receipt envelopes, replay handling | Supported real builder requires Codex CLI events. Default capture omits prompts, commands and outputs; receipt spans are not measured execution latency. |
| Conversation observation | Selected conversation importer, provenance and bounded text projections | Useful for task requirements; not execution telemetry. Returned project-chat views expose turn times/tool activity but no configuration/usage. Historical settings stay unknown. |
| Configuration | Deterministic ExecutionConfiguration snapshot; explicit contiguous attempts; conflicts with emitted model/provider fail attribution | Builder requires a known model and manually declared segment coverage. Declarations remain declarations, not native observed configuration. Mixed or incomplete runs are excluded. |
| Independent verification | Exact-byte file verifier; JUnit importer binds report, task/run, acceptance version and final artifact; complete pass/fail produces separate assessment | File hashes establish identity, not program correctness. Operator must execute trusted checks and honestly supply completion/exit/report receipts. No automatic directory snapshot or test runner. |
| Outcomes/observations | Append-only assessments, supersession, eligible/ineligible real derivations and quality reports; resolver selects one head per run at cutoff | Human acceptance alone remains unverified. Unknown/censored/partial/mixed records do not supply binary labels. Historical derivation availability is conservative. |
| Success estimation | Beta(1,1) reference, exact configuration × declared task group; explicit real dataset, target/version, budget and cutoff | Each target is filtered separately. No arbitrary task-description or semantic-feature learner; sparse data gives broad uncertainty. |
| Chronological evaluation | Global/per-configuration/unpooled references; Brier/log loss/calibration; separate train/score cutoffs and assessment resolution | No current real coding cohort to evaluate; related retries/tasks are not independent evidence. |
| Feature experiments | Separate fixed-checkpoint logistic experiment and optional representation experiments | Real examples require independently resolved labels, retained events and input-availability receipts. Semantic extraction has not been validated as utility input. |

Core code: `domain/models.py`, `adapters/codex.py`, `adapters/conversations.py`,
`runs/`, `verification/`, `observations/`, `learn/estimator.py`,
`learn/evaluation.py`, and `learn/task_state.py` under `src/model_learner/`.

## Current inventory and three-project feasibility

Read-only aggregate queries inspected six existing local SQLite ledgers. Only the
verification-smoke ledger has observations: one unknown derivation and one eligible
verified-success derivation for the **same run**, in separate cohorts. Read-only
repository resolution revalidated the eligible cohort: one row, one eligible run,
no exclusions. A separate actual JUnit producer-validation ledger contains one
verified assessment but no attempts or observations and was not an agent coding
execution. Other inspected ledgers contain no learning observations. These counts
cover inspected local evidence, not every historical execution on the machine.

The user approved bounded reads of the three selected project chats, inspection,
and local verification. The returned views contain 3, 4 and 4 turns respectively;
all returned turns have start/end times and pagination reports no more turns.
That establishes exposed view coverage only. It does not prove original-history
completeness or identify 11 independent executions. Initial work, later revisions,
checks and explanatory responses must not be silently treated as interchangeable
attempts. No historical model/provider/reasoning/version, token/cost measurements,
per-turn artifact snapshots or acceptance/report bindings were recovered.

| Project | Independently checked current artifact | Historical learner feasibility |
| --- | --- | --- |
| JSONL Validator | Existing suite: 27 passed. New independent checks: 3/3 passed, covering valid Unicode/whitespace, invalid records/physical line reporting, and encoding/argument errors. The prior three passes were user-supplied background; these are fresh bounded checks. | Useful current acceptance evidence and future coding-task family. No supported captured run/configuration/attempt or historical artifact/report binding; zero eligible coding observations. |
| Markdown Indexer | Existing suite: 22 passed. New independent checks: 4/4 passed, covering recursive fields/JSONL, hidden and excluded subtrees, title fallback/Unicode, empty/error inputs. | Scope changed from CSV to JSONL and added exclusions. Current checks address the final artifact; do not apply them to an earlier acceptance version or infer earlier-artifact correctness. Same execution-attribution blockers. |
| Job Status Selection | Existing suite: 8 passed. New independent checks: 3/3 passed, covering all 24 permutations of interleaved offset-aware events, equal-instant last-event ties, and empty/fractional inputs. | Useful regression-task family. Turn/tool timestamps are insufficient for configuration or final-snapshot attribution. Same execution-attribution blockers. |

All test processes completed with exit 0. New checks use independently authored
synthetic inputs and expected results, outside the producing chats. Existing
agent-authored tests were rerun separately and are not described as independently
authored acceptance criteria. Tests ran on private byte-identical copies. Before/
after manifests confirm original files and tested copies unchanged. A private
JUnit report, command completion/exit/time receipts and SHA-256 fingerprints bind
the current checks to retained artifacts. These are **post-hoc current-artifact
checks**, not preregistered historical acceptance or new agent executions; they
create neither historical ledger associations nor eligible learning rows.

Do not create retroactive tasks/attempts with guessed times/settings to force these
reports through the builder. Historical outcome evidence can be kept as private
research. To reuse any project prospectively, declare a new task/version and a
new execution from an explicitly recorded starting state. A verification-only
rerun of already completed code is not another coding-agent trial.

## Minimal collection workflow

Collect five upcoming genuine coding tasks first; extend to ten if useful. Keep
one explicitly chosen configuration for the first batch to simplify attribution.
Choose ordinary supervised local work within an authorized scope. This uses the
existing observational CLI, not the separate benchmark real-execution controller,
whose containment gate remains blocked. Do not bypass that controller or relabel
benchmark/simulated fixtures as personal real observations.

Keep everything private under an ignored pilot directory. Use one stable machine
identifier and one new `source_kind=real` dataset ID/version. Do not mix the smoke
record into the coding cohort. The operator launches the agent and trusted tests;
Model Learner imports evidence.

1. **Before execution:** write the task objective, boundaries of scope and named
   independent acceptance tests. Freeze their source/version and required JUnit
   identities (`classname::name`). Create the Task with `task create` and repeated
   `--required-test`; keep its returned UUID. Record a starting-code manifest,
   runtime/test environment, explicit configuration JSON and approved launch
   options in a local receipt. Record known provider/model/reasoning/harness and
   versions only when supported; keep unavailable fields null. Per-run receipts
   belong outside configuration metadata, so timestamps/IDs do not accidentally
   create a new configuration arm for every run.
2. **Execute externally:** capture the selected `codex exec --json` stream with
   `capture codex` into a unique private file. Record actual operator launch/stop
   times, process completion/exit, requested/effective settings where known and
   any configuration transitions. Preserve capture receipt times as receipt
   times; leave native times, execution latency and costs unknown when absent.
   No full private transcript retention is required.
3. **Close and associate:** import the capture, inspect diagnostics/session IDs,
   and freeze the final code snapshot before independent testing. Use `run create`
   with explicit time bounds and final artifact; use `run attempt` for the actual
   contiguous configuration segment(s). The current convenience CLI creates
   bounded runs/attempts after closure; pre-execution task/configuration/launch
   receipts preserve provenance without falsely claiming these IDs existed early.
   One deliberately fresh, single-task CLI invocation can justify one bounded run
   and one unchanged configuration segment. That does not justify the same mapping
   for an arbitrary conversation. Keep interrupted, mixed and missing records.
4. **Verify independently:** with the agent stopped, run frozen trusted acceptance
   tests against the frozen artifact and generate bounded pytest/JUnit XML. For a
   multi-file project, retain an exact archive or canonical content manifest that
   identifies every tested dependency; the operator binds the executed files and
   environment to it. The verifier hashes one file, not the whole working tree.
   Preserve actual report generation time, XML digest, artifact digest, completion
   and exit code in a `JUnitReportBinding` JSON receipt. Missing receipt facts stay
   null; never use the agent’s final message as a receipt.
5. **Record:** `verify junit`, then `outcome assess --verification-id`, then
   `observations build`. No evidence means unknown; incomplete/skipped reports
   remain indeterminate. A complete independently failing acceptance report gives
   one failed run, not one failure per internal test. If acceptance evidence changes,
   append an assessment with `--supersedes` rather than overwriting it.
6. **Audit the batch:** use `observations quality` for derivation/missingness counts
   and `observations resolve --cutoff` for one latest supported row per run. Export
   real observations locally. Review capture gaps, configuration coverage, evidence
   bindings and unknowns before any separately authorized learning.

Existing command sequence (substitute actual IDs, paths and aware recorded times):

```sh
uv run model-learner init --database .model-learner/pilot/ledger.sqlite3
uv run model-learner task create "PREEXECUTION_OBJECTIVE" \
  --acceptance-id TARGET_ID --acceptance-version VERSION \
  --task-group coding-regression --required-test 'CLASSNAME::TEST_NAME' \
  --database .model-learner/pilot/ledger.sqlite3
# External approved agent invocation pipes its JSON stream to:
uv run model-learner capture codex .model-learner/pilot/run-01.capture.jsonl \
  --source-version RECORDED_CLI_VERSION
uv run model-learner import codex .model-learner/pilot/run-01.capture.jsonl \
  --machine-id STABLE_MACHINE_ID --database .model-learner/pilot/ledger.sqlite3
uv run model-learner run create TASK_UUID --session-id SESSION_UUID \
  --started-at ACTUAL_START --ended-at ACTUAL_END --artifact FINAL_SNAPSHOT_FILE \
  --database .model-learner/pilot/ledger.sqlite3
uv run model-learner run attempt RUN_UUID --configuration-file CONFIGURATION_JSON \
  --started-at ACTUAL_START --ended-at ACTUAL_END \
  --declaration-source operator-launch-receipt --database .model-learner/pilot/ledger.sqlite3
# Operator runs the frozen acceptance checks and writes the binding receipt.
uv run model-learner verify junit RUN_UUID REPORT_XML \
  --artifact FINAL_SNAPSHOT_FILE --binding-file BINDING_JSON \
  --database .model-learner/pilot/ledger.sqlite3
uv run model-learner outcome assess RUN_UUID --verification-id VERIFICATION_UUID \
  --database .model-learner/pilot/ledger.sqlite3
uv run model-learner observations build RUN_UUID --outcome-id OUTCOME_UUID \
  --dataset-id personal-coding-pilot --dataset-version 1 \
  --database .model-learner/pilot/ledger.sqlite3
uv run model-learner observations quality --dataset-id personal-coding-pilot \
  --dataset-version 1 --database .model-learner/pilot/ledger.sqlite3
uv run model-learner observations resolve --dataset-id personal-coding-pilot \
  --dataset-version 1 --cutoff ACTUAL_AUDIT_TIME --database .model-learner/pilot/ledger.sqlite3
```

Use `--database .model-learner/pilot/ledger.sqlite3` on **every** pilot command that
reads/writes the ledger; initialization alone does not change the default database.
The capture command shown is a stream consumer, not an agent launcher. Run from
the Model Learner checkout or its installed environment. Trusted acceptance
commands depend on the selected future projects and are fixed before those runs.

The minimum private per-run receipt includes Task UUID/description/creation time;
acceptance ID/version/test-source hash/test IDs; actual launch/settings source;
Run and Attempt IDs once created; segment bounds and boundary basis; capture and
native-session references; starting/final artifact manifests; operator environment;
verification/report/binding/assessment IDs and availability times; dataset identity;
and explicit missingness reasons. Existing models hold the canonical fields;
existing metadata and ordinary local receipts cover declaration provenance and
environment facts. No new infrastructure is necessary.

## Utility-learning readiness and eventual feature comparison

One additional correctly captured, attributed and independently verified coding
execution is sufficient to exercise the existing real estimator on a coding
target. Required information is the Task/Run/outcome/evidence association, supported
CLI capture, bounded complete known-model configuration coverage, matching versioned
acceptance and final artifact, and honest decision/record/label-availability times.
Unknown provider/version/reasoning are retained; model is required by the builder.
Missing cost/tokens/latency do **not** prevent binary-success learning when there
is no declared resource limit requiring them. They prevent resource estimates or
budget compliance claims. Do not remove a real budget merely to obtain eligibility.

Five to ten tasks are a collection-quality pilot, not evidence of predictive
improvement. Different acceptance IDs/versions and budgets form different estimator
cohorts. Ordinary task-specific test suites may leave one sample per target. Never
rename unrelated acceptance targets to manufacture sample size. A later repeated
task family can share an actual frozen acceptance contract if substantively valid;
otherwise a suite-level target needs separately approved design. Even a common
task-group label does not bypass target filtering. Configuration comparisons from
manually assigned projects remain confounded by task difficulty.

Reliable initial features are declared task group/type, language/environment when
explicitly recorded, acceptance version and exact configuration with missingness.
Only task group/configuration currently enter the Beta-Bernoulli predictor. At a
predeclared checkpoint, supported event/tool counts, observed tool failures and
token counts with coverage/missingness can support the separate existing feature
experiment. A tool failure is not a failed task. Final tests, completion claims,
final costs, repaired code, and after-the-fact descriptions are unavailable initial
predictors. Difficulty, intent/scope inferred from prose and semantic task state
are not validated utility features. Pre-execution description length, if retained,
is an observable measurement, not established difficulty or predictive signal.

Eventually compare metadata-only and metadata-plus-semantic variants on **the
same eligible runs**, horizon, target, budget and chronological partitions. Freeze
semantic extractor/schema and source-only input prefixes before outcomes; record
input availability, unknowns and human-adjudicated extraction quality separately
from independent execution outcomes. Fit transformations only on the training
prefix; exclude training-related retries/task families from holdout; report paired
Brier/log-loss differences, calibration denominators and task/family dependence.
Use identical rows or report a separate coverage analysis so semantic missingness
does not select a favorable scoring cohort. Existing feature C uses observed
failure-state metrics, **not** the unvalidated semantic extractor; the optional
representation experiment is also a separate offline research path.

The current task-state experiment requires at least 30 eligible training labels,
20 scored labels, five task clusters in each partition and both training classes;
these floors do not guarantee adequate statistical precision. Its real inputs also
need initial task/configuration/run/session availability by decision time and
retained checkpoint event receipts. After-close CLI associations alone cannot
establish that contract. Initial semantic prediction snapshots and their downstream
feature adapter are likewise not supplied by this assessment. Retain prospective
receipts now; design any missing evaluation contract separately if that comparison
is later requested. Do not backdate rows or lower floors for the 5–10-run pilot.

## Exact next actions and blockers

1. Select the first five actual upcoming coding tasks and one explicit configuration;
   choose the ordinary CLI path if eligible utility observations are the priority.
2. Before the first invocation, create its Task, freeze trusted acceptance tests,
   record configuration/starting-state receipts and choose a private pilot dataset.
3. Capture, freeze, independently verify and record that one execution with the
   commands above. Check its eligibility reasons before repeating the workflow.
4. Complete five, optionally ten, and review unique-run counts, verification and
   missingness. Stop at the collection report; seek separate direction for fitting
   or expanding evaluation. A verified failure is useful data; do not discard it or
   count retries as independent successes.

Historical blockers are unsupported CLI capture/attribution and absent snapshot/
acceptance/report bindings; passing today cannot repair them. Prospective collection
has no missing production capability, provided CLI execution is acceptable and
independent frozen checks/operator receipts exist. A desktop-only requirement
would need a separately authorized supported execution-observation/attribution
increment. Cross-task pooling and semantic checkpoint evaluation have the distinct
target/availability/sample-size blockers above. No benchmark containment change is
part of this recommendation.

Private source identifiers, project code, test sources, XML, manifests, commands,
local paths and per-turn evidence remain under ignored local storage. Public
findings contain only sanitized behavior and aggregate counts. No production code,
dependencies, model configuration, database history or acceptance semantics changed.
