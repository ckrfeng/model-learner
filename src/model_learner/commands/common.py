"""Shared presentation and local-ledger helpers for commands."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
from uuid import UUID

import typer
from pydantic import BaseModel

from model_learner.storage.database import Database, Repository, StorageError

DEFAULT_DATABASE = Path(".model-learner/model-learner.sqlite3")


def repository(path: Path) -> Repository:
    """Require an initialized ledger; read commands never initialize it."""
    try:
        return Repository(Database(path))
    except StorageError as error:
        raise typer.BadParameter(
            f"{error}. Run `model-learner init --database {path}` first."
        ) from error


def _json_default(value: Any) -> Any:
    if isinstance(value, BaseModel):
        return value.model_dump(mode="json")
    if is_dataclass(value) and not isinstance(value, type):
        return asdict(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, (UUID, Path)):
        return str(value)
    if isinstance(value, Enum):
        return value.value
    raise TypeError(f"cannot serialize {type(value).__name__}")


def write_json(value: Any) -> None:
    typer.echo(json.dumps(value, default=_json_default, indent=2, allow_nan=False))


def aware_time(value: str) -> datetime:
    """Parse a cutoff without guessing the user's timezone."""
    try:
        timestamp = datetime.fromisoformat(value)
    except ValueError as error:
        raise typer.BadParameter("time must be ISO 8601 with a timezone") from error
    if timestamp.tzinfo is None or timestamp.utcoffset() is None:
        raise typer.BadParameter("time must include a timezone")
    return timestamp
