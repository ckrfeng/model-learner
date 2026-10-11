"""Declared-description suggestions preserve the ledger and unknown semantics."""

import json
import os
import socket
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.domain.models import AcceptanceSpec, Session, Task, TaskSessionLink
from model_learner.representation.potion import MODEL_REVISION
from model_learner.storage.database import Database, Repository

START = datetime(2026, 1, 1, tzinfo=UTC)


def setup(tmp_path):
    path = tmp_path / "ledger.sqlite3"
    database = Database(path)
    database.initialize()
    ledger = Repository(database)
    tasks = []
    for index, description in enumerate(
        (
            "Fix concurrent session updates",
            "Fix concurrent session updates",
            "future-only",
        )
    ):
        tasks.append(
            ledger.create_task(
                Task(
                    description=description,
                    created_at=START + timedelta(seconds=index),
                    acceptance_spec=AcceptanceSpec(identifier="fixture", version="1"),
                    metadata={"private_transcript": "NEVER_INCLUDE_THIS_PAYLOAD"},
                )
            )
        )
    session = ledger.create_session(Session(source="fixture"))
    for task in tasks[:2]:
        ledger.associate_session(
            TaskSessionLink(task_id=task.task_id, session_id=session.session_id)
        )
    return path, ledger, tasks


def invoke(path, task_id, *extra):
    return CliRunner().invoke(
        app, ["task", "similar", str(task_id), "--database", str(path), *extra]
    )


def test_ranked_distinct_task_is_never_a_continuation_or_ledger_write(tmp_path):
    path, ledger, tasks = setup(tmp_path)
    before = (ledger.list_tasks(), ledger.list_task_session_links(tasks[1].task_id))
    for backend in ("text", "tfidf"):
        result = invoke(path, tasks[1].task_id, "--backend", backend)
        assert result.exit_code == 0, result.output
        data = json.loads(result.output)
        assert data["related_tasks"] == [
            {
                "task_id": str(tasks[0].task_id),
                "similarity_score": 1.0,
                "provenance": "inferred_description_relatedness",
                "continuation": "not_established_by_similarity",
            }
        ]
        assert data["exclusions"]["created_after_query"] == 1
        assert data["provenance"]["source_counts"]["declared"] == 1
        assert "NEVER_INCLUDE_THIS_PAYLOAD" not in result.output
        assert tasks[0].description not in result.output
    assert before == (
        ledger.list_tasks(),
        ledger.list_task_session_links(tasks[1].task_id),
    )


def test_unavailable_potion_is_explicit_and_lexical_command_still_works(tmp_path):
    path, _, tasks = setup(tmp_path)
    result = invoke(
        path,
        tasks[1].task_id,
        "--backend",
        "potion",
        "--model-path",
        str(tmp_path),
        "--model-revision",
        MODEL_REVISION,
        "--model-sha256",
        "0" * 64,
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "semantic_unavailable"
    assert data["related_tasks"] == []
    assert data["provenance"]["revision"] == MODEL_REVISION
    assert invoke(path, tasks[1].task_id).exit_code == 0


def test_empty_unknown_and_invalid_options(tmp_path):
    path, _, tasks = setup(tmp_path)
    first = invoke(path, tasks[0].task_id)
    assert first.exit_code == 0
    assert json.loads(first.output)["status"] == "empty"
    for extra in (
        ("--backend", "potion"),
        ("--model-sha256", "0" * 64),
        ("--limit", "0"),
    ):
        assert invoke(path, tasks[1].task_id, *extra).exit_code == 2
    assert invoke(path, uuid4()).exit_code == 2


def test_unsupported_historical_descriptions_are_counted(tmp_path):
    path, ledger, tasks = setup(tmp_path)
    for description in (" " * 3, "x" * 4097):
        ledger.create_task(
            Task(
                description=description,
                created_at=START,
                acceptance_spec=AcceptanceSpec(identifier="fixture", version="1"),
            )
        )
    result = invoke(path, tasks[1].task_id)
    assert result.exit_code == 0
    assert json.loads(result.output)["exclusions"]["unsupported_description"] == 2


def test_invalid_ledger_record_error_does_not_echo_private_content(tmp_path):
    path, ledger, tasks = setup(tmp_path)
    corrupted = tasks[0].model_dump(mode="json")
    corrupted["description"] = {"private": "PRIVATE_MALFORMED_PAYLOAD"}
    with ledger.database.connection() as connection:
        connection.execute(
            "UPDATE tasks SET data = ? WHERE task_id = ?",
            (json.dumps(corrupted), str(tasks[0].task_id)),
        )
    result = invoke(path, tasks[1].task_id)
    assert result.exit_code == 2
    assert "invalid declared task records" in result.output
    assert "PRIVATE_MALFORMED_PAYLOAD" not in result.output


@pytest.mark.skipif(
    not os.environ.get("MODEL_LEARNER_TEST_POTION_PATH"),
    reason="explicit approved local Potion bundle required",
)
def test_actual_potion_retrieval_is_pinned_local_and_retains_task_ids(
    tmp_path, monkeypatch
):
    def deny(*args, **kwargs):
        raise AssertionError("local retrieval attempted a network connection")

    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    path, _, tasks = setup(tmp_path)
    result = invoke(
        path,
        tasks[1].task_id,
        "--backend",
        "potion",
        "--model-path",
        os.environ["MODEL_LEARNER_TEST_POTION_PATH"],
        "--model-revision",
        MODEL_REVISION,
        "--model-sha256",
        "930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2",
    )
    assert result.exit_code == 0, result.output
    data = json.loads(result.output)
    assert data["status"] == "ok"
    assert data["related_tasks"][0]["task_id"] == str(tasks[0].task_id)
    assert data["provenance"]["encoder"]["revision"] == MODEL_REVISION
    assert data["provenance"]["encoder"]["device"] == "cpu"
