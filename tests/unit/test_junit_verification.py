"""Sanitized JUnit metadata parsing and immutable acceptance declarations."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from pydantic import ValidationError

from model_learner.domain.models import AcceptanceSpec, Task
from model_learner.verification import _expected
from model_learner.verification.junit import (
    MAX_REPORT_BYTES,
    JUnitReportBinding,
    JUnitSummary,
    _criterion,
    junit_criterion,
    parse_junit_xml,
)

FIXTURES = Path(__file__).parents[1] / "fixtures/junit"


def test_pytest_report_preserves_exact_counts_and_parameterized_identities() -> None:
    summary = parse_junit_xml((FIXTURES / "passing.xml").read_bytes())
    assert summary.counts.model_dump() == {
        "tests": 3,
        "passed": 3,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
    }
    assert summary.diagnostics == ()
    assert summary.cases[1].test_id == "tests.test_calculator::test_divide[positive]"
    failure = parse_junit_xml((FIXTURES / "failing.xml").read_bytes())
    assert failure.counts.model_dump() == {
        "tests": 3,
        "passed": 1,
        "failures": 1,
        "errors": 1,
        "skipped": 0,
    }
    assert failure.cases[0].status == "failure"
    assert failure.cases[1].status == "error"
    serialized = failure.model_dump_json()
    assert "PRIVATE" not in serialized
    assert "SANITIZED" not in serialized
    assert "assert 4" not in serialized


@pytest.mark.parametrize(
    "contents,diagnostic",
    [
        (b"", "malformed_xml"),
        (b"<testsuite", "malformed_xml"),
        (b"<report/>", "unsupported_xml_root"),
        (b"<testsuites/>", "no_test_cases"),
        (
            b'<!DOCTYPE testsuite [<!ENTITY secret "hidden">]><testsuite/>',
            "xml_declarations_unsupported",
        ),
        (
            b'<?xml version="1.0"?><testsuite/>'.decode().encode("utf-16"),
            "xml_encoding_unsupported",
        ),
        (b" " * (MAX_REPORT_BYTES + 1), "report_too_large"),
        (
            b'<testsuite><testcase classname="t" name="x"/></testsuite>',
            "missing_or_invalid_suite_counts",
        ),
        (
            b'<testsuite tests="2" failures="0" errors="0" skipped="0">'
            b'<testcase classname="t" name="x"/></testsuite>',
            "suite_counts_mismatch",
        ),
        (
            b'<testsuite tests="1" failures="0" errors="0" skipped="0">'
            b'<testcase name="x"/></testsuite>',
            "missing_or_ambiguous_test_identity",
        ),
        (
            b'<testsuite tests="2" failures="0" errors="0" skipped="0">'
            b'<testcase classname="t" name="x"/><testcase classname="t" name="x"/>'
            b"</testsuite>",
            "duplicate_test_identity",
        ),
        (
            b'<testsuite tests="1" failures="1" errors="0" skipped="0">'
            b'<testcase classname="t" name="x"><failure/><error/></testcase>'
            b"</testsuite>",
            "conflicting_case_status",
        ),
        (b"<testsuites>" * 34 + b"</testsuites>" * 34, "xml_nesting_limit"),
        (
            b'<testsuites><testcase classname="t" name="x"/></testsuites>',
            "unsupported_xml_structure",
        ),
        (
            b'<testsuite tests="1" failures="0" errors="0" skipped="0">'
            b'<testcase classname="t" name="x" status="notrun"/></testsuite>',
            "unsupported_case_state",
        ),
        (
            b'<testsuite tests="1" failures="0" errors="0" skipped="0">'
            b'<error/><testcase classname="t" name="x"/></testsuite>',
            "unsupported_xml_structure",
        ),
    ],
)
def test_invalid_or_incomplete_reports_are_diagnostic(
    contents: bytes, diagnostic: str
) -> None:
    assert diagnostic in parse_junit_xml(contents).diagnostics


def test_multiple_suites_aggregate_without_double_counting() -> None:
    summary = parse_junit_xml(
        b'<testsuites tests="2" failures="1" errors="0" skipped="0">'
        b'<testsuite tests="1" failures="0" errors="0" skipped="0">'
        b'<testcase classname="first" name="x"/></testsuite>'
        b'<testsuite tests="1" failures="1" errors="0" skipped="0">'
        b'<testcase classname="second" name="y"><failure/></testcase></testsuite>'
        b"</testsuites>"
    )
    assert summary.counts.tests == 2
    assert summary.counts.passed == summary.counts.failures == 1
    assert summary.diagnostics == ()


@pytest.mark.parametrize(
    "identities",
    [None, [], ["bad"], ["t::"], ["::x"], ["t::x", "t::x"], [1], ["t::   "]],
)
def test_acceptance_requires_nonempty_unambiguous_unique_test_ids(identities) -> None:
    with pytest.raises(ValueError, match="required_test_ids"):
        junit_criterion(required_test_ids=identities)


def test_acceptance_is_canonical_and_independent_of_caller_mutation() -> None:
    ids = ["t::b", "t::a"]
    criterion = junit_criterion(required_test_ids=ids)
    ids.append("t::c")
    assert criterion == {
        "version": "junit-xml/v1",
        "required_test_ids": ["t::a", "t::b"],
    }


def test_parameterized_name_can_contain_double_colon() -> None:
    identity = "tests.test_value::test_value[a::b]"
    assert junit_criterion(required_test_ids=[identity])["required_test_ids"] == [
        identity
    ]
    summary = parse_junit_xml(
        b'<testsuite tests="1" failures="0" errors="0" skipped="0">'
        b'<testcase classname="tests.test_value" name="test_value[a::b]"/>'
        b"</testsuite>"
    )
    assert summary.cases[0].test_id == identity
    assert summary.diagnostics == ()


@pytest.mark.parametrize(
    "changes",
    [
        {"command_exit_code": True},
        {"command_exit_code": "0"},
        {"command_exit_code": -1},
        {"execution_completed": "true"},
        {"report_sha256": "bad"},
        {"artifact_fingerprint": "bad"},
        {"report_generated_at": datetime(2026, 10, 10)},
        {"source": "agent_report"},
        {"command": "pytest"},
    ],
)
def test_binding_requires_strict_external_metadata(changes: dict) -> None:
    receipt = dict(
        task_id=uuid4(),
        run_id=uuid4(),
        acceptance_spec=AcceptanceSpec(identifier="tests", version="1"),
        artifact_fingerprint="sha256:" + "a" * 64,
        report_sha256="b" * 64,
        report_generated_at=datetime(2026, 10, 10, tzinfo=UTC),
        source="pytest-junit",
        execution_completed=True,
        command_exit_code=0,
    )
    with pytest.raises(ValidationError):
        JUnitReportBinding(**(receipt | changes))


def test_summary_rejects_forged_counts() -> None:
    summary = parse_junit_xml((FIXTURES / "passing.xml").read_bytes()).model_dump()
    summary["counts"]["failures"] = 1
    with pytest.raises(ValueError, match="contradict"):
        JUnitSummary.model_validate(summary)


@pytest.mark.parametrize("alternate", [None, {}, {"version": "file-sha256/v1"}])
def test_multiple_acceptance_verifiers_are_not_independent_success_routes(
    alternate,
) -> None:
    task = Task(
        description="Ambiguous acceptance",
        acceptance_spec=AcceptanceSpec(identifier="tests-and-bytes", version="1"),
        metadata={
            "junit_verifier": junit_criterion(required_test_ids=["tests::example"]),
            "file_digest_verifier": alternate,
        },
    )
    with pytest.raises(ValueError, match="multiple acceptance"):
        _criterion(task)
    with pytest.raises(ValueError, match="multiple acceptance"):
        _expected(task)
