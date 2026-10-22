"""J1 newly authored synthetic fixtures only. Never HTTP, credentials or Git."""

import copy
import hashlib
import importlib.util
import json
import socket
import sys
from pathlib import Path

import pytest

from model_learner.understanding import decisions_offline as adapter
from model_learner.understanding.intent import (
    LABELS,
    QUESTIONS,
    SCORE_CONTROL,
    Prediction,
    Question,
    baseline,
    canonical,
)
from model_learner.understanding.intent_evaluation import (
    MANIFEST_SHA256,
    Reference,
    evaluate_development,
    load_development,
    metrics,
    mock_response,
)

ROOT = Path(__file__).parents[1] / "fixtures/intent"


def response():
    return json.loads(mock_response())


def test_frozen_dataset_questions_and_no_holdout_predictions(monkeypatch):
    assert (
        hashlib.sha256((ROOT / "manifest.json").read_bytes()).hexdigest()
        == MANIFEST_SHA256
    )
    assert len(load_development(ROOT)) == 8
    seen = []
    from model_learner.understanding import intent_evaluation as evaluation

    original = evaluation.baseline

    def collect(text):
        seen.append(text)
        return original(text)

    monkeypatch.setattr(evaluation, "baseline", collect)
    report = evaluate_development(ROOT)
    assert len(seen) == 8
    assert set(seen) == {c.description for c, _ in load_development(ROOT)}
    assert report["holdout"]["predictions_collected"] == 0
    assert [q.kind for q in QUESTIONS] == ["choice", "noul"]
    assert "difficulty" not in str([q.model_dump() for q in QUESTIONS])


def test_actual_local_serialization_contains_only_projected_inputs():
    for case, reference in load_development(ROOT):
        body = adapter.fixture_request(case.description)
        data = json.loads(body)
        assert data["state"] == case.description
        assert data["target"] == {
            "model": adapter.MODEL,
            "origin": adapter.ORIGIN,
            "path": adapter.PATH,
            "method": "POST",
        }
        assert data["provider"] == {"allow_fallbacks": False}
        assert data["provider_slug"] is None
        assert data["schema"] == "j1-local-fixture/v1"
        # Check exact keys; declared choice labels are necessarily public.
        assert set(data) == {
            "schema",
            "contract",
            "target",
            "provider",
            "provider_slug",
            "state",
            "questions",
            "input_token_plan",
            "output_token_plan",
        }
        assert set(reference.model_dump()) & set(data) == set()
        assert case.id.encode() not in body
        assert b"reference_labels" not in body and b"holdout" not in body
        assert b'executable_changes":' not in body
        fake = adapter.FakeTransport(mock_response())
        adapter.parse_fixture_response(fake.send(body))
        assert fake.calls == 1


@pytest.mark.parametrize(
    "file", ["inputs.json", "reference_labels.json", "manifest.json"]
)
def test_frozen_tampering_rejected(tmp_path, file):
    for source in ROOT.glob("*.json"):
        (tmp_path / source.name).write_bytes(source.read_bytes())
    with (tmp_path / file).open("ab") as stream:
        stream.write(b" ")
    with pytest.raises(ValueError, match="frozen"):
        load_development(tmp_path)


def test_mock_report_reproducible_and_explicit_unknowns():
    first = evaluate_development(ROOT)
    assert canonical(first) == canonical(evaluate_development(ROOT))
    assert first["status"] == "PARTIAL"
    assert "mocked plumbing" in first["external_model_evidence"]
    assert first["mocked_local_fixture"]["primary_intent_accuracy"] == 1 / 8
    assert first["mocked_local_fixture"]["binary_brier"] == 0.25
    assert first["billing_coverage"]["known_cost"] == 0
    for receipt in first["receipts"]:
        assert receipt["reported_model"] is None
        assert receipt["reported_provider"] is None
        assert receipt["reported_cost_usd"] is None
        assert receipt["effective_model_revision"] is None
        assert receipt["routing_status"] == "unknown"


@pytest.mark.parametrize(
    "kwargs",
    [
        {"origin": "http://openrouter.ai"},
        {"origin": "https://openrouter.ai.evil.test"},
        {"origin": "https://jev-ai.pro"},
        {"origin": "https://typesafe.test"},
        {"path": "/api/v1/chat/completions"},
        {"path": "/api/alpha/decisions/"},
        {"method": "GET"},
        {"method": "post"},
        {"redirected": True},
        {"status": 301},
        {"status": 429},
        {"status": 500},
    ],
)
def test_fake_transport_rejects_target_status_redirect_and_never_retries(kwargs):
    fake = adapter.FakeTransport(mock_response())
    with pytest.raises(ValueError):
        fake.send(adapter.fixture_request("Fictional task"), **kwargs)
    with pytest.raises(ValueError, match="retries forbidden"):
        fake.send(adapter.fixture_request("Fictional task"))
    assert fake.calls == 1


@pytest.mark.parametrize(
    "field,value",
    [
        ("provider", {"allow_fallbacks": True}),
        ("provider", {"allow_fallbacks": False, "only": ["typesafe"]}),
        ("provider_slug", "typesafe"),
        ("questions", []),
        ("target", {"model": "another-model"}),
        ("contract", "unfrozen/v2"),
        ("extra", "reference label"),
    ],
)
def test_fake_transport_rejects_actual_serialized_substitutions(field, value):
    body = json.loads(adapter.fixture_request("Fictional task"))
    body[field] = value
    with pytest.raises(ValueError):
        adapter.FakeTransport(mock_response()).send(canonical(body))


@pytest.mark.parametrize(
    "failure", [TimeoutError(), OSError(), ValueError("unknown settlement")]
)
def test_error_stops_single_attempt(failure):
    fake = adapter.FakeTransport(failure)
    with pytest.raises(type(failure)):
        fake.send(adapter.fixture_request("Fictional task"))
    with pytest.raises(ValueError, match="retries"):
        fake.send(adapter.fixture_request("Fictional task"))
    assert fake.calls == 1


def test_exact_answer_identity_is_order_independent_but_not_optional():
    payload = response()
    payload["answers"].reverse()
    prediction, receipt = adapter.parse_fixture_response(canonical(payload))
    assert prediction.intent == "unclear"
    assert prediction.origin == "mocked_external_model"
    assert receipt["requested_model"] == adapter.MODEL
    for answers in [
        [],
        payload["answers"][:1],
        [payload["answers"][0]] * 2,
        payload["answers"] + [payload["answers"][0]],
    ]:
        with pytest.raises(ValueError):
            adapter.parse_fixture_response(canonical(payload | {"answers": answers}))


@pytest.mark.parametrize(
    "field,value",
    [
        ("label", "undeclared"),
        ("label", []),
        ("confidence", True),
        ("confidence", "1"),
        ("confidence", -0.1),
        ("confidence", 1.1),
        ("kind", "noul"),
        ("id", "wrong_id"),
        ("reasoning", "fictional explanation"),
        ("distribution", {"unclear": 1}),
        ("distribution", dict.fromkeys(LABELS, 0.0)),
    ],
)
def test_malformed_choice_rejected(field, value):
    payload = response()
    payload["answers"][0][field] = value
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(canonical(payload))


@pytest.mark.parametrize("probability", [True, "0.5", None, [], -0.01, 1.01])
def test_noul_wrong_types_and_range_rejected(probability):
    payload = response()
    payload["answers"][1]["true_probability"] = probability
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(canonical(payload))


@pytest.mark.parametrize("replacement", [b"NaN", b"Infinity", b"-Infinity"])
def test_nonfinite_and_duplicate_json_rejected(replacement):
    raw = mock_response().replace(
        b'"true_probability":0.5', b'"true_probability":' + replacement
    )
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(raw)
    with pytest.raises(ValueError, match="duplicate"):
        adapter.decode(b'{"a":0,"a":1}', 100)


def test_local_tolerance_and_confidence_consistency():
    payload = response()
    answer = payload["answers"][0]
    answer["distribution"]["unclear"] = 1 - 0.5e-6
    adapter.parse_fixture_response(canonical(payload))
    answer["distribution"]["unclear"] = 0.9
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(canonical(payload))
    answer["distribution"]["bug_fix"] = 0.1
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(canonical(payload))


def test_fictional_score_control_is_not_a_difficulty_target():
    answer = {
        "id": SCORE_CONTROL.id,
        "kind": "score",
        "weighted_score": 1.2,
        "levels": [
            {"value": 0.0, "probability": 0.2},
            {"value": 1.0, "probability": 0.4},
            {"value": 2.0, "probability": 0.4},
        ],
        "confidence": 0.7,
    }
    assert adapter.parse_answer(answer, SCORE_CONTROL)["weighted_score"] == 1.2
    for field, value in [
        ("weighted_score", 1.5),
        ("confidence", -1),
        ("levels", []),
        ("reasoning", "fictional explanation"),
    ]:
        with pytest.raises(ValueError):
            adapter.parse_answer(answer | {field: value}, SCORE_CONTROL)
    changed = copy.deepcopy(answer)
    changed["levels"][0]["value"] = 1.0
    with pytest.raises(ValueError):
        adapter.parse_answer(changed, SCORE_CONTROL)
    with pytest.raises(ValueError):
        Question(id="bad", kind="noul", prompt="fictional", labels=("a", "b"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("model", "typesafe/jev-other"),
        ("provider", "another-provider"),
        ("schema", "pretend-official"),
    ],
)
def test_reported_substitution_never_success(field, value):
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(canonical(response() | {field: value}))


@pytest.mark.parametrize(
    "usage,status,cost",
    [
        (None, "missing", None),
        ({}, "partial", None),
        ([], "malformed", None),
        ({"cost": 0}, "partial", 0),
        ({"cost": 0.002}, "partial", 0.002),
        ({"cost": "0"}, "malformed", None),
        ({"cost": -1}, "malformed", None),
        ({"cost": True}, "malformed", None),
        ({"cost": float("nan")}, "malformed", None),
        ({"cost": float("inf")}, "malformed", None),
        ({"prompt_tokens": 10, "completion_tokens": 2, "cost": 0}, "complete", 0),
        ({"prompt_tokens": True, "completion_tokens": 1.2}, "malformed", None),
        ({"X-Jev-Cost": 0}, "partial", None),
    ],
)
def test_provisional_usage_known_zero_unknown_and_malformed(usage, status, cost):
    result = adapter.usage_projection(usage)
    assert result["reported_cost_usd"] == cost
    assert result["cost_estimate_usd"] is None
    assert result["usage_status"] == status


@pytest.mark.parametrize(
    "kwargs",
    [
        {"input_token_plan": 0},
        {"input_token_plan": 20_001},
        {"output_token_plan": 513},
        {"output_token_plan": True},
        {"input_token_plan": 1.0},
    ],
)
def test_token_planning_bounds(kwargs):
    with pytest.raises(ValueError):
        adapter.fixture_request("Fictional task", **kwargs)


def test_input_request_response_and_question_bounds(monkeypatch):
    for text in ["", " ", "a" * 4097, "🪐" * 1025]:
        with pytest.raises(ValueError):
            adapter.fixture_request(text)
    with pytest.raises(ValueError):
        Question(id="control", kind="noul", prompt="a" * 2049)
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(b" " * (adapter.MAX_RESPONSE_BYTES + 1))
    monkeypatch.setattr(adapter, "MAX_REQUEST_BYTES", 10)
    with pytest.raises(ValueError):
        adapter.fixture_request("Fictional task")


def test_metrics_independent_hand_calculation_and_abstention():
    refs = (
        Reference(id="a", intent="bug_fix", executable_changes=True),
        Reference(id="b", intent="bug_fix", executable_changes=False),
        Reference(id="c", intent="new_feature", executable_changes=None),
        Reference(id="d", intent="documentation", executable_changes=True),
    )
    predictions = {
        "a": Prediction(
            intent="bug_fix", code_probability=0.8, origin="mocked_external_model"
        ),
        "b": Prediction(
            intent="new_feature", code_probability=0.3, origin="mocked_external_model"
        ),
        "c": Prediction(
            intent=None, code_probability=0.9, origin="mocked_external_model"
        ),
    }
    result = metrics(refs, predictions)
    assert result["primary_intent_accuracy"] == 0.25
    assert result["macro_f1_all_six_classes"] == pytest.approx((2 / 3) / 6)
    assert result["binary_brier"] == pytest.approx((0.04 + 0.09) / 2)
    assert result["binary_accuracy_at_0_5"] == 1
    assert result["primary_coverage"] == 0.5
    assert result["missing_or_malformed_rate"] == 0.25
    assert result["binary_scorable_count"] == 2
    assert result["binary_reference_count"] == 3
    assert result["confusion_matrix"]["documentation"]["abstain"] == 1
    absent = metrics(refs, {})
    assert absent["binary_brier"] is None
    assert absent["primary_intent_accuracy"] == 0
    with pytest.raises(ValueError):
        metrics(refs, {"unrelated": None})


def test_fixed_baseline_predicts_requested_intent_only():
    assert (
        baseline("Investigate the bug; no repair requested").intent == "investigation"
    )
    assert baseline("Document the repair in a guide").code_probability == 0
    assert baseline("Improve this").intent == "unclear"


def test_no_network_or_credential_environment_dependency(monkeypatch):
    import os

    def forbidden(*args, **kwargs):
        raise AssertionError("network/environment access forbidden")

    monkeypatch.setattr(os, "getenv", forbidden)
    monkeypatch.setattr(os, "environ", {})
    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(socket, "getaddrinfo", forbidden)
    monkeypatch.setattr(socket, "create_connection", forbidden)
    evaluate_development(ROOT)
    packet = adapter.readiness()
    assert not packet["ready"] and packet["credential_read"] is False
    assert packet["provider_slug"] is None
    assert "remaining_prepaid_balance" in packet["blockers"]
    assert "enforceable_usd_cap" in packet["blockers"]
    with pytest.raises(adapter.ContractUnavailable):
        adapter.serialize_decisions("Fictional task")


def test_executable_demo_preserves_learning_advice_and_safe_report(monkeypatch):
    scripts = Path(__file__).parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    spec = importlib.util.spec_from_file_location(
        "j1_demo", scripts / "intent_example.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    report = module.demo(ROOT)
    assert report["learner_isolation"]["advisory_unchanged"]
    assert report["learner_isolation"]["beta_bernoulli_unchanged"]
    assert report["learner_isolation"]["fictional_canonical_input_unchanged"]
    assert report["learner_isolation"]["advisory_status"] == "abstain"
    raw = canonical(report)
    for case, _ in load_development(ROOT):
        assert case.description.encode() not in raw
    # Pure privacy functions only: never invoke the guard's Git-backed modes.
    spec = importlib.util.spec_from_file_location(
        "j1_privacy", scripts / "privacy_guard.py"
    )
    guard = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, guard)
    spec.loader.exec_module(guard)
    assert guard.content_reasons(raw) == set()
    assert guard.content_reasons(adapter.fixture_request("Fictional task")) == set()


def test_complete_fake_evaluation_accounts_for_errors_without_retry():
    supplied = {
        "dev-01": TimeoutError("fictional untrusted prose"),
        "dev-02": b'{"wrong":true}',
        "dev-03": mock_response(),
    }
    report = evaluate_development(ROOT, responses=supplied)
    assert report["mocked_local_fixture"]["missing_or_malformed_rate"] == 7 / 8
    assert report["mocked_local_fixture"]["binary_scorable_count"] == 1
    assert all(r["local_attempts"] == 1 for r in report["receipts"])
    assert b"untrusted prose" not in canonical(report)
    assert report["billing_coverage"]["reported_cost_usd"] is None
    with pytest.raises(ValueError):
        evaluate_development(ROOT, responses={"holdout-01": mock_response()})


def test_bounded_hostile_nesting_and_enormous_numbers_are_rejected():
    with pytest.raises(ValueError):
        adapter.decode(b"[" * 2000 + b"]" * 2000, 5000)
    assert adapter.usage_projection({"cost": 10**1000})["usage_status"] == "malformed"
    payload = response()
    payload["answers"][1]["true_probability"] = 10**1000
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(canonical(payload))
