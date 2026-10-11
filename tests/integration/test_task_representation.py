"""Sanitized native checkpoint reconstruction and independent benchmark labels."""

import hashlib
from dataclasses import asdict
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
from model_learner.learn.task_state import TaskStateExample
from model_learner.representation import (
    RepresentationExample,
    TaskDescription,
    evaluate_task_representation,
)

FIXTURES = Path(__file__).parents[1] / "fixtures/execution"
START = datetime(2026, 10, 10, 12, tzinfo=UTC)


def example():
    batch = read_codex_capture(
        FIXTURES / "controlled_capture.jsonl", machine_id="fixture"
    )
    events = tuple(
        e.model_copy(update={"ingested_at": e.observed_at + timedelta(seconds=1)})
        for e in batch.events
    )
    task_id = uuid5(NAMESPACE_URL, "representation-integration/task")
    run_id = uuid5(NAMESPACE_URL, "representation-integration/run")
    time = START + timedelta(seconds=4)
    point = extract_execution_checkpoints(
        events, session_id=batch.sessions[0].session_id, checkpoints=[time]
    )[0]
    point = point.model_copy(update={"task_id": task_id, "run_id": run_id})
    text = "Implement a public integer clamping helper with ordered inclusive bounds."
    dataset = DatasetReference(
        source_kind=DataSourceKind.BENCHMARK,
        dataset_id="representation-receipt-fixture",
        dataset_version="1",
    )
    spec = AcceptanceSpec(identifier="public-clamp-tests", version="1")
    row = Observation(
        source_kind=DataSourceKind.BENCHMARK,
        dataset=dataset,
        source_record_id="fixture-run",
        task_id=task_id,
        run_id=run_id,
        task_group="fixture",
        configuration=ExecutionConfiguration(model="fixture", harness="fixture"),
        acceptance_spec=spec,
        outcome_status=OutcomeStatus.SUCCESS,
        verification_status=VerificationStatus.VERIFIED,
        attribution_status=AttributionStatus.SINGLE_CONFIGURATION,
        eligible_for_configuration_learning=True,
        evidence_ids=(uuid5(NAMESPACE_URL, "representation-fixture-final-junit"),),
        decision_at=START,
        label_available_at=START + timedelta(seconds=20),
        recorded_at=START + timedelta(seconds=20),
    )
    return RepresentationExample(
        state=TaskStateExample(
            observation=row,
            checkpoint=point,
            initial_available_at=START,
            inputs_available_at=time,
            events=events,
        ),
        description=TaskDescription(
            task_id=task_id,
            task_family="public-clamp",
            text=text,
            text_sha256=hashlib.sha256(text.encode()).hexdigest(),
            source="public",
            available_at=START,
        ),
    )


def evaluate(value):
    return evaluate_task_representation(
        [value],
        dataset=value.state.observation.dataset,
        acceptance_spec=value.state.observation.acceptance_spec,
        train_until=START,
        evaluation_at=START + timedelta(seconds=30),
        checkpoint_offset_seconds=4,
        bootstrap_replicates=100,
    )


def test_retained_events_rebuild_common_cohort_and_unknown_model_resources():
    value = example()
    result = evaluate(value)
    assert result.scored_count == 1 and not result.exclusions
    assert all(v.status == "insufficient_data" for v in result.variants)
    assert result.overhead["semantic"]["actual_load_seconds"] is None
    assert result.overhead["semantic"]["actual_model_memory_bytes"] is None
    assert "Public integer" not in str(asdict(result))
    # Later buffered events remain retained but do not enter checkpoint features.
    assert value.state.checkpoint.facts.event_count == 3
    foreign = value.state.events[0].model_copy(
        update={"run_id": uuid5(NAMESPACE_URL, "foreign-run")}
    )
    changed = value.model_copy(
        update={
            "state": value.state.model_copy(
                update={"events": (foreign, *value.state.events[1:])}
            )
        }
    )
    with pytest.raises(ValueError, match="facts disagree"):
        evaluate(changed)


def test_benchmark_without_native_evidence_is_not_promoted_to_simulation():
    value = example()
    changed = value.model_copy(
        update={"state": value.state.model_copy(update={"events": None})}
    )
    report = evaluate(changed)
    assert report.scored_count == 0
    assert report.exclusions["checkpoint_event_evidence_required"] == 1
    assert report.dataset["source_kind"] == "benchmark"


def test_future_ingestion_and_changed_facts_cannot_enter_checkpoint():
    value = example()
    first = value.state.events[0].model_copy(
        update={"ingested_at": START + timedelta(days=1)}
    )
    delayed = value.model_copy(
        update={
            "state": value.state.model_copy(
                update={"events": (first, *value.state.events[1:])}
            )
        }
    )
    with pytest.raises(ValueError, match="facts disagree"):
        evaluate(delayed)
    facts = value.state.checkpoint.facts.model_copy(update={"event_count": 999})
    corrupted = value.model_copy(
        update={
            "state": value.state.model_copy(
                update={
                    "checkpoint": value.state.checkpoint.model_copy(
                        update={"facts": facts}
                    )
                }
            )
        }
    )
    with pytest.raises(ValueError, match="facts disagree"):
        evaluate(corrupted)
