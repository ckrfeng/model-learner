"""Explicit opt-in: new synthetic launchd/Colima controls, never a model or pilot.

No installation, pull, host mounts, credentials, old canary replay or Git writes.
Temporary jobs/state are removed; optional retained evidence remains synthetic.
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path

import pytest

from model_learner.benchmark import supervision as control

pytestmark = pytest.mark.skipif(
    os.environ.get("MODEL_LEARNER_SUPERVISION_RUNTIME_TEST") != "1",
    reason="explicit synthetic launchd/Colima opt-in required",
)


def until(predicate, seconds=15):
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.05)
    raise AssertionError("bounded synthetic handshake did not complete")


@pytest.mark.parametrize("scenario", ["normal", "timeout", "controller_crash"])
def test_independent_launchd_control_and_retained_receipt(tmp_path, scenario):
    directory = tmp_path / "job"
    args = [
        sys.executable,
        "-B",
        "-m",
        "model_learner.benchmark.supervision",
        "run",
        str(directory),
        "--mode",
        "normal" if scenario == "normal" else "live",
        "--seconds",
        "4" if scenario == "timeout" else "12",
    ]
    env = {
        "HOME": str(Path.home()),
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "PYTHONDONTWRITEBYTECODE": "1",
    }
    process = subprocess.Popen(
        args,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    receipt = None
    lease = None
    try:
        until(
            lambda: (
                (directory / "start-consumed.json").exists()
                or process.poll() is not None
            )
        )
        assert process.poll() is None, process.communicate()[1].decode()
        lease = control.load(directory)
        runtime = control.Runtime(directory)
        if scenario == "controller_crash":
            # New worker has a real detached-session child before owned SIGKILL.
            def alive_tree():
                info = runtime.inspect(lease)
                return (
                    info is not None
                    and info["State"]["Running"]
                    and len(runtime.pids(lease.container_id)) >= 3
                )

            until(alive_tree, 4)
            process.kill()  # Only this test's owned controller Popen.
            process.communicate(timeout=5)
            assert process.returncode < 0
        until(lambda: (directory / "receipt.json").exists(), 20)
        receipt = control.validate_receipt(directory)
        assert receipt.cleanup_confirmed and receipt.container_absent
        assert receipt.descendants_absent and receipt.output_stable_after_stop
        assert receipt.input_observed
        assert receipt.canonical_attempt_latency is None
        assert (
            receipt.stop_reason
            == {
                "normal": "completed",
                "timeout": "deadline",
                "controller_crash": "controller_exit",
            }[scenario]
        )
        if scenario == "normal":
            assert receipt.output_sha256 == control.digest(control.OUTPUT)
        else:
            assert len(receipt.observed_guest_pids) >= 3
            assert receipt.output_sha256 is None
        assert runtime.inspect(lease) is None
        # Restart is idempotent cleanup, never a new worker or new receipt.
        before = control.read(directory, "receipt.json")
        assert control.recover(directory) == receipt
        with pytest.raises(FileExistsError):
            control.start(directory)
        assert control.read(directory, "receipt.json") == before
        if process.poll() is None:
            process.communicate(timeout=5)
            assert process.returncode == 0
        retained_root = Path(
            os.environ.get("MODEL_LEARNER_SUPERVISION_EVIDENCE", str(tmp_path))
        )
        retained = retained_root / (scenario + "-" + lease.owner.hex)
        control.finalize(directory, retained)
        assert not directory.exists()
        assert control.validate_receipt(retained) == receipt
        query_code, query_error = control._launchctl(
            ["print", f"gui/{os.getuid()}/{lease.label}"], 1
        )
        assert (
            query_code != 0
            and (b'Could not find service "' + lease.label.encode() + b'"')
            in query_error
        )
        summary = {
            "scenario": scenario,
            "receipt": receipt.model_dump(mode="json"),
            "temporary_state_removed": True,
            "launchd_job_absent": True,
            "evidence_directory": str(retained),
        }
        print(json.dumps(summary, sort_keys=True))
    finally:
        if process.poll() is None:
            process.kill()
            process.communicate(timeout=5)
        if directory.exists() and (directory / "lease.json").exists():
            # Recover only this UUID/immutable owned worker. Keep uncertain state.
            try:
                recovered = control.recover(directory)
                if recovered.cleanup_confirmed:
                    control.finalize(directory, tmp_path / "failure-cleanup")
            except Exception:
                pass
