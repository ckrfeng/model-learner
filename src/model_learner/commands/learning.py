"""Explicit dataset selection for simulation and statistical reference commands."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated

import typer

from model_learner.commands.common import (
    DEFAULT_DATABASE,
    aware_time,
    repository,
    write_json,
)
from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    DataSourceKind,
    ExecutionConfiguration,
    Observation,
    ResourceBudget,
)
from model_learner.learn import BetaBernoulli, evaluate
from model_learner.simulate import SimulationConfig, SimulationTruth, generate
from model_learner.storage.database import StorageError

sim_app = typer.Typer(help="Generate explicitly simulated data.", no_args_is_help=True)
learn_app = typer.Typer(help="Estimate verified binary outcomes.", no_args_is_help=True)


@sim_app.command("generate")
def generate_simulation(
    seed: Annotated[int | None, typer.Option(help="Default: 1.")] = None,
    count: Annotated[int | None, typer.Option(min=0, help="Default: 1000.")] = None,
    dataset_id: Annotated[
        str | None, typer.Option(help="Default: synthetic-reference.")
    ] = None,
    dataset_version: Annotated[str | None, typer.Option(help="Default: 1.")] = None,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
    config_file: Annotated[
        Path | None,
        typer.Option(help="Scenario JSON; explicit CLI options override it."),
    ] = None,
    truth_output: Annotated[
        Path | None,
        typer.Option(help="New evaluator-only truth JSON, kept out of ledger."),
    ] = None,
) -> None:
    """Persist observations; keep known probabilities in a separate optional file."""
    try:
        values = (
            SimulationConfig.model_validate_json(config_file.read_text()).model_dump()
            if config_file
            else {}
        )
        overrides = {
            "seed": seed,
            "count": count,
            "dataset_id": dataset_id,
            "dataset_version": dataset_version,
        }
        config = SimulationConfig.model_validate(
            values
            | {key: value for key, value in overrides.items() if value is not None}
        )
        ledger = repository(database)
        result = generate(config)
        if truth_output:
            with truth_output.open("x", encoding="utf-8") as output:
                output.write(result.truth.model_dump_json(indent=2) + "\n")
        for observation in result.observations:
            ledger.add_observation(observation)
    except (OSError, ValueError, ArithmeticError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(
        {
            "dataset": result.truth.dataset,
            "observations_processed": len(result.observations),
            "truth_output": truth_output,
            "configurations": {
                o.configuration.configuration_id: o.configuration
                for o in result.observations
            },
            "first_decision_at": result.observations[0].decision_at
            if result.observations
            else None,
            "last_recorded_at": result.observations[-1].recorded_at
            if result.observations
            else None,
        }
    )


def _inputs(
    database: Path,
    source_kind: DataSourceKind,
    dataset_id: str,
    dataset_version: str,
) -> tuple[DatasetReference, list[Observation]]:
    dataset = DatasetReference(
        source_kind=source_kind,
        dataset_id=dataset_id,
        dataset_version=dataset_version,
    )
    observations = repository(database).list_observations(
        source_kind.value, dataset_id=dataset_id
    )
    # Repository filtering predates dataset versions; keep this boundary explicit.
    return dataset, [o for o in observations if o.dataset == dataset]


@learn_app.command("predict")
def predict(
    source_kind: Annotated[DataSourceKind, typer.Option()],
    dataset_id: Annotated[str, typer.Option()],
    dataset_version: Annotated[str, typer.Option()],
    acceptance_id: Annotated[str, typer.Option()],
    acceptance_version: Annotated[str, typer.Option()],
    cutoff: Annotated[str, typer.Option(help="ISO timestamp with timezone.")],
    group: Annotated[str, typer.Option()],
    configuration_id: Annotated[str | None, typer.Option()] = None,
    configuration_file: Annotated[
        Path | None, typer.Option(help="Configuration JSON, including an unseen arm.")
    ] = None,
    budget_file: Annotated[
        Path | None, typer.Option(help="ResourceBudget JSON.")
    ] = None,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Predict one exact configuration and group, including prior-only uncertainty."""
    try:
        dataset, observations = _inputs(
            database, source_kind, dataset_id, dataset_version
        )
        if (configuration_id is None) == (configuration_file is None):
            raise ValueError(
                "supply exactly one configuration ID or configuration file"
            )
        configuration = (
            ExecutionConfiguration.model_validate_json(configuration_file.read_text())
            if configuration_file
            else next(
                (
                    o.configuration
                    for o in observations
                    if o.configuration.configuration_id == configuration_id
                ),
                None,
            )
        )
        if configuration is None:
            raise ValueError("unknown configuration ID in the selected dataset")
        acceptance = AcceptanceSpec(
            identifier=acceptance_id, version=acceptance_version
        )
        budget = (
            ResourceBudget.model_validate_json(budget_file.read_text())
            if budget_file
            else None
        )
        estimator = BetaBernoulli.fit(
            observations,
            dataset=dataset,
            cutoff=aware_time(cutoff),
            acceptance_spec=acceptance,
            resource_budget=budget,
        )
        write_json(
            {
                "dataset": dataset,
                "cutoff": aware_time(cutoff),
                "acceptance_spec": acceptance,
                "resource_budget": budget,
                "configuration": configuration,
                "training": estimator.training_summary,
                "prediction": estimator.predict(configuration, group),
            }
        )
    except (OSError, ValueError, ArithmeticError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error


@learn_app.command("eval")
def evaluate_learning(
    source_kind: Annotated[DataSourceKind, typer.Option()],
    dataset_id: Annotated[str, typer.Option()],
    dataset_version: Annotated[str, typer.Option()],
    acceptance_id: Annotated[str, typer.Option()],
    acceptance_version: Annotated[str, typer.Option()],
    train_until: Annotated[
        str, typer.Option(help="Frozen training cutoff, ISO timestamp.")
    ],
    evaluation_at: Annotated[
        str, typer.Option(help="Held-out label availability cutoff.")
    ],
    truth_file: Annotated[
        Path | None, typer.Option(help="Optional separate simulator truth JSON.")
    ] = None,
    budget_file: Annotated[Path | None, typer.Option()] = None,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Compare global, per-arm, and unpooled references on time-ordered holdout."""
    try:
        dataset, observations = _inputs(
            database, source_kind, dataset_id, dataset_version
        )
        report = evaluate(
            observations,
            dataset=dataset,
            train_until=aware_time(train_until),
            evaluation_at=aware_time(evaluation_at),
            acceptance_spec=AcceptanceSpec(
                identifier=acceptance_id, version=acceptance_version
            ),
            resource_budget=ResourceBudget.model_validate_json(budget_file.read_text())
            if budget_file
            else None,
            truth=SimulationTruth.model_validate_json(truth_file.read_text())
            if truth_file
            else None,
        )
        write_json(report)
    except (OSError, ValueError, ArithmeticError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error
