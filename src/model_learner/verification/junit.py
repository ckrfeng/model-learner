"""Read existing JUnit reports; never launch a test process or trust agent text.

The caller supplies an external operator receipt associating the report with the
execution. This is a declaration, not cryptographic attestation of a test run.
"""

import hashlib
import os
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID
from xml.etree import ElementTree

from pydantic import BaseModel, ConfigDict, Field, model_validator

from model_learner.domain.models import (
    AcceptanceSpec,
    Provenance,
    Run,
    Task,
    Verification,
    VerificationResult,
    utc_now,
)
from model_learner.storage.database import Repository

JUNIT_VERIFIER_TYPE = "junit-xml"
JUNIT_VERIFIER_VERSION = "1"
MAX_REPORT_BYTES = 10 * 1024 * 1024


class JUnitReportBinding(BaseModel):
    """Externally supplied receipt; no self-report or command execution fields."""

    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)

    task_id: UUID
    run_id: UUID
    acceptance_spec: AcceptanceSpec
    artifact_fingerprint: str
    report_sha256: str
    report_generated_at: datetime
    source: Literal["pytest-junit", "junit"]
    execution_completed: bool | None = Field(default=None, strict=True)
    command_exit_code: int | None = Field(default=None, strict=True, ge=0, le=255)

    @model_validator(mode="after")
    def validate_receipt(self) -> "JUnitReportBinding":
        from model_learner.verification import digest_criterion, validate_fingerprint

        validate_fingerprint(self.artifact_fingerprint)
        digest_criterion(self.report_sha256)
        if (
            self.report_generated_at.tzinfo is None
            or self.report_generated_at.utcoffset() is None
        ):
            raise ValueError("report_generated_at must include a timezone")
        return self


class JUnitCase(BaseModel):
    model_config = ConfigDict(extra="forbid")
    test_id: str = Field(min_length=1)
    status: Literal["passed", "failure", "error", "skipped"]


class JUnitCounts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tests: int = Field(strict=True, ge=0)
    passed: int = Field(strict=True, ge=0)
    failures: int = Field(strict=True, ge=0)
    errors: int = Field(strict=True, ge=0)
    skipped: int = Field(strict=True, ge=0)


class JUnitSummary(BaseModel):
    """Metadata projection: identities and statuses, no output or failure text."""

    model_config = ConfigDict(extra="forbid")
    version: Literal["junit-results/v1"] = "junit-results/v1"
    counts: JUnitCounts
    cases: tuple[JUnitCase, ...]
    diagnostics: tuple[str, ...] = ()

    @model_validator(mode="after")
    def check_counts(self) -> "JUnitSummary":
        if self.counts != _counts(self.cases):
            raise ValueError("JUnit summary counts contradict case statuses")
        return self


def _counts(cases: tuple[JUnitCase, ...] | list[JUnitCase]) -> JUnitCounts:
    counts = Counter(case.status for case in cases)
    return JUnitCounts(
        tests=len(cases),
        passed=counts["passed"],
        failures=counts["failure"],
        errors=counts["error"],
        skipped=counts["skipped"],
    )


def junit_criterion(*, required_test_ids: list[str] | tuple[str, ...]) -> dict:
    """Predeclare exact required JUnit identities before observing a run."""
    if not isinstance(required_test_ids, (tuple, list)) or not required_test_ids:
        raise ValueError("required_test_ids must be a nonempty list of test identities")
    for identity in required_test_ids:
        if (
            not isinstance(identity, str)
            or "::" not in identity
            or not all(part.strip() for part in identity.split("::", 1))
        ):
            raise ValueError("required_test_ids require classname::name identities")
    if len(set(required_test_ids)) != len(required_test_ids):
        raise ValueError("required_test_ids must not contain duplicates")
    return {"version": "junit-xml/v1", "required_test_ids": sorted(required_test_ids)}


def _criterion(task: Task) -> dict:
    if "file_digest_verifier" in task.metadata and "junit_verifier" in task.metadata:
        raise ValueError("multiple acceptance verifier criteria are unsupported")
    criterion = task.metadata.get("junit_verifier")
    if not isinstance(criterion, dict) or criterion.get("version") != "junit-xml/v1":
        raise ValueError("task has no declared junit-xml/v1 acceptance criterion")
    expected = junit_criterion(required_test_ids=criterion.get("required_test_ids"))
    if criterion != expected:
        raise ValueError("JUnit acceptance criterion is not canonical")
    return expected


def _empty(reason: str) -> JUnitSummary:
    return JUnitSummary(counts=_counts(()), cases=(), diagnostics=(reason,))


def parse_junit_xml(contents: bytes) -> JUnitSummary:
    """Parse the bounded, unnamespaced pytest/JUnit testsuite dialect.

    Unsupported, malformed, conflicting or incomplete XML yields diagnostics,
    never a passing summary. DTDs/entities are refused before XML expansion.
    """
    if len(contents) > MAX_REPORT_BYTES:
        return _empty("report_too_large")
    # Reject UTF-16/32 too: removing NUL bytes makes declaration checks reliable
    # for those encodings, which are outside this deliberately small dialect.
    guarded = contents.replace(b"\x00", b"").upper()
    if b"<!DOCTYPE" in guarded or b"<!ENTITY" in guarded:
        return _empty("xml_declarations_unsupported")
    if b"\x00" in contents:
        return _empty("xml_encoding_unsupported")
    try:
        root = ElementTree.fromstring(contents)
    except ElementTree.ParseError:
        return _empty("malformed_xml")
    if root.tag not in {"testsuites", "testsuite"}:
        return _empty("unsupported_xml_root")
    pending = [(root, 0)]
    while pending:
        node, depth = pending.pop()
        if depth > 32:
            return _empty("xml_nesting_limit")
        pending.extend((child, depth + 1) for child in node)
    cases = []
    diagnostics = []
    allowed_children = {
        "testsuites": {"testsuite"},
        "testsuite": {
            "testsuite",
            "testcase",
            "properties",
            "system-out",
            "system-err",
        },
        "testcase": {
            "failure",
            "error",
            "skipped",
            "properties",
            "system-out",
            "system-err",
        },
        "properties": {"property"},
    }
    for parent in root.iter():
        if any(
            child.tag not in allowed_children.get(parent.tag, set()) for child in parent
        ):
            diagnostics.append("unsupported_xml_structure")
    recognized = {
        "testsuites",
        "testsuite",
        "testcase",
        "properties",
        "property",
        "failure",
        "error",
        "skipped",
        "system-out",
        "system-err",
    }
    for element in root.iter():
        if element.tag not in recognized:
            diagnostics.append("unsupported_xml_element")
        if element.tag != "testcase":
            continue
        if "status" in element.attrib or "result" in element.attrib:
            diagnostics.append("unsupported_case_state")
        classname = element.get("classname")
        name = element.get("name")
        if not classname or not name or "::" in classname:
            diagnostics.append("missing_or_ambiguous_test_identity")
            continue
        statuses = [
            child.tag
            for child in element
            if child.tag in {"failure", "error", "skipped"}
        ]
        if len(statuses) > 1:
            diagnostics.append("conflicting_case_status")
        status = statuses[0] if statuses else "passed"
        cases.append(JUnitCase(test_id=f"{classname}::{name}", status=status))
    # Validate both suite totals and optional aggregate totals. Missing suite
    # counters prevent success; an aggregate wrapper may omit them (pytest does).
    for suite in root.iter():
        if suite.tag not in {"testsuite", "testsuites"}:
            continue
        children = []
        for case in suite.iter("testcase"):
            statuses = [
                child.tag
                for child in case
                if child.tag in {"failure", "error", "skipped"}
            ]
            children.append(
                JUnitCase(
                    test_id="counter", status=statuses[0] if statuses else "passed"
                )
            )
        actual = _counts(children)
        for key in ("tests", "failures", "errors", "skipped"):
            declared = suite.get(key)
            if declared is None and suite.tag == "testsuites":
                continue
            if declared is None or re.fullmatch(r"[0-9]+", declared) is None:
                diagnostics.append("missing_or_invalid_suite_counts")
            elif int(declared) != getattr(actual, key):
                diagnostics.append("suite_counts_mismatch")
    if not cases:
        diagnostics.append("no_test_cases")
    if len({case.test_id for case in cases}) != len(cases):
        diagnostics.append("duplicate_test_identity")
    return JUnitSummary(
        counts=_counts(cases),
        cases=tuple(cases),
        diagnostics=tuple(sorted(set(diagnostics))),
    )


def _reasons(
    summary: JUnitSummary,
    binding: JUnitReportBinding,
    criterion: dict,
    actual_digest: str | None,
) -> list[str]:
    reasons = list(summary.diagnostics)
    if not summary.cases:
        reasons.append("no_test_cases")
    if len({case.test_id for case in summary.cases}) != len(summary.cases):
        reasons.append("duplicate_test_identity")
    if actual_digest is None:
        reasons.append("report_missing")
    if binding.execution_completed is not True:
        reasons.append("test_execution_not_confirmed_complete")
    if binding.command_exit_code is None:
        reasons.append("test_exit_code_unknown")
    elif binding.command_exit_code not in {0, 1}:
        reasons.append("test_process_did_not_complete_normally")
    elif (binding.command_exit_code == 0) != (
        summary.counts.failures + summary.counts.errors == 0
    ):
        reasons.append("test_exit_code_contradicts_report")
    if summary.counts.skipped:
        reasons.append("skipped_tests")
    if set(criterion["required_test_ids"]) - {case.test_id for case in summary.cases}:
        reasons.append("required_tests_missing")
    return sorted(set(reasons))


def _result(summary: JUnitSummary, reasons: list[str]) -> VerificationResult:
    if reasons:
        return VerificationResult.INDETERMINATE
    return (
        VerificationResult.FAIL
        if summary.counts.failures + summary.counts.errors
        else VerificationResult.PASS
    )


def _check_binding(
    run: Run, task: Task, binding: JUnitReportBinding, observed_at: datetime
) -> None:
    if binding.task_id != task.task_id or binding.run_id != run.run_id:
        raise ValueError("JUnit report binding belongs to a different task or run")
    if binding.acceptance_spec != task.acceptance_spec:
        raise ValueError("JUnit report binding acceptance_spec does not match its task")
    if binding.artifact_fingerprint != run.metadata.get("final_artifact_fingerprint"):
        raise ValueError(
            "JUnit report binding artifact does not match the run snapshot"
        )
    if run.started_at is None or binding.report_generated_at < run.started_at:
        raise ValueError("JUnit report predates the declared run")
    if binding.report_generated_at < task.created_at:
        raise ValueError("JUnit report predates the declared task acceptance")
    if binding.report_generated_at > observed_at:
        raise ValueError("JUnit report generation must precede observation")


def verify_junit(
    repository: Repository,
    *,
    run_id: UUID,
    report: Path,
    artifact: Path,
    binding: JUnitReportBinding,
    observed_at: datetime | None = None,
    acceptance_spec: AcceptanceSpec | None = None,
) -> Verification:
    """Store report evidence bound to this task, run and exact artifact bytes."""
    from model_learner.verification import _target, file_sha256

    run, task = _target(repository, run_id)
    criterion = _criterion(task)
    time = observed_at or utc_now()
    if time.tzinfo is None or time.utcoffset() is None:
        raise ValueError("observed_at must include a timezone")
    if acceptance_spec is not None and acceptance_spec != task.acceptance_spec:
        raise ValueError("verification acceptance_spec does not match its task")
    if run.ended_at is None or time < run.ended_at:
        raise ValueError("verification must follow the declared run end")
    _check_binding(run, task, binding, time)
    fingerprint = f"sha256:{file_sha256(artifact)}"
    if fingerprint != binding.artifact_fingerprint:
        raise ValueError(
            "artifact fingerprint does not match the declared run snapshot"
        )
    report = Path(report)
    actual = None
    if not report.exists():
        summary = _empty("report_missing")
    else:
        if not report.is_file():
            raise ValueError("JUnit report must be a regular file")
        with report.open("rb") as stream:
            before = os.fstat(stream.fileno())
            contents = stream.read(MAX_REPORT_BYTES + 1)
            after = os.fstat(stream.fileno())
        current = report.stat()
        fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns")
        if any(
            getattr(before, field) != getattr(after, field)
            or getattr(after, field) != getattr(current, field)
            for field in fields
        ):
            raise ValueError("JUnit report changed while reading")
        if len(contents) > MAX_REPORT_BYTES:
            raise ValueError("JUnit report exceeds the supported size limit")
        actual = hashlib.sha256(contents).hexdigest()
        if actual != binding.report_sha256:
            raise ValueError("JUnit report digest does not match its binding receipt")
        summary = parse_junit_xml(contents)
    reasons = _reasons(summary, binding, criterion, actual)
    evidence = Verification(
        task_id=task.task_id,
        run_id=run_id,
        acceptance_spec=task.acceptance_spec,
        verifier_type=JUNIT_VERIFIER_TYPE,
        verifier_version=JUNIT_VERIFIER_VERSION,
        result=_result(summary, reasons),
        observed_at=time,
        artifact_reference=str(Path(artifact).resolve()),
        artifact_fingerprint=fingerprint,
        report_reference=str(report.resolve()),
        provenance=Provenance.OBSERVED,
        metadata={
            "criterion": criterion,
            "binding": binding.model_dump(mode="json"),
            "test_results": summary.model_dump(mode="json"),
            "report_observed_sha256": actual,
            "completeness_reasons": reasons,
            "capture_method": "read_only_junit_xml",
            "binding_provenance": "external_operator_receipt",
            "content_retained": False,
        },
    )
    return repository.add_verification(evidence)


def validate_junit_evidence(
    run: Run, task: Task, evidence: Verification
) -> JUnitSummary:
    """Recheck projected counts, receipt association and deterministic policy."""
    from model_learner.verification import validate_fingerprint

    if run.task_id != task.task_id:
        raise ValueError("run belongs to a different task")
    if evidence.run_id != run.run_id or evidence.task_id != task.task_id:
        raise ValueError("verification evidence belongs to a different task or run")
    if evidence.acceptance_spec != task.acceptance_spec:
        raise ValueError("verification acceptance_spec does not match its task")
    if evidence.verifier_type != JUNIT_VERIFIER_TYPE or (
        evidence.verifier_version != JUNIT_VERIFIER_VERSION
    ):
        raise ValueError("unsupported JUnit verification evidence")
    if evidence.provenance is not Provenance.OBSERVED:
        raise ValueError("JUnit verification requires observed provenance")
    fingerprint = run.metadata.get("final_artifact_fingerprint")
    validate_fingerprint(fingerprint)
    if evidence.artifact_fingerprint != fingerprint:
        raise ValueError(
            "artifact fingerprint does not match the declared run snapshot"
        )
    if run.ended_at is None or evidence.observed_at < run.ended_at:
        raise ValueError("verification must follow the declared run end")
    criterion = _criterion(task)
    if evidence.metadata.get("criterion") != criterion:
        raise ValueError("verification criterion does not match declared acceptance")
    binding = JUnitReportBinding.model_validate(evidence.metadata.get("binding"))
    _check_binding(run, task, binding, evidence.observed_at)
    actual = evidence.metadata.get("report_observed_sha256")
    if actual is not None and actual != binding.report_sha256:
        raise ValueError("JUnit report digest does not match its binding receipt")
    summary = JUnitSummary.model_validate(evidence.metadata.get("test_results"))
    reasons = _reasons(summary, binding, criterion, actual)
    if evidence.metadata.get("completeness_reasons") != reasons:
        raise ValueError("JUnit completeness reasons contradict the observed summary")
    if evidence.result is not _result(summary, reasons):
        raise ValueError("verification result contradicts the JUnit criterion")
    return summary


def validated_junit_summary(
    repository: Repository, run: Run, task: Task, evidence: Verification
) -> JUnitSummary:
    """Public pure validation helper for analysis of already persisted reports."""
    from model_learner.verification import validate_evidence

    if evidence.verifier_type != JUNIT_VERIFIER_TYPE:
        raise ValueError("evidence is not a JUnit report")
    validate_evidence(repository, run, task, evidence)
    return JUnitSummary.model_validate(evidence.metadata["test_results"])
