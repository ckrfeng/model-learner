"""Private local lifecycle adapter; no transport, inference or background loop.

One trusted owner retains one instance per task. The host supplies a fresh private
root, clocks/IDs and the controller port, and calls ``expire`` from its watchdog.
Calls are synchronous: cancellation flags immediately, then waits for an active
port call to return before cleanup (never races recovery against start). This is
not crash-safe, a process-killing deadline, or provider inference cancellation.
Unknown cleanup retains both state and evidence. Only host-only ``retain`` may
ask the existing controller to dispose of confirmed stopped state.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from model_learner.benchmark import _dispatch_contract as c
from model_learner.benchmark import supervision as control


class ControllerPort(Protocol):
    """Trusted local boundary, never selected or populated by model messages."""

    def start(
        self, directory: Path, *, mode: str, timeout_seconds: float
    ) -> control.Lease: ...
    def load(self, directory: Path) -> control.Lease: ...
    def has_receipt(self, directory: Path) -> bool: ...
    def validate_receipt(self, directory: Path) -> control.Receipt: ...
    def read(self, directory: Path, name: str) -> bytes: ...
    def recover(self, directory: Path) -> control.Receipt: ...
    def finalize(self, directory: Path, retained: Path) -> control.Receipt: ...


class ExistingController:
    """Direct existing operations; tests replace this entire trusted port."""

    start = staticmethod(control.start)
    load = staticmethod(control.load)
    validate_receipt = staticmethod(control.validate_receipt)
    read = staticmethod(control.read)
    recover = staticmethod(control.recover)
    finalize = staticmethod(control.finalize)

    @staticmethod
    def has_receipt(directory: Path) -> bool:
        control.secure_directory(directory)
        try:
            (directory / "receipt.json").lstat()
        except FileNotFoundError:
            return False
        return True  # the existing validator rejects unsafe types/contents


class Adapter:
    def __init__(
        self,
        task: c.TaskBinding,
        root: Path,
        *,
        port: ControllerPort,
        clock: Callable[[], int] = time.monotonic_ns,
        identity: Callable[[], UUID] = uuid4,
    ) -> None:
        # Fresh root and fixed child names are host-owned, never request fields.
        root = Path(root).absolute()
        root.mkdir(mode=0o700, exist_ok=False)
        self._root = control.secure_directory(root)
        self._directory = self._root / "controller"
        self._retained = self._root / "retained"
        self._location = self._directory
        self._task = task
        self._admission = c.Admission(task)
        self._port, self._clock, self._identity = port, clock, identity
        self._lock = threading.Lock()
        self._cancelled = threading.Event()
        self._possible_start = False
        self._recovery_attempted = False
        self._cleanup_confirmed = False
        self._lease: control.Lease | None = None
        self._receipt: control.Receipt | None = None
        self._handle: c.LeaseHandle | None = None
        self._recovery: c.ArtifactReference | None = None
        self._artifact: c.ArtifactReference | None = None
        self._paths: dict[UUID, Path] = {}

    @property
    def phase(self) -> c.Phase:
        return self._admission.phase

    @property
    def cleanup_confirmed(self) -> bool:
        """False means unknown/unconfirmed; it is never proof of presence."""
        return self._cleanup_confirmed

    def issue_call(self, *, expires_ns: int) -> c.HostCall | c.Rejected:
        """Host-only allocation. Model correlation IDs are never used."""
        return self._admission.issue_call(
            self._identity(), now_ns=self._clock(), expires_ns=expires_ns
        )

    def dispatch(self, task: object, call: object, payload: object):
        operation = self._admission.admit(task, call, payload, now_ns=self._clock())
        if isinstance(operation, c.Rejected):
            return operation  # no port access on rejected/replayed proposals
        with self._lock:
            try:
                if self._cancelled.is_set():
                    raise InterruptedError
                if self._clock() >= operation.deadline_ns:
                    reply = self._admission.complete(
                        operation, c.Failed(c.Error.TIMEOUT), now_ns=self._clock()
                    )
                    self._cleanup_once()
                    return reply
                result = self._execute(operation)
                if self._cancelled.is_set():
                    raise InterruptedError
                reply = self._admission.complete(
                    operation, result, now_ns=self._clock()
                )
                if isinstance(reply, c.Completed):
                    self._remember(result)
                    return reply
            except (Exception, KeyboardInterrupt):
                # Start can have taken effect even when no lease was returned.
                reason = (
                    c.Error.UNKNOWN_COMPLETION
                    if operation.operation is c.Operation.START
                    or self._cancelled.is_set()
                    else c.Error.CONTROLLER_FAILURE
                )
                reply = self._admission.complete(
                    operation, c.Failed(reason), now_ns=self._clock()
                )
            self._cleanup_once()
            return reply

    def _execute(self, operation: c.Admitted):
        if operation.operation is c.Operation.START:
            self._possible_start = True  # before entering the side-effect boundary
            lease = self._port.start(
                self._directory,
                mode=operation.arguments.mode,
                timeout_seconds=operation.arguments.timeout_seconds,
            )
            data = control.encode(lease)
            if len(data) > control.MAX_STATE:
                raise ValueError
            # Provisional trusted identity also constrains failure cleanup. The
            # model handle is bound only after contract completion succeeds.
            self._lease = control.Lease.model_validate_json(data)
            self._checked_lease()
            return c.Started(
                lease,
                c.LeaseHandle(self._identity()),
                c.ArtifactReference(self._identity()),
            )
        if self._paths.get(operation.handle.value) != self._location:
            raise ValueError
        self._checked_lease()
        if operation.operation is c.Operation.STATUS:
            if not self._port.has_receipt(self._location):
                # Pending lease state, not proof of worker liveness/completion.
                return c.Running()
            receipt = self._validated_receipt()
            artifact = self._artifact
            if receipt.output_sha256 is not None and artifact is None:
                artifact = c.ArtifactReference(self._identity())
            return c.Stopped(receipt, artifact)
        if self._paths.get(operation.reference.value) != self._location:
            raise ValueError
        if operation.operation is c.Operation.RECOVER:
            receipt = self._recover_once()
            if receipt is None:
                raise ValueError
            artifact = self._artifact
            if receipt.output_sha256 is not None and artifact is None:
                artifact = c.ArtifactReference(self._identity())
            return c.Stopped(receipt, artifact)
        if operation.operation is c.Operation.OUTPUT:
            receipt = self._validated_receipt()
            if control.encode(receipt) != control.encode(self._receipt):
                raise ValueError
            data = self._port.read(self._location, "output.bin")
            if (
                type(data) is not bytes
                or len(data) > control.MAX_HANDOFF
                or len(data) != receipt.output_bytes
                or control.digest(data) != receipt.output_sha256
            ):
                raise ValueError
            return c.Output(data)
        raise ValueError

    def _remember(self, result) -> None:
        if isinstance(result, c.Started):
            self._lease = control.Lease.model_validate_json(
                control.encode(result.lease)
            )
            self._handle, self._recovery = result.handle, result.recovery
            for reference in (self._handle, self._recovery):
                self._paths[reference.value] = self._location
        elif isinstance(result, c.Stopped):
            self._receipt = control.Receipt.model_validate_json(
                control.encode(result.receipt)
            )
            self._cleanup_confirmed = True  # contract checked all stopped assertions
            self._artifact = result.output
            if result.output is not None:
                self._paths[result.output.value] = self._location

    def _checked_lease(self) -> control.Lease:
        lease = self._port.load(self._location)
        data = control.encode(lease)
        if len(data) > control.MAX_STATE:
            raise ValueError
        lease = control.Lease.model_validate_json(data)
        if self._lease is not None and data != control.encode(self._lease):
            raise ValueError  # do not recover a replaced controller identity
        return lease

    def _validated_receipt(self) -> control.Receipt:
        lease = self._checked_lease()
        receipt = self._port.validate_receipt(self._location)
        data = control.encode(receipt)
        if len(data) > control.MAX_STATE:
            raise ValueError
        receipt = control.Receipt.model_validate_json(data)
        if (
            receipt.lease_sha256 != control.digest(control.encode(lease))
            or not receipt.cleanup_confirmed
            or not receipt.container_absent
            or not receipt.descendants_absent
            or not receipt.output_stable_after_stop
            or receipt.errors
        ):
            raise ValueError
        return receipt

    def _recover_once(self) -> control.Receipt | None:
        if self._recovery_attempted:
            return None
        self._recovery_attempted = True  # exceptions also consume this allowance
        self._checked_lease()
        result = self._port.recover(self._location)
        receipt = self._validated_receipt()
        if control.encode(result) != control.encode(receipt):
            raise ValueError
        self._cleanup_confirmed = True
        return receipt

    def _cleanup_once(self) -> None:
        if (
            not self._possible_start
            or self._cleanup_confirmed
            or self._recovery_attempted
        ):
            return
        try:
            self._recover_once()
        except (Exception, KeyboardInterrupt):
            self._cleanup_confirmed = False
        # No deletion, restart, inferred absence or exception disclosure.

    def cancel(self) -> c.Completed | c.Rejected:
        """Host-only local cancellation; never claims provider inference stopped."""
        self._cancelled.set()
        with self._lock:
            self._admission.revoke()
            self._cleanup_once()
            if self._possible_start and not self._cleanup_confirmed:
                return c.Rejected(c.Error.UNKNOWN_COMPLETION)
            return c.Completed(c.Phase.CLOSED)

    def expire(self) -> c.Rejected | None:
        """Host watchdog entry point, independent of untrusted request rejection."""
        with self._lock:
            if (
                self._lease is not None
                and not self._cleanup_confirmed
                and self._clock() >= self._lease.deadline_monotonic_ns
            ):
                self._cancelled.set()
                self._admission.revoke()
                self._cleanup_once()
                return c.Rejected(c.Error.TIMEOUT)
        return None

    def retain(self) -> c.Completed | c.Rejected:
        """Host-only disposal into an owned retained directory after confirmed stop."""
        with self._lock:
            if (
                not self._cleanup_confirmed
                or self._receipt is None
                or self.phase not in {c.Phase.STOPPED, c.Phase.CLOSED}
            ):
                return c.Rejected(c.Error.INVALID_TRANSITION)
            try:
                receipt = self._validated_receipt()
                if control.encode(receipt) != control.encode(self._receipt):
                    raise ValueError
                if self._location != self._retained:
                    result = self._port.finalize(self._location, self._retained)
                    if control.encode(result) != control.encode(receipt):
                        raise ValueError
                    self._location = self._retained
                    if control.encode(self._validated_receipt()) != control.encode(
                        receipt
                    ):
                        raise ValueError
                    self._paths = {key: self._location for key in self._paths}
                return c.Completed(self.phase, self._handle, self._artifact)
            except (Exception, KeyboardInterrupt):
                self._admission.revoke()
                return c.Rejected(c.Error.CONTROLLER_FAILURE)
