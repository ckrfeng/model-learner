"""Explicit opt-in, stdout-only CPU semantic demonstration."""

import json
import sys
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from pydantic import ValidationError

from model_learner.commands.common import write_json
from model_learner.understanding.conversation_state import (
    Conversation,
    analyze,
    from_read,
    render,
)


def conversation_state(
    text_opt_in: Annotated[
        bool,
        typer.Option(help="Authorize processing selected conversation text in memory."),
    ] = False,
    emit_text: Annotated[
        bool,
        typer.Option(
            help="Explicitly include evidence text and check identifiers in stdout."
        ),
    ] = False,
    conversation_id: Annotated[
        UUID | None,
        typer.Option(
            help="One selected existing conversation; otherwise read JSON from stdin."
        ),
    ] = None,
    product_source: Annotated[str | None, typer.Option()] = None,
    machine_id: Annotated[str | None, typer.Option()] = None,
    codex_executable: Annotated[Path | None, typer.Option()] = None,
) -> None:
    """Conversation -> CPU rules -> evidence-linked evolving timeline.

    No database, output file, ingestion or automatic semantic-state retention.
    Live access uses the existing bounded importer, including full-item retrieval
    before non-message content is discarded. stdin checks are caller attestations.
    """
    if not text_opt_in:
        raise typer.BadParameter("processing requires --text-opt-in")
    try:
        if conversation_id is not None:
            if product_source is None or machine_id is None:
                raise ValueError("selected reads require product source and machine ID")
            from model_learner.adapters.app_server import AppServerClient
            from model_learner.adapters.conversations import read_conversation

            with AppServerClient(
                str(conversation_id), executable=codex_executable or "codex"
            ) as client:
                read = read_conversation(
                    client,
                    product_source=product_source,
                    machine_id=machine_id,
                    read_text=True,
                )
            conversation = from_read(read)
        else:
            if any(
                v is not None for v in (product_source, machine_id, codex_executable)
            ):
                raise ValueError(
                    "live source options require a selected conversation ID"
                )
            raw = sys.stdin.buffer.read(65537)
            if len(raw) > 65536:
                raise ValueError("stdin byte limit exceeded")
            conversation = Conversation.model_validate_json(raw)
        write_json(render(analyze(conversation), emit_text=emit_text))
    except (ValidationError, ValueError, OSError):
        # Native text, selected IDs and invalid check fields are never echoed.
        raise typer.BadParameter(
            "invalid, unsupported or unavailable opted-in conversation"
        ) from None


def conversation_eval(
    fixture: Annotated[
        Path, typer.Argument(help="Authored sanitized evaluation JSON.")
    ],
) -> None:
    """Compare keyword/rule/NB baselines on manually specified authored labels."""
    from model_learner.understanding.conversation_evaluation import evaluate

    try:
        if fixture.stat().st_size > 262144:
            raise ValueError("fixture size limit exceeded")
        result = evaluate(json.loads(fixture.read_text()))
    except (OSError, ValueError, KeyError, TypeError):
        raise typer.BadParameter("invalid authored evaluation fixture") from None
    write_json(result)
