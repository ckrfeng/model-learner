"""Hostile bytes and protocol tests; no submitted candidate code is executed."""

import io
import json
import os
import tarfile
from dataclasses import replace
from uuid import uuid4

import pytest

from model_learner.benchmark.fixtures import get_task
from model_learner.benchmark.isolation import require_supported_real_containment
from model_learner.benchmark.secure import (
    MAX_ARTIFACT_BYTES,
    MAX_PROTOCOL_BYTES,
    MAX_TRANSPORT_BYTES,
    FrozenCandidate,
    OfflineController,
    RunBinding,
    SignedReceipt,
    extract_candidate,
    fixture_sha256,
    public_task_envelope,
)
from model_learner.domain.models import ExecutionConfiguration


@pytest.fixture
def binding():
    fixture = get_task("clamp")
    return RunBinding(
        benchmark_id=uuid4(),
        run_id=uuid4(),
        task_id=uuid4(),
        fixture_id=fixture.task_id,
        fixture_sha256=fixture_sha256(fixture),
        configuration_snapshot_id=ExecutionConfiguration(
            provider="simulated", model="fixed-worker", harness="offline-synthetic-v1"
        ).configuration_id,
    )


def archive(
    content=b"public candidate bytes\n",
    *,
    name="solution.py",
    kind=tarfile.REGTYPE,
    pax=None,
    extra=False,
):
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode="w", format=tarfile.PAX_FORMAT) as stream:
        member = tarfile.TarInfo(name)
        member.type = kind
        member.size = len(content) if kind == tarfile.REGTYPE else 0
        member.pax_headers = pax or {}
        stream.addfile(member, io.BytesIO(content) if member.size else None)
        if extra:
            stream.addfile(tarfile.TarInfo("solution.py"))
    return output.getvalue()


def imported(binding, tmp_path):
    controller = OfflineController(binding)
    candidate, receipt = controller.import_candidate(archive())
    control = tmp_path.resolve() / "control"
    control.mkdir()
    candidate.write_exclusive(control)
    return controller, candidate, receipt, control


def responses(controller, *, wrong=False):
    values = []
    for index, (_, _, expected, error) in enumerate(controller.fixture.checks):
        request = json.loads(controller.request(index))
        result = {"request_id": request["request_id"]}
        result.update(
            {"error": error} if error else {"value": 999 if wrong else expected}
        )
        values.append(json.dumps(result).encode())
    return tuple(values)


def test_public_envelope_has_only_public_inputs(binding):
    envelope = public_task_envelope("clamp")
    value = json.loads(envelope)
    assert set(value) == {"version", "description", "files"}
    assert value["files"] == {"solution.py": get_task("clamp").initial_source}
    assert b"checks" not in envelope and b"expected" not in envelope
    assert binding.nonce.encode() not in envelope
    assert b"credential" not in envelope and b"acceptance.py" not in envelope


def test_bounded_bytes_only_import_and_exclusive_freeze(binding, tmp_path):
    controller, candidate, receipt, control = imported(binding, tmp_path)
    assert candidate.contents == b"public candidate bytes\n"
    assert (control / "candidate.py").stat().st_mode & 0o777 == 0o400
    candidate.recheck(control)
    value = controller.verify_receipt(receipt, purpose="artifact_import")
    assert value["binding"] == binding.payload()
    assert value["real_execution_ready"] is False
    assert value["evidence"]["runtime_freeze_verified"] is False
    assert "key" not in json.dumps(receipt.as_dict())
    with pytest.raises(FileExistsError):
        candidate.write_exclusive(control)
    with pytest.raises(ValueError, match="already imported"):
        controller.import_candidate(archive())
    with pytest.raises(ValueError, match="candidate bytes"):
        replace(candidate, contents=b"tampered").write_exclusive(control)


@pytest.mark.parametrize(
    "name",
    [
        "../solution.py",
        "/solution.py",
        "./solution.py",
        "other.py",
        "nested/solution.py",
    ],
)
def test_reject_artifact_paths(name):
    with pytest.raises(ValueError):
        extract_candidate(archive(name=name))


@pytest.mark.parametrize(
    "kind",
    [
        tarfile.SYMTYPE,
        tarfile.LNKTYPE,
        tarfile.DIRTYPE,
        tarfile.CHRTYPE,
        tarfile.BLKTYPE,
        tarfile.FIFOTYPE,
        tarfile.GNUTYPE_SPARSE,
    ],
)
def test_reject_nonregular_artifacts(kind):
    with pytest.raises(ValueError):
        extract_candidate(archive(kind=kind))


@pytest.mark.parametrize(
    "data", [b"bad", b"\0" * 1536, b"\0" * (MAX_TRANSPORT_BYTES + 512)]
)
def test_reject_invalid_or_oversized_transport(data):
    with pytest.raises(ValueError):
        extract_candidate(data)


def test_reject_metadata_duplicate_entries_and_hidden_trailing_archive():
    for data in (
        archive(pax={"comment": "hostile metadata"}),
        archive(extra=True),
        archive() + archive(content=b"hidden"),
        archive(content=b"a" * (MAX_ARTIFACT_BYTES + 1)),
    ):
        with pytest.raises(ValueError):
            extract_candidate(data)
    assert extract_candidate(archive(content=b"")) == b""


def test_reject_symlink_output_and_all_symlink_parents(binding, tmp_path):
    _, candidate, _, control = imported(binding, tmp_path)
    (control / "candidate.py").unlink()
    outside = tmp_path / "outside"
    outside.write_bytes(b"public canary")
    (control / "candidate.py").symlink_to(outside)
    with pytest.raises(FileExistsError):
        candidate.write_exclusive(control)
    assert outside.read_bytes() == b"public canary"
    link = tmp_path / "control-link"
    link.symlink_to(control, target_is_directory=True)
    with pytest.raises(OSError):
        candidate.write_exclusive(link)
    with pytest.raises(ValueError, match="absolute"):
        candidate.write_exclusive(type(control)("relative"))


def test_frozen_file_recheck_rejects_fifo_symlink_and_changed_bytes(binding, tmp_path):
    _, candidate, _, control = imported(binding, tmp_path)
    path = control / "candidate.py"
    path.chmod(0o600)
    path.write_bytes(b"changed")
    with pytest.raises(ValueError, match="changed"):
        candidate.recheck(control)
    path.unlink()
    os.mkfifo(path)
    with pytest.raises(ValueError, match="bounded regular"):
        candidate.recheck(control)
    path.unlink()
    path.symlink_to(tmp_path / "absent")
    with pytest.raises(OSError):
        candidate.recheck(control)


def test_signed_receipts_reject_tamper_purpose_and_cross_run_replay(binding, tmp_path):
    controller, _, receipt, _ = imported(binding, tmp_path)
    with pytest.raises(ValueError, match="authentication"):
        controller.verify_receipt(
            replace(receipt, payload=receipt.payload + b" "), purpose="artifact_import"
        )
    with pytest.raises(ValueError, match="purpose"):
        controller.verify_receipt(receipt, purpose="validation")
    other = OfflineController(replace(binding, run_id=uuid4()))
    with pytest.raises(ValueError, match="authentication"):
        other.verify_receipt(receipt, purpose="artifact_import")
    same_binding_new_authority = OfflineController(binding)
    with pytest.raises(ValueError, match="authentication"):
        same_binding_new_authority.verify_receipt(receipt, purpose="artifact_import")
    with pytest.raises(ValueError, match="exceeds"):
        controller.verify_receipt(
            SignedReceipt(b"a" * (MAX_PROTOCOL_BYTES + 1), "0" * 64),
            purpose="artifact_import",
        )


def test_requests_omit_hidden_controller_material_and_reject_duplicate_issue(
    binding, tmp_path
):
    controller, _, _, _ = imported(binding, tmp_path)
    request = json.loads(controller.request(0))
    assert set(request) == {"request_id", "function", "args"}
    assert request["function"] == "clamp" and request["args"] == [3, 1, 5]
    with pytest.raises(ValueError, match="already issued"):
        controller.request(0)
    for index in (-1, True, 6):
        with pytest.raises(ValueError, match="index"):
            controller.request(index)


def test_independent_validation_hashes_complete_transcript_and_rechecks_artifact(
    binding, tmp_path
):
    controller, candidate, _, control = imported(binding, tmp_path)
    result = controller.validate(control=control, responses=responses(controller))
    value = controller.verify_receipt(result, purpose="validation")
    evidence = value["evidence"]
    assert evidence["candidate_sha256"] == candidate.sha256
    assert evidence["case_count"] == evidence["passed_count"] == 6
    assert evidence["failed_count"] == 0 and evidence["result"] == "pass"
    assert len(evidence["transcript_sha256"]) == 64
    assert evidence["candidate_execution_attested"] is False
    assert value["real_execution_ready"] is False
    with pytest.raises(ValueError, match="already finalized"):
        controller.validate(control=control, responses=())
    with pytest.raises(ValueError, match="unfinished"):
        controller.request(0)
    with pytest.raises(ValueError, match="no supported verified containment"):
        require_supported_real_containment()


def test_valid_primitive_wrong_answers_are_failure_not_protocol_acceptance(
    binding, tmp_path
):
    controller, _, _, control = imported(binding, tmp_path)
    receipt = controller.validate(
        control=control, responses=responses(controller, wrong=True)
    )
    evidence = controller.verify_receipt(receipt, purpose="validation")["evidence"]
    assert evidence["result"] == "fail" and evidence["failed_count"] == 5


def test_unknown_incomplete_inputs_and_mutation_do_not_issue_validation(
    binding, tmp_path
):
    controller, _, _, control = imported(binding, tmp_path)
    with pytest.raises(ValueError, match="complete"):
        controller.validate(control=control, responses=())
    with pytest.raises(ValueError, match="all requests"):
        controller.validate(control=control, responses=(b"{}",) * 6)
    values = responses(controller)
    path = control / "candidate.py"
    path.chmod(0o600)
    path.write_bytes(b"replaced after import")
    with pytest.raises(ValueError, match="changed"):
        controller.validate(control=control, responses=values)


@pytest.mark.parametrize(
    "malformation",
    [
        "foreign",
        "extra",
        "boolean",
        "nonfinite",
        "duplicate",
        "oversize",
        "unknown_error",
        "reordered",
        "nested",
    ],
)
def test_hostile_responses_fail_closed(binding, tmp_path, malformation):
    controller, _, _, control = imported(binding, tmp_path)
    values = list(responses(controller))
    value = json.loads(values[0])
    if malformation == "foreign":
        value["request_id"] = str(uuid4())
    elif malformation == "extra":
        value["report_path"] = "/private/hidden"
    elif malformation == "boolean":
        value["value"] = True
    elif malformation == "nonfinite":
        value["value"] = float("inf")
    elif malformation == "unknown_error":
        value = {"request_id": value["request_id"], "error": "private transcript"}
    elif malformation == "nested":
        value["value"] = {"path": "hidden"}
    values[0] = json.dumps(value).encode()
    if malformation == "duplicate":
        values[0] = values[0][:-1] + b', "value": 3}'
    elif malformation == "oversize":
        values[0] += b" " * MAX_PROTOCOL_BYTES
    elif malformation == "reordered":
        values.reverse()
    with pytest.raises(ValueError):
        controller.validate(control=control, responses=tuple(values))


def test_binding_fixture_mutation_rejected(binding):
    with pytest.raises(ValueError, match="trusted fixture"):
        OfflineController(replace(binding, fixture_sha256="a" * 64))
    with pytest.raises(ValueError, match="snapshot"):
        replace(binding, configuration_snapshot_id=" ")


def test_public_frozen_constructor_rejects_oversized_and_invalid_hashes():
    import hashlib

    data = b"a" * (MAX_ARTIFACT_BYTES + 1)
    with pytest.raises(ValueError, match="oversized"):
        FrozenCandidate(data, hashlib.sha256(data).hexdigest(), "a" * 64)
    with pytest.raises(ValueError):
        FrozenCandidate(b"", hashlib.sha256(b"").hexdigest(), "bad")


def test_recheck_rejects_hardlinked_frozen_artifact(binding, tmp_path):
    _, candidate, _, control = imported(binding, tmp_path)
    os.link(control / "candidate.py", tmp_path / "alias")
    with pytest.raises(ValueError, match="bounded regular"):
        candidate.recheck(control)


def test_unhashable_error_and_large_integer_are_handled_as_protocol_values(
    binding, tmp_path
):
    controller, _, _, control = imported(binding, tmp_path)
    values = list(responses(controller))
    request_id = json.loads(values[0])["request_id"]
    values[0] = json.dumps({"request_id": request_id, "error": []}).encode()
    with pytest.raises(ValueError, match="supported primitive"):
        controller.validate(control=control, responses=tuple(values))
    values[0] = json.dumps({"request_id": request_id, "value": 10**3000}).encode()
    receipt = controller.validate(control=control, responses=tuple(values))
    assert (
        controller.verify_receipt(receipt, purpose="validation")["evidence"][
            "failed_count"
        ]
        == 1
    )
