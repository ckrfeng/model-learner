"""Explicit model selection and opt-in actual pretrained evaluation."""

import json
import os
import socket
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.representation import (
    evaluate_task_representation,
    generate_representation_fixture,
)
from model_learner.representation.potion import (
    MODEL_ID,
    MODEL_REVISION,
    digest_potion_bundle,
    load_potion_encoder,
)

MODEL_PATH = os.environ.get("MODEL_LEARNER_TEST_POTION_PATH")
START = datetime(2026, 1, 1, tzinfo=UTC)


def arguments(path):
    return [
        "learn",
        "representation-eval",
        "--input-file",
        str(path),
        "--source-kind",
        "simulated",
        "--dataset-id",
        "task-state-state_signal-seed-1",
        "--dataset-version",
        "1",
        "--acceptance-id",
        "controlled-task-acceptance",
        "--acceptance-version",
        "1",
        "--train-until",
        "2026-01-01T04:30:00Z",
        "--evaluation-at",
        "2026-01-01T07:30:00Z",
    ]


def test_explicit_potion_failure_reports_requested_model_and_retains_baselines(
    tmp_path,
):
    runner = CliRunner()
    path = tmp_path / "public.json"
    assert (
        runner.invoke(app, ["sim", "representation-fixture", str(path)]).exit_code == 0
    )
    reference = runner.invoke(app, arguments(path))
    assert reference.exit_code == 0
    attempted = runner.invoke(
        app,
        [
            *arguments(path),
            "--model-id",
            MODEL_ID,
            "--model-path",
            str(tmp_path),
            "--model-revision",
            MODEL_REVISION,
            "--model-sha256",
            "0" * 64,
        ],
    )
    assert attempted.exit_code == 0, attempted.output
    before, after = json.loads(reference.output), json.loads(attempted.output)
    assert after["variants"][:2] == before["variants"][:2]
    assert after["cohort_sha256"] == before["cohort_sha256"]
    assert after["variants"][2]["status"] == "semantic_unavailable"
    assert after["overhead"]["semantic"]["model_id"] == MODEL_ID
    assert after["overhead"]["semantic"]["actual_load_seconds"] is None
    assert "torch" not in after["overhead"]["semantic"]["available_packages"]
    assert after["overhead"]["semantic"]["estimated_parameter_bytes"] == 30_236_672


def test_unknown_model_and_potion_without_bundle_fail_before_inference(tmp_path):
    runner = CliRunner()
    path = tmp_path / "missing.json"
    for model_id in ("unknown-model", MODEL_ID):
        assert (
            runner.invoke(app, [*arguments(path), "--model-id", model_id]).exit_code
            == 2
        )


@pytest.mark.skipif(
    not MODEL_PATH, reason="explicit approved local Potion bundle required"
)
def test_actual_pretrained_c_shares_cohort_and_preserves_a_b_without_network(
    monkeypatch,
):
    def deny(*args, **kwargs):
        raise AssertionError("CPU evaluation attempted a network connection")

    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    digest, _ = digest_potion_bundle(MODEL_PATH)
    encoder = load_potion_encoder(
        MODEL_PATH, expected_sha256=digest, revision=MODEL_REVISION
    )
    rows = generate_representation_fixture(seed=1, count=150)
    result = evaluate_task_representation(
        rows,
        dataset=rows[0].state.observation.dataset,
        acceptance_spec=rows[0].state.observation.acceptance_spec,
        train_until=START + timedelta(seconds=180 * 90),
        evaluation_at=START + timedelta(seconds=180 * 150),
        encoder=encoder,
        semantic_model_id=MODEL_ID,
    )
    stored = json.loads(
        (
            Path(__file__).parents[1]
            / "fixtures/representation/controlled_reference.json"
        ).read_text()
    )
    baseline = stored["scenarios"]["state_signal"]["reports"][1]
    assert result.cohort_sha256 == baseline["cohort_sha256"]
    for variant, previous in zip(
        result.variants[:2], baseline["variants"][:2], strict=True
    ):
        current = asdict(variant)
        current.pop("predictions")
        assert json.loads(json.dumps(current)) == previous
    assert all(v.status == "evaluated" for v in result.variants)
    assert len({tuple(unit for unit, _ in v.predictions) for v in result.variants}) == 1
    assert result.variants[2].brier_score == pytest.approx(
        0.05728864862252687, abs=1e-7
    )
    assert result.overhead["semantic"]["device"] == "cpu"
    assert result.overhead["semantic"]["actual_load_seconds"] > 0
    assert result.overhead["semantic"]["actual_inference_seconds"] > 0
    assert result.overhead["semantic"]["actual_model_memory_bytes"] == 30_236_672
    assert rows[0].description.text not in json.dumps(asdict(result))
