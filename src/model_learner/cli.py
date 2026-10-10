"""Command-line entry point for the local Model Learner evidence ledger."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from pydantic import BaseModel

from model_learner import __version__
from model_learner.commands.learning import learn_app, sim_app
from model_learner.commands.observation import (
    capture_app,
    import_app,
)
from model_learner.commands.observation import (
    list_sessions as inspect_sessions,
)
from model_learner.commands.observation import (
    show_session as inspect_session,
)
from model_learner.commands.tasks import (
    observations_app,
    outcome_app,
    run_app,
    verify_app,
)
from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    Event,
    Observation,
    Outcome,
    Project,
    Run,
    Session,
    Task,
    TaskSessionLink,
    Verification,
)
from model_learner.storage.database import Database, Repository, StorageError
from model_learner.storage.jsonl import (
    JsonlValidationError,
    export_jsonl,
    import_jsonl,
    validate_jsonl,
)
from model_learner.verification import digest_criterion

DEFAULT_DATABASE = Path(".model-learner/model-learner.sqlite3")

app = typer.Typer(
    name="model-learner",
    help="Model Learner: local-first AI-model utility from verified outcomes.",
    no_args_is_help=True,
    invoke_without_command=True,
    add_completion=False,
)
task_app = typer.Typer(help="Create and inspect declared tasks.", no_args_is_help=True)
session_app = typer.Typer(
    help="Register and inspect native agent sessions.", no_args_is_help=True
)
records_app = typer.Typer(
    help="Inspect persisted evidence records.", no_args_is_help=True
)
app.add_typer(task_app, name="task")
app.add_typer(session_app, name="session")
app.add_typer(records_app, name="records")
app.add_typer(capture_app, name="capture")
app.add_typer(import_app, name="import")
app.add_typer(sim_app, name="sim")
app.add_typer(learn_app, name="learn")
app.add_typer(run_app, name="run")
app.add_typer(verify_app, name="verify")
app.add_typer(outcome_app, name="outcome")
app.add_typer(observations_app, name="observations")

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


def _show_version(value: bool) -> None:
    if value:
        typer.echo(f"model-learner {__version__}")
        raise typer.Exit()


def _repository(path: Path) -> Repository:
    try:
        return Repository(Database(path))
    except StorageError as error:
        raise typer.BadParameter(
            f"{error}. Run `model-learner init --database {path}` first."
        ) from error


def _write_record(record: BaseModel) -> None:
    typer.echo(record.model_dump_json(indent=2))


def _write_records(records: list[BaseModel]) -> None:
    typer.echo(
        json.dumps([record.model_dump(mode="json") for record in records], indent=2)
    )


@app.callback()
def main(
    version: Annotated[
        bool,
        typer.Option(
            "--version",
            callback=_show_version,
            is_eager=True,
            help="Show the version and exit.",
        ),
    ] = False,
) -> None:
    """Capture evidence and estimate verified outcome probabilities locally."""


@app.command()
def init(
    database: Annotated[
        Path,
        typer.Option("--database", "-d", help="SQLite database path."),
    ] = DEFAULT_DATABASE,
) -> None:
    """Initialize a local SQLite database and apply all migrations."""
    Database(database).initialize()
    typer.echo(f"initialized {database}")


@task_app.command("create")
def create_task(
    description: Annotated[str, typer.Argument(help="Declared task objective.")],
    acceptance_id: Annotated[str, typer.Option(help="Acceptance specification ID.")],
    acceptance_version: Annotated[
        str, typer.Option(help="Acceptance specification version.")
    ],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
    workspace_id: Annotated[str | None, typer.Option()] = None,
    task_group: Annotated[str | None, typer.Option()] = None,
    acceptance_description: Annotated[str | None, typer.Option()] = None,
    expected_sha256: Annotated[
        str | None,
        typer.Option(
            help="Declare exact expected file SHA-256 for read-only verification."
        ),
    ] = None,
) -> None:
    """Create a task; it is not automatically attached to any session."""
    try:
        metadata = (
            {"file_digest_verifier": digest_criterion(expected_sha256)}
            if expected_sha256
            else {}
        )
    except ValueError as error:
        raise typer.BadParameter(str(error)) from error
    task = Task(
        description=description,
        acceptance_spec=AcceptanceSpec(
            identifier=acceptance_id,
            version=acceptance_version,
            description=acceptance_description,
        ),
        workspace_id=workspace_id,
        task_group=task_group,
        metadata=metadata,
    )
    _write_record(_repository(database).create_task(task))


@task_app.command("list")
def list_tasks(
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """List declared tasks in creation order."""
    _write_records(_repository(database).list_tasks())


@task_app.command("attach-session")
def attach_session(
    task_id: Annotated[UUID, typer.Argument()],
    session_id: Annotated[UUID, typer.Argument()],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
    relationship: Annotated[str, typer.Option()] = "related",
    note: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Explicitly relate a native session to a task without claiming completion."""
    link = TaskSessionLink(
        task_id=task_id,
        session_id=session_id,
        relationship=relationship,
        note=note,
    )
    try:
        _write_record(_repository(database).associate_session(link))
    except StorageError as error:
        raise typer.BadParameter(str(error)) from error


@session_app.command("register")
def register_session(
    source: Annotated[str, typer.Option(help="Native session source or adapter.")],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
    native_session_id: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Register a native session independently of any task."""
    _write_record(
        _repository(database).create_session(
            Session(source=source, native_session_id=native_session_id)
        )
    )


@records_app.command("show")
def show_record(
    record_type: Annotated[
        str, typer.Argument(help="One of: " + ", ".join(RECORD_TYPES))
    ],
    identifier: Annotated[UUID, typer.Argument()],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Show one canonical record, including null measurements and evidence links."""
    try:
        model_type = RECORD_TYPES[record_type]
    except KeyError as error:
        raise typer.BadParameter(f"unknown record type: {record_type}") from error
    record = _repository(database).get(model_type, identifier)
    if record is None:
        raise typer.BadParameter(f"no {record_type} with ID {identifier}")
    _write_record(record)


@app.command("sessions")
def sessions(
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """List retained native sessions, independently of declared tasks."""
    inspect_sessions(database)


@session_app.command("show")
def session_detail(
    identifier: Annotated[UUID, typer.Argument(help="Local session UUID.")],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Inspect retained observations, metadata coverage, and receipt timeline."""
    inspect_session(identifier, database)


@records_app.command("export")
def export_records(
    record_type: Annotated[
        str, typer.Argument(help="One of: " + ", ".join(RECORD_TYPES))
    ],
    destination: Annotated[Path, typer.Argument(help="JSONL destination path.")],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
    source_kind: Annotated[
        str | None, typer.Option(help="Required for observations.")
    ] = None,
) -> None:
    """Export one validated record type as JSONL."""
    try:
        model_type = RECORD_TYPES[record_type]
        count = export_jsonl(
            _repository(database), model_type, destination, source_kind=source_kind
        )
    except (KeyError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"exported {count} {record_type} records to {destination}")


@records_app.command("validate")
def validate_records(
    source: Annotated[Path, typer.Argument(help="JSONL file to validate.")],
) -> None:
    """Validate record schemas in a JSONL file without writing a database."""
    try:
        count = validate_jsonl(source)
    except (OSError, JsonlValidationError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"validated {count} records")


@records_app.command("import")
def import_records(
    source: Annotated[Path, typer.Argument(help="JSONL file to import.")],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Import validated records while enforcing persistence relationships."""
    try:
        count = import_jsonl(_repository(database), source)
    except (OSError, JsonlValidationError) as error:
        raise typer.BadParameter(str(error)) from error
    typer.echo(f"imported {count} records")
