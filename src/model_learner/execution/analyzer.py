"""Deterministic, observation-only analysis of the existing Codex projection."""

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from datetime import datetime
from itertools import pairwise
from uuid import UUID

from model_learner.adapters.codex import SOURCE, _supported_event
from model_learner.domain import Event, Provenance, Run, Task, Verification
from model_learner.execution.models import (
    CaseStatusChange,
    ExecutionCheckpoint,
    ExecutionFacts,
    RepeatedFailure,
    StateInference,
    TestCaseObservation,
    TestResultChange,
    TestResultObservation,
    ToolObservation,
)

_TOOLS = {"command_execution", "mcp_tool_call", "file_change", "web_search"}
_USAGE = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
_LIMITATIONS = (
    "Receipt time and ingestion availability are not native execution duration.",
    "Missing capture segments and unobserved tool outcomes remain unknown.",
    "Redacted commands/arguments cannot establish same-operation retries or loops.",
    "Completion and command exit zero do not establish tests passed or task success.",
    "Heuristic states describe available observations; they do not control an agent.",
    "Test changes compare post-run reports for one final artifact, not runtime edits.",
)


def _aware(value: datetime, name: str) -> None:
    if (
        not isinstance(value, datetime)
        or value.tzinfo is None
        or value.utcoffset() is None
    ):
        raise ValueError(f"{name} requires a timezone-aware datetime")


def _order(event: Event) -> tuple:
    capture = event.payload.get("capture_id")
    sequence = event.payload.get("sequence")
    return (
        event.observed_at,
        capture if isinstance(capture, str) else "",
        sequence if type(sequence) is int else 0,
        str(event.event_id),
    )


def _supported(event: Event) -> bool:
    return (
        event.source == SOURCE
        and event.provenance is Provenance.OBSERVED
        and _supported_event(event)
        and bool(event.payload["capture_id"])
        and event.payload["sequence"] >= 1
        and event.payload["native"].get("type") == event.event_type
    )


def _visible_events(
    events: tuple[Event, ...],
    session_id: UUID,
    checkpoint: datetime,
    run: Run | None,
    association_available_at: datetime | None,
) -> list[Event]:
    if run is not None and (
        association_available_at is None or association_available_at > checkpoint
    ):
        return []
    identities: dict[str, Event] = {}
    event_ids: dict[UUID, str] = {}
    for event in events:
        if (
            event.session_id != session_id
            or event.observed_at > checkpoint
            or event.ingested_at > checkpoint
        ):
            continue
        if run is not None:
            if event.run_id is not None and event.run_id != run.run_id:
                continue
            if (
                run.started_at is None
                or event.observed_at < run.started_at
                or (run.ended_at is not None and event.observed_at > run.ended_at)
            ):
                continue
        key = event.stable_key
        prior = identities.get(key)
        # Raw retention and a later replay receipt do not make another observation.
        if prior is not None and prior.model_dump(
            exclude={"raw_payload", "ingested_at"}
        ) != event.model_dump(exclude={"raw_payload", "ingested_at"}):
            raise ValueError("conflicting visible event identity")
        if event.event_id in event_ids and event_ids[event.event_id] != key:
            raise ValueError("conflicting visible event ID")
        identities[key] = event
        event_ids[event.event_id] = key
    return sorted(identities.values(), key=_order)


def _tools(
    events: list[Event], diagnostics: list[str]
) -> tuple[tuple[ToolObservation, ...], int]:
    histories: dict[tuple[str, str], list[Event]] = defaultdict(list)
    missing = 0
    for event in events:
        item = event.payload["native"].get("item", {})
        if (
            event.event_type not in {"item.started", "item.updated", "item.completed"}
            or item.get("type") not in _TOOLS
        ):
            continue
        if not item.get("id"):
            missing += 1
            continue
        histories[(event.payload["capture_id"], item["id"])].append(event)
    tools = []
    for (capture, item_id), history in histories.items():
        latest = history[-1]
        item = latest.payload["native"]["item"]
        types = {event.payload["native"]["item"]["type"] for event in history}
        servers = {
            event.payload["native"]["item"]["server"]
            for event in history
            if event.payload["native"]["item"].get("server")
        }
        names = {
            event.payload["native"]["item"]["tool"]
            for event in history
            if event.payload["native"]["item"].get("tool")
        }
        terminal = latest.event_type == "item.completed"
        status = item.get("status")
        exit_code = item.get("exit_code")
        failed = None
        if terminal:
            if type(exit_code) is int:
                failed = exit_code != 0
            elif status == "failed":
                failed = True
            elif status == "completed" and item["type"] != "command_execution":
                failed = False
        if (
            len(types) > 1
            or len(servers) > 1
            or len(names) > 1
            or (failed is False and status == "failed")
            or (terminal and status == "in_progress")
            or any(event.event_type == "item.completed" for event in history[:-1])
        ):
            diagnostics.append("inconsistent_tool_lifecycle")
            failed = None
        tools.append(
            ToolObservation(
                capture_id=capture,
                item_id=item_id,
                tool_type=item["type"],
                server=next(iter(servers)) if len(servers) == 1 else None,
                tool=next(iter(names)) if len(names) == 1 else None,
                event_ids=tuple(event.event_id for event in history),
                latest_event_id=latest.event_id,
                observed_status=status,
                exit_code=exit_code,
                started_observed=any(
                    event.event_type == "item.started" for event in history
                ),
                terminal_observed=terminal,
                failed=failed,
            )
        )
    return tuple(tools), missing


def _facts(events: list[Event], diagnostics: list[str]) -> ExecutionFacts:
    supported = [event for event in events if _supported(event)]
    kinds = Counter(event.event_type for event in supported)
    tools, missing = _tools(supported, diagnostics)
    failures: dict[tuple, list[ToolObservation]] = defaultdict(list)
    for tool in tools:
        if tool.failed is True:
            identity = (
                (tool.tool_type, tool.server, tool.tool)
                if tool.tool_type == "mcp_tool_call" and tool.server and tool.tool
                else (tool.tool_type, None, None)
            )
            failures[identity].append(tool)
    repeated = tuple(
        RepeatedFailure(
            tool_type=kind,
            server=server,
            tool=name,
            failed_items=len(items),
            event_ids=tuple(item.latest_event_id for item in items),
            identity_basis="named_tool" if server and name else "tool_category",
        )
        for (kind, server, name), items in sorted(
            failures.items(), key=lambda pair: tuple(value or "" for value in pair[0])
        )
        if len(items) >= 2
    )
    usage = dict.fromkeys(_USAGE)
    coverage = dict.fromkeys(_USAGE, 0)
    for event in supported:
        if event.event_type == "turn.completed":
            measured = event.payload["native"].get("usage", {})
            for field in _USAGE:
                if field in measured:
                    usage[field] = (usage[field] or 0) + measured[field]
                    coverage[field] += 1
    return ExecutionFacts(
        event_count=len(events),
        supported_event_count=len(supported),
        unsupported_event_count=len(events) - len(supported),
        event_types=dict(Counter(event.event_type for event in events)),
        event_ids=tuple(event.event_id for event in supported),
        tool_items=tools,
        tool_events_missing_identity=missing,
        completed_tool_items=sum(tool.terminal_observed for tool in tools),
        failed_tool_items=sum(tool.failed is True for tool in tools),
        tool_items_with_unknown_failure=sum(tool.failed is None for tool in tools),
        started_turns=kinds["turn.started"],
        completed_turns=kinds["turn.completed"],
        failed_turns=kinds["turn.failed"],
        repeated_failures=repeated,
        token_usage=usage,
        token_usage_coverage=coverage,
    )


def _execution_state(events: list[Event]) -> StateInference:
    relevant = [
        event
        for event in events
        if _supported(event)
        and event.event_type
        in {"turn.started", "turn.completed", "turn.failed", "item.started"}
    ]
    if not relevant:
        return StateInference(
            state="unknown",
            explanation="No supported execution-state marker is visible.",
        )
    latest = relevant[-1]
    ties = [event for event in relevant if event.observed_at == latest.observed_at]
    if len({event.payload["capture_id"] for event in ties}) > 1:
        return StateInference(
            state="unknown",
            basis_event_ids=tuple(event.event_id for event in ties),
            explanation="Equal receipt times across captures lack a shared order.",
        )
    states = {
        "turn.started": "activity_observed",
        "item.started": "activity_observed",
        "turn.completed": "completed_turn_observed",
        "turn.failed": "failed_turn_observed",
    }
    return StateInference(
        state=states[latest.event_type],
        basis_event_ids=(latest.event_id,),
        explanation="Latest supported marker; a turn state is not task verification.",
    )


def _test_changes(results: list[TestResultObservation]) -> tuple[TestResultChange, ...]:
    changes = []
    multiplicity = Counter(result.observed_at for result in results)
    for previous, current in pairwise(results):
        # UUID sorting does not establish ordering of equal-time observations.
        if (
            multiplicity[previous.observed_at] > 1
            or multiplicity[current.observed_at] > 1
        ):
            continue
        same = previous.case_statuses.keys() == current.case_statuses.keys()
        comparable = (
            same
            and not previous.completeness_reasons
            and not current.completeness_reasons
        )
        changes.append(
            TestResultChange(
                previous_verification_id=previous.verification_id,
                verification_id=current.verification_id,
                same_test_set=same,
                failure_count_delta=current.counts["failures"]
                - previous.counts["failures"]
                if comparable
                else None,
                error_count_delta=current.counts["errors"] - previous.counts["errors"]
                if comparable
                else None,
                passed_count_delta=current.counts["passed"] - previous.counts["passed"]
                if comparable
                else None,
                changed_cases=tuple(
                    CaseStatusChange(
                        test_id=test_id,
                        before=previous.case_statuses[test_id],
                        after=current.case_statuses[test_id],
                    )
                    for test_id in sorted(
                        previous.case_statuses.keys() & current.case_statuses.keys()
                    )
                    if previous.case_statuses[test_id] != current.case_statuses[test_id]
                ),
            )
        )
    return tuple(changes)


def _test_state(results: list[TestResultObservation]) -> StateInference:
    if not results:
        return StateInference(
            state="unknown", explanation="No available, valid, bound JUnit evidence."
        )
    latest_time = max(result.observed_at for result in results)
    latest = [result for result in results if result.observed_at == latest_time]
    statuses = {result.criterion_result for result in latest}
    if len(statuses) != 1 or len(latest) > 1:
        return StateInference(
            state="unknown",
            basis_verification_ids=tuple(result.verification_id for result in latest),
            explanation="Equal-time reports lack a declared revision or shared order.",
        )
    result = latest[0]
    return StateInference(
        state={
            "pass": "passing_report_observed",
            "fail": "failing_report_observed",
            "indeterminate": "indeterminate_report_observed",
        }[result.criterion_result],
        basis_verification_ids=(result.verification_id,),
        explanation="Bound named-test criterion; no outcome assessment is created.",
    )


def _test_results(
    verifications: tuple[Verification, ...],
    checkpoint: datetime,
    task: Task | None,
    run: Run | None,
    association_available_at: datetime | None,
    artifact_available_at: datetime | None,
    evidence_available_at: Mapping[UUID, datetime],
) -> tuple[list[TestResultObservation], Counter]:
    results = []
    excluded = Counter()
    visible: dict[UUID, Verification] = {}
    unavailable_ids: set[UUID] = set()
    for evidence in verifications:
        available = max(
            evidence.observed_at,
            evidence_available_at.get(evidence.verification_id, evidence.observed_at),
        )
        if available > checkpoint:
            continue
        unavailable_reason = None
        if task is None or run is None:
            unavailable_reason = "missing_explicit_target"
        elif task.created_at > checkpoint:
            unavailable_reason = "task_target_not_available"
        elif association_available_at is None or association_available_at > checkpoint:
            unavailable_reason = "run_session_association_not_available"
        elif artifact_available_at is None or artifact_available_at > checkpoint:
            unavailable_reason = "artifact_binding_not_available"
        if unavailable_reason is not None:
            if evidence.verification_id not in unavailable_ids:
                excluded[unavailable_reason] += 1
                unavailable_ids.add(evidence.verification_id)
            continue
        if evidence.verification_id in visible:
            if visible[evidence.verification_id] != evidence:
                raise ValueError("conflicting visible verification identity")
            continue
        visible[evidence.verification_id] = evidence
        if evidence.verifier_type != "junit-xml" or evidence.verifier_version != "1":
            excluded["unsupported_verifier"] += 1
            continue
        # Imported lazily so session-only analysis has no verifier coupling.
        from model_learner.verification.junit import (
            JUnitReportBinding,
            validate_junit_evidence,
        )

        try:
            summary = validate_junit_evidence(run, task, evidence)
        except ValueError:
            excluded["invalid_or_foreign_test_evidence"] += 1
            continue
        identity_counts = Counter(case.test_id for case in summary.cases)
        binding = JUnitReportBinding.model_validate(evidence.metadata["binding"])
        results.append(
            TestResultObservation(
                verification_id=evidence.verification_id,
                observed_at=evidence.observed_at,
                available_at=available,
                availability_basis="caller_receipt"
                if evidence.verification_id in evidence_available_at
                else "declared_observed_at",
                artifact_fingerprint=evidence.artifact_fingerprint,
                report_sha256=evidence.metadata.get("report_observed_sha256"),
                counts=summary.counts.model_dump(),
                cases=tuple(
                    TestCaseObservation(test_id=case.test_id, status=case.status)
                    for case in summary.cases
                ),
                case_statuses={
                    case.test_id: case.status
                    for case in summary.cases
                    if identity_counts[case.test_id] == 1
                },
                ambiguous_test_ids=tuple(
                    sorted(
                        identity
                        for identity, count in identity_counts.items()
                        if count > 1
                    )
                ),
                execution_completed=binding.execution_completed,
                completeness_reasons=tuple(evidence.metadata["completeness_reasons"]),
                criterion_result=evidence.result.value,
            )
        )
    return sorted(
        results, key=lambda result: (result.observed_at, str(result.verification_id))
    ), excluded


def extract_execution_checkpoints(
    events: Iterable[Event],
    *,
    session_id: UUID,
    checkpoints: Iterable[datetime],
    task: Task | None = None,
    run: Run | None = None,
    association_available_at: datetime | None = None,
    artifact_available_at: datetime | None = None,
    verifications: Iterable[Verification] = (),
    evidence_available_at: Mapping[UUID, datetime] | None = None,
) -> tuple[ExecutionCheckpoint, ...]:
    """Project visible facts at inclusive cutoffs without controlling execution.

    Session-only mode needs just observed Events. Run/evidence mode additionally
    requires canonical Task/Run records and explicit association/artifact
    availability receipts; final run state is never used. Event visibility uses
    both observation and ingestion timestamps. Verification has no ingestion
    receipt in the ledger; a caller can supply one, otherwise its trusted declared
    ``observed_at`` is used and that limitation is reported.

    Checkpoints are returned in caller order. Duplicates never add observations;
    conflicting *visible* identities fail closed. Future rows cannot change an
    earlier projection, including through a future duplicate/conflict.
    """
    times = tuple(checkpoints)
    for time in times:
        _aware(time, "checkpoint")
    if (task is None) != (run is None):
        raise ValueError("run-mode analysis requires both task and run")
    if run is not None and run.task_id != task.task_id:
        raise ValueError("run does not belong to the supplied task")
    for name, value in (
        ("association_available_at", association_available_at),
        ("artifact_available_at", artifact_available_at),
    ):
        if value is not None:
            _aware(value, name)
    receipts = evidence_available_at or {}
    for value in receipts.values():
        _aware(value, "evidence_available_at")
    all_events, all_evidence = tuple(events), tuple(verifications)
    effective_association = association_available_at
    if task is not None and effective_association is not None:
        effective_association = max(task.created_at, effective_association)
    snapshots = []
    for time in times:
        selected = _visible_events(
            all_events, session_id, time, run, effective_association
        )
        diagnostics = []
        facts = _facts(selected, diagnostics)
        results, excluded = _test_results(
            all_evidence,
            time,
            task,
            run,
            effective_association,
            artifact_available_at,
            receipts,
        )
        signals = tuple(
            StateInference(
                state="repeated_tool_failures",
                basis_event_ids=failure.event_ids,
                explanation=(
                    "Distinct tool items failed in the named tool/category; "
                    "shared command/arguments, retries, and a failure loop are unknown."
                ),
            )
            for failure in facts.repeated_failures
        )
        limits = list(_LIMITATIONS)
        if run is not None:
            limits.append(
                "Run bounds and scope/artifact availability are explicit declarations."
            )
            if task.created_at > time:
                diagnostics.append("task_target_not_available")
            if effective_association is None or effective_association > time:
                diagnostics.append("run_session_association_not_available")
        if any(result.verification_id not in receipts for result in results):
            limits.append(
                "Verification ingestion time is absent; observed_at is availability."
            )
        snapshots.append(
            ExecutionCheckpoint(
                checkpoint=time,
                session_id=session_id,
                run_id=run.run_id if run is not None else None,
                task_id=task.task_id if task is not None else None,
                facts=facts,
                execution_state=_execution_state(selected),
                signals=signals,
                test_results=tuple(results),
                test_changes=_test_changes(results),
                test_state=_test_state(results),
                excluded_evidence=dict(excluded),
                diagnostics=tuple(sorted(set(diagnostics))),
                limitations=tuple(limits),
            )
        )
    return tuple(snapshots)
