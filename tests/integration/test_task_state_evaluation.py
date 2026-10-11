"""Sanitized native-capture checkpoints and independent fixture labels."""

from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

import pytest

from model_learner.adapters.codex import read_codex_capture
from model_learner.domain.models import (
    AcceptanceSpec,
    AttributionStatus,
    DatasetReference,
    DataSourceKind,
    ExecutionConfiguration,
    Observation,
    OutcomeStatus,
    VerificationStatus,
)
from model_learner.execution import extract_execution_checkpoints
from model_learner.learn.task_state import TaskStateExample, evaluate_task_state
from model_learner.verification.junit import parse_junit_xml

FIXTURES = Path(__file__).parents[1] / "fixtures/execution"
START = datetime(2026, 10, 10, 12, tzinfo=UTC)


def test_native_receipts_rebuilt_and_fixture_final_junit_used_only_as_label():
    batch = read_codex_capture(
        FIXTURES / "controlled_capture.jsonl", machine_id="fixture"
    )
    events = tuple(
        event.model_copy(
            update={"ingested_at": event.observed_at + timedelta(seconds=1)}
        )
        for event in batch.events
    )
    task_id = uuid5(NAMESPACE_URL, "task-state-integration/task")
    run_id = uuid5(NAMESPACE_URL, "task-state-integration/run")
    checkpoint = START + timedelta(seconds=4)
    point = extract_execution_checkpoints(
        events, session_id=batch.sessions[0].session_id, checkpoints=[checkpoint]
    )[0]
    point = point.model_copy(update={"task_id": task_id, "run_id": run_id})
    assert point.facts.event_count == 3
    summary = parse_junit_xml((FIXTURES / "report_passed.xml").read_bytes())
    assert summary.counts.passed == 2
    dataset = DatasetReference(
        source_kind=DataSourceKind.BENCHMARK,
        dataset_id="controlled-receipts",
        dataset_version="1",
    )
    spec = AcceptanceSpec(identifier="controlled-fixture-tests", version="1")
    row = Observation(
        source_kind=DataSourceKind.BENCHMARK,
        dataset=dataset,
        source_record_id="fixture-run",
        task_id=task_id,
        run_id=run_id,
        task_group="fixture",
        configuration=ExecutionConfiguration(model="fixture-model", harness="fixture"),
        acceptance_spec=spec,
        outcome_status=OutcomeStatus.SUCCESS,
        verification_status=VerificationStatus.VERIFIED,
        attribution_status=AttributionStatus.SINGLE_CONFIGURATION,
        eligible_for_configuration_learning=True,
        evidence_ids=(uuid5(NAMESPACE_URL, "fixture-final-junit"),),
        decision_at=START,
        label_available_at=START + timedelta(seconds=20),
        recorded_at=START + timedelta(seconds=20),
    )
    example = TaskStateExample(
        observation=row,
        checkpoint=point,
        initial_available_at=START,
        inputs_available_at=checkpoint,
        events=events,
    )
    report = evaluate_task_state(
        [example],
        dataset=dataset,
        acceptance_spec=spec,
        train_until=START,
        evaluation_at=START + timedelta(seconds=30),
        checkpoint_offset_seconds=4,
        bootstrap_replicates=100,
    )
    assert report.scored_count == 1
    assert report.variants[0].status == "insufficient_data"
    # Retaining future events cannot change bounded facts or target features.
    assert not report.exclusions

    foreign_events = (
        events[0].model_copy(update={"run_id": uuid5(NAMESPACE_URL, "foreign-run")}),
        *events[1:],
    )
    foreign_example = example.model_copy(update={"events": foreign_events})
    with pytest.raises(ValueError, match="facts disagree"):
        evaluate_task_state(
            [foreign_example],
            dataset=dataset,
            acceptance_spec=spec,
            train_until=START,
            evaluation_at=START + timedelta(seconds=30),
            checkpoint_offset_seconds=4,
            bootstrap_replicates=100,
        )
