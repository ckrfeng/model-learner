"""Inspect explicit portable task trajectories without modifying the ledger."""

import json
from itertools import pairwise
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from model_learner.commands.common import write_json
from model_learner.execution.longitudinal import TrajectoryInput, compare_task_states


def task_trajectory(
    input_file: Annotated[
        Path, typer.Argument(help="Explicit task-trajectory-input/v1 JSON.")
    ],
) -> None:
    """Show checkpoint evidence, hypotheses, unknowns and changes as JSON."""
    try:
        trajectory = TrajectoryInput.model_validate_json(
            input_file.read_text(encoding="utf-8")
        )
        points = trajectory.project()
        write_json(
            {
                "dataset": trajectory.dataset,
                "checkpoints": points,
                "changes": [
                    compare_task_states(left, right) for left, right in pairwise(points)
                ],
            }
        )
    except (ValidationError, ValueError) as error:
        # Validation errors contain input excerpts, possibly private text.
        raise typer.BadParameter(
            "invalid trajectory input or evidence; inspect local source"
        ) from error
    except OSError as error:
        raise typer.BadParameter("trajectory input could not be read") from error


def trajectory_eval(
    input_file: Annotated[
        Path, typer.Argument(help="Synthetic longitudinal evaluation fixture JSON.")
    ],
    output: Annotated[
        Path | None, typer.Option(help="New report file; never overwritten.")
    ] = None,
    model_path: Annotated[
        Path | None, typer.Option(help="Existing approved local Potion bundle.")
    ] = None,
    model_revision: Annotated[str | None, typer.Option()] = None,
    model_sha256: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Compare A/B/C rule behavior; semantic distances never verify task changes."""
    from model_learner.representation.potion import load_potion_encoder
    from model_learner.representation.semantic import SemanticUnavailable
    from model_learner.understanding.longitudinal_evaluation import (
        evaluate_longitudinal_fixture,
        load_longitudinal_fixture,
    )

    try:
        supplied = (model_path, model_revision, model_sha256)
        if any(value is not None for value in supplied) and not all(
            value is not None for value in supplied
        ):
            raise typer.BadParameter("Potion requires path, full revision and SHA-256")
        fixture = load_longitudinal_fixture(input_file)
        encoder, unavailable = None, None
        if model_path is not None:
            try:
                encoder = load_potion_encoder(
                    model_path, revision=model_revision, expected_sha256=model_sha256
                )
            except SemanticUnavailable as error:
                unavailable = str(error)
        report = evaluate_longitudinal_fixture(fixture, encoder=encoder)
        if unavailable:
            report["semantic_unavailable_reason"] = unavailable
        if output is not None:
            with output.open("x", encoding="utf-8") as stream:
                json.dump(report, stream, indent=2, allow_nan=False)
                stream.write("\n")
        write_json(report)
    except typer.BadParameter:
        raise
    except (ValidationError, ValueError) as error:
        raise typer.BadParameter(
            "invalid evaluation input or evidence; inspect local source"
        ) from error
    except OSError as error:
        raise typer.BadParameter(
            "evaluation input could not be read or output already exists/unavailable"
        ) from error
