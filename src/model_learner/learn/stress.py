"""Reproducible multi-seed stress evaluation of the fixed-prior references."""

from __future__ import annotations

import hashlib
import json
import math
import random
from collections.abc import Iterable, Mapping
from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from statistics import fmean, stdev
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, Field, model_validator

from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    ExecutionConfiguration,
    Observation,
    OutcomeStatus,
    Task,
)
from model_learner.learn.estimator import (
    Aggregation,
    BetaBernoulli,
    label_exclusion,
    matches_target,
    select_records,
)
from model_learner.learn.evaluation import (
    BaselineMetrics,
    CalibrationBin,
    EvaluationReport,
    evaluate,
)
from model_learner.learn.partial_pooling import PartialPoolingRequest, partial_pool
from model_learner.learn.prospective import (
    CompatibilityPolicy,
    ConfigurationMember,
    TaskMember,
)
from model_learner.simulate import (
    SimulationConfig,
    execution_configurations,
    generate,
)
from model_learner.simulate.generator import (
    SimulationResult,
    SimulationTruth,
    TruthRecord,
    _resource,
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


# Separate frozen stress-only path: the original simulator/default suite above
# retain their identities and random draw ordering. These are synthetic truths.
SELECTION_SEEDS = (11, 23, 37, 41, 53, 67, 71, 83, 97, 101, 113, 127)
SELECTION_MECHANISMS = ("selection_confounded", "assignment_control")
SELECTION_GROUPS = ("group-a", "group-b", "group-c", "group-d")
SELECTION_PROBABILITIES = (
    (0.20, 0.45, 0.70),
    (0.30, 0.55, 0.80),
    (0.40, 0.65, 0.90),
    (0.50, 0.75, 0.95),
)
SELECTION_ASSIGNMENT = (
    (0.05, 0.15, 0.80),
    (0.10, 0.20, 0.70),
    (0.70, 0.20, 0.10),
    (0.80, 0.15, 0.05),
)
SELECTION_START = datetime(2026, 1, 1, tzinfo=UTC)
SELECTION_METRICS = (
    "brier_score",
    "log_loss",
    "calibration_error",
    "truth_rmse",
    "truth_interval_coverage",
    "interval_width",
)


def _selection_stream(seed: int, name: str) -> random.Random:
    seed_bytes = f"selection-streams/v1:{seed}:{name}".encode()
    return random.Random(int.from_bytes(hashlib.sha256(seed_bytes).digest(), "big"))


def _selection_configurations() -> tuple[ExecutionConfiguration, ...]:
    # Explicit effort is required by the unchanged compatibility contract. Do
    # not change the original simulator configurations to add it globally.
    return tuple(
        ExecutionConfiguration(
            provider="synthetic",
            model=f"arm-{arm}",
            model_version="1",
            reasoning_level="synthetic",
            harness="selection-stress-only",
            harness_version="1",
        )
        for arm in "abc"
    )


def _selection_contract(mechanism: str, seed: int) -> dict:
    if (
        mechanism not in SELECTION_MECHANISMS
        or type(seed) is not int
        or seed not in SELECTION_SEEDS
    ):
        raise ValueError("unsupported frozen selection scenario or seed")
    return {
        "version": "selection-confounding-stress/v1",
        "mechanism": mechanism,
        "seed": seed,
        "seeds": SELECTION_SEEDS,
        "count": 120,
        "train_count": 72,
        "start_at": SELECTION_START.isoformat(),
        "spacing_seconds": 60,
        "verification_delay_seconds": 0,
        "unknown_probability": 0,
        "resource_missing_probability": 0,
        "group_probabilities": (0.25,) * 4,
        "assignment_probabilities": SELECTION_ASSIGNMENT
        if mechanism == "selection_confounded"
        else ((1 / 3,) * 3,) * 4,
        "probabilities": SELECTION_PROBABILITIES,
        "cost_means_usd": (0.02, 0.08, 0.2),
        "latency_means_seconds": (10, 25, 50),
        "resource_log_sigma": 0.3,
        "rng": "stdlib-random.Random-MT19937/random-streams/v1",
        "stream_seed": (
            "sha256(selection-streams/v1:seed:group|assignment|outcome|resources)"
        ),
        "group_draw": "floor(4*U)",
        "assignment_draw": "inverse-cumulative-probability",
        "outcome_draw": "U < cell probability",
        "resource_draw": "existing lognormal arithmetic-mean transform",
        "acceptance": TARGET.model_dump(mode="json"),
        "budget": None,
        "configurations": tuple(
            c.model_dump(mode="json") for c in _selection_configurations()
        ),
        "target_choice": (
            "first heldout decision per group; predeclared empty-group sentinel"
        ),
        "task_family": "selection-groups",
    }


def _selection_digest(value: object) -> str:
    return hashlib.sha256(
        json.dumps(
            value, sort_keys=True, separators=(",", ":"), allow_nan=False
        ).encode()
    ).hexdigest()


def _selection_task_id(fingerprint: str, index: int):
    return uuid5(NAMESPACE_URL, f"selection-task:{fingerprint}:{index}")


def _generate_selection(mechanism: str, seed: int) -> SimulationResult:
    """Exactly 120 rows; independent streams keep outcome draws assignment-stable."""
    contract = _selection_contract(mechanism, seed)
    fingerprint = _selection_digest(contract)
    dataset = DatasetReference(
        source_kind="simulated",
        dataset_id=f"selection-{mechanism}-seed-{seed}-{fingerprint}",
        dataset_version="1",
    )
    groups, assignments, outcomes, resources = (
        _selection_stream(seed, name)
        for name in ("group", "assignment", "outcome", "resources")
    )
    configurations = _selection_configurations()
    rows, truths = [], []
    for index in range(120):
        group = int(4 * groups.random())
        u = assignments.random()
        probabilities = contract["assignment_probabilities"][group]
        arm = (
            0
            if u < probabilities[0]
            else 1
            if u < probabilities[0] + probabilities[1]
            else 2
        )
        probability = SELECTION_PROBABILITIES[group][arm]
        success = outcomes.random() < probability
        cost = _resource(resources, contract["cost_means_usd"][arm], 0.3)
        latency = _resource(resources, contract["latency_means_seconds"][arm], 0.3)
        at = SELECTION_START + timedelta(seconds=index * 60)
        source_id = f"{fingerprint}:{index}"
        rows.append(
            Observation(
                observation_id=uuid5(
                    NAMESPACE_URL, f"selection-observation:{source_id}"
                ),
                source_kind="simulated",
                dataset=dataset,
                source_record_id=source_id,
                task_id=_selection_task_id(fingerprint, index),
                task_group=SELECTION_GROUPS[group],
                configuration=configurations[arm],
                acceptance_spec=TARGET,
                attribution_status="single_configuration",
                eligible_for_configuration_learning=True,
                outcome_status="success" if success else "failure",
                verification_status="verified",
                cost_usd=cost,
                latency_seconds=latency,
                decision_at=at,
                label_available_at=at,
                recorded_at=at,
                metadata={"measurement_source": "selection-stress-only/v1"},
            )
        )
        truths.append(
            TruthRecord(
                source_record_id=source_id,
                success_probability=probability,
                realized_success=success,
            )
        )
    return SimulationResult(
        observations=tuple(rows),
        truth=SimulationTruth(
            dataset=dataset, scenario_fingerprint=fingerprint, records=tuple(truths)
        ),
    )


def _selection_policy(
    mechanism: str, seed: int
) -> tuple[CompatibilityPolicy, tuple[Task, ...]]:
    contract = _selection_contract(mechanism, seed)
    fingerprint = _selection_digest(contract)
    dataset = DatasetReference(
        source_kind="simulated",
        dataset_id=f"selection-{mechanism}-seed-{seed}-{fingerprint}",
        dataset_version="1",
    )
    group_rng = _selection_stream(seed, "group")
    groups = [SELECTION_GROUPS[int(4 * group_rng.random())] for _ in range(120)]
    tasks = tuple(
        TaskMember(str(_selection_task_id(fingerprint, i)), group, "selection-groups")
        for i, group in enumerate(groups)
    )
    targets = tuple(
        Task(
            task_id=_selection_task_id(
                fingerprint,
                next((i for i in range(72, 120) if groups[i] == group), 120 + g),
            ),
            description="Predeclared synthetic heldout target",
            task_group=group,
            acceptance_spec=TARGET,
            created_at=SELECTION_START,
        )
        for g, group in enumerate(SELECTION_GROUPS)
    )
    extra = tuple(
        TaskMember(str(t.task_id), t.task_group, "selection-groups")
        for t in targets
        if str(t.task_id) not in {m.task_id for m in tasks}
    )
    return CompatibilityPolicy(
        "selection-compatibility/v1",
        SELECTION_START,
        dataset.model_dump_json(),
        TARGET.model_dump_json(),
        "null",
        tuple(
            ConfigurationMember(c.model_dump_json(), c.model)
            for c in _selection_configurations()
        ),
        (*tasks, *extra),
    ), targets


def _selection_admit(rows, policy, targets, cutoff):
    dataset = DatasetReference.model_validate_json(policy.dataset_json)
    selected, excluded = select_records(rows, dataset)
    members = {m.task_id: m for m in policy.tasks}
    snapshots = {
        m.configuration.configuration_id: m.configuration for m in policy.configurations
    }
    target_ids = {t.task_id for t in targets}
    train, held = [], []
    for row in selected:
        member = members.get(str(row.task_id))
        if member is None or row.configuration.configuration_id not in snapshots:
            excluded["not_admitted_by_policy"] += 1
        elif (
            row.task_group != member.group
            or row.configuration != snapshots[row.configuration.configuration_id]
        ):
            raise ValueError("selection source contradicts frozen membership")
        elif not matches_target(row, TARGET, None):
            excluded["other_target_or_budget"] += 1
        elif row.decision_at < cutoff and row.task_id in target_ids:
            excluded["prediction_task"] += 1
        elif (reason := label_exclusion(row)) is not None:
            excluded[reason] += 1
        elif row.decision_at < cutoff:
            if (
                row.recorded_at > cutoff
                or row.label_available_at is None
                or row.label_available_at > cutoff
            ):
                excluded["not_available_at_cutoff"] += 1
            else:
                train.append(row)
        else:
            held.append(row)
    return train, held, excluded


def _selection_bins(predictions, labels):
    bins = []
    for i in range(10):
        members = [
            (p, y)
            for p, y in zip(predictions, labels, strict=True)
            if min(int(p * 10), 9) == i
        ]
        bins.append(
            CalibrationBin(
                i / 10,
                (i + 1) / 10,
                len(members),
                fmean(p for p, _ in members) if members else None,
                fmean(y for _, y in members) if members else None,
            )
        )
    return tuple(bins)


def _selection_truth(values):
    # Equal unique represented cells, unlike assignment-weighted label scores.
    return {
        "truth_rmse": math.sqrt(fmean((p - t) ** 2 for p, _, _, t in values))
        if values
        else None,
        "truth_interval_coverage": fmean(lo <= t <= hi for _, lo, hi, t in values)
        if values
        else None,
        "interval_width": fmean(hi - lo for _, lo, hi, _ in values) if values else None,
    }


def _selection_run(result: SimulationResult, mechanism: str, seed: int) -> dict:
    """Shared-ID evaluation of existing APIs; simulator truth never enters a fit."""
    policy, targets = _selection_policy(mechanism, seed)
    dataset = DatasetReference.model_validate_json(policy.dataset_json)
    if (
        result.truth.dataset != dataset
        or result.truth.scenario_fingerprint
        != _selection_digest(_selection_contract(mechanism, seed))
    ):
        raise ValueError("selection result does not match frozen scenario")
    rows = tuple(
        Observation.model_validate(r.model_dump()) for r in result.observations
    )
    cutoff = SELECTION_START + timedelta(seconds=72 * 60)
    evaluation_at = SELECTION_START + timedelta(seconds=119 * 60)
    train, held, excluded = _selection_admit(rows, policy, targets, cutoff)
    report = evaluate(
        (*train, *held),
        dataset=dataset,
        train_until=cutoff,
        evaluation_at=evaluation_at,
        acceptance_spec=TARGET,
        training_observations=train,
        # Truth is scoring-only and limited to common admitted source IDs.
        truth=result.truth.model_copy(
            update={
                "records": tuple(
                    t
                    for t in result.truth.records
                    if t.source_record_id
                    in {r.source_record_id for r in (*train, *held)}
                )
            }
        ),
        calibration_bins=10,
    )
    by_id = {r.source_record_id: r for r in held}
    if report.held_out_count != len(held) or report.scored_label_count != len(held):
        raise ValueError("selection heldout labels are not jointly scoreable")
    truths = {t.source_record_id: t.success_probability for t in result.truth.records}
    held_keys = {(r.configuration.configuration_id, r.task_group) for r in held}
    configurations = _selection_configurations()
    grid = tuple(
        (c.configuration_id, g) for g in SELECTION_GROUPS for c in configurations
    )
    training_ids = tuple(sorted(r.source_record_id for r in train))
    held_ids = tuple(sorted(by_id))
    fit_digest, held_digest = (
        _selection_digest(training_ids),
        _selection_digest(held_ids),
    )
    predicted = {}
    methods = []
    for aggregation in AGGREGATIONS:
        learner = BetaBernoulli.fit(
            train,
            dataset=dataset,
            cutoff=cutoff,
            acceptance_spec=TARGET,
            aggregation=aggregation,
        )
        predicted[aggregation] = {
            (c.configuration_id, g): (p.success_probability, p.lower, p.upper)
            for c in configurations
            for g in SELECTION_GROUPS
            for p in (learner.predict(c, g),)
        }
    pp_cells = {}
    pp_exclusions = []
    stable_to_source = {r.stable_key: r.source_record_id for r in train}
    for target in targets:
        pooled = partial_pool(
            PartialPoolingRequest(
                task=target, candidates=configurations, policy=policy, cutoff=cutoff
            ),
            observations=train,
        )
        actual_ids = tuple(
            sorted(
                stable_to_source[e.stable_key]
                for cell in pooled.cells
                for e in cell.evidence
            )
        )
        if actual_ids != training_ids or pooled.eligible_source_count != len(train):
            raise ValueError(
                "partial pooling training identities differ from shared fit"
            )
        pp_exclusions.append(dict(pooled.exclusions))
        for cell in pooled.cells:
            if cell.task_group == target.task_group:
                p = cell.posterior
                pp_cells[cell.configuration_id, cell.task_group] = (
                    p.mean,
                    p.lower.value,
                    p.upper.value,
                )
    predicted["partial_pooling"] = pp_cells
    for name, cache in predicted.items():
        probabilities = [
            cache[r.configuration.configuration_id, r.task_group][0] for r in held
        ]
        labels = [int(r.outcome_status is OutcomeStatus.SUCCESS) for r in held]
        bins = _selection_bins(probabilities, labels)
        binary = {
            "brier_score": fmean(
                (p - y) ** 2 for p, y in zip(probabilities, labels, strict=True)
            )
            if labels
            else None,
            "log_loss": fmean(
                -y * math.log(max(1e-15, min(1 - 1e-15, p)))
                - (1 - y) * math.log1p(-max(1e-15, min(1 - 1e-15, p)))
                for p, y in zip(probabilities, labels, strict=True)
            )
            if labels
            else None,
        }
        if name in AGGREGATIONS:
            baseline = report.baselines[AGGREGATIONS.index(name)]
            if any(
                binary[k] is not None and abs(binary[k] - getattr(baseline, k)) > 1e-14
                for k in binary
            ):
                raise ArithmeticError(
                    "selection scoring disagrees with existing evaluation"
                )
            binary = {k: getattr(baseline, k) for k in binary}
            bins = baseline.calibration
        cell_values = []
        for key in sorted(held_keys):
            known = {
                truths[r.source_record_id]
                for r in held
                if (r.configuration.configuration_id, r.task_group) == key
            }
            if len(known) != 1:
                raise ValueError("selection cell truth is not stationary")
            cell_values.append((*cache[key], known.pop()))
        assignment_values = [
            (
                *cache[r.configuration.configuration_id, r.task_group],
                truths[r.source_record_id],
            )
            for r in held
        ]
        methods.append(
            {
                "method": name,
                "training_ids_digest": fit_digest,
                "heldout_ids_digest": held_digest,
                "training_count": len(train),
                "scored_label_count": len(labels),
                "represented_cell_count": len(held_keys),
                **binary,
                "calibration_error": _ece(bins),
                "calibration_bins": tuple(asdict(b) for b in bins),
                **_selection_truth(cell_values),
                "assignment_weighted_truth": _selection_truth(assignment_values),
                "cell_predictions": tuple(
                    {
                        "configuration_id": cid,
                        "task_group": group,
                        "probability": cache[cid, group][0],
                        "lower": cache[cid, group][1],
                        "upper": cache[cid, group][2],
                        "heldout_count": sum(
                            (r.configuration.configuration_id, r.task_group)
                            == (cid, group)
                            for r in held
                        ),
                    }
                    for cid, group in grid
                ),
            }
        )
    baseline = methods[0]
    return {
        "mechanism": mechanism,
        "seed": seed,
        "scenario": _selection_contract(mechanism, seed),
        "scenario_fingerprint": result.truth.scenario_fingerprint,
        "dataset": dataset.model_dump(mode="json"),
        "cutoff": cutoff.isoformat(),
        "evaluation_at": evaluation_at.isoformat(),
        "policy_fingerprint": policy.fingerprint,
        "target_task_ids": tuple(str(t.task_id) for t in targets),
        "training_count": len(train),
        "heldout_count": len(held),
        "scored_label_count": report.scored_label_count,
        "training_ids_digest": fit_digest,
        "heldout_ids_digest": held_digest,
        "exclusions": dict(sorted(excluded.items())),
        "evaluation_exclusions": report.exclusions,
        "training_exclusions": report.training.excluded,
        "partial_pooling_exclusions": tuple(pp_exclusions),
        "assignment_counts": tuple(
            {
                "task_group": g,
                "configuration_id": cid,
                "train": sum(
                    (r.configuration.configuration_id, r.task_group) == (cid, g)
                    for r in train
                ),
                "heldout": sum(
                    (r.configuration.configuration_id, r.task_group) == (cid, g)
                    for r in held
                ),
            }
            for cid, g in grid
        ),
        "methods": tuple(methods),
        "paired_minus_global": tuple(
            {
                "method": m["method"],
                **{
                    k: m[k] - baseline[k]
                    if m[k] is not None and baseline[k] is not None
                    else None
                    for k in SELECTION_METRICS
                },
            }
            for m in methods
        ),
    }


def run_selection_confounding(
    *,
    results: Mapping[tuple[str, int], SimulationResult] | None = None,
) -> dict:
    """Exactly the frozen 24-run increment; optional frozen rows permit replay.

    Supplied results must cover the full fixed experiment, not an extra campaign.
    No estimator can select an arm and no metric winner is required.
    """
    keys = tuple(
        (mechanism, seed)
        for mechanism in SELECTION_MECHANISMS
        for seed in SELECTION_SEEDS
    )
    if results is not None and set(results) != set(keys):
        raise ValueError("selection replay must contain exactly the frozen 24 runs")
    runs = tuple(
        _selection_run(
            _generate_selection(mechanism, seed)
            if results is None
            else results[mechanism, seed],
            mechanism,
            seed,
        )
        for mechanism, seed in keys
    )
    if any(
        (r["training_count"], r["heldout_count"], r["scored_label_count"])
        != (72, 48, 48)
        for r in runs
    ):
        raise ValueError("selection experiment requires the exact 120/72/48 split")
    summaries = []
    for mechanism in SELECTION_MECHANISMS:
        members = [r for r in runs if r["mechanism"] == mechanism]
        for i, method in enumerate(
            ("global", "per_arm", "unpooled", "partial_pooling")
        ):
            summaries.append(
                {
                    "mechanism": mechanism,
                    "method": method,
                    "metrics": {
                        k: asdict(_distribution(r["methods"][i][k] for r in members))
                        for k in SELECTION_METRICS
                    },
                    "paired_minus_global": {
                        k: asdict(
                            _distribution(
                                r["paired_minus_global"][i][k] for r in members
                            )
                        )
                        for k in SELECTION_METRICS
                    },
                }
            )
    return {
        "version": "selection-confounding-stress/v1",
        "seeds": SELECTION_SEEDS,
        "generated_row_count": 2880,
        "design": selection_design(),
        "runs": runs,
        "equal_seed_summaries": tuple(summaries),
        "method": (
            "All methods share eligible prefix IDs and heldout scored IDs. "
            "Binary scores/ECE "
            "weight heldout assignments; latent metrics weight unique "
            "represented heldout "
            "cells equally. Assignment-weighted latent diagnostics are also exposed. "
            "Sample seed variation is descriptive; repeated labels/cells are "
            "not independent "
            "replications. No causal estimate, adjustment, utility or model switching."
        ),
    }


def selection_design() -> dict:
    """Expected assignments are probabilities, never asserted observed counts."""
    rows = []
    for mechanism in SELECTION_MECHANISMS:
        assignment = (
            SELECTION_ASSIGNMENT
            if mechanism == "selection_confounded"
            else ((1 / 3,) * 3,) * 4
        )
        rows.append(
            {
                "mechanism": mechanism,
                "assignment_probabilities": assignment,
                "expected_counts_per_30_in_each_group": tuple(
                    tuple(30 * p for p in r) for r in assignment
                ),
                "assignment_weighted_latent_rate_by_arm": tuple(
                    math.fsum(
                        assignment[g][a] * SELECTION_PROBABILITIES[g][a]
                        for g in range(4)
                    )
                    / math.fsum(assignment[g][a] for g in range(4))
                    for a in range(3)
                ),
            }
        )
    return {
        "groups": SELECTION_GROUPS,
        "arms": ("arm-a", "arm-b", "arm-c"),
        "known_probability_matrix": SELECTION_PROBABILITIES,
        "equal_group_latent_rate_by_arm": tuple(
            fmean(SELECTION_PROBABILITIES[g][a] for g in range(4)) for a in range(3)
        ),
        "mechanisms": tuple(rows),
        "overlap": (
            "Every assignment probability is positive; minimum .05 in "
            "confounded design. Sparse realized cells may be zero."
        ),
    }
