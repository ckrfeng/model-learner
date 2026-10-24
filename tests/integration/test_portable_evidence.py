"""W2 fixtures are wholly fictional; the real contract is exercised, not real data.

All artifacts/reports are generated in pytest temporary directories. No model,
conversation history, private ledger, network or external verifier is accessed.
"""

import hashlib
import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import TypeAdapter

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
from model_learner.learn.prospective import (
    CompatibilityPolicy,
    ConfigurationMember,
    TaskMember,
    canonical,
    forecast,
    freeze,
)
from model_learner.observations import build_real_observation
from model_learner.observations.resolution import resolve_real_observations
from model_learner.runs import create_bounded_run, declare_attempt
from model_learner.storage import evidence as portable
from model_learner.storage.database import Database, Repository, StorageError
from model_learner.storage.jsonl import export_jsonl, import_jsonl
from model_learner.verification import (
    JUnitReportBinding,
    assess_run,
    junit_criterion,
    verify_junit,
)

START = datetime(2026, 1, 1, tzinfo=UTC)
CUTOFF = START + timedelta(hours=1)
LATE = START + timedelta(hours=2)
DATASET = DatasetReference(
    source_kind="real", dataset_id="synthetic-w2-contract", dataset_version="1"
)
KINDS = (Task, Session, Run, Attempt, Event, Verification, Outcome, Observation)


def repository(path):
    db = Database(path)
    db.initialize()
    return Repository(db)


@pytest.fixture
def scenario(tmp_path):
    repo = repository(tmp_path / "source.sqlite")
    spec = AcceptanceSpec(identifier="synthetic-tests", version="1")
    task = repo.create_task(
        Task(
            description="Fictional selected task",
            created_at=START,
            acceptance_spec=spec,
            task_group="synthetic-group",
            metadata={
                "junit_verifier": junit_criterion(required_test_ids=["fixture::case"])
            },
        )
    )
    other = repo.create_task(
        Task(
            description="Fictional unrelated task",
            created_at=START,
            acceptance_spec=spec,
        )
    )
    configurations = [
        ExecutionConfiguration(
            provider="fixture",
            model="fixture",
            reasoning_level=effort,
            harness="fixture",
            harness_version="1",
        )
        for effort in ("low", "high")
    ]
    runs, attempts, initial, corrected = [], [], [], []
    for index, state in enumerate(("pass", "fail", "unknown")):
        artifact = tmp_path / f"artifact-{index}.txt"
        artifact.write_text(f"fictional artifact {index}")
        fingerprint = "sha256:" + hashlib.sha256(artifact.read_bytes()).hexdigest()
        session = repo.create_session(
            Session(source=SOURCE, native_session_id=f"fixture-{index}")
        )
        repo.associate_session(
            TaskSessionLink(
                task_id=task.task_id,
                session_id=session.session_id,
                associated_at=START,
            )
        )
        run = repo.create_run(
            Run(
                task_id=task.task_id,
                started_at=START,
                ended_at=START + timedelta(minutes=1),
                metadata={"final_artifact_fingerprint": fingerprint},
            )
        )
        repo.associate_run_session(
            RunSessionLink(
                run_id=run.run_id,
                session_id=session.session_id,
                associated_at=START,
            )
        )
        attempt = repo.create_attempt(
            Attempt(
                run_id=run.run_id,
                configuration=configurations[index % 2],
                started_at=run.started_at,
                ended_at=run.ended_at,
                metadata={"configuration_provenance": "human_declaration"},
            )
        )
        repo.add_event(
            Event(
                source=SOURCE,
                source_version="1",
                machine_id="fixture",
                capture_method="fixture",
                native_session_id=session.native_session_id,
                session_id=session.session_id,
                run_id=run.run_id,
                event_type="thread.started",
                provenance="observed",
                observed_at=START,
                ingested_at=START,
            )
        )
        unknown = assess_run(
            repo, run_id=run.run_id, recorded_at=START + timedelta(minutes=2)
        )
        build_real_observation(
            repo,
            run_id=run.run_id,
            outcome_id=unknown.outcome_id,
            dataset=DATASET,
            recorded_at=START + timedelta(minutes=2),
        )
        initial.append(unknown)
        if state != "unknown":
            report = tmp_path / f"report-{index}.xml"
            report.write_text(
                f'<testsuite tests="1" failures="{int(state == "fail")}" '
                'errors="0" skipped="0">'
                '<testcase classname="fixture" name="case">'
                + ("<failure/>" if state == "fail" else "")
                + "</testcase></testsuite>"
            )
            binding = JUnitReportBinding(
                task_id=task.task_id,
                run_id=run.run_id,
                acceptance_spec=spec,
                artifact_fingerprint=fingerprint,
                report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
                report_generated_at=run.ended_at,
                source="pytest-junit",
                execution_completed=True,
                command_exit_code=int(state == "fail"),
            )
            verification = verify_junit(
                repo,
                run_id=run.run_id,
                artifact=artifact,
                report=report,
                binding=binding,
                observed_at=START + timedelta(minutes=3),
            )
            outcome = assess_run(
                repo,
                run_id=run.run_id,
                verification_id=verification.verification_id,
                recorded_at=START + timedelta(minutes=4),
                supersedes_outcome_id=unknown.outcome_id,
            )
            corrected.append(outcome)
            build_real_observation(
                repo,
                run_id=run.run_id,
                outcome_id=outcome.outcome_id,
                dataset=DATASET,
                recorded_at=START + timedelta(minutes=4),
            )
        runs.append(run)
        attempts.append(attempt)
    return repo, task, other, runs, attempts, initial, corrected


def test_gap_primary_jsonl_loses_associations(scenario, tmp_path):
    repo, task, _, runs, *_ = scenario
    restored = repository(tmp_path / "legacy.sqlite")
    for kind in KINDS:
        path = tmp_path / f"{kind.__name__}.jsonl"
        export_jsonl(repo, kind, path, source_kind="real")
        import_jsonl(restored, path)
    # Regression evidence: legacy JSONL remains primary-record-only (test J).
    assert restored.list_run_session_links(runs[0].run_id) == []
    assert len(restored.list_tasks()) == 2
    assert repo.list_run_session_links(runs[0].run_id)


def test_gap_declared_time_cannot_establish_actual_receipt(scenario):
    repo, _, _, runs, *_ = scenario
    # Fictional external receipt: these records are first delivered at LATE,
    # despite every source timestamp predating CUTOFF. Existing API has no slot.
    actual_receipt = LATE
    snapshot = resolve_real_observations(repo, dataset=DATASET, cutoff=CUTOFF)
    assert actual_receipt > CUTOFF
    # The legacy contract remains declared-time, not prospective-receipt proof.
    assert any(row.eligible_for_configuration_learning for row in snapshot.observations)


def bundle_for(scenario, monkeypatch):
    repo, task, _, _, _, _, corrected = scenario
    raw = portable.scoped_bundle(repo, task_id=task.task_id, dataset=DATASET)
    late_outcome = corrected[1]
    late_ids = {str(late_outcome.outcome_id), str(late_outcome.evidence_ids[0])}
    early = raw.model_copy(
        update={
            "entries": tuple(
                entry
                for entry in raw.entries
                if not any(identity in canonical(entry.record) for identity in late_ids)
            )
        }
    )
    book = portable.ReceiptBook()
    monkeypatch.setattr(portable, "utc_now", lambda: START + timedelta(minutes=10))
    book.capture(early)
    # Persist/reload receipt history; replay must not shift first knowledge.
    book = portable.ReceiptBook.model_validate_json(book.model_dump_json())
    monkeypatch.setattr(portable, "utc_now", lambda: LATE)
    book.capture(raw)
    book.capture(raw)
    return portable.scoped_bundle(
        repo, task_id=task.task_id, dataset=DATASET, receipts=book
    )


def roundtrip(bundle, tmp_path):
    path = tmp_path / "bundle.json"
    path.write_text(bundle.model_dump_json())
    restored_bundle = portable.EvidenceBundle.model_validate_json(path.read_text())
    restored = repository(tmp_path / "restored.sqlite")
    portable.import_bundle(restored, restored_bundle)
    return restored, restored_bundle


def producer_records(scenario):
    """Supported APIs create fictional declarations, never an executed task."""
    repo, task, _, _, attempts, *_ = scenario
    session = repo.create_session(
        Session(source=SOURCE, native_session_id="fixture-declaration-producer")
    )
    run = create_bounded_run(
        repo,
        task_id=task.task_id,
        session_id=session.session_id,
        started_at=START,
        ended_at=START + timedelta(minutes=1),
        final_artifact_fingerprint="sha256:" + hashlib.sha256(b"fictional").hexdigest(),
    )
    attempt = declare_attempt(
        repo,
        run_id=run.run_id,
        configuration=attempts[0].configuration,
        started_at=run.started_at,
        ended_at=run.ended_at,
    )
    return run, attempt


def test_producer_declaration_metadata_roundtrip(scenario, tmp_path):
    source, task, other, *_ = scenario
    run, attempt = producer_records(scenario)
    assert run.metadata["boundary_source"] == "human_declaration"
    assert attempt.metadata == {
        "configuration_provenance": "human_declaration",
        "boundary_source": "human_declaration",
        "declaration_source": "human",
    }
    raw = portable.scoped_bundle(source, task_id=task.task_id, dataset=DATASET)
    for record in (run, attempt):
        entry = next(
            e for e in raw.entries if portable.key(e.parse()) == portable.key(record)
        )
        assert entry.parse() == record
    assert all(entry.received_at is None for entry in raw.entries)
    assert not portable.resolve_bundle(raw, cutoff=CUTOFF).observations
    restored, copied = roundtrip(raw, tmp_path)
    portable.import_bundle(restored, copied)
    for kind, record in ((Run, run), (Attempt, attempt)):
        assert (
            restored.get(kind, getattr(record, kind.__name__.lower() + "_id")) == record
        )
    assert source.get(Run, run.run_id) == run
    assert source.get(Attempt, attempt.attempt_id) == attempt
    assert str(other.task_id) not in copied.model_dump_json()


@pytest.mark.parametrize("kind", [Run, Attempt])
def test_producer_declarations_still_reject_unknown_metadata(scenario, kind):
    records = dict(zip((Run, Attempt), producer_records(scenario), strict=True))
    record = records[kind]
    changed = record.model_copy(
        update={"metadata": record.metadata | {"unknown_extra": "fictional"}}
    )
    with pytest.raises(ValueError, match="unsupported public metadata"):
        portable._public(changed)


@pytest.mark.parametrize(
    "kind,field",
    [
        (Run, "boundary_source"),
        (Attempt, "boundary_source"),
        (Attempt, "declaration_source"),
    ],
)
@pytest.mark.parametrize(
    "value", ["custom", "", None, 1, True, ["human"], {"source": "human"}]
)
def test_public_declaration_values_are_exact(scenario, kind, field, value):
    record = scenario[0].list_records(kind)[0]
    changed = record.model_copy(update={"metadata": record.metadata | {field: value}})
    with pytest.raises(ValueError, match="unsupported public declaration metadata"):
        portable._public(changed)


def test_a_e_association_roundtrip_idempotence(scenario, tmp_path, monkeypatch):
    source, task, other, runs, attempts, *_ = scenario
    bundle = bundle_for(scenario, monkeypatch)
    restored, copied = roundtrip(bundle, tmp_path)
    portable.import_bundle(restored, copied)
    assert [r.task_id for r in restored.list_tasks()] == [task.task_id]
    assert str(other.task_id) not in copied.model_dump_json()
    for run, attempt in zip(runs, attempts, strict=True):
        assert restored.get(Run, run.run_id) == run
        assert restored.get(Attempt, attempt.attempt_id) == attempt
        assert restored.list_run_session_links(
            run.run_id
        ) == source.list_run_session_links(run.run_id)
    assert restored.list_task_session_links(
        task.task_id
    ) == source.list_task_session_links(task.task_id)
    assert len(restored.list_observations("real")) == 5
    state = portable.resolve_bundle(copied, cutoff=LATE)
    assert sum(r.eligible_for_configuration_learning for r in state.observations) == 2


def test_c_d_receipt_cutoff_correction_and_history(scenario, monkeypatch):
    _, _, _, runs, _, initial, corrected = scenario
    bundle = bundle_for(scenario, monkeypatch)
    before = portable.resolve_bundle(bundle, cutoff=CUTOFF)
    after = portable.resolve_bundle(bundle, cutoff=LATE)
    earlier = next(s for s in before.assessments if s.run_id == runs[1].run_id)
    later = next(s for s in after.assessments if s.run_id == runs[1].run_id)
    assert earlier.outcome == initial[1]
    assert later.outcome == corrected[1]
    assert sum(r.eligible_for_configuration_learning for r in before.observations) == 1
    assert sum(r.eligible_for_configuration_learning for r in after.observations) == 2
    assert len([e for e in bundle.entries if e.record_type == "Outcome"]) == 5
    assert portable.resolve_bundle(bundle, cutoff=CUTOFF) == before
    no_receipts = bundle.model_copy(
        update={
            "entries": tuple(
                e.model_copy(update={"received_at": None}) for e in bundle.entries
            )
        }
    )
    assert not portable.resolve_bundle(no_receipts, cutoff=LATE).observations


def changed(bundle, kind, mutate):
    entries = list(bundle.entries)
    index = next(i for i, e in enumerate(entries) if e.record_type == kind.__name__)
    entry = entries[index]
    data = json.loads(json.dumps(entry.record))
    mutate(data)
    if kind is Observation:
        data["stable_key"] = None
    record = kind.model_validate(data)
    entries[index] = portable.Entry(
        record_type=kind.__name__,
        record=record.model_dump(mode="json"),
        sha256=portable._digest(record),
        received_at=entry.received_at,
    )
    return bundle.model_copy(update={"entries": tuple(entries)})


@pytest.mark.parametrize("field", ["artifact", "report", "acceptance", "attempt"])
def test_b_reject_rebound_verification(scenario, tmp_path, monkeypatch, field):
    bundle = bundle_for(scenario, monkeypatch)
    if field == "attempt":
        binding = dict(bundle.verification_attempts)
        binding[next(iter(binding))] = scenario[4][1].attempt_id
        invalid = bundle.model_copy(update={"verification_attempts": binding})
    else:

        def mutate(data):
            if field == "artifact":
                data["artifact_fingerprint"] = "sha256:" + "0" * 64
            elif field == "report":
                data["metadata"]["binding"]["report_sha256"] = "0" * 64
            else:
                data["acceptance_spec"]["version"] = "2"

        invalid = changed(bundle, Verification, mutate)
    destination = repository(tmp_path / "reject.sqlite")
    with pytest.raises((ValueError, StorageError)):
        portable.import_bundle(destination, invalid)
    assert not destination.list_tasks()


@pytest.mark.parametrize(
    "damage", ["dangling", "configuration", "root", "branch", "foreign_session"]
)
def test_f_invalid_associations(scenario, tmp_path, monkeypatch, damage):
    bundle = bundle_for(scenario, monkeypatch)
    if damage == "dangling":
        invalid = changed(bundle, Attempt, lambda d: d.update(run_id=str(uuid4())))
    elif damage == "configuration":
        invalid = changed(
            bundle,
            Observation,
            lambda d: d.update(
                configuration=ExecutionConfiguration(model="incompatible").model_dump(
                    mode="json"
                )
            ),
        )
    elif damage == "foreign_session":
        invalid = changed(
            bundle, RunSessionLink, lambda d: d.update(session_id=str(uuid4()))
        )
    else:
        original = scenario[6][0]
        data = original.model_dump()
        data["outcome_id"] = uuid4()
        if damage == "root":
            data["supersedes_outcome_id"] = None
        record = Outcome.model_validate(data)
        invalid = bundle.model_copy(
            update={
                "entries": (
                    *bundle.entries,
                    portable.Entry(
                        record_type="Outcome",
                        record=record.model_dump(mode="json"),
                        sha256=portable._digest(record),
                        received_at=LATE,
                    ),
                )
            }
        )
    destination = repository(tmp_path / "reject.sqlite")
    with pytest.raises((ValueError, StorageError)):
        portable.import_bundle(destination, invalid)
    assert not destination.list_tasks()


def test_f_existing_identity_cannot_be_rebound(scenario, tmp_path, monkeypatch):
    bundle = bundle_for(scenario, monkeypatch)
    destination = repository(tmp_path / "conflict.sqlite")
    other = scenario[2]
    destination.create_task(other)
    destination.create_run(scenario[3][0].model_copy(update={"task_id": other.task_id}))
    with pytest.raises(StorageError, match="conflicts"):
        portable.import_bundle(destination, bundle)
    assert destination.list_tasks() == [other]


def test_g_unknown_remains_unknown(scenario, monkeypatch):
    bundle = bundle_for(scenario, monkeypatch)
    state = portable.resolve_bundle(bundle, cutoff=LATE)
    row = next(r for r in state.observations if r.run_id == scenario[3][2].run_id)
    assert row.outcome_status.value == "unknown"
    assert not row.eligible_for_configuration_learning
    assert row.label_available_at is None
    assert row.cost_usd is None


def test_h_frozen_forecast_reconstructs_exact_membership(
    scenario, tmp_path, monkeypatch
):
    bundle = bundle_for(scenario, monkeypatch)
    _, restored = roundtrip(bundle, tmp_path)
    task, target = scenario[1:3]
    configurations = [a.configuration for a in scenario[4][:2]]
    policy = CompatibilityPolicy(
        "synthetic-policy/v1",
        START,
        DATASET.model_dump_json(),
        task.acceptance_spec.model_dump_json(),
        "null",
        tuple(
            ConfigurationMember(c.model_dump_json(), c.reasoning_level)
            for c in configurations
        ),
        (
            TaskMember(str(task.task_id), "synthetic-group", "fixture"),
            TaskMember(str(target.task_id), "synthetic-group", "fixture"),
        ),
    )
    # A separate fictional prediction target is explicitly declared; its unrelated
    # source records are not included in the selected evidence export.
    kwargs = dict(
        policy=policy,
        task_id=target.task_id,
        run_id=uuid4(),
        configuration=configurations[0],
        cutoff=CUTOFF,
    )
    original = forecast(
        portable.resolve_bundle(bundle, cutoff=CUTOFF).observations, **kwargs
    )
    path = tmp_path / "frozen.json"
    fingerprint = freeze(path, original)
    frozen_bytes = path.read_bytes()
    policy_file = tmp_path / "policy.json"
    policy_file.write_bytes(TypeAdapter(CompatibilityPolicy).dump_json(policy))
    restored_policy = TypeAdapter(CompatibilityPolicy).validate_json(
        policy_file.read_bytes()
    )
    assert restored_policy.fingerprint == policy.fingerprint
    kwargs["policy"] = restored_policy
    reconstructed = forecast(
        portable.resolve_bundle(restored, cutoff=CUTOFF).observations, **kwargs
    )
    assert reconstructed == original
    assert original.predictions[0].probability == 2 / 3
    assert len(original.predictions[0].evidence_keys) == 1
    assert original.task_id == str(target.task_id)
    assert original.configuration_id == configurations[0].configuration_id
    assert original.acceptance_json == task.acceptance_spec.model_dump_json()
    assert json.loads(frozen_bytes) == json.loads(canonical(asdict(reconstructed)))
    portable.resolve_bundle(restored, cutoff=LATE)
    assert path.read_bytes() == frozen_bytes
    assert hashlib.sha256(frozen_bytes).hexdigest() == fingerprint


def test_i_public_projection_removes_locators_and_unrelated_data(scenario, monkeypatch):
    bundle = bundle_for(scenario, monkeypatch)
    text = bundle.model_dump_json()
    assert "Fictional unrelated task" not in text
    assert str(scenario[2].task_id) not in text
    assert str(Path.home()) not in text
    assert "/private/" not in text
    assert "fictional artifact" not in text
    assert "<testsuite" not in text
    for entry in bundle.entries:
        if entry.record_type == "Verification":
            assert entry.record["report_reference"].startswith("sha256:")
            assert entry.record["artifact_reference"].startswith("sha256:")


@pytest.mark.parametrize(
    "kind,field,value",
    [
        (Event, "payload", {"tool_output": "fictional private tool contents"}),
        (
            Event,
            "raw_payload",
            {"messages": [{"role": "user", "content": "fictional"}]},
        ),
        (Task, "metadata", {"private_prompt": "fictional private request"}),
        (Session, "native_session_id", "Bearer fictional-credential"),
    ],
)
def test_i_unsupported_public_content_rejected(scenario, kind, field, value):
    record = scenario[0].list_records(kind)[0]
    data = record.model_dump()
    data[field] = value
    with pytest.raises(ValueError):
        portable._public(kind.model_validate(data))


@pytest.mark.parametrize(
    "kind",
    [
        Task,
        Session,
        Run,
        Attempt,
        Event,
        Verification,
        Outcome,
        Observation,
        TaskSessionLink,
        RunSessionLink,
    ],
)
def test_c_every_late_dependency_blocks_early_learning(scenario, monkeypatch, kind):
    bundle = bundle_for(scenario, monkeypatch)
    # Delay all records of a type, including the original assessment if relevant.
    late = bundle.model_copy(
        update={
            "entries": tuple(
                e.model_copy(update={"received_at": LATE})
                if e.record_type == kind.__name__
                else e
                for e in bundle.entries
            )
        }
    )
    state = portable.resolve_bundle(late, cutoff=CUTOFF)
    assert not any(r.eligible_for_configuration_learning for r in state.observations)
    assert (
        sum(
            r.eligible_for_configuration_learning
            for r in portable.resolve_bundle(late, cutoff=LATE).observations
        )
        == 2
    )


def test_d_received_correction_with_late_verification_has_no_label_fallback(
    scenario, monkeypatch
):
    bundle = bundle_for(scenario, monkeypatch)
    # Correction is received before its verification: resolve the head but refuse
    # to train it; an older derivation cannot substitute for the missing evidence.
    verification_id = str(scenario[6][0].evidence_ids[0])
    bundle = bundle.model_copy(
        update={
            "entries": tuple(
                e.model_copy(update={"received_at": LATE})
                if e.record_type == "Verification"
                and e.record["verification_id"] == verification_id
                else e
                for e in bundle.entries
            )
        }
    )
    state = portable.resolve_bundle(bundle, cutoff=CUTOFF)
    assert not any(r.run_id == scenario[3][0].run_id for r in state.observations)
    assert any(
        "unavailable" in reason
        for exclusion in state.exclusions
        for reason in exclusion.reasons
    )


def test_f_dangling_observation_proof_rejected(scenario, tmp_path, monkeypatch):
    bundle = bundle_for(scenario, monkeypatch)
    invalid = changed(
        bundle, Observation, lambda d: d["metadata"].update(event_ids=[str(uuid4())])
    )
    with pytest.raises(StorageError, match="dangling"):
        portable.import_bundle(repository(tmp_path / "bad.sqlite"), invalid)


def test_receipt_replay_and_digest_integrity(scenario, monkeypatch):
    bundle = bundle_for(scenario, monkeypatch)
    book = portable.ReceiptBook()
    monkeypatch.setattr(portable, "utc_now", lambda: LATE)
    book.capture(bundle)
    assert all(time == LATE for _, time in book.receipts.values())
    first = book.model_dump_json()
    monkeypatch.setattr(portable, "utc_now", lambda: LATE + timedelta(days=1))
    book.capture(bundle)
    assert book.model_dump_json() == first
    bad = changed(bundle, Session, lambda d: d.update(native_session_id="rebound"))
    with pytest.raises(ValueError, match="rebound"):
        book.capture(bad)
    entry = bundle.entries[0].model_copy(update={"sha256": "0" * 64})
    with pytest.raises(ValueError, match="digest"):
        entry.parse()


def test_i_repository_privacy_guard_accepts_synthetic_bundle(scenario, monkeypatch):
    import runpy

    guard = runpy.run_path(str(Path(__file__).parents[2] / "scripts/privacy_guard.py"))
    bundle = bundle_for(scenario, monkeypatch)
    assert not guard["secret_reasons"](bundle.model_dump_json().encode())
    assert not guard["content_reasons"](bundle.model_dump_json().encode())


@pytest.mark.parametrize(
    "report_body",
    [
        '<testsuite tests="1" failures="0" errors="0" skipped="1">'
        '<testcase classname="fixture" name="case"><skipped/></testcase></testsuite>',
        "<unsupported-report/>",
    ],
)
def test_g_incomplete_and_unsupported_reports_remain_unknown(
    scenario,
    tmp_path,
    monkeypatch,
    report_body,
):
    repo, task, _, runs, _, _, corrected = scenario
    run = runs[0]
    report = tmp_path / "incomplete.xml"
    report.write_text(report_body)
    evidence = verify_junit(
        repo,
        run_id=run.run_id,
        artifact=tmp_path / "artifact-0.txt",
        report=report,
        binding=JUnitReportBinding(
            task_id=task.task_id,
            run_id=run.run_id,
            acceptance_spec=task.acceptance_spec,
            artifact_fingerprint=run.metadata["final_artifact_fingerprint"],
            report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
            report_generated_at=run.ended_at,
            source="junit",
            execution_completed=True,
            command_exit_code=0,
        ),
        observed_at=START + timedelta(minutes=6),
    )
    unknown = assess_run(
        repo,
        run_id=run.run_id,
        verification_id=evidence.verification_id,
        supersedes_outcome_id=corrected[0].outcome_id,
        recorded_at=START + timedelta(minutes=7),
    )
    build_real_observation(
        repo,
        run_id=run.run_id,
        outcome_id=unknown.outcome_id,
        dataset=DATASET,
        recorded_at=START + timedelta(minutes=7),
    )
    state = portable.resolve_bundle(bundle_for(scenario, monkeypatch), cutoff=LATE)
    row = next(r for r in state.observations if r.run_id == run.run_id)
    assert row.outcome_status.value == "unknown"
    assert not row.eligible_for_configuration_learning
    assert row.label_available_at is None


def test_f_destination_requires_empty_or_exact_replay(scenario, monkeypatch, tmp_path):
    bundle = bundle_for(scenario, monkeypatch)
    destination = repository(tmp_path / "partial.sqlite")
    task = next(e.parse() for e in bundle.entries if e.record_type == "Task")
    destination.create_task(task)
    with pytest.raises(StorageError, match="empty or an exact scoped replay"):
        portable.import_bundle(destination, bundle)
    assert not destination.list_records(Run)


def test_f_event_cannot_be_rebound_to_another_run(scenario, monkeypatch, tmp_path):
    bundle = bundle_for(scenario, monkeypatch)
    invalid = changed(
        bundle, Event, lambda d: d.update(run_id=str(scenario[3][1].run_id))
    )
    with pytest.raises(StorageError, match="foreign observation event"):
        portable.import_bundle(repository(tmp_path / "bad-event.sqlite"), invalid)
