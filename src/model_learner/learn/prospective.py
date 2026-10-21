"""Small prospective experiment adapter; canonical records are never rewritten.

Compatibility is declared, not inferred from outcomes. Full pooling below is a
reference hypothesis, not a hierarchical model or evidence of compatibility.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from uuid import UUID

from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    ExecutionConfiguration,
    Observation,
    OutcomeStatus,
    ResourceBudget,
)
from model_learner.learn.estimator import (
    BetaBernoulli,
    label_exclusion,
    require_aware,
    select_records,
)


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


@dataclass(frozen=True)
class ConfigurationMember:
    snapshot_json: str
    family: str

    @property
    def configuration(self) -> ExecutionConfiguration:
        return ExecutionConfiguration.model_validate_json(self.snapshot_json)


@dataclass(frozen=True)
class TaskMember:
    task_id: str
    group: str
    family: str


@dataclass(frozen=True)
class CompatibilityPolicy:
    version: str
    declared_at: datetime
    dataset_json: str
    acceptance_json: str
    budget_json: str
    configurations: tuple[ConfigurationMember, ...]
    tasks: tuple[TaskMember, ...]

    def __post_init__(self) -> None:
        require_aware(self.declared_at, "policy declaration")
        if not self.version:
            raise ValueError("policy needs an explicit version")
        DatasetReference.model_validate_json(self.dataset_json)
        AcceptanceSpec.model_validate_json(self.acceptance_json)
        if self.budget_json != "null":
            ResourceBudget.model_validate_json(self.budget_json)
        families: dict[str, str] = {}
        ids = []
        for member in self.configurations:
            configuration = member.configuration
            if not member.family or not all(
                (
                    configuration.provider,
                    configuration.model,
                    configuration.reasoning_level,
                    configuration.harness,
                )
            ):
                raise ValueError(
                    "explicit family, provider, model, effort and harness required"
                )
            ids.append(configuration.configuration_id)
            values = configuration.model_dump(mode="json")
            for key in ("configuration_id", "schema_version", "harness_version"):
                values.pop(key)
            # Only these descriptive fields may differ without behavioral review.
            values["metadata"] = {
                k: v
                for k, v in values["metadata"].items()
                if k not in {"settings_source", "model_version_basis"}
            }
            signature = canonical(values)
            if member.family in families and families[member.family] != signature:
                raise ValueError("incompatible configurations in one family")
            families[member.family] = signature
        task_ids = [task.task_id for task in self.tasks]
        if len(set(ids)) != len(ids) or len(set(task_ids)) != len(task_ids):
            raise ValueError("duplicate policy membership")
        for task in self.tasks:
            UUID(task.task_id)
            if not task.group or not task.family:
                raise ValueError("task group and family required")
        groups: dict[str, str] = {}
        for task in self.tasks:
            if task.group in groups and groups[task.group] != task.family:
                raise ValueError("one narrow group cannot have conflicting families")
            groups[task.group] = task.family

    @property
    def fingerprint(self) -> str:
        return digest(
            canonical(asdict(self) | {"declared_at": self.declared_at.isoformat()})
        )


@dataclass(frozen=True)
class FrozenPrediction:
    predictor: str
    probability: float
    lower: float
    upper: float
    successes: int
    failures: int
    evidence_keys: tuple[str, ...]
    evidence_runs: tuple[str, ...]


@dataclass(frozen=True)
class ForecastBundle:
    version: str
    cutoff: str
    policy_fingerprint: str
    task_id: str
    run_id: str
    configuration_id: str
    task_group: str
    dataset_json: str
    acceptance_json: str
    budget_json: str
    predictions: tuple[FrozenPrediction, ...]
    exclusions: tuple[tuple[str, int], ...]


def forecast(
    observations: Iterable[Observation],
    *,
    policy: CompatibilityPolicy,
    task_id: UUID,
    run_id: UUID,
    configuration: ExecutionConfiguration,
    cutoff: datetime,
) -> ForecastBundle:
    """Pure calculation. Real rows must first undergo ledger evidence resolution."""
    require_aware(cutoff, "forecast cutoff")
    # Nested mutable domain metadata must still match its declared snapshot ID.
    configuration = ExecutionConfiguration.model_validate(configuration.model_dump())
    if policy.declared_at > cutoff:
        raise ValueError("policy was not available at prediction time")
    configurations = {
        m.configuration.configuration_id: m for m in policy.configurations
    }
    tasks = {t.task_id: t for t in policy.tasks}
    member = configurations.get(configuration.configuration_id)
    task = tasks.get(str(task_id))
    if member is None or task is None:
        raise ValueError("prediction target is not explicitly admitted by policy")
    dataset = DatasetReference.model_validate_json(policy.dataset_json)
    acceptance = AcceptanceSpec.model_validate_json(policy.acceptance_json)
    budget = (
        None
        if policy.budget_json == "null"
        else ResourceBudget.model_validate_json(policy.budget_json)
    )
    excluded: Counter[str] = Counter()
    visible = []
    for row in observations:
        if row.decision_at >= cutoff or row.recorded_at > cutoff:
            excluded["not_available_at_cutoff"] += 1
        else:
            visible.append(row)
    rows, duplicate_exclusions = select_records(visible, dataset)
    excluded.update(duplicate_exclusions)
    admitted = []
    for row in rows:
        prior_task = tasks.get(str(row.task_id))
        if row.task_id == task_id:
            excluded["prediction_task"] += 1
        elif (
            prior_task is None
            or row.configuration.configuration_id not in configurations
        ):
            excluded["not_admitted_by_policy"] += 1
        elif row.task_group != prior_task.group:
            raise ValueError("observation group contradicts frozen task membership")
        else:
            admitted.append(row)
    predictions = []
    for name in ("A", "B", "C"):
        selected = []
        for row in admitted:
            source = configurations[row.configuration.configuration_id]
            prior_task = tasks[str(row.task_id)]
            if name == "A":
                match = (
                    row.configuration.configuration_id == configuration.configuration_id
                    and prior_task.group == task.group
                )
            else:
                match = source.family == member.family and (
                    prior_task.group == task.group
                    if name == "B"
                    else prior_task.family == task.family
                )
            if match:
                selected.append(row)
        estimator = BetaBernoulli.fit(
            selected,
            dataset=dataset,
            cutoff=cutoff,
            acceptance_spec=acceptance,
            resource_budget=budget,
            aggregation="unpooled" if name == "A" else "global",
        )
        posterior = estimator.predict(configuration, task.group)
        # Reuse the learner's availability/target rules for the audit evidence list.
        evidence = [
            r
            for r in selected
            if label_exclusion(r) is None
            and r.label_available_at is not None
            and r.label_available_at <= cutoff
            and r.acceptance_spec is not None
            and (r.acceptance_spec.identifier, r.acceptance_spec.version)
            == (acceptance.identifier, acceptance.version)
            and r.resource_budget == budget
        ]
        predictions.append(
            FrozenPrediction(
                name,
                posterior.success_probability,
                posterior.lower,
                posterior.upper,
                posterior.successes,
                posterior.failures,
                tuple(sorted(r.stable_key for r in evidence if r.stable_key)),
                tuple(sorted(str(r.run_id) for r in evidence)),
            )
        )
        excluded.update(
            {f"{name}:{k}": v for k, v in estimator.training_summary.excluded.items()}
        )
    return ForecastBundle(
        "prospective-forecast/v1",
        cutoff.isoformat(),
        policy.fingerprint,
        str(task_id),
        str(run_id),
        str(configuration.configuration_id),
        task.group,
        policy.dataset_json,
        policy.acceptance_json,
        policy.budget_json,
        tuple(predictions),
        tuple(sorted(excluded.items())),
    )


def freeze(path: Path, bundle: ForecastBundle) -> str:
    """Exclusive creation; return digest for an external preparation manifest."""
    payload = canonical(asdict(bundle)) + "\n"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(payload)
    path.chmod(0o400)
    return digest(payload)


def score_frozen(path: Path, expected_sha256: str, outcome: Observation) -> dict:
    """Score a bound, independently resolved label without fitting or ledger writes."""
    payload = path.read_text(encoding="utf-8")
    if digest(payload) != expected_sha256:
        raise ValueError("frozen forecast digest mismatch")
    bundle = json.loads(payload)
    if (
        str(outcome.task_id),
        str(outcome.run_id),
        outcome.configuration.configuration_id,
        outcome.task_group,
    ) != (
        bundle["task_id"],
        bundle["run_id"],
        bundle["configuration_id"],
        bundle["task_group"],
    ):
        raise ValueError("outcome does not match the forecast execution")
    target = AcceptanceSpec.model_validate_json(bundle["acceptance_json"])
    budget = (
        None
        if bundle["budget_json"] == "null"
        else ResourceBudget.model_validate_json(bundle["budget_json"])
    )
    if (
        outcome.dataset != DatasetReference.model_validate_json(bundle["dataset_json"])
        or outcome.acceptance_spec is None
        or (outcome.acceptance_spec.identifier, outcome.acceptance_spec.version)
        != (target.identifier, target.version)
        or outcome.resource_budget != budget
    ):
        raise ValueError("outcome target, dataset or budget mismatch")
    cutoff = datetime.fromisoformat(bundle["cutoff"])
    if (
        label_exclusion(outcome) is not None
        or outcome.label_available_at is None
        or outcome.decision_at < cutoff
        or outcome.label_available_at <= cutoff
        or outcome.recorded_at <= cutoff
    ):
        raise ValueError("requires a verified binary outcome after the frozen forecast")
    y = int(outcome.outcome_status is OutcomeStatus.SUCCESS)
    return {
        p["predictor"]: {
            "brier_score": (p["probability"] - y) ** 2,
            "log_loss": -y * math.log(p["probability"])
            - (1 - y) * math.log1p(-p["probability"]),
        }
        for p in bundle["predictions"]
    }
