"""Synthetic receipts and frozen byte evidence only; no candidate execution."""

import json

import pytest

import model_learner.benchmark as benchmark
from model_learner.adapters.codex import capture_codex_stream, ingest_codex_capture
from model_learner.benchmark.evidence import (
    BenchmarkEvidence,
    export_benchmark_evidence,
    import_benchmark_evidence,
)
from model_learner.domain.models import (
    Attempt,
    Event,
    ExecutionConfiguration,
    Observation,
    Outcome,
    OutcomeStatus,
    Run,
    RunSessionLink,
    RunState,
    TaskSessionLink,
    utc_now,
)
from model_learner.learn.estimator import BetaBernoulli
from model_learner.storage.database import Database, Repository
from model_learner.verification import (
    JUnitReportBinding,
    assess_run,
    file_sha256,
    verify_junit,
)


def ledger(path):
    database = Database(path)
    database.initialize()
    return Repository(database)


def fixture(
    tmp_path,
    *,
    verified=True,
    conflict=False,
    state=RunState.FINISHED,
    configuration=None,
    resource_budget=None,
    stop_reason=None,
):
    protected, parent = tmp_path / "protected", tmp_path / "disposable"
    protected.mkdir()
    (protected / "README.md").write_text("harmless synthetic repository")
    parent.mkdir()
    prepared = benchmark.prepare_benchmark(
        parent=parent,
        task_id="clamp",
        protected_repository=protected,
        configuration=configuration
        or ExecutionConfiguration(
            provider="fixture",
            model="fixture-model",
            harness="fixture-harness",
            harness_version="1",
        ),
        execution_origin="fixture",
        isolation_mechanism="synthetic data only",
    )
    repository = Repository(Database(prepared.control / "ledger.sqlite3"))
    # Declared source timestamps are current past receipts, never forged imports.
    started = utc_now()
    capture = prepared.control / "capture.jsonl"
    with capture.open("x") as stream:
        capture_codex_stream(
            [
                json.dumps(
                    {
                        "type": "thread.started",
                        "thread_id": "fixture-thread",
                        "model": "conflict" if conflict else "fixture-model",
                    }
                ),
                json.dumps(
                    {
                        "type": "item.completed",
                        "hidden_test": "HIDDEN_SECRET",
                        "future_label": "FUTURE_LABEL",
                        "item": {
                            "id": "i",
                            "type": "agent_message",
                            "text": "I succeeded PRIVATE_SELF_REPORT",
                        },
                    }
                ),
            ],
            stream,
            source_version="synthetic-emitter/v1",
        )
    ended = utc_now()
    snapshot = benchmark.snapshot_candidate(prepared.root)
    run = Run(
        task_id=prepared.task.task_id,
        resource_budget=resource_budget,
        stop_reason=stop_reason,
        started_at=started,
        ended_at=ended,
        state=state,
        metadata={
            "final_artifact_fingerprint": "sha256:" + file_sha256(snapshot),
            "benchmark_id": str(prepared.benchmark_id),
            "execution_origin": "fixture",
        },
    )
    repository.create_run(run)
    imported = ingest_codex_capture(repository, capture, machine_id="synthetic")
    events = repository.list_records(Event)
    session_id = events[0].session_id
    repository.associate_session(
        TaskSessionLink(task_id=prepared.task.task_id, session_id=session_id)
    )
    repository.associate_run_session(
        RunSessionLink(run_id=run.run_id, session_id=session_id)
    )
    repository.create_attempt(
        Attempt(
            run_id=run.run_id,
            configuration=prepared.configuration,
            started_at=started,
            ended_at=ended,
            metadata={"configuration_provenance": "operator_predeclaration"},
        )
    )
    verification = None
    if verified:
        # Receipt fixture, no Python candidate or acceptance process is launched.
        # Derive names from the independently predeclared fixture criterion.
        ids = prepared.task.metadata["junit_verifier"]["required_test_ids"]
        cases = "".join(
            f'<testcase classname="{identity.rsplit("::", 1)[0]}" '
            f'name="{identity.rsplit("::", 1)[1]}"/>'
            for identity in ids
        )
        report = prepared.control / "report.xml"
        report.write_text(
            f'<testsuite tests="{len(ids)}" failures="0" errors="0" skipped="0">'
            f"{cases}</testsuite>"
        )
        binding = JUnitReportBinding(
            task_id=run.task_id,
            run_id=run.run_id,
            acceptance_spec=prepared.task.acceptance_spec,
            artifact_fingerprint=run.metadata["final_artifact_fingerprint"],
            report_sha256=file_sha256(report),
            report_generated_at=utc_now(),
            source="junit",
            execution_completed=True,
            command_exit_code=0,
        )
        verification = verify_junit(
            repository,
            run_id=run.run_id,
            artifact=snapshot,
            report=report,
            binding=binding,
        )
    outcome = assess_run(
        repository,
        run_id=run.run_id,
        verification_id=(
            verification.verification_id
            if verification and state is RunState.FINISHED
            else None
        ),
    )
    result = benchmark.BenchmarkResult(
        benchmark_id=prepared.benchmark_id,
        dataset=prepared.dataset,
        execution_origin="fixture",
        configuration=prepared.configuration,
        run=run,
        outcome=outcome,
        verification=verification,
        telemetry_events=imported.events_inserted,
        telemetry_diagnostics=0,
        reasons=(),
        ledger=prepared.control / "ledger.sqlite3",
    )
    (prepared.control / "result.json").write_text(result.model_dump_json())
    return prepared, repository, result


def test_export_import_exact_evidence_and_no_hidden_future_content(tmp_path):
    prepared, source, result = fixture(tmp_path)
    evidence = export_benchmark_evidence(
        prepared.root, checkpoints=(result.run.started_at, result.run.ended_at)
    )
    assert evidence.observation.eligible_for_configuration_learning
    assert evidence.observation.source_kind.value == "benchmark"
    assert evidence.observation.dataset.dataset_id.endswith(":fixture")
    assert evidence.observation.configuration.harness_version == "1"
    assert evidence.observation.cost_usd is None
    assert evidence.observation.latency_seconds is None
    assert len(evidence.native_events) == 2
    assert all(event.raw_payload is None for event in evidence.native_events)
    encoded = evidence.model_dump_json()
    for private in (
        "HIDDEN_SECRET",
        "FUTURE_LABEL",
        "PRIVATE_SELF_REPORT",
        "required_test_ids",
        "candidate.py",
    ):
        assert private not in encoded
    assert len(evidence.verification_bindings) == 1
    assert all(not point.eligible_for_task_state for point in evidence.checkpoints)
    assert all(
        point.checkpoint.facts.event_count == 0 for point in evidence.checkpoints
    )
    destination = ledger(tmp_path / "destination.sqlite3")
    row = import_benchmark_evidence(
        destination, BenchmarkEvidence.model_validate_json(encoded), root=prepared.root
    )
    assert row.recorded_at >= evidence.exported_at
    again = import_benchmark_evidence(
        destination,
        export_benchmark_evidence(
            prepared.root, checkpoints=(result.run.started_at, result.run.ended_at)
        ),
        root=prepared.root,
    )
    assert again == row
    assert len(destination.list_observations("benchmark")) == 1
    assert destination.list_observations("real") == []
    assert [item.ingested_at for item in source.list_records(Event)] == [
        item.ingested_at for item in evidence.native_events
    ]
    estimator = BetaBernoulli.fit(
        [row],
        dataset=row.dataset,
        cutoff=utc_now(),
        acceptance_spec=row.acceptance_spec,
    )
    assert estimator.training_summary.eligible_label_count == 1


@pytest.mark.parametrize(
    "verified,conflict,state",
    [
        (False, False, RunState.FINISHED),
        (True, True, RunState.FINISHED),
        (True, False, RunState.ABANDONED),
    ],
)
def test_unknown_conflict_and_incomplete_not_eligible(
    tmp_path, verified, conflict, state
):
    prepared, _, _ = fixture(
        tmp_path, verified=verified, conflict=conflict, state=state
    )
    evidence = export_benchmark_evidence(prepared.root)
    assert not evidence.observation.eligible_for_configuration_learning
    if not verified:
        assert evidence.observation.outcome_status is OutcomeStatus.UNKNOWN
        assert evidence.observation.label_available_at is None
    assert evidence.observation.configuration == prepared.configuration


def test_historical_cutoff_excludes_future_label_and_no_backdating(tmp_path):
    prepared, _, result = fixture(tmp_path)
    evidence = export_benchmark_evidence(
        prepared.root, historical_cutoff=result.run.ended_at
    )
    assert evidence.observation.outcome_status is OutcomeStatus.UNKNOWN
    assert evidence.observation.outcome_id is None
    assert evidence.observation.evidence_ids == ()
    assert evidence.verification_bindings == ()
    assert evidence.native_events == ()
    assert evidence.observation.recorded_at > result.outcome.recorded_at
    assert str(result.outcome.outcome_id) not in evidence.model_dump_json()


def test_source_revalidation_rejects_tamper_without_import(tmp_path):
    prepared, _, _ = fixture(tmp_path)
    evidence = export_benchmark_evidence(prepared.root)
    destination = ledger(tmp_path / "destination.sqlite3")
    (prepared.control / "candidate.py").chmod(0o600)
    (prepared.control / "candidate.py").write_text("tampered harmless bytes")
    with pytest.raises(ValueError, match="artifact"):
        import_benchmark_evidence(destination, evidence, root=prepared.root)
    assert destination.list_observations("benchmark") == []


def test_latest_revision_and_historical_head_preserved(tmp_path):
    prepared, source, result = fixture(tmp_path)
    before = utc_now()
    revised = source.add_outcome(
        Outcome(
            run_id=result.run.run_id,
            status=OutcomeStatus.UNKNOWN,
            verification_status="unverified",
            assessment_source="human_assessment",
            supersedes_outcome_id=result.outcome.outcome_id,
        )
    )
    current = export_benchmark_evidence(prepared.root)
    past = export_benchmark_evidence(prepared.root, historical_cutoff=before)
    assert current.observation.outcome_id == revised.outcome_id
    assert current.observation.outcome_status is OutcomeStatus.UNKNOWN
    assert not current.observation.eligible_for_configuration_learning
    assert past.observation.outcome_id == result.outcome.outcome_id
    assert past.observation.eligible_for_configuration_learning


def test_digest_corruption_and_conflicting_destination_replay(tmp_path):
    prepared, _, _ = fixture(tmp_path)
    evidence = export_benchmark_evidence(prepared.root)
    values = evidence.model_dump(mode="json")
    values["fixture_id"] = "changed"
    with pytest.raises(ValueError, match="digest"):
        BenchmarkEvidence.model_validate(values)
    destination = ledger(tmp_path / "destination.sqlite3")
    row = evidence.observation
    forged = Observation.model_validate(
        {**row.model_dump(), "stable_key": None, "metadata": {"forged": True}}
    )
    destination.add_observation(forged)
    with pytest.raises(ValueError, match="conflicting"):
        import_benchmark_evidence(destination, evidence, root=prepared.root)
    assert len(destination.list_observations("benchmark")) == 1


def test_no_session_checkpoint_request_retained(tmp_path):
    protected, parent = tmp_path / "protected", tmp_path / "disposable"
    protected.mkdir()
    parent.mkdir()
    prepared = benchmark.prepare_benchmark(
        parent=parent,
        task_id="clamp",
        protected_repository=protected,
        configuration=ExecutionConfiguration(model="fixture"),
        execution_origin="fixture",
        isolation_mechanism="no process",
    )
    started = utc_now()
    result = benchmark.finalize_benchmark(
        prepared.root, started_at=started, ended_at=utc_now(), isolation_confirmed=True
    )
    evidence = export_benchmark_evidence(
        prepared.root, checkpoints=(result.run.started_at,)
    )
    assert evidence.requested_checkpoints == (result.run.started_at,)
    assert evidence.checkpoints == ()
    assert evidence.checkpoint_reasons == ("no_linked_session_for_checkpoints",)
    assert not evidence.observation.eligible_for_configuration_learning
    destination = ledger(tmp_path / "destination.sqlite3")
    import_benchmark_evidence(destination, evidence, root=prepared.root)


def test_cutoff_and_revised_history_safe_in_existing_learner(tmp_path):
    prepared, source, result = fixture(tmp_path)
    destination = ledger(tmp_path / "destination.sqlite3")
    evidence = export_benchmark_evidence(prepared.root)
    first = import_benchmark_evidence(destination, evidence, root=prepared.root)
    earlier_fit = BetaBernoulli.fit(
        [first],
        dataset=first.dataset,
        cutoff=result.outcome.recorded_at,
        acceptance_spec=first.acceptance_spec,
    )
    assert earlier_fit.training_summary.eligible_label_count == 0
    source.add_outcome(
        Outcome(
            run_id=result.run.run_id,
            status=OutcomeStatus.UNKNOWN,
            verification_status="unverified",
            assessment_source="human_assessment",
            supersedes_outcome_id=result.outcome.outcome_id,
        )
    )
    newest = import_benchmark_evidence(
        destination, export_benchmark_evidence(prepared.root), root=prepared.root
    )
    assert newest.outcome_status is OutcomeStatus.UNKNOWN
    with pytest.raises(ValueError, match="conflicting observations"):
        BetaBernoulli.fit(
            destination.list_observations("benchmark"),
            dataset=first.dataset,
            cutoff=utc_now(),
            acceptance_spec=first.acceptance_spec,
        )
    # Explicitly selected latest derivation remains unknown, no earlier-label fallback.
    current_fit = BetaBernoulli.fit(
        [newest],
        dataset=first.dataset,
        cutoff=utc_now(),
        acceptance_spec=first.acceptance_spec,
    )
    assert current_fit.training_summary.eligible_label_count == 0


def test_independent_evidence_retained_for_interrupted_unknown_run(tmp_path):
    prepared, _, result = fixture(tmp_path, state=RunState.ABANDONED)
    evidence = export_benchmark_evidence(prepared.root)
    assert result.outcome.status is OutcomeStatus.UNKNOWN
    assert result.outcome.evidence_ids == ()
    assert evidence.observation.outcome_status is OutcomeStatus.UNKNOWN
    assert evidence.observation.evidence_ids == ()
    assert (
        evidence.verification_bindings[0].verification_id
        == result.verification.verification_id
    )
    assert not evidence.observation.eligible_for_configuration_learning
    past = export_benchmark_evidence(
        prepared.root, historical_cutoff=result.run.ended_at
    )
    assert past.verification_bindings == ()


def test_arbitrary_configuration_metadata_rejected(tmp_path):
    protected, parent = tmp_path / "protected", tmp_path / "disposable"
    protected.mkdir()
    parent.mkdir()
    prepared = benchmark.prepare_benchmark(
        parent=parent,
        task_id="clamp",
        protected_repository=protected,
        configuration=ExecutionConfiguration(
            model="fixture", metadata={"future_label": "HIDDEN_SECRET"}
        ),
        execution_origin="fixture",
        isolation_mechanism="no process",
    )
    started = utc_now()
    benchmark.finalize_benchmark(
        prepared.root, started_at=started, ended_at=utc_now(), isolation_confirmed=True
    )
    with pytest.raises(ValueError, match="empty arbitrary configuration metadata"):
        export_benchmark_evidence(prepared.root)


@pytest.mark.parametrize(
    "dimension", ["model", "provider", "harness", "harness_version"]
)
def test_blank_configuration_dimensions_remain_ineligible(tmp_path, dimension):
    values = dict(
        provider="fixture",
        model="fixture-model",
        harness="fixture-harness",
        harness_version="1",
    )
    values[dimension] = "   "
    configuration = ExecutionConfiguration(**values)
    prepared, _, _ = fixture(tmp_path, configuration=configuration)
    evidence = export_benchmark_evidence(prepared.root)
    assert evidence.observation.configuration == configuration
    assert not evidence.observation.eligible_for_configuration_learning
    assert (
        f"configuration_{dimension}_unknown"
        in evidence.observation.metadata["exclusions"]
    )
