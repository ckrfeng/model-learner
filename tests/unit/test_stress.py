"""Multi-seed diagnostics, sparse uncertainty, drift failure and missingness."""

import json
import math
from dataclasses import asdict

import pytest
from pydantic import ValidationError

from model_learner.learn import StressScenario, reference_scenarios, run_stress_suite
from model_learner.simulate import SimulationConfig


def custom_scenario(**changes) -> StressScenario:
    return StressScenario(
        name="controlled",
        description="Analytic one-cell example.",
        simulation=SimulationConfig(
            count=4,
            arm_weights=(1, 0, 0),
            group_weights=(1, 0, 0, 0),
            probabilities=((1, 1, 1),) * 4,
            unknown_probability=0,
            **changes,
        ),
        train_count=2,
    )


def test_multi_seed_reproducibility_and_explicit_dataset_isolation() -> None:
    kwargs = dict(seeds=(9, 17), count=24, calibration_bins=4)
    report = run_stress_suite(**kwargs)
    assert report == run_stress_suite(**kwargs)
    assert len(report.scenarios) == 8
    datasets = []
    for scenario in report.scenarios:
        assert len(scenario.runs) == 2
        assert len(scenario.baselines) == 3
        assert len(scenario.comparisons) == 2
        for run in scenario.runs:
            assert run.simulation["seed"] == run.seed
            assert len(run.unpooled_cells) == 12
            datasets.append(run.evaluation.dataset["dataset_id"])
            assert run.evaluation.dataset["source_kind"] == "simulated"
    assert len(set(datasets)) == len(datasets)
    json.dumps(asdict(report), allow_nan=False)


def test_hand_computed_scores_pooled_bins_and_paired_comparisons() -> None:
    report = run_stress_suite(
        seeds=(0, 1), scenarios=(custom_scenario(),), calibration_bins=4
    ).scenarios[0]
    for baseline in report.baselines:
        assert baseline.label_count == baseline.truth_count == 4
        assert baseline.brier_score.seed_count == 2
        assert baseline.brier_score.mean == 0.0625
        assert baseline.brier_score.standard_deviation == 0
        assert baseline.brier_score.standard_error == 0
        assert baseline.log_loss.mean == pytest.approx(-math.log(0.75))
        assert baseline.pooled_brier_score == 0.0625
        assert baseline.pooled_log_loss == baseline.log_loss.mean
        assert baseline.pooled_calibration_error == 0.25
        assert baseline.calibration_error.mean == 0.25
        assert baseline.pooled_calibration[-1].count == 4
        assert baseline.pooled_calibration[-1].mean_prediction == 0.75
        assert baseline.pooled_calibration[-1].observed_success_rate == 1
        assert baseline.truth_interval_coverage.mean == 0
        assert baseline.macro_cell_interval_coverage.mean == 0
        assert baseline.represented_cell_count == 2
    for comparison in report.comparisons:
        assert comparison.unpooled_minus_baseline_brier.mean == 0
        assert comparison.unpooled_better_seed_count == 0
        assert comparison.tied_seed_count == 2


def test_all_prior_only_cells_remain_visible_including_unsampled_arms() -> None:
    run = (
        run_stress_suite(seeds=(0,), scenarios=(custom_scenario(),))
        .scenarios[0]
        .runs[0]
    )
    cells = run.unpooled_cells
    assert sum(cell.training_label_count for cell in cells) == 2
    assert sum(cell.held_out_count for cell in cells) == 2
    unseen = [cell for cell in cells if cell.training_label_count == 0]
    assert len(unseen) == 11
    for cell in unseen:
        assert cell.prediction == 0.5
        assert cell.lower == pytest.approx(0.025)
        assert cell.upper == pytest.approx(0.975)
        assert cell.held_out_count == 0
        assert cell.truth_interval_coverage is None


def test_missing_scores_and_empty_truth_remain_undefined() -> None:
    scenario = StressScenario(
        name="empty",
        description="No observations.",
        simulation=SimulationConfig(count=0),
        train_count=0,
    )
    report = run_stress_suite(seeds=(1,), scenarios=(scenario,)).scenarios[0]
    for metric in report.baselines:
        assert metric.brier_score.seed_count == 0
        assert metric.brier_score.mean is None
        assert metric.pooled_brier_score is None
        assert metric.pooled_calibration_error is None
        assert metric.truth_interval_coverage.mean is None
        assert metric.macro_cell_interval_coverage.mean is None
        assert metric.truth_count == metric.label_count == 0
    assert report.comparisons[0].unpooled_minus_baseline_brier.mean is None


def test_unknown_is_not_failure_and_does_not_fabricate_binary_calibration() -> None:
    scenario = StressScenario(
        name="unknown",
        description="Every label hidden.",
        simulation=SimulationConfig(count=30, unknown_probability=1),
        train_count=15,
    )
    report = run_stress_suite(seeds=(1, 2), scenarios=(scenario,)).scenarios[0]
    for run in report.runs:
        assert run.evaluation.training.eligible_label_count == 0
        assert run.evaluation.scored_label_count == 0
        assert all(cell.training_label_count == 0 for cell in run.unpooled_cells)
    for metric in report.baselines:
        assert metric.pooled_brier_score is None
        assert metric.pooled_log_loss is None
        assert metric.calibration_error.seed_count == 0
        assert metric.truth_count == 30
        assert metric.truth_interval_coverage.mean == 1


def test_maturity_changes_scores_and_availability_but_never_frozen_training() -> None:
    scenarios = reference_scenarios(count=100)
    pending, mature = scenarios[-2:]
    report = run_stress_suite(seeds=(3,), scenarios=(pending, mature))
    first, second = [scenario.runs[0] for scenario in report.scenarios]
    assert first.evaluation.training.eligible_label_count == 36
    assert second.evaluation.training.eligible_label_count == 36
    assert first.evaluation.scored_label_count == 15
    assert second.evaluation.scored_label_count == 40
    assert first.evaluation.exclusions["held_out_not_available"] == 25
    assert first.unpooled_cells[0].prediction == second.unpooled_cells[0].prediction
    for a, b in zip(first.unpooled_cells, second.unpooled_cells, strict=True):
        assert a.training_label_count == b.training_label_count
        assert (a.prediction, a.lower, a.upper) == (b.prediction, b.lower, b.upper)


def test_drift_reveals_narrow_wrong_intervals_without_learning_future_truth() -> None:
    scenario = StressScenario(
        name="deterministic-drift",
        description="An extreme known counterexample.",
        simulation=SimulationConfig(
            count=40,
            unknown_probability=0,
            arm_weights=(1, 0, 0),
            group_weights=(1, 0, 0, 0),
            probabilities=((1, 1, 1),) * 4,
            drift_at_index=20,
            drift_probabilities=((0, 0, 0),) * 4,
        ),
        train_count=20,
    )
    report = run_stress_suite(seeds=(1, 2), scenarios=(scenario,)).scenarios[0]
    assert report.baselines[-1].brier_score.mean == pytest.approx((21 / 22) ** 2)
    assert report.baselines[-1].truth_interval_coverage.mean == 0
    assert report.baselines[-1].interval_width.mean < 0.2
    assert all(run.unpooled_cells[0].training_label_count == 20 for run in report.runs)


def test_pooled_scores_use_available_label_denominators() -> None:
    scenario = StressScenario(
        name="missing",
        description="Varying score denominators by seed.",
        simulation=SimulationConfig(count=80, unknown_probability=0.6),
        train_count=40,
    )
    report = run_stress_suite(seeds=(1, 2, 3), scenarios=(scenario,)).scenarios[0]
    baseline = report.baselines[-1]
    metrics = [run.evaluation.baselines[-1] for run in report.runs]
    assert len({metric.label_count for metric in metrics}) > 1
    assert baseline.pooled_brier_score == pytest.approx(
        sum(metric.label_count * metric.brier_score for metric in metrics)
        / sum(metric.label_count for metric in metrics)
    )
    assert baseline.label_count == sum(b.count for b in baseline.pooled_calibration)
    assert baseline.brier_score.mean == pytest.approx(
        sum(metric.brier_score for metric in metrics) / 3
    )


@pytest.mark.parametrize("seeds", [(), (1, 1), (True,), (1.5,)])
def test_seed_contract_rejects_fake_replication(seeds) -> None:
    with pytest.raises(ValueError, match="seeds"):
        run_stress_suite(seeds=seeds, count=10)


@pytest.mark.parametrize(
    "changes",
    [
        {"count": 1},
        {"count": True},
        {"train_fraction": 0},
        {"train_fraction": float("nan")},
    ],
)
def test_invalid_reference_scenarios(changes) -> None:
    with pytest.raises(ValueError):
        reference_scenarios(**changes)


def test_invalid_scenario_and_suite_contracts() -> None:
    with pytest.raises(ValidationError, match="must not exceed"):
        StressScenario(
            name="bad",
            description="",
            simulation=SimulationConfig(count=4),
            train_count=5,
        )
    with pytest.raises(ValidationError):
        custom_scenario(verification_delay_seconds=float("inf"))
    with pytest.raises(ValueError, match="distinct names"):
        run_stress_suite(scenarios=(custom_scenario(), custom_scenario()))
    with pytest.raises(ValueError, match="nonempty"):
        run_stress_suite(scenarios=())
    with pytest.raises(ValueError, match="positive integer"):
        run_stress_suite(calibration_bins=True)


def test_stationary_multi_seed_coverage_and_pooling_tradeoff() -> None:
    # Fixed seeds test implementation behavior, not a universal coverage guarantee.
    scenarios = reference_scenarios(count=600)[:2]
    balanced, homogeneous = run_stress_suite(
        seeds=range(12), scenarios=scenarios
    ).scenarios
    assert (
        balanced.baselines[-1].brier_score.mean < balanced.baselines[0].brier_score.mean
    )
    assert (
        homogeneous.baselines[-1].brier_score.mean
        > homogeneous.baselines[0].brier_score.mean
    )
    for scenario in (balanced, homogeneous):
        reference = scenario.baselines[-1]
        assert reference.brier_score.seed_count == 12
        assert 0.85 < reference.truth_interval_coverage.mean < 1
        assert reference.brier_score.standard_deviation > 0
        assert reference.brier_score.standard_error == pytest.approx(
            reference.brier_score.standard_deviation / math.sqrt(12)
        )
    # A global marginally calibrated prediction still misses heterogeneous cells.
    assert balanced.baselines[0].pooled_calibration_error < 0.05
    assert balanced.baselines[0].macro_cell_interval_coverage.mean < 0.5


def test_imbalanced_selection_preserves_rare_arm_uncertainty() -> None:
    scenario = reference_scenarios(count=300)[3]
    run = run_stress_suite(seeds=(0,), scenarios=(scenario,)).scenarios[0].runs[0]
    common = [c for c in run.unpooled_cells if c.model == "arm-a"]
    rare = [c for c in run.unpooled_cells if c.model != "arm-a"]
    assert sum(c.training_label_count for c in common) > 170
    assert sum(c.training_label_count for c in rare) < 10
    assert min(c.upper - c.lower for c in rare) > max(c.upper - c.lower for c in common)
    assert any(c.training_label_count == 0 for c in rare)
