"""Pure fixed-prior outcome inference with explicit data and temporal selection."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from statistics import fmean
from typing import Literal

from model_learner.domain.models import (
    AcceptanceSpec,
    AttributionStatus,
    DatasetReference,
    ExecutionConfiguration,
    Observation,
    OutcomeStatus,
    ResourceBudget,
    VerificationStatus,
)
from model_learner.learn.numerics import MAX_BETA_SHAPE_SUM, beta_quantile

Aggregation = Literal["global", "per_arm", "unpooled"]


@dataclass(frozen=True)
class MeasurementSummary:
    known_count: int
    missing_count: int
    mean: float | None
    minimum: float | None
    maximum: float | None


@dataclass(frozen=True)
class ResourceSummary:
    observation_count: int
    cost_usd: MeasurementSummary
    latency_seconds: MeasurementSummary


@dataclass(frozen=True)
class TrainingSummary:
    selected_count: int
    eligible_label_count: int
    excluded: dict[str, int]
    resources: ResourceSummary


@dataclass(frozen=True)
class PosteriorSummary:
    configuration_id: str
    task_group: str
    aggregation: Aggregation
    successes: int
    failures: int
    alpha: float
    beta: float
    success_probability: float
    variance: float
    credible_mass: float
    lower: float
    upper: float
    resources: ResourceSummary

    @property
    def sample_count(self) -> int:
        return self.successes + self.failures


def require_aware(value: datetime, name: str) -> None:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError(f"{name} must include a timezone")


def matches_target(
    observation: Observation,
    acceptance_spec: AcceptanceSpec,
    resource_budget: ResourceBudget | None,
) -> bool:
    target = observation.acceptance_spec
    return (
        target is not None
        and (target.identifier, target.version)
        == (acceptance_spec.identifier, acceptance_spec.version)
        and observation.resource_budget == resource_budget
    )


def select_records(
    observations: Iterable[Observation], dataset: DatasetReference
) -> tuple[list[Observation], Counter[str]]:
    """Select one dataset and count reimports without counting an experiment twice.

    Conflicting derivations/assessment revisions of one experimental unit are
    rejected. Use the assessment resolver before learning real revision histories;
    silently treating a revision as another trial is incorrect.
    """
    rows: dict[str, Observation] = {}
    units: dict[str, str] = {}
    identifiers: dict[str, str] = {}
    excluded: Counter[str] = Counter()
    for row in observations:
        if row.source_kind != dataset.source_kind or row.dataset != dataset:
            excluded["other_dataset"] += 1
            continue
        if row.schema_version != 2:
            excluded["legacy_schema"] += 1
            continue
        assert row.stable_key is not None
        identity = str(row.observation_id)
        if identity in identifiers and identifiers[identity] != row.stable_key:
            raise ValueError("conflicting observation identifier")
        identifiers[identity] = row.stable_key
        unit = str(row.run_id) if row.run_id is not None else row.source_record_id
        if unit is None:
            raise ValueError("observation is missing its independent experimental unit")
        if unit in units and units[unit] != row.stable_key:
            raise ValueError("conflicting observations for one experimental unit")
        units[unit] = row.stable_key
        if row.stable_key in rows:
            excluded["duplicate"] += 1
            # Reimport time is not first knowledge of this immutable observation.
            if row.recorded_at < rows[row.stable_key].recorded_at:
                rows[row.stable_key] = row
        else:
            rows[row.stable_key] = row
    return sorted(
        rows.values(), key=lambda row: (row.decision_at, row.stable_key)
    ), excluded


def label_exclusion(row: Observation) -> str | None:
    if row.outcome_status not in (OutcomeStatus.SUCCESS, OutcomeStatus.FAILURE):
        return "missing_or_nonbinary_label"
    if row.verification_status is not VerificationStatus.VERIFIED:
        return "unverified_label"
    if (
        not row.eligible_for_configuration_learning
        or row.attribution_status is not AttributionStatus.SINGLE_CONFIGURATION
        or row.configuration.model is None
    ):
        return "ineligible_attribution"
    return None


def resource_summary(rows: Iterable[Observation]) -> ResourceSummary:
    rows = list(rows)

    def describe(field: str) -> MeasurementSummary:
        values = [
            getattr(row, field) for row in rows if getattr(row, field) is not None
        ]
        return MeasurementSummary(
            known_count=len(values),
            missing_count=len(rows) - len(values),
            mean=fmean(values) if values else None,
            minimum=min(values) if values else None,
            maximum=max(values) if values else None,
        )

    return ResourceSummary(len(rows), describe("cost_usd"), describe("latency_seconds"))


class BetaBernoulli:
    """An unpooled Beta(1,1) reference; broader pooling is baseline-only.

    Exact configuration snapshot IDs distinguish harnesses, versions and settings.
    This learner estimates the selected acceptance target, not utility or policy.
    """

    @classmethod
    def fit(
        cls,
        observations: Iterable[Observation],
        *,
        dataset: DatasetReference,
        cutoff: datetime,
        acceptance_spec: AcceptanceSpec,
        resource_budget: ResourceBudget | None = None,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
        credible_mass: float = 0.95,
        aggregation: Aggregation = "unpooled",
    ) -> BetaBernoulli:
        require_aware(cutoff, "cutoff")
        if not all(
            math.isfinite(value) for value in (prior_alpha, prior_beta, credible_mass)
        ):
            raise ValueError("prior and credible mass must be finite")
        if prior_alpha < 0.5 or prior_beta < 0.5 or not 0.5 <= credible_mass <= 0.999:
            raise ValueError(
                "supported prior shapes must be at least 0.5 and credible mass "
                "must be in [0.5, 0.999]"
            )
        if prior_alpha + prior_beta > MAX_BETA_SHAPE_SUM:
            raise ValueError("supported prior shape sum is at most 100,000")
        if aggregation not in ("global", "per_arm", "unpooled"):
            raise ValueError("unknown aggregation")
        learner = cls()
        learner.prior_alpha = prior_alpha
        learner.prior_beta = prior_beta
        learner.credible_mass = credible_mass
        learner.aggregation = aggregation
        learner._counts: dict[tuple[str, str], list[int]] = defaultdict(lambda: [0, 0])
        learner._resources: dict[tuple[str, str], list[Observation]] = defaultdict(list)
        rows, excluded = select_records(observations, dataset)
        known: list[Observation] = []
        eligible_count = 0
        for row in rows:
            if not matches_target(row, acceptance_spec, resource_budget):
                excluded["other_target_or_budget"] += 1
                continue
            if row.decision_at >= cutoff or row.recorded_at > cutoff:
                excluded["not_available_at_cutoff"] += 1
                continue
            known.append(row)
            key = learner._key(row.configuration, row.task_group)
            learner._resources[key].append(row)
            reason = label_exclusion(row)
            if reason is not None:
                excluded[reason] += 1
                continue
            if row.label_available_at is None or row.label_available_at > cutoff:
                excluded["label_not_available_at_cutoff"] += 1
                continue
            eligible_count += 1
            learner._counts[key][
                0 if row.outcome_status is OutcomeStatus.SUCCESS else 1
            ] += 1
            if (
                prior_alpha + prior_beta + sum(learner._counts[key])
                > MAX_BETA_SHAPE_SUM
            ):
                raise ValueError("supported posterior shape sum is at most 100,000")
        learner.training_summary = TrainingSummary(
            selected_count=len(known),
            eligible_label_count=eligible_count,
            excluded=dict(excluded),
            resources=resource_summary(known),
        )
        return learner

    def _key(
        self, configuration: ExecutionConfiguration, task_group: str
    ) -> tuple[str, str]:
        assert configuration.configuration_id is not None
        if self.aggregation == "global":
            return "*", "*"
        if self.aggregation == "per_arm":
            return configuration.configuration_id, "*"
        return configuration.configuration_id, task_group

    def predict(
        self, configuration: ExecutionConfiguration, task_group: str
    ) -> PosteriorSummary:
        if not task_group:
            raise ValueError("task_group must not be empty")
        key = self._key(configuration, task_group)
        successes, failures = self._counts.get(key, [0, 0])
        alpha = self.prior_alpha + successes
        beta = self.prior_beta + failures
        tail = (1 - self.credible_mass) / 2
        assert configuration.configuration_id is not None
        return PosteriorSummary(
            configuration_id=configuration.configuration_id,
            task_group=task_group,
            aggregation=self.aggregation,
            successes=successes,
            failures=failures,
            alpha=alpha,
            beta=beta,
            success_probability=alpha / (alpha + beta),
            variance=alpha * beta / ((alpha + beta) ** 2 * (alpha + beta + 1)),
            credible_mass=self.credible_mass,
            lower=beta_quantile(tail, alpha, beta),
            upper=beta_quantile(1 - tail, alpha, beta),
            resources=resource_summary(self._resources.get(key, [])),
        )
