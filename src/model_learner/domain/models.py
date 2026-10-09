"""Typed, versioned records for the local evidence ledger.

These models deliberately model what is known, rather than inventing values for
telemetry that a source did not provide.  They are contracts, not predictions.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    """Return a timezone-aware timestamp suitable for persisted records."""
    return datetime.now(UTC)


def _stable_event_key(values: dict[str, Any]) -> str:
    """Create a reproducible event key when an importer has no native event ID."""
    material = {
        "source": values["source"],
        "source_version": values["source_version"],
        "native_session_id": values["native_session_id"],
        "native_event_id": values.get("native_event_id"),
        "observed_at": values["observed_at"].isoformat(),
        "event_type": values["event_type"],
        "payload": values["payload"],
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()


class VersionedModel(BaseModel):
    """Shared strict settings and an explicit version for every stored record."""

    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, allow_inf_nan=False
    )

    schema_version: int = Field(default=1, ge=1)

    @model_validator(mode="after")
    def require_aware_timestamps(self) -> VersionedModel:
        for value in self.__dict__.values():
            if isinstance(value, datetime) and (
                value.tzinfo is None or value.utcoffset() is None
            ):
                raise ValueError("timestamps must include a timezone")
        return self


class Provenance(StrEnum):
    OBSERVED = "observed"
    INFERRED = "inferred"
    DECIDED = "decided"


class DataSourceKind(StrEnum):
    REAL = "real"
    SIMULATED = "simulated"
    BENCHMARK = "benchmark"


class RunState(StrEnum):
    RUNNING = "running"
    FINISHED = "finished"
    ABANDONED = "abandoned"
    UNKNOWN = "unknown"


class OutcomeStatus(StrEnum):
    SUCCESS = "success"
    FAILURE = "failure"
    ABANDONED = "abandoned"
    UNKNOWN = "unknown"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"


class VerificationResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INDETERMINATE = "indeterminate"


class AcceptanceSpec(VersionedModel):
    identifier: str = Field(min_length=1)
    version: str = Field(min_length=1)
    description: str | None = None


class ResourceBudget(VersionedModel):
    max_cost_usd: float | None = Field(default=None, ge=0)
    max_tokens: int | None = Field(default=None, ge=0)
    max_duration_seconds: float | None = Field(default=None, ge=0)


class Task(VersionedModel):
    """A user-declared objective, independent of any native agent session."""

    task_id: UUID = Field(default_factory=uuid4)
    description: str = Field(min_length=1)
    acceptance_spec: AcceptanceSpec
    created_at: datetime = Field(default_factory=utc_now)
    workspace_id: str | None = None
    task_group: str | None = None
    resource_budget: ResourceBudget | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Session(VersionedModel):
    """A native-agent session, which may cover zero, one, or many tasks."""

    session_id: UUID = Field(default_factory=uuid4)
    source: str = Field(min_length=1)
    native_session_id: str | None = None
    started_at: datetime | None = None
    ended_at: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_time_range(self) -> Session:
        if self.ended_at is not None and self.started_at is not None:
            if self.ended_at < self.started_at:
                raise ValueError("ended_at must not precede started_at")
        return self


class TaskSessionLink(VersionedModel):
    """An explicit association; it does not assert that either record is complete."""

    task_id: UUID
    session_id: UUID
    associated_at: datetime = Field(default_factory=utc_now)
    relationship: str = Field(default="related", min_length=1)
    note: str | None = None


class ExecutionConfiguration(VersionedModel):
    """Execution dimensions kept separate from task identity and result labels."""

    provider: str | None = None
    model: str | None = None
    model_version: str | None = None
    reasoning_level: str | None = None
    harness: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class Run(VersionedModel):
    """One bounded execution of a task, potentially spanning multiple sessions."""

    run_id: UUID = Field(default_factory=uuid4)
    task_id: UUID
    state: RunState = RunState.UNKNOWN
    started_at: datetime | None = None
    ended_at: datetime | None = None
    starting_state_fingerprint: str | None = None
    resource_budget: ResourceBudget | None = None
    stop_reason: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_time_range(self) -> Run:
        if self.ended_at is not None and self.started_at is not None:
            if self.ended_at < self.started_at:
                raise ValueError("ended_at must not precede started_at")
        return self


class Attempt(VersionedModel):
    """A contiguous, observable configuration segment inside a run."""

    attempt_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    configuration: ExecutionConfiguration
    started_at: datetime | None = None
    ended_at: datetime | None = None
    strategy: str | None = None
    input_tokens: int | None = Field(default=None, ge=0)
    output_tokens: int | None = Field(default=None, ge=0)
    cost_usd: float | None = Field(default=None, ge=0)
    latency_seconds: float | None = Field(default=None, ge=0)
    measurement_source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_time_range(self) -> Attempt:
        if self.ended_at is not None and self.started_at is not None:
            if self.ended_at < self.started_at:
                raise ValueError("ended_at must not precede started_at")
        return self


class Event(VersionedModel):
    """An immutable source observation with a stable re-import key."""

    event_id: UUID = Field(default_factory=uuid4)
    observed_at: datetime
    ingested_at: datetime = Field(default_factory=utc_now)
    source: str = Field(min_length=1)
    source_version: str = Field(min_length=1)
    machine_id: str = Field(min_length=1)
    capture_method: str = Field(min_length=1)
    native_session_id: str = Field(min_length=1)
    session_id: UUID | None = None
    run_id: UUID | None = None
    native_event_id: str | None = None
    event_type: str = Field(min_length=1)
    provenance: Provenance
    payload: dict[str, Any] = Field(default_factory=dict)
    raw_payload: dict[str, Any] | None = None
    adapter_version: str | None = None
    stable_key: str | None = None

    @model_validator(mode="after")
    def provide_stable_key(self) -> Event:
        if self.stable_key is None:
            object.__setattr__(self, "stable_key", _stable_event_key(self.model_dump()))
        return self


class Verification(VersionedModel):
    """Evidence about an acceptance target, not a universal correctness claim."""

    verification_id: UUID = Field(default_factory=uuid4)
    task_id: UUID | None = None
    run_id: UUID | None = None
    acceptance_spec: AcceptanceSpec
    verifier_type: str = Field(min_length=1)
    verifier_version: str | None = None
    result: VerificationResult
    observed_at: datetime = Field(default_factory=utc_now)
    artifact_reference: str | None = None
    artifact_fingerprint: str | None = None
    report_reference: str | None = None
    provenance: Provenance = Provenance.OBSERVED
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def require_target(self) -> Verification:
        if self.task_id is None and self.run_id is None:
            raise ValueError("verification requires task_id or run_id")
        return self


class Outcome(VersionedModel):
    """An append-only task-result assessment whose verification is separate."""

    outcome_id: UUID = Field(default_factory=uuid4)
    run_id: UUID
    status: OutcomeStatus
    verification_status: VerificationStatus
    assessment_source: str = Field(min_length=1)
    recorded_at: datetime = Field(default_factory=utc_now)
    evidence_ids: tuple[UUID, ...] = ()
    supersedes_outcome_id: UUID | None = None
    note: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_evidence_claim(self) -> Outcome:
        if (
            self.verification_status is not VerificationStatus.UNVERIFIED
            and not self.evidence_ids
        ):
            raise ValueError("verified outcomes require one or more evidence_ids")
        if (
            self.assessment_source == "agent_report"
            and self.verification_status is not VerificationStatus.UNVERIFIED
        ):
            raise ValueError("an agent report alone cannot be marked verified")
        return self


class Observation(VersionedModel):
    """Future learner input, kept explicitly separate by source kind."""

    observation_id: UUID = Field(default_factory=uuid4)
    source_kind: DataSourceKind
    task_group: str = Field(min_length=1)
    configuration: ExecutionConfiguration
    task_id: UUID | None = None
    run_id: UUID | None = None
    outcome_id: UUID | None = None
    outcome_status: OutcomeStatus | None = None
    verification_status: VerificationStatus | None = None
    cost_usd: float | None = Field(default=None, ge=0)
    latency_seconds: float | None = Field(default=None, ge=0)
    recorded_at: datetime = Field(default_factory=utc_now)
    metadata: dict[str, Any] = Field(default_factory=dict)
