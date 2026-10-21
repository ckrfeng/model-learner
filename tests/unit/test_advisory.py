"""W6A fictional observations; no measured model performance or private data."""

from dataclasses import replace
from datetime import timedelta
from uuid import UUID

import pytest

from model_learner.domain.models import (
    DataSourceKind,
    ExecutionConfiguration,
    ResourceBudget,
    Task,
)
from model_learner.learn.advisory import AdvisoryRequest, advise
from model_learner.learn.prospective import ConfigurationMember
from tests.unit.test_prospective import (
    CUTOFF,
    HIGH,
    LOW,
    LOW2,
    START,
    T4,
    TARGET,
    policy,
    row,
)


def request(**changes):
    values = dict(
        task=Task(
            task_id=T4,
            description="Fictional held-out task",
            acceptance_spec=TARGET,
            task_group="scalar",
            created_at=START,
        ),
        candidates=(LOW, LOW2, HIGH),
        policy=policy(),
        cutoff=CUTOFF,
    )
    return AdvisoryRequest(**(values | changes))


def predictions(report, index=0):
    return {p["predictor"]: p for p in report["candidates"][index]["estimates"]}


def test_cold_start_has_prior_and_abstains():
    result = advise(request())
    assert result["version"] == "configuration-advisory/v1"
    assert result["advisory"]["status"] == "abstain"
    assert result["advisory"]["selected_configuration_id"] is None
    for candidate in result["candidates"]:
        assert len(candidate["estimates"]) == 6
        for estimate in candidate["estimates"]:
            assert estimate["probability"] == 0.5
            assert estimate["eligible_count"] == 0
            assert estimate["lower"] == pytest.approx(0.025)
            assert estimate["upper"] == pytest.approx(0.975)


@pytest.mark.parametrize("success, expected", [(True, 2 / 3), (False, 1 / 3)])
def test_verified_labels_update_exact_configuration(success, expected):
    result = advise(request(), observations=[row(1, success=success)])
    estimates = predictions(result)
    assert estimates["A"]["probability"] == expected
    assert estimates["A"]["eligible_count"] == 1
    assert predictions(result, 2)["A"]["probability"] == 0.5


@pytest.mark.parametrize("state", ["unknown", "censored", "unverified"])
def test_unknown_is_not_binary_evidence(state):
    changes = dict(eligible_for_configuration_learning=False)
    if state == "unverified":
        changes["verification_status"] = "unverified"
    else:
        changes.update(outcome_status=state, label_available_at=None)
    result = advise(request(), observations=[row(1, **changes)])
    assert result["eligible_source_count"] == 0
    assert predictions(result)["A"]["probability"] == 0.5
    assert sum(result["exclusions"].values()) == 1


def test_distinct_models_and_efforts_and_declared_compatible_runtime():
    lower = ExecutionConfiguration(
        provider="fixture",
        model="fictional-lower",
        reasoning_level="low",
        harness="fixture",
        harness_version="1",
    )
    req = request()
    new_policy = replace(
        req.policy,
        configurations=(
            *req.policy.configurations,
            ConfigurationMember(lower.model_dump_json(), "lower"),
        ),
    )
    req = request(policy=new_policy, candidates=(LOW, HIGH, lower))
    result = advise(
        req,
        observations=[
            row(1),
            row(2, configuration=HIGH, success=False),
            row(3, configuration=lower),
            row(4, configuration=LOW2),
        ],
    )
    assert [predictions(result, i)["A"]["probability"] for i in range(3)] == [
        2 / 3,
        1 / 3,
        2 / 3,
    ]
    assert predictions(result)["B"]["probability"] == 3 / 4
    assert (
        len({c["configuration"]["configuration_id"] for c in result["candidates"]}) == 3
    )


def test_target_and_paired_arm_are_excluded():
    result = advise(
        request(), observations=[row(1, task=T4), row(2, task=T4, configuration=HIGH)]
    )
    assert result["eligible_source_count"] == 0
    assert result["exclusions"] == {"prediction_task": 2}
    assert all(p["probability"] == 0.5 for p in predictions(result).values())


@pytest.mark.parametrize("field", ["decision_at", "label_available_at", "recorded_at"])
def test_later_source_times_do_not_change_initial_predictions(field):
    later = CUTOFF + timedelta(seconds=1)
    changes = {field: later, "recorded_at": later}
    if field == "decision_at":
        changes["label_available_at"] = later
    report = advise(request(), observations=[row(1, **changes)])
    assert predictions(report) == predictions(advise(request()))
    assert report["availability"]["method"] == "declared-source-timestamps-only/v1"


def test_duplicate_replay_never_inflates_count():
    source = row(1)
    result = advise(request(), observations=[source, source, source])
    assert predictions(result)["A"]["eligible_count"] == 1
    assert result["exclusions"] == {"duplicate": 2}


@pytest.mark.parametrize(
    "changes, reason",
    [
        (
            {"acceptance_spec": TARGET.model_copy(update={"version": "2"})},
            "other_target_or_budget",
        ),
        ({"resource_budget": ResourceBudget(max_tokens=100)}, "other_target_or_budget"),
        (
            {"configuration": ExecutionConfiguration(model="unapproved")},
            "not_admitted_by_policy",
        ),
    ],
)
def test_wrong_target_budget_or_configuration_is_excluded(changes, reason):
    report = advise(request(), observations=[row(1, **changes)])
    assert report["eligible_source_count"] == 0
    assert report["exclusions"] == {reason: 1}


def test_wrong_dataset_and_source_kind_are_not_pooled():
    from tests.unit.test_prospective import DATASET

    result = advise(
        request(),
        observations=[
            row(1, dataset=DATASET.model_copy(update={"dataset_version": "2"})),
            row(
                2,
                source_kind="benchmark",
                dataset=DATASET.model_copy(
                    update={"source_kind": DataSourceKind.BENCHMARK}
                ),
            ),
        ],
    )
    assert result["eligible_source_count"] == 0
    assert result["exclusions"] == {"other_dataset": 2}


def test_unknown_resources_are_null_and_known_resources_descriptive():
    report = advise(
        request(), observations=[row(1), row(2, cost_usd=2, latency_seconds=3)]
    )
    estimate = predictions(report)["A"]
    assert estimate["tokens"] is None
    assert estimate["resources"]["cost_usd"] == dict(
        known_count=1, missing_count=1, mean=2, minimum=2, maximum=2
    )
    assert report["candidates"][0]["effective_backend_revision"] is None
    empty = predictions(advise(request()))["A"]["resources"]["latency_seconds"]
    assert empty["mean"] is empty["minimum"] is empty["maximum"] is None


def test_policy_comparisons_match_independent_hand_calculation():
    from tests.unit.test_prospective import T2, T3

    # A: 1 success; B: 2 successes; C: 2 successes + 1 failure.
    # global adds other family/arm: 2 successes + 3 failures.
    # per-arm spans groups/families: 1 success + 2 failures.
    rows = [
        row(1),
        row(2, configuration=LOW2),
        row(3, task=T2, group="structured", success=False),
        row(4, task=T3, group="other-scalar", success=False),
        row(5, configuration=HIGH, success=False),
    ]
    values = predictions(advise(request(), observations=rows))
    expected = {
        "fixed_prior": (0, 0),
        "global": (2, 3),
        "per_arm": (1, 2),
        "A": (1, 0),
        "B": (2, 0),
        "C": (2, 1),
    }
    for name, (successes, failures) in expected.items():
        item = values[name]
        assert (item["successes"], item["failures"]) == (successes, failures)
        assert item["probability"] == (1 + successes) / (2 + successes + failures)
        assert len(item["evidence"]) == successes + failures


def test_deterministic_without_mutating_input():
    req, rows = request(), [row(1), row(2, success=False)]
    before = [r.model_dump_json() for r in rows]
    assert advise(req, observations=rows) == advise(req, observations=reversed(rows))
    assert before == [r.model_dump_json() for r in rows]


def test_metadata_and_task_prose_are_never_exported():
    import json

    req = request()
    req.task.description = "fictional private prose sentinel"
    req.task.metadata = {
        "source_path": "/fictional/private/task",
        "payload": "fictional payload sentinel",
    }
    source = row(
        1,
        metadata={
            "source_path": "/fictional/private/row",
            "payload": "fictional payload sentinel",
        },
    )
    output = json.dumps(advise(req, observations=[source, row(2, task=UUID(int=999))]))
    for value in (
        "private prose sentinel",
        "/fictional/private",
        "payload sentinel",
        str(UUID(int=999)),
    ):
        assert value not in output


def test_unapproved_decision_policy_cannot_select_or_hide_estimates():
    result = advise(
        request(decision_policy="choose-highest-mean"), observations=[row(1)]
    )
    assert result["advisory"]["reason"] == "unsupported_decision_policy"
    assert result["advisory"]["selected_configuration_id"] is None
    assert predictions(result)["A"]["probability"] == 2 / 3


@pytest.mark.parametrize(
    "change",
    ["budget", "acceptance", "task_group", "future", "candidate", "empty", "policy"],
)
def test_invalid_frozen_target_fails_closed(change):
    req = request()
    if change == "budget":
        req.task.resource_budget = ResourceBudget(max_tokens=1)
    elif change == "acceptance":
        req.task.acceptance_spec = TARGET.model_copy(update={"version": "2"})
    elif change == "task_group":
        req.task.task_group = "different"
    elif change == "future":
        req.task.created_at = CUTOFF + timedelta(seconds=1)
    elif change == "candidate":
        req.candidates = (ExecutionConfiguration(model="not-approved"),)
    elif change == "empty":
        req.candidates = ()
    else:
        req.policy = replace(req.policy, declared_at=CUTOFF + timedelta(seconds=1))
    with pytest.raises(ValueError):
        advise(req)


@pytest.mark.parametrize(
    "label", ["/fictional/private/path", "not a public identifier"]
)
def test_private_or_prose_identity_labels_are_rejected(label):
    req = request()
    from tests.unit.test_prospective import DATASET

    req.policy = replace(
        req.policy,
        dataset_json=DATASET.model_copy(update={"dataset_id": label}).model_dump_json(),
    )
    with pytest.raises(ValueError, match="public identifier"):
        advise(req)
