# Bounded local semantic extraction experiment — 2026-10-13

Status: design prepared; model weights require the user's approval. No local model
comparison or improvement claim exists yet. Production analysis remains unchanged.

This is an explicitly authorized experiment outside the initial-release scope in
the master plan (§1.2). It changes no production architecture or outcome semantics.
The existing 15 user messages are consumed diagnostics. All references are
AI-authored, not human-verified ground truth.

## Representation and input policy

The existing representation retains positive/removal evidence overlays, a single
objective anchor, actor-attributed reports and lexical candidate links. It does
not solve active scope, reinstatement or accepted assistant proposals. Source-span
integrity and semantic correctness must therefore be measured separately.

Use every unchanged user-only prefix for each diagnostic checkpoint, preserving
original roles, turns and message/evidence identity. No assistant text, tools,
existing predictions, annotations or matching ledger enters candidate C's input.
New synthetic cases use the same prefix policy. No truncation or summary replaces
source text. Unsupported bounds produce unavailable predictions, not empty events.

The common output is a nullable current objective plus message-local events:

- `requested_action`, `requirement_added`, `constraint`;
- `decision`, `decision_reversed`;
- `requirement_removed`, `requirement_revised`, `requirement_reinstated`;
- `reported_failure`, `reported_progress`, `completion_claim`;
- `conditional`, `earlier_reference`, `uncertainty`.

Each objective/event carries a source message ID, exact quote and occurrence,
semantic summary, mode (`request`, `hypothetical`, `report`, `unknown`), optional
condition and nullable earlier target (source message ID, exact quote, occurrence).
The harness resolves quotes to original half-open character offsets, records source
role/turn and rejects invalid citations. An unknown or ambiguous target remains
null. A target denotes source evidence, not an accepted state mutation. Multiple
events can cite one region; distinct obligations must retain distinct summaries.

Requests and conditional permissions cannot imply an observed failure/progress or
completion. Code/example values are specification evidence, not execution reports.
Textual test assertions remain reports. Independent verification is always null
in this experiment; no message extraction can supply it. Current objective means
the focal requested activity at that checkpoint, including a later reporting phase.

## Initial candidate and runtime

Choose **Qwen2.5-1.5B-Instruct, official GGUF Q4_K_M** initially: 1.54B parameters,
1.12 GB download, Apache-2.0. The model card specifically describes instruction
following and JSON generation. Its 32,768-token model context comfortably exceeds
the intended short prefixes; use a bounded 8,192-token runtime context initially.
Allow approximately 2–3 GiB process memory as a planning estimate, not a measurement.
Quantization may reduce semantic reliability; actual speed and memory must be run.
[Model card](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF),
[weight listing](https://huggingface.co/Qwen/Qwen2.5-1.5B-Instruct-GGUF/tree/main).

Alternatives considered: Qwen3-1.7B official Q8_0 (1.83 GB, Apache-2.0), with
non-thinking mode available but additional template/mode handling; SmolLM2-1.7B
Instruct (Apache-2.0), English-oriented instruction/function-call support and about
1.06 GB Q4_K_M conversion. Neither is downloaded or evaluated. Vendor benchmark
claims do not establish superiority on task-state extraction.
[Qwen3](https://huggingface.co/Qwen/Qwen3-1.7B-GGUF),
[SmolLM2](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct),
[SmolLM2 GGUF](https://huggingface.co/HuggingFaceTB/SmolLM2-1.7B-Instruct-GGUF).

Use a repository-local **llama.cpp** runtime (MIT), CPU only, no Metal/GPU offload,
one request at a time and loopback access only if using its server. Pin the runtime
revision and weight revision/hash. This avoids PyTorch/Transformers dependencies
and leaves the project environment/lockfile unchanged. C/C++ runtime plus system
libraries suffice; source building requires a compiler and CMake. Prefer a bounded
official ARM64 release binary if compatible. Grammar-constrained JSON supplies
syntax only: validate evidence and semantics separately. No hosted endpoint,
external LLM API, fine-tuning, agent framework or automatic model routing.
[Runtime](https://github.com/ggml-org/llama.cpp),
[JSON grammar support](https://github.com/ggml-org/llama.cpp/blob/master/grammars/README.md).

## Freeze and comparison protocol

A: use the current frozen analyzer with its recorded SHA-256, unchanged. Preserve
the old private reports; map its output into the common schema without inventing
unsupported events or resolved targets. For new cases, run this identical source.

B: an isolated deterministic parser preserves Markdown list items, wrapped prose,
code blocks, questions and conditionals. Its semantic rules are intentionally
bounded; preserve ambiguity and abstain rather than treat all text as obligations.
Use general structure/cue rules, no diagnostic-specific phrases or thresholds.

C: one zero-shot prompt, no diagnostic demonstrations, original prefix text and
the common schema. Include no A/B predictions or reference labels. Freeze decoding
settings, prompt, parser, adapters, evaluator and limits before any evaluation.
No prompt/rule tuning on either diagnostic or holdout results.

Before candidate predictions, author and independently review a small synthetic
reference set on fresh topics/forms, covering all change subtypes, ambiguous
targets, indirect requests, code examples, reports, questions and conditionals.
Freeze source and reference hashes with a timestamp. The reviewer must not inspect
candidate predictions. Keep labels in a separate file never supplied to C. These
are prediction-blind AI judgments, not authenticated human labels or random samples.
After evaluation this set is consumed; do not call it untouched in future work.

Freeze a separate diagnostic reference adapter before new predictions. Preserve
the original independent annotations and disclose policy changes/atomization.
Old post-hoc scores remain historical; do not silently equate new scorer results
with 21/24 or 21/84. No new source retrieval is needed.

## Measurement and decision rules

Report diagnostic and fresh-holdout results separately, with per-case examples:

1. Objective core-action agreement per checkpoint; unknown objectives counted.
2. Atomic requirement precision/recall with matched/predicted/reference counts.
3. Decision and reversal recognition, distinguishing requests for recommendations.
4. Added/removed/revised requirement precision/recall by subtype.
5. Reinstatement precision/recall separately.
6. Earlier-target correctness conditional on recognized events, plus recovery over
   all reference links. Null/ambiguous targets remain explicit.
7. False failure reports and negative-case denominators.
8. False completion claims and negative-case denominators; false verification.
9. Valid source evidence, role attribution and semantic evidence matching separately.
10. Unavailable/invalid predictions, nullable objectives/targets, required abstention,
    unparsed units and source uncertainty; empty denominators give null ratios.
11. CPU wall-clock latency per prefix, median/p95, load/cold timing separately;
    no prompt-cache advantage, serial inference, actual threads/context/tokens.
12. Process peak RSS in bytes, with measurement method and scope (runtime versus
    driver), independently from planning estimates and weight download size.

Require one-to-one atomic semantic matching; span overlap alone cannot establish
equivalence. Preserve requests/reports/conditions and target identity. Any manual
semantic mapping is an explicit AI scoring judgment with a saved ledger and an
independent audit. Do not cherry-pick correct events or duplicate overlap categories.

Frozen scoring detail: the positive-obligation family includes `requested_action`,
`requirement_added`, `constraint`, and `requirement_revised`. Other families require
the exact subtype and mode; obligation subtypes may match within this family.
One output event can match at most one reference event, even if its wording bundles
several obligations. Do not split predictions after results. Objective anchors do
not create extra obligation atoms. Mode must match; condition and negation must be
semantically supported. Invalid-citation events remain in precision denominators
and cannot match. Unavailable generations remain unavailable, not correct empty
outputs. A semantic match requires supported meaning and correct evidence context;
literal span overlap alone never earns credit. Save unmatched predictions/references
implicitly by complete indexed output plus explicit successful pairs and reasons.

For diagnostic references, preserve the original 84 positive atoms and 28 choice
atoms. Merge four canonical revisions into their corresponding obligation atoms;
retain one removal and one reinstatement separately. Mark the two originally
explicit reversed choices as reversals. Overlapping obligation/choice categories
are retained and disclosed; no combined accuracy is computed. Earlier citations
in this adapter identify whole messages; target credit additionally requires the
correct earlier semantic obligation. Historical 21/24, 21/84 and 0/6 remain separate
because the new frozen scorer forbids post-hoc prediction splitting and gives
requested-action evidence a common obligation-family mapping. Diagnostic conditional
and semantic-uncertainty reference populations are unavailable; do not invent them.

False failure/completion negatives are checkpoints with no such reference report;
also report false event counts. Null-objective correctness is separate from
non-null agreement. Target recovery includes all non-null reference links,
including explicit references/reversals; also report the six diagnostic canonical
scope links separately from overlapping choice links. Null-target correctness is
limited to matched relational events with a null reference target. Runtime p95
uses nearest rank over all attempted requests, including unavailable generations;
median is the ordinary middle value/mean. Peak RSS is the entire server lifetime
high-water mark, measured by macOS `getrusage` for its fresh driver's sole child;
driver high-water memory is reported separately.

Predeclared meaningful-improvement screen: C improves holdout requirement recall
by at least 20 percentage points over both A/B while keeping precision at least
0.85, improves objective agreement by at least 20 points, recovers at least half
of reference earlier links, and creates no false completion/verification claims.
Also require median CPU latency at most 30 seconds/prefix and peak runtime RSS at
most 4 GiB. These are pragmatic experiment thresholds, not reliability guarantees.
Report all dimensions even if the screen fails; small dependent samples do not
justify population accuracy, calibrated uncertainty or downstream utility claims.

Recommend the simplest supported approach. A hybrid may preserve structure/evidence
deterministically, infer semantics locally and apply explicit provenance-bearing
state updates, with verification separate. Passing this screen can justify further
prospective human-adjudicated evaluation; it does not authorize production changes.

## Isolation and stopping point

Put experimental code under `experiments/local_task_state/`, sanitized synthetic
fixtures alongside it, and all private diagnostics/model/runtime artifacts under
ignored `.model-learner/`. Do not modify the production analyzer or integrate
estimators. Run meaningful experiment tests, the repository suite and Ruff checks,
obtain independent review, and update STATUS with sanitized actual findings.
Weight download is gated by the user's explicit instruction. Finish comparison
and recommendation after approval; stop there.
