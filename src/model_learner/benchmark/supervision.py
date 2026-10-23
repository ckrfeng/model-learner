"""Finite synthetic-only Colima control; not an agent backend or learning signal.

An independent temporary per-user launchd job watches controller exit/deadline.
Only this module's two fixed workers, pinned image and dedicated socket are used.
No credentials, model transport, canonical records or arbitrary commands enter it.
"""

from __future__ import annotations

import argparse
import ast
import base64
import hashlib
import importlib.metadata
import importlib.util
import json
import os
import plistlib
import re
import select
import selectors
import stat
import subprocess
import sys
import time
from contextlib import closing
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator

from model_learner.benchmark.offline import _bounded, _create_arguments, _policy_matches
from model_learner.domain.models import AcceptanceSpec, ExecutionConfiguration, utc_now

VERSION = "synthetic-container-control/v1"
IMAGE = "sha256:24bb3511a0db7b5114a4aee033c65a8a4148f39b7b80a398e548546db967a36f"
INPUT = b"public synthetic supervisor input v1\n"
OUTPUT = b"public synthetic supervisor output v1\n"
OWNER_LABEL = "local.model-learner.synthetic-owner"
TARGET = AcceptanceSpec(identifier="synthetic-supervised-data", version="1")
CONFIG = ExecutionConfiguration(harness="synthetic-colima-control", harness_version="1")
MAX_STATE = 64 * 1024
MAX_HANDOFF = 1024

# Base Python starts without site initialization. Only these verified copies are
# added to its standard-library search path; editable installs/.pth never run.
BOOTSTRAP = b"""import hashlib, json, os, pathlib, runpy, stat, sys
sys._model_learner_stage = "manifest"
diagnostic_directory = pathlib.Path(sys.argv[-1])
def report(outcome, kind):
    try:
        info = diagnostic_directory.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid():
            return
        if stat.S_IMODE(info.st_mode) != 0o700:
            return
        stages = {"manifest", "bundle_verify", "helper", "watch_register", "ready"}
        stage = getattr(sys, "_model_learner_stage", "helper")
        stage = stage if stage in stages else "helper"
        types = {"AssertionError", "TypeError", "ValueError", "OSError",
                 "RuntimeError", "PackageNotFoundError", "ValidationError",
                 "ImportError", "ModuleNotFoundError", "PermissionError"}
        kind = kind if kind in types else "OtherError" if kind else None
        data = json.dumps({"stage": stage, "outcome": outcome,
                           "exception_type": kind}).encode() + b"\\n"
        fd = os.open(diagnostic_directory / "helper-diagnostic.json",
                     os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(data[:512])
            stream.flush()
            os.fsync(stream.fileno())
    except Exception:
        pass
sys.excepthook = lambda kind, value, traceback: report("error", kind.__name__)
root = pathlib.Path(__file__).parent
manifest_bytes = (root / "manifest.json").read_bytes()
assert hashlib.sha256(manifest_bytes).hexdigest() == sys.argv[1]
manifest = json.loads(manifest_bytes)
sys._model_learner_stage = "bundle_verify"
for name, expected in manifest["files"].items():
    path = root / name
    assert not path.is_symlink() and path.is_file()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
exe_hash = hashlib.sha256(pathlib.Path(sys.executable).read_bytes()).hexdigest()
assert exe_hash == manifest["interpreter_sha256"]
sys.path.insert(0, str(root / "lib"))
sys._model_learner_bundle = (str(root), sys.argv[1])
sys.argv = sys.argv[2:]
sys._model_learner_stage = "helper"
runpy.run_path(sys.argv[0], run_name="__main__")
report("returned", None)
"""


class HelperRuntime(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)
    interpreter: str
    interpreter_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bundle: str
    manifest_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    bootstrap_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def helper_files():
    """Static project import closure and installed dependency RECORD bytes."""
    root = Path(__file__).resolve().parents[2]
    pending = ["model_learner.benchmark.supervision"]
    sources = {}
    while pending:
        name = pending.pop()
        relative = Path(*name.split("."))
        path = root / relative.with_suffix(".py")
        if not path.is_file():
            path = root / relative / "__init__.py"
        if not path.is_file() or name in sources:
            continue
        if path.is_symlink():
            raise ValueError("symlink project source refused")
        data = path.read_bytes()
        sources[name] = (path.relative_to(root).as_posix(), data)
        parts = name.split(".")
        pending.extend(".".join(parts[:i]) for i in range(1, len(parts)))
        package = name if path.name == "__init__.py" else name.rpartition(".")[0]
        for node in ast.walk(ast.parse(data)):
            if isinstance(node, ast.Import):
                pending.extend(
                    a.name for a in node.names if a.name.startswith("model_learner")
                )
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ""
                if node.level:
                    module = importlib.util.resolve_name(
                        "." * node.level + module, package
                    )
                if module.startswith("model_learner"):
                    pending.append(module)
                    pending.extend(module + "." + a.name for a in node.names)
    files = {"lib/" + name: data for name, data in sources.values()}
    versions = {}
    for name in (
        "pydantic",
        "pydantic-core",
        "annotated-types",
        "typing-extensions",
        "typing-inspection",
    ):
        distribution = importlib.metadata.distribution(name)
        versions[name] = distribution.version
        for item in distribution.files or ():
            if ".dist-info" in str(item) or ".." in item.parts or item.suffix == ".pyc":
                continue
            if item.suffix not in {".py", ".so", ".typed", ".pyi"}:
                continue
            path = Path(distribution.locate_file(item))
            if path.is_symlink() or not item.hash or item.hash.mode != "sha256":
                raise ValueError("unverified installed dependency")
            data = path.read_bytes()
            actual = (
                base64.urlsafe_b64encode(hashlib.sha256(data).digest())
                .decode()
                .rstrip("=")
            )
            if actual != item.hash.value:
                raise ValueError("installed dependency RECORD mismatch")
            key = "lib/" + item.as_posix()
            if key in files:
                raise ValueError("ambiguous packaged source")
            files[key] = data
    return files, versions


def package_helper():
    """Materialize installed code outside Documents; never download or run hooks."""
    interpreter = Path(sys._base_executable).resolve()
    if "Documents" in interpreter.parts or not interpreter.is_file():
        raise ValueError("supported base interpreter required")
    files, versions = helper_files()
    files["bootstrap.py"] = BOOTSTRAP
    interpreter_hash = digest(interpreter.read_bytes())
    manifest = json.dumps(
        {
            "interpreter_sha256": interpreter_hash,
            "versions": versions,
            "files": {name: digest(data) for name, data in sorted(files.items())},
        },
        sort_keys=True,
    ).encode()
    manifest_hash = digest(manifest)
    parent = Path.home() / ".local/share/model-learner/supervision-helper-v1"
    parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    secure_directory(parent)
    bundle = parent / manifest_hash
    if not bundle.exists():
        bundle.mkdir(mode=0o700)
        for name, data in files.items():
            path = bundle / name
            parent_path = bundle
            for component in Path(name).parts[:-1]:
                parent_path = parent_path / component
                parent_path.mkdir(mode=0o700, exist_ok=True)
            durable(path.parent, path.name, data)
        durable(bundle, "manifest.json", manifest)
    secure_directory(bundle)
    if read(bundle, "manifest.json") != manifest:
        raise ValueError("helper manifest mismatch")
    for name, data in files.items():
        path = bundle / name
        secure_directory(path.parent)
        # Dependency binaries can exceed the small lease-state read limit.
        info = path.lstat()
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_nlink != 1
        ):
            raise ValueError("unsafe packaged file")
        if stat.S_IMODE(info.st_mode) != 0o600 or path.read_bytes() != data:
            raise ValueError("helper copy mismatch")
    return HelperRuntime(
        interpreter=str(interpreter),
        interpreter_sha256=interpreter_hash,
        bundle=str(bundle),
        manifest_sha256=manifest_hash,
        bootstrap_sha256=digest(BOOTSTRAP),
    )


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def worker(mode: str) -> str:
    """No caller source or input; the frozen input is data in this fixed worker."""
    if mode not in {"normal", "live"}:
        raise ValueError("unsupported synthetic worker")
    body = (
        "set -eu; printf 'public synthetic supervisor input v1\\n' > /workspace/input; "
        "chmod 444 /workspace/input; "
        "test ! -e /var/run/docker.sock; test ! -e /run/containerd/containerd.sock; "
        "test ! -e /Users/carterfeng/Documents/Code/model-learner; "
        'test -z "$(ip route)"; '
        "if nc -z -w 1 192.0.2.1 80 2>/dev/null; then exit 45; fi; "
        "sha256sum /workspace/input | cut -d ' ' -f1; "
    )
    if mode == "normal":
        return body + "sleep 0.3; printf 'public synthetic supervisor output v1\\n'"
    return body + (
        "setsid sh -c 'trap \"\" TERM; sleep 25; echo forbidden-late-output' & "
        "exec sleep 30"
    )


class Lease(BaseModel):
    """Noncanonical, operator-owned intent; durable before any worker start."""

    model_config = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False, strict=True
    )
    version: Literal["synthetic-container-control/v1"] = VERSION
    source: Literal["synthetic_control_only"] = "synthetic_control_only"
    run_id: UUID
    owner: UUID
    target: AcceptanceSpec = TARGET
    configuration: ExecutionConfiguration = CONFIG
    container_id: str | None = Field(default=None, pattern=r"^[0-9a-f]{64}$")
    worker_mode: Literal["normal", "live"]
    input_sha256: str
    helper_sha256: str
    controller_pid: int = Field(ge=2)
    prepared_at: datetime
    prepared_monotonic_ns: int = Field(ge=1)
    deadline_monotonic_ns: int = Field(ge=1)
    helper_runtime: HelperRuntime | None = None
    purpose: Literal["synthetic_worker", "no_worker_preflight"] = "synthetic_worker"

    @model_validator(mode="after")
    def fixed(self):
        if self.target != TARGET or self.configuration != CONFIG:
            raise ValueError("synthetic target/configuration required")
        if self.input_sha256 != digest(INPUT):
            raise ValueError("frozen input mismatch")
        if not re.fullmatch(r"[0-9a-f]{64}", self.helper_sha256):
            raise ValueError("helper digest required")
        if self.prepared_at.utcoffset() is None:
            raise ValueError("aware wall observation required")
        if not 0 < self.deadline_monotonic_ns - self.prepared_monotonic_ns <= 30e9:
            raise ValueError("finite synthetic deadline required")
        return self

    @property
    def name(self):
        return "ml-control-" + self.owner.hex

    @property
    def label(self):
        return "local.model-learner.control." + self.owner.hex


class Receipt(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, allow_inf_nan=False, strict=True
    )
    version: Literal["synthetic-container-control/v1"] = VERSION
    source: Literal["synthetic_control_only"] = "synthetic_control_only"
    lease_sha256: str
    run_id: UUID
    target: AcceptanceSpec
    configuration: ExecutionConfiguration
    container_id: str | None = Field(pattern=r"^[0-9a-f]{64}$")
    stop_reason: Literal[
        "completed",
        "deadline",
        "controller_exit",
        "recovery",
        "arm_failure",
        "control_error",
    ]
    prepared_at: datetime
    stopped_at: datetime
    prepared_monotonic_ns: int
    stopped_monotonic_ns: int
    input_sha256: str
    input_observed: bool
    output_sha256: str | None
    output_bytes: int | None
    observed_guest_pids: tuple[int, ...]
    container_absent: bool
    descendants_absent: bool
    output_stable_after_stop: bool
    cleanup_confirmed: bool
    errors: tuple[str, ...] = ()
    canonical_attempt_latency: None = None
    model_transport: Literal["absent"] = "absent"


def encode(value: BaseModel) -> bytes:
    exclude = set()
    if isinstance(value, Lease):
        if value.helper_runtime is None:
            exclude.add("helper_runtime")
        if value.purpose == "synthetic_worker":
            exclude.add("purpose")
    return (value.model_dump_json(exclude=exclude) + "\n").encode()


def unique_json(data: bytes):
    def pairs(items):
        value = {}
        for key, item in items:
            if key in value:
                raise ValueError("ambiguous duplicate state key")
            value[key] = item
        return value

    try:
        return json.loads(data, object_pairs_hook=pairs)
    except (RecursionError, UnicodeError) as exc:
        raise ValueError("unsupported state JSON") from exc


def secure_directory(directory: Path) -> Path:
    directory = Path(directory).absolute()
    for part in (*reversed(directory.parents), directory):
        if part.is_symlink():
            raise ValueError("symlink state path refused")
    info = directory.stat()
    if info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700:
        raise ValueError("private operator directory required")
    return directory


def read(directory: Path, name: str) -> bytes:
    directory = secure_directory(directory)
    fd = os.open(directory / name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        info = os.fstat(stream.fileno())
        if (
            not stat.S_ISREG(info.st_mode)
            or info.st_uid != os.getuid()
            or info.st_nlink != 1
            or stat.S_IMODE(info.st_mode) & 0o077
            or info.st_size > MAX_STATE
        ):
            raise ValueError("bounded private state file required")
        data = stream.read(MAX_STATE + 1)
        after = os.fstat(stream.fileno())
        current = (directory / name).lstat()
        for field in ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_mode"):
            if getattr(info, field) != getattr(after, field) or getattr(
                after, field
            ) != getattr(current, field):
                raise ValueError("state changed while reading")
        if len(data) > MAX_STATE:
            raise ValueError("oversized state")
        return data


def durable(directory: Path, name: str, data: bytes, *, replace=False):
    secure_directory(directory)
    target = directory / (name + ".pending" if replace else name)
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    if replace:
        os.replace(target, directory / name)
    fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def load(directory: Path) -> Lease:
    data = read(directory, "lease.json")
    unique_json(data)
    return Lease.model_validate_json(data)


class Runtime:
    """Dedicated existing Colima only; no discovery, contexts, pull or secrets."""

    def __init__(self, directory: Path):
        state = Path.home() / ".mlrt-v1"
        self.env = {
            "HOME": str(Path.home()),
            "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
            "LIMA_HOME": str(state / "lima"),
            "DOCKER_CONFIG": str(directory / "docker-config"),
        }
        self.docker = [
            "/usr/local/bin/docker",
            "--config",
            self.env["DOCKER_CONFIG"],
            "--host",
            "unix://" + str(state / "colima/model-learner/docker.sock"),
        ]
        self.lima = [
            str(Path.home() / ".local/share/model-learner/runtime-v1/bin/limactl"),
            "shell",
            "colima-model-learner",
            "sh",
            "-c",
        ]

    def command(self, args, *, guest=False):
        return _bounded(
            (self.lima if guest else self.docker) + list(args),
            deadline=time.monotonic() + 4,
            env=self.env,
        )

    def verify(self):
        mounted = self.command(
            [
                "r=$(findmnt -rn -t virtiofs,9p -o TARGET); s=$?; "
                'test "$s" -le 1 || exit 1; printf "%s" "$r"'
            ],
            guest=True,
        )
        if mounted.strip():
            raise ValueError("VM host shares refused")
        image = json.loads(self.command(["image", "inspect", IMAGE]))[0]
        if (
            image.get("Descriptor", {}).get("digest") != IMAGE
            or image["Architecture"] != "arm64"
            or image["Config"].get("Volumes")
            or image["Config"].get("Env")
            != ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
        ):
            raise ValueError("pinned credential-free image required")

    def inspect(self, lease: Lease):
        selector = (
            "id=" + lease.container_id
            if lease.container_id
            else "name=^/" + lease.name + "$"
        )
        ids = self.command(
            ["ps", "-a", "--no-trunc", "--filter", selector, "--format", "{{.ID}}"]
        )
        rows = ids.decode().splitlines()
        if not rows:
            return None  # Successful daemon query, not an inspect error.
        if len(rows) != 1 or not re.fullmatch(r"[0-9a-f]{64}", rows[0]):
            raise ValueError("ambiguous container identity")
        info = json.loads(self.command(["inspect", rows[0]]))[0]
        if (
            info["Id"] != rows[0]
            or info["Name"] != "/" + lease.name
            or info["Config"].get("Labels", {}).get(OWNER_LABEL) != str(lease.owner)
            or (lease.container_id and rows[0] != lease.container_id)
            or not _policy_matches(info, IMAGE)
            or info["Config"].get("Env")
            != ["PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"]
            or info["Config"]["Cmd"] != ["-c", worker(lease.worker_mode)]
        ):
            raise ValueError("container ownership/policy mismatch")
        return info

    def pids(self, identity):
        rows = self.command(["top", identity, "-eo", "pid"]).decode().splitlines()[1:]
        pids = tuple(int(row.strip()) for row in rows)
        if len(pids) > 16 or any(pid < 2 for pid in pids):
            raise ValueError("bounded owned process list required")
        return pids

    def absent(self, pids):
        if pids:
            self.command(
                [
                    "for p in "
                    + " ".join(map(str, pids))
                    + "; do test ! -e /proc/$p || exit 1; done"
                ],
                guest=True,
            )
        return True


def validate_receipt(directory: Path) -> Receipt:
    lease = load(directory)
    data = read(directory, "receipt.json")
    unique_json(data)
    receipt = Receipt.model_validate_json(data)
    if (
        receipt.lease_sha256 != digest(encode(lease))
        or receipt.run_id != lease.run_id
        or receipt.target != lease.target
        or receipt.configuration != lease.configuration
        or (lease.container_id and receipt.container_id != lease.container_id)
        or receipt.input_sha256 != lease.input_sha256
        or receipt.prepared_at != lease.prepared_at
        or receipt.prepared_monotonic_ns != lease.prepared_monotonic_ns
        or receipt.stopped_at.utcoffset() is None
        or receipt.stopped_at < lease.prepared_at
        or receipt.stopped_monotonic_ns < lease.prepared_monotonic_ns
    ):
        raise ValueError("receipt binding/time mismatch")
    if receipt.output_sha256 is not None:
        output = read(directory, "output.bin")
        if (
            not receipt.input_observed
            or len(output) > MAX_HANDOFF
            or digest(output) != receipt.output_sha256
            or len(output) != receipt.output_bytes
        ):
            raise ValueError("output binding mismatch")
    elif receipt.output_bytes is not None:
        raise ValueError("unknown output size required")
    if (
        len(receipt.observed_guest_pids) > 16
        or len(set(receipt.observed_guest_pids)) != len(receipt.observed_guest_pids)
        or any(pid < 2 for pid in receipt.observed_guest_pids)
    ):
        raise ValueError("invalid owned-process evidence")
    expected = (
        receipt.container_absent
        and receipt.descendants_absent
        and receipt.output_stable_after_stop
        and not receipt.errors
    )
    if receipt.cleanup_confirmed != expected:
        raise ValueError("cleanup assertion contradicts evidence")
    return receipt


def cleanup(directory: Path, reason: str, runtime=None) -> Receipt:
    """Only an exact owned identity; uncertainty is retained, never absence."""
    lease = load(directory)
    if (directory / "receipt.json").exists():
        return validate_receipt(directory)
    runtime = runtime or Runtime(directory)
    identity = lease.container_id
    pids = ()
    absent = descendants = stable = input_observed = False
    output = None
    errors = []
    try:
        info = runtime.inspect(lease)
        if info is None:
            absent = descendants = True
            stable = True
        else:
            identity = info["Id"]
            if lease.container_id is None:
                lease = Lease.model_validate(
                    lease.model_dump() | {"container_id": identity}
                )
                durable(directory, "lease.json", encode(lease), replace=True)
            if info["State"]["Running"]:
                pids = runtime.pids(identity)
                runtime.command(["kill", "--signal", "KILL", identity])
            runtime.command(["wait", identity])
            stopped = runtime.inspect(lease)
            if (
                stopped is None
                or stopped["State"]["Running"]
                or stopped["State"].get("Pid") != 0
            ):
                raise ValueError("stopped container not confirmed")
            first = runtime.command(["logs", identity])
            second = runtime.command(["logs", identity])
            stable = first == second
            header, separator, payload = first.partition(b"\n")
            if (
                reason == "arm_failure"
                and not first
                and not info["State"]["Running"]
                and not (directory / "start-consumed.json").exists()
            ):
                # An unarmed worker never ran: absent input/output is unknown,
                # not a failed cleanup or fabricated observed input digest.
                pass
            elif header != lease.input_sha256.encode() or not separator:
                errors.append("input_receipt_missing_or_mismatched")
            else:
                input_observed = True
                if len(payload) > MAX_HANDOFF:
                    errors.append("output_too_large")
                elif payload:
                    if payload != OUTPUT:
                        errors.append("unexpected_synthetic_output")
                    else:
                        output = payload
            descendants = runtime.absent(pids)
            runtime.command(["rm", "--force", identity])
            absent = runtime.inspect(lease) is None
    except Exception:
        errors.append("cleanup_or_runtime_uncertain")
        # Removal is still attempted only after immutable ownership was checked.
        if identity and "info" in locals() and info is not None:
            try:
                runtime.command(["rm", "--force", identity])
                absent = runtime.inspect(lease) is None
                descendants = runtime.absent(pids)
            except Exception:
                pass
    if output is not None:
        durable(directory, "output.bin", output)
    receipt = Receipt(
        lease_sha256=digest(encode(lease)),
        run_id=lease.run_id,
        target=lease.target,
        configuration=lease.configuration,
        container_id=identity,
        stop_reason=reason,
        prepared_at=lease.prepared_at,
        stopped_at=utc_now(),
        prepared_monotonic_ns=lease.prepared_monotonic_ns,
        stopped_monotonic_ns=time.monotonic_ns(),
        input_sha256=lease.input_sha256,
        input_observed=input_observed,
        output_sha256=None if output is None else digest(output),
        output_bytes=None if output is None else len(output),
        observed_guest_pids=pids,
        container_absent=absent,
        descendants_absent=descendants,
        output_stable_after_stop=stable,
        cleanup_confirmed=absent and descendants and stable and not errors,
        errors=tuple(errors),
    )
    durable(directory, "receipt.json", encode(receipt))
    return validate_receipt(directory)


def launchd(directory: Path, lease: Lease):
    runtime = lease.helper_runtime
    if runtime is None:
        raise ValueError("pinned helper runtime required")
    bundle = Path(runtime.bundle)
    if digest(Path(runtime.interpreter).read_bytes()) != runtime.interpreter_sha256:
        raise ValueError("base interpreter changed")
    if digest(read(bundle, "bootstrap.py")) != runtime.bootstrap_sha256:
        raise ValueError("bootstrap changed")
    plist = {
        "Label": lease.label,
        "ProgramArguments": [
            runtime.interpreter,
            "-I",
            "-B",
            "-S",
            str(bundle / "bootstrap.py"),
            runtime.manifest_sha256,
            str(directory / "helper.py"),
            "watch",
            str(directory),
        ],
        "EnvironmentVariables": {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
        "WorkingDirectory": "/",
        "RunAtLoad": True,
        "ProcessType": "Background",
        "StandardOutPath": "/dev/null",
        "StandardErrorPath": "/dev/null",
    }
    durable(directory, "job.plist", plistlib.dumps(plist))
    subprocess.run(
        [
            "/bin/launchctl",
            "bootstrap",
            f"gui/{os.getuid()}",
            str(directory / "job.plist"),
        ],
        check=True,
        capture_output=True,
        timeout=10,
    )


def start(directory: Path, *, mode="normal", timeout_seconds=5, runtime=None):
    """One exclusive start. Existing or ambiguous state requires recovery only."""
    if type(timeout_seconds) not in (int, float) or not 0.5 <= timeout_seconds <= 30:
        raise ValueError("finite 0.5..30-second synthetic deadline required")
    worker(mode)
    directory = Path(directory).absolute()
    directory.mkdir(mode=0o700, exist_ok=False)
    secure_directory(directory)
    (directory / "docker-config").mkdir(mode=0o700)
    source = Path(__file__).read_bytes()
    durable(directory, "helper.py", source)
    now = time.monotonic_ns()
    lease = Lease(
        run_id=uuid4(),
        owner=uuid4(),
        worker_mode=mode,
        input_sha256=digest(INPUT),
        helper_sha256=digest(source),
        controller_pid=os.getpid(),
        prepared_at=utc_now(),
        prepared_monotonic_ns=now,
        deadline_monotonic_ns=now + int(timeout_seconds * 1e9),
        helper_runtime=package_helper(),
    )
    durable(directory, "lease.json", encode(lease))
    runtime = runtime or Runtime(directory)
    try:
        runtime.verify()
        args = _create_arguments(lease.name, IMAGE, worker(mode))
        args[1:1] = ["--label", OWNER_LABEL + "=" + str(lease.owner)]
        identity = runtime.command(args).decode().strip()
        lease = Lease.model_validate(lease.model_dump() | {"container_id": identity})
        durable(directory, "lease.json", encode(lease), replace=True)
        runtime.inspect(lease)
        launchd(directory, lease)
        deadline = time.monotonic() + 4
        while not (directory / "ready.json").exists():
            if (directory / "receipt.json").exists() or time.monotonic() > deadline:
                raise ValueError("independent supervisor not armed")
            time.sleep(0.025)
        ready = unique_json(read(directory, "ready.json"))
        if ready != {
            "lease_sha256": digest(encode(lease)),
            "controller_pid": os.getpid(),
        }:
            raise ValueError("supervisor handshake mismatch")
        if time.monotonic_ns() >= lease.deadline_monotonic_ns:
            raise ValueError("deadline passed before dispatch")
        durable(
            directory, "start-consumed.json", b'{"synthetic_start_consumed":true}\n'
        )
        runtime.command(["start", identity])
        return lease
    except Exception:
        # Worker cannot start before the independent watcher handshake. Once
        # armed, leave cleanup solely with it (including ambiguous start RPC).
        if not (directory / "ready.json").exists():
            stopped = cleanup(directory, "arm_failure", runtime)
            if stopped.cleanup_confirmed:
                unload(lease)
        raise


def watch(directory: Path):
    lease = load(directory)
    if (
        lease.container_id is None
        or digest(read(directory, "helper.py")) != lease.helper_sha256
    ):
        raise ValueError("armed immutable identity/helper required")
    if lease.helper_runtime is not None and getattr(
        sys, "_model_learner_bundle", None
    ) != (lease.helper_runtime.bundle, lease.helper_runtime.manifest_sha256):
        raise ValueError("verified helper bundle required")
    runtime = None
    sys._model_learner_stage = "watch_register"
    with closing(select.kqueue()) as queue:
        event = select.kevent(
            lease.controller_pid,
            filter=select.KQ_FILTER_PROC,
            flags=select.KQ_EV_ADD | select.KQ_EV_ONESHOT,
            fflags=select.KQ_NOTE_EXIT,
        )
        try:
            queue.control([event], 0, 0)
            durable(
                directory,
                "ready.json",
                json.dumps(
                    {
                        "lease_sha256": digest(encode(lease)),
                        "controller_pid": lease.controller_pid,
                    }
                ).encode(),
            )
            sys._model_learner_stage = "ready"
            if lease.purpose == "no_worker_preflight":
                return
            runtime = Runtime(directory)
            while True:
                if queue.control(None, 1, 0):
                    return cleanup(directory, "controller_exit", runtime)
                if time.monotonic_ns() >= lease.deadline_monotonic_ns:
                    return cleanup(directory, "deadline", runtime)
                info = runtime.inspect(lease)
                if info is None or info["State"]["Status"] == "exited":
                    return cleanup(directory, "completed", runtime)
                time.sleep(0.025)
        except Exception:
            if lease.purpose == "no_worker_preflight":
                raise
            return cleanup(directory, "control_error", runtime)


def recover(directory: Path, runtime=None):
    """Restart is cleanup-only. Never starts work or resets consumed state."""
    lease = load(directory)  # Malformed/ambiguous ownership authorizes no kill.
    if (directory / "receipt.json").exists():
        return validate_receipt(directory)
    if (directory / "job.plist").exists():
        unload(lease)
        if (directory / "receipt.json").exists():
            return validate_receipt(directory)
    return cleanup(directory, "recovery", runtime)


class DisposalError(ValueError):
    """Stable non-secret category; callers retain state on every failure."""

    def __init__(self, category):
        self.category = category
        super().__init__("launchd disposal: " + category)


def _launchctl(args, timeout):
    """Discard stdout at source; cap private stderr and reap our own CLI only."""
    process = subprocess.Popen(
        ["/bin/launchctl", *args],
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )
    deadline = time.monotonic() + timeout
    data = bytearray()
    try:
        with selectors.DefaultSelector() as selector:
            selector.register(process.stderr, selectors.EVENT_READ)
            while selector.get_map():
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise subprocess.TimeoutExpired("launchctl", timeout)
                for key, _ in selector.select(min(0.05, remaining)):
                    chunk = os.read(key.fd, min(1024, 4097 - len(data)))
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        data.extend(chunk)
                        if len(data) > 4096:
                            raise DisposalError("stderr_limit")
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise subprocess.TimeoutExpired("launchctl", timeout)
        return process.wait(timeout=remaining), bytes(data)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait(timeout=1)
        process.stderr.close()


def unload(lease: Lease):
    """Finite exact-label removal; explicit absence requires a healthy domain."""
    domain = f"gui/{os.getuid()}"
    service = f"{domain}/{lease.label}"
    deadline = time.monotonic() + 5
    booted_out = False

    def command(args):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise DisposalError("deadline_expired")
        return _launchctl(args, min(1.0, remaining))

    def healthy_domain():
        domain_code, domain_error = command(["print", domain])
        if domain_code != 0:
            raise DisposalError("domain_failure")
        if domain_error:
            raise DisposalError("unrecognized_stderr")

    try:
        while True:
            code, error = command(["print", service])
            # Bind the full observed launchctl absence message to this exact
            # label and GUI UID. A phrase for a different job is not evidence.
            absent = re.fullmatch(
                rb'(?:Bad request\.\s*)?Could not find service "'
                + re.escape(lease.label.encode())
                + rb'" in domain for user gui: '
                + str(os.getuid()).encode()
                + rb"\s*",
                error,
            )
            if code != 0 and absent:
                healthy_domain()
                return
            if code != 0 or error:
                healthy_domain()
                raise DisposalError("unrecognized_stderr")
            if not booted_out:
                boot_code, boot_error = command(["bootout", service])
                if boot_error:
                    raise DisposalError("unrecognized_stderr")
                if boot_code != 0:
                    raise DisposalError("bootout_failure")
                booted_out = True
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise DisposalError("deadline_expired")
            time.sleep(min(0.05, remaining))
    except subprocess.TimeoutExpired:
        raise DisposalError("command_timeout") from None
    except KeyboardInterrupt:
        raise DisposalError("cancelled") from None
    except OSError:
        raise DisposalError("command_error") from None


def finalize(directory: Path, retained: Path):
    """Retain bound evidence, unload only this label, remove temporary state."""
    receipt = validate_receipt(directory)
    if not receipt.cleanup_confirmed:
        raise ValueError("uncertain cleanup; state must remain for review")
    lease = load(directory)
    unload(lease)
    retained.mkdir(mode=0o700, exist_ok=False)
    for name in ("lease.json", "receipt.json", "output.bin", "helper-diagnostic.json"):
        if (directory / name).exists():
            durable(retained, name, read(directory, name))
    validate_receipt(retained)
    names = {p.name for p in directory.iterdir()}
    if names - {
        "lease.json",
        "helper.py",
        "job.plist",
        "ready.json",
        "start-consumed.json",
        "receipt.json",
        "output.bin",
        "docker-config",
        "helper-diagnostic.json",
    }:
        raise ValueError("unexpected state; refuse removal")
    if list((directory / "docker-config").iterdir()):
        raise ValueError("unexpected client state; refuse removal")
    (directory / "docker-config").rmdir()
    for path in directory.iterdir():
        if path.is_symlink() or not path.is_file():
            raise ValueError("unexpected state type")
        path.unlink()
    directory.rmdir()
    return receipt


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("watch", "run", "recover"))
    parser.add_argument("directory", type=Path)
    parser.add_argument("--mode", choices=("normal", "live"), default="normal")
    parser.add_argument("--seconds", type=float, default=5)
    args = parser.parse_args()
    if args.action == "watch":
        watch(args.directory)
    elif args.action == "recover":
        recover(args.directory)
    else:
        start(args.directory, mode=args.mode, timeout_seconds=args.seconds)
        deadline = time.monotonic() + args.seconds + 40
        while not (args.directory / "receipt.json").exists():
            if time.monotonic() >= deadline:
                recover(args.directory)
                break
            time.sleep(0.025)
        validate_receipt(args.directory)


if __name__ == "__main__":
    main()
