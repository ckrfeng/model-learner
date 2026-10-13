"""Bounded, in-memory task-state hypotheses; prose never supplies verification."""

from __future__ import annotations

import copy
import re
from collections import Counter
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt, StrictStr

Intent = Literal[
    "objective",
    "requirement_added",
    "requirement_removed",
    "requirement_revised",
    "decision",
    "decision_reversed",
    "task_changed",
    "progress",
    "attempt_failed",
    "unresolved",
    "completion_claim",
    "ambiguous",
    "other",
]
INTENTS = tuple(Intent.__args__)


class Contract(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Message(Contract):
    role: Literal["user", "assistant"]
    text: StrictStr = Field(max_length=16384)
    turn: StrictInt = Field(ge=1, le=1000)


class Check(Contract):
    """Caller-attested independent evidence, never extracted from a message.

    revision binds a full acceptance check to the exact inferred scope. This is
    a demonstration sidecar, not an authenticated verifier or ledger outcome.
    """

    after_message: StrictInt = Field(ge=0)
    revision: StrictInt = Field(ge=1)
    evidence_id: StrictStr = Field(min_length=1, max_length=128)
    artifact_id: StrictStr = Field(min_length=1, max_length=128)
    acceptance_spec: StrictStr = Field(min_length=1, max_length=128)
    source: Literal["independent_verifier", "independent_human"]
    result: Literal["passed", "failed", "indeterminate"]
    scope: Literal["full_task", "partial"]


class Conversation(Contract):
    messages: tuple[Message, ...] = Field(max_length=128)
    checks: tuple[Check, ...] = Field(default=(), max_length=1000)
    history_complete: bool | None = None
    source_kind: Literal["real", "simulated", "benchmark", "unknown"] = "unknown"


def clauses(text: str) -> tuple[tuple[int, int, str], ...]:
    """Locate sentences outside fenced code; preserve exact evidence offsets."""
    # Quotes are ambiguous evidence; do not execute or obey embedded content.
    masked = re.sub(r"```[\s\S]*?(?:```|$)", lambda m: " " * len(m[0]), text)
    found = []
    for match in re.finditer(r"[^.!?\n;]+[.!?]?", masked):
        raw = match[0]
        start = match.start() + len(raw) - len(raw.lstrip(" \t-*"))
        end = match.end() - len(raw) + len(raw.rstrip())
        if start < end:
            found.append((start, end, text[start:end]))
    return tuple(found)


def tokens(text: str) -> tuple[str, ...]:
    return tuple(re.findall(r"[^\W_]+", text.casefold()))


def keyword_intent(text: str, role: str) -> Intent:
    """Deliberately weak reference: ignores negation, attribution and context."""
    t = text.casefold()
    for label, pattern in (
        ("completion_claim", r"\bdone\b|complete|passed"),
        ("attempt_failed", r"fail|broken|bug"),
        ("requirement_removed", r"remov|exclud|drop|skip"),
        ("requirement_added", r"must|need|support|include"),
        ("progress", r"added|implemented|fixed|updated"),
        ("decision", r"choose|use|decided"),
    ):
        if re.search(pattern, t):
            return label
    return "objective" if role == "user" else "other"


def rule_intent(text: str, role: str) -> Intent:
    """English speech-act cues, with conservative question/negation handling."""
    t = text.casefold().strip()
    if (
        "?" in t
        or re.search(r"\b(maybe|perhaps|might|possibly|if|hypothetical)\b", t)
        or t.startswith((">", '"', "“", "'"))
        or re.search(r"\b(said|says|claims?|example)\b|quoted (statement|claim)", t)
    ):
        return "ambiguous"
    if re.search(
        r"\b(new task|different task|switch tasks|forget "
        r"(?:this|that)|instead of this task)\b",
        t,
    ):
        return "task_changed" if role == "user" else "ambiguous"
    if re.search(r"\b(revert|reverse|go back|changed my mind)\b", t):
        return "decision_reversed" if role == "user" else "decision"
    if re.search(
        r"\b(not|never|no longer) "
        r"(?:done|complete|finished|resolved)\b|\b(still|remain\w*) "
        r"(?:pending|incomplete|unresolved|blocked)\b|\b(not "
        r"yet|cannot|unable|blocked|unresolved|pending)\b",
        t,
    ):
        return "unresolved"
    if re.search(
        r"\b(failed|failing|broken|crashes|does not work|did not "
        r"work|doesn.t work|bug|incorrect)\b",
        t,
    ):
        return "attempt_failed"
    if role == "user":
        if re.search(r"\b(replace|instead|rather than|change .+ to|revise)\b", t):
            return "requirement_revised"
        if re.search(
            r"\b(remove|exclude|drop|skip|omit|no longer require|do not "
            r"include|don.t include|without)\b",
            t,
        ):
            return "requirement_removed"
        if re.search(r"\b(choose|decided|decision|use|prefer|let.s)\b", t):
            return "decision"
        if re.search(
            r"\b(also|add|must|need|require|support|include|ensure|keep|only|av"
            r"oid|preserve|should|now)\b",
            t,
        ):
            return "requirement_added"
        if re.search(
            r"\b(build|write|implement|create|compare|explain|design|develop|ma"
            r"ke|summarize|building|writing|implementing|creating|comparing|"
            r"studying|learning|developing|working on|understand|learn|study|"
            r"research|evaluate|analyze|plan|translate|explore|investigate)\b",
            t,
        ):
            return "objective"
    if re.search(
        r"\b(done|finished|completed|complete|all tests passed|tests pass)\b", t
    ):
        return "completion_claim"
    if re.search(
        r"\b(implemented|added|updated|fixed|tested|wrote|created|resolved)\b", t
    ) and not re.search(r"\b(will|plan|going to|not|haven.t|didn.t)\b", t):
        return "progress"
    if role == "assistant" and re.search(r"\b(decided|choose|use|strategy)\b", t):
        return "decision"
    return "other"


_STOP = set(
    "a an the please now also must should need require include "
    "support remove exclude drop skip omit do not no longer only use "
    "choose decided we i you it this that to of for and or with from "
    "is be as task build write implement create compare explain "
    "instead replace change revise".split()
)


def _content(text: str) -> set[str]:
    return set(tokens(text)) - _STOP


def _links(text: str, facts: list[dict], ids: list[str]) -> list[str]:
    query = _content(text)
    return [f["id"] for f in facts if f["id"] in ids and query & _content(f["text"])]


def analyze(conversation: Conversation, *, classifier=None) -> dict:
    """No I/O, model downloads, storage, task associations or learning outcomes.

    Each checkpoint sees only its prefix. Scope edits invalidate earlier checks.
    Match scores are hypotheses, never probabilities of correct understanding.
    """
    if not isinstance(conversation, Conversation):
        raise ValueError("validated Conversation required")
    messages = conversation.messages
    if sum(len(m.text.encode()) for m in messages) > 65536:
        raise ValueError("conversation text byte limit exceeded")
    if any(a.turn > b.turn for a, b in zip(messages, messages[1:], strict=False)):
        raise ValueError("source message order must be nondecreasing")
    if any(c.after_message >= len(messages) for c in conversation.checks):
        raise ValueError("check is outside the conversation")
    segments = tuple(clauses(m.text) for m in messages)
    if sum(len(parts) for parts in segments) > 256:
        raise ValueError("conversation clause limit exceeded")
    classify = classifier or rule_intent
    facts, timeline = [], []
    state = {
        "task": 0,
        "revision": 0,
        "objective": None,
        "requirement_evidence": [],
        "removal_evidence": [],
        "decision_evidence": [],
        "unresolved": [],
        "progress": [],
        "completion_reports": [],
        "uncertainty": [],
        "verification": "unknown",
        "verification_evidence": [],
    }
    for index, message in enumerate(messages):
        changes = []
        for start, end, text in segments[index]:
            intent = classify(text, message.role)
            if intent not in INTENTS:
                raise ValueError("unsupported classifier intent")
            # A statistical model cannot relax source or evidence safety rules.
            if message.role == "assistant" and intent in {
                "objective",
                "requirement_added",
                "requirement_removed",
                "requirement_revised",
                "task_changed",
                "decision_reversed",
            }:
                intent = "other"
            fid = f"m{index}:s{start}-{end}"
            fact = {
                "id": fid,
                "message": index,
                "turn": message.turn,
                "role": message.role,
                "span": [start, end],
                "text": text,
                "intent": intent,
                "evidence_kind": f"{message.role}_statement",
                "interpretation": "inferred",
                "links": [],
            }
            prior_objective = state["objective"]
            if intent == "task_changed" or (
                prior_objective is None
                and message.role == "user"
                and intent == "objective"
            ):
                if intent == "task_changed":
                    state.update(
                        requirement_evidence=[],
                        removal_evidence=[],
                        decision_evidence=[],
                        unresolved=[],
                        progress=[],
                        completion_reports=[],
                        uncertainty=[],
                    )
                state.update(task=state["task"] + 1, objective=fid)
                state["revision"] += 1
                changes.append(
                    {
                        "kind": "task_changed" if prior_objective else "objective",
                        "evidence": fid,
                        "previous": prior_objective,
                    }
                )
            if message.role == "user" and intent in {
                "objective",
                "requirement_added",
                "requirement_revised",
                "requirement_removed",
            }:
                if intent in {"requirement_removed", "requirement_revised"}:
                    # Sparse overlap only proposes targets. No automatic deletion:
                    # list scopes and pronouns cannot be safely resolved by overlap.
                    fact["links"] = _links(text, facts, state["requirement_evidence"])
                    state[
                        "removal_evidence"
                        if intent == "requirement_removed"
                        else "requirement_evidence"
                    ].append(fid)
                    if not fact["links"]:
                        state["uncertainty"].append(
                            {"evidence": fid, "reason": "change_target_unresolved"}
                        )
                else:
                    state["requirement_evidence"].append(fid)
                state["revision"] += 1
                changes.append(
                    {
                        "kind": intent,
                        "evidence": fid,
                        "targets": fact["links"],
                        "application": "scope_overlay"
                        if intent in {"requirement_removed", "requirement_revised"}
                        else "added",
                    }
                )
                if state["objective"] is None:
                    state["uncertainty"].append(
                        {"evidence": fid, "reason": "objective_not_established"}
                    )
            if intent in {"decision", "decision_reversed"}:
                fact["links"] = _links(text, facts, state["decision_evidence"])
                state["decision_evidence"].append(fid)
                if message.role == "user":
                    state["requirement_evidence"].append(fid)
                    state["revision"] += 1
                    if state["objective"] is None:
                        state["uncertainty"].append(
                            {"evidence": fid, "reason": "objective_not_established"}
                        )
                changes.append(
                    {"kind": intent, "evidence": fid, "targets": fact["links"]}
                )
                if intent == "decision_reversed":
                    if not fact["links"]:
                        state["uncertainty"].append(
                            {"evidence": fid, "reason": "reversal_target_unresolved"}
                        )
            if intent in {"attempt_failed", "unresolved"}:
                state["unresolved"].append(fid)
                changes.append({"kind": intent, "evidence": fid})
            if intent in {"progress", "completion_claim"}:
                state[
                    "progress" if intent == "progress" else "completion_reports"
                ].append(fid)
                changes.append({"kind": intent, "evidence": fid})
            if intent == "ambiguous":
                state["uncertainty"].append(
                    {"evidence": fid, "reason": "ambiguous_or_indirect_statement"}
                )
            if message.role == "user" and intent == "other":
                state["uncertainty"].append(
                    {"evidence": fid, "reason": "unparsed_user_statement"}
                )
            facts.append(fact)
        state["verification"] = "unknown"
        state["verification_evidence"] = []
        applicable = [
            c
            for c in conversation.checks
            if c.after_message == index and c.revision == state["revision"]
        ]
        state["verification_evidence"] = [c.model_dump() for c in applicable]
        full = [c for c in applicable if c.scope == "full_task"]
        if full and state["objective"] is not None:
            latest = max(c.after_message for c in full)
            current = [c for c in applicable if c.after_message == latest]
            outcomes = {c.result for c in current}
            state["verification"] = (
                "verified"
                if outcomes == {"passed"}
                else "failed_check"
                if outcomes == {"failed"}
                else "unknown"
            )
            state["verification_evidence"] = [c.model_dump() for c in current]
        # Unknown history and unresolved reports limit scope; check provenance is
        # separately visible, and a failed check is not a failed task outcome.
        timeline.append(
            {
                "after_message": index,
                "turn": message.turn,
                "state": copy.deepcopy(state),
                "changes": changes,
            }
        )
    return {
        "format": "conversation-task-state/v1",
        "backend": "local_cpu",
        "source_kind": conversation.source_kind,
        "facts": facts,
        "timeline": timeline,
        "coverage": {
            "messages": len(messages),
            "history_complete": conversation.history_complete,
        },
        "state_semantics": {
            "requirement_evidence": "positive statements plus revision "
            "overlays; not an active requirement set",
            "removal_evidence": "negative scope overlays; original evidence "
            "is retained",
            "decision_evidence": "actor-attributed proposals/decisions plus "
            "reversals; acceptance is not inferred",
            "unresolved": "reported obstacles; later progress does not prove "
            "resolution",
            "verification": "independent full acceptance evidence at this "
            "exact checkpoint only",
        },
        "limitations": [
            "English cue rules infer speech acts; unsupported phrasing can be missed.",
            "Requirements and decisions are evidence with scope overlays, not "
            "resolved logical formulas.",
            "Lexical change targets are candidates; pronouns and partial list "
            "edits need review.",
            "Progress and obstacles are reports; their real-world truth is unknown.",
            "Independent checks are caller-attested and scoped, not "
            "authenticated here.",
            "No transcript or semantic state is persisted by this function.",
        ],
    }


def render(result: dict, *, emit_text: bool = False) -> dict:
    """Explicit display consent for text and independent evidence identifiers."""
    output = copy.deepcopy(result)
    if not emit_text:
        for fact in output["facts"]:
            fact.pop("text")
        for checkpoint in output["timeline"]:
            for check in checkpoint["state"]["verification_evidence"]:
                for key in ("evidence_id", "artifact_id", "acceptance_spec"):
                    check.pop(key)
    output["text_emitted"] = emit_text
    return output


def from_read(read) -> Conversation:
    """Reuse an opted-in importer read in memory; never ingest or copy raw data."""
    messages = tuple(
        Message(
            role=m["role"],
            turn=i + 1,
            text="\n".join(read.text[m["native_message_id"]]),
        )
        for i, t in enumerate(read.metadata["turns"])
        for m in (t["messages"] or [])
    )
    if read.metadata["items_view"] != "full":
        raise ValueError("semantic analysis requires an opted-in text read")
    return Conversation(messages=messages, history_complete=None, source_kind="real")


def intent_counts(result: dict) -> dict[str, int]:
    return dict(Counter(f["intent"] for f in result["facts"]))
