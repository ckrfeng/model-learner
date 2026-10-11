"""Pilot preregistration must retain separation and cannot schedule agent execution."""

from collections import Counter
from dataclasses import asdict

import pytest

from model_learner.benchmark.pilot import PILOT_TASK_IDS, build_pilot_plan
from model_learner.domain.models import ExecutionConfiguration


def configuration(reasoning_level="low"):
    return ExecutionConfiguration(
        provider="controlled-provider",
        model="controlled-model",
        reasoning_level=reasoning_level,
        harness="controlled-cli",
        harness_version="test-version",
        configuration_version="pilot-v1",
    )


def test_preregistered_paired_task_states_and_disjoint_partitions():
    a, b = configuration(), configuration("medium")
    plan = build_pilot_plan(configuration_a=a, configuration_b=b)
    assert len(plan.runs) == 24
    assert len(PILOT_TASK_IDS) == len(set(PILOT_TASK_IDS)) == 12
    assert [row.ordinal for row in plan.runs] == list(range(1, 25))
    for task_id in PILOT_TASK_IDS:
        pair = [row for row in plan.runs if row.fixture_id == task_id]
        assert {row.arm for row in pair} == {"A", "B"}
        assert len({row.partition for row in pair}) == 1
        assert len({row.initial_source_sha256 for row in pair}) == 1
        assert len({row.task_description_sha256 for row in pair}) == 1
        assert pair[0].configuration != pair[1].configuration
    for partition, task_count in (("training", 8), ("held_out", 4)):
        rows = [row for row in plan.runs if row.partition == partition]
        assert len({row.fixture_id for row in rows}) == task_count
        assert Counter(row.arm for row in rows) == {"A": task_count, "B": task_count}
        assert Counter(row.arm for row in rows[::2]) == {
            "A": task_count // 2,
            "B": task_count // 2,
        }
    assert plan.execution_status == "blocked_unvalidated_containment"
    assert plan.predictive_status == "blocked_export_contract_and_insufficient_data"
    assert plan.primary_checkpoint_seconds == 30
    assert plan.agent_wall_limit_seconds == 120
    assert plan == build_pilot_plan(configuration_a=a, configuration_b=b)
    other = build_pilot_plan(configuration_a=a, configuration_b=b, seed=2)
    assert plan.runs != other.runs
    # No realized outcomes, acceptance values or telemetry enter preregistration.
    assert "outcome" not in str(asdict(plan))


def test_plan_requires_operator_configuration_and_distinct_arms():
    a = configuration()
    with pytest.raises(ValueError, match="distinct"):
        build_pilot_plan(configuration_a=a, configuration_b=a)
    for field in (
        "provider",
        "model",
        "reasoning_level",
        "harness",
        "harness_version",
        "configuration_version",
    ):
        incomplete = a.model_copy(update={field: None})
        with pytest.raises(ValueError, match=field):
            build_pilot_plan(
                configuration_a=incomplete, configuration_b=configuration("medium")
            )
    with pytest.raises(ValueError, match="seed"):
        build_pilot_plan(
            configuration_a=a, configuration_b=configuration("medium"), seed=True
        )
