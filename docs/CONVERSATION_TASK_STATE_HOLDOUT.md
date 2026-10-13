# Conversation task-state holdout evaluation — 2026-10-12

**Recommendation: retain this as a reviewable evidence extractor. Its semantic
state is not reliable enough to become trusted input to success/utility estimation.**
Independent prediction-blind synthetic scenarios expose substantial objective,
change, decision and paraphrase failures. Two bounded corrections fix demonstrated
defects, but the untouched evaluation shows no broad recognition improvement.
No predictive comparison, real conversation evaluation, routing or Governor was run.

## Freeze, independence and leakage

Before implementation changes, `frozen_v1/` archived the complete rule/state module,
evaluator, original dataset and original reference. `manifest.json` records their
SHA-256 hashes, Git revision, runtime, limits and classifier configuration. The
existing results reproduced exactly: keyword **40/54**, contextual rules **51/54**,
Naive Bayes **36/54**; final-state agreements **14/23**, **20/23**, **9/23**.
NB uses the same 52 training examples, role/unigram/bigram features, Laplace 1 and
0.7 log-score-margin abstention. Rules remain the default. No model was downloaded.
The archived evaluator imports production names: the regression replay test
explicitly binds them to the archived backend before reproducing the old reference.
Executing that archive alone is not a frozen replay.

The original examples shared authorship and cue vocabulary with development;
rules and one reversal fixture were corrected after inspection. Final signatures
omitted intermediate states, target links and resolved logical scope. Its high
score is diagnostic agreement, not generalization evidence.

A separate agent with no inherited conversation authored **12 cases, 63 messages,
85 semantic events** without inspecting implementation, prior fixtures or model
predictions. Labels and exact spans were frozen before first baseline execution.
Topics include fictional catalogs, flyers, debugging, widgets, writing, sequential
and concurrent tasks, ambiguity and verification. Source kind is always simulated.
An independent reviewer audited the freeze and scorer. These are independent
**agent** judgments, not human annotation or representative population sampling.

After inspecting those results, only the two corrections below were made and
`revision_v1_manifest.json` froze the revised source hash. The blind author then
created **8 untouched cases, 38 messages, 46 events** on fresh topics. A later
**1-case / 6-message / 8-event** untouched coverage supplement explicitly removes
and reinstates the same requirement. It changes neither earlier set. Both frozen
and revised rules were evaluated on every set; no subsequent rule tuning occurred.
The first set is now diagnostic for future development. The second and supplement
were untouched for this comparison, but are consumed tests for future changes.

## Measurements

One-to-one matching requires the same message, overlapping exact character spans
and label; it tolerates clause-boundary differences. Reference multi-act sentences
remain multi-act, exposing the analyzer's one-intent limitation. Objectives and
verification are scored after every message, separately from fact classification.
Requirement counts include explicitly labeled initial constraints. Missing
metric denominators produce null. No confidence intervals are claimed: cases are
curated, and checkpoints within each conversation are dependent.

| Measurement | Frozen baseline: first 12 | Frozen baseline: untouched 8 | Revised: untouched 8 |
| --- | --- | --- | --- |
| Explicit opening objective extraction | 5/11 (45.5%) | 3/7 (42.9%) | 3/7 (42.9%) |
| Current objective evidence checkpoints | 27/63 | 14/38 | 14/38 |
| Typed requirement precision / recall | 13/18 / 13/23 | 5/6 / 5/10 | 5/6 / 5/10 |
| Requirement-change detection, subtype tolerant | 15/18 / 15/23 | 5/6 / 5/10 | 5/6 / 5/10 |
| Typed decision precision / recall | 2/6 / 2/8 | 0/2 / 0/3 | 0/2 / 0/3 |
| Distinct decision-region detection | 2/6 / 2/6 | 0/2 / 0/3 | 0/2 / 0/3 |
| Decision reversal recall | 1/2 | 0/1 | 0/1 |
| Typed changes: false positives / misses | 9 / 18 | 3 / 10 | 3 / 10 |
| Task-switch recognition | 0/2 | 0/2 | 0/2 |
| Exact source span and actor integrity | 81/81 | 47/47 | 47/47 |
| Exact boundaries among label-aligned facts | 33/34 | 16/17 | 16/17 |
| Semantic target-link precision / recall | 3/8 / 3/7 | null / 0/4 | null / 0/4 |
| Completion-claim recall / false claims | 7/10 / 0 | 4/5 / 0 | 4/5 / 0 |
| Verification checkpoint agreement | 62/63 | 38/38 | 38/38 |
| False verified claims | 0 | 0 | 0 |
| Required uncertainty coverage | 1/2 | 2/2 | 2/2 |
| Strict ambiguous-act precision / recall | 0/6 / 0/1 | 0/2 / 0/1 | 0/2 / 0/1 |

The first set's revised results retain all recognition metrics; required uncertainty
improves from **1/2 to 2/2**. This is a diagnostic correction, not untouched evidence
of improved uncertainty calibration. Every metric on the untouched eight is
identical across versions. In the separate reinstatement case, both versions miss
the initial objective (0/1), recognize 1/3 requirement subtypes (2/3 changes allowing
subtype differences), miss the reinstatement, and have 6/6 verification agreement
with no false completion or verification claim. No improvement is demonstrated.

Source-span integrity measures traceability, **not semantic attribution accuracy**.
The target-edge metric counts every emitted candidate edge, including incorrect
ordinary-decision links, and requires matched reference source and target events.
Candidates are not asserted active requirements; their poor precision limits their
use for automatic attribution. The intact spans make manual correction possible.

## Scoring artifacts and actual failures

Frozen references were preserved, including disputed labels. Reviewed supplemental
metrics are reported alongside strict scores, rather than relabeling after seeing
predictions. The initial baseline report is retained; `*_baseline_audited.json`
adds the reviewed metrics and corrects a scorer omission of an ordinary-decision
edge. Target precision was initially 3/7 and is correctly **3/8**. All revised and
untouched reports use the audited scorer. This correction changes measurement,
not the frozen model's behavior.

- **Verification policy artifact:** holdout-06 correctly becomes verified at its
  full-check checkpoint. Its reference also expects verified after a later thanks.
  The documented analyzer deliberately resets verification on every later message.
  Thus 62/63 includes one policy mismatch, not a failed verifier or false claim;
  the other 62 checkpoints agree. No verification semantics were changed.
- **Objective evidence policy:** holdout-10 expects the latest equivalent paraphrase
  to replace the initial objective source. The analyzer preserves its initial
  source. This would be a provenance policy discrepancy if either were extracted;
  both are actually missed here. Untouched labels allow retention of the initial
  source for equivalent wording.
- **Subtype/representation artifacts:** “Put those details in the opening line
  instead” and “Compare the entire header row rather than matching a single word”
  are reference additions but model revisions. Recognizing a scope edit is partly
  correct; subtype-tolerant scoring recovers these two. Same-span decision reversal
  plus replacement labels create two secondary-act misses; distinct-region scoring
  avoids treating them as two wholly missed choices. Full logical replacement is
  still beyond the evidence-overlay representation.
- **Concurrent tasks:** holdout-05's task switch labels the new focal task, while the
  earlier agenda remains active. A single objective/task slot cannot represent both.
  The scorer does not claim that matching one focal slot would solve concurrency.
- **Abstention labels:** an assistant clarification question is reference `other`
  but model `ambiguous`; this is a speech-act policy difference. Conversely, an
  unparsed user statement can carry useful uncertainty even when its label is not
  `ambiguous`. Required-uncertainty coverage measures that separately. These tiny
  denominators do not establish calibrated uncertainty or a safe abstention policy.

Concrete semantic failures that survive these distinctions:

| Example | Actual inference | Root cause / implication |
| --- | --- | --- |
| “Help me organize a small synthetic book catalog.” | Other; no objective | Missing ordinary objective paraphrases. |
| “I am putting together … and could use a draft …” | Decision; no objective | Uncontextualized `use` cue takes priority over the speech act. |
| “Now make a packing checklist …” after another task | Added requirement | `now` dominates objective meaning; task switches require fixed cues. |
| “That attempt … did not fix the importer.” | Other | Failure vocabulary misses paraphrased unsuccessful attempts. |
| “It would help if the opening mentioned …” | Ambiguous | Blanket conditional handling abstains on a clear indirect request. |
| “Give each phase an example.” | Ambiguous | `example` is mistaken for a quotation/indirect-evidence cue. |
| “Remove that filter.” with two prior filters | Multiple candidate links, initially no ambiguity flag | Lexical overlap cannot choose a referent; the bounded fix adds uncertainty. |
| “Switch from phase order to player-turn order.” | Other | Decision-reversal vocabulary misses natural replacements. |
| Untouched “The no-trailing-newline case remains untested.” | Other | Unresolved-state paraphrases are missed; progress does not prove resolution. |
| Untouched reinstate an ingredient-swapping note “included after all” | Other | Requirement reinstatement and active logical scope are not recovered. |

Completion reporting has misses such as “The reference sheet is ready.” Zero false
completion claims in these fixtures is useful but small-sample evidence. Successful,
partial and failed checks are synthetic declarations, not actual verified artifacts.
The untouched failed-check scenario correctly reports `failed_check` despite an
assistant completion claim; neither becomes a canonical failed-task outcome.

## Scheduling objective investigation and bounded corrections

Only the user's supplied sentence was used; the original private conversation was
not reread, enumerated or retained. The frozen analyzer receives the entire 92-character
sentence as one clause: “I'm researching three task-scheduling algorithms: FIFO,
shortest-job-first, and round-robin.” It classifies it `other`. Its objective regex
includes `research` with a word boundary, but omits `researching`, although it already
recognizes progressive forms of several other verbs. This explains failure with
known intact input; state update then correctly leaves the objective unknown.

The importer preserves text parts and the bridge joins them without lexical
normalization. A synthetic bridge regression preserves the supplied sentence
exactly and establishes its objective after correction. Missing original input or
original-source preprocessing cannot be definitively ruled out without a fresh
approved original read; prior aggregate demonstrations did not retain those bytes.
No evidence threshold participates in this rule path, and the supplied objective
is explicit rather than a reference-label ambiguity.

Corrections are limited to progressive forms of the **existing** objective verb
vocabulary and explicit uncertainty for more than one candidate removal/revision/
reversal target. Tests retain question, conditional and actor safeguards. Candidates
and original evidence remain intact; no target is selected, requirement deleted,
active-scope solver added, threshold tuned, neural network introduced, importer
changed, or estimator connected. The untouched failure patterns remain documented.

## Next integration assessment

Potential research features include actor-separated counts of reported obstacles,
reported attempts/progress and scope edits, objective availability, ambiguity and
coverage/missingness. Treat them as **inferred reports**, never artifact truth.
Source spans and ordering are useful for human audit. Completion and independent
verification remain separate; final verification and outcomes must not enter a
pre-outcome predictor. Active requirements, resolved change targets, concurrent
objective identity, semantic difficulty and inferred completion are currently too
unreliable for automatic grouping, attribution or success labels.

Missing information should remain null with explicit coverage/reason masks:
unsupported language, unparsed text, history completeness unknown, unavailable
objective, or ambiguous target. A zero count is valid only as a count of recognized
facts in a stated prefix; it does not mean zero real changes or failures. Unknown
success, cost and verification must not become zero-valued failure/cost features.
No confidence probability should be invented from rule matches.

A future pilot must explicitly associate a conversation prefix with declared
Task/Run/Attempt and acceptance version. Bound each feature to a checkpoint and
availability receipt; never attribute later scope edits or reports to earlier
attempts. Preserve proposed user changes separately from accepted scope, and
maintain acceptance versions when the target changes. Multiple tasks or mixed
configurations require explicit segment attribution or exclusion. Current inferred
task segments and source turn ordering do not create those ledger associations;
native message timestamps are unavailable in the conversation bridge.

Existing outcome data can exercise the plumbing and leakage checks, and the
existing `learn.task_state` comparison can eventually compare metadata features
with a small predeclared reported-semantic-feature ablation. It already enforces
chronological availability, independent verified labels, disjoint task clusters,
fixed checkpoints, and insufficient-data results. Its default floors are 30
training labels, 20 scored labels, five task clusters per split and both training
classes; these are pragmatic floors, not a guarantee of adequate power.

The recorded prior outcome audit in STATUS found one genuinely verified fixed-reply
smoke observation, a separate JUnit producer validation, and **zero suitable real
longitudinal coding trajectories**. The selected conversation demonstrations have
no independent outcome checks or canonical execution associations. No new private
ledger or conversation enumeration was performed here. There are no demonstrated
eligible paired conversation-prefix/outcome data on which to claim predictive
benefit; simulated favorable state-signal results cannot supply that evidence.

**Next recommended step, not implemented:** human-adjudicate a small prospective,
explicitly selected prefix dataset under the existing privacy/annotation workflow,
resolve labeling policy, and collect independent artifact outcomes plus checkpoint
and attempt receipts. First validate a conservative reported-signal subset on a
new frozen semantic holdout. Only with adequate paired outcomes should the existing
predictive evaluator compare metadata versus that subset, with identical cutoffs
and Brier/calibration reporting. Broader cue accumulation or a larger neural model
is not justified by this evaluation. Stop here pending user instruction.

## Reproduction and checks

All report files are simulated and may be retained. From the repository:

```sh
UV_CACHE_DIR="$PWD/.uv-cache" .tools/bin/uv run --no-sync python -m \
  model_learner.understanding.conversation_holdout \
  tests/fixtures/conversation_state/holdout_v1.json \
  --frozen tests/fixtures/conversation_state/frozen_v1
UV_CACHE_DIR="$PWD/.uv-cache" .tools/bin/uv run --no-sync python -m \
  model_learner.understanding.conversation_holdout \
  tests/fixtures/conversation_state/post_holdout_v1.json
UV_CACHE_DIR="$PWD/.uv-cache" .tools/bin/uv run --no-sync pytest \
  tests/unit/test_conversation_holdout.py
```

Omit `--frozen` for revised rules; substitute `scope_reversal_holdout_v1.json` for
its untouched supplement. Regression tests reproduce the hash-checked baseline
archive, audited baseline and revised reports, preserving label digests. The first
raw baseline report is superseded only for its scorer defect. Actual full checks
and independent final review are recorded in STATUS.md.
