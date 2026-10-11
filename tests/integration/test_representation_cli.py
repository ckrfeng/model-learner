"""Public offline inputs and optional semantic loading through the CLI."""

import json
from datetime import UTC, datetime, timedelta

from typer.testing import CliRunner

from model_learner.cli import app


def _arguments(path, seed=1, count=150):
    start = datetime(2026, 1, 1, tzinfo=UTC)
    return [
        "learn",
        "representation-eval",
        "--input-file",
        str(path),
        "--source-kind",
        "simulated",
        "--dataset-id",
        f"task-state-state_signal-seed-{seed}",
        "--dataset-version",
        "1",
        "--acceptance-id",
        "controlled-task-acceptance",
        "--acceptance-version",
        "1",
        "--train-until",
        (start + timedelta(seconds=180 * int(count * 0.6))).isoformat(),
        "--evaluation-at",
        (start + timedelta(seconds=180 * count)).isoformat(),
        "--bootstrap-replicates",
        "100",
    ]


def test_public_representation_fixture_and_no_model_evaluation(tmp_path):
    runner = CliRunner()
    path = tmp_path / "public.json"
    generated = runner.invoke(app, ["sim", "representation-fixture", str(path)])
    assert generated.exit_code == 0, generated.output
    assert json.loads(generated.output)["source_kind"] == "simulated"
    evaluated = runner.invoke(app, _arguments(path))
    assert evaluated.exit_code == 0, evaluated.output
    report = json.loads(evaluated.output)
    assert report["training_count"] >= 30
    assert report["scored_count"] >= 20
    assert len(report["variants"]) == 3
    assert report["variants"][0]["status"] == "evaluated"
    assert report["variants"][1]["status"] == "evaluated"
    assert report["variants"][2]["brier_score"] is None
    assert "unavailable" in report["variants"][2]["status"]
    assert not list(tmp_path.glob("*.sqlite3"))
    overwrite = runner.invoke(app, ["sim", "representation-fixture", str(path)])
    assert overwrite.exit_code == 2


def test_model_loading_requires_full_pin_and_invalid_input_is_sanitized(tmp_path):
    runner = CliRunner()
    path = tmp_path / "private.json"
    path.write_text('[{"private_transcript": "PRIVATE-CONTENT-CANARY"}]')
    result = runner.invoke(app, _arguments(path))
    assert result.exit_code == 2
    assert "PRIVATE-CONTENT-CANARY" not in result.output
    missing_pin = runner.invoke(app, [*_arguments(path), "--model-path", str(tmp_path)])
    assert missing_pin.exit_code == 2
    assert "all three model options" in missing_pin.output


def test_unavailable_pinned_model_preserves_baseline_scores(tmp_path, monkeypatch):
    from model_learner import representation

    def unavailable(*args, **kwargs):
        raise representation.SemanticUnavailable("local CPU runtime unavailable")

    monkeypatch.setattr(representation, "load_cpu_encoder", unavailable)
    runner = CliRunner()
    path = tmp_path / "public.json"
    assert (
        runner.invoke(app, ["sim", "representation-fixture", str(path)]).exit_code == 0
    )
    evaluated = runner.invoke(
        app,
        [
            *_arguments(path),
            "--model-path",
            str(tmp_path / "operator-model"),
            "--model-sha256",
            "a" * 64,
            "--model-revision",
            "b" * 40,
        ],
    )
    assert evaluated.exit_code == 0, evaluated.output
    report = json.loads(evaluated.output)
    assert report["variants"][0]["status"] == "evaluated"
    assert report["variants"][2]["brier_score"] is None
    assert report["overhead"]["semantic"]["reason"] == ("local CPU runtime unavailable")


def test_representation_commands_are_visible_in_help():
    runner = CliRunner()
    assert "representation-eval" in runner.invoke(app, ["learn", "--help"]).output
    assert "representation-fixture" in runner.invoke(app, ["sim", "--help"]).output
