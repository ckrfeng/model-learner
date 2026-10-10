"""Independent synthetic experiments using the existing M1.1 observation schema."""

from __future__ import annotations

import hashlib
import json
import math
import random
from datetime import UTC, datetime, timedelta
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field, model_validator

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


class SimulationConfig(BaseModel):
    """Three arms × four groups; probabilities are indexed [group][arm]."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    seed: int = 1
    count: int = Field(default=1000, ge=0)
    dataset_id: str = Field(default="synthetic-reference", min_length=1)
    dataset_version: str = Field(default="1", min_length=1)
    start_at: datetime = datetime(2026, 1, 1, tzinfo=UTC)
    spacing_seconds: float = Field(default=60, gt=0)
    verification_delay_seconds: float = Field(default=30, ge=0)
    unknown_probability: float = Field(default=0.1, ge=0, le=1)
    resource_missing_probability: float = Field(default=0.1, ge=0, le=1)
    arm_weights: tuple[float, float, float] = (1, 1, 1)
    group_weights: tuple[float, float, float, float] = (1, 1, 1, 1)
    probabilities: tuple[tuple[float, float, float], ...] = (
        (0.65, 0.8, 0.9),
        (0.45, 0.65, 0.8),
        (0.75, 0.7, 0.85),
        (0.25, 0.5, 0.7),
    )
    drift_at_index: int | None = Field(default=None, ge=0)
    drift_probabilities: tuple[tuple[float, float, float], ...] | None = None
    cost_means_usd: tuple[float, float, float] = (0.02, 0.08, 0.2)
    latency_means_seconds: tuple[float, float, float] = (10, 25, 50)
    resource_log_sigma: float = Field(default=0.3, ge=0)

    @model_validator(mode="after")
    def validate_scenario(self) -> SimulationConfig:
        if self.start_at.tzinfo is None or self.start_at.utcoffset() is None:
            raise ValueError("start_at must include a timezone")
        for weights in (self.arm_weights, self.group_weights):
            if any(weight < 0 for weight in weights) or sum(weights) <= 0:
                raise ValueError(
                    "assignment weights must be nonnegative with a positive sum"
                )
        for matrix in (self.probabilities, self.drift_probabilities):
            if matrix is not None and (
                len(matrix) != 4
                or any(
                    not 0 <= probability <= 1 for row in matrix for probability in row
                )
            ):
                raise ValueError("probabilities must be a 4 × 3 matrix in [0, 1]")
        if (self.drift_at_index is None) != (self.drift_probabilities is None):
            raise ValueError("drift requires both an index and probabilities")
        if any(
            value < 0 for value in (*self.cost_means_usd, *self.latency_means_seconds)
        ):
            raise ValueError("resource means must be nonnegative")
        return self


class TruthRecord(BaseModel):
    """Evaluator data that must never be attached to learner observations."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    source_record_id: str
    success_probability: float = Field(ge=0, le=1)
    realized_success: bool


class SimulationTruth(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    simulator_version: str = "1"
    dataset: DatasetReference
    scenario_fingerprint: str
    records: tuple[TruthRecord, ...]


class SimulationResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observations: tuple[Observation, ...]
    truth: SimulationTruth


def generate(config: SimulationConfig) -> SimulationResult:
    """Return reproducible independent runs, including unlabelled executions.

    Unknown labels are missing completely at random, not failures. The known
    simulator Bernoulli result stands in for synthetic verification only; this
    does not provide any verification capability for real executions.
    """
    # Count is excluded so a longer generation retains the same experiment prefix.
    scenario = config.model_dump(mode="json", exclude={"count"})
    fingerprint = hashlib.sha256(
        json.dumps(scenario, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
    rng = random.Random(config.seed)
    dataset = DatasetReference(
        source_kind=DataSourceKind.SIMULATED,
        dataset_id=config.dataset_id,
        dataset_version=config.dataset_version,
    )
    acceptance = AcceptanceSpec(identifier="simulated-binary-success", version="1")
    configurations = tuple(
        ExecutionConfiguration(
            provider="synthetic",
            model=f"arm-{arm}",
            model_version="1",
            harness="independent-bernoulli-simulator",
            harness_version="1",
        )
        for arm in ("a", "b", "c")
    )
    observations: list[Observation] = []
    truth: list[TruthRecord] = []
    for index in range(config.count):
        group = rng.choices(range(4), weights=config.group_weights)[0]
        arm = rng.choices(range(3), weights=config.arm_weights)[0]
        matrix = config.probabilities
        if config.drift_at_index is not None and index >= config.drift_at_index:
            assert config.drift_probabilities is not None
            matrix = config.drift_probabilities
        probability = matrix[group][arm]
        success = rng.random() < probability
        unknown = rng.random() < config.unknown_probability
        cost = _resource(rng, config.cost_means_usd[arm], config.resource_log_sigma)
        latency = _resource(
            rng, config.latency_means_seconds[arm], config.resource_log_sigma
        )
        if rng.random() < config.resource_missing_probability:
            cost = None
        if rng.random() < config.resource_missing_probability:
            latency = None
        decision = config.start_at + timedelta(seconds=index * config.spacing_seconds)
        label_at = decision + timedelta(seconds=config.verification_delay_seconds)
        # Unknown executions can still have an observed resource report.
        recorded_at = label_at
        source_id = f"{fingerprint}:{index}"
        observations.append(
            Observation(
                observation_id=uuid5(
                    NAMESPACE_URL, f"model-learner-simulation:{source_id}"
                ),
                source_kind=DataSourceKind.SIMULATED,
                dataset=dataset,
                source_record_id=source_id,
                task_group=f"group-{'abcd'[group]}",
                configuration=configurations[arm],
                acceptance_spec=acceptance,
                attribution_status=AttributionStatus.SINGLE_CONFIGURATION,
                eligible_for_configuration_learning=not unknown,
                outcome_status=(
                    OutcomeStatus.UNKNOWN
                    if unknown
                    else OutcomeStatus.SUCCESS
                    if success
                    else OutcomeStatus.FAILURE
                ),
                verification_status=(
                    VerificationStatus.UNVERIFIED
                    if unknown
                    else VerificationStatus.VERIFIED
                ),
                cost_usd=cost,
                latency_seconds=latency,
                decision_at=decision,
                label_available_at=None if unknown else label_at,
                recorded_at=recorded_at,
                metadata={"measurement_source": "synthetic-generator-v1"},
            )
        )
        truth.append(
            TruthRecord(
                source_record_id=source_id,
                success_probability=probability,
                realized_success=success,
            )
        )
    return SimulationResult(
        observations=tuple(observations),
        truth=SimulationTruth(
            dataset=dataset, scenario_fingerprint=fingerprint, records=tuple(truth)
        ),
    )


def _resource(rng: random.Random, mean: float, sigma: float) -> float:
    """Lognormal measurements parameterized by arithmetic expectation."""
    return (
        0.0 if mean == 0 else rng.lognormvariate(math.log(mean) - sigma**2 / 2, sigma)
    )
