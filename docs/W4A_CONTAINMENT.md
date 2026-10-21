# W4A.1 offline containment and watchdog readiness

**PARTIAL engineering result; W4B launch BLOCKED.** Checked 2026-10-21 using
fictional canaries and finite local Python subprocesses only. No production
source, schema, eligibility rule, frozen W4A contract or real-execution gate
changed. No verified process-tree watchdog was delivered: the required descendant
boundary is unavailable. Passing diagnostic tests below reproduce failures of
isolation; they are not security approval.

## Baseline and scope

Coordinator attestation confirms both GitHub Desktop commits and pushes:
`72bcab1a59a430ac8eb16c989254c46356f1c716` (four preparation files), then
`762aceb3424ea7913c8a01a16637a4053e530cf3` (STATUS/operator documentation).
Read-only Git inspection found `main`, HEAD and cached `origin/main` equal to the
latter commit, ahead/behind 0/0, all six reviewed files committed, empty index
diff, no tracked modifications and no untracked files. No fetch independently
checked the live remote. No pre-existing edits needed preservation. Existing
`.githooks` configuration and executable privacy hook were retained.

The chat's reported working directory matches the registered Model Learner project
`5e9ee82f-ab79-435f-a8c9-8bb3c4b689d3`. No model setting was changed. Read only the
authorized synthetic W4A preparation package within ignored storage; no other
private evidence was enumerated or opened. All six protected and two public
starting-file digests still match the frozen public manifest.

## Backend and boundary evidence

Host: `macOS-26.6.2-arm64-arm-64bit`, Python `3.12.14`.

| Backend | Actual finding |
| --- | --- |
| macOS `/usr/bin/sandbox-exec` | One new call to existing `macos-canary-probe/v1`: exit 71, `sandbox_bootstrap_unavailable`. Candidate shell never established allowed reads/writes; all denial claims UNPROVEN. No repeated bootstrap attempts or escalation. |
| Docker `/usr/local/bin/docker` | CLI present; supported local Desktop socket absent. Default `docker-offline-probe/v1` returns `image_approval_required`; selecting its fixed supported image reaches `docker_desktop_socket_missing`. No daemon command/container/image/network probe ran. Local image presence is unknown, not assumed absent or approved. |
| Other local command-line backends | `podman`, `bwrap`, `firejail`, `limactl`, `colima` absent from PATH. No exhaustive host software inventory or installation attempted. |
| Same-user folders / Python `-I` | Negative control can read all seven external synthetic categories and write outside its workspace. Neither is isolation. |
| Existing real benchmark gate | `require_supported_real_containment()` still rejects unconditionally. |

Actual macOS profile SHA-256:
`846b9b6387017ff846750e5bed62376e75e8f0a67012f018c7a3cd99d732443d`.
Profile with the disposable workspace normalized to `/SYNTHETIC_WORKSPACE`:
`4f9b1aa8e60f68e6aaee6ecd645c986153a5dee20f6bfce9f037df72a819e85f`.
Policy source is unchanged `src/model_learner/benchmark/isolation.py::_profile`.
Docker policy hash/runtime version are null because it could not start. This
inventory is scoped to existing supported facilities in this execution context.

| Probe | Same-user synthetic control | Supported isolated execution |
| --- | --- | --- |
| C1 public TASK.md/planner.py read | PASS | UNPROVEN: bootstrap failed |
| C2 workspace write | PASS | UNPROVEN |
| C3 protected-test read denial | FAIL: fictional canary readable | UNPROVEN |
| C4 reference/oracle read denial | FAIL: fictional canary readable | UNPROVEN |
| C5 other-arm read denial | FAIL: fictional canary readable | UNPROVEN |
| C6 forecast/evidence read denial | FAIL: both fictional categories readable | UNPROVEN |
| C7 fake-credential read denial | FAIL: fictional canary readable | UNPROVEN |
| C8 unrelated-host read denial | FAIL: fictional canary readable | UNPROVEN |
| C9 outside write denial | FAIL: synthetic outside file created | UNPROVEN |
| C10 symlink/traversal denial | FAIL: both reads succeeded | UNPROVEN |
| C11 descendant restriction | FAIL: child read outside canary | UNPROVEN |
| C12 tool network denial | UNPROVEN: not attempted | UNPROVEN: no isolated local facility |
| C13 integrations/privilege denial | UNPROVEN: no real integration or privilege probe | UNPROVEN |
| C14 candidate cannot access verifier secrets | UNPROVEN: unsafe architecture identified, no arbitrary candidate run | BLOCKED pending separate worker boundary |

All seven canary categories are newly authored fictional data in pytest temporary
directories. No actual credentials, other-arm artifacts, tests, oracle or private
evidence are supplied to these child processes. C1/C2 establish only functioning
negative controls. A few canaries could not establish general adversarial security
even if successful. No external or loopback network connection was attempted.

**Verifier verdict: BLOCKED.** The frozen protected `test_acceptance.py` imports
`oracle` and then calls `spec.loader.exec_module(submission)` in the same process.
The preparation runner admits only the reviewed reference/starter. Read-only
mounts, Python isolated mode or an import allowlist cannot hide that runtime from
hostile Python. `src/model_learner/verification/junit.py` validates existing report
bindings; it does not isolate or run candidate code. A separate restricted worker,
with trusted tests/oracle/report writer outside its filesystem and address space,
bounded typed request/response transport, and enforceable filesystem/network/
process controls is required. Performance accounting must still honor the frozen
CPU-time contract and be recalibrated on that runtime. This is an unsupported
security component requiring a separate design decision; no substitute verifier
was implemented and no arbitrary candidate was executed with hidden source.

## Process controls and watchdog limits

Existing `benchmark/offline.py::_bounded` limits one Docker-client process and
output; its caller separately destroys a named container. It is not an agent
process-tree watchdog. `adapters/app_server.py::AppServerClient.close` also stops
only its direct child. Codex capture observes a stream without launching it.
The `execution/` modules analyze observations, not process ownership.

Fresh synthetic evidence in `tests/integration/test_w4a_process_boundaries.py`:

| Requirement | Actual evidence and limit |
| --- | --- |
| W1 normal exit | PASS for existing bounded helper; measured local interval 0.015004625 s in the final focused run. |
| W2 deadline | Direct child stopped at 0.402371667 s with a 0.4 s synthetic deadline; helper raises `wall_deadline_exceeded`. This is a polled stop with scheduling/cleanup overhead, not an exact hard wall ceiling. |
| W3 parent exits first | FAIL for descendant containment: child prints a later survival marker after parent exit; timeout case likewise writes a later marker after the parent was killed. |
| W4 ignores graceful termination | An in-group child ignores SIGTERM and is stopped by group SIGKILL. A `start_new_session=True` child escapes the original group and survives until its fixed one-second self-exit. Thus process-tree readiness FAIL. |
| W5 ownership | Signals target only owned Popen roots or a newly created group with an unreaped leader. A separately created control process remains alive through group termination. No discovered/recycled descendant PID is signaled. This limited control passes; arbitrary descendant ownership is unproven. |
| W6 recorded cancellation | UNPROVEN: no reusable controller terminal-state/cancellation receipt exists. No cancellation API was fabricated. |
| W7 timeout versus task failure | Existing helper raises an infrastructure exception, creates no outcome. Frozen W4A contract makes wall timeout indeterminate. Existing lifecycle regressions preserve unknown/incomplete labels; no watchdog-to-outcome integration exists. |
| W8 timing | Local test controller uses `time.monotonic_ns()` start/stop; helper deadlines use `time.monotonic()`. Elapsed includes local launch/wait/cleanup overhead, not provider/native inference or verified completion. No canonical latency was populated. |
| W9 repeated termination | Duplicate test cleanup of one owned Popen root is safe. Group retry is not certified: initial detached case received EPERM when signaling a group with its terminated, unreaped leader. Final diagnostic retains that observed error and verifies child survival. |
| W10 observed cleanup | All direct children reaped; known synthetic descendant PIDs checked absent. Escaped children self-exit, so this proves test cleanup, **not watchdog enforcement**. No observed test orphan remains. |

Initial diagnostic run: seven passed, one failed at the second group signal with
`PermissionError`. The diagnostic was corrected to retain that host result only
for the empty original group; denial of the in-group SIGKILL still fails. All
eight final diagnostics passed. Final tests do not reinterpret EPERM as cleanup.

**Process-tree watchdog verdict: BLOCKED.** A group kill cannot stop a child that
creates a new session. Reliable untrusted-tree ownership/termination requires an
OS-enforced boundary preventing escape or a supported whole-boundary teardown.
Installing/starting such a runtime or building a new supervisor/security backend
is outside this increment. Stopped the implementation subtask at this concrete
blocker; did not introduce a weaker production watchdog or agent launcher.
Sequential attempts, cancellation receipts, a hard 600-second exposure bound and
controller-crash cleanup remain unimplemented. Provider token/dollar caps, remote
inference cancellation and native model latency are separate unknowns.

## Read-only budget and receipt assessment

1. `domain/models.py::ResourceBudget.max_duration_seconds` is a nonnegative scalar
   with no clock/basis discriminator. The ordinary builder in
   `observations/__init__.py` compares it to the sum of complete attributed
   `Attempt.latency_seconds`, excluding unknown/exceeded values. Existing policy
   in `docs/PROSPECTIVE_FAMILY_EVALUATION.md` forbids inventing this latency from
   operator wall time. The schema alone does not define a native-inference clock.
2. A future external controller can measure local elapsed launch-to-observed-stop
   time using a monotonic clock. Without whole-tree containment its root stop is
   not even proof of the last descendant's stop. It cannot measure native model
   inference latency, provider cancellation or cost from that interval.
3. Existing metadata/sidecars can preserve explicitly named local process
   intervals and their limitations without changing canonical latency. They
   cannot presently make this non-null benchmark budget eligible. Never replace
   the declared 600-second budget with null or write wall time into latency.
4. `benchmark/evidence.py::export_benchmark_evidence` retains the budget and adds
   `budget_measurements_not_supported` for every non-null budget. Its
   `BenchmarkEvidence` lacks first-receipt times for run/attempt declarations and
   verification, plus prospective initial/scope receipts. Its checkpoints remain
   audit projections. `storage/evidence.py::ReceiptBook` supplies digest/first
   receipt mechanics, but `_replay` requires REAL and `resolve_bundle` delegates
   to the real observation resolver. It is not a benchmark adapter. Codex capture
   receipt timestamps in `adapters/codex.py` are not native event timestamps.
5. A narrow W4A.2 **receipt-only** benchmark sidecar is structurally plausible:
   preserve benchmark provenance, task/run/attempt/configuration/acceptance/digest
   bindings and all first-receipt gates without changing canonical records or
   borrowing historical evidence. Eligibility can remain false while measurements
   are missing. This feasibility assessment did not implement or validate it.
6. Full 600-second budget eligibility is **BLOCKED pending policy decision**:
   decide the duration target and accepted measurement/coverage/stop receipt
   contract before implementing eligibility. An explicit versioned benchmark
   policy/sidecar may avoid a canonical schema migration; if multiple duration
   bases must be first-class canonical budgets, a schema decision is required.
   Current semantics cannot be silently broadened. Timeout is not verified failure
   absent an approved acceptance-by-deadline target; the frozen W4A contract
   currently calls it indeterminate.

## Validation and handoff

- New diagnostics: **8 passed in 4.01 s**, no skips. Actual unsupported macOS and
  Docker availability results above are separate from these negative controls.
- Existing focused containment/benchmark/capture/verification/learning and W2/W3
  regressions: **418 passed, one opt-in Docker skip in 17.96 s**; includes all
  nine public W4A preparation checks. No Git-policy tests were selected; all 55
  tests that stage/commit in fixtures were excluded. No Potion/model tests ran.
- Ruff repository lint and format, whitespace, non-staged privacy and final
  unchanged-index checks are recorded in the accompanying STATUS checkpoint.
- Ignored output only: `.model-learner/w4a-containment-probes-v1/` contains backend
  JSON, initial index digest and three focused plus one regression JUnit XML.
  Temporary canaries/subprocess files are disposable pytest artifacts. Existing
  W4A preparation files and protected hashes are unchanged.

| Readiness area | Verdict |
| --- | --- |
| Agent containment | BLOCKED: same-user control FAIL, supported backend denials UNPROVEN |
| Untrusted verifier isolation | BLOCKED: separate worker boundary missing |
| Process-tree watchdog | BLOCKED: demonstrated descendant escape; no safe utility delivered |
| Benchmark budget/receipt adapter | BLOCKED for full eligibility; receipt-only extension plausible but unimplemented |

Smallest next bounded step: separately authorize W4A.2 receipt/measurement-contract
work, first resolving duration semantics; keep unsupported budget evidence
ineligible. A separate supported isolation-backend/verifier decision is required
before W4B can progress. W4A.2, W4B, human allowance decisions and agent execution
were not started. No staging, commit, push, publication, dependency/image download,
privilege change, additional model or private-history access occurred.
