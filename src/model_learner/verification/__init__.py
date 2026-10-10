"""Read-only deterministic file verification and append-only assessments.

The verifier reads bytes only. It never launches a shell, tests, or an agent.
"""

import hashlib
import os
import re
from datetime import datetime
from pathlib import Path
from uuid import UUID

from model_learner.domain.models import (
    AcceptanceSpec,
    Outcome,
    OutcomeStatus,
    Provenance,
    Run,
    Task,
    Verification,
    VerificationResult,
    VerificationStatus,
    utc_now,
)
from model_learner.storage.database import Repository, StorageError

VERIFIER_TYPE = "file-sha256"
VERIFIER_VERSION = "1"


def digest_criterion(expected_sha256: str) -> dict[str, str]:
    """Declare the immutable acceptance check when creating a task."""
    if (
        not isinstance(expected_sha256, str)
        or re.fullmatch(r"[0-9a-f]{64}", expected_sha256) is None
    ):
        raise ValueError("expected_sha256 requires 64 lowercase hexadecimal digits")
    return {"version": "file-sha256/v1", "expected_sha256": expected_sha256}


def validate_fingerprint(fingerprint: str) -> None:
    if not isinstance(fingerprint, str) or not fingerprint.startswith("sha256:"):
        raise ValueError("artifact fingerprint requires sha256:<64 lowercase hex>")
    digest_criterion(fingerprint.removeprefix("sha256:"))


def file_sha256(path: Path | str) -> str:
    """Hash a regular local file without storing private file contents."""
    path = Path(path)
    if not path.is_file():
        raise ValueError("artifact must be a regular file")
    with path.open("rb") as artifact:
        before = os.fstat(artifact.fileno())
        digest = hashlib.file_digest(artifact, "sha256").hexdigest()
        after = os.fstat(artifact.fileno())

    def snapshot(stat: os.stat_result) -> tuple[int, int, int, int]:
        return (stat.st_dev, stat.st_ino, stat.st_size, stat.st_mtime_ns)

    if snapshot(before) != snapshot(after) or snapshot(after) != snapshot(path.stat()):
        raise ValueError("artifact changed while hashing; retry a stable snapshot")
    return digest


def _target(repository: Repository, run_id: UUID) -> tuple[Run, Task]:
    run = repository.get(Run, run_id)
    if run is None:
        raise StorageError("unknown run")
    task = repository.get(Task, run.task_id)
    if task is None:  # pragma: no cover - repository foreign-key guarantee
        raise StorageError("unknown task")
    return run, task


def _expected(task: Task) -> str:
    criterion = task.metadata.get("file_digest_verifier")
    if not isinstance(criterion, dict) or criterion.get("version") != "file-sha256/v1":
        raise ValueError("task has no declared file-sha256/v1 acceptance criterion")
    expected = criterion.get("expected_sha256")
    digest_criterion(expected)
    return expected


def verify_file(
    repository: Repository,
    *,
    run_id: UUID,
    artifact: Path,
    observed_at: datetime | None = None,
    acceptance_spec: AcceptanceSpec | None = None,
) -> Verification:
    """Compare exact file bytes against the task's predeclared digest criterion.

    A changed/wrong run artifact is rejected; a matching run artifact that does
    not satisfy the criterion produces FAIL evidence, not a task assessment.
    """
    run, task = _target(repository, run_id)
    if acceptance_spec is not None and acceptance_spec != task.acceptance_spec:
        raise ValueError("verification acceptance_spec does not match its task")
    expected = _expected(task)
    digest = file_sha256(artifact)
    fingerprint = f"sha256:{digest}"
    if run.metadata.get("final_artifact_fingerprint") != fingerprint:
        raise ValueError(
            "artifact fingerprint does not match the declared run snapshot"
        )
    time = observed_at or utc_now()
    verification = Verification(
        task_id=task.task_id,
        run_id=run_id,
        acceptance_spec=task.acceptance_spec,
        verifier_type=VERIFIER_TYPE,
        verifier_version=VERIFIER_VERSION,
        result=VerificationResult.PASS
        if digest == expected
        else VerificationResult.FAIL,
        observed_at=time,
        artifact_reference=str(artifact.resolve()),
        artifact_fingerprint=fingerprint,
        provenance=Provenance.OBSERVED,
        metadata={
            "criterion": digest_criterion(expected),
            "actual_sha256": digest,
            "capture_method": "read_only_file_hash",
            "content_retained": False,
        },
    )
    if run.ended_at is None or time < run.ended_at:
        raise ValueError("verification must follow the declared run end")
    return repository.add_verification(verification)


def validate_evidence(
    repository: Repository, run: Run, task: Task, evidence: Verification
) -> None:
    """Check deterministic evidence binding before any eligible outcome claim."""
    if evidence.run_id != run.run_id or evidence.task_id != task.task_id:
        raise ValueError("verification evidence belongs to a different task or run")
    if evidence.acceptance_spec != task.acceptance_spec:
        raise ValueError("verification acceptance_spec does not match its task")
    if evidence.verifier_type != VERIFIER_TYPE or evidence.verifier_version != "1":
        raise ValueError("unsupported deterministic verification evidence")
    if evidence.provenance is not Provenance.OBSERVED:
        raise ValueError("deterministic verification requires observed provenance")
    fingerprint = run.metadata.get("final_artifact_fingerprint")
    validate_fingerprint(fingerprint)
    if evidence.artifact_fingerprint != fingerprint:
        raise ValueError(
            "artifact fingerprint does not match the declared run snapshot"
        )
    expected = _expected(task)
    actual = fingerprint.removeprefix("sha256:")
    if evidence.metadata.get("criterion") != digest_criterion(expected):
        raise ValueError(
            "verification criterion does not match the declared acceptance"
        )
    if evidence.metadata.get("actual_sha256") != actual:
        raise ValueError("verification actual digest does not match its artifact")
    result = VerificationResult.PASS if actual == expected else VerificationResult.FAIL
    if evidence.result is not result:
        raise ValueError("verification result contradicts the deterministic criterion")
    if run.ended_at is None or evidence.observed_at < run.ended_at:
        raise ValueError("verification must follow the declared run end")


def _revision(
    repository: Repository, run_id: UUID, supersedes: UUID | None, time: datetime
) -> None:
    if supersedes is None:
        return
    previous = repository.get(Outcome, supersedes)
    if previous is None or previous.run_id != run_id:
        raise ValueError("superseded outcome must belong to the same run")
    if previous.recorded_at > time:
        raise ValueError("revision timestamp must follow the superseded assessment")
    if any(
        item.supersedes_outcome_id == supersedes
        for item in repository.list_records(Outcome)
    ):
        raise ValueError("superseded outcome already has a revision")


def assess_run(
    repository: Repository,
    *,
    run_id: UUID,
    verification_id: UUID | None = None,
    assessment_source: str = "deterministic_verifier",
    recorded_at: datetime | None = None,
    supersedes_outcome_id: UUID | None = None,
    note: str | None = None,
) -> Outcome:
    """Assess final evidence; absent evidence remains unknown even if completed."""
    run, task = _target(repository, run_id)
    time = recorded_at or utc_now()
    status = OutcomeStatus.UNKNOWN
    verification_status = VerificationStatus.UNVERIFIED
    evidence_ids = ()
    if verification_id is not None:
        evidence = repository.get(Verification, verification_id)
        if evidence is None:
            raise StorageError("unknown verification evidence")
        validate_evidence(repository, run, task, evidence)
        if time < evidence.observed_at:
            raise ValueError("assessment timestamp must follow verification")
        status = (
            OutcomeStatus.SUCCESS
            if evidence.result is VerificationResult.PASS
            else OutcomeStatus.FAILURE
        )
        verification_status = VerificationStatus.VERIFIED
        evidence_ids = (evidence.verification_id,)
    outcome = Outcome(
        run_id=run_id,
        status=status,
        verification_status=verification_status,
        assessment_source=assessment_source,
        recorded_at=time,
        evidence_ids=evidence_ids,
        supersedes_outcome_id=supersedes_outcome_id,
        note=note,
        metadata={"assessment_method": "deterministic_file_digest"},
    )
    if run.ended_at is None or time < run.ended_at:
        raise ValueError("assessment must follow the declared run end")
    _revision(repository, run_id, supersedes_outcome_id, time)
    return repository.add_outcome(outcome)


def assess_human(
    repository: Repository,
    *,
    run_id: UUID,
    status: OutcomeStatus,
    recorded_at: datetime | None = None,
    supersedes_outcome_id: UUID | None = None,
    note: str | None = None,
    censor_reason: str | None = None,
) -> Outcome:
    """Retain explicit human acceptance separately from deterministic evidence."""
    run, _ = _target(repository, run_id)
    time = recorded_at or utc_now()
    outcome = Outcome(
        run_id=run_id,
        status=status,
        verification_status=VerificationStatus.UNVERIFIED,
        assessment_source="human_assessment",
        recorded_at=time,
        supersedes_outcome_id=supersedes_outcome_id,
        note=note,
        censor_reason=censor_reason,
        metadata={"assessment_method": "human_declaration"},
    )
    if run.ended_at is None or time < run.ended_at:
        raise ValueError("assessment must follow the declared run end")
    _revision(repository, run_id, supersedes_outcome_id, time)
    return repository.add_outcome(outcome)
