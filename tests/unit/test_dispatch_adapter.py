"""Hand-authored synthetic task/state/environment; no runtime or transport evidence.

The fake port writes only deterministic fixtures in pytest temporary directories.
Its start/recover/finalize never invoke the controller lifecycle or a subprocess.
Read-only existing receipt validation is exercised on those synthetic files.
"""

import json
import plistlib
import threading
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from model_learner.benchmark import _dispatch_contract as c
from model_learner.benchmark import supervision as control
from model_learner.benchmark._dispatch_adapter import Adapter, ExistingController
from model_learner.domain.models import Task

NOW = 1_000_000_000
WALL = datetime(2026, 1, 1, tzinfo=UTC)
DATA = b"public synthetic adapter output\n"


class Clock:
    now = NOW

    def __call__(self):
        return self.now


class FakeController:
    def __init__(self, clock):
        self.clock = clock
        self.calls = []
        self.start_error = False
        self.recovery_error = False
        self.uncertain = False
        self.delay_start = 1
        self.on_start = None

    def start(self, directory, *, mode, timeout_seconds):
        self.calls.append(("start", directory))
        directory.mkdir(mode=0o700)
        value = control.Lease(
            run_id=UUID(int=10),
            owner=UUID(int=11),
            container_id="a" * 64,
            worker_mode=mode,
            input_sha256=control.digest(control.INPUT),
            helper_sha256="b" * 64,
            controller_pid=123,
            prepared_at=WALL,
            prepared_monotonic_ns=self.clock.now,
            deadline_monotonic_ns=self.clock.now + int(timeout_seconds * 1e9),
        )
        control.durable(directory, "lease.json", control.encode(value))
        if self.on_start:
            self.on_start()
        self.clock.now += self.delay_start
        if self.start_error:
            raise RuntimeError("synthetic diagnostic /private/mock not for reply")
        return value

    def load(self, directory):
        self.calls.append(("load", directory))
        return control.load(directory)

    def has_receipt(self, directory):
        self.calls.append(("has_receipt", directory))
        return ExistingController.has_receipt(directory)

    def validate_receipt(self, directory):
        self.calls.append(("validate_receipt", directory))
        return control.validate_receipt(directory)

    def read(self, directory, name):
        self.calls.append(("read", directory))
        return control.read(directory, name)

    def stopped(self, directory, data=DATA, *, confirmed=True):
        value = control.load(directory)
        result = control.Receipt(
            lease_sha256=control.digest(control.encode(value)),
            run_id=value.run_id,
            target=value.target,
            configuration=value.configuration,
            container_id=value.container_id,
            stop_reason="completed",
            prepared_at=WALL,
            stopped_at=WALL + timedelta(seconds=1),
            prepared_monotonic_ns=value.prepared_monotonic_ns,
            stopped_monotonic_ns=self.clock.now,
            input_sha256=value.input_sha256,
            input_observed=True,
            output_sha256=control.digest(data) if data is not None else None,
            output_bytes=len(data) if data is not None else None,
            observed_guest_pids=(2, 3),
            container_absent=confirmed,
            descendants_absent=confirmed,
            output_stable_after_stop=confirmed,
            cleanup_confirmed=confirmed,
        )
        if data is not None:
            control.durable(
                directory,
                "output.bin",
                data,
                replace=(directory / "output.bin").exists(),
            )
        control.durable(
            directory,
            "receipt.json",
            control.encode(result),
            replace=(directory / "receipt.json").exists(),
        )
        return result

    def recover(self, directory):
        self.calls.append(("recover", directory))
        if self.recovery_error:
            raise RuntimeError("synthetic cleanup diagnostic")
        return self.stopped(directory, confirmed=not self.uncertain)

    def finalize(self, directory, retained):
        self.calls.append(("finalize", directory))
        retained.mkdir(mode=0o700)
        for name in ("lease.json", "receipt.json", "output.bin"):
            if (directory / name).exists():
                control.durable(retained, name, control.read(directory, name))
        return control.validate_receipt(retained)


@pytest.fixture
def env(tmp_path):
    clock = Clock()
    port = FakeController(clock)
    selected = Task(
        task_id=UUID(int=1),
        description="public synthetic adapter task",
        acceptance_spec=control.TARGET.model_copy(deep=True),
        created_at=WALL,
    )
    task = c.TaskBinding.from_task(selected, checker_sha256="c" * 64)
    identities = iter(UUID(int=n) for n in range(1000, 4000))
    root = tmp_path / "adapter"
    adapter = Adapter(
        task, root, port=port, clock=clock, identity=lambda: next(identities)
    )
    return adapter, task, port, clock, root


def request(env, method="start", handle=None, **arguments):
    adapter, task, _, clock, _ = env
    permit = adapter.issue_call(expires_ns=clock.now + 10_000_000_000)
    value = {"method": method, "arguments": arguments}
    if handle is not None:
        value["handle"] = str(handle)
    return adapter.dispatch(task, permit, json.dumps(value).encode())


def started(env):
    result = request(env)
    assert isinstance(result, c.Completed) and result.phase is c.Phase.ACTIVE
    return result.handle


def stopped(env, handle, data=DATA):
    _, _, port, clock, root = env
    clock.now += c.POLL_NS
    port.stopped(root / "controller", data)
    result = request(env, "status", handle.value)
    assert isinstance(result, c.Completed) and result.phase is c.Phase.STOPPED
    return result


def count(port, operation):
    return sum(name == operation for name, _ in port.calls)


def test_valid_mapping_status_retention_output(env):
    adapter, _, port, clock, root = env
    handle = started(env)
    assert request(env, "status", handle.value) == c.Completed(c.Phase.ACTIVE, handle)
    result = stopped(env, handle)
    assert result.reference != handle
    assert adapter.retain() == result
    assert count(port, "finalize") == 1
    assert adapter.retain() == result
    assert count(port, "finalize") == 1
    output = request(env, "output", handle.value)
    assert output == c.Completed(c.Phase.CLOSED, handle, result.reference, DATA)
    assert len(output.json()) <= c.MAX_REPLY_BYTES
    assert ("read", root / "retained") in port.calls
    assert adapter.cleanup_confirmed
    assert count(port, "start") == 1 and count(port, "recover") == 0
    assert clock.now < control.load(root / "retained").deadline_monotonic_ns


def test_rejected_replayed_forged_calls_never_reach_port(env):
    adapter, task, port, clock, _ = env
    permit = adapter.issue_call(expires_ns=clock.now + 10_000_000_000)
    assert adapter.dispatch(task, permit, b'{"method":"shell"}') == c.Rejected(
        c.Error.INVALID_PAYLOAD
    )
    assert port.calls == []
    assert adapter.dispatch(task, permit, b'{"method":"start"}') == c.Rejected(
        c.Error.DUPLICATE_CALL
    )
    assert port.calls == []
    handle = started(env)
    before = list(port.calls)
    assert request(env, "start") == c.Rejected(c.Error.INVALID_TRANSITION)
    assert request(env, "status", UUID(int=10)) == c.Rejected(c.Error.HANDLE_MISMATCH)
    fresh = adapter.issue_call(expires_ns=clock.now + 10_000_000_000)
    assert adapter.dispatch(None, fresh, b'{"method":"start"}') == c.Rejected(
        c.Error.INVALID_TASK
    )
    assert request(env, "output", handle.value) == c.Rejected(
        c.Error.INVALID_TRANSITION
    )
    assert port.calls == before


@pytest.mark.parametrize(
    "uncertain,error", [(False, False), (True, False), (False, True)]
)
def test_ambiguous_start_cleanup_only_once_and_state_retained(env, uncertain, error):
    adapter, _, port, _, root = env
    port.start_error, port.uncertain, port.recovery_error = True, uncertain, error
    result = request(env)
    assert result == c.Rejected(c.Error.UNKNOWN_COMPLETION)
    assert result.json() == b'{"error": "unknown_completion"}'
    assert adapter.phase is c.Phase.INDETERMINATE
    assert adapter.cleanup_confirmed is (not uncertain and not error)
    assert (root / "controller" / "lease.json").exists()
    assert adapter.retain() == c.Rejected(c.Error.INVALID_TRANSITION)
    adapter.cancel()
    adapter.cancel()
    assert request(env) == c.Rejected(c.Error.INVALID_TRANSITION)
    assert count(port, "start") == count(port, "recover") == 1
    assert count(port, "finalize") == 0


def test_explicit_recovery_and_output(env):
    adapter, _, port, _, _ = env
    handle = started(env)
    result = request(env, "recover", handle.value)
    assert isinstance(result, c.Completed) and result.phase is c.Phase.STOPPED
    assert count(port, "recover") == 1
    before = list(port.calls)
    assert request(env, "recover", handle.value) == c.Rejected(
        c.Error.INVALID_TRANSITION
    )
    assert port.calls == before
    assert request(env, "output", handle.value).data == DATA
    assert adapter.cleanup_confirmed


def test_cancellation_before_start_has_no_port_calls(env):
    adapter, _, port, _, _ = env
    assert adapter.cancel() == c.Completed(c.Phase.CLOSED)
    assert request(env) == c.Rejected(c.Error.INVALID_TRANSITION)
    assert port.calls == []


def test_cancel_active_recovers_exact_owned_directory(env):
    adapter, _, port, _, root = env
    handle = started(env)
    assert adapter.cancel() == c.Completed(c.Phase.CLOSED)
    assert count(port, "recover") == 1
    assert ("recover", root / "controller") in port.calls
    before = list(port.calls)
    assert request(env, "status", handle.value) == c.Rejected(c.Error.STALE_HANDLE)
    assert adapter.cancel() == c.Completed(c.Phase.CLOSED)
    assert port.calls == before


def test_cancellation_during_start_waits_then_cleans_without_restart(env):
    adapter, _, port, _, root = env
    entered, release, cancelling = (
        threading.Event(),
        threading.Event(),
        threading.Event(),
    )
    replies = []

    def pause():
        entered.set()
        assert release.wait(3)

    def cancel():
        cancelling.set()
        replies.append(adapter.cancel())

    port.on_start = pause
    worker = threading.Thread(target=lambda: replies.append(request(env)))
    worker.start()
    assert entered.wait(3)
    canceller = threading.Thread(target=cancel)
    canceller.start()
    assert cancelling.wait(3)
    assert adapter._cancelled.wait(3)
    assert count(port, "recover") == 0
    release.set()
    worker.join(3)
    canceller.join(3)
    assert not worker.is_alive() and not canceller.is_alive()
    assert c.Rejected(c.Error.UNKNOWN_COMPLETION) in replies
    assert count(port, "start") == count(port, "recover") == 1
    assert adapter.cleanup_confirmed and (root / "controller").exists()


def test_host_deadline_cleanup_separate_from_rejected_proposals(env):
    adapter, _, port, clock, root = env
    handle = started(env)
    clock.now = control.load(root / "controller").deadline_monotonic_ns
    before = list(port.calls)
    assert request(env, "status", handle.value) == c.Rejected(c.Error.TIMEOUT)
    assert port.calls == before
    assert adapter.expire() == c.Rejected(c.Error.TIMEOUT)
    assert adapter.cleanup_confirmed and count(port, "recover") == 1
    assert adapter.expire() is None
    assert count(port, "start") == 1


def test_start_completion_timeout_recovers_once(env):
    adapter, _, port, _, _ = env
    port.delay_start = 10_000_000_000
    assert request(env) == c.Rejected(c.Error.TIMEOUT)
    assert adapter.phase is c.Phase.INDETERMINATE
    assert adapter.cleanup_confirmed
    assert count(port, "start") == count(port, "recover") == 1


@pytest.mark.parametrize(
    "mutation", ["changed", "oversized", "missing", "receipt", "unbound"]
)
def test_output_revalidated_and_bound_to_original_receipt(env, mutation):
    adapter, _, port, _, root = env
    handle = started(env)
    stopped(env, handle)
    directory = root / "controller"
    if mutation == "changed":
        control.durable(
            directory, "output.bin", b"changed synthetic bytes", replace=True
        )
    elif mutation == "oversized":
        control.durable(
            directory, "output.bin", b"x" * (control.MAX_HANDOFF + 1), replace=True
        )
    elif mutation == "missing":
        (directory / "output.bin").unlink()
    elif mutation == "receipt":
        port.stopped(directory, b"different valid synthetic output")
    else:
        adapter._paths.pop(adapter._artifact.value)
    result = request(env, "output", handle.value)
    assert result == c.Rejected(c.Error.CONTROLLER_FAILURE)
    assert len(result.json()) < c.MAX_REPLY_BYTES
    assert adapter.phase is c.Phase.INDETERMINATE
    assert directory.exists() and count(port, "finalize") == 0


def test_no_output_is_not_failure_or_empty_output(env):
    _, _, port, _, _ = env
    handle = started(env)
    stopped(env, handle, None)
    before = list(port.calls)
    assert request(env, "output", handle.value) == c.Rejected(c.Error.NO_OUTPUT)
    assert port.calls == before


@pytest.mark.parametrize("data", [b"", b"x" * control.MAX_HANDOFF])
def test_output_bounds(env, data):
    handle = started(env)
    stopped(env, handle, data)
    assert request(env, "output", handle.value).data == data


def test_replaced_lease_never_authorizes_recovery(env):
    adapter, _, port, _, root = env
    handle = started(env)
    directory = root / "controller"
    value = control.load(directory).model_copy(update={"owner": UUID(int=99)})
    control.durable(directory, "lease.json", control.encode(value), replace=True)
    assert request(env, "status", handle.value) == c.Rejected(
        c.Error.CONTROLLER_FAILURE
    )
    assert count(port, "recover") == 0
    assert not adapter.cleanup_confirmed
    assert directory.exists()


def test_uncertain_receipt_retains_state_and_refuses_disposal(env):
    adapter, _, port, clock, root = env
    handle = started(env)
    port.uncertain = True
    clock.now += c.POLL_NS
    port.stopped(root / "controller", confirmed=False)
    assert request(env, "status", handle.value) == c.Rejected(
        c.Error.CONTROLLER_FAILURE
    )
    assert not adapter.cleanup_confirmed
    assert adapter.retain() == c.Rejected(c.Error.INVALID_TRANSITION)
    assert (root / "controller" / "receipt.json").exists()
    assert count(port, "recover") == 1 and count(port, "finalize") == 0


def test_port_failures_return_safe_errors_and_preserve_state(env, monkeypatch):
    adapter, _, port, _, root = env
    handle = started(env)

    def fail(directory):
        raise RuntimeError("synthetic exception /private/mock credential=not-real")

    monkeypatch.setattr(port, "has_receipt", fail)
    assert (
        request(env, "status", handle.value).json()
        == b'{"error": "controller_failure"}'
    )
    assert adapter.cleanup_confirmed and (root / "controller").exists()
    assert count(port, "recover") == 1


def test_finalize_failure_preserves_evidence_and_revokes(env, monkeypatch):
    adapter, _, port, _, root = env
    handle = started(env)
    stopped(env, handle)

    def fail(directory, retained):
        raise RuntimeError("synthetic disposal diagnostic")

    monkeypatch.setattr(port, "finalize", fail)
    assert adapter.retain() == c.Rejected(c.Error.CONTROLLER_FAILURE)
    assert (root / "controller" / "receipt.json").exists()
    assert request(env, "output", handle.value) == c.Rejected(c.Error.STALE_HANDLE)


def test_generated_launch_environment_only_allowlist_no_parent_values(
    tmp_path, monkeypatch
):
    # Replace the entire environment with public synthetic values; never inspect
    # or print the user's parent environment or launch an actual child/job.
    monkeypatch.setattr(
        control.os,
        "environ",
        {"MODEL_LEARNER_PUBLIC_SENTINEL": "public-synthetic-value"},
    )
    directory = tmp_path / "job"
    directory.mkdir(mode=0o700)
    bundle = tmp_path / "bundle"
    bundle.mkdir(mode=0o700)
    interpreter = tmp_path / "synthetic-interpreter"
    interpreter.write_bytes(b"public fake interpreter; never executable")
    bootstrap = b"public synthetic bootstrap; never executed"
    control.durable(bundle, "bootstrap.py", bootstrap)
    runtime = control.HelperRuntime(
        interpreter=str(interpreter),
        interpreter_sha256=control.digest(interpreter.read_bytes()),
        bundle=str(bundle),
        manifest_sha256="a" * 64,
        bootstrap_sha256=control.digest(bootstrap),
    )
    value = control.Lease(
        run_id=UUID(int=20),
        owner=UUID(int=21),
        container_id="b" * 64,
        worker_mode="normal",
        input_sha256=control.digest(control.INPUT),
        helper_sha256="c" * 64,
        controller_pid=123,
        prepared_at=WALL,
        prepared_monotonic_ns=NOW,
        deadline_monotonic_ns=NOW + 5_000_000_000,
        helper_runtime=runtime,
    )
    boundaries = []

    def blocked_run(args, **kwargs):
        boundaries.append((args, kwargs))
        assert args[:2] == ["/bin/launchctl", "bootstrap"]
        assert Path(args[-1]) == directory / "job.plist"

    monkeypatch.setattr(control.subprocess, "run", blocked_run)
    control.launchd(directory, value)
    job = plistlib.loads(control.read(directory, "job.plist"))
    assert job["EnvironmentVariables"] == {"PATH": "/usr/bin:/bin:/usr/sbin:/sbin"}
    assert "MODEL_LEARNER_PUBLIC_SENTINEL" not in job["EnvironmentVariables"]
    assert "public-synthetic-value" not in str(job)
    assert len(boundaries) == 1
    assert boundaries[0][1]["timeout"] == 10


def test_poll_cadence_rejection_has_no_port_calls(env):
    _, _, port, _, _ = env
    handle = started(env)
    assert request(env, "status", handle.value).phase is c.Phase.ACTIVE
    before = list(port.calls)
    assert request(env, "status", handle.value) == c.Rejected(c.Error.POLL_TOO_SOON)
    assert port.calls == before


def test_output_race_after_validated_receipt_is_rejected(env, monkeypatch):
    adapter, _, port, _, root = env
    handle = started(env)
    stopped(env, handle)

    def changed_read(directory, name):
        assert directory == root / "controller" and name == "output.bin"
        return b"same source changed after validation"

    monkeypatch.setattr(port, "read", changed_read)
    assert request(env, "output", handle.value) == c.Rejected(
        c.Error.CONTROLLER_FAILURE
    )
    assert adapter.phase is c.Phase.INDETERMINATE
    assert (root / "controller" / "receipt.json").exists()


def test_returned_lease_must_match_owned_state_before_handle_binding(env, monkeypatch):
    adapter, _, port, _, root = env
    original = port.start

    def mismatched(directory, **kwargs):
        value = original(directory, **kwargs)
        return value.model_copy(update={"owner": UUID(int=99)})

    monkeypatch.setattr(port, "start", mismatched)
    assert request(env) == c.Rejected(c.Error.UNKNOWN_COMPLETION)
    assert not adapter.cleanup_confirmed
    assert count(port, "recover") == 0
    assert (root / "controller" / "lease.json").exists()
    assert request(env) == c.Rejected(c.Error.INVALID_TRANSITION)


def test_root_is_exclusive_private_and_not_model_supplied(env):
    adapter, task, port, clock, root = env
    assert root.stat().st_mode & 0o777 == 0o700
    with pytest.raises(FileExistsError):
        Adapter(task, root, port=port, clock=clock)
    permit = adapter.issue_call(expires_ns=clock.now + 1_000_000_000)
    assert adapter.dispatch(
        task, permit, b'{"method":"start","path":"/synthetic/path"}'
    ) == c.Rejected(c.Error.INVALID_PAYLOAD)
    assert port.calls == []


def test_no_existing_controller_lifecycle_reached(env, monkeypatch):
    hits = []

    def forbidden(*args, **kwargs):
        hits.append(True)
        raise AssertionError("real lifecycle boundary reached")

    for name in ("start", "recover", "finalize", "launchd", "watch", "Runtime"):
        monkeypatch.setattr(control, name, forbidden)
    handle = started(env)
    stopped(env, handle)
    assert env[0].retain().phase is c.Phase.STOPPED
    assert request(env, "output", handle.value).data == DATA
    assert hits == []
