"""Read-only reports join captured coding executions and independent outcomes."""

import hashlib
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from model_learner.adapters.codex import ingest_codex_capture
from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    ExecutionConfiguration,
    Outcome,
    OutcomeStatus,
    Run,
    Session,
    Task,
    Verification,
    VerificationResult,
    VerificationStatus,
    utc_now,
)
from model_learner.observations import build_real_observation
from model_learner.runs import create_bounded_run, declare_attempt
from model_learner.storage.database import Database, Repository
from model_learner.verification import (
    JUnitReportBinding,
    assess_run,
    file_sha256,
    junit_criterion,
    validated_junit_summary,
    verify_junit,
)

FIXTURES = Path(__file__).parents[1] / "fixtures"
START = datetime(2026, 10, 10, 12, tzinfo=UTC)
END = START + timedelta(minutes=1)
OBSERVED = END + timedelta(minutes=1)
ASSESSED = OBSERVED + timedelta(minutes=1)
REQUIRED = [
    "tests.test_calculator::test_add",
    "tests.test_calculator::test_divide[positive]",
    "tests.test_calculator::test_divide[negative]",
]
DATASET = DatasetReference(
    source_kind="real", dataset_id="controlled-junit-fixture", dataset_version="1"
)


def workflow(
    tmp_path: Path, *, task_created_at: datetime = START - timedelta(minutes=1)
) -> tuple[Repository, Task, Run, Path]:
    database = Database(tmp_path / "ledger.sqlite3")
    database.initialize()
    repo = Repository(database)
    ingest_codex_capture(
        repo, FIXTURES / "codex/exec_capture.jsonl", machine_id="fixture"
    )
    session = repo.list_records(Session)[0]
    artifact = tmp_path / "calculator.py"
    artifact.write_text("def add(a, b):\n    return a + b\n")
    task = repo.create_task(
        Task(
            description="Controlled coding fixture",
            acceptance_spec=AcceptanceSpec(identifier="calculator-tests", version="1"),
            created_at=task_created_at,
            metadata={"junit_verifier": junit_criterion(required_test_ids=REQUIRED)},
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
    declare_attempt(
        repo,
        run_id=run.run_id,
        configuration=ExecutionConfiguration(provider="fixture", model="fixture-model"),
        started_at=START,
        ended_at=END,
    )
    return repo, task, run, artifact


def receipt(
    task: Task,
    run: Run,
    report: Path,
    *,
    exit_code: int | None = 0,
    complete: bool | None = True,
) -> JUnitReportBinding:
    return JUnitReportBinding(
        task_id=task.task_id,
        run_id=run.run_id,
        acceptance_spec=task.acceptance_spec,
        artifact_fingerprint=run.metadata["final_artifact_fingerprint"],
        report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),
        report_generated_at=END,
        source="pytest-junit",
        execution_completed=complete,
        command_exit_code=exit_code,
    )


def observation(repo: Repository, run: Run, outcome: Outcome):
    return build_real_observation(
        repo,
        run_id=run.run_id,
        outcome_id=outcome.outcome_id,
        dataset=DATASET,
        recorded_at=max(utc_now(), ASSESSED),
    )


@pytest.mark.parametrize(
    "fixture,exit_code,status",
    [
        ("passing.xml", 0, OutcomeStatus.SUCCESS),
        ("failing.xml", 1, OutcomeStatus.FAILURE),
    ],
)
def test_captured_coding_execution_to_verified_report_observation(
    tmp_path: Path, fixture: str, exit_code: int, status: OutcomeStatus
) -> None:
    repo, task, run, artifact = workflow(tmp_path)
    unknown = assess_run(repo, run_id=run.run_id, recorded_at=END)
    assert unknown.status is OutcomeStatus.UNKNOWN
    assert not observation(repo, run, unknown).eligible_for_configuration_learning
    report = FIXTURES / "junit" / fixture
    binding = receipt(task, run, report, exit_code=exit_code)
    evidence = verify_junit(
        repo,
        run_id=run.run_id,
        artifact=artifact,
        report=report,
        binding=binding,
        observed_at=OBSERVED,
    )
    assert evidence.task_id == task.task_id
    assert evidence.run_id == run.run_id
    assert evidence.acceptance_spec == task.acceptance_spec
    assert evidence.artifact_fingerprint == run.metadata["final_artifact_fingerprint"]
    assert evidence.report_reference == str(report.resolve())
    assert evidence.metadata["report_observed_sha256"] == binding.report_sha256
    assert evidence.metadata["binding_provenance"] == "external_operator_receipt"
    summary = validated_junit_summary(repo, run, task, evidence)
    assert summary.counts.tests == 3
    outcome = assess_run(
        repo,
        run_id=run.run_id,
        verification_id=evidence.verification_id,
        recorded_at=ASSESSED,
        supersedes_outcome_id=unknown.outcome_id,
    )
    row = observation(repo, run, outcome)
    assert row.outcome_status is status
    assert row.verification_status is VerificationStatus.VERIFIED
    assert row.eligible_for_configuration_learning
    assert row.evidence_ids == (evidence.verification_id,)
    assert len(repo.list_records(Outcome)) == 2
    assert repo.get(Verification, evidence.verification_id) == evidence
    assert "PRIVATE" not in evidence.model_dump_json()
    assert "SANITIZED_FAILURE_BODY" not in evidence.model_dump_json()


@pytest.mark.parametrize(
    "fixture,exit_code,complete,reason",
    [
        ("skipped.xml", 0, True, "skipped_tests"),
        ("partial.xml", 0, True, "required_tests_missing"),
        ("passing.xml", None, True, "test_exit_code_unknown"),
        ("passing.xml", 0, None, "test_execution_not_confirmed_complete"),
        ("passing.xml", 0, False, "test_execution_not_confirmed_complete"),
        ("passing.xml", 2, True, "test_process_did_not_complete_normally"),
        ("passing.xml", 1, True, "test_exit_code_contradicts_report"),
        ("failing.xml", 0, True, "test_exit_code_contradicts_report"),
    ],
)
def test_incomplete_report_never_becomes_verified_binary_outcome(
    tmp_path: Path,
    fixture: str,
    exit_code: int | None,
    complete: bool | None,
    reason: str,
) -> None:
    repo, task, run, artifact = workflow(tmp_path)
    report = FIXTURES / "junit" / fixture
    evidence = verify_junit(
        repo,
        run_id=run.run_id,
        artifact=artifact,
        report=report,
        binding=receipt(task, run, report, exit_code=exit_code, complete=complete),
        observed_at=OBSERVED,
    )
    assert evidence.result is VerificationResult.INDETERMINATE
    assert reason in evidence.metadata["completeness_reasons"]
    outcome = assess_run(
        repo,
        run_id=run.run_id,
        verification_id=evidence.verification_id,
        recorded_at=ASSESSED,
    )
    row = observation(repo, run, outcome)
    assert outcome.status is OutcomeStatus.UNKNOWN
    assert outcome.verification_status is VerificationStatus.UNVERIFIED
    assert outcome.evidence_ids == (evidence.verification_id,)
    assert row.label_available_at is None
    assert not row.eligible_for_configuration_learning


def test_missing_report_is_retained_as_unknown(tmp_path: Path) -> None:
    repo, task, run, artifact = workflow(tmp_path)
    binding = receipt(task, run, FIXTURES / "junit/passing.xml")
    evidence = verify_junit(
        repo,
        run_id=run.run_id,
        artifact=artifact,
        report=tmp_path / "not-created.xml",
        binding=binding,
        observed_at=OBSERVED,
    )
    assert evidence.result is VerificationResult.INDETERMINATE
    assert evidence.metadata["report_observed_sha256"] is None
    assert "report_missing" in evidence.metadata["completeness_reasons"]
    assert validated_junit_summary(repo, run, task, evidence).counts.tests == 0
    outcome = assess_run(
        repo,
        run_id=run.run_id,
        verification_id=evidence.verification_id,
        recorded_at=ASSESSED,
    )
    assert outcome.status is OutcomeStatus.UNKNOWN


@pytest.mark.parametrize(
    "field",
    [
        "task_id",
        "run_id",
        "acceptance_spec",
        "artifact_fingerprint",
        "report_sha256",
        "report_generated_at",
    ],
)
def test_foreign_stale_or_conflicting_report_receipt_rejected(
    tmp_path: Path, field: str
) -> None:
    repo, task, run, artifact = workflow(tmp_path)
    report = FIXTURES / "junit/passing.xml"
    values = receipt(task, run, report).model_dump()
    if field.endswith("_id"):
        values[field] = uuid4()
    elif field == "acceptance_spec":
        values[field]["version"] = "old"
    elif field == "artifact_fingerprint":
        values[field] = "sha256:" + "a" * 64
    elif field == "report_sha256":
        values[field] = "a" * 64
    else:
        values[field] = START - timedelta(seconds=1)
    with pytest.raises(ValueError):
        verify_junit(
            repo,
            run_id=run.run_id,
            report=report,
            artifact=artifact,
            binding=JUnitReportBinding(**values),
            observed_at=OBSERVED,
        )
    assert repo.list_records(Verification) == []


def test_changed_artifact_or_future_report_receipt_is_rejected(tmp_path: Path) -> None:
    repo, task, run, artifact = workflow(tmp_path)
    report = FIXTURES / "junit/passing.xml"
    binding = receipt(task, run, report)
    future = JUnitReportBinding(
        **(binding.model_dump() | {"report_generated_at": ASSESSED})
    )
    with pytest.raises(ValueError, match="generation"):
        verify_junit(
            repo,
            run_id=run.run_id,
            artifact=artifact,
            report=report,
            binding=future,
            observed_at=OBSERVED,
        )
    artifact.write_text("changed")
    with pytest.raises(ValueError, match="artifact fingerprint"):
        verify_junit(
            repo,
            run_id=run.run_id,
            artifact=artifact,
            report=report,
            binding=binding,
            observed_at=OBSERVED,
        )
    assert repo.list_records(Verification) == []


def test_report_cannot_predate_declared_acceptance(tmp_path: Path) -> None:
    repo, task, run, artifact = workflow(
        tmp_path, task_created_at=END + timedelta(seconds=30)
    )
    report = FIXTURES / "junit/passing.xml"
    with pytest.raises(ValueError, match="predates the declared task acceptance"):
        verify_junit(
            repo,
            run_id=run.run_id,
            artifact=artifact,
            report=report,
            binding=receipt(task, run, report),
            observed_at=OBSERVED,
        )
    assert repo.list_records(Verification) == []


def test_report_modified_during_read_is_rejected(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo, task, run, artifact = workflow(tmp_path)
    report = tmp_path / "changing.xml"
    report.write_bytes((FIXTURES / "junit/passing.xml").read_bytes())
    binding = receipt(task, run, report)
    original_open = Path.open

    class ChangingReport:
        def __init__(self, stream):
            self.stream = stream

        def __enter__(self):
            self.stream.__enter__()
            return self

        def __exit__(self, *args):
            return self.stream.__exit__(*args)

        def fileno(self):
            return self.stream.fileno()

        def read(self, limit):
            contents = self.stream.read(limit)
            with original_open(report, "wb") as writer:
                writer.write(contents + b"changed")
            return contents

    def changed_open(path, *args, **kwargs):
        stream = original_open(path, *args, **kwargs)
        return ChangingReport(stream) if path == report and args == ("rb",) else stream

    monkeypatch.setattr(Path, "open", changed_open)
    with pytest.raises(ValueError, match="report changed"):
        verify_junit(
            repo,
            run_id=run.run_id,
            artifact=artifact,
            report=report,
            binding=binding,
            observed_at=OBSERVED,
        )
    assert repo.list_records(Verification) == []


@pytest.mark.parametrize(
    "mode", ["result", "counts", "criterion", "binding", "reasons"]
)
def test_forged_projected_evidence_cannot_be_assessed(
    tmp_path: Path, mode: str
) -> None:
    repo, task, run, artifact = workflow(tmp_path)
    report = FIXTURES / "junit/passing.xml"
    evidence = verify_junit(
        repo,
        run_id=run.run_id,
        artifact=artifact,
        report=report,
        binding=receipt(task, run, report),
        observed_at=OBSERVED,
    )
    values = evidence.model_dump()
    values["verification_id"] = uuid4()
    if mode == "result":
        values["result"] = "fail"
    elif mode == "counts":
        values["metadata"]["test_results"]["counts"]["failures"] = 1
    elif mode == "criterion":
        values["metadata"]["criterion"] = junit_criterion(
            required_test_ids=["foreign::x"]
        )
    elif mode == "binding":
        values["metadata"]["binding"]["run_id"] = str(uuid4())
    else:
        values["metadata"]["completeness_reasons"] = ["invented"]
    forged = repo.add_verification(Verification(**values))
    with pytest.raises(ValueError):
        assess_run(
            repo,
            run_id=run.run_id,
            verification_id=forged.verification_id,
            recorded_at=ASSESSED,
        )
    assert repo.list_records(Outcome) == []


def test_imported_verified_claim_with_indeterminate_evidence_cannot_learn(
    tmp_path: Path,
) -> None:
    repo, task, run, artifact = workflow(tmp_path)
    report = FIXTURES / "junit/partial.xml"
    evidence = verify_junit(
        repo,
        run_id=run.run_id,
        artifact=artifact,
        report=report,
        binding=receipt(task, run, report),
        observed_at=OBSERVED,
    )
    forged = repo.add_outcome(
        Outcome(
            run_id=run.run_id,
            status=OutcomeStatus.FAILURE,
            verification_status=VerificationStatus.VERIFIED,
            assessment_source="manual-import",
            recorded_at=ASSESSED,
            evidence_ids=(evidence.verification_id,),
        )
    )
    with pytest.raises(ValueError, match="determinate|binary"):
        observation(repo, run, forged)


@pytest.mark.parametrize(
    "xml",
    [
        b"",
        b"<testsuites><testsuite",
        b"<testsuites/>",
        b'<testsuite tests="2" failures="0" errors="0" skipped="0">'
        b'<testcase classname="tests.test_calculator" name="test_add"/>'
        b"</testsuite>",
    ],
)
def test_invalid_reports_remain_indeterminate(tmp_path: Path, xml: bytes) -> None:
    repo, task, run, artifact = workflow(tmp_path)
    report = tmp_path / "invalid.xml"
    report.write_bytes(xml)
    evidence = verify_junit(
        repo,
        run_id=run.run_id,
        artifact=artifact,
        report=report,
        binding=receipt(task, run, report),
        observed_at=OBSERVED,
    )
    assert evidence.result is VerificationResult.INDETERMINATE
    assert evidence.metadata["completeness_reasons"]
