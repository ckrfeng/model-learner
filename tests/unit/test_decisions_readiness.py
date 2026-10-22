"""J2 synthetic/mock controls; no HTTP, credentials, Git writes or holdout runs."""

import hashlib
import json
from decimal import Decimal
from pathlib import Path

import pytest

from model_learner.understanding import decisions_offline as wire
from model_learner.understanding import decisions_readiness as j2
from model_learner.understanding.intent import canonical
from model_learner.understanding.intent_evaluation import mock_response

ROOT = Path(__file__).parents[1] / "fixtures/intent"


def test_frozen_projection_never_reads_references(monkeypatch):
    original = Path.read_bytes
    reads = []

    def read(path):
        reads.append(path.name)
        assert path.name in {"manifest.json", "inputs.json"}
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", read)
    body = j2.frozen_request(ROOT)
    assert reads == ["manifest.json", "inputs.json"]
    value = json.loads(body)
    assert set(value) == {"model", "questions", "state"}
    assert hashlib.sha256(value["state"].encode()).hexdigest() == j2.INPUT_SHA256
    assert value["model"] == wire.MODEL
    assert not any(s in body for s in (b"dev-01", b"holdout", b"reference_labels"))
    assert body == wire.fixture_request(value["state"])


@pytest.mark.parametrize("name", ["inputs.json", "manifest.json"])
def test_changed_frozen_files_refuse_before_marker(tmp_path, name):
    for source in ("inputs.json", "manifest.json"):
        (tmp_path / source).write_bytes((ROOT / source).read_bytes())
    with (tmp_path / name).open("ab") as stream:
        stream.write(b" ")
    transport = wire.FakeTransport(mock_response())
    with pytest.raises(ValueError, match="frozen"):
        j2.rehearse(tmp_path, tmp_path / "mock", transport)
    assert transport.calls == 0
    assert not (tmp_path / "mock").exists()


def test_readiness_cannot_be_enabled_by_authorization_or_account_limit(monkeypatch):
    def forbidden(*args, **kwargs):
        pytest.fail("network/credential access forbidden")

    import socket

    monkeypatch.setattr(socket, "socket", forbidden)
    monkeypatch.setattr(j2.os, "getenv", forbidden)
    packet = j2.readiness(ROOT)
    assert packet["authorization"].startswith("one_conditional_post_authorized")
    assert not packet["ready"]
    assert packet["contract"] == "PARTIAL"
    assert packet["routing"] == packet["spending"] == packet["live_smoke"] == "BLOCKED"
    assert packet["credential_read"] is False
    assert packet["paid_posts"] == 0
    assert packet["protocol"]["retries"] == 0
    assert (
        packet["request_sha256"] == hashlib.sha256(j2.frozen_request(ROOT)).hexdigest()
    )
    with pytest.raises(wire.ContractUnavailable, match="provider_only"):
        j2.refuse_live(ROOT)
    # Numeric budget checks cannot update captured route/enforcement evidence.
    assert not j2.budget_blockers(
        remaining_prepaid_usd=Decimal("15"), enforced_exposure_usd=Decimal("0.99")
    )
    assert j2.readiness(ROOT) == packet


@pytest.mark.parametrize(
    "value",
    [
        None,
        0,
        True,
        0.1,
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-1"),
        Decimal("0"),
    ],
)
def test_unknown_invalid_or_zero_budget_is_not_permission(value):
    assert j2.budget_blockers(remaining_prepaid_usd=value, enforced_exposure_usd=value)


@pytest.mark.parametrize(
    "exposure,balance", [("1", "15"), ("1.01", "15"), ("16", "20"), ("0.9", "0.8")]
)
def test_budget_requires_strict_cap_and_existing_funds(exposure, balance):
    assert "exposure_exceeds_budget" in j2.budget_blockers(
        remaining_prepaid_usd=Decimal(balance), enforced_exposure_usd=Decimal(exposure)
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("planned_input_tokens", 20_001),
        ("planned_input_tokens", True),
        ("planned_output_tokens", 513),
        ("planned_output_tokens", 0),
    ],
)
def test_cumulative_token_and_output_plans(field, value):
    assert j2.budget_blockers(**{field: value})


def test_mock_marker_is_durable_before_dispatch_and_never_live(tmp_path, monkeypatch):
    original = wire.FakeTransport.send
    synced = []
    real_sync = j2.os.fsync

    def sync(fd):
        synced.append(fd)
        real_sync(fd)

    monkeypatch.setattr(j2.os, "fsync", sync)

    def send(transport, body):
        marker = tmp_path / "mock-attempt-consumed.json"
        assert marker.is_file() and len(synced) == 2
        assert (
            json.loads(marker.read_bytes())["request_sha256"]
            == hashlib.sha256(body).hexdigest()
        )
        return original(transport, body)

    monkeypatch.setattr(wire.FakeTransport, "send", send)
    receipt = j2.rehearse(ROOT, tmp_path, wire.FakeTransport(mock_response()))
    assert receipt["completion"] == "mocked_parsed"
    assert receipt["mode"] == "mock_only" and receipt["paid_posts"] == 0
    assert receipt["actual_billed_cost_usd"] is None
    assert not receipt["routing_verified"]
    assert receipt["prediction"]
    second = wire.FakeTransport(mock_response())
    with pytest.raises(FileExistsError):
        j2.rehearse(ROOT, tmp_path, second)
    assert second.calls == 0


@pytest.mark.parametrize("existing", [b"", b"partial", b'{"mode":"mock_only"}'])
def test_ambiguous_existing_marker_refuses_without_reading(tmp_path, existing):
    (tmp_path / "mock-attempt-consumed.json").write_bytes(existing)
    transport = wire.FakeTransport(mock_response())
    with pytest.raises(FileExistsError):
        j2.rehearse(ROOT, tmp_path, transport)
    assert transport.calls == 0


@pytest.mark.parametrize(
    "error",
    [TimeoutError("private-error-sentinel"), RuntimeError("private-error-sentinel")],
)
def test_ambiguous_dispatch_is_consumed_and_error_text_omitted(tmp_path, error):
    transport = wire.FakeTransport(error)
    receipt = j2.rehearse(ROOT, tmp_path, transport)
    assert receipt["completion"] == "mocked_error_or_ambiguous"
    assert receipt["actual_billed_cost_usd"] is None
    assert b"private-error-sentinel" not in canonical(receipt)
    with pytest.raises(FileExistsError):
        j2.rehearse(ROOT, tmp_path, wire.FakeTransport(mock_response()))
    assert transport.calls == 1


@pytest.mark.parametrize(
    "model,provider,expected",
    [
        (wire.PUBLISHED_RETURNED_MODEL, "TypeSafe", "mocked_parsed"),
        ("typesafe/jev-1.14-other", "TypeSafe", "mocked_error_or_ambiguous"),
        (wire.MODEL, "Other", "mocked_error_or_ambiguous"),
    ],
)
def test_versioned_identity_and_provider_mismatch(tmp_path, model, provider, expected):
    response = json.loads(mock_response())
    response.update(model=model, provider=provider)
    receipt = j2.rehearse(ROOT, tmp_path, wire.FakeTransport(canonical(response)))
    assert receipt["completion"] == expected
    assert not receipt["routing_verified"] and receipt["actual_billed_cost_usd"] is None


@pytest.mark.parametrize(
    "usage,expected",
    [
        (None, "mocked_parsed"),
        ({"cost": 0}, "mocked_parsed"),
        ({"cost": "unknown"}, "mocked_parsed"),
        ({"cost": 1}, "mocked_error_or_ambiguous"),
        ({"input_tokens": 4097}, "mocked_error_or_ambiguous"),
        ({"output_tokens": 257}, "mocked_error_or_ambiguous"),
    ],
)
def test_accounting_uncertainty_and_plan_breach(tmp_path, usage, expected):
    response = json.loads(mock_response())
    response["usage"] = usage
    receipt = j2.rehearse(ROOT, tmp_path, wire.FakeTransport(canonical(response)))
    assert receipt["completion"] == expected
    assert receipt["actual_billed_cost_usd"] is None
    if usage == {"cost": 0}:
        assert receipt["reported_usage"]["reported_cost_usd"] == 0
    if usage is None or usage == {"cost": "unknown"}:
        assert receipt["reported_usage"]["reported_cost_usd"] is None


def test_nonfake_transport_rejected_before_marker(tmp_path):
    class Transport:
        def send(self, body):
            pytest.fail("must never dispatch")

    with pytest.raises(ValueError, match="offline fake"):
        j2.rehearse(ROOT, tmp_path, Transport())
    assert not list(tmp_path.iterdir())


def test_marker_sync_failure_refuses_dispatch_and_retains_consumption(
    tmp_path, monkeypatch
):
    def fail(fd):
        raise OSError("synthetic sync failure")

    monkeypatch.setattr(j2.os, "fsync", fail)
    transport = wire.FakeTransport(mock_response())
    with pytest.raises(OSError):
        j2.rehearse(ROOT, tmp_path, transport)
    assert transport.calls == 0
    assert (tmp_path / "mock-attempt-consumed.json").exists()
    with pytest.raises(FileExistsError):
        j2.rehearse(ROOT, tmp_path, transport)


def test_symlink_marker_refused_without_following(tmp_path):
    target = tmp_path / "unrelated"
    target.write_bytes(b"preserve")
    (tmp_path / "mock-attempt-consumed.json").symlink_to(target)
    transport = wire.FakeTransport(mock_response())
    with pytest.raises(FileExistsError):
        j2.rehearse(ROOT, tmp_path, transport)
    assert target.read_bytes() == b"preserve" and transport.calls == 0


def test_classification_preserves_existing_verified_outcomes_learning_and_advice(
    tmp_path, monkeypatch
):
    import sys

    scripts = Path(__file__).parents[2] / "scripts"
    monkeypatch.syspath_prepend(str(scripts))
    from advisory_example import example

    from model_learner.learn.advisory import advise
    from model_learner.learn.estimator import BetaBernoulli

    payload = example(with_evidence=True)
    original = payload.model_dump_json()

    def estimate():
        return BetaBernoulli.fit(
            payload.observations,
            dataset=payload.observations[0].dataset,
            cutoff=payload.request.cutoff,
            acceptance_spec=payload.request.task.acceptance_spec,
            resource_budget=payload.request.task.resource_budget,
        ).predict(payload.request.candidates[0], payload.request.task.task_group)

    before_estimate = estimate()
    before_advice = advise(payload.request, observations=payload.observations)
    receipt = j2.rehearse(ROOT, tmp_path, wire.FakeTransport(mock_response()))
    assert receipt["prediction"] and receipt["completion"] == "mocked_parsed"
    assert payload.model_dump_json() == original
    assert estimate() == before_estimate
    assert advise(payload.request, observations=payload.observations) == before_advice
    assert "model_learner.understanding.decisions_readiness" in sys.modules


@pytest.mark.parametrize("mutation", ["model", "criteria", "question"])
def test_frozen_wire_contract_substitution_refuses_before_dispatch(
    tmp_path, monkeypatch, mutation
):
    if mutation == "model":
        monkeypatch.setattr(wire, "MODEL", wire.PUBLISHED_RETURNED_MODEL)
    elif mutation == "criteria":
        monkeypatch.setitem(wire.CHOICE_CRITERIA, "bug_fix", "Changed criterion")
    else:
        original = wire.fixture_request
        questions = (
            wire.QUESTIONS[0].model_copy(update={"prompt": "Changed instructions"}),
            wire.QUESTIONS[1],
        )

        def altered(description, **kwargs):
            return original(description, questions=questions, **kwargs)

        monkeypatch.setattr(wire, "fixture_request", altered)
    transport = wire.FakeTransport(mock_response())
    with pytest.raises(ValueError):
        j2.rehearse(ROOT, tmp_path / "mock", transport)
    assert transport.calls == 0 and not (tmp_path / "mock").exists()
