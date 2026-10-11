# Task-state predictive evaluation

This local experiment compares initial information with checkpoint execution
features. It writes no ledger records, launches no agent and makes no routing
recommendation. `learn.task_state` is an independent numerical module; existing
learner/domain contracts remain intact.

## Operator commands

```sh
uv run model-learner sim state-fixture /tmp/state-fixture.json --seed 1 --count 400
uv run model-learner learn state-eval \
  --input-file /tmp/state-fixture.json --source-kind simulated \
  --dataset-id task-state-state_signal-seed-1 --dataset-version 1 \
  --acceptance-id controlled-task-acceptance --acceptance-version 1 \
  --train-until 2026-01-01T12:00:00Z \
  --evaluation-at 2026-01-01T20:00:00Z --checkpoint-offset-seconds 30
uv run model-learner learn state-experiment --seeds 5 --count 400
```

Check command help for supported output options. The evaluation API returns a
`TaskStateReport`; `dataclasses.asdict(report)` is JSON-serializable. The portable
input is a strict JSON array of `TaskStateExample` objects, each containing an
existing `Observation`, existing `ExecutionCheckpoint`, `initial_available_at`,
`inputs_available_at`, and optional retained `events`. Source kind, exact dataset
version, acceptance criterion and budget are selected explicitly and never pooled
across datasets.

For real/benchmark data, construct observations through existing independent
verification and historical assessment resolution first. The evaluator requires
verified, eligible, single-configuration labels with evidence identifiers, and
retained event evidence. It rebuilds checkpoint facts using event observation and
ingestion timestamps, bounded by the run start, fixed horizon and session;
explicit foreign-run events are excluded. A mismatch rejects the input.
Null-run event membership relies on the trusted session/boundary declaration.
This portable evaluator does not independently attest final labels or reconstruct
historical ledger revisions; callers must supply the resolved observation valid
at the relevant training/scoring cutoff. An inaccessible future observation
cannot replace an earlier observation or produce a duplicate conflict.

`initial_available_at` declares the maximum availability time of the task group,
acceptance target, exact configuration snapshot and task/run/session association.
It must be no later than the initial decision. `inputs_available_at` declares the
maximum receipt time of checkpoint inputs and must be no later than the
checkpoint. Real and benchmark examples require auditable retained events;
simulated examples can explicitly contain synthetic projections. Never put
prompts, commands, outputs or private transcripts into committed examples.

## Comparison and leakage controls

All variants use the identical selected cohort, frozen training cutoff, scoring
cutoff and predeclared checkpoint horizon (default 30 seconds after the initial
decision). There is one checkpoint per run per evaluation. Changing the horizon
is a separately reported experiment; choosing each run's most predictive
checkpoint would invalidate the comparison.

| Variant | Feature groups |
| --- | --- |
| A | Task group and exact model/configuration snapshot |
| B | A plus event/tool/turn counts, token counts and missing indicators |
| C | B plus observed failure counts, repeated-failure counts and failure/unknown fractions |
| C without initial | Metrics and task-state features |
| C without metrics | Initial and task-state features |
| C without state | Initial and metrics (identical to B) |

C includes the simple metrics so its difference from B isolates additional state
information. These are explicitly allowlisted observed state features from the
existing analyzer, rather than an inferred task-success label. JUnit results,
test-state categories, terminal execution states, final resource use, final
outcomes, IDs and arbitrary metadata are excluded from predictors. Current
analyzer JUnit results describe the final artifact; feeding them into prediction
would risk predicting acceptance from its own verification. Independent JUnit
verification still supplies the eventual acceptance label. Intermediate-artifact
test progression remains outside the current contracts and this experiment.

Labels known at or before the checkpoint are excluded. Training decisions precede
`train_until`; checkpoints, observations and labels must be available by that
cutoff. Held-out decisions begin at `train_until` and checkpoints/labels must be
available by `evaluation_at`. Retries sharing a task with any selected training
run are excluded from scoring. Exact duplicate runs are counted once; conflicting
visible snapshots fail closed. Unavailable future snapshots are filtered before
identity conflicts. Unknown, censored, unverified, missing, unavailable or
unattributable labels remain explicit exclusions and never become failures.

The model is a fixed L2 logistic reference, not a replacement for the existing
Beta-Bernoulli estimator. Task/config categories, log1p count transformations,
missing indicators and mean/std scaling use only the training prefix. Unseen
categories are ignored, and the scaling floor is 1. Fixed ridge 0.05 and 400
full-batch gradient steps are predeclared; no hyperparameter or feature selection
uses held-out outcomes. The learning rate is bounded using the training design.

## Scores, uncertainty and insufficient data

Reports include training/held-out/scored counts, independent task counts,
exclusion counts, Brier scores, fixed calibration bins (counts, mean prediction,
observed success fraction), and paired Brier differences for A/B, B/C and each
feature-group ablation. Positive differences mean the candidate has lower Brier.
95% percentile intervals resample held-out task clusters using the same draws
for every variant. The default is 300 bootstrap draws; seed and draw count are
reported. These intervals condition on the frozen fit and omit training
uncertainty and dependence between different tasks. Bin calibration is a noisy,
bin-dependent descriptive diagnostic. Ablations are exploratory without a
multiplicity correction. An interval crossing zero does not resolve improvement;
a positive interval supports only a conditional comparison on this dataset.

Defaults require at least 30 eligible training labels and 20 scored labels,
at least five task clusters in each partition, and both classes in training.
Below these floors, results say `insufficient_data`, retain sample/exclusion
counts and return null scores/intervals. These pragmatic floors do not guarantee
adequate precision. Missing labels and missing checkpoint coverage may select a
nonrepresentative cohort. No causal model superiority follows from these scores.

## Reproducible controlled evidence

`generate_task_state_fixture` samples observed failure state first, then samples
an independent eventual Bernoulli acceptance conditional on that state. Unknown
labels are independently missing with probability 0.05. In `state_signal`, success
probability is 0.85 without repeated failures and 0.15 with them. In `null_signal`,
it is 0.5 regardless of state. Task group/model assignments and simple metric
distributions are identical across scenarios. Synthetic projections explicitly
identify their origin and retain no private data. Realized labels and generating
probabilities are never estimator inputs.

The reference experiment used seeds 0–4, 400 independent tasks per seed,
a chronological 60% training prefix and the same 30-second checkpoint for all
variants. Each seed has 222–231 eligible training labels and 150–154 scored
labels. Means below give each independent seed equal weight.

| Controlled scenario | A Brier | B Brier | C Brier | B minus C |
| --- | --- | --- | --- | --- |
| State signal | 0.249377 | 0.249568 | 0.133440 | 0.116128 |
| Null signal | 0.251462 | 0.251353 | 0.251842 | -0.000489 |

State-signal per-seed improvements range from 0.078503 to 0.138317. Null-signal
improvements range from -0.002473 to 0.001888. The synthetic favorable case
establishes that this reference can use a deliberately constructed signal;
the null case shows that adding state can add noise. This is no evidence of real
coding-task improvement or real calibration. Per-seed calibration, score/paired
intervals, sample counts, exclusions and ablations are stored in
[`controlled_reference.json`](../tests/fixtures/task_state/controlled_reference.json).
Seed spread is descriptive, not a nominal confidence interval over populations.

Reproduce the artifact with `run_task_state_experiment()` and remove each
variant's `predictions` before JSON serialization (the checked-in summary omits
per-run prediction UUIDs to keep the artifact small). Real-task results can be
added through separately selected, independently verified benchmark/real
examples once enough labels and prospective checkpoints exist. Existing final
benchmark outputs alone do not establish historically available initial inputs;
retain the required receipts and event evidence during collection.
