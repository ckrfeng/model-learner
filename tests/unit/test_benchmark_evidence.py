"""Evidence export privacy and regular-file boundary checks."""

from datetime import datetime

import pytest

from model_learner.benchmark.evidence import _native_projection, _regular
from model_learner.domain.models import Event, utc_now


def test_native_projection_allowlist_omits_raw_hidden_labels_and_arbitrary_fields():
    event = Event(
        observed_at=utc_now(),
        source="codex.exec",
        source_version="fixture-v1",
        machine_id="fixture",
        capture_method="stdout_capture_import",
        native_session_id="fixture-thread",
        event_type="item.completed",
        provenance="observed",
        adapter_version="1",
        payload={
            "native": {
                "type": "item.completed",
                "future_label": 1,
                "item": {
                    "id": "item-1",
                    "type": "command_execution",
                    "status": "completed",
                    "exit_code": 1,
                    "command": "PRIVATE_COMMAND",
                    "output": "HIDDEN_TEST_SECRET",
                },
            },
            "hidden_acceptance": "HIDDEN_TEST_SECRET",
            "redacted_fields": ["item.command", "HIDDEN_TEST_SECRET"],
            "capture_id": "c",
            "sequence": 1,
        },
        raw_payload={"text": "PRIVATE_RAW"},
    )
    projected = _native_projection(event)
    assert projected.event_id == event.event_id
    assert projected.stable_key == event.stable_key
    assert projected.ingested_at == event.ingested_at
    assert projected.raw_payload is None
    assert projected.payload["redacted_fields"] == ["item.command"]
    assert projected.payload["redacted_field_count"] == 2
    assert projected.payload["native"]["item"]["exit_code"] == 1
    for secret in ("PRIVATE", "HIDDEN", "future_label", "hidden_acceptance"):
        assert secret not in projected.model_dump_json()


def test_regular_file_rejects_symlink_and_directory(tmp_path):
    file = tmp_path / "file"
    file.write_text("harmless")
    link = tmp_path / "link"
    link.symlink_to(file)
    _regular(file)
    for path in (link, tmp_path):
        with pytest.raises(ValueError, match="regular"):
            _regular(path)


def test_native_projection_rejects_naive_event_receipts():
    with pytest.raises(ValueError, match="timezone"):
        Event(
            observed_at=datetime(2026, 1, 1),
            source="codex.exec",
            source_version="1",
            machine_id="fixture",
            capture_method="fixture",
            native_session_id="thread",
            event_type="thread.started",
            provenance="observed",
        )
