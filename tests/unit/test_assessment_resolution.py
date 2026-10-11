"""Revision selection uses visible lineage, never future labels or UUID priority."""

from datetime import UTC, datetime, timedelta
from itertools import permutations
from uuid import UUID

import pytest

from model_learner.domain.models import Outcome
from model_learner.observations.resolution import resolve_assessment

TIME = datetime(2026, 10, 10, 12, tzinfo=UTC)
RUN = UUID(int=1)


def outcome(number: int, *, minute: int = 0, parent: int | None = None, **kwargs):
    return Outcome(
        outcome_id=UUID(int=number),
        run_id=kwargs.pop("run_id", RUN),
        status=kwargs.pop("status", "unknown"),
        verification_status="unverified",
        assessment_source="human_assessment",
        recorded_at=TIME + timedelta(minutes=minute),
        supersedes_outcome_id=UUID(int=parent) if parent is not None else None,
        **kwargs,
    )


def test_chain_reconstruction_inclusive_cutoff_and_input_order() -> None:
    a = outcome(10)
    b = outcome(11, minute=1, parent=10, status="success")
    c = outcome(12, minute=2, parent=11, status="censored", censor_reason="withdrawn")
    for records in permutations((a, b, c)):
        assert resolve_assessment(records, run_id=RUN, cutoff=TIME).outcome == a
        assert (
            resolve_assessment(
                records, run_id=RUN, cutoff=TIME + timedelta(minutes=1)
            ).outcome
            == b
        )
        final = resolve_assessment(records, run_id=RUN, cutoff=c.recorded_at)
        assert final.outcome == c
        assert final.visible_outcome_ids == (a.outcome_id, b.outcome_id, c.outcome_id)
        assert not final.issues
    assert a.status.value == "unknown" and b.status.value == "success"


def test_future_branch_does_not_invalidate_historical_resolution() -> None:
    a = outcome(10)
    b = outcome(11, minute=1, parent=10)
    future = outcome(12, minute=2, parent=10, status="failure")
    at_b = resolve_assessment((a, b, future), run_id=RUN, cutoff=b.recorded_at)
    assert at_b.outcome == b and not at_b.issues
    final = resolve_assessment((future, b, a), run_id=RUN, cutoff=future.recorded_at)
    assert final.outcome is None
    assert final.issues == ("branching_supersession",)


@pytest.mark.parametrize(
    ("records", "issue"),
    [
        ([outcome(10), outcome(11)], "multiple_assessment_roots"),
        ([outcome(11, parent=99)], "missing_or_unavailable_parent"),
        ([outcome(11, parent=10), outcome(10, run_id=UUID(int=2))], "foreign_parent"),
        ([outcome(10, minute=1), outcome(11, parent=10)], "revision_predates_parent"),
        ([outcome(10, parent=10)], "cyclic_supersession"),
        ([outcome(10, parent=11), outcome(11, parent=10)], "cyclic_supersession"),
        ([outcome(10), outcome(10, status="failure")], "conflicting_outcome_identity"),
    ],
)
def test_malformed_visible_lineage_fails_closed(records, issue: str) -> None:
    state = resolve_assessment(records, run_id=RUN, cutoff=TIME + timedelta(minutes=3))
    assert state.outcome is None and issue in state.issues


def test_future_parent_is_indistinguishable_from_missing_parent() -> None:
    child = outcome(11, parent=10)
    future_parent = outcome(10, minute=1, status="success")
    missing = resolve_assessment((child,), run_id=RUN, cutoff=TIME)
    future = resolve_assessment((child, future_parent), run_id=RUN, cutoff=TIME)
    assert missing == future
    assert missing.issues == ("missing_or_unavailable_parent",)


def test_identical_replayed_assessments_and_equal_timestamps() -> None:
    a, b = outcome(10), outcome(11, parent=10, status="failure")
    state = resolve_assessment((a, b, a, b), run_id=RUN, cutoff=TIME)
    assert state.outcome == b and not state.issues
    assert len(state.visible_outcome_ids) == 2


def test_long_history_and_no_assessment() -> None:
    records = [outcome(10)] + [outcome(i, parent=i - 1) for i in range(11, 2011)]
    assert resolve_assessment(records, run_id=RUN, cutoff=TIME).outcome == records[-1]
    empty = resolve_assessment(records, run_id=RUN, cutoff=TIME - timedelta(seconds=1))
    assert empty.outcome is None and not empty.issues and not empty.visible_outcome_ids


def test_naive_cutoff_rejected() -> None:
    with pytest.raises(ValueError, match="timezone"):
        resolve_assessment([], run_id=RUN, cutoff=TIME.replace(tzinfo=None))


def test_conflicting_identity_affects_every_run_independent_of_input_order() -> None:
    a = outcome(10)
    b = outcome(10, run_id=UUID(int=2), status="failure")
    child = outcome(11, parent=10)
    for run_id in (RUN, UUID(int=2)):
        expected = resolve_assessment((a, b, child), run_id=run_id, cutoff=TIME)
        assert expected.outcome is None
        assert "conflicting_outcome_identity" in expected.issues
        for records in permutations((a, b, child)):
            assert resolve_assessment(records, run_id=run_id, cutoff=TIME) == expected


def test_semantically_identical_replay_ignores_metadata_key_order() -> None:
    first = outcome(10, metadata={"a": 1, "b": 2})
    replay = outcome(10, metadata={"b": 2, "a": 1})
    state = resolve_assessment((first, replay), run_id=RUN, cutoff=TIME)
    assert state.outcome == first and not state.issues
