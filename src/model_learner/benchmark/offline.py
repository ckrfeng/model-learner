"""Fixed, harmless Docker Desktop experiment. Never an agent launch backend.

No host mounts are permitted. A local immutable image is required and never pulled.
Success covers the reported synthetic probes only, and cannot unlock real runs.
"""

import hashlib
import io
import json
import os
import platform
import re
import selectors
import shutil
import subprocess
import tarfile
import tempfile
import time
from pathlib import Path
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, ConfigDict, Field

from model_learner.domain.models import utc_now

VERSION = "docker-offline-probe/v1"
MEMORY_BYTES = 128 * 1024 * 1024
WORKSPACE_BYTES = 1024 * 1024
PIDS = 16
WALL_SECONDS = 15
MAX_OUTPUT_BYTES = 64 * 1024
MAX_ARTIFACT_BYTES = 1024
ARTIFACT = b"public synthetic artifact\n"
SUPPORTED_SYNTHETIC_IMAGE = (
    "sha256:c4d56c24da4f009ecf8352146b43497fe78953edb4c679b841732beb97e588b0"
)
_IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")


class OfflineIsolationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal["docker-offline-probe/v1"] = VERSION
    status: Literal["validated", "unavailable", "failed"]
    reason: str
    observed_at: str = Field(default_factory=lambda: utc_now().isoformat())
    platform: str = Field(default_factory=platform.platform)
    runtime_version: str | None = None
    image_id: str | None = None
    policy_sha256: str | None = None
    checks: dict[str, bool] = Field(default_factory=dict)
    artifact_sha256: str | None = None
    artifact_extraction: (
        Literal["controller_tar_stream_after_fixed_worker_ready"] | None
    ) = None
    host_mounts: tuple[str, ...] = ()
    limits: dict[str, int] = Field(
        default_factory=lambda: {
            "cpu_millicores": 1000,
            "memory_bytes": MEMORY_BYTES,
            "pids": PIDS,
            "workspace_bytes": WORKSPACE_BYTES,
            "wall_seconds": WALL_SECONDS,
            "output_bytes": MAX_OUTPUT_BYTES,
            "artifact_bytes": MAX_ARTIFACT_BYTES,
        }
    )
    real_execution_ready: Literal[False] = False


class _ProbeError(Exception):
    pass


def _bounded(command: list[str], *, deadline: float, env: dict[str, str]) -> bytes:
    """Drain stdout incrementally with a hard byte cap and watchdog, discard stderr.

    A killed Docker client does not kill a container; the caller always removes
    the named container in its finally clause, including on command failures.
    """
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise _ProbeError("wall_deadline_exceeded")
    process = subprocess.Popen(
        command,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        env=env,
    )
    output = bytearray()
    try:
        assert process.stdout is not None
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise _ProbeError("wall_deadline_exceeded")
                for key, _ in selector.select(min(remaining, 0.2)):
                    part = os.read(key.fd, 4096)
                    if not part:
                        selector.unregister(key.fileobj)
                        continue
                    output.extend(part)
                    if len(output) > MAX_OUTPUT_BYTES:
                        raise _ProbeError("output_limit_exceeded")
        code = process.wait(timeout=max(0.01, deadline - time.monotonic()))
        if code:
            raise _ProbeError("runtime_command_failed")
        return bytes(output)
    except subprocess.TimeoutExpired as exc:
        raise _ProbeError("wall_deadline_exceeded") from exc
    finally:
        if process.poll() is None:
            process.kill()
        process.wait(timeout=2)
        if process.stdout is not None:
            process.stdout.close()


def _extract_artifact(data: bytes) -> bytes:
    """Validate Docker's tar transport without writing paths or following links."""
    if len(data) > MAX_OUTPUT_BYTES:
        raise _ProbeError("artifact_transport_oversized")
    try:
        with tarfile.open(fileobj=io.BytesIO(data), mode="r:") as archive:
            members = archive.getmembers()
            if len(members) != 1:
                raise _ProbeError("artifact_member_count")
            member = members[0]
            if (
                member.name != "solution.py"
                or not member.isreg()
                or member.size > MAX_ARTIFACT_BYTES
                or member.size < 0
                or member.linkname
            ):
                raise _ProbeError("artifact_not_bounded_regular_file")
            stream = archive.extractfile(member)
            if stream is None:
                raise _ProbeError("artifact_missing")
            result = stream.read(MAX_ARTIFACT_BYTES + 1)
            if len(result) != member.size:
                raise _ProbeError("artifact_size_mismatch")
            return result
    except (tarfile.TarError, OSError) as exc:
        raise _ProbeError("artifact_transport_invalid") from exc


def _create_arguments(name: str, image: str, script: str) -> list[str]:
    return [
        "create",
        "--pull",
        "never",
        "--name",
        name,
        "--network",
        "none",
        "--read-only",
        "--cap-drop",
        "ALL",
        "--security-opt",
        "no-new-privileges",
        "--user",
        "65534:65534",
        "--cpus",
        "1",
        "--memory",
        str(MEMORY_BYTES),
        "--memory-swap",
        str(MEMORY_BYTES),
        "--pids-limit",
        str(PIDS),
        "--ipc",
        "none",
        "--cgroupns",
        "private",
        "--ulimit",
        "nofile=64:64",
        "--tmpfs",
        f"/workspace:rw,nosuid,nodev,noexec,size={WORKSPACE_BYTES},mode=1777",
        "--shm-size",
        "1m",
        "--workdir",
        "/workspace",
        "--log-driver",
        "local",
        "--log-opt",
        "max-size=64k",
        "--log-opt",
        "max-file=1",
        "--log-opt",
        "compress=false",
        "--entrypoint",
        "/bin/sh",
        image,
        "-c",
        script,
    ]


def _policy_matches(value: dict, image: str) -> bool:
    host, config = value["HostConfig"], value["Config"]
    return all(
        [
            value["Image"] == image,
            host["NetworkMode"] == "none",
            host["ReadonlyRootfs"] is True,
            host["Privileged"] is False,
            host["NanoCpus"] == 1_000_000_000,
            host["Memory"] == MEMORY_BYTES,
            host["MemorySwap"] == MEMORY_BYTES,
            host["PidsLimit"] == PIDS,
            host["IpcMode"] == "none",
            host["CgroupnsMode"] == "private",
            host["PidMode"] == "",
            host["CapDrop"] == ["ALL"],
            "no-new-privileges" in host["SecurityOpt"],
            not host.get("Binds"),
            not host.get("Devices"),
            not host.get("DeviceRequests"),
            not host.get("VolumesFrom"),
            config["User"] == "65534:65534",
            config["Entrypoint"] == ["/bin/sh"],
            host["Tmpfs"]
            == {
                "/workspace": f"rw,nosuid,nodev,noexec,size={WORKSPACE_BYTES},mode=1777"
            },
            not value["Mounts"],
            not config.get("Volumes"),
            host["LogConfig"]
            == {
                "Type": "local",
                "Config": {"max-size": "64k", "max-file": "1", "compress": "false"},
            },
        ]
    )


def _script(outside: Path) -> str:
    # Generated paths contain only tempfile/uuid names and are never user input.
    path = str(outside)
    if not re.fullmatch(r"/[A-Za-z0-9_./-]+", path):
        raise _ProbeError("synthetic_path_invalid")
    return f"""set -eu
mark() {{ printf '%s\n' "$1"; }}
printf 'public\n' > /workspace/allowed.txt
IFS= read -r value < /workspace/allowed.txt
[ "$value" = public ] && mark workspace_read_write
printf 'public synthetic artifact\n' > /workspace/solution.py
for name in repository hidden-test credentials source runtime.sock; do
  if (IFS= read -r value < '{path}/'$name) 2>/dev/null; then exit 21; fi
  mark "$name"_read_denied
  if (printf 'changed\n' > '{path}/'$name) 2>/dev/null; then exit 22; fi
  mark "$name"_write_denied
done
ln -s '{path}/source' /workspace/outside-link
if (IFS= read -r value < /workspace/outside-link) 2>/dev/null; then exit 23; fi
mark symlink_denied
if (IFS= read -r value < '/workspace/../{path.lstrip("/")}/source') 2>/dev/null; then
  exit 24
fi
mark traversal_denied
if /bin/sh -c 'IFS= read -r value < "$1"' child '{path}/source' 2>/dev/null; then
  exit 25
fi
mark descendant_read_denied
if (printf 'changed\n' > /outside-write) 2>/dev/null; then exit 26; fi
mark root_write_denied
[ -z "${{MODEL_LEARNER_SYNTHETIC_SECRET+x}}" ] && mark credential_environment_absent
[ ! -e /var/run/docker.sock ] && [ ! -e /run/containerd/containerd.sock ] &&
[ ! -e /run/podman/podman.sock ] && mark runtime_socket_absent
[ ! -e /Users ] && [ ! -e /host ] && [ ! -e /run/host ] && mark host_shares_absent
[ "$(cat /sys/fs/cgroup/memory.max)" = '{MEMORY_BYTES}' ] && mark memory_limit_effective
[ "$(cat /sys/fs/cgroup/pids.max)" = '{PIDS}' ] && mark pids_limit_effective
[ "$(cat /sys/fs/cgroup/cpu.max)" = '100000 100000' ] && mark cpu_limit_effective
# Bounded fork pressure: on failure the subshell's trap kills its own children.
set +e
(
  children=''
  trap 'kill $children 2>/dev/null || :' EXIT
  i=0
  while [ "$i" -lt 32 ]; do
    sleep 30 &
    children="$children $!"
    i=$((i+1))
  done
) 2>/workspace/pids.err
set -e
while IFS= read -r line; do
  case "$line" in
    *"Resource temporarily unavailable"*|*"can't fork"*) mark pids_cap_enforced; break;;
  esac
done < /workspace/pids.err
# Loopback proves the tool can connect before testing forbidden destinations.
printf 'public-loopback\n' | nc -l -p 8123 -s 127.0.0.1 -w 2 &
listener=$!
sleep 0.1
nc -w 2 127.0.0.1 8123 > /workspace/network.txt
wait "$listener"
IFS= read -r value < /workspace/network.txt
[ "$value" = public-loopback ] && mark network_positive_control
# The same zero-I/O mode must succeed, so unsupported flags cannot fake denial.
nc -l -p 8124 -s 127.0.0.1 -w 2 >/dev/null &
listener=$!
sleep 0.1
nc -w 1 -z 127.0.0.1 8124 && mark network_probe_mode_positive_control
wait "$listener"
for address in 192.0.2.1 192.168.65.1 169.254.169.254; do
  if nc -w 1 -z "$address" 80 2>/dev/null; then exit 27; fi
done
mark external_host_metadata_network_denied
# The task tmpfs has an actual storage cap. This intentionally fills it.
if dd if=/dev/zero of=/workspace/fill bs=1048576 count=2 2>/dev/null; then exit 28; fi
mark workspace_size_enforced
rm /workspace/fill
mark probe_ready
# Leave a descendant alive so host destruction must remove the whole boundary.
sleep 120 &
wait
"""


_REQUIRED = {
    "workspace_read_write",
    "symlink_denied",
    "traversal_denied",
    "descendant_read_denied",
    "root_write_denied",
    "credential_environment_absent",
    "runtime_socket_absent",
    "host_shares_absent",
    "memory_limit_effective",
    "pids_limit_effective",
    "pids_cap_enforced",
    "cpu_limit_effective",
    "network_positive_control",
    "network_probe_mode_positive_control",
    "external_host_metadata_network_denied",
    "workspace_size_enforced",
    "probe_ready",
} | {
    f"{name}_{operation}_denied"
    for name in ("repository", "hidden-test", "credentials", "source", "runtime.sock")
    for operation in ("read", "write")
}


def probe_offline_isolation(image_id: str | None = None) -> OfflineIsolationResult:
    """Test a fixed synthetic task on an existing local Docker Desktop daemon.

    Never starts/installs a daemon, pulls an image, mounts host files, accepts an
    arbitrary task/program, or modifies the unconditional real-execution gate.
    """
    if image_id is None:
        return OfflineIsolationResult(
            status="unavailable", reason="image_approval_required"
        )
    if not _IMAGE_ID.fullmatch(image_id):
        raise ValueError("image must be an immutable local sha256 image ID")
    if image_id != SUPPORTED_SYNTHETIC_IMAGE:
        return OfflineIsolationResult(
            status="unavailable",
            reason="unsupported_synthetic_image",
            image_id=image_id,
        )
    docker = shutil.which("docker")
    if platform.system() != "Darwin" or docker is None:
        return OfflineIsolationResult(
            status="unavailable", reason="docker_desktop_missing"
        )
    # A single local Desktop socket only. Ambient remote Docker contexts/env,
    # user CLI proxies, credentials, and plugins are deliberately not imported.
    endpoint = Path.home() / ".docker/run/docker.sock"
    if not endpoint.is_socket():
        return OfflineIsolationResult(
            status="unavailable", reason="docker_desktop_socket_missing"
        )
    name = "model-learner-offline-" + uuid4().hex
    checks: dict[str, bool] = {}
    runtime = None
    artifact_hash = None
    policy_hash = None
    status: Literal["validated", "unavailable", "failed"] = "unavailable"
    reason = "runtime_unavailable"
    created = False
    with tempfile.TemporaryDirectory(
        prefix="model-learner-offline-", dir="/private/tmp"
    ) as temp:
        root = Path(temp)
        config, outside = root / "client", root / "outside"
        config.mkdir()
        outside.mkdir()
        (config / "config.json").write_text("{}\n")
        canaries = [
            outside / value
            for value in (
                "repository",
                "hidden-test",
                "credentials",
                "source",
                "runtime.sock",
            )
        ]
        for path in canaries:
            path.write_bytes(b"public synthetic canary\n")
        command = [docker, "--config", str(config), "--host", "unix://" + str(endpoint)]
        env = {"PATH": "/usr/local/bin:/usr/bin:/bin", "HOME": str(config)}
        deadline = time.monotonic() + WALL_SECONDS

        def invoke(args: list[str], *, until: float | None = None) -> bytes:
            try:
                return _bounded(command + args, deadline=until or deadline, env=env)
            except _ProbeError as exc:
                if str(exc) == "runtime_command_failed":
                    raise _ProbeError(f"runtime_{args[0]}_failed") from exc
                raise

        try:
            server = json.loads(invoke(["version", "--format", "{{json .Server}} "]))
            if (
                not server
                or server.get("Os") != "linux"
                or not server.get("Platform", {})
                .get("Name", "")
                .startswith("Docker Desktop")
            ):
                raise _ProbeError("local_linux_desktop_required")
            runtime = server["Version"]
            ids = [image_id]
            selected = None
            for candidate in dict.fromkeys(ids):
                if not candidate or not _IMAGE_ID.fullmatch(candidate):
                    continue
                image = json.loads(invoke(["image", "inspect", candidate]))[0]
                image_config = image["Config"]
                safe_env = all(
                    entry.split("=", 1)[0]
                    in {
                        "PATH",
                        "HOME",
                        "LANG",
                        "LC_ALL",
                        "NGINX_VERSION",
                        "PKG_RELEASE",
                        "DYNPKG_RELEASE",
                    }
                    for entry in image_config.get("Env") or []
                )
                if not image_config.get("Volumes") and safe_env:
                    selected = candidate
                    break
            if selected is None:
                raise _ProbeError("no_approved_local_volume_free_image")
            image_id = selected
            args = _create_arguments(name, selected, _script(outside))
            policy_args = _create_arguments(
                "<disposable-task>", selected, _script(Path("/synthetic-outside"))
            )
            policy_hash = hashlib.sha256(
                json.dumps(policy_args, separators=(",", ":")).encode()
            ).hexdigest()
            # A create failure can occur after daemon allocation: cleanup by our
            # unique generated name even when the client has not returned an ID.
            created = True
            invoke(args)
            inspected = json.loads(invoke(["inspect", name]))[0]
            if not _policy_matches(inspected, selected):
                raise _ProbeError("effective_policy_mismatch")
            checks["runtime_policy_inspected"] = True
            invoke(["start", name])
            status = "failed"
            while time.monotonic() < deadline:
                markers = set(
                    invoke(["logs", "--tail", "40", name])
                    .decode("ascii", errors="replace")
                    .splitlines()
                )
                if "probe_ready" in markers:
                    checks.update({key: key in markers for key in sorted(_REQUIRED)})
                    break
                state = json.loads(
                    invoke(["inspect", "--format", "{{json .State}}", name])
                )
                if not state["Running"]:
                    raise _ProbeError("probe_bootstrap_or_check_failed")
                time.sleep(0.05)
            else:
                raise _ProbeError("wall_deadline_exceeded")
            if not all(checks.values()):
                raise _ProbeError("required_probe_marker_missing")
            # Docker cp cannot see this runtime's tmpfs mounts. The fixed worker
            # has completed all writes at probe_ready and only sleeps afterwards.
            # An independent controller-selected tar process sends regular bytes
            # to the host parser. This is NOT a hostile-worker freezing transport.
            data = _extract_artifact(
                invoke(
                    [
                        "exec",
                        "--user",
                        "65534:65534",
                        "--workdir",
                        "/workspace",
                        name,
                        "/bin/tar",
                        "-cf",
                        "-",
                        "solution.py",
                    ]
                )
            )
            invoke(["pause", name])
            checks["independent_artifact_extraction"] = data == ARTIFACT
            artifact_hash = hashlib.sha256(data).hexdigest()
            # Force removal must kill the sleeping descendant as well as PID 1.
            invoke(["rm", "--force", name])
            created = False
            remaining = invoke(
                ["ps", "--all", "--quiet", "--filter", "name=^/" + name + "$"]
            )
            checks["whole_boundary_destroyed"] = not remaining.strip()
            checks["host_canaries_unchanged"] = all(
                path.read_bytes() == b"public synthetic canary\n" for path in canaries
            )
            # A separate fresh boundary deliberately reaches the watchdog while
            # its PID 1 and sleeping descendant remain alive. Killing the client
            # alone is insufficient; force removal is independently confirmed.
            created = True
            invoke(_create_arguments(name, selected, "sleep 120 & wait"))
            invoke(["start", name])
            state = json.loads(invoke(["inspect", "--format", "{{json .State}}", name]))
            if not state["Running"]:
                raise _ProbeError("watchdog_bootstrap_failed")
            try:
                invoke(["wait", name], until=min(deadline, time.monotonic() + 1))
            except _ProbeError as exc:
                if str(exc) != "wall_deadline_exceeded":
                    raise
                checks["watchdog_deadline_enforced"] = True
            else:
                raise _ProbeError("watchdog_not_exercised")
            invoke(["rm", "--force", name])
            created = False
            checks["watchdog_descendants_destroyed"] = not invoke(
                ["ps", "--all", "--quiet", "--filter", "name=^/" + name + "$"]
            ).strip()
            status = "validated" if all(checks.values()) else "failed"
            reason = (
                "fixed_offline_probes_passed"
                if status == "validated"
                else "synthetic_check_failed"
            )
        except (OSError, ValueError, KeyError, IndexError, _ProbeError) as exc:
            reason = (
                str(exc)
                if isinstance(exc, _ProbeError)
                else "runtime_receipt_unavailable"
            )
        finally:
            if created:
                try:
                    invoke(["rm", "--force", name], until=time.monotonic() + 5)
                    checks["whole_boundary_destroyed"] = not invoke(
                        ["ps", "--all", "--quiet", "--filter", "name=^/" + name + "$"],
                        until=time.monotonic() + 5,
                    ).strip()
                except (OSError, _ProbeError):
                    checks["whole_boundary_destroyed"] = False
                    status, reason = "failed", "cleanup_unconfirmed"
    return OfflineIsolationResult(
        status=status,
        reason=reason,
        runtime_version=runtime,
        image_id=image_id,
        policy_sha256=policy_hash,
        checks=checks,
        artifact_sha256=artifact_hash,
        artifact_extraction=(
            "controller_tar_stream_after_fixed_worker_ready" if artifact_hash else None
        ),
    )
