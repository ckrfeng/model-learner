# Model Learner status

## One normal trusted-adapter runtime integration — 2026-10-23

**One new synthetic normal-path adapter/controller lifecycle passed, exit 0.**
Started clean on `main` at HEAD/cached origin
`6b32333aa20615f3807dc9176494c61ebedfc705`; no pre-existing edits. Read-only
preflight found the existing dedicated profile running: Colima 0.10.3, Lima 2.2.1
(matching its recorded running version), Docker client 29.8.2, zero VM host shares,
and exact ARM64 image
`sha256:24bb3511a0db7b5114a4aee033c65a8a4148f39b7b80a398e548546db967a36f`.
Installed binary hashes were recorded and rechecked before start; no installation,
profile/context change or runtime upgrade occurred.

Actual adapter use admitted the host-selected fixed synthetic target/config/input
with host-generated task/call identities and an opaque lease handle: **1 start,
31 bounded status calls, 1 output, 1 finalization, 0 recovery, 0 retry**. The normal
worker completed within the existing five-second lease; its validated receipt
bound the fixed input, stable stopped output and cleanup assertions. Exactly one
start event was independently found for its exact container. Output was **38
bytes**, SHA-256
`0cdeb83a8b7d787e41e9dbe720820b4bdbf6baad8a01849670fa3a5e98ae90bb`.
Adapter finalization retained validated lease/receipt/output/helper diagnostic
and removed temporary state. Independent exact-container queries confirmed
absence before/after retention; exact service absence returned 113 and the GUI
domain returned 0 with empty stderr. No guest PIDs were recorded in this normal
completion, so the empty PID check adds no descendant-enumeration evidence.

Ignored private evidence is
`.model-learner/dispatch-adapter-normal-v1-20261023-01/`: preflight/runtime identity,
one-shot drivers/guard, host binding and phase journal, bounded replies, retained
controller evidence, exact start event and independent absence summaries.
All **24 files** match the completeness inventory (23 entries plus inventory
itself). Integration receipt SHA-256
`7177eb03662f4a34657a4ac6de1d58f708832fd2ac7c93a3719c2e33c23e274b`;
inventory SHA-256
`4a5f8de4e749da5d12032833b2decf553ab9989526876bd2753cbb221a640f9e`.
No tests were rerun: checkout exactly matched the reviewed adapter commit. Only
driver syntax, evidence digest/completeness and STATUS whitespace/diff checks
were added; source/tests/controller behavior are unchanged.

This is one synthetic adapter integration, separate from the earlier three
controller-only cases, W4A/W4B and model transport. No model/provider/auth/external
network request, canonical record, coding task or Git publication occurred.
The adapter remains synchronous/in-memory, not crash durable. Generated launch
environment checks do not prove live inheritance or malicious-host/tool isolation.
Model identity/effort, routing/billing, provider retry, output/spend and remote-stop
evidence remain open; W4A's 600-second latency semantics are unchanged. Only this
STATUS entry is tracked and unstaged; index/HEAD unchanged. Stop here; no transport
work or second run started.

## Offline trusted lifecycle adapter — 2026-10-23

Added private `benchmark._dispatch_adapter` around the existing admission contract.
One host-owned instance per task owns a fresh private root, opaque handle/path
maps and retained output lookup. Start occurs only after admission and binds the
returned lease only when it matches owned state. Status validates lease/receipt
state; an active lease without a receipt is pending state, not worker liveness
proof. Output revalidates the original receipt and exact bounded bytes/hash.
Host-only retention delegates disposal only after confirmed stopped validation.
Existing controller and pure admission implementations remain unchanged.

Ambiguous start, cancellation, timeout or adapter failure can attempt cleanup-only
recovery at most once, against the exact owned directory; a replaced known lease
authorizes no recovery. Unknown cleanup keeps state/evidence and prevents
disposal. Start is never retried. The adapter is synchronous and in-memory, not
crash-safe: cancellation flags immediately but waits for an active port call to
return before recovery; the host must call `expire()` from its watchdog. Local
cleanup is not provider inference cancellation or a hard process deadline.

Verification: **147 passed** (29 synthetic adapter cases plus 118 contract cases)
using `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/unit/test_dispatch_adapter.py tests/unit/test_dispatch_contract.py`.
Touched-file Ruff lint/format checks passed; no configured type checker or broad
suite run. Fake ports exercised lifecycle mapping, retention, concurrent cancel,
uncertain cleanup, identity replacement, output races, and zero port access for
rejected/replayed proposals. The existing launcher generated a job from synthetic
files behind a mocked bootstrap boundary: its environment contained only the
existing fixed `PATH` entry and omitted the synthetic parent sentinel. No child,
launchd job or worker ran; this checks generated environment only, not runtime
inheritance, malicious-host isolation or transport acceptance.

Started clean on `main`, HEAD/cached origin
`f1098bedc301cde893e6b160199bda9d3c2fcb03`; no pre-existing edits. Source, synthetic
tests and this entry remain unstaged; index unchanged. No stage/commit/push,
publication, live controller/runtime/model/provider/auth/network operation or
actual environment-value inspection. Next dependency is separately reviewed
isolated controller integration acceptance without a model/provider call; not
started. Native identity, auth/billing, provider retry, output/spend, remote-stop
and tool-isolation evidence remain open. W4A/W4B retain their separate gates.

## Private typed dispatch admission contract — 2026-10-23

Added private `benchmark._dispatch_contract` and hand-authored synthetic unit
fixtures only. Host-selected task/checker snapshots, host-issued one-use call
permits, one start attempt, controller-created lease binding and distinct opaque
lease/artifact references support start, bounded status, stopped output and
cleanup-only recovery. Exact task context, single-flight transitions, 25 ms poll
cadence and existing controller deadlines are checked. Invalid or uncertain
completion becomes indeterminate; start cannot be replayed. Rejections expose
fixed enums only. State is host-owned memory, not a durable crash-safe registry.

Private protocol bounds are 1,024 request bytes, 2,048 serialized reply bytes and
2,048 host call IDs per instance; existing 64 KiB controller state, 1,024-byte
handoff, 0.5–30 second lease and four-second command bounds remain unchanged.
These protocol/cache bounds do not change task acceptance, spend budgets or the
separate frozen 600-second W4A semantics. No public export, adapter, wire client,
canonical observation/verification record or runtime behavior was added.

Focused verification: **118 passed** with
`PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest -q -p no:cacheprovider tests/unit/test_dispatch_contract.py`.
Ruff check and format check passed for the two changed Python files. No configured
type checker; no broad suite or runtime tests run. Synthetic controller boundary
sentinels recorded zero calls, including recovery and rejection paths. An initial
fixture polled two nanoseconds too early and was corrected before the passing run.

Started clean on `main`, HEAD/cached origin
`8e23b11f2b785158710292684fb582b08c0091a7`; no pre-existing edits. Source, tests and
this status entry are unstaged for coordinator review; Git index unchanged. No
model/provider/auth/network/worker/controller operation or Git publication.
The approved trusted dispatcher architecture remains unimplemented as an
execution harness and technically unaccepted. Native identity, auth/billing,
provider retry, output/spend and tool-isolation unknowns remain. Next separately
scoped dependency: offline trusted lifecycle adapter and clean child-environment,
cancellation and bounded handoff evidence, without a model request. Not started;
W4B-P0 and W4A retain their separate gates. Stop after this contract increment.

## First real public coding-task acceptance — 2026-10-23

**Narrow M0–M4 observer flow complete for one public task on the supported local
Codex CLI path. Overall Model Learner work remains open.** The task implemented
`normalize_line_endings(text)` against four frozen, intentionally public cases.
The independently authored public checker was unchanged and rerun by the operator
outside candidate access against the stopped immutable artifact: **4 passed,
0 failed, 0 skipped**, checker exit 0. Candidate process was reaped and its public
workspace removed before that independent check. No implementation was added to
the product source.

| Acceptance criterion | Preserved evidence |
| --- | --- |
| Reproducible local setup | Previously published Python/uv lockfile and installed CLI setup evidence; installer was not rerun for this acceptance. |
| Supported real local-agent capture | One corrected top-level `codex.exec` launch, parent/child exit 0/0, 18 metadata events, no capture diagnostics. |
| Explicit task and acceptance linkage | Frozen task/starter/public checker and four required case identities linked to the actual session, bounded run and single declared configuration segment. |
| Artifact-bound independent outcome | Exact stopped artifact and complete JUnit report bound to task/run/spec, artifact/report digests, generation time/source, completion and actual checker exit. Unknown assessment retained, then verified success appended. |
| Eligible real observation/export | Existing builder returned one eligible `source_kind=real` observation, zero exclusions; eligibility was inspected before exporting one row. |
| Idempotent reimport/rebuild | Identical capture inserted 0 events and recognized 18 duplicates; summary and observation identity stable; both unknown and verified assessments preserved. |

Requested/operator-declared configuration: `gpt-6.1-sol`, medium,
`codex.exec` / CLI `0.163.0-alpha.11`, local provider config ID
`openai_no_retries`, backend label OpenAI. Native model/provider/reasoning fields
were absent. Eligibility uses the existing explicit manual-configuration contract,
not native identity attestation. Cost, native inference latency, model revision,
runtime authentication/billing route and actual provider retry behavior remain
unknown. Observed usage: 70,439 input tokens including 54,272 cached input;
340 output tokens including 20 reasoning tokens. Subset counts are not added
again. About **20.733 seconds is process wall time only**, not canonical Attempt
latency. The 39 stderr bytes were `unclassified_nonempty`; raw text and meaning
were not retained. Exhaustive native-tool isolation is not proven.

Sanitized content bindings:

| Artifact | SHA-256 |
| --- | --- |
| Stopped public implementation | `3b6c3de2f75edbf8a64694ac1704d783b374c08e8e5f12c3bc519cf644bc907c` |
| Independently generated JUnit report | `747b96a7c1d7ffbde8d4924ddfc9c607a5e06586b5fe3bca2e025ac9b0e0823e` |

The coordinator independently checked all 33 preserved evidence artifacts and
the report/artifact binding. Captures, ledger, receipts and execution identifiers
remain private and ignored. Two earlier failed launches remain separate immutable
history; no discarded diagnostic or historical cause is reconstructed here.

The [finite acceptance matrix](docs/SYNTHETIC_CONTAINER_SUPERVISION.md#proposed-trusted-model-dispatch-decision--2026-10-23)
now marks this narrow real coding-task endpoint complete. Trusted/custom model
transport architecture is approved under standing authorization, but remains
unimplemented and technically unaccepted; this ordinary CLI run did not validate
it. W4B-P0 remains separately authorized but unexecuted.
W4A graph coding/containment and the unchanged 600-second attributed Attempt-latency
gates remain open. This single-task acceptance establishes no general model/task/
provider/harness capability, statistical advantage or whole-product completion.

This checkpoint changes documentation only, from a clean `main` baseline
`be0d13fc90a8f7eeef0a7ad7767a6eec0fda0af1`. No pre-existing edits. Only document
privacy, whitespace and local-link checks were run; no installer, candidate,
test/verifier, import/replay, provider or runtime was rerun. No code/dependency/
contract/budget change, staging, commit or push. All three edited documents passed
those checks; no staged guard was run. Stop for coordinator review.

## Trusted model-dispatch architecture recommendation — 2026-10-23

**Superseding authorization note:** standing human authorization approves the
previously presented versioned trusted-dispatcher recommendation. The approval
stops in this historical entry no longer apply; no renewed confirmation is
required for that architecture. Implementation and technical acceptance remain
open, including native-tool isolation, authentication/routing and spend evidence.

**Documentation decision prepared; architecture change awaits human decision.**
Started clean on `main`, HEAD/cached origin
`91800683ef6f4f9c163957219ba72a3757ab8658`; no pre-existing edits. Read the full
coordinator-supplied planner dispatch and existing published contracts/evidence
only. Requested `gpt-6.1-sol` / medium remains unverified by supported current-turn
metadata; no model override or subagent. No feasibility/probe/research repetition.

[Reviewable recommendation and finite acceptance matrix](docs/SYNTHETIC_CONTAINER_SUPERVISION.md#proposed-trusted-model-dispatch-decision--2026-10-23)
compare exactly two routes: wait for a proven supported Codex interface, or build
a purpose-built trusted host dispatcher. Recommend the latter conditionally, as
a separate external execution harness observed by Model Learner. Existing
controller remains the fixed-worker lifecycle/handoff authority; host transport
owns authentication/spend; dispatcher owns typed positive tool enforcement;
independent operator/receiver owns verification and first-arrival evidence.

One substantive decision is required: authorize a new versioned dispatcher harness
in place of proposed `codex.exec`, keeping OpenAI / `gpt-6.1-sol` / medium, frozen
task/checker, one attempt/no retry and exposure ceilings. Supported endpoint access
to that exact model/effort and enforceable budgets are unknown. No presently proven
route preserves the entire frozen configuration; a different harness must receive
a new configuration identity. If model/provider/budget preservation cannot be
proved, stop/wait; no substitution or fallback. No architecture change adopted.
Already-authorized ordinary setup, necessary free pinned downloads and the
separate acceptance-only pilot are not reopened as permission requests.

The matrix distinguishes M0–M4's incomplete real product endpoint, unimplemented
trusted model transport, the authorized but unexecuted separate W4B-P0 synthetic
pilot, W4A's unchanged graph/containment and 600-second attributed Attempt-latency
gates, and final real E2E. Historical CLI metadata smoke is not a verified coding
outcome; synthetic/benchmark/fixture success cannot complete the real endpoint.
First-call <=$1 and total <=min($15, proven remaining prepaid), lower effective
key limits and stricter frozen J2 limits remain intact. Jev metadata's $5 key
remaining/$0 usage is not wallet, TypeSafe-only/no-fallback or output-bound proof.

Exactly two documentation paths changed: supervision guide and this status.
Only focused working-byte privacy and whitespace checks were run; no code/tests,
runtime, provider request, credential read, agent, candidate, pilot, download,
model session or unrelated research. No new test/runtime evidence is claimed.
Both edited files passed those checks; HEAD/cached origin and index remain aligned
with baseline, no staging/commit/push/fetch. Prior source/tests/artifacts preserved.
Proposed coordinator commit: `docs: propose trusted model dispatch boundary`.
Stop after this decision record; subsequent implementation requires the specific
architecture decision, not another generic setup approval.

## Offline host-only Codex transport feasibility — 2026-10-23

**Bounded feasibility complete; required CLI boundary unproven. No bridge built.**
Started clean on `main`, HEAD/cached origin
`ede078e4ea5fe2af49ded078fba2b6059f2b0de9`, containing the published synthetic
supervision acceptance. Requested `gpt-6.1-sol` / medium remains unverified by
supported current-turn metadata. No new chat, checkout, subagent or model change.

Installed local CLI reports `0.163.0-alpha.11`. Inspected only relevant supervisor
APIs, CLI help/config interfaces, isolated default feature flags and its locally
generated app-server JSON Schema. The shell feature is configurable, but neither
help nor typed schema proves that every native/deferred/nested tool can be denied
while only the fixed stdio bridge is exposed. `ToolsV2` describes web search;
generic configuration and dynamic-tool fields do not provide an exclusive tool
policy contract. MCP `--env` documents setting values, not clearing inherited
variables before server startup. These are evidence gaps, not a universal claim
that Codex lacks such capabilities. No guessed switch or declaration was accepted
as independent isolation proof.

One public synthetic sentinel test confirmed clean child-process environment
creation in ordinary subprocess code only. No actual Codex MCP child was started,
so its environment separation is explicitly **not verified**. Static interface
checks after initial help used temporary empty HOME/CODEX_HOME and a clean explicit
environment; no real credential or user config was read. Evidence and focused XML
are ignored under `.model-learner/control-transport-feasibility-v1/`.

Added a compact decision in `docs/SYNTHETIC_CONTAINER_SUPERVISION.md` identifying
the missing enforceable effective-tool allowlist and pre-exec environment-clearing
proof, plus the minimum trusted dispatcher/controller boundary. Only that guide
and this status changed. No bridge/source/test implementation, MCP server, model
session/request, authentication, provider/network call, denied browser, container,
runtime canary, candidate, W4B or W4A execution occurred. Existing 3-case runtime
acceptance remains historical fixed-synthetic evidence; no new runtime claim.

Focused installed tests: **88 passed**, zero skips (supervision and mocked offline
adapter selection); no new tests were needed for this decision-only edit. Ruff
lint/format passed for 237 files. Both public files pass working-byte privacy and
whitespace checks; read-only HEAD privacy guard passed 305 files, zero rejected.
Git HEAD/cached origin, branch and index remain unchanged. No executor staging,
commit, fetch or push; prior artifacts and runtime source/tests remain unchanged.

Stop at the capability gap. A subsequent implementation needs a supported offline
effective-tool/dispatch proof and actual stdio-launcher sentinel verification
before any bridge integration. Jev prepaid balance, effective TypeSafe-only/no-
fallback routing and provider output bound remain unestablished; no check was
repeated. W4A's 600-second semantics and observer-first provenance are unchanged.
Proposed coordinator commit: `docs: record blocked Codex bridge feasibility`.

## Finite launchd disposal verification — 2026-10-23

**Requested synthetic supervision increment complete: 3 runtime cases passed.**
No next milestone, general agent backend, model relay, pilot or W4A/W4B execution
was started. Continued the same five pending paths on `main` over
`40176882eb20788f895741067dda46d0b9228807`; no Git writes. Requested
`gpt-6.1-sol` / medium remains unverified by supported current-turn metadata.

One narrow diagnostic queried only the recorded failed-normal service label and
GUI domain. Service return code **113** classified as exact-service absence;
domain return code **0**, empty stderr, classified healthy. Both stdout streams
were discarded at source; stderr had a 4 KiB cap and two-second command limits.
Only return codes, byte counts and allowlisted categories were retained. This
confirms the later absent/healthy state; it does **not** establish that the earlier
failure was a particular launchd transition or domain failure. No old job was
recreated, differential probe repeated, or unrelated job/log inspected.

`unload` now uses a five-second monotonic verification deadline, at-most-one-second
commands and short 50 ms polls of only the exact lease-derived service. It checks
for existing absence first, otherwise bootouts that label once and treats continued
presence as transitional until the deadline. Success requires the complete
recognized absence message bound to this label and GUI UID, followed by a healthy
GUI domain with empty stderr. All service/domain/bootout stdout is discarded;
private stderr is capped at 4 KiB. Domain failure, unexpected stderr, command
timeout, cancellation, deadline expiry, command error and bootout failure produce
distinct non-secret error categories and retain state. Only the owned launchctl
CLI process is killed/reaped on timeout/cancellation/output overflow; reaping has
a separate one-second bound. The helper READY handshake, containment/cleanup,
receipt semantics, dependency pins and frozen W4A 600-second budget are unchanged.
The integration test's independent service query now uses the same bounded runner.

Final focused selection: **88 passed**, zero skips, 1.32 s (73 supervision unit
tests plus 15 existing mocked offline-adapter tests). New tests cover transient
presence then absence, already-absent idempotence, wrong label/UID, domain failure,
unknown stderr, timeout, cancellation, deadline expiry, state retention, stdout
discard, stderr overflow and owned CLI reaping. Ruff caught one long synthetic
test string and integration formatting; corrected, then repository lint/format
passed for **237 files**. No full-suite claim.

Exactly one authorized actual selection used `pytest -x`: **3 passed**, zero skips,
**11.30 s**, in the dedicated existing Colima profile. Normal completion retained
the exact 38-byte fixed output; timeout stopped on the deadline; abrupt owned
controller SIGKILL stopped on controller exit. Timeout/crash each observed three
guest PIDs including the detached-session descendant. All cases passed observed
input binding, stable post-stop output, stopped/absent container and observed
guest-process absence, valid bound receipt, recovery idempotence, controller
completion/reaping, exact launchd absence and temporary-state removal. Separate
read-only checks confirmed all three exact containers/services absent, healthy
GUI domain, valid receipts and normal helper-return diagnostics. No case was
retried; no canary, provider, credential, agent, candidate or pilot ran. These are
finite synthetic observations, not a hard deadline or general crash guarantee.

All prior supervision artifacts remain byte-identical, including 20 original
pinned files and three original failure receipt bindings. New ignored evidence
is `.model-learner/supervision-control-v1/disposal-repair-v1/`: diagnostic, focused
reports, runtime XML, three retained receipt/output/diagnostic bundles, final
absence observations and hash inventory. Same five public paths pass working-byte
privacy/whitespace; HEAD privacy guard passed **301 files, zero rejected**. Git
HEAD/cached origin, branch and index digest are unchanged. No stage/commit/push,
fetch, download, credentials access or security/privacy-setting change.

Stop here for coordinator review. Proposed commits: `feat: add fail-closed
synthetic container supervision` (module and both test files), then `docs: record
synthetic supervision acceptance and limits` (guide and status). Coordinator alone
stages, runs the staged privacy guard and commits with verified human attribution.
Jev, production model/auth relay, W4A/W4B real coding/containment/duration and final
trusted E2E remain open; moving to any of them requires a new instruction.

## Packaged-helper exception capture and repair — 2026-10-23

**Python helper readiness validated; full runtime acceptance still BLOCKED at
launchd disposal verification.** Continued the same five pending public paths on
`main` over `40176882eb20788f895741067dda46d0b9228807`. No differential probe was
repeated. Effective current-turn model/reasoning metadata remains unavailable;
requested `gpt-6.1-sol` / medium was not independently enforced or changed.

One owned ordinary subprocess ran the exact previously failed packaged
interpreter/bootstrap/helper sequence with a newly bound, validated no-worker
lease. Private stdout/stderr were captured with an 8 KiB cap per stream and a
ten-second timeout; the process exited 1 and was reaped. The actual exception was
`TypeError: 'select.kqueue' object does not support the context manager protocol`
at `watch`. No launchd job/container was created by this diagnostic; its temporary
state was removed. The metadata hypothesis was not supported: no `.dist-info` or
dependency change was made. Raw captures remain private ignored artifacts.

Repaired only the established queue-lifecycle error using `contextlib.closing`.
Regression coverage uses the real kqueue registration and verifies explicit close
in the fake test. The pinned bootstrap now writes one exclusive mode-0600,
at-most-512-byte `helper-diagnostic.json` containing only an allowlisted stage,
outcome and exception type. Error messages, traceback/source, paths and task
payload are excluded. Uncaught Python errors use this receipt; raw standard
streams remain discarded. Finalization retains the safe diagnostic when present.
Tests verify success/error/tamper stages, size/mode and private-message exclusion.
All dependency RECORD checks, digest pins, Pydantic validation and legacy lease
encoding remain intact. No downloads, credentials or privacy/security changes.

Exactly one corrected launchd no-worker preflight reached the **real READY**
lease/PID handshake and returned normally (`stage=ready`). Its immediate removal
check was inconclusive; later exact-service queries verified absence, then only
the matching temporary state was removed. This disposal observation is separate
from the original preflight result; no helper retry was used. No container query
or start occurred in either no-worker diagnostic/preflight.

With READY and disposal verified, executed exactly one `pytest -x` runtime
selection. **1 failed in 2.93 s**, stopping at the normal scenario's
`finalize -> unload -> temporary supervisor removal not verified`. Before that
failure, the real fixed normal worker had passed input/output binding, completed
stop reason, stable output, container/guest-process absence, cleanup confirmation,
recovery idempotence and controller exit assertions. This is partial evidence,
not a passing runtime test. Timeout and controller-crash cases were **not run**.
No runtime retry, old canary, model, provider, agent, candidate or pilot followed.
The test's failure cleanup later finalized successfully. Separately verified the
exact container and launchd service absent and original temporary job directory
removed; retained the valid receipt/output and separate disposal observation.
The immediate removal-check failure's cause remains unestablished; no removal
policy was weakened or repaired speculatively.

Final focused selection: **72 passed**, zero skips (57 supervision unit tests,
15 existing mocked offline-adapter tests). Repository Ruff lint/format passed for
237 files; same five public paths pass working-byte privacy/whitespace checks;
read-only HEAD privacy guard passed 301 files, zero rejected. All baseline
supervision evidence remains byte-identical, including the 20 explicitly pinned
files and three original failed runtime receipt bindings. New private evidence is
only `.model-learner/supervision-control-v1/packaged-repair-v1/`. Integration source
is unchanged. Git HEAD/cached origin, branch and index digest remain unchanged;
executor did not stage, commit, fetch or push. No full-suite claim.

Next separately authorized event: diagnose the exact launchd removal-verification
failure with bounded safe observations before another runtime acceptance run.
Timeout/controller-crash supervision, W4A/W4B and final trusted E2E remain open;
W4A's 600-second semantics and canonical measurement contracts are unchanged.
Coordinator-only proposed commit units: `feat: add fail-closed synthetic container
supervision` (module and both test files), then `docs: record supervision readiness
and disposal blocker` (guide and this status). Coordinator reviews/stages, runs the
staged privacy guard and uses verified human attribution; executor stops here.

## Differential Python startup diagnosis — 2026-10-23

**Bounded diagnosis complete; packaged helper readiness still BLOCKED.** Exactly
three new no-worker launchd probes used identical PATH-only environment, cwd `/`,
marker code and ten-second bounds. Resolved base Python succeeded both with
`-I -B -S -c` and `-I -B -c`; the repository venv entry point with `-I -B -S -c`
did not reach its marker. The previous venv `-I -B` failure was not rerun. One
one-second sample of only the blocked owned process showed Python initialization
at an open call. This distinguishes entry-point behavior, not the underlying OS
mechanism; no TCC denial, security exception or privacy-setting remedy is proven.
All three unique jobs, owned processes and temporary probe directories were removed.

The same pending supervision module now prepares a content-addressed helper bundle
under `~/.local/share/model-learner/supervision-helper-v1/`, using the resolved
existing base Python, `-I -B -S`, explicit cwd `/` and an explicit import directory.
It copies the static project import closure (15 modules) and the five existing
Pydantic dependencies, checking installed dependency RECORD hashes and all copied
bytes. No download, editable `.pth`, symlink-only venv copy or validation removal.
Manifest/interpreter/bootstrap digests bind the new lease runtime descriptor;
bootstrap verifies the manifest/files before imports. Legacy lease encoding omits
the new default fields, preserving old receipt digests. An explicit no-worker
lease purpose uses the actual kqueue registration and lease/PID ready handshake,
then returns before constructing Runtime or querying a container. It grants no
worker execution or containment acceptance.

Exactly **one final no-worker launchd preflight** used those actual production
arguments, the final source and a Pydantic-validated synthetic lease. It **failed**:
no ready acknowledgement within ten seconds, job exited code 1, no start-consumed
file. Exit stage/cause is unestablished because job stderr was discarded. No repeat,
additional sample, runtime suite, canary or container operation followed. Exact
job/process absence and temporary-state removal were verified. The verified host
code bundle remains installed; it is not an active job or a validated supervisor.

Evidence is ignored under
`.model-learner/supervision-control-v1/differential-v1/`: three probe observations,
one final-readiness bundle, initial and final focused reports. All 20 baseline
artifact files remain byte-identical; the three original failed runtime receipt
bindings still validate locally. No secrets, private sessions or credentials read.

Validation: first focused run **70 passed, 1 failed**, exposing intermediate
bundle directories created with insufficiently private modes; corrected to create
each directory explicitly mode 0700. Final focused selection **71 passed**, zero
skips (56 supervision unit tests and 15 existing mocked offline-adapter tests).
Repository Ruff lint and format passed (**237 files**); working-byte privacy and
whitespace checks passed on the same five pending public paths. Read-only HEAD
privacy guard passed **301 files, zero rejected**. No full-suite/runtime claim.
Integration test source is unchanged. Git HEAD/cached origin, branch and index
digest remain at the preceding checkpoint; no staging, commit, push or fetch.

Next separately authorized event: diagnose the packaged helper's exit code 1 with
a bounded owned-job diagnostic and retained stderr, before any further readiness
or container acceptance attempt. Crash/stop/receipt acceptance, W4A/W4B and final
trusted E2E remain open. No model, provider, credential relay, agent or pilot ran.

## Synthetic host supervision and receipt — 2026-10-23

**PARTIAL implementation; runtime arming and crash/stop acceptance BLOCKED.**
Stopped actual runtime attempts at the independent-ready invariant. No worker,
agent, arbitrary candidate, W4B pilot, model transport, credential, provider request
or payment occurred. Existing Colima setup and its previous 14 canaries were not
repeated. No real supervision guarantee or W4A/final-E2E completion is claimed.

Continued the same Model Learner checkout on `main`, initial HEAD/cached
`origin/main` `40176882eb20788f895741067dda46d0b9228807`, clean index/worktree, no
pre-existing public edits. Effective current-turn model/reasoning is unavailable
through this executor's supported metadata; requested `gpt-6.1-sol` / medium was
not independently enforced or changed. No new chat/checkout/subagent. Initial
index SHA-256 `c7a42eccfcc5648473a4c6123b313905b0e8d3421eff9caf637f9bfa4a7e95f6`
and final HEAD/branch/cached origin/index remain unchanged; no remote fetch.

Exactly five authored public paths, all unstaged/uncommitted:

| Path | Change |
| --- | --- |
| `src/model_learner/benchmark/supervision.py` | New fixed synthetic-only controller, durable lease, temporary per-user watcher, recovery/disposal and noncanonical bound receipt. |
| `tests/unit/test_supervision.py` | New 52 synthetic tests; no launchd, Docker, network, credentials or Git writes. |
| `tests/integration/test_supervision_runtime.py` | New explicit opt-in normal/deadline/owned-controller-kill acceptance; blocked at arming, no worker started. |
| `docs/SYNTHETIC_CONTAINER_SUPERVISION.md` | New implemented contract, trust/measurement limits and exact unsuccessful runtime evidence. |
| `STATUS.md` | This checkpoint only. |

Reuses existing `AcceptanceSpec`, `ExecutionConfiguration`, restricted container
arguments/policy and bounded-command helper. Those modules are unchanged. New
`synthetic-container-control/v1` is noncanonical, `synthetic_control_only`, with
fixed data and exactly two fixed worker modes; arbitrary commands/models/images/
endpoints are not accepted by the controller entry point. No ledger records,
canonical receipt book, estimator, eligibility or advisory integration. Controller
UUID is an alias, not a canonical Run. Model/provider are absent; canonical Attempt
latency is always null. W4B frozen task/checker/manifest, W4A 600-second budget,
acceptance identities and all production trust semantics are unchanged.

Exclusive/fsynced mode-0700 state precedes any start; an ownership reservation
precedes Docker create. The immutable ID, fixed target/config, input/helper digests,
controller identity and wall/monotonic observations bind the lease. Independent
launchd ready acknowledgement is mandatory before exclusive/fsynced start
consumption. Existing/ambiguous state is recovery-only; no automatic second start.
Ownership/policy checks, runtime-query success and guest-process observations are
required for cleanup claims. Receipt validates exact lease/output binding and
keeps unobserved input/output unknown. Failed cleanup/disposal retains state.
No input, code, auth or runtime socket is host-mounted into workers; only the
fixed synthetic driver/data and existing bounded tmpfs policy are configured.
Actual worker-side isolation/network checks did not run because arming failed.

Actual validation (installed environment, bytecode/plugin autoload/cache disabled):

- New marker-only per-user launchd preflight **passed**: unique label bootstrapped,
  marker appeared, bootout succeeded, job absent and preflight state removed.
  This proves only that simple independent jobs execute, not Python supervision.
- Final focused selection: **67 passed**, zero skips, 0.34 s: 52 new unit tests
  plus 15 existing mocked offline-adapter tests, checking reused policy interfaces.
  Command: `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
  .venv/bin/python -B -m pytest -q -p no:cacheprovider
  tests/unit/test_supervision.py tests/unit/test_benchmark_offline.py
  --junitxml=.model-learner/supervision-control-v1/focused-final.xml`.
- Actual opt-in new runtime selection: **3 failed**, zero skips, 13.65 s, all at
  `independent supervisor not armed`. Command used
  `MODEL_LEARNER_SUPERVISION_RUNTIME_TEST=1`, explicit ignored evidence directory,
  and `pytest -q -s -p no:cacheprovider tests/integration/test_supervision_runtime.py
  --junitxml=.model-learner/supervision-control-v1/runtime.xml` through supported
  escalation. All three created restricted containers, but **zero starts**;
  start-consumption files were absent. No controller-kill/normal/timeout worker
  acceptance was exercised. No further runtime trial after this failed gate.
- launchd reported each owned Python helper running without ready acknowledgement.
  One scoped one-second stack sample showed Python initialization waiting at an
  open call. It does not establish a TCC denial or approved remedy. No privacy/
  security change, interpreter relocation, runtime workaround or bypass attempted.
- External disposal verified all three exact container IDs absent, unloaded only
  their unique labels, verified helpers/jobs absent, then removed each temporary
  job directory. Original receipts/helper bytes were retained unchanged alongside
  separate disposal observations. No temporary supervisor or worker remains.
- Initial cleanup treated empty logs from unstarted workers as missing-input error.
  Final code restricts unknown-input handling to the never-started arming-failure
  case; an overbroad exemption caused one unit failure (44 passed), was narrowed,
  then passed. Final review added duplicate-key, process-evidence, hardlink and
  fsync-failure controls. Original failed runtime/unit XML remains retained.
- Repository Ruff lint/format (**237 files**), tracked/new whitespace and pure
  working-byte privacy passed on all **5 authored public files**, without exemptions.
  `GIT_OPTIONAL_LOCKS=0 python3 scripts/privacy_guard.py --tree HEAD` passed:
  **301 files, zero rejected** (published baseline only). No staged guard/staging.

No full-suite claim. Excluded: old real isolation/process/host-access probes,
W4B-P0, W6B/W7A demos/replay, models/Potion, Jev/account, downloads, unrelated
experiments and Git-mutating tests. New opt-in integration tests are not silently
converted into skips or a passing crash-control result. Default test collection
skips service execution unless explicitly enabled; future finite validation must
use fail-fast `pytest -x` after the blocked helper startup is resolved.

New ignored evidence is only `.model-learner/supervision-control-v1/`: initial
runtime/unit XML, final focused XML, and three `arming-failure-<owner>/` bundles
with original lease/helper/plist/receipt and external-disposal observations.
Original runtime profiles/artifacts and all other private data were preserved.
Initial read-only snapshot and one owned-helper diagnostic are under `/private/tmp/`.
No `.env.local` access, host configuration/security changes, downloads, permanent
login item, root daemon, staging/commit/push/merge or index/ref mutation.

Single next event: demonstrate the selected Python helper initializes and arms
under its temporary per-user launchd job through an approved execution path.
Then actual crash/stop/receipt acceptance still needs its bounded test; do not
launch a pilot based on unit tests or the marker-only preflight. Model/auth relay,
supervisor/VM loss, logout/reboot and hostile-code guarantees remain unestablished.
Jev, W4A/W4B real coding/containment/duration and final trusted E2E stay open.

Suggested small coherent coordinator commit units:
1. `feat: add fail-closed synthetic container supervision` — module and both tests.
2. `docs: record synthetic supervision contract and arming blocker` — guide/STATUS.

Coordinator alone reviews/stages, checks the active local hook, runs
`python3 scripts/privacy_guard.py --staged`, commits/pushes with verified human
attribution. Executor leaves all changes uncommitted and stops at this blocker.

## Jev official live-readiness review — 2026-10-23

**BLOCKED before paid dispatch; precise external-evidence stop.** Continued the
same registered Model Learner checkout/project
`5e9ee82f-ab79-435f-a8c9-8bb3c4b689d3`; no new chat/checkout. Initial `main`, HEAD and
cached `origin/main` were clean at `80781a4a3dfc8a93e2874943fa937df1685d56f3`,
preceded by `f4f5143d2f1af33735daca93f1481ac651c75958`. No pre-existing public edits.
Read-only inspection found both commit authors match `ckrfeng` and no recognized
AI coauthor/signoff trailers. No commit or authenticated push identity is asserted
for a future commit. Current-turn model/effort is not exposed to this executor's
supported metadata; the prior coordinator attestation applies to its named earlier
turn, not independently to this turn. No model selection/override was performed.

Reviewed current AGENTS, plan observation/inference/decision boundaries, J1/J2 docs,
readiness and offline transport source, plus targeted current official OpenRouter/
TypeSafe public documentation. [Current gate findings and source links](docs/J2_DECISIONS_READINESS.md#official-live-gate-review--2026-10-23)
record the new evidence: Decisions now documents a provider-routing object; the
provider guide documents `only` and disabling fallback. The model page lists Jev
1.14/TypeSafe and public pricing. Response usage/cost fields are documented.
These are documentation facts, not live route/account/charge verification.

Essential facts still missing: endpoint-specific enforceable conservative output
bound; actual selected credential/account/provider-route identity and policy;
current remaining prepaid/key limits and bounded single-request/total exposure;
reviewed secret-safe loading/transport. The existing local fake request has no
live routing fields, and local byte/usage rejection cannot enforce provider work.
Public documentation endpoints were browsed; one model-endpoints metadata fetch
was inaccessible through the tool. No paid inference, authenticated account GET,
credential use, retry, fallback/substitution, purchase or provider switch occurred.
No private input, source code or holdout was submitted.

`.env.local` metadata only: present, ignored, regular, nonsymlink, group/other mode
bits present. Contents/values were never read; ACL/effective access, key validity,
account identity and secure availability remain unknown. No exposure is asserted
from mode bits alone; file and permissions were preserved. No secrets requested
in chat. Account probes cannot substitute for the missing output guarantee.
The existing paid authorization is preserved: one attempt, no retries/substitution,
maximum $1 and lesser of remaining prepaid or $15 total. No further spending
permission requested, no automatic dispatch, no live marker consumed and no real
usage/cost receipt exists. Missing cost remains unknown, not zero.

Exactly two documentation files changed, all unstaged/uncommitted:

- `docs/J2_DECISIONS_READINESS.md`: append dated official evidence/gate table and
  specific next evidence; historical J1/J2 claims preserved in their time scope.
- `STATUS.md`: this checkpoint only.

No code, test, fixture, protocol/hash, default live refusal, advisory/utility trust,
estimator or evidence schema changes. No new mock abstraction or live client.
Published W4B-P0/W6B/W7A, historical experiments and the 204/85 completed test
selections were not repeated. For this documentation-only stop no pytest run was
needed; focused integration/paid validation remains unexecuted, not passed.
Required repository Ruff lint/format, whitespace and privacy checks passed;
exact results below. No staging/staged guard, index/ref mutation or Git write.

Validation: `.venv/bin/ruff check --no-cache .` passed;
`.venv/bin/ruff format --check --no-cache .` passed (**233 files**);
`GIT_OPTIONAL_LOCKS=0 git diff --check` passed;
`GIT_OPTIONAL_LOCKS=0 python3 scripts/privacy_guard.py --tree HEAD` passed
(**301 files, zero rejected**); pure working-byte path/content privacy and newline/
trailing-whitespace checks passed on both changed Markdown files without exemptions.
No new ignored repository artifacts; no ignored paths removed. Initial read-only
snapshot is `/private/tmp/jev-live-readiness-initial-state.json`; index SHA-256
`b49405fb964ae47334527a510878234967c624c2bca5ebcc2189d943933b6af3`
and HEAD/branch/cached origin remain unchanged. All unrelated/private files preserved.

Proposed single coherent commit: `docs: record Jev live-smoke evidence blockers`
(both paths). Latest human policy supersedes historical Desktop-only notes:
coordinator alone may stage/commit with Git CLI and push with GitHub CLI or
authenticated Git, verifying human `ckrfeng` attribution and no AI trailers.
Executor performs none of those actions. Stop here; obtain the named technical
evidence through secure operator/provider channels before any later dispatch.
Jev live smoke, W4A/W4B actual coding/containment/600-second gates and final trusted
E2E remain open. This review supplies no coding-agent utility evidence.

## Bounded Jev offline HTTP-envelope contract — 2026-10-23

**PASS for this offline transport/contract increment; live Jev remains BLOCKED.**
Continued the already-open existing Model Learner checkout; no new checkout or
chat was created. Supported project listing maps project
`5e9ee82f-ab79-435f-a8c9-8bb3c4b689d3` to this working directory. The executor could
not independently verify model/reasoning through its supported metadata/tools.
The coordinator independently verified `gpt-6.1-sol` with effort medium for turn
`01a1672f-ebfb-7ce2-a8bb-662493b2ede2` through narrowly scoped selected current-turn
local session `turn_context` metadata.
No model override, delegated coding agent or provider call was launched.

Initial branch `main`, HEAD and cached `origin/main`:
`485e2b3e02644ec09be12acdc38212dc1a7038d8`; index/worktree clean, no untracked public
work. Existing origin remains `https://github.com/ckrfeng/model-learner.git`.
Read-only inspection only; no live fetch. Initial index SHA-256
`9295d9c9734836139be83901af8e03227274e732889b8e56ed77c9f5bec472bb`
is retained outside the repository and unchanged. No pre-existing edits needed
preservation. Published W4B-P0/W6B/W7A and their evidence were not rerun.

Demonstrated missing gap: J1's fake checked status/redirect through caller arguments
and returned bare bytes; J2 had no explicit HTTP response metadata object to
exercise absent/duplicate media type, encoding/length conflicts or returned route
metadata before parsing. Added one deliberately narrow offline envelope seam,
reusing the existing frozen request, fake request/policy validation, durable mock
marker, typed answer parsing, budget checks and sanitized receipt choreography.
No HTTP/network implementation, credential loading or invented provider fields.
No official-provider research was needed: captured J1/J2 field evidence suffices
for offline fixtures; undocumented live routing/enforcement is still unresolved.

Exact changed paths, all unstaged/uncommitted:

| Path | Delivered change |
| --- | --- |
| `src/model_learner/understanding/decisions_transport.py` | New `ResponseFixture` / exact `MockHTTPTransport`; explicit bounded response metadata and one local exchange. |
| `src/model_learner/understanding/decisions_readiness.py` | Admit this second exact offline fake; add explicit fixture contract/evidence-class tags only to its receipts. Live refusal/readiness and legacy fake receipts unchanged. |
| `tests/unit/test_decisions_transport.py` | New 60 original synthetic DEVELOPMENT envelope and integration controls. |
| `docs/J2_DECISIONS_READINESS.md` | Document demonstrated gap, local dialect, reuse, reproduction and remaining gates. |
| `STATUS.md` | This checkpoint only. |

The new local dialect checks exact existing HTTPS origin/path, explicit integer
200 and false redirect state, bounded byte body, required JSON Content-Type,
case-insensitive duplicate/header shape controls, optional identity encoding and
matching decimal Content-Length. Alternate routes, redirects, missing/malformed
metadata, extra headers, unsupported/compressed bodies, malformed typed answers,
model/provider substitution and enabled fallback are refused without retry.
This restrictive fixture dialect is not a normative provider schema or proven
production transport. Response metadata and model/provider fields are simulated
declarations, not independently authenticated route evidence.

Actual offline E2E evidence: frozen public fictional `dev-01` input through J2's
durable mock marker, explicit envelope checks, existing wire/parser and sanitized
receipt. Success is `mocked_parsed`, `mode=mock_only`,
`evidence_class=synthetic_development_http_fixture`, zero paid POSTs, routing false,
actual billed cost null. Errors yield no prediction and preserve consumed marker.
No raw body/header/error prose enters receipts. New success/error receipts fail
Observation, Verification and AdvisoryInput validation; existing fictional outcome
inputs and complete abstaining advice remain byte/result-identical. No trust rule,
canonical outcome/learning, estimator, forecast or advisory code changed.

Validation using installed environment; no sync/install. Commands use
`PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B
-m pytest -q -p no:cacheprovider`:

- Focused: `tests/unit/test_decisions_transport.py`,
  `tests/unit/test_decisions_readiness.py`, `tests/unit/test_intent_offline.py`,
  `--junitxml=/private/tmp/jev-transport-focused.xml`: **204 passed**, zero skips,
  0.38 s (60 new + 144 existing). Secret/network APIs forbidden in the new
  integration control; only frozen manifest/input files are read for dispatch,
  never draft reference labels or holdout predictions.
- Relevant regressions: `tests/unit/test_advisory.py`,
  `tests/integration/test_advisory.py`, `tests/unit/test_learning.py`,
  `tests/unit/test_prospective.py`,
  `--junitxml=/private/tmp/jev-transport-regressions.xml`: **85 passed**, zero skips,
  2.32 s; model/Docker opt-in environment variables unset.
- `.venv/bin/ruff check --no-cache .` passed;
  `.venv/bin/ruff format --check --no-cache .` passed (**233 files**).
- `GIT_OPTIONAL_LOCKS=0 python3 scripts/privacy_guard.py --tree HEAD` passed:
  **299 files inspected, zero rejected**. This checks the published baseline,
  not the new working bytes. Pure non-staged path/content privacy and whitespace
  screening additionally passed all **5 changed public files**, without exemptions.
  `GIT_OPTIONAL_LOCKS=0 git diff --check` passed. No staged guard/staging.

Initial lint found six long test-source lines; formatting resolved them before
the first test run. No test failures occurred. No full-suite claim: Git-mutating
privacy/temp-repository tests, W4A probes, W4B-P0, W6B/W7A demos/replay, model/Potion,
Docker, historical experiments and live-provider/account checks were excluded.
No new ignored repository artifact; reports and initial read-only snapshot are
under `/private/tmp/jev-transport-*`. Existing ignored/private data was preserved,
with no ignored path added or removed. Final HEAD/branch/cached remote/index match
the initial state. Only the five listed paths changed; no unrelated edits.

No `.env.local`/secret read or use, DNS/socket/HTTP call, paid/provider request,
holdout classification, fallback/substitution execution, purchase/top-up/subscription,
security/runtime change or Git/index/ref mutation occurred. Optional sandbox
approval is independent of this offline classification increment. Existing
conditional later paid authorization remains preserved; no smoke here. Live gates
still require endpoint/provider and route/no-fallback enforcement, bounded output
and spend, secure credential transport, current prepaid/pricing/settlement evidence
and separately gated one-shot execution. The $1 / lesser-of-remaining-prepaid-or-$15
later boundary is not relaxed; no allowance size is assumed.

Suggested coherent nonempty Desktop commit units:

1. `feat: validate offline Decisions HTTP response envelopes` —
   `src/model_learner/understanding/decisions_transport.py`,
   `src/model_learner/understanding/decisions_readiness.py` and
   `tests/unit/test_decisions_transport.py` (implementation and 60 tests).
2. `docs: record offline Decisions transport contract and evidence` —
   `docs/J2_DECISIONS_READINESS.md` and `STATUS.md`.

Coordinator alone reviews/stages, runs `python3 scripts/privacy_guard.py --staged`,
commits through GitHub Desktop and separately pushes approved verified commits.
Executor stops here with changes uncommitted. Jev live evaluation, W4A/W4B actual
coding/containment/600-second gates and final real trusted E2E remain open; this
offline fixture increment completes none of those gates.

## W4B-P0 first observer-first pilot contract — 2026-10-22

**READY FOR HUMAN REVIEW for this offline subgate. W4B remains incomplete;
EXTERNAL_RUNTIME_UNAPPROVED blocks launch.** One synthetic data task, frozen start,
trusted data-only checker, versioned pre-run manifest and finite approval packet
are complete. No real execution, measured inference, subscription/paid call,
production history import, runtime implementation or successor increment occurred.

Project registration `5e9ee82f-ab79-435f-a8c9-8bb3c4b689d3` matches this checkout
via supported `list_projects`. Requested executor model/effort was `gpt-6.1-sol` /
medium; supported metadata does not expose the effective current-turn model or
reasoning, so neither is independently verified. No model override or delegated
agent was launched. Initial `main`, HEAD and cached `origin/main` all matched
`1aa916bb0708091b5dc94accb4ebda2e93f9d7a7`, origin
`https://github.com/ckrfeng/model-learner.git`; clean index/worktree and no untracked
public work. Live origin was not fetched. Initial index SHA-256
`2433a67ac1c3caddbd0815e0015d778d576b926ac8b4395068d362f6f390b7f4`
remains unchanged. No preexisting public edits needed preservation.

Exact authored inventory (all unstaged/uncommitted):

| Path | State / delivered behavior |
| --- | --- |
| `tests/fixtures/w4b_p0/v1/TASK.md` | New complete synthetic Signal Note configuration task v1; exactly one exercise. |
| `tests/fixtures/w4b_p0/v1/start/pyproject.toml` | New sole starting artifact; no solution or executable candidate code. |
| `scripts/check_w4b_p0.py` | New bounded regular-file/no-symlink TOML checker; exact semantics/preservation, deterministic nine-case JUnit and digests. |
| `tests/unit/test_w4b_p0.py` | New 46 offline controls, independently authored temporary reference, negatives and existing JUnit binding checks. |
| `docs/experiments/w4b_p0_v1.json` | New frozen hashes, acceptance IDs, source/config/resource proposals, chronology/API mapping and six pending decisions. |
| `docs/W4B_P0_APPROVAL.md` | New reviewable finite approval packet, trust/runtime gates and exact eventual handoff. |
| `STATUS.md` | This checkpoint only. |

Frozen instruction SHA-256:
`586cfc26363d4a43ff11f84a205eea826c6866fb5278e91b0694a472e07a250c`.
Start artifact SHA-256:
`c028ee621c2900049775d8b1114d6dff31d45c56c8a4984d8a3054e96f561f69`.
Checker SHA-256:
`73580780616176f2dc97443e7ab6e02afdb023cf56e6a92a124c8b0c8d8e2cae`.
The manifest tests verify these exact bytes and sole start-file membership.

Data acceptance `w4b-p0-signal-note-data/1` freezes nine exact IDs. Checker reads
only the selected artifact (8,192 bytes maximum), rejects observed symlink
components/nonregular files, malformed/duplicate TOML, wrong types, malformed or
conflicting requirements, omissions/extras and changed preserved fields. It never
imports/builds candidate code or runs commands. All report cases are pass/failure,
no skips; checker infrastructure failure remains unknown without complete evidence.
Operator-owned immutable parent directories and external independent control remain
preconditions, not security proven by parser/file checks. Hashes establish content
identity, not authentic execution, model identity or verifier independence.

Offline results with installed environment, bytecode/plugin autoload/pytest cache
disabled (no dependency installation):

- Final focused checker/manifest/binding/privacy controls: **46 passed**, zero
  skips, 0.21 s. Earlier 36/43-case runs also passed; review added bounded-depth,
  CLI/exclusive-report, tamper and TOML date/nonfinite/type controls before freeze.
- Exact reference: **9 passed / 0 failed / 0 skipped**; artifact SHA-256
  `a35b52314dd298a4f5ca2ae51097510b443cafd5b63eb9cc95eb65c011c66ec0`,
  report SHA-256 `4671384fc6d330e390ba6873bf52f2d2ef9315ffce1290b44552373e22c3b37f`.
- Incomplete start: **2 passed / 7 failed / 0 skipped**, as expected; report
  SHA-256 `f39f65f3a34f5eb1cd16756b24cf43841084372cc6317aeee842219a3f56ce52`.
  A manual reference check initially selected the system temporary-directory alias
  and correctly failed the no-symlink-parent rule; selecting its physical path
  passed. No boundary rule was relaxed.
- Existing compatibility selection: **341 passed**, zero skips, 26.54 s:
  `tests/unit/test_junit_verification.py`,
  `tests/integration/test_junit_verification.py`,
  `tests/integration/test_portable_evidence.py`,
  `tests/integration/test_execution_lifecycle.py`,
  `tests/integration/test_benchmark_receipts.py`,
  `tests/integration/test_external_handoff.py`, `tests/unit/test_prospective.py`,
  `tests/unit/test_learning.py`, `tests/unit/test_advisory.py`,
  `tests/integration/test_advisory.py`. Existing W6B covers P10 self-report
  ineligibility, P11 unknown telemetry/600-second exclusion, receipts, corrections,
  forecast scoring, duplicate learner accounting and later read-only advice.
- Repository Ruff lint and format passed (**231 files**); tracked/new whitespace
  and non-staged pure privacy screening passed on all **7 authored public files**,
  without exemptions. No staged guard: staging is prohibited.

Reports are outside the repository at `/private/tmp/w4bp0-focused.xml` and
`/private/tmp/w4bp0-compatibility.xml`; initial read-only state is retained at
`/private/tmp/w4bp0-initial-state.json`. Tests use disposable synthetic ledgers,
never real pilot Task/Run/forecast records or private historical ledgers. No
full-suite claim: Git-mutating privacy tests, W4A host/process/containment probes,
model/Potion, Docker, Jev and W7A demo/replay were excluded. The existing W6B
integration suite was exercised; W7A code was not changed or rerun.

No production storage/schema/migrations, estimator, forecast, eligibility,
W6A/W6B/W7A behavior or live package configuration changed. W4A and duration
**Option A remain `ResourceBudget(max_duration_seconds=600)`**, same acceptance
version. For this separate exercise the manifest compares a new canonical
600-second target (complete attributed Attempt latency required, presently absent)
and a distinct explicitly no-budget acceptance-only Task/target requiring human
approval. Recommend consideration of the latter for the smallest observer demo;
neither proposal is selected. Safety process time never becomes native latency.
Cost/tokens/model revision/billing/stop guarantees remain unknown, not zero.

Read-only installed CLI help confirms relevant interface options only; it emitted
a PATH-alias permission warning, with no escalation. No auth/config read, provider
availability check, runtime activation or containment re-probe. External environment
identity, candidate/credential/verifier isolation, tool/network policy, whole-boundary
stop, immutable handoff, trusted first receipts and actual configuration evidence
remain pending. Future proposal is exactly `gpt-6.1-sol`, medium, one attempt,
zero retries; subscription exposure and finite resource authorization are pending.
Dataset proposal explicitly separates actual real-on-synthetic execution from
preparation/benchmark/natural-work evidence and requires approval before use.

Final read-only state: same HEAD/branch/cached origin/index, only STATUS tracked
modified plus the six new public files above; all unstaged. No authored ignored
repository artifacts. One newly observed ignored Finder metadata file,
`tests/fixtures/.DS_Store`, was preserved without reading its contents; no ignored
paths disappeared. No unrelated work was changed. No Git writes, stage, commit,
push, merge, remote/ref/index change or security-policy modification performed.

Proposed nonempty GitHub Desktop groups (coordinator only):
1. `feat: prepare one data-only observer pilot contract` — task/start/checker/tests/
   manifest together.
2. `docs: record first pilot approval gates and offline evidence` — packet/STATUS.

Coordinator reviews/stages and runs `python3 scripts/privacy_guard.py --staged`
before any Desktop commit; push requires separate approved verification. Stop at
P0. Next action is human review of the six finite decisions in the packet, not
execution. Full W4B/W5/full W6/W7 remain incomplete; authorized external execution,
trusted independent outcome, actual receipt chronology, frozen prospective scoring,
eligible learner update and later read-only advice still need real evidence.

## W7A newcomer fictional offline demo/replay — 2026-10-22

**PASS for W7A offline usability and replay. Real working-v1 end-to-end
acceptance remains integration pending; full W7 and W4B/W5/full W6 incomplete.**
Stop at W7A; no next milestone or real execution started.

Reused `scripts/external_handoff_example.py` as the single public entry point:
no arguments now runs W6B and checks replay in disposable storage;
`--output-directory` retains a new directory and checks it;
`--replay-directory` independently reloads the retained fictional evidence.
Replay imports exact scoped bundles twice in temporary ledgers, checks intake,
execution-only membership, retained first/final receipts, actual artifact/JUnit
bindings, resolved eligibility/outcomes, original-cutoff forecast reconstruction,
checksums/scores and identical advice/summary. It never rewrites retained evidence
or recaptures receipts. Missing/changed checked evidence refuses with a nonzero
exit and sanitized error category. Existing output directories are refused.

Added 26 positive/negative checks in `tests/integration/test_offline_demo.py`,
including repeated read-only replay, missing/changed artifacts and metadata,
source/receipt/summary substitutions and a substituted forecast with a matching
local checksum. Added `docs/OFFLINE_DEMO.md` with purpose, prerequisites, simplest
command/expected result, retention/replay, inspected files, verified scope,
fictional provenance and real-evidence gaps; linked README and W6B runbook.

All original W6B fixture events/data remain fictional. The dataset's `real`
source-kind exercises real-contract APIs only in disposable storage. No real
model performance or coding-agent evidence is claimed. Checksums establish
content identity, not external authenticity; independently controlled external
execution/verifier, historical receipts, whole-boundary termination and resource
coverage are not established. No schema, migration, source-kind/receipt rules,
estimator, prospective policy, W6A calculations, duration Option A or W4A
600-second limit changed. No production source, dependencies, model assets,
launchers, sandboxes, watchdogs, governors, selectors or Jev components added.

Baseline HEAD `2492259b19878893c92688b1a494db5db81108ae`; index/worktree clean,
no pre-existing edits. Six changed public paths: the script, new replay tests,
new newcomer guide, README, W6B runbook and this STATUS. Everything remains
unstaged/uncommitted; no Git/index/ref mutation, push, network, credential access,
paid call, dependency installation or private-history access.

Validation (installed environment; bytecode, plugin autoload and pytest cache
disabled; model/Docker opt-ins unset):

- New replay acceptance: **26 passed**, 18.98 s.
- Focused W2/W3/W6A/W6B/receipt/prospective/learning selection including W7A:
  **301 passed**, 45.39 s.
- Broader safe offline selection: **1,302 passed, 7 existing opt-in skips**,
  101.94 s. Skips: six Potion asset checks and one Docker check.
- Final retained run and independent replay: identical JSON, exit 0;
  `.model-learner/w7a-final-v1/` contains the fictional evidence. Earlier
  `.model-learner/w7a-demo-v1/` is preserved from before final formatting and
  requires its original script bytes to replay (source digest intentionally pins
  the checkout). Pytest fixtures are disposable temporary files.
- Final Ruff lint/format (**227 files**) and whitespace passed. Working-byte
  privacy passed on all **6 public files and 17 generated fictional projections**,
  without exemptions; baseline HEAD privacy passed (**291 files, 0 rejected**).
  Retained advisory CLI/API JSON agrees. No staged guard invoked because staging
  is prohibited.

The broader selection excludes Git-mutating privacy tests and the existing
W4A containment/process/host-access diagnostics; this is not a full-suite claim.
Next step requires user direction; no successor work is authorized. Suggested
Conventional Commit summary: `feat: add inspectable fictional offline demo replay`.

## J2 bounded Decisions integration/readiness — 2026-10-22

**PARTIAL overall. Offline contract PASS; full contract PARTIAL; routing BLOCKED;
spending BLOCKED; live smoke BLOCKED. Zero paid POSTs, free GETs, network calls,
credential reads or live attempts. Stop at J2.**

Only the captured published examples from J1 were used; no contract discovery.
Conditional authorization and the user-confirmed OpenRouter spending limit are
recorded without assuming current funds or a hard per-request cap. Decisions
TypeSafe-only/no-fallback and output-limit enforcement remain undocumented.
Current pricing/settlement, remaining prepaid balance, enforceable exposure
strictly below $1, and a validated secret-safe live transport are unproven.
Consequently no credential access, GET preflight, live transport or paid POST was
necessary or permitted by the acceptance gates. No live one-shot marker was armed
or consumed. No top-up/purchase/subscription/alternative provider.

Added `understanding/decisions_readiness.py`, a pure offline packet writer,
focused tests and `docs/J2_DECISIONS_READINESS.md`. The packet validates the frozen
manifest/input hashes and selects only fictional development `dev-01`; it never
reads draft references. Exact request SHA-256 is pinned to
`f7a2a32a6aabb5fb7a8d85f1150309a9a13a93a19aadf05e5fc09b50c284035b`.
Changed model/questions/criteria refuse before dispatch. Separate protocol hashes
record required TypeSafe-only, fallback false, zero retries, one paid POST maximum,
4,096 input / 256 output token plans, strict <$1 exposure and overall $15 prepaid
ceiling. These remain local requirements, never invented provider wire controls.
`readiness()` cannot be enabled through caller booleans or numeric budget evidence;
`refuse_live()` always raises without network/credential access.

Mock-only rehearsal exclusively creates and file/directory-syncs a fixed mode-0600
marker before dispatch. Existing/partial/symlink markers refuse; sync failure,
timeout, malformed/mismatched responses and ambiguous attempts never permit retry.
This is a tested **mock** guard, not a deployed live-attempt safeguard. Sanitized
mock receipts retain UTC times, request/protocol/response hashes, typed predictions,
confidence and reported metadata/usage where valid; exception prose/raw responses
are omitted. Actual billed cost remains null and route verification false, even
with official example model/provider metadata. Missing/malformed cost stays unknown;
explicit reported zero is retained. J2 cap checks reject cost >=$1 and usage above
its 4,096/256 plan. No receipt becomes a verification or learner/advisory input.

The frozen J1 fixture/rubric/baseline bytes and all historical experiment evidence
remain unchanged. No holdout predictions, gold review, model training/download,
coding agent, W4B/W5/W7, canonical records, database or learner changes. Existing
J1 labels remain AI-authored drafts; Jev accuracy/calibration remain unmeasured.

Actual validation using the installed environment, Python bytecode and pytest
plugin autoload/cache disabled:

- Final J1 + J2 acceptance: **144 passed**, 0.32 s; includes request/parser,
  identity/routing/redirect controls inherited unchanged from J1, budget gates,
  frozen label-free selection, durable mock refusal, secret-free offline path and
  unchanged fictional canonical inputs / Beta-Bernoulli / full W6A advice.
- Relevant J1/J2, semantic/task-state/representation/understanding, conversation
  state, learning/prospective, W6A/W6B and receipt regressions: **474 passed,
  1 existing opt-in skip**, 24.00 s before the final request-digest pin. Final pin
  and its three substitution tests then passed in the 144-case acceptance above.
  Skipped: actual Potion relevance metrics, requiring explicit opt-in/model assets.
- Offline readiness writer passed; ignored readiness packet regenerated. No mock
  dispatch or live marker consumed by this writer.
- Repository Ruff lint/format, whitespace and non-staged privacy checks passed.
  One generated regression testcase name matched a credential pattern and was
  replaced by its digest in the new ignored XML before final privacy screening;
  result/counts are preserved. No credential file was accessed.
  Full suite, Git-mutating privacy/temporary-repository tests, containment/process
  diagnostics, historical coding experiments and live-provider checks were not run.
  No environment installation or dependency change.

Baseline and final `main` HEAD:
`20605ef064673ff6aa2cbae9b0fb768e13ef2e73`. Baseline index/worktree clean;
no pre-existing changes. Final index unchanged/empty; only tracked modification
is `STATUS.md`, with four new unstaged/untracked paths:

- `src/model_learner/understanding/decisions_readiness.py`
- `scripts/decisions_readiness_example.py`
- `tests/unit/test_decisions_readiness.py`
- `docs/J2_DECISIONS_READINESS.md`

New ignored receipts: `.model-learner/j2-readiness-v1/readiness.json`,
`acceptance.xml`, `regressions.xml`. Existing ignored J1/private artifacts preserved;
no secret file read, no policy exemptions, no staging/index/ref mutation, commit,
push, merge or publication. Non-staged privacy screening checks working bytes;
the staged guard was deliberately not invoked. Suggested later coherent commit:
`feat: add fail-closed Decisions readiness checks` (all five paths; imperative:
Add frozen development readiness checks and mock one-shot controls). User review
and any later resolution of the blocked evidence gates remain unstarted; no next
workstream is authorized by this delivery.

## J1 optional task-intent offline evaluation — 2026-10-22

**PARTIAL: supplied official Decisions examples implemented offline; live
routing/resource enforcement BLOCKED. Jev accuracy/calibration unmeasured.
Independent human gold review pending. Stop at J1.**

Delivered frozen primary-intent/executable-source questions and precise rubric,
six intent classes, deterministic baseline, 24 distinct newly authored fictional
cases (8 development / 16 holdout), strict parser, fake transport, metrics,
executable demo and sanitized ignored report. No holdout baseline/mock/provider
predictions were collected. Labels are authored drafts, **not human gold**.
Internal question/baseline/source/metric hashes, input hashes, manifest and splits
are unchanged by the official wire-format follow-up. Manifest SHA-256 remains
`31e5fe76d0306effdfe1ad7bba8318bc39c16207128ba8aeca3630e332d7a8c2`.

Inspected required instructions/status/design/README/prospective/advisory/handoff/
readiness/privacy guidance and existing task-state, semantic, configuration
identity, estimator/advisory, Potion and test interfaces. No existing Jev adapter
or usable task-intent baseline existed. Existing pinned Potion support remains
unchanged and unnecessary for the fixed-rule baseline; no weights/cache reads,
downloads, dependency additions or installation. No canonical Task/Run/Attempt/
Observation, SQLite, outcome/verification/eligibility, Beta-Bernoulli, A/B/C or
W6A calculation changes. Ordinary learning/advice do not import J1.

### Official example follow-up and exact current behavior

Initial delivery was deliberately local-only because no captured schema was
available and network was forbidden. After that delivery the coordinator supplied
literal Choice/Noul/Score request and response examples from the official
OpenRouter Jev guide, plus provider/model page identity evidence. Those inline
examples now drive `openrouter-decisions-published-examples/v2`; no page fetch,
HTTP/DNS/credential probe or live request occurred. The initial provisional
chat-style usage token mapping was corrected to the supplied Decisions fields.
The coordinator's earlier two free authenticated GETs were not repeated.

`fixture_request` now emits the demonstrated exact top-level fields `model`,
`state`, `questions` keyed by question ID. Choice uses `type`, `instructions`,
`criteria` object; Noul uses `type`, `instructions`; score control uses `criteria`
array. Full frozen rubric stays in instructions; all six Choice labels map to
concise rubric-consistent category descriptions. No case IDs, split, references, outcomes, source code, hidden tests,
local-schema markers, reasoning, invented provider or token fields are serialized.
Actual byte-level projection/substitution tests exercise this serializer.

Response parsing handles keyed `answers`: Choice `choice`/`probabilities`/
`confidence`, Noul `noul` probability, Score `score`/`legend`/`probabilities`/
`confidence`. Confidence is separate from category probability. Exact IDs/types/
labels/levels/shapes/ranges/distribution totals and weighted score are validated;
extra/missing/duplicate IDs/keys, unsupported reasoning, malformed JSON/UTF-8,
nesting >32, nonfinite or invalid numeric values reject. Local tolerance `1e-6`
is not asserted as officially documented. Score is a fictional parser control,
never an unlabeled difficulty or utility target.

Requested model `typesafe/jev-1.14` remains distinct from the demonstrated returned
`typesafe/jev-1.14-20261014`. Both exact identities are explicitly admitted; other
versions/providers reject. Reported provider `TypeSafe`, bounded generation ID,
usage input/output tokens and scalar cost are preserved. Effective backend
revision is never inferred from the slug. Deterministic mock metadata can remain
null; parsed fixtures never become live success, verified route or actual charges.
Missing/malformed usage/cost stays unknown; explicit zero stays zero; estimates
remain separate/null; no chat-completion token aliases or `X-Jev-*` accounting.

The examples and provider page support slug `typesafe`, but **do not establish
Decisions support/enforcement of `provider.only` or `allow_fallbacks`**. Required
policy is TypeSafe only / fallback false / zero retries, checked out of band by
the fake. No unsupported routing fields are serialized and no claim is made of
serialized provider enforcement. `serialize_decisions` refuses live use and no
HTTP transport exists. The single-use fake rejects target/path/method/status/
redirect/model/question/provider/fallback substitutions and repeat attempts.
Bytes, description, question and token-planning bounds are checked; reported
input/output/USD usage above local caps stops without retry. These checks are
**not hard provider USD/token enforcement**. The original contract's serialized
routing guarantee remains an explicitly incomplete acceptance item.

`readiness()` always fails closed. Supplied provider identity is recorded, while
endpoint route/fallback behavior, output enforcement, documented float tolerance,
credential/account/key limits, actual prepaid balance, exact pricing/billing,
enforceable <=$1 exposure and separate one-request authorization remain blocked.
Credential name only: `OPENROUTER_API_KEY`; no local secret contents or environment
secret was read. Existing prepaid funds only; no top-up/subscription/purchase.
A later approved smoke permits at most one POST, no retry/fallback/batch/expansion;
missing route/cost/settlement, timeout/error, substitution or cap violation stops.

The executable demo now uses published request/response shapes with fake answers
fixed independently of inputs/references; mock accuracy 1/8 and Brier 1/4 are
plumbing checks against draft references, **not Jev accuracy/calibration**.
It proves unchanged fictional canonical inputs, actual Beta-Bernoulli estimates
and full W6A advice (still abstaining), exporting a sanitized versioned ignored
report. No global integration/enablement or second learner. One possible future
human-review experiment labels exactly these 24 fictional cases blinded to
predictions, then records disagreements/new version before holdout collection;
**not started**. With 16 holdout cases eventual conclusions are exploratory.

### Coordinator criteria-review correction

Review found the v1 wire representation repeated Choice labels and numeric score
indices instead of defining the options. Corrected all six existing Choice options
using descriptions consistent with the original RUBRIC, preserving production
question IDs, labels, instructions and task semantics. The parser-only Score
control now describes the fill level of a fictional tank: empty, partially filled,
full, with a matching instruction and exact expected legend validation. Incorrect
or swapped legend descriptions reject even with valid keys/probabilities/score.
Unregistered criteria cannot silently fall back to label/index placeholders.

Only the wire representation advances to `openrouter-decisions-published-examples/v2`;
v1 definitions are preserved under ignored `criteria-wire-v1.json` and its version
is retained in source. `understanding/intent.py`, both frozen production questions,
RUBRIC, CODE_RUBRIC, original internal Score control, baseline and all three JSON
fixture/manifest files are byte-identical to the pre-review snapshot. No holdout
predictions, new labels, live route behavior or learning/advice changes.

Pre-existing edits at review start were the eight tracked follow-up files listed
below. This correction changes only `decisions_offline.py`, its unit test, this
STATUS and the J1 guide; the other four pre-existing edits are preserved unchanged.
No new public paths, staging, commit or push. Current readiness remains false;
provider filtering/fallback and enforceable resource controls still block live use.
Criteria review: **102 acceptance tests passed in 0.54 s**; the relevant
semantic/identity/forecast/eligibility/learner/W6A/W6B selection passed
**391 tests, zero skips, in 25.75 s**. Ruff lint/format, executable demo, whitespace
and non-staged privacy screening passed. The earlier broader result is retained
as pre-correction evidence; no Git-mutating/containment/live tests were run.
Exact review delta and frozen-file hash checks are recorded in ignored
`criteria-review-inventory.json`.

### Actual validation

| Check | Actual result |
| --- | --- |
| Criteria-review acceptance | **102 passed**, 0.54 s. |
| Criteria-review relevant regressions | **391 passed**, zero skips, 25.75 s; includes the acceptance cases. |
| Pre-criteria-review official-example/offline acceptance | **90 passed**, 0.20 s; all published typed shapes, actual serialization, usage/cost, bounds/cap stops, no network/credential access, metric arithmetic, privacy and learner/advisory isolation. |
| Broader permitted selection before the criteria correction | **1,222 passed, 7 existing opt-in skips**, 69.75 s; includes final routing packet, all cap controls and all 90 new acceptance tests. |
| Prior focused semantic task state / identity / forecast / eligibility / learner / W6A / W6B selection | **368 passed**, zero skips, 25.20 s at initial delivery; these modules also included in the broader selections. |
| Earlier bounded evidence | Initial acceptance **79 passed**; usage-field follow-up **80 passed**; first published-example acceptance **87 passed** and broader **1,219 passed, 7 skipped**, 65.94 s before final cap controls. |
| Executable demo | Passed; `.model-learner/j1-offline-v1/synthetic-report.json`, 8 development cases, no holdout predictions, zero paid requests. |
| Repository Ruff lint / format | Passed; **221 files** already formatted. |
| Whitespace / non-staged privacy | Passed on all 12 authored public paths, regenerated sanitized report and all 8 actual serialized development requests; no policy exemptions. |
| Staged privacy guard | Not run by executor: no staging authorized. Coordinator must review/stage and run the guard before each Desktop commit. |

Existing installed environment only; clean test process environment, bytecode,
pytest plugin autoload/cache disabled. Broad selection excludes
`tests/integration/test_privacy_guard.py` (55 Git-mutating cases including temporary
repos), `test_w4a_containment.py`, `test_w4a_process_boundaries.py` and
`test_benchmark_host_access.py` (9 prior containment/process diagnostics).
Seven existing skips: six opt-in Potion checks and one opt-in Docker check.
No full-suite/live-provider/model-weight/containment rerun claim. Initial hostile
nesting and two lint issues were fixed before initial final checks. No historic
private experiment, live agent or paid inference was run.

### Inventory and Git state

Original coordinator baseline: clean `main`, empty index, no pre-existing edits,
HEAD=cached `origin/main`=`9f507edb7c3c9d1124ad1c972ad37712848f83fa`.
The initial 12-path delivery was left uncommitted by this executor: README, STATUS,
J1 guide, demo, three intent source modules, four fixture files and test. During
follow-up the original delivery appeared as commits `d5803fa` / `a6f0786` outside
this executor. Read-only checks now show `main`, HEAD=cached `origin/main`=
`a6f0786e4c2b51f69f60a6d5c30aba124a81f949`, empty index, exactly eight modified
tracked follow-up files, no new/untracked/removed or unrelated public changes:

- `src/model_learner/understanding/decisions_offline.py`
- `src/model_learner/understanding/intent_evaluation.py`
- `scripts/intent_example.py`
- `tests/unit/test_intent_offline.py`
- `README.md`
- `STATUS.md`
- `docs/J1_OFFLINE_INTENT.md`
- `tests/fixtures/intent/README.md`

The three frozen JSON fixture files and `understanding/intent.py` remain unchanged.
Ignored outputs stay under `.model-learner/j1-offline-v1/`: initial/final inventories,
initial focused/broad JUnit, usage-field and official-example acceptance/regression
JUnit, regenerated sanitized synthetic report. Pytest fixtures use disposable
system temporary storage; Ruff may refresh its existing ignored cache. No prior
private artifacts or user data were read, modified or deleted. This executor
performed no staging/commits/pushes/merge/publication or index/ref/remote mutation;
read-only Git inspection disabled optional locks and filesystem monitor.

Suggested follow-up Desktop groups (source and tests together):

1. `fix: use published Decisions wire examples offline` — two changed source
   modules, demo and required acceptance test.
2. `docs: record Decisions evidence and routing blockers` — README, STATUS,
   J1 guide and fictional fixture README.

[Full use/limits/receipt packet](docs/J1_OFFLINE_INTENT.md). W1–W3, W4A offline
preparation and W6A/W6B remain as before; W4B/W5/full W6/W7 incomplete. External
approved environments own execution, isolation, independent verification and
termination. W4A coding/containment/600-second Option A gates are distinct;
no J1 classification/mock result counts as coding-agent evidence. Stop at J1.

## W6B external verified-evidence handoff — 2026-10-21

**PASS for bounded fictional offline handoff. Actual working-v1 end-to-end
acceptance remains integration pending; W4B launch remains BLOCKED.** Existing
production interfaces completed the required handoff without a reproduced missing
capability. Added only an executable fictional operator example, 42 integration
tests and a runbook. No production source, schema/migration, canonical model,
verification/receipt/eligibility policy, estimator, W6A calculation or benchmark
contract changed. Stop at W6B; no successor milestone is started.

Read-only preflight found `main`, HEAD and cached `origin/main` both
`a3964fca019a3636ccaf95a69f0d0d4f355e0998`, ahead/behind 0/0, empty index diff,
no tracked changes and no untracked/pre-existing edits. No fetch occurred.
Project catalog mapped Model Learner ID
`5e9ee82f-ab79-435f-a8c9-8bb3c4b689d3` to this repository; current-chat metadata
confirmed its working directory. Before any edits/tests, the coordinator confirmed
project membership and effective `gpt-6.1-sol` from current turn-context fields for
turn `01a15f24-e5a5-7fa2-89ba-2bd59dfaa577`. No private historical transcript was
inspected. This executor performed no staging, commits, pushes, index/ref changes,
subagents, dependency installation, actual agents, paid inference, network calls,
runtime setup or containment diagnostics.

Inspected AGENTS, current STATUS/design/readiness/prospective/advisory/benchmark-
receipt/containment/privacy guidance and the canonical models, storage, supported
Codex adapter/CLI, JUnit/file verification, assessment/resolution, real derivation,
Beta-Bernoulli, prospective and advisory interfaces and W2/W3/W6A integration tests.
The existing `scoped-evidence/v1`, `ReceiptBook`, disposable import, JUnit binding,
real resolver, forecast/freeze/score and advisory APIs already suffice. No new
adapter was justified; there is no manufactured failing production-gap assertion.

`scripts/external_handoff_example.py` first records three fictional Task contracts,
configuration, reviewed verifier-source digest and compatibility policy. Each
forecast and separate hash file is retained before its target execution. A
fictional producer supplies only execution metadata and stopped data bytes;
capture/import uses the actual Codex APIs. A serialized scoped bundle crosses
into a fresh receiver, with exact frozen-intake checks and current-clock first
receipts. Producer labels, verifications and receipt assertions are refused by
the **example's reviewed choreography**, not silently trusted.

A separate reviewed data-only fixture compares at most 65 bytes against its fixed
expected answer and generates a complete JUnit report without executing candidate
code. Existing JUnit verification binds exact artifact/report/Task/Run/acceptance;
the sidecar binds Verification to the full Attempt. Existing assessment and
derivation yield one eligible verified success and one eligible verified failure.
These are explicitly `synthetic-w6b-disposable-only` real-contract test records,
never measured model execution, personal learning data or relabeled benchmarks.

Calculated A/B/C forecasts are 1/2, then 2/3. The success scores Brier 1/4 and
log loss ln(2); the failure scores Brier 4/9 and log loss ln(3), independently
checked against the original frozen probabilities. Later Beta(2,2) has mean 1/2,
one success and one failure, unchanged by replay. W6A global/per-arm/A/B/C advice
has two eligible labels and mean 1/2, retains evidence references and abstains.
API and actual CLI JSON agree. Policy, scoped identities/joins/Attempt map,
cutoffs, evidence membership and forecasts reproduce after serialization and
disposable reconstruction. Advice preserves actual producer/receiver/forecast
file hashes. Costs, canonical latency, tokens and effective backend revisions
remain unknown.

Negative controls cover untrusted completion/producer reports, wrong or missing
artifact, report digest/Task/Run/acceptance mismatch, skipped/missing/malformed/
unsupported cases, conflicting native/requested model, every dependency type's
missing/late receipt, later correction, exact replay, paired target arm/unrelated/
future exclusions, incomplete/abandoned unknowns, unsupported non-null duration,
metadata privacy, read-only advice, invalid-before-write and refused partial live
merge. Existing W2/W3/W6A regressions retain their broader contract coverage.

Actual final validation with the already installed environment:

| Check | Result |
| --- | --- |
| New W6B acceptance | **42 passed**, 5.55 s; also included in both runs below. |
| Focused capture/verification/assessment/W2/W3/receipts/learner/prospective/W6A regressions | **404 passed**, zero skips, 25.28 s. |
| Broader permitted offline selection | **1,132 passed, 7 existing opt-in skips**, 69.04 s. |
| Executable retained operator example | Passed; `.model-learner/w6b-handoff-v1/operator-example/` contains the exact fictional workflow outputs. |
| Repository Ruff lint / format | Passed; **214 files checked** in the final check. |
| Whitespace and non-staged privacy | Passed on the four public changed files and generated sanitized scoped/advisory projections, without exemptions. |
| Staged privacy guard | Not run: executor may not stage. Coordinator runs it after exact Desktop review/staging. |

Tests use installed `.venv` Python with bytecode and plugin auto-loading disabled
and `-p no:cacheprovider`, and local Ruff `--no-cache`. Both regression commands
unset `MODEL_LEARNER_TEST_POTION_PATH` and `MODEL_LEARNER_OFFLINE_DOCKER_TEST`.
Broad selection excludes `tests/integration/test_privacy_guard.py` (55 cases
mutating Git/index/commits, including temporary repos), `test_w4a_containment.py`,
`test_w4a_process_boundaries.py` and `test_benchmark_host_access.py` (nine completed
containment/process diagnostics). Seven skips remain six opt-in Potion tests and
one opt-in Docker test. Existing trusted synthetic verifier/worker regressions
are included. No full-suite claim, model-weight load, external runtime probe or
actual container execution. Initial new test failures were fixture-only: a later
resolver cutoff used for historical reconstruction, reused observation identity,
and incorrect exclusion spelling; corrected against unchanged production rules.
Initial formatting/line-length issues were corrected before final checks.

Public before/after inventory: initially clean; modified tracked `STATUS.md` only;
new/untracked `scripts/external_handoff_example.py`,
`tests/integration/test_external_handoff.py`, `docs/EXTERNAL_EVIDENCE_HANDOFF.md`.
No unrelated changes existed or needed preservation. All four paths remain
uncommitted and unstaged. New ignored artifacts are confined to
`.model-learner/w6b-handoff-v1/`: focused/regression JUnit reports, privacy/inventory
records and `operator-example/` (intake/policy, two forecasts/hash files, per-run
producer/receiver SQLite, fictional data/capture/XML/bundles/receipt books, advisory
input/output and summary). Pytest's generated fixtures remain in disposable
system temporary storage. No earlier private/ignored directory was opened.

Proposed coherent nonempty GitHub Desktop groups, coordinator alone operates Git:

1. `test: demonstrate external verified evidence handoff` — executable example
   and its required integration tests together.
2. `docs: record external handoff readiness` — runbook and STATUS after checked
   behavior. No production-code commit is needed.

The [runbook/readiness matrix](docs/EXTERNAL_EVIDENCE_HANDOFF.md) maps P1–P12 and
N1–N14 and distinguishes declared, received, validated, independently verified
fixture and unknown claims. Canonical JUnit/bundle validation does not authenticate
independent external verifier control; a self-consistent forged report cannot be
detected from hashes and declarations alone. The positive trust root is the known
reviewed local fixture, and the example refuses producer verification authority.
It is not a production security boundary or approval for arbitrary external XML.
Live merge, general provenance/attestation and managed execution remain unsupported.

Retain Option A and W4A's exact 600-second budget. This separately identified
no-budget data fixture does not repair it; a non-null real-contract duration with
unknown latency remains ineligible (`budget_duration_unknown`), and benchmark
`budget_measurements_not_supported` remains intact. macOS bootstrap/Docker socket,
same-user isolation, protected-verifier, whole-tree stop and resource-coverage
findings are unchanged. Future real external execution needs separately approved
runtime, trust/verifier/termination guarantees and exact finite resources.
W1/W2/W3/W6A and bounded W6B offline work are complete; W4A real runs blocked;
W4B/W5/full W6/W7 incomplete. Predictive superiority and automatic model choice
are not required for working v1. No next milestone or real run is requested.

## W6A offline read-only configuration advisory — 2026-10-21

**PASS for W6A's bounded offline advisory. W4B launch remains BLOCKED.**
Delivered a functioning library/CLI using existing estimators and receipt-aware
real-contract resolution, with 44 fictional acceptance cases and an executable
three-configuration example. This does not complete W4B/W5, full W6 or W7, prove
predictive superiority, or authorize real execution. Stop at this increment.

Preflight confirmed this chat's Model Learner project ID
`5e9ee82f-ab79-435f-a8c9-8bb3c4b689d3`, clean `main`, HEAD and cached `origin/main`
both `bde6656da4f9b0b4e5e6482adcd5c1cf5c35a4a8`, empty index diff, no tracked
modifications or untracked files. No fetch occurred. The coordinator confirmed
the current turn's effective model `gpt-6.1-sol` before implementation; only
read-only preflight preceded that confirmation. No pre-existing or unrelated edits
needed preservation. No Git/index/ref mutation, subagent, installation, private
historical-data read, network call, paid inference or runtime probe occurred.

Existing interface inspection: `learn predict` provides a single configuration/
group prediction with declared-time real-ledger resolution. The existing pure
`forecast` already provides A/B/C with a frozen membership policy and target-Task
exclusion. Neither offers the requested multi-candidate receipt-input advisory.
Initial new acceptance collection failed with `ModuleNotFoundError` for the absent
advisory module before production edits. The implementation reuses those actual
estimators and `storage.evidence.resolve_bundle`; no underlying learning,
eligibility, domain, storage or security architecture was changed.

Public entry points:

- `model_learner.learn.advisory.advise(AdvisoryRequest, observations=(), bundles=())`.
- `model-learner learn advise --input-file INPUT.json`, using the versioned
  `AdvisoryInput` envelope and emitting `configuration-advisory/v1` JSON.
- `scripts/advisory_example.py`, with `--with-evidence` and `--input` options.

Six calculations are supported: fixed Beta(1,1), admitted global cumulative,
exact-configuration cumulative, exact-cell A, declared compatible-family B and
broad task-family C. Probabilities and conditional 95% posterior intervals come
from the unchanged existing implementations. Each retains exact target/source/
candidate/policy identities, eligible counts and source evidence references.
The explicit global comparator pools admitted arms; A/B/C preserve the existing
model/effort compatibility rules. All use the same cutoff, source universe,
acceptance and budget, excluding the target Task's runs and paired arms.

Real-contract input must be scoped receipt bundles; caller-asserted raw real rows
are rejected. Existing verification, assessment-head, persisted derivation and
Attempt-binding gates are revalidated in disposable SQLite, without modifying the
source. Null/late receipts remain unavailable despite old declared timestamps;
corrections cannot replace retained earlier advice. Missing receipt dependency
counts and resolution exclusions remain visible. Imported receipts do not attest
authentic historical time. Simulated rows explicitly use declared times only.
Source kinds/datasets never pool. Benchmark resolution is unsupported and yields
prior-only estimates with reasons; complete W4A.2 receipts do not upgrade labels
or budget coverage. The actual fictional 600-second budgeted exporter/receipt test
retains `budget_measurements_not_supported` and zero eligible evidence.

`abstain-only/v1` always leaves human choice explicit, including cold start and
unapproved decision-policy requests; probabilities/evidence remain visible.
No five-label threshold, ranking, selection authority or saved shadow decision was
invented. Known eligible-evidence cost/latency summaries retain coverage counts;
unavailable means, token measurements and effective backend revisions stay null.
Output omits task prose, arbitrary metadata, private locators and unrelated rows;
projected labels use a conservative public-identifier profile and still require
human review. CLI validation does not echo source payloads.

Exact public inventory, all left uncommitted:

| Path | State and scope |
| --- | --- |
| `src/model_learner/learn/advisory.py` | New narrow public request/input API and deterministic JSON projection. |
| `src/model_learner/commands/learning.py` | Modified; adds only the explicit-file `learn advise` command. |
| `tests/unit/test_advisory.py` | New synthetic contract/estimator/exclusion/missingness/privacy tests. |
| `tests/integration/test_advisory.py` | New receipt/correction/read-only/benchmark/CLI cases using reviewed fictional helpers. |
| `scripts/advisory_example.py` | New executable fictional cold-start/prior-evidence example. |
| `docs/CONFIGURATION_ADVISORY.md` | New input/output, predictor, availability, example and 18-case coverage guide. |
| `docs/REAL_DATA_READINESS.md` | Modified; appends consolidated five-decision real-execution register. |
| `STATUS.md` | Modified; this checkpoint only, historical evidence preserved. |

Actual validation with the already installed environment:

| Check | Result |
| --- | --- |
| W6A acceptance | **44 passed**, 2.13 s; all 18 requested case groups mapped in the guide. |
| Focused learning/prospective/assessment/receipt/W2/W3/CLI regressions | **281 passed**, zero skips, 17.76 s, including all new cases. |
| Broader offline repository selection | **1,090 passed, 7 existing opt-in skips**, 70.09 s. |
| Actual executable CLI examples | Cold and prior-evidence JSON each exactly equals the public API result; command help passed. |
| Repository Ruff lint / format | Passed; **211 files checked** in the final run. |
| Whitespace and non-staged privacy | Passed on all eight public changes; generated cold/prior advisory outputs pass pure privacy checks without exemptions. |
| Staged privacy guard | Not run because this executor may not stage; coordinator must run after exact Desktop review/staging. |

Both focused/broad invocations explicitly unset `MODEL_LEARNER_TEST_POTION_PATH`
and `MODEL_LEARNER_OFFLINE_DOCKER_TEST`. Broader checks exclude
`tests/integration/test_privacy_guard.py` (55 Git/index/commit-mutating cases),
`test_w4a_containment.py`, `test_w4a_process_boundaries.py` and
`test_benchmark_host_access.py` (nine completed containment/process diagnostics).
The seven skips remain six optional local Potion tests and one optional actual
Docker test. No model-weight load, container launch, historical experiment rerun
or unqualified full-suite claim. Ordinary trusted synthetic verifier regressions
are included. Checks use `.venv/bin/python -B -m pytest -q -p no:cacheprovider`
with bytecode and plugin auto-loading disabled, and local Ruff with `--no-cache`;
no dependency sync/download was necessary.

Initial expanded tests exposed fixture construction mistakes (a string replacing
an enum without validation, Task versus Run budget location, and absent explicit
reasoning effort in a reused benchmark fixture). Corrected only the new fixtures
against the actual contracts. Initial Ruff formatting/import/unused-import issues
were corrected. Final product tests and checks above passed without skips in W6A.

The executable example admits one fictional Low success and one High failure
from separate prior Tasks, with a third distinct lower-model arm. A/B/C means are
**2/3, 1/3, 1/2**; global is 1/2 with two labels; cold start is 1/2 for every
configuration. Conditional exact-cell intervals are approximately
[0.158114, 0.987421], [0.012579, 0.841886], [0.025, 0.975]. Cost, latency, tokens
and backend revisions are unknown. These are calculated synthetic quantities,
never measurements of actual Sol/Luna performance. Both cases abstain.

New ignored artifacts only under `.model-learner/w6a-advisory-v1/`:
`acceptance.xml`, `focused.xml`, `regressions.xml`, `cold-input.json`,
`cold-advisory.json`, `verified-input.json`, `verified-advisory.json`,
`privacy.json` and `inventory.json`. Disposable real-contract reconstruction,
fictional artifacts/reports and databases remain in pytest/system temporary
storage. No earlier ignored research/experiment directory was opened or changed.

Proposed coherent nonempty Desktop commit groups, coordinator alone operates Git:

1. `feat: add offline configuration advisory` — advisory API, CLI, both required
   test files and executable fictional example together.
2. `docs: document advisory and real execution decisions` — advisory guide,
   appended decision register and STATUS.

The [decision register](docs/REAL_DATA_READINESS.md#w6a-real-execution-decision-register--2026-10-21)
consolidates supported runtime, protected verifier, whole-tree termination,
duration and exact resource authorization, each with known evidence, smallest
option, next validation and what approval would authorize. Retain duration
**Option A** and the canonical 600-second budget. No budget adapter, Option B/C,
migration or weakening of missing-measurement exclusions occurred.
Smallest remaining work toward working v1 is a human-selected supported execution
backend and bounded protected-worker/whole-boundary termination design, followed
by separately authorized offline validation. Security/runtime/verifier/stop/resource
gates still block W4B; later real runs and API spending require their exact separate
authorizations. No next milestone is started.

## W4A.2 benchmark first-receipt provenance — 2026-10-21

**PASS for the bounded receipt-only increment. W4B launch remains BLOCKED.**
Added a source-revalidated, versioned benchmark receipt sidecar and 69 fictional
acceptance cases. Receipt coverage does not upgrade statistical eligibility,
verification, trusted historical time or execution security. The proposed target
remains exactly `ResourceBudget(max_duration_seconds=600)`; its existing
`budget_measurements_not_supported` exclusion survives. No canonical model,
SQLite migration, exporter/learner/forecast algorithm or duration policy changed.

Starting read-only inspection confirmed clean `main`, HEAD and cached
`origin/main` at `b9aa6512d0117ef2d17d865ee0ecbe4a719f8c75`, ahead/behind 0/0,
empty index diff and no tracked/untracked edits. No fetch was performed. There
were no pre-existing or unrelated edits to preserve. Exact index-byte SHA-256
was retained before edits and checked unchanged at handoff. Coordinator remains
the only operator for Desktop staging, mandatory staged guard, commits and pushes.

Before production edits, the supported synthetic benchmark exporter produced a
verified success under a declared 600-second Run budget, still ineligible. An
assertion requiring first-receipt metadata failed (one expected failure), proving
the export lacked dependency first-receipt states. Actual report/text:
`.model-learner/w4a2-receipts-v1/gap-before.{xml,txt}`. It creates fictional Task,
configuration, Run, Attempt, frozen criterion, complete synthetic JUnit binding and
assessment in disposable storage. Report-input validity is tested; no model or
new candidate acceptance process was launched by these new receipt fixtures.

Delivered public paths, all uncommitted:

| Path | Change |
| --- | --- |
| `src/model_learner/benchmark/receipts.py` | New exact-source digest/identity bundle, local first-receipt book and cutoff availability audit. |
| `tests/integration/test_benchmark_receipts.py` | New 69 cases covering A–O and R1–R12 boundaries with fictional evidence only. |
| `tests/integration/test_benchmark_evidence.py` | Existing synthetic helper gains optional budget/stop-reason arguments; defaults preserved. |
| `docs/BENCHMARK_RECEIPTS.md` | New sidecar/API schema, acceptance mapping, limits and duration options A/B/C decision comparison. |
| `STATUS.md` | This checkpoint; previous evidence retained. |

`benchmark_receipt_bundle` revalidates a retained export through the unchanged
source exporter and containment gate, then hashes exact relevant source records.
The bundle retains benchmark/dataset/fixture/version, original Task/Run/Attempt/
Outcome/Observation/configuration/acceptance identities, separately named source
times, safe associations, supersession ancestry and artifact/report digest
references. It omits prose, raw events, hidden tests, candidate/report contents,
private filesystem locators and unrelated records. Exact canonical source hashes
are distinct from the sanitized bundle hash; neither proves authenticity.

`BenchmarkReceiptBook.capture` returns a new book, reads only the current receiver
clock, preserves identical captures and rejects conflicting identity/digest content
atomically. No backdating parameter exists. `as_of` requires every record and
export binding to have a non-null receipt and source times at/before cutoff.
Missing/null/late receipts across all 13 dependency kinds and future source times
fail closed. JSON reload/replay preserves membership, digests, exclusions, unknowns
and counts. A later correction receives its own time and cannot alter the earlier
bundle's historical availability. The adapter audits exact snapshots; it does not
select a current assessment head, fall back to older success or emit learner rows.

Limitations remain explicit: one quiescent finalized benchmark Run/target per book;
no live/multi-writer merge or initial prospective scope capture; verification has
no explicit canonical Attempt link; resource coverage, native latency, charges and
unknown configuration versions remain unavailable. `fully_available` means receipt
coverage for the declared bundle, not proof of those unsupported associations.
Replay must use the retained exact export: a newly timestamped export with the
same immutable Observation ID is conflicting content and is rejected. Imported
receipts are local declarations, not external timestamp attestations. No REAL-only
W2 resolver or fake real-source wrapper is used. No new canonical IDs are invented.

Actual final validation with the installed environment:

| Check | Result |
| --- | --- |
| New acceptance cases | **69 passed**, included in both final runs below. |
| Focused benchmark/W2/W3, domain/budget, assessment, JUnit, learner and prospective regressions | **360 passed**, zero skips, 21.00 s. |
| Broader offline repository selection | **1,046 passed, 7 existing opt-in skips**, 63.64 s. |
| Ruff lint / format | Passed repository-wide; **206 files formatted**. |
| Git whitespace / new-file whitespace | Passed. |
| Non-staged privacy screening | All five changed public files passed pure path/content checks without exemptions; generated sanitized bundle also passes in the acceptance test. |
| Staged guard | Not run: staging is prohibited here. Coordinator must run after reviewed Desktop staging. |

The broad selection excludes `tests/integration/test_privacy_guard.py` (55 tests
that mutate Git/index/commits), `test_w4a_containment.py`,
`test_w4a_process_boundaries.py` and `test_benchmark_host_access.py` (nine completed
containment/process diagnostics not rerun). Six skipped tests require an explicit
local Potion bundle; one requires an explicitly opted-in Docker experiment.
Both opt-in environment variables were unset. No full-suite claim, runtime backend
probe/retry, Docker/image operation, model execution or historical experiment rerun.
Existing regression tests run their ordinary trusted synthetic acceptance fixtures.

Exact broad command (focused path selection recorded in the report inventory):

```sh
env -u MODEL_LEARNER_TEST_POTION_PATH -u MODEL_LEARNER_OFFLINE_DOCKER_TEST \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  --ignore=tests/integration/test_privacy_guard.py \
  --ignore=tests/integration/test_w4a_containment.py \
  --ignore=tests/integration/test_w4a_process_boundaries.py \
  --ignore=tests/integration/test_benchmark_host_access.py \
  --junitxml=.model-learner/w4a2-receipts-v1/regressions.xml
.venv/bin/ruff check --no-cache .
.venv/bin/ruff format --check --no-cache .
git diff --check
```

Initial implementation test exposed a bare fixture SHA-256 versus prefixed-hash
mismatch (one failure); fixed against the actual exporter interface. Initial Ruff
found import order, two ambiguous local names and line length; all corrected.
Initial reports were preserved. Work paused on the human model correction; before
resuming any edits/tests, the specifically authorized current-chat metadata check
confirmed effective model `gpt-6.1-sol` for turn
`01a15ede-68a1-7830-a6f4-5e16df786904`. Only model/turn_id fields were read; no
conversation content or other logs were inspected. No subagent was used.

New ignored output only under `.model-learner/w4a2-receipts-v1/`:
`initial-state.json`, `gap-before.xml`, `gap-before.txt`, `acceptance-initial.xml`,
`acceptance-second.xml`, `acceptance-third.xml`, `focused-final.xml`,
`focused-final.txt`, `regressions.xml`, `regressions.txt`, `validation.json` and
`inventory.json` (manifest excludes itself). Disposable databases/captures/reports
remain in pytest temporary storage. No historical ignored evidence was opened.
No private fixture was added or privacy policy changed.

Proposed nonempty GitHub Desktop groups; coordinator alone reviews/stages/guards:

1. `feat: record benchmark evidence first receipts` — receipt source, new acceptance
   tests and the existing synthetic helper's optional budget/stop parameters.
2. `docs: document benchmark receipts and duration decision` — operator document
   and STATUS.

Recommend duration **Option A**, retaining current canonical semantics and missing
measurement exclusion. B would require an explicitly versioned process-elapsed
benchmark target with proven whole-tree execution/termination/clock coverage; C
would require a different prospectively approved statistical target. Neither was
implemented or selected as W4A policy. No latency fabrication, budget nulling,
source relabeling, token-to-charge conversion or timeout-to-failure conversion.

Stop at W4A.2. Smallest next action: human review of the duration/coverage target
and supported containment/verifier/process-tree boundary. Agent isolation,
untrusted-verifier isolation, reliable descendant stop and the enforceable
600-second ceiling remain blocked before W4B. No W4B/W5, measured coding agent,
paid inference, install, security change, staging, commit, push or publication.

## W4A.1 offline containment and watchdog readiness — 2026-10-21

**PARTIAL engineering result; W4B launch remains BLOCKED.** Completed the bounded
offline investigation and reproducible synthetic diagnostics. No production
watchdog was added because an escaped descendant demonstrably survives a group
stop. No production/schema/estimator/eligibility changes, frozen-contract edits,
agent or paid execution, private historical evidence access, dependencies/images,
privilege changes, staging, commits, pushes or W4A.2 work occurred.

W4A commit gate confirmed: coordinator attests GitHub Desktop commits/pushes
`72bcab1a59a430ac8eb16c989254c46356f1c716` and
`762aceb3424ea7913c8a01a16637a4053e530cf3`. Read-only initial inspection found
`main`, HEAD and cached `origin/main` at the latter, ahead/behind 0/0, all six
reviewed paths committed, no staged/unstaged/untracked changes. No live remote
fetch was performed. No pre-existing or unrelated edits needed preservation.
Chat working directory matches registered Model Learner project
`5e9ee82f-ab79-435f-a8c9-8bb3c4b689d3`; default model settings were preserved.

Delivered only these public changes, all left uncommitted:

| Path | Change |
| --- | --- |
| `tests/integration/test_w4a_containment.py` | New two-case fictional seven-category filesystem/descendant negative control and unchanged real-gate regression. |
| `tests/integration/test_w4a_process_boundaries.py` | New six-case finite subprocess diagnostics: normal exit, direct-child timeout, surviving descendant, group membership/escape, independent control and duplicate root cleanup. |
| `docs/W4A_CONTAINMENT.md` | New backend inventory, C1–C14 and W1–W10 evidence/unsupported cases, verifier boundary and read-only budget/receipt assessment. |
| `STATUS.md` | This checkpoint only; previous evidence preserved. |

Actual host is macOS 26.6.2 arm64 / Python 3.12.14. One existing macOS probe again
failed bootstrap with exit 71; denial results remain UNPROVEN. Docker CLI exists
but its supported Desktop socket is absent. Default diagnostic returns
`image_approval_required`; fixed-image availability check stops at
`docker_desktop_socket_missing` before daemon/image/container/network operations.
Image availability is unknown. No podman/bwrap/firejail/limactl/colima on PATH.
Same-user Python `-I` reads all seven fictional external canaries, follows symlink
and traversal, writes outside, and permits a child to read outside. Network and
integration/privilege denial were not tested without a supported isolated facility.

The frozen verifier imports candidate Python into the process holding its oracle.
No arbitrary candidate was run there. A separately restricted worker and trusted
driver/report writer remain required; read-only hidden files do not suffice.

Existing `_bounded` stops only its direct child: an authored descendant survives
the timeout. Group SIGKILL stops an in-group SIGTERM-ignoring child, but a child
that creates a new session survives. A second signal to the empty original group
receives EPERM on this host. The initial test exposed that error (7 passed, 1
failed); final diagnostics retain it explicitly without calling it cleanup.
All synthetic children are finite; direct children were reaped and known child
PIDs were observed absent after cleanup. No unrelated processes were signaled.
This is not an enforceable watchdog. Cancellation receipts, arbitrary descendant
ownership, controller-crash handling and the hard 600-second ceiling remain
unsupported. Final measured local normal/timeout intervals were 0.015004625 /
0.402371667 seconds (0.4-second test deadline); actual monotonic start/stop values
are in ignored JUnit properties. These are not native inference latency.

Read-only contract finding: `ResourceBudget` has no duration-basis field; ordinary
observations compare duration to complete attributed attempt latency. Benchmark
export excludes every non-null budget with `budget_measurements_not_supported`.
W2 replay/receipt resolution requires the real-data contract and cannot be used
unchanged for benchmark rows. A receipt-only benchmark sidecar appears feasible
without canonical schema changes, retaining ineligibility, but full 600-second
eligibility needs an explicit duration/coverage policy decision first. No nulling
of budgets, source-kind relabeling, fabricated latency or timeout failure label.
Exact source boundaries and required receipt fields are in the operator document.

| Readiness area | Verdict |
| --- | --- |
| Agent containment | **BLOCKED**; same-user control FAIL, supported denials UNPROVEN. |
| Untrusted-verifier isolation | **BLOCKED**; separate worker boundary absent. |
| Process-tree watchdog | **BLOCKED**; actual descendant escape, no safe utility delivered. |
| Benchmark budget/receipt adapter | **BLOCKED** for full eligibility; receipt-only extension plausible but unimplemented. |

Validation with the installed environment (no dependency sync): final new
diagnostics **8 passed in 4.01 s**, zero skips; existing focused regressions
**418 passed, one existing opt-in Docker skip in 17.96 s**. Includes all nine W4A
public checks and W2/W3, containment, capture, JUnit, assessment, observation and
learning regressions. No Git-policy tests (55 in the prior checkpoint), actual
Docker test, Potion/model tests or historical experiments were run. No full-suite
claim. All six protected plus two public starting hashes match the frozen W4A
manifest; preparation source, acceptance IDs and hashes were not rewritten.

Commands for the new checks:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider -o junit_family=xunit1 \
  tests/integration/test_w4a_containment.py \
  tests/integration/test_w4a_process_boundaries.py
.venv/bin/ruff check --no-cache .
.venv/bin/ruff format --check --no-cache .
git diff --check
```

The 418-case selection is the preceding W4A checkpoint's exact 299-case list plus
`tests/unit/test_benchmark*.py` and `tests/integration/test_benchmark*.py`, with
both MODEL_LEARNER_TEST_POTION_PATH and MODEL_LEARNER_OFFLINE_DOCKER_TEST unset.
Repository Ruff lint/format passed (203 files); whitespace checks cover tracked
diff and all new files. Non-staged pure `path_reasons`/`content_reasons` screening
passed all four changed public files without exceptions. An initial screening
driver import failed before inspection; corrected import succeeded. The staged
guard was not run because staging is prohibited. Coordinator must run it after
reviewed Desktop staging. Index-byte SHA-256, HEAD/branch and cached remote were
checked unchanged; no Git mutation was performed.

New ignored artifacts only: `.model-learner/w4a-containment-probes-v1/backend.json`,
`initial_index.sha256`, `focused-initial.xml`, `focused-final.xml`,
`focused-receipts.xml`, `regressions.xml`. Disposable pytest canaries/process files
use temporary storage. No other ignored Model Learner data was enumerated.
Final public inventory: STATUS modified, the three new files above untracked,
index diff empty; no unrelated edits.

Proposed nonempty GitHub Desktop groups (coordinator alone reviews/stages/guards):
1. `test: characterize W4A containment and process-tree gaps` — both new test files.
2. `docs: record W4A containment blockers and budget boundaries` — operator document
   and STATUS. Tests remain independently useful with the existing production code.

Stop here. Smallest next bounded milestone: separately authorized W4A.2 benchmark
receipt/measurement-contract work, with a duration policy decision before budget
eligibility implementation. Supported OS containment and verifier isolation need
their own decision before W4B; no launch or allowance approval is implied.

## W4A discriminating pilot preparation — 2026-10-21

**PARTIAL: concrete offline task package validated; real launch remains blocked.**
Prepared only W4A. No W4B/W5, measured coding agent, additional model, subagent,
paid inference, network probe, install, private historical evidence access, staging,
commit, push, branch/ref change or production/schema/estimator change occurred.
Synthetic regression databases are disposable; no persistent experiment ledger
was opened or written. Existing historical checkpoints below remain unchanged.

W3 gate verified before writes: `main`, HEAD and cached `origin/main` both
`386d54686009eb21ca5c200294c906f58f2b7793`, with source/test predecessor
`98d568a01ca9de10f3bb6bb678c9dc372b72f32b`. Both expected path groups and W3 source/
tests were present. The supplied coordinator attestation confirms GitHub Desktop
commits and push. No fetch or independent live remote verification was performed.
Initial staged state, tracked modifications and untracked inventory were empty;
no pre-existing edits required preservation. Existing executable local hook retained.

Selected one newly constructed **Transactional Dependency Graph Planner** task.
Medium-to-hard is a pre-outcome assessment based on transactional graph invariants,
deterministic topological order, rollback and scale, not a learned difficulty or
model-performance finding. The complete frozen contract specifies the exact Python
API, inputs, errors, idempotence, final-batch cycle semantics, state isolation,
performance thresholds and success definition. Starter source is intentionally
unimplemented, with no unrelated planted bugs. Only two files enter each arm.

Delivered public files (exact inventory):

| Path | Initial | Final |
| --- | --- | --- |
| `tests/fixtures/w4a/TASK.md` | Absent | New frozen candidate contract and provenance |
| `tests/fixtures/w4a/planner.py` | Absent | New incomplete synthetic starter |
| `tests/unit/test_w4a_preparation.py` | Absent | New nine manifest/policy checks |
| `docs/experiments/w4a_preparation.json` | Absent | New versioned preparation manifest |
| `docs/W4A_PREPARATION.md` | Absent | New operator packet, commands and evidence |
| `STATUS.md` | Tracked, clean | This checkpoint prepended |

All five new public files remain untracked and STATUS modified; index remains
empty. No other public file changes. Proposed GitHub Desktop groups:

1. `test: prepare transactional graph pilot contract and checks` — TASK.md,
   planner.py, test_w4a_preparation.py, w4a_preparation.json (full paths above).
2. `docs: record W4A preparation evidence and launch blockers` —
   docs/W4A_PREPARATION.md and STATUS.md.

Coordinator alone reviews/stages, runs the mandatory staged privacy guard, and
creates any approved commits. No push authorization is granted by this work.

New ignored package: `.model-learner/w4a-preparation-v1/` only. Its `inventory.json`
lists every retained file/digest, excluding itself. It includes six protected
Python files (independent acceptance, immutable permutation oracle, heap-based
trusted reference, oracle anchors, preparation controls and restricted verifier),
three identical two-file starting workspaces, protected hash/test-ID manifest,
seven synthetic canaries, and local XML/JSON/text validation reports. Earlier
private evidence was not enumerated or read. Protected files never enter starting
snapshots, but same-user read protection is NOT established by ignored paths/0700.

Acceptance checks: 15 fixed JUnit identities; exact API and edge semantics;
64 exhaustive three-node graphs; 2,400 seeded transactional batches; rollback,
replay, metamorphic and state/input-isolation checks; 8,000-node chain and a
2,000-node/24,000-edge DAG. Oracle independently enumerates permutations and has
analytic anchors (including 25 labeled three-node DAGs). All authoring/review was
by this executor; no independent person/model review is claimed.

Actual final validation using the already installed environment:

| Check | Actual result |
| --- | --- |
| Frozen reference acceptance | **15 passed**, no skips, complete exact-identity JUnit report. |
| Frozen starter acceptance | **15 expected failures**, zero passes/skips; complete report proves starter does not solve the task. |
| Protected acceptance + oracle + preparation controls | **26 passed**, 0.93 s; 15 acceptance, three oracle and eight controls. |
| Public manifest/configuration/forecast checks | **9 passed**, also included in focused regression below. |
| Focused existing workflow regression | **299 passed**, no skips, 19.07 s; includes all 35 W3 and 39 W2 cases. |
| Reference final CPU trials | 0.199302, 0.195065, 0.187644 seconds; median 0.195065; all below the 2-second reference calibration threshold. Host evidence only. |
| Starting-state integrity | Three copies match both frozen file hashes and exact two-file membership. Protected hashes and all 15 required IDs preserved. |
| Tamper/report controls | Altered starter/reference/oracle/acceptance rejected before execution; arbitrary submissions not accepted by preparation runner; missing/skipped/malformed reports cannot satisfy contract. |
| Actual macOS isolation probe | **UNAVAILABLE**: sandbox bootstrap failed, exit 71; read/write/symlink/descendant denial unproven, not a successful denial. |
| Same-user synthetic read control | All seven synthetic canaries readable from candidate directory; folder separation alone fails the boundary requirement. |
| Existing real collection gate | Refuses collection; unchanged. Offline Docker diagnostic says image approval required; no container launched. |
| Ruff lint / format | Repository-wide passed (200 files formatted); six ignored protected Python files separately passed. |
| Whitespace / non-staged privacy | All six public files passed pure path/content/secret screening without exemptions and explicit whitespace checks. |
| Staged guard | Not run: staging forbidden. Coordinator must run after reviewed staging. |

The first trusted reference+oracle run passed 18 tests. An initial minimal runner
misclassified the failing starter because the traceback included the timeout
message in source text; fixed to inspect actual JUnit failure messages, then
validated the final complete failure. Initial reports are preserved, not replaced.
Private Ruff issues were fixed before final manifest freeze and checks. No false
initial-green claim; final results above apply to the final frozen sources.

Exact final commands (from repository root; environment prevents bytecode/cache
writes and third-party pytest plugin auto-loading):

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  .model-learner/w4a-preparation-v1/protected/verify_preparation.py \
  reference --report-name reference-frozen
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B \
  .model-learner/w4a-preparation-v1/protected/verify_preparation.py \
  starter --report-name starter-frozen
W4A_CANDIDATE="$PWD/.model-learner/w4a-preparation-v1/protected/reference.py" \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv/bin/python -B -m pytest -q -c /dev/null \
  --rootdir=.model-learner/w4a-preparation-v1/protected -p no:cacheprovider \
  .model-learner/w4a-preparation-v1/protected \
  --junitxml=.model-learner/w4a-preparation-v1/reports/protected_frozen.xml
env -u MODEL_LEARNER_TEST_POTION_PATH -u MODEL_LEARNER_OFFLINE_DOCKER_TEST \
  PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/unit/test_w4a_preparation.py tests/unit/test_prospective.py \
  tests/unit/test_learning.py tests/unit/test_codex_adapter.py \
  tests/unit/test_task_workflow.py tests/unit/test_junit_verification.py \
  tests/unit/test_assessment_resolution.py \
  tests/integration/test_portable_evidence.py \
  tests/integration/test_execution_lifecycle.py \
  tests/integration/test_codex_ingestion.py tests/integration/test_run_associations.py \
  tests/integration/test_task_workflow.py tests/integration/test_junit_verification.py \
  tests/integration/test_assessment_resolution.py \
  tests/integration/test_assessment_integrity.py \
  tests/integration/test_resolution_learning_cli.py \
  tests/integration/test_learning_storage.py \
  --junitxml=.model-learner/w4a-preparation-v1/reports/focused_regressions.xml
.venv/bin/ruff check --no-cache .
.venv/bin/ruff format --check --no-cache .
.venv/bin/ruff check --no-cache .model-learner/w4a-preparation-v1/protected/*.py
.venv/bin/ruff format --check --no-cache .model-learner/w4a-preparation-v1/protected/*.py
git diff --check
```

Existing report-name directories are exclusive: use a new name for a fresh offline
review, not overwrite. Pure privacy screening called only `path_reasons` and
`content_reasons` on the exact six public files; it did not stage or inspect private
contents. Explicit new-file whitespace and hash checks were also performed.
No full-suite claim: all 55 Git-policy tests were excluded (they stage/commit in
fixtures); the actual Docker and six Potion opt-in tests were not selected or
enabled, and unrelated broader tests were not rerun because production code did
not change. No dependency sync/download was needed.

Proposed arms verified only against permitted local metadata: OpenAI gpt-6-luna
low, gpt-6.1-sol low, gpt-6.1-sol high; all listed with requested effort supported.
CLI is 0.163.0-alpha.10.2. Advertised context capacities are 272,000 and 500,000;
actual authenticated availability/backend revision and effective context remain
unknown. Distinct configuration hashes/families and one Task association are
explicit. No paid or authenticated availability probe was attempted.

Forecast design prepares fixed Beta(1,1), global, per-arm and A/B/C, all sharing
source universe, target/budget, whole-Task exclusion and a common frozen cutoff.
All matched-arm forecasts must freeze before the first run. No execution forecast
was issued. New benchmark dataset has zero approved evidence, so prior-only is
expected; private/historical summaries are excluded. Unknowns remain unknown.
Synthetic in-memory checks verify effort separation and future/target exclusion;
existing W2/W3 regressions cover receipt gates and independent outcomes.

Blockers: no validated agent or untrusted-verifier read/network/credential/cross-arm
boundary; existing real benchmark gate remains closed; no proven 600-second agent
process-tree watchdog. Additionally, W2 resolution is real-source-specific and the
benchmark exporter marks non-null resource budgets ineligible; the new task's
benchmark receipt/budget integration is not supported. Proposed resource budget
remains 600 seconds, not silently null. No token/dollar ceiling is demonstrated.
Proposed three sequential one-attempt runs expose up to 1,800 process seconds if
a watchdog is implemented; that is not a hard token or monetary bound. Subscription
allowance consumption requires a separate concrete decision, and new spending
remains unauthorized. The private verifier runs only reviewed reference/starter
code, not untrusted generated submissions.

Next decision: accept this task/arm preparation baseline and authorize a bounded
offline containment plus benchmark receipt/budget integration increment. After
those blockers and isolated-runtime calibration pass, separately approve the exact
three arms, one-attempt cohort and allowance/resource exposure, then freeze every
forecast. W4B cannot safely launch on approval wording alone. Stop here; no further
milestone, launch authorization or automatic execution has been prepared.


## W3 integrated execution lifecycle — 2026-10-20

**W3 PASS for the authorized offline synthetic contract.** P1–P10 and N1–N10
are covered by the runnable lifecycle suite and the explicitly mapped existing W2
Attempt-binding/receipt tests. No W4 work, real model execution, private evidence
access, network call, dependency download or historical experiment change occurred.
This does not prove predictive superiority, generalization or real-run provenance.

Initial inventory: branch `main`, HEAD
`0a8b24ebb0d057528d3fa280e6e5316dd8788e67`; no tracked modifications, no untracked
files, no staged changes. Final HEAD/branch/index are unchanged. Final inventory:

| Path | Before | After |
| --- | --- | --- |
| `src/model_learner/storage/evidence.py` | Tracked, clean | Modified |
| `tests/integration/test_execution_lifecycle.py` | Absent | Untracked, new |
| `docs/PROSPECTIVE_FAMILY_EVALUATION.md` | Tracked, clean | Modified, W3 appended |
| `STATUS.md` | Tracked, clean | Modified, W3 checkpoint prepended |

No other tracked modifications or untracked files. All work remains uncommitted;
no staging, commit, push, publishing, branch/ref changes or nested agents occurred.

Existing functionality exercised before production edits: Task/contract creation,
actual `capture codex` and `import codex` CLI paths, explicit Run/Attempt/Session
associations, separate local pytest acceptance execution, actual JUnit production,
artifact/report-bound verification, assessment and eligible observation derivation.
The first full workflow failed at W2 export because actual adapter Session metadata
was unsupported. A separate failing regression exposed the analogous rejection of
adapter metadata-only Events. An empty-scope regression independently reproduced
receipt-gated snapshots incorrectly describing declared-time-only availability.
The pre-fix run had four failures across these three reproduced rejection/display
conditions. No verifier/learner defect or schema migration was required.

Delivered:

- `storage/evidence.py`: accept only the existing supported Codex adapter's
  structural Session/Event metadata, using its existing native metadata validator;
  reject unsupported payload/raw fields. Keep emitted model/provider facts for
  conflict detection and preserve identities. Add receipt-aware descriptive
  snapshot metadata using the existing dataclass; no eligibility change.
- `test_execution_lifecycle.py`: 35 cases, wholly fictional and temporary. Frozen
  Task/test contract and configuration precede capture; a pre-outcome forecast
  uses receipt-resolved prior evidence. Actual local tests create JUnit results;
  a genuinely broken artifact supplies the verified-failure control. Score before
  verified observation persistence, then learn once, reconstruct scoped evidence,
  replay twice, and reproduce original frozen bytes/membership. Analytic Beta
  posteriors and closed-form interval checks, timing, correction, conflict,
  leakage, tampering, missingness and privacy controls are explicit.
- Prospective document: concise lifecycle contract, runnable command, complete
  P/N coverage map, receipt meanings, supported metadata and remaining limits.
- This status checkpoint only; historical status/document content preserved.

Actual checks with the already installed environment:

| Check | Result |
| --- | --- |
| W3 acceptance/regression cases | **35 passed**, 5.67 s. All positive and negative requirement groups covered. |
| Focused capture, associations, file/JUnit verification, outcomes/corrections, observations, storage, portable evidence, prospective and Bayesian learning suites | **305 passed**, 18.15 s, including W3 and all 39 W2 cases. |
| Broad repository regression, with explicit exclusions below | **969 passed, 7 skipped**, 71.38 s. |
| Repository-wide Ruff lint | Passed. |
| Repository-wide Ruff format check | Passed; 196 files already formatted. |
| Git working-tree whitespace and explicit new-file whitespace | Passed. |
| Non-staged privacy screening | Pure guard path/secret/content checks passed on all four changed/new files without exemptions. The generated adapter-backed synthetic bundle also passed pure guard content/secret checks in W3. |
| Mandatory staged privacy guard | Not run: staging is prohibited for this executor. Coordinator must run it after reviewing/staging through GitHub Desktop. |

Test invocations used `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
.venv/bin/python -B -m pytest -q -p no:cacheprovider`. Focused selection included
`test_execution_lifecycle`, `test_portable_evidence`, `test_codex_ingestion`,
`test_codex_adapter`, `test_run_associations`, both task-workflow/JUnit/assessment-
resolution suites, `test_coding_execution_cli`, `test_assessment_integrity`,
`test_resolution_learning_cli`, `test_learning_storage`, `test_learning`,
`test_prospective` and `test_storage`. Broad invocation added
`--ignore=tests/integration/test_privacy_guard.py`; its 55 Git-policy tests stage
or commit in temporary repositories and are excluded under the absolute executor
Git restriction. No staged-guard result is claimed. Ruff used the local executable
with `--no-cache`; no `uv sync` or dependency installation was necessary.

Both optional environment gates were explicitly unset for focused/broad tests.
All seven broad skips are existing opt-ins: one Docker test
(`test_actual_docker_offline_boundary_and_watchdog`) and six local Potion tests
(`test_actual_pretrained_c_shares_cohort_and_preserves_a_b_without_network`,
`test_actual_potion_retrieval_is_pinned_local_and_retains_task_ids`,
`test_actual_pinned_local_potion_diagnostics_network_disabled`,
`test_actual_approved_pretrained_potion_cpu_without_network`,
`test_actual_potion_relevance_metrics_match_frozen_reference`,
`test_existing_local_potion_annotation_evaluation_if_explicitly_enabled`).
No Docker or model-weight opt-in was enabled; no unqualified full-suite claim.

Limits: one Task/dataset per bundle, one full Attempt per verified Run, one hashed
artifact, manually declared configuration/bounds, unauthenticated receipt times,
metadata-only supported capture and disposable reconstruction. Native event time,
effective-model confirmation, native duration and cost remain unknown. The
`source_kind=real` contract is exercised only in a temporary fictional dataset;
synthetic usage is parsing evidence, not model telemetry. Caller-resolved labels
and separately preserved forecast digests remain required for trusted scoring.
No live-ledger merge, general transcript sanitization or real experiment is proven.

Proposed coherent commit groups (coordinator performs all Git mutations):

1. `fix: integrate Codex capture metadata with scoped evidence`
   - `src/model_learner/storage/evidence.py`
   - `tests/integration/test_execution_lifecycle.py`
   Keep the integration fixes and their required regression tests together.
2. `docs: record W3 lifecycle validation and limits`
   - `docs/PROSPECTIVE_FAMILY_EVALUATION.md`
   - `STATUS.md`

Next bounded action: coordinator reviews the four files, stages selected groups in
GitHub Desktop, runs the mandatory staged privacy guard and creates any approved
commits. The smallest step toward W4 is a separately authorized finite-feasibility
scope specifying a selected task, frozen acceptance, privacy/containment and hard
resource limits. W4 implementation/execution is not started or authorized here.

## W2 portable evidence and as-of forecast integrity — 2026-10-20

**W2 PASS for the bounded synthetic contract.** No W3 work or real experiment was
started. Historical W1/Experiment 4 missingness and all earlier checkpoints remain
unchanged; this does not establish predictive superiority or real-run provenance.

Initial state: `main`, HEAD `f7be75b2022d5bb8a364bd25ce289474aac2d02d`, empty
index, no tracked modifications. The only pre-existing untracked files were
`src/model_learner/learn/prospective.py` and `tests/unit/test_prospective.py`.
Both remain byte-for-byte unchanged. Their startup/final SHA-256 values are
`9f9df915fb52ceaf2ccccd6a7250642101b18ea9e82959a8093abc16ece7d53c` and
`16e6bea6e0fbb66cf699e43f6954bcd45e0026128ed1bedf683e10089129c386`.

Reproduced before production edits: two failing synthetic tests showed that
primary JSONL loses explicit Run/Task–Session links and that declared source times
cannot exclude evidence actually received after a forecast. The fixture has two
Tasks, three Runs, three Sessions/Attempts, two configurations, a verified success,
a verified failure, unknown outcomes, frozen acceptance, artifact/report digests,
assessment corrections and delayed receipt. The final legacy tests document these
unchanged limitations; W2 acceptance tests exercise the additive repair.

Delivered:

- New `src/model_learner/storage/evidence.py`: versioned scoped sidecar and
  prospective receipt book; sanitized metadata projection; explicit verification
  attempt bindings; isolated validation and idempotent reconstruction; receipt-gated
  view using the existing assessment/observation resolver. No migration or changes
  to domain contracts, existing JSONL, estimator, verifier or database implementation.
- New `tests/integration/test_portable_evidence.py`: **39 passing synthetic cases**
  covering A–J, including all ten record/association receipt gates, null receipts,
  late corrections, dangling/rebound identities, incomplete/unsupported reports,
  unchanged unknown cost, exact frozen probability/evidence membership, privacy
  projection and pure guard checks. No real data or model execution.
- Modified `docs/PROSPECTIVE_FAMILY_EVALUATION.md`: appended supported contract,
  reconstruction procedure, timing assumptions, privacy boundaries and limits.
- Modified `STATUS.md`: this checkpoint only; historical content preserved.

The new integration tests reuse the pre-existing untracked prospective adapter;
that is a working-tree dependency, not a claim that W1 already committed it. The
coordinator must review its disposition separately. No other edits were present
or changed. Four untracked files remain: the two pre-existing files and the two
new W2 source/test files. Nothing was staged, committed, pushed or published.
HEAD, branch and index remain unchanged. No other repository, private ledger,
conversation history, credential file, dependency installation or paid API was used.

Actual validation with the existing local environment (no dependency downloads):

| Check | Actual result |
| --- | --- |
| Initial synthetic gap reproduction | 2 expected failures before production edits: lost links and late-receipt leakage under the legacy contract. |
| Final W2 acceptance suite | 39 passed in 6.32 s. |
| Focused storage/association/verification/resolution/learning/evaluation/prospective suites | 213 passed in 9.78 s, including the then-current 35 W2 cases; the 4 subsequently added cases passed in the final W2 suite. |
| Broad regression with the explicit Git-policy exclusion below | 934 passed, 7 existing opt-in skips in 58.37 s. |
| Repository-wide Ruff lint | Passed. |
| Repository-wide Ruff format verification | Passed; 195 files already formatted. |
| Whitespace and privacy | Working-tree diff whitespace passed. Pure guard path/secret/content screening passed for all 4 W2 files plus the 2 unchanged prospective files, without exemptions; generated synthetic bundle also passes content screening. Final screening after the documentation update also passed; explicit new-file whitespace checks passed. |
| Staged privacy guard | Not run; index unchanged. Coordinator must run after reviewed staging. |

Tests use `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
.venv/bin/python -B -m pytest ... -p no:cacheprovider`; Ruff uses the existing
`.venv/bin/ruff` with `--no-cache`. Broad regression explicitly unsets
`MODEL_LEARNER_TEST_POTION_PATH` and `MODEL_LEARNER_OFFLINE_DOCKER_TEST` and excludes
`tests/integration/test_privacy_guard.py`: that file stages and commits in temporary
Git repositories, prohibited by this task's absolute no-staging/no-commit rule.
Thus no unqualified full-suite result is claimed. Pure privacy screening does not
replace the later mandatory staged guard or human privacy review.

Limits: one selected Task/dataset, metadata-only Events, existing deterministic
verifiers and one complete Attempt per verified Run. Import requires an empty
or exact-replay disposable destination; it is not a transactional live merge.
Keep the sidecar for receipt-aware resolution. Missing receipt is unavailable;
capture uses the actual current clock and cannot retroactively validate history.
Imported declarations/hashes do not attest time or independent execution. Public
projection omits prose/locators and refuses unsupported metadata; arbitrary private
text/novel secret formats still require human review. Full artifacts/transcripts,
automatic capture and cryptographic time attestation are outside W2.

Next: coordinator reviews the exact four W2 changes and the separately identified
pre-existing adapter/test dependency, selects files in GitHub Desktop, and runs the
required staged privacy guard before any commit. Proposed summary:
`fix: preserve scoped evidence associations and receipt cutoffs`.
After review, the smallest W3 decision is a separately authorized synthetic
capture → verifier → resolver integration scope. No further milestone is started.

## W1 evidence reconciliation and draft protocol — 2026-10-20

Current bounded increment: three documentary phases delivered for human review;
**historical receipt/binding reconciliation remains incomplete**. No existing
plan milestone is newly declared complete. W1 is a working-v1 review gate, not a
renumbering of the master plan. W2–W7 remain outside this execution authorization.
The historical checkpoints below are preserved verbatim and retain their earlier
scope; their “current” or “next” statements are historical, not new authorization.

Delivered only:

- `docs/experiments/experiment_4_reconciliation.json`: one versioned sanitized
  sidecar in the existing aggregate-artifact directory because no public
  Experiment 4 reconciliation manifest was available. Four paired Tasks T1–T4,
  eight reported executions, Low/High arms distinct from A/B/C policies.
- `docs/PROSPECTIVE_FAMILY_EVALUATION.md`: appended W1 reconciliation, prospective
  DRAFT, provenance decision gates and compact W1–W7 mapping to actual plan
  §§4–5, M1/M3/M4/M5/M6-B/M7 and §§7–8. M8 remains optional; M9/M10+ excluded.
  Original adapter documentation is unchanged. No plan or source/test edits.

Evidence: earlier research corroborated T1/T2 from sanitized summaries; this is
inherited corroboration, not a new raw audit. Newly inspected STATUS summaries
supply reported T1/T2 forecasts, verification counts and native token aggregates.
Operator process times are attributed to the earlier report. T3/T4 remain later
user-reported successes; earlier T3-unstarted scope is preserved. No permitted
final T3/T4 artifact, duration or token total was supplied. Exact IDs, frozen
hashes/cutoffs, availability receipts, effective settings, artifact/report binding
and correction chains remain explicit unknowns. No private evidence was accessed.

New offline arithmetic: conditional all-success sequences yield A/B mean Brier
**0.180556**, natural-log loss **0.549306**; C **0.115903 / 0.402359**. Four-task
paired averaging equals eight-arm averaging, without eight independent tasks.
C exactly ties the cumulative matching-arm Beta(1,1) baseline under the same
prior-success sequence. T1/T2 summary values agree with the first two positions;
original frozen files for all tasks remain unavailable, so no complete original
score audit is claimed. No superiority, calibration, difficulty learning,
compatibility transfer, failure prediction or Low/High equivalence established.

The future protocol is **DRAFT — NOT PREREGISTERED; NO TASKS SELECTED OR FROZEN;
NO RUN AUTHORIZED**. Luna Low / Sol Low / Sol High are unverified candidate labels.
Proposed feasibility: 12 tasks, 24/36 attempts, 6/9 process-hours plus overhead;
confirmation uses a fixed precision rule and proposed 60-task hard cap. Unresolved
token, monetary and operator limits block runs. No new infrastructure required
for this documentary scope; any specific receipt/association repair needs its
own demonstrated gap and separate bounded authorization.

Actual checks after inspecting the focused test and import definitions:

| Command/check | Actual result |
| --- | --- |
| `PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -B -m pytest tests/unit/test_prospective.py --noconftest -p no:cacheprovider --basetemp=/private/tmp/model-learner-w1-pytest -q` | 19 passed in 0.14 s; synthetic fixtures only, temporary output isolated. No model or experiment executed. |
| `.venv/bin/ruff check --no-cache src/model_learner/learn/prospective.py tests/unit/test_prospective.py` | Passed. |
| `.venv/bin/ruff format --check --no-cache src/model_learner/learn/prospective.py tests/unit/test_prospective.py` | Passed; 2 files already formatted. |
| Temporary standard-library W1 validator, invoked through installed Python with bytecode disabled | Passed: manifest fields, IDs/counts, source-tier/null reasons, permitted links, summary metrics, exact formulas/six-decimal tolerance, task/arm averaging, Beta equality and document consistency. Baseline preservation and HEAD/branch/index entry hash checked. |
| Scoped working-tree privacy check using existing guard's `path_reasons`, `secret_reasons`, `content_reasons` on the three deliverables, without exemptions | Passed; no rejected content. Manual incremental review found no private transcripts, credentials or personal absolute paths. Scanner coverage is limited, not proof of perfect privacy. |
| `GIT_OPTIONAL_LOCKS=0 git diff --no-ext-diff --check` plus explicit new-file whitespace validation | Passed. |
| Full `uv run pytest`, repository-wide Ruff and `uv sync` | Not run: this increment prohibits installation/cache access and uninspected broad checks/private traversal. Existing local executables and inspected focused checks used instead. No full-suite result claimed. |
| `python3 scripts/privacy_guard.py --staged` | Pending coordinator after reviewed staging; not run and nothing staged. Guard has no working-tree CLI mode; scoped pure content functions above do not replace the required staged guard. |

Baseline: branch `main`, HEAD `bedfaca887228e314de592533bef1149b031b3f6`, empty
staged diff. Pre-existing changes were modified `STATUS.md` (+169 lines versus
HEAD), untracked 63-line prospective document, untracked 337-line
`src/model_learner/learn/prospective.py`, and untracked 313-line
`tests/unit/test_prospective.py`. Their original bytes were preserved. The new
increment consists only of this STATUS section, the appended document sections
and the new sidecar. The source/test hashes and index entries match startup;
HEAD/branch are unchanged. No staging, commit, branch/worktree operation, private
read, network, agent launch, model call, inference, experiment, purchase or
publication occurred. Temporary baseline/check files remain outside Git.

Next human decision: review these additions; optionally supply the smallest
sanitized frozen/association/verification export described in the document;
approve or revise arms, selection/holdout, verifier and hard budgets; decide
whether any narrow provenance repair is necessary. Stop here. Future runs or
implementation require a separate Model Learner project prompt. The coordinator
alone selects/stages reviewed content, runs the staged privacy guard, and may
commit/verify through GitHub Desktop. No push is authorized.

## Historical checkpoints — preserved pre-W1 content

Current work: T2 matched pair complete after separate approval of HIGH. Fresh
preflight confirmed unchanged A/B=0.5 and C=2/3 forecasts, exact clean starting
snapshot, frozen gpt-6.1-sol high configuration/runtime hashes, and **24 no-model
isolation probes**, including denial of Low's actual solution/results. Exactly one
High execution, agent/capture exits 0, no timeout, retry or repair. High independently
passed all **63 acceptance + 14 regressions**, exact identities, compilation and
scope; zero failures/errors/skips. Low previously passed the same 77 cases.
High operator wall **128.693 seconds** versus Low **88.488 seconds**; Low finished
40.205 seconds faster in this pair. High native input **216,696** (cached subset
200,576), output **6,532** (reasoning subset 1,991), versus Low 238,667 input
(214,400 cached), 4,189 output (260 reasoning). Derived uncached input: High
16,120, Low 24,267. No cost inference; effective native configuration/version,
native latency and dollar cost remain unknown. High had three nonzero internal
command exits versus Low eight; command text/output absent, causes unknown.
High frozen A/B scores: Brier **0.25**, natural-log loss **0.693147**. C scores:
Brier **0.111111**, log loss **0.405465**. These match Low's scores. High's scores
were preserved BEFORE its observation insertion/refitting; High's forecast used
only pre-T2 evidence and never used Low's outcome. C has lower losses for these
two successful executions of one matched task; this does not establish general
predictive improvement, calibration or configuration superiority.
High import stored 33 events without diagnostics, replay inserted zero. Both T2
real verified-success observations correctly retain separate Runs/configurations
under the same Task, eligible without exclusions. Resolver/CLI consumes all four
pilot observations across two Tasks. Each exact T2 group/configuration cell has
one success, Beta(2,1), mean 0.667, 95% interval [0.158,0.987]. Neither post-update
summary replaces a forecast. Original repository tracked contents/HEAD/status,
protected tests, earlier evidence, runtime hashes, adapter and all frozen inputs
are unchanged; Low candidate/evidence preserved. Private per-arm archives/reports,
score-order records, comparison, manifests and immutable ledger snapshots remain
ignored. Relevant workflow checks **114 passed**, Ruff lint/format clean (193
files). No original-repository edit, algorithm change, patch transfer, additional
agent, commit or push. **STOP: T2 complete; T3 has not started and requires separate
explicit approval.**

T2 Low-only checkpoint follows.

T2 LOW execution complete after separate explicit approval. Exactly
one frozen gpt-6.1-sol low-reasoning run; agent/capture exits 0, no timeout, repair
or retry. Independent preserved-candidate evaluation passed **63 acceptance + 14
regression cases**, exact identities, source compilation and scope; zero failures,
errors/skips. Frozen A/B probabilities 0.5 scored Brier **0.25**, log loss
**0.693147**; frozen C probability 2/3 scored Brier **0.111111**, log loss
**0.405465**. Scores were preserved BEFORE inserting the new learning observation
or fitting a new posterior. C's lower losses apply to this one held-out success;
they do not establish general predictive improvement or task exchangeability.
Operator wall **88.488 seconds**. Native input **238,667** (cached subset 214,400),
output **4,189** (reasoning subset 260). Eight internal commands exited nonzero;
their text/output is absent from metadata capture, so causes remain unknown.
Effective native model/version/configuration, native latency and dollar cost remain
unknown; configuration is retained as the exact frozen operator declaration.
Import stored 40 events without diagnostics; replay inserted zero. New real
success/verified observation is correctly associated with the second Task, its
prospectively assigned Run and Low configuration; eligible with no exclusions.
Existing resolver/CLI consumes all three observations across two Tasks without
exclusions; the new exact group/Low cell uses one success, Beta(2,1), mean 0.667
and 95% interval [0.158,0.987]. This post-update estimate replaces no forecast.
All frozen preparation files, prior evidence, original repository tracked contents/
HEAD/status, protected tests, runtime hashes and learner adapter are unchanged.
High's workspace remains pristine and both pre-T2 forecasts are unchanged.
Private final archive, bound JUnit report, scoring-order evidence, usage, result,
manifest and immutable after-Low ledger snapshot remain ignored. Relevant
forecast/JUnit/ingestion checks **114 passed**; Ruff lint/format clean (193 files).
No production algorithm change, original-repository edit, patch transfer, extra
agent, commit or push. **STOP: T2 High and all later executions remain unlaunched
and require separate explicit approval.**

T2 preparation checkpoint follows.

Second prospective matched task preparation complete; **no T2
coding-agent execution**. Existing CLI and resolver confirm both T1 real verified
successes remain eligible, correctly associated with task/configuration, with no
exclusions. Reused unchanged compatibility policy, configurations and adapter.
Both forecasts were frozen from the same pre-T2 ledger snapshot: A/B remain
Beta(1,1), mean 0.5 [0.025,0.975]; C uses only the matching-effort T1 success,
Beta(2,1), mean 0.667 [0.158,0.987]. C's cross-task exchangeability is an explicit
assumption, not learned difficulty. Both arms are frozen before either executes;
Low's later outcome must not change High's forecast. Runtime transfer remains
untested because only one runtime is admitted.
Identical clean task-specific source exports reproduce the same **63 acceptance
+ 14 regression cases**: each untouched baseline has 29 passes and 48 expected
acceptance failures, zero errors/skips, all regressions pass. Exact test identities
and protected digests are frozen. Both arms pass **19 no-model isolation probes**,
including previous solutions, other arm, protected tests, ledger and forecasts.
Original selected source/HEAD/status, earlier frozen evidence and runtime hashes
are unchanged; preexisting unrelated repository edits remain present. Active
ledger now contains two declared Tasks and only the original two T1 observations;
no T2 Run or outcome. All private preparation/evidence remain ignored.
User explicitly selected **Low then High** to balance T1's order. Both check-only
execution gates pass. Adapter tests **19 passed**; Ruff lint/format clean (193
files). No production code/algorithm or original task repository changes, agents,
commits or pushes. **STOP: separate approval required for T2 Low first; High and
later tasks remain unauthorized.**

T1 completed checkpoint follows.

T1 prospective matched pair complete. LOW executed exactly once
following separate approval and fresh High-solution/evidence isolation probes.
Low independently passed **36 acceptance + 6 regressions**, zero failures/errors/
skips, exact identities and scope passed; no repair or retry. Agent/capture exits
0, no timeout. Low operator wall **51.994 seconds**, versus High **96.723 seconds**
(44.729 seconds / 46.2% less in this pair). Low native input **117,743** (cached
subset 86,784), output **2,690** (reasoning subset 355). High input 205,955 (cached
180,608), output 4,854 (reasoning 1,595). Derived uncached input is higher for Low
(30,959 vs 25,347); native latency and dollar cost remain unknown. No savings claim.
Low has three nonzero internal command exits versus High five; their text/output
is absent, so causes remain unknown. Final independent checks passed for both.
Low imported 30 events without diagnostics; replay added zero. Active real ledger
has one Task and two eligible success/verified observations, no exclusions. Existing
CLI consumes both but each arm retains **one success**: Beta(2,1), mean 0.667,
95% interval [0.158,0.987]. Low frozen A/B/C forecasts stayed 0.5 and each scored
Brier 0.25/log loss 0.693147 BEFORE Low observation persistence/refitting. Both
forecasts were frozen before High; High never informed Low's forecast.
All frozen inputs, High evidence, original task source/HEAD/status, runtime hashes
and learner adapter code are unchanged. Private final artifacts, bound reports,
scores, comparison and immutable per-arm ledger snapshots remain ignored.
This single-task pair does not distinguish prior-only predictors or establish
configuration superiority/generalization. No algorithm changes, commits, pushes,
patch transfer or additional agent/task execution. **STOP: T2 remains unstarted;
separate explicit approval required.**

Earlier High-only checkpoint follows.

High-only checkpoint: first prospective matched task HIGH execution complete after
explicit approval. Exactly one gpt-6.1-sol high-reasoning CLI run; agent/capture
exits 0, no timeout or retry, operator pipeline wall **96.723 seconds**. All
**36 frozen independent acceptance and 6 regression cases passed**, no failures,
errors/skips; exact required identities and scoped algorithm preservation passed.
Stored one real success/verified observation, single-configuration eligible with
no exclusions; existing CLI consumed one success. Frozen A/B/C probabilities each
0.5 scored Brier **0.25**, natural-log loss **0.693147**, before observation
persistence/fitting. Reference High cell is Beta(2,1), mean 0.667 and 95% interval
[0.158,0.987]. Identical prior-only forecasts do not establish predictive gain.
Native input **205,955** (cached subset 180,608); output **4,854** (reasoning subset
1,595). Native effective configuration/version, latency and dollar cost unknown.
Five nonzero internal command exits retained; command text/output was not captured,
so causes remain unknown. Import stored 33 events without diagnostics; replay
added zero. Relevant forecast/capture/JUnit checks **114 passed**; Ruff/format clean.
All frozen preparation files, Low forecasts and clean Low workspace are unchanged;
original task repository source/HEAD/status unchanged. Private final archive,
report, scores, execution ledger and immutable after-High snapshot remain ignored.
No repairs, production algorithm changes, patch transfer, commit, push or other
agent launch. Stop: LOW remains unlaunched and needs separate explicit approval.

Preparation checkpoint (before the High execution) follows.

Preparation work: minimal prospective configuration/task-family adapter and first
matched-task preparation complete; coding-agent executions remain **zero**.
Added a pure API over the unchanged Beta-Bernoulli estimator: exact-cell A,
explicit compatible-configuration-family B, and broader task-family C. Policies
preserve model/effort and behavioral distinctions; canonical records are unchanged.
Exclusive read-only forecast files carry external hashes; bound verified labels
are scored without refitting. Real callers must first resolve ledger evidence.
Four genuine boundary-hardening tasks across three repositories are selected in
ignored private storage. First low/high workspaces and protected tests match;
36 independent acceptance plus 6 regression cases reproduce 25 failures and
17 passes in each untouched baseline, no errors/skips. Both final forecasts are
prior-only 0.5 with 95% interval [0.025,0.975]; no historical data was relabelled.
Only one runtime is admitted, so B=A until a later separately reviewed runtime
contrast exists. Operator safety stop is separate from a null learner budget;
unknown native latency/cost remain null. Isolation canaries pass for both arms.
Checks: **961 passed, 7 existing skips**; Ruff lint/format clean (192 files), CLI
help exit 0. Documentation: docs/PROSPECTIVE_FAMILY_EVALUATION.md. Private drafts,
preflight transport failures and authoritative final manifests are retained.
No task repository edits, dependency changes, agents, neural models, Governor,
commits or pushes. Next step is separate explicit approval of the first arm;
no execution or later implementation is authorized by preparation.

Prior completed experiment status follows.

Current work: experiment 3 complete after separate explicit approvals for A and B.
Exactly two sequential supervised Codex CLI invocations requested gpt-6.1-sol,
A low reasoning and B high reasoning, each with the frozen 600-second safety stop.
Both used identical clean 35-file exports of the original prepared commit, task
instructions and protected tests. Before B, original snapshot/runtime/input hashes
matched; fresh no-model canaries denied reads of A's actual solutions/results,
ledger snapshot, protected tests and original source, including symlink escape.
The newer original Git HEAD was not used. Both unchanged forecasts were frozen
before A: zero selected observations, Beta(1,1), mean 0.5, 95% interval
[0.025, 0.975]. B did not use a prediction updated after A.

Both agent/capture processes exited 0 without timeout. Each candidate passed all
51 independent acceptance and 168 frozen regression cases, with exact required
identities and no failures/errors/skips. Scoped changes preserve existing exports;
Ruff lint passed for both. The same additional formatting check failed on each
agent-added test file. No candidate repair or retry followed acceptance testing.
Operator wall times: A 61.455 seconds, B 144.989 seconds (B/A 2.36).
Native usage: A 190,626 input (142,336 cached subset), 3,223 output (120 reasoning
subset); B 303,549 input (245,376 cached subset), 7,335 output (1,828 reasoning
subset). B used 1.59 times the input and 2.28 times the output tokens on this pair.
Nonzero internal command exits: A five, B six. Their command text/output is absent
from the frozen metadata capture, so causes remain unknown. Native effective
configuration/version, latency and dollar cost remain unknown. Frozen supervision
retains stderr counts/hashes rather than text. No missing telemetry was fabricated.

Imports retained 26/36 events without diagnostics; both replays added zero.
Existing tools recorded two eligible single-configuration success / verified real
observations for one paired Task. The unpooled estimator consumed both with no
exclusions and one success per exact arm: each Beta(2,1), mean 0.667, 95% interval
[0.158, 0.987]. Collection and consumption work; one run per configuration does
not establish predictive accuracy, calibration, general superiority or cost savings.
Fixed order, cache/backend effects and stochastic variation remain limitations.
Both final archives/snapshots and A's prior evidence are unchanged. Original file
contents match before-run hashes; during A, Git HEAD/status changed externally
and was preserved; during B, original contents/HEAD/status remained unchanged.
Relevant Model Learner checks: 95 passed; Ruff/format clean. Private comparison,
JUnit bindings, captures, manifests, full workspace archives and after-run ledger
snapshots remain ignored. No original-repository mutation, patch transfer, new
infrastructure, extra coding agent, commit, push or publication. Stopped after
Experiment 3; no additional execution or milestone is started or authorized.

Prior work: experiment 2 complete after explicit user approval. One ordinary
Codex CLI execution fixed ShortcutLens DataLoader seed validation. All 172 frozen
required checks passed (60 independent acceptance cases, 112 initial regressions),
with zero failures/errors/skips. Candidate and applied-code scoped regressions each
passed 129 cases; Ruff passed. The verified two-file patch is applied; unrelated
concurrent project work was preserved. Capture/import retained 18 events with no
diagnostics; replay added zero. One real single-configuration verified-success
observation is eligible and consumed by the existing learner with no exclusions.
Prior-only mean 0.5 [0.025, 0.975] became 0.667 [0.158, 0.987] after one label;
this establishes workflow operation, not predictive accuracy. Operator wall time
was 31.64 seconds; native latency, dollar cost and effective native configuration
remain unknown. Relevant Model Learner checks: 95 passed; Ruff/format clean.
No new Model Learner infrastructure, semantic changes, additional agents, training,
commit or publication. Stopped after this one experiment; no further run authorized.

Prior work: first supervised real CSV coding experiment complete after explicit
user approval. One Codex CLI invocation requested gpt-6.1-sol with low reasoning,
produced a standalone standard-library CSV comparison script, and exited 0.
Metadata capture exited 0; import stored 11 events and one session without
diagnostics. All 18 independent acceptance tests, frozen before execution, passed
on the exact final script snapshot without failures/errors/skips or source changes.
Bound JUnit evidence produced one verified-success assessment and one eligible
single-configuration real observation. Existing reference learner consumption
selected one eligible success with no exclusions. Capture replay added zero events.
Operator agent wall time was 123.44 seconds; native latency, dollar cost and native
configuration/version confirmation remain unknown. Full repository checks:
931 passed, 7 existing skips; Ruff and formatting clean. Private experiment files
remain ignored. No production implementation, semantic analyzer, new trained model,
Governor, commit or publication changes. Stopped after this one experiment; no
additional run or milestone is authorized.

Prior work: real execution/outcome readiness assessment complete. Existing
capture, task/run/attempt, JUnit verification, assessment resolution and learning
contracts support a minimal prospective 5–10-run ordinary Codex CLI collection
pilot without new infrastructure. Read-only inventory/resolution establishes one
eligible real fixed-reply smoke run and zero eligible real coding runs. With user
approval, the three selected project artifacts passed fresh independent checks;
passing current checks does not establish historical configuration/attempt binding.
Sanitized assessment and exact operator sequence: docs/REAL_DATA_READINESS.md.
Private reports, snapshots and receipts remain ignored. No production code,
training, semantic integration, routing or Governor changes. Stopped after the
assessment/recommendation; prospective collection is unstarted.

Prior work: bounded local CPU semantic-extraction comparison complete.
Qwen2.5-1.5B-Instruct Q4_K_M was downloaded with explicit approval and evaluated
with a frozen zero-shot prompt/schema on 15 consumed diagnostic and 16 fresh
prediction-blind simulated checkpoints. It did not improve extraction: holdout
positive-obligation alignment is 3/25 precision and 3/31 recall, versus frozen
rules 10/16 and 10/31, structural parsing 12/13 and 12/31. Known objectives are
0/15, 0/15 and 4/15 respectively; all have 0/9 earlier-link recovery.
Only 4/33 local-model holdout events satisfy message-local evidence validation;
all 31 model generations are schema-valid, illustrating why JSON validity is
insufficient. Median holdout inference is 4.98 seconds and peak runtime RSS about
2.2 GiB. These are AI-reference agreement findings, not human-verified accuracy.
No production analyzer, estimator, dependency or routing change. Sanitized report
is docs/LOCAL_TASK_STATE_COMPARISON.md; private evidence and independent final
review remain ignored. Stopped after comparison/recommendation. No further model
or milestone started.

Prior work: authorized comparison of frozen predictions with independent
AI-authored Work annotations complete. All 15 exposed user messages and 150
reference fields validated; inputs and analyzer hashes remain unchanged. Private
report separates semantic agreement, missing/incomplete predictions, unsupported
fields, contextual matching and annotation policy. Typed positive-obligation
agreement is 21/24 normalized predicted units and 21/84 reference obligations;
alternate positive evidence covers 32/84. Current core-action objective agreement
is 3/15; topic compatibility is separately 8/15. These are post-hoc AI-reference
agreement measurements, not human-adjudicated accuracy or generalization.
No analyzer execution, implementation, training or outcome integration occurred.
Validation and independent methodology review are recorded at the end. Stop after
the comparison report; human adjudication and any further experiment are unstarted.

Prior work: blind human-adjudication worksheet preparation complete, with all
15 exposed user messages and 150 blank annotation cells. No human labels were
filled. The later comparison was separately authorized by the user and uses
independent AI annotations; genuine human adjudication remains pending.

Prior work: selected-conversation coverage recovery and projected evaluation
complete. All 15 exposed user messages across the same four selections now have
predictions (3/3, 4/4, 4/4, 4/4); original full-text results remain separate and
unchanged. A prediction-frozen all-user-prefix policy omits assistant text into a
separate message-local report view. The analyzer, rules and default importer
limits are unchanged. Approved diagnostic transport reads used a separate 256-KiB
allowance; non-message payloads caused the two original wire failures, and earlier
assistant prose caused the research clause failure. Objectives still remain unknown
for two selections; omission loses one user-to-assistant candidate edge. No human
labels or independent outcomes inspected; semantic accuracy remains unmeasured.
Checks: 870 passed, 7 existing opt-in skips; Ruff and formatting clean.
Independent review is recorded below. Stop after evaluation and recommendations;
human adjudication and outcome integration remain unstarted.

Prior focused semantic task-state generalization evaluation is complete.
The baseline and original diagnostic
results are frozen. Prediction-blind independently agent-authored synthetic
holdouts expose substantial failures: opening objectives 5/11 on the first 12
cases; typed requirement precision 13/18 and recall 13/23. Two bounded corrections
recognize progressive objective verbs and flag multiple candidate change targets.
On eight untouched cases the revision and baseline have identical recognition
results: opening objectives 3/7, typed requirement precision 5/6 and recall 5/10.
A separately untouched requirement-reinstatement case also shows no improvement.
No false verified claims occur; reference-policy artifacts are documented.
The user-supplied scheduling sentence reproduces an objective-rule morphology
defect with intact text and is fixed in a synthetic bridge regression. The private
original was not reread. No real outcome/predictive benefit is established.
Do not integrate these semantic hypotheses as trusted utility features yet.
Full checks passed: 865 tests, 7 existing opt-in skips, clean Ruff and formatting.
Independent final code/evaluation review found no blockers. Stopped after
evaluation and recommendations.
The standalone importer and prior longitudinal/retrieval increments remain intact.
The earlier 40-query human-review batch still has no genuine human labels or
accepted reviews. Real coding-agent benchmark execution remains disabled.
Last requested work: diagnose coverage for the same four selected conversations,
freeze separate evidence views, evaluate the unchanged analyzer, report limitations
and recommend whether to human-adjudicate. No later milestone is started.
Updated: 2026-10-13

## Completed milestones

- M0-A: repository and environment assessment.
- M0-B: project foundation implemented and acceptance checks passed.
- M1-A: typed, versioned domain contracts implemented.
- M1-B: SQLite persistence, JSONL validation, and storage CLI implemented.
- M1.1: evidence-safe observation, attribution, dataset, schema-version, and
  optional project-context contracts implemented.

## Implementation status

- Repository assessment: existing plan and minimal README, no implementation or
  development tooling; existing Git remote preserved.
- Python 3.12+ package under `src/model_learner/`, with an installed `model-learner`
  console entry point. Help and version output work; no arguments display help
  with exit code 2, and unsupported input is rejected with exit code 2.
- uv-managed editable installation and lockfile; pytest and Ruff in the default
  development group. README documents installation and development checks.
- Created `.gitignore`, `.python-version`, `pyproject.toml`, `uv.lock`, `AGENTS.md`,
  `STATUS.md`, `src/model_learner/__init__.py`, `src/model_learner/cli.py`,
  `tests/unit/test_package.py`, and `tests/integration/test_cli.py`.
  Updated the existing `README.md`; the master plan is unchanged.
- Domain contracts now cover tasks, native sessions, explicit task/session links,
  runs, attempts, execution configurations, events, verifications, outcomes, and
  future observations. Every record has a schema version. Timestamps must be
  timezone-aware, unknown telemetry remains nullable, and invalid values fail
  Pydantic validation.
- Task identity is distinct from session identity. Associations are stored only in
  `task_sessions`; registering a session does not attach it to a task or imply a
  complete task. Runs are bounded executions of a task; attempts are the
  configuration-bearing segments inside runs.
- Execution configuration records provider, model, optional model version,
  optional reasoning level, optional harness, and metadata. Missing provider,
  model, usage, latency, and cost are represented as `null`, never zero.
- Outcomes separately record `success`, `failure`, `abandoned`, or `unknown` and
  `verified`, `partially_verified`, or `unverified`. Verification evidence has its
  own provenance and identifiers. An `agent_report` outcome itself is always
  unverified; a separate independently sourced assessment can cite verification.
- SQLite uses numbered, forward-only migrations, foreign keys, WAL mode, a busy
  timeout, canonical JSON rows, and short transactions. Events use a stable key
  and idempotent insert behavior; outcomes remain append-only. Evidence linked to
  a different task or run is rejected.
- Added JSONL validation/import/export for primary records. Observation queries
  require an explicit `real`, `simulated`, or `benchmark` source kind so future
  summaries cannot silently mix datasets.
- Added `model-learner init`, `task create`, `task list`, `session register`,
  `task attach-session`, and `records show` CLI operations, plus JSONL record
  import/export/validation commands. README documents the M1 local ledger flow.
- Pydantic v2 is a runtime dependency; `uv.lock` was updated accordingly.
- At the M1.1 checkpoint, no agent hooks, provider integration, automated
  verification, simulator, learner, routing, or TUI had been implemented. The
  parallel slices below now add CLI observation and reference learning.
- M1.1 adds an additive second SQLite migration. New records use schema version
  2; known M1 schema version 1 records remain readable but legacy observations
  cannot be marked learning-eligible. Unknown schema versions are rejected.
- Learning observations now identify their real/simulated/benchmark dataset and
  version, have deterministic stable keys for idempotent persistence, record
  decision and label-availability times separately, and retain target acceptance
  specifications, evidence IDs, attribution status, and eligibility.
- Real version-2 observations require a task, run, outcome, acceptance
  specification, outcome/verification status, and a matching attempt for a
  single-configuration attribution. Repository checks ensure all links, evidence,
  acceptance specification, configuration, and labels agree with ledger records.
- `censored` is distinct from `unknown`; censored outcomes require a reason and
  neither censored nor unknown observations can be learning-eligible. Mixed or
  incomplete attribution is retained but cannot be eligible for
  configuration-level learning.
- Execution configurations now have a deterministic snapshot ID plus optional
  configuration and harness versions. Optional manually declared `Project` and
  `ProjectTaskLink` records group tasks without changing task identity or adding
  project discovery.

## Parallel first slices delivered

The user explicitly authorized the first useful local-observation and learning
slices together. Two implementation subagents used one initially clean checkout
with strictly separate ownership: `adapters/` and Codex fixtures/tests versus
`simulate/`, `learn/`, and statistical tests. The coordinator owns CLI integration,
CLI integration tests, README, and this status. An independent third subagent
reviewed data integrity, privacy, numerical validity, and temporal leakage.
`MODEL_LEARNER_BUILD_ORDER.txt` is absent. Domain contracts, migrations, dependency
manifest, lockfile, and master plan are unchanged.

- **Local observation (M3-A/B and narrow M3-C slice):** a versioned read-only
  adapter consumes the documented `codex exec --json` stream. A small stream
  wrapper creates `codex-exec-capture/v1` receipt-time envelopes; it never launches
  or controls Codex. Session/event records use the existing M1.1 ledger, retain
  native thread/item identities, observed provenance, source/emitter/adapter
  versions, and redaction/missingness metadata. Tool lifecycles, completed/failed
  turns, per-field token usage coverage, and emitted configuration fields can be
  rebuilt from retained metadata. Completion creates no outcomes or learner rows.
- Capture retains a metadata projection of native observations by default;
  prompts, reasoning, commands, arguments, and outputs are omitted. Full private
  payload retention is an explicit local `--retain-raw` opt-in. Capture files are
  created exclusively; ingestion diagnostics describe rejected rows without
  reproducing private contents. Replay is idempotent; conflicting capture replay
  is rejected rather than counted as another event.
- **Probabilistic learning (M2-A/B reference slice):** seeded, reproducible
  synthetic observations cover three generic configuration arms and four task
  groups, configurable probabilities, assignment imbalance, independent missing
  labels/resources, delayed labels, resource distributions, and step drift.
  Simulator probabilities and realized truth live in a separate evaluator-only
  artifact; they never become Observation features or ledger rows.
- A pure Beta-Bernoulli estimator uses a fixed Beta(1,1) default prior and exact
  configuration snapshots. It selects one source/dataset/version and acceptance
  target/budget, counts only eligible verified binary outcomes available at the
  cutoff, excludes missing/unverified/mixed/legacy records, deduplicates reimports,
  and rejects conflicting observations for one experimental unit. Outputs include
  successes/failures, posterior mean/variance, 95% equal-tail credible intervals,
  exclusions, and descriptive resources with known/missing denominators.
- Frozen chronological evaluation compares global, per-configuration, and
  unpooled references with Brier score, log loss, calibration bins, separate
  simulator-truth probability errors, and assignment-weighted/grouped interval
  coverage/width. Empty denominators produce null metrics, not zero scores.
  Training and evaluation cutoffs apply to record and label availability.
- CLI commands now include `capture codex`, `import codex`, `sessions`,
  `session show`, `sim generate`, `learn predict`, and `learn eval`. Dataset,
  acceptance version, budget, configuration, and timestamps are explicit. The
  README and `docs/CODEX_OBSERVATION.md` / `docs/PROBABILISTIC_LEARNING.md` document
  usage, assumptions, source assessment, and limitations.

### Real local validation

Tested on macOS arm64 using installed **codex-cli 0.162.0-alpha.17.2**. A bounded
CLI smoke session used `exec --json --ephemeral --ignore-user-config
--ignore-rules --sandbox read-only` with a sanitized instruction to emit a fixed
reply without tools or file changes. Initial filesystem-sandbox attempts exited
1 before JSON events; a coordinator check identified `Operation not permitted`
without displaying native stderr. An authorized execution outside the outer
filesystem sandbox, retaining Codex's own read-only agent sandbox, exited 0.
Four actual JSON events were captured as metadata-only observations: first import
inserted four events and one session, replay inserted none and recognized four
duplicates, with no diagnostics. Private source messages/stderr were not retained.
The safe capture and test ledger stay under ignored `.model-learner/`.

For this smoke test, native stdout was buffered before envelope creation. Receipt
timestamps therefore describe receipt of that buffer, never native execution
times or durations. Normal pipe capture records stream receipt as data arrives;
upstream buffering still affects timing. Native timestamps, model settings not
emitted by the CLI, monetary cost, and verified task success remain unknown.
Existing desktop rollout records were assessed structurally only; their private
format is not implemented as a supported source. This is a validated **CLI**
slice, not passive capture of the current desktop development session.

## Test evidence

Executed on macOS arm64 with Python 3.12.14, uv 0.12.24, pytest 9.1.1,
Typer 0.27.3, Rich 14.3.4, and Ruff 0.16.10 on 2026-10-09.

| Command / check | Actual result |
| --- | --- |
| `uv sync` | Exit 0; resolved 14 packages, installed 13 including the editable project. |
| `uv run pytest` | Exit 0; **8 passed in 0.20s**. |
| `uv run ruff check .` | Exit 0; `All checks passed!` |
| `uv run ruff format --check .` | Exit 0; `8 files already formatted`. |
| `uv run model-learner --help` | Exit 0; readable help with `--help` and `--version`. |
| `uv run model-learner --version` | Exit 0; `model-learner 0.1.0`. |
| `uv sync --locked --offline` | Exit 0; lockfile accepted, 13 packages checked. |
| `uv build --offline` | Exit 0; source distribution and wheel built. |
| Archive inspection | Wheel contains only the two package modules and distribution metadata, with the correct console entry point. Source distribution excludes local tools, virtual environment, caches, OS files, and private runtime data. |
| `git diff --check` | Exit 0; no whitespace errors. |
| `uv sync --locked` | Exit 0; installed Pydantic v2 and its locked dependencies into the local virtual environment. |
| `uv run pytest` | Exit 0; **21 passed in 0.41s**. Covers schema validation, invalid timestamps/outcomes, null measurements, migrations, task/session links, evidence integrity, event idempotence, JSONL round-trip, source-kind separation, and M1 CLI operations. |
| `uv run ruff check .` | Exit 0; `All checks passed!` |
| `uv run ruff format --check .` | Exit 0; `16 files already formatted`. |
| `uv run model-learner --help` | Exit 0; lists `init`, `task`, `session`, and `records` commands. |
| `uv run pytest` | Exit 0; **29 passed in 0.52s**. M1.1 coverage includes M1-to-M1.1 migration, schema-version rejection and legacy reading, evidence-linked real observations, unknown/censored labels, mixed-attribution rejection, observation deduplication, temporal validity, dataset filtering, configuration identity, and optional project/task links. |
| `uv run ruff check .` | Exit 0; `All checks passed!` |
| `uv run ruff format --check .` | Exit 0; `16 files already formatted`. |
| `git diff --check` | Exit 0; no whitespace errors. |

M0 tests cover imports/version metadata, help, version, no arguments, invalid
options, unsupported commands, and the installed executable from an unrelated
directory. Help/version invocations create no files in that directory. The M1
tests above add domain, storage, JSONL, and CLI coverage; no master-plan edits or
later milestone implementations were made.

For this session, `.tools/bin` was prepended to `PATH`, `UV_CACHE_DIR` was set to
`$PWD/.uv-cache`, and `UV_PYTHON` selected Codex's bundled Python 3.12.14 during
setup. The resulting `.venv` is ready for local use. These environment overrides
are local validation setup and are not required on a machine with uv/Python ready.

### Parallel-slice checks — 2026-10-10

Used the existing Python 3.12.14 / uv 0.12.24 / Ruff 0.16.10 environment with
repository-local tool/cache paths. No new dependencies were required.

| Command / check | Actual result |
| --- | --- |
| Pre-change `uv run pytest` | Exit 0; **29 passed in 0.56s**. |
| Observation subagent's owned tests | Exit 0; **24 passed in 0.43s**; owned Ruff lint/format checks passed. |
| Learning subagent's owned tests | Exit 0; **47 passed in 0.45s**; owned Ruff lint/format checks passed. |
| Final coordinator `uv run pytest` | Exit 0; **105 passed in 1.62s**. |
| Final coordinator `uv run ruff check .` | Exit 0; `All checks passed!` |
| Final coordinator `uv run ruff format --check .` | Exit 0; `38 files already formatted`. |
| `uv run model-learner --help` | Exit 0; includes capture/import/session inspection and sim/learn commands. |
| Installed CLI, actual metadata-only smoke capture in a fresh final ledger | First import: one session, four events; replay: zero new sessions/events, four duplicates; both had no diagnostics. `sessions` and `session show` returned four timeline events with native time/cost/latency unknown and verification unknown. |
| `git diff --check` | Exit 0; no whitespace errors. |

Coordinator integration coverage exercises capture privacy, diagnostic exit codes,
exclusive capture destinations, import/replay/timeline, arbitrary valid manual
event metadata, simulation persistence/deduplication, explicit scenario overrides,
target/dataset filtering, prediction, held-out evaluation, timezone rejection,
and prior-only empty datasets. Existing M1.1 tests continue passing unchanged.
The obsolete CLI test treating `learn` as unsupported now checks the still
unsupported `recommend` command instead.

Independent review identified and prompted regression-tested fixes for modified
capture replay (including native thread/version changes), phantom sessions after
rejected replay, malformed thread-boundary attribution, and unsupported ledger
payload inspection. Statistical review prompted explicit numeric-domain limits
and complete target/budget reporting. No contract or migration alteration was
needed. The two implementation slices remain independently testable.
Final independent review confirmed **105 tests passed**, clean Ruff/formatting,
and no unresolved blockers within the requested slice.

## Requested Workstreams A/B/C — 2026-10-10

The coordinator read the plan, AGENTS.md, prior status and implementation. The
build-order file remains absent. Three Codex subagents had separate ownership:
new run/verification/observation modules and tests; simulation/learning stress
modules and tests; and Desktop feasibility research. The coordinator owned shared
contracts/migrations/storage, CLI integration, integration tests, README and this
status. The research agent independently reviewed the final implementation.
The master plan, dependencies and lockfile are unchanged.

### Workstream A — delivered and real integration exercised

- Added the additive `RunSessionLink` contract and migration 3 (`run_sessions`).
  Existing version-1/2 contracts and primary records remain readable. Associations
  require the session to be explicitly linked to the run's task. Imported events
  are never rewritten to attach a run.
- Explicit bounded runs retain declared state, receipt-time range, final artifact
  fingerprint and boundary provenance. Attempts retain exact configuration
  snapshots, contiguous boundaries and human declaration source; no inferred task
  classification or fabricated native model telemetry is used.
- Added a deterministic **read-only SHA-256 file verifier**. The expected digest is
  declared with the task; the final artifact snapshot is declared with the run.
  Verification retains artifact reference/fingerprint, acceptance version, result,
  verifier version, observation time, criterion and observed provenance. It reads
  bytes without retaining them and checks for file changes while hashing. It never
  executes an arbitrary verifier command or launches an agent.
- Completed execution remains separate from assessment. Evidence-free assessment
  yields unknown; explicit human labels remain unverified. Matching final evidence
  yields verified success/failure against this exact bytes-only criterion.
  Wrong/stale artifact/spec, contradictory result, foreign evidence, invalid times
  and branching supersession are rejected. Assessments remain append-only.
- Real observation building retains task/run/outcome/attempt/evidence links,
  dataset identity, acceptance/budget, label availability and eligibility reasons.
  It requires actual captured Codex CLI events in the selected receipt-time range.
  Mixed, incomplete or contradicted attribution, unknown/unverified labels, and
  unknown/exceeded declared budgets stay ineligible. Unknown resources stay null.
  Rebuilding the same derivation is idempotent. Quality reports explicitly count
  assessment derivations, with dataset and missingness denominators.
- Added `task create --expected-sha256`, `run create/attach-session/attempt/show`,
  `verify file`, `outcome assess/human`, and `observations build/quality`. Existing
  source-filtered JSONL export serves real observations. Usage and semantics are
  documented in `README.md` and `docs/TASK_VERIFICATION.md`.
- Independent review reproduced two defects: repeating the same captured run
  counted it twice, and concurrent association could bypass overlap validation.
  Inclusive overlapping bounds for the same session are now rejected (including
  different tasks and additional session links). Preflight avoids ordinary phantom
  runs, and `BEGIN IMMEDIATE` serializes the association check and write. Regression
  tests cover repeat, shared endpoints, disjoint ranges and competing writers.

**Actual real workflow:** An operator-only validation script under ignored
`.model-learner/verification-smoke/` declared an exact sanitized reply digest
**before** running installed `codex-cli 0.162.0-alpha.17.2` on macOS arm64.
The explicit invocation used `exec --json --ephemeral --ignore-user-config
--ignore-rules --skip-git-repo-check --sandbox read-only`, an isolated temporary
working directory, `--model gpt-6.1-sol`, low reasoning, and `--output-last-message`.
It requested a fixed reply without tools or file changes. The operator launches
this test; the shipped Model Learner APIs/CLI remain observers. Based on the
previous demonstrated outer-sandbox failure, this bounded validation received
execution approval outside that outer sandbox while retaining Codex's own
read-only sandbox. No native stderr or raw prompts/messages were retained.

The CLI exited 0 and the streaming capture retained four metadata-only events,
with zero diagnostics. First import inserted four; replay inserted zero and
recognized four duplicates. A distinct task/run/session and explicitly declared
configuration segment were linked. Finished execution first produced unknown,
unverified, ineligible assessment. The predeclared exact reply bytes then passed
verification; an appended assessment produced success/verified and an eligible
real observation. Rebuild returned the same observation ID. JSONL exported both
real derivations (unknown and assessed, in explicitly distinct cohorts), and
fitting only the assessed dataset counted **one** label. Cost and latency remained
null; configuration provenance was the operator's explicit command declaration,
not an emitted native model/version. Native model version remains unknown.
This validates the real capture-to-verification path for a fixed reply; it does
not establish coding-task utility or native Desktop capture.

### Workstream B — delivered with actual multi-seed evidence

- Added pure `run_stress_suite()` and eight reproducible scenarios: balanced,
  homogeneous, sparse, imbalanced, drift, missing, delayed-pending and delayed-mature.
  Each seed/scenario has an explicit simulated dataset and complete configuration.
  The existing Beta(1,1) estimator and seeded generation behavior are preserved.
- Reports retain per-seed counts/cutoffs/exclusions, calibration bins and ECE,
  Brier/log loss, evaluator-only truth errors and interval coverage/width,
  assignment-weighted and represented-cell macro coverage, all 12 cell predictions,
  across-seed variation, and paired global/per-arm/unpooled comparisons.
  Undefined metrics remain null. Repeated cell predictions are not represented as
  independent coverage trials, and Monte Carlo SE is not real-world confidence.
- Added `learn stress` with repeated `--seed`/`--scenario`, count, frozen split,
  calibration bins and exclusive optional JSON output. It never writes ledger rows.
  `docs/STATISTICAL_EVALUATION.md` records complete reproduction and actual results.
- Actual reference experiment: seeds 0–19, 1,000 observations per seed/scenario
  (sparse capped at 48), 60% training split, ten calibration bins. Balanced unpooled
  mean Brier was **0.197198** and latent 95%-interval coverage **0.968000**.
  Homogeneous global Brier **0.211467** beat unpooled **0.216226**. Sparse scenarios
  had 4–8 prior-only cells per seed; imbalance had 1–6 despite 600 training labels.
  Under a sharp 0.9→0.2 drift at the split, unpooled Brier was **0.630445**, coverage
  **0.000000**, and mean interval width **0.168369**: concrete overconfidence.
  Global marginal ECE **0.005608** in heterogeneous balanced data masked conditional
  coverage **0.233375**. Missing/delayed scenarios reduced evidence without recoding
  unknown as failure or admitting future labels. No complex ML was introduced.

### Workstream C — feasibility assessed, no adapter

- `docs/CODEX_DESKTOP_FEASIBILITY.md` records official documented interfaces,
  coverage, reliability, privacy and integration difficulty. The research agent
  used the OpenAI Docs skill, public CLI help and generated installed-version
  protocol schemas; it did not access private transcripts or app databases.
- App-server read-only stored-thread APIs, prospective OTel and lifecycle hooks
  are candidates. Public historical schemas have optional timing/configuration
  and lack complete historical per-turn model/usage. The default public daemon
  control socket was absent (`daemon version` exited 1). Desktop visibility,
  passive connectivity and delivery fidelity therefore remain unvalidated.
- No Desktop adapter, daemon, hook, telemetry setting or control integration was
  installed. Continue supporting explicit CLI capture. The report proposes a
  narrow sanitized public-transport feasibility spike as future work only.

### Actual verification and independent review

Existing local Python 3.12.14 / uv 0.12.24 / Ruff 0.16.10 environment, repository
local tool/cache paths; no dependency installation was needed.

| Command / check | Actual result |
| --- | --- |
| Pre-change `uv run pytest` | Exit 0; **105 passed in 1.45s**. |
| A owned tests / lint / format | **32 passed in 0.69s**; lint passed; 5 files formatted. |
| B learning/storage tests / lint / format | **66 passed in 2.85s**; lint and format passed. |
| Final coordinator `uv run pytest` | Exit 0; **164 passed in 4.94s**. |
| Final coordinator `uv run ruff check .` | Exit 0; `All checks passed!` |
| Final coordinator `uv run ruff format --check .` | Exit 0; **51 files already formatted**. |
| Installed CLI `--help` and `learn stress --help` | Exit 0; new workflow/stress commands and flags present. |
| Real operator-run CLI workflow | Exit 0; four events, safe replay, unknown then verified, eligible real export, one learner label. |
| Independent final suite | **164 passed in 4.72s**; lint and formatting passed. |
| Independent association/task/CLI regressions | **29 passed**; duplicate and concurrent overlap repros resolved. |
| `git diff --check` | Exit 0; no whitespace errors. |

The independent reviewer found no remaining blocking implementation issue within
these workstreams after the regression-tested fixes. Real validation completed
subsequently with the result above. Fixtures remain sanitized/synthetic and real
validation artifacts remain ignored; they are never claimed as Git fixtures.

**Remaining limits:** Digest verification proves exact bytes of one regular file,
not general correctness; a copy of identical bytes satisfies that criterion.
Configuration/boundary declarations are trusted explicit user assertions; native
metadata remains separate. Multi-operation run creation can leave a harmless
unlinked run after exceptional I/O/concurrent failures; the builder rejects it.
The learner still needs explicit resolution when a cohort contains multiple
assessment derivations for one run; this smoke intentionally selected distinct
cohorts for unknown and assessed rows. Simulation uses independent Bernoulli
trials, completely-at-random missingness, independent assignment and simple step
drift; correlated retries, confounding and biased delayed outcomes remain untested.
No synthetic result establishes real calibration. Desktop capture remains
unvalidated; the fixed-reply CLI smoke establishes neither Desktop nor coding-task
performance.

## Decisions

- Use the plan's `src/model_learner/` layout and Typer/Rich CLI.
- Package version comes from `src/model_learner/__init__.py`; Hatchling derives
  distribution metadata from the same value.
- M0 added only foundation dependencies; M1 adds Pydantic and defers later components.
- Pin the development interpreter to Python 3.12; package metadata allows 3.12+.
- Use Pydantic v2 for strict, versioned contracts and the standard-library
  `sqlite3` module for local persistence; preserve each canonical record as JSON
  alongside indexed relationship columns.
- Make the M1 database migration-only: upgrades are forward-only and no downgrade
  path is supplied yet. The first migration creates the complete M1 ledger.
- Treat schema version 1 as a legacy read format and schema version 2 as the
  current M1.1 contract. Future schema versions require an explicit supported
  parser or upcaster; they are not accepted optimistically.
- Preserve project context as an explicit optional relationship. It is a manual
  grouping only and is not task identity, task difficulty, automatic discovery,
  or global activity tracking.

## Historical assessment resolution and drift investigation — 2026-10-10

The coordinator inspected the plan, repository instructions, status, code and
tests before editing. Two implementation subagents had non-overlapping ownership:
observation derivation/resolution and its tests/docs; recent-window inference,
drift evaluation, additive gradual simulation and its tests/docs. The coordinator
owned repository integrity checks, CLI integration, frozen evaluation inputs,
integration tests, package exports, README and this status. A third subagent
performed independent read-only statistical and data-integrity review. Domain
contracts, migrations, dependencies, lockfile and the master plan are unchanged.

### Assessment resolution delivered

- Added pure `resolve_assessment` and persisted-cohort
  `resolve_observation_revisions`, plus read-only evidence-checked
  `resolve_real_observations`. A cutoff includes only available assessment
  revisions and evidence. One complete unbranched visible chain selects its head;
  equal timestamps resolve by lineage. Missing/unavailable or foreign parents,
  backwards edges, cycles, branches, multiple roots and conflicting identities
  fail closed with deterministic diagnostics. Future branches cannot invalidate
  earlier state. Original outcome/evidence/observation rows remain append-only.
- Preserved unknown and censored heads without fallback to older binary labels.
  Exact proof/target/evidence/attribution/resource-budget checks still determine
  learning eligibility. At most one observation per run is returned; stable
  identities and deduplication prevent revisions or replay becoming extra trials.
- Refactored the existing builder into read-only derivation plus the compatible
  idempotent persistence wrapper. Historical learning requires a unique matching
  builder derivation recorded by the cutoff. Its immutable attempt IDs reconstruct
  the earlier declaration set, preserving explicit task-group overrides and
  excluding later declarations. Missing or malformed proof fails closed. Without
  proof, the assessment remains visible but configuration/attribution availability
  is unknown and learning is ineligible.
- Existing task/run session association timestamps and capture observation/ingest
  times are checked independently. Added read-only task/session link access.
  Repository outcome insertion now validates parent identity/run/time and evidence
  time and atomically checks branching with insertion, covering JSONL imports and
  competing writers without a migration.
- Added `observations resolve`. Real `learn predict` resolves the selected cohort
  at its cutoff; real `learn eval` independently resolves training and scoring
  snapshots, so a later censored/revised assessment cannot change frozen training.
  Pure estimator APIs retain explicit resolved-row input and conflict rejection.
  See `docs/ASSESSMENT_RESOLUTION.md` for APIs and limits.

**Historical limits:** Availability follows trusted declared timestamps. Run and
Attempt lack declaration receipts; Verification lacks ingestion receipts. A
persisted derivation proves availability only within those existing contracts,
not actual SQLite insertion time. Without a recorded proof, complete historical
attribution cannot be reconstructed. Snapshots expose these limitations. No
backdated unknown knowledge is promoted to a verified learning observation.

### Drift investigation delivered

- Independently reproduced the original frozen 20-seed stress results. Unpooled
  coverage was balanced **0.968000**, homogeneous **0.945250**, sparse **0.970000**,
  imbalanced **0.949750**, missing **0.961000**, delayed-pending **0.953672** and
  delayed-mature **0.957750**. The sharp split **0.9 to 0.2** drift alone had
  **0.000000** coverage in that suite. Stationary coverage is compatible with the
  stated assumptions in these tested scenarios, not a real-world guarantee.
- Audited the coverage metric and information flow. It checks whether an interval
  contains evaluator-only latent success probability, not whether it contains a
  future binary outcome. A stationary fixed-parameter posterior cannot promise
  current-time coverage after drift. Frozen pre-change training cannot adapt.
  Truth is evaluator-only; training checks decision, record and label cutoffs.
- Added explicit `RecentWindowBetaBernoulli`: fixed Beta prior with labels from
  `[cutoff - window_duration, cutoff)`, using decision age, never arrival age.
  The existing full-history estimator remains the default. No exponentially
  weighted method was added; another uncertain interval convention was unnecessary
  to test the requested simple baseline.
- Added `run_drift_suite` and `learn drift`: block-prequential full-history versus
  fixed 120/300-step windows, 50-step refits, seeds **0–19**, **1,000** decisions
  per seed/scenario and ten calibration bins. Seven scenarios cover heterogeneous
  and homogeneous stationary conditions, abrupt and gradual drift, 85% independent
  missing labels, 98:1:1 assignments and delayed verification. Additive gradual
  simulation preserves existing default fingerprints and seeded prefixes.
- Reports retain per-seed Brier, calibration bins/ECE, empirical current-p coverage,
  widths, assignment-weighted and represented-cell macro coverage, cell sample
  counts, tail metrics, paired differences and adaptation censoring. Adaptation
  requires three consecutive blocks with probability MAE at most 0.1 after drift
  ends. Recovery time has refit-step resolution, retrospective certification and
  survivor-only means; unrecovered seeds are explicitly censored.

| Scenario | Full-history Brier / ECE / coverage | Recent 120 Brier / ECE / coverage |
| --- | --- | --- |
| Stationary heterogeneous | 0.194192 / 0.035466 / 0.965833 | 0.207131 / 0.068866 / 0.959667 |
| Stationary homogeneous | 0.214616 / 0.045822 / 0.954583 | 0.227774 / 0.104458 / 0.959083 |
| Abrupt drift | 0.369329 / 0.440229 / 0.000000 | 0.221218 / 0.165865 / 0.808667 |
| Gradual drift | 0.351974 / 0.379013 / 0.103417 | 0.210493 / 0.120210 / 0.876833 |
| Sparse labels with drift | 0.352703 / 0.412883 / 0.234833 | 0.243423 / 0.241188 / 0.940833 |
| Imbalanced assignments with drift | 0.371025 / 0.442353 / 0.015750 | 0.219452 / 0.151061 / 0.767333 |
| Delayed verification with drift | 0.456481 / 0.528721 / 0.000000 | 0.250000 / 0.300500 / 1.000000 |

Abrupt recovery: full history **0/20**; recent 120 **16/20**, mean **281.25**
steps among recovered seeds; recent 300 **20/20**, mean **300** steps. Last-quarter
abrupt coverage was **0.000000 / 0.972333 / 0.952000**, respectively. Delayed
verification takes 150 steps, longer than the 120-step window: it has **zero**
usable labels, prior-only predictions, and **0/20** recovery. Its 100% coverage is
the broad prior, not useful adaptation or validated nonstationary uncertainty.

Sample-size sensitivity also ran 20 seeds at **240** decisions with fixed
120/300 windows and 50-step refits, then proportionate **29/72** windows and
12-step refits. At 240, a 300-step window equals full history. The fixed 120
abrupt Brier was **0.362787**, versus **0.401582** full history; shorter
proportionate windows gave **0.224872 / 0.253312**, versus **0.356845** full
history. Smaller cells increase prior influence and noise; calibration and
recovery depend on window, cadence, delay and evidence count. These are designed
comparisons, not tuning on held-out outcomes. Full results/reproduction are in
`docs/DRIFT_INVESTIGATION.md` and sanitized `docs/experiments/drift_reference.json`.

**Statistical limits:** Coverage under drift is empirical descriptive coverage,
with no nominal Bayesian claim. Repeated forecasts/cells/blocks are dependent;
independent simulation seeds define replication. ECE is a noisy bin-dependent
diagnostic. Verification missingness/delay are independent of outcomes here.
Real calibration, informative delays, confounding and correlated retries remain
unvalidated. Recent windows improve these drift scenarios but worsen stationary
scores; the experiments do not justify replacing the existing estimator.

### Actual checks and independent review

Existing macOS arm64 Python 3.12.14 / uv 0.12.24 / Ruff 0.16.10 environment;
repository-local tool/cache paths, no dependencies installed.

| Check | Actual result |
| --- | --- |
| Pre-change `uv run pytest` | **164 passed in 4.98s**. |
| Assessment agent relevant tests | **64 passed**; owned lint/format passed. |
| Drift agent recent/drift/simulation/stress tests | **60 passed in 4.39s**; owned lint/format passed. |
| Coordinator final `uv run pytest` | **232 passed in 8.53s**. |
| Coordinator `uv run ruff check .` | `All checks passed!` |
| Coordinator `uv run ruff format --check .` | **61 files already formatted**. |
| Installed CLI resolve/drift help | Exit 0; documented options present. |
| Independent full suite | **232 passed in 7.90s**; lint/format and whitespace passed. |
| Independent statistical verification | Reproduced original 20-seed stress table; checked final 20-seed aggregates against per-seed values; independently reproduced seeds 0/1 for all seven 1,000-decision scenarios. |

Regression tests include historical reconstruction, equal-time chains, corrupted
graphs, conflicting identities/proofs, delayed evidence, future revisions/events/
associations, attribution availability, exact prior attribution after later
declarations, group overrides, unknown/censoring, duplicate learning, concurrent
revision insertion, separate historical train/score states, window boundaries,
late old labels, truth isolation and chronological prediction freezing.
Independent review found no remaining blocking code or statistical issue. No
new real capture was required or attempted; these checks exercise ledger
reconstruction and explicitly synthetic evaluation. The system remains
observational and predictive. No routing, switching, embeddings, fine-tuning,
TUI, cloud sync, Desktop capture or Governor was implemented. No commit, push,
merge, publication or global hook installation was performed. Stop here.

## Coding-task verification and execution-state analysis — 2026-10-10

The coordinator read the plan, repository instructions, status and existing
contracts before implementing the requested two workstreams. Two implementation
subagents used separate ownership: verification modules/JUnit tests and fixtures,
versus execution-analysis modules/tests and controlled examples. The coordinator
owns CLI integration, the observation determinate-evidence guard, CLI integration
tests, README and status. A third agent completed independent read-only review.
Domain contracts, storage/migrations, dependencies, lockfile and master plan are
unchanged. One pre-existing Python code block in the drift documentation received
only the formatting required by the installed Ruff checker.

### Coding verification

- Added bounded, read-only pytest/JUnit XML parsing with per-test identities and
  pass/failure/error/skipped status, separate counts, report hash/reference,
  parser/verifier versions and provenance. Failure messages, stack traces,
  commands and captured outputs are omitted from evidence metadata.
- Acceptance predeclares required test identities. An external binding receipt
  declares task/run, exact acceptance specification, tested artifact SHA-256,
  report SHA-256, generation time, completion and process exit. Association,
  artifact bytes, report digest and result/count consistency are rechecked before
  assessment and observation derivation. The existing file verifier is preserved.
- Missing/malformed/unsupported/contradictory reports, missing required tests,
  skipped tests, unknown completion or unsuitable process exit remain
  indeterminate. Finished execution alone remains unknown. Determinate evidence
  can produce a separately appended verified assessment; indeterminate evidence
  cannot become an eligible binary learning label, including imported claims.
- Added `task create --required-test` and `verify junit ... --artifact ...
  --binding-file ...`. No test process, command or agent is launched by these
  APIs/commands. Sanitized pytest-style fixtures cover passes, failures, errors,
  skips and partial/inconsistent reports. See `docs/JUNIT_VERIFICATION.md`.

### Execution analysis

- Added a pure read-only extractor returning multiple explicit checkpoint
  projections from existing Codex capture events. Both observation and ingestion
  times must be available. Counts, tool lifecycle/status/exit observations,
  per-field token coverage and source evidence IDs remain separate from versioned
  heuristic states. Unsupported observations and unavailable data stay explicit.
- Distinct failed items can establish repeated failures of a tool category or
  named MCP tool. Commands/arguments are redacted; identical-operation retries,
  root causes, loops and stalls cannot be established from these observations.
  Completion/zero exit do not imply tests passed or task success. Unknown native
  duration, cost and verified task success remain null.
- Explicitly scoped run mode accepts validated JUnit evidence with declared
  association/artifact availability and optional evidence availability receipts.
  It compares test status/count changes only for unambiguous report ordering;
  different test sets or incomplete reports cannot establish aggregate progress.
  The current ledger binds reports to one final artifact and observes verification
  after run end. This compares repeated reports of that snapshot; it does not
  reconstruct test progression across intermediate coding edits.
- Added `session analyze ... --checkpoint ...` with repeatable checkpoints for
  event-only inspection. Python run/evidence mode requires explicit receipts.
  Tests and controlled examples cover missingness, replay, future visibility,
  malformed/unsupported events, repeated failures, report binding and changes.
  See `docs/EXECUTION_ANALYSIS.md`.

**Limits:** XML support is a bounded documented JUnit dialect, not all vendor
extensions. Report bindings and receipt timestamps are trusted operator
declarations, not cryptographic attestation of execution. Snapshot hashing covers
one regular file, not repository dependencies/environment. Verification has no
ingestion timestamp in the existing ledger; an explicit analyzer receipt is
preferable, otherwise trusted `observed_at` availability is disclosed. Metadata-only
CLI captures do not contain structured test results. Desktop capture remains
unsupported. These changes do not establish coding-agent performance calibration.

### Checks and independent review

Existing macOS arm64 Python 3.12.14 / uv 0.12.24 / Ruff 0.16.10 environment,
repository-local tool/cache paths; no new dependencies were installed.

| Check | Actual result |
| --- | --- |
| Baseline `uv run pytest` | **232 passed in 9.41s**. |
| A final relevant tests | **103 passed in 2.31s**; owned lint and formatting passed. |
| B final owned unit/integration tests | **38 passed in 0.19s**; owned lint and formatting passed. |
| Coordinator CLI integration tests | **5 passed in 0.62s**. |
| Coordinator full `uv run pytest --junitxml=<ignored path>` | **346 passed in 10.04s**. |
| Coordinator `uv run ruff check .` | `All checks passed!` |
| Coordinator `uv run ruff format --check .` | **75 files already formatted**. |
| Independent full `uv run pytest` | **346 passed in 9.85s**. |
| Independent Ruff lint/format and `git diff --check` | Passed; **75 files already formatted**. |
| Fresh selected pytest report | **1 passed in 0.13s**; actual XML parsed, bound to an unchanged tested module, persisted and assessed as pass/success/verified. |

The full generated pytest XML was **10,537,007 bytes**, exceeding the **10,485,760
byte** parser limit because a security-test parameter embeds a large byte fixture
in its case name. Parsing returned `report_too_large`, without passing evidence.
A fresh bounded report for the predeclared `test_summary_rejects_forged_counts`
then validated the real pytest producer format through parsing, digest binding,
ledger persistence and assessment. These were actual operator-run project checks,
not a coding-agent execution or coding-utility claim. The XML/receipts/validation
ledger remain under ignored `.model-learner/`; no learning observations were made.

Independent review prompted regression-tested fixes for raw private binding
values in CLI errors, acceptance targets unavailable at historical checkpoints,
optional completion-field omission, malformed XML hierarchy/case state, ambiguous
equal-time report comparisons, conflicting/incomplete projections, and dual
acceptance verifier declarations. Wrong task/run/spec/artifact/report associations,
missing/skipped/partial results, delayed receipts and replay are covered. The
reviewer found **no remaining blocking issue** in the requested scope after the
final fixes and complete checks.

No routing, automatic switching, Governor, neural network, CPU fine-tuning, TUI,
agent control, unrestricted command execution, migration or next milestone was
implemented. No commit, push, merge, publication or global hook installation was
performed. Stop after these two workstreams.

## Real coding-task and task-state predictive evaluation — 2026-10-10

The coordinator read the plan, repository instructions, status and existing
implementation before assigning two separate implementation subagents. A owns
the new `benchmark/` package, public task fixtures, benchmark tests and operator
documentation. B owns `learn/task_state.py`, predictive tests, controlled evidence
and methods documentation. The coordinator owns CLI integration, four CLI tests,
README and this status. A third, independent reviewer examined statistical
validity, data integrity, privacy and isolation. Existing domain contracts,
storage migrations, dependencies, lockfile and master plan are unchanged.

### Workstream A: operator-controlled real coding-task harness

- Two predefined public single-module tasks (`clamp`, `duration`) have versioned
  objectives and independent acceptance tests. Preparation predeclares exact
  configuration, task/acceptance, starting fixture and benchmark dataset before
  an agent runs. New disposable roots and all control/results/ledger files are
  outside the protected repository; resolved overlapping paths, symlinks and
  non-regular inputs are rejected.
- Agent execution is exclusively operator-controlled. No API/CLI command launches
  an agent, paid API or arbitrary test command. Operators must supply OS/container
  containment with no repository mount, protect control files, stop/reap the agent
  and its descendants, then separately run the provided acceptance controller.
  Source-tree fingerprints detect protected source changes; they do not replace
  or attest OS containment. Exact inventory exclusions and resource/process
  boundaries are documented in `docs/CODING_TASK_EVALUATION.md`.
- A stopped-run snapshot freezes one candidate module with digest and timing
  checks. The trusted acceptance controller evaluates each test through a separate
  Python worker, independently compares primitive values/errors and creates JUnit.
  Candidate code never imports into the controller. Existing bound JUnit
  verification and append-only assessments are reused; agent completion and
  self-report supply no acceptance label.
- Metadata-only Codex capture preserves source/version, events, receipt times,
  token coverage and native model/provider observations without prompts/outputs.
  Exact operator configuration attribution is retained, with emitted conflicts
  explicit. Unknown costs remain unknown. Missing/partial/malformed/skipped
  evidence, missing telemetry and incomplete executions remain visible; incomplete
  or unverifiable outcomes are unknown. No learning observation is manufactured.
- Public coding tasks always use `source_kind=benchmark`. Dataset IDs end in
  `:real` or `:fixture` to separate real agent runs from controlled fixture checks.
  Finalization validates in a private staging ledger and can retry rejected
  evidence without leaving a partial canonical run. A lock prevents parallel
  finalizers; final publication is not multi-file crash-atomic.
- Added `benchmark tasks`, `prepare`, `show`, `snapshot`, `finalize`, `cleanup`.
  Fixture acceptance covers named tests only. No real coding-agent performance
  run was attempted; the harness is code-complete and fixture-validated, with
  operator-controlled real integration pending.

### Workstream B: frozen task-state predictive evaluation

- Compares A (initial task group/exact configuration), B (A plus simple observed
  event/tool/turn/token metrics and missingness), C (B plus observed failure,
  repeated-failure and failure/unknown-fraction state), and C minus each of the
  three feature groups. Every variant uses identical chronological fit/score
  cutoffs, selected rows and fixed checkpoint horizon. This experiment does not
  replace the existing Beta-Bernoulli learner.
- Initial configuration/association and feature availability receipts are explicit.
  Non-simulated checkpoint facts are rebuilt from retained observed/ingested
  events with run/session/horizon bounds; mismatches and foreign-run leakage are
  rejected. Final JUnit/test state, terminal execution state, final resources and
  outcomes are excluded from predictors. Labels already known at checkpoint are
  excluded. Training-only category vocabulary/scaling, unavailable-future filtering
  before identity conflicts and disjoint task clusters prevent tested leakage.
- Fixed L2 logistic reference has predeclared settings. Reports include Brier,
  calibration bins, label/task counts, exclusion reasons, paired task-cluster
  bootstrap intervals and feature-group ablations. Sparse/single-class cohorts
  return `insufficient_data` and null scores. Intervals condition on the fitted
  model, omit training uncertainty and cross-task time dependence, and ablations
  are exploratory. Selected/missing labels can remain nonrepresentative.
- Added `sim state-fixture`, `learn state-eval`, `learn state-experiment`.
  Portable real/benchmark inputs require prior independently verified,
  historically resolved labels and prospective availability receipts; JSON
  validation is not evidence attestation. See `docs/TASK_STATE_EVALUATION.md`.

Actual controlled CLI experiment: seeds **0–4**, **400 independent tasks per seed**,
60% chronological training prefix, 30-second checkpoint, 300 paired bootstrap
replicates. Eligible training counts per seed were **222, 228, 231, 231, 229**;
scored counts were **153, 150, 151, 154, 153**. Equal-seed mean Brier scores:

| Controlled scenario | A | B | C | B minus C |
| --- | --- | --- | --- | --- |
| Deliberate state signal | 0.249377 | 0.249568 | 0.133440 | 0.116128 |
| Null state signal | 0.251462 | 0.251353 | 0.251842 | -0.000489 |

All five state-signal paired intervals were positive; every null-signal interval
included zero. The favorable fixture shows use of a deliberately generated signal;
the null fixture provides no evidence of improvement. This establishes neither
real-task predictive improvement nor real calibration. Per-seed calibration,
scores, counts, conditional intervals and ablations are retained in the public
`tests/fixtures/task_state/controlled_reference.json`; no private data is included.

### Actual checks and independent review

Existing macOS arm64 Python 3.12.14 / uv 0.12.24 / Ruff 0.16.10 environment;
repository-local tool/cache paths, no new dependencies or paid executions.

| Check | Actual result |
| --- | --- |
| Baseline `uv run pytest` | **346 passed in 14.06s**. |
| A owned unit/integration tests | **24 passed in 2.92s**; owned lint/format passed. |
| B final owned unit/integration tests | **23 passed in 8.22s**; owned lint/format passed. |
| Coordinator CLI integration tests | **4 passed in 0.51s**. |
| Coordinator final `uv run pytest` | **397 passed in 21.39s**. |
| Coordinator `uv run ruff check .` | `All checks passed!` |
| Coordinator `uv run ruff format --check .` | **91 files already formatted**. |
| Independent final full suite | **397 passed in 21.56s**; lint/format and whitespace passed. |
| Actual CLI controlled experiment | Five seeds, two scenarios, six variants per seed; results above. |
| Independent numerical reproduction | All **60 per-seed variant Brier scores** recomputed directly from saved predictions and regenerated labels; agreement within **1e-14**. |

Review prompted fixes for candidate monkeypatching of evaluator builtins,
retry-safe finalization after verifier rejection, captured/configuration conflicts,
origin-specific datasets, candidate/report timing, foreign-run checkpoint
events and consistent synthetic event/tool/turn/usage projections. Regression
tests cover these along with repository/control/candidate
tampering, symlink/path rejection, failure/unknown evidence, capture privacy,
future records/labels, delayed labels, task retries, preprocessing and empty data.
The reviewer found no remaining blocking issue in the requested scope.

No automatic routing, Governor, neural fine-tuning, cloud synchronization,
subsequent milestone, commit, push, merge, publication or global hook installation
was implemented. Stop after these two workstreams.

## Real benchmark safety and controlled pilot preparation — 2026-10-10

The coordinator read the requested design, repository instructions, status and
evaluation documents and inspected the implementation before changes. Two
implementation/research subagents had separate ownership: A owns the containment
audit, diagnostic probe, benchmark safety gates and safety documentation; B owns
the synthetic task catalog, pure pilot preregistration, acceptance fixtures and
operator experiment protocol. The coordinator owns CLI integration, README,
integration tests and this status. A separate read-only reviewer checked the
final implementation and protocol, including the final host-access demonstration.
The master plan, estimator, domain contracts, migrations and dependencies remain
unchanged. No paid coding-agent execution was launched.

### Safety findings and delivered boundary

- The existing harness enforced path separation, immutable snapshots, hashes and
  operator declarations, but no OS containment. Python `-I` and a separate worker
  interpreter do not prevent submitted code from reading or writing host files.
  Source fingerprints detect changes after the fact; they cannot prevent them.
- A controlled local candidate read and overwrote synthetic files outside its
  task directory while passing all six `clamp` acceptance checks. This actual
  harmless test demonstrates the current worker's host access; no private files
  or real Model Learner source were read or modified by that candidate.
- Added `benchmark isolation-probe`: a fixed, five-second macOS diagnostic creates
  disposable synthetic workspace/private/source canaries, checks permitted access
  and attempts forbidden reads/writes, symlink reads and child-process reads.
  It accepts no arbitrary program or private path. Bootstrap failure is reported
  as unavailable with unknown denial results; it cannot masquerade as successful
  confinement. Even a passing diagnostic has `real_execution_ready=false`.
- Real benchmark finalization now refuses collection before creating a lock,
  staging ledger or result: there is no supported, verified containment backend.
  Neither an isolation string, the existing confirmation flag nor a passing
  diagnostic enables it. Preparation, inspection, snapshots and disposal remain
  available; controlled public fixture finalization continues working. Manifest
  origin/dataset consistency checks prevent a single-field origin relabeling.
- The minimal proposed real boundary is a fresh, clean VM with no host shares or
  integration, no agent-readable secrets, a bounded external provider relay and
  a separate credential-free acceptance environment. Required resource limits,
  harmless canary validation and operator receipts are documented. This setup is
  a protocol requirement, not an implemented or validated agent runner.

### Pilot preparation

- Twelve public synthetic single-module Python tasks have versioned independent
  acceptance tests and controlled solution fixtures. Existing `clamp`/`duration`
  behavior is preserved; ten tasks add arithmetic, parsing, sequences and graphs.
  Named tests establish only their stated acceptance criterion.
- `benchmark pilot-plan` accepts two declared configuration files and a fixed
  seed, emits 24 paired runs with balanced arm order, an 8-family training /
  4-family held-out split, and hashes of matching initial source and task text.
  Each run requires a fresh disposable root. It launches no execution and writes
  no evidence or ledger rows. The primary checkpoint is 30 seconds; 10/60 seconds
  are diagnostic only; the agent wall limit is 120 seconds.
- The operator protocol predeclares configuration identities, initial-state
  checks, time/event availability, allowed A/B/C feature groups, independent
  verification, cost/latency provenance and missingness. Hidden acceptance data,
  final outcomes, final resource totals and future telemetry are excluded from
  checkpoint features. A/B/C share the same cohort and cutoffs.
- Current benchmark finalization creates associations and imports telemetry after
  execution. The real observation builder cannot export benchmark observations,
  and each fixture has a separate exact acceptance target. Prospective checkpoint
  export and pooled suite evaluation therefore remain blocked; receipts must not
  be backdated and targets must not be fabricated. The existing predictive floors
  remain 30 training labels, 20 scored labels, five task clusters per partition,
  and both training classes. This 24-run pilot must report `insufficient_data`;
  it cannot establish real predictive improvement.

### Actual checks and independent review

Executed on macOS 26.6.2 arm64 with Python 3.12.14, uv 0.13.0 and Ruff 0.16.10.
The default external uv cache was unwritable; using
`UV_CACHE_DIR="$PWD/.uv-cache"` resolved that environment issue. No dependencies
were added or installed.

| Check | Actual result |
| --- | --- |
| Baseline coordinator `uv run pytest` | **397 passed in 20.69s**. |
| Baseline Ruff lint / format | Passed; **91 files** formatted. |
| A owned benchmark checks | **32 passed in 1.63s**; owned Ruff lint/format passed. |
| B owned pilot checks | **51 passed in 10.29s**; owned Ruff lint/format passed. |
| Coordinator diagnostic/pilot CLI tests | **5 passed** across readiness, paired preparation and private-diagnostic checks. |
| First expanded full suite | **460 passed, 1 failed in 29.23s**: an original CLI test assumed exactly two task IDs. The scoped catalog assertion was updated and its four-test file passed. |
| Final coordinator `uv run pytest` | **462 passed in 34.22s**. |
| Final coordinator `uv run ruff check .` | `All checks passed!` |
| Final coordinator `uv run ruff format --check .` | **102 files already formatted**. |
| Final `git diff --check` | Passed. |
| Independent full suite before final canary demonstration | **461 passed in 32.81s**; Ruff lint/format and whitespace passed. |
| Final synthetic host-access demonstration | Coordinator **1 passed in 0.40s**; independently **1 passed in 0.46s**. Outside synthetic read/write succeeded while all six acceptance checks passed. |
| Actual nested and elevated restrictive macOS canary probes | Both `unavailable`, `sandbox_bootstrap_unavailable`; no successful positive controls or demonstrated denial; outside canaries unchanged. |
| Elevated permissive macOS profile diagnostic | `/usr/bin/true` exited **0**; establishes profile application availability only. Fixed restrictive shell startup diagnostics exited **134** before output. |
| Benchmark CLI help | Passed; includes `isolation-probe` and `pilot-plan`. |

Independent review prompted clarification that +10/+60 are diagnostic horizons,
while +30 is primary. Final review found no remaining actionable defect in this
preparation scope; its final lint, **102-file** format and whitespace checks passed.
The actual restrictive containment profile is unvalidated, and the proposed
VM/relay/candidate transport was not executed. These are real-experiment blockers,
not passing isolation claims. Ready now: operator configuration preregistration,
disposable staging, all-task controlled acceptance rehearsal and recording
protocols in `docs/BENCHMARK_SAFETY.md` / `docs/REAL_EVALUATION_PILOT.md`.

The requested audit/probe attempts and pilot preparation are complete. No real
coding-agent execution, routing, Governor, fine-tuning, cloud synchronization,
web GUI, subsequent milestone, commit, push, merge or publication was performed.

## Offline isolation experiment and benchmark evidence pipeline — 2026-10-11

Read the requested design, repository instructions, status, safety and pilot
documents and inspected the current benchmark implementation. Two implementation
subagents had non-overlapping ownership: A owns `benchmark/offline.py`, its
unit/integration tests and `docs/OFFLINE_BENCHMARK_ISOLATION.md`; B owns
`benchmark/evidence.py`, its unit/integration tests and `docs/BENCHMARK_EVIDENCE.md`.
The coordinator owns CLI integration, pipeline CLI tests, README, updates to the
existing safety/pilot documentation and this status. A separate read-only reviewer
checked security, evidence integrity, statistical semantics and actual containment.
The master plan, domain contracts, migrations, estimator, dependencies and lockfile
remain unchanged. The existing real-execution gate remains unconditional.

### Actual isolated offline experiment

- Existing Docker Desktop **4.94.0 (241994)** / Engine **29.8.2** on macOS
  **26.6.2 arm64**, Linux **7.0.14-linuxkit**, cgroup v2 was available. No system
  software, image, global security setting or daemon was installed/started.
- The fixed probe requires an explicitly approved, locally cached immutable public
  `docker/welcome-to-docker` image. Only
  `sha256:c4d56c24da4f009ecf8352146b43497fe78953edb4c679b841732beb97e588b0`
  is supported in this experiment; absent/unapproved images fail closed without
  pulling. An unspecified image returns `unavailable/image_approval_required`.
- Each fresh container has **zero host mounts**, an unprivileged user, read-only
  root, all capabilities dropped, no-new-privileges, private process/cgroup
  boundary, IPC disabled and **network none**. Host home, credentials, repository,
  hidden tests and runtime sockets are never mounted. The controller uses an empty
  Docker client configuration and minimal environment; actual policy is inspected
  before starting. Only synthetic canaries are probed.
- Limits: **1 CPU, 128 MiB memory with no additional swap, 16 processes, 1 MiB
  task tmpfs, 15-second enclosing deadline, 64 KiB transport/log cap, 1 KiB
  artifact cap and 64 file descriptors**. CPU/memory values were read back from
  effective kernel cgroups, not load-stressed. Actual process creation and task
  storage overflow were refused. A second disposable boundary deliberately hit
  the watchdog with a sleeping descendant; whole-container removal was confirmed.
- Actual worker workspace positive controls passed. Outside synthetic
  repository/source/credential/hidden-test/runtime reads and writes, symlink,
  traversal and child-process reads were denied. Exact network-tool-mode loopback
  positive controls passed before external/host/metadata connections were denied.
  Host canaries were unchanged. No real credentials or source were read by workers.
- Coordinator and independent reviewer each observed
  **`validated/fixed_offline_probes_passed`, all 33 checks true**, zero host mounts,
  fixed-artifact hash
  `b91b66771b6ab7ce8f906c171c351e0f729ec21205db88ed835be3d56e47b048`, and policy
  fingerprint `2fb1b75be291c30610dc7b50e6ef92e1c9c8a17d473dc686fd5064fb68b73061`.
  The reviewer independently found no remaining probe containers. Ordinary
  enclosing-sandbox daemon access returned unavailable; scoped outer-sandbox
  approval permitted only this fixed harmless diagnostic, without broadening
  worker permissions. Every receipt retained **`real_execution_ready=false`**.
- Paused Docker `cp` could not see the task tmpfs and was rejected. Independent
  extraction instead uses a controller-requested stream from the pinned tar tool
  after the fixed worker has finished writing, followed by bounded in-memory
  regular-file validation, exact expected-byte comparison, pause and destruction.
  **Hostile artifact freeze-before-read is not validated.** This synthetic probe
  is not a general candidate runner, independent acceptance transport or paid
  agent execution backend. Cleanup has bounded additional control grace; an
  unavailable/hung daemon or unconfirmed destruction fails closed.

### Offline evidence handoff

- Added source-revalidated `benchmark-evidence/v1` export/import using the existing
  `Observation` contract. It preserves benchmark/task/run/attempt/assessment IDs,
  exact operator configuration and harness provenance, fixture family/version/hash,
  origin-specific datasets, acceptance target and artifact/report bindings.
- Retained native metadata-only events preserve IDs, adapter/emitter versions,
  original observation/ingestion times and safe redaction/missingness metadata.
  Raw transcripts, commands/outputs, candidate/report bodies, hidden case IDs and
  arbitrary native metadata are excluded. Arbitrary configuration metadata is
  rejected rather than hashed into a hidden-label channel or silently rewritten.
- Independent visible verification remains in the audit even for interrupted
  runs whose unknown assessment cites no evidence. Labels use only selected
  assessment-linked independent verification; agent self-report never labels a
  run. Unknown/censored/incomplete outcomes, attribution/configuration conflicts
  and nullable resources remain explicit. Blank or missing required configuration
  dimensions prevent eligibility. No unknown price becomes zero.
- Historical export resolves the visible assessment head and excludes future
  labels, verification, event ingestion and unavailable associations. Export/import
  availability stays actual; no timestamps or scope declarations are backdated.
  Requested checkpoints retain missing-session/unavailable-input reasons. **All
  checkpoint projections remain `eligible_for_task_state=false`** because this
  finalization path has no prospective initial/configuration/scope collector.
- Import requires the retained trusted benchmark root, rederives the whole bundle,
  checks current artifact/report bytes and uses an atomic replay-check/insertion
  transaction. Reimport returns one unchanged observation. An exclusive optional
  output file refuses overwriting prior evidence. No export/import executes code.
- Eligible `:fixture` rows support **algorithm rehearsal only**, not model utility
  measurement. An actual handwritten public clamp candidate passed the existing
  independent acceptance/finalization workflow, then exported/imported twice as
  one eligible fixture observation. The unknown CLI fixture stayed ineligible.
  Synthetic receipt fixtures separately exercised exact-target learner consumption,
  historical revisions, leakage rejection and interrupted verification retention.
- Exact targets and family dependence remain explicit; no suite target, pooling,
  changed estimator or lowered sufficiency floor was introduced. Multiple benchmark
  revisions in one learner input still fail closed as conflicting trials; select
  one immutable revision per evaluation snapshot. This does not add benchmark
  history resolution to the real-only CLI or establish predictive improvement.

### Review and checks

Commands use the existing `.tools/bin/uv` and repository-local `UV_CACHE_DIR`.
Independent review prompted fixes for arbitrary image selection, network-mode
false positives, actual PID/watchdog tests, bounded regular-file checks, missing
checkpoint coverage, interrupted verification retention, configuration metadata
and blank identity dimensions. No remaining actionable issue was found in the
requested synthetic experiment/evidence scope; the real blockers remain below.

| Check | Actual result |
| --- | --- |
| Baseline coordinator `uv run pytest` | **462 passed in 28.63s**. |
| Baseline Ruff lint/format | Passed; **102 files** formatted. |
| A unit/ordinary integration | **16 passed, 1 opt-in runtime test skipped**. |
| A actual opt-in Docker integration | **2 passed in 1.85s** with scoped approval. |
| B final owned tests | **19 passed in 0.67s**; owned lint/format passed. |
| Coordinator pipeline CLI integration | **6 passed in 0.70s**, including actual public fixture acceptance and refusal to overwrite export. |
| Intermediate full regression before A integration file landed | **502 passed in 29.50s**. |
| Coordinator actual Docker CLI | Exit **0**; all **33 checks true**, real readiness **false**. |
| Independent actual Docker replay and cleanup inventory | All **33 checks true**; no remaining probe containers. |
| Final coordinator `uv run pytest` | **503 passed, 1 opt-in test skipped in 30.70s**. The skipped actual test was separately executed successfully by A; coordinator/reviewer also ran the actual probe. |
| Final coordinator `uv run ruff check .` | `All checks passed!` |
| Final coordinator `uv run ruff format --check .` | **111 files already formatted**. |
| Final coordinator `git diff --check` | Passed. |
| Independent final focused evidence/offline/CLI checks | **26 passed, 1 opt-in test skipped in 1.34s**; lint/format/whitespace passed. |

No real or paid agents, production orchestration, routing, Governor, fine-tuning,
cloud synchronization, next milestone, commit, push, merge, publication, global
hook or system security change was performed. Stop after the requested offline
experiment and evidence pipeline.

## Secure execution boundary and CPU task representation — 2026-10-11

Read AGENTS.md, the master plan, status, and current benchmark/execution-state
modules. Two subagents had separate implementation ownership: A owns new
`benchmark/secure.py`, its security tests and `docs/SECURE_BENCHMARK_BOUNDARY.md`;
B owns new `representation/`, its evaluation tests/public fixtures and
`docs/CPU_TASK_REPRESENTATION.md`. The coordinator owns representation CLI commands,
CLI tests, README and this status. Each subagent independently reviews the other's
work read-only. The existing offline isolation and evidence-export workstreams
remain complete. Domain contracts, migrations, probabilistic learner, master plan,
dependencies and lockfile are unchanged.

### A — controller components delivered; real execution blocked

- Added a bounded, bytes-only single-file archive parser and immutable candidate
  object. It accepts only regular `solution.py` bytes, rejects traversal, links,
  device/FIFO/sparse/metadata entries, excess size, duplicate entries and hidden
  trailing data, and never imports or executes candidate source.
- Exclusive freezing pins directory descriptors, refuses symlink parents and
  existing outputs, and validation rechecks bounded current regular-file bytes,
  stable identity and metadata. This is controller-side freezing after transport;
  it does **not** prove hostile writers stopped before transport. Operator-owned
  control directories must remain inaccessible to workers.
- Public fixture envelopes and primitive function requests contain only public
  task inputs. Expected answers, case identities, control/report paths and signing
  material remain controller-side. Responses have size/type/field/request-ID
  checks. Wrong numeric answers fail comparison; missing/malformed evidence emits
  no validation receipt.
- Per-run ephemeral HMAC receipts bind benchmark/task/run, exact fixture and
  configuration snapshot, nonce, candidate/transport hashes and the controller's
  complete ordered comparison transcript. Tamper, foreign controller/run, wrong
  purpose, response replay, duplicate import and repeat finalization are rejected.
  Receipt authentication is in-process only; keys are not persisted or exported.
- Every receipt is `offline_synthetic_controller_only` with
  `real_execution_ready=false`, `runtime_freeze_verified=false` or
  `candidate_execution_attested=false`. They cannot create verified observations
  or satisfy the unchanged unconditional real-finalization gate.
- Actual integration launches only fixed harmless Python workers with an empty
  environment. Public synthetic credential environment canaries are absent; six
  clamp comparisons pass against an opaque non-Python candidate marker, and
  replay to another request is refused. Hostile tests supply only bytes/files;
  no hostile candidate code is executed on the host.

No acceptable exact-agent credential relay or hostile runtime artifact transport
was established. A separate credential-free candidate execution boundary also
remains unimplemented. The fixed Docker probe cannot attest these mechanisms.
One safe real coding-agent benchmark execution therefore remains **blocked**;
no real/paid agent was launched and containment requirements were preserved.

### B — optional local CPU prototype

- New independent representation inputs carry a public/sanitized initial task
  description, SHA-256, availability time, task identity and dependence family.
  The prototype collects no raw transcripts, writes no ledger rows and changes
  neither the probabilistic learner nor agent behavior.
- A uses existing task-group/exact-configuration features; B adds deterministic
  checkpoint metrics, failures, repeated failures and unknown/missing fractions;
  C adds an optional frozen pretrained CPU representation. Final tests, terminal
  states, final resources, outcomes and arbitrary metadata never enter features.
- Frozen chronological cohorts retain exact source/dataset/target/budget selection,
  visible labels and input availability. Task, family and exact description reuse
  cannot cross training/scoring partitions. Non-simulated checkpoint facts require
  retained bounded events; future records, unknown labels and insufficient cohorts
  remain explicit exclusions. Training-only feature vocabulary/scaling and a fixed
  logistic reference use no held-out fitting or fine-tuning.
- A/B/C share scored units. Reports include Brier scores, calibration bins,
  family-cluster paired bootstrap intervals, task/family counts, exclusions,
  reproducibility bindings and component timing/memory measurements. Floors stay
  30 training labels, 20 scored labels, five families per partition and both
  training classes. These floors do not guarantee precision.
- Added `sim representation-fixture` and `learn representation-eval`. Semantic
  loading requires an explicit existing three-file MiniLM safetensors bundle,
  expected bundle hash and full revision identity. Loading uses a bounded private
  snapshot, explicit architecture/tokenizer and CPU inference only; no download,
  remote inference, automatic model selection or software installation occurs.
  Unavailable semantic loading preserves A/B results and null C metrics.
- The current repository environment lacks `torch`, `transformers` and
  `safetensors`, and no local model was supplied. The optional pretrained adapter
  is **integration-pending**. C scores, actual model load/inference overhead and
  actual semantic memory remain unavailable; no semantic improvement is claimed.

Coordinator controlled evaluation: seeds 0–4, 150 simulated tasks per seed,
60% chronological training prefix, fixed +30-second checkpoint, 300 paired family
bootstrap draws. Training labels: **80, 89, 88, 87, 86**; scored labels:
**58, 58, 58, 57, 57**. Every partition has six families. Equal-seed means:

| Controlled scenario | A Brier | B Brier | A minus B | C |
| --- | --- | --- | --- | --- |
| Deliberate state signal | 0.256719 | 0.122489 | 0.134229 | unavailable |
| Null state signal | 0.254266 | 0.258117 | -0.003851 | unavailable |

All five state-signal conditional intervals were positive. In the null scenario,
two intervals excluded zero in opposite directions; six clusters provide limited
uncertainty evidence. These constructed held-out comparisons are algorithm
rehearsal only. They establish neither real predictive improvement nor benefit
from semantic embeddings.

Actual installed CLI rehearsal in a fresh process used seed 1 / 150 public
synthetic tasks: 89 training and 58 scored labels, A/B evaluated and C
`semantic_unavailable`. A feature extraction averaged **0.286 microseconds** and
reference prediction **1.36 microseconds** per checkpoint; B measured
**2.52 / 2.57 microseconds**, respectively. Reference fits took **0.0266 / 0.0682
seconds**. The feature Python-object census was **64,156 / 425,482 bytes** for
147 rows; this excludes other objects and runtime memory. Whole-process lifetime
peak RSS after the run was **52,822,016 bytes**, not incremental component RAM.
These are one wall-clock sample, excluding input parsing/cohort validation, and
are not stable performance guarantees. The semantic FP32 parameter estimate is
**90,800,000 bytes** (rounded 22.7M parameters), excluding runtime, activations
and feature objects; actual semantic memory/inference measurements remain null.

### Checks and independent review

Existing Python 3.12.14 / repository-local uv environment; commands use
`UV_CACHE_DIR="$PWD/.uv-cache"` and `--no-sync` to prevent dependency installation.
No global configuration, software installation, paid execution or subsequent
milestone was performed.

| Check | Actual result |
| --- | --- |
| Pre-change `uv run --no-sync pytest` | **503 passed, 1 opt-in runtime test skipped in 34.16s**. |
| Pre-change Ruff lint/format | Passed; **111 files already formatted**. |
| A final owned unit/integration tests | **40 passed in 0.42s**; owned lint/format passed. |
| Coordinator representation CLI tests | **4 passed in 0.67s**; includes unavailable model and sanitized invalid input. |
| B final owned unit/integration tests | **19 passed in 3.15s**; owned lint/format passed. |
| First combined coordinator suite | **564 passed, 1 opt-in runtime test skipped in 32.89s**. |
| Combined Ruff lint/format and whitespace | Passed; **123 files already formatted**. |
| Actual installed representation CLI rehearsal | Exit **0**; 150 public synthetic inputs, A/B evaluated, C unavailable; measured overhead above. |
| Independent A security review/checks by B | **40 passed in 0.36s**; no actionable defect in synthetic scope; real credential/runtime blockers confirmed. |
| Final combined coordinator `uv run --no-sync pytest` | **566 passed, 1 opt-in runtime test skipped in 34.05s**. |
| Final coordinator Ruff lint/format and whitespace | Passed; **125 files already formatted**; `git diff --check` passed. |
| Independent final B evaluation and parent CLI checks by A | **23 passed in 3.74s**; owned lint/format and whitespace passed. |
| Independent numerical reproduction by A | All **10 stored reports** matched exactly for cohort digests, counts, metrics/calibration/intervals, comparisons and methods; C remained unavailable. |

Independent security and evaluation reviews found no remaining actionable defect
within the delivered offline scope. Review prompted fixes for bounded hostile
integer/error responses, archive metadata prechecks, frozen-file identity/size
checks, exact configuration snapshot identity, task versus family denominators,
incomplete pretrained weight rejection and native future-ingestion/fact tests.
Actual runtime/credential mechanisms and pretrained model compatibility remain
unvalidated blockers, not passing claims. The pre-existing `.DS_Store` modification
was preserved. No AI Governor, automatic switching, fine-tuning, software install,
paid agent, commit, push, merge or publication was performed. Stop after these
two workstreams; await user direction.

## Pretrained CPU semantic C evaluation — 2026-10-11

The user confirmed no existing model was configured, accepted the previous A/B
work, requested completion of C and approved `minishlab/potion-base-8M` weights.
After compatibility inspection, the user separately approved installing pinned
CPU dependencies in the repository's optional environment. Read the repository
instructions, relevant learning/evaluation plan, prior status and C implementation.
One implementation subagent owns only `representation/potion.py` and its guard/
actual-model tests; a separate read-only subagent independently reviews model
provenance, CPU/privacy, evaluation and reproduction. The coordinator owns narrow
semantic dimension/metadata support, explicit CLI selection, optional dependencies,
the fixed experiment reproducer, integration tests, reports and documentation.

### Identity, compatibility and delivered behavior

- The original C loader is a strict 384-dimensional MiniLM BERT adapter. Potion is
  a 256-dimensional pretrained Model2Vec static embedding model, so it is not a
  direct drop-in. A separate narrow adapter retains the text-to-vector interface;
  the evaluator now validates either supported dimension. A/B input features,
  cohorts, numerical fitting, cutoffs, bootstrap policy and old reference artifact
  are unchanged. The explicitly preferred lightweight model was retained.
- Confirmed public identity, MIT license, 256-dimensional configuration and file
  sizes **before downloading**. Model revision is
  **`bf8b056651a2c21b8d2565580b8569da283cab23`**. Three files total **30,920,628 bytes**;
  the F32 table is **29,528 × 256**, **30,236,672 bytes** / 7,559,168 parameters.
  Weights match published upstream SHA-256
  `f65d0f325faadc1e121c319e2faa41170d3fa07d8c89abd48ca5358d9a223de2`.
  Approved bundle SHA-256 is
  `930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2`.
- Downloaded public unauthenticated revision-pinned `config.json`,
  `model.safetensors` and `tokenizer.json`, checking exact upstream identities and
  size. Weights/download receipts are in ignored `.model-learner/models/`; Git
  exclusion was checked. No private description/transcript was downloaded/uploaded.
- Added optional `semantic` dependency **`model2vec==0.9.0`**, with all dependencies
  locked in `uv.lock`. Actual core CPU packages: NumPy **2.5.4**, safetensors
  **0.8.0**, tokenizers **0.23.3**. Installation changed only the approved local
  project environment; no global configuration or software was changed.
- The local loader copies bounded no-follow regular files into a private snapshot
  and checks the supplied bundle hash plus fixed approved file identities before
  constructing the audited static model from NumPy arrays/local tokenizer. No Hub
  loading helper, model-supplied code, pickle, GPU or remote inference is used.
  Weights are read-only; incomplete/incompatible matrices and tokenizer IDs fail.
  Missing/bad explicit Potion loads remain unavailable and cannot fall back to
  another model; reports identify the requested Potion backend correctly.
- Inference uses only bounded public/sanitized descriptions, max 4096 characters,
  256 tokens, batch size one, no multiprocessing, mean token pooling and L2
  normalization. The runtime first truncates characters to
  `256 * median_token_length`, then tokens. Unknown tokens are removed; no-known-
  token text produces a zero vector. No fine-tuning, switching or private collection.
- `learn representation-eval --model-id minishlab/potion-base-8M` requires explicit
  local model path, full approved revision and bundle hash. The previous optional
  MiniLM default remains intact. `representation.potion_experiment` reproduces
  only the same fixed ten public simulated cohorts in fresh subprocesses, refuses
  output overwrite and fails if original A/B metrics/cohort hashes change.

### Actual held-out predictive evidence

New `tests/fixtures/representation/potion_reference.json` retains all ten
pretrained reports (state/null scenarios × seeds 0–4), without description text,
model weights or per-run predictions. Data/settings match the prior reference:
150 simulated tasks per seed, 60% chronological fit, **2026-01-01 04:30 / 07:30
UTC** cutoffs, +30-second checkpoint, 300 paired family-bootstrap draws. Training
counts remain **80, 89, 88, 87, 86**; scored counts **58, 58, 58, 57, 57**; six
training/six held-out families. All A/B scores, intervals, calibration, paired
comparisons, counts and cohort hashes match the original artifact exactly.

| Scenario | Mean A Brier | Mean B Brier | Mean C Brier | Mean B minus C |
| --- | --- | --- | --- | --- |
| Deliberate state signal | 0.256719 | 0.122489 | 0.122641 | -0.000152 |
| Null state signal | 0.254266 | 0.258117 | 0.258446 | -0.000329 |

Positive B minus C means C improves. All five state-signal paired 95% intervals
include zero. Null seed 4 has a positive interval **[0.000056, 0.000736]**;
the other four include zero. Full per-seed C Brier intervals, paired differences
and calibration bins are in the artifact and methods document. There is
**no consistent semantic improvement**. Intervals condition on fixed fits with
only six scored families and no multiplicity correction; seed means are
descriptive, not pooled confidence intervals.

The existing invented descriptions are independent of outcomes and struggling
state, so these fixtures contain no designed semantic outcome signal. This is
real pretrained **CPU inference on synthetic evaluation data**, not evidence of
real-world task understanding or model utility. A null/negative result on these
fixtures cannot show that embeddings are useless on real tasks.

### Actual loading, inference and memory measurements

Ten fresh Python 3.12.14/macOS arm64 workers use a minimal environment, requested
single-thread CPU limits, disabled tokenizer parallelism/multiprocessing and
socket connection guards before loading/inference. All reported **zero network
connection attempts**. OS caches were not cleared. Serial latency measures five
passes over the same scored public descriptions after evaluation warmup.

| Component | Actual result |
| --- | --- |
| Fresh-process model loading, including imports/snapshot/hash checks/construction | **0.167–0.264 s**, mean **0.192 s**. |
| First-description warmup | Mean **3.83 ms**, separate from loading and steady inference. |
| Embedding throughput | Mean **52.97 microseconds/description** over selected rows. |
| Warm serial description latency | Worker medians **58.33–59.88 microseconds**, p95 **62.04–65.71 microseconds**; 285–290 samples per worker. |
| Fixed C reference prediction | Mean **25.83 microseconds/checkpoint**, separate from embedding. |
| Fixed C reference fitting | Mean **0.603 s**; not encoder fine-tuning or inference. |
| Actual F32 embedding-table memory | **30,236,672 bytes**; excludes tokenizer/runtime. |
| Whole fresh-process peak RSS | **139,575,296–140,345,344 bytes**, including load/features/fits and latency measurements. |

Embedding latency includes output conversion/validation but excludes C feature
dictionary assembly, B feature extraction, cohort parsing and reference prediction.
Peak RSS is a process lifetime high-water mark, not incremental model RAM. C
feature-object census averages **4,055,355 bytes**; object census and timing are
descriptive measurements, not guaranteed worst-case resource requirements. These
short public descriptions do not establish long-input latency. All actual phase
measurements/runtime/model identities are retained; no semantic measurement is null.

### Checks and independent review

Use the approved optional environment (`uv sync --locked --extra semantic`).
Actual-model tests opt in with `MODEL_LEARNER_TEST_POTION_PATH` pointing to the
approved ignored bundle; tests never discover/download weights automatically.
Checks use repository-local cache/tools and `uv run --no-sync` to preserve it.

| Check | Actual result |
| --- | --- |
| Adapter owned actual/protocol checks | **31 passed in 0.47s**, including approved pretrained inference with sockets blocked. |
| Coordinator focused representation/Potion/CLI checks | **57 passed in 5.28s**. |
| Coordinator full suite with actual-model opt-in | **600 passed, 1 skipped in 37.06s**. Sole skip is unchanged offline Docker runtime opt-in. |
| Coordinator Ruff lint/format and whitespace | Passed; **129 files already formatted**; `git diff --check` passed. |
| Independent full suite with actual-model opt-in | **600 passed, 1 skipped in 37.65s**; lint/format/whitespace passed. |
| Independent canonical numerical reproduction | All **ten reports** match exactly for complete A/B/C score/calibration/interval results, paired comparisons, cohort hashes, counts, exclusions and methods. |
| Independent privacy/leakage/replay checks | Actual CPU load/encode succeeds with sockets disabled; exact embedding replay; input reversal and held-out label changes preserve predictions. |
| Protected baseline/boundary diff check | Original A/B reference, feature inputs, benchmark and execution modules unchanged. |
| Actual installed Potion CLI rehearsal | Exit **0**; seed 1 has 89 training / 58 scored rows, all A/B/C evaluated and C Brier **0.057289**. |

Review found and prompted fixes for unavailable-model identity/estimates and a
protocol-test compatibility regression, plus a formatting issue; focused/full
checks pass after repair. Guard tests cover bad revision/hash/file identity,
unsafe files/paths, incomplete matrices and bounded text/output. Independent
final documentation review confirms measured results and limitations, with no
remaining blocking finding. Historical dependency wording and repository-local
tool instructions were clarified. The pre-existing `.DS_Store` modification was
preserved.

No real coding agent, cloud/paid inference, Governor, automatic switching,
fine-tuning, benchmark boundary change, commit, push, merge or publication was
performed. Stop after C; no additional milestone is authorized.

## Semantic task understanding and relevance evaluation — 2026-10-11

Read the user request, AGENTS.md, current STATUS, relevant observation/identity,
privacy and evaluation plan sections, existing CPU encoder, representation and
task-state evaluators, documentation and tests before implementation. The main
agent owns architecture, CLI integration, README and this status. Non-overlapping
subagents own retrieval plus unit tests and dataset/evaluation/reproducer plus
their tests/docs. A third read-only reviewer independently checks labels,
leakage, false associations, privacy, performance and numerical reproduction.
The pre-existing `.DS_Store`, `pyproject.toml` and `uv.lock` changes are preserved.
No dependency, domain schema, master plan, learner or benchmark boundary changes
were needed for this increment.

### Delivered subset and limits

- `understanding/retrieval.py`: bounded in-memory description retrieval with
  deterministic token Jaccard, candidate-only TF-IDF and optional frozen Potion
  cosine. Explicit public/sanitized/declared input provenance, max 4096 characters
  per description and 10,000 candidate tasks; no transcript discovery or retention.
  Scores are inferred relatedness, never calibrated continuation/success
  probabilities. Zero/unknown representations remain unknown. Finite vectors,
  dimensions, deterministic ties and self exclusion are checked.
- `understanding/evaluation.py`, `experiment.py` and
  `tests/fixtures/understanding/`: authored relevance dataset, frozen SHA-256
  manifest, metrics and actual three-worker-per-backend reference measurements.
  Labels are technical judgments written by a separate evaluation agent before
  any encoder invocation, independently inspected by the reviewer; they are not
  derived from the encoder. They lack independent external human adjudication.
  Text is newly constructed and reviewable, with no third-party/private content
  or asserted external license. No outcome-success labels exist in this dataset.
- `model-learner task similar TASK_ID`: optional read-only shortlist command,
  TF-IDF default; `--backend text` or explicitly pinned local `--backend potion`.
  Returns distinct task IDs, similarity scores, explanation, provenance and
  exclusion/unknown counts without description text. Candidate creation
  declarations cannot be later than the query's declaration; this is not an
  attestation of historical ingestion availability. Model absence/bad pins return
  `semantic_unavailable` and no fallback suggestions. Other commands still work.
- Similarity never creates associations or changes task identities. Explicit
  task/session/run links remain authoritative. Shared sessions and equivalent
  descriptions do not establish continuation; integration tests retain distinct
  tasks with identical descriptions and a shared session. No continuation
  classifier is delivered or assigned classification metrics.
- This intentionally chooses the smallest reliably evaluable subset: related-task
  retrieval. Characteristic/ambiguity/dependency inference and evolving-scope or
  implementation-to-debugging detection remain unimplemented. Scope-diverged
  descriptions are hard retrieval negatives, not a longitudinal evolution test.
  No sanitized execution-summary collector or semantic utility features are added.

### Frozen relevance evidence

Dataset `authored-semantic-retrieval-v1`, frozen content SHA-256
`75a4208dea16b4aec6c6d3cfa59d5e29f67f2c028a70823f49cf56baf9b4000d`.
Development: four queries, two families/projects, twelve candidates. Locked test:
twelve queries, six families/projects, thirty-six candidates, two relevant tasks
per query. Family, project and query rewrite groups are disjoint between splits;
TF-IDF fits only the candidate corpus of the selected split. Query-to-historical
same-family matches are intended retrieval targets, not supervised training.
No thresholds or parameters are chosen from the locked test. Labels, family and
project annotations do not reach the retrieval index. Full known rankings use
fixed deterministic ties; unknown representations receive no retrieval credit.

| Locked-test method | Precision@1 | Precision@3 | Recall@3 | MRR | nDCG@3 |
| --- | --- | --- | --- | --- | --- |
| Token Jaccard | 0.250000 | 0.277778 | 0.416667 | 0.439316 | 0.352191 |
| TF-IDF | 0.250000 | 0.277778 | 0.416667 | 0.452649 | 0.358881 |
| Pinned Potion | 0.333333 | 0.416667 | 0.625000 | 0.574537 | 0.525548 |

Potion recovers fifteen of twenty-four relevant top-three slots versus ten for
either lexical baseline. Top-one relevant results improve only from three to
four of twelve; eight Potion first suggestions remain irrelevant. All six
original wording-trap queries choose their high-overlap wrong-objective distractor
first for every backend. Potion improves paraphrased duplicate-payment retrieval
(two relevant top-three results versus zero lexical), but confuses paraphrased
authentication concurrency with an unrelated payment regression test, and still
ranks changed-scope descriptions too highly. Scores require human review.

Two correlated rewrites per family and one repeated candidate structure make
this a small purposive six-family experiment. Means are descriptive; no population
confidence interval, significance claim, real-task accuracy or success-prediction
claim is warranted. The measured improvement supports only optional shortlist
exploration. It does not justify semantic decisions, automatic grouping or
feeding embeddings into the Bayesian estimator. Earlier synthetic outcome
prediction remains unchanged and has no consistent semantic gain.
The reviewer found two mixed-relevance text-baseline cutoff ties where frozen
task-ID ordering favors the positive label; TF-IDF/Potion have no such top-one or
top-three boundary ties. Potion's gain against TF-IDF is unaffected. A future
dataset should use opaque IDs. Potion's Recall@3 improves in four of six families
and worsens in the keyboard and query-plan families.

### Actual CPU measurements

Three fresh workers for each backend, Python 3.12.14/macOS arm64, requested
single-thread limits, tokenizer parallelism disabled, socket connections blocked
before loading. Every worker reports zero connection attempts. OS caches were
not cleared. Five warm serial passes measure twelve test queries against the
same thirty-six candidates; timings are descriptive, not large-ledger estimates.

| Component | Measured range across workers |
| --- | --- |
| Potion model loading, runtime imports/snapshot/hash/construction | 0.178–0.264 seconds |
| Potion warm single-description median encoding | 62.50–68.29 microseconds |
| Potion warm query median, including encode/score/sort | 0.4397–0.4636 milliseconds |
| Text warm query median | 0.0388–0.0436 milliseconds |
| TF-IDF warm query median | 0.0427–0.0435 milliseconds |
| Potion embedding table alone | 30,236,672 bytes |
| Whole Potion worker peak RSS | 132,202,496–132,235,264 bytes |
| Whole lexical worker peak RSS | 38,502,400–38,600,704 bytes |

Whole-process peak RSS is a lifetime high-water mark, not incremental model RAM.
Index construction/model loading are excluded from warm query time and reported
separately in the artifact. These short descriptions and tiny indexes do not
establish worst-case CPU/latency. Overhead buys a narrow top-three relevance gain,
but poor top-one precision and insufficient data favor keeping TF-IDF default.
Fine-tuning is not justified by this evidence; acquire independently human-reviewed
labels and a larger project/family-disjoint test first.

### Validation and next step

- Pre-change full suite: **598 passed, 3 skipped in 35.84s** (model/Docker opt-ins
  absent in this initial check).
- Retrieval owner's focused checks: **42 passed in 0.15s**, Ruff lint/format and
  whitespace passed.
- Coordinator final registered CLI focused tests with sockets blocked:
  **6 passed in 0.65s**, including malformed-ledger privacy diagnostics.
- Evaluation owner's focused actual-model checks: **22 passed in 0.38s**;
  owned Ruff lint/format passed.
- Independent reviewer exactly reproduced all three backends' development/test
  stored top-three similarity scores, relevant-target ranks, per-query/family
  metrics and provenance with socket connections blocked; zero attempts. Timing
  fields are intentionally not compared.
- Coordinator final `uv run pytest`: **670 passed, 1 skipped in 38.73s**.
  The unchanged Docker integration opt-in is the sole skip. Actual pinned model
  tests are enabled via the explicit `MODEL_LEARNER_TEST_POTION_PATH`.
- Coordinator `uv run ruff check .`: **All checks passed!**
- Coordinator `uv run ruff format --check .`: **139 files already formatted**.
- Final `git diff --check`: passed. Checks use the repository-local uv/cache and
  `UV_NO_SYNC=1` to preserve the installed approved optional semantic runtime.
- Independent reviewer full actual-model run before the final added metric test:
  **669 passed, 1 skipped in 38.20s**, lint/format/whitespace passed. The
  coordinator's final run above includes that additional test.

Independent review found no remaining blocking defect in the delivered scope.
It prompted pre-encoding provenance corrections, disclosure of text tie-order
sensitivity, precise reported-ranking wording and updating status resource ranges
to the final stored artifact. External human adjudication, diverse negative
objectives and no-relevant-history cases remain evaluation limitations.

See `docs/SEMANTIC_TASK_EVALUATION.md` for provenance, reproducer, per-capability
limitations and error analysis. The next recommended increment is larger
independently human-adjudicated retrieval data with diverse real-world objectives,
plus explicit success criteria and changing-scope labels before extending task
understanding. No fine-tuning, routing, paid agent execution, web GUI, remote
inference, model downloads, Governor or utility-estimator integration was performed.
Stop after this requested increment; the recommended next increment is not started.

## Task annotation workflow and evaluation protocol — 2026-10-11

Delivered only the requested preparation/evaluation increment. The original
retrieval v1 fixture and its reference results remain frozen. No new retrieval
accuracy, task-classification accuracy or model-utility improvement is claimed.

- `understanding/annotations.py` defines strict `task-annotations/v1` local
  artifacts with task-description snapshots, optional caller-declared canonical
  task UUIDs, source SHA-256/locators/authorship, split/project/family/lineage,
  timezone-aware availability and separately sourced observed facts. Facts retain
  their own real/simulated/benchmark origin; judgments always remain inferred.
- Complete per-query candidate judgments separately record similarity,
  continuation, scope and apparent-difficulty changes, rationales, evidence
  references and hard negatives. Query-level no-match is yes/no/unknown; yes
  requires every candidate explicitly irrelevant in that frozen corpus. Unknown
  judgments remain unknown. Distinct explicit canonical task IDs cannot be
  overridden by a continuation label, and annotations never create ledger links.
- Human author identity and independent reviewer identity/kind/time are explicit
  caller attestations. Accept/reject reviews bind to descriptions, provenance and
  labels by content hash. Self-review (including case/whitespace variants), stale
  reviews, agent-only labels/reviews, missing annotations and unresolved rejection
  block freezing. Relabeling invalidates current reviews; exclusive revision files
  retain prior decisions and a parent-content digest. Identities are not authenticated.
- Split checks reject shared projects, families, lineages, canonical task IDs,
  normalized description copies and exact source records across train/development/
  test, including a source used as a description in one split and a fact in another.
  Facts cannot postdate their snapshot; historical candidates cannot postdate the
  query. Unknown correlations and source-locator aliases still require human audit.
- Freeze locks data and a prospective backend/k/strict score threshold/selection
  note plus Potion revision/hash where applicable. Evaluation requires the frozen
  human-reviewed artifact before model loading. Only descriptions enter retrieval;
  TF-IDF fits candidate text only, and labels/groups/facts enter reporting afterward.
- `understanding/annotation_evaluation.py` reports per-query/family and aggregate
  TP/FP/FN/TN, precision, known-target recall, pairwise false-positive rate,
  hard-negative errors, no-match false acceptance, coverage and abstention. Unknown
  labels are excluded from confusion denominators and counted separately; unknown
  representations are separate operational abstentions. No-match recall and other
  empty denominators are null. Precision@k retains the requested slot denominator.
  Continuation/scope/difficulty have label coverage only, with no classifier or
  fabricated predictions. The protocol documents their future independent tests.
- `commands/annotations.py` and CLI registration provide `annotation prepare`,
  `show`, `label`, `review`, `freeze` and `evaluate`, all using explicitly supplied
  local files, exclusive output creation and privacy-safe malformed-input errors.
  No ledger access, transcript collection, network inference or automatic fallback.
- `tests/fixtures/understanding/annotations/` contains 18 snapshots and nine
  complete **agent-authored draft proposals**, with three independent example
  cohorts. Three historical descriptions reuse frozen sanitized v1 text; one
  context fact reuses the simulated controlled execution fixture. Source hashes
  are verified in tests. UUIDs/checkpoints are hypothetical benchmark context,
  not real ledger records. These public exposed examples are workflow rehearsals,
  not a fresh held-out human-reviewed accuracy dataset.
- `docs/TASK_ANNOTATIONS.md`, the root README and a pointer in the original
  semantic-evaluation doc explain collection, independent review, rejection,
  versioning, leakage checks, development-only policy selection, exact metric
  denominators and limitations. Existing TF-IDF/Potion code and learner semantics
  are unchanged; no security boundary or database migration was modified.

### Actual validation and independent review

macOS arm64 / Python 3.12.14. Used the existing `.tools/bin/uv` and repository-local
`UV_CACHE_DIR=$PWD/.uv-cache`; the default global cache is outside sandbox writes.
No packages, model weights or paid agents were provisioned for this increment.

| Check | Actual result |
| --- | --- |
| Initial full `uv run pytest` during implementation | **720 passed, 5 skipped in 32.10s** before the final source-overlap/fixture/model tests; optional model path absent. |
| Focused annotation unit + CLI checks after review fix | **56 passed in 1.38s**; independent reviewer separately reproduced **56 passed in 1.63s** before two further encoder tests. |
| Final full `uv run pytest` with `MODEL_LEARNER_TEST_POTION_PATH` set to the existing approved `potion-base-8M-bf8b056651a2c21b8d2565580b8569da283cab23` local bundle | **728 passed, 1 skipped in 33.33s**. Includes all 58 new annotation tests and actual pinned local Potion evaluation, with socket connections denied in the new model test. The remaining skip is the existing explicitly enabled Docker offline isolation check. |
| `uv run ruff check .` | **All checks passed!** |
| `uv run ruff format --check .` | **146 files already formatted** |
| `git diff --check` | Exit 0; no whitespace errors. |
| `uv run model-learner annotation --help` | Exit 0; all six operations displayed. |

Independent subagent implementation review inspected contracts, evaluator, CLI,
tests, provenance and claims. It found one P2 split-leakage gap: description and
fact source origins used separate namespaces. Fixed by checking both against the
same source-location namespace, with a cross-role regression. Reviewer verified
the correction and found no remaining semantic/provenance/privacy/metric blockers.
Its final formatting observation was corrected and the final checks above passed.
This is independent code review, **not independent human annotation review**.
The documentation reviewer authored the protocol prose but did not implement the
schema, evaluator or CLI. Implementation/CLI and example-authoring subagents had
separate file ownership.

The workflow and protocol are complete. Actual realistic human label collection,
adjudication and prospectively unexposed test cohorts remain pending and must occur
before substantive task-understanding accuracy claims. Hidden cohort aliases,
honest human attestations and no test-driven policy selection require operator
discipline. Retrieval evaluation remains separate from model-utility prediction.
No fine-tuning, larger model download, paid agent, routing, security-boundary
change, web GUI, commit, push, merge or publication occurred. Stop here.

## First independent human semantic-review batch prepared — 2026-10-11

Read AGENTS.md, the master plan, status, annotation protocol, original semantic
evaluation documentation, annotation CLI/contracts/evaluator and workflow tests.
This is data preparation and review guidance, not a feature milestone. No
implementation blocker was found, and no source code, dependency, schema,
database, model, or frozen prior experiment was changed. Pre-existing tracked
`.DS_Store`, `pyproject.toml`, and `uv.lock` modifications were preserved.

- Prepared ignored local `.model-learner/annotations/semantic-human-review-v1/`:
  source material, `seed.json`, CLI-created `collection-000.json`, a neutral query
  inventory, 40 blank forms in the existing query-judgment format, and local
  inspection/author/reviewer/revision directories. The collection identity is
  `semantic-human-review-v1`, schema `task-annotations/v1`, source kind `benchmark`.
- 40 newly agent-authored realistic technical queries and 32 historical snapshots
  cover eight project/family cohorts. Development has 10 queries and 8 candidates;
  test has 30 queries and 24 candidates. Complete per-query labeling requires
  **800 pair judgments**. Project/family/lineage groups are disjoint between splits;
  correlated variants stay together. IDs are neutral and order is shuffled.
- Material includes related/independent work, wording traps, different-wording
  technical equivalents, shared-capability/different-objective comparisons,
  explicit continuations, absent identity declarations, changed objectives under
  retained task identity, unrelated tasks, and intended no-history cases. These
  construction intentions are not judgments: actual relevance/no-match counts
  await exhaustive human assessment against the full split candidate pool.
- All descriptions, UUIDs and availability checkpoints are hypothetical benchmark
  context. No real history, private transcripts, execution facts, or outcomes were
  collected. Source locators refer to inspectable `authored_descriptions.json`,
  SHA-256 `2cede15f28ac8f193d7eb1a73a87efab24ba90fc7d515c9be073b6e0a908188b`.
  No prior retrieval fixture text/labels were reused. All data stays local/ignored.
- Zero annotations, zero reviews, no selected protocol/freeze, and no scores,
  rankings, or evaluation reports. Forms have unknown dimensions and empty
  rationales, intentionally failing submission until completed by a human.
- `docs/HUMAN_REVIEW_BATCH.md` provides chronological exact commands to inspect,
  author labels, independently accept/reject, correct, re-review, freeze, and
  later evaluate. It separates objective similarity, shared capability context
  in the existing rationale, and explicit identity/continuation. No capability
  label field or second annotation system was introduced. Two distinct actual
  humans must review source material without score exposure; software/agent
  review cannot substitute for human annotation review.
- The guide proposes a prospective fixed k=3, strict score >0 comparison for
  TF-IDF and the existing pinned Potion bundle, with separate frozen artifacts
  before held-out evaluation. This is not a calibrated rejection policy. Freeze
  and evaluation commands are provided for the operator, **not executed** here.

### Actual preparation checks

Existing macOS/Python 3.12.14 environment; `.tools/bin/uv`, repository-local
`UV_CACHE_DIR`, and `--no-sync` preserve installed dependencies. No installation
or model download occurred. Existing tests use separate fixtures, not labels for
this batch.

| Check | Actual result |
| --- | --- |
| `uv run --no-sync model-learner annotation prepare ... --dataset-id semantic-human-review-v1` | Exit 0; exclusively created pending `collection-000.json` with parent seed digest. |
| `uv run --no-sync model-learner annotation show ... --query-id q-93b477` | Exit 0; one query and all 24 test candidates, with no labels or model scores. |
| Local structural/source audit | Passed: exact counts, all source hashes/locators, complete candidate forms, checkpoints, split validation, and parent digest; all 40 unchanged blank forms reject submission. Human-review completeness gate rejects the pending collection. No frozen artifact/report exists. |
| `uv run --no-sync pytest tests/unit/test_task_annotations.py tests/unit/test_semantic_evaluation.py tests/integration/test_annotations_cli.py` | **78 passed, 2 skipped in 1.77s**. Skips are existing explicit local-model opt-ins; no actual-model test was enabled for this data-only activity. |
| `uv run --no-sync ruff check .` | **All checks passed!** |
| `uv run --no-sync ruff format --check .` | **147 files already formatted** |
| `git check-ignore` for seed/collection | Both files ignored under `.model-learner/`. |
| `git diff --check` | Passed. |

Batch preparation is complete. Manual source/context audit, genuine human labeling
and independent acceptance are still required before finalizing or evaluating.
The evidence will remain a small constructed benchmark even after human review;
it does not establish population accuracy on real task history, continuation
prediction, shared-capability classification, or model utility. No new models,
fine-tuning, routing, Governor, subagent, commit, push, merge or publication.
Stop here; the next action belongs to the human annotator and independent reviewer.

## First longitudinal task-state understanding — 2026-10-11

Read the plan, repository instructions, existing status, task-state/semantic/
annotation documentation and relevant code before implementation. A review
subagent independently audited evidence and later reviewed provenance, temporal
leakage, feature correctness, unsupported semantic inference, privacy and evaluation.
A separate implementation subagent owned only the synthetic evaluator, fixture
and its tests; the coordinator owned projections, CLI, integration and documentation.
No core architecture change or new database migration was needed. The pre-existing
working-tree changes to `.DS_Store`, `pyproject.toml` and `uv.lock` were preserved;
this increment did not alter them or add dependencies.

### Evidence audit and delivered behavior

- The real checked-in Codex derivative has four metadata-only buffered smoke
  events, without tools, code edits, semantic text or verified coding outcomes.
  Rich execution/JUnit/predictive/retrieval fixtures are explicitly synthetic.
- Safe aggregate inspection of ignored local ledgers found one genuine verified
  fixed-reply smoke observation plus its earlier unknown derivation, and a
  separate operator-run JUnit producer validation without execution events or
  learning observations. Smoke task/association availability follows captured
  events and cannot be backdated. There are **zero suitable real longitudinal
  coding trajectories** for this evaluation, not zero verified records anywhere.
  The audit read no description, raw payload or private transcript contents.
- `execution.longitudinal` reuses the existing checkpoint extractor and domain
  contracts. Identity/objective is separate from evolving state. Observed event
  receipts and retained tool/test evidence, derived counts/deltas/failure groups,
  inferred author phase/progress/scope/difficulty hypotheses and unknowns remain
  explicit. The nested existing execution projection retains compatibility;
  new `derived` fields give computed counts their proper epistemic classification.
- Optional `CheckpointSummary` takes explicitly submitted bounded public/sanitized
  text, SHA-256, actor/source declaration, observation/availability times and
  optional already visible evidence IDs. Text alone is not parsed into semantic
  claims. Actor identity/privacy are self-attested, not authenticated or attested
  by a digest. Unknown fields/tied latest reports remain unknown.
- Future events/summaries, delayed ingestion, scope/declaration receipts, run
  bounds, references and conflicts are checked at each cutoff. Raw payloads and
  arbitrary metadata do not enter outputs or embeddings. Completed turns,
  successful tools and reported completion never verify task success. No progress
  percentages, native execution times, unknown costs or identical retry causes
  are manufactured. Final-artifact JUnit visibility reuses existing checks;
  intermediate-artifact progression remains unsupported.
- `TrajectoryInput` is an explicit portable input over existing records, not a
  ledger schema or automatic collection mechanism. `task trajectory INPUT.json`
  makes state/changes inspectable; `learn trajectory-eval FIXTURE.json` compares
  the synthetic variants, with optional explicitly pinned local Potion. Reports
  use exclusive destinations and private invalid-input excerpts are omitted.

### Evaluation actually established

`tests/fixtures/longitudinal/` contains seven agent-authored **simulated** scenarios,
fourteen checkpoints, a digest manifest and an actual pinned local CPU reference.
The cases cover normal reported progression, unsuccessful tool actions, declared
complexity growth, implementation-to-debugging, reported completion without
verification, missing evidence and no observed change. They include no fabricated
verification/outcome records, human labels or accepted reviews.

| Variant / check | Actual result and interpretation |
| --- | --- |
| A initial only | Seven abstentions about subsequent change; appropriate lack of evolving evidence. |
| B metadata only | 6/7 status and 3/7 full dimension agreement with authored rules; zero semantic transitions established. |
| B including explicit reports | 7/7 status and dimension agreement; four cases obtain semantic hypothesis changes from author declarations. This is software rule agreement, not human-reviewed semantic accuracy. |
| C with existing Potion | Actual pinned CPU cosine diagnostics computed; identical classifications to B **by construction**, with no semantic threshold/classifier. No additional recognition or predictive benefit demonstrated. |
| Unsupported-inference checks | 154 implementation invariant checks, zero violations; not a population inference-error rate. |
| Downstream independently verified outcomes | `insufficient_data`, zero eligible outcomes in this longitudinal dataset and null scores. No outcome model fitted and no real-world improvement claimed. |

The Potion model/revision/bundle pins are unchanged. The actual-model test denies
socket connections and reproduces reference cosines within 1e-12. Missing weights
stay unavailable; no model download, alternative model, training or cloud inference.
The old outcome evaluators remain intact. A future outcome experiment must choose
one prospective checkpoint horizon per run, resolve labels historically and split
independent lineages; fourteen checkpoints here are not fourteen outcome trials.

### Validation and independent review

Used the existing local uv/Python environment with `.tools/bin` on PATH and
repository-local `UV_CACHE_DIR`. Full validation explicitly set
`MODEL_LEARNER_TEST_POTION_PATH` to the already approved local bundle.

| Executed check | Actual result |
| --- | --- |
| Final `uv run pytest` | **770 passed, 1 skipped in 38.37s**; skipped existing opt-in Docker offline isolation test. |
| `uv run ruff check .` | Exit 0; all checks passed. |
| `uv run ruff format --check .` | Exit 0; 155 files already formatted. |
| `git diff --check` | Exit 0; no whitespace errors. |
| Independent focused suite, actual pinned Potion | **42 passed in 0.63s**; no skips, sockets denied in actual-model test. |
| Actual installed `learn trajectory-eval` with full Potion pins and new `/tmp` output | Exit 0; A/B/metadata-only/C results, 154 checks / zero violations and `insufficient_data` reproduced. |

Review found a semantic-input visibility bypass in an early evaluator version:
its separate text filter omitted reference/run-bound/ambiguity eligibility.
Fixed by using the same projected states for objectives and summaries; encoder-spy
regressions cover delayed scope/description, late event references, pre-run text,
future text and tied summaries. Final independent review found no unresolved
privacy, provenance, temporal, feature or evaluation blockers. Software subagent
review does not count as human annotation/adjudication.

### Minimum evidence needed next

`docs/LONGITUDINAL_TASK_STATE.md` provides the concrete proposal: a manual opt-in
pilot on 5–10 independently scoped, already occurring local trajectories to study
evidence usability. Record a sanitized initial objective/target/configuration and
association receipts prospectively; submit brief sanitized checkpoint sidecars
about activity, attempted mechanism, obstacle, progress evidence and scope change;
keep author hypotheses separate from facts and store private sidecars in ignored
local storage. Later acquire distinct genuine human trajectory labels/review and
independently verified outcome/label-availability receipts. Intermediate-artifact
test evolution requires a separately scoped contract, not relaxed final-verifier
semantics. Enough independent prospective outcomes are needed before prediction.

The next recommended increment is **manual prospective summary collection and
evidence-usability review**. This proposal is not started. No raw transcript
collection, hooks, paid agents, benchmark-security bypass, retrieval expansion,
model switching, routing, Governor, GUI, commit, push, merge or publication.
Stopped after the requested implementation/evaluation.

## Selected Desktop and Work conversation feasibility — 2026-10-11

Read the master plan, AGENTS.md, status, existing observation/domain/association
code, deterministic execution and longitudinal projections, task retrieval,
annotations and optional local CPU encoder. Investigated Codex Desktop and ChatGPT
Work Local separately using official documentation, exposed desktop tool contracts,
public CLI help and freshly generated installed-version protocol schemas.

- `docs/CONVERSATION_INGESTION_FEASIBILITY.md` records source-by-source access,
  text/event/model/time/usage coverage, storage distinctions, account-export gaps,
  shared identity semantics, privacy, a bounded validation proposal and adapter
  tests. The prior Desktop report now points to this selected-history assessment.
- The exposed desktop `read_thread` reader supports an exact thread/chat ID and
  older-turn cursors. Its contract describes summaries and truncated optional
  outputs; complete raw messages/events and historical measurements are not
  established. This tool is available to an agent session, not a demonstrated
  callable interface for the standalone Model Learner CLI.
- Public Codex app-server supports stored reads without resuming. Installed
  `Thread` exposes optional model/effort explicitly described as current/latest
  settings, optional native project and source-origin fields, and a separate
  session-tree ID. `Turn` has nullable times/duration but no usage field. Message
  item variants lack per-message timestamps. Experimental history pagination
  needs version/capability checks; stored items cannot invent original lifecycles.
- Installed CLI remains `0.162.0-alpha.17.2`; help and fresh public schema
  generation exited 0. Schemas are outside Git under
  `/private/tmp/model-learner-history-protocol-20261011`. The read-only public
  daemon-version query exited 1 because its default control socket was absent.
  This blocks that endpoint only; it does not prove no desktop reader exists.
- Work Local can have a Codex-backed local task; ChatGPT-backed conversations with
  local execution are distinct. Official docs describe local-only Work history
  and cloud coordination with local execution. Product surface, backend, execution
  and transcript storage must stay separate. No selected Work backend was tested;
  public standalone Work-history access and account-export coverage remain
  unestablished. The Responses Conversations API is not established as an export
  interface for existing desktop chats.
- Existing Session/task/run/project links preserve the required identity
  separation. The report proposes a source-aware ordered snapshot with missingness,
  privacy and actual receipt times. Existing reviewed-text retrieval and explicit
  summaries can be reused. Execution analysis and the real observation builder
  currently require the exact Codex CLI source; relabeling snapshots as CLI events
  would fabricate provenance. No source-neutral projection was implemented.
- Only optional pinned existing Potion CPU relatedness is proposed. Embeddings
  cannot establish reasoning, progress, continuation or task identity; reported
  semantic hypotheses remain distinct from independently verified outcomes.
- No histories were enumerated, no thread/chat was read, and no private database,
  rollout, authentication token, intercepted traffic or scraped UI was accessed.
  No account export was requested, no daemon started, no global setting changed,
  and no agent execution, adapter, model download, routing or Governor added.

### Actual investigation checks

Existing repository-local uv/cache and `--no-sync` preserved installed dependencies.
No new tests were written for documentation-only changes.

| Executed check | Actual result |
| --- | --- |
| `uv run --no-sync pytest -q` with ten selected observation/domain/workflow/execution/retrieval/annotation/longitudinal test files | **183 passed, 2 skipped in 1.11s**; optional model opt-ins were not enabled. |
| `uv run --no-sync ruff check .` | Exit 0; all checks passed. |
| `uv run --no-sync ruff format --check .` | Exit 0; 155 files already formatted. |
| Documentation diff `git diff --check` | Exit 0; no whitespace errors. |

These are existing regression and schema/help checks, not real Desktop or Work
history validation. Full suite and actual-model integration were not rerun for
this documentation-only assessment. The pre-existing `.DS_Store` change remains.

Next permitted step only after selection/approval: read one exact, non-sensitive
existing conversation per source through the built-in reader, initially one turn,
at most ten turns and 64 KiB retained text each, outputs/attachments excluded.
Preserve identity, ordering basis, source provenance, optional times and missing
fields in ignored local storage. Reader access can place returned text in the
assistant context/tool history; local inference alone cannot make that read
device-only. Standalone app-server validation additionally needs an existing
supported endpoint. No automatic history discovery or speculative integration.
Stop after this feasibility report; controlled validation and implementation
remain unstarted.

## Selected conversation identifier discovery — 2026-10-11

The user supplied two non-sensitive test descriptions but no IDs/links. Inspected
exposed tool definitions, official desktop command/app-server documentation and
the already generated public `ThreadListParams` / `ThreadListResponse` schemas.
Updated `docs/CONVERSATION_INGESTION_FEASIBILITY.md` with the discovery boundary.

- Desktop `list_threads` has no title/source filter, can return generated summaries
  and always includes every pinned chat. It does not meet targeted metadata-only
  discovery limits; it was not called.
- App-server title filtering is documented, but installed responses include a
  required preview usually containing the first user message, with no suppression
  parameter. Selected Desktop connectivity remains unvalidated; `appServer` alone
  cannot distinguish Codex and Work. No RPC or endpoint probe was performed.
- Official **Copy chat deep link** (`Cmd+Option+L` on macOS) provides a manual route
  to a local technical thread ID. The user can copy each selected test's link and
  label its product/mode. No UI/clipboard inspection, history enumeration, private
  database/credential access, conversation read or shared-snapshot creation occurred.
- Both selected access tests, actual returned-field coverage, standalone Python
  connectivity and automatic local ingestion remain **unvalidated**. No adapter,
  model, routing, Governor or application setting change was implemented.

Next step: await the two user-supplied deep links, confirm each selected source and
identity, disclose the exact reader/context exposure and request explicit approval
per conversation. Only then read one turn with outputs disabled; expansion remains
bounded by ten turns and 64 KiB retained text per approved conversation. Stop after
validation/reporting; no adapter implementation is authorized.

Checks used the existing environment with `.tools/bin` on PATH, repository-local
`UV_CACHE_DIR` and `--no-sync`; no dependency changes or new tests were needed.

| Executed check | Actual result |
| --- | --- |
| `uv run --no-sync pytest -q` | **764 passed, 7 skipped in 33.61s**; optional integration opt-ins were not enabled. |
| `uv run --no-sync ruff check .` | Exit 0; all checks passed. |
| `uv run --no-sync ruff format --check .` | Exit 0; 156 files already formatted. |
| `git diff --check` | Exit 0; no whitespace errors. |

These regression checks do not validate selected conversation access. Only this
status and the feasibility documentation changed; the pre-existing `.DS_Store`
modification was preserved. No commit, push, merge or publication was performed.

## Controlled selected-conversation validation: pre-read transport stage — 2026-10-11

The user supplied exact local deep links for the Work scheduling-algorithms test
and Codex CSV-parser test. They confirmed both surfaces use the unified ChatGPT
macOS application with a mode selector. Shared UI/link scheme, local execution,
project working directories and guessed `~/Documents/Codex/` / `~/.codex/` paths
are not evidence of a shared backend or selected transcript storage.

- Requested explicit approval separately for each agent-mediated read, identifying
  `mcp__codex_app__read_thread`, model-context/tool-history exposure and the exact
  initial/maximum scope. No read approval is inferred from a supplied link.
- Installed public help/version checks succeeded. The read-only daemon-version
  query again found the documented default control socket absent (exit 1).
- A standalone ordinary Python subprocess invoked the installed supported
  `codex app-server proxy` with empty input and a ten-second timeout: child exit 1,
  zero stdout bytes, missing default socket. No conversation RPC was sent.
- Public stored-history protocol candidates exist, but selected access and source
  coverage remain unverified. Full `thread/read` lacks a turn limit; paginated
  request schemas lack output/attachment suppression. No daemon, alternate socket,
  private history/config/authentication access or application setting change.

At this stage the feasibility document recorded these transport facts and distinguished them
from successful independent Python conversation access. Both selected-content
validations remain pending their approvals. No native IDs, raw messages or
adapter implementation were added to tracked files.

Next permitted work: after each separate approval, read that selected ID with one
turn and outputs disabled; examine returned coverage and expand only within the
approved ten-turn/64-KiB limit. Report each source independently and stop without
implementing an adapter. Standalone automatic ingestion remains unestablished.

Documentation follow-up checks: `uv run --no-sync ruff check .` passed;
`uv run --no-sync ruff format --check .` reported 156 files already formatted;
`git diff --check` passed. No new Python test was needed or run for these
documentation-only changes. Prior regression evidence is recorded above and is
not evidence of either selected-content read. The pre-existing `.DS_Store` change
was preserved; no commit, push, merge or publication.

## Controlled selected-conversation validation: completed — 2026-10-11

The user explicitly approved both exact-ID agent reads separately with context
exposure disclosed. Used `mcp__codex_app__read_thread`, one turn per request,
`includeOutputs=false`, per-item text cap 3,000 characters, only each selected
conversation's cursors. No attachments, tool outputs, unrelated enumeration,
source execution/resumption, private database/authentication access, settings
change or adapter implementation. Returned text entered model context/tool history;
no transcripts or snapshot payloads were written to workspace files.

- **Codex CSV-parser sample:** three unique turns across three pages, all returned
  IDs matching the approved selection. Reader reports `kind=codex`, `hostId=local`.
  Three user and three assistant message items, plus one separate empty reasoning
  summary. Expected requirement progression is preserved; implementation remains
  unverified. Cumulative serialized retained responses: **5,396 UTF-8 bytes**.
- **Work Local scheduling sample:** three unique turns across three pages, stable
  matching selected ID. Reader also reports `kind=codex`, `hostId=local`, despite
  its user-declared Work product surface. Three user and three assistant message
  items preserve the expected narrowing/incomplete research progression. Cumulative
  serialized retained responses: **4,415 UTF-8 bytes**.
- Explicit `newest_first` pagination, native turn/item IDs, user-before-assistant
  item ordering and increasing start times after reversing the pages establish
  ordering within returned material. Both final pages have `hasMore=false` and
  `nextCursor=null`; this does not prove complete original history.
- Thread creation/update and turn start/completion/duration/status fields returned.
  No per-message timestamps, model/provider/effort, token usage or cost fields.
  No tool-call items exposed; zero original tool activity cannot be inferred.
  No content-truncation marker; longest text items are 460 / 159 characters,
  below the cap. Source lossless fidelity and omitted details remain unknown.
- The first Work request's byte-count wrapper failed before retaining/displaying
  its response; repeated the same one-turn request, without expansion. Four Work
  reader calls versus three Codex calls; retained scope is three turns each.
- Message-bearing user/assistant items were returned rather than merely generated
  retrieval summaries. Exact verbatim equivalence was not independently compared
  with the UI. Reader backend classification and local host do not locate transcript
  storage or establish device-only data. Returned cwd is project context.
- Independent Python history access remains **unvalidated**: the ordinary Python
  proxy probe in the preceding stage failed at an absent default endpoint before
  conversation RPC. Public App Server stored-read/pagination protocols are
  candidates, but neither selected ID was read through that transport. No general
  standalone interface for the agent-only desktop reader was established.

The updated feasibility report contains separate per-source coverage and smallest
integration conclusions. A bounded selected-snapshot projection is supported by
agent-returned evidence but still requires an agent. No autonomous ingestion adapter
is justified until supported endpoint reachability, selected-source mapping and
content exclusions are validated. Do not implement the handoff as a substitute for
the user's ordinary local Python application requirement.

Stopped after controlled validation/reporting. No next implementation milestone is
authorized; native IDs, working paths and transcripts were omitted from tracked
documentation. Current checks: `uv run --no-sync ruff check .` passed;
`uv run --no-sync ruff format --check .` passed (156 files formatted), and
`git diff --check` passed. No Python behavior changed; the prior full regression
suite (764 passed, 7 skipped) was not repeated. Actual integration evidence here
is the selected reader responses and the failed ordinary Python proxy probe,
not repository test success. No new tests, dependency changes, commit, push,
merge or publication; the pre-existing `.DS_Store` change was preserved.

## Independent Python stdio history experiment — 2026-10-11

The user explicitly approved temporary App Server startup and exact-ID reads for
the same two non-sensitive tests before any server process was launched. Read the
official App Server documentation, current status, relevant M3 plan boundary and
previously generated public parameter schemas. No runtime/package was installed.

Exact child command used the already installed executable:

```text
/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex app-server --listen stdio://
```

An ordinary **Python 3.9.6** standard-library client used subprocess stdin/stdout
JSONL, `initialize`/`initialized` with experimental pagination opt-in, then both
exact-ID `thread/read(includeTurns=false)` requests before any turn requests.
The protocol allowlist contained only those handshake methods and
`thread/turns/list`. No frontier-model retrieval or inference operation was sent.

| Actual check | Codex CSV-parser test | Work Local scheduling test |
| --- | --- | --- |
| Selected metadata access | Success; returned ID equals selected ID | Success; returned ID equals selected ID |
| Returned originator | `Codex Desktop` | `codex_work_desktop` |
| Other source/history fields | `source=vscode`, `threadSource=user`, `historyMode=paginated`, status `notLoaded` | Same |
| Server-limited turns | `limit=1`, `sortDirection=desc`, `itemsView=notLoaded`; three unique turns after cursor expansion | Same |
| Comparison with agent reader | Latest turn ID and all three start/completion/duration tuples match | Same |
| End/order | Final cursor null; reversing pages yields increasing start times | Same |
| Model metadata | `gpt-6.1-sol`, provider `openai`, effort `high`; current/latest thread settings only | Same |
| Returned/excluded content | Thread preview received privately; all turn items omitted server-side | Same |
| Measurements | Thread/turn times present; token/usage fields absent | Same |
| Response bytes in expanded run | 2,705 | 2,725 |

First successful run retrieved metadata plus one turn scaffold per source. The
second successful bounded run expanded to three turn scaffolds each, always one
turn per page. Cumulative response accounting across both runs: **4,390 bytes**
Codex / **4,430 bytes** Work, below 64 KiB each and only three unique turns each.
All returned items arrays were empty with `itemsView=notLoaded`. No attachment,
tool-output, message-item body or full-history request was issued. Nonempty thread
preview establishes limited text availability, not complete original messages.
No explicit truncation field; source/preview completeness and fidelity remain
unknown. No per-turn historical model attribution or token/cost recovery claim.

The outer execution sandbox blocked startup before handshake (`Operation not
permitted`; two startup/diagnostic attempts exited 1 without conversation RPC).
Scoped execution-sandbox escalation allowed the same approved protocol test.
Both successful temporary servers terminated on stdin EOF with exit **0**.
This corrects the earlier endpoint limit: an absent daemon proxy socket does not
prevent independent stdio access. No internal socket discovery was performed.

Private responses stayed inside Python memory; only sanitized coverage/error
facts reached terminal output/model context. No private response/log/transcript
file, native conversation ID or working/history path was added to Git or report
fixtures. The one-off probe outside Git was removed. No private database,
credential or undocumented rollout inspected; no unrelated conversation listed;
no resume/start, model turn, tool execution, mutation method or application setting
change. Read-only RPC behavior was validated, not zero incidental server startup
filesystem writes. Native path fields were not followed.

The updated feasibility report now justifies a narrow selected-ID standalone
**metadata/turn-record adapter** over this temporary stdio transport for these
samples. It preserves separate product provenance/originator and unknown historical
fields; it creates no automatic task/run links or verified outcomes. A standalone
message-text adapter still needs a supported selective-content boundary or a
separately approved scope: the inspected pagination parameters lack attachment/
tool-output filters, so summary/full item retrieval was not tested. Evidence for
this Codex-backed Work record does not establish every Work backend/storage path.

No adapter was implemented. Stop after this experiment/report; no next milestone,
new model, routing or Governor work is authorized. Documentation-only checks:
`uv run --no-sync ruff check .` passed; `uv run --no-sync ruff format --check .`
passed (156 files formatted); `git diff --check` passed. No production Python
behavior changed, so pytest was not repeated and no new test fixture was added.
The actual integration evidence is the independent subprocess result and its
bounded identity/time comparison, not repository regression tests. The pre-existing
`.DS_Store` change was preserved. No commit, push, merge or publication.

## Selective standalone text validation — 2026-10-11

The user explicitly approved **one full-view turn per selected test** after the
schema/documentation findings, with a stop for approval before implementing the
importer. Installed schema generation succeeded for CLI 0.162.0-alpha.17.2.
`summary` is a display summary; `full` includes every available persisted turn
item. Neither turn pagination nor item pagination has a message-only, attachment
or tool-output filter. Client exclusion occurs after the server returns content.

The temporary standard-library Python 3.9.6 client used the same stdio transport
and allowlist (`initialize`, `initialized`, `thread/read`, `thread/turns/list`).
After handshake it requested metadata without turns, then one latest full turn
per selection, with `limit=1` and descending order. No cursor expansion, item-list
RPC, unrelated enumeration or control method was sent. One notification was
ignored privately; server-initiated requests were prohibited. Scoped execution-
sandbox escalation was used for the approved process. Probe and temporary server
both exited **0**; server shutdown completed on stdin EOF.

| Actual sanitized coverage | Codex test | Work Local test |
| --- | --- | --- |
| Identity/source | Selected ID matched; originator `Codex Desktop` | Selected ID matched; originator `codex_work_desktop` |
| Runtime/history | `source=vscode`, `threadSource=user`, paginated | Same |
| Turn/item scope | One turn, confirmed full view, older cursor remains | Same |
| Messages/order | One user then one assistant, source ordinals 0/1, unique IDs | Same |
| User / assistant text bytes | 117 / 460 | 135 / 144 |
| Extracted text retained in memory | 577 bytes | 279 bytes |
| Metadata plus turn response bytes | 2,625 | 2,327 |
| Turn start/end/duration | Populated | Populated |
| Message timestamps | Absent / unknown | Absent / unknown |
| Other items / non-text user parts | Zero / zero in this turn | Zero / zero in this turn |
| Explicit truncation marker | None exposed | None exposed |

All four text fields were nonempty and survived local JSON round-trip comparison
without normalization or clipping. This validates extraction, not original-source
fidelity. The original test-message baseline is unavailable for independent
equality checks. Codex's 460-character assistant field matches the earlier reported
maximum length only; that does not establish text equality. Latest user strings
do not equal the first-message-style thread previews, as expected for later turns.
No source-completeness claim follows from full persisted view or missing markers.

Responses, previews, text and native errors stayed inside Python memory; only
coverage facts reached terminal/model context. No body/transcript file, fixture,
native ID or returned private path was added to Git. The temporary probe was
removed after use. One turn and under 64 KiB per selection stayed within the
ten-turn / 64-KiB ceilings. No inference/execution, task/run association, outcome
or learning record was created. Zero other items here does not imply server-side
exclusion elsewhere.

One-turn standalone user/assistant text access is supported for both samples.
Three-turn standalone text history, independent verbatim fidelity, historical
model/usage/cost attribution and other Work backends remain unvalidated. No
importer implemented; user approval is required before Phase 2 and bounded Phase 3
validation. Documentation-only checks: `uv run --no-sync ruff check .` passed;
`uv run --no-sync ruff format --check .` passed (156 files formatted);
`git diff --check` passed. Used the existing repository-local uv/cache paths.
No production Python changed, so pytest was not repeated. Full tests, sanitized
fixtures and independent importer review remain Phase 3 work after approval.
The pre-existing `.DS_Store` change was preserved. No commit, push or publication.

## Minimal standalone conversation importer — 2026-10-11

The user approved this narrow implementation and bounded three-turn validation
after the one-turn full-view probes. Read the repository instructions, M3 plan,
prior status/feasibility and existing observation/session/storage/CLI boundaries.
Used the current checkout; the pre-existing `.DS_Store` change was preserved.

### Delivered behavior

- New `adapters/app_server.py`: standard-library JSONL subprocess transport, exact
  selected UUID, experimental handshake, existing read-only allowlist, no server
  request responses or control operations. Default turn view is `notLoaded`;
  explicit full reads are bounded to ten one-turn pages and 64 KiB total response
  bytes, with timeouts and shutdown. Native response/error/notification bodies are
  never printed. No global discovery, private format parsing or model inference.
- New `adapters/conversations.py`: the two validated originators map to separate
  declared product sources over backend `codex`. Only the observed paginated
  `vscode`/`user` format is accepted. Native conversation identity includes source,
  backend, product and machine scope; canonical task identity stays separate.
  Existing Session/Event contracts hold `codex-conversation-snapshot/v1` snapshots,
  with ordered turns/messages, IDs, original timestamp units, explicit exclusions,
  truncation/missingness and retrieval receipt times. Unknown message times,
  configuration, usage and cost remain null; current thread model fields are dropped.
- Metadata retention is default. Preview/title/path/opaque extras and non-message
  bodies are excluded; full reads discard reasoning/attachments/tool results after
  server retrieval. Only explicit `retain_text` / `--retain-text` stores user and
  assistant text parts. `--read-text` reads text into memory without storing it.
  Storage must be under the workspace's ignored, untracked `.model-learner/`, with
  private directory/database permissions and no symlink paths.
- `Repository.add_session_snapshot` atomically creates a session and immutable
  snapshot. Retained-fact identity excludes receipt time and opaque transport
  cursors; identical fresh replay preserves the first receipt. Changed retained
  facts/view/retention policy append an explicit new snapshot version, with
  collision checks and rollback on failure. Native tools are not manufactured as
  execution lifecycle events. No migration, dependency or lockfile change.
- `import conversation` accepts one selected UUID, source and stable machine ID;
  `session show` reports conversation snapshot coverage and unknowns. README
  documents the exact command and privacy choices. This source remains excluded
  from existing Codex CLI execution projections and real learning builders.
  No task/run/project associations, verified outcomes or observations are generated.

### Actual three-turn validation

Used Python 3.12.14 and Codex CLI 0.162.0-alpha.17.2. Two independent full-view reads
per selection fetched three one-turn pages each, with null final cursors. Every
temporary server exited **0**, as did the validation wrapper. Scoped execution-
sandbox escalation covered the approved processes; private replies stayed inside
Python memory. Only sanitized coverage was emitted; the temporary script was
removed. Metadata snapshots were retained in a private ignored local ledger.

| Coverage | Codex test | Work Local test |
| --- | --- | --- |
| Identities/originators | Validated | Validated |
| Exposed turns/messages | Three unique turns / six unique messages | Same |
| Native ordering | User before assistant in each source-ordered turn | Same |
| Native times | Start/end/duration populated, starts increasing | Same |
| User/assistant bytes by turn | 159/234, 96/464, 117/460 | 159/105, 120/78, 135/144 |
| In-memory text per read | 1,530 bytes | 741 bytes |
| Wire bytes across both reads | 11,712 including handshake/notifications | 9,856 including handshake/notifications |
| Fresh-read text equality | Exact for all six fields | Same |
| Latest-turn lengths vs prior probe | Match | Match |
| First user equals thread preview | No; preview is not an exact baseline | Same |
| Excluded non-message counts by turn | 0 / 1 / 0 | 0 / 0 / 0 |
| Non-text user parts | Zero exposed | Zero exposed |
| Explicit turn truncation marker | None exposed / unknown fidelity | Same |
| First metadata import / replay | One snapshot / zero new snapshots | Same |

The ledger contains exactly two sessions and two metadata snapshots, all message
text/raw fields null. No recovered live string appears in retained canonical event
JSON or SQLite bytes. No task/run/verification/outcome/real-learning row exists.
No live text was stored. This validates client storage, not zero incidental server
startup writes or unknown source/cloud copies. Native paths were not followed.

Complete exposed three-turn history and repeatable text are validated for these
two samples. Original UI equality remains unverified without independent originals;
preview comparison failed. Codex's middle assistant field is 464 bytes in full view,
while the earlier agent reader reported a 460-character maximum; interface coverage
does not resolve original fidelity. Message timestamps, historical configurations,
usage/cost, hidden history/branches and other Work backends remain unestablished.

### Checks and independent review

Added authored sanitized three-turn fixture/fake stdio peer and unit/integration
tests for both sources, exact Unicode/multiline/whitespace text, privacy omission,
opt-in storage, native ordering, null time/resource fields, truncation, bounds,
malformed data/errors, controlled CLI diagnostics, private paths, transactions,
snapshot versioning, fresh replay and learning isolation.

An independent subagent reviewed the implementation and ran **41 focused tests**.
Both review findings were fixed: untrusted type rejection and cursor-independent
snapshot identity. A further independent varying-cursor regression check passed
(**1 passed**); final review reported **no remaining actionable findings**. The
reviewer accessed no live conversation or existing private storage.

| Command | Actual result |
| --- | --- |
| `uv run pytest` | **805 passed, 7 skipped in 48.43s**; optional host/model checks remained disabled. |
| `uv run ruff check .` | Passed; all checks passed. |
| `uv run ruff format --check .` | Passed; 162 files already formatted. |
| `git diff --check` | Passed. |

Used existing repository-local uv/cache paths; no installation was needed. No
global scanning, automatic grouping, routing, Governor, new CPU model, fine-tuning,
cloud inference, commit, push, merge or publication. Stop after the importer.

## CPU conversation semantic task-state demonstration — 2026-10-11

Read the repository instructions, master-plan observation/inference/privacy and
baseline/evaluation semantics, prior status and conversation feasibility evidence.
Reused the current checkout, existing environment and completed importer; preserved
the pre-existing `.DS_Store` change. No dependency, schema, storage, importer or
core architectural change was needed.

### Delivered behavior

- `understanding/conversation_state.py` is a pure CPU, in-memory analyzer over
  opted-in ordered user/assistant messages. Each message checkpoint retains its
  objective hypothesis, positive requirement/revision evidence, removal overlays,
  actor-attributed decision/reversal evidence, issue/progress/completion reports,
  ambiguity and missingness. Exact message character spans support interpretations;
  lexical target links are review candidates, not logical entailment or confidence.
- Original requirement/decision evidence remains alongside removals and revisions.
  The schema explicitly calls these evidence lists, not active resolved requirements.
  Partial list edits/pronouns and implicit scope/task changes remain limitations.
  Reported obstacles are historical statements; later progress does not prove
  independent resolution. Assistant proposals cannot impose user requirements.
- Independent full/partial acceptance sidecars remain outside prose. Completion
  claims never produce verification. Checks must match the exact checkpoint and
  inferred revision with a named artifact/acceptance target. Partial-only checks
  remain visible with unknown completion; contradictions/indeterminate checks stay
  unknown. A failed check is not a failed task. Passes never carry forward to later
  messages. Sidecars are explicit caller attestations, not authenticated verifiers
  or new ledger outcome/observation records.
- Inputs are bounded to 64 KiB text, 128 messages and 256 non-code clauses. Evidence
  and timeline construction use only each available prefix. Real, simulated,
  benchmark and unknown source declarations remain distinct; the live bridge is
  real and authored evaluation/demo inputs are simulated.
- `task conversation-state --text-opt-in` accepts stdin JSON or one exact selected
  live UUID with declared source/machine and the existing executable. No discovery,
  ingestion, file output or automatic persistence. Default stdout omits text/check
  identifiers; separate `--emit-text` authorizes display. Invalid-input diagnostics
  omit private content. Full-view source reads have the existing non-message
  retrieval exclusion and unknown original-fidelity limits.
- `understanding/conversation_evaluation.py` and `learn conversation-state-eval`
  compare a weak keyword baseline, contextual English rules and a dependency-free
  unigram/bigram/role multinomial NB classifier with fixed smoothing/abstention.
  Training uses only separate authored training examples. No embeddings-only
  requirement understanding, optional model load, cloud inference or routing.
- `docs/CONVERSATION_TASK_STATE.md`, README and authored simulated fixtures provide
  executable examples, timelines, evaluation/reference reports and limitations.
  The synthetic end-to-end demo covers a genuine streaming-to-buffered reversal
  and a synthetic independent acceptance check. It is not real verified evidence.

### Actual selected demonstrations

The existing exact-ID importer performed bounded full reads of the two approved
samples. The ordinary sandbox initialization failed as before; reviewed escalation
allowed the bounded existing read-only subprocess. It sent only the existing
handshake/history allowlist. Both again exposed three turns and six ordered
user/assistant messages; temporary servers exited 0. Live transcript strings and
derived state stayed in Python memory. Sanitized signal/count summaries were
printed; no native identifiers, excerpts, real transcript fixtures or semantic
snapshots were retained. Existing private metadata storage was not ingested into
or modified by the analysis code.

- **CSV:** initial parser objective and ordinary comma-field requirement recognized;
  quoted-comma support added at turn 2 and multiline quoted-field support at turn 3.
  One user issue report is recognized. Six uncertainty entries remain after turn 3.
  The final analysis took about **0.47 ms**, excluding retrieval, on 1,530 bytes.
- **Work Local:** the initial objective wording is **not recognized**. A constraint
  is extracted; FIFO exclusion is recognized but its initial target is unresolved.
  The last turn identifies remaining round-robin/shortest-job scope and user plus
  assistant incompletion reports. Seven uncertainty entries remain after turn 3.
  The final analysis took about **1.49 ms**, excluding retrieval, on 741 bytes.
- Both have zero independent check inputs and verification stays **unknown** at
  every checkpoint. No explicit progress report, decision or completion claim is
  recognized under these cues; that does not establish absence of real progress.
  Original UI fidelity, hidden history and original message times remain unknown.
  Warm timing observations and these two examples do not establish generalization.

### Evaluation actually established

`tests/fixtures/conversation_state/evaluation.json` has **52 training examples** and
**23 separate varied evaluation conversations / 54 manually specified intent
labels**, plus expected final-state signatures. Cases cover additions, removals,
revisions, genuine decision reversals, task switches, failed attempts, unresolved
work, independent full/partial verification, completion claims,
negation, planned progress, ambiguity and unresolved references. Labels were
manually specified by the implementing agent, not independently by human annotators.

| Variant | Intent accuracy | Macro F1 on present labels | Matching final signatures |
| --- | --- | --- | --- |
| Keyword baseline | 40/54 (74.1%) | 0.502 | 14/23 |
| Contextual rules — selected | 51/54 (94.4%) | 0.925 | 20/23 |
| Naive Bayes | 36/54 (66.7%) | 0.599 | 9/23 |

The first rule run scored 48/54; fixture/demo inspection exposed a quotation cue
mistaking quoted fields for indirect claims, missing objective phrasing and a
constraint mistaken for objective. Those defects were corrected. Independent
review found an example that repeated a choice instead of reversing it; corrected
SQLite-to-PostgreSQL/streaming-to-buffered examples and regenerated the reference.
Intent/final-state labels and NB training/features/margin were unchanged. This is
therefore a **diagnostic regression set**, not an untouched held-out evaluation.
No statistical improvement or generalized semantic understanding is established.

The rules still miss an implicit accessibility requirement, an implicit task switch
and ambiguous short approval. NB adds false scope changes, planned-progress and
indirect-success errors. The report includes per-case errors, confusion/category
counts, per-field agreement, dataset digest and actual CPU timing. Final signatures
measure evidence message positions and selected state fields, not fully normalized
logical requirements, link-target accuracy, all intermediate states or real success.
The reproducible checked-in reference excludes volatile elapsed fields.

### Checks and independent review

Used existing Python 3.12.14 / uv environment with repository-local cache and
`UV_NO_SYNC=1` to preserve installed optional capabilities. No model runtime was
needed; existing optional model/host checks remained disabled.

| Executed check | Actual result |
| --- | --- |
| `uv run pytest` | **840 passed, 7 skipped in 48.47s**. Existing optional model/host checks skipped. |
| Final focused unit/CLI suite after review fixture correction | **35 passed in 0.65s**. |
| Independent final focused suite | **35 passed in 0.56s**. |
| `uv run ruff check .` | Passed; all checks passed. |
| `uv run ruff format --check .` | Passed; 169 files already formatted. |
| `git diff --check` | Passed. |
| Installed CPU demo/evaluation commands | Exit 0; authored simulated timeline and references reproduced. |

Coverage includes source attribution, scope overlays/links, negation, conditional
and quoted ambiguity, fenced-code exclusion, input bounds, future/prefix isolation,
verification invalidation/conflicts/partial coverage, content-free errors, default
redaction, explicit display, no retained files, existing fake-stdio bridge, actual
synthetic demo, no network fitting and exact evaluation reference reproduction.
Independent review requested changes to stale/partial verification visibility,
input clause bounds, fixture validation and true reversal coverage; all were fixed.
Final independent review reports **no remaining actionable findings** and accessed
no private conversations or ignored storage. Software review is not human labeling.

The next evidence step would be separately authorized genuine independent human
labels and an untouched, more diverse evaluation, plus better objective/reference
resolution if requested. None is started. The existing pending human-review batch
and earlier prospective-summary pilot remain untouched. No ingestion expansion,
model routing, Governor, paid agent, cloud inference, commit, push, merge or
publication. Stopped after the requested demonstration and evaluation.

## Known issues / blockers

- Independent synthetic holdouts expose substantial semantic objective/change/
  decision failures. The bounded fixes show no broad recognition gain on untouched
  examples. Trusted semantic utility integration remains unsupported; eligible
  paired real conversation-prefix/outcome data is not demonstrated.
- Real benchmark collection is fail-closed pending a supported, validated
  agent backend, credential relay, hostile artifact freezing/extraction, separate
  candidate-only acceptance transport and exact-runtime run-bound validation
  receipts. The validated fixed offline shell probe and new synthetic controller
  receipts do not attest these real-agent boundaries.
- Actual Potion CPU semantic C evaluation is complete on synthetic cohorts, with
  no consistent improvement. Real-world semantic predictive benefit remains
  unestablished. The optional original MiniLM backend is still integration-pending;
  its model/torch/transformers were not provisioned or validated here.
- The pilot is prepared for operator review and controlled fixture rehearsal.
  Manually authorizing payment does not resolve containment or predictive export
  limitations; no real experiment has been authorized or run here.

- No known M0 implementation defects or unresolved blockers.
- uv is installed in the ignored `.tools/bin/`, rather than the default shell PATH.
  From this checkout, use `export PATH="$PWD/.tools/bin:$PATH"` before uv commands,
  or install uv normally as described in the README. Python 3.12.14 is available
  through the existing `.venv`; the system `python3` remains 3.9.6.
- Initial sandboxed dependency download failed due to restricted network access;
  the authorized network retry succeeded. Locked offline sync now works locally.
- uv build warned that the repository-local cache might enter distributions;
  archive inspection confirmed it is excluded by `.gitignore`.
- Other operating systems and Python versions have not been tested.
- The pre-existing tracked `.DS_Store` was left unchanged. `.gitignore` prevents
  adding new OS metadata but does not remove files already tracked by Git.
- The execution-event importer supports explicitly selected Codex CLI streams only;
  passive desktop capture remains unsupported.
  Bounded selected agent-mediated reads of both Desktop and Work Local tests are
  now validated. Independent stdio selected thread/turn metadata access is also
  validated. The standalone selected-ID importer now validates all three exposed
  turns and six user/assistant messages for each approved sample. Metadata-only
  live storage and fresh replay are checked. Original UI verbatim fidelity, hidden
  history completeness, historical measurements and other backends remain unverified.
  The requested increment now adds a narrow read-only file digest verifier and
  evidence-linked real task-observation builder plus bound JUnit report verification.
  Arbitrary test command execution and whole-repository artifact verification remain
  unsupported.
- JSONL imports enforce record schemas and relationships but are intentionally
  limited to primary records; task/session links are managed through the explicit
  attach commands rather than exported as a standalone record stream. The new
  run/session links likewise require explicit reconstruction on ledger transfer.
- SQLite is appropriate for the local-first, single-machine milestone but does
  not make multiple concurrent writers parallel; short transactions and a busy
  timeout reduce contention only.
- Decision/policy records, automatic project discovery, intervention-state learning,
  and cache-cost attribution remain unimplemented. The new learner estimates a
  selected binary acceptance target; it does not claim full expected utility,
  causal model superiority, or effects of interventions/budgets.
- Simulator outcomes are independent; missingness is completely at random.
  Correlated retries, outcome-dependent missingness, and selection confounding
  are not modeled. Real CLI fitting now resolves conflicting assessment histories
  at the requested cutoff; pure estimator callers must pass resolved rows.
  Simulation calibration does not establish real calibration.
- The initial numerical interval implementation supports shapes at least 0.5,
  posterior shape sum at most 100,000, and interval mass in [0.5, 0.999]. The
  default Beta(1,1) permits at most 99,998 verified trials per cell. Unsupported
  inputs fail explicitly; larger-scale numerical methods are deferred.
- Receipt-time capture is affected by upstream buffering and is not execution
  duration. The native CLI stream lacks complete event IDs; independently
  recapturing a stream is not globally deduplicated. Replay requires retaining
  the same capture identity and machine ID. Metadata/raw-retention policy and
  emitter-version enrichment cannot rewrite already persisted events.

## Next recommended increment (not started)

- Latest request: private selected-real-conversation reports are produced, with
  explicit incomplete evaluation due to existing importer/analyzer bounds. Next
  unstarted step requires separate direction for a supported bounded strategy
  covering rejected text reads and the unsupported final prefix, followed by
  human adjudication. Independent outcome integration remains unstarted. No
  limits, rules, models or estimators were changed.

- Latest request: frozen semantic baseline and independent holdout evaluation,
  scheduling root cause, bounded corrections and untouched reevaluation are
  complete. Full checks and independent review passed. Next recommendation:
  human-adjudicated prospective prefixes, conservative reported-signal validation,
  and independent outcomes with checkpoint/attempt receipts before any predictive
  comparison or trusted utility integration. Await separate instruction; no next
  milestone is started. Earlier recommendations are historical.

- First longitudinal state reconstruction and synthetic A/B/C rule evaluation are
  complete. Next: an explicitly authorized manual prospective sanitized-summary
  pilot and independent evidence-usability review, as specified above and in
  `docs/LONGITUDINAL_TASK_STATE.md`. No pilot or next implementation is started.
  The earlier retrieval human-review batch remains pending; it need not expand
  before demonstrating utility. Earlier recommendations below are historical.
- The local 40-query human-review batch is prepared; the annotation workflow and
  protocol remain complete. The next evidence step is genuine independent human
  labeling/adjudication of that batch, then retrieval/no-match/abstention
  measurement under a prospectively frozen policy. No next implementation increment,
  semantic classifier, fine-tuning or utility integration is authorized or started.
  Earlier checkpoint entries below are historical.
- The fixed offline isolation experiment and benchmark evidence pipeline are
  delivered. The requested secure controller components and CPU representation
  prototype are also delivered for their offline scope; await new user direction.
  A real pilot still requires the exact agent/credential/artifact/independent
  acceptance boundary plus prospective checkpoint collection. The requested
  pretrained Potion C evaluation is complete; optional MiniLM validation was not
  requested. No real run, further installation or next milestone is authorized.
- The requested coding-verification, execution-analysis, coding-task evaluation
  and task-state evaluation workstreams are delivered and checked. No next
  milestone is authorized. Real benchmark executions remain operator-controlled
  and were not launched; real predictive improvement remains unestablished.
- Intermediate artifact snapshots and complete declaration/evidence ingestion
  receipts would require separately scoped contracts. No new schema is introduced
  here; no subsequent milestone has started.
- Complete receipt-time reconstruction beyond trusted declared timestamps would
  require a separately scoped declaration/ingestion availability contract. No
  schema change has been made for that future work.
- Further statistical work could examine informative verification delays,
  correlated retries and selection confounding. The recent-window experiment
  does not justify replacing full history as the default estimator.
- Desktop capture requires a separately scoped, sanitized public-transport spike.
  A suitable passive connection to this running Desktop instance is unvalidated.
- No recommendation, routing, model switching, fine-tuning, TUI, cloud sync,
  runtime intervention control, or AI Governor was implemented. No commit, push,
  merge, publication, or global hook installation was made. Stop at the requested
  workstreams; await user direction.

## Focused conversation task-state holdout evaluation — 2026-10-12

Read MODEL_LEARNER_PLAN.md, AGENTS.md, STATUS.md and the conversation task-state
methodology/implementation before edits. Kept observation, inference and outcomes
separate; no estimator, ingestion, contract, migration, dependency, routing or
Governor change. The pre-existing `.DS_Store` change remains untouched.

### Frozen baseline and independent reference labeling

- Archived original rules/state logic, diagnostic evaluator, dataset and reference
  in `tests/fixtures/conversation_state/frozen_v1/`, with SHA-256 manifest, runtime
  and NB/default-rule configuration. Before any rule edits, original keyword/rule/
  NB results reproduced exactly: **40/54, 51/54, 36/54**, final states
  **14/23, 20/23, 9/23**. Archive replay tests bind its evaluator imports to archived
  rules, avoiding mutable-production imports. Existing diagnostic files unchanged.
- Confirmed original evaluation leakage: shared agent/cue authorship, inspected
  examples and fixture corrections during development; final-state scores omitted
  intermediate states, logical scope and target links. This was not a holdout.
- A separate agent with no inherited conversation context authored/froze labels
  without implementation, previous examples or predictions: **12 scenarios /
  63 messages / 85 events**. A different independent agent audited the scorer,
  freeze, metric semantics and reported artifacts. No human annotation is claimed.
- Frozen baseline ran on the first set before implementation changed. Only then
  two bounded corrections were made and revision hash frozen. The blind author
  independently produced **8 untouched scenarios / 38 messages / 46 events**;
  both archived and revised rules were evaluated. A later **1 untouched scenario /
  6 messages / 8 events** closes explicit removal/reinstatement coverage. Neither
  earlier set nor its labels was modified. No later rule tuning occurred.
- `understanding/conversation_holdout.py` is a small pure synthetic scoring/replay
  module, runnable with `python -m`; it adds no CLI infrastructure or persistence.
  Scores span-aligned events, intermediate objective/verification state, all target
  candidate edges, completion, uncertainty and subtype-tolerant supplemental
  recognition. Invalid references fail; missing denominators are null.

### Actual results and failures

| Measurement | Frozen first 12 | Frozen untouched 8 | Revised untouched 8 |
| --- | --- | --- | --- |
| Explicit opening objectives | **5/11** | **3/7** | **3/7** |
| Objective checkpoint agreement | **27/63** | **14/38** | **14/38** |
| Typed requirement precision / recall | **13/18 / 13/23** | **5/6 / 5/10** | **5/6 / 5/10** |
| Subtype-tolerant requirement detection | **15/18 / 15/23** | **5/6 / 5/10** | **5/6 / 5/10** |
| Typed decision precision / recall | **2/6 / 2/8** | **0/2 / 0/3** | **0/2 / 0/3** |
| Decision reversal recall | **1/2** | **0/1** | **0/1** |
| Typed change false positives / misses | **9 / 18** | **3 / 10** | **3 / 10** |
| Task-switch recall | **0/2** | **0/2** | **0/2** |
| Semantic target precision / recall | **3/8 / 3/7** | **null / 0/4** | **null / 0/4** |
| Source-span / actor integrity | **81/81** | **47/47** | **47/47** |
| Completion recall / false claims | **7/10 / 0** | **4/5 / 0** | **4/5 / 0** |
| Verification checkpoint agreement | **62/63** | **38/38** | **38/38** |
| False verified claims | **0** | **0** | **0** |
| Required uncertainty coverage | **1/2** | **2/2** | **2/2** |

The first-set revision improves required uncertainty from **1/2 to 2/2**, while
recognition metrics remain unchanged. This is diagnostic, after inspection.
All untouched eight-case metrics are identical across versions: **no broad
recognition gain demonstrated**. The additional reinstatement case also has
identical results: opening objective **0/1**, typed requirements **1/2 precision /
1/3 recall**, subtype-tolerant edits **2/2 precision / 2/3 recall**; the actual
reinstatement is missed. No false completion/verification claims; **6/6**
verification checkpoints agree. Small curated sets are not a real population
estimate, and dependent checkpoints are not independent accuracy trials.

Concrete failures include missing “Help me organize …”, treating “could use …” as
a decision, merging “Now make …” into old scope, missing failed-attempt and
unresolved paraphrases, over-abstaining on indirect requests and ordinary “example”
wording, missing natural changed decisions, and unresolved concurrent-task identity.
Evidence boundaries are intact, but that does not establish semantic correctness.

Scoring artifacts are preserved/documented in
`docs/CONVERSATION_TASK_STATE_HOLDOUT.md`: one first-set reference expects
verification to persist after a thanks, contrary to the exact-checkpoint contract;
latest-paraphrase objective provenance differs from initial-source retention;
addition/revision subtypes are arguable in two cases; same-span reversal/choice
labels duplicate two decision regions. Supplemental decision-region detection is
**2/6 precision / 2/6 recall**. Strict ambiguous-act agreement is **0/6 precision /
0/1 recall** in the first set and **0/2 / 0/1** in the untouched eight, but assistant
clarification questions and unparsed-user uncertainty are separate policy issues.
No labels were corrected against predictions. No verification semantics changed.

Independent scorer review found one emitted ordinary-decision edge omitted from
target precision. The original `holdout_v1_baseline.json` remains preserved;
`holdout_v1_baseline_audited.json` counts all edges and exact matched target
identity (**3/8**, not initial **3/7** precision), with unchanged model predictions.
Freeze manifests distinguish the original and audited scorer digests. Reviewed
revised/post/supplement reports and all synthetic references are retained separately.

### Scheduling investigation and narrow improvements

Used only the supplied scheduling sentence, not the private original. Frozen rules
preserve the entire **92-character** clause, classify it `other`, and consequently
leave objective unknown. `research` is recognized but `researching` is absent under
a word-boundary regex; there is no threshold in that path. Synthetic importer
bridge evidence preserves the same text exactly. The reference objective is
explicit. This isolates an extraction defect for intact input; original source
fidelity/missing text cannot be fully excluded without an approved fresh read.

Added progressive forms of existing objective verbs and explicit uncertainty when
more than one lexical candidate could be a removal/revision/reversal target.
Retained original evidence and candidate links; selected no target and added no
logical scope solver. Question/conditional/assistant guards remain tested. Known
supplied wording now establishes an objective with verification unknown. No
conversation-specific algorithm rule or broader cue fitting was introduced.

### Integration assessment and stopping point

- Useful future candidates: actor-separated reported obstacle/progress/scope
  signals, objective availability and coverage/uncertainty masks, with exact source
  spans for audit. They remain inferred reports. Active scope, automatic task
  identity, definitive links, semantic difficulty and inferred success are too
  unreliable. Missing data stays null plus an explicit reason/mask; a recognized
  count of zero is not proof of zero real events. Final outcome/checks must not
  leak into earlier predictors.
- Associate prospective prefixes with explicit Task/Run/Attempt, acceptance
  version and availability receipts. Source turn order is not an execution attempt
  boundary; current conversation segments create no ledger associations. Exclude
  ambiguous multiple-task or mixed-configuration attribution.
- Existing synthetic outcomes and `learn.task_state` can exercise plumbing and
  controlled ablation, not establish real semantic benefit. Recorded prior audit
  has one verified fixed-reply smoke observation and no suitable real longitudinal
  coding trajectories; selected conversations have no independently verified
  outcomes or run associations. No new private datastore or historical conversation
  enumeration occurred. Sufficient eligible paired real prefix/outcome data is
  **not demonstrated**, so no predictive model was fitted or gain claimed.
- Next recommendation, **unstarted**: human-adjudicate a small explicit prospective
  selection, resolve label policy, verify a conservative reported-signal subset on
  another frozen semantic set, and collect independent artifacts/outcomes with
  checkpoint/attempt receipts. With adequate paired labels, use the existing
  chronological metadata-versus-semantic-subset comparison and identical cohort/
  cutoffs; default floors are 30 training and 20 scored labels, five task clusters
  per split and both training classes, not a power guarantee. No larger neural
  network is justified yet. Stop after this evaluation/recommendation.

### Actual checks and review

Existing macOS arm64 Python **3.12.14**, Pydantic **2.14.0**, uv-managed environment;
used repository-local `UV_CACHE_DIR` and `uv run --no-sync` to preserve installed
optional capabilities. No installation, model download, cloud or paid execution.

| Executed check | Actual result |
| --- | --- |
| Frozen original diagnostic execution before implementation edits | Exact equality with original reference; baseline results above. |
| Focused new scorer tests before corrections | **7 passed in 0.13s**. |
| Focused scorer/analyzer/CLI suite after corrections | **57 passed in 1.06s**. |
| Final new holdout regression suite | **25 passed in 0.13s**. |
| `uv run --no-sync pytest` | **865 passed, 7 skipped in 50.49s**. Existing model/host opt-in tests skipped. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 174 files already formatted. |
| `git diff --check` | Passed; no whitespace errors. |
| Independent initial scorer/freeze audit | Reproduced baseline/reference and hashes; focused **37 passed**. Target-edge issue corrected, other artifacts documented. |
| Independent final code/evaluation review | **60 focused tests passed in 0.91s**, whole-repo Ruff/format/diff clean; source/dataset/scorer freezes and all six audited reports reproduced. No actionable blockers. Reviewer did not rerun the full suite. |

Changes are limited to the two source corrections, focused synthetic evaluator,
freeze/holdout/report artifacts, meaningful regression tests, this status and
linked evaluation documentation. Existing observation/probabilistic estimators
remain unchanged. No commit, push, merge, publication or later milestone started.

## First selected real-conversation evaluation reports — 2026-10-12

Read AGENTS.md, the existing status, M3/M4 plan semantics and the conversation
importer/task-state/holdout documentation. Used the current checkout, preserving
the pre-existing `.DS_Store` modification. Read only the four user-selected IDs
through the supported standalone `AppServerClient` / `read_conversation`; no
history enumeration, desktop reader fallback, private storage parsing or project
artifact/test-result access. Selected identifiers, titles, message excerpts and
semantic snapshots remain exclusively in ignored private local storage.

### Freeze and privacy

- Saved the current production analyzer and importer source copies, SHA-256
  digests, Git/runtime versions, default rule configuration and source selection
  before analysis. The original historical baseline archive is not substituted
  for the current analyzer. No source, classifier, limit, dependency or model edit.
- Processed opted-in extracted user/assistant text in Python memory. Full item
  retrieval receives other content before local exclusion; non-message bodies
  never reach semantic inference. No raw response, full transcript, preview,
  attachment body, tool result or unnecessary assistant prose was persisted.
- Saved immutable predictions, input/prediction hashes and version bindings before
  rendering or reviewing reports. No selected reference labels or independent
  project verification results were inspected before or after freezing. Only
  supporting semantic/uncertainty excerpts and source metadata are retained.
- Private artifacts include four source-specific prediction/coverage reports,
  aggregate coverage and transition summary, human-interpretation queue,
  limitations and a file-hash manifest under `.model-learner/`. Directories/files
  have private permissions and every artifact is Git-ignored. Nothing is committed.

### Actual coverage and incomplete evaluation

The rows below are anonymized selection positions, not invented task identities.

| Selection | Successful source coverage | Semantic coverage / gate |
| --- | --- | --- |
| Codex A | Metadata-only: 3 native turns, cursor exhausted; message count unknown | Full-view read rejected after 67,887 wire bytes crossed 65,536; no predictions. Metadata fallback: 3,874 bytes. |
| Codex B | Metadata-only: 4 native turns, cursor exhausted; message count unknown | Full-view read rejected after 69,123 wire bytes crossed 65,536; no predictions. Metadata fallback: 4,078 bytes. |
| Codex C | 4 native turns, 12 messages, 4 user messages; 35,482 wire bytes / 6,372 extracted text bytes | All 12 messages and 4 user turns analyzed. |
| Work Local D | 4 native turns, 11 messages, 4 user messages; 52,058 wire bytes / 20,417 extracted text bytes | First 9 messages / 3 user turns analyzed; fourth user's prefix has 261 clauses, full input 297, above 256. |

Every successful read validates the selected product originator and Codex backend,
preserves reversed descending turn pages and original item order, and exhausts
exposed cursors. This does not prove complete original history, hidden branches or
UI fidelity. Source truncation flags remain null/not emitted; application-bound
rejections are reported separately. Message timestamps, historical model/settings,
tokens and cost remain unknown. Native thread/turn time fields are retained as
source history metadata; retrieval receipts are not execution timestamps.
Non-message item counts for the two full-view successful reads are 19 and 17;
their bodies were excluded. Such counts are not reconstructed tool telemetry.

The initial sandboxed server exited 1 before any selected read. Scoped execution
permission enabled the same bounded process; successful temporary servers exited
0. A private report-writing mapping error interrupted the batch after one source's
predictions were saved. It was repaired, and the repeated selected read confirmed
identical input/predictions without replacing that original freeze. The Work
source was reread only to capture coverage and freeze admissible original prefixes
after its full analysis failed. No message/clause clipping or summarization was
used to evade the bounds; later checkpoints are explicitly unavailable.

### Reported transitions and interpretation limits

- The completely analyzed source never establishes an objective: it recognizes
  3 added-requirement facts, 4 decision facts, 2 failure reports, 5 progress reports
  and 7 completion claims. Two completion claims are user-attributed and five
  assistant-attributed. Its final positive evidence includes the two user decisions,
  for 5 requirement evidence entries; these are not normalized active requirements.
- The partial Work source establishes an initial objective and retains it through
  the analyzed prefix. It recognizes 2 removals, 1 addition, 1 revision, 7 decisions,
  1 unresolved report, 2 progress reports and 3 assistant completion claims.
  Two scope edits have unresolved target links. The fourth user turn has no state
  prediction and is not silently assigned the earlier scope.
- Neither analyzed source recognizes a decision reversal or task switch. This is
  a detection count, not proof of absence. Unparsed/ambiguous statements, missing
  objectives, candidate targets, proposed versus accepted assistant choices, and
  instruction/status-example versus event-report distinctions require human review.
- All **21 available message checkpoints** have `verification=unknown` and zero
  independent check inputs. Assistant statements about tests/completion never
  become verified outcomes. User-reported status is not independent verification.
- Per-user-turn reports distinguish request-prefix state from subsequent assistant
  response state, preserving cumulative evidence and exact message/character spans.
  Blocked sources expose only native-turn coverage slots; no user turns, objectives
  or semantic zeros are fabricated from metadata. No human labels, accuracy scores,
  causal claims or real predictive benefit are established.

### Actual checks and stopping point

Existing Python 3.12.14 / uv-managed environment; used repository-local uv/cache
paths and `--no-sync`. No installation, paid execution, network inference or model
download. Model Learner's own regression tests are separate from independent tests
of the selected projects and do not supply semantic inputs or project outcomes.

| Executed check | Actual result |
| --- | --- |
| `uv run --no-sync pytest` | **865 passed, 7 skipped in 46.49s**; existing opt-in host/model checks skipped. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 174 files already formatted. |
| Private artifact integrity/privacy check | Passed: manifest and prediction hashes, unchanged source hashes, private permissions, Git ignore, source-role/turn/span references, no raw text in prediction/metadata snapshots and unknown verification. |

Reports are produced; full requested semantic evaluation remains incomplete under
the supported bounds. Next unstarted step: separate direction for a supported
bounded strategy covering both rejected text reads and the final Work prefix,
then human adjudication. No rules/models were tuned, no estimators connected,
and no Task/Run/Attempt associations, execution telemetry or historical model
attribution were invented. No outcome integration, commit, push, merge, publication
or subsequent milestone. Stop after these reports.


## Selected-input coverage recovery — 2026-10-12

Read repository instructions/status, relevant M3/M4 provenance semantics,
conversation task-state/holdout/importer documentation and prior selected-report
metadata. Preserved the pre-existing `.DS_Store` modification and prior STATUS
content. Implemented only input selection/coverage reporting in
`understanding/conversation_projection.py`, five regressions reusing existing
fixtures, and `docs/CONVERSATION_INPUT_PROJECTION.md`. No new semantic evaluation
conversation or reference label. Production analyzer/importer/transport source
hashes exactly match the original private evaluation freeze.

### Privacy and deterministic freeze

Requested and received explicit approval for one bounded reread of only the same
four IDs: temporary read-only App Server, ten one-turn pages, at most 256 KiB
cumulative transport per source. The diagnostic runner loads unchanged transport
code in an isolated module namespace with the approved byte allowance; production
64-KiB default and importer extracted-text bounds stay unchanged. No discovery,
related conversation, datastore, project artifact or independent outcome access.
Full-item responses are received before local non-message exclusion; only numeric
item-type/count/byte statistics survive. No private text/raw response/excerpt is
printed or retained. Native source mapping and text-free predictions are private
under ignored `.model-learner/projected-real-evaluation-20261012/`, with 0700/0600
permissions and exclusive artifact writes. Original artifacts remain immutable.

Policy/helper/runner hashes and original manifest digest froze before the read or
prediction evaluation. Each source's predictions/hash/input digest froze before
comparison to old predictions. No human labels or independent project checks were
inspected before or after freeze. No classifier tuning, new model, estimator,
Governor, canonical task association, outcome inference or verified claim.

### Actual diagnosis and recovered coverage

| Original selection | User messages / UTF-8 bytes / clauses | Assistant messages / bytes / clauses | Actual wire bytes | Projected user checkpoints |
| --- | --- | --- | --- | --- |
| Codex A | 3 / 1,326 / 30 | 9 / 3,247 / 48 | 93,795 | 3/3 |
| Codex B | 4 / 1,272 / 28 | 10 / 4,366 / 62 | 110,337 | 4/4 |
| Codex C | 4 / 1,791 / 44 | 8 / 4,581 / 59 | 35,482 | 4/4 |
| Work Local D | 4 / 1,578 / 37 | 7 / 18,839 / 260 | 52,058 | 4/4 |

All temporary servers exited 0 and exposed pagination exhausted. That does not
prove complete original history or UI fidelity; truncation markers were not
emitted. No text, clause, message-count or per-message-character limit was reached
in any projected user prefix or any of 34 separate whole-assistant-message reads.
No arbitrary truncation, summarization or omitted user requirements/decisions.

A/B exceeded original transport bounds because command/file-change items dominate
wire input. Compact reserialized command/file item bytes were 53,899/27,203 for A
and 64,876/29,698 for B; whole extracted message text was only 4,573/5,638 bytes.
Documented per-item metrics distinguish reserialized sizes from exact wire bytes.
All source message IDs are unique, bridge strings equal source-part newline joins,
and joining expansion is zero in all four sources. No parsing duplication,
normalization or lexical expansion. Source-authored repetition is not excluded.

D's fourth user text is 246 bytes/6 clauses; the prior full prefix already has 255
clauses and rises to 261. Three earlier assistant messages contribute 15,808 bytes
and 218 clauses. All four user messages together have 37 clauses, recovering the
fourth checkpoint without processing those explanations as task-intent input.
The original complete full-input total is 297 clauses. Short clause distributions
are recorded, and no clause splitting rule was modified.

### Predictions and limits

- Frozen policy: every unchanged user message in source order, every full user
  prefix, original native IDs/item ordinals/turns/full-message evidence-span mapping.
  Checkpoints list included users, omitted assistants, bounds and available versus
  unavailable fields. Assistant reports are analyzed separately per whole message,
  with no cumulative execution state. Independent evidence stays null/unavailable.
- Final user intent counts (add/revise/remove; decision/reversal): A 10/1/0 and 1/0;
  B 3/0/0 and 2/0; C 3/0/0 and 2/0; D 3/1/2 and 2/0. Objectives are recognized
  only for B/D. A/C remain unknown; many clauses remain other/ambiguous. No detected
  reversal/task switch is a recognition count, not proof of absence.
- Separate assistant reported progress/completion counts: A 2/4, B 5/5, C 4/5,
  D 4/3. Test results have no dedicated field in this frozen analyzer; these reports
  never become independent execution checks or outcomes. All 49 analyzed
  user-prefix/assistant-message endpoints have verification unknown.
- User-clause classifications agree with original frozen predictions on 44/44
  shared C clauses and 31/31 shared D clauses. This is reproducibility, not accuracy.
  A/B have no original semantic baseline; D's fourth user is newly covered.
- C loses one candidate user-decision link to an omitted assistant decision.
  D's overlapping user candidate links are unchanged, but one removal and one
  revision target remain unresolved. Original full-text predictions stay separate;
  no projected output is relabeled as the historical baseline.
- Short approvals, implicit requirements/objectives, instruction/status-example
  versus event reports, proposed versus accepted assistant decisions, lexical
  targets and cross-message context need human adjudication. Missing independent
  checks, execution histories, historical settings/cost, source fidelity and task/
  run associations remain unknown. No semantic accuracy score is supported.

Recommendation: useful enough for human-adjudicated semantic review of the same
selected sources with both views and original references. Freeze the adjudication
policy before reviewing. Not ready as trusted success/utility features. Human
adjudication, outcome integration and all later milestones remain unstarted.

### Actual checks and independent review

Existing Python 3.12.14 environment; repository-local uv cache and `--no-sync`.
No installs, cloud inference or model downloads.

| Executed check | Actual result |
| --- | --- |
| Focused projection/analyzer/importer tests | 57 passed in 0.20s. |
| `uv run --no-sync pytest` | 870 passed, 7 existing opt-in skips in 51.54s. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 177 files already formatted. |
| `git diff --check` | Passed. |
| Freeze/private artifact integrity | Source hashes, original manifest, prediction digests, exact source mappings, no retained message text, unknown verification and ignored private permissions checked. |
| Independent code/report review | No actionable defects; 5 projection tests and Ruff lint/format passed. Numeric totals and omission/baseline qualifications reviewed. One turn-number wording correction applied. Reviewer read no private artifacts/labels/outcomes and did not rerun the full suite. |

Stop after this evaluation and recommendations. No commit, push, merge,
publication or later milestone started.

## Blind human-adjudication worksheet — 2026-10-12

Phase 1 only. Read repository instructions and the requested conversation-state,
holdout and input-projection documentation. Existing approved evaluation data
omitted full original message text, so requested and received explicit permission
to reread only the same four selections: at most ten one-turn pages and 256 KiB
cumulative transport per conversation, retaining user text only in ignored local
storage. The initial sandboxed attempt failed with a content-free diagnostic;
the scoped approved run succeeded and all four temporary servers exited 0.

Created one Markdown worksheet under ignored `.model-learner/annotations/`.
It contains 3, 4, 4 and 4 unchanged user messages, native message/evidence IDs,
conversation IDs and original turn/message/item positions. All ten annotation
fields per message are blank; multiple entries and earlier requirement/decision
references are supported. No predictions, reference labels or AI interpretations
are included. No assistant prose, tool body, preview or raw response was retained.
Original text is the unchanged source-part newline join. Chronological ordering
uses native turn-start metadata across conversations and preserves source order
within each conversation. Exact message timestamps, hidden history and original
UI fidelity remain unknown and are described in the worksheet.

The one-off preparation script reused the existing read-only importer and an
isolated transport module with the explicitly approved 256-KiB allowance. No
production source or default was edited, and the semantic analyzer was never
loaded or run. Frozen evaluation/prediction artifacts were not opened; metadata-
only inode/size/mtime/mode checks confirmed both existing artifact trees stayed
unchanged. No labeling, prediction comparison, tuning, training or outcome
integration occurred. Private output directory/file permissions are 0700/0600.
The temporary preparation script was removed after validation.

| Check | Actual result |
| --- | --- |
| Bounded selected-source reads | All four completed within the approved bounds; exposed cursors exhausted. |
| Worksheet structural/text verification | 15 distinct native message IDs, exact rendered text round-trips, 150 blank annotation fields, source order preserved; user text byte totals match the documented source totals. |
| Privacy and unchanged-artifact checks | Output Git-ignored, private permissions confirmed, no private contents printed; existing evaluation artifact metadata unchanged. |
| Preparation-script Ruff | Passed after formatting and correcting long lines; collector was not rerun. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 177 files already formatted. |

No pytest run: this task changes only a private worksheet and this status note;
relevant validation is the source/text/order/blinding verification above. No
implementation milestone started. Stop with the worksheet ready. Genuine human
annotation is pending; Phase 2 comparison requires separate user authorization.

## Frozen prediction / independent AI-reference comparison — 2026-10-12

The user separately authorized comparison against completed independent Work
annotations. Read AGENTS, status and conversation task-state/holdout/projection
documentation; used only existing private artifacts and the earlier blank source
worksheet. No conversation retrieval, analyzer import/execution, implementation,
rule tuning, training, model download or outcome/utility/Governor integration.
The AI annotations remain explicitly distinct from human-adjudicated truth.

Delivered a detailed private report, reproducible matching ledger, input/hash
inventory, validation evidence and independent methodology review under ignored
`.model-learner/`. No private text, annotations, native IDs or per-conversation
interpretations were added to tracked files. Both original result sets retain
their bytes, size and modification timestamps. The prediction manifest's 20
entries, original source hashes and projection hash validate unchanged. Native
message IDs, source positions, complete user-prefix order and unchanged worksheet
text align for 15/15 messages; all 150 reference cells are populated. All 139
unique new user-fact spans validate. Local freeze receipts predate the annotation
file; blindness is supported by attestations, not an authenticated audit of when
annotation began. Assistant context and independent execution evidence remain
unavailable.

Measurements use explicit post-hoc atomization, semantic equivalence and disclosed
same-message contextual matching. They separate new events from cumulative state,
incomplete/missing predictions from incorrect events, unsupported representations
from misses, and annotation-policy overlap from distinct changes. They do not
collapse 150 cells into one accuracy score:

- Current core-action objective agreement: **3/15**; broader topic compatibility
  separately **8/15**.
- Typed positive-obligation alignment: **21/24** normalized predicted semantic
  units and **21/84** reference obligations. Raw fragment alignment is **21/25**;
  the extra unit is an adjacent duplicate fragment, not a semantic false positive.
  Alternative positive evidence covers **32/84** obligations.
- Choice-content alignment: **6/8** predicted units and **6/28** reference choices;
  explicit reversal recall **0/2**, with precision unavailable at **0/0**.
- Narrow supported-operation scope-change alignment: **2/3** predicted changes
  and **2/5** reference transitions. The broader reference revision policy is not
  directly comparable; unsupported reinstatement has no semantic precision/recall.
- Native-message attribution of matched obligations: **32/32**, distinct from
  semantic target-link agreement. The one emitted user scope-target candidate is
  unsupported (**0/1**). Source traceability is not semantic correctness.
- Nominal field mappings: **135/150**, including partial mappings; descriptive
  nonempty field presence **49/150**. Neither is accuracy. Full active-scope,
  unresolved-work inventory and semantic uncertainty agreement are unavailable.

The report documents every message's substantive disagreements and evidence,
five ranked human-review priorities, representation limits and a minimal next
experiment. Rules can support an inspectable evidence-review subset; they do not
reliably resolve task scope, temporal changes or speech acts. Recommended next
step, unstarted: human adjudication/policy freeze, then a separately authorized
bounded local semantic-extractor comparison with this baseline unchanged. New
blind cases are needed for any subsequent generalization claim. No predictive
utility improvement is claimed and no semantic features enter outcome estimators.

| Executed check | Actual result |
| --- | --- |
| Read-only comparison artifact validation | Passed: unchanged inputs/source hashes, 15 native IDs, 150 cells, 139 facts, turn ordering, metric sums, table structure, private permissions and Git ignore. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 177 files already formatted. |
| Explicit private report-script Ruff checks | Passed; four scripts lint-clean and formatted. Initial local script formatting/lint issues were repaired without changing either input set. |
| `git diff --check` | Passed. |
| Independent methodology/ledger/report review | Accepted after distinguishing duplicate fragments, unsupported reinstatement and topic versus objective agreement; numeric sums, source mappings and hashes independently checked. No remaining substantive blockers. |

No pytest run: there is no implementation change, and this task explicitly forbids
rerunning the analyzer. Artifact validation is the relevant test and invokes no
analyzer code. Pre-existing working-tree changes are preserved. No commit, push,
merge or publication. Stop after the private comparison report; no next experiment
or milestone started.


## Git repository privacy/security audit — 2026-10-13

Completed the explicitly requested audit and safe preventive implementation only.
Read the repository instructions/status/plan privacy sections, README, ignore rules
and existing benchmark/observation privacy guidance. Initial state: main, 233
tracked files, zero staged changes and one modified Finder metadata file. Locally
available history: 28 refs, 25 reachable commits, 233 historical paths, 339 unique
blobs, 343 path/blob/mode combinations and 7,312,448 bytes. Every reachable blob
and commit metadata was locally scanned without emitting secret or transcript
contents. No historical-only deleted paths, special index modes or LFS pointers.
No high-confidence credentials or raw private transcripts confirmed. Broad
conversation/credential-canary matches were resolved through fixture provenance
and source context; existing real sanitized smoke metadata remains distinct from
simulated fixtures.

Two findings: tracked `.DS_Store` in two historical versions, and one identifying
absolute home-path reference in public developer documentation. Both are reachable
from cached origin history; live GitHub exposure/public visibility was not checked.
Finder metadata is removed from the index only; its modified local bytes, size and
mtime are unchanged. The public documentation prefix is now portable. Earlier
copies remain in Git history. No rotation indicated by the detected findings;
optional historical cleanup needs separate approval and human metadata-risk review.

Delivered strengthened ignores, a standard-library actual-index/committed-tree
privacy guard, 17 exact reviewed fixture digests, executable versioned pre-commit
hook, push/PR GitHub CI workflow, permanent AGENTS policy, developer instructions
and sanitized report in `docs/REPOSITORY_PRIVACY.md`. Local hooksPath is activated
as `.githooks`; no global Git settings changed. Hook/CI failures propagate nonzero.
Tests run only harmless synthetic fixtures in isolated temporary repositories.
They demonstrate path/content rejection, force-add protection, real staged bytes,
index policy provenance, safe source/docs/fixtures, nonleaking diagnostics, local
preservation, unusual names, hook and committed-tree enforcement, fail-closed
special/large/invalid entries, and replacement-object resistance.

| Executed check | Actual result |
| --- | --- |
| Local object/history inventory and content scan | 25 commits / 339 unique blobs inspected; no detected credentials; two sanitized hygiene/privacy findings. No fetch or external scanning. |
| `uv run --no-sync pytest` | 927 passed, 7 existing opt-in skips in 90.74 s. Collected before the final two guard regressions; final affected tests rerun below. Includes concurrently present unrelated experiment tests. |
| Final `uv run --no-sync pytest tests/integration/test_privacy_guard.py -q` | 55 passed in 10.28 s. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 188 files already formatted. |
| `git diff --check` and `git diff --cached --check` | Passed. |
| Scoped proposed index and tree, isolated temporary index/object store | 238 entries inspected, zero rejections in both modes; no implementation files staged in the actual checkout. |
| Actual index / hook state | Only `.DS_Store` deletion staged; hook active. Until reviewed policy is staged, guard rejects 17 existing session-format fixtures as expected. |
| Independent security review and recheck | Reproduced replacement-ref bypass; fixed every Git reader and added index/tree regression. Proposed-tree source-field false positive corrected with structural JSON parsing and acceptance regression. Final independent 55-test/Ruff recheck passed; no remaining blockers. |

Existing environment/cache used; no dependency installations or AI calls. The
initial uv invocation could not access its default out-of-workspace cache; reran
successfully with the existing repository-local `.uv-cache`. A non-UTF-8 filename
creation test hit a local filesystem restriction; its final test exercises Git's
index directly, without weakening filename handling. No private datasets deleted,
private data staged for testing, fetch, history rewrite, commit, push, merge or
GitHub setting changes. Unrelated concurrently appearing experiment files are
preserved and excluded from the recommended security commit.

Limits: heuristic detection cannot prove arbitrary prose/encoded secrets are
public; exact fixture exemptions require provenance review. Local hooks can be
bypassed; CI needs enforced GitHub rules and protected policy/workflow reviews.
CI checks final trees, not earlier intermediate commits or external copies. Only
locally reachable history and cached origin refs were audited; unfetched/deleted
remote refs, forks/releases and unreachable/reflog-only objects remain uninspected.
Stop after the audit; await approval before committing/pushing or any historical
remediation. Next development experiment/milestone remains separately authorized.


## Bounded local CPU semantic-extraction comparison — 2026-10-13

Completed only the explicitly authorized experiment. Read AGENTS/status/master
plan (especially observation/inference/verification boundaries), requested
conversation-state/holdout/projection documentation and the prior private
AI-reference comparison. The initial checkout's Finder modification and later
concurrent repository privacy-audit changes were preserved; this task did not
create their hook, CI, privacy guard or staged Finder deletion.

Delivered isolated experimental code under `experiments/local_task_state/`, a
compact evidence-bearing schema, one frozen zero-shot prompt, deterministic
structural parsing and a read-only frozen-analyzer adapter. The common schema
separates requested actions, obligations/constraints, choices/reversals, changes,
reinstatement, reports, conditionals, earlier references and uncertainty. Exact
original quotes, message identities, roles/turns and half-open source spans are
validated. Targets stay nullable; no candidate link is promoted into accepted
active scope or independent verification. Production source remains unchanged:
analyzer SHA-256 `9f90a466de5e0bc0957277a453afb304491213fccb1ca517d7c1ca992978319b`.

Investigated Qwen2.5-1.5B-Instruct, Qwen3-1.7B and SmolLM2-1.7B using primary
model/runtime documentation. Explicit user approval permitted only the selected
official Qwen2.5 Q4_K_M weights: 1,117,320,736 bytes, Apache-2.0, publisher hash
verified. Local official llama.cpp b11580 ARM64 runtime uses CPU only (device
none, zero GPU layers, no KV offload), six threads, one slot, no prompt cache,
8,192-token context and bounded output. Runtime/weights remain ignored; project
dependencies and lockfile unchanged. No cloud/paid inference or fine-tuning.

The 15 original real user checkpoints remain consumed diagnostics. A separate
prediction-blind AI author created four fresh simulated topics, 16 checkpoints,
56 events and nine earlier links. Original and synthetic sources/references,
prompt, schema, extractors, runtime configuration and initial scorer froze before
prediction generation. An independent pre-output-inspection review required
scorer integrity fixes (unique coverage, nonnegative indices, match reasons) and
a request-only positive-obligation denominator amendment; original scorer/freeze
were retained. Original-denominator sensitivities are disclosed. No prediction-
informed prompt/rule tuning or reference relabeling. A distinct final reviewer
checked all input receipts, validations, metrics and semantic matching ledgers;
one B uncertainty match was corrected. Original private comparison/input bytes
and the independent synthetic labels remain unchanged.

| Audited finding | Frozen rules A | Structural B | Local model C |
| --- | --- | --- | --- |
| Fresh holdout objectives / known objectives | 1/16; 0/15 | 5/16; 4/15 | 1/16; 0/15 |
| Holdout positive-obligation precision / recall | 10/16; 10/31 | 12/13; 12/31 | 3/25; 3/31 |
| Holdout earlier-link recovery | 0/9 | 0/9 | 0/9 |
| Holdout valid local event citations | 56/56 | 24/24 | 4/33 |
| Holdout false failure / completion events | 3 / 0 | 0 / 0 | 0 / 0 |
| Diagnostic objectives | 3/15 | 8/15 | 0/15 |
| Diagnostic positive-obligation precision / recall | 23/30; 23/84 | 35/43; 35/84 | 2/30; 2/84 |
| Diagnostic canonical scope-target recovery | 0/6 | 1/6 | 0/6 |
| Diagnostic valid local event citations | 139/139 | 95/95 | 4/32 |

These are common-schema, one-to-one AI-reference matches. Old post-hoc typed
21/24 and 21/84/overlay32/84 measurements remain historical and unchanged; they
are not directly interchangeable with the new scorer. Invalid C events remain
in precision denominators, with raw outputs retained. They usually repeat earlier
messages or confuse message ordinals with exact-quote occurrences. All C
objectives are null. Zero false status claims coexists with missing all three
holdout failures and both completion claims. Verification is null by contract at
all 93 candidate checkpoints; this is a safeguard, not semantic accuracy evidence.

C holdout median/p95 is 4.98/14.53 s (16 trials), diagnostics 9.07/14.17 s (15).
Runtime lifetime peak RSS is 2,344,894,464 and 2,353,102,848 bytes respectively;
fresh-process loads 7.11 and 1.55 s. macOS getrusage measures the sole runtime
child separately from the driver (~1.1 GiB transient hashing peak). Every prompt
cache count is zero, every generation ends normally, and none is truncated.
Initial sandbox startup failed to bind loopback without producing predictions;
scoped approved execution succeeded and both measured servers exited zero.
Repository checks overlapped early holdout inference, so timings are observational
rather than idle-machine benchmarks. Post-run runner/scorer hardening preserves
the actually executed versions and changes no saved prediction.

The sanitized report and design are `docs/LOCAL_TASK_STATE_COMPARISON.md` and
`docs/LOCAL_TASK_STATE_EXPERIMENT.md`. All private source/diagnostic annotations,
raw results, comparison ledgers, model/runtime, freeze/version receipts, resource
logs and independent final review stay in ignored local storage. Public fixtures
are independently authored simulated material, never copied private conversations.
The new permanent privacy instructions were read when concurrent changes appeared.

| Executed check | Actual result |
| --- | --- |
| Final `uv run --no-sync pytest` | 931 passed, 7 existing opt-in skips in 56.00 s; includes concurrent privacy-guard tests. |
| Final focused experiment tests | 6 passed in 0.08 s after all reporting/hardening changes; independent reviewer rerun: 6 passed in 0.11 s. |
| `uv run --no-sync ruff check .` | Passed; all checks passed. |
| `uv run --no-sync ruff format --check .` | Passed; 189 files already formatted. |
| `git diff --check` | Passed. |
| Private input/output/artifact validation | Passed: 93 identical-prefix receipts, every saved extraction/metric reproduced, 31 cache-zero stopped generations, prior comparison manifest and source/reference/prompt freezes unchanged. |
| Independent semantic/code/methodology review | Accepted with denominator/context sensitivities, partial objective/reference-population limits, and one B uncertainty correction; no extractor/label tuning. |

Recommendation: C fails the semantic improvement screen despite practical CPU
resources. Keep production and trusted estimators unchanged. Structure/evidence
parsing can support human review, but a local-inference/state-update hybrid remains
unproven. Any later candidate/prompt experiment needs separate authorization and
fresh prediction-blind, preferably human-adjudicated cases. No next milestone,
model download, commit, push, merge, publication or outcome integration started.

## Real execution/outcome readiness assessment — 2026-10-13

Read AGENTS, STATUS, relevant plan identity/provenance/learning and M3/M4/M6
sections, existing observation/verification/learning documentation and implementation.
Delivered only the sanitized assessment in docs/REAL_DATA_READINESS.md and this
status update; no runtime or schema changes. Preserved the pre-existing untracked
experiment source file without reading or modifying it.

### Actual evidence and privacy scope

- Six existing local SQLite ledgers were queried read-only for aggregate counts;
  the eligible smoke cohort was revalidated through read-only repository assessment
  resolution. **One eligible real fixed-reply execution; zero eligible real coding
  executions**. An unknown smoke derivation is the same run, not another trial.
  The separate actual JUnit producer-validation assessment has no learner rows and
  is not a coding-agent execution. Counts are scoped to inspected local evidence.
- User explicitly approved the three selected chat reads, local project inspection
  and verification. Returned views expose 3/4/4 turns with timestamps, but no
  configuration/usage fields. Turns/tool activity do not create attempts; no
  historical task/run/configuration attribution or native timing was invented.
- Independently authored synthetic probes executed outside the producing chats on
  byte-identical private copies: **JSONL Validator 3/3**, **Markdown Indexer 4/4**,
  **Job Status Selection 3/3** passed. Separately rerun existing agent-authored
  suites: **27**, **22**, **8** passed respectively. All processes exited zero.
  Job-selection probes include all 24 interleavings of the offset-aware fixture.
  Markdown's current final scope is JSONL plus exclusions, distinct from its
  earlier CSV request; acceptance versions must not be retroactively merged.
- Original artifacts and tested copies remained unchanged under before/after
  content manifests. Private JUnit XML, report/artifact/test-source hashes,
  process timestamps/exit/completion receipts, copied code, and bounded chat
  metadata are retained under ignored `.model-learner/real-data-readiness-20261013/`.
  No transcript or project source is copied into public documentation/fixtures.
  Fresh checks establish current named-check results, not historical acceptance,
  agent execution outcomes, universal correctness or independent trial counts.
  No new ledger observations/associations/assessments were created.

### Recommendation, blockers and next user-directed step

Use the existing ordinary operator-run CLI capture/JUnit workflow for the next
5–10 genuine coding executions. Create the task and freeze trusted acceptance
before execution; retain actual launch/configuration/starting-state receipts;
import capture; explicitly declare bounded run/attempt coverage; freeze and
independently check the final artifact; import JUnit binding evidence; assess,
build and resolve real observations. Keep unknown cost/native times/model versions
null and manual settings labeled declarations. No collector or infrastructure
layer is needed for this collection pilot.

Historical project eligibility remains blocked by supported execution capture,
known configuration/segment attribution and per-execution artifact/acceptance/report
bindings. Passing final code today cannot repair those omissions. Desktop-only
collection would need separately authorized execution-observation support. The
separate benchmark real-execution containment gate remains unchanged; the ordinary
observation path does not bypass it.

Existing estimators can consume correctly eligible coding rows under exact dataset,
acceptance/version, budget and configuration selectors. Unrelated acceptance
criteria cannot be pooled by renaming them; ordinary new tasks may yield only one
row per target. Five to ten rows test collection coverage, not predictive benefit.
Future semantic comparison needs frozen pre-outcome inputs and independent labels,
comparable targets, prospective availability receipts, chronological/task-family
holdout and adequate sample size; current task-state floors remain 30 training,
20 scored, five task clusters per partition and both training classes. After-close
CLI associations alone cannot satisfy initial checkpoint availability. No semantic
state is integrated and no models were trained.

Next unstarted step: user selects the first five upcoming tasks and explicit
configuration, then follows the documented operator sequence for one execution
before repeating it. Stop at the collection/quality report; training/evaluation
expansion remains separately directed. No paid agent launch, commit, push, merge,
publication, new model, routing, Governor or next milestone was performed.

### Actual checks

- Initial `uv run --no-sync` invocations could not access the default external uv
  cache; retried successfully with repository-local `UV_CACHE_DIR=.uv-cache`.
  No installation or escalation was needed.
- `UV_CACHE_DIR=.uv-cache uv run --no-sync pytest`: **931 passed, 7 existing opt-in
  skips in 60.53s**. These repository tests are distinct from project acceptance.
- `UV_CACHE_DIR=.uv-cache uv run --no-sync ruff check .`: passed.
- `UV_CACHE_DIR=.uv-cache uv run --no-sync ruff format --check .`: passed,
  **189 files already formatted**.
- Private project check driver: three existing suites and the fresh **10-test**
  independent pytest/JUnit suite passed, zero failures/errors/skips; original and
  copy integrity checks passed. Checks are post-hoc and do not run a coding agent.
- `git diff --check`: passed; private receipt/XML paths confirmed Git-ignored.

## First supervised real CSV coding experiment — 2026-10-13

After reading AGENTS, status, readiness guidance and relevant plan contracts, the
operator prepared one ordinary supervised CLI coding task. This uses the existing
real observation workflow documented in docs/REAL_DATA_READINESS.md; the separate
benchmark controller and its blocked containment gate are unchanged.

- Independently authored 18 synthetic black-box acceptance tests before execution.
  Froze the CLI interface, JSON schema, exact comparison behavior, CSV quoting,
  validation/error behavior and dependency constraint. Required pytest/JUnit
  identities, test/criteria digests, configuration, prompt, launch arguments and
  starting-state manifest were recorded before approval. A constant-output negative
  control failed 15 checks; all 18 report identities matched the task declaration.
- Actual unpaid local Codex sandbox canary allowed working-directory writes and
  denied writes to acceptance source, the control directory and neighboring
  temporary storage. The agent's working directory was separate from this
  repository. This demonstrates the selected write boundary, not a VM or complete
  host-read isolation. Agent tool networking, escalation, web/apps/plugins/hooks
  and additional agents were disabled; provider access used existing ChatGPT auth.
- The user explicitly approved one execution and subsequent verification/audit.
  Executed exactly one fresh ephemeral Codex CLI invocation requesting OpenAI
  gpt-6.1-sol, low reasoning, CLI 0.162.0-alpha.17.2. Agent and live metadata capture
  each exited 0, with no timeout. Operator agent-process wall time: 123.44 seconds.
  Receipt timestamps and operator wall measurements are not native latency.
- Capture/import retained 11 supported events for one session, one completed turn
  and three observed tool items, with zero import diagnostics. Native cumulative
  usage: 91,335 input tokens, including 60,416 cached input; 6,587 output tokens,
  including 199 reasoning output. Subsets are not added to their parent totals.
  Model/provider/reasoning/version were not emitted by the stream: requested
  settings are explicitly operator declarations, not observed native configuration.
- Stopped the agent and copied its sole standalone module to an exact private
  snapshot before independent testing. Original/snapshot digests agree; starting
  instructions, frozen acceptance/configuration/command files and final code remain
  unchanged. Executed the frozen suite under a local filesystem/network sandbox:
  **18 passed in 0.99s**, exit 0, zero failures/errors/skips. No candidate repair or
  second coding-agent invocation followed the independent result.
- Used existing `run create`, `run attempt`, `verify junit`, `outcome assess` and
  `observations build`. An actual operator receipt binds task/run, acceptance
  version, final artifact/report digests, report generation time, completion and
  exit status. The persisted outcome is **success / verified**, with one matching
  verification; the real observation has **single_configuration** attribution,
  eligibility true and no exclusions.
- `observations quality` and historical `observations resolve` confirm one eligible
  real execution in this new private dataset. Existing `learn predict` consumed
  exactly one selected eligible success, zero failures and zero exclusions. This
  exercises the existing fixed-prior reference; it creates no new trained model
  or model weights and establishes no predictive accuracy or model superiority.
- Replay inserted zero events and recognized all 11 duplicates. Final ledger audit:
  one Task, Run, Attempt, Session, Verification, Outcome and Observation; 11 Events.
  Dollar cost and canonical attempt/observation latency remain null. Native usage
  is retained on captured events; the existing attempt convenience CLI does not
  fabricate resource measurements from the stream or operator clock.
- Private tests, configuration, command/launch receipts, metadata capture, snapshot,
  XML/binding, ledger, returned CLI records and compact experiment result remain
  under ignored `.model-learner/first-real-csv-20261013/`. Public status contains only
  sanitized behavior and aggregate evidence. Preserved the pre-existing untracked
  experiment file without reading or modifying it.

Validation: relevant capture/JUnit tests **80 passed**; full repository tests
**931 passed, 7 existing opt-in skips in 58.60s**; Ruff and formatting clean;
`git diff --check` clean. No production code, dependencies, semantic analyzer,
benchmark infrastructure, new model training, AI Governor, commit, push, merge,
publication or global hook changes. The requested single experiment is complete.
Next step remains unstarted and requires separate user direction; do not run
another task or expand evaluation automatically.

## Experiment 2: ShortcutLens seed-validation preparation — 2026-10-16

The user selected one real project maintenance task and authorized preparation
only. Installed Python 3.13.9 / PyTorch 2.14.1 CPU Generator probes accept the
tested Python-integer endpoints -2**63 and 2**64-1 and reject adjacent values.
ShortcutLens's existing nonnegative policy is preserved. Direct NumPy Integral
inputs fail at the Torch boundary and require normalization. With a synthetic
source, both oversized Torch-bound seeds load data, render 12 images and write
a temporary manifest before raising ValueError. No real dataset was accessed.

Prepared a byte-identical temporary working copy and initial manifest of 30
project/instruction files from a clean original repository. Independently authored
60 synthetic acceptance cases and copied the 112 existing regression cases outside
the agent's writable workspace. Baseline: 160 passed, 12 failed, no errors/skips;
all failures are the selected seed defects. Required JUnit identities are declared
in the existing Task ledger. The existing pre-execution predictor selected zero
labels for this new real target and returned Beta(1,1): probability 0.5, 95%
credible interval [0.025, 0.975]. Prior CSV acceptance is not pooled.

Requested configuration: OpenAI gpt-6.1-sol / low reasoning, existing Codex CLI
0.162.0-alpha.17.2 and ChatGPT authentication. Effective native settings and model
version remain unknown until emitted. The existing metadata-only capture pipeline
is prepared with one-off operator supervision, a 600-second safety stop and no
automatic second invocation. Local no-model sandbox canaries confirm working-copy
writes allowed, protected/original/environment/neighbor writes denied and tool
network denied. Web/apps/plugins/hooks/additional agents are disabled.

The strict agent sandbox produces an OpenMP temporary-registration warning that
affects three existing empty-stderr import checks. This is disclosed in the prompt;
source/test changes or warning suppression to hide it are prohibited. The separate
trusted verification sandbox permits standard temporary files while keeping the
final snapshot and frozen tests read-only. Its preflight reproduces exactly the
same 12 seed failures, with no extra failures and no changed acceptance tests.

Private tests, source snapshots, manifests, declared settings, prediction, command
scripts and receipts remain under ignored local experiment storage. Relevant
Model Learner capture/JUnit checks: **95 passed in 1.43s**; Ruff lint/format clean
(190 files). No ShortcutLens source changes, production infrastructure, semantic
analyzer change, dependency installation, model call, additional agent, commit or
publication occurred. Launch count is zero. Next step is explicit user approval
of this single prepared execution; final verification, outcome, observation and
learner consumption remain unstarted.

## Experiment 2: approved execution, verification and learner consumption

After explicit approval, executed exactly one prepared ephemeral Codex CLI
invocation requesting OpenAI gpt-6.1-sol / low reasoning. The supervisor checked
frozen preparation and starting-file hashes before launch. Agent and metadata
capture both exited 0, with no timeout; operator pipeline wall time was 31.64
seconds. No second invocation or coordinator repair followed independent results.

- The helper now rejects oversized Torch-bound seeds before source/manifest access
  and converts valid Integral scalars to Python integers at the Torch boundary.
  Default behavior, negative-seed policy and large NumPy-only seeds are preserved.
- Froze a canonical final archive and per-file manifest with the agent stopped.
  Independent verification passed all **172 required cases**, no failures, errors
  or skips, with exact JUnit identity agreement. Frozen inputs and final source
  remained unchanged. The 60 independent cases use synthetic verification inputs;
  the coding execution and observation are real, not simulated or benchmark data.
- The final candidate's repository suite, including 17 agent-added cases, passed
  **129 tests**. Ruff passed. Applied only the two verified task files after
  checking their initial hashes. Device work committed after preparation and new
  unrelated training files were preserved. Earlier global clean/head guards
  aborted before writing; scoped transfer and post-apply checks succeeded.
  Retained scoped regressions against the applied code passed **129 tests**;
  unrelated new training tests were not executed as part of this experiment.
- Capture/import stored **18 events**, one session and one completed turn, with
  six observed tool items and no diagnostics. Replay inserted zero events and
  recognized 18 duplicates. Native turn usage emitted 124,382 input tokens,
  including 98,688 cached, and 1,721 output tokens, including 47 reasoning.
  Subsets are not added to parent totals. Model/provider/reasoning/version were
  absent from the stream; configuration remains an operator declaration.
- Existing run/attempt, bound JUnit verifier, outcome assessor and observation
  builder produced **success / verified**, single-configuration attribution,
  eligibility true and no exclusions. Report/artifact digests and actual process
  receipts bind the required checks to the exact final archive. Cost and canonical
  observation latency remain null; operator wall time is not native latency.
- Existing quality/resolution/prediction commands selected one eligible success,
  zero failures and no exclusions. Baseline was Beta(1,1), mean 0.5 and 95%
  interval [0.025, 0.975]; after recording it is Beta(2,1), mean 0.667 and interval
  [0.158, 0.987]. The resolver's deterministic snapshot UUID/cutoff differ from
  the persisted row identity/time; every other field, including stable key, run,
  outcome, evidence, configuration and eligibility, matches. The ledger contains
  only one observation. No cross-target pooling or predictive-accuracy claim.

Private evidence and result report remain in ignored experiment storage. Ledger
audit: one Task, Run, Attempt, Session, Verification, Outcome and Observation;
18 Events. Final relevant capture/JUnit tests **95 passed in 1.41s**; Ruff lint
passed and formatting reports 190 files formatted. No Model Learner production
code, semantic analyzer, dependency, benchmark controller, extra coding agent,
training, commit, push or publication changes. The selected task and experiment
are complete. No additional run or milestone is started or authorized.

## Reviewed synthetic holdout fixture approval — 2026-10-17

Approved only `experiments/local_task_state/holdout_sources.json` in the privacy
fixture allowlist, using the unchanged SHA-256 from its independent AI authorship
review: `45c03da6e66ac39461fcea7cefbb8c91cf28ff30b51915b19ca6c6b531fa7942`.
Full inspection found four simulated conversations / 16 user messages and no
private conversation information. The review documents fresh authoring without
private diagnostic access; it is not human-verified provenance. Fixture bytes
remain unchanged. The guard now permits this exact experiment path in the policy;
other experiment paths remain invalid. Exemptions still require the exact digest
and cover conversation structure only, preserving secret/path/binary checks.

Added index/tree regressions for exact reviewed acceptance and rejection of
modified content, new unapproved conversation content (even when labeled
simulated), identical bytes at an unapproved path, and missing approval. A separate
regression rejects an attempt to approve another experiment path.

Validation: privacy integration and local-task-state unit tests **72 passed in
14.16s**; repository Ruff lint and formatting passed (**190 files formatted**);
`git diff --check` passed. Current `HEAD` privacy check passed (250 files). The
actual index contains the already-staged fixture but the old allowlist, so its
privacy check rejects that fixture as expected until the updated policy is staged.
An isolated proposed index and tree with the scoped changes each passed privacy
checks (**251 files, zero rejections**). Actual index bytes/mtime and reviewed
fixture bytes were preserved. Initial uv checks required approved cache access
outside the workspace. No commit or push was performed in this repository.

This approval is complete. No further milestone or experiment is started; the
next action is the user's review and staging of the scoped approval changes.
