# Independent prediction-blind methodology review

Authorship: independent AI; not human verified. Review completed at 2026-10-13T05:13:12.971325+00:00.

## Blindness and ownership attestation

I read only `AGENTS.md`, `docs/LOCAL_TASK_STATE_EXPERIMENT.md`, and the two fresh
files I authored. I did not inspect private diagnostic transcripts, the production
analyzer implementation, prior fixtures, candidate prompts/rules, candidate
predictions, scoring ledgers, or model outputs. I did not run candidates. The four
new topics, sources, and labels were authored before seeing any predictions.
My assigned scope comprises only this review, `holdout_sources.json`, and
`holdout_reference.json`; I made no other repository changes.

The sources contain four simulated conversations and 16 user-only checkpoints.
The references are independent AI judgments, not human ground truth. Independence
here is prediction blindness and fresh authoring, not human adjudication or
statistical independence of correlated prefixes. These artifacts may be scored
once under the frozen protocol; subsequent reuse is consumed evaluation.

## Findings on the stated policy

The policy has appropriate boundaries: original user-only prefixes, no candidate
or annotation input to C, immutable candidate settings, separated diagnostics and
holdout, explicit provenance, no inferred independent verification, and separate
syntax/span/semantic assessments. This review evaluates that written policy;
it cannot certify implementation compliance without inspecting the harness.

The following operational details must be fixed before scoring:

1. Freeze the exact event-family membership and one-to-one matching rules. State
   whether requirement metrics include `requested_action`, `constraint`,
   `conditional`, or just requirement subtypes. A repeated objective and its
   corresponding requested-action event must not create two requirement atoms.
   Related requests for advice and revision can be separate only when their
   distinct requested behaviors are preserved. Save every semantic match and
   non-match, not only successful examples.
2. For target metrics, separate recognized-event conditional correctness from
   recovery across all nine reference non-null links. Score a null target as
   correct abstention only where the reference target is null. Report non-null
   hallucinated targets separately. Missing recognition must reduce link recovery;
   otherwise a candidate could improve conditional target accuracy by omission.
3. Report null-objective correctness separately and include it in checkpoint
   agreement. The first seed-exchange checkpoint intentionally supplies no
   recoverable activity. A generic task guessed from object names is not a valid
   substitute. Missing/unavailable prediction is distinct from a valid null.
4. Define report negative-case denominators by checkpoint or by reference atom
   before evaluation, and state which. Code values `failed` and `completed`,
   permission to act if a printer jams, and a still-unrecorded audio stop are not
   observed failures or whole-task completion. A partial completion claim can be
   true to the source even when other work or outcome verification remains open.
5. Citation validity is mechanical substring/identity integrity; it does not show
   semantic support. Require current-message evidence for message-local events,
   original message identity, and an earlier same-conversation target. For a code
   value to be an instruction atom, the surrounding source must explicitly
   authorize using that example as specification. Preserve evidence context when
   adjudicating, even if the exact citation is a short field line.
6. Freeze A/B adapters, C prompt/schema/decoding, label files, evaluator, matching
   ledger policy, context/token bounds, and timestamped hashes before prediction
   generation. Fairness requires the same checkpoint prefixes and output policy.
   An adapter must preserve unsupported-event absence and unavailable results;
   it must not infer a new event or target from a label.
7. Use serial runtime trials with identical limits, actual configured threads,
   explicit input/output token counts, and no reused-prefix cache advantage.
   Measure cold process/model load separately from warm per-request wall time.
   Document p95 calculation for this tiny sample, including timeout handling.
   A timeout remains unavailable and must not disappear from latency reporting.
8. Measure peak runtime-process RSS independently from driver memory. A server
   process lifetime maximum differs from per-request peak; identify the process,
   scope, sampling or high-water mechanism, units, and any child-process treatment.
   Weight file size and estimated memory are not measured RSS. CPU-only operation
   should be evidenced by the recorded runtime settings/logs.

The improvement screen is a predeclared pragmatic filter. Even passing all its
conditions cannot demonstrate population accuracy, human-verified semantic truth,
calibrated uncertainty, production safety, or utility. With four conversations,
checkpoints are dependent, and a single family has few examples. Retain all
negative and ambiguous cases, report counts and null denominators, and give
conversation-level context alongside checkpoint metrics.

## Reference conventions fixed before predictions

Current objective is the latest focal requested activity. It may cite an earlier
message while the focal task persists; explicit requests to plan recording, send
a handout, revise a clue, or review results change that focus. Unknown initial
intent gives a literal null objective. This is focal activity, not active-scope
reconstruction or an assertion that earlier requirements have been executed.

Desired content additions are `requirement_added`; restrictions and limits are
`constraint`; explicit user selections are `decision`. A replacement is one
`requirement_revised` atom rather than an invented remove/add pair. Explicit
withdrawal of a selection is `decision_reversed`. A reinstated requirement links
to its original positive instruction, while the removal remains an independently
observable prior event. No target claims accepted state mutation.

The seed YAML is explicitly introduced as a field-name/sample-value specification,
so it supplies four requirement atoms. Its status values supply no failure or
completion claim. Conditional permission to email is `conditional` in hypothetical
mode, and does not authorize inferring that printing failed. Explicit later print
failure and packet-label completion are reports. Two reported audio recording
statuses are progress observations; the unrecorded stop is not a failure.

The puzzle asks whether gentler wording would help and requests a revision; these
are advice/action requests, not a user decision that gentler wording has been
selected. Trial solves and the unsolved third clue are attributed reports. The
textile printing completion is separate from the reported failed size-preservation
attempt, and neither yields independent verification. An unidentified pending
textile revision has unknown mode, unspecified content, and null target; a candidate
must not guess that it changes the cotton instruction or fabricate its new wording.

All citations have occurrence 0 and exact original text. Multiple events may use
one region when they represent separate meanings (for example unresolved revision
and uncertainty). Evidence validation confirmed every quote occurs exactly once,
events cite the current message, objective evidence is not from the future, and
all nine non-null target citations point to earlier messages in the same
conversation. There are 56 events covering all 14 allowed event kinds and one null
objective. No independent-verification field or affirmative verification label is
provided by this reference schema.

## Fixture freeze

Authoring and citation validation finished at 2026-10-13T05:13:12.971325+00:00, before inspecting predictions.

- `holdout_sources.json` SHA-256: `45c03da6e66ac39461fcea7cefbb8c91cf28ff30b51915b19ca6c6b531fa7942`
- `holdout_reference.json` SHA-256: `b2b57cc505672a51a9158e1fe430183969f60c2d919a06d90d305651cc1049ca`

Validation was a source/reference-only Python check of structure, unique exact
quotes, message-local citations, chronological targets, modes, coverage, and counts.
No candidate was run and no score was observed. The parent task should preserve
these hashes in its experiment freeze manifest and independently audit its saved
semantic matching ledger after prediction generation. Altering any source or label
requires a new hash and an explicit disclosure; prediction-informed label edits
would end the stated blindness guarantee.
