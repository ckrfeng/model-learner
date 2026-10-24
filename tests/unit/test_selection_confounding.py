"""Frozen M6-B synthetic assignment contrast; no historical or measured data.

Generate the 2,880-row experiment once per test session. Replay and negative
boundary tests reuse those rows; no extra seeds, observations or tuned campaign.
"""

import hashlib
import json
import math
from datetime import timedelta
from pathlib import Path
from statistics import fmean, stdev
from uuid import UUID

import pytest

from model_learner.domain.models import (
    DataSourceKind,
    ExecutionConfiguration,
    Observation,
    ResourceBudget,
)
from model_learner.learn import stress
from model_learner.learn.estimator import BetaBernoulli


@pytest.fixture(scope="session")
def frozen_data():
    return {
        (m, s): stress._generate_selection(m, s)
        for m in stress.SELECTION_MECHANISMS
        for s in stress.SELECTION_SEEDS
    }


@pytest.fixture(scope="session")
def selection_report(frozen_data, tmp_path_factory):
    report = stress.run_selection_confounding(results=frozen_data)
    # Temporary synthetic metrics for the required human-readable report. This
    # is not another experiment, report publication or committed data artifact.
    path = tmp_path_factory.mktemp("selection-confounding") / "metrics.json"
    path.write_text(json.dumps(report, sort_keys=True, allow_nan=False) + "\n")
    return report


def test_fixed_design_seeds_workload_and_identity(frozen_data, selection_report):
    assert stress.SELECTION_SEEDS == (11, 23, 37, 41, 53, 67, 71, 83, 97, 101, 113, 127)
    assert len(frozen_data) == 24
    assert sum(len(v.observations) for v in frozen_data.values()) == 2880
    assert selection_report["generated_row_count"] == 2880
    assert len({r.truth.dataset.dataset_id for r in frozen_data.values()}) == 24
    assert len({r.truth.scenario_fingerprint for r in frozen_data.values()}) == 24
    for (m, s), result in frozen_data.items():
        contract = stress._selection_contract(m, s)
        assert result.truth.scenario_fingerprint == stress._selection_digest(contract)
        assert contract["count"] == 120 and contract["train_count"] == 72
        assert (
            contract["verification_delay_seconds"]
            == contract["unknown_probability"]
            == contract["resource_missing_probability"]
            == 0
        )
        assert contract["seed"] == s and contract["mechanism"] == m
        for i, row in enumerate(result.observations):
            assert row.decision_at == stress.SELECTION_START + timedelta(seconds=60 * i)
            assert row.decision_at == row.recorded_at == row.label_available_at
            assert row.cost_usd is not None and row.latency_seconds is not None
            assert row.source_kind.value == "simulated"
            assert row.eligible_for_configuration_learning
            assert "probability" not in row.metadata


def test_shared_split_ids_denominators_counts_and_exclusions(selection_report):
    for run in selection_report["runs"]:
        assert (
            run["training_count"],
            run["heldout_count"],
            run["scored_label_count"],
        ) == (72, 48, 48)
        assert run["cutoff"] == "2026-01-01T01:12:00+00:00"
        assert run["evaluation_at"] == "2026-01-01T01:59:00+00:00"
        assert len(run["assignment_counts"]) == 12
        assert sum(c["train"] for c in run["assignment_counts"]) == 72
        assert sum(c["heldout"] for c in run["assignment_counts"]) == 48
        assert (
            run["exclusions"]
            == run["training_exclusions"]
            == run["evaluation_exclusions"]
            == {}
        )
        assert run["partial_pooling_exclusions"] == ({},) * 4
        assert run["training_ids_digest"] != run["heldout_ids_digest"]
        for method in run["methods"]:
            assert method["training_ids_digest"] == run["training_ids_digest"]
            assert method["heldout_ids_digest"] == run["heldout_ids_digest"]
            assert method["training_count"] == 72 and method["scored_label_count"] == 48
            assert len(method["calibration_bins"]) == 10
            assert sum(b["count"] for b in method["calibration_bins"]) == 48
            assert len(method["cell_predictions"]) == 12
            assert method["represented_cell_count"] == sum(
                c["heldout"] > 0 for c in run["assignment_counts"]
            )
    assert any(
        c["train"] == 0 or c["heldout"] == 0
        for run in selection_report["runs"]
        for c in run["assignment_counts"]
    )


def test_probability_assignment_expectations_and_weighted_truth_discrepancy():
    design = stress.selection_design()
    assert design["known_probability_matrix"] == (
        (0.2, 0.45, 0.7),
        (0.3, 0.55, 0.8),
        (0.4, 0.65, 0.9),
        (0.5, 0.75, 0.95),
    )
    confounded, control = design["mechanisms"]
    assert confounded["assignment_probabilities"] == (
        (0.05, 0.15, 0.8),
        (0.1, 0.2, 0.7),
        (0.7, 0.2, 0.1),
        (0.8, 0.15, 0.05),
    )
    expected = ((1.5, 4.5, 24), (3, 6, 21), (21, 6, 3), (24, 4.5, 1.5))
    assert confounded["expected_counts_per_30_in_each_group"] == expected
    assert control["expected_counts_per_30_in_each_group"] == ((10, 10, 10),) * 4
    assert min(p for r in confounded["assignment_probabilities"] for p in r) == 0.05
    # Hand calculation for arm-a: unequal group mixture vs uniform group truth.
    assert design["equal_group_latent_rate_by_arm"][0] == pytest.approx(0.35)
    expected_a = (0.05 * 0.2 + 0.1 * 0.3 + 0.7 * 0.4 + 0.8 * 0.5) / (
        0.05 + 0.1 + 0.7 + 0.8
    )
    assert confounded["assignment_weighted_latent_rate_by_arm"][0] == pytest.approx(
        expected_a
    )
    assert expected_a != pytest.approx(0.35)
    assert control["assignment_weighted_latent_rate_by_arm"] == pytest.approx(
        design["equal_group_latent_rate_by_arm"]
    )


def test_independent_streams_and_assignment_only_contrast(frozen_data):
    for seed in stress.SELECTION_SEEDS:
        left = frozen_data["selection_confounded", seed]
        right = frozen_data["assignment_control", seed]
        assert [r.task_group for r in left.observations] == [
            r.task_group for r in right.observations
        ]
        assert any(
            a.configuration != b.configuration
            for a, b in zip(left.observations, right.observations, strict=True)
        )
        for name in ("group", "assignment", "outcome", "resources"):
            a, b = (
                stress._selection_stream(seed, name),
                stress._selection_stream(seed, name),
            )
            assert [a.random() for _ in range(120)] == [b.random() for _ in range(120)]
        for a, b in zip(left.observations, right.observations, strict=True):
            i, j = (
                "abc".index(a.configuration.model[-1]),
                "abc".index(b.configuration.model[-1]),
            )
            assert a.cost_usd / (0.02, 0.08, 0.2)[i] == pytest.approx(
                b.cost_usd / (0.02, 0.08, 0.2)[j]
            )
            assert a.latency_seconds / (10, 25, 50)[i] == pytest.approx(
                b.latency_seconds / (10, 25, 50)[j]
            )


def test_replay_and_heldout_truth_changes_never_enter_fit(
    frozen_data, selection_report, monkeypatch
):
    mechanism, seed = "selection_confounded", 11
    result = frozen_data[mechanism, seed]
    prior = selection_report["runs"][0]
    fit_ids = tuple(sorted(r.source_record_id for r in result.observations[:72]))
    cutoff = stress.SELECTION_START + timedelta(seconds=72 * 60)
    calls = []
    original_fit = BetaBernoulli.fit
    original_pool = stress.partial_pool

    def fit(cls, observations, **kwargs):
        rows = tuple(observations)
        assert tuple(sorted(r.source_record_id for r in rows)) == fit_ids
        assert all(
            r.decision_at < cutoff
            and r.recorded_at <= cutoff
            and r.label_available_at <= cutoff
            for r in rows
        )
        calls.append("baseline")
        return original_fit(rows, **kwargs)

    def pool(request, *, observations=(), bundles=()):
        rows = tuple(observations)
        assert tuple(sorted(r.source_record_id for r in rows)) == fit_ids
        assert not any(r.task_id == request.task.task_id for r in rows)
        calls.append("partial_pooling")
        return original_pool(request, observations=rows, bundles=bundles)

    monkeypatch.setattr(BetaBernoulli, "fit", classmethod(fit))
    monkeypatch.setattr(stress, "partial_pool", pool)
    assert stress._selection_run(result, mechanism, seed) == prior
    assert calls.count("baseline") == 6 and calls.count("partial_pooling") == 4
    changed = result.model_copy(
        update={
            "truth": result.truth.model_copy(
                update={
                    "records": tuple(
                        t
                        if i < 72
                        else t.model_copy(
                            update={"success_probability": 1 - t.success_probability}
                        )
                        for i, t in enumerate(result.truth.records)
                    )
                }
            )
        }
    )
    perturbed = stress._selection_run(changed, mechanism, seed)
    for a, b in zip(prior["methods"], perturbed["methods"], strict=True):
        assert a["cell_predictions"] == b["cell_predictions"]
        assert a["brier_score"] == b["brier_score"] and a["log_loss"] == b["log_loss"]
    assert prior["methods"][0]["truth_rmse"] != perturbed["methods"][0]["truth_rmse"]


def test_binary_cell_metrics_and_equal_seed_summaries(frozen_data, selection_report):
    for run in selection_report["runs"]:
        held = frozen_data[run["mechanism"], run["seed"]].observations[72:]
        for method in run["methods"]:
            predictions = {
                (c["configuration_id"], c["task_group"]): c
                for c in method["cell_predictions"]
            }
            pairs = [
                (
                    predictions[r.configuration.configuration_id, r.task_group][
                        "probability"
                    ],
                    int(r.outcome_status.value == "success"),
                )
                for r in held
            ]
            assert method["brier_score"] == pytest.approx(
                fmean((p - y) ** 2 for p, y in pairs)
            )
            assert method["log_loss"] == pytest.approx(
                fmean(-y * math.log(p) - (1 - y) * math.log1p(-p) for p, y in pairs)
            )
            ece = (
                sum(
                    b["count"] * abs(b["mean_prediction"] - b["observed_success_rate"])
                    for b in method["calibration_bins"]
                    if b["count"]
                )
                / 48
            )
            assert method["calibration_error"] == pytest.approx(ece)
            for b in method["calibration_bins"]:
                if not b["count"]:
                    assert b["mean_prediction"] is b["observed_success_rate"] is None
    for summary in selection_report["equal_seed_summaries"]:
        runs = [
            r
            for r in selection_report["runs"]
            if r["mechanism"] == summary["mechanism"]
        ]
        index = ("global", "per_arm", "unpooled", "partial_pooling").index(
            summary["method"]
        )
        for metric in stress.SELECTION_METRICS:
            values = [r["methods"][index][metric] for r in runs]
            differences = [
                r["methods"][index][metric] - r["methods"][0][metric] for r in runs
            ]
            for field, reference in (
                ("metrics", values),
                ("paired_minus_global", differences),
            ):
                d = summary[field][metric]
                assert d["seed_count"] == 12
                assert d["mean"] == pytest.approx(fmean(reference))
                assert d["standard_deviation"] == pytest.approx(stdev(reference))
                assert (d["minimum"], d["maximum"]) == (min(reference), max(reference))
    json.dumps(selection_report, allow_nan=False)


def recast(row, **changes):
    return Observation.model_validate(row.model_dump() | changes | {"stable_key": None})


@pytest.mark.parametrize(
    "kind,reason",
    [
        ("dataset", "other_dataset"),
        ("source_kind", "other_dataset"),
        ("acceptance", "other_target_or_budget"),
        ("budget", "other_target_or_budget"),
        ("configuration", "not_admitted_by_policy"),
        ("task", "not_admitted_by_policy"),
        ("target", "prediction_task"),
        ("late", "not_available_at_cutoff"),
    ],
)
def test_common_admission_boundaries(frozen_data, kind, reason):
    mechanism, seed = "selection_confounded", 11
    row = frozen_data[mechanism, seed].observations[0]
    policy, targets = stress._selection_policy(mechanism, seed)
    cutoff = stress.SELECTION_START + timedelta(seconds=72 * 60)
    if kind == "dataset":
        changes = {
            "dataset": row.dataset.model_copy(update={"dataset_version": "other"})
        }
    elif kind == "source_kind":
        changes = {
            "source_kind": "benchmark",
            "dataset": row.dataset.model_copy(
                update={"source_kind": DataSourceKind.BENCHMARK}
            ),
        }
    elif kind == "acceptance":
        changes = {
            "acceptance_spec": row.acceptance_spec.model_copy(
                update={"version": "other"}
            )
        }
    elif kind == "budget":
        changes = {"resource_budget": ResourceBudget(max_tokens=1)}
    elif kind == "configuration":
        changes = {"configuration": ExecutionConfiguration(model="unadmitted")}
    elif kind == "task":
        changes = {"task_id": UUID(int=1)}
    elif kind == "target":
        changes = {"task_id": targets[0].task_id, "task_group": targets[0].task_group}
    else:
        changes = {"recorded_at": cutoff + timedelta(seconds=1)}
    altered = recast(row, **changes)
    train, held, exclusions = stress._selection_admit(
        [altered], policy, targets, cutoff
    )
    assert train == held == [] and exclusions == {reason: 1}


def test_group_snapshot_contradiction_and_undefined_diagnostics(frozen_data):
    row = frozen_data["selection_confounded", 11].observations[0]
    policy, targets = stress._selection_policy("selection_confounded", 11)
    cutoff = stress.SELECTION_START + timedelta(seconds=72 * 60)
    for changes in (
        {"task_group": "unadmitted-group"},
        {"configuration": row.configuration.model_copy(update={"schema_version": 1})},
    ):
        with pytest.raises(ValueError, match="contradicts frozen membership"):
            stress._selection_admit([recast(row, **changes)], policy, targets, cutoff)
    assert stress._selection_truth([]) == {
        "truth_rmse": None,
        "truth_interval_coverage": None,
        "interval_width": None,
    }
    assert stress._ece(stress._selection_bins([], [])) is None
    d = stress._distribution([None, None])
    assert (
        d.seed_count == 0
        and d.mean is d.standard_deviation is d.minimum is d.maximum is None
    )
    assert stress._distribution([0.5]).standard_deviation is None
    with pytest.raises(ValueError, match="exactly the frozen"):
        stress.run_selection_confounding(results={})
    json.dumps(stress._selection_truth([]), allow_nan=False)


def test_original_generator_bytes_preserved():
    assert (
        hashlib.sha256(
            Path("src/model_learner/simulate/generator.py").read_bytes()
        ).hexdigest()
        == "fcb857d20c4e12d3ee0b9f1d89f97a2ea422d75a96547110ca8777aef33b98d1"
    )


def test_conditional_cell_diagnostics_do_not_weight_frequent_assignments():
    cells = [(0.1, 0.05, 0.15, 0.1), (0.7, 0.65, 0.75, 0.9)]
    conditional = stress._selection_truth(cells)
    observed = stress._selection_truth([cells[0]] * 9 + [cells[1]])
    assert conditional["truth_interval_coverage"] == 0.5
    assert observed["truth_interval_coverage"] == 0.9
    assert conditional["truth_rmse"] == pytest.approx(math.sqrt(0.04 / 2))
    assert observed["truth_rmse"] == pytest.approx(math.sqrt(0.04 / 10))
