"""Offline stdio, CLI, atomic replay and explicit local text retention."""

import json
import sqlite3
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from model_learner.adapters.app_server import (
    READ_METHODS,
    AppServerClient,
    ConversationError,
)
from model_learner.adapters.conversations import (
    ingest_conversation,
    read_conversation,
    require_private_database,
)
from model_learner.cli import app
from model_learner.domain import (
    Event,
    Observation,
    Outcome,
    Run,
    Session,
    Task,
    Verification,
)
from model_learner.storage.database import Database, Repository, StorageError

FIXTURE = Path(__file__).parents[1] / "fixtures/conversations/app_server.py"
SELECTED_ID = "00000000-0000-4000-8000-000000000001"


@pytest.fixture
def executable(tmp_path):
    path = tmp_path / "fake-codex"
    path.write_text(
        f"#!{sys.executable}\nimport runpy\n"
        f"runpy.run_path({str(FIXTURE)!r}, run_name='__main__')\n"
    )
    path.chmod(0o700)
    return path


@pytest.fixture
def ledger(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    db = Database(tmp_path / ".model-learner/history.sqlite3")
    db.initialize()
    return Repository(db)


def read(executable, *, text=True, product="codex_desktop"):
    with AppServerClient(SELECTED_ID, executable=executable) as client:
        result = read_conversation(
            client, product_source=product, machine_id="fixture", read_text=text
        )
    assert client.exit_code == 0
    assert set(client.sent_methods) == READ_METHODS
    assert client.sent_methods["thread/turns/list"] == 3
    return result


def test_fresh_read_replay_is_duplicate_free_and_creates_no_learning(
    ledger, executable
):
    first_read = read(executable)
    first = ingest_conversation(ledger, first_read)
    initial = ledger.list_records(Event)
    second_read = read(executable)
    assert second_read.retrieved_at > first_read.retrieved_at
    second = ingest_conversation(ledger, second_read)
    assert first["snapshots_inserted"] == 1
    assert second["snapshots_duplicate"] == 1 and second["snapshots_inserted"] == 0
    assert ledger.list_records(Event) == initial
    assert len(ledger.list_records(Session)) == 1
    event = initial[0]
    assert event.run_id is None and event.raw_payload is None
    assert event.observed_at == first_read.retrieved_at
    serialized = event.model_dump_json()
    assert "PRIVATE_" not in serialized and "Whitespace" not in serialized
    assert "current-only" not in serialized
    assert ledger.database.path.stat().st_mode & 0o777 == 0o600
    assert ledger.database.path.parent.stat().st_mode & 0o777 == 0o700
    for kind in (Task, Run, Verification, Outcome):
        assert ledger.list_records(kind) == []
    assert ledger.list_records(Observation, source_kind="real") == []


def test_sanitized_opt_in_is_exact_and_does_not_rewrite_metadata_snapshot(
    ledger, executable
):
    result = read(executable)
    ingest_conversation(ledger, result)
    first = ledger.list_records(Event)[0]
    opted = ingest_conversation(ledger, result, retain_text=True)
    assert opted["snapshots_inserted"] == 1
    assert opted["text_retention"] == "opt_in"
    assert ledger.get(Event, first.event_id) == first
    text_event = next(
        e for e in ledger.list_records(Event) if e.payload["text_retention"] == "opt_in"
    )
    messages = [m for t in text_event.payload["turns"] for m in t["messages"]]
    for message in messages:
        assert message["text"] == result.text[message["native_message_id"]]
    assert "café" in messages[2]["text"][0]
    assert "PRIVATE_" not in text_event.model_dump_json()
    replay = ingest_conversation(ledger, read(executable), retain_text=True)
    assert replay["snapshots_duplicate"] == 1


def test_default_metadata_can_not_opt_into_missing_text(ledger, executable):
    result = read(executable, text=False)
    assert result.text == {}
    with pytest.raises(ConversationError, match="explicit full text read"):
        ingest_conversation(ledger, result, retain_text=True)
    assert ledger.list_records(Session) == []


def test_product_and_machine_identity_are_separate(ledger, executable, monkeypatch):
    first = read(executable)
    ingest_conversation(ledger, first)
    monkeypatch.setenv("MODEL_LEARNER_FIXTURE_ORIGINATOR", "codex_work_desktop")
    second = read(executable, product="chatgpt_work_local")
    assert first.session.session_id != second.session.session_id
    ingest_conversation(ledger, second)
    assert len(ledger.list_records(Session)) == 2


def test_changed_snapshot_appends_explicit_version(ledger, executable):
    result = read(executable)
    ingest_conversation(ledger, result)
    result.metadata["turns"][0]["source_truncated"] = True
    report = ingest_conversation(ledger, result)
    assert report["snapshots_inserted"] == 1
    assert len({e.payload["snapshot_digest"] for e in ledger.list_records(Event)}) == 2


def test_fresh_opaque_cursors_do_not_duplicate_source_snapshot(
    ledger, executable, monkeypatch
):
    monkeypatch.setenv("MODEL_LEARNER_FIXTURE_CURSOR_PREFIX", "first:")
    first_read = read(executable)
    ingest_conversation(ledger, first_read)
    monkeypatch.setenv("MODEL_LEARNER_FIXTURE_CURSOR_PREFIX", "second:")
    second_read = read(executable)
    assert first_read.metadata == second_read.metadata
    report = ingest_conversation(ledger, second_read)
    assert report["snapshots_duplicate"] == 1
    assert len(ledger.list_records(Event)) == 1


def test_storage_conflict_and_transaction_rollback(ledger, executable):
    result = read(executable)
    ingest_conversation(ledger, result)
    event = ledger.list_records(Event)[0]
    changed = event.model_copy(update={"payload": {"private": "SECRET"}})
    with pytest.raises(StorageError, match="retained-data conflict"):
        ledger.add_session_snapshot(result.session, changed)
    assert ledger.list_records(Event) == [event]
    # A failing event insertion rolls back session creation in the same transaction.
    with ledger.database.connection() as connection:
        connection.execute(
            "CREATE TRIGGER reject_snapshot BEFORE INSERT ON events "
            "BEGIN SELECT RAISE(ABORT, 'controlled insertion failure'); END"
        )
    # Use an actual new UUID, preserving event/session agreement.
    from uuid import uuid4

    new_session = result.session.model_copy(update={"session_id": uuid4()})
    new_event = event.model_copy(
        update={
            "event_id": uuid4(),
            "stable_key": "new-snapshot",
            "session_id": new_session.session_id,
        }
    )
    with pytest.raises(sqlite3.IntegrityError):
        ledger.add_session_snapshot(new_session, new_event)
    assert ledger.get(Session, new_session.session_id) is None


@pytest.mark.parametrize(
    "mode",
    [
        "server_request",
        "rpc_error",
        "wrong_id",
        "malformed",
        "oversized",
        "timeout",
        "eof",
    ],
)
def test_transport_fails_closed_without_private_diagnostics(
    executable, monkeypatch, mode, capsys
):
    monkeypatch.setenv("MODEL_LEARNER_FIXTURE_MODE", mode)
    with pytest.raises(ConversationError) as raised:
        with AppServerClient(SELECTED_ID, executable=executable, timeout=0.1):
            pass
    assert "PRIVATE_" not in str(raised.value)
    assert "PRIVATE_" not in repr(raised.value)
    assert capsys.readouterr().out == ""


def test_read_rpc_error_and_notifications(executable, monkeypatch):
    monkeypatch.setenv("MODEL_LEARNER_FIXTURE_MODE", "notification")
    with AppServerClient(SELECTED_ID, executable=executable) as client:
        result = read_conversation(
            client, product_source="codex_desktop", machine_id="fixture"
        )
        assert result.coverage()["turns"] == 3
        assert client.notifications_ignored == 5
        with pytest.raises(ConversationError, match="RPC method denied"):
            client.request("thread/resume", {"threadId": SELECTED_ID})
        with pytest.raises(ConversationError, match="scope denied"):
            client.request("thread/read", {"threadId": "other", "includeTurns": True})


def test_private_path_rejects_public_and_symlink_storage(ledger, tmp_path):
    public = tmp_path / "public.sqlite3"
    public.write_text("")
    with pytest.raises(ConversationError, match="inside .model-learner"):
        require_private_database(public)
    link = ledger.database.path.parent / "link.sqlite3"
    link.symlink_to(public)
    with pytest.raises(ConversationError, match="symlinks"):
        require_private_database(link)


def test_cli_metadata_import_inspection_and_replay(ledger, executable):
    runner = CliRunner()
    args = [
        "import",
        "conversation",
        SELECTED_ID,
        "--product-source",
        "codex_desktop",
        "--machine-id",
        "fixture",
        "--codex-executable",
        str(executable),
        "--database",
        str(ledger.database.path),
    ]
    first = runner.invoke(app, args)
    assert first.exit_code == 0, first.output
    report = json.loads(first.output)
    assert report["items_view"] == "notLoaded" and report["messages"] is None
    assert "PRIVATE_" not in first.output
    second = runner.invoke(app, args)
    assert second.exit_code == 0, second.output
    assert json.loads(second.output)["snapshots_duplicate"] == 1
    detail = runner.invoke(
        app,
        [
            "session",
            "show",
            report["session_id"],
            "--database",
            str(ledger.database.path),
        ],
    )
    assert detail.exit_code == 0, detail.output
    payload = json.loads(detail.output)
    assert payload["summary"]["turns"] == 3
    assert payload["summary"]["verification"] == "unknown"
    assert payload["summary"]["usage"] is None
    assert payload["timeline"][0]["payload"]["turns"][0]["native_turn_id"] == "turn-0"


def test_cli_invalid_source_reports_no_native_data(ledger, executable):
    runner = CliRunner()
    result = runner.invoke(
        app,
        [
            "import",
            "conversation",
            SELECTED_ID,
            "--product-source",
            "unsupported",
            "--machine-id",
            "fixture",
            "--codex-executable",
            str(executable),
            "--database",
            str(ledger.database.path),
        ],
    )
    assert result.exit_code == 2
    assert "PRIVATE_" not in result.output
    assert ledger.list_records(Session) == []


def test_cli_malformed_native_type_has_no_traceback_or_private_text(
    ledger, executable, monkeypatch
):
    monkeypatch.setenv("MODEL_LEARNER_FIXTURE_MODE", "malformed_item_type")
    result = CliRunner().invoke(
        app,
        [
            "import",
            "conversation",
            SELECTED_ID,
            "--product-source",
            "codex_desktop",
            "--machine-id",
            "fixture",
            "--codex-executable",
            str(executable),
            "--database",
            str(ledger.database.path),
            "--read-text",
        ],
    )
    assert result.exit_code == 2
    assert "PRIVATE_" not in result.output and "Traceback" not in result.output
    assert ledger.list_records(Event) == []
