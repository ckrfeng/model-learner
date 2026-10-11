# Optional local CPU task representation prototype

Delivered 2026-10-11. This is a separate observational/predictive experiment in
`model_learner.representation`; the existing probabilistic learner is unchanged.
It collects no transcripts, performs no remote inference or automatic downloads, fine-tunes
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

## Original MiniLM adapter (initial integration pending)

The original narrow adapter supports
[`sentence-transformers/all-MiniLM-L6-v2`](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2),
using its 384-dimensional masked mean pooling and L2 normalization. The operator
must already have an approved local bundle and `torch`, `transformers` and
`safetensors` installed. The initial A/B work installed/downloaded none. No model
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

**Initial local runtime inspection:** torch, transformers and safetensors were all
absent. No existing approved bundle was supplied. Therefore actual model loading,
pretrained inference, C held-out scoring and semantic resource measurement remain
unavailable at that checkpoint. Negative descriptor/configuration/loader tests validate
guards, not compatibility with an actual installed runtime/model. Actual adapter
integration must be validated with operator-approved existing software/model
before making a MiniLM comparison claim. The approved Potion integration below
completes actual C evaluation with a separate explicit backend.

## Initial A/B controlled rehearsal and overhead

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

## Completed pretrained Potion C evaluation — 2026-10-11

The user selected [minishlab/potion-base-8M](https://huggingface.co/minishlab/potion-base-8M)
and approved model download plus project-local optional CPU dependencies. Its
[pinned configuration](https://huggingface.co/minishlab/potion-base-8M/blob/bf8b056651a2c21b8d2565580b8569da283cab23/config.json)
is a 256-dimensional Model2Vec static model, rather than the original
384-dimensional BERT architecture. A narrow `representation.potion` adapter
preserves the text-to-vector interface and existing A/B implementation. The
evaluator's semantic dimension check now supports the two explicit adapters;
no model is automatically selected or substituted when loading fails.

- Model: `minishlab/potion-base-8M`; revision
  `bf8b056651a2c21b8d2565580b8569da283cab23`; MIT license.
- The approved bundle is exactly `config.json`, `model.safetensors`, and
  `tokenizer.json`: **30,920,628 bytes**. Frozen F32 weights have shape
  **29,528 × 256**, or **30,236,672 bytes** / 7,559,168 parameters.
- Weights' [upstream SHA-256](https://huggingface.co/minishlab/potion-base-8M/blob/bf8b056651a2c21b8d2565580b8569da283cab23/model.safetensors):
  `f65d0f325faadc1e121c319e2faa41170d3fa07d8c89abd48ca5358d9a223de2`.
  Bundle SHA-256: `930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2`.
  All three files must match hardcoded approved-revision identities and the
  supplied bundle pin, after bounded no-follow copying to a private snapshot.
- Weights and download receipts reside under ignored `.model-learner/models/`;
  no weights, private descriptions or transcripts are committed. This download
  used only public unauthenticated revision-pinned URLs, with exact file identity
  and size verification. Runtime loading never downloads or discovers models.
- Optional runtime is `model2vec==0.9.0`, with all dependencies pinned in
  `uv.lock`; actual NumPy **2.5.4**, safetensors **0.8.0**, tokenizers **0.23.3**.
  The adapter directly constructs `StaticModel` from local safetensors NumPy
  arrays and a local tokenizer, bypassing the Hub loader. It loads no custom
  model code/pickle, uses no GPU/cloud inference, and marks weights read-only.
- Text is bounded to 4096 characters; fixed inference uses batch size one,
  256 tokens, no multiprocessing, UNK removal, mean pooling and L2 normalization.
  Model2Vec first truncates characters to `256 * median_token_length`, then
  truncates to 256 tokens. A no-known-token input yields a zero vector. No
  embedding weights are trained; the same fixed logistic reference fits only
  its ordinary training partition. See the [pinned runtime implementation](https://raw.githubusercontent.com/MinishLab/model2vec/v0.9.0/model2vec/model.py).

### Same frozen cohort, predictive results and uncertainty

`potion_reference.json` records all ten actual pretrained evaluations: the same
original two scenarios, seeds 0–4, 150 simulated tasks, cutoffs **04:30 / 07:30
UTC on 2026-01-01**, +30-second checkpoint, and 300 paired family bootstrap draws.
Every original A/B score, calibration bin, interval, paired comparison, sample
count and cohort SHA matches `controlled_reference.json` exactly. The old artifact
is unchanged. Independent review reproduced all ten complete numerical reports.

| Scenario | Mean A Brier | Mean B Brier | Mean C Brier | Mean B minus C |
| --- | --- | --- | --- | --- |
| Deliberate state signal | 0.256719 | 0.122489 | 0.122641 | -0.000152 |
| Null state signal | 0.254266 | 0.258117 | 0.258446 | -0.000329 |

Positive B minus C means lower C Brier. Per-seed paired 95% intervals:

| Seed | State-signal B minus C interval | Null-signal B minus C interval |
| --- | --- | --- |
| 0 | [-0.001283, 0.000962] | [-0.001251, 0.001700] |
| 1 | [-0.000068, 0.000872] | [-0.000147, 0.001748] |
| 2 | [-0.002088, 0.000562] | [-0.006240, 0.001969] |
| 3 | [-0.000470, 0.000267] | [-0.001557, 0.000491] |
| 4 | [-0.000886, 0.000186] | [0.000056, 0.000736] |

All five state intervals cross zero; one null seed has a positive interval.
There is **no consistent semantic improvement**. Six held-out families provide
limited uncertainty evidence, fits are treated as fixed, and the exploratory
comparisons have no multiplicity correction. Equal-seed means are descriptive,
not pooled confidence intervals. Each C score interval and all calibration bins
remain in the artifact.

These public descriptions were generated independently of eventual outcomes
and struggling state. The existing data has **no designed semantic outcome
signal**. Results establish actual pretrained integration, overhead and held-out
numerical behavior, not real-world task understanding. A null/negative result
here cannot show that embeddings are useless for real tasks. No real coding
agents were launched, and the blocked benchmark execution system is unchanged.

### Actual CPU overhead and memory

Ten fresh Python 3.12.14/macOS arm64 processes used minimal environments,
requested single-thread CPU limits, and disabled tokenizer parallelism and
multiprocessing. Socket connection methods were blocked before loading and
encoding; **zero connection attempts** occurred in every worker. OS file caches
were not cleared. Times include adapter conversion/validation; these short
public task descriptions are not a worst-case performance benchmark.

| Component | Actual measurement |
| --- | --- |
| Fresh-process model load | **0.167–0.264 s**, mean **0.192 s**; includes snapshot/hash checks and runtime import/construction. |
| First description warmup | Mean **3.83 ms**; reported separately. |
| Bulk embedding throughput, batch size one | Mean **52.97 µs/description** over selected training/scoring inputs. |
| Serial description latency after warmup | Per-worker median **58.33–59.88 µs**, p95 **62.04–65.71 µs**; five passes over scored descriptions (285–290 samples each). |
| Frozen C reference prediction | Mean **25.83 µs/checkpoint**, separate from embedding. |
| Fixed C reference fit | Mean **0.603 s**; training overhead, not inference or encoder fine-tuning. |
| Actual F32 embedding-table memory | **30,236,672 bytes**; excludes tokenizer/runtime/other objects. |
| Whole fresh-process peak RSS | **139,575,296–140,345,344 bytes** (139.58–140.35 MB decimal), including load, features, fitting and measurements. |

RSS is a lifetime high-water mark, not incremental model RAM. C feature-object
census averages **4,055,355 bytes**, versus **415,670 bytes** for B; this is an
approximate Python object census. The 52.97 µs embedding number excludes C feature
dictionary construction, B extraction, cohort parsing and C reference prediction.
All phase measurements, runtime versions and model identities are retained in the
new report. The initial MiniLM 90.8 MB parameter estimate is not used for Potion.

Reproduce using the approved ignored bundle and existing optional environment:

```sh
export PATH="$PWD/.tools/bin:$PATH"
export UV_CACHE_DIR="$PWD/.uv-cache"
uv sync --locked --extra semantic
uv run --no-sync python -m model_learner.representation.potion_experiment \
  --model-path "$PWD/.model-learner/models/potion-base-8M-bf8b056651a2c21b8d2565580b8569da283cab23" \
  --bundle-sha256 930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2 \
  --reference tests/fixtures/representation/controlled_reference.json \
  --output /tmp/new-potion-report.json
```

The reproducer refuses existing output and fails if frozen A/B metrics or cohort
bindings differ. It never downloads, launches agents or writes ledger records.
For an existing input file, `learn representation-eval` accepts explicit
`--model-id minishlab/potion-base-8M` plus `--model-path`, `--model-sha256` and
`--model-revision`; default behavior remains the original optional MiniLM choice.
Tests requiring weights opt in through `MODEL_LEARNER_TEST_POTION_PATH`; default
tests do not scan caches, install software or download models. Stop after C.
