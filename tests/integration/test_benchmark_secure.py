"""Fixed harmless synthetic workers only; no candidate source is executed."""

import io
import json
import subprocess
import sys
import tarfile
from uuid import uuid4

import pytest

from model_learner.benchmark.fixtures import get_task
from model_learner.benchmark.isolation import require_supported_real_containment
from model_learner.benchmark.secure import (
    OfflineController,
    RunBinding,
    fixture_sha256,
    public_task_envelope,
)
from model_learner.domain.models import ExecutionConfiguration

# This fixed worker computes clamp directly, not by importing submitted bytes.
# Its host privileges are not contained; it performs no hostile operations.
_WORKER = """import json, os, sys
request = json.loads(sys.stdin.buffer.read(4097))
assert set(request) == {'request_id', 'function', 'args'}
assert request['function'] == 'clamp'
assert 'MODEL_LEARNER_SYNTHETIC_SECRET' not in os.environ
assert 'OPENAI_API_KEY' not in os.environ
assert 'HOME' not in os.environ
value, lower, upper = request['args']
response = {'request_id': request['request_id']}
if lower > upper:
    response['error'] = 'ValueError'
else:
    response['value'] = min(max(value, lower), upper)
sys.stdout.write(json.dumps(response))
"""


def test_synthetic_credential_separation_freeze_and_bound_validation(
    tmp_path, monkeypatch
):
    monkeypatch.setenv("MODEL_LEARNER_SYNTHETIC_SECRET", "public-synthetic-canary")
    monkeypatch.setenv("OPENAI_API_KEY", "public-synthetic-canary-not-a-credential")
    fixture = get_task("clamp")
    controller = OfflineController(
        RunBinding(
            benchmark_id=uuid4(),
            run_id=uuid4(),
            task_id=uuid4(),
            fixture_id="clamp",
            fixture_sha256=fixture_sha256(fixture),
            configuration_snapshot_id=ExecutionConfiguration(
                provider="simulated",
                model="fixed-worker",
                harness="offline-synthetic-v1",
            ).configuration_id,
        )
    )
    envelope = json.loads(public_task_envelope("clamp"))
    assert set(envelope["files"]) == {"solution.py"}
    # Opaque candidate marker is not Python and cannot accidentally be executed.
    content = b"public synthetic candidate marker; never executed\n"
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w", format=tarfile.USTAR_FORMAT) as archive:
        member = tarfile.TarInfo("solution.py")
        member.size = len(content)
        archive.addfile(member, io.BytesIO(content))
    candidate, imported = controller.import_candidate(data.getvalue())
    control = tmp_path.resolve() / "control"
    control.mkdir()
    candidate.write_exclusive(control)
    responses = []
    for index in range(len(fixture.checks)):
        request = controller.request(index)
        completed = subprocess.run(
            [sys.executable, "-I", "-c", _WORKER],
            input=request,
            env={},
            cwd=tmp_path,
            capture_output=True,
            timeout=2,
            check=True,
        )
        assert completed.stderr == b""
        assert len(completed.stdout) < 4096
        responses.append(completed.stdout)
    validation = controller.validate(control=control, responses=tuple(responses))
    assert (
        controller.verify_receipt(imported, purpose="artifact_import")["evidence"][
            "runtime_freeze_verified"
        ]
        is False
    )
    validated = controller.verify_receipt(validation, purpose="validation")
    assert validated["evidence"]["passed_count"] == 6
    assert validated["evidence"]["candidate_execution_attested"] is False
    assert validated["scope"] == "offline_synthetic_controller_only"
    assert validated["real_execution_ready"] is False
    with pytest.raises(ValueError, match="no supported verified containment"):
        require_supported_real_containment()


def test_harmless_worker_response_cannot_be_replayed_to_another_request(tmp_path):
    fixture = get_task("clamp")
    controller = OfflineController(
        RunBinding(
            benchmark_id=uuid4(),
            run_id=uuid4(),
            task_id=uuid4(),
            fixture_id="clamp",
            fixture_sha256=fixture_sha256(fixture),
            configuration_snapshot_id=ExecutionConfiguration(
                provider="simulated",
                model="fixed-worker",
                harness="offline-synthetic-v1",
            ).configuration_id,
        )
    )
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w") as archive:
        archive.addfile(tarfile.TarInfo("solution.py"))
    candidate, _ = controller.import_candidate(data.getvalue())
    control = tmp_path.resolve() / "control"
    control.mkdir()
    candidate.write_exclusive(control)
    requests = [controller.request(i) for i in range(6)]
    completed = subprocess.run(
        [sys.executable, "-I", "-c", _WORKER],
        input=requests[0],
        env={},
        capture_output=True,
        timeout=2,
        check=True,
    )
    with pytest.raises(ValueError, match="request binding"):
        controller.validate(control=control, responses=(completed.stdout,) * 6)
