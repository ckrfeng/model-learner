"""Explicit decision-age window around the unchanged fixed-prior estimator."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    Observation,
    ResourceBudget,
)
from model_learner.learn.estimator import (
    Aggregation,
    BetaBernoulli,
    label_exclusion,
    matches_target,
    require_aware,
    select_records,
)


@dataclass(frozen=True)
class WindowSummary:
    decision_start: str
    decision_end: str
    discarded_observation_count: int
    discarded_eligible_label_count: int


class RecentWindowBetaBernoulli(BetaBernoulli):
    """Fit Beta counts within [cutoff - duration, cutoff), using available labels.

    The window measures execution decision age, not label arrival age. A very old
    run verified today cannot masquerade as recent evidence. The Beta interval is
    conditional on a constant probability within this window; empirical coverage
    for current-time probabilities must be checked separately under drift.
    """

    @classmethod
    def fit(
        cls,
        observations: Iterable[Observation],
        *,
        window_duration: timedelta,
        dataset: DatasetReference,
        cutoff: datetime,
        acceptance_spec: AcceptanceSpec,
        resource_budget: ResourceBudget | None = None,
        prior_alpha: float = 1.0,
        prior_beta: float = 1.0,
        credible_mass: float = 0.95,
        aggregation: Aggregation = "unpooled",
    ) -> RecentWindowBetaBernoulli:
        require_aware(cutoff, "cutoff")
        if not isinstance(window_duration, timedelta) or window_duration <= timedelta(
            0
        ):
            raise ValueError("window_duration must be a positive timedelta")
        start = cutoff - window_duration
        # Resolve/deduplicate first so discarding cannot hide conflicting units.
        rows, exclusions = select_records(observations, dataset)
        discarded = [
            row
            for row in rows
            if row.decision_at < start
            and row.recorded_at <= cutoff
            and matches_target(row, acceptance_spec, resource_budget)
        ]
        discarded_keys = {row.stable_key for row in discarded}
        retained = [row for row in rows if row.stable_key not in discarded_keys]
        learner = super().fit(
            retained,
            dataset=dataset,
            cutoff=cutoff,
            acceptance_spec=acceptance_spec,
            resource_budget=resource_budget,
            prior_alpha=prior_alpha,
            prior_beta=prior_beta,
            credible_mass=credible_mass,
            aggregation=aggregation,
        )
        exclusions.update(learner.training_summary.excluded)
        if discarded:
            exclusions["outside_recent_window"] += len(discarded)
        learner.training_summary = replace(
            learner.training_summary, excluded=dict(exclusions)
        )
        learner.window_summary = WindowSummary(
            start.isoformat(),
            cutoff.isoformat(),
            len(discarded),
            sum(
                label_exclusion(row) is None
                and row.label_available_at is not None
                and row.label_available_at <= cutoff
                for row in discarded
            ),
        )
        return learner
