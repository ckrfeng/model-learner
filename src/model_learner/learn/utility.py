"""Explicit utility conventions over existing advisory estimates; never execute."""

from __future__ import annotations

import math
from collections.abc import Mapping
from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    TypeAdapter,
    model_validator,
)

from model_learner.learn.advisory import AdvisoryInput, _public_label

Predictor = Literal["fixed_prior", "global", "per_arm", "A", "B", "C"]
Nonnegative = Annotated[float, Field(ge=0)]
Probability = Annotated[float, Field(ge=0, le=1)]
Count = Annotated[int, Field(ge=0)]
SnapshotID = Annotated[str, Field(pattern=r"^[a-f0-9]{64}$")]
ERROR = "invalid utility policy or advisory contract"


class _Frozen(BaseModel):
    model_config = ConfigDict(
        frozen=True,
        extra="forbid",
        strict=True,
        allow_inf_nan=False,
        hide_input_in_errors=True,
    )


class _Limits(_Frozen):
    minimum_eligible_labels: Annotated[int, Field(ge=1)]
    maximum_interval_width: Probability | None
    maximum_cost_usd: Nonnegative | None
    maximum_latency_seconds: Nonnegative | None


class QualityFirst(_Limits):
    version: Literal["quality-first/v1"]


class CostSensitive(_Limits):
    version: Literal["cost-sensitive/v1"]
    success_value_usd: Annotated[float, Field(gt=0)]


class Balanced(_Limits):
    version: Literal["balanced/v1"]
    quality_weight: Probability
    cost_weight: Probability
    latency_weight: Probability
    cost_reference_usd: Annotated[float, Field(gt=0)]
    latency_reference_seconds: Annotated[float, Field(gt=0)]

    @model_validator(mode="after")
    def normalized_weights(self):
        if (
            abs(
                math.fsum((self.quality_weight, self.cost_weight, self.latency_weight))
                - 1
            )
            > 1e-12
        ):
            raise ValueError("balanced weights must sum to one within 1e-12")
        return self


UtilityPolicy = Annotated[
    QualityFirst | CostSensitive | Balanced, Field(discriminator="version")
]
_POLICY = TypeAdapter(UtilityPolicy)


class Measurement(_Frozen):
    known_count: Count
    missing_count: Count
    mean: Nonnegative | None
    minimum: Nonnegative | None
    maximum: Nonnegative | None

    @model_validator(mode="after")
    def consistent(self):
        if self.known_count == 0:
            if any(v is not None for v in (self.mean, self.minimum, self.maximum)):
                raise ValueError("inconsistent measurement coverage")
        elif (
            any(v is None for v in (self.mean, self.minimum, self.maximum))
            or not self.minimum <= self.mean <= self.maximum
        ):
            raise ValueError("inconsistent measurement coverage")
        return self


class Resources(_Frozen):
    observation_count: Count
    cost_usd: Measurement
    latency_seconds: Measurement

    @model_validator(mode="after")
    def consistent(self):
        if any(
            m.known_count + m.missing_count != self.observation_count
            for m in (self.cost_usd, self.latency_seconds)
        ):
            raise ValueError("inconsistent resource coverage")
        return self


class _Estimate(_Frozen):
    predictor: Predictor
    status: Literal["available", "unavailable"]
    probability: Probability
    lower: Probability
    upper: Probability
    credible_mass: Annotated[float, Field(gt=0, lt=1)]
    successes: Count
    failures: Count
    eligible_count: Count
    resources: Resources

    @model_validator(mode="after")
    def consistent(self):
        if (
            self.lower > self.upper
            or self.eligible_count != self.successes + self.failures
            or self.resources.observation_count != self.eligible_count
        ):
            raise ValueError("inconsistent advisory estimate")
        return self


class Configuration(_Frozen):
    configuration_id: SnapshotID
    provider: str | None
    model: str | None
    reasoning_level: str | None
    model_version: str | None
    harness: str | None
    harness_version: str | None
    configuration_version: str | None

    @model_validator(mode="after")
    def public_labels(self):
        for field in type(self).model_fields:
            _public_label(getattr(self, field))
        return self


class _Dataset(_Frozen):
    schema_version: int
    source_kind: Literal["real", "simulated", "benchmark"]
    dataset_id: str
    dataset_version: str


class _Acceptance(_Frozen):
    identifier: str
    version: str


class _Budget(_Frozen):
    schema_version: int
    max_cost_usd: Nonnegative | None
    max_tokens: Count | None
    max_duration_seconds: Nonnegative | None


class _Versions(_Frozen):
    estimator: Literal["beta-bernoulli/fixed-beta-1-1/v1"]
    forecast: Literal["prospective-forecast/v1"]
    compatibility_policy: str
    policy_fingerprint: SnapshotID
    decision_policy: Literal["abstain-only/v1"]


class AdvisoryIdentity(_Frozen):
    version: Literal["configuration-advisory/v1"]
    task_id: str
    task_group: str
    dataset: _Dataset
    acceptance: _Acceptance
    resource_budget: _Budget | None
    cutoff: str
    versions: _Versions

    @model_validator(mode="after")
    def public_identity(self):
        if str(UUID(self.task_id)) != self.task_id:
            raise ValueError("invalid canonical task identity")
        cutoff = datetime.fromisoformat(self.cutoff)
        if cutoff.tzinfo is None or cutoff.utcoffset() is None:
            raise ValueError("cutoff must be timezone aware")
        for v in (
            self.task_group,
            self.dataset.dataset_id,
            self.dataset.dataset_version,
            self.acceptance.identifier,
            self.acceptance.version,
        ):
            _public_label(v)
        _public_label(self.versions.compatibility_policy, version=True)
        return self


class CandidateUtility(_Frozen):
    configuration: Configuration
    predictor: Predictor
    status: Literal["available", "unavailable"]
    probability: Probability | None
    lower: Probability | None
    upper: Probability | None
    credible_mass: float | None
    successes: Count | None
    failures: Count | None
    eligible_count: Count | None
    resources: Resources | None
    eligible: bool
    reasons: tuple[str, ...]
    utility: float | None


class UtilityAdvice(_Frozen):
    version: Literal["explicit-utility-advice/v1"] = "explicit-utility-advice/v1"
    advisory: AdvisoryIdentity
    policy: UtilityPolicy
    predictor: Predictor
    decision_at: AwareDatetime
    status: Literal["hypothetical_choice", "abstain"]
    reason: Literal["highest_utility", "utility_tie", "no_eligible_candidates"]
    selected_configuration_id: SnapshotID | None
    selected_utility: float | None
    candidates: tuple[CandidateUtility, ...]
    interpretation: str = (
        "Conditional success intervals are unchanged. Utility is a point calculation "
        "using declared resource means and caller parameters, not a utility interval, "
        "calibrated value, outcome, execution instruction or superiority claim."
    )


def _candidate(configuration, estimate, policy, predictor):
    if estimate is None:
        return CandidateUtility(
            configuration=configuration,
            predictor=predictor,
            status="unavailable",
            probability=None,
            lower=None,
            upper=None,
            credible_mass=None,
            successes=None,
            failures=None,
            eligible_count=None,
            resources=None,
            eligible=False,
            reasons=("predictor_not_available",),
            utility=None,
        )
    reasons = []
    if estimate.status != "available":
        reasons.append("predictor_not_available")
    if estimate.eligible_count < policy.minimum_eligible_labels:
        reasons.append("insufficient_eligible_labels")
    if (
        policy.maximum_interval_width is not None
        and estimate.upper - estimate.lower > policy.maximum_interval_width
    ):
        reasons.append("interval_too_wide")
    cost, latency = estimate.resources.cost_usd, estimate.resources.latency_seconds
    needs_cost = (
        isinstance(policy, CostSensitive)
        or isinstance(policy, Balanced)
        and policy.cost_weight > 0
        or policy.maximum_cost_usd is not None
    )
    needs_latency = (
        isinstance(policy, Balanced)
        and policy.latency_weight > 0
        or policy.maximum_latency_seconds is not None
    )
    if needs_cost and cost.known_count == 0:
        reasons.append("missing_cost_estimate")
    if needs_latency and latency.known_count == 0:
        reasons.append("missing_latency_estimate")
    if (
        policy.maximum_cost_usd is not None
        and cost.mean is not None
        and cost.mean > policy.maximum_cost_usd
    ):
        reasons.append("maximum_cost_exceeded")
    if (
        policy.maximum_latency_seconds is not None
        and latency.mean is not None
        and latency.mean > policy.maximum_latency_seconds
    ):
        reasons.append("maximum_latency_exceeded")
    utility = None
    if not reasons:
        p = estimate.probability
        if isinstance(policy, QualityFirst):
            utility = p
        elif isinstance(policy, CostSensitive):
            utility = policy.success_value_usd * p - cost.mean
        else:
            utility = math.fsum(
                (
                    policy.quality_weight * p,
                    -policy.cost_weight * (cost.mean / policy.cost_reference_usd)
                    if policy.cost_weight
                    else 0,
                    -policy.latency_weight
                    * (latency.mean / policy.latency_reference_seconds)
                    if policy.latency_weight
                    else 0,
                )
            )
        if not math.isfinite(utility):
            raise ValueError(ERROR)
    return CandidateUtility(
        configuration=configuration,
        predictor=predictor,
        status=estimate.status,
        probability=estimate.probability,
        lower=estimate.lower,
        upper=estimate.upper,
        credible_mass=estimate.credible_mass,
        successes=estimate.successes,
        failures=estimate.failures,
        eligible_count=estimate.eligible_count,
        resources=estimate.resources,
        eligible=not reasons,
        reasons=tuple(reasons),
        utility=utility,
    )


def evaluate_utility(
    advisory: Mapping,
    *,
    policy: UtilityPolicy | Mapping,
    predictor: Predictor,
    decision_at: datetime,
) -> UtilityAdvice:
    """Pure projection and explicit ranking; invalid payloads never enter errors."""
    try:
        validated_policy = _POLICY.validate_python(
            policy.model_dump() if isinstance(policy, BaseModel) else policy
        )
        predictor = TypeAdapter(Predictor).validate_python(predictor)
        decision_at = TypeAdapter(AwareDatetime).validate_python(
            decision_at, strict=True
        )
        identity = AdvisoryIdentity.model_validate(
            {field: advisory[field] for field in AdvisoryIdentity.model_fields}
        )
        if decision_at < datetime.fromisoformat(identity.cutoff):
            raise ValueError(ERROR)
        candidates = []
        for raw in advisory["candidates"]:
            configuration = Configuration.model_validate(raw["configuration"])
            selected = [e for e in raw["estimates"] if e["predictor"] == predictor]
            if len(selected) > 1:
                raise ValueError(ERROR)
            estimate = (
                None
                if not selected
                else _Estimate.model_validate(
                    {k: selected[0][k] for k in _Estimate.model_fields}
                )
            )
            candidates.append(
                _candidate(configuration, estimate, validated_policy, predictor)
            )
        candidates.sort(key=lambda c: c.configuration.configuration_id)
        ids = [c.configuration.configuration_id for c in candidates]
        if not ids or len(set(ids)) != len(ids):
            raise ValueError(ERROR)
        eligible = [c for c in candidates if c.eligible]
        best = max((c.utility for c in eligible), default=None)
        winners = [c for c in eligible if abs(c.utility - best) <= 1e-12]
        winner = winners[0] if len(winners) == 1 else None
        return UtilityAdvice(
            advisory=identity,
            policy=validated_policy,
            predictor=predictor,
            decision_at=decision_at,
            status="hypothetical_choice" if winner else "abstain",
            reason="highest_utility"
            if winner
            else "utility_tie"
            if winners
            else "no_eligible_candidates",
            selected_configuration_id=winner.configuration.configuration_id
            if winner
            else None,
            selected_utility=winner.utility if winner else None,
            candidates=tuple(candidates),
        )
    except (ValueError, TypeError, KeyError, AttributeError, OverflowError):
        raise ValueError(ERROR) from None


class ShadowInput(_Frozen):
    version: Literal["explicit-utility-shadow-input/v1"]
    advisory: AdvisoryInput
    policy: UtilityPolicy
    predictor: Predictor
    decision_at: AwareDatetime
    human_selected_configuration_id: SnapshotID | None = None


class ShadowRecord(_Frozen):
    version: Literal["explicit-utility-shadow-record/v1"] = (
        "explicit-utility-shadow-record/v1"
    )
    input_sha256: SnapshotID
    advice: UtilityAdvice
    human_selected_configuration_id: SnapshotID | None
    interpretation: str = (
        "Nonexecuting hypothetical decision snapshot. Human choice is separate. "
        "No execution, outcome, propensity or counterfactual result is recorded."
    )


def shadow_record(
    payload: ShadowInput, advisory: Mapping, *, input_sha256: str
) -> ShadowRecord:
    try:
        ids = {c.configuration_id for c in payload.advisory.request.candidates}
        if (
            payload.human_selected_configuration_id is not None
            and payload.human_selected_configuration_id not in ids
        ):
            raise ValueError(ERROR)
        result = evaluate_utility(
            advisory,
            policy=payload.policy,
            predictor=payload.predictor,
            decision_at=payload.decision_at,
        )
        if {c.configuration.configuration_id for c in result.candidates} != ids:
            raise ValueError(ERROR)
        return ShadowRecord(
            input_sha256=input_sha256,
            advice=result,
            human_selected_configuration_id=payload.human_selected_configuration_id,
        )
    except (ValueError, TypeError, AttributeError):
        raise ValueError(ERROR) from None
