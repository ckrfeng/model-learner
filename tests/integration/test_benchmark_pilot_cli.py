"""Operator preregistration is usable without any agent or execution backend."""

import json

from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.domain.models import ExecutionConfiguration


def test_pilot_cli_freezes_paired_initial_states_and_reports_gates(tmp_path):
    configurations = []
    for arm, reasoning in (("a", "low"), ("b", "high")):
        path = tmp_path / f"{arm}.json"
        path.write_text(
            ExecutionConfiguration(
                provider="fixture",
                model="fixture-model",
                reasoning_level=reasoning,
                harness="fixture",
                harness_version="1",
                configuration_version="1",
            ).model_dump_json()
        )
        configurations.append(path)
    invocation = CliRunner().invoke(
        app,
        [
            "benchmark",
            "pilot-plan",
            "--configuration-a",
            str(configurations[0]),
            "--configuration-b",
            str(configurations[1]),
        ],
    )
    assert invocation.exit_code == 0, invocation.output
    plan = json.loads(invocation.output)
    assert len(plan["runs"]) == 24
    for first, second in zip(plan["runs"][::2], plan["runs"][1::2], strict=True):
        assert first["fixture_id"] == second["fixture_id"]
        assert first["initial_source_sha256"] == second["initial_source_sha256"]
        assert first["task_description_sha256"] == second["task_description_sha256"]
        assert first["configuration"] != second["configuration"]
    assert plan["execution_status"] == "blocked_unvalidated_containment"
    assert "insufficient_data" in plan["predictive_status"]
    assert sorted(path.name for path in tmp_path.iterdir()) == ["a.json", "b.json"]


def test_invalid_pilot_config_diagnostic_omits_private_values(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text('{"configuration_id":"PRIVATE_SENTINEL"}')
    invocation = CliRunner().invoke(
        app,
        [
            "benchmark",
            "pilot-plan",
            "--configuration-a",
            str(path),
            "--configuration-b",
            str(path),
        ],
    )
    assert invocation.exit_code == 2
    assert "invalid pilot execution configuration" in invocation.output
    assert "PRIVATE_SENTINEL" not in invocation.output
