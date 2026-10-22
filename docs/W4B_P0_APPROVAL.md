# W4B-P0 first observer-first pilot approval packet — v1

**READY FOR HUMAN REVIEW for offline preparation only.** No pilot approved or
executed; W4B remains incomplete. `EXTERNAL_RUNTIME_UNAPPROVED` blocks launch.
This packet concerns exactly one future run on one synthetic configuration task,
not the W4A graph task, a benchmark collection or ordinary repository work.

## Frozen package

- Complete public instruction: [TASK.md](../tests/fixtures/w4b_p0/v1/TASK.md).
- Complete initial artifact: [start/pyproject.toml](../tests/fixtures/w4b_p0/v1/start/pyproject.toml).
  Only this file and the exact instruction enter the candidate workspace;
  no reference solution, checker, report, receipt or private material enters it.
- [Pre-run manifest](experiments/w4b_p0_v1.json): exact instruction/start/checker
  SHA-256 values, all nine required IDs, proposed configuration, target alternatives,
  evidence mapping and pending approval register. This is a preparation record,
  not a canonical Task/Run, real forecast, execution receipt or approval.
- [Trusted checker](../scripts/check_w4b_p0.py): stdlib `tomllib`, no candidate
  imports/builds, commands or network. It reads one selected bounded regular file
  and returns deterministic complete JUnit with artifact/report digests. Every
  case has pass/failure, never a skip. Invalid artifact/parse means downstream
  checks fail closed. Infrastructure inability to finish/report remains unknown.
  The operator writes reports only outside the candidate boundary using exclusive
  creation. For a future approved run, the trusted operator can invoke
  `.venv/bin/python -B scripts/check_w4b_p0.py FINAL --report NEW_OPERATOR_XML`
  only against the immutable handed-off snapshot, after candidate access ends.
  Its final JSON reports both digests; it does not write a binding or ledger row.

Checker/contract authorship and this review are by this preparation executor.
No independent human audit, external runtime attestation or provider availability
is implied. Public checker source is acceptable; security relies on independent
control of its frozen bytes, execution, report and evidence store, not secrecy.
The bounded parser reduces candidate-code risk but does not establish general
hostile-environment safety. Symlink/file checks assume immutable operator-owned
parent directories, not a filesystem adversary racing the checker. A digest proves
content identity only, not external-runner authenticity or independence.

## Practical external environment proposal and missing evidence

Propose an operator-run Codex CLI in a separately approved isolated environment,
with only the two approved inputs visible and the single final TOML handed out.
No specific backend, image, account or runtime is selected/approved. A normal
same-user local Codex CLI is not isolation. Read-only `codex exec --help` confirmed
the installed CLI describes explicit model selection, directory, JSON output,
ephemeral mode and user-config exclusion. Help printed a PATH-alias permission
warning; no permission escalation followed. This is interface evidence only,
not proof of containment, identity, effective effort, entitlement or stop controls.
No config/auth file was read. No containment probe was repeated.

W4A.1 already found macOS bootstrap failure, absent supported Docker socket,
readable same-user canaries and escaped descendants surviving group termination.
Those findings still block assuming a trusted boundary. Before launch obtain:

1. Named, pinned runtime and validated candidate-only input/output filesystem;
   no access to host repositories, checker, evidence store or receiver.
2. Credential isolation (harness/provider credentials outside candidate access),
   exact tool policy and network policy; no uncontrolled integrations or hooks.
3. Supported actual provider/model/configuration/execution identity and stable
   capture identity; operator settings are declarations until corroborated.
4. Defined completion, cancellation and stop ownership, including descendants
   and controller failure; a safety timeout alone is not a proven stop guarantee.
5. Immutable final artifact transfer, independent operator-controlled checker,
   trusted first-receipt receiver and retained actual clocks/digests.
6. Missing capture, ambiguous configuration, interrupted execution, artifact
   transfer failure, verifier integrity loss or incomplete report retained as
   unknown/ineligible as existing contracts require. No automatic retry.

No runtime installation/activation, image acquisition, watchdog, privilege change
or new execution platform is authorized by this packet.

## Duration and exposure decision — two mutually exclusive proposals

W4A and **Option A remain frozen at `ResourceBudget(max_duration_seconds=600)`**,
with the existing acceptance version. Nothing here changes their records.

| Proposed target for this one exercise | Meaning and current support |
| --- | --- |
| `w4b-p0-signal-note-duration/1`, non-null 600 seconds | Current canonical acceptance-with-budget semantics; requires complete accepted attributed Attempt latency. Operator process elapsed, stream receipt span and safety deadline do not satisfy it. With absent measurements real observations retain `budget_duration_unknown`; the benchmark path independently retains `budget_measurements_not_supported`. Currently unsuitable for a supported duration-learning claim. |
| `w4b-p0-signal-note-acceptance-only/1`, explicit null budget | Separate new Task/target if specifically approved before execution; all frozen data checks, no duration-bounded success claim. A separately approved external safety stop/exposure cap still applies. Cannot relabel W4A or remove its budget. Existing nullable-budget APIs suffice; no policy implemented. |

Recommend human consideration of the second distinct target for the smallest
acceptance/observer demo because available evidence supplies no canonical latency.
Neither target is selected by preparation. Choosing the first with unavailable
measurement must retain ineligibility and cannot complete real learner integration.
The second still requires the same runtime/trust/resource approval gates.

Proposed coding configuration: provider OpenAI, model **`gpt-6.1-sol`**, reasoning
**medium**, harness `codex.exec`. Exact harness/config versions, backend model
revision, availability and effective effort are pending evidence. No substitute,
upgrade or fallback. Exactly **one attempt, zero retries**, including infrastructure
retries. Proposed external safety deadline is 600 seconds, enforcement unproven;
it is separate from the statistical target and not approved. Human must specify
token/exposure limits and accept/reject any unenforceable bounds before launch.

Propose existing subscription allowance only if separately confirmed and approved.
Allowance consumption is separate from monetary spending. No new API spending,
credit purchase, OpenRouter/Jev or subscription probe is authorized. Billing,
token usage, native latency, enforceable caps and actual monetary cost remain
unknown, never zero. No measured inference or allowance use occurred here.

## Exact eventual W6B-compatible evidence handoff

Use existing APIs, as exercised by W6B/W7A; the example is choreography, not a
security gateway. The manifest contains a field-to-API mapping. Before a future
approved launch create one Task under the approved target, freeze its acceptance,
required IDs/start/checker/configuration and explicit dataset. Preselect its Run
UUID and freeze `CompatibilityPolicy`, cutoff and `forecast` via `freeze`; retain
the returned digest with the trusted receiver **before any execution/outcome**.
No execution-specific real forecast is created in P0. New cohort is prior-only;
no historical ledger was inspected and no evidence is borrowed from preparation.

The external operator owns launch/stop/capture; Model Learner observes. Import
the supported `capture_codex_stream` / `ingest_codex_capture` evidence; explicitly
associate native Session, Task, Run and the single contiguous Attempt. Record
requested versus supported observed configuration, provenance, bounds, capture
completeness and stopped artifact digest. Missing telemetry remains null. Run
and Attempt may be closed/associated after execution, without backdating records
or claiming their later availability existed at the forecast cutoff.

Export execution-only `scoped_bundle`; receiver reviews exact approved Task,
Run/configuration/dataset/acceptance and rejects producer verification/labels or
borrowed receipt authority. `import_bundle` validates identities; actual receiver
`ReceiptBook.capture` records first arrival and is persisted. Do not transplant
synthetic example IDs/config/dataset or producer clock into a real receipt.

Operator independently checks the immutable final TOML with the pinned checker.
Retain complete nine-case XML and `JUnitReportBinding`: actual Task/Run UUIDs,
chosen acceptance spec, `sha256:` artifact fingerprint, bare report SHA-256,
actual timezone-aware generation time, `source="junit"`, true completion and
actual checker exit (0 pass, 1 complete failed acceptance). An unreadable/missing
artifact can produce a failed local report but cannot supply the required artifact
binding: retain unknown/ineligible rather than inventing a fingerprint. An
interrupted/failed checker process supplies no complete verification. Producer
JUnit or completion text alone has no authority; independence needs external
evidence, which `verify_junit` and schema validation cannot authenticate.

Use `verify_junit` then `assess_run` then `build_real_observation`; explicitly bind
Verification to the actual Attempt using existing bundle associations and retain
new receiver receipts for each dependency. Retain excluded/unknown derivations
and reasons, including config conflicts, incomplete coverage or budget unknowns.
Use `resolve_bundle` at actual cutoff for eligible rows. Score only the retained
forecast/digest via `score_frozen` after a supported label becomes available;
never refit it. Existing Beta-Bernoulli consumes eligible deduplicated rows; later
`advise` receives scoped bundles and remains read-only/abstaining. One trial
establishes no predictive superiority, calibration or general model preference.

Proposed eventual dataset is `source_kind=real`, ID
`real-on-synthetic-w4b-p0`, version `1`: actual external execution on this public
synthetic task, explicitly segregated from natural-work data, simulated checks and
benchmark rows. Human must approve this classification and exact target; never
relabel an existing benchmark run to enter the REAL-only resolver. If classification
is rejected, stop for review; no benchmark adapter or source-kind change is in P0.

## Finite human decisions — none approved

All six entries in the manifest are pending. A later approval must name:

1. Exact task/start/instruction/checker hashes and acceptance/required IDs; confirm
   trusted operator/checker/receiver identities and independent control evidence.
2. One validated external runtime and immutable input/output/tool/network/credential
   policies, with execution identity and full-boundary stop evidence.
3. `gpt-6.1-sol`, medium, confirmed provider/harness versions/availability; exactly
   one attempt, zero retries, no substitution or continuing cohort.
4. One of the two explicit target contracts and the segregated dataset/source-kind;
   any null-budget target is a distinct Task requiring specific approval.
5. Exact subscription allowance exposure, monetary authorization (no new spend
   proposed), token/safety/operator-time ceilings, enforceability evidence and
   explicitly accepted unknowns. Unresolved limits block launch.
6. Actual forecast cutoff/digest custody and evidence-handoff plan, plus treatment
   of ambiguity, missing data, cancellation and verifier failure.

Approval is valid only for those named task/model/environment/attempt/resource
bounds. Packet completion is not approval. No blanket approval or later batch,
W5/W7 work, automatic routing, runtime implementation or agent execution follows.
Full W4B still needs authorized external execution, trusted independent outcome,
legitimate receipt chronology, frozen forecast scoring, eligible learner update
and later read-only advice, with unknown/failure/duplicate/privacy controls.

## Offline validation and coordinator handoff

Focused new tests cover P1–P9 and P12. Existing W6B negative controls supply P10
(self-report unverified), P11 (null telemetry and missing-duration exclusion),
receipt, forecast, outcome, learner and advisory regression coverage. No candidate
Python, sandbox diagnostics, Git-mutating tests or W7A demo/replay are rerun.
Actual final counts and checks are recorded in STATUS.

Leave all changes unstaged/uncommitted. Suggested nonempty Desktop commit groups:

1. `feat: prepare one data-only observer pilot contract` — TASK/start, checker,
   focused tests and manifest together.
2. `docs: record first pilot approval gates and offline evidence` — this packet
   and STATUS.

Coordinator alone reviews/stages, runs `python3 scripts/privacy_guard.py --staged`,
commits via GitHub Desktop, then separately verifies/pushes only approved commits
to existing origin/main. Executor performs no Git writes.
