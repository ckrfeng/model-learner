"""Bounded read-only subset of the documented App Server stdio protocol.

Native responses and diagnostics stay in memory. This client never answers
server-initiated requests, invokes inference, subscribes, or enumerates history.
"""

from __future__ import annotations

import json
import os
import selectors
import subprocess
import time
from collections import Counter
from pathlib import Path
from typing import Any
from uuid import UUID

MAX_BYTES = 64 * 1024
MAX_TURNS = 10
READ_METHODS = frozenset(
    {"initialize", "initialized", "thread/read", "thread/turns/list"}
)


class ConversationError(ValueError):
    """Content-free protocol, projection or privacy diagnostic."""


class AppServerClient:
    """One selected conversation per short-lived server, with strict RPC bounds."""

    def __init__(
        self,
        conversation_id: str,
        *,
        executable: str | Path = "codex",
        timeout: float = 20,
    ) -> None:
        try:
            UUID(conversation_id)
        except (ValueError, TypeError, AttributeError):
            raise ConversationError("invalid selected conversation ID") from None
        if not 0 < timeout <= 60:
            raise ConversationError("invalid response timeout")
        self.conversation_id = conversation_id
        self.executable = str(executable)
        self.timeout = timeout
        self.response_bytes = 0
        self.sent_methods: Counter[str] = Counter()
        self.notifications_ignored = 0
        self.exit_code: int | None = None
        self._id = 0
        self._buffer = b""
        self._turn_calls = 0
        self._process: subprocess.Popen | None = None
        self._selector = selectors.DefaultSelector()

    def __enter__(self) -> AppServerClient:
        try:
            self._process = subprocess.Popen(
                [self.executable, "app-server", "--listen", "stdio://"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
            )
            self._selector.register(self._process.stdout, selectors.EVENT_READ)
            self.request(
                "initialize",
                {
                    "clientInfo": {
                        "name": "model_learner_history",
                        "title": "Model Learner selected history",
                        "version": "0.1.0",
                    },
                    "capabilities": {"experimentalApi": True},
                },
            )
            self._send("initialized", {}, notification=True)
            return self
        except Exception:
            self.close()
            raise ConversationError("App Server initialization failed") from None

    def _send(
        self, method: str, params: dict[str, Any], *, notification: bool = False
    ) -> int:
        if method not in READ_METHODS or self._process is None:
            raise ConversationError("RPC method denied")
        if notification != (method == "initialized"):
            raise ConversationError("invalid handshake notification")
        if method == "thread/read":
            if (
                params
                != {
                    "threadId": self.conversation_id,
                    "includeTurns": False,
                }
                or self.sent_methods[method]
            ):
                raise ConversationError("metadata read scope denied")
        elif method == "thread/turns/list":
            if (
                set(params)
                - {"threadId", "limit", "sortDirection", "itemsView", "cursor"}
                or params.get("threadId") != self.conversation_id
                or type(params.get("limit")) is not int
                or params["limit"] != 1
                or params.get("sortDirection") != "desc"
                or params.get("itemsView") not in {"notLoaded", "full"}
                or ("cursor" in params and not isinstance(params["cursor"], str))
                or self._turn_calls >= MAX_TURNS
            ):
                raise ConversationError("turn read scope denied")
            self._turn_calls += 1
        elif self.sent_methods[method]:
            raise ConversationError("duplicate handshake denied")
        self._id += 1
        envelope = {"method": method, "params": params}
        if not notification:
            envelope["id"] = self._id
        try:
            self._process.stdin.write(json.dumps(envelope).encode() + b"\n")
            self._process.stdin.flush()
        except (OSError, ValueError):
            raise ConversationError("App Server write failed") from None
        self.sent_methods[method] += 1
        return self._id

    def request(self, method: str, params: dict[str, Any]) -> dict[str, Any]:
        identity = self._send(method, params)
        deadline = time.monotonic() + self.timeout
        while time.monotonic() < deadline:
            if b"\n" not in self._buffer:
                if not self._selector.select(max(0, deadline - time.monotonic())):
                    break
                chunk = os.read(self._process.stdout.fileno(), 4096)
                if not chunk:
                    raise ConversationError("App Server ended before response")
                self.response_bytes += len(chunk)
                if self.response_bytes > MAX_BYTES:
                    self._buffer = b""
                    raise ConversationError("conversation response byte limit exceeded")
                self._buffer += chunk
                continue
            line, self._buffer = self._buffer.split(b"\n", 1)
            try:
                response = json.loads(line)
            except (ValueError, UnicodeError):
                raise ConversationError("invalid App Server JSON") from None
            if not isinstance(response, dict):
                raise ConversationError("invalid App Server envelope")
            if "method" in response:
                if "id" in response:
                    raise ConversationError("server-initiated request denied")
                self.notifications_ignored += 1
                continue
            if response.get("id") != identity:
                raise ConversationError("unexpected App Server response ID")
            if "error" in response:
                raise ConversationError("App Server read unsupported or rejected")
            if not isinstance(response.get("result"), dict):
                raise ConversationError("invalid App Server result")
            return response["result"]
        raise ConversationError("App Server response timeout")

    def close(self) -> None:
        self._buffer = b""
        self._selector.close()
        if self._process is None:
            return
        self._process.stdin.close()
        try:
            self.exit_code = self._process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self._process.terminate()
            try:
                self.exit_code = self._process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self.exit_code = self._process.wait(timeout=3)
        self._process.stdout.close()

    def __exit__(self, *_: object) -> None:
        self.close()
