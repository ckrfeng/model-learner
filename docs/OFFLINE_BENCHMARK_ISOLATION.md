# Offline synthetic worker isolation experiment

This is a fixed harmless containment experiment, not an agent executor or an
independent acceptance backend. Real benchmark collection remains blocked by
`require_supported_real_containment()`. A passing receipt always retains
`real_execution_ready=false`. No paid agents, provider calls, package downloads,
system installation, daemon startup, or global security changes are involved.

The experiment uses an already installed Docker Desktop Linux VM on macOS.
Docker documents the [Mac VM boundary](https://docs.docker.com/desktop/setup/install/mac-permission-requirements/),
[container isolation and run controls](https://docs.docker.com/engine/containers/run/),
and [resource controls](https://docs.docker.com/engine/containers/resource_constraints/).
These documents describe mechanisms; actual local probes establish the limited
results below. Docker containers share the Desktop VM kernel. This experiment
does not certify a disposable whole VM or demonstrate resilience to kernel bugs.

## Approved runtime and policy

`probe_offline_isolation(image_id=...)` and `benchmark offline-isolation-probe
--image-id ...` require an explicit immutable locally cached image ID. There is no
automatic image selection and no pull. This version supports only the inspected
public `docker/welcome-to-docker` image:

```
sha256:c4d56c24da4f009ecf8352146b43497fe78953edb4c679b841732beb97e588b0
```

Actual local image inspection showed its public repository tag and identical
repository digest, no declared volumes, and only PATH/NGINX_VERSION/PKG_RELEASE/
DYNPKG_RELEASE environment keys. This pins the exact synthetic shell baseline;
it is not a signature or supply-chain attestation and is not an approved agent
image. Arbitrary local images, tags, caller programs, mounts and arguments are
unsupported. No image environment containing credential variable names is
accepted. The image's default service entrypoint is replaced by a fixed shell.

The host controller uses only the local Docker Desktop Unix socket, a fresh empty
Docker client configuration, and a minimal controller environment. Ambient Docker
contexts, proxy settings, user configuration and credential environment are not
inherited. The runtime socket is available only to the trusted host controller.

Every task has a new randomly named container, read-only image root, unprivileged
UID/GID 65534, all capabilities dropped, no-new-privileges, private PID/network/
cgroup boundary and IPC disabled. No bind mounts, volumes, host home, Model Learner
repository, hidden verifier, host device or runtime socket mounts are allowed.
The controller checks the actual Docker inspect policy before starting.

| Resource | Enforced configuration / measurement |
| --- | --- |
| Network | `none`; exact connection-mode loopback positive test; external/host/metadata attempts denied |
| CPU | 1 CPU CFS quota; effective cgroup `cpu.max` readback |
| Memory | 128 MiB hard memory and total memory+swap cap; effective `memory.max` readback |
| Processes | 16; effective `pids.max` readback and actual bounded fork refusal |
| Task storage | New 1 MiB `nosuid,nodev,noexec` tmpfs; actual allocation overflow refused |
| Wall time | 15-second enclosing command deadline; deliberate one-second watchdog test on a second fresh boundary |
| Host extraction | 64 KiB transport cap; one regular artifact no larger than 1 KiB |
| Logs | One 64 KiB local-driver log, compression disabled; each controller response capped at 64 KiB |
| Open descriptors | 64 soft/hard per process |

CPU and memory values are actual kernel cgroup settings, not load/stress tests.
The task tmpfs limit covers `/workspace`; standard container runtime pseudo-files
remain present and the container memory cap applies to other anonymous/tmpfs
memory. A watchdog kills its Docker client, then force-removes the whole named
container; the latter is mandatory to destroy descendants. On failures, cleanup
gets up to two additional five-second control operations. This cleanup grace can
extend the overall diagnostic beyond 15 seconds; it is not additional authorized
task execution. Cleanup failure returns `failed/cleanup_unconfirmed` and never
certifies isolation. The host daemon is a trusted part of this experimental
boundary; a hung/unreachable daemon leaves destruction unconfirmed.

## Harmless probes and independent extraction

Host-side test-created public files stand for repository source, hidden tests,
credentials, an outside mutable file and a runtime control file. None is mounted.
The fixed worker proves allowed workspace reads/writes, attempts outside absolute
reads/writes, symlink reads, path traversal and descendant reads, checks absent
host-share/runtime-socket paths and synthetic credential environment, and attempts
forbidden external/host/metadata connections. It uses the same `nc -z` mode for
an independent loopback positive test, so rejected command flags cannot appear as
successful network isolation. No real credentials or private files are probed.
The host independently compares the public canaries afterwards.

A fixed readiness marker means the fixed shell has finished all task writes and
only a sleeping descendant remains. The host independently invokes the pinned
image's tar utility to stream just `solution.py`, validates the archive in memory,
rejects extra members, traversal, absolute paths, symlinks, hard links, devices,
FIFOs and oversized data, and compares the extracted bytes to the fixed public
artifact. No archive is extracted to the host filesystem. It then pauses and
force-removes the container and checks that the named boundary is absent.

This quiescent fixed-worker extraction is sufficient for this synthetic
experiment. It is **not** an adversarial freeze-before-read transport. Docker
`cp` from this runtime's paused container could not see its tmpfs artifact and
returned “Could not find the file”; that approach was tested and rejected. A
hostile worker could mutate an artifact during running-container streaming.
Supporting real agents or submitted candidate execution still needs a separate
immutable artifact/freezing transport and an independent verifier outside the
candidate boundary. This experiment does not execute candidate functions or
hidden acceptance tests.

## Actual results

The authorized synthetic experiment ran on macOS 26.6.2 arm64 with Docker Desktop
4.94.0 (241994), Engine 29.8.2, Linux kernel 7.0.14-linuxkit, cgroup v2, and the
pinned image above. The ordinary enclosing development sandbox could not access
the Desktop Unix socket. A scoped approved outer-sandbox execution of the fixed
harmless probe reached the actual Docker enforcement boundary; no worker access
policy was broadened.

The complete probe returned `validated/fixed_offline_probes_passed`, all 33 checks
true, zero host mounts, actual process/storage refusal, independent fixed-artifact
streaming, unchanged host canaries, and actual watchdog-triggered removal of a
second container with a live sleeping descendant. The stable policy fingerprint
was `2fb1b75be291c30610dc7b50e6ef92e1c9c8a17d473dc686fd5064fb68b73061`;
the artifact SHA-256 was
`b91b66771b6ab7ce8f906c171c351e0f729ec21205db88ed835be3d56e47b048`.
These are containment experiment results, not model-performance observations.
Machine-readable receipts use aware UTC observation times; the initial complete
pass was 2026-10-11T05:55:06Z (2026-10-11 00:55:06 America/Chicago).

Unit tests mock the runtime for protocol/error coverage; they do not attest
containment. The actual integration test is opt-in and fails if any required
probe or cleanup fails:

```sh
MODEL_LEARNER_OFFLINE_DOCKER_TEST=1 uv run pytest tests/integration/test_benchmark_offline.py
```

Do not rerun outside an enclosing sandbox merely to run an agent. Only the fixed
harmless experiment is authorized here. A missing runtime, unapproved/missing
image, bootstrap failure, missing marker, policy mismatch, overflow, unavailable
transport, deadline or unconfirmed cleanup fails closed with an explicit reason.
No result changes the real-finalization gate.

Remaining real-execution blockers: no agent credential relay, no reviewed general
agent image/transport, no adversarial artifact freeze/extraction, no separate
candidate-only acceptance transport, and no run-bound backend attestation. This
work stops after the offline experiment; production orchestration is outside
scope.
