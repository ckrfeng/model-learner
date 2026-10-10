"""Exercise independent observation and learning slices through the local CLI."""

import json
from pathlib import Path

from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.domain.models import (
    Event,
    ExecutionConfiguration,
    Observation,
    Outcome,
    Provenance,
)
from model_learner.storage.database import Database, Repository

runner = CliRunner()


def invoke(arguments: list[str], *, input: str | None = None) -> dict | list:
    result = runner.invoke(app, arguments, input=input)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


def initialize(path: Path) -> Repository:
    result = runner.invoke(app, ["init", "--database", str(path)])
    assert result.exit_code == 0, result.output
    return Repository(Database(path))


def test_capture_import_and_timeline_preserve_unknowns(tmp_path: Path) -> None:
    database = tmp_path / "ledger.sqlite3"
    ledger = initialize(database)
    capture = tmp_path / "capture.jsonl"
    native = [
        {"type": "thread.started", "thread_id": "sanitized-thread"},
        {
            "type": "item.completed",
            "item": {
                "id": "item-1",
                "type": "command_execution",
                "command": "echo private-command-content",
                "aggregated_output": "private-output",
                "exit_code": 0,
                "status": "completed",
            },
        },
        {"type": "turn.completed", "usage": {"input_tokens": 12, "output_tokens": 3}},
    ]
    captured = invoke(
        ["capture", "codex", str(capture), "--source-version", "test-version"],
        input="\n".join(json.dumps(event) for event in native),
    )
    assert captured["accepted"] == 3
    assert "private-output" not in capture.read_text()
    assert "private-command-content" not in capture.read_text()
    arguments = [
        "import",
        "codex",
        str(capture),
        "--machine-id",
        "test-machine",
        "--database",
        str(database),
    ]
    first = invoke(arguments)
    second = invoke(arguments)
    assert first["events_inserted"] == 3
    assert second["events_inserted"] == 0
    assert second["events_duplicate"] == 3
    sessions = invoke(["sessions", "--database", str(database)])
    detail = invoke(
        ["session", "show", sessions[0]["session_id"], "--database", str(database)]
    )
    assert detail["summary"]["usage"]["input_tokens"] == 12
    assert detail["summary"]["usage"]["cached_input_tokens"] is None
    assert detail["summary"]["native_started_at"] is None
    assert detail["summary"]["cost_usd"] is None
    assert detail["summary"]["verification"] == "unknown"
    assert len(detail["timeline"]) == 3
    assert ledger.list_records(Outcome) == []
    assert ledger.list_observations("real") == []
    assert all(event.provenance == "observed" for event in ledger.list_records(Event))
    first_event = ledger.list_records(Event)[0]
    ledger.add_event(
        Event(
            observed_at=first_event.observed_at,
            source="codex.exec",
            source_version="unknown",
            machine_id="test-machine",
            capture_method="manual",
            native_session_id="sanitized-thread",
            session_id=first_event.session_id,
            event_type="manual-note",
            provenance=Provenance.OBSERVED,
            payload={"capture_id": [], "sequence": {}},
        )
    )
    manual_detail = invoke(
        ["session", "show", sessions[0]["session_id"], "--database", str(database)]
    )
    assert len(manual_detail["timeline"]) == 4
    assert manual_detail["summary"]["unsupported_event_count"] == 1


def test_capture_diagnostics_and_existing_destination_are_nonzero(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "captured.jsonl"
    result = runner.invoke(
        app,
        ["capture", "codex", str(destination), "--source-version", "test"],
        input='private-invalid-json\n{"type":"thread.started","thread_id":"t"}\n',
    )
    assert result.exit_code == 1
    assert json.loads(result.output)["accepted"] == 1
    assert "private-invalid-json" not in result.output
    original = destination.read_bytes()
    repeated = runner.invoke(
        app,
        ["capture", "codex", str(destination), "--source-version", "test"],
        input='{"type":"turn.started"}\n',
    )
    assert repeated.exit_code == 2
    assert destination.read_bytes() == original


def test_simulation_prediction_and_evaluation_cli(tmp_path: Path) -> None:
    database = tmp_path / "ledger.sqlite3"
    ledger = initialize(database)
    truth = tmp_path / "truth.json"
    scenario = tmp_path / "scenario.json"
    scenario.write_text(json.dumps({"unknown_probability": 0}))
    arguments = [
        "sim",
        "generate",
        "--seed",
        "7",
        "--count",
        "100",
        "--dataset-id",
        "cli-sim",
        "--config-file",
        str(scenario),
        "--database",
        str(database),
    ]
    generated = invoke(arguments + ["--truth-output", str(truth)])
    invoke(arguments)
    assert len(ledger.list_records(Observation, source_kind="simulated")) == 100
    assert ledger.list_observations("real") == []
    config_id = next(iter(generated["configurations"]))
    selector = [
        "--source-kind",
        "simulated",
        "--dataset-id",
        "cli-sim",
        "--dataset-version",
        "1",
        "--acceptance-id",
        "simulated-binary-success",
        "--acceptance-version",
        "1",
        "--database",
        str(database),
    ]
    predicted = invoke(
        [
            "learn",
            "predict",
            *selector,
            "--cutoff",
            "2026-01-01T00:50:00Z",
            "--configuration-id",
            config_id,
            "--group",
            "group-a",
        ]
    )
    assert 0 < predicted["prediction"]["success_probability"] < 1
    assert predicted["training"]["eligible_label_count"] == 50
    evaluated = invoke(
        [
            "learn",
            "eval",
            *selector,
            "--train-until",
            "2026-01-01T00:50:00Z",
            "--evaluation-at",
            "2026-01-02T00:00:00Z",
            "--truth-file",
            str(truth),
        ]
    )
    assert evaluated["held_out_count"] == 50
    assert evaluated["scored_label_count"] == 50
    assert {b["aggregation"] for b in evaluated["baselines"]} == {
        "global",
        "per_arm",
        "unpooled",
    }
    assert all(b["truth"]["count"] == 50 for b in evaluated["baselines"])
    assert all(b["brier_score"] is not None for b in evaluated["baselines"])
    invalid_time = runner.invoke(
        app,
        [
            "learn",
            "predict",
            *selector,
            "--cutoff",
            "2026-01-01T00:50:00",
            "--configuration-id",
            config_id,
            "--group",
            "group-a",
        ],
    )
    assert invalid_time.exit_code == 2
    assert "timezone" in invalid_time.output


def test_empty_dataset_prediction_shows_prior(tmp_path: Path) -> None:
    database = tmp_path / "ledger.sqlite3"
    initialize(database)
    configuration = tmp_path / "configuration.json"
    configuration.write_text(ExecutionConfiguration(model="unseen").model_dump_json())
    predicted = invoke(
        [
            "learn",
            "predict",
            "--source-kind",
            "real",
            "--dataset-id",
            "empty",
            "--dataset-version",
            "1",
            "--acceptance-id",
            "human-acceptance",
            "--acceptance-version",
            "1",
            "--cutoff",
            "2026-10-10T00:00:00Z",
            "--configuration-file",
            str(configuration),
            "--group",
            "repair",
            "--database",
            str(database),
        ]
    )
    assert predicted["prediction"]["success_probability"] == 0.5
    assert predicted["prediction"]["upper"] - predicted["prediction"]["lower"] > 0.9
    assert predicted["prediction"]["resources"]["cost_usd"]["mean"] is None
    assert predicted["acceptance_spec"]["identifier"] == "human-acceptance"
    assert predicted["resource_budget"] is None


def test_scenario_options_survive_unset_cli_defaults(tmp_path: Path) -> None:
    database = tmp_path / "ledger.sqlite3"
    initialize(database)
    scenario = tmp_path / "scenario.json"
    scenario.write_text(
        json.dumps(
            {"seed": 93, "count": 3, "dataset_id": "scenario", "dataset_version": "v2"}
        )
    )
    generated = invoke(
        [
            "sim",
            "generate",
            "--config-file",
            str(scenario),
            "--database",
            str(database),
        ]
    )
    assert generated["observations_processed"] == 3
    assert generated["dataset"]["dataset_id"] == "scenario"
    assert generated["dataset"]["dataset_version"] == "v2"
