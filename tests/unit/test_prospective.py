"""New synthetic fixtures only; no private executions or transcripts."""

import math
from dataclasses import FrozenInstanceError, asdict, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    ExecutionConfiguration,
    Observation,
    ResourceBudget,
)
from model_learner.learn.prospective import (
    CompatibilityPolicy,
    ConfigurationMember,
    TaskMember,
    canonical,
    forecast,
    freeze,
    score_frozen,
)

START = datetime(2026, 1, 1, tzinfo=UTC)
CUTOFF = START + timedelta(hours=1)
DATASET = DatasetReference(
    source_kind="simulated", dataset_id="prospective-fixture", dataset_version="1"
)
TARGET = AcceptanceSpec(identifier="synthetic-boundary-contract", version="1")
LOW = ExecutionConfiguration(
    provider="fixture",
    model="fixture",
    reasoning_level="low",
    harness="fixture",
    harness_version="1",
    metadata={"network": "off"},
)
LOW2 = ExecutionConfiguration(
    provider="fixture",
    model="fixture",
    reasoning_level="low",
    harness="fixture",
    harness_version="2",
    metadata={"network": "off"},
)
HIGH = ExecutionConfiguration(
    provider="fixture",
    model="fixture",
    reasoning_level="high",
    harness="fixture",
    harness_version="1",
    metadata={"network": "off"},
)
T1, T2, T3, T4 = (UUID(int=i) for i in range(1, 5))
RUN = UUID(int=100)


def policy():
    return CompatibilityPolicy(
        "fixture/v1",
        START,
        DATASET.model_dump_json(),
        TARGET.model_dump_json(),
        "null",
        tuple(
            ConfigurationMember(c.model_dump_json(), family)
            for c, family in ((LOW, "low"), (LOW2, "low"), (HIGH, "high"))
        ),
        tuple(
            TaskMember(str(t), g, f)
            for t, g, f in (
                (T1, "scalar", "boundary"),
                (T2, "structured", "boundary"),
                (T3, "other-scalar", "other"),
                (T4, "scalar", "boundary"),
            )
        ),
    )


def row(i, task=T1, configuration=LOW, group="scalar", success=True, **changes):
    values = dict(
        source_kind="simulated",
        dataset=DATASET,
        source_record_id=f"synthetic-{i}",
        task_id=task,
        run_id=UUID(int=1000 + i),
        task_group=group,
        configuration=configuration,
        acceptance_spec=TARGET,
        attribution_status="single_configuration",
        eligible_for_configuration_learning=True,
        outcome_status="success" if success else "failure",
        verification_status="verified",
        decision_at=START + timedelta(seconds=i + 1),
        recorded_at=START + timedelta(seconds=i + 2),
        label_available_at=START + timedelta(seconds=i + 2),
    )
    return Observation(**(values | changes))


def predict(rows=(), configuration=LOW2, **kwargs):
    return forecast(
        rows,
        policy=kwargs.pop("policy", policy()),
        task_id=T4,
        run_id=RUN,
        configuration=configuration,
        cutoff=CUTOFF,
        **kwargs,
    )


def test_a_b_c_have_distinct_correct_evidence_without_mutating_records():
    rows = [
        row(1),
        row(2, task=T2, group="structured", success=False),
        row(3, configuration=HIGH, success=False),
    ]
    before = [r.model_dump_json() for r in rows]
    a, b, c = predict(rows).predictions
    assert [(p.successes, p.failures) for p in (a, b, c)] == [(0, 0), (1, 0), (1, 1)]
    assert [p.probability for p in (a, b, c)] == [0.5, 2 / 3, 0.5]
    assert b.evidence_runs == (str(rows[0].run_id),)
    assert [r.model_dump_json() for r in rows] == before


@pytest.mark.parametrize("field", ["decision_at", "recorded_at", "label_available_at"])
def test_future_labels_and_records_do_not_change_forecast(field):
    previous = row(1)
    changes = {field: CUTOFF + timedelta(seconds=1)}
    if field in ("decision_at", "label_available_at"):
        changes["recorded_at"] = CUTOFF + timedelta(seconds=2)
    if field == "decision_at":
        changes["label_available_at"] = CUTOFF + timedelta(seconds=2)
    future_success = row(2, **changes)
    future_failure = row(2, success=False, **changes)
    assert (
        predict([previous, future_success]).predictions
        == predict([previous, future_failure]).predictions
    )
    assert (
        predict([previous, future_success]).predictions
        == predict([previous]).predictions
    )


def test_no_current_task_leakage_from_other_arm_or_previous_run():
    current = row(1, task=T4, configuration=HIGH)
    assert predict([current]).predictions == predict().predictions


def test_policy_must_precede_forecast():
    with pytest.raises(ValueError, match="not available"):
        predict(policy=replace(policy(), declared_at=CUTOFF + timedelta(seconds=1)))


@pytest.mark.parametrize(
    "change",
    [
        {"reasoning_level": "high"},
        {"model": "other"},
        {"provider": "other"},
        {"model_version": "other"},
        {"harness": "other"},
        {"metadata": {"network": "on"}},
    ],
)
def test_incompatible_configurations_cannot_share_family(change):
    values = LOW.model_dump()
    values.update(change)
    values["configuration_id"] = None
    other = ExecutionConfiguration(**values)
    with pytest.raises(ValueError, match="incompatible"):
        replace(
            policy(),
            configurations=(
                ConfigurationMember(LOW.model_dump_json(), "same"),
                ConfigurationMember(other.model_dump_json(), "same"),
            ),
        )


def test_cosmetic_metadata_and_reviewed_version_changes_can_share():
    values = LOW2.model_dump()
    values["configuration_id"] = None
    values["metadata"] = {"network": "off", "settings_source": "synthetic wording"}
    other = ExecutionConfiguration(**values)
    replace(
        policy(),
        configurations=(
            ConfigurationMember(LOW.model_dump_json(), "same"),
            ConfigurationMember(other.model_dump_json(), "same"),
        ),
    )


def test_unlisted_configuration_excluded_and_cannot_be_prediction_target():
    values = LOW.model_dump()
    values["configuration_id"] = None
    values["harness_version"] = "unreviewed"
    unlisted = ExecutionConfiguration(**values)
    assert (
        predict([row(1, configuration=unlisted)]).predictions == predict().predictions
    )
    with pytest.raises(ValueError, match="not explicitly admitted"):
        predict(configuration=unlisted)


def test_wrong_group_rejected_and_other_family_not_used_by_c():
    with pytest.raises(ValueError, match="contradicts"):
        predict([row(1, group="structured")])
    # A/B intentionally use the same narrow group; C has a different explicit family.
    assert (
        predict([row(1, task=T3, group="other-scalar")]).predictions[2].successes == 0
    )


def test_duplicate_task_and_conflicting_group_membership_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        replace(policy(), tasks=policy().tasks + (policy().tasks[0],))
    with pytest.raises(ValueError, match="conflicting families"):
        replace(
            policy(),
            tasks=policy().tasks
            + (TaskMember(str(UUID(int=8)), "scalar", "conflict"),),
        )


def test_targets_budgets_verification_and_duplicates_are_not_pooled():
    good = row(1)
    wrong = [
        row(2, acceptance_spec=AcceptanceSpec(identifier="other", version="1")),
        row(3, resource_budget=ResourceBudget(max_duration_seconds=10)),
        row(
            4,
            verification_status="unverified",
            eligible_for_configuration_learning=False,
        ),
        row(
            5,
            dataset=DatasetReference(
                source_kind="simulated", dataset_id="other", dataset_version="1"
            ),
        ),
    ]
    assert predict([good, good, *wrong]).predictions == predict([good]).predictions


def test_freeze_is_exclusive_immutable_and_scores_success_and_failure(tmp_path: Path):
    bundle = predict([row(1)])
    path = tmp_path / "forecast.json"
    sha = freeze(path, bundle)
    before = path.read_bytes()
    with pytest.raises(FileExistsError):
        freeze(path, predict())
    with pytest.raises(FrozenInstanceError):
        bundle.cutoff = "replacement"
    for success in (True, False):
        outcome = row(
            20,
            task=T4,
            configuration=LOW2,
            success=success,
            run_id=RUN,
            decision_at=CUTOFF + timedelta(seconds=1),
            recorded_at=CUTOFF + timedelta(seconds=3),
            label_available_at=CUTOFF + timedelta(seconds=3),
        )
        scores = score_frozen(path, sha, outcome)
        assert scores["B"]["brier_score"] == pytest.approx((2 / 3 - int(success)) ** 2)
        assert scores["B"]["log_loss"] == pytest.approx(
            -math.log(2 / 3 if success else 1 / 3)
        )
        assert path.read_bytes() == before
    # Predictions remain unchanged even after computing a later fit with new outcomes.
    predict([row(1), row(8, task=T2, group="structured", success=False)])
    assert canonical(asdict(bundle)) + "\n" == before.decode()
    path.chmod(0o600)
    path.write_text("{}")
    with pytest.raises(ValueError, match="digest mismatch"):
        score_frozen(path, sha, outcome)


def test_scoring_rejects_unbound_or_unverified_outcomes(tmp_path: Path):
    path = tmp_path / "forecast.json"
    sha = freeze(path, predict())
    outcome = row(
        5,
        task=T4,
        configuration=LOW2,
        run_id=RUN,
        decision_at=CUTOFF + timedelta(seconds=1),
        recorded_at=CUTOFF + timedelta(seconds=3),
        label_available_at=CUTOFF + timedelta(seconds=3),
    )
    for changes in (
        {"run_id": UUID(int=99)},
        {
            "verification_status": "unverified",
            "eligible_for_configuration_learning": False,
        },
        {"resource_budget": ResourceBudget(max_tokens=1)},
    ):
        values = outcome.model_dump()
        values.update(changes)
        values["stable_key"] = None
        with pytest.raises(ValueError):
            score_frozen(path, sha, Observation(**values))
