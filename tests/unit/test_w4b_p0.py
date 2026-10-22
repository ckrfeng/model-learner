"""Original synthetic configuration fixtures; no model, candidate execution or Git.

The reference bytes below are independently written from TASK.md, not generated
from checker expectations. They exist only in test temporary storage, never in
the candidate starting workspace. W6B regressions cover receipts/learning policy.
"""

import hashlib
import json
import os
import sys
from datetime import timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from model_learner.domain.models import AcceptanceSpec, Run, Task, Verification, utc_now
from model_learner.storage.database import Database, Repository
from model_learner.verification import (
    JUnitReportBinding,
    junit_criterion,
    parse_junit_xml,
    verify_junit,
)
from scripts import check_w4b_p0 as checker
from scripts import privacy_guard

ROOT = Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "tests/fixtures/w4b_p0/v1"
MANIFEST = ROOT / "docs/experiments/w4b_p0_v1.json"
REFERENCE = """[project]
name = "signal-note"
version = "0.2.0"
description = "Fictional offline note formatter."
requires-python = ">=3.12,<3.14"
dependencies = []
[build-system]
requires = ["hatchling>=1.27,<2"]
build-backend = "hatchling.build"
[project.scripts]
signal-note = "signal_note.cli:main"
[project.optional-dependencies]
dev = ["pytest>=8,<9", "ruff>=0.12,<1"]
[tool.hatch.build.targets.wheel]
packages = ["src/signal_note"]
[tool.ruff]
target-version = "py312"
line-length = 88
[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]
[tool.ruff.format]
quote-style = "double"
indent-style = "space"
[tool.signal_note]
default_style = "compact"
retention_days = 7
[tool.signal_note.labels]
team = "fictional"
channel = "local"
"""


@pytest.fixture
def artifact(tmp_path):
    path = tmp_path / "pyproject.toml"
    path.write_text(REFERENCE)
    return path


def test_p1_p7_reference_and_exact_deterministic_report(artifact):
    before = artifact.read_bytes()
    result = checker.check(artifact)
    assert result.passed
    assert result == checker.check(artifact)
    assert result.artifact_sha256 == hashlib.sha256(before).hexdigest()
    assert result.report_sha256 == hashlib.sha256(result.report).hexdigest()
    summary = parse_junit_xml(result.report)
    assert not summary.diagnostics
    assert tuple(c.test_id for c in summary.cases) == checker.REQUIRED_IDS
    assert summary.counts.passed == 9
    assert (
        summary.counts.skipped == summary.counts.failures == summary.counts.errors == 0
    )
    assert len(result.report) < 8192
    assert artifact.read_bytes() == before


def test_p2_incomplete_start_fails():
    result = checker.check(FIXTURE / "start/pyproject.toml")
    assert not result.passed
    assert result.cases[:2] == (True, True)
    assert parse_junit_xml(result.report).counts.skipped == 0


@pytest.mark.parametrize("kind", ["missing", "directory", "symlink", "parent", "fifo"])
def test_p3_file_boundaries(tmp_path, artifact, kind):
    selected = tmp_path / "selected"
    if kind == "directory":
        selected.mkdir()
    elif kind == "symlink":
        selected.symlink_to(artifact)
    elif kind == "parent":
        selected.symlink_to(tmp_path, target_is_directory=True)
        selected = selected / artifact.name
    elif kind == "fifo":
        os.mkfifo(selected)
    result = checker.check(selected)
    assert not any(result.cases)
    assert result.artifact_sha256 is None
    summary = parse_junit_xml(result.report)
    assert summary.counts.failures == 9 and summary.counts.skipped == 0


def test_p3_exact_size_and_overflow(artifact):
    data = REFERENCE.encode()
    artifact.write_bytes(data + b"#" + b"x" * (checker.MAX_BYTES - len(data) - 1))
    assert checker.check(artifact).passed
    with artifact.open("ab") as stream:
        stream.write(b"x")
    assert not any(checker.check(artifact).cases)


@pytest.mark.parametrize(
    "data",
    [
        b"\xff",
        b"x=" + b"[" * 1500 + b"1" + b"]" * 1500,
        b"[tool.signal_note." + b"a." * 1100 + b"b]\nx=1",
    ],
)
def test_p3_bounded_invalid_encoding_and_deep_data(artifact, data):
    artifact.write_bytes(data)
    result = checker.check(artifact)
    assert result.cases[0] and not result.passed
    assert parse_junit_xml(result.report).counts.skipped == 0


@pytest.mark.parametrize("valid", [True, False])
def test_checker_command_exit_and_exclusive_report(
    artifact, tmp_path, monkeypatch, capsys, valid
):
    if not valid:
        artifact.write_text("[project]\n")
    report = tmp_path / "operator.xml"
    monkeypatch.setattr(
        sys, "argv", ["checker", str(artifact), "--report", str(report)]
    )
    assert checker.main() == (0 if valid else 1)
    summary = json.loads(capsys.readouterr().out)
    assert (
        summary["artifact_sha256"] == hashlib.sha256(artifact.read_bytes()).hexdigest()
    )
    assert summary["report_sha256"] == hashlib.sha256(report.read_bytes()).hexdigest()
    original = report.read_bytes()
    with pytest.raises(FileExistsError):
        checker.main()
    assert report.read_bytes() == original


@pytest.mark.parametrize(
    "old,new",
    [
        ('version = "0.2.0"', 'version = "0.3.0"'),
        (">=3.12,<3.14", ">=3.10"),
        ("hatchling.build", "setuptools.build_meta"),
        ("signal_note.cli:main", "signal_note.cli:other"),
        ("pytest>=8,<9", "pytest ???"),
        ('"pytest>=8,<9", "ruff>=0.12,<1"', '"pytest>=8,<9", "pytest>=8,<9"'),
        ("line-length = 88", "line-length = 100"),
        ("retention_days = 7", "retention_days = 8"),
        ('channel = "local"', 'channel = "remote"'),
        ("dependencies = []", 'dependencies = ["requests"]'),
        ("dependencies = []", "dependencies = 2026-01-01"),
        ("retention_days = 7", "retention_days = nan"),
        ("retention_days = 7", "retention_days = true"),
        ('name = "signal-note"', 'name = "signal-note"\ndynamic = ["version"]'),
    ],
)
def test_p4_p6_wrong_semantics_or_preservation(artifact, old, new):
    artifact.write_text(REFERENCE.replace(old, new))
    result = checker.check(artifact)
    assert result.cases[1] and not result.passed
    assert parse_junit_xml(result.report).counts.skipped == 0


@pytest.mark.parametrize(
    "changed",
    [
        REFERENCE.replace('requires-python = ">=3.12,<3.14"\n', ""),
        REFERENCE + '\n[project]\nversion = "9"\n',
        REFERENCE.replace('version = "0.2.0"', 'version = "0.2.0"\nversion = "9"'),
        REFERENCE + '\n[dependency-groups]\ndev = ["pytest<8"]\n',
        REFERENCE.replace('default_style = "compact"\n', ""),
        REFERENCE.replace("[tool.signal_note.labels]", "[tool.signal_note.other]"),
        'project = "wrong type"',
        "tool = []",
        "invalid = [",
    ],
)
def test_p5_omissions_duplicates_contradictions_and_types(artifact, changed):
    artifact.write_text(changed)
    assert not checker.check(artifact).passed


@pytest.fixture
def binding_workflow(tmp_path, artifact):
    """Disposable synthetic records only; no canonical real pilot is created."""
    db = Database(tmp_path / "synthetic.sqlite3")
    db.initialize()
    repo = Repository(db)
    now = utc_now()
    task = repo.create_task(
        Task(
            description="Synthetic W4B-P0 checker compatibility control",
            acceptance_spec=AcceptanceSpec(
                identifier="w4b-p0-signal-note-data", version="1"
            ),
            created_at=now - timedelta(seconds=3),
            metadata={
                "junit_verifier": junit_criterion(
                    required_test_ids=checker.REQUIRED_IDS
                )
            },
        )
    )
    result = checker.check(artifact)
    run = repo.create_run(
        Run(
            task_id=task.task_id,
            started_at=now - timedelta(seconds=2),
            ended_at=now - timedelta(seconds=1),
            metadata={"final_artifact_fingerprint": "sha256:" + result.artifact_sha256},
        )
    )
    report = tmp_path / "operator.xml"
    report.write_bytes(result.report)
    binding = JUnitReportBinding(
        task_id=task.task_id,
        run_id=run.run_id,
        acceptance_spec=task.acceptance_spec,
        artifact_fingerprint=run.metadata["final_artifact_fingerprint"],
        report_sha256=result.report_sha256,
        report_generated_at=now,
        source="junit",
        execution_completed=True,
        command_exit_code=0,
    )
    return repo, run, artifact, report, binding


def test_p8_existing_junit_binding(binding_workflow):
    repo, run, artifact, report, binding = binding_workflow
    evidence = verify_junit(
        repo, run_id=run.run_id, artifact=artifact, report=report, binding=binding
    )
    assert evidence.result.value == "pass"
    assert evidence.artifact_fingerprint == binding.artifact_fingerprint
    assert evidence.metadata["report_observed_sha256"] == binding.report_sha256


@pytest.mark.parametrize(
    "field",
    ["task_id", "run_id", "acceptance_spec", "artifact_fingerprint", "report_sha256"],
)
def test_p9_wrong_binding_fails_closed(binding_workflow, field):
    repo, run, artifact, report, binding = binding_workflow
    values = {
        "task_id": uuid4(),
        "run_id": uuid4(),
        "acceptance_spec": AcceptanceSpec(identifier="wrong", version="2"),
        "artifact_fingerprint": "sha256:" + "0" * 64,
        "report_sha256": "0" * 64,
    }
    with pytest.raises(ValueError):
        verify_junit(
            repo,
            run_id=run.run_id,
            artifact=artifact,
            report=report,
            binding=binding.model_copy(update={field: values[field]}),
        )
    assert not repo.list_records(Verification)


@pytest.mark.parametrize("target", ["artifact", "report"])
def test_p9_changed_bytes_fail_closed(binding_workflow, target):
    repo, run, artifact, report, binding = binding_workflow
    selected = artifact if target == "artifact" else report
    with selected.open("ab") as stream:
        stream.write(b"\n")
    with pytest.raises(ValueError):
        verify_junit(
            repo, run_id=run.run_id, artifact=artifact, report=report, binding=binding
        )
    assert not repo.list_records(Verification)


def test_manifest_frozen_start_contract_and_pending_approvals():
    manifest = json.loads(MANIFEST.read_text())
    assert manifest["version"] == "w4b-p0-prerun/1"
    for entry in [
        *manifest["starting_workspace"],
        manifest["instruction"],
        manifest["checker"],
    ]:
        assert (
            hashlib.sha256((ROOT / entry["path"]).read_bytes()).hexdigest()
            == entry["sha256"]
        )
    assert sorted(p.name for p in (FIXTURE / "start").iterdir()) == ["pyproject.toml"]
    assert manifest["acceptance"]["required_test_ids"] == list(checker.REQUIRED_IDS)
    assert manifest["allowed_outputs"] == ["pyproject.toml"]
    assert manifest["execution"]["attempts"] == 1
    assert manifest["execution"]["retries"] == 0
    assert manifest["execution"]["runtime_status"] == "EXTERNAL_RUNTIME_UNAPPROVED"
    assert manifest["resource_targets"][0]["budget"]["max_duration_seconds"] == 600
    assert manifest["resource_targets"][1]["budget"] is None
    assert manifest["selected_resource_target"] is None
    assert all(a["status"] == "pending" for a in manifest["approvals"])
    assert manifest["real_execution_records_created"] is False


def test_p12_public_synthetic_inputs_and_pure_privacy():
    paths = [
        FIXTURE / "TASK.md",
        FIXTURE / "start/pyproject.toml",
        MANIFEST,
        ROOT / "scripts/check_w4b_p0.py",
        Path(__file__),
        ROOT / "docs/W4B_P0_APPROVAL.md",
    ]
    for path in paths:
        assert not privacy_guard.path_reasons(str(path.relative_to(ROOT)))
        assert not privacy_guard.content_reasons(path.read_bytes())
    # Reviewed checker is data-only: no launch/import/eval/network/credential APIs.
    import ast

    tree = ast.parse((ROOT / "scripts/check_w4b_p0.py").read_text())
    imports = {
        n.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for n in node.names
    }
    assert imports <= {"argparse", "hashlib", "json", "os", "stat", "tomllib"}
    calls = {
        node.func.id
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
    }
    assert not calls & {"eval", "exec", "compile", "__import__"}
