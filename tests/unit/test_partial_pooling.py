"""M6-A synthetic counts and fictional observations, freshly authored; no real data."""

import math
from dataclasses import replace
from datetime import timedelta
from fractions import Fraction

import pytest
from pydantic import ValidationError

from model_learner.domain.models import (
    DataSourceKind,
    ExecutionConfiguration,
    ResourceBudget,
)
from model_learner.learn import partial_pooling as pp
from model_learner.learn.estimator import BetaBernoulli
from model_learner.learn.prospective import ConfigurationMember
from tests.unit.test_advisory import request as advisory_request
from tests.unit.test_prospective import (
    CUTOFF,
    DATASET,
    HIGH,
    LOW,
    LOW2,
    T2,
    T3,
    T4,
    row,
)


def request(**changes):
    values = advisory_request().model_dump(exclude={"decision_policy"})
    return pp.PartialPoolingRequest(**(values | changes))


def predicted(result, configuration=LOW):
    return next(
        c
        for c in result.cells
        if c.configuration_id == configuration.configuration_id
        and c.task_group == "scalar"
    )


def weights(result, family="low", task_family="boundary"):
    return next(
        d
        for d in result.domains
        if (d.configuration_family, d.task_family) == (family, task_family)
    )


def test_cold_rational_reference_and_variance_decomposition():
    result = pp.partial_pool(request())
    cell = predicted(result)
    posterior = cell.posterior
    assert cell.status == "prior-only"
    assert [h.weight for h in weights(result).states] == [1 / 9] * 9
    assert posterior.mean == 0.5
    assert posterior.variance == pytest.approx(float(Fraction(133, 1782)), abs=1e-15)
    assert posterior.between_variance == pytest.approx(1 / 24)
    assert posterior.within_variance + posterior.between_variance == posterior.variance
    assert posterior.variance != pytest.approx(1 / 12)  # Not Beta(1,1).
    assert weights(result).effective_hyperstate_count == pytest.approx(9)


@pytest.mark.parametrize("success", [True, False])
def test_one_label_hand_derived_rational_reference(success):
    result = pp.partial_pool(request(), observations=[row(1, success=success)])
    posterior = predicted(result).posterior
    expected = Fraction(1157, 1782)
    assert posterior.mean == pytest.approx(
        float(expected if success else 1 - expected), abs=1e-14
    )
    assert posterior.variance == pytest.approx(
        float(Fraction(83125, 1587762)), abs=1e-14
    )
    for h in weights(result).states:
        assert h.weight == pytest.approx(
            2 * (h.mu if success else 1 - h.mu) / 9, abs=1e-14
        )


def test_empty_cell_borrows_only_in_explicit_domain():
    peer = row(1, configuration=LOW2)
    result = pp.partial_pool(request(), observations=[peer])
    cell = predicted(result)
    assert cell.status == "borrowing"
    assert cell.successes == cell.failures == 0
    assert weights(result).label_count == weights(result).populated_cell_count == 1
    assert cell.posterior.mean == pytest.approx(7 / 12)
    for other in (row(2, configuration=HIGH), row(3, task=T3, group="other-scalar")):
        separated = pp.partial_pool(request(), observations=[other])
        assert (
            predicted(separated).posterior
            == predicted(pp.partial_pool(request())).posterior
        )
    # Enumerating another empty candidate does not update hyperweights.
    smaller = pp.partial_pool(request(candidates=(LOW,)), observations=[peer])
    assert weights(smaller) == weights(result)


def test_separate_cells_versus_same_cell_likelihood():
    separate = pp.partial_pool(
        request(), observations=[row(1), row(2, configuration=LOW2, success=False)]
    )
    together = pp.partial_pool(request(), observations=[row(1), row(2, success=False)])
    for result, same in ((separate, False), (together, True)):
        likelihood = [
            mu * (1 - mu) * (k / (k + 1) if same else 1) for mu, k in pp.SUPPORT
        ]
        total = math.fsum(likelihood)
        assert [h.weight for h in weights(result).states] == pytest.approx(
            [v / total for v in likelihood], abs=1e-14
        )
    assert [v for _, v in weights(separate).kappa_marginal] == pytest.approx(
        [1 / 3] * 3
    )
    concentration = dict(weights(together).kappa_marginal)
    assert concentration[32] > concentration[8] > concentration[2]


def test_private_single_component_known_beta_reference():
    posterior = pp._mixture(((1.0, 2.0, 1.0),), 0.95)
    assert posterior.mean == pytest.approx(2 / 3)
    assert posterior.variance == pytest.approx(1 / 18)
    assert posterior.between_variance == 0
    assert posterior.lower.value == pytest.approx(math.sqrt(0.025), abs=1e-12)
    assert posterior.upper.value == pytest.approx(math.sqrt(0.975), abs=1e-12)


def density_integral(x, success, panels):
    """Independent Simpson density integral; no production CDF/weight helpers.

    Under theta=sin(t)^2, all endpoint exponents are nonnegative (a,b>=.5).
    Prior weights are 1/9; one-success weights are the analytic 2*mu/9.
    """
    stop = math.asin(math.sqrt(x))
    step = stop / panels
    components = []
    for mu in (0.25, 0.5, 0.75):
        for kappa in (2, 8, 32):
            a = mu * kappa + int(success)
            b = (1 - mu) * kappa
            w = 2 * mu / 9 if success else 1 / 9
            components.append(
                (
                    w,
                    a,
                    b,
                    math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)),
                )
            )

    def density(t):
        sine, cosine = math.sin(t), math.cos(t)
        return math.fsum(
            w * 2 * sine ** (2 * a - 1) * cosine ** (2 * b - 1) * normalizer
            for w, a, b, normalizer in components
        )

    return (
        step
        / 3
        * math.fsum(
            (
                density(0),
                density(stop),
                *((4 if i % 2 else 2) * density(i * step) for i in range(1, panels)),
            )
        )
    )


@pytest.mark.parametrize("success", [False, True])
def test_independent_density_integration_at_cdf_and_interval_endpoints(success):
    result = pp.partial_pool(request(), observations=[row(1)] if success else [])
    posterior = predicted(result).posterior
    components = tuple(
        (h.weight, h.mu * h.kappa + int(success), (1 - h.mu) * h.kappa)
        for h in weights(result).states
    )
    for x, target in (
        (posterior.lower.value, 0.025),
        (posterior.upper.value, 0.975),
        (0.2, None),
        (0.5, None),
        (0.8, None),
    ):
        coarse = density_integral(x, success, 4096)
        fine = density_integral(x, success, 8192)
        assert abs(coarse - fine) <= 1e-8
        assert abs(fine - pp._cdf(x, components)) <= 1e-7
        if target is not None:
            assert abs(fine - target) <= 1e-7


def test_small_homogeneous_heterogeneous_examples_against_unchanged_baselines():
    req = request()
    sparse = row(1)
    homogeneous = [sparse, *(row(i, task=T2, group="structured") for i in range(2, 12))]
    opposing = [
        sparse,
        *(row(i, task=T2, group="structured", success=False) for i in range(2, 12)),
    ]
    base = predicted(pp.partial_pool(req, observations=[sparse])).posterior.mean
    same = predicted(pp.partial_pool(req, observations=homogeneous)).posterior.mean
    other = predicted(pp.partial_pool(req, observations=opposing)).posterior.mean
    assert same > base > other
    abundant = [
        row(i, success=i <= 100)
        if i <= 100
        else row(i, task=T2, group="structured", success=False)
        for i in range(1, 201)
    ]
    result = pp.partial_pool(req, observations=abundant)
    direct = predicted(result)
    peer = next(c for c in result.cells if c.task_group == "structured")
    assert direct.posterior.mean > 0.9 and peer.posterior.mean < 0.1
    for aggregation, expected in (
        ("unpooled", 101 / 102),
        ("global", 0.5),
        ("per_arm", 0.5),
    ):
        reference = BetaBernoulli.fit(
            abundant,
            dataset=DATASET,
            cutoff=CUTOFF,
            acceptance_spec=req.task.acceptance_spec,
            aggregation=aggregation,
        ).predict(LOW, "scalar")
        assert reference.success_probability == expected
    assert predicted(result, LOW2).status == "borrowing"
    assert predicted(result, HIGH).status == "prior-only"


@pytest.mark.parametrize("field", ["decision_at", "recorded_at", "label_available_at"])
def test_cutoff_excludes_late_source_and_decision_equality(field):
    late = CUTOFF + timedelta(seconds=1)
    changes = {"recorded_at": late, field: late}
    if field == "decision_at":
        changes["label_available_at"] = late
    result = pp.partial_pool(request(), observations=[row(1, **changes)])
    assert result.eligible_source_count == 0
    assert dict(result.exclusions) == {"not_available_at_cutoff": 1}
    equal = row(2, decision_at=CUTOFF, label_available_at=CUTOFF, recorded_at=CUTOFF)
    assert pp.partial_pool(request(), observations=[equal]).eligible_source_count == 0
    at = row(3, label_available_at=CUTOFF, recorded_at=CUTOFF)
    assert pp.partial_pool(request(), observations=[at]).eligible_source_count == 1


def test_target_all_arms_dataset_and_membership():
    sources = [
        row(1, task=T4),
        row(2, task=T4, configuration=HIGH),
        row(3, dataset=DATASET.model_copy(update={"dataset_version": "2"})),
        row(
            4,
            source_kind="benchmark",
            dataset=DATASET.model_copy(
                update={"source_kind": DataSourceKind.BENCHMARK}
            ),
        ),
    ]
    result = pp.partial_pool(request(), observations=sources)
    assert result.eligible_source_count == 0
    assert dict(result.exclusions) == {"prediction_task": 2, "other_dataset": 2}
    with pytest.raises(ValueError, match="group contradicts"):
        pp.partial_pool(request(), observations=[row(5, group="structured")])


@pytest.mark.parametrize(
    "changes,reason",
    [
        ({"resource_budget": ResourceBudget(max_tokens=3)}, "other_target_or_budget"),
        (
            {
                "acceptance_spec": advisory_request().task.acceptance_spec.model_copy(
                    update={"version": "2"}
                )
            },
            "other_target_or_budget",
        ),
        (
            {"configuration": ExecutionConfiguration(model="unadmitted")},
            "not_admitted_by_policy",
        ),
        (
            {
                "outcome_status": "unknown",
                "label_available_at": None,
                "eligible_for_configuration_learning": False,
            },
            "missing_or_nonbinary_label",
        ),
        ({"verification_status": "unverified"}, "unverified_label"),
        ({"eligible_for_configuration_learning": False}, "ineligible_attribution"),
    ],
)
def test_label_and_contract_exclusions(changes, reason):
    result = pp.partial_pool(request(), observations=[row(1, **changes)])
    assert result.eligible_source_count == 0
    assert dict(result.exclusions) == {reason: 1}


def test_dedup_conflict_order_and_input_immutability():
    req = request()
    rows = [row(1), row(2, configuration=LOW2, success=False)]
    before = req.model_dump_json(), [r.model_dump_json() for r in rows]
    result = pp.partial_pool(req, observations=rows)
    assert result == pp.partial_pool(req, observations=reversed(rows))
    assert result == pp.partial_pool(
        request(candidates=tuple(reversed(req.candidates))), observations=rows
    )
    replay = pp.partial_pool(req, observations=[*rows, rows[0]])
    assert replay.cells == result.cells and replay.domains == result.domains
    assert dict(replay.exclusions) == {"duplicate": 1}
    with pytest.raises(ValueError, match="experimental unit"):
        pp.partial_pool(req, observations=[rows[0], row(3, run_id=rows[0].run_id)])
    assert before == (req.model_dump_json(), [r.model_dump_json() for r in rows])
    with pytest.raises(ValidationError):
        result.cells[0].posterior.mean = 0.9
    assert (
        pp.PartialPoolingResult.model_validate_json(result.model_dump_json()) == result
    )


@pytest.mark.parametrize(
    "change",
    [
        "budget",
        "acceptance",
        "group",
        "future",
        "empty",
        "candidate",
        "policy",
        "naive",
    ],
)
def test_invalid_target_contract(change):
    req = request()
    values = req.model_dump()
    if change == "budget":
        req.task.resource_budget = ResourceBudget(max_tokens=1)
    elif change == "acceptance":
        req.task.acceptance_spec.version = "2"
    elif change == "group":
        req.task.task_group = "different"
    elif change == "future":
        req.task.created_at = CUTOFF + timedelta(seconds=1)
    elif change == "empty":
        values["candidates"] = ()
    elif change == "candidate":
        values["candidates"] = (ExecutionConfiguration(model="other"),)
    elif change == "policy":
        values["policy"] = replace(
            req.policy, declared_at=CUTOFF + timedelta(seconds=1)
        )
    else:
        values["cutoff"] = CUTOFF.replace(tzinfo=None)
    if change in {"budget", "acceptance", "group", "future"}:
        values = req.model_dump()
    with pytest.raises(ValueError):
        pp.partial_pool(pp.PartialPoolingRequest(**values))


@pytest.mark.parametrize(
    "field,value",
    [
        ("model", "different"),
        ("reasoning_level", "high"),
        ("model_version", "v2"),
        ("configuration_version", "2"),
    ],
)
def test_incompatible_snapshots_cannot_share_family(field, value):
    values = LOW.model_dump(exclude={"configuration_id"}) | {field: value}
    cfg = ExecutionConfiguration(**values)
    with pytest.raises(ValueError, match="incompatible"):
        replace(
            request().policy,
            configurations=(
                ConfigurationMember(LOW.model_dump_json(), "same"),
                ConfigurationMember(cfg.model_dump_json(), "same"),
            ),
        )
    separate = replace(
        request().policy,
        configurations=(
            *(
                m
                for m in request().policy.configurations
                if m.configuration.configuration_id != cfg.configuration_id
            ),
            ConfigurationMember(cfg.model_dump_json(), "separate"),
        ),
    )
    result = pp.partial_pool(
        request(policy=separate, candidates=(cfg,)), observations=[row(1)]
    )
    assert (
        next(
            c for c in result.cells if c.configuration_id == cfg.configuration_id
        ).posterior.mean
        == 0.5
    )


def test_snapshot_revalidation_unknown_fields_and_benchmark_refusal():
    req = request()
    req.candidates[0].metadata["network"] = "changed"
    with pytest.raises(ValueError, match="invalid partial pooling"):
        pp.partial_pool(req)
    with pytest.raises(ValidationError):
        request(unrecognized=True)
    benchmark = replace(
        request().policy,
        dataset_json=DATASET.model_copy(
            update={"source_kind": DataSourceKind.BENCHMARK}
        ).model_dump_json(),
    )
    with pytest.raises(ValueError, match="benchmark"):
        pp.partial_pool(request(policy=benchmark))


@pytest.mark.parametrize(
    "label",
    [
        "/fictional/private/path",
        "https://fixture.invalid",
        "unreviewed prose",
        "sk-" + "z" * 25,
    ],
)
def test_public_label_refusal_does_not_echo(label):
    policy = replace(
        request().policy,
        tasks=tuple(replace(t, family=label) for t in request().policy.tasks),
    )
    with pytest.raises(ValueError) as error:
        pp.partial_pool(request(policy=policy))
    assert label not in str(error.value)


def test_metadata_prose_not_exported():
    req = request()
    req.task.description = "synthetic prose sentinel"
    req.task.metadata = {"locator": "/fictional/private/source"}
    source = row(1, metadata={"payload": "synthetic payload sentinel"})
    encoded = pp.partial_pool(req, observations=[source]).model_dump_json()
    for marker in (
        "synthetic prose",
        "synthetic payload",
        "/fictional/private",
        "network",
    ):
        assert marker not in encoded
    assert "selected_configuration" not in encoded


@pytest.mark.parametrize(
    "s,f", [(0, 0), (10000, 0), (0, 10000), (5000, 5000), (9999, 1)]
)
def test_legal_envelope_extremes_and_complement_symmetry(s, f):
    w = pp._weights({("cfg", "group"): (s, f)})
    components = tuple(
        (weight, mu * k + s, (1 - mu) * k + f)
        for (mu, k), weight in zip(pp.SUPPORT, w, strict=True)
    )
    posterior = pp._mixture(components, 0.95)
    reverse_w = pp._weights({("cfg", "group"): (f, s)})
    reflected = pp._mixture(
        tuple(
            (weight, mu * k + f, (1 - mu) * k + s)
            for (mu, k), weight in zip(pp.SUPPORT, reverse_w, strict=True)
        ),
        0.95,
    )
    assert posterior.mean == pytest.approx(1 - reflected.mean, abs=2e-12)
    assert posterior.variance == pytest.approx(reflected.variance, abs=2e-13)
    assert 0 <= posterior.lower.value < posterior.upper.value <= 1
    assert posterior.lower.value == pytest.approx(1 - reflected.upper.value, abs=2e-12)
    for q in (posterior.lower, posterior.upper):
        assert q.residual <= 1e-9 and q.bracket_width <= 1e-12 and q.iterations <= 64
    assert math.fsum(w) == pytest.approx(1, abs=1e-12)


@pytest.mark.parametrize(
    "counts",
    [
        {("c", "g"): (10001, 0)},
        {(str(i), "g"): (1, 0) for i in range(257)},
        {("c", "g"): (-1, 2)},
        {("c", "g"): (float("nan"), 0)},
        {("c", "g"): (True, 0)},
    ],
)
def test_count_refusals(counts):
    with pytest.raises(ValueError):
        pp._weights(counts)


@pytest.mark.parametrize(
    "components",
    [
        ((0.0, 1.0, 1.0),),
        ((float("nan"), 1.0, 1.0),),
        ((1.0, 0.4, 1.0),),
        ((1.0, 50001.0, 50000.0),),
        ((-1.0, 1.0, 1.0),),
        ((1.0, float("inf"), 1.0),),
    ],
)
def test_mixture_refusals(components):
    with pytest.raises(ValueError):
        pp._mixture(components, 0.95)


@pytest.mark.parametrize("mass", [0.49, 1, float("nan"), float("inf")])
def test_credible_mass_refusal(mass):
    with pytest.raises(ValueError):
        pp.partial_pool(request(credible_mass=mass))


def test_cdf_failure_propagates_without_fallback(monkeypatch):
    def fail(*args):
        raise ArithmeticError("synthetic CDF nonconvergence")

    monkeypatch.setattr(pp, "beta_cdf", fail)
    with pytest.raises(ArithmeticError, match="synthetic CDF nonconvergence"):
        pp.partial_pool(request())


def test_quantile_exhaustion_nonfinite_and_underflow_diagnostics(monkeypatch):
    with pytest.raises(ValueError):
        pp._quantile(float("nan"), ((1.0, 1.0, 1.0),))
    monkeypatch.setattr(pp, "beta_cdf", lambda *args: 0.5)
    with pytest.raises(ArithmeticError, match="64 iterations"):
        pp._mixture(((1.0, 1.0, 1.0),), 0.95)
    monkeypatch.setattr(pp, "beta_cdf", lambda *args: float("nan"))
    with pytest.raises(ArithmeticError, match="invalid mixture CDF"):
        pp._mixture(((1.0, 1.0, 1.0),), 0.95)
    # Independent normalization can underflow under the finite cell/label envelope.
    counts = {(str(i), "g"): (39, 0) for i in range(256)}
    w = pp._weights(counts)
    domain = pp._domain("cfg", "task", counts, w)
    assert domain.underflowed_components == sum(v == 0 for v in w)
    assert domain.effective_hyperstate_count >= 1


@pytest.mark.parametrize("mass", [0.5, 0.999])
@pytest.mark.parametrize("s,f", [(10000, 0), (0, 10000), (5000, 5000)])
def test_supported_mass_endpoints_at_label_limit(mass, s, f):
    ws = pp._weights({("c", "g"): (s, f)})
    posterior = pp._mixture(
        tuple(
            (w, mu * k + s, (1 - mu) * k + f)
            for (mu, k), w in zip(pp.SUPPORT, ws, strict=True)
        ),
        mass,
    )
    assert posterior.lower.value < posterior.upper.value
    assert max(posterior.lower.residual, posterior.upper.residual) <= 1e-9


def test_reimport_ties_choose_same_opaque_reference_and_bad_policy_revalidates():
    source = row(1)
    from uuid import UUID

    copy = source.model_copy(update={"observation_id": UUID(int=1)})
    left = pp.partial_pool(request(), observations=[source, copy])
    right = pp.partial_pool(request(), observations=[copy, source])
    assert left == right
    req = request()
    object.__setattr__(
        req.policy,
        "configurations",
        (*req.policy.configurations, req.policy.configurations[0]),
    )
    with pytest.raises(ValueError, match="invalid partial pooling request"):
        pp.partial_pool(req)


def test_finite_budget_and_scope_type_refusals():
    req = request()
    req.task.resource_budget = ResourceBudget(max_tokens=1)
    object.__setattr__(req.task.resource_budget, "max_duration_seconds", float("inf"))
    with pytest.raises(ValueError, match="invalid partial pooling request"):
        pp.partial_pool(req)
    with pytest.raises(ValueError, match="another source universe"):
        pp.partial_pool(request(), bundles=[object()])


@pytest.mark.parametrize("alias", ["schema", "metadata"])
def test_same_id_contradictory_source_snapshot_is_refused(alias):
    class MimicOff:
        def __str__(self):
            return "off"

    changes = (
        {"schema_version": 1}
        if alias == "schema"
        else {"metadata": {"network": MimicOff()}}
    )
    configuration = LOW.model_copy(update=changes)
    assert configuration.configuration_id == LOW.configuration_id
    assert configuration != LOW
    source = row(1, configuration=configuration)
    with pytest.raises(
        ValueError, match="source configuration contradicts admitted snapshot"
    ):
        pp.partial_pool(request(), observations=[source])


def test_exact_admitted_source_snapshot_preserves_counts_and_references():
    from uuid import UUID

    source = row(
        1,
        attempt_id=UUID(int=21),
        outcome_id=UUID(int=22),
        evidence_ids=(UUID(int=23),),
    )
    result = pp.partial_pool(request(), observations=[source])
    cell = predicted(result)
    assert result.eligible_source_count == cell.successes == 1
    reference = cell.evidence[0]
    for field in ("observation_id", "run_id", "attempt_id", "outcome_id"):
        assert getattr(reference, field) == str(getattr(source, field))
    assert reference.verification_ids == tuple(str(v) for v in source.evidence_ids)
    assert result.task_id == str(request().task.task_id)


@pytest.mark.parametrize(
    "field",
    [
        "observation_id",
        "run_id",
        "attempt_id",
        "outcome_id",
        "evidence_ids",
        "task_id",
        "target_task_id",
    ],
)
def test_uuid_subclass_reference_is_refused_without_echo(field):
    from uuid import UUID

    marker = "/synthetic/private/reference"

    class MarkerUUID(UUID):
        def __str__(self):
            return marker

    req = request()
    source = row(1)
    if field == "target_task_id":
        req.task.task_id = MarkerUUID(int=req.task.task_id.int)
    else:
        value = MarkerUUID(int=1)
        # Observation stable-key material intentionally excludes observation_id;
        # recompute for the other fields to reach the UUID boundary itself.
        source = row(1, **{field: (value,) if field == "evidence_ids" else value})
    with pytest.raises(ValueError) as error:
        pp.partial_pool(req, observations=[source])
    assert marker not in str(error.value)
    assert "canonical UUID" in str(error.value)
