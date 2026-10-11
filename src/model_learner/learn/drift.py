"""Block-prequential comparison of full history and explicit recent windows."""

from __future__ import annotations

import math
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import fmean, stdev

from model_learner.domain.models import OutcomeStatus
from model_learner.learn.estimator import (
    BetaBernoulli,
    PosteriorSummary,
    label_exclusion,
)
from model_learner.learn.evaluation import CalibrationBin
from model_learner.learn.recent import RecentWindowBetaBernoulli
from model_learner.learn.stress import TARGET, MetricDistribution, StressScenario
from model_learner.simulate.generator import (
    SimulationConfig,
    SimulationResult,
    execution_configurations,
    generate,
)


@dataclass(frozen=True)
class DriftMetrics:
    label_count: int
    truth_count: int
    brier_score: float | None
    calibration: tuple[CalibrationBin, ...]
    calibration_error: float | None
    interval_coverage: float | None
    macro_cell_interval_coverage: float | None
    interval_width: float | None
    probability_mae: float | None


@dataclass(frozen=True)
class DriftCell:
    configuration_id: str
    task_group: str
    sample_count: int
    prediction: float
    lower: float
    upper: float


@dataclass(frozen=True)
class DriftBlock:
    cutoff: str
    decision_end: str
    training_label_count: int
    discarded_label_count: int
    prior_only_cell_count: int
    cells: tuple[DriftCell, ...]
    metrics: DriftMetrics


@dataclass(frozen=True)
class DriftBaselineRun:
    name: str
    window_steps: int | None
    metrics: DriftMetrics
    tail_metrics: DriftMetrics
    adaptation_delay_steps: float | None
    adaptation_observed: bool
    adaptation_followup_steps: float | None
    blocks: tuple[DriftBlock, ...]


@dataclass(frozen=True)
class DriftRun:
    seed: int
    simulation: dict
    scenario_fingerprint: str
    score_start: str
    evaluation_at: str
    baselines: tuple[DriftBaselineRun, ...]


@dataclass(frozen=True)
class DriftBaselineSummary:
    name: str
    brier_score: MetricDistribution
    calibration_error: MetricDistribution
    interval_coverage: MetricDistribution
    macro_cell_interval_coverage: MetricDistribution
    interval_width: MetricDistribution
    tail_brier_score: MetricDistribution
    tail_interval_coverage: MetricDistribution
    adaptation_delay_steps: MetricDistribution
    adapted_seed_count: int
    adaptation_censored_seed_count: int
    paired_brier_difference_from_full: MetricDistribution
    better_seed_count: int


@dataclass(frozen=True)
class DriftScenarioReport:
    name: str
    description: str
    runs: tuple[DriftRun, ...]
    baselines: tuple[DriftBaselineSummary, ...]


@dataclass(frozen=True)
class DriftSuiteReport:
    seeds: tuple[int, ...]
    window_steps: tuple[int, ...]
    refit_steps: int
    calibration_bins: int
    scenarios: tuple[DriftScenarioReport, ...]
    method: str = (
        "Block-prequential: train only on earlier decisions with immutable records "
        "and verified labels available at each block-start cutoff; freeze predictions "
        "within block. Estimators share assignments, scoring cutoffs and Beta(1,1). "
        "Recent windows use decision age, not verification arrival age. Binary scores "
        "use labels mature at evaluation_at; simulator truth only evaluates current "
        "latent probability. Equal-tail Beta intervals have 95% posterior mass under "
        "a constant-p model, with no nominal nonstationary coverage claim. Coverage "
        "weights decision assignments; macro coverage weights represented cells. "
        "Repeated blocks/cells are dependent; distributions use independent seeds. "
        "Tail is last quarter of scored decision span. Adaptation is first of three "
        "consecutive blocks with assignment-weighted probability MAE <= 0.1 after "
        "drift finishes; unobserved recovery is censored, not assigned a zero delay."
    )


@dataclass(frozen=True)
class _Prediction:
    posterior: PosteriorSummary
    probability: float
    label: int | None


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


def _metrics(values: list[_Prediction], bin_count: int) -> DriftMetrics:
    scored = [value for value in values if value.label is not None]
    bins = []
    for index in range(bin_count):
        members = [
            value
            for value in scored
            if min(int(value.posterior.success_probability * bin_count), bin_count - 1)
            == index
        ]
        bins.append(
            CalibrationBin(
                index / bin_count,
                (index + 1) / bin_count,
                len(members),
                fmean(v.posterior.success_probability for v in members)
                if members
                else None,
                fmean(v.label for v in members) if members else None,
            )
        )
    grouped: dict[tuple[str, str], list[bool]] = {}
    for value in values:
        p = value.posterior
        grouped.setdefault((p.configuration_id, p.task_group), []).append(
            p.lower <= value.probability <= p.upper
        )
    return DriftMetrics(
        len(scored),
        len(values),
        fmean((v.posterior.success_probability - v.label) ** 2 for v in scored)
        if scored
        else None,
        tuple(bins),
        sum(
            b.count * abs(b.mean_prediction - b.observed_success_rate)
            for b in bins
            if b.count
        )
        / len(scored)
        if scored
        else None,
        fmean(v.posterior.lower <= v.probability <= v.posterior.upper for v in values)
        if values
        else None,
        fmean(fmean(cell) for cell in grouped.values()) if grouped else None,
        fmean(v.posterior.upper - v.posterior.lower for v in values)
        if values
        else None,
        fmean(abs(v.posterior.success_probability - v.probability) for v in values)
        if values
        else None,
    )


def drift_scenarios(*, count: int = 1000) -> tuple[StressScenario, ...]:
    """Seven declared scenarios, with drift and delay crossed where informative."""
    _positive_integer(count, "count", minimum=8)
    start = int(count * 0.4)
    low = ((0.2, 0.2, 0.2),) * 4
    high = ((0.9, 0.9, 0.9),) * 4

    def scenario(name: str, description: str, **changes) -> StressScenario:
        config = SimulationConfig(
            **(dict(count=count, unknown_probability=0) | changes)
        )
        return StressScenario(
            name=name, description=description, simulation=config, train_count=start
        )

    drifting = dict(probabilities=high, drift_at_index=start, drift_probabilities=low)
    return (
        scenario("stationary", "Balanced heterogeneous stationary probabilities."),
        scenario(
            "homogeneous",
            "Balanced homogeneous stationary p=0.7.",
            probabilities=((0.7, 0.7, 0.7),) * 4,
        ),
        scenario("abrupt", "Balanced abrupt 0.9 to 0.2 drift.", **drifting),
        scenario(
            "gradual",
            "Balanced linear 0.9 to 0.2 drift over 30% of runs.",
            gradual_drift_steps=max(1, int(count * 0.3)),
            **drifting,
        ),
        scenario(
            "sparse",
            "Abrupt drift with 85% independently missing labels.",
            **(drifting | {"unknown_probability": 0.85}),
        ),
        scenario(
            "imbalanced",
            "Abrupt drift with arm assignment 98:1:1.",
            arm_weights=(98, 1, 1),
            **drifting,
        ),
        scenario(
            "delayed",
            "Abrupt drift; verification arrives 15% of span later.",
            verification_delay_seconds=count * 60 * 0.15,
            **drifting,
        ),
    )


def _positive_integer(value: int, name: str, minimum: int = 1) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{name} must be an integer at least {minimum}")


def _run(
    scenario: StressScenario,
    seed: int,
    windows: tuple[int, ...],
    refit_steps: int,
    calibration_bins: int,
) -> DriftRun:
    config = SimulationConfig.model_validate(
        scenario.simulation.model_dump()
        | {
            "seed": seed,
            "dataset_id": f"drift-investigation:{scenario.name}:seed-{seed}",
        }
    )
    result = generate(config)
    score_start = config.start_at + timedelta(
        seconds=scenario.train_count * config.spacing_seconds
    )
    evaluation_at = max(
        (row.recorded_at for row in result.observations), default=score_start
    )
    if scenario.evaluation_delay_seconds is not None:
        evaluation_at = max(
            score_start,
            config.start_at
            + timedelta(
                seconds=max(config.count - 1, 0) * config.spacing_seconds
                + scenario.evaluation_delay_seconds
            ),
        )
    names = (("full_history", None),) + tuple(
        (f"recent_{window}", window) for window in windows
    )
    baselines = tuple(
        _baseline(
            result,
            config,
            scenario.train_count,
            evaluation_at,
            name,
            window,
            refit_steps,
            calibration_bins,
        )
        for name, window in names
    )
    return DriftRun(
        seed,
        config.model_dump(mode="json"),
        result.truth.scenario_fingerprint,
        score_start.isoformat(),
        evaluation_at.isoformat(),
        baselines,
    )


def _baseline(
    result: SimulationResult,
    config: SimulationConfig,
    start: int,
    evaluation_at: datetime,
    name: str,
    window: int | None,
    refit_steps: int,
    bin_count: int,
) -> DriftBaselineRun:
    truth = {r.source_record_id: r for r in result.truth.records}
    blocks = []
    all_values: list[_Prediction] = []
    tail_values: list[_Prediction] = []
    tail_start = start + int((config.count - start) * 0.75)
    for index in range(start, config.count, refit_steps):
        cutoff = config.start_at + timedelta(seconds=index * config.spacing_seconds)
        end = min(index + refit_steps, config.count)
        kwargs = dict(
            dataset=result.truth.dataset, cutoff=cutoff, acceptance_spec=TARGET
        )
        if window is None:
            learner = BetaBernoulli.fit(result.observations, **kwargs)
        else:
            learner = RecentWindowBetaBernoulli.fit(
                result.observations,
                window_duration=timedelta(seconds=window * config.spacing_seconds),
                **kwargs,
            )
        posteriors = {
            (c.configuration_id, group): learner.predict(c, group)
            for c in execution_configurations()
            for group in ("group-a", "group-b", "group-c", "group-d")
        }
        values = []
        for row_index, row in enumerate(result.observations[index:end], start=index):
            label = (
                int(row.outcome_status is OutcomeStatus.SUCCESS)
                if label_exclusion(row) is None
                and row.recorded_at <= evaluation_at
                and row.label_available_at is not None
                and row.label_available_at <= evaluation_at
                else None
            )
            value = _Prediction(
                posteriors[(row.configuration.configuration_id, row.task_group)],
                truth[row.source_record_id].success_probability,
                label,
            )
            values.append(value)
            if row_index >= tail_start:
                tail_values.append(value)
        all_values.extend(values)
        cells = tuple(
            DriftCell(
                p.configuration_id,
                p.task_group,
                p.sample_count,
                p.success_probability,
                p.lower,
                p.upper,
            )
            for p in posteriors.values()
        )
        blocks.append(
            DriftBlock(
                cutoff.isoformat(),
                (
                    config.start_at + timedelta(seconds=end * config.spacing_seconds)
                ).isoformat(),
                learner.training_summary.eligible_label_count,
                learner.window_summary.discarded_eligible_label_count
                if window is not None
                else 0,
                sum(cell.sample_count == 0 for cell in cells),
                cells,
                _metrics(values, bin_count),
            )
        )
    drift_end = (
        None
        if config.drift_at_index is None
        else (config.drift_at_index + (config.gradual_drift_steps or 0))
    )
    delay = None
    if drift_end is not None:
        for block_index in range(len(blocks) - 2):
            index = start + block_index * refit_steps
            if index < drift_end:
                continue
            if all(
                block.metrics.probability_mae is not None
                and block.metrics.probability_mae <= 0.1
                for block in blocks[block_index : block_index + 3]
            ):
                delay = float(index - drift_end)
                break
    return DriftBaselineRun(
        name,
        window,
        _metrics(all_values, bin_count),
        _metrics(tail_values, bin_count),
        delay,
        delay is not None,
        float(max(config.count - drift_end, 0)) if drift_end is not None else None,
        tuple(blocks),
    )


def run_drift_suite(
    *,
    seeds: Iterable[int] = range(20),
    count: int = 1000,
    window_steps: Iterable[int] = (120, 300),
    refit_steps: int = 50,
    calibration_bins: int = 10,
    scenarios: Iterable[StressScenario] | None = None,
) -> DriftSuiteReport:
    """Pure reproducible comparison; windows/refit cadence are fixed before scoring.

    Explicit scenarios supersede count. This simulation harness never writes a
    ledger, reads real records, or chooses an estimator from future scores.
    """
    seeds, windows = tuple(seeds), tuple(window_steps)
    if not seeds or any(isinstance(s, bool) or not isinstance(s, int) for s in seeds):
        raise ValueError("seeds must be nonempty integers")
    if len(set(seeds)) != len(seeds):
        raise ValueError("seeds must be distinct")
    if not windows or len(set(windows)) != len(windows):
        raise ValueError("window_steps must be nonempty and distinct")
    for window in windows:
        _positive_integer(window, "window_steps")
    _positive_integer(refit_steps, "refit_steps")
    _positive_integer(calibration_bins, "calibration_bins")
    scenarios = tuple(drift_scenarios(count=count) if scenarios is None else scenarios)
    if not scenarios or len({s.name for s in scenarios}) != len(scenarios):
        raise ValueError("scenarios must be nonempty with distinct names")
    reports = []
    for scenario in scenarios:
        runs = tuple(
            _run(scenario, seed, windows, refit_steps, calibration_bins)
            for seed in seeds
        )
        summaries = []
        for baseline_index, first in enumerate(runs[0].baselines):
            metrics = [run.baselines[baseline_index] for run in runs]
            differences = [
                metric.metrics.brier_score - run.baselines[0].metrics.brier_score
                for metric, run in zip(metrics, runs, strict=True)
                if metric.metrics.brier_score is not None
                and run.baselines[0].metrics.brier_score is not None
            ]
            has_drift = scenario.simulation.drift_at_index is not None
            summaries.append(
                DriftBaselineSummary(
                    first.name,
                    _distribution(m.metrics.brier_score for m in metrics),
                    _distribution(m.metrics.calibration_error for m in metrics),
                    _distribution(m.metrics.interval_coverage for m in metrics),
                    _distribution(
                        m.metrics.macro_cell_interval_coverage for m in metrics
                    ),
                    _distribution(m.metrics.interval_width for m in metrics),
                    _distribution(m.tail_metrics.brier_score for m in metrics),
                    _distribution(m.tail_metrics.interval_coverage for m in metrics),
                    _distribution(m.adaptation_delay_steps for m in metrics),
                    sum(m.adaptation_observed for m in metrics),
                    sum(not m.adaptation_observed for m in metrics) if has_drift else 0,
                    _distribution(differences),
                    sum(difference < 0 for difference in differences),
                )
            )
        reports.append(
            DriftScenarioReport(
                scenario.name, scenario.description, runs, tuple(summaries)
            )
        )
    return DriftSuiteReport(
        seeds, windows, refit_steps, calibration_bins, tuple(reports)
    )
