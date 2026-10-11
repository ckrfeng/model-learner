from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from model_learner.domain.models import DataSourceKind, Observation, OutcomeStatus
from model_learner.execution.models import StateInference
from model_learner.learn.task_state import (
    TaskStateExample,
    _features,
    _fit,
    evaluate_task_state,
    generate_task_state_fixture,
    load_task_state_examples,
    run_task_state_experiment,
)

START = datetime(2026, 1, 1, tzinfo=UTC)


def evaluate(rows, **kwargs):
    kwargs.setdefault("bootstrap_replicates", 100)
    return evaluate_task_state(
        rows,
        dataset=rows[0].observation.dataset,
        acceptance_spec=rows[0].observation.acceptance_spec,
        train_until=START + timedelta(seconds=180 * 90),
        evaluation_at=START + timedelta(seconds=180 * 150),
        **kwargs,
    )


def replace_observation(example, **changes):
    values = example.observation.model_dump()
    values.update(changes, stable_key=None)
    return example.model_copy(
        update={"observation": Observation.model_validate(values)}
    )


@pytest.fixture(scope="module")
def rows():
    return generate_task_state_fixture(seed=3, count=150)


def test_common_cohort_calibration_ablations_and_paired_uncertainty(rows):
    report = evaluate(rows)
    assert report.training_count >= 80
    assert report.scored_count >= 50
    assert len(report.variants) == 6
    assert len({v.scored_count for v in report.variants}) == 1
    assert len({tuple(run for run, _ in v.predictions) for v in report.variants}) == 1
    assert all(
        sum(b.count for b in v.calibration) == report.scored_count
        for v in report.variants
    )
    assert report.variants[1].predictions == report.variants[-1].predictions
    assert all(
        v.brier_interval.lower <= v.brier_score <= v.brier_interval.upper
        for v in report.variants
    )
    assert report.comparisons[1].brier_improvement > 0.05
    assert report.comparisons[1].interval.lower > 0
    assert "simulated" == report.dataset["source_kind"]


def test_reproducible_generator_and_experiment():
    assert generate_task_state_fixture(seed=9, count=5) == generate_task_state_fixture(
        seed=9, count=5
    )
    assert generate_task_state_fixture(seed=9, count=6)[
        :5
    ] == generate_task_state_fixture(seed=9, count=5)
    result = run_task_state_experiment(
        seeds=(0, 1), count=150, bootstrap_replicates=100
    )
    assert result == run_task_state_experiment(
        seeds=(0, 1), count=150, bootstrap_replicates=100
    )
    assert result["scenarios"]["state_signal"]["mean_state_brier_improvement"] > 0.05
    assert (
        abs(result["scenarios"]["null_signal"]["mean_state_brier_improvement"]) < 0.04
    )


def test_future_events_and_labels_cannot_rewrite_frozen_fit(rows):
    reference = evaluate(rows)
    future = replace_observation(
        rows[0],
        recorded_at=START + timedelta(days=30),
        outcome_status=OutcomeStatus.FAILURE
        if rows[0].observation.outcome_status is OutcomeStatus.SUCCESS
        else OutcomeStatus.SUCCESS,
    )
    result = evaluate((*rows, future))
    assert result.variants == reference.variants
    assert result.exclusions["observation_not_available"] == 1


def test_delayed_training_label_excluded(rows):
    changed = replace_observation(
        rows[0],
        label_available_at=START + timedelta(days=30),
        recorded_at=START + timedelta(days=30),
    )
    report = evaluate((changed, *rows[1:]))
    assert report.training_count == evaluate(rows).training_count - 1
    assert report.exclusions["observation_not_available"] == 1


def test_future_label_changes_do_not_change_predictions(rows):
    changed = list(rows)
    for index in range(90, 150):
        row = changed[index]
        if row.observation.outcome_status in (
            OutcomeStatus.SUCCESS,
            OutcomeStatus.FAILURE,
        ):
            changed[index] = replace_observation(
                row,
                outcome_status=OutcomeStatus.FAILURE
                if row.observation.outcome_status is OutcomeStatus.SUCCESS
                else OutcomeStatus.SUCCESS,
            )
    reference, result = evaluate(rows), evaluate(changed)
    assert [v.predictions for v in result.variants] == [
        v.predictions for v in reference.variants
    ]
    assert result.variants[2].brier_score != reference.variants[2].brier_score


def test_label_known_at_checkpoint_and_unavailable_inputs_excluded(rows):
    changed = list(rows)
    changed[0] = replace_observation(
        rows[0], label_available_at=rows[0].checkpoint.checkpoint
    )
    changed[1] = rows[1].model_copy(
        update={
            "inputs_available_at": rows[1].checkpoint.checkpoint + timedelta(seconds=1)
        }
    )
    changed[2] = rows[2].model_copy(
        update={
            "initial_available_at": rows[2].observation.decision_at
            + timedelta(seconds=1)
        }
    )
    report = evaluate(changed)
    assert report.exclusions["label_known_at_checkpoint"] == 1
    assert report.exclusions["checkpoint_inputs_unavailable"] == 1
    assert report.exclusions["initial_information_unavailable"] == 1


def test_fixed_horizon_no_repeated_checkpoint_selection(rows):
    changed = rows[0].model_copy(
        update={
            "checkpoint": rows[0].checkpoint.model_copy(
                update={
                    "checkpoint": rows[0].checkpoint.checkpoint + timedelta(seconds=1)
                }
            )
        }
    )
    assert evaluate((changed, *rows[1:])).exclusions["wrong_checkpoint_horizon"] == 1
    with pytest.raises(ValueError, match="conflicting"):
        evaluate((*rows, changed))
    duplicate = evaluate((*rows, rows[0]))
    assert duplicate.exclusions["duplicate_run"] == 1
    assert duplicate.variants == evaluate(rows).variants


def test_retry_tasks_do_not_cross_fit_and_score(rows):
    changed = replace_observation(rows[100], task_id=rows[0].observation.task_id)
    changed = changed.model_copy(
        update={
            "checkpoint": changed.checkpoint.model_copy(
                update={"task_id": changed.observation.task_id}
            )
        }
    )
    report = evaluate((*rows[:100], changed, *rows[101:]))
    assert report.exclusions["task_overlaps_training"] == 1
    assert report.held_out_count == evaluate(rows).held_out_count - 1


def test_initial_vocabulary_and_scaling_are_training_only(rows):
    groups = ("initial", "metrics", "state")
    fit = _fit(list(rows[:30]), groups)
    values = _features(rows[100], groups)
    values["initial:configuration=never_seen"] = 1
    assert fit.predict(values) == fit.predict(_features(rows[100], groups))
    assert "initial:configuration=never_seen" not in fit.names
    assert all(scale >= 1 for scale in fit.scales)


def test_final_target_and_terminal_state_never_enter_features(rows):
    point = rows[0].checkpoint.model_copy(
        update={
            "execution_state": StateInference(
                state="completed", explanation="Final report"
            ),
            "test_state": StateInference(
                state="passed", explanation="Final acceptance"
            ),
            "cost_usd": None,
        }
    )
    changed = rows[0].model_copy(update={"checkpoint": point})
    for groups in (
        ("initial",),
        ("initial", "metrics"),
        ("initial", "metrics", "state"),
    ):
        assert _features(changed, groups) == _features(rows[0], groups)
    assert not any("test" in name for name in _features(changed, ("state",)))


def test_insufficient_data_retains_counts_and_null_metrics(rows):
    report = evaluate(rows[:10])
    assert report.scored_count == 0
    assert all(v.status == "insufficient_data" for v in report.variants)
    assert all(
        v.brier_score is None and v.brier_interval.lower is None
        for v in report.variants
    )
    assert all(
        comparison.interpretation == "insufficient_data"
        for comparison in report.comparisons
    )


def test_source_kinds_never_mix(rows):
    foreign = replace_observation(
        rows[100],
        source_kind=DataSourceKind.BENCHMARK,
        dataset=rows[100].observation.dataset.model_copy(
            update={"source_kind": DataSourceKind.BENCHMARK}
        ),
    )
    report = evaluate((*rows, foreign))
    assert report.exclusions["other_dataset"] == 1
    assert report.variants == evaluate(rows).variants


def test_non_simulated_rows_require_auditable_events_and_independent_evidence(rows):
    converted = [
        replace_observation(
            row,
            source_kind=DataSourceKind.BENCHMARK,
            dataset=row.observation.dataset.model_copy(
                update={"source_kind": DataSourceKind.BENCHMARK}
            ),
        )
        for row in rows
    ]
    report = evaluate(converted)
    assert report.exclusions["checkpoint_event_evidence_required"] == len(rows)
    assert report.scored_count == 0


def test_conflicting_event_projection_is_rejected(rows):
    changed = rows[0].model_copy(update={"events": ()})
    with pytest.raises(ValueError, match="facts disagree"):
        evaluate((changed, *rows[1:]))


def test_strict_load_and_roundtrip(tmp_path, rows):
    import json

    path = tmp_path / "examples.json"
    path.write_text(json.dumps([row.model_dump(mode="json") for row in rows[:3]]))
    assert load_task_state_examples(str(path)) == rows[:3]
    path.write_text("{}")
    with pytest.raises(ValueError, match="JSON array"):
        load_task_state_examples(str(path))
    assert asdict(evaluate(rows))["scored_count"] > 0


@pytest.mark.parametrize(
    "changes",
    [
        {"min_training": 1},
        {"min_scored": True},
        {"bootstrap_replicates": 2},
        {"calibration_bins": 0},
        {"checkpoint_offset_seconds": float("nan")},
    ],
)
def test_invalid_settings(rows, changes):
    with pytest.raises(ValueError):
        evaluate(rows, **changes)


def test_identity_and_timezone_validation(rows):
    values = rows[0].model_dump()
    values["initial_available_at"] = datetime(2026, 1, 1)
    with pytest.raises(ValidationError, match="timezone"):
        TaskStateExample.model_validate(values)
    values = rows[0].model_dump()
    values["checkpoint"]["task_id"] = rows[1].observation.task_id
    with pytest.raises(ValidationError, match="identifiers"):
        TaskStateExample.model_validate(values)


def test_controlled_fixture_projection_invariants():
    for example in generate_task_state_fixture(seed=1, count=100):
        facts = example.checkpoint.facts
        assert sum(facts.event_types.values()) == facts.event_count
        assert len(facts.event_ids) == facts.supported_event_count == facts.event_count
        assert facts.unsupported_event_count == 0
        assert facts.completed_tool_items == sum(
            tool.terminal_observed for tool in facts.tool_items
        )
        assert facts.failed_tool_items == sum(
            tool.failed is True for tool in facts.tool_items
        )
        assert facts.tool_items_with_unknown_failure == sum(
            tool.failed is None for tool in facts.tool_items
        )
        assert facts.completed_turns == facts.event_types["turn.completed"] == 1
        assert facts.started_turns == facts.event_types["turn.started"] == 1
        assert facts.event_types["item.started"] == len(facts.tool_items)
        assert facts.event_types["item.completed"] == facts.completed_tool_items
        assert all(
            coverage <= facts.completed_turns
            for coverage in facts.token_usage_coverage.values()
        )
        assert all(
            (facts.token_usage[key] is None) == (coverage == 0)
            for key, coverage in facts.token_usage_coverage.items()
        )
        for failure in facts.repeated_failures:
            failed_items = tuple(
                tool for tool in facts.tool_items if tool.failed is True
            )
            assert failure.failed_items == len(failed_items)
            assert failure.event_ids == tuple(
                tool.latest_event_id for tool in failed_items
            )
            assert failure.event_ids == example.checkpoint.signals[0].basis_event_ids
        assert example.checkpoint.execution_state.state == "completed_turn_observed"
