"""Contract checks for documented Codex JSONL and metadata-only receipt capture."""

import io
import json
from datetime import UTC, datetime
from pathlib import Path

import pytest

from model_learner.adapters.codex import (
    CAPTURE_FORMAT,
    capture_codex_stream,
    read_codex_capture,
    summarize_session,
)
from model_learner.domain import Event, Provenance

FIXTURE = Path(__file__).parents[1] / "fixtures/codex/exec_capture.jsonl"
NOW = datetime(2026, 10, 10, 12, tzinfo=UTC)


def captured(tmp_path: Path, native: list[dict], **kwargs) -> Path:
    path = tmp_path / "capture.jsonl"
    with path.open("w") as stream:
        capture_codex_stream(
            [json.dumps(record) for record in native],
            stream,
            source_version="fixture-v1",
            clock=lambda: NOW,
            capture_id="test-capture",
            **kwargs,
        )
    return path


def test_fixture_reconstructs_observations_without_verified_outcomes() -> None:
    batch = read_codex_capture(FIXTURE, machine_id="test-machine")
    assert not batch.diagnostics
    assert len(batch.sessions) == 1
    assert len(batch.events) == 10
    assert batch.sessions[0].started_at is None
    assert batch.sessions[0].ended_at is None
    assert all(event.provenance is Provenance.OBSERVED for event in batch.events)
    summary = summarize_session(batch.sessions[0], batch.events)
    assert summary["observed_tool_items"] == 2
    assert summary["completed_turns"] == 1
    assert summary["failed_turns"] == 1
    assert summary["usage"]["input_tokens"] == 30
    assert summary["usage"]["cached_input_tokens"] == 10
    assert summary["usage"]["reasoning_output_tokens"] is None
    assert summary["cost_usd"] is None
    assert summary["latency_seconds"] is None
    assert summary["verification"] == "unknown"
    assert summary["configurations"][0]["model"] is None
    assert summary["configurations"][0]["provider"] is None
    assert batch.events[2].native_event_id is None
    assert batch.events[2].payload["native"]["item"]["id"] == "item_1"
    assert batch.events[-1].event_type == "future.native_event"


def test_capture_default_removes_transcript_arguments_outputs_and_unknown_values(
    tmp_path: Path,
) -> None:
    native = [
        {"type": "thread.started", "thread_id": "thread-1"},
        {
            "type": "item.completed",
            "item": {
                "id": "i1",
                "type": "mcp_tool_call",
                "server": "example",
                "tool": "query",
                "arguments": "SECRET",
                "result": "SECRET",
                "text": "SECRET",
            },
            "unknown": "SECRET",
        },
    ]
    path = captured(tmp_path, native)
    assert "SECRET" not in path.read_text()
    batch = read_codex_capture(path, machine_id="test")
    event = batch.events[1]
    assert event.raw_payload["item"]["id"] == "i1"
    assert event.payload["redacted_fields"] == [
        "item.arguments",
        "item.result",
        "item.text",
        "unknown",
    ]
    assert event.payload["native_observed_at"] is None
    assert event.payload["timestamp_basis"] == "capture_receipt"
    assert event.observed_at == NOW


def test_raw_retention_is_explicit_at_both_capture_and_import(tmp_path: Path) -> None:
    path = captured(
        tmp_path,
        [
            {"type": "thread.started", "thread_id": "t"},
            {"type": "error", "message": "SECRET"},
        ],
        retain_raw=True,
    )
    assert "SECRET" in path.read_text()
    safe = read_codex_capture(path, machine_id="test")
    assert "SECRET" not in safe.events[1].model_dump_json()
    raw = read_codex_capture(path, machine_id="test", retain_raw=True)
    assert raw.events[1].raw_payload["message"] == "SECRET"
    assert "message" not in raw.events[1].payload["native"]


def test_identical_native_lines_keep_distinct_stable_ids_and_replay(
    tmp_path: Path,
) -> None:
    path = captured(
        tmp_path,
        [
            {"type": "thread.started", "thread_id": "t"},
            {"type": "turn.started"},
            {"type": "turn.started"},
        ],
    )
    first = read_codex_capture(path, machine_id="test")
    second = read_codex_capture(path, machine_id="test")
    assert first.events[1].stable_key != first.events[2].stable_key
    assert [event.event_id for event in first.events] == [
        event.event_id for event in second.events
    ]
    assert first.sessions == second.sessions
    assert (
        summarize_session(first.sessions[0], first.events + second.events)[
            "event_count"
        ]
        == 3
    )


def test_plain_native_stream_has_no_invented_event_time(tmp_path: Path) -> None:
    path = tmp_path / "plain.jsonl"
    path.write_text('{"type":"thread.started","thread_id":"t"}\n')
    batch = read_codex_capture(path, machine_id="test")
    assert not batch.sessions and not batch.events
    assert len(batch.diagnostics) == 1


def test_missing_thread_bad_json_and_naive_times_are_diagnosed(tmp_path: Path) -> None:
    path = captured(tmp_path, [{"type": "turn.started"}])
    native = {
        "format": CAPTURE_FORMAT,
        "capture_id": "c",
        "sequence": 2,
        "captured_at": "2026-10-10T12:00:00",
        "source_version": "v",
        "event": {"type": "thread.started", "thread_id": "t"},
    }
    with path.open("a") as stream:
        stream.write("PRIVATE MALFORMED\n" + json.dumps(native) + "\n")
    batch = read_codex_capture(path, machine_id="test")
    assert not batch.events
    assert [diagnostic.line for diagnostic in batch.diagnostics] == [1, 2, 3]
    assert "PRIVATE" not in str(batch.diagnostics)


def test_capture_malformed_input_and_bad_timestamps() -> None:
    stream = io.StringIO()
    report = capture_codex_stream(
        ["SECRET malformed", "[]", '{"type":"turn.started"}'],
        stream,
        source_version="unknown",
        clock=lambda: NOW,
    )
    assert report.accepted == 1 and len(report.diagnostics) == 2
    assert "SECRET" not in str(report)
    report = capture_codex_stream(
        ['{"type":"turn.started"}'],
        io.StringIO(),
        source_version="unknown",
        clock=lambda: datetime(2026, 10, 10),
    )
    assert report.accepted == 0 and len(report.diagnostics) == 1
    with pytest.raises(ValueError):
        capture_codex_stream([], io.StringIO(), source_version="")


def test_multiple_native_threads_and_capture_boundaries(tmp_path: Path) -> None:
    path = captured(
        tmp_path,
        [
            {"type": "thread.started", "thread_id": "a"},
            {"type": "turn.started"},
            {"type": "thread.started", "thread_id": "b"},
            {"type": "turn.completed"},
        ],
    )
    batch = read_codex_capture(path, machine_id="test")
    assert len(batch.sessions) == 2
    assert [event.native_session_id for event in batch.events] == ["a", "a", "b", "b"]
    assert (
        summarize_session(batch.sessions[1], batch.events)["usage"]["input_tokens"]
        is None
    )


def test_resource_coverage_ignores_invalid_numbers_and_keeps_zero(
    tmp_path: Path,
) -> None:
    path = captured(
        tmp_path,
        [
            {"type": "thread.started", "thread_id": "a"},
            {
                "type": "turn.completed",
                "usage": {
                    "input_tokens": 0,
                    "cached_input_tokens": -1,
                    "output_tokens": True,
                },
            },
            {"type": "turn.completed"},
        ],
    )
    batch = read_codex_capture(path, machine_id="test")
    summary = summarize_session(batch.sessions[0], batch.events)
    assert summary["usage"]["input_tokens"] == 0
    assert summary["usage"]["output_tokens"] is None
    assert summary["usage"]["cached_input_tokens"] is None
    assert summary["usage"]["completed_turns_with_usage"] == 1
    assert summary["usage"]["completed_turns_total"] == 2
    assert summary["usage"]["field_coverage"] == {"input_tokens": 1}


def test_conflicting_sequence_is_rejected(tmp_path: Path) -> None:
    path = captured(
        tmp_path,
        [{"type": "thread.started", "thread_id": "a"}, {"type": "turn.started"}],
    )
    envelope = json.loads(path.read_text().splitlines()[1])
    envelope["event"] = {"type": "turn.completed"}
    with path.open("a") as stream:
        stream.write(json.dumps(envelope) + "\n")
    batch = read_codex_capture(path, machine_id="test")
    assert len(batch.events) == 2
    assert len(batch.diagnostics) == 1


def test_valid_ledger_event_without_adapter_payload_remains_visible() -> None:
    batch = read_codex_capture(FIXTURE, machine_id="test")
    session = batch.sessions[0]
    manual = Event(
        source="codex.exec",
        source_version="unknown",
        machine_id="test",
        capture_method="manual",
        native_session_id=session.native_session_id,
        session_id=session.session_id,
        event_type="manual.entry",
        provenance=Provenance.OBSERVED,
        observed_at=NOW,
    )
    summary = summarize_session(session, [*batch.events, manual])
    assert summary["event_count"] == 11
    assert summary["supported_event_count"] == 10
    assert summary["unsupported_event_count"] == 1
    assert summary["event_types"]["manual.entry"] == 1
    assert summary["usage"]["input_tokens"] == 30
    empty = summarize_session(session, [manual])
    assert empty["unsupported_event_count"] == 1
    assert empty["first_capture_at"] is None
    assert empty["usage"]["input_tokens"] is None


def test_sanitized_real_cli_smoke_preserves_observed_usage_and_unknowns() -> None:
    fixture = FIXTURE.with_name("real_smoke_capture.jsonl")
    batch = read_codex_capture(fixture, machine_id="fixture-machine")
    assert not batch.diagnostics
    assert len(batch.sessions) == 1 and len(batch.events) == 4
    assert [event.event_type for event in batch.events] == [
        "thread.started",
        "turn.started",
        "item.completed",
        "turn.completed",
    ]
    summary = summarize_session(batch.sessions[0], batch.events)
    assert summary["completed_turns"] == 1
    assert summary["observed_tool_items"] == 0
    assert summary["usage"]["input_tokens"] == 14524
    assert summary["usage"]["cached_input_tokens"] == 12288
    assert summary["usage"]["output_tokens"] == 8
    assert summary["usage"]["reasoning_output_tokens"] == 0
    assert summary["configurations"][0]["model"] is None
    assert summary["configurations"][0]["provider"] is None
    assert summary["verification"] == "unknown"
    assert summary["native_started_at"] is None
    assert summary["latency_seconds"] is None


def test_rejected_thread_start_does_not_supply_identity_to_following_events(
    tmp_path: Path,
) -> None:
    path = captured(
        tmp_path,
        [{"type": "thread.started", "thread_id": "t"}, {"type": "turn.started"}],
    )
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    lines[0]["redacted_fields"] = "invalid"
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    batch = read_codex_capture(path, machine_id="test")
    assert len(batch.diagnostics) == 2
    assert not batch.sessions and not batch.events


@pytest.mark.parametrize("bad_field", ["redacted_fields", "captured_at"])
def test_rejected_second_thread_boundary_invalidates_previous_identity(
    tmp_path: Path, bad_field: str
) -> None:
    path = captured(
        tmp_path,
        [
            {"type": "thread.started", "thread_id": "a"},
            {"type": "thread.started", "thread_id": "b"},
            {"type": "turn.completed", "usage": {"input_tokens": 100}},
            {"type": "thread.started", "thread_id": "c"},
            {"type": "turn.completed", "usage": {"input_tokens": 7}},
        ],
    )
    lines = [json.loads(line) for line in path.read_text().splitlines()]
    lines[1][bad_field] = "invalid"
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    batch = read_codex_capture(path, machine_id="test")
    assert [diagnostic.line for diagnostic in batch.diagnostics] == [2, 3]
    assert [session.native_session_id for session in batch.sessions] == ["a", "c"]
    assert [event.native_session_id for event in batch.events] == ["a", "c", "c"]
    first = summarize_session(batch.sessions[0], batch.events)
    assert first["completed_turns"] == 0
    assert first["usage"]["input_tokens"] is None
    assert (
        summarize_session(batch.sessions[1], batch.events)["usage"]["input_tokens"] == 7
    )
