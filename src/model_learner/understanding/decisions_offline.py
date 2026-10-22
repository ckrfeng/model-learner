"""Offline implementation of supplied OpenRouter Decisions examples.

No HTTP library, credential loading, DNS, retries or live transport. Published
examples establish demonstrated shapes, not routing support or a normative schema.
"""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass

from model_learner.understanding.intent import (
    QUESTIONS,
    SCORE_CONTROL,
    Prediction,
    Question,
    canonical,
)

ORIGIN = "https://openrouter.ai"
PATH = "/api/alpha/decisions"
MODEL = "typesafe/jev-1.14"
PUBLISHED_RETURNED_MODEL = "typesafe/jev-1.14-20261014"
PROVIDER_SLUG = "typesafe"
PREVIOUS_WIRE_VERSION = "openrouter-decisions-published-examples/v1"
WIRE_VERSION = "openrouter-decisions-published-examples/v2"
CHOICE_CRITERIA = {
    "bug_fix": "Restore stated existing intended behavior.",
    "new_feature": "Add stated new behavior.",
    "refactor": "Reorganize executable implementation while preserving behavior.",
    "investigation": "Diagnose, compare or explain without a requested repair.",
    "documentation": "Change prose or examples intended only as documentation.",
    "unclear": (
        "No clear primary intent: equal independent objectives, vague requests, "
        "or insufficient context."
    ),
}
SCORE_INSTRUCTIONS = (
    "Classify the current fill level of the fictional tank using these ordered levels."
)
SCORE_CRITERIA = (
    "Empty: the fictional tank contains no liquid.",
    "Partially filled: the fictional tank contains some liquid below capacity.",
    "Full: the fictional tank is at capacity.",
)
CREDENTIAL_NAME = "OPENROUTER_API_KEY"  # Name only; never read here.
MAX_REQUEST_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 32 * 1024
MAX_DESCRIPTION_BYTES = 4096
MAX_INPUT_TOKEN_PLAN = 20_000
MAX_OUTPUT_TOKEN_PLAN = 512
TOLERANCE = 1e-6  # Conservative local validation tolerance; official tolerance unknown.


class ContractUnavailable(ValueError):
    """Provider routing/enforcement not established for this endpoint."""


def serialize_decisions(*args, **kwargs) -> bytes:
    """Live use is always blocked; documented example bytes are fake-only."""
    raise ContractUnavailable(
        "Decisions provider filtering/fallback enforcement unverified"
    )


def question_definition(question: Question) -> dict:
    """Map frozen internal semantics onto the published typed field names."""
    value = {"type": question.kind, "instructions": question.prompt}
    if question.kind == "choice":
        if question.labels != QUESTIONS[0].labels:
            raise ValueError("no frozen descriptions for these choice criteria")
        value["criteria"] = {label: CHOICE_CRITERIA[label] for label in question.labels}
    elif question.kind == "score":
        if question.levels != tuple(float(i) for i in range(len(question.levels))):
            raise ValueError("published score levels must be zero-based indices")
        if question != SCORE_CONTROL:
            raise ValueError("no frozen descriptions for this score control")
        value["instructions"] = SCORE_INSTRUCTIONS
        value["criteria"] = list(SCORE_CRITERIA)
    return value


def fixture_request(
    description: str,
    *,
    input_token_plan: int = 4096,
    output_token_plan: int = 256,
    questions: tuple[Question, ...] = QUESTIONS,
) -> bytes:
    """Published request fields only, for the offline fake transport.

    Routing/output enforcement is unverified: no invented provider or token fields
    are added. Planning limits/policy remain local and cannot authorize live use.
    Only reviewed fictional caller inputs are appropriate; not a text sanitizer.
    """
    if type(description) is not str or not description.strip():
        raise ValueError("a nonblank fictional description is required")
    if len(description.encode()) > MAX_DESCRIPTION_BYTES:
        raise ValueError("description byte bound")
    if not 1 <= len(questions) <= 2 or len({q.id for q in questions}) != len(questions):
        raise ValueError("one or two distinct questions required")
    for value, maximum in (
        (input_token_plan, MAX_INPUT_TOKEN_PLAN),
        (output_token_plan, MAX_OUTPUT_TOKEN_PLAN),
    ):
        if type(value) is not int or not 0 < value <= maximum:
            raise ValueError("token planning bound")
    body = canonical(
        {
            "model": MODEL,
            "state": description,
            "questions": {q.id: question_definition(q) for q in questions},
        }
    )
    if len(body) > MAX_REQUEST_BYTES:
        raise ValueError("serialized request bound")
    return body


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def decode(body: bytes, maximum: int):
    if type(body) is not bytes or len(body) > maximum:
        raise ValueError("bounded bytes required")
    try:
        value = json.loads(
            body,
            object_pairs_hook=_unique,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("nonfinite JSON")
            ),
        )
        pending = [(value, 0)]
        while pending:
            node, depth = pending.pop()
            if depth > 32:
                raise ValueError("JSON nesting bound")
            if isinstance(node, dict):
                pending.extend((child, depth + 1) for child in node.values())
            elif isinstance(node, list):
                pending.extend((child, depth + 1) for child in node)
        return value
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise ValueError("invalid JSON") from exc


def number(value, low=0, high=1):
    if type(value) not in (int, float) or not low <= value <= high:
        raise ValueError("invalid numeric value")
    try:
        converted = float(value)
    except OverflowError as exc:
        raise ValueError("invalid numeric value") from exc
    if not math.isfinite(converted):
        raise ValueError("invalid numeric value")
    return converted


def keys(value, expected):
    if type(value) is not dict or set(value) != set(expected):
        raise ValueError("unsupported local shape")


def parse_answer(answer: dict, question: Question) -> dict:
    """Parse the demonstrated Choice/Noul/Score answer shape, without reasoning."""
    fields = {
        "choice": {"type", "choice", "confidence", "probabilities"},
        "noul": {"type", "noul"},
        "score": {"type", "score", "legend", "probabilities", "confidence"},
    }
    keys(answer, fields[question.kind])
    if answer["type"] != question.kind:
        raise ValueError("answer type mismatch")
    if question.kind == "noul":
        return {"true_probability": number(answer["noul"])}
    confidence = number(answer["confidence"])
    labels = (
        question.labels
        if question.kind == "choice"
        else tuple(str(i) for i in range(len(question.levels)))
    )
    keys(answer["probabilities"], labels)
    distribution = {k: number(v) for k, v in answer["probabilities"].items()}
    if abs(sum(distribution.values()) - 1) > TOLERANCE:
        raise ValueError("invalid distribution total")
    if question.kind == "choice":
        label = answer["choice"]
        if type(label) is not str or label not in question.labels:
            raise ValueError("undeclared label")
        # Confidence is separate from category probability in the published shape.
        return {"label": label, "confidence": confidence, "distribution": distribution}
    definition = question_definition(question)
    keys(answer["legend"], labels)
    if any(
        type(text) is not str or not text.strip() or len(text) > 2048
        for text in answer["legend"].values()
    ):
        raise ValueError("invalid score legend")
    if answer["legend"] != dict(zip(labels, definition["criteria"], strict=True)):
        raise ValueError("score legend differs from requested criteria")
    weighted = number(answer["score"], min(question.levels), max(question.levels))
    expected = sum(
        distribution[str(i)] * level for i, level in enumerate(question.levels)
    )
    if abs(weighted - expected) > TOLERANCE:
        raise ValueError("inconsistent weighted score")
    return {
        "weighted_score": weighted,
        "confidence": confidence,
        "levels": dict(zip(labels, question.levels, strict=True)),
    }


def usage_projection(usage) -> dict:
    """Project the usage fields in the supplied official Decisions example.

    This is the documented example subset, not a complete normative schema.
    Only scalar usage.cost is treated as reported USD, never X-Jev headers.
    Unknown/malformed is null, explicit zero remains zero; no charge estimate.
    """
    result = {
        "input_tokens": None,
        "output_tokens": None,
        "reported_cost_usd": None,
        "cost_estimate_usd": None,
        "usage_status": "missing",
    }
    if usage is None:
        return result
    if type(usage) is not dict:
        return result | {"usage_status": "malformed"}
    malformed = False
    for source, target in (
        ("input_tokens", "input_tokens"),
        ("output_tokens", "output_tokens"),
        ("cost", "reported_cost_usd"),
    ):
        value = usage.get(source)
        if value is None:
            continue
        if source == "cost":
            try:
                number(value, 0, float("inf"))
                valid = True
            except ValueError:
                valid = False
        else:
            valid = type(value) is int and 0 <= value <= 2**63 - 1
        if valid:
            result[target] = value
        else:
            malformed = True
    return result | {
        "usage_status": "malformed"
        if malformed
        else "partial"
        if any(
            result[k] is None
            for k in ("input_tokens", "output_tokens", "reported_cost_usd")
        )
        else "complete"
    }


def parse_response(
    body: bytes, *, questions: tuple[Question, ...] = QUESTIONS
) -> tuple[dict, dict]:
    """Validate published example fields; null metadata preserves unknown fixtures.

    No result here establishes routing enforcement, live completion or verification.
    Returned model identities are explicitly admitted, never inferred from a slug.
    """
    value = decode(body, MAX_RESPONSE_BYTES)
    keys(value, {"answers", "model", "provider", "usage", "id"})
    if value["model"] not in (None, MODEL, PUBLISHED_RETURNED_MODEL) or value[
        "provider"
    ] not in (None, "TypeSafe"):
        raise ValueError("unexpected reported model/provider")
    generation = value["id"]
    if generation is not None and (
        type(generation) is not str
        or not re.fullmatch(r"gen-dec-[A-Za-z0-9-]{1,120}", generation)
    ):
        raise ValueError("invalid generation identity")
    keys(value["answers"], {q.id for q in questions})
    parsed = {q.id: parse_answer(value["answers"][q.id], q) for q in questions}
    return parsed, {
        "requested_model": MODEL,
        "reported_model": value["model"],
        "effective_model_revision": None,
        "reported_provider": value["provider"],
        "routing_status": "unknown"
        if value["provider"] is None
        else "mocked_declaration",
        "generation_id": generation,
        "timestamp": None,
        "local_receipt": None,
        "completion": "mocked",
        **usage_projection(value["usage"]),
    }


def parse_fixture_response(body: bytes) -> tuple[Prediction, dict]:
    parsed, receipt = parse_response(body)
    return Prediction(
        intent=parsed[QUESTIONS[0].id]["label"],
        code_probability=parsed[QUESTIONS[1].id]["true_probability"],
        origin="mocked_external_model",
    ), receipt


@dataclass
class FakeTransport:
    """Single-use, no HTTP capability. Required route policy is out of band.

    It rejects unverified provider fields, never pretending they are supported.
    A fake's route-policy check is not real endpoint enforcement.
    """

    response: bytes | Exception
    calls: int = 0
    questions: tuple[Question, ...] = QUESTIONS

    def send(
        self,
        body: bytes,
        *,
        origin=ORIGIN,
        path=PATH,
        method="POST",
        status=200,
        redirected=False,
        allow_fallbacks=False,
        provider_only=(PROVIDER_SLUG,),
    ) -> bytes:
        if self.calls:
            raise ValueError("one local attempt only; retries forbidden")
        self.calls += 1
        if (
            (origin, path, method) != (ORIGIN, PATH, "POST")
            or redirected
            or status != 200
        ):
            raise ValueError("target/status/redirect rejected")
        if allow_fallbacks is not False or provider_only != (PROVIDER_SLUG,):
            raise ValueError("fallback/provider substitution rejected")
        request = decode(body, MAX_REQUEST_BYTES)
        if type(request) is not dict or type(request.get("state")) is not str:
            raise ValueError("invalid request")
        if body != fixture_request(request["state"], questions=self.questions):
            raise ValueError(
                "altered model/questions or unsupported provider/bounds fields"
            )
        if isinstance(self.response, Exception):
            raise self.response
        value = decode(self.response, MAX_RESPONSE_BYTES)
        usage = usage_projection(value.get("usage") if type(value) is dict else None)
        for field, maximum in (
            ("input_tokens", MAX_INPUT_TOKEN_PLAN),
            ("output_tokens", MAX_OUTPUT_TOKEN_PLAN),
            ("reported_cost_usd", 1),
        ):
            if usage[field] is not None and usage[field] > maximum:
                raise ValueError("reported usage exceeds local offline cap")
        return self.response


def readiness() -> dict:
    """Offline packet only. No enabling path, even with a local credential."""
    return {
        "version": "jev-one-request-readiness/v1",
        "ready": False,
        "mode": "offline_only",
        "wire_examples": WIRE_VERSION,
        "schema_basis": "supplied_official_examples; not_complete_normative_schema",
        "credential_name": CREDENTIAL_NAME,
        "credential_read": False,
        "origin": ORIGIN,
        "path": PATH,
        "method": "POST",
        "requested_model": MODEL,
        "intended_provider": "TypeSafe",
        "provider_slug": PROVIDER_SLUG,
        "provider_slug_basis": "user-supplied official provider/model pages",
        "required_provider_only": [PROVIDER_SLUG],
        "allow_fallbacks": False,
        "routing_fields_serialized": False,
        "routing_controls_verified": False,
        "retries": 0,
        "max_requests": 1,
        "max_exposure_usd": 1,
        "max_input_token_plan": MAX_INPUT_TOKEN_PLAN,
        "max_output_token_plan": MAX_OUTPUT_TOKEN_PLAN,
        "max_request_bytes": MAX_REQUEST_BYTES,
        "max_response_bytes": MAX_RESPONSE_BYTES,
        "blockers": [
            "provider_filter_and_fallback_enforcement",
            "official_float_tolerance",
            "provider_output_limit_enforcement",
            "credential_account_key_limits",
            "remaining_prepaid_balance",
            "exact_model_pricing_and_billing_terms",
            "enforceable_usd_cap",
            "separate_one_request_authorization",
        ],
        "stop_on": [
            "timeout",
            "error",
            "unknown_settlement",
            "missing_route",
            "missing_cost",
            "cap_violation",
            "unexpected_model_provider",
        ],
        "funding": "existing_prepaid_only; no topup/subscription/provider_fallback",
    }
