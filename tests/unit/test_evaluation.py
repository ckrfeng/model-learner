"""Held-out scores, truth comparisons and temporal leakage barriers."""

import math
from datetime import timedelta

import pytest

from model_learner.domain.models import AcceptanceSpec, DatasetReference, Observation
from model_learner.learn import evaluate
from model_learner.simulate import (
    SimulationConfig,
    SimulationTruth,
    TruthRecord,
    generate,
)

TARGET = AcceptanceSpec(identifier="simulated-binary-success", version="1")


def test_hand_computed_frozen_prefix_scores() -> None:
    result = generate(
        SimulationConfig(
            count=4,
            unknown_probability=0,
            resource_missing_probability=1,
            probabilities=((1, 1, 1),) * 4,
            arm_weights=(1, 0, 0),
            group_weights=(1, 0, 0, 0),
        )
    )
    cutoff = result.observations[2].decision_at
    report = evaluate(
        result.observations,
        dataset=result.truth.dataset,
        train_until=cutoff,
        evaluation_at=result.observations[-1].recorded_at,
        acceptance_spec=TARGET,
        truth=result.truth,
        calibration_bins=4,
    )
    assert report.training.eligible_label_count == 2
    assert report.held_out_count == report.scored_label_count == 2
    assert report.held_out_resources.cost_usd.missing_count == 2
    assert [metric.aggregation for metric in report.baselines] == [
        "global",
        "per_arm",
        "unpooled",
    ]
    for metric in report.baselines:
        assert metric.brier_score == pytest.approx((0.75 - 1) ** 2)
        assert metric.log_loss == pytest.approx(-math.log(0.75))
        assert sum(item.count for item in metric.calibration) == 2
        assert metric.calibration[-1].observed_success_rate == 1
        assert metric.calibration[-1].mean_prediction == 0.75
        assert metric.truth.count == 2
        assert metric.truth.mean_absolute_error == 0.25
        assert (
            metric.truth.interval_coverage == 0
        )  # point p=1 is outside a continuous posterior
        assert len(metric.grouped_truth) == 1


def test_future_training_labels_and_held_out_labels_do_not_train() -> None:
    result = generate(
        SimulationConfig(
            count=5,
            unknown_probability=0,
            verification_delay_seconds=180,
            probabilities=((1, 1, 1),) * 4,
            arm_weights=(1, 0, 0),
            group_weights=(1, 0, 0, 0),
        )
    )
    report = evaluate(
        result.observations,
        dataset=result.truth.dataset,
        train_until=result.observations[2].decision_at,
        evaluation_at=result.observations[-1].recorded_at,
        acceptance_spec=TARGET,
        truth=result.truth,
    )
    assert report.training.eligible_label_count == 0
    assert report.scored_label_count == 3
    for metric in report.baselines:
        assert metric.brier_score == 0.25
        assert metric.log_loss == pytest.approx(math.log(2))
    # Alter test outcomes only: latent-label scores change, trained estimates do not.
    changed = []
    for row in result.observations:
        values = row.model_dump(exclude={"stable_key"})
        if row.decision_at >= result.observations[2].decision_at:
            values["outcome_status"] = "failure"
        changed.append(Observation.model_validate(values))
    altered = evaluate(
        changed,
        dataset=result.truth.dataset,
        train_until=result.observations[2].decision_at,
        evaluation_at=result.observations[-1].recorded_at,
        acceptance_spec=TARGET,
    )
    assert altered.training == report.training
    assert altered.baselines[2].brier_score == report.baselines[2].brier_score


def test_unknown_labels_have_no_scores_but_can_be_evaluated_against_truth() -> None:
    result = generate(SimulationConfig(count=10, unknown_probability=1))
    report = evaluate(
        result.observations,
        dataset=result.truth.dataset,
        train_until=result.observations[4].decision_at,
        evaluation_at=result.observations[-1].recorded_at,
        acceptance_spec=TARGET,
        truth=result.truth,
    )
    assert report.held_out_count == 6
    assert report.scored_label_count == 0
    assert report.exclusions["missing_or_nonbinary_label"] == 6
    for metric in report.baselines:
        assert metric.brier_score is None
        assert metric.log_loss is None
        assert metric.truth.count == 6
        assert all(item.mean_prediction is None for item in metric.calibration)
    assert report.missing_truth_count == 0


def test_baselines_pool_only_in_explicit_comparisons() -> None:
    result = generate(SimulationConfig(count=100, seed=42, unknown_probability=0))
    report = evaluate(
        result.observations,
        dataset=result.truth.dataset,
        train_until=result.observations[60].decision_at,
        evaluation_at=result.observations[-1].recorded_at,
        acceptance_spec=TARGET,
        truth=result.truth,
    )
    assert report.training.eligible_label_count == 60
    assert report.scored_label_count == 40
    assert len({item.brier_score for item in report.baselines}) == 3
    assert report.baselines[2].truth.root_mean_squared_error >= 0
    assert report == evaluate(
        result.observations,
        dataset=result.truth.dataset,
        train_until=result.observations[60].decision_at,
        evaluation_at=result.observations[-1].recorded_at,
        acceptance_spec=TARGET,
        truth=result.truth,
    )


def test_empty_evaluation_does_not_fabricate_scores() -> None:
    config = SimulationConfig(count=0)
    result = generate(config)
    report = evaluate(
        [],
        dataset=result.truth.dataset,
        train_until=config.start_at,
        evaluation_at=config.start_at,
        acceptance_spec=TARGET,
        truth=result.truth,
    )
    assert report.held_out_count == 0
    assert report.training.eligible_label_count == 0
    assert all(
        metric.brier_score is None and metric.truth.count == 0
        for metric in report.baselines
    )
    assert report.held_out_resources.cost_usd.mean is None


def test_wrong_or_conflicting_truth_is_rejected_and_partial_truth_is_counted() -> None:
    result = generate(SimulationConfig(count=4, unknown_probability=0))
    kwargs = dict(
        dataset=result.truth.dataset,
        train_until=result.observations[1].decision_at,
        evaluation_at=result.observations[-1].recorded_at,
        acceptance_spec=TARGET,
    )
    wrong_dataset = result.truth.model_copy(
        update={
            "dataset": DatasetReference(
                source_kind="simulated", dataset_id="different", dataset_version="1"
            )
        }
    )
    with pytest.raises(ValueError, match="selected simulated dataset"):
        evaluate(result.observations, truth=wrong_dataset, **kwargs)
    duplicate = result.truth.model_copy(update={"records": result.truth.records * 2})
    with pytest.raises(ValueError, match="duplicate simulator truth"):
        evaluate(result.observations, truth=duplicate, **kwargs)
    extra = result.truth.model_copy(
        update={
            "records": (
                TruthRecord(
                    source_record_id="wrong-record",
                    success_probability=0.5,
                    realized_success=True,
                ),
            )
        }
    )
    with pytest.raises(ValueError, match="identifiers do not match"):
        evaluate(result.observations, truth=extra, **kwargs)
    last = result.truth.records[-1]
    conflict = result.truth.model_copy(
        update={
            "records": (
                last.model_copy(update={"realized_success": not last.realized_success}),
            )
        }
    )
    with pytest.raises(ValueError, match="realization conflicts"):
        evaluate(result.observations, truth=conflict, **kwargs)
    partial = SimulationTruth(
        **(result.truth.model_dump() | {"records": result.truth.records[1:2]})
    )
    report = evaluate(result.observations, truth=partial, **kwargs)
    assert report.missing_truth_count == 2
    assert report.baselines[0].truth.count == 1


def test_test_record_availability_and_invalid_cutoffs() -> None:
    result = generate(SimulationConfig(count=10))
    cutoff = result.observations[5].decision_at
    kwargs = dict(
        dataset=result.truth.dataset, train_until=cutoff, acceptance_spec=TARGET
    )
    report = evaluate(result.observations, evaluation_at=cutoff, **kwargs)
    assert report.held_out_count == 0
    assert report.scored_label_count == 0
    assert report.exclusions["held_out_not_available"] == 5
    with pytest.raises(ValueError, match="must not precede"):
        evaluate(
            result.observations, evaluation_at=cutoff - timedelta(seconds=1), **kwargs
        )
    with pytest.raises(ValueError, match="positive integer"):
        evaluate(
            result.observations, evaluation_at=cutoff, calibration_bins=0, **kwargs
        )


def test_changing_evaluator_probabilities_cannot_change_training_or_binary_scores() -> (
    None
):
    result = generate(SimulationConfig(count=50, unknown_probability=0))
    kwargs = dict(
        dataset=result.truth.dataset,
        train_until=result.observations[25].decision_at,
        evaluation_at=result.observations[-1].recorded_at,
        acceptance_spec=TARGET,
    )
    altered_truth = result.truth.model_copy(
        update={
            "records": tuple(
                record.model_copy(update={"success_probability": 0.01})
                for record in result.truth.records
            )
        }
    )
    original = evaluate(result.observations, truth=result.truth, **kwargs)
    altered = evaluate(result.observations, truth=altered_truth, **kwargs)
    assert original.training == altered.training
    for first, second in zip(original.baselines, altered.baselines, strict=True):
        assert first.brier_score == second.brier_score
        assert first.log_loss == second.log_loss
        assert first.calibration == second.calibration
        assert first.truth != second.truth
