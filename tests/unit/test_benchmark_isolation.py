"""Containment diagnostics cannot authorize real agent evidence collection."""

import json
import subprocess
from pathlib import Path

import pytest

from model_learner.benchmark import (
    finalize_benchmark,
    isolation,
    load_benchmark,
    prepare_benchmark,
)
from model_learner.domain.models import ExecutionConfiguration, utc_now


def _available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(isolation.platform, "system", lambda: "Darwin")
    monkeypatch.setattr(Path, "is_file", lambda _: True)


def test_absent_backend_is_unknown_and_never_ready(monkeypatch) -> None:
    monkeypatch.setattr(isolation.platform, "system", lambda: "Linux")
    probe = isolation.probe_macos_containment()
    assert probe.status == "unavailable"
    assert probe.outside_read_denied is None
    assert probe.real_execution_ready is False


def test_bootstrap_failure_does_not_count_as_denied_access(monkeypatch) -> None:
    _available(monkeypatch)
    monkeypatch.setattr(
        isolation.subprocess,
        "run",
        lambda *args, **kwargs: subprocess.CompletedProcess(args[0], 134, b""),
    )
    probe = isolation.probe_macos_containment()
    assert probe.status == "unavailable"
    assert probe.exit_code == 134
    assert probe.permitted_read is False
    assert probe.outside_read_denied is None
    assert probe.outside_write_denied is None
    assert probe.canaries_unchanged is True


@pytest.mark.parametrize("failure", [OSError(), subprocess.TimeoutExpired("probe", 5)])
def test_spawn_or_timeout_is_unavailable(monkeypatch, failure) -> None:
    _available(monkeypatch)

    def unavailable(*args, **kwargs):
        raise failure

    monkeypatch.setattr(isolation.subprocess, "run", unavailable)
    assert isolation.probe_macos_containment().status == "unavailable"


@pytest.mark.parametrize("allow_escape", [False, True])
def test_fixed_canary_probe_checks_escape_and_scopes_success(
    monkeypatch, allow_escape
) -> None:
    _available(monkeypatch)

    def simulated_probe(command, **options):
        assert options["env"] == {}
        assert options["timeout"] == 5
        assert options["stdin"] == subprocess.DEVNULL
        assert command[0] == "/usr/bin/sandbox-exec"
        assert "(deny default)" in command[2]
        workspace, outside = Path(command[-2]), Path(command[-1])
        assert workspace != outside
        assert (workspace / "outside-link").resolve() == outside / "private-canary.txt"
        if allow_escape:
            (outside / "source-canary.txt").write_text("changed\n")
        markers = (
            b"permitted_read\npermitted_write\noutside_read_denied\n"
            b"outside_write_denied\nsymlink_read_denied\ndescendant_read_denied\n"
        )
        return subprocess.CompletedProcess(command, 0, markers)

    monkeypatch.setattr(isolation.subprocess, "run", simulated_probe)
    probe = isolation.probe_macos_containment()
    assert probe.status == ("failed" if allow_escape else "probe_passed")
    assert probe.canaries_unchanged is (not allow_escape)
    assert probe.real_execution_ready is False


def _real(tmp_path):
    protected, parent = tmp_path / "source", tmp_path / "disposable"
    protected.mkdir()
    parent.mkdir()
    (protected / "public.py").write_text("public\n")
    return prepare_benchmark(
        parent=parent,
        task_id="clamp",
        configuration=ExecutionConfiguration(model="declared-model"),
        protected_repository=protected,
        isolation_mechanism="operator says isolated; no verified backend",
        execution_origin="real",
    )


def test_operator_declaration_cannot_enable_real_collection(tmp_path) -> None:
    prepared = _real(tmp_path)
    before = (prepared.control / "ledger.sqlite3").read_bytes()
    with pytest.raises(ValueError, match="no supported verified containment"):
        finalize_benchmark(
            prepared.root,
            started_at=utc_now(),
            ended_at=utc_now(),
            isolation_confirmed=True,
        )
    assert not (prepared.control / "finalizing.lock").exists()
    assert not (prepared.control / "result.json").exists()
    assert (prepared.control / "ledger.sqlite3").read_bytes() == before


def test_origin_cannot_be_changed_to_bypass_real_gate(tmp_path) -> None:
    prepared = _real(tmp_path)
    manifest = prepared.control / "manifest.json"
    data = json.loads(manifest.read_text())
    data["execution_origin"] = "fixture"
    manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError, match="dataset declaration changed"):
        load_benchmark(prepared.root)
