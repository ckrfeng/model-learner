"""Projection checks reuse existing fixtures; no new evaluation conversations."""

import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from model_learner.understanding.conversation_projection import (
    EvidenceViews,
    evaluate,
    from_read,
)
from model_learner.understanding.conversation_state import Conversation, analyze

DEMO = Path(__file__).parents[1] / "fixtures/conversation_state/demo.json"


def views():
    data = json.loads(DEMO.read_text())
    rows = tuple(
        dict(
            original_message=i,
            native_message_id=f"message-{i}",
            native_turn_id=f"turn-{m['turn']}",
            source_item_ordinal=0,
            **m,
        )
        for i, m in enumerate(data["messages"])
    )
    return EvidenceViews(rows, None, "simulated")


def test_all_users_and_exact_source_spans_survive_without_assistant_state():
    source = views()
    report = evaluate(source)
    users = tuple(r for r in source.rows if r["role"] == "user")
    assert report["source_kind"] == "simulated"
    assert len(report["checkpoints"]) == len(users)
    for i, checkpoint in enumerate(report["checkpoints"]):
        assert checkpoint["included_user_turns"] == [r["turn"] for r in users[: i + 1]]
        assert [r["native_message_id"] for r in checkpoint["references"]] == [
            r["native_message_id"] for r in users[: i + 1]
        ]
        result = checkpoint["prediction"]
        expected = analyze(
            Conversation(
                messages=tuple(
                    {k: r[k] for k in ("role", "text", "turn")} for r in users[: i + 1]
                ),
                source_kind="simulated",
            )
        )
        assert result["timeline"] == expected["timeline"]
        for fact in result["facts"]:
            ref = fact["source_reference"]
            original = source.rows[ref["original_message"]]
            assert ref["native_message_id"] == original["native_message_id"]
            a, b = fact["span"]
            assert (
                expected["facts"][result["facts"].index(fact)]["text"]
                == original["text"][a:b]
            )
            assert ref["original_evidence_id"] == f"m{ref['original_message']}:s{a}-{b}"
            assert "text" not in fact
    assert report["checkpoints"][-1]["omitted_assistant_messages"] == [2]
    assert len(report["execution_messages"]) == 3
    assert all(
        e["prediction"]["timeline"][-1]["state"]["verification"] == "unknown"
        for e in report["execution_messages"]
    )
    assert report["independent_verification"] is None
    assert not any(
        c["prediction"]["timeline"][-1]["state"]["progress"]
        for c in report["checkpoints"]
    )
    assert "The multiline attempt failed" not in json.dumps(report)


@pytest.mark.parametrize(
    "text,bound",
    [
        ("x. " * 257, "clauses"),
        ("x" * 16385, "message_characters"),
        ("é" * 16384, "text"),
    ],
)
def test_bounds_are_explicit_and_later_users_never_silently_disappear(text, bound):
    source = views()
    # Perturb existing messages solely to exercise resource limits.
    rows = tuple(r | {"text": text} if r["role"] == "user" else r for r in source.rows)
    report = evaluate(EvidenceViews(rows, None, "simulated"))
    assert len(report["checkpoints"]) == 6
    final = report["checkpoints"][-1]
    assert final["prediction"] is None and final["bounds_reached"][bound]
    assert len(final["references"]) == 6


def test_read_bridge_preserves_parts_order_and_refuses_metadata_only():
    source = views()
    read = SimpleNamespace(metadata={"items_view": "full", "turns": []}, text={})
    for row in source.rows:
        read.metadata["turns"].append(
            dict(
                native_turn_id=row["native_turn_id"],
                messages=[
                    dict(
                        native_message_id=row["native_message_id"],
                        role=row["role"],
                        source_item_ordinal=0,
                    )
                ],
            )
        )
        read.text[row["native_message_id"]] = row["text"].split(" ")
    projected = from_read(read)
    assert [r["text"] for r in projected.rows] == [
        "\n".join(r["text"].split(" ")) for r in source.rows
    ]
    assert "Build" not in repr(projected)
    read.metadata["items_view"] = "notLoaded"
    with pytest.raises(ValueError, match="opted-in"):
        from_read(read)
