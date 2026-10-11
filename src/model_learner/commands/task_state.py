"""Portable, chronological task-state evaluation; no agent execution."""

import json
from pathlib import Path
from typing import Annotated

import typer
from pydantic import TypeAdapter, ValidationError

from model_learner.commands.common import aware_time, write_json
from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    DataSourceKind,
    ResourceBudget,
)


def state_eval(
    input_file: Annotated[
        Path, typer.Option(help="JSON array of TaskStateExample v1.")
    ],
    source_kind: Annotated[DataSourceKind, typer.Option()],
    dataset_id: Annotated[str, typer.Option()],
    dataset_version: Annotated[str, typer.Option()],
    acceptance_id: Annotated[str, typer.Option()],
    acceptance_version: Annotated[str, typer.Option()],
    train_until: Annotated[str, typer.Option(help="ISO fit cutoff with timezone.")],
    evaluation_at: Annotated[str, typer.Option(help="ISO score cutoff with timezone.")],
    checkpoint_offset_seconds: Annotated[float, typer.Option(min=0)] = 30,
    budget_file: Annotated[Path | None, typer.Option()] = None,
    min_training: Annotated[int, typer.Option(min=2)] = 30,
    min_scored: Annotated[int, typer.Option(min=2)] = 20,
    bootstrap_replicates: Annotated[int, typer.Option(min=100)] = 300,
    seed: Annotated[int, typer.Option()] = 1,
) -> None:
    """Compare A/B/C and feature ablations on identical frozen cutoffs."""
    from model_learner.learn.task_state import TaskStateExample, evaluate_task_state

    try:
        try:
            examples = TypeAdapter(list[TaskStateExample]).validate_json(
                input_file.read_text()
            )
            budget = (
                ResourceBudget.model_validate_json(budget_file.read_text())
                if budget_file is not None
                else None
            )
        except ValidationError as error:
            raise ValueError("invalid task-state input or resource budget") from error
        result = evaluate_task_state(
            examples,
            dataset=DatasetReference(
                source_kind=source_kind,
                dataset_id=dataset_id,
                dataset_version=dataset_version,
            ),
            acceptance_spec=AcceptanceSpec(
                identifier=acceptance_id, version=acceptance_version
            ),
            train_until=aware_time(train_until),
            evaluation_at=aware_time(evaluation_at),
            checkpoint_offset_seconds=checkpoint_offset_seconds,
            resource_budget=budget,
            min_training=min_training,
            min_scored=min_scored,
            bootstrap_replicates=bootstrap_replicates,
            seed=seed,
        )
    except (OSError, ValueError, ArithmeticError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(result)


def write_examples(examples: list, destination: Path) -> None:
    """Keep experimental inputs separate from the canonical observation ledger."""
    with destination.open("x", encoding="utf-8") as output:
        json.dump([row.model_dump(mode="json") for row in examples], output)
        output.write("\n")


def state_fixture(
    destination: Annotated[Path, typer.Argument(help="New synthetic JSON input file.")],
    seed: Annotated[int, typer.Option()] = 1,
    count: Annotated[int, typer.Option(min=0)] = 400,
    scenario: Annotated[
        str, typer.Option(help="state_signal or null_signal controlled scenario.")
    ] = "state_signal",
) -> None:
    """Generate public simulated checkpoint examples without ledger writes."""
    from model_learner.learn.task_state import generate_task_state_fixture

    try:
        examples = generate_task_state_fixture(
            seed=seed, count=count, scenario=scenario
        )
        write_examples(list(examples), destination)
    except (OSError, ValueError, ArithmeticError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(
        {"source_kind": "simulated", "count": len(examples), "path": destination}
    )


def state_experiment(
    seeds: Annotated[
        int, typer.Option(min=1, help="Number of seeds, starting at zero.")
    ] = 5,
    count: Annotated[int, typer.Option(min=1)] = 400,
    train_fraction: Annotated[float, typer.Option(min=0, max=1)] = 0.6,
    bootstrap_replicates: Annotated[int, typer.Option(min=100)] = 300,
) -> None:
    """Run controlled state-signal and null-signal predictive comparisons."""
    from model_learner.learn.task_state import run_task_state_experiment

    try:
        result = run_task_state_experiment(
            seeds=tuple(range(seeds)),
            count=count,
            train_fraction=train_fraction,
            bootstrap_replicates=bootstrap_replicates,
        )
    except (ValueError, ArithmeticError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(result)
