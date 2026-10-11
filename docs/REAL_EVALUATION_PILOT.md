# Controlled real coding-agent pilot

This is an operator-run **collection feasibility** experiment, not a model
superiority study. It preregisters twelve synthetic Python tasks, two execution
configurations and 24 fresh executions. No real or paid agent execution has been
launched. The independent acceptance controller checks named numeric results and
exceptions; neither agent completion nor self-reported success supplies a label.

**Current stop gate:** real execution/finalization remains blocked by the
fail-closed containment gate described in
[CODING_TASK_EVALUATION.md](CODING_TASK_EVALUATION.md). Task preparation and
fixture validation work. A successful diagnostic macOS probe or an operator
isolation declaration does not authorize a real run. The conditional execution
steps below require a separately validated supported containment backend and
explicit human authorization for the scoped paid experiment. There is no runner,
retry loop or batch launcher in the plan command.

The current controller's workers share its filesystem and are therefore suitable
only for controlled public reference candidates. Real independent acceptance also
requires the candidate-only worker boundary/transport in
[BENCHMARK_SAFETY.md](BENCHMARK_SAFETY.md); merely placing the existing controller
and untrusted candidate together in a credential-free VM is insufficient.

## Frozen task set

These repository-authored synthetic tasks have no external download or license
dependency. `benchmark tasks` reports the exact objective, initial source,
fixture version and independent checks. Every task edits only `solution.py`,
uses the standard library and starts with an unimplemented function. Definitions
and fixed expected values live in `benchmark/fixtures.py`; hand-written public
reference solutions live in `tests/fixtures/benchmark/pilot_solutions.py`.

| Task ID | Objective | Named checks |
| --- | --- | ---: |
| `clamp` | Inclusive bounds and invalid bounds | 6 |
| `duration` | Strict nonnegative duration parsing | 8 |
| `ceil_div` | Signed ceiling division without floating point | 8 |
| `first_index` | First matching index in sorted values | 7 |
| `interval_length` | Union length of unordered half-open intervals | 7 |
| `hex_integer` | Strict signed hexadecimal parsing | 9 |
| `median` | Odd/even median with an empty-input error | 7 |
| `edit_distance` | Insertion/deletion/substitution distance | 7 |
| `components` | Undirected graph components and endpoint checks | 8 |
| `unique_window` | Longest substring without repeated characters | 7 |
| `rpn` | Stack evaluation with exact signed integer division | 11 |
| `balanced_span` | Longest well-formed parenthesis substring | 8 |

Acceptance is finite and public. It establishes only the predeclared named-test
criterion, including the boundaries listed above. It does not establish universal
correctness, security, asymptotic complexity or absence of memorization.
The agent receives only the objective and starting module in its workspace.
Do not expose the controller, fixed expected values, reference solutions,
previous candidates, reports or Model Learner source. Even though these sources
are public, withholding them from the execution environment prevents direct
test-file access; it is not a claim that the tests are unknown to the model.

## Two execution configurations and preregistration

Choose one installed, authorized coding CLI and one model supporting two
reasoning settings. Arm A uses its supported lower setting; arm B uses its
supported higher setting. Keep provider, model, model version where known, CLI
version, Python image, prompt, tool permissions, stop limits and initial state
identical. Change only the reasoning setting. If that pair is unsupported, stop
and preregister a new supported pair before seeing outcomes. There is no claim
that any particular paid model is installed, available or approved.

Create two JSON files outside Git. Use actual inspected settings, not guessed
versions; absence of an immutable model version stays `null`. Both files require
nonempty `provider`, `model`, `reasoning_level`, `harness`, `harness_version` and
`configuration_version`. For example, this is a **template to fill**, not a
usable configuration:

```json
{
  "provider": "OPERATOR_SELECTED_PROVIDER",
  "model": "OPERATOR_SELECTED_MODEL",
  "model_version": null,
  "reasoning_level": "OPERATOR_SUPPORTED_LOWER_SETTING",
  "harness": "OPERATOR_SELECTED_CLI",
  "harness_version": "ACTUAL_INSTALLED_VERSION",
  "configuration_version": "real-coding-pilot-v1"
}
```

Arm B changes `reasoning_level` to the selected supported higher setting. Keep
credentials out of configuration metadata. Record the exact image/runtime,
CLI-version inspection, configuration hashes and permitted tooling in the
operator-owned preregistration file. The plan requires distinct exact
configuration IDs. Unknown model version remains explicitly unknown.

After filling and checking both files, use the existing CLI:

```sh
model-learner benchmark tasks
model-learner benchmark pilot-plan \
  --configuration-a /private/tmp/pilot-arm-a.json \
  --configuration-b /private/tmp/pilot-arm-b.json \
  --seed 1 > /private/tmp/pilot-plan.json
```

Use a fresh output destination; shell redirection can overwrite an existing file.
Retain this file unchanged. `build_pilot_plan` is also a pure Python API in
`model_learner.benchmark.pilot`. It randomizes task order with seed 1, places eight
whole task families in training and four in held-out, and balances which arm
runs first within each partition. Finish all training task pairs before any
held-out pair. No retries, replacement tasks, switching configurations or choosing
checkpoints using outcomes. A failed preparation can be retried before any run;
an executed attempt remains in the denominator even if evidence is missing.
Balanced order reduces an obvious order bias but cannot remove service drift,
cross-task dependence or public-task contamination. The schedule is not an
assignment-propensity model and does not create decision records.

For each row, stage a **new** root with the corresponding configuration:

```sh
model-learner benchmark prepare clamp \
  --parent /private/tmp \
  --configuration-file /private/tmp/pilot-arm-a.json \
  --isolation-mechanism 'pilot pending supported containment validation' \
  --dataset-id controlled-coding-pilot --dataset-version 1 \
  --execution-origin real
```

Replace `clamp` and the arm file with the plan row. Preparation launches nothing
and does not clear the execution gate. The final dataset is
`source_kind=benchmark`, ID `controlled-coding-pilot:real`, version `1`; controlled
candidate checks belong to a separate `:fixture` dataset, never this real dataset.

Before execution, compare each task pair's fixture/acceptance fingerprint and
the actual bytes of both `solution.py` and `TASK.txt`. The plan records SHA-256
of the initial source and description; the harness additionally binds the trusted
controller and required test IDs. Use independent fresh clean machine images,
empty agent context and separate disposable agent workspace per row. Pair identity
is the fixture ID/version and its fingerprints, not the random task UUID assigned
by each preparation. Keep both arms of a family in the same partition and treat
the family as a dependence cluster in any future pooled evaluation. Fingerprints
establish identical declared bytes, not filesystem isolation.

## Limits, checkpoints and allowed features

Use the containment resource policy in CODING_TASK_EVALUATION.md. This plan adds
a hard 120-second wall limit for the agent; the enclosing supervisor must terminate
and reap descendants at that limit. Use identical fixed resource limits for
both arms. Do not silently substitute a longer run or a paid retry. Independent
acceptance keeps the existing five-second per-worker timeout and must additionally
have bounded OS resources and controller-level time/process limits. The declared
wall cap is an execution-policy limit, not a fabricated `ResourceBudget` outcome
or a claim that interrupted execution failed acceptance.

All times use aware UTC timestamps. Fix `t0` as the actual initial decision/start
receipt. Request checkpoints at `t0 + 10`, **`t0 + 30` (primary)** and `t0 + 60`
seconds. The +10 and +60 horizons are collection diagnostics only.
Each predictive comparison uses exactly one predeclared horizon per run. Do not
choose the best horizon, use the last available point or forward-fill missing
token usage. Record a run ending before a checkpoint as early-stopped coverage;
record absent capture or unavailable inputs explicitly. Never prolong a solved
task solely to manufacture checkpoint coverage. Native stream buffering can make
receipt-time features unavailable even when work occurred earlier.

| Checkpoint | Allowed prospective information |
| --- | --- |
| `t0` | Declared task group and exact execution configuration |
| `+10`, `+30`, `+60` | Same initial data; counts of received supported events, tool items and started turns; input/cached/output tokens with missing indicators; observed failed tools/turns, unknown tool failures, repeated-failure counts and failure/unknown fractions |

Every feature input must have both observation and ingestion availability no
later than its checkpoint. The existing analyzer/evaluator rebuilds bounded
facts from retained events. Arbitrary metadata, prompts, commands, outputs,
artifact content, IDs, inferred terminal execution state, JUnit/test state,
hidden-test results, agent success claims, future events, final costs, final
latency and final outcomes are excluded from predictors. Never expose independent
acceptance during agent work. Run acceptance only after stopping/reaping and
freezing the final candidate. Labels known at or before a checkpoint are excluded
from scoring at that horizon rather than treated as predictive evidence.

**Prospective checkpoint export is currently blocked.** Benchmark finalization
imports events and creates run/session/attempt associations after the stopped
run. Consequently its `Event.ingested_at` values are later than the checkpoint.
Replaying a capture into a ledger later does not make those events historically
available, and association declarations cannot be backdated to `t0`. The existing
`import codex` and `extract_execution_checkpoints` APIs can import observed events
and show session-only projections, but the benchmark workflow lacks a verified
prospective ingestion/association handoff. Native session identity may itself
first be emitted after the initial decision. Do not manufacture a run-bound
`TaskStateExample` by setting ingestion/initial-availability timestamps to native
or capture timestamps. A separately scoped prospective collector/receipt contract
is required before the pilot can supply eligible checkpoint examples. Raw
stream receipt envelopes can still be retained as metadata for auditing the gap.

## Evidence and recording sheet

Keep operator manifests, metadata-only capture, reports and receipts outside Git
and outside the agent mount. Use one row for every scheduled run, including
not-started/blocked/interrupted/unknown rows. Record:

| Domain | Required fields |
| --- | --- |
| Assignment | Plan version/seed, ordinal, fixture family/version, partition, arm and exact configuration ID |
| Initial state | Root identifier, source/description/fixture/acceptance fingerprints, image/runtime version and initial availability receipt |
| Containment | Supported backend/version, policy digest, validation receipt, explicit limits, reaping confirmation and any failed canary |
| Execution | Actual start/stop, stop reason, operator launch authorization reference, session/capture IDs, actual emitted model/provider conflicts |
| Telemetry | Adapter/emitter version, metadata-only capture digest, receipt bounds, diagnostics, observed/ingested timestamps, per-field usage coverage |
| Checkpoints | Fixed horizon, receipt/scope availability, retained bounded event IDs, missing/early-stopped reason; eligible export currently blocked |
| Verification | Frozen candidate hash/time, acceptance version/test IDs, report hash, independently observed controller completion/exit and generation receipt, verification and assessment IDs |
| Cost | Nullable amount and currency, actual provider invoice/usage attribution source if available, receipt time and known/missing denominator |
| Latency | Operator start-to-stop wall time and basis, separate verification wall time; native duration nullable with source if actually supplied |

Do not infer dollars from tokens, set unknown money to zero or label subscription
execution free. Operator wall duration is not native execution duration; capture
receipt span is neither. Keep resource receipts in the external recording sheet
when no corresponding trustworthy harness field exists. Run finalization does
not manufacture cost/latency observations. Capture only supported metadata using
`capture codex`; no `--retain-raw` for this pilot. Missing capture/report/receipt,
malformed/skipped/partial tests, configuration conflicts, unknown price and
containment failures remain reason-coded evidence gaps. An interrupted run's
assessment remains unknown; a complete independently verified failing named-test
criterion is a failure. Report this distinction in denominators.

## A/B/C predictive comparisons and current evidence limits

Use the existing `evaluate_task_state` framework and settings in
[TASK_STATE_EVALUATION.md](TASK_STATE_EVALUATION.md), without editing the
probabilistic estimator:

| Variant | Predictors |
| --- | --- |
| A | Initial task group and exact execution configuration |
| B | A plus received event/tool/turn/token metrics and missing indicators |
| C | B plus observed failure/repeated-failure/unknown fractions and counts |

Retain all three existing feature-group ablations. Freeze one training cutoff
after the training collection/labels and before any held-out decision, and one
scoring cutoff after held-out independent verification. Train preprocessing and
category vocabularies solely on the training prefix. Keep the 30-second primary
horizon, 30 eligible training labels, 20 scored labels, at least five task
clusters in each partition and both classes in training. Keep default ridge,
gradient steps, calibration bins and 300 bootstrap draws; use seed 1. Report
Brier, fixed calibration-bin counts and paired task-cluster intervals only when
the existing sufficiency checks pass; otherwise retain null scores/intervals and
`insufficient_data`. Do not lower floors to get a result from this pilot.

Three independent limits prevent a scored real comparison today:

1. The fail-closed real-execution containment gate remains unresolved.
2. No supported benchmark-to-observation export exists. The current real builder
   requires `source_kind=real` and human-declared attempts; benchmark results have
   `source_kind=benchmark` and operator-predeclared attempts. Do not relabel them
   as real, change provenance or invent verified eligible observations.
3. Each fixture has a distinct `public-coding-TASK` acceptance target, whereas
   the evaluator selects one exact acceptance target. Do not rewrite individual
   evidence to a fictional common target or pool scores across incompatible
   targets. A future suite-level target/projection must be explicitly designed
   and evidence-validated. Even a legitimate shared-target export would give only
   16 training and eight held-out rows here, below the 30/20 floors; four held-out
   task families also fail the five-cluster floor. Per-target cohorts are smaller.

The plan's 8/4 family split is a future collection-control declaration, not a
claim that today's evaluator already recognizes fixture-family clustering across
random per-root task UUIDs. Future export must preserve that family dependence
and avoid training/held-out reuse. A larger task set requires new authorization
and preregistration. This pilot should establish capture and independent
verification coverage, observable state variation and missingness, not predictive
improvement. Selecting 12 trivial tasks may yield no failures or no useful state
variation; report that as insufficient evidence.

## Operator sequence and stop rules

1. Review the task definitions and trusted checks, fill/freeze two configurations,
   save the plan outside Git, and stage paired fresh roots. Verify pair hashes.
2. Run the harmless containment diagnostic and retain its actual result. **Stop
   before launching an agent** while a supported containment backend is absent
   or unvalidated. A failed/unknown result is a blocker, not a warning to bypass.
3. Conditional on a separately validated supported backend, complete the clean
   disposable agent and acceptance environments specified in the safety protocol.
   Retain policy/resource/probe receipts. Obtain explicit human authorization for
   the task set, configurations and spend cap; it may cover the full experiment.
   The plan does not supply authorization or require repeated approval within an
   already authorized scope.
4. Launch that one agent externally under the supervised 120-second wall cap,
   capture supported metadata outside its mount, record actual boundaries and
   fixed-horizon coverage. Do not run acceptance or reveal other candidates.
5. Stop/reap, run `benchmark snapshot ROOT`, then run acceptance through the
   supported candidate-only worker transport, keeping the trusted controller and
   fixed expectations outside the candidate boundary. Record actual completion,
   exit, report generation and report hash. Missing evidence stays unknown.
6. Use `benchmark finalize` only when its supported containment gate is satisfied,
   with the actual operator receipts documented in CODING_TASK_EVALUATION.md.
   An operator declaration alone cannot pass today's real-finalization gate.
   Retain `result.json`, manifest, ledger, snapshot/report and capture before cleanup.
7. Complete scheduled training pairs; freeze cutoff before held-out collection.
   If the gate fails, configuration changes, source/control tampering occurs or
   limits cannot be enforced, stop and record the blocker. Do not replace the
   run or retry automatically. Finish with coverage/missingness counts per arm,
   family and partition; annotate every denied/not-started run.
8. Report predictive export as blocked until its independent contracts exist;
   report the planned cohort as insufficient for current A/B/C floors. Dispose
   each validated root explicitly with `benchmark cleanup ROOT` after saving
   wanted metadata/evidence outside Git. Do not proceed to another milestone.

Ready now: twelve versioned task definitions, independently checked acceptance,
deterministic paired preregistration, fresh-state staging and an operator recording
protocol. Blocked: supported real-agent containment, real executions, prospective
checkpoint/benchmark observation export and sufficient real predictive evidence.
