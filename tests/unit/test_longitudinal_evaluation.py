"""Synthetic rule checks, abstention, embedding diagnostics and leakage guards."""

import hashlib
import json
import os
import socket
from datetime import timedelta
from pathlib import Path

import pytest
from pydantic import ValidationError

from model_learner.execution.longitudinal import extract_longitudinal_task_states
from model_learner.understanding.longitudinal_evaluation import (
    LongitudinalFixture,
    evaluate_longitudinal_fixture,
    load_longitudinal_fixture,
)

FIXTURE = Path(__file__).parents[1] / "fixtures/longitudinal/scenarios.json"
MODEL_SHA256 = "930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2"


class RecordingEncoder:
    dimensions = 2
    metadata = {"model_id": "test-only-encoder", "synthetic": True}

    def __init__(self):
        self.texts = []

    def encode(self, texts):
        self.texts.extend(texts)
        return tuple((1.0, float(len(text))) for text in texts)


def case_fixture(fixture, case):
    return fixture.model_copy(update={"cases": (case,)})


def project(fixture, row):
    return extract_longitudinal_task_states(
        row.events,
        session_id=row.session_id,
        checkpoints=row.checkpoints,
        task=row.task,
        run=row.run,
        dataset=fixture.dataset,
        description=row.description,
        summaries=row.summaries,
        association_available_at=row.association_available_at,
        task_available_at=row.task_available_at,
    )


def test_inspectable_fixture_seven_scenarios_and_no_outcomes():
    fixture = load_longitudinal_fixture(FIXTURE)
    assert fixture.dataset.source_kind.value == "simulated"
    assert fixture.authorship == "agent_authored_synthetic_rule_checks"
    assert fixture.human_reviewed is False
    assert fixture.outcomes_present is False
    assert len(fixture.cases) == 7
    assert len({row.scenario for row in fixture.cases}) == 7
    assert all(
        event.raw_payload is None for row in fixture.cases for event in row.events
    )
    assert all(
        summary.actor_kind == "agent"
        for row in fixture.cases
        for summary in row.summaries
    )
    report = evaluate_longitudinal_fixture(fixture)
    assert report["label_origin"] == fixture.authorship
    assert report["human_reviewed"] is False
    downstream = report["downstream_outcome_prediction"]
    assert downstream["status"] == "insufficient_data"
    assert downstream["scores"] is None
    assert downstream["eligible_independently_verified_real_outcomes"] == 0
    assert downstream["eligible_outcomes_in_fixture"] == 0
    json.dumps(report, allow_nan=False)


def test_comparisons_report_abstention_and_confusion_separately_from_guardrails():
    report = evaluate_longitudinal_fixture(load_longitudinal_fixture(FIXTURE))
    a = report["state_change_recognition"]["A"]
    b = report["state_change_recognition"]["B"]
    assert a["unknown_prediction_count"] == 7
    assert a["abstention_rate"] == 1.0
    assert a["status_agreement_on_non_abstentions"] is None
    assert a["confusion"]["changed"]["unknown"] == 5
    assert b["unknown_prediction_count"] == 1
    assert b["confusion"]["changed"]["changed"] == 5
    assert b["confusion"]["no_observed_change"]["no_observed_change"] == 1
    assert b["confusion"]["unknown"]["unknown"] == 1
    assert b["dimension_rule_agreement_count"] == 7
    assert "not semantic accuracy" in b["interpretation"]
    assert report["state_change_recognition"]["C"]["status"] == "unavailable"
    guardrails = report["unsupported_inference_guardrails"]
    assert guardrails["status"] == "passed"
    assert guardrails["check_count"] == 154
    assert guardrails["violation_count"] == 0
    assert all(count == 14 for count in guardrails["checks_by_name"].values())
    metadata = report["state_change_recognition"]["B_metadata_only"]
    assert metadata["status_rule_agreement"] == 6 / 7
    assert metadata["dimension_rule_agreement_count"] == 3
    assert (
        report["deterministic_telemetry_sufficiency"][
            "cases_with_declared_semantic_change"
        ]
        == 4
    )
    assert (
        report["deterministic_telemetry_sufficiency"][
            "semantic_changes_in_metadata_only"
        ]
        == 0
    )


def test_expectation_labels_do_not_enter_extraction_or_embedding_text():
    fixture = load_longitudinal_fixture(FIXTURE)
    changed = fixture.model_copy(
        update={
            "cases": tuple(
                row.model_copy(
                    update={
                        "expected": row.expected.model_copy(
                            update={"status": "unknown", "dimensions": ()}
                        )
                    }
                )
                for row in fixture.cases
            )
        }
    )
    encoder_one, encoder_two = RecordingEncoder(), RecordingEncoder()
    first = evaluate_longitudinal_fixture(fixture, encoder=encoder_one)
    second = evaluate_longitudinal_fixture(changed, encoder=encoder_two)
    for variant in ("A", "B", "C"):
        first_rows = first["state_change_recognition"][variant]["cases"]
        second_rows = second["state_change_recognition"][variant]["cases"]
        assert [r["predicted_status"] for r in first_rows] == [
            r["predicted_status"] for r in second_rows
        ]
        assert [r["dimensions"] for r in first_rows] == [
            r["dimensions"] for r in second_rows
        ]
    assert encoder_one.texts == encoder_two.texts


def test_cpu_similarity_alone_cannot_supply_semantic_change():
    fixture = load_longitudinal_fixture(FIXTURE)
    row = next(r for r in fixture.cases if r.scenario == "complexity_growth")
    row = row.model_copy(
        update={
            "summaries": tuple(
                s.model_copy(
                    update={
                        "phase": None,
                        "progress": None,
                        "scope": None,
                        "difficulty": None,
                    }
                )
                for s in row.summaries
            )
        }
    )
    encoder = RecordingEncoder()
    report = evaluate_longitudinal_fixture(case_fixture(fixture, row), encoder=encoder)
    b, c = [report["state_change_recognition"][variant] for variant in ("B", "C")]
    assert b["cases"][0]["predicted_status"] == "unknown"
    assert b["cases"][0]["dimensions"] == []
    assert c["cases"] == b["cases"]
    assert c["classification_difference_from_B"] == 0
    assert c["status"] == "evaluated_diagnostic_only"
    assert len(c["semantic_diagnostics"][0]["checkpoints"]) == 2
    assert encoder.texts


def test_future_summary_text_never_reaches_encoder_or_earlier_state():
    fixture = load_longitudinal_fixture(FIXTURE)
    row = next(r for r in fixture.cases if r.scenario == "no_meaningful_change")
    text = (
        "FUTURE PRIVATE-LIKE CANARY: this deliberately synthetic text is unavailable."
    )
    future = row.summaries[0].model_copy(
        update={
            "summary_id": "future-summary",
            "text": text,
            "text_sha256": hashlib.sha256(text.encode()).hexdigest(),
            "observed_at": row.checkpoints[-1] + timedelta(seconds=1),
            "available_at": row.checkpoints[-1] + timedelta(seconds=2),
            "phase": "debugging",
        }
    )
    updated = row.model_copy(update={"summaries": (*row.summaries, future)})
    encoder = RecordingEncoder()
    before = evaluate_longitudinal_fixture(
        case_fixture(fixture, row), encoder=RecordingEncoder()
    )
    after = evaluate_longitudinal_fixture(
        case_fixture(fixture, updated), encoder=encoder
    )
    assert text not in encoder.texts
    assert before == after
    assert project(fixture, row) == project(fixture, updated)


@pytest.mark.parametrize(
    "reason",
    ["unavailable_reference", "outside_run", "scope_late", "equal_time_ambiguity"],
)
def test_rejected_or_ambiguous_summary_text_never_reaches_encoder(reason):
    fixture = load_longitudinal_fixture(FIXTURE)
    row = next(r for r in fixture.cases if r.scenario == "no_meaningful_change")
    text = "SYNTHETIC EXCLUDED SUMMARY CANARY"
    summary = row.summaries[0].model_copy(
        update={"text": text, "text_sha256": hashlib.sha256(text.encode()).hexdigest()}
    )
    updates = {"summaries": (summary,)}
    if reason == "unavailable_reference":
        unavailable_event = row.events[0].model_copy(
            update={"ingested_at": row.checkpoints[-1] + timedelta(seconds=1)}
        )
        updates["events"] = (unavailable_event,)
    elif reason == "outside_run":
        updates["summaries"] = (
            summary.model_copy(
                update={"observed_at": row.run.started_at - timedelta(seconds=1)}
            ),
        )
    elif reason == "scope_late":
        updates["association_available_at"] = row.checkpoints[-1] + timedelta(seconds=1)
    else:
        updates["summaries"] = (
            summary,
            row.summaries[0].model_copy(
                update={"summary_id": "equal-time-other-summary"}
            ),
        )
    row = row.model_copy(update=updates)
    encoder = RecordingEncoder()
    report = evaluate_longitudinal_fixture(case_fixture(fixture, row), encoder=encoder)
    assert text not in encoder.texts
    points = report["state_change_recognition"]["C"]["semantic_diagnostics"][0][
        "checkpoints"
    ]
    assert all(point["status"] == "unknown" for point in points)
    if reason == "scope_late":
        assert row.description.text not in encoder.texts


def test_delayed_objective_is_not_encoded_before_its_receipt():
    fixture = load_longitudinal_fixture(FIXTURE)
    row = next(r for r in fixture.cases if r.scenario == "no_meaningful_change")
    row = row.model_copy(
        update={
            "description": row.description.model_copy(
                update={"available_at": row.checkpoints[-1] + timedelta(seconds=1)}
            )
        }
    )
    encoder = RecordingEncoder()
    report = evaluate_longitudinal_fixture(case_fixture(fixture, row), encoder=encoder)
    assert row.description.text not in encoder.texts
    assert row.summaries[0].text in encoder.texts
    points = report["state_change_recognition"]["C"]["semantic_diagnostics"][0][
        "checkpoints"
    ]
    assert all(point["objective_summary_cosine"] is None for point in points)


def test_late_ingestion_of_event_cannot_change_early_state():
    fixture = load_longitudinal_fixture(FIXTURE)
    row = next(
        r for r in fixture.cases if r.scenario == "repeated_unsuccessful_approaches"
    )
    late_event = row.events[1].model_copy(
        update={"ingested_at": row.checkpoints[-1] + timedelta(seconds=1)}
    )
    row = row.model_copy(update={"events": (row.events[0], late_event)})
    states = project(fixture, row)
    assert states[0].execution.facts.failed_tool_items == 1
    assert states[1].execution.facts.failed_tool_items == 1
    report = evaluate_longitudinal_fixture(case_fixture(fixture, row))
    assert (
        report["state_change_recognition"]["B"]["cases"][0]["predicted_status"]
        == "no_observed_change"
    )
    assert report["unsupported_inference_guardrails"]["status"] == "passed"


def test_category_failures_and_completion_remain_unverified_and_uncertain():
    fixture = load_longitudinal_fixture(FIXTURE)
    repeated = next(
        r for r in fixture.cases if r.scenario == "repeated_unsuccessful_approaches"
    )
    state = project(fixture, repeated)[-1]
    assert state.derived.repeated_failure_groups == 1
    assert state.execution.facts.repeated_failures[0].identity_basis == "tool_category"
    assert state.execution.facts.repeated_failures[0].same_operation_retry is None
    assert all(value.value is None for value in state.inferred.values())
    apparent = next(
        r for r in fixture.cases if r.scenario == "apparent_progress_unverified"
    )
    state = project(fixture, apparent)[-1]
    assert state.inferred["progress"].value == "completion_reported"
    assert state.inferred["progress"].provenance == "inferred"
    assert state.progress_percentage is None
    assert state.verified_task_success is None
    assert state.execution.test_results == ()


@pytest.mark.parametrize(
    "field,value", [("human_reviewed", True), ("outcomes_present", True)]
)
def test_fixture_rejects_claims_of_human_review_or_verified_outcomes(field, value):
    data = json.loads(FIXTURE.read_text())
    data[field] = value
    with pytest.raises(ValidationError):
        LongitudinalFixture.model_validate(data)


def test_loader_checks_frozen_digest_and_explicit_simulated_source():
    digest = hashlib.sha256(FIXTURE.read_bytes()).hexdigest()
    assert len(load_longitudinal_fixture(FIXTURE, expected_sha256=digest).cases) == 7
    with pytest.raises(ValueError, match="frozen digest"):
        load_longitudinal_fixture(FIXTURE, expected_sha256="0" * 64)
    data = json.loads(FIXTURE.read_text())
    data["dataset"]["source_kind"] = "real"
    with pytest.raises(ValidationError, match="only simulated"):
        LongitudinalFixture.model_validate(data)


def test_frozen_manifest_and_reference_preserve_synthetic_provenance():
    manifest = json.loads(FIXTURE.with_name("manifest.json").read_text())
    reference = json.loads(FIXTURE.with_name("reference.json").read_text())
    fixture = load_longitudinal_fixture(
        FIXTURE, expected_sha256=manifest["fixture_sha256"]
    )
    report = evaluate_longitudinal_fixture(fixture)
    assert manifest["human_reviewed"] is False
    assert manifest["source_kind"] == "simulated"
    assert reference["reference_provenance"]["socket_connections_denied"] is True
    assert (
        reference["reference_provenance"]["fixture_sha256"]
        == manifest["fixture_sha256"]
    )
    for variant in ("A", "B", "B_metadata_only"):
        assert (
            report["state_change_recognition"][variant]
            == reference["state_change_recognition"][variant]
        )
    assert (
        report["unsupported_inference_guardrails"]
        == reference["unsupported_inference_guardrails"]
    )
    assert (
        report["downstream_outcome_prediction"]
        == reference["downstream_outcome_prediction"]
    )


@pytest.mark.parametrize("vector", [(float("nan"), 1), (True, 1), (1,), ("text", 1)])
def test_invalid_cpu_vectors_fail_without_producing_similarity(vector):
    class InvalidEncoder(RecordingEncoder):
        def encode(self, texts):
            return tuple(vector for _ in texts)

    with pytest.raises(ValueError):
        evaluate_longitudinal_fixture(
            load_longitudinal_fixture(FIXTURE), encoder=InvalidEncoder()
        )


def test_actual_pinned_local_potion_diagnostics_network_disabled(monkeypatch):
    path = os.environ.get("MODEL_LEARNER_TEST_POTION_PATH")
    if not path:
        pytest.skip("explicit approved local Potion bundle required")

    def deny(*args, **kwargs):
        raise AssertionError("longitudinal evaluation must not access the network")

    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    from model_learner.representation.potion import MODEL_REVISION, load_potion_encoder

    encoder = load_potion_encoder(
        path, expected_sha256=MODEL_SHA256, revision=MODEL_REVISION
    )
    report = evaluate_longitudinal_fixture(
        load_longitudinal_fixture(FIXTURE), encoder=encoder
    )
    c = report["state_change_recognition"]["C"]
    assert c["status"] == "evaluated_diagnostic_only"
    assert c["classification_difference_from_B"] == 0
    assert c["cases"] == report["state_change_recognition"]["B"]["cases"]
    reference = json.loads(FIXTURE.with_name("reference.json").read_text())
    expected = reference["state_change_recognition"]["C"]["semantic_diagnostics"]
    for actual_case, expected_case in zip(
        c["semantic_diagnostics"], expected, strict=True
    ):
        for actual, frozen in zip(
            actual_case["checkpoints"], expected_case["checkpoints"], strict=True
        ):
            for field in ("objective_summary_cosine", "previous_summary_cosine"):
                if frozen[field] is None:
                    assert actual[field] is None
                else:
                    assert actual[field] == pytest.approx(frozen[field], abs=1e-12)
    missing = next(
        r for r in c["semantic_diagnostics"] if r["case_id"] == "missing_evidence"
    )
    assert all(point["status"] == "unknown" for point in missing["checkpoints"])
    json.dumps(report, allow_nan=False)
