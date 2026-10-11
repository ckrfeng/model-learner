# First independent human semantic review batch

Prepared on 2026-10-11. The local batch is ready; human labeling and independent
human review have **not** occurred. No retrieval scores, rankings, frozen policy,
or evaluation report were generated for this batch.

All data is under the ignored local directory
`.model-learner/annotations/semantic-human-review-v1/`. Nothing was uploaded.
The only repository changes for this activity are documentation and status.
The existing `task-annotations/v1` schema and six annotation CLI operations are
used unchanged. The annotation protocol is [TASK_ANNOTATIONS.md](TASK_ANNOTATIONS.md).

## Material and review workload

The batch has 40 realistic but **agent-authored, constructed** technical queries
and 32 historical descriptions. It is benchmark material, not real user history,
real execution evidence, or private transcripts. UUIDs and availability times
are hypothetical declarations/checkpoints. No execution facts were fabricated.

| Split | Queries | Historical candidates per query | Pair judgments |
| --- | ---: | ---: | ---: |
| Development | 10 | 8 | 80 |
| Test | 30 | 24 | 720 |
| Total | 40 | 32 across both splits | 800 |

Development covers catalog schema upgrades and mobile offline synchronization.
Test covers tenant authorization, image orientation, calendar recurrence,
export pagination, diagnostic privacy, and binary sensor decoding. Projects,
families, and lineages are disjoint between splits. Related rewrites and
descriptions of the same underlying objective stay together. Neutral example
IDs do not encode labels. Candidate order is shuffled independently of judgment.
No previous retrieval fixture text or judgments were reused.

The authored material includes repair/test relationships, different-wording
technical equivalents, same-wording documentation objectives, nearby work that
uses similar capabilities, explicit continuations, independently declared
related tasks, missing task declarations, unrelated work, and plausible
no-relevant-history queries. One query retains its historical task identity
while changing its objective. These are construction intentions, **not labels**;
humans decide relevance against the entire split corpus. Intended no-match cases
can turn out to have a relevant candidate after review.

Files:

- `authored_descriptions.json`: inspectable source material, with agent authorship
  and hypothetical declarations; each snapshot references this file by hash and
  JSON locator. Do not edit it after collection begins.
- `seed.json`: unannotated versioned seed.
- `collection-000.json`: prepared dataset `semantic-human-review-v1`, created
  through `annotation prepare`; zero annotations and zero reviews.
- `QUERY_INVENTORY.md` and `query-ids.txt`: all 40 query descriptions/IDs, without
  expected answers or scores.
- `templates/QUERY_ID.json`: existing query-judgment format with all dimensions
  unknown and **empty rationales**. These are incomplete forms, not label proposals.
  Schema validation rejects submission until every rationale is filled.
- `labels-author/`, `labels-reviewer/`, `inspection/`, `revisions/`: local working
  directories. `inspection/q-93b477.json` is an example of score-free CLI output.

## What the two humans review

Use actual identities for a human author and a **different human** reviewer.
An agent reviewing these files is not independent human annotation review.
Each person should inspect the original descriptions and declared context before
seeing the other's judgments. The reviewer can record first-pass judgments in
`labels-reviewer/` using the same JSON forms, then compare with the submitted
author labels. Only the existing CLI records official labels/review decisions.

For every query, inspect **every historical candidate in its split**, including
other projects. Do not review just the nearest-looking candidates. Check source
references, UUIDs, checkpoints, and group assignments for hidden duplicates or
incorrect declarations before collecting labels. If task material itself is
wrong, prepare a corrected seed under a new dataset identity rather than silently
editing collected context or a frozen file.

Keep these three questions separate in each pair's `rationale`:

1. Objective/mechanism: is the historical task useful work on the same objective
   or mechanism? Set `similarity` to `relevant`, `irrelevant`, or `unknown`.
2. Shared capabilities: what technical skills or requirements overlap, and does
   that overlap actually make the historical work relevant? Shared technology,
   language, vocabulary, or generic testing skill alone is insufficient. Record
   this comparison in the existing rationale; there is no separate capability
   label field or capability classifier in this workflow.
3. Identity/continuation: what explicit declaration supports `yes`, `no`, or
   `unknown`? Distinct declared UUIDs cannot be labeled a continuation. Missing
   declaration can remain unknown. A retained task identity can coexist with a
   changed objective and irrelevant historical work.

Also judge `scope_change` and `difficulty_change` separately. Compare the stated
acceptance constraints, and use unknown with a reason when comparison is not
supported. No execution difficulty or success is known. Set `hard_negative=true`
only for an explicitly irrelevant but plausibly confusable candidate. Cite the
query and candidate snapshot IDs in `evidence_refs`; these descriptions are the
available evidence, not observed execution outcomes.

For `no_match`, use `yes` only when **all** candidates are irrelevant, `no` when
at least one is relevant, and `unknown` when uncertainty prevents an exhaustive
conclusion. Replace every empty rationale, including cross-project negatives.
Unknown after genuine inspection is a valid judgment; an untouched form is not.

Do not run `task similar`, retrieval experiments, or evaluation to help label
this batch. Do not expose scores to either human during label adjudication.
Accept only after independently checking all dimensions and citations. Reject
with a concrete disagreement note; a human author must correct the affected
judgments and obtain new independent acceptance. Merely accepting an agent's
labels would not satisfy the human-author requirement.

## Exact commands, in chronological order

Run in one shell from this checkout. `--no-sync` preserves the existing installed
environment; no dependency installation or download is needed. This preparation
command was **already executed**, so start with inspection of `collection-000.json`.
It is shown for provenance, not as a command to rerun over an existing output:

```sh
cd /Users/carterfeng/Documents/Code/model-learner
export PATH="$PWD/.tools/bin:$PATH"
export UV_CACHE_DIR="$PWD/.uv-cache"
BATCH="$PWD/.model-learner/annotations/semantic-human-review-v1"

# Already executed; existing destination is intentionally never overwritten.
# uv run --no-sync model-learner annotation prepare "$BATCH/seed.json" \
#   "$BATCH/collection-000.json" --dataset-id semantic-human-review-v1

CURRENT="$BATCH/collection-000.json"
cat "$BATCH/QUERY_INVENTORY.md"
uv run --no-sync model-learner annotation show "$CURRENT"
Q=q-93b477
uv run --no-sync model-learner annotation show "$BATCH/collection-000.json" --query-id "$Q"
```

Choose the two actual human identities by answering these local shell prompts.
Do not substitute agent names and attest them as humans:

```sh
printf 'Actual human label author ID: '
read -r ANNOTATOR
printf 'Different actual human reviewer ID: '
read -r REVIEWER
```

The author copies a blank form and fills it in after inspecting the descriptions.
The reviewer independently inspects the original collection and may fill a
separate copy before comparing. `open -e` opens a local file in macOS TextEdit;
save it as plain JSON before using the CLI. Any plain-text editor also works.
The `cp -n` commands preserve an existing working form:

```sh
cp -n "$BATCH/templates/$Q.json" "$BATCH/labels-author/$Q.json"
open -e "$BATCH/labels-author/$Q.json"

# Reviewer first pass, before reading author labels:
uv run --no-sync model-learner annotation show "$BATCH/collection-000.json" --query-id "$Q"
cp -n "$BATCH/templates/$Q.json" "$BATCH/labels-reviewer/$Q.json"
open -e "$BATCH/labels-reviewer/$Q.json"
```

When the author has completed the form, submit it through the existing CLI.
Advance `CURRENT` **only on command success**:

```sh
uv run --no-sync model-learner annotation label "$CURRENT" "$Q" \
  "$BATCH/labels-author/$Q.json" --annotator "$ANNOTATOR" --actor-kind human \
  --output "$BATCH/revisions/$Q-labeled-01.json" && \
  CURRENT="$BATCH/revisions/$Q-labeled-01.json"
uv run --no-sync model-learner annotation show "$CURRENT" --query-id "$Q"
```

The reviewer now compares submitted labels with their independent first pass.
Choose **one** of the following decisions, enter a substantive note, and execute
the corresponding command. Do not accept just because the file validates.

```sh
# Acceptance branch, if all submitted judgments are accepted:
printf 'Independent acceptance rationale: '
read -r NOTE
uv run --no-sync model-learner annotation review "$CURRENT" "$Q" \
  --reviewer "$REVIEWER" --actor-kind human --decision accept --note "$NOTE" \
  --output "$BATCH/revisions/$Q-accepted-01.json" && \
  CURRENT="$BATCH/revisions/$Q-accepted-01.json"
```

```sh
# Rejection branch, if any submitted judgment needs correction:
printf 'Disagreement and evidence to recheck: '
read -r NOTE
uv run --no-sync model-learner annotation review "$CURRENT" "$Q" \
  --reviewer "$REVIEWER" --actor-kind human --decision reject --note "$NOTE" \
  --output "$BATCH/revisions/$Q-rejected-01.json" && \
  CURRENT="$BATCH/revisions/$Q-rejected-01.json"

# Human author corrects the complete query form after evidence-based discussion:
open -e "$BATCH/labels-author/$Q.json"
uv run --no-sync model-learner annotation label "$CURRENT" "$Q" \
  "$BATCH/labels-author/$Q.json" --annotator "$ANNOTATOR" --actor-kind human \
  --output "$BATCH/revisions/$Q-labeled-02.json" && \
  CURRENT="$BATCH/revisions/$Q-labeled-02.json"
uv run --no-sync model-learner annotation show "$CURRENT" --query-id "$Q"

# Reviewer rechecks the corrected judgments before entering an acceptance note:
printf 'Independent rationale after correction: '
read -r NOTE
uv run --no-sync model-learner annotation review "$CURRENT" "$Q" \
  --reviewer "$REVIEWER" --actor-kind human --decision accept --note "$NOTE" \
  --output "$BATCH/revisions/$Q-accepted-02.json" && \
  CURRENT="$BATCH/revisions/$Q-accepted-02.json"
```

Relabeling removes current reviews for that query, requiring new acceptance.
The older immutable revision retains the rejection. If correction still fails
review, record another rejection and repeat with fresh `-03`, `-04`, etc. output
names. Correcting an already accepted label follows the same relabel/review steps.

Repeat inspection, author labeling, and independent review for **every ID** in
`query-ids.txt`, changing `Q` each time and carrying the newest `CURRENT` forward.
Every label must include all 8 or 24 split candidates. Do not bulk-submit untouched
forms or bulk-accept reviews. Keep the same latest revision when switching humans;
in a new shell, set `CURRENT` to that actual absolute path instead of starting over.

```sh
cat "$BATCH/query-ids.txt"
# Set Q to the next actual ID from the list, then repeat the steps above.
uv run --no-sync model-learner annotation show "$CURRENT"
```

## Finalize and evaluate later, after complete human acceptance

These commands are supplied for your later use. They were **not executed**.
Freezing fails until every query has a human author, a distinct accepting human
reviewer, and no unresolved rejection. Include genuinely reviewed unknown judgments
in the report; do not describe the batch as fully adjudicated binary relevance
if unknown similarities remain.

The prospective comparison is TF-IDF and the existing pinned local Potion encoder,
each at k=3 and strict score >0.0. This fixed baseline policy is specified before
any batch rankings; it is not a calibrated relevance/rejection threshold. The
development cohort supports checking this choice without selecting on test results.
If choosing another policy, decide and record it using development evidence only,
then freeze all comparison policies before opening any test report. Never pick
the better test policy and describe it as prospectively selected.

From the **same final reviewed `CURRENT`**, create two frozen artifacts before
running either test evaluation. No training occurs. Potion uses only the existing
local bundle; do not provision a new model if it is unavailable.

```sh
uv run --no-sync model-learner annotation freeze "$CURRENT" "$BATCH/frozen-tfidf-v1.json" \
  --backend tfidf --k 3 --minimum-score 0.0 \
  --selection-note "Prospective fixed baseline: TF-IDF, k=3, strict score >0; no batch rankings used to select this policy."

uv run --no-sync model-learner annotation freeze "$CURRENT" "$BATCH/frozen-potion-v1.json" \
  --backend potion --k 3 --minimum-score 0.0 \
  --model-revision bf8b056651a2c21b8d2565580b8569da283cab23 \
  --model-sha256 930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2 \
  --selection-note "Prospective pinned Potion comparison: k=3, strict score >0; no batch rankings used to select this policy."

uv run --no-sync model-learner annotation evaluate "$BATCH/frozen-tfidf-v1.json" \
  --split development --output "$BATCH/development-report-tfidf-v1.json"
uv run --no-sync model-learner annotation evaluate "$BATCH/frozen-potion-v1.json" \
  --split development \
  --model-path "$PWD/.model-learner/models/potion-base-8M-bf8b056651a2c21b8d2565580b8569da283cab23" \
  --output "$BATCH/development-report-potion-v1.json"

uv run --no-sync model-learner annotation evaluate "$BATCH/frozen-tfidf-v1.json" \
  --split test --output "$BATCH/test-report-tfidf-v1.json"
uv run --no-sync model-learner annotation evaluate "$BATCH/frozen-potion-v1.json" \
  --split test \
  --model-path "$PWD/.model-learner/models/potion-base-8M-bf8b056651a2c21b8d2565580b8569da283cab23" \
  --output "$BATCH/test-report-potion-v1.json"
```

Keep counts, unknowns, no-match false acceptance, hard-negative errors, coverage,
abstention, and per-query/per-family errors alongside aggregate precision/recall.
These results will describe a small constructed human-reviewed benchmark, not
population accuracy on actual task history. Continuation, scope, and difficulty
remain reviewed labels with coverage reporting; the existing evaluator has no
predictor for those dimensions. Shared capabilities are rationale context only.
There is no claim about verified task success, model utility, or routing.

Stop at review preparation now. If test scores later motivate changing examples
or labels, preserve this dataset and results, then collect a new version and
fresh holdout under separate user direction.
