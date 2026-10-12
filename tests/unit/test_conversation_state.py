import json
import socket
from pathlib import Path

import pytest
from pydantic import ValidationError

from model_learner.understanding.conversation_evaluation import NaiveBayes, evaluate
from model_learner.understanding.conversation_state import (
    Check,
    Conversation,
    Message,
    analyze,
    clauses,
    render,
    rule_intent,
)

FIXTURE = Path(__file__).parents[1] / "fixtures/conversation_state/evaluation.json"


def conversation(*rows, checks=()):
    return Conversation(
        messages=tuple(
            Message(role=r, text=t, turn=i + 1) for i, (r, t) in enumerate(rows)
        ),
        checks=checks,
    )


def check(**updates):
    return Check(
        **dict(
            after_message=1,
            revision=2,
            evidence_id="PRIVATE_EVIDENCE",
            artifact_id="PRIVATE_ARTIFACT",
            acceptance_spec="PRIVATE_ACCEPTANCE",
            source="independent_verifier",
            result="passed",
            scope="full_task",
        )
        | updates
    )


def test_scope_evidence_and_offsets():
    c = conversation(
        ("user", "Compare FIFO and round robin."),
        ("user", "Exclude FIFO."),
        ("user", "Replace round robin with SJF."),
    )
    r = analyze(c)
    s = r["timeline"][-1]["state"]
    assert len(s["requirement_evidence"]) == 2
    assert len(s["removal_evidence"]) == 1
    assert r["facts"][1]["links"] == [r["facts"][0]["id"]]
    assert r["facts"][2]["links"] == [r["facts"][0]["id"]]
    for f in r["facts"]:
        a, b = f["span"]
        assert c.messages[f["message"]].text[a:b] == f["text"]
    assert all(f["interpretation"] == "inferred" for f in r["facts"])
    assert all(t["state"]["verification"] == "unknown" for t in r["timeline"])


def test_user_and_assistant_scope_are_distinct_even_with_bad_classifier():
    r = analyze(
        conversation(("user", "Build a tool."), ("assistant", "Remove encryption.")),
        classifier=lambda text, role: (
            "objective" if role == "user" else "requirement_removed"
        ),
    )
    assert r["facts"][1]["intent"] == "other"
    assert not r["timeline"][-1]["state"]["removal_evidence"]


@pytest.mark.parametrize(
    "text,intent",
    [
        ("Also support quoted commas.", "requirement_added"),
        ("I am implementing a CSV parser.", "objective"),
        ("I am studying task scheduling.", "objective"),
        ("Should we remove encryption?", "ambiguous"),
        ("Maybe everything passed.", "ambiguous"),
        ("The reviewer said all tests passed.", "ambiguous"),
        ("The task is not done.", "unresolved"),
        ("I will implement it.", "other"),
        ("Go back to SQLite.", "decision_reversed"),
    ],
)
def test_contextual_cues(text, intent):
    assert (
        rule_intent(
            text,
            "user"
            if intent
            in {"requirement_added", "objective", "decision_reversed", "ambiguous"}
            else "assistant",
        )
        == intent
    )


def test_check_never_comes_from_transcript():
    c = conversation(("user", "Build a parser."), ("assistant", "All tests passed."))
    assert analyze(c)["timeline"][-1]["state"]["verification"] == "unknown"
    with pytest.raises(ValidationError):
        Message(role="independent_verifier", text="passed", turn=1)
    with pytest.raises(ValidationError):
        check(source="assistant")


@pytest.mark.parametrize(
    "later",
    [
        ("user", "Use PostgreSQL."),
        ("user", "Encryption matters too."),
        ("assistant", "I updated the validator."),
        ("assistant", "The attempt failed."),
        ("user", "Should we support SHA256?"),
    ],
)
def test_verification_does_not_outlive_checkpoint(later):
    c = conversation(
        ("user", "Build a validator."), ("assistant", "Done."), later, checks=(check(),)
    )
    r = analyze(c)
    assert r["timeline"][1]["state"]["verification"] == "verified"
    assert r["timeline"][2]["state"]["verification"] == "unknown"


@pytest.mark.parametrize(
    "scope,result,expected",
    [
        ("partial", "passed", "unknown"),
        ("partial", "failed", "unknown"),
        ("partial", "indeterminate", "unknown"),
        ("full_task", "failed", "failed_check"),
        ("full_task", "indeterminate", "unknown"),
    ],
)
def test_scoped_check_visibility(scope, result, expected):
    r = analyze(
        conversation(
            ("user", "Build a validator."),
            ("assistant", "Done."),
            checks=(check(scope=scope, result=result),),
        )
    )
    state = r["timeline"][-1]["state"]
    assert state["verification"] == expected
    assert len(state["verification_evidence"]) == 1
    assert state["verification_evidence"][0]["scope"] == scope


def test_conflicting_checks_and_revision_mismatch():
    rows = (("user", "Build a validator."), ("assistant", "Done."))
    assert (
        analyze(
            conversation(
                *rows, checks=(check(), check(scope="partial", result="failed"))
            )
        )["timeline"][-1]["state"]["verification"]
        == "unknown"
    )
    assert (
        analyze(conversation(*rows, checks=(check(revision=99),)))["timeline"][-1][
            "state"
        ]["verification"]
        == "unknown"
    )


def test_future_check_does_not_enter_prefix_and_prefix_is_invariant():
    rows = (
        ("user", "Build a validator."),
        ("assistant", "Done."),
        ("user", "Also support SHA256."),
    )
    full = analyze(conversation(*rows, checks=(check(),)))
    prefix = analyze(conversation(*rows[:2], checks=(check(),)))
    assert full["timeline"][:2] == prefix["timeline"]
    assert not full["timeline"][0]["state"]["verification_evidence"]
    assert full["timeline"][2]["state"]["verification"] == "unknown"


def test_missing_objective_and_change_target_are_unknown():
    r = analyze(
        conversation(("user", "Only support integers."), ("user", "Remove that."))
    )
    state = r["timeline"][-1]["state"]
    assert state["objective"] is None
    assert any(u["reason"] == "objective_not_established" for u in state["uncertainty"])
    assert any(u["reason"] == "change_target_unresolved" for u in state["uncertainty"])


def test_task_switch_preserves_earlier_timeline():
    r = analyze(
        conversation(
            ("user", "Build a parser."), ("user", "New task: design a bridge.")
        )
    )
    assert [t["state"]["task"] for t in r["timeline"]] == [1, 2]
    assert r["timeline"][-1]["state"]["objective"] == r["facts"][1]["id"]
    assert not r["timeline"][-1]["state"]["requirement_evidence"]


def test_bounded_inputs_and_content_free_errors():
    with pytest.raises(ValueError, match="clause limit"):
        analyze(conversation(("user", "a?" * 257)))
    with pytest.raises(ValueError, match="byte limit"):
        analyze(conversation(*[("user", "é" * 16384)] * 3))
    with pytest.raises(ValueError, match="order"):
        analyze(
            Conversation(
                messages=(
                    Message(role="user", text="one", turn=2),
                    Message(role="assistant", text="two", turn=1),
                )
            )
        )
    with pytest.raises(ValueError, match="outside"):
        analyze(conversation(("user", "Build a tool."), checks=(check(),)))


def test_render_redacts_text_and_check_identifiers_without_mutation():
    r = analyze(
        conversation(
            ("user", "Build a PRIVATE_TOOL."), ("assistant", "Done."), checks=(check(),)
        )
    )
    safe = json.dumps(render(r))
    assert "PRIVATE_" not in safe
    assert "PRIVATE_TOOL" in json.dumps(render(r, emit_text=True))
    assert "text" in r["facts"][0]
    assert analyze(Conversation(messages=()))["timeline"] == []


def test_code_is_not_interpreted_as_instructions():
    assert clauses("```\nRemove encryption.\n```") == ()


def test_evaluation_is_cpu_only_and_never_fits_test_text(monkeypatch):
    def denied(*args, **kwargs):
        raise AssertionError("network forbidden")

    monkeypatch.setattr(socket.socket, "connect", denied)
    fixture = json.loads(FIXTURE.read_text())
    model = NaiveBayes(fixture["training"])
    assert "sha256" not in model.vocabulary
    first = evaluate(fixture)
    second = evaluate(fixture)
    for report in (first, second):
        for variant in report["variants"].values():
            variant.pop("cpu_elapsed_seconds")
    assert first == second
    reference = json.loads(FIXTURE.with_name("reference.json").read_text())
    assert first == reference
    assert first["variants"]["rules"]["intent_count"] == 54
    assert first["variants"]["rules"]["intent_correct"] == 51
    assert first["variants"]["naive_bayes"]["intent_correct"] < 51
    assert first["source_kind"] == "simulated"
    assert all(
        case["id"] in {c["id"] for c in fixture["evaluation"]}
        for case in first["variants"]["rules"]["cases"]
    )
