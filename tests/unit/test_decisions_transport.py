"""Authored synthetic DEVELOPMENT HTTP fixtures, not provider captures or holdout.

Reuses J2 dev-01 request and J1's fixed label-independent mock response. No new
classification examples, credentials, network, paid requests or utility evidence.
"""

import hashlib
import json
from dataclasses import replace
from pathlib import Path

import pytest
from pydantic import ValidationError

from model_learner.understanding import decisions_offline as wire
from model_learner.understanding import decisions_readiness as j2
from model_learner.understanding.decisions_transport import (
    VERSION,
    MockHTTPTransport,
    ResponseFixture,
)
from model_learner.understanding.intent import canonical
from model_learner.understanding.intent_evaluation import mock_response

ROOT = Path(__file__).parents[1] / "fixtures/intent"


def response(**changes):
    return replace(
        ResponseFixture(
            origin=wire.ORIGIN,
            path=wire.PATH,
            status=200,
            redirected=False,
            headers=(("Content-Type", "application/json"),),
            body=mock_response(),
        ),
        **changes,
    )


def test_valid_frozen_exchange_preserves_wire_and_receipt_boundaries(tmp_path):
    fixture = response()
    transport = MockHTTPTransport(fixture)
    receipt = j2.rehearse(ROOT, tmp_path, transport)
    assert transport.calls == 1
    assert receipt["completion"] == "mocked_parsed"
    assert receipt["prediction"] == wire.parse_response(fixture.body)[0]
    assert receipt["request_sha256"] == j2.REQUEST_SHA256
    assert receipt["response_sha256"] == hashlib.sha256(fixture.body).hexdigest()
    assert receipt["transport_contract"] == VERSION
    assert receipt["evidence_class"] == "synthetic_development_http_fixture"
    assert receipt["mode"] == "mock_only" and receipt["paid_posts"] == 0
    assert not receipt["routing_verified"]
    assert receipt["actual_billed_cost_usd"] is None
    assert not j2.readiness(ROOT)["ready"]
    assert fixture == response()
    with pytest.raises(FileExistsError):
        j2.rehearse(ROOT, tmp_path, MockHTTPTransport(fixture))
    with pytest.raises(ValueError, match="retries forbidden"):
        transport.send(j2.frozen_request(ROOT))


@pytest.mark.parametrize(
    "headers",
    [
        (("content-type", "application/json; charset=utf-8"),),
        (("CONTENT-TYPE", "APPLICATION/JSON"), ("Content-Encoding", "identity")),
        (
            ("Content-Type", "application/json"),
            ("Content-Length", str(len(mock_response()))),
        ),
    ],
)
def test_supported_explicit_envelope_dialect(tmp_path, headers):
    receipt = j2.rehearse(ROOT, tmp_path, MockHTTPTransport(response(headers=headers)))
    assert receipt["completion"] == "mocked_parsed"


@pytest.mark.parametrize(
    "changes",
    [
        {"origin": "https://example.invalid"},
        {"origin": "http://openrouter.ai"},
        {"path": "/api/v1/chat/completions"},
        {"path": wire.PATH + "?route=other"},
        {"status": 301},
        {"status": 429},
        {"status": 500},
        {"status": 204},
        {"status": "200"},
        {"status": True},
        {"redirected": True},
        {"redirected": None},
        {"redirected": 0},
        {"body": None},
        {"body": "{}"},
        {"body": b"x" * (wire.MAX_RESPONSE_BYTES + 1)},
        {"headers": ()},
        {"headers": (("Content-Type", "text/html"),)},
        {"headers": (("Content-Type", "application/json; charset=latin1"),)},
        {
            "headers": (
                ("Content-Type", "application/json"),
                ("content-type", "text/html"),
            )
        },
        {"headers": (("Content-Type", "application/json\r\nInjected: value"),)},
        {"headers": (("Content-Type", "application/json"), ("Location", wire.ORIGIN))},
        {
            "headers": (
                ("Content-Type", "application/json"),
                ("Content-Encoding", "gzip"),
            )
        },
        {"headers": (("Content-Type", "application/json"), ("Content-Length", "-1"))},
        {"headers": (("Content-Type", "application/json"), ("Content-Length", "1"))},
        {"headers": (("Content-Type", "application/json"), ("Content-Length", ""))},
        {
            "headers": (
                ("Content-Type", "application/json"),
                ("Content-Length", "1234567"),
            )
        },
        {"headers": (("Content-Type", "application/json"), ("Content-Length", "١"))},
        {"headers": (("Content-Type", "application/json"), ("Content-Length", 123))},
        {
            "headers": (
                ("Content-Type", "application/json"),
                ("X-Fixture", "do-not-echo"),
            )
        },
        {
            "headers": (
                ("Content-Type", "application/json"),
                ("Content-Encoding", "x" * 257),
            )
        },
        {"headers": (("Content-Type", "application/json"),) * 17},
        {"headers": [("Content-Type", "application/json")]},
        {"headers": ("Content-Type",)},
    ],
)
def test_invalid_envelope_consumes_mock_once_and_omits_raw_data(tmp_path, changes):
    transport = MockHTTPTransport(response(**changes))
    receipt = j2.rehearse(ROOT, tmp_path, transport)
    assert transport.calls == 1
    assert receipt["completion"] == "mocked_error_or_ambiguous"
    assert receipt["prediction"] is receipt["response_sha256"] is None
    assert receipt["actual_billed_cost_usd"] is None and not receipt["routing_verified"]
    assert "headers" not in receipt and "body" not in receipt
    assert b"do-not-echo" not in canonical(receipt)
    assert (tmp_path / "mock-attempt-consumed.json").is_file()
    with pytest.raises(FileExistsError):
        j2.rehearse(ROOT, tmp_path, MockHTTPTransport(response()))


@pytest.mark.parametrize(
    "field", ["origin", "path", "status", "redirected", "headers", "body"]
)
def test_missing_envelope_fields_have_no_assumed_defaults(field):
    values = dict(
        origin=wire.ORIGIN,
        path=wire.PATH,
        status=200,
        redirected=False,
        headers=(("Content-Type", "application/json"),),
        body=mock_response(),
    )
    values.pop(field)
    with pytest.raises(TypeError):
        ResponseFixture(**values)


@pytest.mark.parametrize(
    "policy",
    [
        {"allow_fallbacks": True},
        {"allow_fallbacks": None},
        {"provider_only": ("other",)},
        {"provider_only": ()},
        {"provider_only": (wire.PROVIDER_SLUG, "other")},
    ],
)
def test_seam_reuses_existing_no_fallback_provider_controls(tmp_path, policy):
    receipt = j2.rehearse(ROOT, tmp_path, MockHTTPTransport(response(), **policy))
    assert receipt["prediction"] is None
    assert receipt["completion"] == "mocked_error_or_ambiguous"
    assert receipt["paid_posts"] == 0


@pytest.mark.parametrize(
    "body", [b"", b"not-json", b"{}", b'{"model":null,"model":null}']
)
def test_http_success_is_not_a_valid_decisions_result(tmp_path, body):
    receipt = j2.rehearse(ROOT, tmp_path, MockHTTPTransport(response(body=body)))
    assert receipt["completion"] == "mocked_error_or_ambiguous"
    assert receipt["prediction"] is None


@pytest.mark.parametrize(
    "field,value", [("model", "unapproved-model"), ("provider", "Other")]
)
def test_http_success_cannot_substitute_reported_model_or_provider(
    tmp_path, field, value
):
    data = json.loads(mock_response())
    data[field] = value
    receipt = j2.rehearse(
        ROOT, tmp_path, MockHTTPTransport(response(body=canonical(data)))
    )
    assert receipt["prediction"] is None and not receipt["routing_verified"]


@pytest.mark.parametrize("error", [TimeoutError("do-not-echo"), OSError("do-not-echo")])
def test_transport_error_is_not_model_output_or_trusted_evidence(tmp_path, error):
    transport = MockHTTPTransport(error)
    receipt = j2.rehearse(ROOT, tmp_path, transport)
    assert transport.calls == 1 and receipt["prediction"] is None
    assert receipt["completion"] == "mocked_error_or_ambiguous"
    assert receipt["response_sha256"] is None
    assert receipt["actual_billed_cost_usd"] is None
    assert b"do-not-echo" not in canonical(receipt)


def test_exact_fake_only_no_secret_network_or_reference_reads(tmp_path, monkeypatch):
    import socket

    def forbidden(*args, **kwargs):
        pytest.fail("live/secret/reference access forbidden")

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(j2.os, "getenv", forbidden)
    original = Path.read_bytes
    reads = []

    def read(path):
        assert path.name in {"manifest.json", "inputs.json"}
        reads.append(path.name)
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    assert j2.rehearse(ROOT, tmp_path / "good", MockHTTPTransport(response()))[
        "prediction"
    ]
    assert reads == ["manifest.json", "inputs.json"]
    with pytest.raises(wire.ContractUnavailable):
        j2.refuse_live(ROOT)

    class Substitute(MockHTTPTransport):
        def send(self, body):
            forbidden()

    with pytest.raises(ValueError, match="exact offline fake"):
        j2.rehearse(ROOT, tmp_path / "refused", Substitute(response()))
    assert not (tmp_path / "refused").exists()


@pytest.mark.parametrize("success", [True, False])
def test_success_and_error_leave_advisory_and_outcome_inputs_unchanged(
    tmp_path, monkeypatch, success
):
    from model_learner.domain.models import Observation, Verification
    from model_learner.learn.advisory import AdvisoryInput, advise

    monkeypatch.syspath_prepend(str(Path(__file__).parents[2] / "scripts"))
    from advisory_example import example

    payload = example(with_evidence=True)
    before = payload.model_dump_json()
    advice = advise(payload.request, observations=payload.observations)
    fixture = response() if success else TimeoutError("synthetic failure")
    receipt = j2.rehearse(ROOT, tmp_path, MockHTTPTransport(fixture))
    assert (receipt["prediction"] is not None) is success
    assert payload.model_dump_json() == before
    assert advise(payload.request, observations=payload.observations) == advice
    assert advice["advisory"]["status"] == "abstain"
    for target in (AdvisoryInput, Observation, Verification):
        with pytest.raises(ValidationError):
            target.model_validate(receipt)
