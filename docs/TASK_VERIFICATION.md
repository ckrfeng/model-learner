# Explicit tasks, deterministic verification, and real observations

Model Learner records the activity of an independently operated agent. This
workflow never launches or controls an agent, changes a model, or runs a verifier
command. The future AI Governor owns agent control.

The supported real-data source remains an explicitly imported, metadata-first
`codex exec --json` capture. Native task completion and tool exits are activity
observations; they do not establish task success or failure.

## What this increment verifies

`file-sha256/v1` tests one narrow acceptance criterion: a regular file's exact
bytes have the SHA-256 digest declared when the task was created. Declare that
criterion only for a task whose acceptance is exact byte equality. A hash match
does not establish that a program is correct, that tests passed, or that a broad
natural-language objective was satisfied. Identical bytes at another path satisfy
the same criterion; path identity is not part of this check.

The expected digest resides in the task's immutable metadata alongside its
acceptance identifier/version. The run separately records the declared final
artifact fingerprint (`sha256:<64 lowercase hex digits>`). Verification hashes the
artifact read-only and rejects changed or wrong snapshots. If the snapshot is
correctly bound but differs from the acceptance digest, it records fail evidence.
Stat checks before and after reading reject ordinary concurrent modifications;
the file is not locked, and this is not an adversarial snapshot/attestation system.

Evidence preserves task/run identity, acceptance specification, verifier version,
observed time, artifact path/fingerprint, expected and actual hashes, observed
provenance, and the read-only capture method. It retains no file contents.
Artifact paths and task descriptions can themselves contain private information;
keep the ledger and exported records local unless sharing them intentionally.

## Local CLI flow

Use an existing sanitized capture and the explicit IDs returned by commands.
Replace the illustrative timestamps with the capture interval's real observer
receipt times. See [CODEX_OBSERVATION.md](CODEX_OBSERVATION.md) for capture details.

```bash
model-learner init
model-learner import codex local.capture.jsonl --machine-id local-machine
model-learner sessions
model-learner task create "Write exact declared output bytes" \
  --acceptance-id exact-output --acceptance-version 1 \
  --acceptance-description "File SHA-256 equals the declared digest" \
  --expected-sha256 YOUR_EXPECTED_64_HEX_DIGEST --task-group exact-output
model-learner run create TASK_UUID --session-id SESSION_UUID \
  --started-at 2026-10-10T12:00:00+00:00 \
  --ended-at 2026-10-10T12:01:00+00:00 --artifact output.txt
model-learner run attempt RUN_UUID --configuration-file configuration.json \
  --started-at 2026-10-10T12:00:00+00:00 \
  --ended-at 2026-10-10T12:01:00+00:00 --declaration-source human
model-learner outcome assess RUN_UUID
model-learner verify file RUN_UUID output.txt
model-learner outcome assess RUN_UUID --verification-id VERIFICATION_UUID \
  --supersedes EARLIER_UNKNOWN_OUTCOME_UUID
model-learner observations build RUN_UUID --outcome-id OUTCOME_UUID \
  --dataset-id personal-codex --dataset-version 1
model-learner run show RUN_UUID
model-learner observations quality --dataset-id personal-codex --dataset-version 1
model-learner records export observation observations.jsonl --source-kind real
```

`configuration.json` is an exact `ExecutionConfiguration` declaration, for example:

```json
{"provider": null, "model": null, "harness": "codex.exec"}
```

Unknown model remains unknown and makes the observation ineligible. If a human
knows the executed configuration, they may declare its actual model/provider and
versions. The record labels that statement `human_declaration`; it does not claim
the native stream emitted it. Model/provider values explicitly emitted by captured
events that contradict the declaration exclude the run from clean attribution.

Task identity is independent of native session identity. A task can reference
several sessions and a session can cover several explicitly declared task runs.
`run attach-session` attaches a session already linked to that run's task via
`task attach-session`. Run boundaries are explicit; events are never rewritten.
All boundaries use aware timestamps. Native receipt time is not promoted into
execution time or measured latency. Bounds are inclusive; overlapping run ranges
in the same session, including shared endpoints, are rejected to prevent counting
one execution twice. Use genuinely disjoint ranges for separate runs.

## Assessments and eligibility

`outcome assess` without evidence appends unknown/unverified, including for a
finished run. A verifier result alone creates no assessment. Assessing supported
final evidence produces success/verified or failure/verified. Wrong run/task,
stale acceptance, wrong artifact, contradictory hash/result, and impossible time
ordering are rejected. Internal failed test cycles never create task failures.

`outcome human RUN_UUID --status success` records distinct human acceptance and
keeps it unverified. Other explicit statuses include failure, abandoned, unknown,
and censored; censored requires `--censor-reason`. Human labels alone do not enter
configuration-level verified-success learning. Assessment revisions append a new
record with `--supersedes`; the original assessment and evidence survive. Revision
targets must belong to the same run, follow it in time, and have no existing child.

The real observation builder requires a linked supported Codex CLI session with
captured observed events inside the bounded interval. It keeps assessment and
evidence identities, acceptance, budget, dataset/version, event/session/attempt
provenance, explicit decision/label-availability/recording times, and exclusions.
Record time must follow assessment and capture ingestion. Repeating an identical
derivation returns the same canonical observation even when called later.

Eligible observations require verified binary final evidence and known-model,
single-configuration segments covering the entire run contiguously, without gaps
or overlaps. Multiple segments of the same exact configuration count as one run;
different configurations retain mixed attribution and are ineligible. Missing
segments, models, or conflicting emitted telemetry retain incomplete attribution.
Task groups are declared manually; absent groups use the explicit `__ungrouped__`
marker. No task classification is performed.

Cost/latency stay null unless the complete run's segments supply all corresponding
measurements. Receipt intervals are never used to invent latency or cost. Active
resource-budget limits whose measurements are missing or exceed the limit exclude
learning eligibility while preserving the exact file verification result. Token
budget checks require known input and output token counts for every segment.

Quality output identifies source/dataset/version and counts retained assessment
derivations, verified/unverified/partial status, unknown/censored outcomes,
human assessments, mixed/incomplete attribution, eligibility, and missing cost or
latency. Historical revisions are not independent experimental trials. The current
learner rejects conflicting derivations for one experimental unit; before learning
from revised histories, select the applicable latest assessment explicitly. This
increment does not silently overwrite or reconcile earlier learner observations.

## Limits and validation

The integration fixture exercises capture/replay, explicit task association,
bounded attempts, pass/fail evidence, unknown and human/censored assessments,
revisions, real-contract observations, JSONL export, artifact/acceptance safety,
mixed attribution, native configuration contradictions, and missing budgets.
Fixture observations marked real test the M1.1 real-data contracts; they are not
claimed as authentic historical agent performance.

This verifier accepts regular files only, without directory/Git snapshots or test
report adapters. Imported arbitrary verification records are not trusted by the
deterministic assessment API. Ledger contents are evidence records, not tamper-proof
attestations. Bounded run creation uses short separate repository transactions;
an exceptional I/O/concurrency failure can leave a declared run without a session
link. The builder rejects unlinked runs rather than guessing the missing link.
No automated classifier, routing, switching, TUI, or cloud synchronization is added.

A separate real fixed-reply CLI validation also passed on 2026-10-10 with
`codex-cli 0.162.0-alpha.17.2`: four metadata events, replay without duplicates,
unknown completion then matching predeclared digest evidence, one eligible real
observation and one learner label. See STATUS.md for operator command boundaries,
manual configuration provenance, dataset selection and unknown resources. It
validates this workflow only, not coding-task performance or Desktop capture.
