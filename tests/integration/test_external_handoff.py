"""W6B fictional data only; no agent, generated-code execution, network or Git.

Reports come from the reviewed data-only fixture in the executable example.
These tests establish offline interface integration, never external authenticity.
"""

import hashlib
import json
import math
import runpy
from dataclasses import asdict
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import TypeAdapter
from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    Event,
    Observation,
    Outcome,
    ResourceBudget,
    Run,
    Session,
    Task,
    Verification,
    utc_now,
)
from model_learner.learn.advisory import AdvisoryInput, advise
from model_learner.learn.estimator import BetaBernoulli
from model_learner.learn.prospective import CompatibilityPolicy, forecast, score_frozen
from model_learner.observations import build_real_observation
from model_learner.storage import evidence as portable
from model_learner.storage.database import StorageError
from model_learner.verification import assess_run, verify_junit
from scripts import external_handoff_example as example


@pytest.fixture
def intake(tmp_path):
    task = example.declare()
    directory = tmp_path / "handoff"
    source, run = example.produce(directory, task, uuid4())
    receiver, book = example.receive_execution(directory, task, run.run_id)
    binding = example.trusted_report(directory, task, run)
    return directory, task, source, run, receiver, book, binding


@pytest.fixture
def completed(intake):
    directory, _, _, run, receiver, book, binding = intake
    row, bundle = example.verify_and_receive(receiver, book, directory, run, binding)
    return intake, row, bundle


def verify(intake, binding=None):
    directory, _, _, run, receiver, _, original = intake
    return verify_junit(
        receiver,
        run_id=run.run_id,
        artifact=directory / "answer.txt",
        report=directory / "independent.xml",
        binding=binding or original,
    )


def replace_record(bundle, kind, update):
    entries = list(bundle.entries)
    index = next(i for i, e in enumerate(entries) if e.record_type == kind.__name__)
    record = entries[index].parse()
    data = record.model_dump(mode="json")
    update(data)
    changed = kind.model_validate(data)
    entries[index] = entries[index].model_copy(
        update={
            "record": changed.model_dump(mode="json"),
            "sha256": portable._digest(changed),
        }
    )
    return bundle.model_copy(update={"entries": tuple(entries)})


def file_hashes(root):
    return {
        str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
        for p in root.rglob("*")
        if p.is_file()
    }


def test_p1_p12_complete_operator_workflow(tmp_path):
    summary = example.demonstrate(tmp_path)
    assert summary["eligible_outcomes"] == 2
    assert summary["forecast_probabilities"] == [0.5, 2 / 3]
    envelope = AdvisoryInput.model_validate_json(
        (tmp_path / "advisory-input.json").read_text()
    )
    before = file_hashes(tmp_path)
    result = advise(envelope.request, bundles=envelope.bundles)
    assert result == json.loads((tmp_path / "advisory.json").read_text())
    assert result["eligible_source_count"] == 2
    estimates = {p["predictor"]: p for p in result["candidates"][0]["estimates"]}
    assert result["advisory"]["status"] == "abstain"
    for name in ("global", "per_arm", "A", "B", "C"):
        assert estimates[name]["probability"] == 0.5
        assert estimates[name]["eligible_count"] == 2
        assert len(estimates[name]["evidence"]) == 2
    command = CliRunner().invoke(
        app, ["learn", "advise", "--input-file", str(tmp_path / "advisory-input.json")]
    )
    assert command.exit_code == 0, command.output
    assert json.loads(command.output) == result
    assert file_hashes(tmp_path) == before  # actual producer/receiver/forecast bytes
    prior_rows = []
    policy = TypeAdapter(CompatibilityPolicy).validate_json(
        (tmp_path / "policy.json").read_bytes()
    )
    intake = json.loads((tmp_path / "intake.json").read_text())
    for i, bundle in enumerate(envelope.bundles):
        frozen_path = tmp_path / f"forecast-{i}.json"
        frozen = json.loads(frozen_path.read_text())
        cutoff = datetime.fromisoformat(frozen["cutoff"])
        assert (tmp_path / f"forecast-{i}.sha256").read_text().strip() == summary[
            "forecast_sha256"
        ][i]
        selected = Task.model_validate(intake["tasks"][i])
        assert portable._digest(selected) == portable._digest(
            next(e.parse() for e in bundle.entries if e.record_type == "Task")
        )
        assert selected.created_at < cutoff
        run = next(e.parse() for e in bundle.entries if e.record_type == "Run")
        assert cutoff < run.started_at < run.ended_at
        assert example.CONFIG.configuration_id == frozen["configuration_id"]
        reconstructed = forecast(
            [
                row
                for prior in envelope.bundles[:i]
                for row in portable.resolve_bundle(prior, cutoff=cutoff).observations
            ],
            policy=policy,
            task_id=run.task_id,
            run_id=run.run_id,
            configuration=example.CONFIG,
            cutoff=cutoff,
        )
        assert json.loads(json.dumps(asdict(reconstructed))) == frozen
        rows = portable.resolve_bundle(
            bundle, cutoff=envelope.request.cutoff
        ).observations
        assert len(rows) == 1 and rows[0].eligible_for_configuration_learning
        assert rows[0].outcome_status.value == ("success" if i == 0 else "failure")
        assert rows[0].cost_usd is rows[0].latency_seconds is None
        assert not portable.resolve_bundle(bundle, cutoff=cutoff).observations
        scores = score_frozen(frozen_path, summary["forecast_sha256"][i], rows[0])
        probability, label = frozen["predictions"][0]["probability"], 1 - i
        for score in scores.values():
            assert score["brier_score"] == pytest.approx((probability - label) ** 2)
            assert score["log_loss"] == pytest.approx(
                -math.log(probability if label else 1 - probability)
            )
        assert scores == summary["scores"][i]
        # Scoped reconstruction and exact replay preserve all associations.
        restored = example.repository(tmp_path / f"reconstructed-{i}.sqlite")
        portable.import_bundle(restored, bundle)
        portable.import_bundle(restored, bundle)
        attempt = restored.list_records(Attempt)[0]
        assert bundle.verification_attempts == {
            restored.list_records(Verification)[0].verification_id: attempt.attempt_id
        }
        assert attempt.run_id == run.run_id and attempt.configuration == example.CONFIG
        assert len(restored.list_run_session_links(run.run_id)) == 1
        assert len(restored.list_task_session_links(run.task_id)) == 1
        assert len(restored.list_records(Session)) == 1
        assert len(restored.list_records(Event)) == 4
        book = portable.ReceiptBook.model_validate_json(
            (tmp_path / f"handoff-{i}" / "receipts.json").read_text()
        )
        assert (
            portable.scoped_bundle(
                restored, task_id=run.task_id, dataset=example.DATASET, receipts=book
            )
            == bundle
        )
        prior_rows.extend(rows)
    estimator = BetaBernoulli.fit(
        prior_rows * 2,
        dataset=example.DATASET,
        cutoff=envelope.request.cutoff,
        acceptance_spec=example.SPEC,
    )
    posterior = estimator.predict(example.CONFIG, "fictional-data")
    assert (posterior.successes, posterior.failures, posterior.success_probability) == (
        1,
        1,
        0.5,
    )
    assert estimator.training_summary.eligible_label_count == 2
    assert estimator.training_summary.excluded["duplicate"] == 2


def test_p5_receipts_are_receiver_observations_and_replay_is_stable(completed):
    intake, row, bundle = completed
    directory, _, _, run, receiver, book, _ = intake
    execution_book = portable.ReceiptBook.model_validate_json(
        (directory / "execution-receipts.json").read_text()
    )
    assert all(time > run.ended_at for _, time in execution_book.receipts.values())
    assert all(
        e.received_at >= e.parse().ingested_at
        for e in bundle.entries
        if e.record_type == "Event"
    )
    original = book.model_dump_json()
    book.capture(bundle)
    assert book.model_dump_json() == original
    assert (
        build_real_observation(
            receiver,
            run_id=run.run_id,
            outcome_id=row.outcome_id,
            dataset=example.DATASET,
        )
        == row
    )
    assert len(receiver.list_records(Observation, source_kind="real")) == 1


def test_n1_completion_claim_and_exit_zero_are_unknown(intake):
    _, _, _, run, receiver, *_ = intake
    outcome = assess_run(receiver, run_id=run.run_id)
    row = build_real_observation(
        receiver,
        run_id=run.run_id,
        outcome_id=outcome.outcome_id,
        dataset=example.DATASET,
    )
    assert row.outcome_status.value == "unknown"
    assert not row.eligible_for_configuration_learning
    assert not receiver.list_records(Verification)


@pytest.mark.parametrize("claim", ["verification", "receipt"])
def test_n1_fixture_boundary_refuses_producer_authority(completed, claim):
    intake, _, bundle = completed
    directory, task, _, run, *_ = intake
    package = (
        bundle
        if claim == "verification"
        else portable.EvidenceBundle.model_validate_json(
            (directory / "execution.json").read_text()
        ).model_copy(
            update={
                "entries": tuple(
                    e
                    for e in bundle.entries
                    if e.record_type not in {"Verification", "Outcome", "Observation"}
                )
            }
        )
    )
    (directory / "execution.json").write_text(package.model_dump_json())
    before = file_hashes(directory)
    with pytest.raises(ValueError, match="execution-only"):
        example.receive_execution(directory, task, run.run_id)
    assert file_hashes(directory) == before


@pytest.mark.parametrize(
    "field", ["artifact", "report", "acceptance", "task", "run", "missing_artifact"]
)
def test_n2_n3_bad_bindings_never_insert_verification(intake, field):
    directory, _, _, _, receiver, _, binding = intake
    updates = {
        "artifact": {"artifact_fingerprint": "sha256:" + "0" * 64},
        "report": {"report_sha256": "0" * 64},
        "acceptance": {
            "acceptance_spec": AcceptanceSpec(
                identifier=example.SPEC.identifier, version="2"
            )
        },
        "task": {"task_id": uuid4()},
        "run": {"run_id": uuid4()},
        "missing_artifact": {},
    }
    if field == "missing_artifact":
        (directory / "answer.txt").unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        verify(intake, binding.model_copy(update=updates[field]))
    assert not receiver.list_records(Verification)


@pytest.mark.parametrize(
    "body",
    [
        '<testsuite tests="1" failures="0" errors="0" skipped="1">'
        '<testcase classname="fixture" name="exact_answer">'
        "<skipped/></testcase></testsuite>",
        '<testsuite tests="1" failures="0" errors="0" skipped="0">'
        '<testcase classname="fixture" name="other"/></testsuite>',
        "<broken",
        "<unsupported/>",
    ],
)
def test_n4_incomplete_reports_are_unknown(intake, body):
    directory, _, _, run, receiver, _, binding = intake
    (directory / "independent.xml").write_text(body)
    evidence = verify(
        intake,
        binding.model_copy(
            update={"report_sha256": example.file_sha256(directory / "independent.xml")}
        ),
    )
    assert evidence.result.value == "indeterminate"
    outcome = assess_run(
        receiver, run_id=run.run_id, verification_id=evidence.verification_id
    )
    row = build_real_observation(
        receiver,
        run_id=run.run_id,
        outcome_id=outcome.outcome_id,
        dataset=example.DATASET,
    )
    assert (
        row.outcome_status.value == "unknown"
        and not row.eligible_for_configuration_learning
    )


@pytest.mark.parametrize(
    "kind,mutate",
    [
        (Verification, lambda d: d.update(artifact_fingerprint="sha256:" + "0" * 64)),
        (
            Verification,
            lambda d: d["metadata"]["binding"].update(report_sha256="0" * 64),
        ),
        (Verification, lambda d: d["acceptance_spec"].update(version="2")),
        (Run, lambda d: d.update(task_id=str(uuid4()))),
    ],
)
def test_n14_bad_serialized_bundle_leaves_destination_empty(
    completed, tmp_path, kind, mutate
):
    _, _, bundle = completed
    invalid = replace_record(bundle, kind, mutate)
    destination = example.repository(tmp_path / "reject.sqlite")
    with pytest.raises((ValueError, StorageError)):
        portable.import_bundle(destination, invalid)
    assert not destination.list_tasks()


@pytest.mark.parametrize("change", ["task", "run", "acceptance", "configuration"])
def test_p1_frozen_intake_cannot_be_rebound(intake, change):
    directory, task, _, run, *_ = intake
    approved = task
    approved_run = run.run_id
    if change == "task":
        approved = task.model_copy(update={"task_id": uuid4()})
    elif change == "run":
        approved_run = uuid4()
    elif change == "acceptance":
        approved = task.model_copy(
            update={"acceptance_spec": AcceptanceSpec(identifier="other", version="1")}
        )
    else:
        package = portable.EvidenceBundle.model_validate_json(
            (directory / "execution.json").read_text()
        )

        def mutate(data):
            data["configuration"]["model"] = "other"
            data["configuration"]["configuration_id"] = None

        (directory / "execution.json").write_text(
            replace_record(package, Attempt, mutate).model_dump_json()
        )
    before = file_hashes(directory)
    with pytest.raises(ValueError, match="frozen intake"):
        example.receive_execution(directory, approved, approved_run)
    assert file_hashes(directory) == before


def test_n5_reported_model_conflict_retained_unknown(tmp_path):
    task, directory = example.declare(), tmp_path / "conflict"
    _, run = example.produce(directory, task, uuid4(), emitted_model="other-model")
    receiver, book = example.receive_execution(directory, task, run.run_id)
    row, bundle = example.verify_and_receive(
        receiver, book, directory, run, example.trusted_report(directory, task, run)
    )
    assert not row.eligible_for_configuration_learning
    assert (
        "declared_configuration_conflicts_with_native_telemetry"
        in row.metadata["exclusions"]
    )
    assert (
        not portable.resolve_bundle(bundle, cutoff=utc_now())
        .observations[0]
        .eligible_for_configuration_learning
    )


@pytest.mark.parametrize(
    "kind", list(portable.KINDS) + [portable.TaskSessionLink, portable.RunSessionLink]
)
def test_n6_missing_or_delayed_dependency_is_unavailable(completed, kind):
    _, _, bundle = completed
    cutoff = utc_now()
    for receipt in (None, cutoff + timedelta(days=1)):
        delayed = bundle.model_copy(
            update={
                "entries": tuple(
                    e.model_copy(update={"received_at": receipt})
                    if e.record_type == kind.__name__
                    else e
                    for e in bundle.entries
                )
            }
        )
        assert not any(
            o.eligible_for_configuration_learning
            for o in portable.resolve_bundle(delayed, cutoff=cutoff).observations
        )


def test_n7_correction_preserves_retained_forecast(completed, tmp_path):
    intake, _, bundle = completed
    directory, task, _, run, receiver, book, _ = intake
    later = example.declare()
    policy = example.policy_for([task, later])
    cutoff = utc_now()
    original = forecast(
        portable.resolve_bundle(bundle, cutoff=cutoff).observations,
        policy=policy,
        task_id=later.task_id,
        run_id=uuid4(),
        configuration=example.CONFIG,
        cutoff=cutoff,
    )
    from model_learner.learn.prospective import freeze

    frozen = tmp_path / "frozen.json"
    checksum = freeze(frozen, original)
    previous = receiver.list_records(Outcome)[0]
    correction = receiver.add_outcome(
        Outcome(
            run_id=run.run_id,
            status="unknown",
            verification_status="unverified",
            assessment_source="human",
            supersedes_outcome_id=previous.outcome_id,
        )
    )
    build_real_observation(
        receiver,
        run_id=run.run_id,
        outcome_id=correction.outcome_id,
        dataset=example.DATASET,
    )
    book.capture(
        portable.scoped_bundle(receiver, task_id=task.task_id, dataset=example.DATASET)
    )
    latest = portable.scoped_bundle(
        receiver, task_id=task.task_id, dataset=example.DATASET, receipts=book
    )
    assert portable.resolve_bundle(latest, cutoff=cutoff) == portable.resolve_bundle(
        bundle, cutoff=cutoff
    )
    assert (
        not portable.resolve_bundle(latest, cutoff=utc_now())
        .observations[0]
        .eligible_for_configuration_learning
    )
    assert hashlib.sha256(frozen.read_bytes()).hexdigest() == checksum
    assert original.predictions[0].probability == 2 / 3


def test_n9_target_other_arm_unadmitted_and_future_excluded(completed):
    intake, row, _ = completed
    _, task, *_ = intake
    policy = example.policy_for([task])
    cutoff = utc_now()
    target_arm = row.model_copy(
        update={
            "configuration": example.CONFIG.model_copy(
                update={"reasoning_level": "high"}
            ),
            "stable_key": "other-arm",
            "observation_id": uuid4(),
            "run_id": uuid4(),
        }
    )
    unrelated = row.model_copy(
        update={
            "task_id": uuid4(),
            "run_id": uuid4(),
            "stable_key": "unrelated",
            "observation_id": uuid4(),
        }
    )
    future = row.model_copy(
        update={"recorded_at": cutoff + timedelta(days=1), "stable_key": "future"}
    )
    prediction = forecast(
        [row, target_arm, unrelated, future],
        policy=policy,
        task_id=task.task_id,
        run_id=uuid4(),
        configuration=example.CONFIG,
        cutoff=cutoff,
    )
    assert all(
        not p.evidence_keys and p.probability == 0.5 for p in prediction.predictions
    )
    assert dict(prediction.exclusions)["prediction_task"] == 2
    assert dict(prediction.exclusions)["not_admitted_by_policy"] == 1
    assert dict(prediction.exclusions)["not_available_at_cutoff"] == 1


def test_n11_unsupported_nonnull_budget_stays_ineligible(tmp_path):
    task, directory = example.declare(), tmp_path / "budget"
    _, run = example.produce(
        directory, task, uuid4(), budget=ResourceBudget(max_duration_seconds=600)
    )
    receiver, book = example.receive_execution(directory, task, run.run_id)
    row, _ = example.verify_and_receive(
        receiver, book, directory, run, example.trusted_report(directory, task, run)
    )
    assert row.latency_seconds is row.cost_usd is None
    assert row.resource_budget.max_duration_seconds == 600
    assert not row.eligible_for_configuration_learning
    assert "budget_duration_unknown" in row.metadata["exclusions"]


def test_n12_metadata_projection_and_pure_privacy(completed):
    intake, _, bundle = completed
    directory, _, source, *_ = intake
    unrelated = source.create_task(example.declare())
    encoded = bundle.model_dump_json()
    for forbidden in (
        str(directory),
        str(Path.home()),
        str(unrelated.task_id),
        "Fictional pass self-report",
        "<testsuite",
        "42\\n",
        "messages",
    ):
        assert forbidden not in encoded
    guard = runpy.run_path(str(Path(__file__).parents[2] / "scripts/privacy_guard.py"))
    assert not guard["content_reasons"](encoded.encode())
    assert not guard["secret_reasons"](encoded.encode())


@pytest.mark.parametrize("state", ["abandoned", "unknown", "incomplete"])
def test_n10_unverified_stops_remain_unknown(tmp_path, state):
    task, directory = example.declare(), tmp_path / "unfinished"
    _, run = example.produce(directory, task, uuid4())
    package = portable.EvidenceBundle.model_validate_json(
        (directory / "execution.json").read_text()
    )
    if state == "incomplete":
        package = replace_record(package, Attempt, lambda d: d.update(ended_at=None))
    else:
        package = replace_record(package, Run, lambda d: d.update(state=state))
    (directory / "execution.json").write_text(package.model_dump_json())
    receiver, _ = example.receive_execution(directory, task, run.run_id)
    outcome = assess_run(receiver, run_id=run.run_id)
    row = build_real_observation(
        receiver,
        run_id=run.run_id,
        outcome_id=outcome.outcome_id,
        dataset=example.DATASET,
    )
    assert row.outcome_status.value == "unknown"
    assert row.label_available_at is None
    assert not row.eligible_for_configuration_learning


def test_n14_partial_live_merge_is_refused(completed, tmp_path):
    _, _, bundle = completed
    destination = example.repository(tmp_path / "partial.sqlite")
    task = next(e.parse() for e in bundle.entries if e.record_type == "Task")
    destination.create_task(task)
    with pytest.raises(StorageError, match="empty or an exact scoped replay"):
        portable.import_bundle(destination, bundle)
    assert destination.list_tasks() == [task]
    assert not destination.list_records(Run)
