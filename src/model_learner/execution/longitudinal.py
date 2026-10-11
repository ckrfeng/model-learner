"""Evidence-bounded task trajectories; declarations are not verified progress."""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from datetime import datetime
from itertools import pairwise
from typing import Literal
from uuid import UUID

from pydantic import Field, model_validator

from model_learner.domain.models import DatasetReference, Event, Run, Task, Verification
from model_learner.execution.analyzer import extract_execution_checkpoints
from model_learner.execution.models import ExecutionCheckpoint, Projection
from model_learner.learn.estimator import require_aware
from model_learner.representation.inputs import TaskDescription


class CheckpointSummary(Projection):
    """Explicit opt-in sanitized report, with self-attested source/actor identity.

    Structured fields are the author's hypotheses, not facts inferred from text.
    A digest binds the submitted text; it does not prove sanitation or authorship.
    """

    version: Literal["checkpoint-summary/v1"] = "checkpoint-summary/v1"
    summary_id: str = Field(min_length=1, max_length=128)
    task_id: UUID
    run_id: UUID
    dataset: DatasetReference
    observed_at: datetime
    available_at: datetime
    text: str = Field(min_length=1, max_length=4096)
    text_sha256: str = Field(pattern="^[0-9a-f]{64}$")
    source: Literal["public", "sanitized"]
    source_reference: str = Field(min_length=1, max_length=256)
    actor_id: str = Field(min_length=1, max_length=128)
    actor_kind: Literal["human", "agent", "operator"]
    event_ids: tuple[UUID, ...] = ()
    verification_ids: tuple[UUID, ...] = ()
    phase: Literal["planning", "implementation", "debugging", "verification"] | None = (
        None
    )
    progress: Literal["work_reported", "blocked", "completion_reported"] | None = None
    scope: str | None = Field(default=None, min_length=1, max_length=256)
    difficulty: str | None = Field(default=None, min_length=1, max_length=256)

    @model_validator(mode="after")
    def validate_receipt(self) -> CheckpointSummary:
        for name in ("observed_at", "available_at"):
            require_aware(getattr(self, name), name)
        if self.available_at < self.observed_at:
            raise ValueError("summary availability must not precede observation")
        if hashlib.sha256(self.text.encode()).hexdigest() != self.text_sha256:
            raise ValueError("summary text does not match its SHA-256 receipt")
        if any(
            value is not None and not value.strip()
            for value in (
                self.summary_id,
                self.text,
                self.source_reference,
                self.actor_id,
                self.scope,
                self.difficulty,
            )
        ):
            raise ValueError("summary declarations must be nonblank")
        return self


class TaskIdentity(Projection):
    task_id: UUID
    run_id: UUID
    session_id: UUID
    objective: str | None
    objective_sha256: str | None
    objective_source: str | None
    objective_available_at: datetime | None
    scope_available: bool
    provenance: Literal["observed_declaration"] = "observed_declaration"


class StateValue(Projection):
    value: str | None = None
    provenance: Literal["inferred", "unknown"] = "unknown"
    basis_summary_ids: tuple[str, ...] = ()
    explanation: str = "No unambiguous available declaration supports this dimension."


class ObservedEvent(Projection):
    event_id: UUID
    event_type: str
    observed_at: datetime
    available_at: datetime
    source: str
    source_version: str
    capture_id: str
    sequence: int
    timestamp_basis: Literal["capture_receipt"] = "capture_receipt"
    provenance: Literal["observed"] = "observed"


class DerivedState(Projection):
    counts: dict[str, int]
    token_usage: dict[str, int | None]
    token_usage_coverage: dict[str, int]
    repeated_failure_groups: int
    provenance: Literal["derived"] = "derived"
    rule_version: str = "longitudinal-task-state/v1"


class TaskStateCheckpoint(Projection):
    version: Literal["longitudinal-task-state/v1"] = "longitudinal-task-state/v1"
    dataset: DatasetReference
    checkpoint: datetime
    identity: TaskIdentity
    observed: tuple[ObservedEvent, ...]
    summaries: tuple[CheckpointSummary, ...]
    execution: ExecutionCheckpoint
    derived: DerivedState
    inferred: dict[str, StateValue]
    excluded_summaries: dict[str, int]
    unknown: tuple[str, ...]
    limitations: tuple[str, ...]
    verified_task_success: None = None
    progress_percentage: None = None


class TaskStateChange(Projection):
    previous_checkpoint: datetime
    checkpoint: datetime
    status: Literal["changed", "no_observed_change", "unknown"]
    dimensions: tuple[str, ...]
    new_information: tuple[str, ...]
    metric_deltas: dict[str, int]
    explanation: str
    provenance: Literal["derived"] = "derived"
    rule_version: str = "longitudinal-task-state/v1"


class TrajectoryInput(Projection):
    """Explicit local projection inputs, not a new ledger record or collector."""

    version: Literal["task-trajectory-input/v1"] = "task-trajectory-input/v1"
    dataset: DatasetReference
    task: Task
    run: Run
    session_id: UUID
    checkpoints: tuple[datetime, ...]
    association_available_at: datetime | None
    task_available_at: datetime | None = None
    description: TaskDescription | None = None
    events: tuple[Event, ...] = ()
    summaries: tuple[CheckpointSummary, ...] = ()
    verifications: tuple[Verification, ...] = ()
    artifact_available_at: datetime | None = None
    evidence_available_at: dict[UUID, datetime] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_checkpoints(self) -> TrajectoryInput:
        for value in self.checkpoints:
            require_aware(value, "checkpoint")
        if len(self.checkpoints) < 2 or any(
            right <= left for left, right in pairwise(self.checkpoints)
        ):
            raise ValueError("trajectory requires at least two increasing checkpoints")
        return self

    def project(self) -> tuple[TaskStateCheckpoint, ...]:
        return extract_longitudinal_task_states(
            self.events,
            session_id=self.session_id,
            checkpoints=self.checkpoints,
            task=self.task,
            run=self.run,
            association_available_at=self.association_available_at,
            task_available_at=self.task_available_at,
            dataset=self.dataset,
            description=self.description,
            summaries=self.summaries,
            verifications=self.verifications,
            artifact_available_at=self.artifact_available_at,
            evidence_available_at=self.evidence_available_at,
        )


_DIMENSIONS = ("phase", "progress", "scope", "difficulty")
_LIMITS = (
    "Objective and summaries are explicit authorized declarations; "
    "actor/privacy claims are self-attested.",
    "Summary fields describe hypotheses; text is not automatically interpreted.",
    "Receipt timestamps and receipt spans are not native execution times or duration.",
    "Activity, tool success, reported progress and completed turns "
    "do not verify completion.",
    "Repeated category failures do not identify identical approaches, "
    "retry causes or stalls.",
    "Current bound JUnit evidence concerns one final artifact, "
    "not intermediate code progression.",
    "No observed change does not establish unchanged latent task state.",
)


def extract_longitudinal_task_states(
    events: Iterable[Event],
    *,
    session_id: UUID,
    checkpoints: Iterable[datetime],
    task: Task,
    run: Run,
    association_available_at: datetime | None,
    dataset: DatasetReference,
    description: TaskDescription | None = None,
    summaries: Iterable[CheckpointSummary] = (),
    verifications: Iterable[Verification] = (),
    artifact_available_at: datetime | None = None,
    evidence_available_at: Mapping[UUID, datetime] | None = None,
    task_available_at: datetime | None = None,
) -> tuple[TaskStateCheckpoint, ...]:
    """Rebuild each prefix using current extraction, without reading raw payloads.

    Task creation/association/description availability are trusted declarations.
    Optional task_available_at supplies a stronger external declaration receipt.
    Final assessments and run state never enter this projection. Explicit future
    rows are filtered before duplicate conflicts and reference checks.
    """
    events, summaries = tuple(events), tuple(summaries)
    if task_available_at is not None:
        require_aware(task_available_at, "task_available_at")
    scope_at = association_available_at
    if scope_at is not None:
        require_aware(scope_at, "association_available_at")
        scope_at = max(scope_at, task.created_at, task_available_at or task.created_at)
    if description is not None and description.task_id != task.task_id:
        raise ValueError("description belongs to a different task")
    points = extract_execution_checkpoints(
        events,
        session_id=session_id,
        checkpoints=checkpoints,
        task=task,
        run=run,
        association_available_at=scope_at,
        verifications=verifications,
        artifact_available_at=artifact_available_at,
        evidence_available_at=evidence_available_at,
    )
    result = []
    for point in points:
        scope_available = scope_at is not None and scope_at <= point.checkpoint
        objective = (
            description
            if (
                description is not None
                and scope_available
                and description.available_at <= point.checkpoint
            )
            else None
        )
        event_ids = set(point.facts.event_ids)
        verification_ids = {row.verification_id for row in point.test_results}
        visible = {}
        excluded: dict[str, int] = {}
        for summary in summaries:
            if max(summary.observed_at, summary.available_at) > point.checkpoint:
                continue
            reason = None
            if summary.task_id != task.task_id or summary.run_id != run.run_id:
                reason = "foreign_task_or_run"
            elif summary.dataset != dataset:
                reason = "foreign_dataset"
            elif not scope_available:
                reason = "scope_unavailable"
            elif (
                run.started_at is None
                or summary.observed_at < run.started_at
                or (run.ended_at is not None and summary.observed_at > run.ended_at)
            ):
                reason = "outside_run_bounds"
            elif (
                not set(summary.event_ids) <= event_ids
                or not set(summary.verification_ids) <= verification_ids
            ):
                reason = "unavailable_or_foreign_reference"
            if reason:
                excluded[reason] = excluded.get(reason, 0) + 1
                continue
            prior = visible.get(summary.summary_id)
            if prior is not None and prior != summary:
                raise ValueError("conflicting visible summary identity")
            visible[summary.summary_id] = summary
        retained = tuple(
            sorted(visible.values(), key=lambda row: (row.observed_at, row.summary_id))
        )
        latest = (
            tuple(
                row for row in retained if row.observed_at == retained[-1].observed_at
            )
            if retained
            else ()
        )
        inferred = {}
        for name in _DIMENSIONS:
            value = getattr(latest[0], name) if len(latest) == 1 else None
            inferred[name] = StateValue(
                value=value,
                provenance="inferred" if value is not None else "unknown",
                basis_summary_ids=tuple(row.summary_id for row in latest),
                explanation=(
                    "Latest explicit summary author's hypothesis; "
                    "not independently verified."
                )
                if value is not None
                else "No unambiguous available declaration supports this dimension.",
            )
        facts = point.facts
        counts = {
            "events": facts.event_count,
            "supported_events": facts.supported_event_count,
            "unsupported_events": facts.unsupported_event_count,
            "tool_items": len(facts.tool_items),
            "completed_tools": facts.completed_tool_items,
            "failed_tools": facts.failed_tool_items,
            "unknown_tools": facts.tool_items_with_unknown_failure,
            "started_turns": facts.started_turns,
            "completed_turns": facts.completed_turns,
            "failed_turns": facts.failed_turns,
        }
        # Only allowlisted event receipts are copied, never arbitrary payload/raw text.
        receipts = {}
        for event in events:
            if (
                event.event_id in event_ids
                and event.session_id == session_id
                and event.run_id in (None, run.run_id)
                and run.started_at is not None
                and event.observed_at >= run.started_at
                and (run.ended_at is None or event.observed_at <= run.ended_at)
                and max(event.observed_at, event.ingested_at) <= point.checkpoint
            ):
                receipts.setdefault(
                    event.event_id,
                    ObservedEvent(
                        event_id=event.event_id,
                        event_type=event.event_type,
                        observed_at=event.observed_at,
                        available_at=max(event.observed_at, event.ingested_at),
                        source=event.source,
                        source_version=event.source_version,
                        capture_id=event.payload["capture_id"],
                        sequence=event.payload["sequence"],
                    ),
                )
        unknown = [name for name, value in inferred.items() if value.value is None]
        unknown.extend(
            (
                "verified_completion",
                "progress_percentage",
                "same_operation_retry",
                "native_execution_time",
                "cost",
            )
        )
        if objective is None:
            unknown.append("authorized_objective")
        if not facts.supported_event_count:
            unknown.append("supported_execution_evidence")
        if not point.test_results:
            unknown.append("bound_test_evidence")
        result.append(
            TaskStateCheckpoint(
                dataset=dataset,
                checkpoint=point.checkpoint,
                identity=TaskIdentity(
                    task_id=task.task_id,
                    run_id=run.run_id,
                    session_id=session_id,
                    objective=objective.text if objective else None,
                    objective_sha256=objective.text_sha256 if objective else None,
                    objective_source=objective.source if objective else None,
                    objective_available_at=objective.available_at
                    if objective
                    else None,
                    scope_available=scope_available,
                ),
                observed=tuple(
                    sorted(
                        receipts.values(),
                        key=lambda row: (row.observed_at, row.capture_id, row.sequence),
                    )
                ),
                summaries=retained,
                execution=point,
                derived=DerivedState(
                    counts=counts,
                    token_usage=facts.token_usage,
                    token_usage_coverage=facts.token_usage_coverage,
                    repeated_failure_groups=len(facts.repeated_failures),
                ),
                inferred=inferred,
                excluded_summaries=excluded,
                unknown=tuple(unknown),
                limitations=_LIMITS + point.limitations,
            )
        )
    return tuple(result)


def compare_task_states(
    previous: TaskStateCheckpoint, current: TaskStateCheckpoint
) -> TaskStateChange:
    """Compare evidence, never interpret increased counts as semantic progress."""
    if previous.dataset != current.dataset or (
        previous.identity.task_id,
        previous.identity.run_id,
        previous.identity.session_id,
    ) != (
        current.identity.task_id,
        current.identity.run_id,
        current.identity.session_id,
    ):
        raise ValueError("state comparisons require the same dataset/task/run/session")
    if current.checkpoint <= previous.checkpoint:
        raise ValueError("state comparison requires increasing checkpoints")
    deltas = {
        name: current.derived.counts[name] - value
        for name, value in previous.derived.counts.items()
    }
    dimensions, new = [], []
    # Missing scope cannot be interpreted as inactivity or a semantic change.
    sufficient = previous.identity.scope_available and current.identity.scope_available
    if sufficient:
        if (
            previous.execution.facts.tool_items != current.execution.facts.tool_items
            or any(
                deltas[key]
                for key in (
                    "supported_events",
                    "started_turns",
                    "completed_turns",
                    "failed_turns",
                )
            )
        ):
            dimensions.append("activity")
        if (
            any(
                deltas[key] for key in ("failed_tools", "failed_turns", "unknown_tools")
            )
            or previous.derived.repeated_failure_groups
            != current.derived.repeated_failure_groups
        ):
            dimensions.append("failure")
        if previous.execution.test_results != current.execution.test_results:
            dimensions.append("tests")
        for name in _DIMENSIONS:
            before, after = previous.inferred[name], current.inferred[name]
            if (
                before.value is not None
                and after.value is not None
                and before.value != after.value
            ):
                dimensions.append(name)
            elif before.value is None and after.value is not None:
                new.append(name)
            elif before.value is not None and after.value is None:
                new.append(f"{name}_became_unknown")
        if {row.summary_id for row in previous.summaries} != {
            row.summary_id for row in current.summaries
        }:
            new.append("summary")
        if (
            previous.identity.objective is None
            and current.identity.objective is not None
        ):
            new.append("objective")
    supported = bool(
        previous.observed
        or current.observed
        or previous.summaries
        or current.summaries
        or previous.execution.test_results
        or current.execution.test_results
    )
    status = (
        "changed"
        if sufficient and dimensions
        else "no_observed_change"
        if sufficient and supported and not new
        else "unknown"
    )
    return TaskStateChange(
        previous_checkpoint=previous.checkpoint,
        checkpoint=current.checkpoint,
        status=status,
        dimensions=tuple(dimensions),
        new_information=tuple(new),
        metric_deltas=deltas,
        explanation=(
            "Changes describe retained observations or declared hypotheses; "
            "latent progress and verification remain unknown."
        )
        if sufficient and supported
        else "Insufficient scoped execution evidence to compare task state.",
    )
