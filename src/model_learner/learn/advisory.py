"""Offline, read-only presentation of existing estimators; never selects an arm.

Real-contract input is scoped evidence, not caller-asserted eligible rows. The
receipt resolver validates it in disposable storage without touching its source.
Simulated rows use declared times only. Benchmark resolution is unsupported here.
"""

from __future__ import annotations

import re
from collections import Counter
from collections.abc import Iterable
from dataclasses import asdict
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    DataSourceKind,
    ExecutionConfiguration,
    Observation,
    ResourceBudget,
    Task,
)
from model_learner.learn.estimator import (
    BetaBernoulli,
    label_exclusion,
    matches_target,
    require_aware,
    resource_summary,
    select_records,
)
from model_learner.learn.prospective import CompatibilityPolicy, forecast
from model_learner.storage.evidence import EvidenceBundle, resolve_bundle

VERSION = "configuration-advisory/v1"


def _public_label(value: str | None, *, version: bool = False) -> None:
    """Conservative identifier projection, matching the receipt sidecar approach."""
    if value is None:
        return
    pattern = r"[A-Za-z0-9_.:+-]{1,160}"
    if version:
        pattern = r"[A-Za-z0-9_.:+-]+(?:/[A-Za-z0-9_.:+-]+)?"
    if (
        not re.fullmatch(pattern, value)
        or ".." in value
        or re.search(r"(?:sk-|gh[pousr]_)[A-Za-z0-9_-]{16,}", value)
    ):
        raise ValueError("advisory requires reviewed public identifier labels")


class AdvisoryRequest(BaseModel):
    """Explicit target and frozen source universe; contains no execution request."""

    model_config = ConfigDict(extra="forbid")
    task: Task
    candidates: tuple[ExecutionConfiguration, ...]
    policy: CompatibilityPolicy
    cutoff: datetime
    # No selection policies are implemented or approved by this interface.
    decision_policy: str | None = None


class AdvisoryInput(BaseModel):
    """Versioned command input; never reads a default database or evidence path."""

    model_config = ConfigDict(extra="forbid")
    version: Literal["configuration-advisory-input/v1"] = (
        "configuration-advisory-input/v1"
    )
    request: AdvisoryRequest
    observations: tuple[Observation, ...] = ()
    bundles: tuple[EvidenceBundle, ...] = ()


def _reference(row: Observation) -> dict:
    return {
        "observation_id": str(row.observation_id),
        "stable_key": row.stable_key,
        "run_id": str(row.run_id) if row.run_id else None,
        "attempt_id": str(row.attempt_id) if row.attempt_id else None,
        "outcome_id": str(row.outcome_id) if row.outcome_id else None,
        "verification_ids": sorted(str(i) for i in row.evidence_ids),
    }


def advise(
    request: AdvisoryRequest,
    *,
    observations: Iterable[Observation] = (),
    bundles: Iterable[EvidenceBundle] = (),
) -> dict:
    """Return deterministic JSON-compatible estimates and explicit abstention.

    No clock reads, learner updates, saved forecasts, network or execution. Output
    deliberately projects identities/scalars, never descriptions or metadata.
    Callers must review identity labels before sharing; this is not a general
    secret scrubber. Real input is always resolved here through receipt gates.
    """
    # Revalidate mutable nested contracts and snapshot hashes at the boundary.
    request = AdvisoryRequest.model_validate_json(request.model_dump_json())
    task, policy, cutoff = request.task, request.policy, request.cutoff
    require_aware(cutoff, "advisory cutoff")
    dataset = DatasetReference.model_validate_json(policy.dataset_json)
    acceptance = AcceptanceSpec.model_validate_json(policy.acceptance_json)
    budget = (
        None
        if policy.budget_json == "null"
        else ResourceBudget.model_validate_json(policy.budget_json)
    )
    members = {m.task_id: m for m in policy.tasks}
    target = members.get(str(task.task_id))
    if (
        target is None
        or task.task_group != target.group
        or task.acceptance_spec != acceptance
        or task.resource_budget != budget
        or task.created_at > cutoff
        or policy.declared_at > cutoff
    ):
        raise ValueError("target or policy does not match the frozen advisory contract")
    ids = [c.configuration_id for c in request.candidates]
    approved = {m.configuration.configuration_id for m in policy.configurations}
    if not ids or len(set(ids)) != len(ids) or not set(ids) <= approved:
        raise ValueError("candidates must be distinct, explicitly admitted snapshots")
    for value in (
        dataset.dataset_id,
        dataset.dataset_version,
        acceptance.identifier,
        acceptance.version,
        target.group,
    ):
        _public_label(value)
    _public_label(policy.version, version=True)
    for configuration in request.candidates:
        for field in (
            "provider",
            "model",
            "model_version",
            "reasoning_level",
            "harness",
            "harness_version",
            "configuration_version",
        ):
            _public_label(getattr(configuration, field))

    rows, scopes = list(observations), list(bundles)
    excluded: Counter[str] = Counter()
    resolution_excluded: Counter[str] = Counter()
    limitations: set[str] = set()
    if dataset.source_kind is DataSourceKind.REAL:
        if rows:
            raise ValueError("real advisory requires scoped receipt evidence, not rows")
        seen: dict[UUID, EvidenceBundle] = {}
        for bundle in scopes:
            bundle = EvidenceBundle.model_validate_json(bundle.model_dump_json())
            if bundle.dataset != dataset:
                excluded["other_dataset_bundle"] += 1
                continue
            if str(bundle.task_id) not in members or bundle.task_id == task.task_id:
                excluded["unadmitted_or_target_task_bundle"] += 1
                continue
            if bundle.task_id in seen:
                if seen[bundle.task_id] != bundle:
                    raise ValueError("conflicting evidence snapshots for one task")
                excluded["duplicate_bundle"] += 1
                continue
            seen[bundle.task_id] = bundle
            snapshot = resolve_bundle(bundle, cutoff=cutoff)
            rows.extend(snapshot.observations)
            limitations.update(snapshot.availability_limitations)
            for item in snapshot.exclusions:
                resolution_excluded.update(item.reasons)
            # Missing receipts can hide whole runs before resolver enumeration.
            excluded["missing_receipt_entries"] += sum(
                e.received_at is None for e in bundle.entries
            )
            excluded["late_receipt_entries"] += sum(
                e.received_at is not None and e.received_at > cutoff
                for e in bundle.entries
            )
        availability = "receipt-gated-scoped-resolution/v1"
        limitations.add(
            "Imported receipts are declarations, not authenticated time attestations"
        )
    else:
        if scopes:
            raise ValueError(
                "scoped real evidence cannot be used in another source universe"
            )
        availability = "declared-source-timestamps-only/v1"
        limitations.add(
            "Declared timestamps do not establish historical receipt or authenticity"
        )
        if dataset.source_kind is DataSourceKind.BENCHMARK:
            # W4A.2 receipt coverage is not an eligible observation resolver.
            excluded["benchmark_resolution_not_supported"] += len(rows)
            if budget is not None:
                excluded["budget_measurements_not_supported"] += len(rows)
            rows = []
            limitations.add(
                "Benchmark receipt coverage cannot establish statistical eligibility"
            )

    visible = []
    for original in rows:
        row = Observation.model_validate(original.model_dump())
        if row.decision_at >= cutoff or row.recorded_at > cutoff:
            excluded["not_available_at_cutoff"] += 1
        else:
            visible.append(row)
    selected, duplicates = select_records(visible, dataset)
    excluded.update(duplicates)
    admitted = []
    for row in selected:
        member = members.get(str(row.task_id))
        if row.task_id == task.task_id:
            excluded["prediction_task"] += 1
        elif member is None or row.configuration.configuration_id not in approved:
            excluded["not_admitted_by_policy"] += 1
        elif row.task_group != member.group:
            raise ValueError("observation group contradicts frozen membership")
        elif not matches_target(row, acceptance, budget):
            excluded["other_target_or_budget"] += 1
        else:
            admitted.append(row)
    eligible = []
    for row in admitted:
        reason = label_exclusion(row)
        if reason:
            excluded[reason] += 1
        elif row.label_available_at is None or row.label_available_at > cutoff:
            excluded["label_not_available_at_cutoff"] += 1
        else:
            eligible.append(row)

    def estimate(name, probability, lower, upper, successes, failures, evidence):
        evidence = sorted(evidence, key=lambda r: r.stable_key)
        return {
            "predictor": name,
            "status": "available",
            "probability": probability,
            "lower": lower,
            "upper": upper,
            "credible_mass": 0.95,
            "successes": successes,
            "failures": failures,
            "eligible_count": successes + failures,
            "evidence": [_reference(r) for r in evidence],
            "resources": asdict(resource_summary(evidence)),
            "tokens": None,
        }

    candidates = []
    for configuration in request.candidates:
        estimates = []
        for name, aggregation, training in (
            ("fixed_prior", "global", []),
            ("global", "global", eligible),
            ("per_arm", "per_arm", eligible),
        ):
            posterior = BetaBernoulli.fit(
                training,
                dataset=dataset,
                cutoff=cutoff,
                acceptance_spec=acceptance,
                resource_budget=budget,
                aggregation=aggregation,
            ).predict(configuration, target.group)
            evidence = [
                r
                for r in training
                if aggregation == "global" or r.configuration == configuration
            ]
            estimates.append(
                estimate(
                    name,
                    posterior.success_probability,
                    posterior.lower,
                    posterior.upper,
                    posterior.successes,
                    posterior.failures,
                    evidence,
                )
            )
        bundle = forecast(
            eligible,
            policy=policy,
            task_id=task.task_id,
            # Pure forecast requires a run identity; this sentinel is never saved
            # or presented as a Run, and creates no canonical record.
            run_id=UUID(int=0),
            configuration=configuration,
            cutoff=cutoff,
        )
        for prediction in bundle.predictions:
            evidence = [r for r in eligible if r.stable_key in prediction.evidence_keys]
            estimates.append(
                estimate(
                    prediction.predictor,
                    prediction.probability,
                    prediction.lower,
                    prediction.upper,
                    prediction.successes,
                    prediction.failures,
                    evidence,
                )
            )
        candidates.append(
            {
                "configuration": {
                    k: getattr(configuration, k)
                    for k in (
                        "configuration_id",
                        "provider",
                        "model",
                        "reasoning_level",
                        "model_version",
                        "harness",
                        "harness_version",
                        "configuration_version",
                    )
                },
                "effective_backend_revision": None,
                "effective_backend_revision_basis": "declaration_only; not_established",
                "estimates": estimates,
            }
        )

    return {
        "version": VERSION,
        "task_id": str(task.task_id),
        "task_group": target.group,
        "dataset": dataset.model_dump(mode="json"),
        "acceptance": {
            "identifier": acceptance.identifier,
            "version": acceptance.version,
        },
        "resource_budget": budget.model_dump(mode="json") if budget else None,
        "cutoff": cutoff.isoformat(),
        "versions": {
            "estimator": "beta-bernoulli/fixed-beta-1-1/v1",
            "forecast": "prospective-forecast/v1",
            "compatibility_policy": policy.version,
            "policy_fingerprint": policy.fingerprint,
            "decision_policy": "abstain-only/v1",
        },
        "availability": {"method": availability, "limitations": sorted(limitations)},
        "exclusions": dict(sorted((k, v) for k, v in excluded.items() if v)),
        "resolution_exclusions": dict(sorted(resolution_excluded.items())),
        "eligible_source_count": len(eligible),
        "interval_interpretation": (
            "Conditional 95% Beta posterior intervals under the declared pooling "
            "assumptions; not guarantees of model superiority or calibration."
        ),
        "comparison": (
            "Descriptive estimates only; global intentionally pools admitted arms."
        ),
        "advisory": {
            "status": "abstain",
            "selected_configuration_id": None,
            "reason": (
                "unsupported_decision_policy"
                if request.decision_policy
                else "no_eligible_evidence_and_no_approved_decision_policy"
                if not eligible
                else "no_approved_decision_policy"
            ),
            "explanation": (
                "Human choice required; probability differences do not "
                "authorize selection."
            ),
        },
        "candidates": candidates,
    }
