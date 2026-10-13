# Selected conversation coverage recovery — 2026-10-12

All **15 exposed user messages** in the original four selections now have
predictions: 3, 4, 4 and 4 messages respectively. The semantic analyzer is unchanged.
This is a new projected-input evaluation, **not** a replacement for the original
full-text baseline. It supports human review; it does not establish semantic
accuracy, verified outcomes or predictive utility.

Only the previous four exact IDs were used. No conversations were added or
unrelated histories enumerated. The user separately approved a bounded reread:
ten one-turn pages and 256 KiB cumulative transport per selected conversation.
The one-off diagnostic client loads the unchanged transport source in an isolated
module with that explicit wire allowance. Production importer defaults remain
64 KiB; extracted message text stayed below its unchanged 64-KiB bound. All
analyzer bounds and rules remain unchanged. Temporary servers exited 0.

Native IDs, titles, source references, per-message shapes, frozen predictions,
policy/source hashes and comparison reports remain in ignored private storage.
No private text, tool body, raw response or excerpt was printed or saved. Numeric
item metrics do not reconstruct independent tool results. No human reference
labels or independent project outcome checks were inspected, including after
prediction freeze. Tests below concern Model Learner itself.

## Diagnosed input and coverage

A–D are the original selection positions; they introduce no new task identities.
UTF-8 text bytes are extracted message bytes, not serialized RPC bytes.

| Selection | Original coverage | New user coverage | User messages / bytes / clauses | Assistant messages / bytes / clauses | Complete-read wire bytes |
| --- | --- | --- | --- | --- | --- |
| Codex A | No predictions; 64-KiB wire rejection | 3/3 | 3 / 1,326 / 30 | 9 / 3,247 / 48 | 93,795 |
| Codex B | No predictions; 64-KiB wire rejection | 4/4 | 4 / 1,272 / 28 | 10 / 4,366 / 62 | 110,337 |
| Codex C | All 4 user messages; 12 total messages | 4/4 | 4 / 1,791 / 44 | 8 / 4,581 / 59 | 35,482 |
| Work Local D | First 3 user messages; 9 total messages | 4/4 | 4 / 1,578 / 37 | 7 / 18,839 / 260 | 52,058 |

All exposed cursors were exhausted. Original history completeness, hidden branches,
source/UI fidelity and truncation remain unknown; native truncation markers were
not emitted. These fractions describe exposed user messages, not a proven complete
original conversation. No projected user checkpoint reached 64 KiB, 128 messages,
16,384 characters per message or 256 clauses.

Measured item counts and UTF-8 bytes after compact JSON reserialization:

| Item type | A count / bytes | B count / bytes | C count / bytes | D count / bytes |
| --- | --- | --- | --- | --- |
| User message | 3 / 1,899 | 4 / 2,003 | 4 / 2,608 | 4 / 2,320 |
| Assistant message | 9 / 4,828 | 10 / 6,140 | 8 / 6,060 | 7 / 20,171 |
| Command execution | 19 / 53,899 | 20 / 64,876 | 9 / 15,446 | 0 / 0 |
| File change | 5 / 27,203 | 3 / 29,698 | 5 / 6,163 | 0 / 0 |
| Reasoning | 11 / 2,063 | 8 / 3,521 | 5 / 535 | 9 / 1,222 |
| Web search | 0 / 0 | 0 / 0 | 0 / 0 | 8 / 24,140 |

These are exposed item counts, not telemetry or verification. Zero means no item
of that type exposed in this read. Reserialized sizes exclude RPC envelopes,
thread metadata, escaping differences and transport notifications, so they are
not an exact wire-byte decomposition. Private diagnostics also record total
UTF-8 string-value bytes per item type, without retaining the strings.

A and B were dominated by command/file-change payloads, excluded from semantic
inference only **after** full-item transport. Their message text totals were just
4,573 and 5,638 bytes. Assistant text exceeds user text in every selection; in D
it accounts for 92.3% of message bytes and 87.5% of clauses. Non-message bodies
were measured structurally and never supplied to the analyzer.

Parsing showed no duplication or expansion: unique source message IDs were
validated; each analyzed message equals the importer's exact newline join of
original parts. Every selected message has zero joining-byte expansion. No
normalization, summaries, deduplication, lexical expansion or clause clipping was
applied. This does not assert that the source authors never repeated content.
The analyzer masks fenced code and locates clauses in the original character
coordinate system; it does not expand text.

D's fourth user message is only **246 bytes and 6 clauses**. Three earlier long
assistant messages contribute **15,808 bytes and 218 clauses** (112, 41 and 65).
The original prefix before the fourth user has 255 clauses; adding that message
produced 261, and the entire full input has 297. Removing assistant messages gives
31 clauses through the third user and 37 through the fourth. Of the full 297
clauses, 57 are at most 32 characters and 36 at most 16; punctuation/newline splitting
contributes short spans, but the main constraint is cumulative assistant prose,
not anomalous expansion of that final user message. No segmentation rule changed.

## Frozen evidence-view policy

`understanding.conversation_projection` is a pure, in-memory selection/reporting
helper; it performs no retrieval, file writes, model training or ledger integration.
The policy, helper/runner hashes and original artifact-manifest digest were frozen
before the reread or semantic prediction evaluation. The production analyzer,
importer and transport source hashes equal the original evaluation's freeze.

**Task intent:** every exposed user message, unchanged, in original chronological
order. Each checkpoint includes the entire user prefix, preserving earlier
requirements, decisions and reversals even if a later prefix fails a bound. Failed
prefixes get null predictions and explicit bounds; no messages are clipped or
silently discarded. Original one-based analysis turn numbers are preserved; user-only turns are not
renumbered. Native IDs,
full-message indices, item ordinals and exact spans accompany predictions. Original
full-input evidence IDs are sidecars; the analyzer's projected IDs and internal
state links remain intact and separately identifiable.

Every checkpoint records included user turns, omitted earlier assistant message
indices and sizes, analyzable/unavailable fields, input sizes and each analyzer
bound. The separate source mapping records all omitted assistant messages,
including responses after the checkpoint. Later source content never enters an
earlier prediction.

**Execution/progress:** each whole assistant message is analyzed independently
with its original role and references. All 34 assistant messages fit individually.
This view retains recognized reported issues, choices, progress and completion
claims, with no cross-message state reconstruction. It cannot recover attempts
without a recognized failure cue, typed test results (the frozen analyzer has no
such field), causal obstacles or independent execution evidence. Non-message item
counts/bytes remain diagnosis only. Independent verification is null with
`not inspected or supplied` missingness, never inferred from assistant claims.

This representation makes user-stated objectives, requirements, changes,
decisions/reversals, status and uncertainty evaluable. Assistant choices, proposals,
reported tests/completion and context required to interpret short approvals are
unavailable **in that task-intent view**. Separate assistant reports do not restore
accepted intent automatically. Neither view computes a resolved active requirement
set or supplies an independent outcome. Recognized zeros are not observed absences.

## Frozen semantic predictions and comparison

The following counts are recognized user facts over each final user prefix,
not manually adjudicated truths. `Add/revise/remove` counts exclude objectives
and decisions that also contribute to the analyzer's positive evidence overlay.

| Selection | Objective established | Add / revise / remove | Decisions / reversals | Failure / progress / completion reports | Other / ambiguous | Final uncertainty entries |
| --- | --- | --- | --- | --- | --- | --- |
| A | No | 10 / 1 / 0 | 1 / 0 | 0 / 0 / 0 | 14 / 4 | 31 |
| B | Yes; 6 objective clauses recognized | 3 / 0 / 0 | 2 / 0 | 1 / 0 / 0 | 12 / 4 | 16 |
| C | No | 3 / 0 / 0 | 2 / 0 | 2 / 1 / 2 | 24 / 10 | 39 |
| D | Yes; 3 objective clauses recognized | 3 / 1 / 2 | 2 / 0 | 0 / 0 / 0 | 23 / 3 | 28 |

No user-prefix task switch or decision reversal was recognized. Verification is
unknown at all 15 user checkpoints and all 34 assistant-message checkpoints.
User status reports are also not independent verification. The two user-attributed
completion claims in C remain predictions needing review, not task outcomes.

Separate assistant view: A recognizes 2 progress reports and 4 completion claims;
B recognizes 3 decisions, 5 progress reports and 5 completion claims; C recognizes
2 decisions, 4 progress reports and 5 completion claims; D recognizes 8 decisions,
4 progress reports, 3 completion claims and 1 unresolved report. These counts
never enter the task-intent view or become verified outcomes.

For C, **44/44** user-clause intent classifications agree with the original frozen
full-input predictions. For the original available D prefix, **31/31** agree.
Original message indices and exact spans align. This establishes reproducibility
on overlapping source clauses, **not** semantic correctness. A/B have no original
predictions to compare; D's fourth user has no original baseline prediction.

Omissions can still change interpretation: C loses one candidate edge from a user
decision to an earlier assistant decision. The projected view explicitly records
an empty candidate set rather than transferring the assistant choice. D has no
changed candidate links on overlapping user clauses, but the new fourth-user
interpretation still lacks preceding assistant explanations. Counts and cumulative
state differ because assistant facts are excluded and D gains its last user turn.
Original and projected artifact sets remain separate and the original manifest
is unchanged. No new full-text predictions are passed off as the original baseline.

## Remaining failures, uncertainty and recommendation

Coverage recovery does not repair the analyzer's known semantic limitations.
Objectives remain unavailable for A/C; many user clauses remain `other` or
`ambiguous`, and their requirements or references cannot be presumed understood.
Two scope-edit targets in D remain unresolved (one removal and one revision). Candidate links are lexical suggestions;
assistant omission demonstrably loses a context edge in C. One-intent clauses,
English cue vocabulary, instruction-versus-report ambiguity, conditional requests,
implicit task switches, pronouns and partially edited lists remain unresolved.
No new accuracy, false-positive or false-negative rates can be established without
human adjudication; these are observable prediction gaps and previously documented
failure risks, not newly scored reference disagreements.

Missing execution evidence, native message times, historical model/settings,
usage/cost, artifact fingerprints, declared Task/Run/Attempt associations and
independent checks remain unknown. Assistant test claims are not parsed into
structured check results or authenticated. The isolated per-message execution
view cannot show causal sequences or cross-message resolution. Source fidelity is
not independently checked.

**Recommendation:** this representation is useful enough to continue to
human-adjudicated semantic evaluation of the same selected sources. Review both
views side by side, original source references, unknown-objective cases,
requirement overlays, missing/ambiguous targets, reported-status classifications
and context-dependent approvals. Freeze an adjudication policy first. No success
or utility estimator should consume these hypotheses as trusted features yet.
Outcome collection/integration, neural training and AI Governor remain unstarted.
Stop after this evaluation and recommendations; do not add test conversations.

## Validation

Five new projection regressions reuse the existing demo fixture and bounded-size
perturbations; no semantic evaluation conversation or reference label was added.
They verify every user prefix and exact source spans, omitted assistant state,
independent verification missingness, simulated source kind, and explicit text/
clause/message-size failures without dropping later user checkpoints.

Actual full checks and independent review results are recorded in STATUS.md.
Private policy/prediction freezes and original manifest integrity checks precede
comparison. Re-running the private collector would reread private sources and
requires authorization; report review does not require rerunning it.
