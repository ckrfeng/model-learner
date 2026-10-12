"""Read-only Codex stream capture, import, and retained timeline inspection."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer

from model_learner.adapters.app_server import AppServerClient, ConversationError
from model_learner.adapters.codex import (
    capture_codex_stream,
    ingest_codex_capture,
    summarize_session,
)
from model_learner.adapters.conversations import (
    SOURCE as CONVERSATION_SOURCE,
)
from model_learner.adapters.conversations import (
    ingest_conversation,
    read_conversation,
    require_private_database,
    summarize_conversation,
)
from model_learner.commands.common import DEFAULT_DATABASE, repository, write_json
from model_learner.domain.models import Event, Session
from model_learner.storage.database import StorageError

capture_app = typer.Typer(
    help="Capture an existing agent stream.", no_args_is_help=True
)
import_app = typer.Typer(help="Import a captured agent stream.", no_args_is_help=True)


@import_app.command("conversation")
def import_conversation(
    conversation_id: Annotated[
        str, typer.Argument(help="Explicit selected native conversation UUID.")
    ],
    product_source: Annotated[
        str,
        typer.Option(
            help="codex_desktop or chatgpt_work_local; verified against originator."
        ),
    ],
    machine_id: Annotated[
        str, typer.Option(help="Explicit stable local machine/scope identity.")
    ],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
    codex_executable: Annotated[
        str, typer.Option(help="Installed Codex executable.")
    ] = "codex",
    read_text: Annotated[
        bool,
        typer.Option(
            help="Receive full items; discard other content. Text stays in memory."
        ),
    ] = False,
    retain_text: Annotated[
        bool,
        typer.Option(
            help="Explicit local text storage opt-in; implies full-item retrieval."
        ),
    ] = False,
) -> None:
    """Import one bounded conversation; defaults to server-side item omission.

    Full view has no server-side attachment/tool-output filter. Text retention is
    restricted to the workspace's Git-ignored .model-learner database.
    """
    try:
        require_private_database(database)
        ledger = repository(database)
        with AppServerClient(conversation_id, executable=codex_executable) as client:
            read = read_conversation(
                client,
                product_source=product_source,
                machine_id=machine_id,
                read_text=read_text or retain_text,
            )
        if client.exit_code != 0:
            raise ConversationError("App Server did not shut down cleanly")
        report = ingest_conversation(ledger, read, retain_text=retain_text)
    except Exception:
        # Never render upstream exceptions, which can contain native payloads.
        raise typer.BadParameter(
            "conversation import rejected; check source, protocol bounds "
            "and private storage"
        ) from None
    write_json(report)


@capture_app.command("codex")
def capture_codex(
    destination: Annotated[Path, typer.Argument(help="New capture JSONL file.")],
    source_version: Annotated[str, typer.Option(help="Installed Codex CLI version.")],
    retain_raw: Annotated[
        bool, typer.Option(help="Opt in to retaining private native payloads locally.")
    ] = False,
) -> None:
    """Read Codex exec --json from stdin; timestamp receipt without launching Codex."""
    try:
        # Never overwrite the source evidence or an earlier capture.
        with destination.open("x", encoding="utf-8") as output:
            report = capture_codex_stream(
                sys.stdin, output, source_version=source_version, retain_raw=retain_raw
            )
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(report)
    if report.diagnostics:
        raise typer.Exit(code=1)


@import_app.command("codex")
def import_codex(
    source: Annotated[Path, typer.Argument(help="Timestamped Codex capture JSONL.")],
    machine_id: Annotated[str, typer.Option(help="Explicit local machine identity.")],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
    source_version: Annotated[str | None, typer.Option()] = None,
    retain_raw: Annotated[
        bool, typer.Option(help="Opt in to storing full native payloads in the ledger.")
    ] = False,
) -> None:
    """Import captured metadata; session completion never creates outcome labels."""
    try:
        report = ingest_codex_capture(
            repository(database),
            source,
            machine_id=machine_id,
            source_version=source_version,
            retain_raw=retain_raw,
        )
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(report)
    if report.diagnostics:
        raise typer.Exit(code=1)


def list_sessions(database: Path) -> None:
    write_json(repository(database).list_records(Session))


def _timeline_key(event: Event) -> tuple:
    """Use native sequence only when arbitrary ledger metadata is well typed."""
    capture = event.payload.get("capture_id")
    sequence = event.payload.get("sequence")
    return (
        event.observed_at,
        capture if isinstance(capture, str) else "",
        sequence if type(sequence) is int else 0,
        str(event.event_id),
    )


def show_session(identifier: UUID, database: Path) -> None:
    ledger = repository(database)
    session = ledger.get(Session, identifier)
    if session is None:
        raise typer.BadParameter(f"no session with ID {identifier}")
    events = sorted(
        (e for e in ledger.list_records(Event) if e.session_id == identifier),
        key=_timeline_key,
    )
    write_json(
        {
            "session": session,
            "summary": (
                summarize_conversation(session, events)
                if session.source == CONVERSATION_SOURCE
                else summarize_session(session, events)
            ),
            "timeline": [
                {
                    "event_id": e.event_id,
                    "native_event_id": e.native_event_id,
                    "observed_at": e.observed_at,
                    "provenance": e.provenance,
                    "source": e.source,
                    "payload": e.payload,
                    "event_type": e.event_type,
                }
                for e in events
            ],
        }
    )
