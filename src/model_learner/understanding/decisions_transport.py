"""Offline HTTP-envelope seam for J2's frozen fictional DEVELOPMENT request.

These are authored fixtures, not captured HTTP or provider attestations. There is
no socket, HTTP client, credential, redirect, retry or fallback implementation.
The exact fake type is admitted by J2; arbitrary/live clients remain refused.
"""

from __future__ import annotations

from dataclasses import dataclass

from model_learner.understanding import decisions_offline as wire

VERSION = "decisions-offline-http-envelope/v1"


@dataclass(frozen=True)
class ResponseFixture:
    """Explicit mock response metadata; no assumed status, route or media type."""

    origin: str
    path: str
    status: int
    redirected: bool
    headers: tuple[tuple[str, str], ...]
    body: bytes


def _validate(response: ResponseFixture) -> None:
    if (
        type(response) is not ResponseFixture
        or (response.origin, response.path) != (wire.ORIGIN, wire.PATH)
        or type(response.status) is not int
        or response.status != 200
        or response.redirected is not False
        or type(response.body) is not bytes
        or len(response.body) > wire.MAX_RESPONSE_BYTES
    ):
        raise ValueError("offline response target/status/body refused")
    if type(response.headers) is not tuple or len(response.headers) > 16:
        raise ValueError("offline response headers refused")
    headers = {}
    for entry in response.headers:
        if (
            type(entry) is not tuple
            or len(entry) != 2
            or any(type(value) is not str for value in entry)
        ):
            raise ValueError("offline response header shape refused")
        name, value = entry
        name = name.lower()
        if (
            name not in {"content-type", "content-length", "content-encoding"}
            or name in headers
            or len(value) > 256
            or any(ord(char) < 32 or ord(char) > 126 for char in value)
        ):
            raise ValueError("offline response header refused")
        headers[name] = value.lower()
    if headers.get("content-type") not in {
        "application/json",
        "application/json; charset=utf-8",
    }:
        raise ValueError("offline response media type refused")
    if headers.get("content-encoding", "identity") != "identity":
        raise ValueError("offline response encoding refused")
    length = headers.get("content-length")
    if length is not None and (
        not length.isascii()
        or not length.isdecimal()
        or len(length) > 6
        or int(length) != len(response.body)
    ):
        raise ValueError("offline response length refused")


@dataclass
class MockHTTPTransport:
    """One local fixture exchange; uses existing wire validation, never HTTP.

    Local required route policy is not serialized into undocumented wire fields.
    Headers deliberately support a small local fixture dialect, not a normative
    provider contract. Raw headers/body/error prose never enter J2 receipts.
    """

    response: ResponseFixture | Exception
    allow_fallbacks: bool = False
    provider_only: tuple[str, ...] = (wire.PROVIDER_SLUG,)
    calls: int = 0

    def send(self, body: bytes) -> bytes:
        if self.calls:
            raise ValueError("one offline exchange only; retries forbidden")
        self.calls += 1
        if isinstance(self.response, Exception):
            raise self.response
        _validate(self.response)
        # Reuse J1's request/model/question, routing and usage controls. No new
        # provider request fields or alternative route implementation is invented.
        return wire.FakeTransport(self.response.body).send(
            body,
            origin=self.response.origin,
            path=self.response.path,
            status=self.response.status,
            redirected=self.response.redirected,
            allow_fallbacks=self.allow_fallbacks,
            provider_only=self.provider_only,
        )
