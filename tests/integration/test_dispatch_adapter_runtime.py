"""One opt-in synthetic recovery case; no model, ledger, candidate or transport.

Select this exact test node explicitly and provide --basetemp pointing to
<fresh ignored evidence root>/pytest-state. A trusted host must first place a
ready preflight.json there with pinned binary/source hashes and runtime identity.
An exclusive attempt marker forbids reuse. General suite/file selection skips.
All task text/input comes from public synthetic constants; no session fixtures.
"""

import json
import os
import re
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import pytest

from model_learner.benchmark import _dispatch_contract as c
from model_learner.benchmark import supervision as control
from model_learner.benchmark._dispatch_adapter import Adapter, ExistingController
from model_learner.domain.models import Task

NODE = "test_dispatch_adapter_runtime.py::test_cleanup_only_recovery"
pytestmark = pytest.mark.skipif(
    not any(argument.endswith(NODE) for argument in sys.argv[1:]),
    reason="requires exact recovery node selection and fresh trusted preflight",
)


def _save(root, name, value):
    data = (
        value
        if type(value) is bytes
        else (json.dumps(value, sort_keys=True, indent=2) + "\n").encode()
    )
    fd = os.open(root / name, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    return {"bytes": len(data), "sha256": control.digest(data)}


def _journal(root, value):
    fd = os.open(root / "journal.jsonl", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write((json.dumps(value, sort_keys=True) + "\n").encode())
        stream.flush()
        os.fsync(stream.fileno())


def _exact_absence(runtime, lease, pids):
    assert runtime.inspect(lease) is None
    assert runtime.absent(pids)
    code, error = control._launchctl(["print", f"gui/{os.getuid()}/{lease.label}"], 1)
    pattern = (
        rb'(?:Bad request\.\s*)?Could not find service "'
        + re.escape(lease.label.encode())
        + rb'" in domain for user gui: '
        + str(os.getuid()).encode()
        + rb"\s*"
    )
    assert code != 0 and re.fullmatch(pattern, error)
    domain_code, domain_error = control._launchctl(["print", f"gui/{os.getuid()}"], 1)
    assert domain_code == 0 and not domain_error
    return {
        "container_absent": True,
        "observed_pids_absent": True,
        "observed_pid_count": len(pids),
        "exact_service_absent": True,
        "service_exit": code,
        "service_stderr_bytes": len(error),
        "domain_healthy": True,
        "domain_exit": domain_code,
        "domain_stderr_bytes": 0,
        "exhaustive_descendant_enumeration": False,
    }


def test_cleanup_only_recovery(request):
    basetemp = request.config.getoption("basetemp")
    assert basetemp is not None
    root = Path(basetemp).absolute().parent
    repository = Path(__file__).resolve().parents[2]
    assert Path(basetemp).name == "pytest-state"
    assert root.is_relative_to(repository / ".model-learner")
    control.secure_directory(root)
    _save(root, "attempt-consumed.json", {"one_start_only": True})
    counts = {"start": 0, "recover": 0, "finalize": 0, "typed_recover": 0, "output": 0}
    result = {
        "synthetic_only": True,
        "status": "failed",
        "stage": "preflight",
        "safe_error": None,
        "counts": counts,
        "canonical_records_created": 0,
        "model_provider_calls": 0,
    }
    state = root / "adapter-state"
    adapter = None

    class AuditedController(ExistingController):
        """Count boundaries without replacing any existing lifecycle behavior."""

        def start(self, directory, *, mode, timeout_seconds):
            assert directory == state / "controller"
            assert mode == "live" and timeout_seconds == 12
            counts["start"] += 1
            assert counts["start"] == 1
            _journal(root, {"boundary": "start", "count": counts["start"]})
            return super().start(directory, mode=mode, timeout_seconds=timeout_seconds)

        def recover(self, directory):
            assert directory == state / "controller"
            counts["recover"] += 1
            assert counts["recover"] == 1
            _journal(
                root, {"boundary": "cleanup_only_recover", "count": counts["recover"]}
            )
            return super().recover(directory)

        def finalize(self, directory, retained):
            assert directory == state / "controller" and retained == state / "retained"
            counts["finalize"] += 1
            assert counts["finalize"] == 1
            _journal(root, {"boundary": "finalize", "count": counts["finalize"]})
            return super().finalize(directory, retained)

    def dispatch(method, handle=None):
        if method == "recover":
            counts["typed_recover"] += 1
        if method == "output":
            counts["output"] += 1
        call = adapter.issue_call(expires_ns=time.monotonic_ns() + 5_000_000_000)
        assert isinstance(call, c.HostCall)
        value = {"method": method, "arguments": {}}
        if method == "start":
            value["arguments"] = {"mode": "live", "timeout_seconds": 12}
        if handle is not None:
            value["handle"] = str(handle.value)
        _journal(
            root,
            {"method": method, "host_call_sha256": control.digest(call.value.bytes)},
        )
        reply = adapter.dispatch(binding, call, json.dumps(value).encode())
        if isinstance(reply, c.Rejected):
            result["safe_error"] = reply.error.value
            pytest.fail("fixed adapter rejection; see sanitized recovery receipt")
        assert isinstance(reply, c.Completed)
        encoded = reply.json()
        assert type(encoded) is bytes and len(encoded) <= c.MAX_REPLY_BYTES
        _save(root, "reply-" + method + ".json", encoded)
        _journal(root, {"method": method, "phase": reply.phase.value})
        return reply

    try:
        preflight = json.loads((root / "preflight.json").read_bytes())
        assert preflight["status"] == "ready" and preflight["image"] == control.IMAGE
        assert 0 <= time.monotonic_ns() - preflight["checked_monotonic_ns"] < 120e9
        for row in preflight["pinned_files"]:
            assert control.digest(Path(row["path"]).read_bytes()) == row["sha256"]
        result["source_commit"] = preflight["source_commit"]
        result["runtime_identity"] = preflight["runtime_identity"]
        result["source_files"] = preflight["source_files"]
        selected = Task(
            description="Public fixed synthetic live worker cleanup-only adapter case",
            acceptance_spec=control.TARGET.model_copy(deep=True),
        )
        binding = c.TaskBinding.from_task(
            selected,
            checker_sha256=control.digest(Path(control.__file__).read_bytes()),
        )
        assert isinstance(binding, c.TaskBinding)
        _save(
            root,
            "host-binding.json",
            {
                "task_id_sha256": control.digest(binding.task_id.bytes),
                "task_snapshot_sha256": binding.task_sha256,
                "checker_sha256": binding.checker_sha256,
                "target": control.TARGET.model_dump(mode="json"),
                "configuration": control.CONFIG.model_dump(mode="json"),
                "input_sha256": control.digest(control.INPUT),
                "mode": "live",
                "timeout_seconds": 12,
            },
        )
        adapter = Adapter(binding, state, port=AuditedController())
        result["stage"] = "start"
        since = datetime.now(UTC).isoformat()
        reply = dispatch("start")
        assert reply.phase is c.Phase.ACTIVE and type(reply.handle) is c.LeaseHandle
        handle = reply.handle
        lease = control.load(state / "controller")
        assert lease.target == control.TARGET and lease.configuration == control.CONFIG
        assert lease.input_sha256 == control.digest(control.INPUT)
        assert lease.worker_mode == "live"
        assert handle.value not in (binding.task_id, lease.run_id, lease.owner)
        assert adapter._paths[handle.value] == state / "controller"
        consumed = control.read(state / "controller", "start-consumed.json")
        assert json.loads(consumed) == {"synthetic_start_consumed": True}
        ready = json.loads(control.read(state / "controller", "ready.json"))
        assert ready == {
            "lease_sha256": control.digest(control.encode(lease)),
            "controller_pid": os.getpid(),
        }
        runtime = control.Runtime(state / "controller")
        result["stage"] = "observe_active_worker"
        deadline = min(lease.deadline_monotonic_ns, time.monotonic_ns() + c.COMMAND_NS)
        observed = ()
        while time.monotonic_ns() < deadline:
            info = runtime.inspect(lease)
            assert info is not None and info["State"]["Running"]
            observed = runtime.pids(lease.container_id)
            if len(observed) >= 3:
                break
            time.sleep(c.POLL_NS / 1e9)
        assert len(observed) >= 3
        assert time.monotonic_ns() < lease.deadline_monotonic_ns
        assert adapter.phase is c.Phase.ACTIVE
        _save(
            root,
            "active-observation.json",
            {
                "lease_active": True,
                "exact_container_running": True,
                "observed_pid_count": len(observed),
                "observed_pids_sha256": control.digest(json.dumps(observed).encode()),
                "start_marker": {
                    "bytes": len(consumed),
                    "sha256": control.digest(consumed),
                },
            },
        )
        result["stage"] = "typed_recover"
        reply = dispatch("recover", handle)
        assert reply.phase is c.Phase.STOPPED and reply.handle == handle
        receipt = control.validate_receipt(state / "controller")
        assert receipt.stop_reason == "recovery" and receipt.cleanup_confirmed
        assert receipt.input_observed and receipt.input_sha256 == control.digest(
            control.INPUT
        )
        assert receipt.container_absent and receipt.descendants_absent
        assert receipt.output_stable_after_stop and not receipt.errors
        assert (
            receipt.canonical_attempt_latency is None
            and receipt.model_transport == "absent"
        )
        pids = tuple(sorted(set(observed) | set(receipt.observed_guest_pids)))
        result["observed_before_recovery_pid_count"] = len(observed)
        result["receipt_observed_pid_count"] = len(receipt.observed_guest_pids)
        result["lease"] = {
            "bytes": len(control.encode(lease)),
            "sha256": control.digest(control.encode(lease)),
        }
        result["receipt"] = {
            "bytes": len(control.encode(receipt)),
            "sha256": control.digest(control.encode(receipt)),
        }
        result["stop_reason"] = receipt.stop_reason
        result["stage"] = "output_binding"
        if receipt.output_sha256 is None:
            assert receipt.output_bytes is None and reply.reference is None
            assert not (state / "controller" / "output.bin").exists()
            result["output"] = {"state": "absent", "bytes": None, "sha256": None}
        else:
            output = dispatch("output", handle)
            assert output.reference == reply.reference
            assert (
                type(output.data) is bytes and len(output.data) <= control.MAX_HANDOFF
            )
            assert len(output.data) == receipt.output_bytes
            assert control.digest(output.data) == receipt.output_sha256
            result["output"] = {
                "state": "present",
                "bytes": len(output.data),
                "sha256": control.digest(output.data),
            }
        result["stage"] = "independent_absence_before_retention"
        before = _exact_absence(runtime, lease, pids)
        _save(root, "absence-before-retention.json", before)
        result["stage"] = "retain"
        retained = adapter.retain()
        assert isinstance(retained, c.Completed)
        assert retained.handle == handle and retained.reference == reply.reference
        assert control.validate_receipt(state / "retained") == receipt
        assert not (state / "controller").exists()
        _save(root, "reply-retained.json", retained.json())
        result["stage"] = "independent_final_absence"
        final = _exact_absence(runtime, lease, pids)
        final["temporary_state_removed"] = True
        final["retained_receipt_valid"] = True
        _save(root, "absence-final.json", final)
        result["stage"] = "one_start_event"
        raw = runtime.command(
            [
                "events",
                "--since",
                since,
                "--until",
                datetime.now(UTC).isoformat(),
                "--filter",
                "container=" + lease.container_id,
                "--filter",
                "event=start",
                "--format",
                "{{json .}}",
            ]
        )
        _save(root, "exact-container-start-events.raw", raw)
        events = [json.loads(line) for line in raw.splitlines() if line.strip()]
        assert len(events) == 1 and events[0].get("Action") == "start"
        assert events[0]["Actor"]["ID"] == lease.container_id
        assert counts["start"] == counts["recover"] == counts["finalize"] == 1
        assert counts["typed_recover"] == 1
        result["exact_start_event_count"] = 1
        result["absence"] = final
        result["limits"] = [
            "synthetic_recovery_only",
            "in_memory_not_crash_durable",
            "no_exhaustive_descendant_or_host_isolation_claim",
            "no_live_environment_inheritance_or_transport_acceptance",
            "no_provider_identity_billing_retry_output_spend_or_remote_stop_evidence",
        ]
        result["status"], result["stage"] = "passed", "complete"
    except BaseException as exc:
        result["failure_type"] = type(exc).__name__
        result["safe_error"] = result["safe_error"] or "integration_check_failed"
        if adapter is not None:
            # The adapter owns exactly one cleanup-only allowance, including an
            # ambiguous start. A consumed recovery allowance is never retried.
            adapter.cancel()
            result["failure_cleanup_confirmed"] = adapter.cleanup_confirmed
        raise
    finally:
        result["test_check_exit"] = 0 if result["status"] == "passed" else 1
        _save(root, "recovery-receipt.json", result)
