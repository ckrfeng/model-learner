"""Validate M1's versioned evidence contracts."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    AttributionStatus,
    DatasetReference,
    DataSourceKind,
    Event,
    ExecutionConfiguration,
    Observation,
    Outcome,
    OutcomeStatus,
    Provenance,
    Run,
    Task,
    VerificationStatus,
)


def task() -> Task:
    return Task(
        description="Repair parser regression",
        acceptance_spec=AcceptanceSpec(identifier="pytest", version="1"),
    )


def test_missing_measurements_remain_unknown() -> None:
    attempt = Attempt(
        run_id=Run(task_id=task().task_id).run_id,
        configuration=ExecutionConfiguration(provider="example", model="model-a"),
    )

    assert attempt.input_tokens is None
    assert attempt.output_tokens is None
    assert attempt.cost_usd is None
    assert attempt.configuration.model_version is None


def test_event_builds_a_stable_key_from_observed_data() -> None:
    timestamp = datetime(2026, 10, 9, tzinfo=UTC)
    common = {
        "observed_at": timestamp,
        "source": "fixture",
        "source_version": "1",
        "machine_id": "test-machine",
        "capture_method": "import",
        "native_session_id": "native-123",
        "event_type": "tool_finished",
        "provenance": Provenance.OBSERVED,
        "payload": {"exit_code": 0},
    }

    assert Event(**common).stable_key == Event(**common).stable_key


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (
            lambda: Event(
                observed_at=datetime(2026, 10, 9),
                source="fixture",
                source_version="1",
                machine_id="test-machine",
                capture_method="import",
                native_session_id="native-123",
                event_type="tool_finished",
                provenance=Provenance.OBSERVED,
            ),
            "timestamps must include a timezone",
        ),
        (
            lambda: Outcome(
                run_id=Run(task_id=task().task_id).run_id,
                status=OutcomeStatus.SUCCESS,
                verification_status=VerificationStatus.VERIFIED,
                assessment_source="manual",
            ),
            "verified outcomes require one or more evidence_ids",
        ),
        (
            lambda: Outcome(
                run_id=Run(task_id=task().task_id).run_id,
                status=OutcomeStatus.SUCCESS,
                verification_status=VerificationStatus.VERIFIED,
                assessment_source="agent_report",
                evidence_ids=(uuid4(),),
            ),
            "agent report alone cannot be marked verified",
        ),
    ],
)
def test_invalid_records_fail_validation(factory: object, message: str) -> None:
    with pytest.raises(ValidationError, match=message):
        factory()  # type: ignore[operator]


def test_task_identity_is_independent_of_run_identity() -> None:
    declared_task = task()
    run = Run(task_id=declared_task.task_id)

    assert run.task_id == declared_task.task_id
    assert run.run_id != declared_task.task_id


def test_schema_versions_reject_unsupported_contracts() -> None:
    with pytest.raises(ValidationError, match="schema_version"):
        Task(
            schema_version=3,
            description="Unsupported contract",
            acceptance_spec=AcceptanceSpec(identifier="pytest", version="1"),
        )


def test_schema_version_one_observations_remain_readable_but_ineligible() -> None:
    legacy = Observation(
        schema_version=1,
        source_kind=DataSourceKind.REAL,
        task_group="maintenance",
        configuration=ExecutionConfiguration(provider="example", model="model-a"),
    )

    assert legacy.dataset is None
    assert legacy.eligible_for_configuration_learning is False


def test_configuration_identity_is_stable_and_versioned() -> None:
    first = ExecutionConfiguration(
        provider="example",
        model="model-a",
        model_version="2026-10-01",
        harness="codex",
        harness_version="1.0",
    )
    second = ExecutionConfiguration(
        provider="example",
        model="model-a",
        model_version="2026-10-01",
        harness="codex",
        harness_version="1.0",
    )

    assert first.configuration_id == second.configuration_id
    assert first.schema_version == 2


def test_observation_rejects_mixed_or_temporally_invalid_learning_labels() -> None:
    decision_at = datetime(2026, 10, 9, tzinfo=UTC)
    dataset = DatasetReference(
        source_kind=DataSourceKind.SIMULATED,
        dataset_id="simulator",
        dataset_version="1",
    )
    common = {
        "source_kind": DataSourceKind.SIMULATED,
        "dataset": dataset,
        "source_record_id": "row-1",
        "task_group": "maintenance",
        "configuration": ExecutionConfiguration(provider="example", model="model-a"),
        "outcome_status": OutcomeStatus.SUCCESS,
        "verification_status": VerificationStatus.VERIFIED,
        "decision_at": decision_at,
        "label_available_at": datetime(2026, 10, 10, tzinfo=UTC),
        "recorded_at": datetime(2026, 10, 11, tzinfo=UTC),
    }

    with pytest.raises(ValidationError, match="single-configuration"):
        Observation(
            **common,
            attribution_status=AttributionStatus.MIXED_CONFIGURATION,
            eligible_for_configuration_learning=True,
        )
    with pytest.raises(ValidationError, match="must not precede decision_at"):
        Observation(
            **(
                common
                | {
                    "attribution_status": AttributionStatus.SINGLE_CONFIGURATION,
                    "label_available_at": datetime(2026, 10, 8, tzinfo=UTC),
                }
            ),
        )
    with pytest.raises(ValidationError, match="stable_key"):
        Observation(
            **(
                common
                | {
                    "attribution_status": AttributionStatus.SINGLE_CONFIGURATION,
                    "stable_key": "not-derived",
                }
            ),
        )
