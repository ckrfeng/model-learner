"""Read-only temporal reconstruction against a deterministic sanitized ledger."""

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from model_learner.adapters.codex import SOURCE
from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    DatasetReference,
    Event,
    ExecutionConfiguration,
    Observation,
    Outcome,
    Run,
    RunSessionLink,
    Session,
    Task,
    TaskSessionLink,
    Verification,
)
from model_learner.observations import build_real_observation
from model_learner.observations.resolution import (
    resolve_observation_revisions,
    resolve_real_observations,
)
from model_learner.storage.database import Database, Repository
from model_learner.verification import (
    assess_human,
    assess_run,
    digest_criterion,
    verify_file,
)

START = datetime(2026, 10, 10, 12, tzinfo=UTC)
END = START + timedelta(minutes=1)
LABEL = END + timedelta(minutes=2)
DATASET = DatasetReference(
    source_kind="real", dataset_id="fixture", dataset_version="1"
)


def ledger(tmp_path: Path, *, ingestion: datetime = END, association: datetime = END):
    database = Database(tmp_path / "ledger.sqlite3")
    database.initialize()
    repo = Repository(database)
    artifact = tmp_path / "artifact.txt"
    artifact.write_bytes(b"sanitized bytes")
    digest = hashlib.sha256(artifact.read_bytes()).hexdigest()
    task = repo.create_task(
        Task(
            description="exact fixture bytes",
            created_at=START,
            acceptance_spec=AcceptanceSpec(identifier="exact-bytes", version="1"),
            metadata={"file_digest_verifier": digest_criterion(digest)},
        )
    )
    session = repo.create_session(Session(source=SOURCE, native_session_id="fixture"))
    repo.associate_session(
        TaskSessionLink(
            task_id=task.task_id,
            session_id=session.session_id,
            associated_at=association,
        )
    )
    run = repo.create_run(
        Run(
            task_id=task.task_id,
            started_at=START,
            ended_at=END,
            metadata={"final_artifact_fingerprint": f"sha256:{digest}"},
        )
    )
    repo.associate_run_session(
        RunSessionLink(
            run_id=run.run_id, session_id=session.session_id, associated_at=association
        )
    )
    repo.create_attempt(
        Attempt(
            run_id=run.run_id,
            configuration=ExecutionConfiguration(model="fixture-model"),
            started_at=START,
            ended_at=END,
            metadata={"configuration_provenance": "human_declaration"},
        )
    )
    repo.add_event(
        Event(
            observed_at=START + timedelta(seconds=1),
            ingested_at=ingestion,
            source=SOURCE,
            source_version="1",
            machine_id="fixture",
            capture_method="fixture",
            native_session_id="fixture",
            session_id=session.session_id,
            event_type="thread.started",
            provenance="observed",
        )
    )
    unknown = assess_run(repo, run_id=run.run_id, recorded_at=END)
    evidence = verify_file(
        repo,
        run_id=run.run_id,
        artifact=artifact,
        observed_at=LABEL - timedelta(minutes=1),
    )
    success = assess_run(
        repo,
        run_id=run.run_id,
        verification_id=evidence.verification_id,
        recorded_at=LABEL,
        supersedes_outcome_id=unknown.outcome_id,
    )
    return repo, run, unknown, success


def build(repo, run, outcome, time):
    return build_real_observation(
        repo,
        run_id=run.run_id,
        outcome_id=outcome.outcome_id,
        dataset=DATASET,
        recorded_at=time,
    )


def snapshot(repo, cutoff, **kwargs):
    return resolve_real_observations(repo, dataset=DATASET, cutoff=cutoff, **kwargs)


def test_historical_state_delayed_label_and_read_only_repeated_snapshot(
    tmp_path,
) -> None:
    repo, run, unknown, success = ledger(tmp_path)
    original = repo.list_records(Outcome)
    before = snapshot(repo, LABEL - timedelta(seconds=1))
    assert before.assessments[0].outcome == unknown
    assert before.observations[0].outcome_status.value == "unknown"
    assert before.observations[0].label_available_at is None
    assert not before.observations[0].eligible_for_configuration_learning
    # A post-hoc declaration with no historical availability proof cannot train.
    posthoc = snapshot(repo, LABEL)
    assert posthoc.assessments[0].outcome == success
    assert not posthoc.observations[0].eligible_for_configuration_learning
    assert posthoc.observations[0].configuration.model is None
    assert posthoc.observations[0].attempt_id is None
    assert posthoc.observations[0].metadata["attempt_ids"] == []
    assert (
        "historical_derivation_availability_unknown"
        in posthoc.observations[0].metadata["exclusions"]
    )
    assert not repo.list_observations("real")
    saved = build(repo, run, success, LABEL)
    final = snapshot(repo, LABEL)
    assert final == snapshot(repo, LABEL)
    assert (
        len(final.observations) == 1
        and final.observations[0].eligible_for_configuration_learning
    )
    assert final.observations[0].stable_key == saved.stable_key
    assert repo.list_records(Outcome) == original
    assert repo.list_observations("real") == [saved]
    assert final.availability_limitations and final.method


def test_delayed_derivation_not_historically_eligible(tmp_path) -> None:
    repo, run, _, success = ledger(tmp_path)
    build(repo, run, success, LABEL + timedelta(minutes=1))
    assert not snapshot(repo, LABEL).observations[0].eligible_for_configuration_learning
    assert (
        snapshot(repo, LABEL + timedelta(minutes=1))
        .observations[0]
        .eligible_for_configuration_learning
    )


@pytest.mark.parametrize(
    "status,extra", [("unknown", {}), ("censored", {"censor_reason": "withdrawn"})]
)
def test_latest_unknown_and_censored_do_not_fall_back_to_verified_label(
    tmp_path, status, extra
) -> None:
    repo, run, _, success = ledger(tmp_path)
    old = build(repo, run, success, LABEL)
    revision_time = LABEL + timedelta(minutes=1)
    revised = assess_human(
        repo,
        run_id=run.run_id,
        status=status,
        recorded_at=revision_time,
        supersedes_outcome_id=success.outcome_id,
        **extra,
    )
    state = snapshot(repo, revision_time)
    assert state.assessments[0].outcome == revised
    assert state.observations[0].outcome_status.value == status
    assert not state.observations[0].eligible_for_configuration_learning
    assert state.observations[0].label_available_at is None
    # Missing latest derivation is exclusion, never the former successful row.
    persisted = resolve_observation_revisions(
        [old], repo.list_records(Outcome), dataset=DATASET, cutoff=revision_time
    )
    assert not persisted.observations
    assert persisted.exclusions[0].reasons == ("no_visible_head_derivation",)


def test_future_capture_and_future_association_are_not_historical_evidence(
    tmp_path,
) -> None:
    repo, _, _, _ = ledger(tmp_path, ingestion=LABEL + timedelta(minutes=1))
    state = snapshot(repo, LABEL)
    assert not state.observations
    assert "no captured events" in state.exclusions[0].reasons[0]
    other = tmp_path / "other"
    other.mkdir()
    repo, _, _, _ = ledger(other, association=LABEL + timedelta(minutes=1))
    state = snapshot(repo, LABEL)
    assert not state.observations
    assert "explicitly linked" in state.exclusions[0].reasons[0]


def test_future_verification_cannot_validate_visible_assessment(tmp_path) -> None:
    repo, _, _, success = ledger(tmp_path)
    # Construct corrupt legacy evidence timestamps directly; modern assessment
    # writers reject this history. No future evidence label may enter a snapshot.
    evidence = repo.get(Verification, success.evidence_ids[0])
    values = evidence.model_dump()
    values["observed_at"] = LABEL + timedelta(minutes=1)
    modified = evidence.__class__.model_validate(values)
    with repo.database.connection() as connection:
        connection.execute(
            "UPDATE verifications SET data = ? WHERE verification_id = ?",
            (modified.model_dump_json(), str(evidence.verification_id)),
        )
    state = snapshot(repo, LABEL)
    assert state.assessments[0].outcome == success
    assert not state.observations
    assert state.exclusions[0].reasons == ("assessment evidence unavailable at cutoff",)


def test_persisted_cohort_resolution_deduplicates_and_filters_dataset_time(
    tmp_path,
) -> None:
    repo, run, unknown, success = ledger(tmp_path)
    first = build(repo, run, unknown, END)
    latest = build(repo, run, success, LABEL)
    rows = [latest, first, latest.model_copy(update={"observation_id": uuid4()})]
    state = resolve_observation_revisions(
        rows, repo.list_records(Outcome), dataset=DATASET, cutoff=LABEL
    )
    assert (
        len(state.observations) == 1
        and state.observations[0].outcome_id == success.outcome_id
    )
    earlier = resolve_observation_revisions(
        rows, repo.list_records(Outcome), dataset=DATASET, cutoff=END
    )
    assert earlier.observations == (first,)
    foreign = DATASET.model_copy(update={"dataset_version": "other"})
    assert not resolve_observation_revisions(
        rows, repo.list_records(Outcome), dataset=foreign, cutoff=LABEL
    ).observations
    assert len(repo.list_records(Observation, source_kind="real")) == 2


def test_conflicting_derivations_fail_closed(tmp_path) -> None:
    repo, run, _, success = ledger(tmp_path)
    first = build(repo, run, success, LABEL)
    values = first.model_dump()
    values["metadata"]["different_derivation"] = True
    values["stable_key"] = None
    second = Observation.model_validate(values)
    state = resolve_observation_revisions(
        [first, second], repo.list_records(Outcome), dataset=DATASET, cutoff=LABEL
    )
    assert not state.observations
    assert state.exclusions[0].reasons == ("conflicting_head_derivations",)


def test_explicit_run_cohort_and_invalid_dataset(tmp_path) -> None:
    repo, run, _, _ = ledger(tmp_path)
    assert not snapshot(repo, LABEL, run_ids=[]).observations
    assert (
        snapshot(repo, LABEL, run_ids=[run.run_id, run.run_id]).assessments[0].run_id
        == run.run_id
    )
    with pytest.raises(ValueError, match="real dataset"):
        resolve_real_observations(
            repo,
            dataset=DatasetReference(
                source_kind="simulated", dataset_id="x", dataset_version="1"
            ),
            cutoff=LABEL,
        )


def test_later_attribution_changes_do_not_rewrite_earlier_immutable_proof(
    tmp_path,
) -> None:
    repo, run, _, success = ledger(tmp_path)
    build(repo, run, success, LABEL)
    original = snapshot(repo, LABEL)
    assert original.observations[0].eligible_for_configuration_learning
    # The immutable earlier builder proof binds the exact attempt set. New
    # untimestamped declarations cannot enter that historical attribution.
    repo.create_attempt(
        Attempt(
            run_id=run.run_id,
            configuration=ExecutionConfiguration(model="other-fixture-model"),
            started_at=START,
            ended_at=END,
            metadata={"configuration_provenance": "human_declaration"},
        )
    )
    changed = snapshot(repo, LABEL)
    assert changed == original
    assert changed.observations[0].eligible_for_configuration_learning


def test_persisted_duplicate_derivation_keeps_earliest_availability(tmp_path) -> None:
    repo, run, _, success = ledger(tmp_path)
    first = build(repo, run, success, LABEL)
    later = first.model_copy(update={"recorded_at": LABEL + timedelta(minutes=1)})
    for rows in ([later, first], [first, later]):
        state = resolve_observation_revisions(
            rows,
            repo.list_records(Outcome),
            dataset=DATASET,
            cutoff=LABEL + timedelta(minutes=2),
        )
        assert state.observations == (first,)


def test_custom_task_group_in_persisted_derivation_is_preserved(tmp_path) -> None:
    repo, run, _, success = ledger(tmp_path)
    saved = build_real_observation(
        repo,
        run_id=run.run_id,
        outcome_id=success.outcome_id,
        dataset=DATASET,
        recorded_at=LABEL,
        task_group="explicit-fixture-group",
    )
    state = snapshot(repo, LABEL)
    assert state.observations[0].task_group == "explicit-fixture-group"
    assert state.observations[0].stable_key == saved.stable_key
    assert state.observations[0].eligible_for_configuration_learning


def test_repository_conflicting_persisted_head_derivations_fail_closed(
    tmp_path,
) -> None:
    repo, run, _, success = ledger(tmp_path)
    build(repo, run, success, LABEL)
    build_real_observation(
        repo,
        run_id=run.run_id,
        outcome_id=success.outcome_id,
        dataset=DATASET,
        recorded_at=LABEL,
        task_group="different-fixture-group",
    )
    state = snapshot(repo, LABEL)
    assert not state.observations
    assert state.exclusions[0].reasons == ("conflicting_head_derivations",)


@pytest.mark.parametrize("attempt_ids", [None, ["not-a-uuid"], [str(uuid4())]])
def test_malformed_or_missing_attempt_proof_fails_closed(tmp_path, attempt_ids) -> None:
    repo, run, _, success = ledger(tmp_path)
    saved = build(repo, run, success, LABEL)
    values = saved.model_dump()
    if attempt_ids is None:
        del values["metadata"]["attempt_ids"]
    else:
        values["metadata"]["attempt_ids"] = attempt_ids
    values["stable_key"] = None
    malformed = Observation.model_validate(values)
    # Simulate a legacy/imported ledger; do not grant unsupported provenance the
    # current declaration set simply because configuration fields happen to agree.
    with repo.database.connection() as connection:
        connection.execute(
            "UPDATE observations SET data = ?, stable_key = ? WHERE observation_id = ?",
            (
                malformed.model_dump_json(),
                malformed.stable_key,
                str(saved.observation_id),
            ),
        )
    state = snapshot(repo, LABEL)
    assert not state.observations
    assert state.exclusions


def test_attempt_selection_requires_historical_cutoff(tmp_path) -> None:
    from model_learner.observations import derive_real_observation

    repo, run, _, success = ledger(tmp_path)
    with pytest.raises(ValueError, match="requires a historical cutoff"):
        derive_real_observation(
            repo,
            run_id=run.run_id,
            outcome_id=success.outcome_id,
            dataset=DATASET,
            recorded_at=LABEL,
            historical_attempt_ids=[],
        )
