"""J1 synthetic tests plus supplied official public examples; no HTTP or Git writes."""

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
CHOICE_ID, NOUL_ID = (q.id for q in QUESTIONS)


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


def test_actual_published_request_shape_and_label_separation():
    for case, reference in load_development(ROOT):
        body = adapter.fixture_request(case.description)
        data = json.loads(body)
        assert set(data) == {"model", "state", "questions"}
        assert data["state"] == case.description and data["model"] == adapter.MODEL
        assert set(data["questions"]) == {CHOICE_ID, NOUL_ID}
        choice, noul = data["questions"][CHOICE_ID], data["questions"][NOUL_ID]
        assert choice == {
            "type": "choice",
            "instructions": QUESTIONS[0].prompt,
            "criteria": {
                "bug_fix": "Restore stated existing intended behavior.",
                "new_feature": "Add stated new behavior.",
                "refactor": (
                    "Reorganize executable implementation while preserving behavior."
                ),
                "investigation": (
                    "Diagnose, compare or explain without a requested repair."
                ),
                "documentation": (
                    "Change prose or examples intended only as documentation."
                ),
                "unclear": (
                    "No clear primary intent: equal independent objectives, "
                    "vague requests, "
                    "or insufficient context."
                ),
            },
        }
        assert noul == {"type": "noul", "instructions": QUESTIONS[1].prompt}
        assert set(reference.model_dump()) & set(data) == set()
        assert case.id.encode() not in body
        assert b"reference_labels" not in body and b"holdout" not in body
        assert b'"provider"' not in body and b'"allow_fallbacks"' not in body
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
        assert (
            receipt["reported_model"] is None and receipt["reported_provider"] is None
        )
        assert (
            receipt["reported_cost_usd"] is None
            and receipt["effective_model_revision"] is None
        )
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
        {"allow_fallbacks": True},
        {"allow_fallbacks": None},
        {"provider_only": ("substitute",)},
        {"provider_only": ()},
    ],
)
def test_fake_target_and_required_route_policy_rejection_no_retry(kwargs):
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
        ("model", "substitute"),
        ("questions", {}),
        ("extra", "reference label"),
        ("max_tokens", 256),
    ],
)
def test_actual_bytes_reject_substitutions_and_undocumented_fields(field, value):
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


def test_answer_ids_keyed_unordered_exact_and_duplicate_json_rejected():
    payload = response()
    payload["answers"] = dict(reversed(list(payload["answers"].items())))
    assert adapter.parse_fixture_response(canonical(payload))[0].intent == "unclear"
    for answers in [
        {},
        {CHOICE_ID: payload["answers"][CHOICE_ID]},
        payload["answers"] | {"extra": {"type": "noul", "noul": 1}},
        [],
    ]:
        with pytest.raises(ValueError):
            adapter.parse_fixture_response(canonical(payload | {"answers": answers}))
    with pytest.raises(ValueError, match="duplicate"):
        adapter.decode(b'{"answers":{"same":{},"same":{}}}', 100)


@pytest.mark.parametrize(
    "field,value",
    [
        ("choice", "undeclared"),
        ("choice", []),
        ("confidence", True),
        ("confidence", "1"),
        ("confidence", -0.1),
        ("confidence", 1.1),
        ("type", "noul"),
        ("id", "wrong_id"),
        ("reasoning", "fictional explanation"),
        ("probabilities", {"unclear": 1}),
        ("probabilities", dict.fromkeys(LABELS, 0.0)),
    ],
)
def test_malformed_choice_rejected(field, value):
    payload = response()
    payload["answers"][CHOICE_ID][field] = value
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(canonical(payload))


@pytest.mark.parametrize("probability", [True, "0.5", None, [], -0.01, 1.01])
def test_noul_wrong_types_and_range_rejected(probability):
    payload = response()
    payload["answers"][NOUL_ID]["noul"] = probability
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(canonical(payload))


@pytest.mark.parametrize("replacement", [b"NaN", b"Infinity", b"-Infinity"])
def test_nonfinite_rejected(replacement):
    raw = mock_response().replace(b'"noul":0.5', b'"noul":' + replacement)
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(raw)


def test_local_float_tolerance_and_independent_confidence():
    payload = response()
    answer = payload["answers"][CHOICE_ID]
    answer["probabilities"]["unclear"] = 1 - 0.5e-6
    adapter.parse_fixture_response(canonical(payload))
    answer["probabilities"]["unclear"] = 0.9
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(canonical(payload))
    answer["probabilities"]["bug_fix"] = 0.1
    answer["confidence"] = 0.7  # No unsupported equality with category probability.
    assert adapter.parse_fixture_response(canonical(payload))[0].intent == "unclear"


def test_supplied_literal_official_choice_and_noul_responses():
    # Provenance: official OpenRouter Jev guide, literals supplied in this task.
    choice = Question(
        id="team",
        kind="choice",
        prompt="Which team?",
        labels=("billing", "technical", "account"),
    )
    wire = {
        "model": "typesafe/jev-1.14-20261014",
        "provider": "TypeSafe",
        "id": "gen-dec-1792170400-UBIaakN5nEoW6gLSGZGD",
        "usage": {"input_tokens": 357, "output_tokens": 38, "cost": 1.4994e-05},
        "answers": {
            "team": {
                "type": "choice",
                "choice": "billing",
                "probabilities": {"billing": 1, "technical": 0, "account": 0},
                "confidence": 1,
            }
        },
    }
    parsed, receipt = adapter.parse_response(canonical(wire), questions=(choice,))
    assert parsed["team"]["label"] == "billing"
    assert receipt["reported_model"] == adapter.PUBLISHED_RETURNED_MODEL
    assert receipt["requested_model"] == adapter.MODEL
    assert receipt["effective_model_revision"] is None
    assert receipt["generation_id"] == wire["id"]
    assert receipt["input_tokens"] == 357 and receipt["output_tokens"] == 38
    assert receipt["reported_cost_usd"] == 1.4994e-05
    noul = Question(id="refund", kind="noul", prompt="Is money back requested?")
    wire.update(
        id="gen-dec-1792170403-8ZxWBk1v84WmZdC8FfC2",
        answers={"refund": {"type": "noul", "noul": 0.98}},
        usage={"input_tokens": 287, "output_tokens": 20, "cost": 1.2054e-05},
    )
    parsed, receipt = adapter.parse_response(canonical(wire), questions=(noul,))
    assert parsed["refund"]["true_probability"] == 0.98
    assert receipt["reported_cost_usd"] == 1.2054e-05


def test_fictional_score_descriptive_request_and_matching_legend():
    # Synthetic tank control using the published Score shape, not a research target.
    answer = {
        "type": "score",
        "score": 1.21,
        "confidence": 0.69,
        "legend": {
            "0": "Empty: the fictional tank contains no liquid.",
            "1": (
                "Partially filled: the fictional tank contains "
                "some liquid below capacity."
            ),
            "2": "Full: the fictional tank is at capacity.",
        },
        "probabilities": {"0": 0, "1": 0.79, "2": 0.21},
    }
    assert adapter.parse_answer(answer, SCORE_CONTROL)["weighted_score"] == 1.21
    parsed, receipt = adapter.parse_response(
        canonical(
            {
                "model": adapter.PUBLISHED_RETURNED_MODEL,
                "provider": "TypeSafe",
                "id": "gen-dec-1792170402-eLn9v13BBrBgVkFOhKyE",
                "usage": {"input_tokens": 354, "output_tokens": 17, "cost": 1.4868e-05},
                "answers": {SCORE_CONTROL.id: answer},
            }
        ),
        questions=(SCORE_CONTROL,),
    )
    assert parsed[SCORE_CONTROL.id]["weighted_score"] == 1.21
    assert receipt["reported_cost_usd"] == 1.4868e-05
    body = adapter.fixture_request(
        "The fictional tank contains some liquid below capacity.",
        questions=(SCORE_CONTROL,),
    )
    assert json.loads(body)["questions"][SCORE_CONTROL.id] == {
        "type": "score",
        "instructions": (
            "Classify the current fill level of the fictional tank "
            "using these ordered levels."
        ),
        "criteria": [
            "Empty: the fictional tank contains no liquid.",
            "Partially filled: the fictional tank contains some liquid below capacity.",
            "Full: the fictional tank is at capacity.",
        ],
    }
    adapter.FakeTransport(mock_response(), questions=(SCORE_CONTROL,)).send(body)
    for field, value in [
        ("score", 1.5),
        ("confidence", -1),
        ("legend", []),
        ("probabilities", {"0": 1}),
        ("reasoning", "explanation"),
    ]:
        with pytest.raises(ValueError):
            adapter.parse_answer(answer | {field: value}, SCORE_CONTROL)
    changed = copy.deepcopy(answer)
    changed["legend"]["3"] = "extra level"
    with pytest.raises(ValueError):
        adapter.parse_answer(changed, SCORE_CONTROL)
    with pytest.raises(ValueError):
        Question(id="bad", kind="noul", prompt="fictional", labels=("a", "b"))


@pytest.mark.parametrize(
    "field,value",
    [
        ("model", "typesafe/jev-other"),
        ("model", "typesafe/jev-1.14-unapproved"),
        ("provider", "another-provider"),
        ("schema", "pretend-official"),
        ("id", "https://private.test/path"),
    ],
)
def test_reported_substitution_or_extra_field_never_success(field, value):
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
        ({"input_tokens": 10, "output_tokens": 2, "cost": 0}, "complete", 0),
        ({"input_tokens": True, "output_tokens": 1.2}, "malformed", None),
        ({"X-Jev-Cost": 0}, "partial", None),
        ({"prompt_tokens": 999, "completion_tokens": 999}, "partial", None),
    ],
)
def test_documented_usage_known_zero_unknown_and_malformed(usage, status, cost):
    result = adapter.usage_projection(usage)
    assert result["reported_cost_usd"] == cost
    assert result["cost_estimate_usd"] is None and result["usage_status"] == status


@pytest.mark.parametrize(
    "kwargs",
    [
        {"input_token_plan": 0},
        {"input_token_plan": 20_001},
        {"output_token_plan": 513},
        {"output_token_plan": True},
        {"input_token_plan": 1.0},
        {"questions": ()},
        {"questions": (*QUESTIONS, SCORE_CONTROL)},
        {"questions": (QUESTIONS[0], QUESTIONS[0])},
    ],
)
def test_token_question_planning_bounds(kwargs):
    with pytest.raises(ValueError):
        adapter.fixture_request("Fictional task", **kwargs)


def test_input_request_response_bounds_and_hostile_nesting(monkeypatch):
    for text in ["", " ", "a" * 4097, "🪐" * 1025]:
        with pytest.raises(ValueError):
            adapter.fixture_request(text)
    with pytest.raises(ValueError):
        Question(id="control", kind="noul", prompt="a" * 2049)
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(b" " * 32769)
    with pytest.raises(ValueError):
        adapter.decode(b"[" * 2000 + b"]" * 2000, 5000)
    assert adapter.usage_projection({"cost": 10**1000})["usage_status"] == "malformed"
    payload = response()
    payload["answers"][NOUL_ID]["noul"] = 10**1000
    with pytest.raises(ValueError):
        adapter.parse_fixture_response(canonical(payload))
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
    assert result["binary_accuracy_at_0_5"] == 1 and result["primary_coverage"] == 0.5
    assert result["missing_or_malformed_rate"] == 0.25
    assert (
        result["binary_scorable_count"] == 2 and result["binary_reference_count"] == 3
    )
    assert result["confusion_matrix"]["documentation"]["abstain"] == 1
    assert metrics(refs, {})["binary_brier"] is None
    with pytest.raises(ValueError):
        metrics(refs, {"unrelated": None})


def test_fixed_baseline_labels_requested_work_and_complete_error_report():
    assert (
        baseline("Investigate the bug; no repair requested").intent == "investigation"
    )
    assert baseline("Document the repair in a guide").code_probability == 0
    assert baseline("Improve this").intent == "unclear"
    report = evaluate_development(
        ROOT,
        responses={
            "dev-01": TimeoutError("untrusted prose"),
            "dev-02": b'{"wrong":true}',
            "dev-03": mock_response(),
        },
    )
    assert report["mocked_local_fixture"]["missing_or_malformed_rate"] == 7 / 8
    assert all(r["local_attempts"] == 1 for r in report["receipts"])
    assert b"untrusted prose" not in canonical(report)
    with pytest.raises(ValueError):
        evaluate_development(ROOT, responses={"holdout-01": mock_response()})


def test_without_network_or_credential_environment_and_failclosed_routing(monkeypatch):
    import os

    def forbidden(*args, **kwargs):
        raise AssertionError("network/environment forbidden")

    monkeypatch.setattr(os, "getenv", forbidden)
    monkeypatch.setattr(os, "environ", {})
    for name in ("socket", "getaddrinfo", "create_connection"):
        monkeypatch.setattr(socket, name, forbidden)
    evaluate_development(ROOT)
    packet = adapter.readiness()
    assert not packet["ready"] and not packet["credential_read"]
    assert packet["provider_slug"] == "typesafe"
    assert (
        not packet["routing_fields_serialized"]
        and not packet["routing_controls_verified"]
    )
    assert packet["allow_fallbacks"] is False and packet["required_provider_only"] == [
        "typesafe"
    ]
    for blocker in (
        "remaining_prepaid_balance",
        "enforceable_usd_cap",
        "provider_filter_and_fallback_enforcement",
    ):
        assert blocker in packet["blockers"]
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
    assert all(
        report["learner_isolation"][k]
        for k in (
            "advisory_unchanged",
            "beta_bernoulli_unchanged",
            "fictional_canonical_input_unchanged",
        )
    )
    assert report["learner_isolation"]["advisory_status"] == "abstain"
    raw = canonical(report)
    for case, _ in load_development(ROOT):
        assert case.description.encode() not in raw
    spec = importlib.util.spec_from_file_location(
        "j1_privacy", scripts / "privacy_guard.py"
    )
    guard = importlib.util.module_from_spec(spec)
    monkeypatch.setitem(sys.modules, spec.name, guard)
    spec.loader.exec_module(guard)
    assert not guard.content_reasons(raw)
    assert not guard.content_reasons(adapter.fixture_request("Fictional task"))


@pytest.mark.parametrize(
    "field,value", [("input_tokens", 20_001), ("output_tokens", 513), ("cost", 1.01)]
)
def test_reported_usage_cap_violation_stops_without_retry(field, value):
    payload = response() | {"usage": {field: value}}
    fake = adapter.FakeTransport(canonical(payload))
    with pytest.raises(ValueError, match="cap"):
        fake.send(adapter.fixture_request("Fictional task"))
    with pytest.raises(ValueError, match="retries"):
        fake.send(adapter.fixture_request("Fictional task"))
    assert fake.calls == 1


@pytest.mark.parametrize("label", LABELS)
def test_fake_transport_rejects_label_only_choice_criteria(label):
    body = json.loads(adapter.fixture_request("Fictional task"))
    body["questions"][CHOICE_ID]["criteria"][label] = label
    with pytest.raises(ValueError, match="altered"):
        adapter.FakeTransport(mock_response()).send(canonical(body))


@pytest.mark.parametrize(
    "level,text",
    [
        ("0", "0"),
        ("1", "Full: the fictional tank is at capacity."),
        ("2", "A different fictional interpretation."),
    ],
)
def test_score_rejects_mismatched_legend_despite_valid_keys_and_weight(level, text):
    legend = {str(i): value for i, value in enumerate(adapter.SCORE_CRITERIA)}
    legend[level] = text
    answer = {
        "type": "score",
        "score": 1.0,
        "confidence": 0.8,
        "legend": legend,
        "probabilities": {"0": 0, "1": 1, "2": 0},
    }
    with pytest.raises(ValueError, match="legend differs"):
        adapter.parse_answer(answer, SCORE_CONTROL)


def test_descriptive_wire_version_preserves_frozen_internal_contracts():
    assert adapter.WIRE_VERSION == "openrouter-decisions-published-examples/v2"
    assert adapter.PREVIOUS_WIRE_VERSION == "openrouter-decisions-published-examples/v1"
    assert SCORE_CONTROL.id == "fictional_score_control_v1"
    assert SCORE_CONTROL.prompt == "Fictional scalar control"
    assert SCORE_CONTROL.levels == (0.0, 1.0, 2.0)
    assert len(load_development(ROOT)) == 8  # Pins original rubric/baseline/manifest.
    assert adapter.readiness()["ready"] is False


@pytest.mark.parametrize(
    "question",
    [
        Question(
            id="unregistered", kind="choice", prompt="Fictional", labels=("x", "y")
        ),
        Question(
            id="unregistered", kind="score", prompt="Fictional", levels=(0.0, 1.0, 2.0)
        ),
    ],
)
def test_unregistered_questions_cannot_fall_back_to_placeholder_criteria(question):
    with pytest.raises(ValueError, match="no frozen descriptions"):
        adapter.question_definition(question)
