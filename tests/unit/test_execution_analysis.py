"""Observable features, historical availability and honest missingness."""

from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

import pytest

from model_learner.domain import (
    AcceptanceSpec,
    Event,
    Provenance,
    Run,
    RunState,
    Task,
    Verification,
    VerificationResult,
)
from model_learner.execution import extract_execution_checkpoints
from model_learner.verification.junit import (
    JUnitReportBinding,
    junit_criterion,
    parse_junit_xml,
)

NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)
SESSION = UUID("00000000-0000-0000-0000-000000000001")
SPEC = AcceptanceSpec(identifier="controlled-tests", version="1")
FINGERPRINT = "sha256:" + "a" * 64
LATEST = NOW + timedelta(seconds=100)


def at(seconds: int) -> datetime:
    return NOW + timedelta(seconds=seconds)


def event(
    sequence: int,
    kind: str,
    *,
    item: dict | None = None,
    usage: dict | None = None,
    **updates,
) -> Event:
    native = {"type": kind}
    if item is not None:
        native["item"] = item
    if usage is not None:
        native["usage"] = usage
    fields = {
        "session_id": SESSION,
        "observed_at": at(sequence),
        "ingested_at": at(sequence),
        "source": "codex.exec",
        "source_version": "controlled-fixture-v1",
        "machine_id": "controlled-machine",
        "capture_method": "stdout_capture_import",
        "native_session_id": "controlled-thread",
        "event_type": kind,
        "adapter_version": "1",
        "provenance": Provenance.OBSERVED,
        "payload": {
            "native": native,
            "capture_id": "controlled-capture",
            "sequence": sequence,
            "timestamp_basis": "capture_receipt",
        },
    }
    fields.update(updates)
    return Event(**fields)


def snapshot(events, checkpoint=LATEST, **kwargs):
    return extract_execution_checkpoints(
        events, session_id=SESSION, checkpoints=[checkpoint], **kwargs
    )[0]


def target():
    task = Task(
        description="Controlled named checks",
        acceptance_spec=SPEC,
        created_at=NOW,
        metadata={"junit_verifier": junit_criterion(required_test_ids=["demo::one"])},
    )
    run = Run(
        task_id=task.task_id,
        started_at=NOW,
        ended_at=at(10),
        state=RunState.FINISHED,
        metadata={"final_artifact_fingerprint": FINGERPRINT},
    )
    return task, run


def evidence(task, run, second, status="passed", *, extra=False, incomplete=False):
    markup = "" if status == "passed" else f"<{status}/>"
    extra_markup = '<testcase classname="demo" name="two"/>' if extra else ""
    summary = parse_junit_xml(
        (
            f'<testsuite tests="{2 if extra else 1}" '
            f'failures="{int(status == "failure")}" '
            f'errors="{int(status == "error")}" skipped="0">'
            f'<testcase classname="demo" name="one">{markup}</testcase>'
            f"{extra_markup}</testsuite>"
        ).encode()
    )
    binding = JUnitReportBinding(
        task_id=task.task_id,
        run_id=run.run_id,
        acceptance_spec=SPEC,
        artifact_fingerprint=FINGERPRINT,
        report_sha256="b" * 64,
        report_generated_at=at(second),
        source="pytest-junit",
        execution_completed=not incomplete,
        command_exit_code=0 if status == "passed" else 1,
    )
    reasons = ["test_execution_not_confirmed_complete"] if incomplete else []
    return Verification(
        task_id=task.task_id,
        run_id=run.run_id,
        acceptance_spec=SPEC,
        observed_at=at(second),
        verifier_type="junit-xml",
        verifier_version="1",
        result=VerificationResult.INDETERMINATE
        if incomplete
        else VerificationResult.PASS
        if status == "passed"
        else VerificationResult.FAIL,
        artifact_fingerprint=FINGERPRINT,
        metadata={
            "criterion": task.metadata["junit_verifier"],
            "binding": binding.model_dump(mode="json"),
            "test_results": summary.model_dump(mode="json"),
            "report_observed_sha256": "b" * 64,
            "completeness_reasons": reasons,
        },
    )


def run_snapshot(events, task, run, reports=(), checkpoint=LATEST, **kwargs):
    arguments = {
        "task": task,
        "run": run,
        "association_available_at": NOW,
        "artifact_available_at": at(10),
        "verifications": reports,
    }
    arguments.update(kwargs)
    return snapshot(events, checkpoint, **arguments)


def test_empty_checkpoints_preserve_unknowns_and_caller_order():
    results = extract_execution_checkpoints(
        [], session_id=SESSION, checkpoints=[at(3), at(1)]
    )
    assert [result.checkpoint for result in results] == [at(3), at(1)]
    assert results[0].facts.event_count == 0
    assert results[0].execution_state.state == "unknown"
    assert results[0].test_state.state == "unknown"
    assert results[0].verified_task_success is None
    assert results[0].native_duration_seconds is None
    assert results[0].cost_usd is None
    assert all(value is None for value in results[0].facts.token_usage.values())


def test_checkpoints_require_timezone_and_target_identity():
    with pytest.raises(ValueError, match="timezone"):
        snapshot([], datetime(2026, 10, 10))
    task, run = target()
    with pytest.raises(ValueError, match="both task and run"):
        snapshot([], run=run)
    with pytest.raises(ValueError, match="supplied task"):
        snapshot([], run=run.model_copy(update={"task_id": uuid4()}), task=task)


def test_checkpoint_filters_observation_and_ingestion_and_other_sessions():
    first = event(1, "turn.started")
    late = event(2, "turn.failed", ingested_at=at(9))
    foreign = event(3, "turn.completed", session_id=uuid4())
    before, after = extract_execution_checkpoints(
        [first, late, foreign], session_id=SESSION, checkpoints=[at(3), at(9)]
    )
    assert before.facts.event_count == 1
    assert before.execution_state.state == "activity_observed"
    assert after.facts.failed_turns == 1
    assert after.execution_state.state == "failed_turn_observed"


def test_future_event_conflicts_cannot_change_prior_checkpoint():
    first = event(1, "turn.started")
    future = first.model_copy(
        update={"event_type": "turn.failed", "ingested_at": at(9)}
    )
    assert snapshot([first, future], at(3)) == snapshot([first], at(3))
    with pytest.raises(ValueError, match="conflicting visible"):
        snapshot([first, future], at(10))


def test_duplicate_replay_does_not_add_events_or_failures():
    failed = event(
        1,
        "item.completed",
        item={"id": "one", "type": "command_execution", "exit_code": 1},
    )
    result = snapshot([failed, failed, failed])
    assert result.facts.event_count == 1
    assert result.facts.failed_tool_items == 1
    assert not result.signals


def test_unsupported_payloads_have_guarded_order_and_no_inferred_state():
    rows = [
        event(1, "custom", payload={"capture_id": [], "sequence": "private"}),
        event(1, "custom", payload={"capture_id": None, "sequence": []}),
        event(1, "turn.completed", source="manual"),
        event(1, "turn.failed", provenance=Provenance.INFERRED),
    ]
    result = snapshot(rows)
    assert result.facts.event_count == 4
    assert result.facts.supported_event_count == 0
    assert result.facts.unsupported_event_count == 4
    assert result.execution_state.state == "unknown"


def test_native_type_disagreement_is_unsupported():
    row = event(1, "turn.completed")
    row = row.model_copy(update={"event_type": "turn.failed"})
    result = snapshot([row])
    assert result.facts.unsupported_event_count == 1
    assert result.facts.failed_turns == 0


def test_command_completion_and_agent_message_are_not_verified_tests():
    rows = [
        event(
            1,
            "item.completed",
            item={"id": "command", "type": "command_execution", "exit_code": 0},
        ),
        event(2, "item.completed", item={"id": "message", "type": "agent_message"}),
        event(3, "turn.completed"),
    ]
    result = snapshot(rows)
    assert result.facts.completed_tool_items == 1
    assert result.facts.failed_tool_items == 0
    assert result.execution_state.state == "completed_turn_observed"
    assert result.test_state.state == "unknown"
    assert result.verified_task_success is None


def test_missing_command_exit_and_item_identity_are_honest_unknowns():
    result = snapshot(
        [
            event(
                1,
                "item.completed",
                item={"id": "one", "type": "command_execution", "status": "completed"},
            ),
            event(
                2, "item.completed", item={"type": "command_execution", "exit_code": 1}
            ),
        ]
    )
    assert result.facts.tool_items_with_unknown_failure == 1
    assert result.facts.tool_events_missing_identity == 1
    assert result.facts.failed_tool_items == 0


def test_started_tool_at_earlier_checkpoint_does_not_see_final_failure():
    rows = [
        event(
            1,
            "item.started",
            item={"id": "one", "type": "command_execution", "status": "in_progress"},
        ),
        event(
            3,
            "item.completed",
            item={
                "id": "one",
                "type": "command_execution",
                "status": "failed",
                "exit_code": 2,
            },
        ),
    ]
    before, after = extract_execution_checkpoints(
        rows, session_id=SESSION, checkpoints=[at(1), at(3)]
    )
    assert before.facts.tool_items[0].failed is None
    assert not before.facts.tool_items[0].terminal_observed
    assert after.facts.tool_items[0].failed is True
    assert after.facts.tool_items[0].started_observed


def test_repeated_failures_preserve_tool_identity_without_claiming_command_retry():
    rows = [
        event(
            i,
            "item.completed",
            item={"id": str(i), "type": "command_execution", "exit_code": 1},
        )
        for i in (1, 2)
    ] + [
        event(
            i,
            "item.completed",
            item={
                "id": str(i),
                "type": "mcp_tool_call",
                "server": "demo",
                "tool": "lookup",
                "status": "failed",
            },
        )
        for i in (3, 4)
    ]
    result = snapshot(rows)
    assert result.facts.failed_tool_items == 4
    assert [failure.identity_basis for failure in result.facts.repeated_failures] == [
        "tool_category",
        "named_tool",
    ]
    assert all(
        failure.same_operation_retry is None
        for failure in result.facts.repeated_failures
    )
    assert all(signal.provenance == "inferred" for signal in result.signals)
    assert result.facts.provenance == "observed"


def test_named_and_anonymous_mcp_failures_can_be_sorted_and_stay_separate():
    rows = []
    for i in range(1, 5):
        item = {"id": str(i), "type": "mcp_tool_call", "status": "failed"}
        if i > 2:
            item.update(server="demo", tool="lookup")
        rows.append(event(i, "item.completed", item=item))
    result = snapshot(rows)
    assert len(result.facts.repeated_failures) == 2
    assert all(failure.failed_items == 2 for failure in result.facts.repeated_failures)


def test_item_identity_is_scoped_to_capture():
    first = event(
        1,
        "item.completed",
        item={"id": "one", "type": "command_execution", "exit_code": 1},
    )
    other = event(
        2,
        "item.completed",
        item={"id": "one", "type": "command_execution", "exit_code": 1},
    )
    other = other.model_copy(
        update={"payload": {**other.payload, "capture_id": "other"}}
    )
    assert snapshot([first, other]).facts.failed_tool_items == 2


def test_known_mcp_identity_survives_omitted_completion_fields():
    started = event(
        1,
        "item.started",
        item={"id": "one", "type": "mcp_tool_call", "server": "demo", "tool": "lookup"},
    )
    completed = event(
        2,
        "item.completed",
        item={"id": "one", "type": "mcp_tool_call", "status": "failed"},
    )
    result = snapshot([started, completed])
    assert result.facts.tool_items[0].server == "demo"
    assert result.facts.tool_items[0].tool == "lookup"
    assert result.facts.tool_items[0].failed is True
    assert not result.diagnostics


def test_conflicting_lifecycle_fails_closed_with_diagnostic():
    rows = [
        event(
            1,
            "item.completed",
            item={
                "id": "one",
                "type": "command_execution",
                "status": "failed",
                "exit_code": 0,
            },
        )
    ]
    result = snapshot(rows)
    assert result.facts.tool_items[0].failed is None
    assert result.diagnostics == ("inconsistent_tool_lifecycle",)


def test_equal_time_capture_order_is_not_invented():
    started = event(1, "turn.started")
    finished = event(2, "turn.completed", observed_at=at(1), ingested_at=at(1))
    finished = finished.model_copy(
        update={"payload": {**finished.payload, "capture_id": "other"}}
    )
    result = snapshot([started, finished])
    assert result.execution_state.state == "unknown"
    assert len(result.execution_state.basis_event_ids) == 2


def test_usage_counts_known_zero_and_preserves_missing_field_coverage():
    result = snapshot(
        [
            event(1, "turn.completed", usage={"input_tokens": 0}),
            event(2, "turn.completed", usage={"input_tokens": 3, "output_tokens": 1}),
        ]
    )
    assert result.facts.token_usage["input_tokens"] == 3
    assert result.facts.token_usage["output_tokens"] == 1
    assert result.facts.token_usage["cached_input_tokens"] is None
    assert result.facts.token_usage_coverage["input_tokens"] == 2
    assert result.facts.token_usage_coverage["output_tokens"] == 1


def test_run_scope_requires_available_explicit_association_and_bounded_events():
    task, run = target()
    rows = [
        event(1, "turn.started"),
        event(11, "turn.completed"),
        event(2, "turn.failed", run_id=uuid4()),
    ]
    before = run_snapshot(
        rows, task, run, checkpoint=at(3), association_available_at=at(5)
    )
    assert before.facts.event_count == 0
    assert "run_session_association_not_available" in before.diagnostics
    after = run_snapshot(rows, task, run)
    assert after.facts.event_count == 1
    # A final FINISHED declaration does not rewrite the captured earlier turn.
    assert after.execution_state.state == "activity_observed"


def test_report_visibility_checks_evidence_and_artifact_and_association_receipts():
    task, run = target()
    report = evidence(task, run, 20)
    assert run_snapshot([], task, run, [report], at(19)).test_state.state == "unknown"
    assert (
        run_snapshot(
            [], task, run, [report], at(21), artifact_available_at=at(30)
        ).test_state.state
        == "unknown"
    )
    unavailable = run_snapshot(
        [], task, run, [report], at(21), association_available_at=at(30)
    )
    assert unavailable.test_results == ()
    assert unavailable.excluded_evidence["run_session_association_not_available"] == 1
    assert (
        run_snapshot(
            [],
            task,
            run,
            [report],
            at(21),
            evidence_available_at={report.verification_id: at(30)},
        ).test_results
        == ()
    )
    available = run_snapshot(
        [],
        task,
        run,
        [report],
        at(30),
        evidence_available_at={report.verification_id: at(30)},
    )
    assert available.test_state.state == "passing_report_observed"
    assert available.test_results[0].available_at == at(30)
    assert available.verified_task_success is None


def test_observed_test_results_change_without_agent_self_reports():
    task, run = target()
    failed = evidence(task, run, 20, "failure")
    passed = evidence(task, run, 30)
    before = run_snapshot([], task, run, [failed, passed], at(25))
    after = run_snapshot([], task, run, [failed, passed], at(35))
    assert before.test_state.state == "failing_report_observed"
    assert not before.test_changes
    assert after.test_state.state == "passing_report_observed"
    assert after.test_changes[0].failure_count_delta == -1
    assert after.test_changes[0].passed_count_delta == 1
    assert after.test_changes[0].changed_cases[0].before == "failure"
    assert after.test_changes[0].changed_cases[0].after == "passed"
    assert after.test_results[0].criterion_result_provenance == "inferred"
    assert any(
        "Verification ingestion time is absent" in limit for limit in after.limitations
    )


def test_changing_test_sets_do_not_imply_fewer_failures():
    task, run = target()
    result = run_snapshot(
        [],
        task,
        run,
        [evidence(task, run, 20, "failure"), evidence(task, run, 30, extra=True)],
    )
    assert not result.test_changes[0].same_test_set
    assert result.test_changes[0].failure_count_delta is None
    assert result.test_changes[0].changed_cases[0].after == "passed"


def test_incomplete_evidence_keeps_counts_but_never_becomes_passing():
    task, run = target()
    incomplete = evidence(task, run, 20, incomplete=True)
    result = run_snapshot([], task, run, [incomplete, evidence(task, run, 30)])
    earlier = run_snapshot([], task, run, [incomplete], at(25))
    assert earlier.test_state.state == "indeterminate_report_observed"
    assert earlier.test_results[0].counts["passed"] == 1
    assert earlier.test_results[0].completeness_reasons
    assert result.test_changes[0].failure_count_delta is None


@pytest.mark.parametrize(
    "corruption", ["task", "run", "artifact", "spec", "result", "counts", "provenance"]
)
def test_foreign_stale_and_fabricated_report_metadata_is_excluded(corruption):
    task, run = target()
    report = evidence(task, run, 20)
    updates = {
        "task": {"task_id": uuid4()},
        "run": {"run_id": uuid4()},
        "artifact": {"artifact_fingerprint": "sha256:" + "c" * 64},
        "spec": {
            "acceptance_spec": AcceptanceSpec(
                identifier=SPEC.identifier, version="stale"
            )
        },
        "result": {"result": VerificationResult.FAIL},
        "provenance": {"provenance": Provenance.INFERRED},
    }
    if corruption == "counts":
        metadata = {
            **report.metadata,
            "test_results": {
                **report.metadata["test_results"],
                "counts": {
                    "tests": 9,
                    "passed": 9,
                    "failures": 0,
                    "errors": 0,
                    "skipped": 0,
                },
            },
        }
        report = report.model_copy(update={"metadata": metadata})
    else:
        report = report.model_copy(update=updates[corruption])
    result = run_snapshot([], task, run, [report])
    assert not result.test_results
    assert result.test_state.state == "unknown"
    assert result.excluded_evidence["invalid_or_foreign_test_evidence"] == 1


def test_tied_report_groups_do_not_generate_arbitrary_changes():
    task, run = target()
    reports = [
        evidence(task, run, 20, "failure"),
        evidence(task, run, 30),
        evidence(task, run, 30, "failure"),
        evidence(task, run, 40),
    ]
    middle = run_snapshot([], task, run, reports, at(35))
    final = run_snapshot([], task, run, reports)
    assert middle.test_state.state == "unknown"
    assert not middle.test_changes
    assert not final.test_changes


def test_verification_dedup_and_future_conflict_are_checkpoint_local():
    task, run = target()
    report = evidence(task, run, 20)
    future = report.model_copy(
        update={"observed_at": at(50), "result": VerificationResult.FAIL}
    )
    result = run_snapshot([], task, run, [report, report, future], at(30))
    assert len(result.test_results) == 1
    with pytest.raises(ValueError, match="conflicting visible verification"):
        run_snapshot([], task, run, [report, future])


def test_evidence_without_explicit_task_context_is_never_verified():
    task, run = target()
    result = snapshot([], verifications=[evidence(task, run, 20)])
    assert result.test_state.state == "unknown"
    assert result.excluded_evidence == {"missing_explicit_target": 1}


def test_future_task_scope_does_not_leak_evidence_or_invalidate_prior_checkpoint():
    task, run = target()
    report = evidence(task, run, 20)
    conflict = report.model_copy(update={"result": VerificationResult.FAIL})
    task = task.model_copy(update={"created_at": at(50)})
    row = event(1, "turn.started")
    earlier = run_snapshot([row], task, run, [report, conflict], at(25))
    assert earlier.facts.event_count == 0
    assert earlier.test_results == ()
    assert earlier.test_state.state == "unknown"
    assert "task_target_not_available" in earlier.diagnostics
    assert earlier.excluded_evidence == {"task_target_not_available": 1}


def test_missing_report_zero_case_entries_do_not_mean_zero_executed_tests():
    task, run = target()
    missing = evidence(task, run, 20)
    missing = missing.model_copy(
        update={
            "result": VerificationResult.INDETERMINATE,
            "metadata": {
                **missing.metadata,
                "report_observed_sha256": None,
                "test_results": {
                    "version": "junit-results/v1",
                    "counts": {
                        "tests": 0,
                        "passed": 0,
                        "failures": 0,
                        "errors": 0,
                        "skipped": 0,
                    },
                    "cases": [],
                    "diagnostics": ["report_missing"],
                },
                "completeness_reasons": [
                    "no_test_cases",
                    "report_missing",
                    "required_tests_missing",
                ],
            },
        }
    )
    result = run_snapshot([], task, run, [missing], at(25))
    assert result.test_state.state == "indeterminate_report_observed"
    assert result.test_results[0].counts["tests"] == 0
    assert result.test_results[0].counts_basis == "retained_report_case_entries"
    assert result.test_results[0].report_sha256 is None
    later = run_snapshot([], task, run, [missing, evidence(task, run, 30)])
    assert later.test_changes[0].failure_count_delta is None


def test_duplicate_case_identities_are_preserved_but_not_arbitrarily_compared():
    task, run = target()
    duplicate = evidence(task, run, 20, "failure")
    summary = parse_junit_xml(
        b'<testsuite tests="2" failures="1" errors="0" skipped="0">'
        b'<testcase classname="demo" name="one"><failure/></testcase>'
        b'<testcase classname="demo" name="one"/></testsuite>'
    )
    duplicate = duplicate.model_copy(
        update={
            "result": VerificationResult.INDETERMINATE,
            "metadata": {
                **duplicate.metadata,
                "test_results": summary.model_dump(mode="json"),
                "completeness_reasons": ["duplicate_test_identity"],
            },
        }
    )
    result = run_snapshot([], task, run, [duplicate, evidence(task, run, 30)])
    observed = result.test_results[0]
    assert observed.counts["tests"] == 2
    assert len(observed.cases) == 2
    assert observed.case_statuses == {}
    assert observed.ambiguous_test_ids == ("demo::one",)
    assert not result.test_changes[0].changed_cases


def test_missing_optional_completion_flag_preserves_unknown_not_key_error():
    task, run = target()
    incomplete = evidence(task, run, 20, incomplete=True)
    binding = {**incomplete.metadata["binding"]}
    del binding["execution_completed"]
    incomplete = incomplete.model_copy(
        update={"metadata": {**incomplete.metadata, "binding": binding}}
    )
    result = run_snapshot([], task, run, [incomplete])
    assert result.test_state.state == "indeterminate_report_observed"
    assert result.test_results[0].execution_completed is None
