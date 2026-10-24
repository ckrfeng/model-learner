"""M7 fictional CLI inputs and temporary ignored roots; no user ledger access."""

import hashlib
import json
import os
import stat

import pytest
from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.commands import learning
from model_learner.learn import advisory, utility
from model_learner.learn.advisory import AdvisoryInput
from model_learner.storage.database import Database
from tests.unit.test_advisory import request
from tests.unit.test_prospective import LOW, LOW2, row
from tests.unit.test_utility import DECISION, policy


@pytest.fixture
def setup(tmp_path, monkeypatch):
    base = tmp_path / ".model-learner"
    monkeypatch.setattr(learning, "_SHADOW_BASE", base)

    def forbidden(*args, **kwargs):
        raise AssertionError("unexpected ledger access")

    monkeypatch.setattr(learning, "repository", forbidden)
    monkeypatch.setattr(Database, "__init__", forbidden)
    req = request(candidates=(LOW, LOW2))
    req.task.description = "synthetic-private-prose"
    req.task.metadata = {"locator": "/synthetic/private/source"}
    source = row(
        1,
        cost_usd=2,
        latency_seconds=10,
        metadata={"payload": "synthetic-private-payload"},
    )
    data = AdvisoryInput(
        request=req,
        observations=(
            source,
            row(2, configuration=LOW2, cost_usd=5, latency_seconds=30),
        ),
    )
    envelope = {
        "version": "explicit-utility-shadow-input/v1",
        "advisory": data.model_dump(mode="json"),
        "policy": policy("cost-sensitive/v1"),
        "predictor": "A",
        "decision_at": DECISION.isoformat(),
        "human_selected_configuration_id": LOW2.configuration_id,
    }
    path = tmp_path / "input.json"
    path.write_text(json.dumps(envelope))
    return base, path, envelope


def invoke(path, destination):
    return CliRunner().invoke(
        app,
        [
            "learn",
            "shadow",
            "--input-file",
            str(path),
            "--output-file",
            str(destination),
        ],
    )


def test_actual_command_one_snapshot_privacy_digest_human_separation_and_replay(
    setup, monkeypatch
):
    base, path, envelope = setup
    output = base / "shadow" / "nested" / "choice.json"
    input_before = path.read_bytes()
    calls = {"advise": 0, "utility": 0}
    advise = advisory.advise
    evaluate = utility.evaluate_utility

    def one_advise(*args, **kwargs):
        calls["advise"] += 1
        return advise(*args, **kwargs)

    def one_utility(*args, **kwargs):
        calls["utility"] += 1
        return evaluate(*args, **kwargs)

    monkeypatch.setattr(advisory, "advise", one_advise)
    monkeypatch.setattr(utility, "evaluate_utility", one_utility)
    result = invoke(path, output)
    assert result.exit_code == 0, result.output
    assert calls == {"advise": 1, "utility": 1}
    record = json.loads(result.output)
    assert json.loads(output.read_text()) == record
    assert record["input_sha256"] == hashlib.sha256(input_before).hexdigest()
    assert record["human_selected_configuration_id"] == LOW2.configuration_id
    assert record["advice"]["selected_configuration_id"] == LOW.configuration_id
    assert (
        record["human_selected_configuration_id"]
        != record["advice"]["selected_configuration_id"]
    )
    for marker in (
        "synthetic-private-prose",
        "synthetic-private-payload",
        "/synthetic/private",
        "source_record_id",
        "observation_id",
    ):
        assert marker not in result.output and marker not in output.read_text()
    assert set(base.rglob("*.json")) == {output}
    assert not (base / "model-learner.sqlite3").exists()
    assert path.read_bytes() == input_before
    if os.name == "posix":
        assert stat.S_IMODE(output.stat().st_mode) == 0o600
        assert stat.S_IMODE(output.parent.stat().st_mode) == 0o700
    before = output.read_bytes()
    duplicate = invoke(path, output)
    assert duplicate.exit_code != 0
    assert output.read_bytes() == before and path.read_bytes() == input_before
    assert (
        "invalid shadow input, evidence or create-only destination" in duplicate.output
    )


@pytest.mark.parametrize(
    "kind",
    [
        "traversal",
        "outside",
        "root",
        "file-symlink",
        "directory-symlink",
        "base-symlink",
        "shadow-symlink",
    ],
)
def test_output_confinement_and_symlink_refusal(setup, tmp_path, kind):
    base, path, _ = setup
    outside = tmp_path / "outside"
    outside.mkdir()
    sentinel = outside / "sentinel.json"
    sentinel.write_bytes(b"fictional existing bytes")
    if kind == "traversal":
        output = base / "shadow" / ".." / "escape.json"
    elif kind == "outside":
        output = outside / "new.json"
    elif kind == "root":
        output = base / "shadow"
    elif kind == "base-symlink":
        base.symlink_to(outside, target_is_directory=True)
        output = base / "shadow" / "new.json"
    else:
        base.mkdir()
        if kind == "shadow-symlink":
            (base / "shadow").symlink_to(outside, target_is_directory=True)
            output = base / "shadow" / "new.json"
        else:
            (base / "shadow").mkdir()
            if kind == "directory-symlink":
                (base / "shadow" / "linked").symlink_to(
                    outside, target_is_directory=True
                )
                output = base / "shadow" / "linked" / "new.json"
            else:
                output = base / "shadow" / "linked.json"
                output.symlink_to(sentinel)
    before = path.read_bytes()
    result = invoke(path, output)
    assert result.exit_code != 0
    assert sentinel.read_bytes() == b"fictional existing bytes"
    assert set(outside.iterdir()) == {sentinel}
    assert path.read_bytes() == before
    assert not (base / "escape.json").exists()


@pytest.mark.parametrize(
    "kind",
    [
        "bad-human",
        "missing-policy-field",
        "extra-policy",
        "invalid-json",
        "missing-timestamp",
    ],
)
def test_bad_envelope_safe_errors_no_record(setup, kind):
    base, path, envelope = setup
    marker = "synthetic-private-payload"
    if kind == "bad-human":
        envelope["human_selected_configuration_id"] = "0" * 64
    elif kind == "missing-policy-field":
        del envelope["policy"]["maximum_cost_usd"]
    elif kind == "extra-policy":
        envelope["policy"]["unexpected"] = marker
    elif kind == "missing-timestamp":
        del envelope["decision_at"]
    if kind == "invalid-json":
        path.write_text(marker)
    else:
        path.write_text(json.dumps(envelope))
    result = invoke(path, base / "shadow" / "record.json")
    assert result.exit_code != 0
    assert marker not in result.output
    assert not base.exists()


def test_null_human_and_explicit_output_required(setup):
    base, path, envelope = setup
    envelope["human_selected_configuration_id"] = None
    path.write_text(json.dumps(envelope))
    absent = CliRunner().invoke(app, ["learn", "shadow", "--input-file", str(path)])
    assert absent.exit_code != 0 and not base.exists()
    result = invoke(path, base / "shadow" / "record.json")
    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["human_selected_configuration_id"] is None


def test_existing_advise_command_remains_abstain_only(setup, tmp_path):
    base, _, envelope = setup
    path = tmp_path / "advisory.json"
    path.write_text(json.dumps(envelope["advisory"]))
    result = CliRunner().invoke(app, ["learn", "advise", "--input-file", str(path)])
    assert result.exit_code == 0, result.output
    output = json.loads(result.output)
    assert output["advisory"]["status"] == "abstain"
    assert output["advisory"]["selected_configuration_id"] is None
    assert output["versions"]["decision_policy"] == "abstain-only/v1"
    assert not base.exists()
