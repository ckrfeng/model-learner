"""Operator-controlled local benchmark staging; never launch an agent."""

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from model_learner.commands.common import aware_time, repository, write_json
from model_learner.domain.models import ExecutionConfiguration, RunState
from model_learner.storage.database import StorageError

benchmark_app = typer.Typer(
    help="Prepare disposable coding tasks and import independent evidence.",
    no_args_is_help=True,
)
PROTECTED_REPOSITORY = Path(__file__).resolve().parents[3]


@benchmark_app.command("isolation-probe")
def isolation_probe() -> None:
    """Test disposable public canaries; this cannot authorize a real agent run."""
    from model_learner.benchmark.isolation import probe_macos_containment

    result = probe_macos_containment()
    write_json(result)
    if result.status != "probe_passed":
        raise typer.Exit(1)


@benchmark_app.command("offline-isolation-probe")
def offline_isolation_probe(
    image_id: Annotated[
        str | None,
        typer.Option(help="Immutable locally installed Docker image ID; never pulls."),
    ] = None,
) -> None:
    """Test a fixed offline synthetic worker; real execution stays disabled."""
    from model_learner.benchmark.offline import probe_offline_isolation

    try:
        result = probe_offline_isolation(image_id=image_id)
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(result)
    if result.status != "validated":
        raise typer.Exit(1)


@benchmark_app.command("evidence-export")
def evidence_export(
    root: Annotated[Path, typer.Argument(help="Trusted finalized benchmark root.")],
    checkpoint: Annotated[
        list[str] | None,
        typer.Option(help="Aware ISO checkpoint; repeat for multiple horizons."),
    ] = None,
    historical_cutoff: Annotated[
        str | None, typer.Option(help="Aware ISO evidence availability cutoff.")
    ] = None,
    output: Annotated[
        Path | None, typer.Option(help="New export file; existing files are refused.")
    ] = None,
) -> None:
    """Export benchmark evidence and audit checkpoint availability."""
    from model_learner.benchmark.evidence import export_benchmark_evidence

    try:
        result = export_benchmark_evidence(
            root,
            checkpoints=tuple(aware_time(value) for value in checkpoint or ()),
            historical_cutoff=(
                aware_time(historical_cutoff) if historical_cutoff else None
            ),
        )
        if output is not None:
            with output.open("x", encoding="utf-8") as stream:
                stream.write(result.model_dump_json(indent=2) + "\n")
    except ValidationError as error:
        raise typer.BadParameter("invalid benchmark evidence") from error
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(result if output is None else {"output": output})


@benchmark_app.command("evidence-import")
def evidence_import(
    path: Annotated[Path, typer.Argument(help="Benchmark evidence JSON export.")],
    root: Annotated[Path, typer.Option(help="Trusted source benchmark root.")],
    database: Annotated[Path, typer.Option(help="Initialized destination ledger.")],
) -> None:
    """Revalidate source evidence and idempotently import its observation."""
    from model_learner.benchmark.evidence import (
        BenchmarkEvidence,
        import_benchmark_evidence,
    )

    try:
        evidence = BenchmarkEvidence.model_validate_json(path.read_text())
        result = import_benchmark_evidence(repository(database), evidence, root=root)
    except ValidationError as error:
        raise typer.BadParameter("invalid benchmark evidence") from error
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(result)


@benchmark_app.command("pilot-plan")
def pilot_plan(
    configuration_a: Annotated[
        Path, typer.Option(help="Frozen arm A configuration JSON.")
    ],
    configuration_b: Annotated[
        Path, typer.Option(help="Frozen arm B configuration JSON.")
    ],
    seed: Annotated[int, typer.Option()] = 1,
) -> None:
    """Preregister 12 task pairs and checkpoints; never launch an execution."""
    from model_learner.benchmark.pilot import build_pilot_plan

    try:
        try:
            arm_a = ExecutionConfiguration.model_validate_json(
                configuration_a.read_text()
            )
            arm_b = ExecutionConfiguration.model_validate_json(
                configuration_b.read_text()
            )
        except ValidationError as error:
            raise ValueError("invalid pilot execution configuration") from error
        result = build_pilot_plan(
            configuration_a=arm_a, configuration_b=arm_b, seed=seed
        )
    except (OSError, ValueError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(result)


@benchmark_app.command("tasks")
def tasks() -> None:
    """List public, predefined coding fixtures and acceptance targets."""
    from model_learner.benchmark import list_tasks

    write_json(list_tasks())


@benchmark_app.command("prepare")
def prepare(
    task_id: Annotated[str, typer.Argument(help="Predefined fixture ID.")],
    parent: Annotated[Path, typer.Option(help="Disposable parent outside this repo.")],
    configuration_file: Annotated[Path, typer.Option(help="Configuration JSON.")],
    isolation_mechanism: Annotated[
        str, typer.Option(help="Operator's OS/container isolation mechanism.")
    ],
    dataset_id: Annotated[str, typer.Option()] = "local-coding",
    dataset_version: Annotated[str, typer.Option()] = "1",
    execution_origin: Annotated[
        str, typer.Option(help="real or fixture; never combined in one dataset.")
    ] = "real",
) -> None:
    """Stage a task; the operator separately chooses and runs any paid agent."""
    from model_learner.benchmark import prepare_benchmark

    try:
        try:
            configuration = ExecutionConfiguration.model_validate_json(
                configuration_file.read_text()
            )
        except ValidationError as error:
            raise ValueError("invalid execution configuration") from error
        result = prepare_benchmark(
            parent=parent,
            task_id=task_id,
            configuration=configuration,
            protected_repository=PROTECTED_REPOSITORY,
            dataset_id=dataset_id,
            dataset_version=dataset_version,
            execution_origin=execution_origin,
            isolation_mechanism=isolation_mechanism,
        )
    except ValidationError as error:
        raise typer.BadParameter("invalid benchmark declaration") from error
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(result)


@benchmark_app.command("show")
def show(root: Annotated[Path, typer.Argument()]) -> None:
    """Inspect the predeclared task and operator-control paths."""
    from model_learner.benchmark import load_benchmark

    try:
        result = load_benchmark(root)
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter("invalid benchmark workspace") from error
    write_json(result)


@benchmark_app.command("snapshot")
def snapshot(root: Annotated[Path, typer.Argument()]) -> None:
    """Freeze candidate bytes after the operator stops the agent."""
    from model_learner.benchmark import snapshot_candidate

    try:
        artifact = snapshot_candidate(root)
    except ValidationError as error:
        raise typer.BadParameter("invalid benchmark manifest") from error
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json({"artifact": artifact})


@benchmark_app.command("finalize")
def finalize(
    root: Annotated[Path, typer.Argument()],
    started_at: Annotated[str, typer.Option(help="ISO operator run start.")],
    ended_at: Annotated[str, typer.Option(help="ISO operator run stop.")],
    state: Annotated[RunState, typer.Option()] = RunState.FINISHED,
    capture: Annotated[Path | None, typer.Option()] = None,
    machine_id: Annotated[str, typer.Option()] = "local-benchmark",
    test_completed: Annotated[bool | None, typer.Option()] = None,
    test_exit_code: Annotated[int | None, typer.Option(min=0, max=255)] = None,
    test_generated_at: Annotated[str | None, typer.Option()] = None,
    isolation_confirmed: Annotated[
        bool,
        typer.Option(help="Record an operator declaration; cannot enable real runs."),
    ] = False,
) -> None:
    """Record independent JUnit evidence, telemetry and unknown outcomes."""
    from model_learner.benchmark import finalize_benchmark

    try:
        result = finalize_benchmark(
            root,
            started_at=aware_time(started_at),
            ended_at=aware_time(ended_at),
            state=state,
            capture=capture,
            machine_id=machine_id,
            test_completed=test_completed,
            test_exit_code=test_exit_code,
            test_generated_at=aware_time(test_generated_at)
            if test_generated_at is not None
            else None,
            isolation_confirmed=isolation_confirmed,
        )
    except ValidationError as error:
        raise typer.BadParameter(
            "invalid benchmark manifest or evidence receipt"
        ) from error
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(result)


@benchmark_app.command("cleanup")
def cleanup(root: Annotated[Path, typer.Argument()]) -> None:
    """Remove the validated disposable tree after exporting wanted results."""
    from model_learner.benchmark import cleanup_benchmark

    try:
        cleanup_benchmark(root)
    except ValidationError as error:
        raise typer.BadParameter("invalid benchmark manifest") from error
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json({"removed": root})
