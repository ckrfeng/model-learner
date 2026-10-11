# Longitudinal task state — first evidence-bounded increment

This increment reconstructs a declared task/run/session at multiple checkpoints.
It reuses `execution.extract_execution_checkpoints`, metadata-only Codex events,
bound JUnit evidence and the existing optional pinned Potion CPU encoder. It adds
no database migration, collector, model training, agent execution or intervention.

## What the evidence audit found

| Signal | Classification | What it supports |
| --- | --- | --- |
| Declared objective and acceptance specification | Observed declaration | Operator intent and target; not evidence of agent understanding |
| Codex event/item type, status, exit code, named MCP tool/server, emitted usage | Observed | Activity records; not operation semantics or verified progress |
| Tool histories, counts, coverage, failure fractions, repeated-category failures, checkpoint deltas | Derived | Changes in retained execution evidence |
| Latest activity/turn marker heuristic | Inferred | Apparent lifecycle state, with supporting event IDs |
| Bound JUnit cases, reports and fingerprints | Observed | Named-test results for the declared final artifact |
| JUnit completeness and criterion interpretation | Derived/rule-inferred | Acceptance evidence limited to that test target and snapshot |
| Explicit assessment | Observed assessment declaration | A claim; independent verification and cutoff resolution remain necessary |
| Explicit checkpoint summary | Observed report; structured phase/progress/scope/difficulty are inferred hypotheses | What an identified author reported by that checkpoint |
| Potion embedding and cosine | Model-inferred representation | Text relationship diagnostic, without an established state-change classifier |
| Actual task progress, semantic phase change, complexity, retry cause or scope change from metadata alone | Unknown | Commands, arguments, error causes and semantic statements are absent |
| Native execution times, monetary cost, un-emitted model configuration | Unknown | Receipt timestamps are not native timestamps |

The only checked-in genuine agent execution derivative,
`tests/fixtures/codex/real_smoke_capture.jsonl`, contains four metadata-only smoke
records: thread start, turn start, a redacted message item and turn completion.
Its timestamps/identities are sanitized replacements and its stdout was buffered.
There are no tool actions, edits, tests, evolving descriptions or verified coding
outcomes. Other rich execution, predictive and retrieval fixtures are constructed
examples. The pending human annotation batch contains no completed independent
human reviews. These sources do not support real semantic-trajectory accuracy or
real predictive improvement claims.

A read-only aggregate audit of ignored local ledgers also found one genuine
verified fixed-reply smoke observation (and its earlier unknown derivation), plus
a separate operator-run JUnit producer validation without agent events or learning
observations. These are real evidence, not a coding-agent longitudinal cohort.
The smoke's task/association availability follows captured execution records;
it cannot be backdated into prospective scoped checkpoints. There are zero
suitable real longitudinal trajectories for this evaluation, rather than zero
verified observations anywhere in the repository's local history.

## Projection and comparisons

`execution.longitudinal.extract_longitudinal_task_states` produces typed,
JSON-compatible states. Identity remains a separate task/run/session record.
An objective is included only through an explicitly authorized existing
`TaskDescription` with bounded text, digest, source and availability receipt;
the function never extracts an objective from transcripts or arbitrary metadata.
Task IDs remain available as identity references even before associated evidence
is available; objective and scoped observations stay unavailable.

Each state contains:

- `observed`: allowlisted event IDs, source/version, capture sequence and receipt
  availability. The retained execution projection preserves tool statuses,
  exit codes, evidence IDs and valid bound test records.
- `derived`: deterministic event/tool/turn counts, token totals and coverage,
  and repeated failure group counts. Changes carry count deltas.
- `summaries`: explicit opt-in report records, including author/source receipts,
  text digest and any cited event/verification IDs.
- `inferred`: phase, progress, scope and difficulty hypotheses taken from an
  unambiguous latest visible summary, with supporting summary IDs. Free text is
  not automatically interpreted. Missing fields and equal-time summaries yield
  unknown; later omission does not carry an older hypothesis forward as current.
- `unknown`, exclusions and limitations. Verified completion and progress
  percentages remain null.

The nested `execution` record is the existing compatibility projection. Its
legacy `facts.provenance="observed"` denotes the observation source, not the
epistemic classification of every computed field. Use the new `derived` fields
for count provenance. Tool-item aggregation, failure interpretation, repeated
failure grouping and test deltas are deterministic calculations; retained
statuses/exits/cases are observations. Existing inferred marker and criterion
fields retain their explicit heuristic provenance.

`compare_task_states` requires increasing checkpoints and identical
dataset/task/run/session identity. It distinguishes activity, failure, test and
declared-hypothesis changes. First availability of a hypothesis or text-only
summary change is `new_information`, not proof that task semantics changed.
`no_observed_change` means supported retained evidence is unchanged; it does not
establish an unchanged latent task. Missing scoped evidence yields `unknown`.
More tools do not imply more progress, higher difficulty or expanded scope.
Repeated failures identify a tool category or named tool, never identical
approaches, a stall, or a causal error pattern.

## Temporal and privacy boundaries

Every event must be observed **and** ingested by the checkpoint, belong to the
selected session/run bounds, and pass the existing supported projection checks.
Association and optional task-declaration receipts gate scoped evidence. A
description and summary must be available by the cutoff. Summary references must
already occur in the valid visible event/test evidence. Future or late summaries
are filtered before duplicate identity conflicts. Visible conflicting IDs fail
closed; ambiguous equal-time summaries do not acquire a UUID-derived ordering.

Raw payloads and arbitrary metadata never enter text representations or output.
Only supplied public/sanitized text is eligible for Potion. Source and actor
identity are self-attested; a SHA-256 receipt binds the text but does not prove
sanitation, human review or truth. CLI validation diagnostics omit input excerpts.
Nothing scans another application's logs or enables automatic transcript capture.

Run state, stop reason and outcome assessments do not enter the new states. JUnit
is visible only after the current final-artifact binding and evidence receipts.
Its current contract supports post-run reports on one final snapshot, not
intermediate test progression across code edits. Verification ingestion time is
absent from the ledger; provide external `evidence_available_at` receipts or
retain the explicitly reported trusted-observation-time limitation. Declaration
and association receipt claims remain trusted caller inputs.

This implementation analyzes one explicitly scoped session/run trajectory at a
time. It does not infer cross-session continuation or merge task identities.

## Inspectable evaluation

`tests/fixtures/longitudinal/scenarios.json` contains seven synthetic trajectories:
normal reported progression, repeated unsuccessful tool actions, declared
complexity growth, implementation-to-debugging declaration, reported completion
without verification, missing evidence and no observed change. Identities and
times are invented. Expected statuses/dimensions are **agent-authored software
checks**, not human-reviewed semantic truth. No outcomes are fabricated.

The evaluator compares initial-only A (abstains about subsequent change), B using
deterministic evidence comparisons and explicit structured reports, a metadata-only
B ablation, and C adding pinned CPU text diagnostics. It reports confusion counts,
unknowns, dimension agreement and unsupported-inference invariants separately.
Structured report fields remain author hypotheses; accepting them as declarations
does not demonstrate discovering their semantics from tools. Potion distances
have no validated classifier or decision threshold and cannot change B's labels.
Equal B/C classifications are a property of this conservative experiment, not
proof that embeddings cannot help a future reviewed semantic classifier.

See the frozen fixture manifest and `reference.json` for actual A/B/C results.
These are implementation checks on designed scenarios, not population accuracy.
Downstream outcome evaluation returns `insufficient_data` and null scores: there
are no independently verified downstream labels in this longitudinal dataset.
The existing `learn.task_state` / `representation.evaluation` prospective outcome
evaluators remain intact for a future valid cohort. Multiple checkpoints from one
run must not become independent outcome trials; select a prospective horizon,
apply historical assessment resolution, split task/family lineages and keep
final verification out of checkpoint predictors.

```sh
uv run model-learner learn trajectory-eval \
  tests/fixtures/longitudinal/scenarios.json --output /tmp/trajectory-report.json

# Optional: reuse ONLY the already approved local bundle, with its existing pins.
uv run --no-sync model-learner learn trajectory-eval \
  tests/fixtures/longitudinal/scenarios.json \
  --model-path "$PWD/.model-learner/models/potion-base-8M-bf8b056651a2c21b8d2565580b8569da283cab23" \
  --model-revision bf8b056651a2c21b8d2565580b8569da283cab23 \
  --model-sha256 930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2

# A single explicit task-trajectory-input/v1 package, without evaluation labels:
uv run model-learner task trajectory /tmp/authorized-trajectory.json
```

`TrajectoryInput` is a portable input object over existing contracts, not a new
ledger schema. Its `project()` method reuses the extractor. Report destinations
are exclusive; missing local weights remain unavailable and trigger no download
or silent backend substitution. Use the existing local uv PATH/cache setup from
`STATUS.md` if uv is not on your shell PATH.

## Minimum next real-data increment — proposal only

Collect a small voluntary pilot on already occurring local work. Start with
5–10 independently scoped trajectories to test evidence usability, not estimate
utility. Before execution, explicitly record a sanitized objective, named
acceptance target, configuration and task/run/session association availability.
Capture metadata through the existing supported stream without launching an agent.

At a few prospectively declared checkpoints (for example start, after an obstacle,
and before final verification), let the operator submit a short sanitized summary
sidecar: current activity, attempted mechanism, encountered obstacle, evidence of
progress and any declared scope/difficulty change. Use `CheckpointSummary` with
observed/available times, source reference, actor kind/ID, text digest and optional
already visible evidence IDs. Keep statements and structured hypotheses distinct
from independently verified facts. Human/manual submission is optional; agent
reports remain explicitly agent reports. This contract is now usable manually;
no hook, automatic generation, persistence collector or background scanning is
implemented or proposed as an automatic default.

Operator review before submitting text should replace identifiers with stable
local aliases and remove secrets, paths, source snippets, prompts and tool output.
Keep private sidecars in ignored `.model-learner/`, with explicit deletion/retention
choices. Export only individually authorized sanitized examples. Sanitation cannot
be proven by the current digest or source flag.

If test progression is needed, separately design intermediate artifact identities
and structured test receipts tied to those snapshots; do not weaken the existing
final-artifact verifier to accept intermediate evidence. Independently record the
eventual assessment, verification and label-availability time. Ask distinct human
authors/reviewers to label trajectories without model scores, using pending review
material rather than attesting human review on their behalf.

The next recommended development increment is this **manual, opt-in prospective
summary pilot and evidence-usability review**, followed by a separately authorized
intermediate-artifact contract only if needed. Resume predictive evaluation only
after enough valid labels, independent task lineages and prospective checkpoints
exist. Real-agent benchmark security restrictions remain in force. This increment
does not start the pilot or another milestone.
