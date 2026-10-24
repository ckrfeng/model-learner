"""Synthetic M7 decision conventions; no measured utility or real task data."""

import copy
import json
from datetime import timedelta

import pytest
from pydantic import ValidationError

from model_learner.learn.advisory import advise
from model_learner.learn.utility import UtilityAdvice, evaluate_utility
from tests.unit.test_advisory import request
from tests.unit.test_prospective import CUTOFF, LOW, LOW2, row

DECISION = CUTOFF + timedelta(minutes=1)


def policy(version="quality-first/v1", **changes):
    values = {
        "version": version,
        "minimum_eligible_labels": 1,
        "maximum_interval_width": None,
        "maximum_cost_usd": None,
        "maximum_latency_seconds": None,
    }
    if version == "cost-sensitive/v1":
        values["success_value_usd"] = 12.0
    if version == "balanced/v1":
        values |= dict(
            quality_weight=0.5,
            cost_weight=0.25,
            latency_weight=0.25,
            cost_reference_usd=10.0,
            latency_reference_seconds=100.0,
        )
    return values | changes


def advisory(*, missing=False):
    return advise(
        request(candidates=(LOW, LOW2)),
        observations=[
            row(
                1,
                cost_usd=None if missing else 2.0,
                latency_seconds=None if missing else 10.0,
            ),
            row(2, configuration=LOW2, cost_usd=5.0, latency_seconds=30.0),
        ],
    )


def evaluate(report=None, **changes):
    return evaluate_utility(
        advisory() if report is None else report,
        **(dict(policy=policy(), predictor="A", decision_at=DECISION) | changes),
    )


def by_id(result, configuration=LOW):
    return next(
        c
        for c in result.candidates
        if c.configuration.configuration_id == configuration.configuration_id
    )


def test_quality_cost_and_balanced_hand_equations():
    quality = evaluate()
    assert quality.status == "abstain" and quality.reason == "utility_tie"
    cost = evaluate(policy=policy("cost-sensitive/v1"))
    assert cost.selected_configuration_id == LOW.configuration_id
    assert by_id(cost).utility == pytest.approx(12 * (2 / 3) - 2)
    assert by_id(cost, LOW2).utility == pytest.approx(12 * (2 / 3) - 5)
    balanced = evaluate(policy=policy("balanced/v1"))
    assert balanced.selected_configuration_id == LOW.configuration_id
    assert by_id(balanced).utility == pytest.approx(
        0.5 * (2 / 3) - 0.25 * (2 / 10) - 0.25 * (10 / 100)
    )
    assert by_id(balanced, LOW2).utility == pytest.approx(
        0.5 * (2 / 3) - 0.25 * (5 / 10) - 0.25 * (30 / 100)
    )
    expensive = advise(
        request(candidates=(LOW, LOW2)),
        observations=[
            row(1, cost_usd=10, latency_seconds=30),
            row(2, cost_usd=10, latency_seconds=30),
            row(3, configuration=LOW2, success=False, cost_usd=1, latency_seconds=10),
        ],
    )
    result = evaluate(
        expensive, policy=policy(maximum_cost_usd=20.0, maximum_latency_seconds=100.0)
    )
    assert result.selected_configuration_id == LOW.configuration_id
    assert by_id(result).utility == 0.75
    # Caller-supplied weights can prioritize latency over the higher quality.
    result = evaluate(
        expensive,
        policy=policy(
            "balanced/v1", quality_weight=0.0, cost_weight=0.0, latency_weight=1.0
        ),
    )
    assert result.selected_configuration_id == LOW2.configuration_id
    assert by_id(result, LOW2).utility == -0.1


@pytest.mark.parametrize(
    "kind,changes,reason",
    [
        ("quality-first/v1", {}, None),
        ("quality-first/v1", {"maximum_cost_usd": 10.0}, "missing_cost_estimate"),
        (
            "quality-first/v1",
            {"maximum_latency_seconds": 100.0},
            "missing_latency_estimate",
        ),
        ("cost-sensitive/v1", {}, "missing_cost_estimate"),
        (
            "balanced/v1",
            {"quality_weight": 1.0, "cost_weight": 0.0, "latency_weight": 0.0},
            None,
        ),
        (
            "balanced/v1",
            {"quality_weight": 0.0, "cost_weight": 1.0, "latency_weight": 0.0},
            "missing_cost_estimate",
        ),
        (
            "balanced/v1",
            {"quality_weight": 0.0, "cost_weight": 0.0, "latency_weight": 1.0},
            "missing_latency_estimate",
        ),
    ],
)
def test_missing_resources_gate_only_required_dimensions(kind, changes, reason):
    result = evaluate(advisory(missing=True), policy=policy(kind, **changes))
    candidate = by_id(result)
    assert candidate.resources.cost_usd.mean is None
    assert candidate.resources.cost_usd.known_count == 0
    assert candidate.resources.cost_usd.missing_count == 1
    assert candidate.resources.latency_seconds.mean is None
    assert candidate.eligible == (reason is None)
    if reason:
        assert reason in candidate.reasons and candidate.utility is None


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"minimum_eligible_labels": 2}, "insufficient_eligible_labels"),
        ({"maximum_interval_width": 0.1}, "interval_too_wide"),
        ({"maximum_cost_usd": 1.0}, "maximum_cost_exceeded"),
        ({"maximum_latency_seconds": 1.0}, "maximum_latency_exceeded"),
    ],
)
def test_explicit_constraints_and_all_ineligible_abstention(changes, reason):
    result = evaluate(policy=policy(**changes))
    assert result.status == "abstain" and result.reason == "no_eligible_candidates"
    assert result.selected_configuration_id is result.selected_utility is None
    assert all(reason in c.reasons for c in result.candidates)


def test_predictor_availability_status_and_fixed_prior_evidence_gate():
    prior = evaluate(predictor="fixed_prior")
    assert prior.reason == "no_eligible_candidates"
    assert all(c.eligible_count == 0 for c in prior.candidates)
    raw = advisory()
    for c in raw["candidates"]:
        c["estimates"] = [e for e in c["estimates"] if e["predictor"] != "A"]
    missing = evaluate(raw)
    assert all(
        c.status == "unavailable" and c.resources is None and c.eligible_count is None
        for c in missing.candidates
    )
    raw = advisory()
    for c in raw["candidates"]:
        next(e for e in c["estimates"] if e["predictor"] == "A")["status"] = (
            "unavailable"
        )
    assert evaluate(raw).reason == "no_eligible_candidates"
    for candidate in raw["candidates"]:
        next(e for e in candidate["estimates"] if e["predictor"] == "A")["status"] = (
            "unsupported"
        )
    with pytest.raises(ValueError, match="invalid utility policy or advisory contract"):
        evaluate(raw)
    with pytest.raises(ValueError):
        evaluate(predictor="unknown")


def test_tie_absolute_tolerance_and_order_invariance():
    raw = advisory()
    for c in raw["candidates"]:
        e = next(e for e in c["estimates"] if e["predictor"] == "A")
        cost = (
            2.0
            if c["configuration"]["configuration_id"] == LOW.configuration_id
            else 2.0 + 0.5e-12
        )
        for k in ("mean", "minimum", "maximum"):
            e["resources"]["cost_usd"][k] = cost
    assert evaluate(raw, policy=policy("cost-sensitive/v1")).reason == "utility_tie"
    original = copy.deepcopy(raw)
    raw["candidates"].reverse()
    assert evaluate(raw, policy=policy("cost-sensitive/v1")) == evaluate(
        original, policy=policy("cost-sensitive/v1")
    )
    for c in raw["candidates"]:
        if c["configuration"]["configuration_id"] == LOW2.configuration_id:
            e = next(e for e in c["estimates"] if e["predictor"] == "A")
            for k in ("mean", "minimum", "maximum"):
                e["resources"]["cost_usd"][k] = 2.0 + 2e-12
    assert (
        evaluate(raw, policy=policy("cost-sensitive/v1")).selected_configuration_id
        == LOW.configuration_id
    )


@pytest.mark.parametrize(
    "version,changes",
    [
        ("quality-first/v1", {"minimum_eligible_labels": True}),
        ("quality-first/v1", {"minimum_eligible_labels": 0}),
        ("quality-first/v1", {"minimum_eligible_labels": 1.0}),
        ("quality-first/v1", {"maximum_cost_usd": True}),
        ("quality-first/v1", {"maximum_cost_usd": -1}),
        ("quality-first/v1", {"maximum_latency_seconds": float("nan")}),
        ("quality-first/v1", {"maximum_interval_width": float("inf")}),
        ("quality-first/v1", {"maximum_interval_width": 1.1}),
        ("quality-first/v1", {"unexpected": "synthetic-private-marker"}),
        ("cost-sensitive/v1", {"success_value_usd": 0.0}),
        ("cost-sensitive/v1", {"success_value_usd": float("inf")}),
        ("cost-sensitive/v1", {"success_value_usd": False}),
        ("balanced/v1", {"quality_weight": -0.1}),
        ("balanced/v1", {"cost_weight": float("nan")}),
        ("balanced/v1", {"quality_weight": 0.1}),
        ("balanced/v1", {"cost_reference_usd": 0.0}),
        ("balanced/v1", {"latency_reference_seconds": -1.0}),
        ("balanced/v1", {"latency_weight": True}),
    ],
)
def test_invalid_policies_fail_closed_without_payload(version, changes):
    with pytest.raises(ValueError) as error:
        evaluate(policy=policy(version, **changes))
    assert str(error.value) == "invalid utility policy or advisory contract"
    assert "synthetic-private-marker" not in str(error.value)


def test_required_fields_no_implicit_policy_limits_or_timestamp():
    for name in policy():
        p = policy()
        del p[name]
        with pytest.raises(ValueError):
            evaluate(policy=p)
    with pytest.raises(ValueError):
        evaluate(decision_at=DECISION.replace(tzinfo=None))
    with pytest.raises(ValueError):
        evaluate(decision_at=CUTOFF - timedelta(seconds=1))
    with pytest.raises(ValueError):
        evaluate(decision_at=True)


@pytest.mark.parametrize(
    "change",
    [
        "probability",
        "counts",
        "coverage",
        "cost",
        "extra",
        "duplicate",
        "version",
        "identity",
    ],
)
def test_malformed_advisory_refusal(change):
    raw = advisory()
    selected = next(
        e for e in raw["candidates"][0]["estimates"] if e["predictor"] == "A"
    )
    if change == "probability":
        selected["probability"] = float("nan")
    elif change == "counts":
        selected["successes"] = 2
    elif change == "coverage":
        selected["resources"]["cost_usd"]["known_count"] = 0
    elif change == "cost":
        selected["resources"]["cost_usd"]["mean"] = True
    elif change == "extra":
        raw["candidates"][0]["configuration"]["metadata"] = {
            "locator": "/synthetic/private"
        }
    elif change == "duplicate":
        raw["candidates"].append(copy.deepcopy(raw["candidates"][0]))
    elif change == "version":
        raw["version"] = "unsupported"
    else:
        raw["task_id"] = "/synthetic/private"
    with pytest.raises(ValueError) as error:
        evaluate(raw)
    assert str(error.value) == "invalid utility policy or advisory contract"


def test_identity_privacy_immutability_and_point_utility():
    raw = advisory()
    raw["unrelated"] = {
        "text": "synthetic-private-prose",
        "locator": "/synthetic/private",
    }
    before = json.dumps(raw, sort_keys=True)
    result = evaluate(raw, policy=policy("cost-sensitive/v1"))
    assert result.advisory.cutoff == raw["cutoff"]
    for field in (
        "dataset",
        "acceptance",
        "resource_budget",
        "versions",
        "task_id",
        "task_group",
    ):
        assert result.advisory.model_dump()[field] == raw[field]
    assert result.policy.model_dump() == policy("cost-sensitive/v1")
    assert json.dumps(raw, sort_keys=True) == before
    assert [c.configuration.configuration_id for c in result.candidates] == sorted(
        c["configuration"]["configuration_id"] for c in raw["candidates"]
    )
    encoded = result.model_dump_json()
    for marker in (
        "synthetic-private-prose",
        "/synthetic/private",
        "utility_lower",
        "utility_upper",
        "propensity",
    ):
        assert marker not in encoded
    assert UtilityAdvice.model_validate_json(encoded) == result
    with pytest.raises(ValidationError):
        by_id(result).resources.cost_usd.mean = 0.0
    assert by_id(result).lower == next(
        e["lower"] for e in raw["candidates"][0]["estimates"] if e["predictor"] == "A"
    )
