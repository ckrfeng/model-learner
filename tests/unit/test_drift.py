"""Prequential scoring, target isolation and reproducible drift sensitivity."""

import hashlib
import json
from dataclasses import asdict

import pytest
from pydantic import ValidationError

from model_learner.learn import drift as module
from model_learner.learn.drift import drift_scenarios, run_drift_suite
from model_learner.learn.stress import StressScenario
from model_learner.simulate.generator import SimulationConfig, generate


def scenario(**changes):
    return StressScenario(
        name="analytic",
        description="Single-cell constant or drifting trial.",
        train_count=4,
        simulation=SimulationConfig(
            **(
                dict(
                    count=12,
                    unknown_probability=0,
                    arm_weights=(1, 0, 0),
                    group_weights=(1, 0, 0, 0),
                    probabilities=((1, 1, 1),) * 4,
                )
                | changes
            )
        ),
    )


def test_analytic_block_refitting_scores_current_labels_only():
    report = run_drift_suite(
        seeds=(1,),
        scenarios=(scenario(),),
        window_steps=(2,),
        refit_steps=2,
        calibration_bins=4,
    )
    full, recent = report.scenarios[0].runs[0].baselines
    assert [block.training_label_count for block in full.blocks] == [4, 6, 8, 10]
    assert [block.training_label_count for block in recent.blocks] == [2] * 4
    assert full.metrics.brier_score == pytest.approx(
        sum((1 / (n + 2)) ** 2 for n in (4, 6, 8, 10)) / 4
    )
    assert recent.metrics.brier_score == 1 / 16
    assert full.metrics.label_count == full.metrics.truth_count == 8
    assert recent.metrics.calibration_error == 0.25
    assert full.metrics.interval_coverage == recent.metrics.interval_coverage == 0
    assert full.adaptation_delay_steps is None
    assert full.adaptation_followup_steps is None
    assert recent.blocks[-1].prior_only_cell_count == 11
    json.dumps(asdict(report), allow_nan=False)


def test_delayed_label_exclusion_and_pending_scoring():
    delayed = scenario(verification_delay_seconds=3 * 60)
    delayed = delayed.model_copy(update={"evaluation_delay_seconds": 0})
    run = (
        run_drift_suite(
            seeds=(1,), scenarios=(delayed,), window_steps=(2,), refit_steps=2
        )
        .scenarios[0]
        .runs[0]
    )
    full, recent = run.baselines
    # Inclusive label cutoff permits index 1 at cutoff index 4; later rows are future.
    assert full.blocks[0].training_label_count == 2
    assert recent.blocks[0].training_label_count == 0
    assert recent.metrics.brier_score == 0.25
    assert full.metrics.label_count == recent.metrics.label_count == 5
    assert full.metrics.truth_count == 8


def test_truth_mutation_never_changes_predictions_training_or_binary_scores(
    monkeypatch,
):
    kwargs = dict(
        seeds=(4,),
        scenarios=(scenario(probabilities=((0.7, 0.7, 0.7),) * 4),),
        window_steps=(4,),
        refit_steps=2,
    )
    before = run_drift_suite(**kwargs).scenarios[0].runs[0]
    original_generate = module.generate

    def altered(config):
        result = original_generate(config)
        truth = result.truth.model_copy(
            update={
                "records": tuple(
                    r.model_copy(update={"success_probability": 0.05})
                    for r in result.truth.records
                )
            }
        )
        return result.model_copy(update={"truth": truth})

    monkeypatch.setattr(module, "generate", altered)
    after = run_drift_suite(**kwargs).scenarios[0].runs[0]
    for old, new in zip(before.baselines, after.baselines, strict=True):
        assert old.metrics.brier_score == new.metrics.brier_score
        assert old.metrics.calibration == new.metrics.calibration
        assert [block.cells for block in old.blocks] == [
            block.cells for block in new.blocks
        ]
        assert [block.training_label_count for block in old.blocks] == [
            block.training_label_count for block in new.blocks
        ]
        assert old.metrics.probability_mae != new.metrics.probability_mae


def test_future_outcomes_do_not_change_first_block_predictions(monkeypatch):
    kwargs = dict(seeds=(4,), scenarios=(scenario(),), window_steps=(3,), refit_steps=2)
    before = run_drift_suite(**kwargs).scenarios[0].runs[0]
    original_generate = module.generate

    def altered(config):
        result = original_generate(config)
        rows = tuple(
            row if index < 4 else row.model_copy(update={"outcome_status": "failure"})
            for index, row in enumerate(result.observations)
        )
        return result.model_copy(update={"observations": rows})

    monkeypatch.setattr(module, "generate", altered)
    after = run_drift_suite(**kwargs).scenarios[0].runs[0]
    for old, new in zip(before.baselines, after.baselines, strict=True):
        assert old.blocks[0].cells == new.blocks[0].cells


def test_gradual_probability_endpoints_and_legacy_fingerprint():
    config = SimulationConfig(
        seed=42,
        count=8,
        drift_at_index=2,
        probabilities=((0.9, 0.9, 0.9),) * 4,
        drift_probabilities=((0.2, 0.2, 0.2),) * 4,
        gradual_drift_steps=4,
    )
    values = [r.success_probability for r in generate(config).truth.records]
    assert values == pytest.approx([0.9, 0.9, 0.9, 0.725, 0.55, 0.375, 0.2, 0.2])
    legacy = SimulationConfig(seed=42, count=24)
    scenario_dump = legacy.model_dump(
        mode="json", exclude={"count", "gradual_drift_steps"}
    )
    expected = hashlib.sha256(
        json.dumps(scenario_dump, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    assert generate(legacy).truth.scenario_fingerprint == expected
    assert (
        generate(legacy).observations
        == generate(legacy.model_copy(update={"count": 48})).observations[:24]
    )
    for changes in (
        {"gradual_drift_steps": 0},
        {"gradual_drift_steps": True},
        {"gradual_drift_steps": 4, "drift_at_index": None, "drift_probabilities": None},
    ):
        with pytest.raises(ValidationError):
            SimulationConfig.model_validate(config.model_dump() | changes)


def test_multi_seed_stationary_and_drift_tradeoff_reproducible():
    selected = drift_scenarios(count=160)
    report = run_drift_suite(
        seeds=range(4), scenarios=selected, window_steps=(40,), refit_steps=20
    )
    assert report == run_drift_suite(
        seeds=range(4), scenarios=selected, window_steps=(40,), refit_steps=20
    )
    assert len(report.scenarios) == 7
    abrupt = report.scenarios[2]
    full, recent = abrupt.baselines
    assert recent.brier_score.mean < full.brier_score.mean
    assert recent.interval_width.mean > full.interval_width.mean
    assert recent.better_seed_count == 4
    assert recent.adapted_seed_count + recent.adaptation_censored_seed_count == 4
    assert report.scenarios[-1].runs[0].baselines[1].blocks[0].training_label_count < 40
    for result in report.scenarios:
        for run in result.runs:
            assert run.simulation["seed"] == run.seed
            assert all(
                len(block.cells) == 12 for b in run.baselines for block in b.blocks
            )


@pytest.mark.parametrize(
    "changes",
    [
        dict(seeds=()),
        dict(seeds=(1, 1)),
        dict(seeds=(True,)),
        dict(window_steps=()),
        dict(window_steps=(0,)),
        dict(window_steps=(1, 1)),
        dict(refit_steps=True),
        dict(calibration_bins=0),
        dict(count=7),
        dict(scenarios=()),
    ],
)
def test_invalid_suite_contracts(changes):
    with pytest.raises(ValueError):
        run_drift_suite(**changes)


def test_unknown_scores_stay_null_and_prior_truth_coverage_is_not_accuracy():
    report = run_drift_suite(
        seeds=(1, 2),
        scenarios=(
            scenario(unknown_probability=1, probabilities=((0.2, 0.2, 0.2),) * 4),
        ),
        window_steps=(2,),
        refit_steps=2,
    )
    for summary in report.scenarios[0].baselines:
        assert summary.brier_score.mean is None
        assert summary.brier_score.seed_count == 0
        assert summary.interval_coverage.mean == 1
    for run in report.scenarios[0].runs:
        for baseline in run.baselines:
            assert baseline.metrics.label_count == 0
            assert baseline.metrics.truth_count == 8
            assert baseline.metrics.calibration_error is None
            assert baseline.metrics.probability_mae == pytest.approx(0.3)
            assert all(block.training_label_count == 0 for block in baseline.blocks)


def test_empty_evaluation_is_explicitly_undefined():
    empty = StressScenario(
        name="empty",
        description="",
        simulation=SimulationConfig(count=0),
        train_count=0,
    )
    report = run_drift_suite(seeds=(1,), scenarios=(empty,), window_steps=(2,))
    for baseline in report.scenarios[0].baselines:
        assert baseline.interval_coverage.mean is None
        assert baseline.brier_score.mean is None
        assert baseline.adaptation_censored_seed_count == 0
