"""Synthetic, hand-authored contract fixtures; no sessions or runtime evidence.

All UUIDs, clocks, checksums and task text below are deterministic test values.
No fixture is an Observation, Verification, AdvisoryInput or transport acceptance.
"""

import base64
import json
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from uuid import UUID

import pytest

from model_learner.benchmark import _dispatch_contract as c
from model_learner.benchmark import supervision
from model_learner.domain.models import AcceptanceSpec, Task

NOW = 1_000_000_000
WALL = datetime(2026, 1, 1, tzinfo=UTC)
HANDLE = c.LeaseHandle(UUID(int=40))
RECOVERY = c.ArtifactReference(UUID(int=41))
ARTIFACT = c.ArtifactReference(UUID(int=42))
DATA = b"public synthetic contract output\n"


def task():
    return Task(
        task_id=UUID(int=1),
        description="public synthetic contract task",
        acceptance_spec=supervision.TARGET.model_copy(deep=True),
        created_at=WALL,
    )


@pytest.fixture
def context():
    binding = c.TaskBinding.from_task(task(), checker_sha256="a" * 64)
    return binding, c.Admission(binding)


def call(state, number, now=NOW, duration=10_000_000_000):
    permit = state.issue_call(
        UUID(int=100 + number), now_ns=now, expires_ns=now + duration
    )
    assert isinstance(permit, c.HostCall)
    return permit


def payload(method="start", *, handle=None, **arguments):
    value = {"method": method, "arguments": arguments}
    if handle is not None:
        value["handle"] = str(handle)
    return json.dumps(value).encode()


def admit(context, number, method="start", now=NOW, handle=None, **arguments):
    binding, state = context
    return state.admit(
        binding,
        call(state, number, now),
        payload(method, handle=handle, **arguments),
        now_ns=now,
    )


def lease(mode="normal", seconds=5):
    return supervision.Lease(
        run_id=UUID(int=2),
        owner=UUID(int=3),
        container_id="b" * 64,
        worker_mode=mode,
        input_sha256=supervision.digest(supervision.INPUT),
        helper_sha256="c" * 64,
        controller_pid=123,
        prepared_at=WALL,
        prepared_monotonic_ns=NOW,
        deadline_monotonic_ns=NOW + int(seconds * 1e9),
    )


def start(context, *, mode="normal", seconds=5):
    operation = admit(context, 1, mode=mode, timeout_seconds=seconds)
    assert isinstance(operation, c.Admitted)
    value = lease(mode, seconds)
    result = context[1].complete(
        operation,
        c.Started(value, HANDLE, RECOVERY),
        now_ns=NOW + 1,
    )
    assert result == c.Completed(c.Phase.ACTIVE, HANDLE)
    return value


def receipt(value, data=DATA):
    return supervision.Receipt(
        lease_sha256=supervision.digest(supervision.encode(value)),
        run_id=value.run_id,
        target=value.target,
        configuration=value.configuration,
        container_id=value.container_id,
        stop_reason="completed",
        prepared_at=value.prepared_at,
        stopped_at=WALL + timedelta(seconds=1),
        prepared_monotonic_ns=NOW,
        stopped_monotonic_ns=NOW + c.POLL_NS,
        input_sha256=value.input_sha256,
        input_observed=True,
        output_sha256=supervision.digest(data) if data is not None else None,
        output_bytes=len(data) if data is not None else None,
        observed_guest_pids=(2, 3),
        container_absent=True,
        descendants_absent=True,
        output_stable_after_stop=True,
        cleanup_confirmed=True,
    )


def stop(context, value, data=DATA, *, now=NOW + c.POLL_NS):
    operation = admit(context, 2, "status", now, HANDLE.value)
    result = context[1].complete(
        operation,
        c.Stopped(receipt(value, data), ARTIFACT if data is not None else None),
        now_ns=now + 1,
    )
    assert result == c.Completed(
        c.Phase.STOPPED, HANDLE, ARTIFACT if data is not None else None
    )


def test_frozen_host_snapshot(context):
    selected = task()
    binding = c.TaskBinding.from_task(selected, checker_sha256="a" * 64)
    original = binding.task_sha256
    selected.description = "changed synthetic task"
    assert binding.task_sha256 == original
    assert c.TaskBinding.from_task(selected, checker_sha256="a" * 64) != binding
    with pytest.raises(FrozenInstanceError):
        binding.task_id = UUID(int=99)


@pytest.mark.parametrize("value,checker", [(None, "a" * 64), (task(), "bad")])
def test_invalid_task_factory(value, checker):
    assert c.TaskBinding.from_task(value, checker_sha256=checker) == c.Rejected(
        c.Error.INVALID_TASK
    )


def test_acceptance_cannot_be_replaced():
    selected = task()
    selected.acceptance_spec = AcceptanceSpec(identifier="other", version="1")
    assert c.TaskBinding.from_task(selected, checker_sha256="a" * 64) == c.Rejected(
        c.Error.INVALID_TASK
    )


@pytest.mark.parametrize("mode,seconds", [("normal", 0.5), ("live", 30)])
def test_valid_start_status_output(context, mode, seconds):
    value = start(context, mode=mode, seconds=seconds)
    running = admit(context, 3, "status", NOW + 2, HANDLE.value)
    assert running.deadline_ns <= value.deadline_monotonic_ns
    assert running.deadline_ns <= running.admitted_ns + c.COMMAND_NS
    assert (
        context[1].complete(running, c.Running(), now_ns=NOW + 3).phase
        is c.Phase.ACTIVE
    )
    stop(context, value, now=NOW + 2 * c.POLL_NS)
    output = admit(context, 4, "output", NOW + 2 * c.POLL_NS + 2, HANDLE.value)
    assert output.reference is ARTIFACT
    assert context[1].complete(
        output, c.Output(DATA), now_ns=NOW + 2 * c.POLL_NS + 3
    ) == c.Completed(c.Phase.CLOSED, HANDLE, ARTIFACT, DATA)
    assert admit(
        context, 5, "status", NOW + 2 * c.POLL_NS + 4, HANDLE.value
    ) == c.Rejected(c.Error.STALE_HANDLE)


@pytest.mark.parametrize(
    "identity",
    [
        None,
        UUID(int=1),
        replace(c.TaskBinding.from_task(task(), checker_sha256="a" * 64)),
    ],
)
def test_exact_task_capability_required(context, identity):
    binding, state = context
    assert state.admit(identity, call(state, 1), payload(), now_ns=NOW) == c.Rejected(
        c.Error.INVALID_TASK
    )
    assert state.phase is c.Phase.NEW


def test_host_call_identity_and_replay(context):
    binding, state = context
    permit = call(state, 1)
    assert state.issue_call(permit.value, now_ns=NOW, expires_ns=NOW + 1) == c.Rejected(
        c.Error.DUPLICATE_CALL
    )
    assert state.admit(binding, replace(permit), payload(), now_ns=NOW) == c.Rejected(
        c.Error.INVALID_CALL
    )
    assert isinstance(state.admit(binding, permit, payload(), now_ns=NOW), c.Admitted)
    assert state.admit(binding, permit, payload(), now_ns=NOW) == c.Rejected(
        c.Error.DUPLICATE_CALL
    )
    assert admit(context, 2) == c.Rejected(c.Error.INVALID_TRANSITION)


@pytest.mark.parametrize("handle", [None, UUID(int=2), UUID(int=3), UUID(int=77)])
def test_raw_missing_and_forged_handles(context, handle):
    start(context)
    assert admit(context, 2, "status", NOW + 2, handle) == c.Rejected(
        c.Error.HANDLE_MISMATCH
    )


@pytest.mark.parametrize("method", ["status", "output", "recover"])
def test_no_operation_before_lease(context, method):
    assert admit(context, 1, method, handle=HANDLE.value) == c.Rejected(
        c.Error.MISSING_LEASE
    )


def test_start_and_output_order(context):
    start(context)
    assert admit(context, 2, now=NOW + 2) == c.Rejected(c.Error.INVALID_TRANSITION)
    assert admit(context, 3, "output", NOW + 3, HANDLE.value) == c.Rejected(
        c.Error.INVALID_TRANSITION
    )
    context[1].revoke()
    assert admit(context, 4, "recover", NOW + 4, HANDLE.value) == c.Rejected(
        c.Error.STALE_HANDLE
    )


@pytest.mark.parametrize(
    "method",
    [
        "native",
        "shell",
        "read_file",
        "network",
        "docker",
        "credentials",
        "auth",
        "endpoint",
        "finalize",
        "tools.call",
        {"method": "start"},
        ["start"],
    ],
)
def test_positive_operation_enum(context, method):
    binding, state = context
    result = state.admit(binding, call(state, 1), payload(method), now_ns=NOW)
    assert result == c.Rejected(c.Error.INVALID_PAYLOAD)
    assert state.phase is c.Phase.NEW


@pytest.mark.parametrize(
    "field",
    [
        "task_id",
        "lease_id",
        "call_id",
        "correlation",
        "target",
        "checker",
        "budget",
        "path",
        "command",
        "docker_args",
        "url",
        "credentials",
        "auth",
        "endpoint",
        "tools",
        "deferred",
    ],
)
def test_unknown_fields_are_rejected(context, field):
    binding, state = context
    proposed = {"method": "start", field: "synthetic-untrusted-value"}
    assert state.admit(
        binding, call(state, 1), json.dumps(proposed).encode(), now_ns=NOW
    ) == c.Rejected(c.Error.INVALID_PAYLOAD)
    assert state.admit(
        binding,
        call(state, 2),
        payload(**{field: "synthetic-untrusted-value"}),
        now_ns=NOW,
    ) == c.Rejected(c.Error.INVALID_PAYLOAD)


@pytest.mark.parametrize(
    "raw",
    [
        b"{",
        b"[]",
        b"null",
        b"\xff",
        b'{"method":"start","method":"status"}',
        b'{"method":"start","arguments":{"mode":"normal","mode":"live"}}',
        b'{"method":"start","arguments":null}',
        b'{"method":"start","handle":true}',
        b'{"method":"start","arguments":{"timeout_seconds":NaN}}',
        "start",
        None,
    ],
)
def test_malformed_requests(context, raw):
    binding, state = context
    assert state.admit(binding, call(state, 1), raw, now_ns=NOW) == c.Rejected(
        c.Error.INVALID_PAYLOAD
    )


@pytest.mark.parametrize(
    "args",
    [
        {"mode": "normal\n"},
        {"mode": 1},
        {"timeout_seconds": True},
        {"timeout_seconds": "5"},
        {"timeout_seconds": 0.49},
        {"timeout_seconds": 30.01},
        {"timeout_seconds": float("inf")},
    ],
)
def test_argument_types_and_bounds(context, args):
    binding, state = context
    assert state.admit(
        binding, call(state, 1), payload(**args), now_ns=NOW
    ) == c.Rejected(c.Error.INVALID_PAYLOAD)


def test_request_byte_boundary_and_consumed_invalid_call(context):
    binding, state = context
    raw = payload()
    raw += b" " * (c.MAX_REQUEST_BYTES - len(raw))
    permit = call(state, 1)
    assert state.admit(binding, permit, raw + b" ", now_ns=NOW) == c.Rejected(
        c.Error.PAYLOAD_LIMIT
    )
    assert state.admit(binding, permit, raw, now_ns=NOW) == c.Rejected(
        c.Error.DUPLICATE_CALL
    )
    assert isinstance(state.admit(binding, call(state, 2), raw, now_ns=NOW), c.Admitted)


@pytest.mark.parametrize(
    "reason",
    [
        c.Error.TIMEOUT,
        c.Error.UNKNOWN_COMPLETION,
        c.Error.CONTROLLER_FAILURE,
        "synthetic private exception /path",
    ],
)
def test_uncertain_start_is_never_replayed(context, reason):
    operation = admit(context, 1)
    result = context[1].complete(operation, c.Failed(reason), now_ns=NOW + 1)
    assert result == c.Rejected(
        reason if type(reason) is c.Error else c.Error.INVALID_RESULT
    )
    assert context[1].phase is c.Phase.INDETERMINATE
    assert admit(context, 2, now=NOW + 2) == c.Rejected(c.Error.INVALID_TRANSITION)
    assert admit(context, 3, "recover", NOW + 3, HANDLE.value) == c.Rejected(
        c.Error.MISSING_LEASE
    )
    assert context[1].complete(
        operation, c.Started(lease(), HANDLE, RECOVERY), now_ns=NOW + 4
    ) == c.Rejected(c.Error.INVALID_CALL)


def test_completion_deadline_and_forged_completion(context):
    operation = admit(context, 1)
    state = context[1]
    assert state.complete(
        replace(operation), c.Started(lease(), HANDLE, RECOVERY), now_ns=NOW + 1
    ) == c.Rejected(c.Error.INVALID_CALL)
    assert state.complete(
        operation, c.Started(lease(), HANDLE, RECOVERY), now_ns=operation.deadline_ns
    ) == c.Rejected(c.Error.TIMEOUT)
    assert state.phase is c.Phase.INDETERMINATE


def test_poll_cadence_deadline_and_cleanup_recovery(context):
    value = start(context)
    first = admit(context, 2, "status", NOW + 2, HANDLE.value)
    context[1].complete(first, c.Running(), now_ns=NOW + 3)
    assert admit(context, 3, "status", NOW + 4, HANDLE.value) == c.Rejected(
        c.Error.POLL_TOO_SOON
    )
    assert admit(
        context, 4, "status", value.deadline_monotonic_ns, HANDLE.value
    ) == c.Rejected(c.Error.TIMEOUT)
    recovery = admit(
        context, 5, "recover", value.deadline_monotonic_ns + 1, HANDLE.value
    )
    assert recovery.reference is RECOVERY
    assert recovery.deadline_ns == recovery.admitted_ns + c.COMMAND_NS
    assert (
        context[1]
        .complete(
            recovery,
            c.Stopped(receipt(value), ARTIFACT),
            now_ns=value.deadline_monotonic_ns + 2,
        )
        .phase
        is c.Phase.STOPPED
    )
    assert admit(
        context, 6, "recover", value.deadline_monotonic_ns + 3, HANDLE.value
    ) == c.Rejected(c.Error.INVALID_TRANSITION)


@pytest.mark.parametrize(
    "change",
    [
        {"run_id": UUID(int=80)},
        {"lease_sha256": "0" * 64},
        {"cleanup_confirmed": False},
        {"container_absent": False},
        {"errors": ("synthetic sensitive exception",)},
        {"output_bytes": c.MAX_HANDOFF + 1},
        {"observed_guest_pids": (2, 2)},
        {"input_observed": False},
        {"prepared_monotonic_ns": NOW - 1},
        {"stopped_monotonic_ns": NOW + 10 * c.POLL_NS},
    ],
)
def test_receipt_binding_failure_is_indeterminate(context, change):
    value = start(context)
    operation = admit(context, 2, "status", NOW + c.POLL_NS, HANDLE.value)
    result = context[1].complete(
        operation,
        c.Stopped(receipt(value).model_copy(update=change), ARTIFACT),
        now_ns=NOW + c.POLL_NS + 1,
    )
    assert result == c.Rejected(c.Error.INVALID_RESULT)
    assert context[1].phase is c.Phase.INDETERMINATE


@pytest.mark.parametrize(
    "result",
    [
        c.Started(lease(), c.LeaseHandle(UUID(int=2)), RECOVERY),
        c.Started(lease(), HANDLE, c.ArtifactReference(HANDLE.value)),
        c.Started(lease().model_copy(update={"worker_mode": "live"}), HANDLE, RECOVERY),
        c.Started(lease().model_copy(update={"container_id": None}), HANDLE, RECOVERY),
        c.Started(
            lease().model_copy(update={"deadline_monotonic_ns": NOW + 1_000_000_000}),
            HANDLE,
            RECOVERY,
        ),
        c.Running(),
        RuntimeError("synthetic private error"),
    ],
)
def test_invalid_start_result(context, result):
    operation = admit(context, 1)
    assert context[1].complete(operation, result, now_ns=NOW + 1) == c.Rejected(
        c.Error.INVALID_RESULT
    )


@pytest.mark.parametrize("data", [b"", b"x" * c.MAX_HANDOFF])
def test_output_boundary(context, data):
    value = start(context)
    stop(context, value, data)
    operation = admit(context, 3, "output", NOW + c.POLL_NS + 2, HANDLE.value)
    assert (
        context[1].complete(operation, c.Output(data), now_ns=NOW + c.POLL_NS + 3).data
        == data
    )


@pytest.mark.parametrize("data", [b"x" * (c.MAX_HANDOFF + 1), b"wrong", "not-bytes"])
def test_output_is_bounded_and_receipt_bound(context, data):
    value = start(context)
    stop(context, value)
    operation = admit(context, 3, "output", NOW + c.POLL_NS + 2, HANDLE.value)
    assert context[1].complete(
        operation, c.Output(data), now_ns=NOW + c.POLL_NS + 3
    ) == c.Rejected(c.Error.INVALID_RESULT)


def test_stopped_without_output(context):
    value = start(context)
    stop(context, value, None)
    assert admit(context, 3, "output", NOW + c.POLL_NS + 2, HANDLE.value) == c.Rejected(
        c.Error.NO_OUTPUT
    )


@pytest.mark.parametrize(
    "now,expires",
    [
        (True, NOW + 1),
        (0, NOW + 1),
        (NOW, True),
        (NOW, NOW),
        (NOW, NOW + c.MAX_LEASE_NS + 1),
    ],
)
def test_host_call_time_bounds(context, now, expires):
    assert context[1].issue_call(
        UUID(int=99), now_ns=now, expires_ns=expires
    ) == c.Rejected(c.Error.INVALID_TIME)


def test_expired_call_and_backwards_time(context):
    binding, state = context
    permit = call(state, 1, duration=1)
    assert state.admit(binding, permit, payload(), now_ns=NOW + 1) == c.Rejected(
        c.Error.TIMEOUT
    )
    assert state.issue_call(
        UUID(int=200), now_ns=NOW, expires_ns=NOW + 1
    ) == c.Rejected(c.Error.INVALID_TIME)


def test_call_cache_bound(context):
    state = context[1]
    for number in range(c.MAX_CALL_IDS):
        call(state, number)
    assert state.issue_call(
        UUID(int=9999), now_ns=NOW, expires_ns=NOW + 1
    ) == c.Rejected(c.Error.CALL_LIMIT)


def test_safe_rejections_never_echo_inputs(context):
    binding, state = context
    raw = payload("synthetic secret /private/example https://invalid.test")
    result = state.admit(binding, call(state, 1), raw, now_ns=NOW)
    assert result.json() == b'{"error": "invalid_payload"}'
    for error in c.Error:
        assert json.loads(c.Rejected(error).json()) == {"error": error.value}


def test_pure_contract_never_calls_controller(context, monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("controller boundary invoked")

    for name in ("start", "watch", "recover", "finalize", "Runtime"):
        monkeypatch.setattr(supervision, name, forbidden)
    value = start(context)
    stop(context, value)
    operation = admit(context, 3, "output", NOW + c.POLL_NS + 2, HANDLE.value)
    context[1].complete(operation, c.Output(DATA), now_ns=NOW + c.POLL_NS + 3)
    assert calls == []


@pytest.mark.parametrize("extra", [0, 1])
def test_serialized_lease_result_bound(context, extra):
    runtime = supervision.HelperRuntime(
        interpreter="synthetic-interpreter",
        interpreter_sha256="a" * 64,
        bundle="",
        manifest_sha256="b" * 64,
        bootstrap_sha256="c" * 64,
    )
    value = lease().model_copy(update={"helper_runtime": runtime})
    padding = c.MAX_STATE - len(supervision.encode(value)) + extra
    runtime = runtime.model_copy(update={"bundle": "x" * padding})
    value = value.model_copy(update={"helper_runtime": runtime})
    assert len(supervision.encode(value)) == c.MAX_STATE + extra
    operation = admit(context, 1)
    result = context[1].complete(
        operation, c.Started(value, HANDLE, RECOVERY), now_ns=NOW + 1
    )
    assert result == (
        c.Rejected(c.Error.INVALID_RESULT)
        if extra
        else c.Completed(c.Phase.ACTIVE, HANDLE)
    )


def test_bounded_safe_reply():
    data = b"\xff" * c.MAX_HANDOFF
    result = c.Completed(c.Phase.CLOSED, HANDLE, ARTIFACT, data)
    encoded = result.json()
    assert type(encoded) is bytes and len(encoded) <= c.MAX_REPLY_BYTES
    value = json.loads(encoded)
    assert set(value) == {"phase", "handle", "artifact", "data_base64"}
    assert base64.b64decode(value["data_base64"]) == data
    assert replace(result, data=data + b"x").json() == c.Rejected(
        c.Error.INVALID_RESULT
    )
    assert replace(result, reference="/synthetic/private/path").json() == c.Rejected(
        c.Error.INVALID_RESULT
    )


def test_recovery_and_rejection_never_call_controller(context, monkeypatch):
    calls = []

    def forbidden(*args, **kwargs):
        calls.append(True)
        raise AssertionError("controller boundary invoked")

    for name in ("start", "watch", "recover", "finalize", "Runtime"):
        monkeypatch.setattr(supervision, name, forbidden)
    value = start(context)
    operation = admit(context, 2, "recover", NOW + c.POLL_NS, HANDLE.value)
    assert operation.reference is RECOVERY
    assert (
        context[1]
        .complete(
            operation, c.Stopped(receipt(value), ARTIFACT), now_ns=NOW + c.POLL_NS + 1
        )
        .phase
        is c.Phase.STOPPED
    )
    assert admit(context, 3, "shell", NOW + c.POLL_NS + 2) == c.Rejected(
        c.Error.INVALID_PAYLOAD
    )
    assert calls == []


@pytest.mark.parametrize("identity", [[], None, "synthetic-forged-id", UUID(int=0)])
def test_wrong_typed_host_identity(context, identity):
    binding, state = context
    assert state.issue_call(identity, now_ns=NOW, expires_ns=NOW + 1) == c.Rejected(
        c.Error.INVALID_CALL
    )
    assert state.admit(
        binding, c.HostCall(identity, NOW + 1), payload(), now_ns=NOW
    ) == c.Rejected(c.Error.INVALID_CALL)


def test_nested_payload_fails_safely(context):
    binding, state = context
    raw = b"[" * 500 + b"0" + b"]" * 500
    assert len(raw) <= c.MAX_REQUEST_BYTES
    assert state.admit(binding, call(state, 1), raw, now_ns=NOW) == c.Rejected(
        c.Error.INVALID_PAYLOAD
    )


def test_completion_clock_failure_consumes_start(context):
    operation = admit(context, 1)
    assert context[1].complete(
        operation, c.Started(lease(), HANDLE, RECOVERY), now_ns=True
    ) == c.Rejected(c.Error.INVALID_TIME)
    assert context[1].phase is c.Phase.INDETERMINATE
    assert admit(context, 2) == c.Rejected(c.Error.INVALID_TRANSITION)


@pytest.mark.parametrize(
    "reference",
    [
        None,
        "/synthetic/path",
        c.ArtifactReference(UUID(int=2)),
        c.ArtifactReference(HANDLE.value),
        RECOVERY,
    ],
)
def test_output_reference_is_opaque_and_unique(context, reference):
    value = start(context)
    operation = admit(context, 2, "status", NOW + c.POLL_NS, HANDLE.value)
    assert context[1].complete(
        operation, c.Stopped(receipt(value), reference), now_ns=NOW + c.POLL_NS + 1
    ) == c.Rejected(c.Error.INVALID_RESULT)
