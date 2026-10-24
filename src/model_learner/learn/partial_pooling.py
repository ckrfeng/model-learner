"""Exact finite hierarchical inference; explicit offline evidence boundary only."""

from __future__ import annotations

import math
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
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
    OutcomeStatus,
    ResourceBudget,
    Task,
)
from model_learner.learn.advisory import _public_label
from model_learner.learn.estimator import (
    label_exclusion,
    matches_target,
    require_aware,
    select_records,
)
from model_learner.learn.numerics import MAX_BETA_SHAPE_SUM, beta_cdf
from model_learner.learn.prospective import CompatibilityPolicy
from model_learner.storage.evidence import EvidenceBundle, resolve_bundle

VERSION = "finite-hierarchical-beta-binomial/v1"
SUPPORT = tuple((mu, kappa) for mu in (0.25, 0.5, 0.75) for kappa in (2, 8, 32))
MAX_CELLS = 256
MAX_LABELS = 10_000


class _Frozen(BaseModel):
    model_config = ConfigDict(frozen=True, extra="forbid", hide_input_in_errors=True)


class PartialPoolingRequest(_Frozen):
    task: Task
    candidates: tuple[ExecutionConfiguration, ...]
    policy: CompatibilityPolicy
    cutoff: datetime
    credible_mass: float = 0.95


class Quantile(_Frozen):
    value: float
    residual: float
    iterations: int
    bracket_width: float


class Marginal(_Frozen):
    mean: float
    within_variance: float
    between_variance: float
    variance: float
    lower: Quantile
    upper: Quantile


class HyperState(_Frozen):
    mu: float
    kappa: int
    weight: float


class Domain(_Frozen):
    configuration_family: str
    task_family: str
    label_count: int
    populated_cell_count: int
    states: tuple[HyperState, ...]
    mu_marginal: tuple[tuple[float, float], ...]
    kappa_marginal: tuple[tuple[int, float], ...]
    mu_edge_mass: float
    kappa_edge_mass: float
    effective_hyperstate_count: float
    underflowed_components: int
    support_warning: str


class EvidenceReference(_Frozen):
    observation_id: str
    stable_key: str
    run_id: str | None
    attempt_id: str | None
    outcome_id: str | None
    verification_ids: tuple[str, ...]


class Cell(_Frozen):
    configuration_id: str
    task_group: str
    configuration_family: str
    task_family: str
    successes: int
    failures: int
    status: Literal["prior-only", "borrowing", "direct-and-pooled"]
    evidence: tuple[EvidenceReference, ...]
    posterior: Marginal


class ConfigurationIdentity(_Frozen):
    configuration_id: str
    provider: str | None
    model: str | None
    model_version: str | None
    reasoning_level: str | None
    harness: str | None
    harness_version: str | None
    configuration_version: str | None


class PartialPoolingResult(_Frozen):
    version: Literal["finite-hierarchical-beta-binomial/v1"] = VERSION
    prior: str = "mu uniform {1/4,1/2,3/4}; independent kappa uniform {2,8,32}"
    cutoff: str
    credible_mass: float
    dataset: tuple[tuple[str, str], ...]
    task_id: str
    task_group: str
    acceptance: tuple[tuple[str, str], ...]
    resource_budget: tuple[tuple[str, float | int | None], ...] | None
    policy_version: str
    policy_fingerprint: str
    candidate_ids: tuple[str, ...]
    configurations: tuple[ConfigurationIdentity, ...]
    domains: tuple[Domain, ...]
    cells: tuple[Cell, ...]
    eligible_source_count: int
    availability_method: str
    availability_limitations: tuple[str, ...]
    exclusions: tuple[tuple[str, int], ...]
    resolution_exclusions: tuple[tuple[str, int], ...]
    limitations: tuple[str, ...] = (
        "Exact finite hyperprior sum, not continuous hyperprior convergence",
        "Coarse support is a prior assumption, not established calibration",
        "Cells share hyperparameters within domains; marginals are not independent",
        "Intervals describe latent success probability; the mean predicts success",
        "Borrowing adds no direct observations or effective observation count",
        "No utility, configuration selection, cost or latency inference",
    )


def _uuid_reference(value: UUID | None) -> str | None:
    """Refuse subclass presentation hooks before identifiers reach public output."""
    if value is None:
        return None
    if type(value) is not UUID:
        raise ValueError("reference identifiers must be canonical UUID values")
    return str(value)


def _check_row_references(row: Observation) -> None:
    for value in (
        row.observation_id,
        row.task_id,
        row.run_id,
        row.attempt_id,
        row.outcome_id,
        *row.evidence_ids,
    ):
        _uuid_reference(value)


def _mass(value: float) -> None:
    if not math.isfinite(value) or not 0.5 <= value <= 0.999:
        raise ValueError("credible mass must be finite and in [0.5, 0.999]")


def _counts(counts: Mapping[tuple[str, str], tuple[int, int]]) -> None:
    for pair in counts.values():
        if len(pair) != 2 or any(type(n) is not int or n < 0 for n in pair):
            raise ValueError("cell counts must be nonnegative integers")
    populated = sum(sum(pair) > 0 for pair in counts.values())
    if populated > MAX_CELLS or sum(sum(pair) for pair in counts.values()) > MAX_LABELS:
        raise ValueError("domain exceeds 256 populated cells or 10000 eligible labels")


def _weights(counts: Mapping[tuple[str, str], tuple[int, int]]) -> tuple[float, ...]:
    """Pure sufficient-statistic kernel; omitted constants are not model scores."""
    _counts(counts)
    if not any(sum(pair) for pair in counts.values()):
        return (1 / 9,) * 9
    logs = []
    for mu, kappa in SUPPORT:
        a, b = mu * kappa, (1 - mu) * kappa
        logs.append(
            -math.log(9)
            + math.fsum(
                math.fsum(
                    (
                        math.lgamma(a + s),
                        math.lgamma(b + f),
                        -math.lgamma(a + b + s + f),
                        -math.lgamma(a),
                        -math.lgamma(b),
                        math.lgamma(a + b),
                    )
                )
                for key in sorted(counts)
                for s, f in (counts[key],)
                if s + f
            )
        )
    if not all(math.isfinite(v) for v in logs):
        raise ArithmeticError("nonfinite hyperstate likelihood")
    maximum = max(logs)
    scaled = tuple(math.exp(v - maximum) for v in logs)
    total = math.fsum(scaled)
    weights = tuple(v / total for v in scaled)
    _components(tuple((w, 0.5, 0.5) for w in weights))
    return weights


def _components(components: Sequence[tuple[float, float, float]]) -> None:
    if not components or any(
        not all(math.isfinite(v) for v in (w, a, b))
        or w < 0
        or a < 0.5
        or b < 0.5
        or a + b > MAX_BETA_SHAPE_SUM
        for w, a, b in components
    ):
        raise ValueError("invalid mixture weights or supported Beta shapes")
    if abs(math.fsum(w for w, _, _ in components) - 1) > 1e-12:
        raise ValueError("mixture weights must sum to one")


def _cdf(x: float, components: Sequence[tuple[float, float, float]]) -> float:
    value = math.fsum(w * beta_cdf(x, a, b) for w, a, b in components if w)
    if not math.isfinite(value) or not 0 <= value <= 1 + 1e-12:
        raise ArithmeticError("invalid mixture CDF")
    return value


def _quantile(p: float, components: Sequence[tuple[float, float, float]]) -> Quantile:
    if not math.isfinite(p) or not 0 < p < 1:
        raise ValueError("quantile probability must be finite and inside (0, 1)")
    lo, hi = 0.0, 1.0
    for iteration in range(1, 65):
        x = (lo + hi) / 2
        cdf = _cdf(x, components)
        if cdf < p:
            lo = x
        else:
            hi = x
        residual = abs(cdf - p)
        if hi - lo <= 1e-12 and residual <= 1e-9:
            return Quantile(
                value=x, residual=residual, iterations=iteration, bracket_width=hi - lo
            )
    raise ArithmeticError(
        "mixture quantile exhausted 64 iterations or residual tolerance"
    )


def _mixture(components: Sequence[tuple[float, float, float]], mass: float) -> Marginal:
    """Private one-or-more component arithmetic; public model always has nine."""
    _mass(mass)
    _components(components)
    mean = math.fsum(w * a / (a + b) for w, a, b in components)
    within = math.fsum(
        w * a * b / ((a + b) ** 2 * (a + b + 1)) for w, a, b in components
    )
    between = math.fsum(w * (a / (a + b) - mean) ** 2 for w, a, b in components)
    variance = math.fsum((within, between))
    if not all(math.isfinite(v) for v in (mean, within, between, variance)):
        raise ArithmeticError("nonfinite mixture moments")
    if variance < -1e-14:
        raise ArithmeticError("negative mixture variance")
    tail = (1 - mass) / 2
    return Marginal(
        mean=mean,
        within_variance=within,
        between_variance=between,
        variance=max(0.0, variance),
        lower=_quantile(tail, components),
        upper=_quantile(1 - tail, components),
    )


def _domain(family, task_family, counts, weights) -> Domain:
    mus = tuple(
        (
            m,
            math.fsum(
                w for (mu, _), w in zip(SUPPORT, weights, strict=True) if mu == m
            ),
        )
        for m in (0.25, 0.5, 0.75)
    )
    kappas = tuple(
        (
            k,
            math.fsum(
                w for (_, kap), w in zip(SUPPORT, weights, strict=True) if kap == k
            ),
        )
        for k in (2, 8, 32)
    )
    return Domain(
        configuration_family=family,
        task_family=task_family,
        label_count=sum(sum(pair) for pair in counts.values()),
        populated_cell_count=sum(sum(pair) > 0 for pair in counts.values()),
        states=tuple(
            HyperState(mu=m, kappa=k, weight=w)
            for (m, k), w in zip(SUPPORT, weights, strict=True)
        ),
        mu_marginal=mus,
        kappa_marginal=kappas,
        mu_edge_mass=math.fsum((mus[0][1], mus[-1][1])),
        kappa_edge_mass=math.fsum((kappas[0][1], kappas[-1][1])),
        effective_hyperstate_count=1 / math.fsum(w * w for w in weights),
        underflowed_components=sum(w == 0 for w in weights),
        support_warning=(
            "High edge mass warns of coarse prior support sensitivity; "
            "not numerical failure"
        ),
    )


def partial_pool(
    request: PartialPoolingRequest,
    *,
    observations: Iterable[Observation] = (),
    bundles: Iterable[EvidenceBundle] = (),
) -> PartialPoolingResult:
    """Resolve explicit evidence and integrate the fixed finite prior."""
    try:
        request = PartialPoolingRequest.model_validate(request.model_dump())
    except (ValueError, TypeError, AttributeError):
        raise ValueError("invalid partial pooling request contract") from None
    _mass(request.credible_mass)
    task, policy, cutoff = request.task, request.policy, request.cutoff
    require_aware(cutoff, "partial pooling cutoff")
    require_aware(task.created_at, "target creation")
    dataset = DatasetReference.model_validate_json(policy.dataset_json)
    acceptance = AcceptanceSpec.model_validate_json(policy.acceptance_json)
    budget = (
        None
        if policy.budget_json == "null"
        else ResourceBudget.model_validate_json(policy.budget_json)
    )
    if budget is not None and any(
        value is not None and not math.isfinite(value)
        for value in budget.model_dump(exclude={"schema_version"}).values()
    ):
        raise ValueError("resource budget must be finite")
    if dataset.source_kind is DataSourceKind.BENCHMARK:
        raise ValueError("benchmark partial pooling is unsupported")
    members = {m.task_id: m for m in policy.tasks}
    configs = {m.configuration.configuration_id: m for m in policy.configurations}
    target = members.get(_uuid_reference(task.task_id))
    if (
        target is None
        or task.task_group != target.group
        or task.acceptance_spec != acceptance
        or task.resource_budget != budget
        or task.created_at > cutoff
        or policy.declared_at > cutoff
    ):
        raise ValueError(
            "target or policy does not match frozen partial pooling contract"
        )
    ids = tuple(c.configuration_id for c in request.candidates)
    if not ids or len(set(ids)) != len(ids) or not set(ids) <= configs.keys():
        raise ValueError("candidates must be distinct explicitly admitted snapshots")
    for candidate in request.candidates:
        if candidate != configs[candidate.configuration_id].configuration:
            raise ValueError("candidate contradicts admitted snapshot")
    for value in (
        dataset.dataset_id,
        dataset.dataset_version,
        acceptance.identifier,
        acceptance.version,
    ):
        _public_label(value)
    _public_label(policy.version, version=True)
    for member in policy.tasks:
        _public_label(member.group)
        _public_label(member.family)
    for member in policy.configurations:
        _public_label(member.family)
        for field in ConfigurationIdentity.model_fields:
            _public_label(getattr(member.configuration, field))

    rows, scopes = list(observations), list(bundles)
    excluded: Counter[str] = Counter()
    resolution_excluded: Counter[str] = Counter()
    limitations: set[str] = set()
    if dataset.source_kind is DataSourceKind.REAL:
        if rows:
            raise ValueError(
                "real partial pooling requires scoped receipt evidence, not rows"
            )
        seen = {}
        for original in scopes:
            try:
                bundle = EvidenceBundle.model_validate_json(original.model_dump_json())
            except (ValueError, TypeError, AttributeError):
                raise ValueError("invalid scoped evidence contract") from None
            if bundle.dataset != dataset:
                excluded["other_dataset_bundle"] += 1
                continue
            if (
                _uuid_reference(bundle.task_id) not in members
                or bundle.task_id == task.task_id
            ):
                excluded["unadmitted_or_target_task_bundle"] += 1
                continue
            if bundle.task_id in seen:
                if seen[bundle.task_id] != bundle:
                    raise ValueError("conflicting evidence snapshots for one task")
                excluded["duplicate_bundle"] += 1
                continue
            seen[bundle.task_id] = bundle
        for key in sorted(seen, key=str):
            bundle = seen[key]
            snapshot = resolve_bundle(bundle, cutoff=cutoff)
            rows.extend(snapshot.observations)
            limitations.update(snapshot.availability_limitations)
            for item in snapshot.exclusions:
                resolution_excluded.update(item.reasons)
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
    visible = []
    for original in rows:
        try:
            row = Observation.model_validate(original.model_dump())
        except (ValueError, TypeError, AttributeError):
            raise ValueError("invalid observation contract") from None
        _check_row_references(row)
        for time in (row.decision_at, row.recorded_at, row.label_available_at):
            if time is not None:
                require_aware(time, "source timestamp")
        if row.decision_at >= cutoff or row.recorded_at > cutoff:
            excluded["not_available_at_cutoff"] += 1
        else:
            visible.append(row)
    visible.sort(
        key=lambda r: (
            r.decision_at,
            r.stable_key or "",
            r.recorded_at,
            _uuid_reference(r.observation_id),
        )
    )
    selected, duplicates = select_records(visible, dataset)
    excluded.update(duplicates)
    eligible = []
    for row in selected:
        member = members.get(_uuid_reference(row.task_id))
        if row.task_id == task.task_id:
            excluded["prediction_task"] += 1
        elif member is None or row.configuration.configuration_id not in configs:
            excluded["not_admitted_by_policy"] += 1
        elif (
            row.configuration
            != configs[row.configuration.configuration_id].configuration
        ):
            raise ValueError("source configuration contradicts admitted snapshot")
        elif row.task_group != member.group:
            raise ValueError("observation group contradicts frozen membership")
        elif not matches_target(row, acceptance, budget):
            excluded["other_target_or_budget"] += 1
        elif (reason := label_exclusion(row)) is not None:
            excluded[reason] += 1
        elif row.label_available_at is None or row.label_available_at > cutoff:
            excluded["label_not_available_at_cutoff"] += 1
        else:
            eligible.append(row)

    by_domain = defaultdict(dict)
    evidence = defaultdict(list)
    cell_domains = {}
    for row in eligible:
        key = (row.configuration.configuration_id, row.task_group)
        domain = (configs[key[0]].family, members[_uuid_reference(row.task_id)].family)
        cell_domains[key] = domain
        evidence[key].append(row)
        s, f = by_domain[domain].get(key, (0, 0))
        success = row.outcome_status is OutcomeStatus.SUCCESS
        by_domain[domain][key] = (s + int(success), f + int(not success))
    for cid in ids:
        key = (cid, target.group)
        domain = (configs[cid].family, target.family)
        cell_domains[key] = domain
        by_domain[domain].setdefault(key, (0, 0))
    domains, weight_map = [], {}
    for domain, counts in sorted(by_domain.items()):
        weights = _weights(counts)
        weight_map[domain] = weights
        domains.append(_domain(*domain, counts, weights))
    cells = []
    for key, domain in sorted(cell_domains.items()):
        s, f = by_domain[domain][key]
        peers = sum(sum(pair) for pair in by_domain[domain].values())
        references = tuple(
            EvidenceReference(
                observation_id=_uuid_reference(r.observation_id),
                stable_key=r.stable_key,
                run_id=_uuid_reference(r.run_id),
                attempt_id=_uuid_reference(r.attempt_id),
                outcome_id=_uuid_reference(r.outcome_id),
                verification_ids=tuple(
                    sorted(_uuid_reference(i) for i in r.evidence_ids)
                ),
            )
            for r in sorted(evidence[key], key=lambda r: r.stable_key)
        )
        cells.append(
            Cell(
                configuration_id=key[0],
                task_group=key[1],
                configuration_family=domain[0],
                task_family=domain[1],
                successes=s,
                failures=f,
                status="prior-only"
                if not peers
                else "borrowing"
                if not s + f
                else "direct-and-pooled",
                evidence=references,
                posterior=_mixture(
                    tuple(
                        (w, mu * k + s, (1 - mu) * k + f)
                        for (mu, k), w in zip(SUPPORT, weight_map[domain], strict=True)
                    ),
                    request.credible_mass,
                ),
            )
        )
    used = sorted({key[0] for key in cell_domains})
    return PartialPoolingResult(
        cutoff=cutoff.isoformat(),
        credible_mass=request.credible_mass,
        dataset=tuple(
            sorted(dataset.model_dump(mode="json", exclude={"schema_version"}).items())
        ),
        task_id=_uuid_reference(task.task_id),
        task_group=target.group,
        acceptance=(
            ("identifier", acceptance.identifier),
            ("version", acceptance.version),
        ),
        resource_budget=tuple(
            sorted(budget.model_dump(exclude={"schema_version"}).items())
        )
        if budget
        else None,
        policy_version=policy.version,
        policy_fingerprint=policy.fingerprint,
        candidate_ids=tuple(sorted(ids)),
        configurations=tuple(
            ConfigurationIdentity(
                **{
                    field: getattr(configs[cid].configuration, field)
                    for field in ConfigurationIdentity.model_fields
                }
            )
            for cid in used
        ),
        domains=tuple(domains),
        cells=tuple(cells),
        eligible_source_count=len(eligible),
        availability_method=availability,
        availability_limitations=tuple(sorted(limitations)),
        exclusions=tuple(sorted((k, v) for k, v in excluded.items() if v)),
        resolution_exclusions=tuple(sorted(resolution_excluded.items())),
    )
