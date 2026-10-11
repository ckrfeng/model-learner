# Real benchmark safety audit and operator boundary

Audit date: 2026-10-10 (America/Chicago). **Real-agent collection remains blocked.**
The current supported harness stages evidence; it does not provide an execution
sandbox. No real or paid coding-agent run was launched in this audit.

The subsequent fixed offline Docker Desktop experiment and its actual validation
scope are documented in [OFFLINE_BENCHMARK_ISOLATION.md](OFFLINE_BENCHMARK_ISOLATION.md).
It is a separate synthetic probe with no host mounts. It does not replace the
agent/credential/acceptance transport requirements below or unlock real runs.
The [benchmark evidence pipeline](BENCHMARK_EVIDENCE.md) supports offline,
source-revalidated exports; prospective checkpoint collection remains blocked.

## What is actually enforced

| Mechanism | Actual protection | Limitation |
| --- | --- | --- |
| Canonical disposable root outside the repository | Harness writes stay outside protected source | An external process still has the host user's access |
| Source/fixture/candidate hashes and trusted control checks | Detect changed inputs before accepting evidence | Cannot prevent or undo a write, protect secrets or prove execution |
| Python `-I`, empty worker environment, five-second worker timeout | Removes Python environment configuration; limits one foreground worker | Filesystem/process access remains shared; descendants and disk writes are not contained |
| Independent controller comparisons | Candidate cannot patch assertions in the controller's interpreter | Candidate workers can access controller files/processes without an OS boundary |
| `--isolation-confirmed` and isolation description | Operator declaration is retained | No OS inspection or attestation |
| New real-origin finalization gate | Refuses unsupported real evidence before creating a run or lock | Does not control externally started agents; preparation is staging only |

There is no Model Learner-enforced macOS filesystem, network, process or
credential containment for agent or submitted candidate execution. The enclosing
Codex development sandbox restricts this development session; it is not a
boundary supplied by the benchmark harness to future operator executions.

An actual controlled integration test ran the existing acceptance controller
against a hand-written `clamp` candidate that read a public synthetic private
canary and overwrote a public synthetic source canary outside its task directory.
All six named acceptance checks passed, and the outside source canary changed.
Only test-created synthetic files were touched. This directly demonstrates that
the current Python `-I` worker can access host files despite correct task answers;
it is not a real-agent performance result or a sandbox escape from a validated
execution boundary.

## Harmless macOS probe and observed result

The fixed `benchmark isolation-probe` diagnostic creates public synthetic
`private-canary.txt` and `source-canary.txt` files in a disposable directory.
Their names stand for protected data; their contents are public. It never reads
actual private files, credentials or source. A separate workspace contains an
allowed file and a symlink to an outside canary. The fixed shell attempts:

1. Read and write inside the allowed workspace (positive bootstrap controls).
2. Read an outside canary and overwrite another outside canary.
3. Read the outside canary through an in-workspace symlink.
4. Read the outside canary from a child shell inheriting the profile.
5. Compare outside canary contents afterwards and delete the disposable tree.

The profile uses deny-default rules, read access to public system runtime
directories, writable workspace only, no network allowance and no arbitrary
program arguments. Execution uses an empty environment and five-second timeout.
This is a fixed harmless diagnostic, not a general untrusted-code runner.
Bootstrap failure leaves denied-operation results null: the forbidden attempts
have not been demonstrated to execute. `probe_passed` would establish only these
canary checks for this profile; `real_execution_ready` is always false.

Actual local results on macOS 26.6.2 arm64:

| Invocation | Actual result |
| --- | --- |
| Deny-default canary probe inside the enclosing development sandbox | `unavailable`, `sandbox_bootstrap_unavailable`; no allowed-read/write marker; outside canaries unchanged |
| Same harmless probe with approved outer-sandbox escalation | `unavailable`, `sandbox_bootstrap_unavailable`; no allowed-read/write marker; outside canaries unchanged |
| Elevated `sandbox-exec` permissive-profile `/usr/bin/true` bootstrap diagnostic | Exit 0; proves the system accepts a sandbox profile, not that containment is effective |
| Fixed deny-default public shell `printf` startup diagnostics | Exit 134 before output, including limited runtime/metadata/service-lookup variants; no containment claim |

Thus the machine has `sandbox-exec`, but this restrictive shell profile is
unvalidated here. Its failure is not evidence that all macOS sandboxing or VMs
are unavailable. An unchanged canary after failed startup is not a passing escape
test. The system-supplied `/usr/share/man/man1/sandbox-exec.1` marks the CLI
deprecated and recommends App Sandbox. Apple's supported
[App Sandbox documentation](https://developer.apple.com/documentation/security/app-sandbox)
describes application entitlements, rather than attesting an arbitrary coding
agent from a working-directory setting. A production profile would require a
separate runtime/privacy audit; we do not broaden it until the agent starts.

## Smallest practical proposed boundary

Use a fresh, offline-installed Linux VM image for each task/configuration run,
with a new disposable task disk. Copy only public task instructions and initial
solution bytes into it. Configure **no host filesystem shares**, clipboard,
personal home/configuration imports, host socket mounts, SSH agent forwarding or
host process access. Do not mount Model Learner source, Git, `control`, capture
files, verifier, private home directories or provider tokens. Apple exposes host
files to a guest through explicit
[shared directory devices](https://developer.apple.com/documentation/virtualization/shared-directories);
omitting these devices is part of the required configuration. This recommendation
is a proposed operator boundary; no VM configuration was executed or validated
in this delivery.

Agent orchestration must keep all provider credentials on the operator host.
A bounded operator-side relay may forward only authorized provider requests;
agent tools and candidate code cannot inspect token material, credential files,
keychains or inherited credential environment variables. Restrict network access
to that relay, deny host/LAN/metadata services, and enforce the operator's spend
cap there. A provider CLI requiring a readable token inside the guest does not
satisfy this requirement. There is currently no supported relay/VM transport in
Model Learner, so this remains an execution blocker, not an instruction to put
an API key in a clean VM.

After stopping and destroying the agent VM, extract only bounded regular
`solution.py` bytes through an operator-owned export. Reject symlinks, device
files, oversized inputs and archive traversal. Freeze the candidate on the host.
For acceptance, boot a fresh **different**, credential-free VM containing only
the candidate and public Python runtime. The trusted controller stays outside
the candidate VM and sends one primitive function request at a time; expected
answers and report/manifest paths are never accessible there. It compares bounded
responses and writes JUnit itself. Disable verification network access and keep
candidate descendants contained until the entire VM is destroyed.

The current controller starts local Python workers and does not implement this
candidate-only transport. Running it with candidate and report in one VM still
permits same-VM interference and does not meet the independent-verifier boundary.
Replacing just `cwd`, adding `-I`, or mounting control read-only while sharing
controller process privileges is insufficient.

## Required limits and preflight for a real experiment

These are proposed upper bounds, aligned with the pilot, not currently enforced
limits for real executions:

| Resource | Agent run | Acceptance run |
| --- | --- | --- |
| Wall-clock deadline | 120 seconds | 60 seconds total; 5 seconds per request |
| VM vCPU/RAM | 2 vCPU / 2 GiB RAM | 1 vCPU / 512 MiB RAM |
| Guest writable capacity | 512 MiB task disk; fixed read-only base | 64 MiB temporary disk; read-only candidate/base |
| Processes | 64 guest task processes, no privilege escalation | 16 candidate processes, no privilege escalation |
| Export/output | 1 MiB candidate; capped 1 MiB metadata capture | 4096 bytes per response; 1 MiB report |
| Network | Only bounded provider relay | None |
| Credentials | No guest-readable credentials | None |
| Monetary budget | Explicit operator-approved per-run and total relay cap | No paid API calls |

The host watchdog must power off the whole VM on deadline/overflow; killing only
the foreground CLI is insufficient. Guest process/disk limits require actual
cgroup/quota or equivalent enforcement, not a promise from the agent. Record the
actual mechanisms and effective values. Paid execution requires a separate
explicit operator authorization; preparation, tests and probe never provide it.

Before any real task, the operator must create **public** source/private/control
canaries on the host and attempt reads/writes from the exact agent tool boundary
and exact acceptance candidate boundary. Include absolute paths, `..`, symlinks,
child processes, host sockets, and private environment variable names populated
only with synthetic values. Show permitted workspace operations also succeed.
Use only synthetic data; never probe a real secret. Verify host canaries unchanged,
absence of host mounts/shared devices, credential separation, blocked network,
enforced disk/process bounds and watchdog destruction of all descendants.
Retain policy/image/configuration fingerprints, runtime versions, operator times,
fixed probe outcomes and limit receipts outside Git. Any unavailable positive
control, missing receipt or successful forbidden operation blocks the run.

## Readiness and remaining blockers

Ready: deterministic disposable staging, source/fixture checks, frozen candidate
hashes, controlled-fixture independent comparisons, metadata-only ingestion,
harmless probe reporting and fail-closed real finalization. The pilot can specify
tasks/configurations and prospective collection without launching them.

Blocked: a verified agent VM/credential relay, a separate candidate-only acceptance
transport, actual resource/network/process-limit enforcement, passing exact-runtime
canary/descendant tests, and binding their receipts to the real run. A manual VM
declaration or a passing shell probe cannot unlock finalization. Supporting that
backend and its receipt validation requires separately scoped implementation;
do not disable the gate or relabel real executions as fixtures to proceed.
