"""Validated JSONL import/export for canonical primary records."""

from __future__ import annotations

import json
from pathlib import Path

from pydantic import BaseModel, ValidationError

from model_learner.domain.models import (
    Attempt,
    Event,
    Observation,
    Outcome,
    Project,
    Run,
    Session,
    Task,
    Verification,
)
from model_learner.storage.database import Repository, StorageError

RECORD_TYPES: dict[str, type[BaseModel]] = {
    "task": Task,
    "project": Project,
    "session": Session,
    "run": Run,
    "attempt": Attempt,
    "event": Event,
    "verification": Verification,
    "outcome": Outcome,
    "observation": Observation,
}


class JsonlValidationError(ValueError):
    """A JSONL row failed its envelope or versioned domain contract."""


def export_jsonl(
    repository: Repository,
    record_type: type[BaseModel],
    destination: Path,
    *,
    source_kind: str | None = None,
) -> int:
    """Write records as envelopes that retain their type and canonical identifiers."""
    records = repository.list_records(record_type, source_kind=source_kind)
    with destination.open("w", encoding="utf-8") as stream:
        for record in records:
            envelope = {
                "record_type": record_type.__name__,
                "record": record.model_dump(mode="json"),
            }
            stream.write(json.dumps(envelope, sort_keys=True, separators=(",", ":")))
            stream.write("\n")
    return len(records)


def import_jsonl(repository: Repository, source: Path) -> int:
    """Validate each row before asking the repository to preserve relationships."""
    imported = 0
    with source.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                envelope = json.loads(line)
                record_name = envelope["record_type"]
                record_type = RECORD_TYPES[record_name.lower()]
                record = record_type.model_validate(envelope["record"])
            except (
                KeyError,
                TypeError,
                json.JSONDecodeError,
                ValidationError,
            ) as error:
                raise JsonlValidationError(f"line {line_number}: {error}") from error
            try:
                repository.import_record(record)
            except (StorageError, ValueError) as error:
                raise JsonlValidationError(f"line {line_number}: {error}") from error
            imported += 1
    return imported


def validate_jsonl(source: Path) -> int:
    """Validate JSONL contracts without changing a database."""
    valid = 0
    with source.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                envelope = json.loads(line)
                record_type = RECORD_TYPES[envelope["record_type"].lower()]
                record_type.model_validate(envelope["record"])
            except (
                KeyError,
                TypeError,
                json.JSONDecodeError,
                ValidationError,
            ) as error:
                raise JsonlValidationError(f"line {line_number}: {error}") from error
            valid += 1
    return valid
