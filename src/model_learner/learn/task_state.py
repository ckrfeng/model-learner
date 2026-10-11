"""Frozen checkpoint prediction experiment, separate from routing and ledger writes."""

from __future__ import annotations

import math
import random
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from statistics import fmean
from typing import Literal
from uuid import NAMESPACE_URL, uuid5

from pydantic import BaseModel, ConfigDict, model_validator

from model_learner.domain.models import (
    AcceptanceSpec,
    AttributionStatus,
    DatasetReference,
    DataSourceKind,
    Event,
    ExecutionConfiguration,
    Observation,
    OutcomeStatus,
    ResourceBudget,
    VerificationStatus,
)
from model_learner.execution.analyzer import extract_execution_checkpoints
from model_learner.execution.models import (
    ExecutionCheckpoint,
    ExecutionFacts,
    RepeatedFailure,
    StateInference,
    ToolObservation,
)
from model_learner.learn.estimator import label_exclusion, matches_target, require_aware
from model_learner.learn.evaluation import CalibrationBin

GROUPS = ("initial", "metrics", "state")
VARIANTS = {
    "A_initial": ("initial",),
    "B_initial_metrics": ("initial", "metrics"),
    "C_initial_metrics_state": GROUPS,
    "C_without_initial": ("metrics", "state"),
    "C_without_metrics": ("initial", "state"),
    "C_without_state": ("initial", "metrics"),
}


class TaskStateExample(BaseModel):
    """One explicitly available checkpoint and independently resolved final label.

    Input receipts are trusted declarations. Real labels must first be resolved
    and validated against the ledger; this portable experiment does not attest
    arbitrary caller-created observations or reconstruct historical revisions.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal["task-state-example/v1"] = "task-state-example/v1"
    observation: Observation
    checkpoint: ExecutionCheckpoint
    initial_available_at: datetime
    inputs_available_at: datetime
    events: tuple[Event, ...] | None = None

    @model_validator(mode="after")
    def validate_identity(self) -> TaskStateExample:
        row, point = self.observation, self.checkpoint
        for name in ("initial_available_at", "inputs_available_at"):
            require_aware(getattr(self, name), name)
        require_aware(point.checkpoint, "checkpoint")
        if row.task_id is None or row.run_id is None:
            raise ValueError("task-state examples require task and run identifiers")
        if point.task_id != row.task_id or point.run_id != row.run_id:
            raise ValueError("checkpoint and label task/run identifiers must agree")
        if point.checkpoint < row.decision_at:
            raise ValueError("checkpoint must not precede the initial decision")
        return self


@dataclass(frozen=True)
class Interval:
    lower: float | None
    upper: float | None
    method: str = "95% percentile task-cluster bootstrap, conditional on frozen fit"


@dataclass(frozen=True)
class VariantResult:
    name: str
    groups: tuple[str, ...]
    status: str
    training_count: int
    scored_count: int
    task_count: int
    feature_count: int
    brier_score: float | None
    brier_interval: Interval
    calibration: tuple[CalibrationBin, ...]
    predictions: tuple[tuple[str, float], ...]


@dataclass(frozen=True)
class PairedComparison:
    reference: str
    candidate: str
    scored_count: int
    task_count: int
    brier_improvement: float | None
    interval: Interval
    interpretation: str


@dataclass(frozen=True)
class TaskStateReport:
    dataset: dict[str, str]
    acceptance_spec: dict[str, str]
    resource_budget: dict | None
    train_until: str
    evaluation_at: str
    checkpoint_offset_seconds: float
    training_count: int
    held_out_count: int
    scored_count: int
    training_task_count: int
    scored_task_count: int
    exclusions: dict[str, int]
    variants: tuple[VariantResult, ...]
    comparisons: tuple[PairedComparison, ...]
    method: dict
    limitations: tuple[str, ...]


def _features(example: TaskStateExample, groups: tuple[str, ...]) -> dict[str, float]:
    """Allowlist only: labels, IDs, end resources and JUnit results never enter X."""
    result: dict[str, float] = {}
    row, facts = example.observation, example.checkpoint.facts
    if "initial" in groups:
        result[f"initial:task={row.task_group}"] = 1.0
        result[f"initial:configuration={row.configuration.configuration_id}"] = 1.0
    if "metrics" in groups:
        for name, value in (
            ("events", facts.event_count),
            ("tool_items", len(facts.tool_items)),
            ("started_turns", facts.started_turns),
            ("supported_events", facts.supported_event_count),
            *[
                (f"tokens_{key}", facts.token_usage.get(key))
                for key in ("input_tokens", "cached_input_tokens", "output_tokens")
            ],
        ):
            result[f"metrics:{name}:missing"] = float(value is None)
            if value is not None:
                if value < 0:
                    raise ValueError("execution metrics must be nonnegative")
                result[f"metrics:{name}"] = math.log1p(value)
    if "state" in groups:
        # Current analyzer JUnit evidence describes a final artifact. Neither
        # its criterion/test state nor terminal execution state is a predictor.
        for name, value in (
            ("failed_tools", facts.failed_tool_items),
            ("unknown_tools", facts.tool_items_with_unknown_failure),
            ("failed_turns", facts.failed_turns),
            ("repeated_failure_groups", len(facts.repeated_failures)),
            (
                "repeated_failure_items",
                sum(x.failed_items for x in facts.repeated_failures),
            ),
        ):
            if value < 0:
                raise ValueError("execution state counts must be nonnegative")
            result[f"state:{name}"] = math.log1p(value)
        result["state:failure_fraction"] = facts.failed_tool_items / max(
            1, facts.completed_tool_items
        )
        result["state:unknown_fraction"] = facts.tool_items_with_unknown_failure / max(
            1, len(facts.tool_items)
        )
    return result


@dataclass(frozen=True)
class _Fit:
    names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]

    def vector(self, features: dict[str, float]) -> list[float]:
        return [1.0] + [
            (features.get(name, 0.0) - mean) / scale
            for name, mean, scale in zip(
                self.names, self.means, self.scales, strict=True
            )
        ]

    def predict(self, features: dict[str, float]) -> float:
        return _sigmoid(
            sum(w * x for w, x in zip(self.weights, self.vector(features), strict=True))
        )


def _sigmoid(value: float) -> float:
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exp = math.exp(value)
    return exp / (1 + exp)


def _fit(rows: list[TaskStateExample], groups: tuple[str, ...]) -> _Fit:
    features = [_features(row, groups) for row in rows]
    names = tuple(sorted(set().union(*(row.keys() for row in features))))
    means = tuple(fmean(row.get(name, 0.0) for row in features) for name in names)
    scales = tuple(
        max(1.0, math.sqrt(fmean((row.get(name, 0.0) - mean) ** 2 for row in features)))
        for name, mean in zip(names, means, strict=True)
    )
    prototype = _Fit(names, means, scales, ())
    vectors = [prototype.vector(row) for row in features]
    labels = [
        int(row.observation.outcome_status is OutcomeStatus.SUCCESS) for row in rows
    ]
    weights = [0.0] * (len(names) + 1)
    # Fixed in advance, never selected on held-out scores. Convex regularized
    # logistic objective; fixed step scales with training design magnitude.
    step = 1 / (0.25 * max(sum(x * x for x in vector) for vector in vectors) + 0.05)
    for _ in range(400):
        gradients = [0.0] * len(weights)
        for vector, label in zip(vectors, labels, strict=True):
            error = (
                _sigmoid(sum(w * x for w, x in zip(weights, vector, strict=True)))
                - label
            )
            for index, value in enumerate(vector):
                gradients[index] += error * value / len(rows)
        for index in range(len(weights)):
            weights[index] -= step * (
                gradients[index] + (0.05 * weights[index] if index else 0)
            )
    return _Fit(names, means, scales, tuple(weights))


def _interval(values: list[float]) -> Interval:
    if not values:
        return Interval(None, None)
    values.sort()

    def quantile(probability: float) -> float:
        position = (len(values) - 1) * probability
        low = int(position)
        return values[low] + (position - low) * (
            values[min(low + 1, len(values) - 1)] - values[low]
        )

    return Interval(quantile(0.025), quantile(0.975))


def evaluate_task_state(
    examples: list[TaskStateExample] | tuple[TaskStateExample, ...],
    *,
    dataset: DatasetReference,
    acceptance_spec: AcceptanceSpec,
    train_until: datetime,
    evaluation_at: datetime,
    checkpoint_offset_seconds: float = 30,
    resource_budget: ResourceBudget | None = None,
    min_training: int = 30,
    min_scored: int = 20,
    bootstrap_replicates: int = 300,
    seed: int = 1,
    calibration_bins: int = 5,
) -> TaskStateReport:
    """Compare predeclared feature groups on one common frozen chronological cohort."""
    require_aware(train_until, "train_until")
    require_aware(evaluation_at, "evaluation_at")
    if evaluation_at <= train_until:
        raise ValueError("evaluation_at must follow train_until")
    if not math.isfinite(checkpoint_offset_seconds) or checkpoint_offset_seconds <= 0:
        raise ValueError("checkpoint offset must be finite and positive")
    for name, value, minimum in (
        ("min_training", min_training, 2),
        ("min_scored", min_scored, 2),
        ("bootstrap_replicates", bootstrap_replicates, 100),
        ("calibration_bins", calibration_bins, 1),
    ):
        if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
            raise ValueError(f"{name} must be an integer at least {minimum}")
    exclusions: Counter[str] = Counter()
    selected: list[TaskStateExample] = []
    seen: dict[str, TaskStateExample] = {}
    for example in examples:
        row, point = example.observation, example.checkpoint
        if row.dataset != dataset or row.source_kind != dataset.source_kind:
            exclusions["other_dataset"] += 1
            continue
        if not matches_target(row, acceptance_spec, resource_budget):
            exclusions["other_target_or_budget"] += 1
            continue
        cutoff = train_until if row.decision_at < train_until else evaluation_at
        if row.decision_at > evaluation_at or point.checkpoint > cutoff:
            exclusions["checkpoint_after_cutoff"] += 1
            continue
        if max(example.initial_available_at, example.inputs_available_at) > cutoff:
            exclusions["example_inputs_not_available"] += 1
            continue
        if row.recorded_at > cutoff:
            exclusions["observation_not_available"] += 1
            continue
        if point.analyzer_version != "codex-execution-checkpoints/v1":
            raise ValueError("unsupported checkpoint analyzer version")
        unit = str(row.run_id)
        if unit in seen:
            if seen[unit] != example:
                raise ValueError("conflicting or repeated checkpoints for one run")
            exclusions["duplicate_run"] += 1
            continue
        seen[unit] = example
        if point.checkpoint != row.decision_at + timedelta(
            seconds=checkpoint_offset_seconds
        ):
            exclusions["wrong_checkpoint_horizon"] += 1
        elif example.initial_available_at > row.decision_at:
            exclusions["initial_information_unavailable"] += 1
        elif example.inputs_available_at > point.checkpoint:
            exclusions["checkpoint_inputs_unavailable"] += 1
        elif (
            row.label_available_at is not None
            and row.label_available_at <= point.checkpoint
        ):
            exclusions["label_known_at_checkpoint"] += 1
        elif row.attribution_status is not AttributionStatus.SINGLE_CONFIGURATION:
            exclusions["incomplete_or_mixed_attribution"] += 1
        elif row.configuration.model is None:
            exclusions["unknown_model"] += 1
        elif (
            dataset.source_kind is not DataSourceKind.SIMULATED
            and example.events is None
        ):
            exclusions["checkpoint_event_evidence_required"] += 1
        else:
            if example.events is not None:
                bounded_events = [
                    event
                    for event in example.events
                    if event.observed_at >= row.decision_at
                    and (event.run_id is None or event.run_id == row.run_id)
                ]
                rebuilt = extract_execution_checkpoints(
                    bounded_events,
                    session_id=point.session_id,
                    checkpoints=[point.checkpoint],
                )[0]
                if rebuilt.facts != point.facts:
                    raise ValueError(
                        "checkpoint facts disagree with bounded event evidence"
                    )
            selected.append(example)
    # No retries of the same task may straddle fit and score. Task identity is
    # the conservative independence cluster, not a run/checkpoint row.
    training_tasks = {
        x.observation.task_id
        for x in selected
        if x.observation.decision_at < train_until
    }
    training: list[TaskStateExample] = []
    held_out: list[TaskStateExample] = []
    scored: list[TaskStateExample] = []
    for example in selected:
        row, point = example.observation, example.checkpoint
        training_row = row.decision_at < train_until
        cutoff = train_until if training_row else evaluation_at
        if not training_row and row.task_id in training_tasks:
            exclusions["task_overlaps_training"] += 1
            continue
        if point.checkpoint > cutoff:
            exclusions["checkpoint_after_cutoff"] += 1
            continue
        if not training_row:
            held_out.append(example)
        reason = label_exclusion(row)
        if reason is not None:
            exclusions[f"{'training' if training_row else 'score'}_{reason}"] += 1
        elif (
            row.label_available_at is None
            or row.label_available_at > cutoff
            or row.recorded_at > cutoff
        ):
            exclusions[
                f"{'training' if training_row else 'score'}_label_unavailable"
            ] += 1
        elif dataset.source_kind is not DataSourceKind.SIMULATED and (
            row.verification_status is not VerificationStatus.VERIFIED
            or not row.evidence_ids
        ):
            exclusions["independent_verified_evidence_required"] += 1
        else:
            (training if training_row else scored).append(example)
    task_ids = sorted({str(x.observation.task_id) for x in scored})
    positions = {
        task: [
            i for i, row in enumerate(scored) if str(row.observation.task_id) == task
        ]
        for task in task_ids
    }
    training_cluster_count = len({x.observation.task_id for x in training})
    sufficient = (
        len(training) >= min_training
        and len(scored) >= min_scored
        and training_cluster_count >= 5
        and len(task_ids) >= 5
        and len({x.observation.outcome_status for x in training}) == 2
    )
    bootstrap: list[list[int]] = []
    if sufficient:
        rng = random.Random(seed)
        bootstrap = [
            [
                index
                for task in rng.choices(task_ids, k=len(task_ids))
                for index in positions[task]
            ]
            for _ in range(bootstrap_replicates)
        ]
    variants: list[VariantResult] = []
    losses: dict[str, list[float]] = {}
    for name, groups in VARIANTS.items():
        predictions: list[float] = []
        fit = _fit(training, groups) if sufficient else None
        if fit is not None:
            predictions = [fit.predict(_features(row, groups)) for row in scored]
        labels = [
            int(row.observation.outcome_status is OutcomeStatus.SUCCESS)
            for row in scored
        ]
        loss = [
            (p - y) ** 2
            for p, y in zip(predictions, labels[: len(predictions)], strict=True)
        ]
        losses[name] = loss
        bins = []
        for index in range(calibration_bins):
            members = [
                (p, y)
                for p, y in zip(predictions, labels[: len(predictions)], strict=True)
                if min(int(p * calibration_bins), calibration_bins - 1) == index
            ]
            bins.append(
                CalibrationBin(
                    index / calibration_bins,
                    (index + 1) / calibration_bins,
                    len(members),
                    fmean(p for p, _ in members) if members else None,
                    fmean(y for _, y in members) if members else None,
                )
            )
        variants.append(
            VariantResult(
                name,
                groups,
                "evaluated" if sufficient else "insufficient_data",
                len(training),
                len(scored),
                len(task_ids),
                len(fit.names) if fit else 0,
                fmean(loss) if loss else None,
                _interval([fmean(loss[i] for i in sample) for sample in bootstrap]),
                tuple(bins),
                tuple(
                    (str(row.observation.run_id), p)
                    for row, p in zip(
                        scored[: len(predictions)], predictions, strict=True
                    )
                ),
            )
        )
    comparisons = []
    for reference, candidate in (
        ("A_initial", "B_initial_metrics"),
        ("B_initial_metrics", "C_initial_metrics_state"),
        *(
            (name, "C_initial_metrics_state")
            for name in VARIANTS
            if name.startswith("C_without")
        ),
    ):
        differences = [
            a - b for a, b in zip(losses[reference], losses[candidate], strict=True)
        ]
        interval = _interval(
            [fmean(differences[i] for i in sample) for sample in bootstrap]
        )
        comparisons.append(
            PairedComparison(
                reference,
                candidate,
                len(scored),
                len(task_ids),
                fmean(differences) if differences else None,
                interval,
                "insufficient_data"
                if not sufficient
                else "conditional evidence of lower Brier on this dataset"
                if interval.lower is not None and interval.lower > 0
                else "no resolved improvement on this dataset",
            )
        )
    return TaskStateReport(
        dataset.model_dump(mode="json", exclude={"schema_version"}),
        acceptance_spec.model_dump(
            mode="json", exclude={"schema_version", "description"}
        ),
        resource_budget.model_dump(mode="json", exclude={"schema_version"})
        if resource_budget
        else None,
        train_until.isoformat(),
        evaluation_at.isoformat(),
        checkpoint_offset_seconds,
        len(training),
        len(held_out),
        len(scored),
        training_cluster_count,
        len(task_ids),
        dict(exclusions),
        tuple(variants),
        tuple(comparisons),
        {
            "model": "fixed L2 logistic reference; ridge=0.05, 400 full-batch steps",
            "preprocessing": (
                "training-only vocabulary and mean/std; unseen categories "
                "ignored; log1p counts with missing indicators"
            ),
            "split": (
                "decision < train_until; checkpoint and labels available by "
                "fit/score cutoff; task clusters disjoint"
            ),
            "uncertainty": (
                "paired held-out task bootstrap; fixed training fit; 95% "
                "percentile intervals"
            ),
            "bootstrap_replicates": bootstrap_replicates,
            "seed": seed,
            "min_training": min_training,
            "min_scored": min_scored,
            "feature_groups": {name: list(groups) for name, groups in VARIANTS.items()},
        },
        (
            (
                "Final JUnit/test state, terminal execution state, outcomes "
                "and final resources are excluded from predictors."
            ),
            (
                "Input/config availability and label provenance are trusted "
                "external receipts; real observations require prior ledger "
                "resolution."
            ),
            (
                "Intervals condition on the fitted model; they omit "
                "training uncertainty and time dependence across different "
                "tasks."
            ),
            (
                "Exploratory ablations have no multiplicity correction; "
                "ECE/bin calibration is descriptive and sample dependent."
            ),
            (
                "Missing labels or unavailable horizons can select a "
                "nonrepresentative cohort; no causal model or real-utility "
                "claim."
            ),
        ),
    )


def load_task_state_examples(path: str) -> tuple[TaskStateExample, ...]:
    """Load an explicit JSON array; reject extra or unknown schema fields."""
    import json
    from pathlib import Path

    with Path(path).open(encoding="utf-8") as stream:
        values = json.load(stream)
    if not isinstance(values, list):
        raise ValueError("task-state input must be a JSON array")
    return tuple(TaskStateExample.model_validate(value) for value in values)


def generate_task_state_fixture(
    *,
    seed: int = 1,
    count: int = 400,
    scenario: Literal["state_signal", "null_signal"] = "state_signal",
) -> tuple[TaskStateExample, ...]:
    """Sanitized independent simulated tasks; no agent, commands or private data.

    Failure state is sampled first. Final acceptance is then drawn independently
    conditional on that state. No realized outcome is copied into a feature.
    Equal metric distributions ensure the signal group has distinct information.
    """
    if isinstance(count, bool) or not isinstance(count, int) or count < 0:
        raise ValueError("count must be a nonnegative integer")
    if scenario not in ("state_signal", "null_signal"):
        raise ValueError("unknown controlled scenario")
    rng = random.Random(seed)
    dataset = DatasetReference(
        source_kind=DataSourceKind.SIMULATED,
        dataset_id=f"task-state-{scenario}-seed-{seed}",
        dataset_version="1",
    )
    spec = AcceptanceSpec(identifier="controlled-task-acceptance", version="1")
    start = datetime(2026, 1, 1, tzinfo=UTC)
    examples = []
    for index in range(count):
        initial = start + timedelta(seconds=180 * index)
        task_id = uuid5(NAMESPACE_URL, f"{dataset.dataset_id}/task/{index}")
        run_id = uuid5(NAMESPACE_URL, f"{dataset.dataset_id}/run/{index}")
        session_id = uuid5(NAMESPACE_URL, f"{dataset.dataset_id}/session/{index}")
        model = rng.randrange(2)
        group = rng.randrange(2)
        struggling = rng.random() < 0.5
        event_count = rng.randrange(10, 30)
        probability = (
            (0.85 if not struggling else 0.15) if scenario == "state_signal" else 0.5
        )
        success = rng.random() < probability
        unknown = rng.random() < 0.05
        configuration = ExecutionConfiguration(
            provider="simulated",
            model=f"fixture-arm-{model}",
            model_version="1",
            harness="controlled-checkpoints",
            harness_version="1",
        )
        row = Observation(
            observation_id=uuid5(
                NAMESPACE_URL, f"{dataset.dataset_id}/observation/{index}"
            ),
            source_kind=DataSourceKind.SIMULATED,
            dataset=dataset,
            source_record_id=str(index),
            task_group=f"fixture-group-{group}",
            configuration=configuration,
            task_id=task_id,
            run_id=run_id,
            acceptance_spec=spec,
            attribution_status=AttributionStatus.SINGLE_CONFIGURATION,
            eligible_for_configuration_learning=not unknown,
            outcome_status=OutcomeStatus.UNKNOWN
            if unknown
            else OutcomeStatus.SUCCESS
            if success
            else OutcomeStatus.FAILURE,
            verification_status=VerificationStatus.UNVERIFIED
            if unknown
            else VerificationStatus.VERIFIED,
            decision_at=initial,
            label_available_at=None if unknown else initial + timedelta(seconds=120),
            recorded_at=initial + timedelta(seconds=120),
        )
        event_ids = tuple(
            uuid5(NAMESPACE_URL, f"{dataset.dataset_id}/event/{index}/{j}")
            for j in range(event_count)
        )
        tools = tuple(
            ToolObservation(
                capture_id=f"fixture-{seed}-{index}",
                item_id=f"item-{j}",
                tool_type="command_execution",
                event_ids=event_ids[j * 2 + 1 : j * 2 + 3],
                latest_event_id=event_ids[j * 2 + 2],
                observed_status="failed" if struggling and j < 3 else "completed",
                exit_code=1 if struggling and j < 3 else 0,
                started_observed=True,
                terminal_observed=True,
                failed=struggling and j < 3,
            )
            for j in range(4)
        )
        repeated = (
            (
                RepeatedFailure(
                    tool_type="command_execution",
                    failed_items=3,
                    event_ids=tuple(
                        tool.latest_event_id for tool in tools if tool.failed
                    ),
                    identity_basis="tool_category",
                ),
            )
            if struggling
            else ()
        )
        facts = ExecutionFacts(
            event_count=event_count,
            supported_event_count=event_count,
            unsupported_event_count=0,
            event_types={
                "turn.started": 1,
                "item.started": 4,
                "item.completed": 4,
                "turn.completed": 1,
                **({"item.updated": event_count - 10} if event_count > 10 else {}),
            },
            event_ids=event_ids,
            tool_items=tools,
            tool_events_missing_identity=0,
            completed_tool_items=4,
            failed_tool_items=3 if struggling else 0,
            tool_items_with_unknown_failure=0,
            started_turns=1,
            completed_turns=1,
            failed_turns=0,
            repeated_failures=repeated,
            token_usage={
                "input_tokens": rng.randrange(100, 1000),
                "output_tokens": rng.randrange(50, 300),
                "cached_input_tokens": None,
                "reasoning_output_tokens": None,
            },
            token_usage_coverage={
                "input_tokens": 1,
                "output_tokens": 1,
                "cached_input_tokens": 0,
                "reasoning_output_tokens": 0,
            },
        )
        point = ExecutionCheckpoint(
            checkpoint=initial + timedelta(seconds=30),
            session_id=session_id,
            run_id=run_id,
            task_id=task_id,
            facts=facts,
            execution_state=StateInference(
                state="completed_turn_observed",
                explanation="Controlled completed turn.",
            ),
            signals=tuple(
                StateInference(
                    state="repeated_tool_failures",
                    basis_event_ids=failure.event_ids,
                    explanation="Controlled observed distinct failed tools.",
                )
                for failure in repeated
            ),
            test_results=(),
            test_changes=(),
            test_state=StateInference(
                state="unknown", explanation="No final tests at checkpoint."
            ),
            diagnostics=(),
            limitations=("Synthetic projection, not native telemetry.",),
        )
        examples.append(
            TaskStateExample(
                observation=row,
                checkpoint=point,
                initial_available_at=initial,
                inputs_available_at=point.checkpoint,
            )
        )
    return tuple(examples)


def run_task_state_experiment(
    *,
    seeds: tuple[int, ...] = tuple(range(5)),
    count: int = 400,
    train_fraction: float = 0.6,
    bootstrap_replicates: int = 300,
) -> dict:
    """Independent seed replication in favorable and null controlled scenarios."""
    from dataclasses import asdict

    if len(set(seeds)) != len(seeds) or not seeds:
        raise ValueError("independent experiment seeds must be nonempty and unique")
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be in (0, 1)")
    output = {}
    for scenario in ("state_signal", "null_signal"):
        reports = []
        for seed in seeds:
            examples = generate_task_state_fixture(
                seed=seed, count=count, scenario=scenario
            )
            start = datetime(2026, 1, 1, tzinfo=UTC)
            dataset = DatasetReference(
                source_kind=DataSourceKind.SIMULATED,
                dataset_id=f"task-state-{scenario}-seed-{seed}",
                dataset_version="1",
            )
            report = evaluate_task_state(
                examples,
                dataset=dataset,
                acceptance_spec=AcceptanceSpec(
                    identifier="controlled-task-acceptance", version="1"
                ),
                train_until=start
                + timedelta(seconds=180 * int(count * train_fraction)),
                evaluation_at=start + timedelta(seconds=180 * count),
                bootstrap_replicates=bootstrap_replicates,
                seed=seed,
            )
            reports.append(report)
        seed_deltas = [r.comparisons[1].brier_improvement for r in reports]
        known = [value for value in seed_deltas if value is not None]
        output[scenario] = {
            "independent_seed_count": len(known),
            "requested_seed_count": len(seeds),
            "mean_state_brier_improvement": fmean(known) if known else None,
            "minimum_seed_improvement": min(known) if known else None,
            "maximum_seed_improvement": max(known) if known else None,
            "reports": [asdict(r) for r in reports],
        }
    return {
        "version": "task-state-experiment/v1",
        "count_per_seed": count,
        "train_fraction": train_fraction,
        "seeds": list(seeds),
        "scenarios": output,
        "interpretation": (
            "Designed simulation evidence only; seed spread is "
            "descriptive. No real predictive improvement established."
        ),
    }
