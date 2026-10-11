"""Bounded longitudinal evidence, semantic abstention and privacy regressions."""

import hashlib
from uuid import uuid4

import pytest
from pydantic import ValidationError

from model_learner.domain.models import DatasetReference, DataSourceKind, Run
from model_learner.execution.longitudinal import (
    CheckpointSummary,
    TrajectoryInput,
    compare_task_states,
    extract_longitudinal_task_states,
)
from model_learner.representation.inputs import TaskDescription
from tests.unit.test_execution_analysis import SESSION, at, event, evidence, target

DATASET = DatasetReference(
    source_kind=DataSourceKind.SIMULATED,
    dataset_id="trajectory-unit",
    dataset_version="1",
)


def inputs():
    task, run = target()
    # Test source target is finished: a running projection never reads that state.
    run = run.model_copy(update={"ended_at": None})
    return task, run


def summary(task, run, *, second=3, **changes):
    text = "Sanitized synthetic checkpoint declaration."
    values = dict(
        summary_id=f"s-{second}",
        task_id=task.task_id,
        run_id=run.run_id,
        dataset=DATASET,
        observed_at=at(second),
        available_at=at(second),
        text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        source="sanitized",
        source_reference="synthetic-unit",
        actor_id="fixture-author",
        actor_kind="agent",
        phase="implementation",
        progress="work_reported",
    )
    values.update(changes)
    return CheckpointSummary(**values)


def project(events=(), *, task=None, run=None, checkpoints=None, **kwargs):
    if task is None:
        task, run = inputs()
    return extract_longitudinal_task_states(
        events,
        task=task,
        run=run,
        session_id=SESSION,
        dataset=DATASET,
        checkpoints=checkpoints if checkpoints is not None else (at(5), at(10)),
        association_available_at=kwargs.pop("association_available_at", at(0)),
        **kwargs,
    )


def test_more_tool_activity_is_not_semantic_progress_or_verification():
    rows = [
        event(2, "turn.started"),
        event(7, "turn.completed", usage={"output_tokens": 5}),
    ]
    before, after = project(rows)
    change = compare_task_states(before, after)
    assert change.status == "changed"
    assert change.dimensions == ("activity",)
    assert after.derived.provenance == "derived"
    assert after.observed[0].provenance == "observed"
    assert all(value.provenance == "unknown" for value in after.inferred.values())
    assert after.verified_task_success is None and after.progress_percentage is None
    assert after.execution.native_duration_seconds is None


def test_summary_claim_changes_are_inferred_with_source_not_verified_facts():
    task, run = inputs()
    reports = [
        summary(task, run),
        summary(
            task,
            run,
            second=7,
            phase="debugging",
            progress="blocked",
            difficulty="new dependency",
        ),
    ]
    before, after = project(task=task, run=run, summaries=reports)
    change = compare_task_states(before, after)
    assert change.dimensions == ("phase", "progress")
    assert "difficulty" in change.new_information
    assert after.inferred["phase"].value == "debugging"
    assert after.inferred["phase"].provenance == "inferred"
    assert after.inferred["phase"].basis_summary_ids == ("s-7",)
    assert after.verified_task_success is None


def test_text_change_alone_does_not_establish_scope_difficulty_or_progress():
    task, run = inputs()
    text = "Completely different wording about more files."
    reports = [
        summary(task, run),
        summary(
            task,
            run,
            second=7,
            text=text,
            text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        ),
    ]
    change = compare_task_states(*project(task=task, run=run, summaries=reports))
    assert change.status == "unknown"
    assert change.dimensions == ()
    assert change.new_information == ("summary",)


def test_future_summary_conflicts_and_late_receipts_cannot_change_earlier_state():
    task, run = inputs()
    early = summary(task, run)
    future = summary(
        task, run, second=8, summary_id=early.summary_id, phase="debugging"
    )
    earlier = project(task=task, run=run, summaries=[early], checkpoints=[at(5)])[0]
    full = project(task=task, run=run, summaries=[early, future], checkpoints=[at(5)])[
        0
    ]
    assert full == earlier
    with pytest.raises(ValueError, match="conflicting visible summary"):
        project(task=task, run=run, summaries=[early, future])
    delayed = summary(task, run, available_at=at(9))
    before, after = project(task=task, run=run, summaries=[delayed])
    assert before.summaries == ()
    assert after.summaries == (delayed,)
    assert compare_task_states(before, after).dimensions == ()


@pytest.mark.parametrize(
    "field,value,reason",
    [
        ("run_id", uuid4(), "foreign_task_or_run"),
        (
            "dataset",
            DATASET.model_copy(update={"source_kind": DataSourceKind.REAL}),
            "foreign_dataset",
        ),
        ("event_ids", (uuid4(),), "unavailable_or_foreign_reference"),
        ("verification_ids", (uuid4(),), "unavailable_or_foreign_reference"),
    ],
)
def test_foreign_or_unavailable_declaration_evidence_stays_unknown(
    field, value, reason
):
    task, run = inputs()
    report = summary(task, run, **{field: value})
    before, after = project(task=task, run=run, summaries=[report])
    assert not after.summaries
    assert after.excluded_summaries == {reason: 1}
    assert compare_task_states(before, after).status == "unknown"


def test_delayed_referenced_event_receipt_blocks_summary_until_available():
    task, run = inputs()
    row = event(2, "turn.started", ingested_at=at(9))
    report = summary(task, run, event_ids=(row.event_id,))
    before, after = project([row], task=task, run=run, summaries=[report])
    assert before.summaries == ()
    assert after.summaries == (report,)


def test_unknown_vs_no_observed_change_and_lost_semantic_coverage():
    assert compare_task_states(*project()).status == "unknown"
    assert (
        compare_task_states(*project([event(2, "turn.started")])).status
        == "no_observed_change"
    )
    task, run = inputs()
    reports = [
        summary(task, run),
        summary(task, run, second=7, phase=None, progress=None),
    ]
    change = compare_task_states(*project(task=task, run=run, summaries=reports))
    assert change.status == "unknown" and not change.dimensions
    assert "phase_became_unknown" in change.new_information


def test_equal_time_reports_remain_ambiguous_even_when_labels_agree():
    task, run = inputs()
    reports = [summary(task, run), summary(task, run, summary_id="independent-summary")]
    after = project(task=task, run=run, summaries=reports)[1]
    assert after.inferred["phase"].value is None
    assert set(after.inferred["phase"].basis_summary_ids) == {
        "s-3",
        "independent-summary",
    }


def test_scope_and_authorized_objective_receipts_gate_projection():
    task, run = inputs()
    text = "Authorized sanitized objective."
    description = TaskDescription(
        task_id=task.task_id,
        task_family="unit",
        text=text,
        text_sha256=hashlib.sha256(text.encode()).hexdigest(),
        source="sanitized",
        available_at=at(8),
    )
    before, after = project(
        [event(2, "turn.started")],
        task=task,
        run=run,
        summaries=[summary(task, run)],
        description=description,
        task_available_at=at(7),
    )
    assert not before.identity.scope_available and before.identity.objective is None
    assert before.observed == () and before.summaries == ()
    assert after.identity.objective == text
    assert compare_task_states(before, after).status == "unknown"


def test_raw_private_text_and_foreign_event_same_id_do_not_enter_projection():
    row = event(2, "turn.started", raw_payload={"private": "secret transcript"})
    foreign = row.model_copy(
        update={"session_id": uuid4(), "source_version": "foreign-private"}
    )
    state = project([foreign, row])[1]
    assert state.observed[0].source_version == row.source_version
    assert "secret transcript" not in state.model_dump_json()
    assert "foreign-private" not in state.model_dump_json()


def test_final_bound_tests_are_visible_only_after_artifact_and_report_receipts():
    task, run = target()
    report = evidence(task, run, 20)
    before, after = project(
        task=task,
        run=run,
        checkpoints=(at(25), at(35)),
        verifications=[report],
        artifact_available_at=at(12),
        evidence_available_at={report.verification_id: at(30)},
    )
    assert not before.execution.test_results
    assert after.execution.test_results[0].verification_id == report.verification_id
    assert compare_task_states(before, after).dimensions == ("tests",)
    assert after.verified_task_success is None


def test_invalid_digests_naive_or_reversed_receipts_and_checkpoint_order_rejected():
    task, run = inputs()
    for changes in (
        {"text_sha256": "a" * 64},
        {"available_at": at(2)},
        {"observed_at": at(3).replace(tzinfo=None)},
    ):
        with pytest.raises(ValidationError):
            summary(task, run, **changes)
    with pytest.raises(ValidationError, match="increasing checkpoints"):
        TrajectoryInput(
            dataset=DATASET,
            task=task,
            run=run,
            session_id=SESSION,
            checkpoints=(at(10), at(5)),
            association_available_at=at(0),
        )


def test_foreign_identity_and_reversed_comparison_rejected():
    before, after = project([event(2, "turn.started")])
    with pytest.raises(ValueError, match="increasing checkpoints"):
        compare_task_states(after, before)
    other = after.model_copy(
        update={
            "identity": after.identity.model_copy(
                update={"run_id": Run(task_id=after.identity.task_id).run_id}
            )
        }
    )
    with pytest.raises(ValueError, match="same dataset"):
        compare_task_states(before, other)
