"""Portable inspection creates no ledger and keeps invalid private input private."""

import json
from pathlib import Path

from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.execution.longitudinal import TrajectoryInput
from tests.unit.test_execution_analysis import SESSION, at, event
from tests.unit.test_longitudinal import DATASET, inputs

RUNNER = CliRunner()
FIXTURE = Path(__file__).parents[1] / "fixtures/longitudinal/scenarios.json"


def test_task_trajectory_prints_scoped_checkpoints_without_ledger_writes(tmp_path):
    task, run = inputs()
    package = TrajectoryInput(
        dataset=DATASET,
        task=task,
        run=run,
        session_id=SESSION,
        checkpoints=(at(5), at(10)),
        association_available_at=at(0),
        events=(event(2, "turn.started"), event(7, "turn.completed")),
    )
    source = tmp_path / "input.json"
    source.write_text(package.model_dump_json())
    result = RUNNER.invoke(app, ["task", "trajectory", str(source)])
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["changes"][0]["dimensions"] == ["activity"]
    assert report["checkpoints"][1]["verified_task_success"] is None
    assert report["checkpoints"][1]["identity"]["objective"] is None
    assert list(tmp_path.iterdir()) == [source]


def test_invalid_private_input_is_not_echoed_in_cli_diagnostics(tmp_path):
    source = tmp_path / "input.json"
    source.write_text('{"private_secret":"sensitive-content"}')
    for command in (["task", "trajectory"], ["learn", "trajectory-eval"]):
        result = RUNNER.invoke(app, [*command, str(source)])
        assert result.exit_code == 2
        assert "sensitive-content" not in result.output
        assert "private_secret" not in result.output


def test_partial_semantic_options_rejected_before_model_access(tmp_path):
    result = RUNNER.invoke(
        app,
        [
            "learn",
            "trajectory-eval",
            str(tmp_path / "input.json"),
            "--model-path",
            str(tmp_path / "model"),
        ],
    )
    assert result.exit_code == 2
    assert "Potion requires" in result.output


def test_evaluation_writes_exclusive_report_and_preserves_unknown_outcomes(tmp_path):
    output = tmp_path / "report.json"
    args = ["learn", "trajectory-eval", str(FIXTURE), "--output", str(output)]
    result = RUNNER.invoke(app, args)
    assert result.exit_code == 0, result.output
    report = json.loads(output.read_text())
    assert report["downstream_outcome_prediction"]["status"] == "insufficient_data"
    assert report["state_change_recognition"]["C"]["status"] == "unavailable"
    assert report["unsupported_inference_guardrails"]["violation_count"] == 0
    previous = output.read_bytes()
    replay = RUNNER.invoke(app, args)
    assert replay.exit_code == 2
    assert output.read_bytes() == previous


def test_missing_potion_keeps_deterministic_report_and_explicit_unavailability(
    tmp_path,
):
    result = RUNNER.invoke(
        app,
        [
            "learn",
            "trajectory-eval",
            str(FIXTURE),
            "--model-path",
            str(tmp_path / "absent-model"),
            "--model-revision",
            "bf8b056651a2c21b8d2565580b8569da283cab23",
            "--model-sha256",
            "930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2",
        ],
    )
    assert result.exit_code == 0, result.output
    report = json.loads(result.output)
    assert report["state_change_recognition"]["C"]["status"] == "unavailable"
    assert "semantic_unavailable_reason" in report
    assert report["state_change_recognition"]["B"]["case_count"] == 7
