# Local CPU task-state comparison — 2026-10-13

**Recommendation: do not add the selected local model to production.** The frozen
Qwen2.5-1.5B-Instruct Q4_K_M configuration did not improve semantic extraction.
Its memory and latency were practical, but its evidence contract and task-state
interpretation were unreliable. Structure-aware parsing helped some lists; it
also remains unsuitable as trusted success/utility-estimator input.

This is diagnostic **AI-reference agreement**, not human-verified semantic accuracy.
Production analyzer, importer, estimator, dependencies and lockfile are unchanged.
No fine-tuning, routing, Governor, cloud inference, paid API, new real-conversation
retrieval, commit or publication occurred. The user approved the single weight
download and comparison. Stop after this report and recommendation.

## Experiment and independence

The [design](LOCAL_TASK_STATE_EXPERIMENT.md) defines the common schema, bounded
source-only prefixes, evidence contract, comparison families and improvement
screen. A uses the existing current frozen analyzer; B is an isolated coarse
structural parser; C uses one zero-shot prompt and schema-constrained local JSON.
Every candidate received identical unchanged user-only prefixes. Existing
predictions and reference labels never entered C's request. All statement modes,
original message IDs, quotes, character coordinates and nullable earlier targets
remain inspectable. There is no active-scope solver or independent verification.

The old 15 messages from four real conversations are consumed diagnostics. Their
unchanged independent AI annotations supplied 84 positive-obligation and 28 choice
atoms. Four canonical revisions were merged into corresponding obligation atoms;
one removal and one reinstatement remain separate. Two choices are explicit
reversals. This adapter froze before predictions; original artifacts are unchanged.
Its overlapping obligation/choice categories do not support a combined accuracy.

A separate prediction-blind AI author created four fresh simulated conversations
about museum audio, a seed exchange, tabletop puzzle cards and textile care cards:
**16 checkpoints, 56 events, nine earlier links, one null objective**. The author
inspected neither candidate implementations nor predictions, prior fixtures or
private diagnostics. Source and reference hashes froze before predictions. These
are independently authored AI judgments, with dependent conversation checkpoints
and no claim of representative sampling. The set was untouched at prediction
time and is now consumed; no prompts or rules were tuned on it.

Initial sources, reference labels, prompt, schema, extractors, runtime settings and
scorer froze before inference. Independent review found validation gaps in the
scorer before output inspection: duplicates, negative indices and missing target
reasons. Those checks were repaired, with original code/freeze archived. The
positive-obligation denominator was also narrowed to request-mode events, excluding
one hypothetical restriction and one unidentified pending revision. This is an
explicit **measurement-policy amendment**, not a pristine scorer preregistration.
The original-denominator sensitivity is reported below. No source/reference,
extractor, prompt, model or decoding setting changed.

The independent final reviewer audited source hashes, all 93 A/B/C input receipts,
revalidated extractions and explicit semantic matching ledgers. One B uncertainty
match was added on review; no diagnostic match changes were requested. All semantic
judgments remain AI-authored. Post-run infrastructure hardening adds strict flags,
source validation, unavailable bound handling and redirect rejection; the actually
executed runner is archived. These changes do not alter the saved predictions.

## Metrics and denominators

Positive obligations include requested actions, additions, constraints and revisions
in request mode. Matching requires supported semantics, the same message and mode;
subtypes may differ within that family. Other families require exact subtypes.
Each output event earns at most one reference atom, even when it bundles several
obligations. Objective anchors do not create extra obligation atoms. Invalid
events stay in precision denominators and cannot match. Context-assisted fragment
matches are disclosed separately. Empty/comparability denominators are unavailable.

**Fresh holdout at first prediction:** counts below are matched/predicted for
precision and matched/reference for recall.

| Measurement | A: frozen rules | B: structural parser | C: local model |
| --- | --- | --- | --- |
| Current objective agreement | 1/16 | 5/16 | 1/16 |
| Known objective agreement, excluding null case | 0/15 | 4/15 | 0/15 |
| Correct null objective | 1/1 | 1/1 | 1/1 |
| Positive-obligation precision | 10/16 | 12/13 | 3/25 |
| Positive-obligation recall | 10/31 | 12/31 | 3/31 |
| Decisions, precision / recall | 1/3; 1/5 | 2/2; 2/5 | 0/1; 0/5 |
| Added requirements, precision / recall | 2/11; 2/10 | 3/4; 3/10 | 0/1; 0/10 |
| Removed requirements, precision / recall | 2/2; 2/3 | 0/0 unavailable; 0/3 | 0/2; 0/3 |
| Revised requirements, precision / recall | 2/4; 2/3 | 1/1; 1/3 | 0/3; 0/3 |
| Reinstatement, precision / recall | 0/0 unavailable; 0/2 | 1/1; 1/2 | 0/0 unavailable; 0/2 |
| Reversal, precision / recall | 0/1; 0/1 | 0/0 unavailable; 0/1 | 0/1; 0/1 |
| Earlier-link recovery | 0/9 | 0/9 | 0/9 |
| Earlier-reference event recall | 0/1 | 0/1 | 0/1 |
| Reported failure recall | 1/3 | 1/3 | 0/3 |
| Reported progress recall | 0/3 | 0/3 | 0/3 |
| Completion-claim recall | 2/2 | 0/2 | 0/2 |
| Conditional event, precision / recall | 0/0 unavailable; 0/1 | 0/1; 0/1 | 0/0 unavailable; 0/1 |
| Source uncertainty, precision / recall | 0/29; 0/3 | 2/6; 2/3 | 0/0 unavailable; 0/3 |
| Valid message-local event citations | 56/56 | 24/24 | 4/33 |

The revision denominator includes one unknown pending edit; it is excluded from
positive obligations. A's field cannot explicitly represent reinstatement; its
0/2 is common-schema coverage, not evidence about a native reinstatement class.
B labels the conditional permission as request, whereas the reference labels it
hypothetical. This mode-policy mismatch prevents conditional credit; no observed
printer failure can be inferred from the permission.

**Consumed diagnostics under the new common scorer:**

| Measurement | A | B | C |
| --- | --- | --- | --- |
| Current core-action objective agreement | 3/15 | 8/15 | 0/15 |
| Positive-obligation precision | 23/30 | 35/43 | 2/30 |
| Positive-obligation recall | 23/84 | 35/84 | 2/84 |
| Decisions, precision / recall | 4/7; 4/28 | 0/0 unavailable; 0/28 | 0/0 unavailable; 0/28 |
| Added requirements, precision / recall | 14/19; 14/80 | 12/15; 12/80 | 0/1; 0/80 |
| Removals, precision / recall | 1/2; 1/1 | 1/1; 1/1 | 0/0 unavailable; 0/1 |
| Revisions, precision / recall | 1/2; 1/4 | 0/0 unavailable; 0/4 | 0/2; 0/4 |
| Reinstatement recall | 0/1 | 1/1 | 0/1 |
| Reversal recall | 0/2 | 0/2 | 0/2 |
| Canonical scope-target recovery | 0/6 | 1/6 | 0/6 |
| All reference-link recovery, including reversed choices | 0/8 | 1/8 | 0/8 |
| Valid message-local event citations | 139/139 | 95/95 | 4/32 |

Historical typed precision 21/24, recall 21/84 and overlay coverage 32/84 remain
unchanged. The new scorer permits requested-action evidence in the common family,
forbids splitting bundled predictions into several matched atoms, and uses a
different declared subtype policy. These new A counts are **not** a rule improvement
or a reproduction of the old measurement. C's valid opening validator action is
outside the preserved 84-atom inventory; its unmatched status is a reference-coverage
artifact, not a false semantic action. Diagnostic conditional/uncertainty/reference
inventories are unavailable; do not interpret their numerical empty matches as
semantic false-positive rates.

## Reports, evidence and abstention

False report event counts differ from negative-checkpoint rates: an extra false
failure can occur in a message that also contains a legitimate failure report.

| Measurement | Diagnostic A / B / C | Holdout A / B / C |
| --- | --- | --- |
| Unmatched/false failure events | 2 / 0 / 0 | 3 / 0 / 0 |
| False failure on negative checkpoints | 1/14; 0/14; 0/14 | 3/13; 0/13; 0/13 |
| False completion events | 2 / 1 / 0 | 0 / 0 / 0 |
| False completion on negative checkpoints | 1/15; 1/15; 0/15 | 0/14; 0/14; 0/14 |
| Unavailable/schema-invalid checkpoints | 0/15 each | 0/16 each |
| Null predicted objectives | 7/15; 0/15; 15/15 | 13/16; 8/16; 16/16 |

C generated schema-valid JSON and stopped normally for **31/31** prefixes, but only
**8/65** raw events satisfied exact-quote and message-local evidence validation.
The other 57 events remain in raw outputs and metric denominators; 23/31 C
checkpoints have no accepted events. Most errors confuse message ordinal with
zero-based quote occurrence, repeat prior-prefix events, or alter quote boundaries.
Do not silently assign occurrence zero, drop repeats and call the result accurate,
or treat valid JSON as semantic understanding. Even its accepted removal has the
wrong report/request mode.

Evidence validity measures bookkeeping; it does not establish semantic support.
All matched events have correct original-message attribution (diagnostic 29/29,
37/37, 2/2 for A/B/C; holdout 16/16, 18/18, 3/3). These are conditional counts;
misses are excluded. No candidate establishes a holdout earlier target. Conditional
link accuracy is 0/4 for A and 0/2 for B among recognized linked reference events;
C has 0/0 unavailable. All predicted targets are null on the holdout. None recognizes
the unidentified null-target revision, so recovery is 0/1 and conditional correct
null-target abstention is unavailable. A blanket null is not calibrated uncertainty.

Independent verification remains null at all 93 candidate checkpoints by schema
and harness design. No verified outcomes were supplied. Zero affirmative verification
fields is a structural safeguard, not an empirical model verification-accuracy score.
Zero false C failure/completion reports coincides with missing all three holdout
failure reports and both completion claims; it does not demonstrate reliable status
interpretation. These are reported events, never independently verified outcomes.

## CPU latency and memory

Official **Qwen2.5-1.5B-Instruct Q4_K_M**: 1,117,320,736 bytes, Apache-2.0;
publisher weight hash verified. Official llama.cpp **b11580** ARM64 runtime, MIT;
12.1 MB runtime archive, no project dependencies added. Apple M3 Pro, 18 GiB RAM,
six CPU threads, GPU layers zero, device none, no KV offload, 8,192-token context,
3,072 output-token limit, seed 20261013, greedy decoding, one request/slot at a time.
[Model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF),
[runtime](https://github.com/ggml-org/llama.cpp).

| Resource | Diagnostics, 15 trials | Holdout, 16 trials |
| --- | --- | --- |
| C median / p95 wall time | 9.07 s / 14.17 s | 4.98 s / 14.53 s |
| A median / p95 wall time | 1.06 ms / 18.27 ms | 0.59 ms / 11.75 ms |
| B median / p95 wall time | 0.63 ms / 1.26 ms | 0.31 ms / 2.61 ms |
| Fresh server/model load | 1.55 s | 7.11 s |
| Runtime lifetime peak RSS | 2,353,102,848 bytes | 2,344,894,464 bytes |
| Driver lifetime peak RSS | about 1.1 GiB | about 1.1 GiB |
| C prompt / generated tokens | 704–1,351 / 140–740 | 579–822 / 18–479 |
| Cached prompt tokens | 0 for every trial | 0 for every trial |

Times include validation and are serial observational measurements; p95 uses
nearest rank. RSS uses macOS `getrusage` in each fresh driver for its sole runtime
child, covering the entire server lifetime, not each request or overall machine
memory. Driver peak includes whole-file weight hashing. Both servers exited zero.
Fresh-process loading is not a cold filesystem-cache benchmark. Repository tests
overlapped early holdout requests, so latency is not a controlled idle-machine
benchmark. No C generation hit the context/output limit. The initial sandbox
attempt could not bind loopback and produced no predictions; its separate failure
receipt is retained. Scoped approved execution then completed both datasets locally.

## Failure examples and sensitivity

These examples are newly authored simulated cases; no private diagnostic text or
native identifiers are included here.

- A interprets “I cannot remember which task I wanted help with” as a failure
  report, and mistakes “reverse of every card” for a decision reversal.
- B treats a whole paragraph as one event. It captures a museum ceiling revision
  while missing the separate removal, and a seed print failure while missing the
  adjacent completion claim and email action. Its blanket `imagine` cue discards
  an entire paragraph containing reinstatement and real progress reports.
- C's first museum request is an accepted action, but its objective is null and
  the ninety-second constraint is omitted. On the next message it repeats the
  earlier request and uses occurrence 1 for quotes occurring only once.
- C's care-card review repeats all four prefix messages as current events, using
  occurrences 0, 1, 2 and 3. It loses the actual shrinkage failure, printing claim
  and verification restriction.
- The unidentified “other instruction” must keep a null target. No candidate
  recovers this unknown edit as the reference represents it. No target was guessed.

Under the original scorer's broader positive-reference denominator of 33, holdout
recall is A **10/33**, B **12/33**, C **3/33**. Under repaired request-only policy it
is 10/31, 12/31, 3/31. Removing A's context-assisted introductory-note fragment gives
9/16 precision and 9/31 recall. Without diagnostic context-assisted requirement
credit: A 16/30 and 16/84; B 34/43 and 34/84; C unchanged. A conservative diagnostic
objective reading excludes B's partial uncertainty-only report anchor, giving
7/15 instead of 8/15. None of these alternatives changes the recommendation.

The prompt asks reinstatement to target prior removal; the independent holdout
author targets the original positive requirement. Both conventions need explicit
future adjudication. The frozen references were retained. Every holdout predicted
target is null, so allowing either convention still gives 0/9 recovered links;
this artifact does not explain the observed target failures.

## Recommendation and stopping point

C fails the predeclared semantic improvement screen: holdout recall and precision
are below both baselines, known objectives remain missing, and target recovery is
zero. It passes the practical runtime limits, which alone cannot justify adoption.
This finding applies to **one quantized model, prompt, schema and decoding
configuration**, not all small pretrained models. Grammar validity, quote copying,
semantic interpretation and focal-state extraction are distinct capabilities.

The simplest supported next direction is deterministic structural/evidence parsing
for a human review aid. B's small coverage gain and remaining failures do not justify
replacing A or feeding semantic hypotheses into trusted estimators. A hybrid with
deterministically assigned evidence IDs, local interpretation and explicit state
updates remains a research hypothesis; this experiment does not establish its
benefit. Independent verification must continue separately.

Any later experiment needs separate authorization and fresh prediction-blind,
preferably human-adjudicated cases. Reducing citation-generation burden is a
plausible future design, not an unreported repair of these outputs. No second model,
new prompt, fine-tuning, state integration or later milestone is started.

## Artifacts and validation

Code and independent synthetic sources/references are isolated under
`experiments/local_task_state/`. All real source text, diagnostic adapters,
weights/runtime, freezes, raw predictions, ledgers, resource logs and independent
final review remain Git-ignored under `.model-learner/local-task-state-20261013/`.
No private diagnostic fixture or transcript enters public files. The public
synthetic author attestation is `experiments/local_task_state/independent-review.md`.

Actual final tests, Ruff, artifact-integrity checks and independent review are
recorded in STATUS. The primary analyzer SHA-256 remains
`9f90a466de5e0bc0957277a453afb304491213fccb1ca517d7c1ca992978319b`.
Concurrent repository privacy-audit changes are preserved and outside this task.
