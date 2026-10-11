"""Window boundaries, label-arrival latency, missingness and deduplication."""

from datetime import timedelta
from uuid import uuid4

import pytest

from model_learner.domain.models import Observation, OutcomeStatus, VerificationStatus
from model_learner.learn.estimator import BetaBernoulli
from model_learner.learn.recent import RecentWindowBetaBernoulli
from tests.unit.test_learning import CONFIG, DATASET, START, TARGET, row


def fit(rows, **changes):
    return RecentWindowBetaBernoulli.fit(
        rows,
        **(
            dict(
                dataset=DATASET,
                cutoff=START + timedelta(seconds=10),
                acceptance_spec=TARGET,
                window_duration=timedelta(seconds=5),
            )
            | changes
        ),
    )


def test_inclusive_start_exclusive_end_and_honest_discard_counts():
    rows = [row(4), row(5), row(9, False), row(10)]
    learner = fit(rows)
    posterior = learner.predict(CONFIG, "group-a")
    assert (posterior.successes, posterior.failures) == (1, 1)
    assert learner.window_summary.discarded_observation_count == 1
    assert learner.window_summary.discarded_eligible_label_count == 1
    assert learner.training_summary.excluded["outside_recent_window"] == 1
    assert learner.training_summary.excluded["not_available_at_cutoff"] == 1


def test_delay_uses_decision_age_not_most_recent_arrival_and_no_future_leak():
    cutoff = START + timedelta(seconds=10)
    rows = [
        row(1, recorded_at=cutoff, label_available_at=cutoff),
        row(5),
        row(
            6,
            label_available_at=cutoff + timedelta(seconds=1),
            recorded_at=cutoff + timedelta(seconds=1),
        ),
        row(7, recorded_at=cutoff + timedelta(seconds=1)),
    ]
    learner = fit(rows)
    assert learner.predict(CONFIG, "group-a").sample_count == 1
    assert learner.window_summary.discarded_eligible_label_count == 1
    assert learner.training_summary.excluded["not_available_at_cutoff"] == 2


def test_missing_censored_and_expired_data_produce_prior_not_failures():
    rows = [
        row(0),
        row(
            6,
            outcome_status=OutcomeStatus.UNKNOWN,
            eligible_for_configuration_learning=False,
            label_available_at=None,
            verification_status=VerificationStatus.UNVERIFIED,
        ),
        row(
            7,
            outcome_status=OutcomeStatus.CENSORED,
            eligible_for_configuration_learning=False,
            label_available_at=None,
        ),
    ]
    learner = fit(rows)
    posterior = learner.predict(CONFIG, "group-a")
    assert posterior.sample_count == 0
    assert (posterior.lower, posterior.upper) == pytest.approx((0.025, 0.975))
    assert learner.training_summary.selected_count == 2
    assert learner.training_summary.resources.cost_usd.mean is None


def test_reimports_deduplicate_and_expired_conflicts_do_not_disappear():
    first = row(5)
    duplicate = Observation.model_validate(
        first.model_dump() | {"observation_id": uuid4()}
    )
    learner = fit([first, duplicate])
    assert learner.predict(CONFIG, "group-a").sample_count == 1
    assert learner.training_summary.excluded["duplicate"] == 1
    with pytest.raises(ValueError, match="experimental unit"):
        fit([row(1), row(1, False)])


def test_long_window_is_exactly_full_history_and_configuration_cells_separate():
    rows = [row(index, index % 2 == 0) for index in range(8)]
    recent = fit(rows, window_duration=timedelta(days=1))
    full = BetaBernoulli.fit(
        rows,
        dataset=DATASET,
        cutoff=START + timedelta(seconds=10),
        acceptance_spec=TARGET,
    )
    assert recent.predict(CONFIG, "group-a") == full.predict(CONFIG, "group-a")
    assert recent.training_summary == full.training_summary
    assert recent.predict(CONFIG, "new-group").sample_count == 0


@pytest.mark.parametrize("duration", [timedelta(0), timedelta(seconds=-1), 5, True])
def test_invalid_window(duration):
    with pytest.raises(ValueError, match="positive timedelta"):
        fit([], window_duration=duration)
