"""Observe documented ``codex exec --json`` output without controlling Codex.

The native stream has no documented event timestamps. A capture envelope retains
observer receipt time explicitly, never claiming it is a native execution time.
Only metadata is retained by default; arbitrary native content is opt-in.
"""

from __future__ import annotations

import json
from collections import Counter
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, TextIO
from uuid import NAMESPACE_URL, uuid4, uuid5

from model_learner.domain import Event, ExecutionConfiguration, Provenance, Session
from model_learner.domain.models import utc_now
from model_learner.storage.database import Repository

CAPTURE_FORMAT = "codex-exec-capture/v1"
ADAPTER_VERSION = "1"
SOURCE = "codex.exec"
_USAGE_FIELDS = (
    "input_tokens",
    "cached_input_tokens",
    "output_tokens",
    "reasoning_output_tokens",
)
_TOOL_TYPES = {"command_execution", "mcp_tool_call", "web_search", "file_change"}


@dataclass(frozen=True)
class CaptureDiagnostic:
    line: int
    reason: str


@dataclass(frozen=True)
class CaptureReport:
    accepted: int
    diagnostics: tuple[CaptureDiagnostic, ...]


@dataclass(frozen=True)
class CaptureBatch:
    sessions: tuple[Session, ...]
    events: tuple[Event, ...]
    diagnostics: tuple[CaptureDiagnostic, ...]
    event_lines: tuple[int, ...] = ()


@dataclass(frozen=True)
class ImportReport:
    sessions: int
    events_inserted: int
    events_duplicate: int
    diagnostics: tuple[CaptureDiagnostic, ...]


def _aware(value: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError("timestamp requires an ISO string")
    result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if result.tzinfo is None or result.utcoffset() is None:
        raise ValueError("timestamp requires a timezone")
    return result


def _metadata(native: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    """Allowlist structural metadata; do not guess where arbitrary secrets live."""
    safe: dict[str, Any] = {}
    omitted: list[str] = []
    for key, value in native.items():
        if key in {"type", "thread_id", "id", "model", "model_provider"}:
            if isinstance(value, str):
                safe[key] = value
        elif key == "item" and isinstance(value, dict):
            item = {}
            for item_key, item_value in value.items():
                if item_key in {"id", "type", "status", "server", "tool"}:
                    if isinstance(item_value, str):
                        item[item_key] = item_value
                elif item_key == "exit_code":
                    if type(item_value) is int or item_value is None:
                        item[item_key] = item_value
                else:
                    omitted.append(f"item.{item_key}")
            safe[key] = item
        elif key == "usage" and isinstance(value, dict):
            usage = {}
            for usage_key, count in value.items():
                if usage_key in _USAGE_FIELDS and type(count) is int and count >= 0:
                    usage[usage_key] = count
                else:
                    omitted.append(f"usage.{usage_key}")
            safe[key] = usage
        else:
            omitted.append(key)
    return safe, sorted(omitted)


def capture_codex_stream(
    lines: Iterable[str],
    output: TextIO,
    *,
    source_version: str,
    retain_raw: bool = False,
    clock: Callable[[], datetime] = utc_now,
    capture_id: str | None = None,
) -> CaptureReport:
    """Wrap an existing stream with receipt times; never launch/control an agent.

    ``retain_raw`` retains potentially private prompts/tool arguments/output.
    Callers must explicitly authorize local retention; this is not redaction.
    Invalid input is diagnosed without reproducing its private content.
    """
    if not source_version:
        raise ValueError("source_version is required (use 'unknown' if unavailable)")
    identity = capture_id or str(uuid4())
    accepted = 0
    diagnostics = []
    for line_number, line in enumerate(lines, 1):
        if not line.strip():
            continue
        received_at = clock()
        try:
            _aware(received_at.isoformat())
            native = json.loads(line)
            if (
                not isinstance(native, dict)
                or not isinstance(native.get("type"), str)
                or not native["type"]
            ):
                raise ValueError("event requires a string type")
        except (ValueError, TypeError):
            diagnostics.append(CaptureDiagnostic(line_number, "invalid native event"))
            continue
        metadata, redacted = _metadata(native)
        envelope = {
            "format": CAPTURE_FORMAT,
            "capture_id": identity,
            "sequence": line_number,
            "captured_at": received_at.isoformat(),
            "source_version": source_version,
            "event": native if retain_raw else metadata,
            "redacted_fields": [] if retain_raw else redacted,
        }
        output.write(json.dumps(envelope, separators=(",", ":")) + "\n")
        output.flush()
        accepted += 1
    return CaptureReport(accepted, tuple(diagnostics))


def read_codex_capture(
    path: Path | str,
    *,
    machine_id: str,
    source_version: str | None = None,
    retain_raw: bool = False,
) -> CaptureBatch:
    """Validate capture envelopes and build M1.1 sessions/events in memory.

    Plain native JSONL is deliberately rejected: import time is not event time.
    Unknown event types survive as observed metadata. Errors are content-free.
    """
    if not machine_id or source_version == "":
        raise ValueError("machine_id and nonempty source_version are required")
    sessions: dict[str, Session] = {}
    events: list[Event] = []
    event_lines: list[int] = []
    diagnostics: list[CaptureDiagnostic] = []
    active_thread: str | None = None
    active_capture: str | None = None
    seen_sequences: dict[tuple[str, int], dict[str, Any]] = {}
    with Path(path).open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, 1):
            if not line.strip():
                continue
            try:
                envelope = json.loads(line)
                if (
                    not isinstance(envelope, dict)
                    or envelope.get("format") != CAPTURE_FORMAT
                ):
                    raise ValueError(
                        "expected timestamped codex-exec-capture/v1 envelope"
                    )
                capture_id = envelope.get("capture_id")
                sequence = envelope.get("sequence")
                if (
                    not isinstance(capture_id, str)
                    or not capture_id
                    or type(sequence) is not int
                    or sequence < 1
                ):
                    raise ValueError("invalid capture identity or sequence")
                observed_at = _aware(envelope["captured_at"])
                version = source_version or envelope.get("source_version")
                if not isinstance(version, str) or not version:
                    raise ValueError("source_version is required")
                if source_version and envelope.get("source_version") not in (
                    None,
                    "unknown",
                    source_version,
                ):
                    raise ValueError("source_version conflicts with capture")
                native = envelope["event"]
                if (
                    not isinstance(native, dict)
                    or not isinstance(native.get("type"), str)
                    or not native["type"]
                ):
                    raise ValueError("event requires a string type")
                identity = (capture_id, sequence)
                if identity in seen_sequences and seen_sequences[identity] != envelope:
                    raise ValueError("capture sequence conflicts with previous event")
                next_thread = active_thread if active_capture == capture_id else None
                if native["type"] == "thread.started":
                    native_thread = native.get("thread_id")
                    if not isinstance(native_thread, str) or not native_thread:
                        raise ValueError("thread.started requires thread_id")
                    next_thread = native_thread
                if next_thread is None:
                    raise ValueError(
                        "event has no preceding thread.started in this capture"
                    )
                metadata, redacted = _metadata(native)
                existing_redacted = envelope.get("redacted_fields", [])
                if not isinstance(existing_redacted, list) or not all(
                    isinstance(item, str) for item in existing_redacted
                ):
                    raise ValueError("invalid redacted_fields")
                session_id = uuid5(
                    NAMESPACE_URL, json.dumps([SOURCE, machine_id, next_thread])
                )
                if next_thread not in sessions:
                    sessions[next_thread] = Session(
                        session_id=session_id,
                        source=SOURCE,
                        native_session_id=next_thread,
                        metadata={
                            "machine_id": machine_id,
                            "adapter_version": ADAPTER_VERSION,
                            "native_timestamp_coverage": "unavailable",
                        },
                    )
                payload = {
                    "native": metadata,
                    "capture_id": capture_id,
                    "sequence": sequence,
                    "timestamp_basis": "capture_receipt",
                    "native_observed_at": None,
                    "redacted_fields": sorted(set(existing_redacted + redacted)),
                }
                key_material = [
                    SOURCE,
                    machine_id,
                    capture_id,
                    sequence,
                ]
                stable_key = str(
                    uuid5(NAMESPACE_URL, json.dumps(key_material, sort_keys=True))
                )
                events.append(
                    Event(
                        event_id=uuid5(NAMESPACE_URL, stable_key),
                        stable_key=stable_key,
                        observed_at=observed_at,
                        source=SOURCE,
                        source_version=version,
                        machine_id=machine_id,
                        capture_method="stdout_capture_import",
                        native_session_id=next_thread,
                        session_id=session_id,
                        native_event_id=metadata.get("id"),
                        event_type=native["type"],
                        provenance=Provenance.OBSERVED,
                        payload=payload,
                        raw_payload=native if retain_raw else metadata,
                        adapter_version=ADAPTER_VERSION,
                    )
                )
                event_lines.append(line_number)
                seen_sequences[identity] = envelope
                active_capture = capture_id
                active_thread = next_thread
            except (ValueError, TypeError, KeyError):
                # A rejected record may hide a thread/capture boundary. Require
                # a fresh valid start instead of attributing later facts using
                # an identity that could now belong to a different thread.
                active_capture = None
                active_thread = None
                diagnostics.append(
                    CaptureDiagnostic(line_number, "invalid capture envelope or event")
                )
    return CaptureBatch(
        tuple(sessions.values()), tuple(events), tuple(diagnostics), tuple(event_lines)
    )


def ingest_codex_capture(
    repository: Repository,
    path: Path | str,
    *,
    machine_id: str,
    source_version: str | None = None,
    retain_raw: bool = False,
) -> ImportReport:
    """Import read-only source observations using existing ledger repositories."""
    batch = read_codex_capture(
        path,
        machine_id=machine_id,
        source_version=source_version,
        retain_raw=retain_raw,
    )
    created = inserted = duplicate = 0
    diagnostics = list(batch.diagnostics)
    accepted: list[tuple[int, Event, bool]] = []
    for line, event in zip(batch.event_lines, batch.events, strict=True):
        existing = repository.get(Event, event.event_id)
        if existing is not None and not _same_observation(existing, event):
            diagnostics.append(
                CaptureDiagnostic(
                    line, "capture identity conflicts with persisted observation"
                )
            )
        else:
            accepted.append((line, event, existing is not None))
    accepted_sessions = {event.session_id for _, event, _ in accepted}
    for session in batch.sessions:
        if (
            session.session_id in accepted_sessions
            and repository.get(Session, session.session_id) is None
        ):
            repository.create_session(session)
            created += 1
    for line, event, exists in accepted:
        persisted = repository.add_event(event)
        # Recheck the canonical row in case another local importer raced us.
        if not _same_observation(persisted, event):
            diagnostics.append(
                CaptureDiagnostic(
                    line, "capture identity conflicts with persisted observation"
                )
            )
            continue
        if exists:
            duplicate += 1
        else:
            inserted += 1
    return ImportReport(created, inserted, duplicate, tuple(diagnostics))


def _same_observation(first: Event, second: Event) -> bool:
    """Compare retained source facts; raw-retention policy is not a new event."""
    return (
        first.observed_at == second.observed_at
        and first.source_version == second.source_version
        and first.native_session_id == second.native_session_id
        and first.native_event_id == second.native_event_id
        and first.event_type == second.event_type
        and first.payload.get("native") == second.payload.get("native")
        and first.payload.get("capture_id") == second.payload.get("capture_id")
        and first.payload.get("sequence") == second.payload.get("sequence")
    )


def summarize_session(session: Session, events: Iterable[Event]) -> dict[str, Any]:
    """Rebuild observed counts, retaining unknown native times/costs/outcomes."""
    selected = {
        event.stable_key: event
        for event in events
        if event.session_id == session.session_id and event.source == SOURCE
    }
    supported = [event for event in selected.values() if _supported_event(event)]
    timeline = sorted(
        supported,
        key=lambda event: (
            event.observed_at,
            event.payload["capture_id"],
            event.payload["sequence"],
        ),
    )
    kinds = Counter(event.event_type for event in timeline)
    tools: set[tuple[str, str]] = set()
    missing_ids = 0
    usage: dict[str, int | None] = dict.fromkeys(_USAGE_FIELDS)
    usage_coverage = Counter()
    with_usage = 0
    configurations: dict[str, dict[str, Any]] = {}
    for event in timeline:
        native = event.payload["native"]
        config = ExecutionConfiguration(
            provider=native.get("model_provider"),
            model=native.get("model"),
            harness="codex.exec",
            harness_version=event.source_version
            if event.source_version != "unknown"
            else None,
        )
        configurations[config.configuration_id] = config.model_dump(mode="json")
        item = native.get("item", {})
        if item.get("type") in _TOOL_TYPES:
            if item.get("id"):
                tools.add((event.payload["capture_id"], item["id"]))
            else:
                missing_ids += 1
        if event.event_type == "turn.completed":
            measured = native.get("usage", {})
            if measured:
                with_usage += 1
            for name in _USAGE_FIELDS:
                if name in measured:
                    usage[name] = (usage[name] or 0) + measured[name]
                    usage_coverage[name] += 1
    usage.update(
        {
            "completed_turns_with_usage": with_usage,
            "completed_turns_total": kinds["turn.completed"],
            "field_coverage": dict(usage_coverage),
        }
    )
    return {
        "native_session_id": session.native_session_id,
        "event_count": len(selected),
        "event_types": dict(Counter(event.event_type for event in selected.values())),
        "supported_event_count": len(timeline),
        "unsupported_event_count": len(selected) - len(timeline),
        "first_capture_at": timeline[0].observed_at.isoformat() if timeline else None,
        "last_capture_at": timeline[-1].observed_at.isoformat() if timeline else None,
        "native_started_at": session.started_at,
        "native_ended_at": session.ended_at,
        "timestamp_basis": "capture_receipt",
        "configurations": list(configurations.values()),
        "observed_tool_items": len(tools),
        "tool_items_missing_id": missing_ids,
        "completed_turns": kinds["turn.completed"],
        "failed_turns": kinds["turn.failed"],
        "usage": usage,
        "cost_usd": None,
        "latency_seconds": None,
        "verification": "unknown",
    }


def _supported_event(event: Event) -> bool:
    """A source name alone cannot identify this adapter's retained schema."""
    payload = event.payload
    native = payload.get("native")
    if (
        event.adapter_version != ADAPTER_VERSION
        or payload.get("timestamp_basis") != "capture_receipt"
        or not isinstance(payload.get("capture_id"), str)
        or type(payload.get("sequence")) is not int
        or not isinstance(native, dict)
    ):
        return False
    # Validate the projection rather than trusting a hand-authored Event payload.
    safe, _ = _metadata(native)
    return safe == native
