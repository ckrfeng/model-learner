"""Explicit local run, verification, and observation workflow commands."""

from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer

from model_learner.commands.common import (
    DEFAULT_DATABASE,
    aware_time,
    repository,
    write_json,
)
from model_learner.domain.models import (
    Attempt,
    DatasetReference,
    ExecutionConfiguration,
    Observation,
    Outcome,
    OutcomeStatus,
    Run,
    RunSessionLink,
    RunState,
    Verification,
)
from model_learner.observations import build_real_observation, data_quality_report
from model_learner.runs import create_bounded_run, declare_attempt
from model_learner.storage.database import StorageError
from model_learner.verification import (
    assess_human,
    assess_run,
    file_sha256,
    verify_file,
)

run_app = typer.Typer(
    help="Declare bounded executions without controlling agents.", no_args_is_help=True
)
verify_app = typer.Typer(
    help="Read-only verification against declared acceptance criteria.",
    no_args_is_help=True,
)
outcome_app = typer.Typer(
    help="Append independent outcome assessments.", no_args_is_help=True
)
observations_app = typer.Typer(
    help="Build real observations and inspect data quality.", no_args_is_help=True
)


@run_app.command("create")
def create_run(
    task_id: Annotated[UUID, typer.Argument()],
    session_id: Annotated[UUID, typer.Option()],
    started_at: Annotated[
        str, typer.Option(help="Explicit ISO timestamp with timezone.")
    ],
    ended_at: Annotated[
        str, typer.Option(help="Explicit end bound, not inferred completion.")
    ],
    state: Annotated[RunState, typer.Option()] = RunState.FINISHED,
    artifact: Annotated[
        Path | None, typer.Option(help="Read-only final file snapshot.")
    ] = None,
    artifact_fingerprint: Annotated[
        str | None, typer.Option(help="sha256:<64 hex digits>.")
    ] = None,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Associate a captured session to a declared task and bounded run."""
    try:
        if artifact is not None and artifact_fingerprint is not None:
            raise ValueError("supply only one artifact or artifact fingerprint")
        fingerprint = (
            f"sha256:{file_sha256(artifact)}" if artifact else artifact_fingerprint
        )
        write_json(
            create_bounded_run(
                repository(database),
                task_id=task_id,
                session_id=session_id,
                started_at=aware_time(started_at),
                ended_at=aware_time(ended_at),
                state=state,
                final_artifact_fingerprint=fingerprint,
            )
        )
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error


@run_app.command("attach-session")
def attach_run_session(
    run_id: Annotated[UUID, typer.Argument()],
    session_id: Annotated[UUID, typer.Argument()],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Attach an additional session already associated with the run's task."""
    try:
        write_json(
            repository(database).associate_run_session(
                RunSessionLink(run_id=run_id, session_id=session_id)
            )
        )
    except StorageError as error:
        raise typer.BadParameter(str(error)) from error


@run_app.command("attempt")
def record_attempt(
    run_id: Annotated[UUID, typer.Argument()],
    configuration_file: Annotated[
        Path, typer.Option(help="Exact ExecutionConfiguration JSON.")
    ],
    started_at: Annotated[str, typer.Option()],
    ended_at: Annotated[str, typer.Option()],
    declaration_source: Annotated[
        str, typer.Option(help="Source of manual configuration assertion.")
    ] = "human",
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Declare one configuration segment with explicit bounds and provenance."""
    try:
        write_json(
            declare_attempt(
                repository(database),
                run_id=run_id,
                configuration=ExecutionConfiguration.model_validate_json(
                    configuration_file.read_text()
                ),
                started_at=aware_time(started_at),
                ended_at=aware_time(ended_at),
                declaration_source=declaration_source,
            )
        )
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error


@run_app.command("show")
def show_run(
    run_id: Annotated[UUID, typer.Argument()],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Inspect execution state separately from verification and assessment."""
    ledger = repository(database)
    run = ledger.get(Run, run_id)
    if run is None:
        raise typer.BadParameter("unknown run")
    write_json(
        {
            "run": run,
            "session_links": ledger.list_run_session_links(run_id),
            "attempts": [r for r in ledger.list_records(Attempt) if r.run_id == run_id],
            "verifications": [
                r for r in ledger.list_records(Verification) if r.run_id == run_id
            ],
            "outcomes": [r for r in ledger.list_records(Outcome) if r.run_id == run_id],
        }
    )


@verify_app.command("file")
def verify_artifact(
    run_id: Annotated[UUID, typer.Argument()],
    artifact: Annotated[Path, typer.Argument()],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Check a file SHA-256 against the criterion declared when creating its task."""
    try:
        write_json(verify_file(repository(database), run_id=run_id, artifact=artifact))
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error


@outcome_app.command("assess")
def assess_outcome(
    run_id: Annotated[UUID, typer.Argument()],
    verification_id: Annotated[UUID | None, typer.Option()] = None,
    supersedes: Annotated[
        UUID | None,
        typer.Option(help="Prior assessment ID; evidence stays append-only."),
    ] = None,
    note: Annotated[str | None, typer.Option()] = None,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Assess retained deterministic evidence; absent evidence yields unknown."""
    try:
        write_json(
            assess_run(
                repository(database),
                run_id=run_id,
                verification_id=verification_id,
                supersedes_outcome_id=supersedes,
                note=note,
            )
        )
    except (ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error


@outcome_app.command("human")
def human_outcome(
    run_id: Annotated[UUID, typer.Argument()],
    status: Annotated[
        OutcomeStatus, typer.Option(help="Explicit unverified human assessment.")
    ],
    supersedes: Annotated[UUID | None, typer.Option()] = None,
    note: Annotated[str | None, typer.Option()] = None,
    censor_reason: Annotated[
        str | None, typer.Option(help="Required for a censored assessment.")
    ] = None,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Record a human label separately from deterministic verification."""
    try:
        write_json(
            assess_human(
                repository(database),
                run_id=run_id,
                status=status,
                supersedes_outcome_id=supersedes,
                note=note,
                censor_reason=censor_reason,
            )
        )
    except (ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error


@observations_app.command("build")
def build_observation(
    run_id: Annotated[UUID, typer.Argument()],
    outcome_id: Annotated[UUID, typer.Option()],
    dataset_id: Annotated[str, typer.Option()],
    dataset_version: Annotated[str, typer.Option()],
    task_group: Annotated[
        str | None, typer.Option(help="Manual group override; no classification.")
    ] = None,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Persist an idempotent real observation with evidence and attribution."""
    try:
        write_json(
            build_real_observation(
                repository(database),
                run_id=run_id,
                outcome_id=outcome_id,
                dataset=DatasetReference(
                    source_kind="real",
                    dataset_id=dataset_id,
                    dataset_version=dataset_version,
                ),
                task_group=task_group,
            )
        )
    except (ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error


@observations_app.command("quality")
def observation_quality(
    dataset_id: Annotated[str, typer.Option()],
    dataset_version: Annotated[str, typer.Option()],
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Report real dataset counts and missingness with explicit denominators."""
    dataset = DatasetReference(
        source_kind="real", dataset_id=dataset_id, dataset_version=dataset_version
    )
    rows = repository(database).list_records(
        Observation, source_kind="real", dataset_id=dataset_id
    )
    write_json(
        {
            "dataset": dataset,
            "quality": data_quality_report([r for r in rows if r.dataset == dataset]),
        }
    )
