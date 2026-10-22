"""W7A replay checks use only newly generated W6B fictional fixtures.

No private history, model execution, external authenticity or performance claim.
"""

import hashlib
import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import external_handoff_example as example


def hashes(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


@pytest.fixture
def retained(tmp_path):
    example.demonstrate(tmp_path)
    return tmp_path


def test_simplest_public_command():
    command = subprocess.run(
        [sys.executable, "-B", "scripts/external_handoff_example.py"],
        cwd=Path(__file__).parents[2],
        capture_output=True,
        text=True,
        check=True,
    )
    summary = json.loads(command.stdout)
    assert summary["origin"] == "fictional-offline-only"
    assert summary["eligible_outcomes"] == 2
    assert summary["forecast_probabilities"] == [0.5, 2 / 3]
    assert summary["scores"][1]["A"]["brier_score"] == pytest.approx(4 / 9)


def test_retain_then_replay_is_read_only(tmp_path, capsys):
    root = tmp_path / "new"
    assert example.main(["--output-directory", str(root)]) == 0
    original = json.loads(capsys.readouterr().out)
    before = hashes(root)
    for _ in range(2):
        assert example.main(["--replay-directory", str(root)]) == 0
        assert json.loads(capsys.readouterr().out) == original
        assert hashes(root) == before
    with pytest.raises(SystemExit) as error:
        example.main(["--output-directory", str(root)])
    assert error.value.code == 1
    assert hashes(root) == before


@pytest.mark.parametrize(
    "relative",
    [
        "intake.json",
        "policy.json",
        "forecast-0.json",
        "forecast-1.sha256",
        "handoff-0/answer.txt",
        "handoff-1/independent.xml",
        "handoff-0/execution.json",
        "handoff-0/execution-receipts.json",
        "handoff-1/resolved.json",
        "handoff-1/receipts.json",
        "advisory-input.json",
        "advisory.json",
        "summary.json",
    ],
)
def test_missing_evidence_refuses_without_writing(retained, relative, capsys):
    (retained / relative).unlink()
    before = hashes(retained)
    with pytest.raises(SystemExit) as error:
        example.main(["--replay-directory", str(retained)])
    assert error.value.code == 1
    assert not capsys.readouterr().out
    assert hashes(retained) == before


@pytest.mark.parametrize(
    "relative",
    [
        "handoff-0/answer.txt",
        "handoff-1/independent.xml",
        "forecast-0.json",
        "forecast-1.sha256",
        "handoff-0/receipts.json",
        "policy.json",
    ],
)
def test_changed_evidence_refuses_without_writing(retained, relative):
    path = retained / relative
    path.chmod(0o600)
    path.write_text("changed fictional evidence")
    before = hashes(retained)
    with pytest.raises((ValueError, KeyError)):
        example.replay(retained)
    assert hashes(retained) == before


@pytest.mark.parametrize("change", ["summary", "source", "first_receipt", "forecast"])
def test_valid_json_substitutions_refused(retained, change):
    if change == "summary":
        path, field, value = retained / "summary.json", "eligible_outcomes", 3
    elif change == "source":
        path, field, value = (
            retained / "intake.json",
            "trusted_fixture_sha256",
            "0" * 64,
        )
    elif change == "first_receipt":
        path, field, value = (
            retained / "handoff-0/execution-receipts.json",
            "receipts",
            {},
        )
    else:
        path, field, value = retained / "forecast-0.json", "task_id", "fictional-other"
    data = json.loads(path.read_text())
    data[field] = value
    path.chmod(0o600)
    path.write_text(json.dumps(data))
    if change == "forecast":
        # Even a matching local checksum cannot repair historical reconstruction.
        (retained / "forecast-0.sha256").write_text(example.file_sha256(path))
    before = hashes(retained)
    with pytest.raises(ValueError):
        example.replay(retained)
    assert hashes(retained) == before


def test_modes_are_exclusive(tmp_path):
    with pytest.raises(SystemExit) as error:
        example.main(
            [
                "--output-directory",
                str(tmp_path / "new"),
                "--replay-directory",
                str(tmp_path),
            ]
        )
    assert error.value.code == 2
    assert not (tmp_path / "new").exists()
