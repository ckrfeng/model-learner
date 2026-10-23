"""Original synthetic control fixtures; no launchd, containers, Git or network."""

import json
import os
import plistlib
import subprocess
import sys
import time
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from model_learner.benchmark import supervision as control
from model_learner.domain.models import (
    AcceptanceSpec,
    Observation,
    Verification,
    utc_now,
)
from model_learner.learn.advisory import AdvisoryInput

PACKAGE_HELPER = control.package_helper


@pytest.fixture(autouse=True)
def no_installed_bundle_writes(monkeypatch):
    monkeypatch.setattr(control, "package_helper", lambda: None)


class FakeRuntime:
    def __init__(self, directory, *, fail=None, output=None):
        self.directory = directory
        self.exists = True
        self.running = True
        self.fail = fail
        self.calls = []
        self.output = output

    def verify(self):
        self.calls.append(["verify"])

    def inspect(self, lease):
        self.calls.append(["inspect", lease.container_id])
        if self.fail == "inspect":
            raise ValueError("uncertain runtime")
        if not self.exists:
            return None
        return {
            "Id": "a" * 64,
            "State": {
                "Running": self.running,
                "Status": "running" if self.running else "exited",
                "Pid": 1001 if self.running else 0,
            },
        }

    def pids(self, identity):
        return (1001, 1002)

    def absent(self, pids):
        if self.fail == "descendants":
            raise ValueError("absence unknown")
        return True

    def command(self, args):
        self.calls.append(args)
        if self.fail == args[0]:
            raise ValueError("synthetic operation failed")
        if args[0] == "create":
            assert (self.directory / "lease.json").exists()
            return ("a" * 64 + "\n").encode()
        if args[0] == "start":
            assert (self.directory / "ready.json").is_file()
            assert (self.directory / "start-consumed.json").is_file()
            self.running = True
        if args[0] == "kill":
            self.running = False
        if args[0] == "logs":
            return (
                self.output
                if self.output is not None
                else (control.digest(control.INPUT).encode() + b"\n" + control.OUTPUT)
            )
        if args[0] == "rm":
            self.exists = False
        return b"0\n"


@pytest.fixture
def state(tmp_path):
    directory = tmp_path / "state"
    directory.mkdir(mode=0o700)
    (directory / "docker-config").mkdir(mode=0o700)
    source = b"synthetic helper bytes"
    control.durable(directory, "helper.py", source)
    now = time.monotonic_ns()
    lease = control.Lease(
        run_id=uuid4(),
        owner=uuid4(),
        container_id="a" * 64,
        worker_mode="normal",
        input_sha256=control.digest(control.INPUT),
        helper_sha256=control.digest(source),
        controller_pid=os.getpid(),
        prepared_at=utc_now(),
        prepared_monotonic_ns=now,
        deadline_monotonic_ns=now + 10_000_000_000,
    )
    control.durable(directory, "lease.json", control.encode(lease))
    return directory, lease


def test_complete_bound_receipt_is_idempotent_and_not_utility(state):
    directory, lease = state
    runtime = FakeRuntime(directory)
    receipt = control.cleanup(directory, "completed", runtime)
    assert receipt.cleanup_confirmed and receipt.container_absent
    assert receipt.descendants_absent and receipt.output_stable_after_stop
    assert receipt.input_observed
    assert receipt.observed_guest_pids == (1001, 1002)
    assert receipt.output_sha256 == control.digest(control.OUTPUT)
    assert receipt.input_sha256 == lease.input_sha256
    assert receipt.canonical_attempt_latency is None
    assert receipt.model_transport == "absent"
    before = list(runtime.calls)
    assert control.recover(directory, runtime) == receipt
    assert runtime.calls == before
    for model in (Observation, Verification, AdvisoryInput):
        with pytest.raises(ValidationError):
            model.model_validate(receipt.model_dump())


@pytest.mark.parametrize(
    "field,value",
    [
        ("run_id", str(uuid4())),
        ("container_id", "b" * 64),
        ("lease_sha256", "0" * 64),
        ("input_sha256", "0" * 64),
        ("output_sha256", "0" * 64),
        ("output_bytes", 999),
        ("stopped_monotonic_ns", 0),
        ("prepared_monotonic_ns", 1),
        ("cleanup_confirmed", False),
        ("container_absent", False),
        ("descendants_absent", False),
        ("output_stable_after_stop", False),
        ("input_observed", False),
        ("target", {"identifier": "different", "version": "2"}),
        ("configuration", {"model": "not-a-synthetic-worker"}),
    ],
)
def test_receipt_rebinding_and_false_assertions_fail_closed(state, field, value):
    directory, _ = state
    control.cleanup(directory, "completed", FakeRuntime(directory))
    payload = json.loads(control.read(directory, "receipt.json"))
    payload[field] = value
    control.durable(
        directory, "receipt.json", json.dumps(payload).encode(), replace=True
    )
    with pytest.raises(ValueError):
        control.validate_receipt(directory)


@pytest.mark.parametrize(
    "failure", ["inspect", "kill", "wait", "logs", "rm", "descendants"]
)
def test_cleanup_failure_never_becomes_verified_absence(state, failure, tmp_path):
    directory, _ = state
    runtime = FakeRuntime(directory, fail=failure)
    receipt = control.cleanup(directory, "recovery", runtime)
    assert not receipt.cleanup_confirmed and receipt.errors
    with pytest.raises(ValueError, match="uncertain cleanup"):
        control.finalize(directory, tmp_path / "retained")
    assert directory.is_dir()
    if failure == "inspect":
        assert not any(call[0] in {"kill", "rm"} for call in runtime.calls)


@pytest.mark.parametrize(
    "output",
    [
        b"",
        b"bad-input\n",
        b"x" * 2048,
        control.digest(control.INPUT).encode() + b"\nwrong",
    ],
)
def test_unbound_or_oversized_output_is_not_accepted(state, output):
    directory, _ = state
    receipt = control.cleanup(
        directory, "completed", FakeRuntime(directory, output=output)
    )
    assert receipt.output_sha256 is None
    assert not receipt.cleanup_confirmed


def test_start_has_durable_intent_guard_and_consumption_before_dispatch(
    tmp_path, monkeypatch
):
    directory = tmp_path / "new"
    runtime = FakeRuntime(directory)

    def arm(path, lease):
        assert control.load(path).container_id == "a" * 64
        assert not any(call[0] == "start" for call in runtime.calls)
        control.durable(
            path,
            "ready.json",
            json.dumps(
                {
                    "lease_sha256": control.digest(control.encode(lease)),
                    "controller_pid": os.getpid(),
                }
            ).encode(),
        )

    monkeypatch.setattr(control, "launchd", arm)
    lease = control.start(directory, runtime=runtime)
    assert lease.container_id == "a" * 64
    assert len([call for call in runtime.calls if call[0] == "start"]) == 1
    create = next(call for call in runtime.calls if call[0] == "create")
    assert "--label" in create and "--pull" in create and "never" in create
    assert "--network" in create and "none" in create
    assert "--mount" not in create and "--volume" not in create
    before = list(runtime.calls)
    with pytest.raises(FileExistsError):
        control.start(directory, runtime=runtime)
    assert runtime.calls == before


def test_arm_failure_never_starts_and_cleanup_is_retained(tmp_path, monkeypatch):
    directory = tmp_path / "failed"
    runtime = FakeRuntime(directory)

    def fail(*args):
        raise OSError("synthetic launchd failure")

    monkeypatch.setattr(control, "launchd", fail)
    unloaded = []
    monkeypatch.setattr(control, "unload", lambda lease: unloaded.append(lease.label))
    with pytest.raises(OSError):
        control.start(directory, runtime=runtime)
    assert not any(call[0] == "start" for call in runtime.calls)
    assert control.validate_receipt(directory).stop_reason == "arm_failure"
    assert unloaded


def test_unstarted_container_cleanup_preserves_unknown_input_and_output(state):
    directory, _ = state
    runtime = FakeRuntime(directory, output=b"")
    runtime.running = False
    receipt = control.cleanup(directory, "arm_failure", runtime)
    assert receipt.cleanup_confirmed
    assert not receipt.input_observed
    assert receipt.output_sha256 is receipt.output_bytes is None


@pytest.mark.parametrize("payload", [b"", b"{", b"{}", b'{"container_id":"ambiguous"}'])
def test_malformed_lease_authorizes_no_runtime_action(state, payload):
    directory, _ = state
    control.durable(directory, "lease.json", payload, replace=True)
    runtime = FakeRuntime(directory)
    with pytest.raises(ValueError):
        control.recover(directory, runtime)
    assert not runtime.calls


def test_duplicate_keys_in_otherwise_valid_lease_refuse_recovery(state):
    directory, lease = state
    raw = control.read(directory, "lease.json").rstrip()
    repeated = raw[:-1] + b',"run_id":"' + str(lease.run_id).encode() + b'"}'
    control.durable(directory, "lease.json", repeated, replace=True)
    runtime = FakeRuntime(directory)
    with pytest.raises(ValueError, match="duplicate"):
        control.recover(directory, runtime)
    assert not runtime.calls


def test_duplicate_receipt_keys_refuse_replay(state):
    directory, _ = state
    control.cleanup(directory, "completed", FakeRuntime(directory))
    raw = control.read(directory, "receipt.json").rstrip()
    control.durable(
        directory,
        "receipt.json",
        raw[:-1] + b',"cleanup_confirmed":true}',
        replace=True,
    )
    with pytest.raises(ValueError, match="duplicate"):
        control.validate_receipt(directory)


@pytest.mark.parametrize("pids", [[1], [1001, 1001], list(range(2, 20))])
def test_invalid_process_absence_claims_refuse(state, pids):
    directory, _ = state
    control.cleanup(directory, "completed", FakeRuntime(directory))
    data = json.loads(control.read(directory, "receipt.json"))
    data["observed_guest_pids"] = pids
    control.durable(directory, "receipt.json", json.dumps(data).encode(), replace=True)
    with pytest.raises(ValueError, match="owned-process"):
        control.validate_receipt(directory)


@pytest.mark.parametrize("mode", [0o644, 0o777])
def test_unsafe_state_permissions_refuse(state, mode):
    directory, _ = state
    (directory / "lease.json").chmod(mode)
    with pytest.raises(ValueError, match="private state"):
        control.load(directory)


def test_symlink_state_and_helper_tamper_refused(state, tmp_path):
    directory, _ = state
    alias = tmp_path / "alias"
    alias.symlink_to(directory, target_is_directory=True)
    with pytest.raises(ValueError, match="symlink state"):
        control.load(alias)
    (directory / "helper.py").write_bytes(b"changed")
    with pytest.raises(ValueError, match="helper required"):
        control.watch(directory)


def test_hardlinked_private_state_is_not_read(state, tmp_path):
    directory, _ = state
    os.link(directory / "lease.json", tmp_path / "second-link")
    with pytest.raises(ValueError, match="private state"):
        control.load(directory)


def test_sync_failure_cannot_dispatch_and_retains_ambiguous_state(
    tmp_path, monkeypatch
):
    directory = tmp_path / "unsynced"
    runtime = FakeRuntime(directory)

    def fail(fd):
        raise OSError("synthetic fsync failure")

    monkeypatch.setattr(control.os, "fsync", fail)
    with pytest.raises(OSError):
        control.start(directory, runtime=runtime)
    assert not runtime.calls and directory.exists()
    with pytest.raises(FileExistsError):
        control.start(directory, runtime=runtime)


@pytest.mark.parametrize("mode", ["agent", "pilot", "custom", "provider"])
def test_only_frozen_synthetic_workers(mode):
    with pytest.raises(ValueError):
        control.worker(mode)


def test_environment_never_inherits_credentials_or_agent_socket(tmp_path, monkeypatch):
    monkeypatch.setenv("OPENROUTER_API_KEY", "synthetic-value-never-forward")
    monkeypatch.setenv("SSH_AUTH_SOCK", "/synthetic/agent.sock")
    runtime = control.Runtime(tmp_path)
    assert set(runtime.env) == {"HOME", "PATH", "LIMA_HOME", "DOCKER_CONFIG"}
    assert "synthetic-value-never-forward" not in str(runtime.env)
    assert "/synthetic/agent.sock" not in str(runtime.env)
    assert "--host" in runtime.docker
    assert ".mlrt-v1/colima/model-learner/docker.sock" in runtime.docker[-1]


def test_recovery_of_reserved_identity_is_cleanup_only(state):
    directory, lease = state
    control.durable(
        directory,
        "lease.json",
        control.encode(lease.model_copy(update={"container_id": None})),
        replace=True,
    )
    runtime = FakeRuntime(directory)
    receipt = control.recover(directory, runtime)
    assert receipt.container_id == "a" * 64 and receipt.cleanup_confirmed
    assert not any(call[0] in {"create", "start"} for call in runtime.calls)


def test_new_configuration_or_target_is_not_admitted(state):
    _, lease = state
    data = lease.model_dump() | {
        "target": AcceptanceSpec(identifier="W4A", version="1")
    }
    with pytest.raises(ValueError, match="synthetic target"):
        control.Lease.model_validate(data)


def test_finalize_retains_valid_receipt_and_removes_temporary_state(
    state, tmp_path, monkeypatch
):
    directory, _ = state
    receipt = control.cleanup(directory, "completed", FakeRuntime(directory))
    removed = []
    monkeypatch.setattr(control, "unload", lambda lease: removed.append(lease.label))
    retained = tmp_path / "retained"
    assert control.finalize(directory, retained) == receipt
    assert removed and not directory.exists()
    assert control.validate_receipt(retained) == receipt


def test_unverified_job_removal_preserves_temporary_state(state, tmp_path, monkeypatch):
    directory, _ = state
    control.cleanup(directory, "completed", FakeRuntime(directory))

    def fail(*args):
        raise ValueError("job absence uncertain")

    monkeypatch.setattr(control, "unload", fail)
    with pytest.raises(ValueError, match="job absence"):
        control.finalize(directory, tmp_path / "retained")
    assert directory.exists()


def absent_message(lease):
    """Synthetic expected launchctl framing; contains no imported job output."""
    return (
        f'Bad request.\nCould not find service "{lease.label}" '
        f"in domain for user gui: {os.getuid()}\n"
    ).encode()


def test_disposal_polls_exact_service_until_absent_with_healthy_domain(
    state, monkeypatch
):
    _, lease = state
    service = f"gui/{os.getuid()}/{lease.label}"
    replies = iter(
        [(0, b""), (0, b""), (0, b""), (113, absent_message(lease)), (0, b"")]
    )
    calls = []

    def command(args, timeout):
        assert 0 < timeout <= 1
        calls.append(args)
        return next(replies)

    monkeypatch.setattr(control, "_launchctl", command)
    monkeypatch.setattr(control.time, "sleep", lambda _: None)
    control.unload(lease)
    assert calls == [
        ["print", service],
        ["bootout", service],
        ["print", service],
        ["print", service],
        ["print", f"gui/{os.getuid()}"],
    ]


def test_disposal_already_absent_does_not_unload_again(state, monkeypatch):
    _, lease = state
    calls = []

    def command(args, timeout):
        calls.append(args)
        return (113, absent_message(lease)) if len(calls) == 1 else (0, b"")

    monkeypatch.setattr(control, "_launchctl", command)
    control.unload(lease)
    assert len(calls) == 2 and all(args[0] == "print" for args in calls)


@pytest.mark.parametrize(
    "fault,category",
    [
        ("domain", "domain_failure"),
        ("domain_stderr", "unrecognized_stderr"),
        ("unknown", "unrecognized_stderr"),
        ("wrong_label", "unrecognized_stderr"),
        ("wrong_uid", "unrecognized_stderr"),
        ("timeout", "command_timeout"),
        ("cancel", "cancelled"),
        ("deadline", "deadline_expired"),
        ("bootout", "bootout_failure"),
        ("bootout_stderr", "unrecognized_stderr"),
    ],
)
def test_disposal_failures_keep_all_state(
    state, tmp_path, monkeypatch, fault, category
):
    directory, lease = state
    control.cleanup(directory, "completed", FakeRuntime(directory))
    original = {p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()}
    clock = [0.0]
    calls = []

    def command(args, timeout):
        calls.append(args)
        if fault == "timeout":
            raise subprocess.TimeoutExpired("launchctl", timeout)
        if fault == "cancel":
            raise KeyboardInterrupt
        if args[0] == "bootout":
            return (
                (1, b"")
                if fault == "bootout"
                else (
                    (0, b"synthetic private error")
                    if fault == "bootout_stderr"
                    else (0, b"")
                )
            )
        if args[-1] == f"gui/{os.getuid()}":
            return (
                (1, b"synthetic domain error")
                if fault == "domain"
                else (0, b"synthetic private error")
            )
        if fault in {"deadline", "bootout", "bootout_stderr"}:
            return 0, b""
        if fault == "unknown":
            return 113, b"synthetic private error"
        message = absent_message(lease)
        if fault == "wrong_label":
            message = message.replace(lease.label.encode(), b"unrelated.synthetic.job")
        if fault == "wrong_uid":
            message = message.replace(f"gui: {os.getuid()}".encode(), b"gui: 999999")
        return 113, message

    monkeypatch.setattr(control, "_launchctl", command)
    monkeypatch.setattr(control.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        control.time, "sleep", lambda delay: clock.__setitem__(0, clock[0] + delay)
    )
    with pytest.raises(control.DisposalError) as caught:
        control.finalize(directory, tmp_path / "retained")
    assert caught.value.category == category
    assert "synthetic private" not in str(caught.value)
    assert not (tmp_path / "retained").exists()
    assert {
        p.name: p.read_bytes() for p in directory.iterdir() if p.is_file()
    } == original
    assert all(
        args[-1] in {f"gui/{os.getuid()}", f"gui/{os.getuid()}/{lease.label}"}
        for args in calls
    )


@pytest.mark.parametrize("output_bytes,expected", [(0, None), (5000, "stderr_limit")])
def test_launchctl_discards_stdout_and_bounds_stderr(
    monkeypatch, output_bytes, expected
):
    popen = subprocess.Popen
    owned = []

    def synthetic(args, **kwargs):
        assert args == ["/bin/launchctl", "print", "synthetic-owned-label"]
        assert kwargs["stdout"] == subprocess.DEVNULL
        process = popen(
            [
                sys.executable,
                "-I",
                "-B",
                "-S",
                "-c",
                f"import os; os.write(2, b'x' * {output_bytes}); "
                "os.write(1, b'private')",
            ],
            **kwargs,
        )
        owned.append(process)
        return process

    monkeypatch.setattr(control.subprocess, "Popen", synthetic)
    if expected:
        with pytest.raises(control.DisposalError, match=expected):
            control._launchctl(["print", "synthetic-owned-label"], 2)
    else:
        assert control._launchctl(["print", "synthetic-owned-label"], 2) == (0, b"")
    assert owned[0].poll() is not None and owned[0].stderr.closed


@pytest.mark.parametrize("cancel", [False, True])
def test_launchctl_reaps_only_owned_cli_on_timeout_or_cancel(monkeypatch, cancel):
    popen = subprocess.Popen
    owned = []

    def synthetic(args, **kwargs):
        process = popen(
            [sys.executable, "-I", "-B", "-S", "-c", "import time; time.sleep(30)"],
            **kwargs,
        )
        owned.append(process)
        return process

    if cancel:

        class InterruptSelector(control.selectors.DefaultSelector):
            def select(self, timeout):
                raise KeyboardInterrupt

        monkeypatch.setattr(control.selectors, "DefaultSelector", InterruptSelector)
    monkeypatch.setattr(control.subprocess, "Popen", synthetic)
    with pytest.raises(KeyboardInterrupt if cancel else subprocess.TimeoutExpired):
        control._launchctl(["print", "synthetic-owned-label"], 0.05)
    assert owned[0].poll() is not None and owned[0].stderr.closed


def test_legacy_lease_encoding_preserves_receipt_binding(state):
    _, lease = state
    encoded = control.encode(lease)
    assert b'"helper_runtime"' not in encoded and b'"purpose"' not in encoded
    assert control.encode(control.Lease.model_validate_json(encoded)) == encoded


def test_verified_bundle_imports_without_site_and_rejects_tamper(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    runtime = PACKAGE_HELPER()
    bundle = Path(runtime.bundle)
    assert "Documents" not in Path(runtime.interpreter).parts
    manifest = json.loads((bundle / "manifest.json").read_bytes())
    assert set(manifest["versions"]) == {
        "pydantic",
        "pydantic-core",
        "annotated-types",
        "typing-extensions",
        "typing-inspection",
    }
    assert not any(name.endswith((".pth", ".pyc")) for name in manifest["files"])
    probe = tmp_path / "probe.py"
    probe.write_text(
        "import sys\nfrom model_learner.benchmark.supervision import Lease\n"
        "assert 'site' not in sys.modules\n"
        "assert not any('Documents' in p for p in sys.path)\n"
        "assert Lease.model_fields['helper_runtime']\n"
    )
    diagnostic = tmp_path / "diagnostic"
    diagnostic.mkdir(mode=0o700)
    args = [
        runtime.interpreter,
        "-I",
        "-B",
        "-S",
        str(bundle / "bootstrap.py"),
        runtime.manifest_sha256,
        str(probe),
        str(diagnostic),
    ]
    result = subprocess.run(
        args,
        capture_output=True,
        timeout=10,
        env={"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"},
        cwd="/",
    )
    assert result.returncode == 0, result.stderr.decode()
    receipt = diagnostic / "helper-diagnostic.json"
    assert json.loads(receipt.read_bytes()) == {
        "stage": "helper",
        "outcome": "returned",
        "exception_type": None,
    }
    receipt.unlink()
    probe.write_text("raise TypeError('synthetic private error payload')\n")
    result = subprocess.run(args, capture_output=True, timeout=10)
    assert result.returncode != 0 and result.stderr == b""
    assert json.loads(receipt.read_bytes()) == {
        "stage": "helper",
        "outcome": "error",
        "exception_type": "TypeError",
    }
    assert receipt.stat().st_mode & 0o777 == 0o600
    assert receipt.stat().st_size <= 512
    receipt.unlink()
    changed = bundle / "lib/typing_extensions.py"
    changed.write_bytes(changed.read_bytes() + b"\n# synthetic tamper\n")
    result = subprocess.run(args, capture_output=True, timeout=10)
    assert result.returncode != 0
    assert json.loads(receipt.read_bytes())["stage"] == "bundle_verify"
    assert json.loads(receipt.read_bytes())["exception_type"] == "AssertionError"
    with pytest.raises(ValueError, match="copy mismatch"):
        PACKAGE_HELPER()


def test_no_worker_preflight_uses_real_handshake_without_runtime(state, monkeypatch):
    directory, lease = state
    lease = lease.model_copy(update={"purpose": "no_worker_preflight"})
    control.durable(directory, "lease.json", control.encode(lease), replace=True)

    class Queue:
        closed = False

        def close(self):
            self.closed = True

        def control(self, changes, maximum, timeout):
            assert changes and maximum == 0
            return []

    queue = Queue()
    monkeypatch.setattr(control.select, "kqueue", lambda: queue, raising=False)
    monkeypatch.setattr(
        control.select, "kevent", lambda *a, **k: object(), raising=False
    )
    for name in ("KQ_FILTER_PROC", "KQ_EV_ADD", "KQ_EV_ONESHOT", "KQ_NOTE_EXIT"):
        monkeypatch.setattr(control.select, name, 1, raising=False)
    monkeypatch.setattr(control, "Runtime", lambda *a: pytest.fail("runtime touched"))
    control.watch(directory)
    assert queue.closed
    assert json.loads(control.read(directory, "ready.json")) == {
        "lease_sha256": control.digest(control.encode(lease)),
        "controller_pid": os.getpid(),
    }
    assert not (directory / "start-consumed.json").exists()


@pytest.mark.skipif(not hasattr(control.select, "kqueue"), reason="kqueue unavailable")
def test_no_worker_registration_uses_real_kqueue_without_context_protocol(
    state, monkeypatch
):
    directory, lease = state
    lease = lease.model_copy(update={"purpose": "no_worker_preflight"})
    control.durable(directory, "lease.json", control.encode(lease), replace=True)
    monkeypatch.setattr(control, "Runtime", lambda *a: pytest.fail("runtime touched"))
    control.watch(directory)
    assert json.loads(control.read(directory, "ready.json"))["lease_sha256"] == (
        control.digest(control.encode(lease))
    )


def test_launchd_pins_production_arguments(state, tmp_path, monkeypatch):
    directory, lease = state
    bundle = tmp_path / "bundle"
    bundle.mkdir(mode=0o700)
    control.durable(bundle, "bootstrap.py", control.BOOTSTRAP)
    interpreter = Path(sys._base_executable).resolve()
    runtime = control.HelperRuntime(
        interpreter=str(interpreter),
        interpreter_sha256=control.digest(interpreter.read_bytes()),
        bundle=str(bundle),
        manifest_sha256="a" * 64,
        bootstrap_sha256=control.digest(control.BOOTSTRAP),
    )
    lease = lease.model_copy(update={"helper_runtime": runtime})
    calls = []
    monkeypatch.setattr(control.subprocess, "run", lambda *a, **k: calls.append(a))
    control.launchd(directory, lease)
    job = plistlib.loads(control.read(directory, "job.plist"))
    assert job["ProgramArguments"] == [
        str(interpreter),
        "-I",
        "-B",
        "-S",
        str(bundle / "bootstrap.py"),
        "a" * 64,
        str(directory / "helper.py"),
        "watch",
        str(directory),
    ]
    assert job["WorkingDirectory"] == "/"
    assert job["EnvironmentVariables"] == {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}
    assert len(calls) == 1
