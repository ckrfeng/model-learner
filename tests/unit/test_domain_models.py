"""Validate M1's versioned evidence contracts."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    Event,
    ExecutionConfiguration,
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
