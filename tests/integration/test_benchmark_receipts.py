"""Fresh fictional benchmark receipts; no model, candidate or private data reads."""

from datetime import timedelta

import pytest

import model_learner.benchmark.receipts as receipts
from model_learner.benchmark.evidence import _digest, export_benchmark_evidence
from model_learner.benchmark.receipts import (
    BenchmarkReceiptBook,
    BenchmarkReceiptBundle,
    benchmark_receipt_bundle,
)
from model_learner.domain.models import (
    Attempt,
    Outcome,
    ResourceBudget,
    RunState,
    Task,
    utc_now,
)
from model_learner.learn.estimator import BetaBernoulli
from tests.integration.test_benchmark_evidence import fixture


def test_initial_receipt_gap(tmp_path):
    prepared, _, result = fixture(
        tmp_path, resource_budget=ResourceBudget(max_duration_seconds=600)
    )
    evidence = export_benchmark_evidence(prepared.root)
    cutoff = utc_now()
    later_arrival = cutoff + timedelta(seconds=10)
    assert result.outcome.recorded_at < cutoff < later_arrival
    assert evidence.observation.outcome_status.value == "success"
    assert not evidence.observation.eligible_for_configuration_learning
    assert (
        "budget_measurements_not_supported"
        in evidence.observation.metadata["exclusions"]
    )
    # Originally red before implementation: the export has neither received nor
    # missing first-receipt states for its underlying Task/Run/Attempt evidence.
    assert "first_receipts" not in evidence.model_dump()
    bundle = benchmark_receipt_bundle(prepared.root, evidence)
    missing = BenchmarkReceiptBook(target=bundle.target).as_of(bundle, cutoff=cutoff)
    assert not missing.fully_available
    assert {reason for _, reason in missing.exclusions} == {"missing_receipt"}


@pytest.fixture
def scenario(tmp_path):
    prepared, repository, result = fixture(
        tmp_path, resource_budget=ResourceBudget(max_duration_seconds=600)
    )
    evidence = export_benchmark_evidence(prepared.root)
    bundle = benchmark_receipt_bundle(prepared.root, evidence)
    return prepared, repository, result, evidence, bundle


def recapture_bundle(values):
    """Rehash controlled synthetic mutations to test semantic validation too."""
    values["content_sha256"] = _digest(
        {k: v for k, v in values.items() if k != "content_sha256"}
    )
    return BenchmarkReceiptBundle.model_validate(values)


def test_a_b_c_j_k_o_capture_identity_budget_and_reconstruction(scenario, monkeypatch):
    prepared, repository, result, evidence, bundle = scenario
    now = utc_now()
    monkeypatch.setattr(receipts, "utc_now", lambda: now)
    empty = BenchmarkReceiptBook(target=bundle.target)
    book = empty.capture(bundle)
    assert empty.receipts == {}  # Atomic value semantics, even on later rejection.
    assert all(r.received_at == now for r in book.receipts.values())
    monkeypatch.setattr(receipts, "utc_now", lambda: now + timedelta(days=1))
    assert book.capture(bundle) == book
    encoded = bundle.model_dump_json()
    restored = BenchmarkReceiptBundle.model_validate_json(encoded)
    restored_book = BenchmarkReceiptBook.model_validate_json(book.model_dump_json())
    assert restored_book.capture(restored) == book
    view = book.as_of(bundle, cutoff=now)
    assert view == restored_book.as_of(restored, cutoff=now)
    assert view.fully_available
    assert len(view.available_records) == len(bundle.records) + 1
    assert view.target.source_kind == "benchmark"
    assert view.target.dataset_id == prepared.dataset.dataset_id
    assert view.target.dataset_version == prepared.dataset.dataset_version
    assert view.target.task_id == result.run.task_id
    assert view.target.configuration_id == prepared.configuration.configuration_id
    assert view.target.acceptance_version == prepared.task.acceptance_spec.version
    assert bundle.attempt_id == evidence.observation.attempt_id
    assert bundle.outcome_id == result.outcome.outcome_id
    assert bundle.observation_id == evidence.observation.observation_id
    assert bundle.export_sha256 == evidence.content_sha256
    assert view.target.resource_budget.max_duration_seconds == 600
    assert not view.exporter_eligible
    assert "budget_measurements_not_supported" in view.learning_exclusions
    assert evidence.observation.latency_seconds is None
    assert evidence.observation.cost_usd is None
    assert all(a.latency_seconds is None for a in repository.list_records(Attempt))
    for record in (prepared.task, result.run, result.outcome):
        binding = next(r for r in bundle.records if r.kind == type(record).__name__)
        assert binding.sha256 == _digest(record.model_dump(mode="json"))
    fitted = BetaBernoulli.fit(
        [evidence.observation],
        dataset=evidence.observation.dataset,
        acceptance_spec=prepared.task.acceptance_spec,
        resource_budget=ResourceBudget(max_duration_seconds=600),
        cutoff=now,
    )
    assert fitted.training_summary.eligible_label_count == 0
    assert (
        fitted.predict(
            prepared.configuration, evidence.observation.task_group
        ).sample_count
        == 0
    )


def test_e_late_local_receipt_does_not_backdate_source_times(scenario, monkeypatch):
    _, _, result, _, bundle = scenario
    cutoff = utc_now()
    late = cutoff + timedelta(seconds=10)
    monkeypatch.setattr(receipts, "utc_now", lambda: late)
    book = BenchmarkReceiptBook(target=bundle.target).capture(bundle)
    assert result.outcome.recorded_at < cutoff < late
    old = book.as_of(bundle, cutoff=cutoff)
    assert not old.available_records
    assert {reason for _, reason in old.exclusions} == {"received_after_cutoff"}
    assert book.as_of(bundle, cutoff=late).fully_available
    assert (
        next(r for r in bundle.records if r.kind == "Outcome").source_times[0].value
        == result.outcome.recorded_at
    )


@pytest.mark.parametrize(
    "kind",
    [
        "Task",
        "Run",
        "Attempt",
        "Configuration",
        "Acceptance",
        "Verification",
        "Outcome",
        "Observation",
        "Event",
        "Session",
        "TaskSessionLink",
        "RunSessionLink",
        "Export",
    ],
)
@pytest.mark.parametrize("missing", ["absent", "null", "late"])
def test_f_g_every_dependency_requires_first_receipt(
    scenario, monkeypatch, kind, missing
):
    *_, bundle = scenario
    now = utc_now()
    monkeypatch.setattr(receipts, "utc_now", lambda: now)
    book = BenchmarkReceiptBook(target=bundle.target).capture(bundle)
    values = book.model_dump(mode="json")
    identity = next(k for k in values["receipts"] if k.startswith(kind + ":"))
    if missing == "absent":
        del values["receipts"][identity]
    else:
        values["receipts"][identity]["received_at"] = (
            None if missing == "null" else (now + timedelta(seconds=10)).isoformat()
        )
    # Imported partial receiver logs are supported; no timestamps are inferred.
    partial = BenchmarkReceiptBook.model_validate(values)
    before = partial.as_of(bundle, cutoff=now)
    assert not before.fully_available
    assert (
        identity,
        "received_after_cutoff" if missing == "late" else "missing_receipt",
    ) in before.exclusions
    monkeypatch.setattr(receipts, "utc_now", lambda: now + timedelta(seconds=20))
    after = partial.capture(bundle)
    assert (
        after.as_of(bundle, cutoff=now) == before
        if missing == "late"
        else not after.as_of(bundle, cutoff=now).fully_available
    )
    assert after.as_of(bundle, cutoff=now + timedelta(seconds=20)).fully_available


def test_d_identity_conflict_rejects_atomically(scenario):
    *_, bundle = scenario
    book = BenchmarkReceiptBook(target=bundle.target).capture(bundle)
    original = book.model_dump_json()
    values = bundle.model_dump(mode="json")
    values["records"][0]["sha256"] = "a" * 64
    changed = recapture_bundle(values)
    with pytest.raises(ValueError, match="rebound"):
        book.capture(changed)
    with pytest.raises(ValueError, match="digest"):
        book.as_of(changed, cutoff=utc_now())
    assert book.model_dump_json() == original


def test_h_correction_receipt_preserves_earlier_export(scenario, monkeypatch):
    prepared, repository, result, _, bundle = scenario
    first = utc_now()
    monkeypatch.setattr(receipts, "utc_now", lambda: first)
    book = BenchmarkReceiptBook(target=bundle.target).capture(bundle)
    frozen = book.as_of(bundle, cutoff=first)
    correction = repository.add_outcome(
        Outcome(
            run_id=result.run.run_id,
            status="unknown",
            verification_status="unverified",
            assessment_source="human_assessment",
            supersedes_outcome_id=result.outcome.outcome_id,
        )
    )
    revised_export = export_benchmark_evidence(prepared.root)
    revised = benchmark_receipt_bundle(prepared.root, revised_export)
    assert revised.supersedes_outcome_id == result.outcome.outcome_id
    assert revised.outcome_id == correction.outcome_id
    assert not revised.exporter_eligible
    late = utc_now() + timedelta(seconds=10)
    monkeypatch.setattr(receipts, "utc_now", lambda: late)
    book = book.capture(revised)
    assert book.as_of(bundle, cutoff=first) == frozen
    assert not book.as_of(revised, cutoff=first).fully_available
    assert book.as_of(revised, cutoff=late).fully_available
    # Revision identities are audit evidence; neither snapshot is a second trial.
    assert len([k for k in book.receipts if k.startswith("Outcome:")]) == 2
    assert book.capture(revised) == book
    values = book.model_dump(mode="json")
    verification = next(k for k in values["receipts"] if k.startswith("Verification:"))
    del values["receipts"][verification]
    incomplete = BenchmarkReceiptBook.model_validate(values)
    assert not incomplete.as_of(revised, cutoff=late).fully_available
    # This adapter audits exact exports and never falls back to an old label or
    # supplies a new independently implemented assessment resolver/learner.


@pytest.mark.parametrize(
    "field,value",
    [
        ("task_id", "00000000-0000-0000-0000-000000000001"),
        ("run_id", "00000000-0000-0000-0000-000000000001"),
        ("dataset_id", "unrelated-fictional"),
        ("dataset_version", "999"),
        ("configuration_id", "a" * 64),
        ("acceptance_version", "999"),
    ],
)
def test_i_wrong_target_rejected(scenario, field, value):
    *_, bundle = scenario
    values = bundle.target.model_dump(mode="json")
    values[field] = value
    wrong = BenchmarkReceiptBook(target=values)
    with pytest.raises(ValueError, match="target"):
        wrong.capture(bundle)
    assert wrong.receipts == {}


@pytest.mark.parametrize(
    "field,value",
    [
        ("task_id", "00000000-0000-0000-0000-000000000001"),
        ("run_id", "00000000-0000-0000-0000-000000000001"),
        ("configuration_id", "a" * 64),
        ("acceptance_sha256", "a" * 64),
    ],
)
def test_i_wrong_record_association_rejected(scenario, field, value):
    *_, bundle = scenario
    values = bundle.model_dump(mode="json")
    values["records"][0][field] = value
    with pytest.raises(ValueError, match="association"):
        recapture_bundle(values)


def test_i_source_revalidation_checks_exact_export_and_artifact(scenario):
    prepared, _, _, evidence, _ = scenario
    values = evidence.model_dump(mode="json")
    values["fixture_id"] = "other"
    values["content_sha256"] = _digest(
        {k: v for k, v in values.items() if k != "content_sha256"}
    )
    with pytest.raises(ValueError, match="disagrees"):
        benchmark_receipt_bundle(prepared.root, type(evidence).model_validate(values))
    artifact = prepared.control / "candidate.py"
    artifact.chmod(0o600)
    artifact.write_text("fictional altered bytes")
    with pytest.raises(ValueError, match="artifact"):
        benchmark_receipt_bundle(prepared.root, evidence)


def test_l_timeout_does_not_become_verified_failure(tmp_path):
    prepared, repository, result = fixture(
        tmp_path,
        verified=False,
        state=RunState.ABANDONED,
        resource_budget=ResourceBudget(max_duration_seconds=600),
        stop_reason="synthetic_timeout",
    )
    evidence = export_benchmark_evidence(prepared.root)
    bundle = benchmark_receipt_bundle(prepared.root, evidence)
    view = (
        BenchmarkReceiptBook(target=bundle.target)
        .capture(bundle)
        .as_of(bundle, cutoff=utc_now())
    )
    assert result.outcome.status.value == "unknown"
    assert result.run.stop_reason == "synthetic_timeout"
    assert evidence.observation.verification_status.value == "unverified"
    assert not view.exporter_eligible
    assert "budget_measurements_not_supported" in view.learning_exclusions
    assert all(a.latency_seconds is None for a in repository.list_records(Attempt))


def test_m_minimal_projection_excludes_private_and_unrelated_data(scenario):
    prepared, repository, _, evidence, bundle = scenario
    unrelated = Task(
        description="UNRELATED_SYNTHETIC_TASK",
        acceptance_spec=prepared.task.acceptance_spec,
    )
    repository.create_task(unrelated)
    assert benchmark_receipt_bundle(prepared.root, evidence) == bundle
    encoded = bundle.model_dump_json()
    for omitted in (
        "HIDDEN_SECRET",
        "PRIVATE_SELF_REPORT",
        "required_test_ids",
        "candidate.py",
        str(prepared.root),
        str(unrelated.task_id),
        "UNRELATED_SYNTHETIC_TASK",
        "raw_payload",
        "artifact_reference",
        "report_reference",
    ):
        assert omitted not in encoded
    assert bundle.verification_references[0].report_sha256
    assert "verification_to_attempt_explicit_link" in bundle.unavailable_fields
    assert "budget_measurement_coverage" in bundle.unavailable_fields
    assert "configuration_model_version" in bundle.unavailable_fields
    assert "attempt_latency_seconds" in bundle.unavailable_fields
    # The public output itself passes pure, non-staged privacy screening.
    from scripts.privacy_guard import content_reasons

    assert content_reasons(encoded.encode()) == set()


@pytest.mark.parametrize(
    "kind", ["Task", "Run", "Attempt", "Verification", "Acceptance"]
)
def test_g_missing_required_record_binding_rejected(scenario, kind):
    *_, bundle = scenario
    values = bundle.model_dump(mode="json")
    values["records"] = [r for r in values["records"] if r["kind"] != kind]
    with pytest.raises(ValueError, match="missing required"):
        recapture_bundle(values)


def test_g_missing_required_association_rejected(scenario):
    *_, bundle = scenario
    values = bundle.model_dump(mode="json")
    next(r for r in values["records"] if r["kind"] == "Attempt")["run_id"] = None
    with pytest.raises(ValueError, match="missing required.*association"):
        recapture_bundle(values)


@pytest.mark.parametrize("unsafe", ["/private/synthetic", "sk-" + "a" * 30])
def test_m_unsafe_public_identifier_rejected(scenario, unsafe):
    *_, bundle = scenario
    values = bundle.model_dump(mode="json")
    values["target"]["dataset_id"] = unsafe
    with pytest.raises(ValueError):
        recapture_bundle(values)


@pytest.mark.parametrize("field", ["content_sha256", "export_sha256"])
def test_r12_digest_corruption_rejected(scenario, field):
    *_, bundle = scenario
    values = bundle.model_dump(mode="json")
    values[field] = "0" * 64
    with pytest.raises(ValueError, match="digest"):
        BenchmarkReceiptBundle.model_validate(values)


def test_r12_versions_and_naive_times_rejected(scenario):
    *_, bundle = scenario
    for versioned in (bundle, BenchmarkReceiptBook(target=bundle.target)):
        values = versioned.model_dump(mode="json")
        values["version"] = "unsupported/v9"
        with pytest.raises(ValueError):
            type(versioned).model_validate(values)
    book = BenchmarkReceiptBook(target=bundle.target).capture(bundle)
    values = book.model_dump(mode="json")
    next(iter(values["receipts"].values()))["received_at"] = "2026-01-01T00:00:00"
    with pytest.raises(ValueError, match="timezone"):
        BenchmarkReceiptBook.model_validate(values)
    with pytest.raises(ValueError, match="timezone"):
        book.as_of(bundle, cutoff=utc_now().replace(tzinfo=None))
    with pytest.raises(TypeError):
        book.capture(bundle, received_at=utc_now() - timedelta(days=1))


def test_source_times_still_gate_even_with_earlier_declared_receipt(
    scenario, monkeypatch
):
    *_, bundle = scenario
    before = bundle.exported_at - timedelta(days=1)
    monkeypatch.setattr(receipts, "utc_now", lambda: before)
    book = BenchmarkReceiptBook(target=bundle.target).capture(bundle)
    view = book.as_of(bundle, cutoff=before)
    assert not view.fully_available
    assert any(reason == "source_time_after_cutoff" for _, reason in view.exclusions)
