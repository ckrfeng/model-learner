# Execution-state checkpoint analysis

`model_learner.execution.extract_execution_checkpoints` is a pure reader of the
existing `codex.exec` Event metadata projection. It returns typed JSON-compatible
checkpoint records. It launches no process, reads no transcript or arbitrary
file, controls no agent, and creates no ledger records or learner observations.
The extractor has no routing, switching, neural model, or Governor behavior.

```python
from model_learner.execution import extract_execution_checkpoints

snapshots = extract_execution_checkpoints(
    captured_events,
    session_id=session.session_id,
    checkpoints=[first_checkpoint, second_checkpoint],  # aware datetimes
)
for snapshot in snapshots:
    print(snapshot.model_dump_json())
```

The CLI exposes this session mode with repeatable explicit cutoffs:

```console
model-learner session analyze SESSION_ID \
  --checkpoint 2026-10-10T12:00:04+00:00 \
  --checkpoint 2026-10-10T12:00:10+00:00
```

Use the ledger option documented by `session analyze --help` to select the
existing local database. The analysis does not create missing sessions.

## Availability and scope

Cutoffs are inclusive. An Event contributes only when both `observed_at` and
`ingested_at` are at or before the checkpoint and its session matches. Matching
supported source, adapter version, receipt timestamp basis, projection structure,
and observed provenance are required for interpreted features. Other visible
events are counted as unsupported; their arbitrary payloads are not interpreted.
Raw retained payloads and agent message contents are never used.

Checkpoint results preserve caller order and can be rebuilt deterministically.
Visible duplicate event identities do not count twice; conflicting visible
identities raise a content-free `ValueError`. Future events, ingestion receipts,
or identity conflicts cannot alter an earlier checkpoint. This replay protection
does not globally deduplicate independently recaptured streams.

Optional run mode takes canonical `task` and `run` records plus an explicit
`association_available_at` receipt for the run/session scope. Events must lie
within declared run receipt-time bounds. The scope is unavailable before the
Task's `created_at` or the association receipt; a missing association receipt is
unknown. A caller is responsible for supplying the correct explicit association.
The extractor does not read SQLite to establish it. Run state, stop reason, final
outcomes, later attempts, and agent claims do not feed execution state.

## Facts and heuristics

`facts` has observed provenance and retains supporting Event IDs. It includes:

- Visible and supported event counts; observed turn start/completion/failure
  marker counts. These count markers, not inferred unique task trials.
- Tool item histories keyed by capture ID plus native item ID. A start and finish
  describe one item. Missing IDs count tool **events**, without inventing unique
  tool executions. Native statuses and exit codes are retained separately.
- Terminal item counts, observed failures, and unknown failure coverage. A
  completed command with no exit code has unknown failure. Terminal status/exit
  contradictions or conflicting item lifecycles emit diagnostics and preserve
  unknown failure. Tool completion does not prove correctness.
- Repeated failures from at least two distinct failed items, grouped by a retained
  MCP server/tool identity where available, otherwise only the tool category.
  Redacted commands/arguments cannot establish identical operations, retries,
  repeated error causes, or a loop. `same_operation_retry` stays null.
- Known token totals with per-field completed-turn coverage. A measured zero is
  zero; absent token fields, native duration, and monetary cost remain null.

`execution_state` and `signals` have inferred provenance, a fixed rule version,
supporting IDs, and explanations. The latest supported turn/start marker suggests
activity, an observed completed turn, or an observed failed turn. Without a marker
the state is unknown. Capture sequence orders equal receipt times within one
capture; independent captures with equal times have no shared chronological order
and yield unknown. Repeated-tool-failure signals describe the counted failures,
without claiming a stall, difficulty, causal explanation, or useful intervention.

## Structured test evidence

Session mode does not infer tests from command names, output, exit zero, turn
completion, or agent claims. Its test state stays unknown without canonical bound
test evidence. Optional run mode supports:

```python
snapshots = extract_execution_checkpoints(
    captured_events,
    session_id=session.session_id,
    checkpoints=cutoffs,
    task=task,
    run=run,
    association_available_at=association_receipt,
    artifact_available_at=artifact_declaration_receipt,
    verifications=junit_evidence,
    evidence_available_at={evidence.verification_id: ingestion_receipt},
)
```

JUnit inputs pass Workstream A's pure `validate_junit_evidence` checks for exact
task, run, acceptance criterion/version, final artifact fingerprint, report
binding/digest, observed provenance, retained case/count consistency, completeness,
and deterministic criterion result. Unsupported or invalid/foreign/stale evidence
is excluded with a counted reason; it cannot become passing evidence. A missing or
future artifact declaration receipt leaves test evidence unavailable. No final
artifact or future report is used to rewrite an earlier state.

Verification lacks a persisted ingestion timestamp. Optional
`evidence_available_at` supplies an external availability receipt. Otherwise the
trusted declared `observed_at` is availability, and the checkpoint explicitly
reports this limitation. Availability never precedes observation. Declaration
receipts and report associations are trusted caller/operator inputs, not a
cryptographic attestation that tests ran against the code.

Test records preserve counts, all retained case entries, unambiguous case statuses,
duplicate identity diagnostics, artifact/report identities, and availability
basis. Counts mean **retained report case entries**, not an inferred total of tests
actually executed. A missing/malformed report can have zero retained entries with
indeterminate status; those zeros are not evidence of zero executed tests or zero
failures. Completeness and criterion result have explicitly inferred provenance;
the execution-completed flag retains external operator receipt provenance.

Changes compare chronologically observed reports within this one canonical
acceptance target and final artifact. Numeric failure/error/pass deltas require
the identical test set and complete reports. Changing suites or incomplete reports
leave deltas null, while changes to unambiguously observed shared case statuses
remain visible. Equal-time report groups lack an explicit revision ordering;
comparisons touching them are suppressed and a tied latest group yields unknown.
Verification-ID sorting provides deterministic output, never a causal order.

**Current boundary:** these are post-run reports bound to one declared final
snapshot. The existing verifier accepts evidence after run completion. This API
does not reconstruct test progression across intermediate code edits or artifact
snapshots, and it cannot attribute improved tests to an agent action. Supporting
that requires a separately scoped checkpoint-artifact evidence contract.
`verified_task_success` remains null; an independently assessed Outcome is still
required for a verified task label.

## Controlled examples and tests

`tests/fixtures/execution/` contains explicitly synthetic metadata-only Codex
events and realistic pytest XML layouts. Integration tests declare controlled
ingestion receipts one second after each event observation. They show:

| Checkpoint | Visible events | Failed tool items | Interpretation |
| --- | ---: | ---: | --- |
| 12:00:04 UTC | 3 | 0 | Started command; its future failure is unavailable |
| 12:00:07 UTC | 6 | 3 | Two named-tool failures; same-operation retry unknown |
| 12:00:10 UTC | 9 | 3 | Completed turn; one unknown command exit; tests unknown |

A ledger integration reads actual fixture XML through the JUnit verifier, then
shows failure and passing report states only after their explicit availability
receipts. The artifact stays fixed: this is a controlled report-status example,
not a real coding success or an edit-causality example. Analyzer execution leaves
Event, Verification, and Outcome rows unchanged.

Unit tests cover delayed ingestion, future conflicts, task/run/artifact/evidence
availability, unsupported metadata, source/provenance rejection, repeated failure
identity, missing IDs/exits, contradictory lifecycles, independent capture ties,
test suite changes, missing/incomplete reports, duplicate cases, foreign/stale
evidence, report ties, and honest unknown resources.
