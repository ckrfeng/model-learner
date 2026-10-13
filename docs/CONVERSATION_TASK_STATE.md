# Local conversation task-state demonstration

The subsequent [prediction-blind holdout evaluation](CONVERSATION_TASK_STATE_HOLDOUT.md)
freezes these results, documents substantial generalization failures and the
bounded researching/ambiguous-target corrections. The selected demonstrations
below remain historical observations; neither source was reread for that evaluation.

Delivered 2026-10-11. This increment analyzes explicitly opted-in text with CPU
rules and evaluates a small statistical alternative. It adds no ingestion
infrastructure, persistence, routing, Governor, cloud inference or model download.
The existing importer is reused unchanged for the two exact selected sources.

`understanding.conversation_state.analyze(Conversation(...))` is the pure in-memory
entry point. Its output is an evolving timeline after each source-ordered message,
with objective, requirement evidence, removals/revisions, actor-attributed decisions
and reversals, reported issues, reported progress, completion claims, uncertainty
and independent check coverage. Every interpretation points to the exact original
message character span. User statements and assistant statements remain distinct;
every speech-act interpretation and change-target candidate is an inference.

## Run the demonstration

From the repository with the existing development environment:

```sh
export PATH="$PWD/.tools/bin:$PATH"
uv run model-learner task conversation-state --text-opt-in --emit-text \
  < tests/fixtures/conversation_state/demo.json
uv run model-learner learn conversation-state-eval \
  tests/fixtures/conversation_state/evaluation.json
```

The demo is **authored simulated data**, not either real conversation. It exercises
an initial CSV objective, quoted-comma addition, failed attempt, mechanism revision,
feature removal, implementation decision, reversal, reported progress and claimed
completion. Its separately supplied synthetic full-acceptance check produces a
`verified` final checkpoint only for its named simulated artifact/acceptance target.
It is not a real verified task or a ledger learning observation.

By default `conversation-state` reads bounded JSON from stdin, processes it only
with `--text-opt-in`, and emits JSON to stdout without evidence text or independent
check identifiers. `--emit-text` explicitly authorizes that display. There is no
output-file option, database call or semantic-state retention. The caller controls
whether stdout is subsequently captured. Do not redirect real output to a retained
file without separate retention authorization. Even redacted output contains
semantic categories that deserve the same care as other derived personal data.

For an already selected source:

```sh
uv run model-learner task conversation-state --text-opt-in \
  --conversation-id SELECTED_UUID --product-source codex_desktop \
  --machine-id YOUR_LOCAL_MACHINE_ID --codex-executable /path/to/codex
```

Use `chatgpt_work_local` for the validated Codex-backed Work source. The UUID and
source are supplied by the user; this command never discovers conversations.
Existing full-view retrieval can receive non-message items before local exclusion.
Only extracted user/assistant text reaches analysis. Source truncation/completeness
is not established by exhausted pagination; the live bridge keeps history
completeness unknown. Existing exact-ID, read-method, byte, timeout and pagination
bounds remain intact. Native identifiers never enter semantic evidence IDs.

API JSON has `messages` (role `user`/`assistant`, text, one-based source turn),
optional `checks`, `history_complete` and `source_kind`. Source defaults to unknown;
live reads are real and authored evaluation/demo inputs are simulated. Check sources
must be `independent_verifier` or `independent_human`, supplied outside message text.
They identify the checkpoint, inferred scope revision, named artifact, acceptance
specification, result and full/partial scope. These declarations are caller
attestations, not authentication or proof that a verifier actually ran.
Invalid private input receives content-free CLI diagnostics. Text is bounded to
64 KiB, 128 messages and 256 non-code clauses. No network is needed for analysis
or evaluation, and no optional CPU model runtime is required.

## What the baseline means

The weak baseline scans keywords without contextual negation. The selected
baseline splits English sentences outside fenced code, identifies explicit
speech-act cues, and gives questions, conditional language, indirect quotations
and uncertainty priority. It distinguishes an assistant's proposed scope from a
user's instruction. Explicit task-change cues open a new inferred task segment;
this creates no canonical Task, session association or execution record.

`requirement_evidence` is **not an active requirement set**. It contains original
positive statements and revisions, with `removal_evidence` as negative scope
overlays. For example, “Compare FIFO and round robin” followed by “Exclude FIFO”
retains the original source, identifies a removal and links its lexical candidate
target. It does not erase the whole comparison or claim a fully resolved logical
scope. Revised requirements and reversed decisions retain original evidence as
well. Their overlaps are target suggestions, never embedding-derived certainty.
The operator must review partial list edits and ambiguous references.

`decision_evidence` preserves actor attribution: assistant decisions can be
proposals whose user acceptance is unknown. `progress` and `unresolved` are
historical reports, not proven current artifacts or independently established
remaining failures. A failure report remains visible after a later “fixed” report;
that later statement alone cannot establish resolution. No progress percentage,
causal explanation, monetary cost or outcome label is inferred.

A completion claim never supplies verification. Only an explicitly supplied
full-task independent check, matching the current inferred revision and exact
checkpoint, can give `verified`. Partial checks are visible and cannot establish
full completion. Failed checks produce `failed_check`, not a failed task outcome;
conflicting or indeterminate results remain unknown. Verification does not carry
forward to any later message: this conservative demo cannot prove that an artifact
or unparsed scope stayed unchanged. Earlier verified checkpoints remain historical.
This is intentionally separate from the existing run/artifact verification ledger.

## Actual selected demonstrations

The two previously approved exact selections were read by the existing bounded
standalone importer. Live strings and derived state stayed in Python memory.
Only sanitized signal/count summaries were displayed, and only aggregate findings
are recorded here and in STATUS. No native identifier, excerpt, raw response,
transcript-derived fixture or retained semantic snapshot was created.
Both again exposed three turns and six ordered user/assistant messages, with
1,530 bytes of extracted CSV text and 741 bytes of Work text. Temporary servers
exited 0. The original UI fidelity and hidden-history completeness remain unknown.

| Turn | Codex CSV parser: recognized evolution | Work Local scheduling: recognized evolution |
| --- | --- | --- |
| 1 | Parser objective and ordinary comma-field requirement | A constraint is extracted; initial objective wording is **not recognized** |
| 2 | Quoted-comma support added | FIFO exclusion detected; initial change target remains unresolved |
| 3 | Multiline quoted-field support added; one user issue report | Remaining round-robin/shortest-job comparison scope recognized; user and assistant incompletion reports |

The independent earlier feasibility description establishes the intended scheduling
objective: compare three algorithms, then exclude FIFO and finish the two-algorithm
comparison. That contextual expectation is kept separate from what this CPU
analyzer actually recovers. Its unknown objective and unresolved removal target
are real demonstration failures, not replaced with a hand-written successful
machine result. CSV retains two, four and six uncertainty entries after the three
assistant messages; Work retains three, five and seven. Neither yields a recognized
explicit progress report, decision or completion claim under the selected cues;
this means none recognized, not evidence that no actual progress occurred.
Both have zero independent check inputs and `unknown` verification throughout.
Final CPU analysis took about 0.47 ms for CSV and 1.49 ms for Work in one warm local
run, excluding retrieval; these are observations, not stable performance promises.

## Manually specified evaluation and statistical comparison

`tests/fixtures/conversation_state/evaluation.json` has 52 training examples and
23 separate evaluation conversations with 54 labeled clauses. The author manually
specified expected intents and final state signatures before first execution.
These are **agent-authored manual labels**, not genuine human annotation or real
population ground truth. Topics vary across software, data, research, travel,
security, education, hardware, algorithms, verification and ambiguous replies.
The set covers all requested additions/removals/revisions/reversals/task switches,
failed attempts, unresolved tasks, explicit scoped verification and ambiguity.

The statistical alternative is dependency-free multinomial Naive Bayes over
role, token unigrams and bigrams with Laplace smoothing. A fixed 0.7 top-log-score
margin abstains as ambiguous. Training uses only the explicitly separated training
array; no test conversation or label is fitted. The training and evaluation topics
differ, but cue language shares authorship. No embeddings alone are used to infer
requirement changes, and the existing Potion relatedness encoder is unnecessary
for this speech-act comparison.

The evaluation produced:

| Variant | Intent accuracy | Macro F1 on present gold labels | Matching final-state signatures |
| --- | --- | --- | --- |
| Keyword baseline | 40/54 = 74.1% | 0.502 | 14/23 |
| Contextual rules, selected | 51/54 = 94.4% | 0.925 | 20/23 |
| Naive Bayes | 36/54 = 66.7% | 0.599 | 9/23 |

These scores describe the final implementation on a **diagnostic set**, not an
untouched held-out test. The first rule run scored 48/54; it exposed a mistaken
quotation cue on “quoted fields” and missing objective verbs. The demonstrations
also exposed ongoing-objective wording and assigning a constraint as objective.
Those defects were corrected after inspection. An independent reviewer also found a reversal example that repeated the same
choice; it was corrected to an actual SQLite-to-PostgreSQL reversal, and the demo
now reverses streaming to buffered. Reference results were regenerated. Intent
labels, final-state labels and NB training/features/margin were unchanged. Final rules still miss an implicit
accessibility requirement, an implicit switch from explanation to translation,
and an ambiguous short approval. NB additionally makes false scope changes,
misreads indirect success and mistakes planned work for progress. It does not
improve this experiment, so the rules remain the default.

The report includes confusion counts, per-case intent errors, error categories,
per-field counts, mismatched final-state fields, dataset digest and actual elapsed
CPU time. The reproducible reference omits volatile elapsed values. Final-state
signatures compare source message positions for objective/requirement/removal/
decision/issue/progress/completion evidence, task count, verification and a minimum
uncertainty count. They **do not measure fully normalized logical requirements,
link-target accuracy, every intermediate state or real task success**. Unit tests
separately check obvious lexical target candidates and prefix visibility.

There is no estimate of broad generalization or downstream utility improvement.
The two real examples are demonstration cases only. Independent software review
is not human annotation. Remaining limits include English-only cues, one primary
intent per clause, decimal/abbreviation splitting, code contents excluded from
interpretation, implicit task changes, paraphrases, ambiguous references and
long-range scope resolution. Every unsupported user statement carries uncertainty.
No later milestone is started after this demonstration and evaluation.
