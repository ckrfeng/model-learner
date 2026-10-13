"""Explicit evidence views; no retrieval, retention, clipping or semantic rules."""

from __future__ import annotations

from dataclasses import dataclass, field

from model_learner.understanding.conversation_state import (
    Conversation,
    Message,
    analyze,
    clauses,
    render,
)

POLICY = {
    "version": "conversation-evidence-views/v1",
    "task_intent": "all user messages, unchanged newline-joined parts, source order",
    "execution": "each whole assistant message analyzed separately; no carryover",
    "checks": "not supplied; independent evidence unavailable, not absent",
    "bounds": "unchanged analyzer; reject oversized prefixes, never clip",
    "references": "original full-view message index, native IDs and exact spans",
    "history": "exposed pagination only; original completeness unknown",
}


@dataclass(frozen=True)
class EvidenceViews:
    # Native identifiers and opted-in text must not leak through repr/logging.
    rows: tuple[dict, ...] = field(repr=False)
    history_complete: bool | None = None
    source_kind: str = "real"


def from_read(read) -> EvidenceViews:
    """Select no messages yet: retain an in-memory mapping of both actors."""
    if read.metadata["items_view"] != "full":
        raise ValueError("projection requires an opted-in full message read")
    rows = []
    seen = set()
    for turn, source in enumerate(read.metadata["turns"], 1):
        for message in source["messages"]:
            native_id = message["native_message_id"]
            if native_id in seen:
                raise ValueError("duplicate source message")
            seen.add(native_id)
            rows.append(
                {
                    "original_message": len(rows),
                    "turn": turn,
                    "role": message["role"],
                    "native_message_id": native_id,
                    "native_turn_id": source["native_turn_id"],
                    "source_item_ordinal": message["source_item_ordinal"],
                    "text": "\n".join(read.text[native_id]),
                }
            )
    return EvidenceViews(tuple(rows))


def shape(rows: tuple[dict, ...]) -> dict:
    return {
        "messages": len(rows),
        "utf8_bytes": sum(len(r["text"].encode()) for r in rows),
        "clauses": sum(len(clauses(r["text"])) for r in rows),
        "max_message_characters": max((len(r["text"]) for r in rows), default=0),
    }


def _predict(rows: tuple[dict, ...], views: EvidenceViews) -> dict:
    sizes = shape(rows)
    bounds = {
        "text": sizes["utf8_bytes"] > 65536,
        "clauses": sizes["clauses"] > 256,
        "messages": sizes["messages"] > 128,
        "message_characters": sizes["max_message_characters"] > 16384,
    }
    references = [{k: v for k, v in r.items() if k != "text"} for r in rows]
    output = {"input": sizes, "bounds_reached": bounds, "references": references}
    if any(bounds.values()):
        return output | {"prediction": None, "status": "blocked_analyzer_bound"}
    conversation = Conversation(
        messages=tuple(
            Message(**{k: r[k] for k in ("role", "turn", "text")}) for r in rows
        ),
        history_complete=views.history_complete,
        source_kind=views.source_kind,
    )
    prediction = render(analyze(conversation))
    # Keep the analyzer's original output intact; attach source references alongside.
    for fact in prediction["facts"]:
        reference = references[fact["message"]]
        start, end = fact["span"]
        fact["source_reference"] = reference | {
            "original_evidence_id": f"m{reference['original_message']}:s{start}-{end}",
            "span": fact["span"],
        }
    return output | {"prediction": prediction, "status": "analyzed"}


def evaluate(views: EvidenceViews) -> dict:
    """Every user checkpoint includes its entire user prefix, even after a block.

    Assistant analysis is a separate message-local report view. A zero recognized
    count never establishes absence, and no assistant statement is a check.
    """
    users = tuple(r for r in views.rows if r["role"] == "user")
    assistants = tuple(r for r in views.rows if r["role"] == "assistant")
    checkpoints = []
    for index, user in enumerate(users):
        omitted = tuple(
            r for r in assistants if r["original_message"] < user["original_message"]
        )
        checkpoints.append(
            _predict(users[: index + 1], views)
            | {
                "at_original_message": user["original_message"],
                "included_user_turns": [r["turn"] for r in users[: index + 1]],
                "omitted_assistant_messages": [r["original_message"] for r in omitted],
                "omitted_assistant_input": shape(omitted),
                "evaluable": [
                    "user objective",
                    "user requirement evidence",
                    "user changes",
                    "user decisions/reversals",
                    "user-reported status",
                    "user ambiguity",
                ],
                "unavailable": [
                    "assistant reports/choices",
                    "acceptance of an omitted assistant proposal",
                    "independent checks",
                    "verified outcomes",
                    "resolved active scope",
                ],
                "context_limitation": "References to omitted assistant proposals "
                "may change interpretation or target links.",
            }
        )
    execution = [
        _predict((r,), views)
        | {
            "included_user_turns": [],
            "omitted_assistant_messages": [
                a["original_message"]
                for a in assistants
                if a["original_message"] < r["original_message"]
            ],
            "evaluable": [
                "this assistant's reported issues, progress, choices "
                "and completion claims"
            ],
            "unavailable": [
                "user intent",
                "cross-message execution state",
                "independent verification",
                "typed test results",
            ],
        }
        for r in assistants
    ]
    return {
        "format": POLICY["version"],
        "source_kind": views.source_kind,
        "history_complete": views.history_complete,
        "role_statistics": {
            role: shape(tuple(r for r in views.rows if r["role"] == role))
            for role in ("user", "assistant")
        },
        "checkpoints": checkpoints,
        "execution_messages": execution,
        "independent_verification": None,
        "verification_missingness": "not inspected or supplied",
        "execution_limitation": "Message-local assistant reports, no cross-message "
        "state or independent execution reconstruction. "
        "Test results have no dedicated semantic field.",
    }
