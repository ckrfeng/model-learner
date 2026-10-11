"""Contract tests; mocked Docker commands do not attest actual containment."""

import io
import json
import sys
import tarfile
import time
from pathlib import Path

import pytest

from model_learner.benchmark import offline


def _archive(name="solution.py", content=offline.ARTIFACT, kind=tarfile.REGTYPE):
    stream = io.BytesIO()
    with tarfile.open(fileobj=stream, mode="w:") as archive:
        member = tarfile.TarInfo(name)
        member.type = kind
        member.size = len(content) if kind == tarfile.REGTYPE else 0
        archive.addfile(member, io.BytesIO(content) if member.size else None)
    return stream.getvalue()


def test_explicit_approved_image_required():
    result = offline.probe_offline_isolation()
    assert result.status == "unavailable"
    assert result.reason == "image_approval_required"
    assert result.real_execution_ready is False
    with pytest.raises(ValueError, match="immutable"):
        offline.probe_offline_isolation("python:latest")
    assert offline.probe_offline_isolation("sha256:" + "a" * 64).reason == (
        "unsupported_synthetic_image"
    )


def test_fixed_policy_has_no_host_mounts_or_network():
    args = offline._create_arguments(
        "synthetic", offline.SUPPORTED_SYNTHETIC_IMAGE, "fixed"
    )
    assert args[args.index("--pull") + 1] == "never"
    assert args[args.index("--network") + 1] == "none"
    assert args[args.index("--user") + 1] == "65534:65534"
    assert args[args.index("--pids-limit") + 1] == str(offline.PIDS)
    assert "--read-only" in args
    assert "--mount" not in args and "--volume" not in args
    assert "--privileged" not in args and "--env-file" not in args
    assert "--pid" not in args and "--device" not in args


def test_artifact_extraction_is_bytes_only():
    assert offline._extract_artifact(_archive()) == offline.ARTIFACT


@pytest.mark.parametrize(
    "name,kind",
    [
        ("../solution.py", tarfile.REGTYPE),
        ("/solution.py", tarfile.REGTYPE),
        ("other.py", tarfile.REGTYPE),
        ("solution.py", tarfile.SYMTYPE),
        ("solution.py", tarfile.LNKTYPE),
        ("solution.py", tarfile.CHRTYPE),
        ("solution.py", tarfile.FIFOTYPE),
    ],
)
def test_artifact_rejects_traversal_links_and_nonregular(name, kind):
    with pytest.raises(offline._ProbeError):
        offline._extract_artifact(_archive(name=name, kind=kind))


def test_artifact_rejects_oversize_and_multiple_files():
    with pytest.raises(offline._ProbeError):
        offline._extract_artifact(
            _archive(content=b"a" * (offline.MAX_ARTIFACT_BYTES + 1))
        )
    data = io.BytesIO()
    with tarfile.open(fileobj=data, mode="w:") as archive:
        for _ in range(2):
            member = tarfile.TarInfo("solution.py")
            archive.addfile(member, io.BytesIO())
    with pytest.raises(offline._ProbeError, match="member_count"):
        offline._extract_artifact(data.getvalue())
    with pytest.raises(offline._ProbeError):
        offline._extract_artifact(b"not an archive")


def test_bounded_transport_caps_output_and_wall_time():
    command = [sys.executable, "-c", "print('public')"]
    assert (
        offline._bounded(command, deadline=time.monotonic() + 2, env={}) == b"public\n"
    )
    with pytest.raises(offline._ProbeError, match="output_limit"):
        offline._bounded(
            [sys.executable, "-c", "print('a' * 70000)"],
            deadline=time.monotonic() + 2,
            env={},
        )
    with pytest.raises(offline._ProbeError, match="wall_deadline"):
        offline._bounded(
            [sys.executable, "-c", "import time; time.sleep(2)"],
            deadline=time.monotonic() + 0.05,
            env={},
        )


@pytest.fixture
def mocked_runtime(monkeypatch, tmp_path):
    monkeypatch.setattr(Path, "is_socket", lambda _: True)
    monkeypatch.setattr(offline.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(offline.shutil, "which", lambda _: "/usr/local/bin/docker")
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    monkeypatch.setattr(offline, "_policy_matches", lambda *_: True)
    calls = []

    def run(command, *, deadline, env):
        args = command[5:]
        calls.append(args)
        assert set(env) == {"PATH", "HOME"}
        assert "DOCKER_HOST" not in env
        if args[0] == "version":
            return json.dumps(
                {
                    "Os": "linux",
                    "Platform": {"Name": "Docker Desktop"},
                    "Version": "test",
                }
            ).encode()
        if args[0] == "image":
            return b'[{"Config":{"Env":["PATH=/bin"],"Volumes":null}}]'
        if args[0] == "inspect":
            return b'[{"Config":{}}]' if len(args) == 2 else b'{"Running":true}'
        if args[0] == "logs":
            return "\n".join(sorted(offline._REQUIRED)).encode()
        if args[0] == "exec":
            return _archive()
        if args[0] == "wait":
            raise offline._ProbeError("wall_deadline_exceeded")
        return b""

    monkeypatch.setattr(offline, "_bounded", run)
    yield calls


def test_mocked_complete_protocol_never_unlocks_real(mocked_runtime):
    result = offline.probe_offline_isolation(offline.SUPPORTED_SYNTHETIC_IMAGE)
    assert result.status == "validated"
    assert all(result.checks.values())
    assert result.real_execution_ready is False
    assert result.host_mounts == ()
    assert result.checks["watchdog_deadline_enforced"]
    assert sum(args[0] == "rm" for args in mocked_runtime) == 2


def test_runtime_failure_is_fail_closed_and_cleanup_runs(mocked_runtime, monkeypatch):
    initial = offline._bounded

    def broken(command, **kwargs):
        if command[5] == "start":
            raise offline._ProbeError("runtime_command_failed")
        return initial(command, **kwargs)

    monkeypatch.setattr(offline, "_bounded", broken)
    result = offline.probe_offline_isolation(offline.SUPPORTED_SYNTHETIC_IMAGE)
    assert result.status == "unavailable"
    assert result.reason == "runtime_start_failed"
    assert result.checks["whole_boundary_destroyed"]
    assert any(args[0] == "rm" for args in mocked_runtime)


def test_missing_positive_bootstrap_cannot_validate(mocked_runtime, monkeypatch):
    initial = offline._bounded

    def missing(command, **kwargs):
        if command[5] == "logs":
            return b"probe_ready\n"
        return initial(command, **kwargs)

    monkeypatch.setattr(offline, "_bounded", missing)
    result = offline.probe_offline_isolation(offline.SUPPORTED_SYNTHETIC_IMAGE)
    assert result.status == "failed"
    assert result.reason == "required_probe_marker_missing"
    assert not result.checks["workspace_read_write"]
    assert result.real_execution_ready is False
