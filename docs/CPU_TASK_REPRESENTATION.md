# Optional local CPU task representation prototype

Delivered 2026-10-11. This is a separate observational/predictive experiment in
`model_learner.representation`; the existing probabilistic learner is unchanged.
It collects no transcripts, performs no remote inference or download, fine-tunes
no semantic model, switches no agents and implements no Governor.

## Inputs and comparisons

`RepresentationExample` contains an existing `TaskStateExample` plus an explicit
`TaskDescription`: task UUID, declared task family, bounded public/sanitized text,
SHA-256 of UTF-8 text, public/sanitized source declaration and an aware availability
timestamp. Text is limited to 4096 characters, must match its receipt, and must
have been available by the initial decision. The operator is responsible for
sanitization, truthful timestamps and conservative family membership. A source
declaration or matching hash cannot establish privacy or historical availability.
No module discovers descriptions in local sessions or reads private transcripts.

The three predeclared variants are:

| Variant | Features |
| --- | --- |
| A_existing | Existing initial task group and exact configuration identity. |
| B_execution_state | A plus existing observed event/tool/turn/token metrics, missingness and deterministic failure/repeated-failure/unknown-fraction counts. |
| C_cpu_semantic | B plus a frozen pretrained CPU embedding of the initial public/sanitized description. |

B preserves the prior task-state evaluator's complete initial/metrics/state
feature allowlist. C adds description embeddings only; it receives no events,
labels, candidate source, hidden tests, reports, final state or final resources.
Final tests/JUnit, terminal execution state, outcomes, future telemetry and final
cost/token totals do not enter any predictor. Real/benchmark checkpoint counts
must match reconstruction from retained observed/ingested events bounded to the
run, session and checkpoint. Non-simulated labels require existing independently
verified, historically resolved evidence; portable JSON is not ledger attestation.
The current benchmark finalization exporter still lacks prospective checkpoints;
this prototype does not make that retrospective data eligible.

## Frozen evaluation

`evaluate_task_representation()` selects one exact source-specific dataset,
acceptance target and budget, then fixes the common A/B/C cohort before semantic
encoding. Fit uses decisions before `train_until`; scoring uses later decisions
whose checkpoint and label were available by `evaluation_at`. Initial and
checkpoint receipts must be available at their declared horizons. Labels already
known by the checkpoint are excluded. Future records are filtered before run
identity conflicts; duplicate/conflicting visible runs fail closed.

Held-out tasks cannot share task UUIDs, declared families or exact description
hashes with the training partition, including training tasks lacking labels.
Repeated runs of a task must use consistent descriptions/families. Records are
sorted deterministically. The report binds the full selected input cohort by a
SHA-256 digest while omitting description text from output.

Each variant fits the same fixed L2 logistic reference (ridge 0.05, 400 full-batch
steps); this reference predictor is separate from the existing Bayesian learner.
Vocabulary, scaling and weights use training rows only. The pretrained encoder is
frozen and uses no task labels. There is no held-out tuning or automatic feature
selection. Evaluation needs at least 30 labelled training rows, 20 scored rows,
five independent families in each partition, and both training classes. These
floors cannot be lowered through this API. Sparse inputs retain counts and null
scores with `insufficient_data`.

Reports give Brier scores, calibration bins, common run predictions, exclusions,
paired differences and seeded 95% percentile bootstrap intervals over held-out
families. `task_count` reports actual task UUID counts; family counts are separate.
Intervals condition on frozen fits and omit training uncertainty/time dependence.
Six held-out families in the fixture yield fragile intervals. Missing receipts or
labels can select a nonrepresentative cohort. These are predictive associations,
not causal agent comparisons. Semantic unavailability never drops difficult rows
from A/B: C stays null with `semantic_unavailable` on a sufficient cohort.

## Optional pretrained CPU adapter and current blocker

The narrow adapter supports only
[`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2),
using its 384-dimensional masked mean pooling and L2 normalization. The operator
must already have an approved local bundle and `torch`, `transformers` and
`safetensors` installed. This work installed/downloaded none of them. No model
cache, credential store or private session directory is scanned.

Provision an operator-owned directory containing **exactly** `config.json`,
`model.safetensors` and `vocab.txt`; remove unused repository files before
approving its content pin. Supply the full declared pretrained commit identity
(40 lowercase hex) and SHA-256 of these three files in sorted filename order:
for each, concatenate UTF-8 filename, NUL, ASCII file byte length, NUL, contents.
The pin must be approved before evaluation, and is not a proof that arbitrary
weights genuinely came from the claimed pretrained revision.

The adapter copies from no-follow regular-file descriptors into a private temporary
snapshot with per-read limits: configuration 64 KiB, vocabulary 2 MiB, safetensors
256 MiB and total 300 MiB. Size changes, symbolic links, special files, additional
files, hash mismatch and unsupported architecture fail closed. It checks known
MiniLM dimensions and uses fixed known BERT configuration values rather than
forwarding arbitrary configuration overrides. Loading uses explicit BERT classes,
CPU, local-files-only, safetensors and no credential token; no model-supplied code,
pickle weights or automatic model classes are accepted. Missing, unexpected,
mismatched or error loading keys are rejected rather than accepting newly randomly
initialized weights. The model uses eval/inference mode with gradients disabled.
Tokenization is capped at 256 word pieces and batch size one.

**Actual local runtime inspection:** torch, transformers and safetensors were all
absent. No existing approved bundle was supplied. Therefore actual model loading,
pretrained inference, C held-out scoring and semantic resource measurement remain
unavailable. Negative descriptor/configuration/loader protocol tests validate
guards, not compatibility with an actual installed runtime/model. Actual adapter
integration must be validated with operator-approved existing software/model
before making any semantic comparison claim. No semantic improvement is claimed.

## Actual controlled rehearsal and overhead

`tests/fixtures/representation/controlled_reference.json` retains actual reports
for seeds 0–4, 150 independent simulated tasks per seed, 60% chronological fit
prefix, a 30-second checkpoint and 300 paired bootstrap draws. Descriptions are
invented public operations with outcome-independent variants; six train families
and six different held-out families are declared. Simulation samples the state
before eventual outcome. This is algorithm rehearsal and not real or benchmark
agent-performance evidence.

| Scenario | Mean A Brier | Mean B Brier | Mean A minus B |
| --- | --- | --- | --- |
| Deliberate state signal | 0.256719 | 0.122489 | 0.134229 |
| Null state signal | 0.254266 | 0.258117 | -0.003851 |

Training counts are 80, 89, 88, 87, 86; scored counts are 58, 58, 58, 57, 57.
All five deliberate-signal intervals are positive. Null-signal intervals differ
across seeds, including two intervals excluding zero in opposite directions;
they provide no consistent improvement evidence. Neither scenario establishes
real predictive improvement, and C metrics are null in every report.

Actual existing Python 3.12.14/macOS arm64 measurements in a fresh process:
state-signal mean A extraction 0.333 microseconds/checkpoint plus reference scoring
1.125 microseconds/checkpoint; B extraction 2.795 microseconds/checkpoint plus
reference scoring 2.709 microseconds/checkpoint. Mean fixed reference fit times
were 27.6 ms (A) and 68.4 ms (B). Feature object census averaged approximately
62.7 kB decimal (A: 62,701 bytes) and 415,670 bytes (B), counting feature
dictionaries/keys/values separately; these are approximate Python object totals,
not whole process RAM. Whole-process lifetime peak RSS was 47.9–49.1 MB decimal
through this run and includes imports, fitting and earlier iterations. Timing is
one observed run, not a hardware-independent performance guarantee.

The report separates model load, warmup, description inference, feature extraction,
reference fitting and reference scoring, and records runtime identity/CPU threads
if an actual model runs. No model overhead measurement is invented for absence:
actual load/inference/model-memory fields are null. The model card's rounded
22.7 million parameters imply an **estimated 90.8 MB FP32 weight floor**; this
excludes runtime, activations, tokenizer, loading copies and predictor memory.
Actual installed-model peak RAM and latency must be measured later. Reported
whole-process peak RSS is a lifetime high-water mark, not incremental model RAM.

## Reproduction

Use the existing environment; no installation is needed for A/B. For seed 1:

```sh
UV_CACHE_DIR="$PWD/.uv-cache" .tools/bin/uv run --no-sync model-learner sim representation-fixture /tmp/public-representation.json --seed 1 --count 150 --scenario state_signal
UV_CACHE_DIR="$PWD/.uv-cache" .tools/bin/uv run --no-sync model-learner learn representation-eval --input-file /tmp/public-representation.json --source-kind simulated --dataset-id task-state-state_signal-seed-1 --dataset-version 1 --acceptance-id controlled-task-acceptance --acceptance-version 1 --train-until 2026-01-01T04:30:00Z --evaluation-at 2026-01-01T07:30:00Z --seed 1
```

Repeat with seeds 0–4 and `null_signal` (change the dataset ID accordingly) for
the stored rehearsal. Reuse input files for statistical reproducibility; timing
and RSS naturally vary. The fixture writer refuses to overwrite prior evidence.
For an already approved bundle, supply all of `--model-path`, `--model-sha256`,
`--model-revision`; unavailable loading retains A/B and reports the C blocker.

Owned checks and independent review evidence are recorded by the coordinator
with final full-suite/lint/format results in STATUS.md.
No next milestone is started.
