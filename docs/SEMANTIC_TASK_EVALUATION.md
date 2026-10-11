# Semantic task retrieval: first independent evaluation

This increment evaluates an optional historical-task shortlist from explicitly
supplied task descriptions. Potion improves top-three relevance on this constructed
fixture, but remains unreliable at distinguishing shared words from a shared
objective. It supplies advisory relatedness, never task identity, continuation,
verification or agent-success probability. No learner features, utility estimates,
routing decisions, raw transcripts, or execution-state summaries are modified.

## Data and freeze

`tests/fixtures/understanding/retrieval_v1.json` contains newly authored, reviewable
technical examples and relevance judgments. A Codex implementation agent authored
them before invoking the evaluated encoder. They are **not externally human
adjudicated**, copied public issues, real user history, model2vec-derived labels,
or actual executed outcomes. Every candidate has a technical judgment rationale;
the query's explicit relevant-ID list determines binary relevance. No third-party
text or external license is asserted. Review checked the rationales separately.

The final pre-encoding content SHA-256 is
`75a4208dea16b4aec6c6d3cfa59d5e29f67f2c028a70823f49cf56baf9b4000d`.
`manifest.json` fixes this hash, cohort counts, k values and freeze policy. Before
initial encoding, review corrected only provenance wording about agent authorship
and an absent repository license; no text, relevance judgment or split changed.
Do not revise v1 labels after inspecting rankings. Future label/data improvements
require a new dataset identity and a new holdout.

The development split has four queries, two families/projects and twelve
candidates. The locked test split has twelve queries, six families/projects and
thirty-six candidates. Each family has two correlated rewrites of one objective
and six candidates: a paraphrased repair, independent regression work on the same
problem, a wording trap with a documentation objective, unrelated work in the same
project, a nearby technical problem, and explicitly changed scope after the
historical problem was resolved. Each query has exactly two relevant candidates.
All candidates outside its family are judged irrelevant under the fixture's
narrow shared-objective/mechanism definition.

Development and test share no project, technical family or rewrite group. Query
rewrites and their target candidates deliberately belong to the same family
**within** a split: recognizing relevant historical examples is the retrieval
objective. That is not a training leak. There is no supervised training,
encoder fitting, or development/test threshold selection. TF-IDF's vocabulary
and smoothed document frequencies are fitted to the candidate corpus only, as
required for a retrieval index; query text and judgments do not enter that fit.
The index receives only candidate IDs, descriptions and source attestations.
Family, project, relevance, rationale and candidate-type annotations enter the
metrics only after ranking.

Candidate identifiers encode family and numbered position. They are not scoring
features, but lexicographic ID ordering resolves exact score ties. Review found
two mixed-relevance Jaccard ties crossing the top-three boundary where this rule
favors relevant candidates; no such TF-IDF boundary ties were found at k=1/3.
This is a limitation of v1. Use opaque, neutral IDs in the next fixture rather
than rewriting a frozen dataset after observing scores.

## Methods and metric denominators

The deterministic baseline uses casefolded alphanumeric token-set Jaccard overlap.
TF-IDF uses token counts, corpus-only `log((1+N)/(1+df))+1` weights and cosine
similarity, with no stemming or stopwords. Potion uses the existing approved local
CPU Model2Vec static encoder, `minishlab/potion-base-8M`, revision
`bf8b056651a2c21b8d2565580b8569da283cab23`, bundle SHA-256
`930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2`.
It remains frozen: 256 dimensions, mean token pooling, L2 normalization, bounded
4096-character inputs and 256-token truncation. No model was downloaded or
fine-tuned for this increment, and no optional dependency was added.

The fixed evaluation ranks every candidate with a known representation, including
zero/negative scores, without a relevance threshold. Ties use ascending task ID.
Unknown representations produce no arbitrary matches and receive zero retrieval
credit when independently labeled targets exist. No measured query or candidate
was unknown. Operational search's default positive-score filter is a display
rule, not a calibrated acceptance threshold.

Precision@k divides relevant returned slots by k, including any missing slots.
Recall@k divides by the two labeled relevant candidates. Thus the maximum
precision@3 here is **2/3**, not 1. MRR uses the full ranking's first relevant rank;
binary nDCG@k divides discounted relevance by the best possible ranking at k.
Numbers below are macro query means. Three fresh repetitions check deterministic
replay and measure overhead; they are not extra independent accuracy samples.
With only six purposively authored test families and two correlated rewrites per
family, no population confidence interval, significance claim or real-world
accuracy claim is justified.

## Frozen locked-test results

`reference.json` retains all nine workers' scores, query ranks, family metrics,
false-association diagnostics, model identity and resource measurements. Stored
top-three scores, relevant-target ranks and metrics replayed identically across
workers.

| Method | Precision@1 | Recall@1 | Precision@3 | Recall@3 | MRR | nDCG@3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Token overlap | 0.2500 | 0.1250 | 0.2778 | 0.4167 | 0.4393 | 0.3522 |
| TF-IDF | 0.2500 | 0.1250 | 0.2778 | 0.4167 | 0.4526 | 0.3589 |
| Potion | 0.3333 | 0.1667 | 0.4167 | 0.6250 | 0.5745 | 0.5255 |

Potion recovers **15 of 24** relevant query/candidate occurrences in the top three,
versus **10 of 24** for both baselines. Top-one correctness improves by only one
query: **4/12 versus 3/12**. Its first result is irrelevant in **8/12** queries;
the baselines have **9/12** irrelevant first results. These are retrieval false
associations, not classifier false-positive rates.

All three methods rank the documentation wording trap first on all six original
queries. Potion's other two top-one errors are a changed-scope billing task and
an independent payment test retrieved for an authentication-renewal query. Text's
remaining three first results are unrelated same-project candidates; TF-IDF's
remaining errors are two such candidates and the changed-scope billing task.
Scope-diverged descriptions deliberately contain old task vocabulary: high
similarity does not establish the current objective or a continuation.

| Test family (two correlated queries) | TF-IDF Recall@3 | Potion Recall@3 |
| --- | ---: | ---: |
| Concurrent session updates | 0.00 | 0.50 |
| Filtered database access path | 0.50 | 0.25 |
| Keyboard dialog focus | 1.00 | 0.50 |
| Native-wheel packaging | 0.75 | 1.00 |
| Duplicate payment delivery | 0.00 | 0.50 |
| Archive path containment | 0.25 | 1.00 |

For the paraphrased checkout replay query, Potion finds both idempotency repair
and repeated-envelope regression work at ranks one and two; lexical methods find
neither in their top three. For the paraphrased login lost-update query, it finds
both relevant authentication tasks at ranks two and three, but puts an unrelated
payment test first. It loses relevant dialog-focus and database-query work versus
TF-IDF. These mixed results are visible in the per-query artifact rather than
hidden by the average.

Development results are reported separately, without selecting a threshold:
TF-IDF/Potion Recall@3 **0.375/0.750**, Precision@1 **0.500/0.250**. They do not
constitute extra locked-test examples or threshold validation.

The fixture has no queries with zero relevant candidates and no independently
adjudicated real tasks. It cannot establish no-match rejection behavior, score
calibration, category classification, changing-scope detection or semantic
continuation inference. Those capabilities are deferred. Task/session links
remain explicit authoritative ledger records; similarity never creates links.
There are no outcome labels and no claim about agent-success prediction.

## Actual CPU overhead

Measured on macOS arm64, Python 3.12.14, with existing model2vec 0.9.0, NumPy 2.5.4,
safetensors 0.8.0 and tokenizers 0.23.3. Each of three workers per method is a fresh
process with requested single-thread environment limits and tokenizer parallelism
disabled before importing the numerical runtime. Socket connections are blocked;
all nine workers report **zero connection attempts**. This is a reproducible
local benchmark guard, not an attestation of hostile-process network isolation.
OS file caches were not cleared.

| Measurement | Token overlap | TF-IDF | Potion |
| --- | ---: | ---: | ---: |
| Model load | n/a | n/a | 0.178–0.264 s |
| Candidate index build (36 descriptions) | 0.118–0.135 ms | 0.274–0.308 ms | 3.747–4.608 ms |
| Warm query search median | 0.0388–0.0436 ms | 0.0427–0.0435 ms | 0.4397–0.4636 ms |
| Warm query search p95 | 0.0459–0.0600 ms | 0.0523–0.0543 ms | 0.4701–0.5475 ms |
| Whole worker peak RSS | 38.57–38.60 MB | 38.50–38.57 MB | 132.20–132.24 MB |

MB is decimal bytes/1,000,000. Model loading includes optional imports,
bounded safe snapshot, fixed file/bundle hashing and construction. The first
single-description encode after loading is measured separately at
**2.85–8.09 ms**. Warm single-description encode medians are
**62.50–68.29 microseconds**, p95 **70.29–78.12 microseconds**, each from five serial
passes over 48 test texts (240 samples per worker). Search measurements use five
serial passes over twelve queries (60 samples per worker), including query
representation, scoring and sorting 36 candidates; they exclude index building
and load. The frozen F32 parameter table is exactly **30,236,672 bytes**.

RSS is the lifetime whole-worker high-water mark, including runtime, data parsing,
indexing and measurements. It is **not incremental model RAM**. The fresh lexical
workers provide a process-level comparison, not an exact subtraction of model
memory. The linear scan timings apply to these short descriptions and 36
candidates; they do not establish a large-history throughput or worst-case bound.

## Integration decision and next evidence

The top-three improvement supports a small, explicitly optional advisory shortlist
experiment; it does not support trusting the top result, grouping tasks, utility
features or routing. `model-learner task similar TASK_ID` defaults to TF-IDF and
also accepts `--backend text` or explicitly pinned `--backend potion` with a local
bundle path/revision/hash. Results explain scores and model provenance. Missing
Potion dependencies/weights return unavailable, without silently changing model.
Descriptions are manually declared text; no transcripts are read. The command
shows historical declared canonical task IDs without merging them or inferring
continuation. Execution-state summaries, characteristic inference and scope
classification are deliberately outside this increment.

Potion's roughly 0.18–0.26-second load and ~132-MB whole-process peak can be
reasonable for an opt-in local shortlist. Warm search is roughly ten times the
lexical baseline here, though both remain submillisecond at this corpus size.
The accuracy benefit is uneven and top-one error rate remains high; the evidence
does not justify switching the default, treating similarity as reliable identity,
or fine-tuning now. A separately authorized next increment should gather more
independently human-reviewed, prospectively locked examples with opaque IDs,
multiple varied negative objectives and **no-relevant-history** queries, then
measure rejection and per-family errors before considering objective-aware
reranking or fine-tuning. Changing-scope and task-characteristic classifiers need
their own independent labels and evaluation, not fabricated outcomes.

## Reproduction

No remote access or installation is required if the approved optional environment
and weights already exist. Use the repo's existing optional environment; tests
never discover/download weights. Run from the repository root, with an explicit
path to the existing approved model:

```sh
export PATH="$PWD/.tools/bin:$PATH"
export UV_CACHE_DIR="$PWD/.uv-cache"
uv run --no-sync python -m model_learner.understanding.experiment \
  --dataset tests/fixtures/understanding/retrieval_v1.json \
  --dataset-sha256 75a4208dea16b4aec6c6d3cfa59d5e29f67f2c028a70823f49cf56baf9b4000d \
  --model-path "$PWD/.model-learner/models/potion-base-8M-bf8b056651a2c21b8d2565580b8569da283cab23" \
  --bundle-sha256 930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2 \
  --output /tmp/semantic-retrieval-reproduction.json
```

Output creation is exclusive. Omitting both model arguments reproduces the two
lexical baselines. Optional actual-model tests use
`MODEL_LEARNER_TEST_POTION_PATH` pointing explicitly to the approved bundle.
Tests cover exact metric denominators, invalid labels/split leakage, freeze/hash
integrity, label changes preserving ranks, annotation changes preserving ranks,
unknown embeddings and exact frozen lexical/optional Potion reproduction.

The subsequent [annotation workflow and evaluation protocol](TASK_ANNOTATIONS.md)
prepares fresh independently human-reviewed data, no-match queries and abstention
evaluation. This original v1 dataset and its results remain frozen; the new
workflow does not turn its agent-authored labels into human-reviewed ground truth.
