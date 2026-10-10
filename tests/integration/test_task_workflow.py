"""Sanitized capture fixtures test real contracts, not genuine agent outcomes."""

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from model_learner.adapters.codex import ingest_codex_capture
from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    AttributionStatus,
    DatasetReference,
    Event,
    ExecutionConfiguration,
    Observation,
    Outcome,
    OutcomeStatus,
    ResourceBudget,
    Run,
    Session,
    Task,
    Verification,
    VerificationStatus,
    utc_now,
)
from model_learner.observations import build_real_observation, data_quality_report
from model_learner.runs import create_bounded_run, declare_attempt
from model_learner.storage.database import Database, Repository, StorageError
from model_learner.storage.jsonl import export_jsonl
from model_learner.verification import (
    assess_human,
    assess_run,
    digest_criterion,
    file_sha256,
    verify_file,
)

FIXTURE = Path(__file__).parents[1] / "fixtures/codex/exec_capture.jsonl"
START = datetime(2026, 10, 10, 12, tzinfo=UTC)
END = START + timedelta(minutes=1)
VERIFIED_AT = END + timedelta(minutes=1)
ASSESSED_AT = VERIFIED_AT + timedelta(minutes=1)
DATASET = DatasetReference(
    source_kind="real", dataset_id="sanitized-workflow-fixture", dataset_version="1"
)


def setup_workflow(
    tmp_path: Path,
    *,
    contents: bytes = b"accepted fixture bytes",
    resource_budget: ResourceBudget | None = None,
) -> tuple[Repository, Task, Run, Path]:
    database = Database(tmp_path / "ledger.sqlite3")
    database.initialize()
    repo = Repository(database)
    ingest_codex_capture(repo, FIXTURE, machine_id="test-machine")
    session = repo.list_records(Session)[0]
    artifact = tmp_path / "artifact.txt"
    artifact.write_bytes(contents)
    task = repo.create_task(
        Task(
            description="Fixture objective: exact expected output bytes",
            acceptance_spec=AcceptanceSpec(
                identifier="exact-file-output",
                version="1",
                description="SHA256 equality",
            ),
            task_group="declared-fixture",
            created_at=START,
            resource_budget=resource_budget,
            metadata={
                "file_digest_verifier": digest_criterion(
                    hashlib.sha256(b"accepted fixture bytes").hexdigest()
                )
            },
        )
    )
    run = create_bounded_run(
        repo,
        task_id=task.task_id,
        session_id=session.session_id,
        started_at=START,
        ended_at=END,
        final_artifact_fingerprint=f"sha256:{file_sha256(artifact)}",
    )
    return repo, task, run, artifact


def configuration(model: str = "fixture-model") -> ExecutionConfiguration:
    return ExecutionConfiguration(provider="fixture", model=model, harness="codex-cli")


def full_attempt(repo: Repository, run: Run) -> None:
    declare_attempt(
        repo,
        run_id=run.run_id,
        configuration=configuration(),
        started_at=START,
        ended_at=END,
    )


def verify_assess(repo: Repository, run: Run, artifact: Path) -> Outcome:
    verification = verify_file(
        repo, run_id=run.run_id, artifact=artifact, observed_at=VERIFIED_AT
    )
    return assess_run(
        repo,
        run_id=run.run_id,
        verification_id=verification.verification_id,
        recorded_at=ASSESSED_AT,
    )


def observation(repo: Repository, run: Run, outcome: Outcome) -> Observation:
    return build_real_observation(
        repo,
        run_id=run.run_id,
        outcome_id=outcome.outcome_id,
        dataset=DATASET,
        recorded_at=max(ASSESSED_AT, utc_now()),
    )


def test_complete_capture_to_verified_real_observation_and_replay(
    tmp_path: Path,
) -> None:
    repo, task, run, artifact = setup_workflow(tmp_path)
    native_events = repo.list_records(Event)
    full_attempt(repo, run)
    unknown = assess_run(repo, run_id=run.run_id, recorded_at=END)
    unknown_row = observation(repo, run, unknown)
    assert unknown.status is OutcomeStatus.UNKNOWN
    assert unknown_row.label_available_at is None
    assert not unknown_row.eligible_for_configuration_learning
    evidence = verify_file(
        repo, run_id=run.run_id, artifact=artifact, observed_at=VERIFIED_AT
    )
    assessed = assess_run(
        repo,
        run_id=run.run_id,
        verification_id=evidence.verification_id,
        recorded_at=ASSESSED_AT,
        supersedes_outcome_id=unknown.outcome_id,
    )
    row = observation(repo, run, assessed)
    assert row.outcome_status is OutcomeStatus.SUCCESS
    assert row.verification_status is VerificationStatus.VERIFIED
    assert row.eligible_for_configuration_learning
    assert row.attribution_status is AttributionStatus.SINGLE_CONFIGURATION
    assert row.cost_usd is None and row.latency_seconds is None
    assert row.metadata["configuration_provenance"] == "human_declaration"
    assert row.task_id == task.task_id != repo.list_records(Session)[0].session_id
    assert repo.list_records(Event) == native_events
    assert all(event.run_id is None for event in native_events)
    assert repo.list_run_session_links(run.run_id)[0].session_id in {
        session.session_id for session in repo.list_sessions_for_task(task.task_id)
    }
    again = build_real_observation(
        repo,
        run_id=run.run_id,
        outcome_id=assessed.outcome_id,
        dataset=DATASET,
        recorded_at=max(ASSESSED_AT, utc_now()) + timedelta(minutes=1),
    )
    assert again == row
    replay = ingest_codex_capture(repo, FIXTURE, machine_id="test-machine")
    assert replay.events_duplicate == 10
    assert observation(repo, run, assessed) == row
    assert len(repo.list_records(Outcome)) == 2
    assert len(repo.list_observations("real")) == 2
    destination = tmp_path / "observations.jsonl"
    assert export_jsonl(repo, Observation, destination, source_kind="real") == 2
    assert row.observation_id.hex in destination.read_text().replace("-", "")
    quality = data_quality_report(repo.list_observations("real"))
    assert quality["counts"]["eligible"] == 1
    assert quality["counts"]["unknown_cost"] == 2
    assert b"accepted fixture bytes" not in evidence.model_dump_json().encode()


def test_failed_final_digest_becomes_one_verified_failure(tmp_path: Path) -> None:
    repo, _, run, artifact = setup_workflow(tmp_path, contents=b"incorrect bytes")
    full_attempt(repo, run)
    outcome = verify_assess(repo, run, artifact)
    row = observation(repo, run, outcome)
    assert outcome.status is OutcomeStatus.FAILURE
    assert row.eligible_for_configuration_learning
    assert len(repo.list_records(Outcome)) == 1


def test_wrong_artifact_or_acceptance_is_rejected_without_evidence(
    tmp_path: Path,
) -> None:
    repo, _, run, artifact = setup_workflow(tmp_path)
    artifact.write_bytes(b"changed bytes")
    with pytest.raises(ValueError, match="artifact fingerprint"):
        verify_file(repo, run_id=run.run_id, artifact=artifact, observed_at=VERIFIED_AT)
    with pytest.raises(ValueError, match="acceptance_spec"):
        verify_file(
            repo,
            run_id=run.run_id,
            artifact=artifact,
            acceptance_spec=AcceptanceSpec(
                identifier="exact-file-output", version="old"
            ),
        )
    assert repo.list_records(Verification) == []


@pytest.mark.parametrize("mode", ["mixed", "gap", "unknown_model", "no_attempt"])
def test_attribution_exclusions_preserve_verified_assessment(
    tmp_path: Path, mode: str
) -> None:
    repo, _, run, artifact = setup_workflow(tmp_path)
    midpoint = START + timedelta(seconds=30)
    if mode == "mixed":
        declare_attempt(
            repo,
            run_id=run.run_id,
            configuration=configuration("first"),
            started_at=START,
            ended_at=midpoint,
        )
        declare_attempt(
            repo,
            run_id=run.run_id,
            configuration=configuration("second"),
            started_at=midpoint,
            ended_at=END,
        )
    elif mode != "no_attempt":
        declare_attempt(
            repo,
            run_id=run.run_id,
            configuration=(
                ExecutionConfiguration() if mode == "unknown_model" else configuration()
            ),
            started_at=START,
            ended_at=midpoint if mode == "gap" else END,
        )
    row = observation(repo, run, verify_assess(repo, run, artifact))
    assert row.outcome_status is OutcomeStatus.SUCCESS
    assert not row.eligible_for_configuration_learning
    assert row.configuration.model is None
    expected = "mixed_configuration" if mode == "mixed" else "incomplete"
    assert row.attribution_status.value == expected
    assert expected in row.metadata["exclusions"]


def test_same_configuration_segments_are_one_full_coverage_observation(
    tmp_path: Path,
) -> None:
    repo, _, run, artifact = setup_workflow(tmp_path)
    midpoint = START + timedelta(seconds=30)
    for start, end in [(START, midpoint), (midpoint, END)]:
        declare_attempt(
            repo,
            run_id=run.run_id,
            configuration=configuration(),
            started_at=start,
            ended_at=end,
        )
    row = observation(repo, run, verify_assess(repo, run, artifact))
    assert row.eligible_for_configuration_learning
    assert len(row.metadata["attempt_ids"]) == 2


def test_human_acceptance_is_distinct_and_unverified(tmp_path: Path) -> None:
    repo, _, run, _ = setup_workflow(tmp_path)
    full_attempt(repo, run)
    outcome = assess_human(
        repo, run_id=run.run_id, status=OutcomeStatus.SUCCESS, recorded_at=ASSESSED_AT
    )
    row = observation(repo, run, outcome)
    assert not row.eligible_for_configuration_learning
    assert outcome.verification_status is VerificationStatus.UNVERIFIED
    assert data_quality_report([row])["counts"]["human_assessed"] == 1


def test_overlapping_outside_or_invalid_attempts_are_rejected(tmp_path: Path) -> None:
    repo, _, run, _ = setup_workflow(tmp_path)
    full_attempt(repo, run)
    with pytest.raises(ValueError, match="overlap"):
        full_attempt(repo, run)
    with pytest.raises(ValueError, match="inside"):
        declare_attempt(
            repo,
            run_id=run.run_id,
            configuration=configuration(),
            started_at=START - timedelta(seconds=1),
            ended_at=END,
        )


def test_future_evidence_and_branching_revisions_are_rejected(tmp_path: Path) -> None:
    repo, _, run, artifact = setup_workflow(tmp_path)
    with pytest.raises(ValueError, match="run end"):
        verify_file(repo, run_id=run.run_id, artifact=artifact, observed_at=START)
    evidence = verify_file(
        repo, run_id=run.run_id, artifact=artifact, observed_at=VERIFIED_AT
    )
    unknown = assess_run(repo, run_id=run.run_id, recorded_at=END)
    with pytest.raises(ValueError, match="follow verification"):
        assess_run(
            repo,
            run_id=run.run_id,
            verification_id=evidence.verification_id,
            recorded_at=END,
        )
    assess_run(
        repo,
        run_id=run.run_id,
        verification_id=evidence.verification_id,
        recorded_at=ASSESSED_AT,
        supersedes_outcome_id=unknown.outcome_id,
    )
    with pytest.raises(ValueError, match="already has a revision"):
        assess_human(
            repo,
            run_id=run.run_id,
            status=OutcomeStatus.UNKNOWN,
            recorded_at=ASSESSED_AT,
            supersedes_outcome_id=unknown.outcome_id,
        )


@pytest.mark.parametrize(
    "field", ["result", "artifact_fingerprint", "criterion", "acceptance_spec"]
)
def test_forged_or_stale_evidence_cannot_be_assessed(
    tmp_path: Path, field: str
) -> None:
    repo, _, run, artifact = setup_workflow(tmp_path)
    evidence = verify_file(
        repo, run_id=run.run_id, artifact=artifact, observed_at=VERIFIED_AT
    )
    values = evidence.model_dump()
    values["verification_id"] = uuid4()
    if field == "criterion":
        values["metadata"]["criterion"] = digest_criterion("a" * 64)
    elif field == "result":
        values["result"] = "fail"
    elif field == "acceptance_spec":
        values[field]["version"] = "outdated"
    else:
        values[field] = "sha256:" + "a" * 64
    forged = repo.add_verification(Verification(**values))
    with pytest.raises(ValueError):
        assess_run(
            repo,
            run_id=run.run_id,
            verification_id=forged.verification_id,
            recorded_at=ASSESSED_AT,
        )
    assert repo.list_records(Outcome) == []


def test_duplicate_run_bounds_are_rejected_without_phantom_run(tmp_path: Path) -> None:
    repo, task, run, _ = setup_workflow(tmp_path)
    with pytest.raises(StorageError, match="overlap"):
        create_bounded_run(
            repo,
            task_id=task.task_id,
            session_id=repo.list_sessions_for_run(run.run_id)[0].session_id,
            started_at=START,
            ended_at=END,
        )
    assert repo.list_records(Run) == [run]


def test_unknown_assessment_cannot_be_observed_before_assessment(
    tmp_path: Path,
) -> None:
    repo, _, run, _ = setup_workflow(tmp_path)
    outcome = assess_run(repo, run_id=run.run_id, recorded_at=ASSESSED_AT)
    with pytest.raises(ValueError, match="follow its assessment"):
        build_real_observation(
            repo,
            run_id=run.run_id,
            outcome_id=outcome.outcome_id,
            dataset=DATASET,
            recorded_at=END,
        )


def test_censored_human_assessment_is_unknown_to_learning(tmp_path: Path) -> None:
    repo, _, run, _ = setup_workflow(tmp_path)
    outcome = assess_human(
        repo,
        run_id=run.run_id,
        status=OutcomeStatus.CENSORED,
        censor_reason="no final artifact retained",
        recorded_at=ASSESSED_AT,
    )
    row = observation(repo, run, outcome)
    assert row.label_available_at is None
    assert not row.eligible_for_configuration_learning
    assert data_quality_report([row])["counts"]["outcome:censored"] == 1


def test_emitted_configuration_conflict_is_preserved_as_exclusion(
    tmp_path: Path,
) -> None:
    import json

    repo, _, run, artifact = setup_workflow(tmp_path)
    full_attempt(repo, run)
    source = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    source[0]["event"]["model"] = "different-emitted-model"
    for row in source:
        row["capture_id"] = "independent-model-capture"
    path = tmp_path / "emitted.jsonl"
    path.write_text("\n".join(json.dumps(row) for row in source) + "\n")
    ingest_codex_capture(repo, path, machine_id="test-machine")
    row = observation(repo, run, verify_assess(repo, run, artifact))
    assert not row.eligible_for_configuration_learning
    assert (
        "declared_configuration_conflicts_with_native_telemetry"
        in row.metadata["exclusions"]
    )
    assert row.metadata["configuration_conflict_event_ids"]


@pytest.mark.parametrize("known_cost", [None, 2.0])
def test_unknown_or_exceeded_budget_is_excluded_without_changing_verification(
    tmp_path: Path, known_cost: float | None
) -> None:
    repo, _, run, artifact = setup_workflow(
        tmp_path, resource_budget=ResourceBudget(max_cost_usd=1)
    )
    repo.create_attempt(
        Attempt(
            run_id=run.run_id,
            configuration=configuration(),
            started_at=START,
            ended_at=END,
            cost_usd=known_cost,
            metadata={"configuration_provenance": "human_declaration"},
        )
    )
    row = observation(repo, run, verify_assess(repo, run, artifact))
    assert not row.eligible_for_configuration_learning
    assert row.outcome_status is OutcomeStatus.SUCCESS
    assert row.verification_status is VerificationStatus.VERIFIED
    reason = "budget_cost_unknown" if known_cost is None else "budget_cost_exceeded"
    assert reason in row.metadata["exclusions"]
