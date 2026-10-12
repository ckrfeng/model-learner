"""Selected Codex-backed conversation snapshots, separate from execution events.

Default reads omit turn items server-side. Explicit text reads receive full items
and discard all non-message bodies locally. Only explicit retention stores text.
"""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import NAMESPACE_URL, UUID, uuid5

from model_learner.adapters.app_server import MAX_BYTES, MAX_TURNS, ConversationError
from model_learner.domain import Event, Provenance, Session
from model_learner.domain.models import utc_now
from model_learner.storage.database import Repository

FORMAT = "codex-conversation-snapshot/v1"
SOURCE = "codex.app-server.history"
PRODUCTS = {
    "codex_desktop": "Codex Desktop",
    "chatgpt_work_local": "codex_work_desktop",
}
_OTHER_ITEMS = {
    "hookPrompt",
    "functionCallOutput",
    "plan",
    "reasoning",
    "commandExecution",
    "fileChange",
    "mcpToolCall",
    "dynamicToolCall",
    "collabAgentToolCall",
    "subAgentActivity",
    "webSearch",
    "imageView",
    "sleep",
    "imageGeneration",
    "enteredReviewMode",
    "exitedReviewMode",
    "contextCompaction",
}
_NON_TEXT = {"image", "localImage", "audio", "localAudio", "skill", "mention"}


def _string(value: Any) -> str:
    if not isinstance(value, str) or not value:
        raise ConversationError("missing or invalid source identity")
    return value


def _timestamp(value: Any) -> int | None:
    if value is not None:
        if type(value) is not int or value < 0:
            raise ConversationError("invalid native timestamp or duration")
        try:
            datetime.fromtimestamp(value, UTC)
        except (ValueError, OverflowError, OSError):
            raise ConversationError("unsupported native timestamp") from None
    return value


def _truncated(record: dict) -> bool | None:
    values = [record[k] for k in ("truncated", "isTruncated") if k in record]
    if any(type(value) is not bool for value in values):
        raise ConversationError("invalid source truncation marker")
    return any(values) if values else None


@dataclass(frozen=True)
class ConversationRead:
    session: Session
    metadata: dict[str, Any] = field(repr=False)
    retrieved_at: datetime
    text: dict[str, list[str]] = field(repr=False)

    def coverage(self) -> dict[str, Any]:
        """No native IDs, paths, strings, digests or cursors in this report."""
        turns = self.metadata["turns"]
        messages = [m for turn in turns for m in (turn["messages"] or [])]
        return {
            "product_source": self.session.metadata["product_source"],
            "backend": "codex",
            "turns": len(turns),
            "messages": len(messages)
            if self.metadata["items_view"] == "full"
            else None,
            "roles_by_turn": [
                [m["role"] for m in (t["messages"] or [])] for t in turns
            ],
            "history_exhausted": self.metadata["history_exhausted"],
            "bounded_history": self.metadata["bounded_history"],
            "items_view": self.metadata["items_view"],
            "text_bytes_in_memory": sum(
                len(s.encode()) for parts in self.text.values() for s in parts
            ),
            "message_timestamps": "not_emitted",
            "original_fidelity": "not_independently_verified",
        }


def read_conversation(
    client: Any,
    *,
    product_source: str,
    machine_id: str,
    read_text: bool = False,
) -> ConversationRead:
    """Project one exact selected ID; pagination order, never time/UUID sorting.

    The caller owns the short-lived client context. ``read_text`` authorizes full
    item retrieval, not text persistence. No model or usage settings are inferred.
    """
    if product_source not in PRODUCTS or not machine_id:
        raise ConversationError(
            "unsupported product source or missing machine identity"
        )
    identity = _string(client.conversation_id)
    try:
        UUID(identity)
    except ValueError:
        raise ConversationError("invalid selected conversation ID") from None
    retrieved_at = utc_now()
    result = client.request(
        "thread/read", {"threadId": identity, "includeTurns": False}
    )
    thread = result.get("thread")
    if not isinstance(thread, dict) or thread.get("id") != identity:
        raise ConversationError("selected conversation identity mismatch")
    if (
        thread.get("originator") != PRODUCTS[product_source]
        or thread.get("historyMode") != "paginated"
        or thread.get("source") != "vscode"
        or thread.get("threadSource") != "user"
        or thread.get("turns") != []
        or thread.get("ephemeral") is not False
    ):
        raise ConversationError("unsupported conversation source format")
    native_tree = _string(thread.get("sessionId"))
    version = _string(thread.get("cliVersion"))
    created = _timestamp(thread.get("createdAt"))
    updated = _timestamp(thread.get("updatedAt"))
    session_id = uuid5(
        NAMESPACE_URL,
        json.dumps([SOURCE, "codex", product_source, machine_id, identity]),
    )
    session = Session(
        session_id=session_id,
        source=SOURCE,
        native_session_id=identity,
        started_at=datetime.fromtimestamp(created, UTC)
        if created is not None
        else None,
        metadata={
            "product_source": product_source,
            "backend": "codex",
            "machine_id": machine_id,
        },
    )
    metadata = {
        "format": FORMAT,
        "backend": "codex",
        "product_source": product_source,
        "native_conversation_id": identity,
        "native_session_tree_id": native_tree,
        "originator": PRODUCTS[product_source],
        "native_source": "vscode",
        "thread_source": "user",
        "thread_created_at_seconds": created,
        "thread_updated_at_seconds": updated,
        "native_creator_cli_version": version,
        "historical_configuration": None,
        "usage": None,
        "cost_usd": None,
        "missingness": {
            "historical_configuration": "not_exposed",
            "usage": "not_exposed",
            "cost_usd": "not_exposed",
            "message_timestamps": "not_emitted",
            "original_fidelity": "not_verified",
        },
        "items_view": "full" if read_text else "notLoaded",
        "order_basis": "descending_native_turn_pages_reversed; native_item_array",
        "pages": [],
        "turns": [],
    }
    # Preview, names, paths, opaque extra data and current model settings die here.
    del result, thread
    text: dict[str, list[str]] = {}
    seen_turns: set[str] = set()
    seen_messages: set[str] = set()
    cursor = None
    seen_cursors: set[str] = set()
    for page_index in range(MAX_TURNS):
        params = {
            "threadId": identity,
            "limit": 1,
            "sortDirection": "desc",
            "itemsView": metadata["items_view"],
        }
        if cursor is not None:
            params["cursor"] = cursor
        page = client.request("thread/turns/list", params)
        data = page.get("data")
        if not isinstance(data, list) or len(data) > 1 or "nextCursor" not in page:
            raise ConversationError("invalid turn page")
        next_cursor = page["nextCursor"]
        if next_cursor is not None:
            _string(next_cursor)
            if next_cursor in seen_cursors or not data:
                raise ConversationError("invalid or repeated continuation cursor")
            seen_cursors.add(next_cursor)
        metadata["pages"].append(
            {
                "page_index": page_index,
                "has_more": next_cursor is not None,
            }
        )
        for native in data:
            if (
                not isinstance(native, dict)
                or native.get("itemsView") != metadata["items_view"]
            ):
                raise ConversationError("unexpected turn items view")
            turn_id = _string(native.get("id"))
            if turn_id in seen_turns:
                raise ConversationError("duplicate source turn ID")
            seen_turns.add(turn_id)
            if not isinstance(native.get("status"), str) or native["status"] not in {
                "completed",
                "interrupted",
                "failed",
                "inProgress",
            }:
                raise ConversationError("unsupported source turn status")
            turn = {
                "native_turn_id": turn_id,
                "root_turn_id": native.get("rootTurnId"),
                "source_page_index": page_index,
                "status": native["status"],
                "started_at_seconds": _timestamp(native.get("startedAt")),
                "completed_at_seconds": _timestamp(native.get("completedAt")),
                "duration_ms": _timestamp(native.get("durationMs")),
                "source_truncated": _truncated(native),
                "error_present": native.get("error") is not None,
                "messages": [] if read_text else None,
                "items_missingness": None if read_text else "not_requested",
                "excluded_nonmessage_items": 0 if read_text else None,
            }
            if turn["root_turn_id"] is not None:
                _string(turn["root_turn_id"])
            items = native.get("items")
            if not isinstance(items, list) or (not read_text and items):
                raise ConversationError("unexpected turn item content")
            for item_index, item in enumerate(items):
                if not isinstance(item, dict):
                    raise ConversationError("invalid source item")
                kind = item.get("type")
                if not isinstance(kind, str):
                    raise ConversationError("invalid source item type")
                if kind in _OTHER_ITEMS:
                    turn["excluded_nonmessage_items"] += 1
                    continue
                if kind not in {"userMessage", "agentMessage"}:
                    raise ConversationError("unsupported source item format")
                message_id = _string(item.get("id"))
                if message_id in seen_messages:
                    raise ConversationError("duplicate source message ID")
                seen_messages.add(message_id)
                excluded_parts = 0
                if kind == "userMessage":
                    if not isinstance(item.get("content"), list):
                        raise ConversationError("invalid user message content")
                    parts = []
                    for part in item["content"]:
                        if not isinstance(part, dict):
                            raise ConversationError("invalid user message part")
                        if not isinstance(part.get("type"), str):
                            raise ConversationError("invalid user message part type")
                        if part.get("type") == "text" and isinstance(
                            part.get("text"), str
                        ):
                            parts.append(part["text"])
                        elif part.get("type") in _NON_TEXT:
                            excluded_parts += 1
                        else:
                            raise ConversationError("unsupported user message part")
                else:
                    if not isinstance(item.get("text"), str):
                        raise ConversationError("invalid assistant message text")
                    parts = [item["text"]]
                text[message_id] = parts
                if sum(len(s.encode()) for p in text.values() for s in p) > MAX_BYTES:
                    raise ConversationError("conversation text byte limit exceeded")
                phase = item.get("phase")
                if phase is not None and (
                    not isinstance(phase, str)
                    or phase not in {"commentary", "final_answer"}
                ):
                    raise ConversationError("unsupported assistant message phase")
                turn["messages"].append(
                    {
                        "native_message_id": message_id,
                        "source_item_ordinal": item_index,
                        "role": "user" if kind == "userMessage" else "assistant",
                        "phase": phase,
                        "timestamp": None,
                        "timestamp_missingness": "not_emitted",
                        "text": None,
                        "text_missingness": "retention_disabled",
                        "text_part_count": len(parts),
                        "text_utf8_bytes": sum(len(s.encode()) for s in parts),
                        "excluded_nontext_parts": excluded_parts,
                        "source_truncated": _truncated(item),
                    }
                )
            metadata["turns"].append(turn)
        cursor = next_cursor
        if cursor is None:
            break
    metadata["turns"].reverse()
    for index, turn in enumerate(metadata["turns"]):
        turn["source_turn_ordinal"] = index
    metadata["history_exhausted"] = cursor is None
    metadata["bounded_history"] = cursor is not None
    metadata["original_history_complete"] = None
    return ConversationRead(session, metadata, retrieved_at, text)


def require_private_database(path: Path) -> None:
    """Require the workspace's ignored local storage and reject symlink paths."""
    absolute = path.absolute()
    root = Path.cwd() / ".model-learner"
    if not absolute.is_relative_to(root) or ".." in absolute.parts:
        raise ConversationError("conversation database must be inside .model-learner")
    if any(parent.is_symlink() for parent in [absolute, *absolute.parents]):
        raise ConversationError("conversation storage symlinks are unsupported")
    if not absolute.is_file():
        raise ConversationError("initialize the private conversation database first")
    try:
        inside_git = (
            subprocess.run(
                ["git", "rev-parse", "--is-inside-work-tree"],
                capture_output=True,
                check=False,
                timeout=5,
            ).returncode
            == 0
        )
        if (
            inside_git
            and subprocess.run(
                ["git", "check-ignore", "--quiet", "--", str(absolute)],
                capture_output=True,
                check=False,
                timeout=5,
            ).returncode
            != 0
        ):
            raise ConversationError(
                "conversation database must be Git-ignored and untracked"
            )
    except (OSError, subprocess.TimeoutExpired):
        raise ConversationError("unable to validate private storage") from None
    root.chmod(0o700)
    absolute.chmod(0o600)


def ingest_conversation(
    repository: Repository, read: ConversationRead, *, retain_text: bool = False
) -> dict[str, Any]:
    """Persist one immutable snapshot atomically; text policy never changes rows."""
    require_private_database(repository.database.path)
    payload = copy.deepcopy(read.metadata)
    payload["text_retention"] = "opt_in" if retain_text else "metadata_only"
    if retain_text:
        if payload["items_view"] != "full":
            raise ConversationError(
                "text retention requires an explicit full text read"
            )
        for turn in payload["turns"]:
            for message in turn["messages"]:
                message["text"] = read.text[message["native_message_id"]]
                message["text_missingness"] = None
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode()).hexdigest()
    snapshot_id = uuid5(read.session.session_id, digest)
    event = Event(
        event_id=snapshot_id,
        stable_key=f"{FORMAT}:{snapshot_id}",
        observed_at=read.retrieved_at,
        ingested_at=read.retrieved_at,
        source=SOURCE,
        source_version=payload["native_creator_cli_version"],
        machine_id=read.session.metadata["machine_id"],
        capture_method="app_server_stdio_history",
        native_session_id=read.session.native_session_id,
        session_id=read.session.session_id,
        native_event_id=None,
        event_type="conversation.snapshot",
        provenance=Provenance.OBSERVED,
        adapter_version="1",
        payload={
            "snapshot_digest": digest,
            "timestamp_basis": "retrieval_receipt",
            **payload,
        },
    )
    created, inserted = repository.add_session_snapshot(read.session, event)
    return {
        "session_id": str(read.session.session_id),
        "snapshot_id": str(snapshot_id),
        "sessions_created": int(created),
        "snapshots_inserted": int(inserted),
        "snapshots_duplicate": int(not inserted),
        "text_retention": payload["text_retention"],
        **read.coverage(),
    }


def summarize_conversation(session: Session, events: list[Event]) -> dict[str, Any]:
    snapshots = [
        e
        for e in events
        if e.source == SOURCE
        and e.session_id == session.session_id
        and e.payload.get("format") == FORMAT
    ]
    latest = max(snapshots, key=lambda e: e.observed_at) if snapshots else None
    return {
        "snapshot_count": len(snapshots),
        "turns": len(latest.payload["turns"]) if latest else 0,
        "history_exhausted": latest.payload["history_exhausted"] if latest else None,
        "original_history_complete": None,
        "historical_configuration": None,
        "usage": None,
        "cost_usd": None,
        "verification": "unknown",
        "timestamp_basis": "retrieval_receipt",
        "product_source": session.metadata.get("product_source"),
        "backend": session.metadata.get("backend"),
    }
