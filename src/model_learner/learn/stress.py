"""Reproducible multi-seed stress evaluation of the fixed-prior references."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import timedelta
from statistics import fmean, stdev

from pydantic import BaseModel, ConfigDict, Field, model_validator

from model_learner.domain.models import AcceptanceSpec
from model_learner.learn.estimator import Aggregation, BetaBernoulli
from model_learner.learn.evaluation import (
    BaselineMetrics,
    CalibrationBin,
    EvaluationReport,
    evaluate,
)
from model_learner.simulate import (
    SimulationConfig,
    execution_configurations,
    generate,
)

TARGET = AcceptanceSpec(identifier="simulated-binary-success", version="1")
AGGREGATIONS: tuple[Aggregation, ...] = ("global", "per_arm", "unpooled")


class StressScenario(BaseModel):
    """One frozen split; None evaluation delay waits for every final record."""

    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)

    name: str = Field(min_length=1)
    description: str
    simulation: SimulationConfig
    train_count: int = Field(ge=0)
    evaluation_delay_seconds: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_split(self) -> StressScenario:
        if self.train_count > self.simulation.count:
            raise ValueError("train_count must not exceed simulation count")
        return self


@dataclass(frozen=True)
class MetricDistribution:
    """Equal-seed descriptive variation; standard error is not a coverage claim."""

    seed_count: int
    mean: float | None
    standard_deviation: float | None
    standard_error: float | None
    minimum: float | None
    maximum: float | None


@dataclass(frozen=True)
class CellDiagnostic:
    model: str
    configuration_id: str
    task_group: str
    training_label_count: int
    prediction: float
    lower: float
    upper: float
    held_out_count: int
    truth_interval_coverage: float | None


@dataclass(frozen=True)
class StressRun:
    seed: int
    simulation: dict
    scenario_fingerprint: str
    evaluation: EvaluationReport
    unpooled_cells: tuple[CellDiagnostic, ...]


@dataclass(frozen=True)
class StressBaselineSummary:
    aggregation: Aggregation
    label_count: int
    truth_count: int
    represented_cell_count: int
    brier_score: MetricDistribution
    log_loss: MetricDistribution
    calibration_error: MetricDistribution
    truth_rmse: MetricDistribution
    truth_interval_coverage: MetricDistribution
    interval_width: MetricDistribution
    macro_cell_interval_coverage: MetricDistribution
    pooled_brier_score: float | None
    pooled_log_loss: float | None
    pooled_calibration: tuple[CalibrationBin, ...]
    pooled_calibration_error: float | None


@dataclass(frozen=True)
class PairedComparison:
    baseline: Aggregation
    unpooled_minus_baseline_brier: MetricDistribution
    unpooled_better_seed_count: int
    tied_seed_count: int


@dataclass(frozen=True)
class StressScenarioReport:
    name: str
    description: str
    runs: tuple[StressRun, ...]
    baselines: tuple[StressBaselineSummary, ...]
    comparisons: tuple[PairedComparison, ...]


@dataclass(frozen=True)
class StressSuiteReport:
    seeds: tuple[int, ...]
    calibration_bins: int
    scenarios: tuple[StressScenarioReport, ...]
    method: str = (
        "Independent seeded simulations with frozen chronological training. "
        "Metric distributions weight seeds equally and omit undefined scores; "
        "pooled binary scores/calibration weight available labels. Truth coverage "
        "weights held-out assignments within each seed; macro coverage weights "
        "represented configuration/group cells equally within each seed. Neither "
        "repeated held-out predictions nor cells are independent coverage trials. "
        "Intervals have nominal mass 0.95 under a stationary Bernoulli model. "
        "Calibration error is equal-width-bin ECE, a noisy descriptive diagnostic."
    )


def reference_scenarios(
    *, count: int = 1000, train_fraction: float = 0.6
) -> tuple[StressScenario, ...]:
    """Both favorable pooling and heterogeneous, sparse or nonstationary cases."""
    if isinstance(count, bool) or not isinstance(count, int) or count < 2:
        raise ValueError("count must be an integer at least 2")
    if not math.isfinite(train_fraction) or not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")

    def scenario(
        name: str,
        description: str,
        *,
        sample_count: int = count,
        evaluation_delay_seconds: float | None = None,
        **changes,
    ) -> StressScenario:
        split = max(1, min(sample_count - 1, int(sample_count * train_fraction)))
        return StressScenario(
            name=name,
            description=description,
            simulation=SimulationConfig(
                count=sample_count, unknown_probability=0, **changes
            ),
            train_count=split,
            evaluation_delay_seconds=evaluation_delay_seconds,
        )

    base = scenario("balanced", "Balanced assignment with heterogeneous task groups.")
    delay = count * base.simulation.spacing_seconds / 4
    return (
        base,
        scenario(
            "homogeneous",
            "Equal success probability in every cell favors pooling.",
            probabilities=((0.7, 0.7, 0.7),) * 4,
        ),
        scenario(
            "sparse",
            "At most 48 runs, with three rare task groups and prior-only cells.",
            sample_count=min(count, 48),
            group_weights=(17, 1, 1, 1),
        ),
        scenario(
            "imbalanced",
            "98:1:1 arm assignment hides rare-arm uncertainty in average scores.",
            arm_weights=(98, 1, 1),
        ),
        scenario(
            "drift",
            "Same configuration identities undergo a sharp probability drop at split.",
            probabilities=((0.9, 0.9, 0.9),) * 4,
            drift_at_index=base.train_count,
            drift_probabilities=((0.2, 0.2, 0.2),) * 4,
        ),
        StressScenario(
            name="missing",
            description="80% completely-at-random missing outcomes; never failures.",
            simulation=SimulationConfig(count=count, unknown_probability=0.8),
            train_count=base.train_count,
        ),
        scenario(
            "delayed_pending",
            "Delayed records leave training and held-out labels unavailable at cutoff.",
            verification_delay_seconds=delay,
            evaluation_delay_seconds=30,
        ),
        scenario(
            "delayed_mature",
            "Same delay, scored after all labels mature; frozen training stays sparse.",
            verification_delay_seconds=delay,
        ),
    )


def run_stress_suite(
    *,
    seeds: Iterable[int] = range(10),
    scenarios: Iterable[StressScenario] | None = None,
    count: int = 1000,
    train_fraction: float = 0.6,
    calibration_bins: int = 10,
) -> StressSuiteReport:
    """Pure evaluation API; never stores simulated rows in a real-data ledger.

    Explicit scenarios supersede count/train_fraction. Each scenario/seed gets a
    separate dataset identity. Duplicate seeds are rejected, not counted as more
    independent evidence. All inputs and per-seed denominators survive the report.
    """
    seeds = tuple(seeds)
    if not seeds or any(isinstance(s, bool) or not isinstance(s, int) for s in seeds):
        raise ValueError("seeds must be a nonempty sequence of integers")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be distinct")
    if (
        isinstance(calibration_bins, bool)
        or not isinstance(calibration_bins, int)
        or calibration_bins < 1
    ):
        raise ValueError("calibration_bins must be a positive integer")
    scenarios = tuple(
        reference_scenarios(count=count, train_fraction=train_fraction)
        if scenarios is None
        else scenarios
    )
    if not scenarios or len({s.name for s in scenarios}) != len(scenarios):
        raise ValueError("scenarios must be nonempty with distinct names")
    reports = []
    for scenario in scenarios:
        runs = []
        for seed in seeds:
            # Validate overrides rather than bypassing the Pydantic contracts.
            config = SimulationConfig.model_validate(
                scenario.simulation.model_dump()
                | {
                    "seed": seed,
                    "dataset_id": (
                        f"{scenario.simulation.dataset_id}:{scenario.name}:seed-{seed}"
                    ),
                }
            )
            result = generate(config)
            train_until = config.start_at + timedelta(
                seconds=scenario.train_count * config.spacing_seconds
            )
            last_decision = config.start_at + timedelta(
                seconds=max(config.count - 1, 0) * config.spacing_seconds
            )
            evaluation_at = max(
                train_until,
                last_decision
                + timedelta(
                    seconds=(
                        config.verification_delay_seconds
                        if scenario.evaluation_delay_seconds is None
                        else scenario.evaluation_delay_seconds
                    )
                ),
            )
            report = evaluate(
                result.observations,
                dataset=result.truth.dataset,
                train_until=train_until,
                evaluation_at=evaluation_at,
                acceptance_spec=TARGET,
                truth=result.truth,
                calibration_bins=calibration_bins,
            )
            learner = BetaBernoulli.fit(
                result.observations,
                dataset=result.truth.dataset,
                cutoff=train_until,
                acceptance_spec=TARGET,
            )
            grouped = {
                (g.configuration_id, g.task_group): g.metrics
                for g in report.baselines[-1].grouped_truth
            }
            cells = []
            for configuration in execution_configurations():
                for task_group in ("group-a", "group-b", "group-c", "group-d"):
                    p = learner.predict(configuration, task_group)
                    truth = grouped.get((p.configuration_id, task_group))
                    cells.append(
                        CellDiagnostic(
                            model=configuration.model,
                            configuration_id=p.configuration_id,
                            task_group=task_group,
                            training_label_count=p.sample_count,
                            prediction=p.success_probability,
                            lower=p.lower,
                            upper=p.upper,
                            held_out_count=truth.count if truth else 0,
                            truth_interval_coverage=(
                                truth.interval_coverage if truth else None
                            ),
                        )
                    )
            runs.append(
                StressRun(
                    seed=seed,
                    simulation=config.model_dump(mode="json"),
                    scenario_fingerprint=result.truth.scenario_fingerprint,
                    evaluation=report,
                    unpooled_cells=tuple(cells),
                )
            )
        summaries = tuple(
            _summarize([run.evaluation.baselines[i] for run in runs])
            for i in range(len(AGGREGATIONS))
        )
        comparisons = []
        for i, aggregation in enumerate(AGGREGATIONS[:-1]):
            differences = [
                run.evaluation.baselines[-1].brier_score
                - run.evaluation.baselines[i].brier_score
                for run in runs
                if run.evaluation.baselines[-1].brier_score is not None
                and run.evaluation.baselines[i].brier_score is not None
            ]
            comparisons.append(
                PairedComparison(
                    aggregation,
                    _distribution(differences),
                    sum(value < 0 for value in differences),
                    sum(value == 0 for value in differences),
                )
            )
        reports.append(
            StressScenarioReport(
                scenario.name,
                scenario.description,
                tuple(runs),
                summaries,
                tuple(comparisons),
            )
        )
    return StressSuiteReport(seeds, calibration_bins, tuple(reports))


def _distribution(values: Iterable[float | None]) -> MetricDistribution:
    values = [value for value in values if value is not None]
    deviation = stdev(values) if len(values) > 1 else None
    return MetricDistribution(
        len(values),
        fmean(values) if values else None,
        deviation,
        deviation / math.sqrt(len(values)) if deviation is not None else None,
        min(values) if values else None,
        max(values) if values else None,
    )


def _ece(bins: tuple[CalibrationBin, ...]) -> float | None:
    count = sum(b.count for b in bins)
    return (
        sum(
            b.count * abs(b.mean_prediction - b.observed_success_rate)
            for b in bins
            if b.count
        )
        / count
        if count
        else None
    )


def _summarize(metrics: list[BaselineMetrics]) -> StressBaselineSummary:
    bins = []
    for index in range(len(metrics[0].calibration)):
        members = [metric.calibration[index] for metric in metrics]
        count = sum(b.count for b in members)
        bins.append(
            CalibrationBin(
                members[0].lower,
                members[0].upper,
                count,
                sum(b.count * b.mean_prediction for b in members if b.count) / count
                if count
                else None,
                sum(b.count * b.observed_success_rate for b in members if b.count)
                / count
                if count
                else None,
            )
        )
    label_count = sum(metric.label_count for metric in metrics)
    return StressBaselineSummary(
        aggregation=metrics[0].aggregation,
        label_count=label_count,
        truth_count=sum(metric.truth.count for metric in metrics),
        represented_cell_count=sum(len(metric.grouped_truth) for metric in metrics),
        brier_score=_distribution(metric.brier_score for metric in metrics),
        log_loss=_distribution(metric.log_loss for metric in metrics),
        calibration_error=_distribution(_ece(metric.calibration) for metric in metrics),
        truth_rmse=_distribution(
            metric.truth.root_mean_squared_error for metric in metrics
        ),
        truth_interval_coverage=_distribution(
            metric.truth.interval_coverage for metric in metrics
        ),
        interval_width=_distribution(
            metric.truth.mean_interval_width for metric in metrics
        ),
        macro_cell_interval_coverage=_distribution(
            fmean(group.metrics.interval_coverage for group in metric.grouped_truth)
            if metric.grouped_truth
            else None
            for metric in metrics
        ),
        pooled_brier_score=(
            sum(
                metric.label_count * metric.brier_score
                for metric in metrics
                if metric.label_count
            )
            / label_count
            if label_count
            else None
        ),
        pooled_log_loss=(
            sum(
                metric.label_count * metric.log_loss
                for metric in metrics
                if metric.label_count
            )
            / label_count
            if label_count
            else None
        ),
        pooled_calibration=tuple(bins),
        pooled_calibration_error=_ece(tuple(bins)),
    )
