"""Deterministic synthetic observations and evaluator-only truth."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from model_learner.domain.models import DataSourceKind, Observation, OutcomeStatus
from model_learner.simulate import SimulationConfig, SimulationTruth, generate


def test_seeded_generation_and_extension_are_reproducible() -> None:
    config = SimulationConfig(seed=42, count=24)
    result = generate(config)
    assert result == generate(config)
    assert result != generate(SimulationConfig(seed=43, count=24))
    longer = generate(SimulationConfig(seed=42, count=48))
    assert result.observations == longer.observations[:24]
    assert result.truth.records == longer.truth.records[:24]
    assert len({row.observation_id for row in result.observations}) == 24


def test_all_twelve_cells_and_schema_contracts() -> None:
    result = generate(SimulationConfig(count=500))
    cells = {(row.configuration.model, row.task_group) for row in result.observations}
    assert len(cells) == 12
    for row in result.observations:
        assert Observation.model_validate_json(row.model_dump_json()) == row
        assert row.source_kind is DataSourceKind.SIMULATED
        assert row.schema_version == 2
        assert row.recorded_at >= row.decision_at
        assert row.configuration.model_version == "1"


def test_truth_never_appears_in_learner_records() -> None:
    result = generate(SimulationConfig(count=10, unknown_probability=1))
    assert all(
        row.outcome_status is OutcomeStatus.UNKNOWN for row in result.observations
    )
    assert all(row.label_available_at is None for row in result.observations)
    assert all(
        not row.eligible_for_configuration_learning for row in result.observations
    )
    for row in result.observations:
        serialized = row.model_dump_json()
        assert "success_probability" not in serialized
        assert "realized_success" not in serialized
        assert "probabilities" not in serialized
        assert "scenario_fingerprint" not in serialized
    assert len(result.truth.records) == 10
    assert (
        SimulationTruth.model_validate_json(result.truth.model_dump_json())
        == result.truth
    )


def test_controlled_imbalance_drift_and_missing_resources() -> None:
    config = SimulationConfig(
        count=6,
        unknown_probability=0,
        resource_missing_probability=1,
        arm_weights=(1, 0, 0),
        group_weights=(0, 0, 0, 1),
        probabilities=((0, 0, 0),) * 4,
        drift_at_index=3,
        drift_probabilities=((1, 1, 1),) * 4,
    )
    result = generate(config)
    assert [row.outcome_status for row in result.observations] == (
        [OutcomeStatus.FAILURE] * 3 + [OutcomeStatus.SUCCESS] * 3
    )
    assert {row.configuration.model for row in result.observations} == {"arm-a"}
    assert {row.task_group for row in result.observations} == {"group-d"}
    assert all(
        row.cost_usd is None and row.latency_seconds is None
        for row in result.observations
    )
    assert [record.success_probability for record in result.truth.records] == [
        0
    ] * 3 + [1] * 3


def test_resources_include_measured_zero_without_unknown_zero_substitution() -> None:
    result = generate(
        SimulationConfig(
            count=20,
            resource_missing_probability=0,
            arm_weights=(1, 0, 0),
            cost_means_usd=(0, 0.1, 1),
            latency_means_seconds=(12, 15, 18),
            resource_log_sigma=0,
        )
    )
    assert all(row.cost_usd == 0 for row in result.observations)
    assert all(row.latency_seconds == pytest.approx(12) for row in result.observations)


@pytest.mark.parametrize(
    "changes",
    [
        {"start_at": datetime(2026, 1, 1)},
        {"probabilities": ((0.5, 0.5, 0.5),)},
        {"probabilities": ((2, 0, 0),) * 4},
        {"arm_weights": (0, 0, 0)},
        {"group_weights": (-1, 1, 1, 1)},
        {"drift_at_index": 5},
        {"resource_log_sigma": float("nan")},
        {"cost_means_usd": (-1, 0, 0)},
    ],
)
def test_invalid_scenarios_fail(changes: dict) -> None:
    with pytest.raises(ValidationError):
        SimulationConfig(**changes)


def test_empty_generation_has_explicit_dataset_and_no_truth_rows() -> None:
    result = generate(SimulationConfig(count=0))
    assert result.observations == ()
    assert result.truth.records == ()
    assert result.truth.dataset.dataset_id == "synthetic-reference"
