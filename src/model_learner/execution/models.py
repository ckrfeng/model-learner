"""Read-only checkpoint projections; observed facts and heuristics are separate."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class Projection(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid")


class ToolObservation(Projection):
    capture_id: str
    item_id: str
    tool_type: str
    server: str | None = None
    tool: str | None = None
    event_ids: tuple[UUID, ...]
    latest_event_id: UUID
    observed_status: str | None = None
    exit_code: int | None = None
    started_observed: bool
    terminal_observed: bool
    failed: bool | None
    provenance: Literal["observed"] = "observed"


class RepeatedFailure(Projection):
    tool_type: str
    server: str | None = None
    tool: str | None = None
    failed_items: int
    event_ids: tuple[UUID, ...]
    identity_basis: Literal["named_tool", "tool_category"]
    same_operation_retry: None = None
    provenance: Literal["observed"] = "observed"


class ExecutionFacts(Projection):
    event_count: int
    supported_event_count: int
    unsupported_event_count: int
    event_types: dict[str, int]
    event_ids: tuple[UUID, ...]
    tool_items: tuple[ToolObservation, ...]
    tool_events_missing_identity: int
    completed_tool_items: int
    failed_tool_items: int
    tool_items_with_unknown_failure: int
    started_turns: int
    completed_turns: int
    failed_turns: int
    repeated_failures: tuple[RepeatedFailure, ...]
    token_usage: dict[str, int | None]
    token_usage_coverage: dict[str, int]
    provenance: Literal["observed"] = "observed"


class StateInference(Projection):
    state: str
    basis_event_ids: tuple[UUID, ...] = ()
    basis_verification_ids: tuple[UUID, ...] = ()
    explanation: str
    rule_version: str = "codex-checkpoint-heuristics/v1"
    provenance: Literal["inferred"] = "inferred"


class TestCaseObservation(Projection):
    test_id: str
    status: Literal["passed", "failure", "error", "skipped"]


class TestResultObservation(Projection):
    verification_id: UUID
    observed_at: datetime
    available_at: datetime
    availability_basis: Literal["caller_receipt", "declared_observed_at"]
    artifact_fingerprint: str
    report_sha256: str | None
    counts: dict[str, int]
    counts_basis: Literal["retained_report_case_entries"] = (
        "retained_report_case_entries"
    )
    cases: tuple[TestCaseObservation, ...]
    case_statuses: dict[str, str]
    ambiguous_test_ids: tuple[str, ...]
    execution_completed: bool | None
    execution_completed_provenance: Literal["external_operator_receipt"] = (
        "external_operator_receipt"
    )
    completeness_reasons: tuple[str, ...]
    criterion_result: Literal["pass", "fail", "indeterminate"]
    criterion_result_provenance: Literal["inferred"] = "inferred"
    completeness_provenance: Literal["inferred"] = "inferred"
    provenance: Literal["observed"] = "observed"


class CaseStatusChange(Projection):
    test_id: str
    before: str
    after: str


class TestResultChange(Projection):
    previous_verification_id: UUID
    verification_id: UUID
    same_test_set: bool
    failure_count_delta: int | None
    error_count_delta: int | None
    passed_count_delta: int | None
    changed_cases: tuple[CaseStatusChange, ...]
    provenance: Literal["observed"] = "observed"


class ExecutionCheckpoint(Projection):
    analyzer_version: str = "codex-execution-checkpoints/v1"
    checkpoint: datetime
    session_id: UUID
    run_id: UUID | None = None
    task_id: UUID | None = None
    timestamp_basis: Literal["capture_receipt"] = "capture_receipt"
    facts: ExecutionFacts
    execution_state: StateInference
    signals: tuple[StateInference, ...]
    test_results: tuple[TestResultObservation, ...]
    test_changes: tuple[TestResultChange, ...]
    test_state: StateInference
    excluded_evidence: dict[str, int] = Field(default_factory=dict)
    diagnostics: tuple[str, ...]
    limitations: tuple[str, ...]
    verified_task_success: None = None
    native_duration_seconds: None = None
    cost_usd: None = None
