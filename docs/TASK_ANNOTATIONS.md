# Task-understanding annotation and evaluation protocol

This workflow collects independently human-reviewed judgments about sanitized
task descriptions. It prepares evidence for evaluating task understanding; it
does not establish that a semantic model understands a task or predicts
model utility better. Existing TF-IDF and frozen local Potion retrieval remain
available. No model training, downloads, automatic routing or web interface are
part of this increment.

## Identity and evidence

Explicit canonical task IDs and task/session links remain authoritative ledger
records. An annotation can describe a relationship or an apparent continuation;
it cannot create, merge, attach or replace a task. Retrieval scores suggest text
relatedness and never establish identity or continuation. Different canonical
tasks can be useful similar work without being the same task.

Each versioned annotation dataset contains explicit task-description snapshots,
queries and their complete historical candidate pools. A snapshot records its
opaque ID, split, project/family/lineage groups, optional canonical task UUID,
availability timestamp and source provenance. The dataset declares its source
kind and referenced observed facts retain their own source kinds. Source references,
SHA-256 digests, locators and authorship retain where each description came from.
Retain separate source kinds for real, simulated and benchmark material.
Constructed sanitized examples are not real executions.

Descriptions are caller-attested sanitized or declared text; the workflow does
not sanitize arbitrary input. Keep private transcripts and secrets out of shared
annotation files. Source digests identify referenced content without importing
that content into the annotation bundle. The CLI validates digest shape and
recorded provenance; it does not automatically open source references or attest
that their contents match. Reviewers should check the referenced sources.

Observed facts have their own evidence references and provenance. For example,
an emitted command exit, named test result or explicit task declaration can be an
observed fact. Similarity, scope and apparent difficulty are human judgments
about the available descriptions and evidence. Repeated failed commands do not
prove greater difficulty; completion does not prove verification; unknown facts
do not prove failure. A human continuation judgment remains an annotation even
when it cites an authoritative declaration.

## Annotation dimensions

For each query, review every candidate in its frozen split corpus. Record a
rationale and evidence references for the judgment. Label dimensions separately:

| Dimension | Judgments | Meaning |
| --- | --- | --- |
| Task similarity | Relevant, irrelevant, unknown | Useful historical work on the same objective or mechanism; shared words or project membership alone are insufficient. |
| Task continuation | Yes, no, unknown | Whether supplied declarations/evidence support continuing the historical task. Similarity alone is insufficient. |
| Scope change | Unchanged, expanded, narrowed, changed, unknown | Compare the current objective and acceptance scope with the historical description. |
| Apparent difficulty change | Easier, same, harder, unknown | A stated human comparison of the available task characteristics, without claiming measured inherent difficulty or model success. |

The query-level no-relevant-history judgment is yes, no or unknown. **Yes** means
all candidates in this specific corpus were judged irrelevant. It does not claim
that no relevant task exists elsewhere. A relevant candidate requires **no**.
Unknown candidate relevance prevents an exhaustive no-match conclusion. Sparse
labels are useful while collecting data but cannot masquerade as a complete
negative corpus for evaluation.

Describe difficult negative examples explicitly: shared wording with a different
objective, unrelated work in the same project, a nearby technical mechanism,
resolved historical work followed by changed scope, and similar independent work
that is not a continuation. Add no-match queries whose plausible historical
candidates are all irrelevant. Do not make a corpus entirely from easy unrelated
negatives or force every query to have a match.

## Independent human review

Preparation creates pending work, not human-reviewed ground truth. An author
records labels, actor identity, actor kind, timestamp, rationales and references.
A distinct human reviewer accepts or rejects that complete query judgment.
Acceptance binds to a digest of its context and labels; a later edit requires
review again. Rejection preserves the review decision rather than silently
approving the author's labels. Resolve disagreement by inspecting source evidence
and revising the dataset, never by following model scores.

Frozen evaluation requires a human author and a different accepting human
reviewer for every query. Human identity and independence are **self-attested**;
the CLI validates recorded actor kinds, distinct IDs and content binding, and
cannot authenticate the people or prove organizational independence. Independent
Codex implementation review is software review, not human annotation review.

Review descriptions and evidence before exposing retrieval rankings. When possible,
have reviewers make their initial judgments independently and discuss disagreements
only afterward. Do not show evaluation scores to persuade a reviewer to change
labels. Any labels or examples revised after observing test results need a new
dataset version and new holdout; preserve the older version and results.

## Groups, freezing and evaluation

Keep train, development and test groups independent at the project, family and
lineage levels. Correlated rewrites, retries, snapshots and descriptions of one
underlying task/execution belong to the same lineage. Group assignments are human
declarations, so inspect for aliases and undisclosed cross-project copies. The
schema cannot discover hidden correlation. Candidate/query matching within a
split is intentional retrieval evaluation, not a training leak.

Validation also rejects cross-split reuse of canonical task IDs, normalized
identical descriptions and exact source digest/locator pairs. Source locations
share one overlap check whether they appear as snapshot origins or observed-fact
origins, so changing a reused source item's role cannot bypass group separation.

The train split reserves independent examples for future work; this increment
does not train any model. Use development examples to choose the retrieval backend,
k, rejection threshold and selection rationale. Freeze those choices before
evaluating test data. If comparing backends, freeze and report each policy rather
than selecting the best one after inspecting test scores. Keep Potion's existing
model ID, revision and bundle SHA-256 explicit when using that backend.

Freeze records the selected backend, k, minimum score, selection note and model
identity, together with a payload hash. The hash detects subsequent edits to the
frozen evaluation artifact. New revisions are written to exclusive destinations;
do not overwrite a reviewed or frozen version. Preparation and collection may
reuse the existing sanitized retrieval descriptions and execution fixture
references, preserving their original authorship and synthetic provenance.

Rankings use descriptions only; labels, group annotations, rationales and observed
facts enter evaluation after retrieval. IDs serve identity and deterministic tie
ordering, so use opaque neutral IDs that do not encode relevance. Candidate-only
TF-IDF vocabulary/IDF fitting remains part of index construction. It does not use
query text or labels as fitted features. Missing representations produce unknown
status rather than fabricated scores or associations.

Report raw counts and denominator definitions alongside metrics:

| Measurement | Denominator and interpretation |
| --- | --- |
| Accepted-result precision | Relevant returned candidates divided by returned candidates with known similarity labels. No known returned candidates gives an undefined denominator. |
| Precision@k | Known relevant returned slots divided by requested k; missing slots and unknown labels receive no credit. |
| Retrieval recall | Relevant returned candidates divided by all labeled relevant candidates. No-match queries have no recall denominator. |
| Pairwise false-positive rate | Irrelevant returned candidates divided by all labeled irrelevant candidates, including candidates not returned. |
| Hard-negative false positives | Report returned hard-negative counts and their labeled denominator separately. |
| No-match false acceptance | No-match queries returning any candidate divided by all labeled no-match queries. |
| Coverage and abstention | Query counts with and without suggestions, split by match/no-match labels and representation status. |

Undefined ratios are null, not zero. Preserve per-query results, split and group
counts, unknown representation counts, source kinds, dataset and model provenance,
frozen policy and hashes. Report unknown representations separately from deliberate
threshold abstention. Unknown similarity labels are excluded from confusion
denominators; report unknown pair and returned-pair counts separately. A system
that abstains on everything can reject no-match
queries while failing to retrieve relevant history; coverage and recall expose
that tradeoff. Correlated queries are not independent samples. Small purposive
fixtures do not justify population confidence intervals or real-world accuracy
claims.

Historical descriptions and referenced facts must be available by the query
checkpoint. Facts must also be available by their owning snapshot. Later
execution results or scope declarations cannot enter an earlier retrieval input.

Continuation, scope and difficulty labels support future independent evaluation.
This increment implements no classifier for those dimensions. A future protocol
must freeze prediction rules before testing and measure class-specific precision,
recall, confusion counts and abstention against the separate reviewed labels.
Do not score a retrieval suggestion as a continuation or scope/difficulty
prediction. Better retrieval accuracy does not demonstrate better model-utility
prediction; that requires separate outcome-linked prospective evaluation.

## CLI collection workflow

Use `model-learner annotation --help` and each subcommand's `--help` for exact
arguments. The local workflow is:

1. `annotation prepare`: create a pending versioned dataset from explicitly
   supplied sanitized task material, with provenance and independent groups.
2. `annotation show`: inspect the descriptions, source/evidence context and
   pending or recorded judgments.
3. `annotation label`: supply a complete query label file with pair judgments,
   rationale, evidence references and author identity; write a new revision.
4. `annotation review`: have a distinct human accept or reject the query labels
   after independent source review; write a new revision.
5. `annotation freeze`: validate complete independent human review and freeze
   the development-selected retrieval policy to a new artifact.
6. `annotation evaluate`: evaluate a frozen split and write a report. Supply only
   the existing pinned local bundle for Potion; missing weights or dependencies
   remain unavailable and do not trigger a download or a backend change.

For a query with two historical candidates, the label file has this shape. Use
the actual IDs from `show`, include every historical candidate in that split and
write the judgments after reviewing their descriptions:

```json
{
  "no_match": "no",
  "rationale": "Prior repair addresses the same defect; the documentation task has a different objective.",
  "pairs": [
    {
      "candidate_id": "c01",
      "similarity": "relevant",
      "continuation": "unknown",
      "scope_change": "unknown",
      "difficulty_change": "unknown",
      "hard_negative": false,
      "rationale": "Same repair objective, with no explicit continuation declaration.",
      "evidence_refs": ["q01", "c01"]
    },
    {
      "candidate_id": "c02",
      "similarity": "irrelevant",
      "continuation": "no",
      "scope_change": "changed",
      "difficulty_change": "unknown",
      "hard_negative": true,
      "rationale": "Shared wording describes documentation rather than repair.",
      "evidence_refs": ["q01", "c02"]
    }
  ]
}
```

Snapshot IDs themselves are valid references to declared descriptions; observed
fact IDs are also valid when they belong to that query or candidate. Do not cite
unrelated evidence. The pair and query `provenance` fields default to `inferred`.

The command sequence below uses local input files and illustrative identities.
Replace them with real actor identities; do not adopt the example judgments as
human ground truth. Repeat label/review for every query, carrying the latest
revision forward, before freezing:

```sh
uv run model-learner annotation prepare seed.json collection-01.json \
  --dataset-id task-review-v1
uv run model-learner annotation show collection-01.json --query-id q01
uv run model-learner annotation label collection-01.json q01 q01-labels.json \
  --annotator alice --actor-kind human --output collection-02.json
uv run model-learner annotation review collection-02.json q01 \
  --reviewer bob --actor-kind human --decision accept \
  --note "Compared the descriptions and cited evidence independently." \
  --output collection-03.json
# After every query is labeled and accepted in the latest revision:
uv run model-learner annotation freeze collection-reviewed.json frozen-v1.json \
  --backend tfidf --k 3 --minimum-score 0.0 \
  --selection-note "Fixed prospective baseline; no held-out rankings inspected."
uv run model-learner annotation evaluate frozen-v1.json \
  --split test --output test-report-v1.json
```

The threshold is a strict cutoff: scores must be greater than `minimum_score`.
The illustrative zero cutoff is a prospective baseline, not a calibrated claim
that positive scores imply relevance. `show` displays supplied descriptions and
judgments without computing scores. The seed must already follow
`task-annotations/v1`; `prepare` gives it a new collection identity rather than
guessing labels or extracting private transcripts.

The checked-in seed/examples demonstrate format and CLI behavior. They do not
assert that actual independent humans reviewed a realistic dataset. Structural
test records that attest human actors are test inputs, not completed annotation
collection. Collect genuine human labels before making reviewed-data accuracy
claims.

## Relationship to the first retrieval experiment

The first dataset and results in [SEMANTIC_TASK_EVALUATION.md](SEMANTIC_TASK_EVALUATION.md)
remain frozen. Those labels were agent-authored and are not independently
human-adjudicated. Reusing their sanitized descriptions preserves that fact and
requires fresh human labeling/review in this workflow; it does not retroactively
change the old experiment's provenance or accuracy evidence.
