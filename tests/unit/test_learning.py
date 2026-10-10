"""Analytic posterior checks and honest temporal/data eligibility."""

import math
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest

from model_learner.domain.models import (
    AcceptanceSpec,
    AttributionStatus,
    DatasetReference,
    DataSourceKind,
    ExecutionConfiguration,
    Observation,
    OutcomeStatus,
    ResourceBudget,
    VerificationStatus,
)
from model_learner.learn import BetaBernoulli
from model_learner.learn.numerics import beta_cdf, beta_quantile

START = datetime(2026, 1, 1, tzinfo=UTC)
DATASET = DatasetReference(
    source_kind=DataSourceKind.SIMULATED, dataset_id="analytic", dataset_version="1"
)
TARGET = AcceptanceSpec(identifier="binary", version="1")
CONFIG = ExecutionConfiguration(provider="fixture", model="arm-a", harness="fixture")


def row(index: int, success: bool = True, **changes: object) -> Observation:
    values = dict(
        source_kind=DataSourceKind.SIMULATED,
        dataset=DATASET,
        source_record_id=f"record-{index}",
        task_group="group-a",
        configuration=CONFIG,
        acceptance_spec=TARGET,
        attribution_status=AttributionStatus.SINGLE_CONFIGURATION,
        eligible_for_configuration_learning=True,
        outcome_status=OutcomeStatus.SUCCESS if success else OutcomeStatus.FAILURE,
        verification_status=VerificationStatus.VERIFIED,
        decision_at=START + timedelta(seconds=index),
        label_available_at=START + timedelta(seconds=index + 1),
        recorded_at=START + timedelta(seconds=index + 1),
    )
    return Observation(**(values | changes))


def fit(rows: list[Observation], **changes: object) -> BetaBernoulli:
    return BetaBernoulli.fit(
        rows,
        **(
            dict(
                dataset=DATASET,
                cutoff=START + timedelta(days=1),
                acceptance_spec=TARGET,
            )
            | changes
        ),
    )


def test_hand_worked_beta_posterior_and_variance() -> None:
    posterior = fit([row(0), row(1), row(2, False)]).predict(CONFIG, "group-a")
    assert (posterior.successes, posterior.failures) == (2, 1)
    assert (posterior.alpha, posterior.beta) == (3, 2)
    assert posterior.success_probability == pytest.approx(3 / 5)
    assert posterior.variance == pytest.approx(3 * 2 / (5**2 * 6))
    assert beta_cdf(posterior.lower, 3, 2) == pytest.approx(0.025, abs=1e-11)
    assert beta_cdf(posterior.upper, 3, 2) == pytest.approx(0.975, abs=1e-11)


def test_zero_sparse_and_dense_uncertainty() -> None:
    empty = fit([]).predict(CONFIG, "group-a")
    sparse = fit([row(0)]).predict(CONFIG, "group-a")
    dense = fit([row(i, i % 2 == 0) for i in range(1000)]).predict(CONFIG, "group-a")
    assert empty.success_probability == 0.5
    assert (empty.lower, empty.upper) == pytest.approx((0.025, 0.975))
    assert sparse.lower == pytest.approx(math.sqrt(0.025))
    assert sparse.upper == pytest.approx(math.sqrt(0.975))
    assert sparse.upper - sparse.lower > 0.8
    assert dense.upper - dense.lower < 0.07
    unseen = fit([row(0)]).predict(CONFIG, "unseen-group")
    assert unseen == fit([]).predict(CONFIG, "unseen-group")


@pytest.mark.parametrize(
    "alpha,beta", [(1, 1), (1, 4), (4, 1), (2, 3), (500, 500), (0.5, 0.5)]
)
def test_numerical_beta_symmetry_and_analytic_integrals(
    alpha: float, beta: float
) -> None:
    for x in (0.02, 0.2, 0.5, 0.8, 0.98):
        assert beta_cdf(x, alpha, beta) + beta_cdf(1 - x, beta, alpha) == pytest.approx(
            1
        )
    if alpha == 1:
        assert beta_cdf(0.2, alpha, beta) == pytest.approx(1 - 0.8**beta)
    if beta == 1:
        assert beta_cdf(0.2, alpha, beta) == pytest.approx(0.2**alpha)
    if (alpha, beta) == (2, 3):
        assert beta_cdf(0.2, alpha, beta) == pytest.approx(
            6 * 0.2**2 - 8 * 0.2**3 + 3 * 0.2**4
        )
    if (alpha, beta) == (0.5, 0.5):
        assert beta_cdf(0.2, alpha, beta) == pytest.approx(
            2 * math.asin(math.sqrt(0.2)) / math.pi
        )
    for probability in (0.025, 0.5, 0.975):
        assert beta_cdf(
            beta_quantile(probability, alpha, beta), alpha, beta
        ) == pytest.approx(probability, abs=1e-10)


def test_only_verified_binary_eligible_labels_train() -> None:
    rows = [
        row(0),
        row(1, False),
        row(2, verification_status=VerificationStatus.UNVERIFIED),
        row(3, verification_status=VerificationStatus.PARTIALLY_VERIFIED),
        row(4, eligible_for_configuration_learning=False),
        row(
            5,
            eligible_for_configuration_learning=False,
            attribution_status=AttributionStatus.MIXED_CONFIGURATION,
        ),
        row(
            6,
            outcome_status=OutcomeStatus.UNKNOWN,
            eligible_for_configuration_learning=False,
            label_available_at=None,
        ),
        row(
            7,
            outcome_status=OutcomeStatus.CENSORED,
            eligible_for_configuration_learning=False,
            label_available_at=None,
        ),
    ]
    learner = fit(rows)
    assert learner.predict(CONFIG, "group-a").sample_count == 2
    assert learner.training_summary.selected_count == 8
    assert learner.training_summary.excluded["unverified_label"] == 2
    assert learner.training_summary.excluded["ineligible_attribution"] == 2
    assert learner.training_summary.excluded["missing_or_nonbinary_label"] == 2


def test_dataset_version_kind_target_budget_and_configuration_are_separate() -> None:
    other_dataset = DatasetReference(
        source_kind="benchmark", dataset_id="analytic", dataset_version="1"
    )
    other_version = DatasetReference(
        source_kind="simulated", dataset_id="analytic", dataset_version="2"
    )
    other_config = ExecutionConfiguration(
        provider="fixture", model="arm-a", harness="different"
    )
    rows = [
        row(0),
        row(1, source_kind="benchmark", dataset=other_dataset),
        row(2, dataset=other_version),
        row(3, acceptance_spec=AcceptanceSpec(identifier="binary", version="2")),
        row(4, resource_budget=ResourceBudget(max_tokens=50)),
        row(5, False, configuration=other_config),
    ]
    learner = fit(rows)
    assert learner.predict(CONFIG, "group-a").success_probability == pytest.approx(
        2 / 3
    )
    assert learner.predict(
        other_config, "group-a"
    ).success_probability == pytest.approx(1 / 3)
    assert learner.training_summary.excluded["other_dataset"] == 2
    assert learner.training_summary.excluded["other_target_or_budget"] == 2


def test_no_future_decision_label_or_record_leaks() -> None:
    cutoff = START + timedelta(seconds=10)
    rows = [
        row(0),
        row(
            1,
            label_available_at=cutoff + timedelta(seconds=1),
            recorded_at=cutoff + timedelta(seconds=1),
        ),
        row(2, recorded_at=cutoff + timedelta(seconds=2)),
        row(10),
    ]
    learner = fit(rows, cutoff=cutoff)
    assert learner.predict(CONFIG, "group-a").sample_count == 1
    assert learner.training_summary.selected_count == 1
    assert learner.training_summary.excluded["not_available_at_cutoff"] == 3


def test_reimports_deduplicate_and_conflicting_experimental_units_fail() -> None:
    first = row(0)
    duplicate = Observation.model_validate(
        first.model_dump()
        | {"observation_id": uuid4(), "recorded_at": START + timedelta(days=3)}
    )
    learner = fit([duplicate, first])
    assert learner.predict(CONFIG, "group-a").sample_count == 1
    assert learner.training_summary.excluded["duplicate"] == 1
    with pytest.raises(ValueError, match="experimental unit"):
        fit([row(0), row(0, False)])
    with pytest.raises(ValueError, match="identifier"):
        fit([first, row(1, observation_id=first.observation_id)])


def test_resource_summaries_include_failed_and_unknown_executions() -> None:
    rows = [
        row(0, cost_usd=0, latency_seconds=10),
        row(1, False, cost_usd=4, latency_seconds=None),
        row(
            2,
            outcome_status=OutcomeStatus.UNKNOWN,
            eligible_for_configuration_learning=False,
            label_available_at=None,
            cost_usd=None,
            latency_seconds=20,
        ),
    ]
    summary = fit(rows).predict(CONFIG, "group-a").resources
    assert summary.observation_count == 3
    assert summary.cost_usd.known_count == 2
    assert summary.cost_usd.missing_count == 1
    assert summary.cost_usd.mean == 2
    assert summary.latency_seconds.mean == 15
    assert fit([]).training_summary.resources.cost_usd.mean is None


@pytest.mark.parametrize(
    "changes",
    [
        {"prior_alpha": 0},
        {"prior_beta": -1},
        {"prior_alpha": math.inf},
        {"credible_mass": 1},
        {"credible_mass": math.nan},
        {"cutoff": datetime(2026, 1, 1)},
    ],
)
def test_invalid_statistical_inputs_fail(changes: dict) -> None:
    with pytest.raises(ValueError):
        fit([], **changes)


def test_numerical_scale_boundary_and_unsupported_priors_fail_explicitly() -> None:
    assert beta_cdf(0.5, 50_000, 50_000) == pytest.approx(0.5, abs=1e-9)
    lower = beta_quantile(0.025, 50_000, 50_000)
    assert beta_cdf(lower, 50_000, 50_000) == pytest.approx(0.025, abs=1e-9)
    for changes in (
        {"prior_alpha": 500_000, "prior_beta": 500_000},
        {"prior_alpha": 1e308, "prior_beta": 1e308},
        {"prior_alpha": 0.001},
    ):
        with pytest.raises(ValueError, match="supported"):
            fit([], **changes)
    with pytest.raises(ValueError, match="posterior shape sum"):
        fit([row(0)], prior_alpha=50_000, prior_beta=50_000)
    with pytest.raises(ValueError, match="shape sum"):
        beta_cdf(0.5, 500_000, 500_000)


@pytest.mark.parametrize("mass", [0.5, 0.999])
def test_supported_credible_mass_boundaries(mass: float) -> None:
    posterior = fit([], credible_mass=mass).predict(CONFIG, "group-a")
    assert posterior.lower == pytest.approx((1 - mass) / 2, abs=1e-13)
    assert posterior.upper == pytest.approx((1 + mass) / 2, abs=1e-13)
    skewed = fit([], prior_alpha=0.5, prior_beta=99_999.5, credible_mass=mass).predict(
        CONFIG, "group-a"
    )
    assert beta_cdf(skewed.lower, skewed.alpha, skewed.beta) == pytest.approx(
        (1 - mass) / 2, abs=1e-8
    )
    assert beta_cdf(skewed.upper, skewed.alpha, skewed.beta) == pytest.approx(
        (1 + mass) / 2, abs=1e-8
    )
    for unsupported in (0.499, 0.9991, math.nextafter(1, 0)):
        with pytest.raises(ValueError, match="credible mass"):
            fit([], credible_mass=unsupported)
