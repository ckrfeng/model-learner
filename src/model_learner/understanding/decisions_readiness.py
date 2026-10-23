"""J2 frozen development packet and mock-only one-shot rehearsal.

Captured evidence cannot authorize live transport. No network or credential API
exists here; arbitrary caller assertions cannot upgrade the evidence to ready.
"""

from __future__ import annotations

import hashlib
import json
import os
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from model_learner.understanding import decisions_offline as wire
from model_learner.understanding.decisions_transport import (
    VERSION as HTTP_FIXTURE_VERSION,
)
from model_learner.understanding.decisions_transport import MockHTTPTransport
from model_learner.understanding.intent import canonical, digest
from model_learner.understanding.intent_evaluation import MANIFEST_SHA256

VERSION = "j2-decisions-readiness/v1"
CASE_ID = "dev-01"
INPUT_SHA256 = "3c74742bb6bd3d697ab738b8037b29e42ea5ab99fe8d8fa0fae8df350737b493"
REQUEST_SHA256 = "f7a2a32a6aabb5fb7a8d85f1150309a9a13a93a19aadf05e5fc09b50c284035b"
INPUT_TOKEN_PLAN = 4096
OUTPUT_TOKEN_PLAN = 256
# This protocol records requirements, not unsupported provider-bound fields.
PROTOCOL = {
    "version": VERSION,
    "wire_version": wire.WIRE_VERSION,
    "origin": wire.ORIGIN,
    "path": wire.PATH,
    "method": "POST",
    "model": wire.MODEL,
    "admitted_returned_models": [wire.MODEL, wire.PUBLISHED_RETURNED_MODEL],
    "required_provider_only": [wire.PROVIDER_SLUG],
    "required_allow_fallbacks": False,
    "retries": 0,
    "max_paid_posts": 1,
    "input_token_plan": INPUT_TOKEN_PLAN,
    "output_token_plan": OUTPUT_TOKEN_PLAN,
    "exposure_strictly_below_usd": "1",
    "overall_prepaid_ceiling_usd": "15",
    "funding": "existing_prepaid_only",
    "case_id": CASE_ID,
    "input_sha256": INPUT_SHA256,
    "request_sha256": REQUEST_SHA256,
    "manifest_sha256": MANIFEST_SHA256,
}


def frozen_request(root: Path) -> bytes:
    """Read frozen fictional inputs only; never open draft reference labels.

    No caller text, case selector or question override is accepted. No predictions
    are made for other development inputs or any holdout input.
    """
    manifest = (root / "manifest.json").read_bytes()
    if hashlib.sha256(manifest).hexdigest() != MANIFEST_SHA256:
        raise ValueError("frozen manifest changed")
    inputs = (root / "inputs.json").read_bytes()
    if (
        hashlib.sha256(inputs).hexdigest()
        != json.loads(manifest)["files"]["inputs.json"]
    ):
        raise ValueError("frozen inputs changed")
    cases = [c for c in json.loads(inputs) if c["id"] == CASE_ID]
    if len(cases) != 1:
        raise ValueError("frozen development identity missing")
    case = cases[0]
    if (
        case["split"] != "development"
        or case["input_sha256"] != INPUT_SHA256
        or hashlib.sha256(case["description"].encode()).hexdigest() != INPUT_SHA256
    ):
        raise ValueError("frozen development input changed")
    body = wire.fixture_request(
        case["description"],
        input_token_plan=INPUT_TOKEN_PLAN,
        output_token_plan=OUTPUT_TOKEN_PLAN,
    )
    if hashlib.sha256(body).hexdigest() != REQUEST_SHA256:
        raise ValueError("frozen wire request changed")
    return body


def budget_blockers(
    *,
    remaining_prepaid_usd: Decimal | None = None,
    enforced_exposure_usd: Decimal | None = None,
    planned_input_tokens: int = INPUT_TOKEN_PLAN,
    planned_output_tokens: int = OUTPUT_TOKEN_PLAN,
) -> list[str]:
    """Check numeric evidence, never prove enforcement or authorize transmission.

    These values must eventually come from documented current provider evidence.
    The user-confirmed account limit alone proves neither input to this function.
    """
    blockers = []
    for name, value in (
        ("remaining_prepaid_balance", remaining_prepaid_usd),
        ("enforceable_per_request_exposure", enforced_exposure_usd),
    ):
        if type(value) is not Decimal or not value.is_finite() or value <= 0:
            blockers.append(name)
    if "enforceable_per_request_exposure" not in blockers and (
        enforced_exposure_usd >= Decimal("1")
        or enforced_exposure_usd > Decimal("15")
        or (
            "remaining_prepaid_balance" not in blockers
            and enforced_exposure_usd > remaining_prepaid_usd
        )
    ):
        blockers.append("exposure_exceeds_budget")
    for name, value, maximum in (
        ("cumulative_input_plan", planned_input_tokens, 20_000),
        ("conservative_output_plan", planned_output_tokens, 512),
    ):
        if type(value) is not int or not 0 < value <= maximum:
            blockers.append(name)
    return blockers


def readiness(root: Path) -> dict:
    body = frozen_request(root)
    return {
        "version": VERSION,
        "ready": False,
        "contract": "PARTIAL",
        "routing": "BLOCKED",
        "spending": "BLOCKED",
        "live_smoke": "BLOCKED",
        "offline_contract": "PASS",
        "endpoint_basis": "captured_official_examples; not_network_verified",
        "protocol": json.loads(canonical(PROTOCOL)),
        "protocol_sha256": digest(PROTOCOL),
        "request_sha256": hashlib.sha256(body).hexdigest(),
        "request_bytes": len(body),
        "authorization": "one_conditional_post_authorized_by_J2; gates_unsatisfied",
        "account_spending_limit": "user_confirmed; amount_and_remaining_not_assumed",
        "credential_read": False,
        "network_calls": 0,
        "paid_posts": 0,
        "live_attempt_marker_consumed": False,
        "blockers": [
            "decisions_provider_only_enforcement_undocumented",
            "decisions_no_fallback_enforcement_undocumented",
            "provider_output_limit_enforcement_undocumented",
            "current_pricing_billing_and_settlement_unverified",
            "credential_safe_local_transport_not_validated",
            "live_durable_one_shot_not_armed",
            *budget_blockers(),
        ],
        "external_model_evidence": "none; no_Jev_accuracy_or_calibration",
    }


def refuse_live(root: Path) -> None:
    """There is deliberately no transport argument or credential-loading path."""
    packet = readiness(root)
    raise wire.ContractUnavailable("J2 blocked: " + ", ".join(packet["blockers"]))


def _consume_mock_marker(directory: Path, request_sha256: str) -> None:
    """Durable exclusive creation before mock dispatch; any existing file refuses.

    Directory is caller-owned disposable/ignored storage. A crash, partial write,
    timeout or ambiguous response never releases this marker. This is a mock
    rehearsal only; it cannot consume or authorize the live paid-attempt marker.
    """
    directory.mkdir(parents=True, exist_ok=True)
    directory_fd = os.open(directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        fd = os.open(
            "mock-attempt-consumed.json",
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
            0o600,
            dir_fd=directory_fd,
        )
        with os.fdopen(fd, "wb") as stream:
            stream.write(
                canonical({"mode": "mock_only", "request_sha256": request_sha256})
            )
            stream.flush()
            os.fsync(stream.fileno())
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)


def rehearse(
    root: Path, directory: Path, transport: wire.FakeTransport | MockHTTPTransport
) -> dict:
    """Single frozen mock request; no credentials, caller text or live labeling.

    Exception messages and raw responses are never placed in receipts. The marker
    persists on all failures, including parsing, accounting or model mismatches.
    """
    if type(transport) not in (wire.FakeTransport, MockHTTPTransport):
        raise ValueError("exact offline fake transport required")
    body = frozen_request(root)
    request_hash = hashlib.sha256(body).hexdigest()
    _consume_mock_marker(directory, request_hash)
    receipt = {
        "version": VERSION,
        "mode": "mock_only",
        "completion": "mocked_error_or_ambiguous",
        "request_sha256": request_hash,
        "protocol_sha256": digest(PROTOCOL),
        "started_at": datetime.now(UTC).isoformat(),
        "paid_posts": 0,
        "actual_billed_cost_usd": None,
        "routing_verified": False,
        "prediction": None,
        "reported_usage": wire.usage_projection(None),
        "generation_id": None,
        "reported_model": None,
        "reported_provider": None,
        "response_sha256": None,
    }
    try:
        response = transport.send(body)
        receipt["response_sha256"] = hashlib.sha256(response).hexdigest()
        parsed, metadata = wire.parse_response(response)
        usage = wire.usage_projection(json.loads(response).get("usage"))
        if (
            (
                usage["input_tokens"] is not None
                and usage["input_tokens"] > INPUT_TOKEN_PLAN
            )
            or (
                usage["output_tokens"] is not None
                and usage["output_tokens"] > OUTPUT_TOKEN_PLAN
            )
            or (
                usage["reported_cost_usd"] is not None
                and usage["reported_cost_usd"] >= 1
            )
        ):
            raise ValueError("reported usage exceeds J2 plan")
        receipt.update(
            completion="mocked_parsed",
            prediction=parsed,
            reported_usage=usage,
            generation_id=metadata["generation_id"],
            reported_model=metadata["reported_model"],
            reported_provider=metadata["reported_provider"],
        )
    except Exception:
        # No retry, raw error text or reclassification as live evidence.
        pass
    receipt["finished_at"] = datetime.now(UTC).isoformat()
    if type(transport) is MockHTTPTransport:
        receipt["transport_contract"] = HTTP_FIXTURE_VERSION
        receipt["evidence_class"] = "synthetic_development_http_fixture"
    return receipt
