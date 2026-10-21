# Prospective configuration/task-family comparison

`model_learner.learn.prospective` is a small pure experiment adapter around the
existing Beta-Bernoulli estimator. It launches nothing, writes no ledger records,
and changes neither configuration identity nor the estimator. Private task plans,
source snapshots, policies, forecasts and evidence stay in ignored storage.

A versioned `CompatibilityPolicy` explicitly admits configuration snapshots and
Task UUIDs. It records dataset, acceptance contract, budget, narrow task groups,
broad task families and declaration time. Every family preserves provider, model,
model version, reasoning effort, harness, configuration version and behavioral
metadata. Explicitly admitted harness versions may differ. Only descriptive
`settings_source` and `model_version_basis` metadata wording is ignored in the
compatibility check. Unknown backend versions remain unknown, not proven equal.
Exact canonical records and their snapshot hashes are never rewritten.

For a prediction on an admitted configuration and held-out Task:

- A uses exact configuration × narrow task group, the existing unpooled reference.
- B selects the declared configuration family and same narrow task group.
- C selects the same configuration family and broader task family.

B/C use the existing global Beta calculation **after** these restrictions, so
low/high efforts and different models cannot be pooled accidentally. Existing
`per_arm` shares groups only within an exact configuration; unrestricted `global`
would erase effort distinctions. Neither alone implements the whole comparison.
All variants retain Beta(1,1), eligibility, target/budget filtering and numerical
credible intervals. Full pooling is an explicit exchangeability assumption, not
a learned compatibility classifier, hierarchical estimator or difficulty model.

Before calling the pure `forecast` function with real data, resolve the historical
ledger through `resolve_real_observations` at the prediction cutoff. Portable
observations and their declared timestamps are not independently authenticated by
the adapter. Only available earlier decisions/records/labels can contribute. All
runs of the prediction Task are excluded, including its other arm. Duplicate rows
count once. Reports retain source evidence keys/run IDs, counts, exclusions and a
policy fingerprint. Prediction objects contain only frozen scalar/tuple fields.

Use `freeze(path, bundle)` to create a new forecast file exclusively. It returns a
SHA-256 for an independent preparation manifest and makes the file read-only.
`score_frozen(path, expected_sha256, resolved_outcome)` validates that digest and
Task/run/configuration/group/dataset/acceptance/budget binding. It requires an
eligible verified binary outcome available after the forecast and computes Brier
and natural-log loss from the saved probabilities without fitting. An externally
supplied trusted manifest matters: file permissions/hashes are not cryptographic
attestation against an operator replacing both the forecast and manifest.

For each matched task freeze both arms before either execution, score before
updating the next task's evidence, retain failures and report unscored unknowns.
A first task in a new cohort is prior-only. Whole-task chronological evaluation
supports limited future-task claims; repetitions of one task do not. With only a
few tasks, report per-task paired differences and conditional posterior intervals,
not reliable calibration, significance or general configuration superiority.
Runtime, tokens and cost are separate descriptive measurements with missingness.

The existing observation builder excludes runs with an unmeasured active resource
budget. If native duration is unavailable, retain `resource_budget=None` and record
the external process safety stop separately; do not invent canonical latency from
operator wall time. A new budget target needs its own measured, validated cohort.
Future runtime membership requires explicit review before affected outcomes and
new forecasts; do not overwrite historical predictions or admit versions based
on observed performance. If only one runtime is admitted, B equals A and runtime
transfer has not been tested.

## W1 addition — Experiment 4 reconciliation (2026-10-20)

[Sanitized reconciliation v1](experiments/experiment_4_reconciliation.json) is a
review record, not a ledger import, a forecast file or a receipt. No suitable
public Experiment 4 manifest exists in the permitted inventory. This one JSON
sidecar uses the existing `docs/experiments/` aggregate-artifact convention; its
explicit version does not introduce a schema framework or change canonical
storage. It retains four task aliases T1–T4, two execution arms Low/High per task,
and three separate forecast policies A/B/C. Eight reported executions are four
paired tasks, with possible repository/module/family dependence.

T1/T2 were corroborated in the earlier research checkout through sanitized
summaries: **inherited corroboration, not a fresh audit of raw executions**.
This increment directly inspected those same public STATUS summaries, including
reported tokens and verification counts. T3/T4 remain later user-reported
successful executions. The earlier report found T3 unstarted in its checkout and
did not corroborate final T3/T4; the scopes describe different chronology, not a
false user report. No permitted final T3/T4 artifacts were found. Exact identities,
cutoffs, receipt times, hashes and bindings absent from these summaries remain
null with reasons. New aliases are not canonical Task/Run/Attempt/Session IDs.
Inspection of a sanitized summary is not independent artifact verification.

The manifest labels direct document inspection, inherited research statements,
user reports, deterministic arithmetic and unknowns at the claim level. T1 Low/
High process times 51.994/96.723 s and T2 88.488/128.693 s are attributed to the
research report (also present in STATUS). These are operator process durations,
not native execution latency. T1/T2 native token aggregates are attributed to
STATUS; cached-input and reasoning-output counts are subsets. T3/T4 durations
and tokens, verification overhead, effective backend revisions and actual charges
remain unknown. Earlier CSV/seed experiments are not part of these eight runs.

Original frozen files/hashes were unavailable in the permitted scope. T1/T2
summary probabilities match the first two reference positions; T3/T4 cannot be
matched to original values. The following is a **conditional arithmetic check**,
not reconstructed forecasts, rescoring of independently verified records or new
predictions from later outcomes. For y=1 at each position, each arm has:

| Policy | Reference probabilities T1–T4 | Mean Brier | Mean natural-log loss |
| --- | --- | ---: | ---: |
| A | 1/2, 1/2, 2/3, 2/3 | 0.180556 | 0.549306 |
| B | 1/2, 1/2, 2/3, 2/3 | 0.180556 | 0.549306 |
| C | 1/2, 2/3, 3/4, 4/5 | 0.115903 | 0.402359 |

Brier is `(p-y)^2`; log loss is `-[y ln(p)+(1-y) ln(1-p)]`.
A/B Brier is `13/72`, log loss `ln(3)/2`; C Brier is
`(1/4+1/9+1/16+1/25)/4`, log loss `ln(5)/4`. Averaging the two
arm losses within each task and then the four tasks equals averaging all eight
arm losses here. This equality does not create eight independent observations.
Rounding tolerance is 0.0000005. A cumulative matching-arm Beta(1,1) baseline with
0, 1, 2, 3 prior successes and no failures gives `(1+s)/(2+s)`, exactly C's
sequence and scores. C's benefit over evidence-starved A/B cells establishes no
advantage over that matched baseline, learned difficulty, discrimination,
calibration, compatibility transfer or model-selection superiority. All-success
pairs establish neither Low/High quality equivalence nor failure prediction;
four pairs support no statistical significance claim.

## W1 prospective protocol v1 — DRAFT

**DRAFT — NOT PREREGISTERED; NO TASKS SELECTED OR FROZEN; NO RUN AUTHORIZED.**
This status describes the proposed future cohorts, not the historical Experiment
4 tasks. Nothing here retroactively preregisters that pilot or authorizes a run.
The following limits and thresholds are proposals for human approval.

**Question/population.** Can estimates made before execution support useful
model/effort advice on the user's intended work? Sample varied difficulty and
localized repairs, multi-file/interface changes, and diagnosis/environment work.
Include genuine user work, genuinely new tasks and benchmarks where appropriate.
Record origin (`real`, `benchmark`, or explicitly synthetic development fixture),
novelty/contamination uncertainty, and task type as separate fields. A benchmark
is not proof of novelty; keep source universes and analyses separate. Assign
manual difficulty bands before outcomes using required interfaces, dependency
interactions and requirement ambiguity, with the rubric frozen at approval.
Record candidates rejected before execution and reasons. Never choose tasks
because an arm already failed or remove hard tasks after seeing outcomes.

Treat the proposed 12-task feasibility cohort as development only, spanning at
least three families and four repositories, crossed where appropriate. If intended
work cannot provide that coverage, a narrower target population and justification
must be approved before selection, with no broad generalization claim. Related
variants, retries and shared source/solution lineages stay together. Future
confirmation is chronologically later, uses untouched tasks and multiple held-out
repositories (and held-out families if the claim includes them), and keeps labels
inaccessible to policy/prompt/feature tuning. One held-out repository cannot
establish generalization across repositories.

**Candidate arms and resources.** Consider Luna Low, Sol Low, Sol High only after
confirming availability and obtaining separate run approval. These are candidate
labels, not verified provider/backend IDs or entitlements. At approval record
provider, exact model/version, effort, tools, harness/version, permissions,
configuration hash, limits, and requested versus observed settings. Unknown
backend revisions stay unknown. No probes, calls or silent substitutions now.
If only two arms are confirmed, explicitly approve that pair and restrict claims
to it; if fewer than two are confirmed, no paired comparison proceeds.

Propose one attempt per task/arm: 24 attempts for two arms or 36 for three.
A 15-minute process cap implies at most six or nine process-hours respectively,
excluding preparation and verification. These are feasibility ceilings, not
statistical power or spending approval. Proposed retry cap is zero, including
infrastructure retries; every selected attempt remains in the accounting.
Approval must separately fix input/output/total-token ceilings per attempt and
cohort, wall-clock boundaries and enforcement, monetary ceiling and its permitted
measurement, and operator preparation/review/verification time limits. Token,
monetary and operator limits are presently **unresolved and block all runs**;
unknown subscription charges are not zero. Stop at any approved ceiling, loss of
containment, verifier integrity breach or human stop. Never add runs automatically.

For a separately approved confirmation cohort, propose a fixed sample rule:
choose useful paired Brier gain δ=0.01 and target 95% half-width h=0.02, then
before selecting tasks set `n = ceil((1.96*s_d/h)^2 * D / q)`, using a
predeclared development-only dispersion estimate or conservative sensitivity
range, dependence inflation D and scorable fraction q. Fix these values and the
analysis before any confirmation labels. Proposed hard cap: 60 tasks, one attempt
per approved arm (120/180 attempts, at most 30/45 process-hours under the same
15-minute cap), plus separately approved token/money/operator caps. If required
n exceeds 60 or the budget, stop at design review or approve an explicitly
exploratory fixed cohort; do not promise the desired precision. Missing labels
consume the fixed sample and are not replaced. This planning approximation is
not a guarantee under few correlated repositories/families. No outcome-dependent
sample expansion, stopping for a win, or indefinite collection is permitted.

**Comparators and frozen selection.** Freeze fixed prior p=0.5, global Beta(1,1),
matching-arm Beta(1,1), and exact A/B/C as primary candidate policies before
selection. Global uses `(1+S)/(2+N)` pooling admitted arms; matching-arm uses the
same formula within exact configurations (across narrow groups in the declared
source universe). Include raw global and per-arm empirical frequencies as
secondary diagnostics: cold start 0.5, otherwise S/N, clipped to
`[0.000001,0.999999]` before both scores. Beta policies need no clipping for these
finite counts. Preserve A/B/C definitions above, including model/effort and
explicit family membership; a global comparator's cross-arm pooling is an
intentional difference. The matched per-arm Beta comparison prevents evaluating
C only against starved narrow cells. Recent windows and task-feature predictors
are deferred secondary candidates, neither fitted nor implemented here.

All policies share an approved source universe, dataset/version, acceptance/budget
constraints, cutoff, and target-task exclusions. Do not blend real, benchmark and
simulated observations. For cross-repository tasks with different acceptance
contracts, declare comparability before outcomes or retain separate targets and
cold-start cells; do not loosen target matching to obtain more evidence. Resolve
one eligible observation per run through valid assessment supersession as of the
cutoff; deduplicate stable evidence keys and retained capture identities. Reject
ambiguous corrections/associations and mixed or incomplete attribution. Unknown,
censored and unverified outcomes do not become binary labels. Retain exclusions
and source evidence keys. Prior-only predictions remain visible with zero counts;
invalid identities/contracts/availability cause forecast abstention. With fewer
than five eligible matching-arm labels, propose abstaining from model-selection
advice while still reporting valid prior probabilities and score coverage.

**Leakage and execution.** Freeze every arm/policy forecast for each task before
any arm starts, together with policy version/hash, source IDs, counts/exclusions,
contract, cutoff and an independently retained reviewed manifest. Exclude the
target task's entire evidence, including its paired arms. Event time, ingestion/
availability time and decision time are distinct; only records and labels known
by the cutoff qualify. Features cannot include final patches, hidden answers,
post-run tokens, outcomes or retrospective difficulty. Checkpoint predictions
are separate later questions. Historical hashes are identities, not trusted time
attestations; newly written timestamps cannot recover past availability.
For confirmation, freeze all cohort predictions from development evidence before
the first confirmation run; do not update from hidden holdout outcomes. Report
this batch holdout separately from any later approved prequential evaluation.
Changes after label exposure require a disclosed new protocol and future holdout.

Later authorized runs need isolated identical starting snapshots, comparable
permissions/budgets, counterbalanced order (rotate arm permutations within
predeclared family/repository blocks), and independent protected acceptance tests.
Keep verifier sources/versions, environment, report and final artifact digests,
required test identities, and completion/exit receipts bound to the exact task/
run/acceptance version. Agent-reported completion is not verification. An intact
complete verifier passing required checks gives verified success; complete valid
acceptance failures give verified failure. Harness/infrastructure errors,
invalid/mismatched verification and absent telemetry are separate unknown cases;
a process timeout is censored unless a prospectively approved, independently
measured within-budget target explicitly makes it a verified failure. Preserve
all aborts, errors, natural failures and selected attempts. Synthetic fault
fixtures may later test engineering behavior, never natural model-quality evidence.

**Analysis and decision.** Primary measure: average Brier across approved arms
within each fully scorable task, then compare policy scores using paired task
differences on common task support. Report partial tasks/arm-level results and
missingness separately; do not silently change arm weights or treat unscored as
failure. Secondary: natural-log loss, verified success and discordance, forecast/
advice coverage and abstention, process duration, verification overhead, and
available input/output/cached tokens with boundaries and missingness counts.
Actual charge stays unknown without permitted billing evidence. Report outcome
class counts and exclusions by arm, task origin/type/difficulty, repository and
family. AUROC is undefined with one class; all-success evidence cannot establish
failure discrimination or calibration.

Feasibility results are descriptive. Confirmation proposes a predeclared 95%
interval for paired task-score differences using repository-cluster resampling
with tasks/arms kept together and family-stratified reporting; specify resample
count/seed and handle crossed family dependence at preregistration. Too few
clusters for credible inference means inconclusive, with descriptive paired
ranges and leave-one-repository/family-out sensitivity, not nominal certainty.
Select one primary comparison (proposed C versus matched per-arm Beta); other
policy comparisons are descriptive unless a multiplicity rule is approved.
Proposed adoption gate: upper interval bound for candidate-minus-baseline Brier
below -0.01, lower bound for success difference above -0.02, advice coverage at
least 90%, and no subgroup exceeding the approved 0.02 success-harm margin.
Unresolved or underpowered subgroup harm is inconclusive, not safe by default.
Ratify thresholds and uncertainty method before selection. Policy score gain
alone is not causal model-choice utility; no off-policy causal claims without
suitable overlap/assignment evidence. Keep the simplest valid advisory when
superiority is unproven; the human retains model choice. No autonomous Governor.

For evaluating advice, propose ranking admissible arms by predicted success,
with a fixed human-approved tie order recorded before outcomes and the five-label
abstention rule above. This is read-only advice. Compare recommended-arm success
against the matched per-arm baseline's recommendation only where both policies
advise and the required paired outcomes are verified; report all other cases as
missing/abstained and retain coverage denominators. The 0.02 success-harm margin
applies to this explicitly defined advisory comparison, not to forecasting
policies as though they themselves executed tasks. Do not infer cost savings or
unobserved alternative outcomes.

**Preregistration gate.** Before selecting/freezing any future cohort, approve
arms and exact identities/availability; task-selection/origin/difficulty/lineage
and chronological split rules; source universes, policies, priors and clipping;
primary contrast/metrics and uncertainty/multiplicity/subgroup rules; fixed sample
rule and all hard resource caps; verifier and outcome-resolution contract;
isolation/counterbalancing, freeze/receipt/leakage controls; abstention, integrity
and stop rules. Resolve all numeric limits and analysis choices above first.
Then separately authorize bounded execution. No tasks, IDs, model access,
benchmarks, training or new experimental evidence have been obtained in W1.

## W1 provenance decision gate

| Required question / actual gap | Permitted evidence and consequence | Existing record / smallest future proposal | Offline acceptance case and separate authorization |
| --- | --- | --- | --- |
| Were declaration and evidence available before decision? | STATUS describes pre-arm freezes; no exact receipt/cutoff records. Historical availability remains unknown. | This manifest resolves the honest claim boundary. A reviewed future manual record can separate declared event time, actual receipt time and decision time; new timestamps cannot repair old knowledge. | Delayed receipt with old event time must not enter earlier forecasts; earlier bytes remain unchanged. Approve sanitized export first; a narrow persisted receipt field only if manual records cannot answer the query. |
| Is the scored forecast the pre-outcome forecast? | Summary probabilities for T1/T2; no original forecast/hash records for any pair, no final T3/T4 values. Full historical reproduction is blocked. | Supply sanitized frozen bundles and separately retained digest/chronology declarations. Existing exclusive freeze and score binding are sufficient in principle; hashes alone are not trusted time attestations. | Replacing bytes or rebinding task/run/configuration/acceptance/budget must reject; late evidence cannot refit a frozen prediction. Existing synthetic adapter tests cover some bindings, not historical truth. Export/read or any additional test/code work needs separate scope. |
| Do scoped exports preserve Task/Run/Attempt/Session associations? | Readiness/STATUS explicitly document association reconstruction outside primary-record export; no pilot IDs available here. Cannot reproduce joins from this sidecar. | A reviewed opaque-ID association table may suffice. Only if it cannot round-trip required relations propose a narrow association export/import extension; no migration or new event platform. | In isolated fixtures export/import selected associations, compare joins, forecasts/resolved outcomes/scores, reject rebinds, replay twice without count growth. Requires separately approved W2 implementation/testing; no private ledger access implied. |
| Did an independent verifier assess the intended artifact and contract? | T1/T2 summary reports bound independent passes; digests/version/receipts absent; T3/T4 binding unknown. No independent artifact audit in W1. | Existing manual reviewed verifier/artifact manifest can carry opaque IDs/digests, required checks and completion receipts. Evidence export is needed, not a new verifier framework. | Mismatched artifact/report/acceptance, incomplete verification and infrastructure error stay ineligible/unknown; a genuine valid failure resolves once. Separate sanitized evidence or W3 fixture scope required. |
| Which correction/supersession head was eligible at cutoff? | Existing resolution docs describe append-only correction; no scoped pilot chain supplied. Cannot audit historical corrections/replay. | Reviewed assessment/observation IDs with supersedes links and availability can answer; retain old records, never silently overwrite. No resolver change justified here. | Late correction excluded from earlier cutoff; current cutoff resolves one head; duplicate replay adds none; conflicting heads/rebind reject. Separate scoped export or offline W2/W3 tests required. |

For this documentary scope, **no new infrastructure required for this scope**.
Historical reconciliation remains incomplete at the binding/receipt level; this
closure is not a claim that future automated portability already works. The
smallest useful next evidence is a sanitized export for T1–T4 with opaque task/
run/attempt/session/configuration associations, requested/observed settings,
acceptance/verifier/artifact/report IDs or digests, original frozen bundles and
external hash/availability declarations, eligible IDs/counts/exclusions, resolved
outcome/supersession references, and available resource scopes. Missing fields
must remain null. No raw transcripts, private paths or credentials are requested.

## Finite working-v1 mapping to the existing plan

These W labels are review gates, not replacement milestone numbers. Existing
code and historical checks do not alone establish integrated completion.

| Gate | Actual plan reference | Current scope/status |
| --- | --- | --- |
| W1 evidence/protocol | §§4–5, M6-B evaluation design | Documentation and conditional arithmetic delivered for review; historical bindings incomplete; not preregistered. |
| W2 canonical intake/freeze | §4, M1, M4-A, §5.3 | Existing contracts/adapter reusable; only demonstrated receipt/association repairs eligible for future approval. |
| W3 capture/verifier/resolution | M3, M4-A/B/C, §7 | Existing components and historical T1/T2 summaries; integrated scope needs separately authorized fixture/real evidence. |
| W4 finite feasibility | M4, M6-B, §§5.3/7 | Pending design, containment, privacy, resources and run approval. |
| W5 held-out comparisons | M6-B, §§5.2–5.4 | Untouched confirmation pending; W5 does not implement or declare M6-A partial pooling complete. |
| W6 portable human advisory | M1 export, M5, M7 | Association round-trip and read-only advice need separate acceptance evidence. Optional M8 TUI is unnecessary. |
| W7 integrated acceptance | §7 end-to-end demo, §8 gates, M6-B/M7 | Pending separately authorized real full-chain task, bounded holdout and engineering failure/unknown fixtures. |

M9 checkpoint/intervention intelligence and future M10+ Governor are later and
outside working-v1. Engineering completeness and predictive superiority remain
separate: working-v1 can provide honest uncertainty/abstention without proving
calibration or beating simple baselines. Jev, purchases, graph storage, semantic
ML and autonomous execution are neither dependencies nor authorized work here.
