"""Explicit dataset selection for simulation and statistical reference commands."""

from __future__ import annotations

from datetime import datetime
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


def _historical_inputs(
    database: Path,
    dataset: DatasetReference,
    observations: list[Observation],
    cutoff: datetime,
) -> tuple[list[Observation], object | None]:
    """Validate real cohort evidence and select its assessment heads at this time."""
    if dataset.source_kind is not DataSourceKind.REAL:
        return observations, None
    from model_learner.observations.resolution import resolve_real_observations

    snapshot = resolve_real_observations(
        repository(database),
        dataset=dataset,
        cutoff=cutoff,
        run_ids={
            row.run_id
            for row in observations
            if row.run_id is not None and row.recorded_at <= cutoff
        },
    )
    return list(snapshot.observations), snapshot


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
        observations, resolution = _historical_inputs(
            database, dataset, observations, aware_time(cutoff)
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
                "assessment_resolution": resolution,
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
        training_rows, training_resolution = _historical_inputs(
            database, dataset, observations, aware_time(train_until)
        )
        scoring_rows, scoring_resolution = _historical_inputs(
            database, dataset, observations, aware_time(evaluation_at)
        )
        report = evaluate(
            scoring_rows,
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
            training_observations=training_rows,
        )
        if source_kind is DataSourceKind.REAL:
            from dataclasses import asdict

            write_json(
                asdict(report)
                | {
                    "training_assessment_resolution": training_resolution,
                    "scoring_assessment_resolution": scoring_resolution,
                }
            )
        else:
            write_json(report)
    except (OSError, ValueError, ArithmeticError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error


@learn_app.command("stress")
def stress_learning(
    seed: Annotated[
        list[int] | None,
        typer.Option(
            "--seed",
            help="Repeat for distinct reproducible seeds; default 0 through 9.",
        ),
    ] = None,
    count: Annotated[
        int,
        typer.Option(min=2, help="Runs per scenario/seed; sparse scenario caps at 48."),
    ] = 1000,
    train_fraction: Annotated[
        float, typer.Option(help="Fraction of decisions before frozen training cutoff.")
    ] = 0.6,
    scenario: Annotated[
        list[str] | None,
        typer.Option(
            "--scenario",
            help="Repeat to select named reference scenarios; default all.",
        ),
    ] = None,
    calibration_bins: Annotated[int, typer.Option(min=1)] = 10,
    output: Annotated[
        Path | None, typer.Option(help="New JSON report destination; no ledger writes.")
    ] = None,
) -> None:
    """Evaluate seeded sparse, imbalance, drift and label-delay scenarios."""
    import json

    from model_learner.commands.common import _json_default
    from model_learner.learn.stress import reference_scenarios, run_stress_suite

    try:
        scenarios = reference_scenarios(count=count, train_fraction=train_fraction)
        if scenario:
            names = set(scenario)
            if len(names) != len(scenario):
                raise ValueError("scenario names must be distinct")
            unknown = names - {s.name for s in scenarios}
            if unknown:
                raise ValueError("unknown scenarios: " + ", ".join(sorted(unknown)))
            scenarios = tuple(s for s in scenarios if s.name in names)
        report = run_stress_suite(
            seeds=seed if seed is not None else range(10),
            scenarios=scenarios,
            calibration_bins=calibration_bins,
        )
        if output:
            encoded = json.dumps(
                report, default=_json_default, indent=2, allow_nan=False
            )
            with output.open("x", encoding="utf-8") as destination:
                destination.write(encoded + "\n")
            write_json(
                {
                    "output": output,
                    "seeds": report.seeds,
                    "scenarios": [s.name for s in report.scenarios],
                }
            )
        else:
            write_json(report)
    except (OSError, ValueError, ArithmeticError) as error:
        raise typer.BadParameter(str(error)) from error


@learn_app.command("drift")
def investigate_drift(
    seed: Annotated[
        list[int] | None,
        typer.Option("--seed", help="Repeat for distinct seeds; default 0 through 19."),
    ] = None,
    count: Annotated[int, typer.Option(min=8)] = 1000,
    window_steps: Annotated[
        list[int] | None,
        typer.Option(
            "--window-steps",
            help="Repeat for decision-age windows; default 120 and 300.",
        ),
    ] = None,
    refit_steps: Annotated[int, typer.Option(min=1)] = 50,
    calibration_bins: Annotated[int, typer.Option(min=1)] = 10,
    output: Annotated[
        Path | None, typer.Option(help="New JSON report destination; no ledger writes.")
    ] = None,
) -> None:
    """Compare full history and recent windows with chronological updates."""
    import json

    from model_learner.commands.common import _json_default
    from model_learner.learn.drift import run_drift_suite

    try:
        report = run_drift_suite(
            seeds=seed if seed is not None else range(20),
            count=count,
            window_steps=window_steps if window_steps is not None else (120, 300),
            refit_steps=refit_steps,
            calibration_bins=calibration_bins,
        )
        if output:
            encoded = json.dumps(
                report, default=_json_default, indent=2, allow_nan=False
            )
            with output.open("x", encoding="utf-8") as destination:
                destination.write(encoded + "\n")
            write_json(
                {
                    "output": output,
                    "seeds": report.seeds,
                    "window_steps": report.window_steps,
                    "scenarios": [s.name for s in report.scenarios],
                }
            )
        else:
            write_json(report)
    except (OSError, ValueError, ArithmeticError) as error:
        raise typer.BadParameter(str(error)) from error
