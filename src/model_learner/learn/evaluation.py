"""Frozen, time-ordered held-out evaluation; simulator truth stays here."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from statistics import fmean

from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    DataSourceKind,
    Observation,
    OutcomeStatus,
    ResourceBudget,
)
from model_learner.learn.estimator import (
    Aggregation,
    BetaBernoulli,
    PosteriorSummary,
    ResourceSummary,
    TrainingSummary,
    label_exclusion,
    matches_target,
    require_aware,
    resource_summary,
    select_records,
)
from model_learner.simulate.generator import SimulationTruth


@dataclass(frozen=True)
class CalibrationBin:
    lower: float
    upper: float
    count: int
    mean_prediction: float | None
    observed_success_rate: float | None


@dataclass(frozen=True)
class TruthMetrics:
    count: int
    mean_absolute_error: float | None
    root_mean_squared_error: float | None
    interval_coverage: float | None
    mean_interval_width: float | None


@dataclass(frozen=True)
class GroupTruthMetrics:
    configuration_id: str
    task_group: str
    metrics: TruthMetrics


@dataclass(frozen=True)
class BaselineMetrics:
    aggregation: Aggregation
    label_count: int
    brier_score: float | None
    log_loss: float | None
    calibration: tuple[CalibrationBin, ...]
    truth: TruthMetrics | None
    grouped_truth: tuple[GroupTruthMetrics, ...]


@dataclass(frozen=True)
class EvaluationReport:
    dataset: dict[str, str]
    acceptance_spec: dict[str, str]
    resource_budget: dict[str, float | int | None] | None
    train_until: str
    evaluation_at: str
    training: TrainingSummary
    held_out_count: int
    scored_label_count: int
    exclusions: dict[str, int]
    held_out_resources: ResourceSummary
    baselines: tuple[BaselineMetrics, ...]
    missing_truth_count: int | None
    method: str = (
        "Frozen prefix training: decisions before train_until and records/labels "
        "available by train_until. Scores use verified held-out labels available "
        "by evaluation_at. Truth intervals describe assignment-weighted coverage "
        "of latent success probability, not future binary outcome coverage."
    )


def evaluate(
    observations: Iterable[Observation],
    *,
    dataset: DatasetReference,
    train_until: datetime,
    evaluation_at: datetime,
    acceptance_spec: AcceptanceSpec,
    resource_budget: ResourceBudget | None = None,
    truth: SimulationTruth | None = None,
    calibration_bins: int = 10,
    training_observations: Iterable[Observation] | None = None,
) -> EvaluationReport:
    """Compare global, exact-configuration and group × configuration Beta priors.

    All models use the same fixed Beta(1,1) prior and frozen training prefix.
    The unpooled entry is the main reference learner, not an advanced model.
    Unknown outcomes contribute to coverage/resource counts but not label scores.
    ``training_observations`` can hold a separately resolved assessment snapshot
    at ``train_until``; the primary rows hold scoring state at ``evaluation_at``.
    Fit still enforces training decision, record and label availability cutoffs.
    """
    require_aware(train_until, "train_until")
    require_aware(evaluation_at, "evaluation_at")
    if evaluation_at < train_until:
        raise ValueError("evaluation_at must not precede train_until")
    if isinstance(calibration_bins, bool) or not isinstance(calibration_bins, int):
        raise ValueError("calibration_bins must be a positive integer")
    if calibration_bins <= 0:
        raise ValueError("calibration_bins must be a positive integer")
    input_rows = list(observations)
    # Historical assessment heads at training and scoring times may differ.
    # The caller can supply independently resolved, frozen training records.
    training_rows = (
        input_rows if training_observations is None else list(training_observations)
    )
    rows, exclusions = select_records(input_rows, dataset)
    held_out: list[Observation] = []
    scored: list[Observation] = []
    for row in rows:
        if not matches_target(row, acceptance_spec, resource_budget):
            exclusions["other_target_or_budget"] += 1
            continue
        if row.decision_at < train_until:
            continue
        if row.decision_at > evaluation_at or row.recorded_at > evaluation_at:
            exclusions["held_out_not_available"] += 1
            continue
        held_out.append(row)
        reason = label_exclusion(row)
        if reason is not None:
            exclusions[reason] += 1
        elif row.label_available_at is None or row.label_available_at > evaluation_at:
            exclusions["held_out_label_not_available"] += 1
        else:
            scored.append(row)
    truth_by_id: dict[str, float] = {}
    if truth is not None:
        if (
            dataset.source_kind is not DataSourceKind.SIMULATED
            or truth.dataset != dataset
        ):
            raise ValueError("truth must belong to the selected simulated dataset")
        if truth.simulator_version != "1":
            raise ValueError("unsupported simulator truth version")
        for record in truth.records:
            if record.source_record_id in truth_by_id:
                raise ValueError("duplicate simulator truth identifier")
            truth_by_id[record.source_record_id] = record.success_probability
        observed_ids = {row.source_record_id for row in rows}
        if set(truth_by_id) - observed_ids:
            raise ValueError("truth identifiers do not match the selected observations")
        labels_by_id = {
            row.source_record_id: row.outcome_status is OutcomeStatus.SUCCESS
            for row in scored
        }
        for record in truth.records:
            if (
                record.source_record_id in labels_by_id
                and labels_by_id[record.source_record_id] != record.realized_success
            ):
                raise ValueError("truth realization conflicts with the held-out label")
    metrics: list[BaselineMetrics] = []
    training: TrainingSummary | None = None
    for aggregation in ("global", "per_arm", "unpooled"):
        learner = BetaBernoulli.fit(
            training_rows,
            dataset=dataset,
            cutoff=train_until,
            acceptance_spec=acceptance_spec,
            resource_budget=resource_budget,
            aggregation=aggregation,
        )
        training = learner.training_summary
        cache: dict[tuple[str | None, str], PosteriorSummary] = {}
        for row in held_out:
            key = row.configuration.configuration_id, row.task_group
            if key not in cache:
                cache[key] = learner.predict(row.configuration, row.task_group)
        predictions = [
            cache[
                (row.configuration.configuration_id, row.task_group)
            ].success_probability
            for row in scored
        ]
        labels = [int(row.outcome_status is OutcomeStatus.SUCCESS) for row in scored]
        bins: list[CalibrationBin] = []
        for index in range(calibration_bins):
            members = [
                (probability, label)
                for probability, label in zip(predictions, labels, strict=True)
                if min(int(probability * calibration_bins), calibration_bins - 1)
                == index
            ]
            bins.append(
                CalibrationBin(
                    lower=index / calibration_bins,
                    upper=(index + 1) / calibration_bins,
                    count=len(members),
                    mean_prediction=fmean(p for p, _ in members) if members else None,
                    observed_success_rate=fmean(y for _, y in members)
                    if members
                    else None,
                )
            )
        comparisons: list[tuple[PosteriorSummary, float]] = []
        grouped: dict[tuple[str, str], list[tuple[PosteriorSummary, float]]] = {}
        for row in held_out:
            if row.source_record_id in truth_by_id:
                posterior = cache[(row.configuration.configuration_id, row.task_group)]
                comparison = posterior, truth_by_id[row.source_record_id]
                comparisons.append(comparison)
                grouped.setdefault(
                    (posterior.configuration_id, row.task_group), []
                ).append(comparison)
        metrics.append(
            BaselineMetrics(
                aggregation=aggregation,
                label_count=len(labels),
                brier_score=(
                    fmean(
                        (p - y) ** 2 for p, y in zip(predictions, labels, strict=True)
                    )
                    if labels
                    else None
                ),
                log_loss=(
                    fmean(
                        -y * math.log(p) - (1 - y) * math.log1p(-p)
                        for p, y in zip(predictions, labels, strict=True)
                    )
                    if labels
                    else None
                ),
                calibration=tuple(bins),
                truth=_truth_metrics(comparisons) if truth is not None else None,
                grouped_truth=tuple(
                    GroupTruthMetrics(configuration, group, _truth_metrics(values))
                    for (configuration, group), values in sorted(grouped.items())
                ),
            )
        )
    assert training is not None
    return EvaluationReport(
        dataset={
            "source_kind": dataset.source_kind.value,
            "dataset_id": dataset.dataset_id,
            "dataset_version": dataset.dataset_version,
        },
        acceptance_spec={
            "identifier": acceptance_spec.identifier,
            "version": acceptance_spec.version,
        },
        resource_budget=(
            resource_budget.model_dump(exclude={"schema_version"})
            if resource_budget is not None
            else None
        ),
        train_until=train_until.isoformat(),
        evaluation_at=evaluation_at.isoformat(),
        training=training,
        held_out_count=len(held_out),
        scored_label_count=len(scored),
        exclusions=dict(exclusions),
        held_out_resources=resource_summary(held_out),
        baselines=tuple(metrics),
        missing_truth_count=(
            sum(row.source_record_id not in truth_by_id for row in held_out)
            if truth is not None
            else None
        ),
    )


def _truth_metrics(values: list[tuple[PosteriorSummary, float]]) -> TruthMetrics:
    if not values:
        return TruthMetrics(0, None, None, None, None)
    return TruthMetrics(
        count=len(values),
        mean_absolute_error=fmean(abs(p.success_probability - t) for p, t in values),
        root_mean_squared_error=math.sqrt(
            fmean((p.success_probability - t) ** 2 for p, t in values)
        ),
        interval_coverage=fmean(p.lower <= t <= p.upper for p, t in values),
        mean_interval_width=fmean(p.upper - p.lower for p, _ in values),
    )
