"""Offline fixture boundary, NOT an implementation of the unverified alpha API.

No HTTP library, credential loading, DNS, retries or live transport is provided.
The fixture envelope and typed answers deliberately identify their local schema.
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass

from model_learner.understanding.intent import (
    QUESTIONS,
    VERSION,
    Prediction,
    Question,
    canonical,
)

ORIGIN = "https://openrouter.ai"
PATH = "/api/alpha/decisions"
MODEL = "typesafe/jev-1.14"
CREDENTIAL_NAME = "OPENROUTER_API_KEY"  # Name only; never read here.
MAX_REQUEST_BYTES = 16 * 1024
MAX_RESPONSE_BYTES = 32 * 1024
MAX_DESCRIPTION_BYTES = 4096
MAX_INPUT_TOKEN_PLAN = 20_000
MAX_OUTPUT_TOKEN_PLAN = 512
LOCAL_SCHEMA = "j1-local-fixture/v1"
TOLERANCE = 1e-6  # LOCAL tolerance; official alpha float tolerance is unverified.


class ContractUnavailable(ValueError):
    """Official captured schema/provider route required before wire implementation."""


def serialize_decisions(*args, **kwargs) -> bytes:
    """Fail closed instead of inventing an official provider-bound request."""
    raise ContractUnavailable("official Decisions schema and provider slug unverified")


def fixture_request(
    description: str, *, input_token_plan: int = 4096, output_token_plan: int = 256
) -> bytes:
    """Local projection of task text/questions only; cannot be sent to a provider.

    Bytes and token plans are independent limits, neither is an enforceable USD cap.
    A reviewed fictional caller is required; this is not a private-text sanitizer.
    """
    if type(description) is not str or not description.strip():
        raise ValueError("a nonblank fictional description is required")
    if len(description.encode()) > MAX_DESCRIPTION_BYTES:
        raise ValueError("description byte bound")
    for value, maximum in (
        (input_token_plan, MAX_INPUT_TOKEN_PLAN),
        (output_token_plan, MAX_OUTPUT_TOKEN_PLAN),
    ):
        if type(value) is not int or not 0 < value <= maximum:
            raise ValueError("token planning bound")
    body = canonical(
        {
            "schema": LOCAL_SCHEMA,
            "contract": VERSION,
            "target": {
                "origin": ORIGIN,
                "path": PATH,
                "method": "POST",
                "model": MODEL,
            },
            "provider": {"allow_fallbacks": False},
            "provider_slug": None,
            "state": description,
            "questions": [q.model_dump(mode="json") for q in QUESTIONS],
            "input_token_plan": input_token_plan,
            "output_token_plan": output_token_plan,
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
    """Strict LOCAL typed parser; deliberately no model-generated explanation."""
    fields = {
        "choice": {"id", "kind", "label", "confidence", "distribution"},
        "noul": {"id", "kind", "true_probability"},
        "score": {"id", "kind", "weighted_score", "levels", "confidence"},
    }
    keys(answer, fields[question.kind])
    if answer["id"] != question.id or answer["kind"] != question.kind:
        raise ValueError("answer identity/type mismatch")
    if question.kind == "noul":
        return {"true_probability": number(answer["true_probability"])}
    number(answer["confidence"])
    if question.kind == "choice":
        keys(answer["distribution"], question.labels)
        distribution = {k: number(v) for k, v in answer["distribution"].items()}
        label = answer["label"]
        if type(label) is not str or label not in question.labels:
            raise ValueError("undeclared label")
        if abs(sum(distribution.values()) - 1) > TOLERANCE:
            raise ValueError("invalid distribution total")
        if abs(answer["confidence"] - distribution[label]) > TOLERANCE:
            raise ValueError("confidence contradicts label probability")
        if distribution[label] + TOLERANCE < max(distribution.values()):
            raise ValueError("choice label contradicts distribution")
        return {
            "label": label,
            "confidence": answer["confidence"],
            "distribution": distribution,
        }
    levels = answer["levels"]
    if type(levels) is not list or len(levels) != len(question.levels):
        raise ValueError("invalid score levels")
    probabilities = []
    for item, level in zip(levels, question.levels, strict=True):
        keys(item, {"value", "probability"})
        if number(item["value"], -1000, 1000) != level:
            raise ValueError("mismatched score level")
        probabilities.append(number(item["probability"]))
    weighted = number(
        answer["weighted_score"], min(question.levels), max(question.levels)
    )
    if (
        abs(sum(probabilities) - 1) > TOLERANCE
        or abs(
            weighted
            - sum(p * v for p, v in zip(probabilities, question.levels, strict=True))
        )
        > TOLERANCE
    ):
        raise ValueError("inconsistent weighted score")
    return {
        "weighted_score": weighted,
        "confidence": answer["confidence"],
        "levels": levels,
    }


def usage_projection(usage) -> dict:
    """Provisional OpenRouter-style usage projection; not alpha-contract verified.

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
        ("prompt_tokens", "input_tokens"),
        ("completion_tokens", "output_tokens"),
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


def parse_fixture_response(body: bytes) -> tuple[Prediction, dict]:
    value = decode(body, MAX_RESPONSE_BYTES)
    keys(value, {"schema", "answers", "model", "provider", "usage"})
    if value["schema"] != LOCAL_SCHEMA:
        raise ValueError("unsupported local response schema")
    if value["model"] not in (None, MODEL) or value["provider"] not in (
        None,
        "TypeSafe",
    ):
        raise ValueError("unexpected reported model/provider")
    answers = value["answers"]
    if type(answers) is not list or len(answers) != len(QUESTIONS):
        raise ValueError("exact answer set required")
    if any(type(a) is not dict or type(a.get("id")) is not str for a in answers):
        raise ValueError("invalid answer identity")
    mapping = {a["id"]: a for a in answers}
    if len(mapping) != len(answers) or set(mapping) != {q.id for q in QUESTIONS}:
        raise ValueError("missing/extra/duplicate answer IDs")
    choice, binary = [parse_answer(mapping[q.id], q) for q in QUESTIONS]
    return Prediction(
        intent=choice["label"],
        code_probability=binary["true_probability"],
        origin="mocked_external_model",
    ), {
        "requested_model": MODEL,
        "reported_model": value["model"],
        "effective_model_revision": None,
        "reported_provider": value["provider"],
        "routing_status": "unknown"
        if value["provider"] is None
        else "mocked_declaration",
        "generation_id": None,
        "timestamp": None,
        "local_receipt": None,
        "completion": "mocked",
        **usage_projection(value["usage"]),
    }


@dataclass
class FakeTransport:
    """Single-use local bytes fixture; has no HTTP capability or credential field."""

    response: bytes | Exception
    calls: int = 0

    def send(
        self,
        body: bytes,
        *,
        origin=ORIGIN,
        path=PATH,
        method="POST",
        status=200,
        redirected=False,
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
        request = decode(body, MAX_REQUEST_BYTES)
        if type(request) is not dict or type(request.get("state")) is not str:
            raise ValueError("invalid fixture request")
        expected = fixture_request(
            request["state"],
            input_token_plan=request.get("input_token_plan"),
            output_token_plan=request.get("output_token_plan"),
        )
        if body != expected:
            raise ValueError("altered fixture target/questions/provider/bounds")
        if isinstance(self.response, Exception):
            raise self.response
        decode(self.response, MAX_RESPONSE_BYTES)
        return self.response


def readiness() -> dict:
    """Evidence packet only. Cannot enable a live call even with local credentials."""
    return {
        "version": "jev-one-request-readiness/v1",
        "ready": False,
        "mode": "offline_only",
        "credential_name": CREDENTIAL_NAME,
        "credential_read": False,
        "origin": ORIGIN,
        "path": PATH,
        "method": "POST",
        "requested_model": MODEL,
        "intended_provider": "TypeSafe",
        "provider_slug": None,
        "allow_fallbacks": False,
        "retries": 0,
        "max_requests": 1,
        "max_exposure_usd": 1,
        "max_input_token_plan": MAX_INPUT_TOKEN_PLAN,
        "max_output_token_plan": MAX_OUTPUT_TOKEN_PLAN,
        "max_request_bytes": MAX_REQUEST_BYTES,
        "max_response_bytes": MAX_RESPONSE_BYTES,
        "blockers": [
            "official_request_response_schema",
            "official_float_tolerance",
            "provider_slug_and_exact_route",
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
