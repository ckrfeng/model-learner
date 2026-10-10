"""Codex native observations integrate with the unchanged M1.1 ledger."""

import json
from pathlib import Path

import pytest

from model_learner.adapters.codex import ingest_codex_capture, summarize_session
from model_learner.domain import Event, Outcome, Run, Session, Task, Verification
from model_learner.storage.database import Database, Repository
from model_learner.storage.jsonl import export_jsonl, import_jsonl

FIXTURE = Path(__file__).parents[1] / "fixtures/codex/exec_capture.jsonl"


def repository(path: Path) -> Repository:
    database = Database(path)
    database.initialize()
    return Repository(database)


def test_import_replay_and_rebuild_preserve_native_observation_only(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path / "local.sqlite3")
    original = FIXTURE.read_bytes()
    first = ingest_codex_capture(repo, FIXTURE, machine_id="local-test")
    events = repo.list_records(Event)
    session = repo.list_records(Session)[0]
    initial_summary = summarize_session(session, events)
    second = ingest_codex_capture(repo, FIXTURE, machine_id="local-test")
    assert first.sessions == 1 and first.events_inserted == 10
    assert second.sessions == 0 and second.events_inserted == 0
    assert second.events_duplicate == 10
    assert not first.diagnostics and not second.diagnostics
    assert events == repo.list_records(Event)
    assert initial_summary == summarize_session(session, repo.list_records(Event))
    assert FIXTURE.read_bytes() == original
    assert all(event.run_id is None for event in events)
    for kind in (Task, Run, Verification, Outcome):
        assert repo.list_records(kind) == []


def test_m1_jsonl_round_trip_preserves_event_ids_and_unknowns(tmp_path: Path) -> None:
    source = repository(tmp_path / "source.sqlite3")
    ingest_codex_capture(source, FIXTURE, machine_id="local-test")
    sessions = tmp_path / "sessions.jsonl"
    events = tmp_path / "events.jsonl"
    assert export_jsonl(source, Session, sessions) == 1
    assert export_jsonl(source, Event, events) == 10
    destination = repository(tmp_path / "destination.sqlite3")
    assert import_jsonl(destination, sessions) == 1
    assert import_jsonl(destination, events) == 10
    assert destination.list_records(Session) == source.list_records(Session)
    assert destination.list_records(Event) == source.list_records(Event)


def test_machine_identity_separates_independent_native_sessions(tmp_path: Path) -> None:
    repo = repository(tmp_path / "local.sqlite3")
    ingest_codex_capture(repo, FIXTURE, machine_id="first")
    second = ingest_codex_capture(repo, FIXTURE, machine_id="second")
    assert second.sessions == 1 and second.events_inserted == 10
    assert len(repo.list_records(Session)) == 2


@pytest.mark.parametrize("mutation", ["usage", "timestamp", "source_version"])
def test_modified_capture_is_rejected_across_imports(
    tmp_path: Path, mutation: str
) -> None:
    repo = repository(tmp_path / "local.sqlite3")
    ingest_codex_capture(repo, FIXTURE, machine_id="local-test")
    initial = repo.list_records(Event)
    session = repo.list_records(Session)[0]
    original_summary = summarize_session(session, initial)
    lines = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    if mutation == "usage":
        lines[5]["event"]["usage"]["input_tokens"] = 100
    elif mutation == "timestamp":
        lines[5]["captured_at"] = "2026-10-11T12:00:00+00:00"
    else:
        lines[5]["source_version"] = "changed-version"
    modified = tmp_path / "modified.jsonl"
    modified.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    result = ingest_codex_capture(repo, modified, machine_id="local-test")
    assert result.events_inserted == 0
    assert result.events_duplicate == 9
    assert len(result.diagnostics) == 1
    assert result.diagnostics[0].line == 6
    assert repo.list_records(Event) == initial
    assert summarize_session(session, initial) == original_summary


def test_raw_retention_choice_does_not_create_another_observation(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path / "local.sqlite3")
    lines = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    lines[4]["event"]["item"]["text"] = "private example"
    raw = tmp_path / "raw-capture.jsonl"
    raw.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    first = ingest_codex_capture(repo, raw, machine_id="local-test")
    second = ingest_codex_capture(repo, raw, machine_id="local-test", retain_raw=True)
    assert first.events_inserted == 10
    assert second.events_inserted == 0 and second.events_duplicate == 10
    assert not second.diagnostics
    assert all(
        "private example" not in event.model_dump_json()
        for event in repo.list_records(Event)
    )


def test_unknown_version_cannot_be_rewritten_by_reimport(tmp_path: Path) -> None:
    repo = repository(tmp_path / "local.sqlite3")
    lines = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    for line in lines:
        line["source_version"] = "unknown"
    path = tmp_path / "unknown.jsonl"
    path.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    first = ingest_codex_capture(repo, path, machine_id="local-test")
    second = ingest_codex_capture(
        repo, path, machine_id="local-test", source_version="v1"
    )
    assert first.events_inserted == 10
    assert second.events_inserted == 0 and second.events_duplicate == 0
    assert len(second.diagnostics) == 10
    assert all(event.source_version == "unknown" for event in repo.list_records(Event))


def test_changed_native_thread_identity_cannot_duplicate_capture(
    tmp_path: Path,
) -> None:
    repo = repository(tmp_path / "local.sqlite3")
    ingest_codex_capture(repo, FIXTURE, machine_id="local-test")
    events = repo.list_records(Event)
    sessions = repo.list_records(Session)
    lines = [json.loads(line) for line in FIXTURE.read_text().splitlines()]
    lines[0]["event"]["thread_id"] = "altered-thread"
    modified = tmp_path / "changed-native-id.jsonl"
    modified.write_text("\n".join(json.dumps(line) for line in lines) + "\n")
    result = ingest_codex_capture(repo, modified, machine_id="local-test")
    assert result.events_inserted == 0 and result.events_duplicate == 0
    assert result.sessions == 0 and len(result.diagnostics) == 10
    assert repo.list_records(Session) == sessions
    assert repo.list_records(Event) == events
