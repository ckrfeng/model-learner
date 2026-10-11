"""Inspectable synthetic rule checks, separate from semantic/outcome accuracy.

Expected labels are agent-authored assertions about controlled examples. They
never enter extraction or embeddings, and they are not human-reviewed truth.
No outcomes are fabricated and no prediction model is fitted by this evaluator.
"""

from __future__ import annotations

import hashlib
import math
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from model_learner.domain import DatasetReference, Event
from model_learner.execution.longitudinal import (
    CheckpointSummary,
    TaskStateCheckpoint,
    TrajectoryInput,
    compare_task_states,
)
from model_learner.representation.inputs import TaskDescription
from model_learner.understanding.retrieval import (
    DescriptionEncoder,
    _embedding_vectors,
)

ChangeStatus = Literal["changed", "no_observed_change", "unknown"]


class _Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class ChangeExpectation(_Record):
    """Implementation checks, explicitly authored by an agent."""

    status: ChangeStatus
    dimensions: tuple[str, ...] = ()
    rationale: str = Field(min_length=1, max_length=4096)


class LongitudinalCase(TrajectoryInput):
    case_id: str = Field(min_length=1, max_length=128)
    scenario: Literal[
        "normal_progression",
        "repeated_unsuccessful_approaches",
        "complexity_growth",
        "implementation_to_debugging",
        "apparent_progress_unverified",
        "missing_evidence",
        "no_meaningful_change",
    ]
    description: TaskDescription
    association_available_at: datetime
    task_available_at: datetime
    checkpoints: tuple[datetime, datetime]
    events: tuple[Event, ...] = Field(default=(), max_length=100)
    summaries: tuple[CheckpointSummary, ...] = Field(default=(), max_length=20)
    expected: ChangeExpectation

    @model_validator(mode="after")
    def validate_scope(self):
        for value in (
            self.association_available_at,
            self.task_available_at,
            *self.checkpoints,
        ):
            if value.tzinfo is None or value.utcoffset() is None:
                raise ValueError("fixture receipts require timezone-aware timestamps")
        if self.checkpoints[0] >= self.checkpoints[1]:
            raise ValueError("fixture checkpoints must be strictly chronological")
        if (
            self.run.task_id != self.task.task_id
            or self.description.task_id != self.task.task_id
        ):
            raise ValueError("fixture task, run and description identities disagree")
        if any(
            event.session_id != self.session_id
            or event.run_id not in (None, self.run.run_id)
            or event.raw_payload is not None
            for event in self.events
        ):
            raise ValueError("fixture events require scoped metadata-only evidence")
        if any(
            summary.task_id != self.task.task_id or summary.run_id != self.run.run_id
            for summary in self.summaries
        ):
            raise ValueError("fixture summary identity disagrees")
        if self.verifications:
            raise ValueError(
                "synthetic rule-check fixtures contain no verification records"
            )
        return self


class LongitudinalFixture(_Record):
    version: Literal["synthetic-longitudinal-fixture/v1"]
    dataset: DatasetReference
    authorship: Literal["agent_authored_synthetic_rule_checks"]
    human_reviewed: Literal[False]
    outcomes_present: Literal[False]
    cases: tuple[LongitudinalCase, ...] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def validate_source(self):
        if self.dataset.source_kind.value != "simulated":
            raise ValueError(
                "this rule-check evaluator accepts only simulated fixtures"
            )
        if len({row.case_id for row in self.cases}) != len(self.cases):
            raise ValueError("fixture case IDs must be unique")
        for row in self.cases:
            if row.dataset != self.dataset:
                raise ValueError("fixture case must use the selected dataset")
            if any(summary.dataset != self.dataset for summary in row.summaries):
                raise ValueError("fixture summaries must use the selected dataset")
        return self


def load_longitudinal_fixture(
    path: str | Path, *, expected_sha256: str | None = None
) -> LongitudinalFixture:
    """Load an explicitly selected bounded fixture; never discover transcripts."""
    data = Path(path).read_bytes()
    if len(data) > 2 * 1024 * 1024:
        raise ValueError("longitudinal fixture exceeds the two MiB limit")
    if (
        expected_sha256 is not None
        and hashlib.sha256(data).hexdigest() != expected_sha256
    ):
        raise ValueError("longitudinal fixture differs from its frozen digest")
    return LongitudinalFixture.model_validate_json(data)


def _classification(rows: list[dict]) -> dict:
    confusion = {label: dict.fromkeys(_LABELS, 0) for label in _LABELS}
    for row in rows:
        confusion[row["expected_status"]][row["predicted_status"]] += 1
    known = [row for row in rows if row["predicted_status"] != "unknown"]
    return {
        "case_count": len(rows),
        "unknown_expected_count": sum(r["expected_status"] == "unknown" for r in rows),
        "unknown_prediction_count": len(rows) - len(known),
        "abstention_rate": (len(rows) - len(known)) / len(rows) if rows else None,
        "confusion": confusion,
        "status_rule_agreement": (
            sum(r["expected_status"] == r["predicted_status"] for r in rows) / len(rows)
            if rows
            else None
        ),
        "status_agreement_on_non_abstentions": (
            sum(r["expected_status"] == r["predicted_status"] for r in known)
            / len(known)
            if known
            else None
        ),
        "dimension_rule_agreement_count": sum(r["dimensions_match"] for r in rows),
        "interpretation": "Synthetic authored rule agreement; not semantic accuracy.",
        "cases": rows,
    }


_LABELS = ("changed", "no_observed_change", "unknown")


def _semantic_diagnostics(
    case_id: str, states: tuple[TaskStateCheckpoint, ...], encoder: DescriptionEncoder
) -> dict:
    """Cosines describe text relationships; no thresholds or change predictions."""
    output = []
    previous = None
    for state in states:
        latest_at = max((s.observed_at for s in state.summaries), default=None)
        latest = [s for s in state.summaries if s.observed_at == latest_at]
        summary = latest[0] if len(latest) == 1 else None
        initial = state.identity.objective
        current = summary.text if summary is not None else None
        texts = tuple(text for text in (initial, current, previous) if text is not None)
        vectors = iter(_embedding_vectors(encoder, texts)) if texts else iter(())
        initial_vector = next(vectors) if initial is not None else None
        current_vector = next(vectors) if current is not None else None
        previous_vector = next(vectors) if previous is not None else None

        def cosine(left, right):
            return (
                max(
                    -1.0,
                    min(
                        1.0, math.fsum(a * b for a, b in zip(left, right, strict=True))
                    ),
                )
                if left is not None and right is not None
                else None
            )

        output.append(
            {
                "checkpoint": state.checkpoint.isoformat(),
                "summary_id": summary.summary_id if summary is not None else None,
                "objective_summary_cosine": cosine(initial_vector, current_vector),
                "previous_summary_cosine": cosine(previous_vector, current_vector),
                "status": "diagnostic_only"
                if current_vector is not None
                else "unknown",
            }
        )
        previous = current
    return {"case_id": case_id, "checkpoints": output}


def evaluate_longitudinal_fixture(
    fixture: LongitudinalFixture, *, encoder: DescriptionEncoder | None = None
) -> dict:
    """A abstains; B compares evidence; C adds optional frozen CPU diagnostics.

    B includes deterministic projection of explicitly declared summary fields.
    Their content stays an assertion by the recorded actor, never an observed
    objective truth. Free text and embedding similarity cannot alter B labels.
    """
    initial_rows, evidence_rows, metadata_rows, diagnostics = [], [], [], []
    checks = Counter()
    violations = []
    for row in fixture.cases:
        states = row.project()
        change = compare_task_states(*states)
        metadata_change = compare_task_states(
            *row.model_copy(update={"summaries": ()}).project()
        )
        common = {
            "case_id": row.case_id,
            "scenario": row.scenario,
            "expected_status": row.expected.status,
            "expected_dimensions": list(row.expected.dimensions),
        }
        initial_rows.append(
            {
                **common,
                "predicted_status": "unknown",
                "dimensions": [],
                "dimensions_match": row.expected.dimensions == (),
                "reason": (
                    "Initial objective alone cannot identify a later state change."
                ),
            }
        )
        evidence_rows.append(
            {
                **common,
                "predicted_status": change.status,
                "dimensions": list(change.dimensions),
                "new_information": list(change.new_information),
                "dimensions_match": set(change.dimensions)
                == set(row.expected.dimensions),
            }
        )
        metadata_rows.append(
            {
                **common,
                "predicted_status": metadata_change.status,
                "dimensions": list(metadata_change.dimensions),
                "new_information": list(metadata_change.new_information),
                "dimensions_match": set(metadata_change.dimensions)
                == set(row.expected.dimensions),
            }
        )
        for state in states:
            visible_events = {
                event.event_id
                for event in row.events
                if event.observed_at <= state.checkpoint
                and event.ingested_at <= state.checkpoint
            }
            visible_summaries = {
                summary.summary_id: summary for summary in state.summaries
            }
            guardrails = {
                "event_temporal_visibility": set(state.execution.facts.event_ids)
                <= visible_events,
                "completion_never_verifies_success": (
                    state.execution.verified_task_success is None
                ),
                "receipt_time_not_native_duration": (
                    state.execution.native_duration_seconds is None
                ),
                "unknown_cost_not_zero": state.execution.cost_usd is None,
                "no_manufactured_progress_percentage": (
                    state.progress_percentage is None
                ),
                "summary_temporal_visibility": all(
                    s.observed_at <= state.checkpoint
                    and s.available_at <= state.checkpoint
                    for s in state.summaries
                ),
                "category_failure_not_same_operation_retry": all(
                    failure.same_operation_retry is None
                    for failure in state.execution.facts.repeated_failures
                ),
            }
            for dimension in ("phase", "progress", "scope", "difficulty"):
                assertion = state.inferred[dimension]
                guardrails[f"{dimension}_requires_visible_declaration"] = (
                    assertion.value is None
                    or (
                        bool(assertion.basis_summary_ids)
                        and all(
                            summary_id in visible_summaries
                            and getattr(visible_summaries[summary_id], dimension)
                            == assertion.value
                            for summary_id in assertion.basis_summary_ids
                        )
                    )
                )
            for name, passed in guardrails.items():
                checks[name] += 1
                if not passed:
                    violations.append(
                        {
                            "case_id": row.case_id,
                            "checkpoint": state.checkpoint.isoformat(),
                            "check": name,
                        }
                    )
        if encoder is not None:
            diagnostics.append(_semantic_diagnostics(row.case_id, states, encoder))
    baseline = _classification(evidence_rows)
    return {
        "evaluation_version": "synthetic-longitudinal-rule-evaluation/v1",
        "dataset": fixture.dataset.model_dump(mode="json"),
        "label_origin": fixture.authorship,
        "human_reviewed": False,
        "state_change_recognition": {
            "A": {
                "features": "Initial task information only",
                **_classification(initial_rows),
            },
            "B": {
                "features": (
                    "Initial information, deterministic execution facts "
                    "and explicit summary assertions"
                ),
                **baseline,
            },
            "B_metadata_only": {
                "features": "B with all checkpoint summary declarations removed",
                **_classification(metadata_rows),
            },
            "C": {
                "features": "B plus optional local CPU text diagnostics",
                "status": "evaluated_diagnostic_only"
                if encoder is not None
                else "unavailable",
                "reason": None
                if encoder is not None
                else "No explicitly supplied local CPU encoder.",
                **(baseline if encoder is not None else {}),
                "semantic_diagnostics": diagnostics,
                "encoder_metadata": encoder.metadata if encoder is not None else None,
                "classification_difference_from_B": 0 if encoder is not None else None,
                "interpretation": (
                    "Cosine alone cannot justify a semantic task-state change."
                ),
            },
        },
        "unsupported_inference_guardrails": {
            "status": "passed" if not violations else "failed",
            "checks_by_name": dict(sorted(checks.items())),
            "check_count": sum(checks.values()),
            "violation_count": len(violations),
            "violations": violations,
            "interpretation": (
                "Implementation invariants; "
                "not a population unsupported-inference rate."
            ),
        },
        "deterministic_telemetry_sufficiency": {
            "cases_with_declared_semantic_change": sum(
                bool(
                    set(row["dimensions"])
                    & {"phase", "progress", "scope", "difficulty"}
                )
                for row in evidence_rows
            ),
            "semantic_changes_in_metadata_only": sum(
                bool(
                    set(row["dimensions"])
                    & {"phase", "progress", "scope", "difficulty"}
                )
                for row in metadata_rows
            ),
            "interpretation": (
                "Telemetry identifies observed activity/failure changes. "
                "Semantic dimensions require explicit author declarations here; "
                "this ablation does not establish semantic understanding."
            ),
        },
        "downstream_outcome_prediction": {
            "status": "insufficient_data",
            "eligible_independently_verified_real_outcomes": 0,
            "eligible_outcomes_in_fixture": 0,
            "scores": None,
            "reason": (
                "No verified outcomes in this synthetic rule-check fixture; "
                "no predictive claim is supported."
            ),
        },
    }
