"""Common evidence contract and a deliberately bounded structural baseline."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

Kind = Literal[
    "requested_action",
    "requirement_added",
    "constraint",
    "decision",
    "decision_reversed",
    "requirement_removed",
    "requirement_revised",
    "requirement_reinstated",
    "reported_failure",
    "reported_progress",
    "completion_claim",
    "conditional",
    "earlier_reference",
    "uncertainty",
]
Mode = Literal["request", "hypothetical", "report", "unknown"]


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Citation(Contract):
    message_id: StrictStr
    quote: StrictStr = Field(min_length=1)
    occurrence: StrictInt = Field(ge=0)


class Statement(Contract):
    summary: StrictStr = Field(min_length=1)
    mode: Mode
    evidence: Citation
    target: Citation | None
    condition: StrictStr | None


class Event(Statement):
    kind: Kind


class Extraction(Contract):
    objective: Statement | None
    events: list[Event] = Field(max_length=128)


def locate(citation: Citation, messages: list[dict]) -> dict:
    """Resolve an exact quote; never fuzzy-correct a fabricated citation."""
    rows = [m for m in messages if m["id"] == citation.message_id]
    if len(rows) != 1:
        raise ValueError("unknown or duplicate evidence message")
    message = rows[0]
    starts = [
        m.start() for m in re.finditer(re.escape(citation.quote), message["text"])
    ]
    if citation.occurrence >= len(starts):
        raise ValueError("quote occurrence is absent")
    start = starts[citation.occurrence]
    return {
        "message_id": message["id"],
        "span": [start, start + len(citation.quote)],
        "role": message["role"],
        "turn": message["turn"],
    }


def validate_output(raw: dict, messages: list[dict]) -> dict:
    """Retain bad-event counts; reject wrong checkpoint/future/self targets."""
    parsed = Extraction.model_validate(raw)
    result = parsed.model_dump()
    accepted, invalid = [], []
    order = {m["id"]: i for i, m in enumerate(messages)}
    for event in result["events"]:
        try:
            event["source"] = locate(
                Citation.model_validate(event["evidence"]), messages
            )
            if event["evidence"]["message_id"] != messages[-1]["id"]:
                raise ValueError("event is not message-local")
            event["target_source"] = None
            if event["target"] is not None:
                event["target_source"] = locate(
                    Citation.model_validate(event["target"]), messages
                )
                if order[event["target"]["message_id"]] >= len(messages) - 1:
                    raise ValueError("target is not earlier evidence")
            accepted.append(event)
        except ValueError as error:
            invalid.append({"event": event, "reason": str(error)})
    result["events"] = accepted
    result["invalid_events"] = invalid
    result["objective_invalid"] = False
    if result["objective"] is not None:
        try:
            result["objective"]["source"] = locate(
                Citation.model_validate(result["objective"]["evidence"]), messages
            )
            if result["objective"]["target"] is not None:
                raise ValueError("objective target must be null")
        except ValueError:
            result["objective"] = None
            result["objective_invalid"] = True
    result["independent_verification"] = None
    return result


def citation(message: dict, start: int, end: int) -> dict:
    quote = message["text"][start:end]
    occurrence = sum(
        1 for m in re.finditer(re.escape(quote), message["text"]) if m.start() < start
    )
    return {"message_id": message["id"], "quote": quote, "occurrence": occurrence}


def units(text: str) -> list[dict]:
    """Preserve list items, wrapped paragraphs, code and original offsets."""
    result, fence, paragraph = [], None, None

    def flush():
        nonlocal paragraph
        if paragraph is not None:
            result.append({"start": paragraph[0], "end": paragraph[1], "type": "prose"})
            paragraph = None

    offset = 0
    for line in text.splitlines(keepends=True):
        stripped = line.strip()
        start = offset + len(line) - len(line.lstrip())
        end = offset + len(line.rstrip())
        marker = re.match(r"(`{3,}|~{3,})", stripped)
        if marker or fence:
            flush()
            if fence is None:
                fence = (marker[1][0], len(marker[1]), start)
            elif marker and marker[1][0] == fence[0] and len(marker[1]) >= fence[1]:
                result.append({"start": fence[2], "end": end, "type": "code"})
                fence = None
        elif not stripped:
            flush()
        elif re.match(r"(?:[-*+] |\d+[.)] )", stripped):
            flush()
            result.append({"start": start, "end": end, "type": "list"})
        elif line.startswith(("    ", "\t")) or re.match(
            r"(?:def |class |from \w+ import |import |return |[\w]+\s*=|[{}\[\]])",
            stripped,
        ):
            flush()
            result.append({"start": start, "end": end, "type": "code"})
        elif paragraph is not None:
            paragraph[1] = end
        else:
            paragraph = [start, end]
        offset += len(line)
    flush()
    if fence:
        result.append({"start": fence[2], "end": len(text), "type": "code"})
    return sorted(result, key=lambda u: u["start"])


def structure_extract(messages: list[dict]) -> dict:
    """No data fitting, corpus-specific vocabulary or forced target selection."""
    objective, events, previous = None, [], []
    for mi, message in enumerate(messages):
        current, header = [], ""
        for unit in units(message["text"]):
            start, end = unit["start"], unit["end"]
            text = message["text"][start:end]
            t = re.sub(r"\s+", " ", text).casefold()
            evidence = citation(message, start, end)
            if unit["type"] == "code":
                continue
            if t.endswith(":"):
                header = text
            base = {
                "summary": text,
                "mode": "request",
                "evidence": evidence,
                "target": None,
                "condition": None,
            }
            conditional = bool(re.search(r"\b(if|unless|provided|when)\b", t))
            hypothetical = bool(
                re.search(r"\b(hypothetical|for example|imagine|suppose)\b", t)
            )
            request = bool(
                re.search(
                    r"^(?:please |can you |could you |would you |"
                    r"i (?:want|need)|let.s |"
                    r"(?:build|create|write|make|compare|explain|run|check|report|summarize|"
                    r"reproduce|add|include|keep|use|choose|drop|remove|replace|"
                    r"restore|do not)\b)",
                    t,
                )
            )
            if conditional:
                base["condition"] = text
                current.append({**base, "kind": "conditional"})
            if hypothetical:
                current.append({**base, "kind": "uncertainty", "mode": "hypothetical"})
                continue
            kind = None
            if re.search(
                r"\b(restore|reinstate|bring .+ back|include .+ after all)\b", t
            ):
                kind = "requirement_reinstated"
            elif (
                re.search(r"\b(replace|instead|rather than|change .+ to|revise)\b", t)
                and request
            ):
                kind = "requirement_revised"
            elif (
                re.search(r"\b(drop|remove|exclude|omit|no longer require)\b", t)
                and request
            ):
                kind = "requirement_removed"
            elif re.search(r"\b(i choose|i decided|let.s use|i prefer)\b", t):
                kind = "decision"
            elif request:
                kind = "requested_action"
                objective = dict(base)
            elif unit["type"] == "list" and header:
                kind = "requirement_added"
                base["summary"] = header + " " + text
            elif re.search(r"\b(must|should|only|never|do not|cannot use)\b", t):
                kind = "constraint"
            elif not conditional and "?" not in t:
                base["mode"] = "report"
                if re.search(
                    r"\b(failed|broken|doesn.t work|did not work|still fails)\b", t
                ):
                    kind = "reported_failure"
                elif re.search(r"\b(done|complete|completed|finished|ready)\b", t):
                    kind = "completion_claim"
                elif re.search(
                    r"\b(added|implemented|fixed|tested|updated|wrote)\b", t
                ):
                    kind = "reported_progress"
            if kind is not None:
                if kind.startswith("requirement_") and kind != "requirement_added":
                    words = set(re.findall(r"\w+", t)) - set(
                        (
                            "the a an it that this requirement please "
                            "remove drop restore add to from"
                        ).split()
                    )
                    targets = [
                        e
                        for e in previous
                        if e["kind"]
                        in {
                            "requirement_added",
                            "constraint",
                            "requested_action",
                            "decision",
                            "requirement_removed",
                            "requirement_revised",
                        }
                        and words & set(re.findall(r"\w+", e["summary"].casefold()))
                    ]
                    if len(targets) == 1:
                        base["target"] = targets[0]["evidence"]
                current.append({**base, "kind": kind})
            else:
                current.append({**base, "kind": "uncertainty", "mode": "unknown"})
        if mi == len(messages) - 1:
            events = current
        previous.extend(current)
    return {"objective": objective, "events": events}


def frozen_extract(messages: list[dict], *, source_kind="unknown") -> dict:
    """Read-only adapter; no reconstructed reinstatement/conditional semantics."""
    from model_learner.understanding.conversation_state import Conversation, analyze

    output = analyze(
        Conversation.model_validate(
            {
                "messages": [
                    {k: m[k] for k in ("role", "turn", "text")} for m in messages
                ],
                "source_kind": source_kind,
            }
        )
    )
    mapping = {
        "objective": "requested_action",
        "requirement_added": "requirement_added",
        "requirement_removed": "requirement_removed",
        "requirement_revised": "requirement_revised",
        "decision": "decision",
        "decision_reversed": "decision_reversed",
        "attempt_failed": "reported_failure",
        "unresolved": "reported_failure",
        "progress": "reported_progress",
        "completion_claim": "completion_claim",
        "ambiguous": "uncertainty",
        "other": "uncertainty",
        "task_changed": "requested_action",
    }
    facts = {f["id"]: f for f in output["facts"]}

    def statement(f):
        kind = mapping[f["intent"]]
        report = kind in {"reported_failure", "reported_progress", "completion_claim"}
        # Candidate links cannot be promoted into resolved earlier targets.
        return {
            "summary": f["text"],
            "mode": "report"
            if report
            else ("unknown" if kind == "uncertainty" else "request"),
            "evidence": citation(messages[f["message"]], *f["span"]),
            "target": None,
            "condition": None,
        }

    anchor = output["timeline"][-1]["state"]["objective"]
    return {
        "objective": statement(facts[anchor]) if anchor else None,
        "events": [
            {**statement(f), "kind": mapping[f["intent"]]}
            for f in facts.values()
            if f["message"] == len(messages) - 1
        ],
    }
