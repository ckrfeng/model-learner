"""Typed, versioned records for the local evidence ledger.

These models deliberately model what is known, rather than inventing values for
telemetry that a source did not provide.  They are contracts, not predictions.
"""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Literal
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


def _stable_configuration_id(values: dict[str, Any]) -> str:
    """Create an immutable identity for one exact configuration snapshot."""
    material = {
        key: value
        for key, value in values.items()
        if key not in {"configuration_id", "schema_version"}
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()


def _stable_observation_key(values: dict[str, Any]) -> str:
    """Identify one immutable derivation without using its random record ID."""
    material = {
        key: value
        for key, value in values.items()
        if key not in {"observation_id", "recorded_at", "stable_key"}
    }
    encoded = json.dumps(material, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(encoded.encode()).hexdigest()


class VersionedModel(BaseModel):
    """Shared strict settings and supported contract versions for stored records."""

    model_config = ConfigDict(
        extra="forbid", validate_assignment=True, allow_inf_nan=False
    )

    # Version 1 is accepted only to read M1 records. New records use version 2.
    # A future version needs an explicit parser/upcaster before it is accepted.
    schema_version: Literal[1, 2] = 2

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
    CENSORED = "censored"


class VerificationStatus(StrEnum):
    VERIFIED = "verified"
    PARTIALLY_VERIFIED = "partially_verified"
    UNVERIFIED = "unverified"


class VerificationResult(StrEnum):
    PASS = "pass"
    FAIL = "fail"
    INDETERMINATE = "indeterminate"


class AttributionStatus(StrEnum):
    """Whether a run result can be attributed to one configuration."""

    SINGLE_CONFIGURATION = "single_configuration"
    MIXED_CONFIGURATION = "mixed_configuration"
    INCOMPLETE = "incomplete"


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


class Project(VersionedModel):
    """An optional, manually declared grouping; it is not task identity."""

    project_id: UUID = Field(default_factory=uuid4)
    name: str = Field(min_length=1)
    created_at: datetime = Field(default_factory=utc_now)
    reference: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectTaskLink(VersionedModel):
    """An explicit optional project grouping for a declared task."""

    project_id: UUID
    task_id: UUID
    associated_at: datetime = Field(default_factory=utc_now)
    relationship: str = Field(default="member", min_length=1)
    note: str | None = None


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
    harness_version: str | None = None
    configuration_version: str | None = None
    configuration_id: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def provide_configuration_id(self) -> ExecutionConfiguration:
        expected = _stable_configuration_id(self.model_dump())
        if self.configuration_id is None:
            object.__setattr__(self, "configuration_id", expected)
        elif self.configuration_id != expected:
            raise ValueError("configuration_id must match the configuration snapshot")
        return self


class RunSessionLink(VersionedModel):
    """An explicit session association to a bounded run; events remain immutable."""

    run_id: UUID
    session_id: UUID
    associated_at: datetime = Field(default_factory=utc_now)


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
    censor_reason: str | None = None
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
        if self.status is OutcomeStatus.CENSORED and not self.censor_reason:
            raise ValueError("censored outcomes require a censor_reason")
        if self.status is not OutcomeStatus.CENSORED and self.censor_reason is not None:
            raise ValueError("only censored outcomes may include a censor_reason")
        return self


class DatasetReference(VersionedModel):
    """Identity of one real, synthetic, or benchmark data cohort."""

    source_kind: DataSourceKind
    dataset_id: str = Field(min_length=1)
    dataset_version: str = Field(min_length=1)


class Observation(VersionedModel):
    """Future learner input, kept explicitly separate by source kind."""

    observation_id: UUID = Field(default_factory=uuid4)
    source_kind: DataSourceKind
    dataset: DatasetReference | None = None
    source_record_id: str | None = None
    task_group: str = Field(min_length=1)
    configuration: ExecutionConfiguration
    task_id: UUID | None = None
    run_id: UUID | None = None
    attempt_id: UUID | None = None
    outcome_id: UUID | None = None
    outcome_status: OutcomeStatus | None = None
    verification_status: VerificationStatus | None = None
    evidence_ids: tuple[UUID, ...] = ()
    acceptance_spec: AcceptanceSpec | None = None
    resource_budget: ResourceBudget | None = None
    attribution_status: AttributionStatus = AttributionStatus.INCOMPLETE
    eligible_for_configuration_learning: bool = False
    cost_usd: float | None = Field(default=None, ge=0)
    latency_seconds: float | None = Field(default=None, ge=0)
    decision_at: datetime = Field(default_factory=utc_now)
    label_available_at: datetime | None = None
    recorded_at: datetime = Field(default_factory=utc_now)
    stable_key: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="after")
    def validate_learning_contract(self) -> Observation:
        if self.schema_version == 2 and self.dataset is None:
            raise ValueError("schema version 2 observations require a dataset")
        if (
            self.dataset is not None
            and self.dataset.source_kind is not self.source_kind
        ):
            raise ValueError("observation dataset source_kind must match source_kind")
        if self.source_kind is DataSourceKind.REAL and self.schema_version == 2:
            if any(
                value is None
                for value in (
                    self.task_id,
                    self.run_id,
                    self.outcome_id,
                    self.acceptance_spec,
                )
            ):
                raise ValueError(
                    "real observations require task, run, outcome, and acceptance links"
                )
            if self.outcome_status is None or self.verification_status is None:
                raise ValueError(
                    "real observations require outcome and verification status"
                )
            if (
                self.attribution_status is AttributionStatus.SINGLE_CONFIGURATION
                and self.attempt_id is None
            ):
                raise ValueError(
                    "single-configuration real observations require attempt_id"
                )
        elif self.schema_version == 2 and not self.source_record_id:
            raise ValueError("non-real observations require a source_record_id")
        if self.eligible_for_configuration_learning:
            if self.schema_version == 1:
                raise ValueError(
                    "schema version 1 observations are not learning-eligible"
                )
            if self.attribution_status is not AttributionStatus.SINGLE_CONFIGURATION:
                raise ValueError(
                    "only single-configuration observations may be eligible "
                    "for learning"
                )
            if self.outcome_status not in (
                OutcomeStatus.SUCCESS,
                OutcomeStatus.FAILURE,
            ):
                raise ValueError(
                    "eligible observations require a success or failure label"
                )
            if self.configuration.model is None:
                raise ValueError("eligible observations require a known model")
            if (
                self.source_kind is DataSourceKind.REAL
                and self.verification_status is not VerificationStatus.VERIFIED
            ):
                raise ValueError("eligible real observations require verified outcomes")
        if self.outcome_status in (OutcomeStatus.UNKNOWN, OutcomeStatus.CENSORED):
            if self.label_available_at is not None:
                raise ValueError(
                    "unknown or censored observations have no label availability"
                )
        elif self.outcome_status is not None and self.label_available_at is None:
            raise ValueError("labelled observations require label_available_at")
        if self.label_available_at is not None:
            if self.label_available_at < self.decision_at:
                raise ValueError("label_available_at must not precede decision_at")
            if self.recorded_at < self.label_available_at:
                raise ValueError("recorded_at must not precede label_available_at")
        if self.recorded_at < self.decision_at:
            raise ValueError("recorded_at must not precede decision_at")
        expected_stable_key = _stable_observation_key(self.model_dump())
        if self.stable_key is None:
            object.__setattr__(self, "stable_key", expected_stable_key)
        elif self.stable_key != expected_stable_key:
            raise ValueError("stable_key must match the observation derivation")
        return self
