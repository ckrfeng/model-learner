"""Private synthetic admission state, with no executor, clock, random IDs or I/O.

One trusted owner retains one instance per frozen task; state is in-memory, not a
durable/crash-safe registry. Host-only methods are not model-callable endpoints.
The future adapter owns paths, controller execution and mandatory cleanup even
when admission fails. Opaque references grant no filesystem access here.
"""

from __future__ import annotations

import base64
import json
import threading
from dataclasses import dataclass
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from model_learner.benchmark.supervision import (
    CONFIG,
    INPUT,
    MAX_HANDOFF,
    MAX_STATE,
    TARGET,
    Lease,
    Receipt,
    digest,
    encode,
    unique_json,
)
from model_learner.domain.models import Task

# Private message/cache bounds, not task acceptance or spend/duration budgets.
MAX_REQUEST_BYTES = 1024
# Enough for the existing 1024-byte handoff as base64 plus fixed opaque metadata.
MAX_REPLY_BYTES = 2048
MAX_CALL_IDS = 2048
# Existing controller worker, command and polling bounds (no runtime changes).
MAX_LEASE_NS = 30_000_000_000
COMMAND_NS = 4_000_000_000
POLL_NS = 25_000_000


class Operation(StrEnum):
    START = "start"
    STATUS = "status"
    OUTPUT = "output"
    RECOVER = "recover"


class Phase(StrEnum):
    NEW = "new"
    STARTING = "starting"
    ACTIVE = "active"
    STOPPED = "stopped"
    INDETERMINATE = "indeterminate"
    CLOSED = "closed"


class Error(StrEnum):
    INVALID_TASK = "invalid_task"
    INVALID_CALL = "invalid_call"
    DUPLICATE_CALL = "duplicate_call"
    CALL_LIMIT = "call_limit"
    INVALID_TIME = "invalid_time"
    INVALID_PAYLOAD = "invalid_payload"
    PAYLOAD_LIMIT = "payload_limit"
    INVALID_TRANSITION = "invalid_transition"
    MISSING_LEASE = "missing_lease"
    HANDLE_MISMATCH = "handle_mismatch"
    STALE_HANDLE = "stale_handle"
    POLL_TOO_SOON = "poll_too_soon"
    NO_OUTPUT = "no_output"
    INVALID_RESULT = "invalid_result"
    TIMEOUT = "timeout"
    CONTROLLER_FAILURE = "controller_failure"
    UNKNOWN_COMPLETION = "unknown_completion"


@dataclass(frozen=True)
class Rejected:
    error: Error

    def json(self) -> bytes:
        return json.dumps({"error": self.error.value}).encode()


def _uuid(value: object) -> bool:
    return type(value) is UUID and value.int != 0


def _sha(value: object) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


@dataclass(frozen=True, repr=False)
class TaskBinding:
    task_id: UUID
    task_sha256: str
    checker_sha256: str

    @classmethod
    def from_task(cls, task: Task, *, checker_sha256: str) -> TaskBinding | Rejected:
        """Snapshot the host-selected task, including acceptance/budget/metadata."""
        if not isinstance(task, Task) or not _sha(checker_sha256):
            return Rejected(Error.INVALID_TASK)
        if task.acceptance_spec != TARGET or not _uuid(task.task_id):
            return Rejected(Error.INVALID_TASK)
        try:
            data = json.dumps(
                task.model_dump(mode="json"), sort_keys=True, allow_nan=False
            ).encode()
        except (TypeError, ValueError, RecursionError):
            return Rejected(Error.INVALID_TASK)
        return cls(task.task_id, digest(data), checker_sha256)


@dataclass(frozen=True, repr=False)
class LeaseHandle:
    value: UUID


@dataclass(frozen=True, repr=False)
class ArtifactReference:
    value: UUID


@dataclass(frozen=True, repr=False)
class HostCall:
    value: UUID
    expires_ns: int


class _Arguments(BaseModel):
    model_config = ConfigDict(
        extra="forbid", frozen=True, strict=True, allow_inf_nan=False
    )


class StartArguments(_Arguments):
    mode: Literal["normal", "live"] = "normal"
    timeout_seconds: int | float = Field(default=5, ge=0.5, le=30)


class EmptyArguments(_Arguments):
    pass


class _Request(_Arguments):
    method: Operation
    arguments: dict = Field(default_factory=dict)
    handle: UUID | None = None


@dataclass(frozen=True, repr=False)
class Admitted:
    operation: Operation
    arguments: StartArguments | EmptyArguments
    call: HostCall
    admitted_ns: int
    deadline_ns: int
    handle: LeaseHandle | None
    reference: ArtifactReference | None


# These are trusted adapter-result types, never decoded from model messages.
@dataclass(frozen=True, repr=False)
class Started:
    lease: Lease
    handle: LeaseHandle
    recovery: ArtifactReference


@dataclass(frozen=True)
class Running:
    pass


@dataclass(frozen=True, repr=False)
class Stopped:
    receipt: Receipt
    output: ArtifactReference | None = None


@dataclass(frozen=True, repr=False)
class Output:
    data: bytes


@dataclass(frozen=True)
class Failed:
    reason: Error  # only TIMEOUT, CONTROLLER_FAILURE or UNKNOWN_COMPLETION


@dataclass(frozen=True, repr=False)
class Completed:
    phase: Phase
    handle: LeaseHandle | None = None
    reference: ArtifactReference | None = None
    data: bytes | None = None

    def json(self) -> bytes | Rejected:
        """Bounded model-facing value, without controller IDs, paths or receipts."""
        if type(self.phase) is not Phase:
            return Rejected(Error.INVALID_RESULT)
        for value, cls in (
            (self.handle, LeaseHandle),
            (self.reference, ArtifactReference),
        ):
            if value is not None and (type(value) is not cls or not _uuid(value.value)):
                return Rejected(Error.INVALID_RESULT)
        if self.data is not None and (
            type(self.data) is not bytes or len(self.data) > MAX_HANDOFF
        ):
            return Rejected(Error.INVALID_RESULT)
        data = json.dumps(
            {
                "phase": self.phase.value,
                "handle": str(self.handle.value) if self.handle else None,
                "artifact": str(self.reference.value) if self.reference else None,
                "data_base64": base64.b64encode(self.data).decode("ascii")
                if self.data is not None
                else None,
            }
        ).encode()
        return data if len(data) <= MAX_REPLY_BYTES else Rejected(Error.PAYLOAD_LIMIT)


class Admission:
    """Single-flight, host-owned state. All transitions are locked memory only."""

    def __init__(self, task: TaskBinding) -> None:
        self._task = task
        self._phase = Phase.NEW
        self._lock = threading.Lock()
        self._calls: dict[UUID, HostCall] = {}
        self._used: set[UUID] = set()
        self._pending: Admitted | None = None
        self._lease: Lease | None = None
        self._handle: LeaseHandle | None = None
        self._recovery: ArtifactReference | None = None
        self._output: ArtifactReference | None = None
        self._receipt: Receipt | None = None
        self._last_poll: int | None = None
        self._now = 0
        self._recovery_used = False

    @property
    def phase(self) -> Phase:
        return self._phase

    def _time(self, now: int) -> bool:
        if type(now) is not int or now <= 0 or now < self._now:
            return False
        self._now = now
        return True

    def issue_call(
        self, identity: UUID, *, now_ns: int, expires_ns: int
    ) -> HostCall | Rejected:
        """Host allocates the ID; no model input is used to mint this permit."""
        with self._lock:
            if not self._time(now_ns) or type(expires_ns) is not int:
                return Rejected(Error.INVALID_TIME)
            if not _uuid(identity):
                return Rejected(Error.INVALID_CALL)
            if identity in self._calls:
                return Rejected(Error.DUPLICATE_CALL)
            if len(self._calls) >= MAX_CALL_IDS:
                return Rejected(Error.CALL_LIMIT)
            if not 0 < expires_ns - now_ns <= MAX_LEASE_NS:
                return Rejected(Error.INVALID_TIME)
            permit = HostCall(identity, expires_ns)
            self._calls[identity] = permit
            return permit

    def revoke(self) -> None:
        """Host invalidates handles; this never performs controller cleanup."""
        with self._lock:
            self._phase = Phase.CLOSED
            self._pending = None

    def admit(
        self, task: object, call: object, payload: object, *, now_ns: int
    ) -> Admitted | Rejected:
        with self._lock:
            if task is not self._task or not isinstance(task, TaskBinding):
                return Rejected(Error.INVALID_TASK)
            if not self._time(now_ns):
                return Rejected(Error.INVALID_TIME)
            if (
                type(call) is not HostCall
                or not _uuid(call.value)
                or self._calls.get(call.value) is not call
            ):
                return Rejected(Error.INVALID_CALL)
            if call.value in self._used:
                return Rejected(Error.DUPLICATE_CALL)
            self._used.add(call.value)  # invalid proposals also consume the permit
            if now_ns >= call.expires_ns:
                return Rejected(Error.TIMEOUT)
            if type(payload) is not bytes:
                return Rejected(Error.INVALID_PAYLOAD)
            if len(payload) > MAX_REQUEST_BYTES:
                return Rejected(Error.PAYLOAD_LIMIT)
            try:
                unique_json(payload)
                request = _Request.model_validate_json(payload)
                args = (
                    StartArguments
                    if request.method is Operation.START
                    else EmptyArguments
                ).model_validate(request.arguments)
            except (ValueError, TypeError, RecursionError):
                return Rejected(Error.INVALID_PAYLOAD)
            if self._pending is not None:
                return Rejected(Error.INVALID_TRANSITION)
            reference = None
            deadline = min(call.expires_ns, now_ns + COMMAND_NS)
            if request.method is Operation.START:
                if self._phase is not Phase.NEW or request.handle is not None:
                    return Rejected(Error.INVALID_TRANSITION)
                self._phase = Phase.STARTING  # one attempt, even if result is unknown
                deadline = call.expires_ns
            else:
                if self._lease is None:
                    return Rejected(Error.MISSING_LEASE)
                if self._phase is Phase.CLOSED:
                    return Rejected(Error.STALE_HANDLE)
                if request.handle != self._handle.value:
                    return Rejected(Error.HANDLE_MISMATCH)
                if request.method is Operation.STATUS:
                    if self._phase is not Phase.ACTIVE:
                        return Rejected(Error.INVALID_TRANSITION)
                    if now_ns >= self._lease.deadline_monotonic_ns:
                        self._phase = Phase.INDETERMINATE
                        return Rejected(Error.TIMEOUT)
                    if (
                        self._last_poll is not None
                        and now_ns - self._last_poll < POLL_NS
                    ):
                        return Rejected(Error.POLL_TOO_SOON)
                    self._last_poll = now_ns
                    deadline = min(deadline, self._lease.deadline_monotonic_ns)
                elif request.method is Operation.OUTPUT:
                    if self._phase is not Phase.STOPPED:
                        return Rejected(Error.INVALID_TRANSITION)
                    if self._output is None:
                        return Rejected(Error.NO_OUTPUT)
                    reference = self._output
                elif request.method is Operation.RECOVER:
                    if (
                        self._phase
                        not in {Phase.ACTIVE, Phase.STOPPED, Phase.INDETERMINATE}
                        or self._recovery_used
                    ):
                        return Rejected(Error.INVALID_TRANSITION)
                    self._recovery_used = True
                    reference = self._recovery
                    # Cleanup-only may follow worker deadline expiry. It does
                    # not extend the lease or authorize a new worker start.
            admitted = Admitted(
                request.method, args, call, now_ns, deadline, self._handle, reference
            )
            self._pending = admitted
            return admitted

    def _indeterminate(self, error: Error) -> Rejected:
        self._phase = Phase.INDETERMINATE
        return Rejected(error)

    def complete(
        self, operation: object, result: object, *, now_ns: int
    ) -> Completed | Rejected:
        """Accept a trusted result, never call an executor or accept an exception."""
        with self._lock:
            if operation is not self._pending or operation is None:
                return Rejected(Error.INVALID_CALL)
            self._pending = None
            if not self._time(now_ns):
                return self._indeterminate(Error.INVALID_TIME)
            if now_ns >= operation.deadline_ns:
                return self._indeterminate(Error.TIMEOUT)
            if isinstance(result, Failed):
                reason = result.reason
                if type(reason) is not Error or reason not in {
                    Error.TIMEOUT,
                    Error.CONTROLLER_FAILURE,
                    Error.UNKNOWN_COMPLETION,
                }:
                    reason = Error.INVALID_RESULT
                return self._indeterminate(reason)
            try:
                if operation.operation is Operation.START and isinstance(
                    result, Started
                ):
                    self._bind_start(operation, result, now_ns)
                    self._phase = Phase.ACTIVE
                elif operation.operation is Operation.STATUS and isinstance(
                    result, Running
                ):
                    self._phase = Phase.ACTIVE
                elif operation.operation in {
                    Operation.STATUS,
                    Operation.RECOVER,
                } and isinstance(result, Stopped):
                    self._bind_stop(result, now_ns)
                    self._phase = Phase.STOPPED
                elif operation.operation is Operation.OUTPUT and isinstance(
                    result, Output
                ):
                    if type(result.data) is not bytes or len(result.data) > MAX_HANDOFF:
                        raise ValueError
                    if (
                        len(result.data) != self._receipt.output_bytes
                        or digest(result.data) != self._receipt.output_sha256
                    ):
                        raise ValueError
                    self._phase = Phase.CLOSED
                    return Completed(
                        self._phase, self._handle, self._output, result.data
                    )
                else:
                    raise ValueError
            except (
                ValueError,
                TypeError,
                AttributeError,
                RecursionError,
                OverflowError,
            ):
                return self._indeterminate(Error.INVALID_RESULT)
            return Completed(self._phase, self._handle, self._output)

    def _opaque(self, reference, cls, forbidden):
        return (
            type(reference) is cls
            and _uuid(reference.value)
            and reference.value not in forbidden
        )

    def _bind_start(self, operation: Admitted, result: Started, now: int) -> None:
        if not isinstance(result.lease, Lease):
            raise ValueError
        data = encode(result.lease)
        if len(data) > MAX_STATE:
            raise ValueError
        lease = Lease.model_validate_json(data)  # detach mutable nested models
        forbidden = {lease.run_id, lease.owner, self._task.task_id}
        if not self._opaque(result.handle, LeaseHandle, forbidden):
            raise ValueError
        if not self._opaque(
            result.recovery, ArtifactReference, forbidden | {result.handle.value}
        ):
            raise ValueError
        if (
            lease.container_id is None
            or lease.purpose != "synthetic_worker"
            or lease.worker_mode != operation.arguments.mode
            or not operation.admitted_ns
            <= lease.prepared_monotonic_ns
            <= now
            < lease.deadline_monotonic_ns
            or lease.deadline_monotonic_ns - lease.prepared_monotonic_ns
            != int(operation.arguments.timeout_seconds * 1e9)
        ):
            raise ValueError
        self._lease, self._handle, self._recovery = (
            lease,
            result.handle,
            result.recovery,
        )

    def _bind_stop(self, result: Stopped, now: int) -> None:
        if not isinstance(result.receipt, Receipt):
            raise ValueError
        data = encode(result.receipt)
        if len(data) > MAX_STATE:
            raise ValueError
        receipt = Receipt.model_validate_json(data)
        lease = self._lease
        if (
            receipt.lease_sha256 != digest(encode(lease))
            or receipt.run_id != lease.run_id
            or receipt.target != TARGET
            or receipt.configuration != CONFIG
            or receipt.container_id != lease.container_id
            or receipt.input_sha256 != digest(INPUT)
            or receipt.prepared_at != lease.prepared_at
            or receipt.prepared_monotonic_ns != lease.prepared_monotonic_ns
            or receipt.stopped_at.utcoffset() is None
            or receipt.stopped_at < lease.prepared_at
            or not lease.prepared_monotonic_ns <= receipt.stopped_monotonic_ns <= now
            or not receipt.cleanup_confirmed
            or not receipt.container_absent
            or not receipt.descendants_absent
            or not receipt.output_stable_after_stop
            or receipt.errors
            or len(receipt.observed_guest_pids) > 16
            or len(set(receipt.observed_guest_pids)) != len(receipt.observed_guest_pids)
            or any(pid < 2 for pid in receipt.observed_guest_pids)
        ):
            raise ValueError
        if receipt.output_sha256 is None:
            if receipt.output_bytes is not None or result.output is not None:
                raise ValueError
        else:
            forbidden = {
                lease.run_id,
                lease.owner,
                self._task.task_id,
                self._handle.value,
                self._recovery.value,
            }
            if (
                not receipt.input_observed
                or not _sha(receipt.output_sha256)
                or type(receipt.output_bytes) is not int
                or not 0 <= receipt.output_bytes <= MAX_HANDOFF
                or not self._opaque(result.output, ArtifactReference, forbidden)
            ):
                raise ValueError
        self._receipt, self._output = receipt, result.output
