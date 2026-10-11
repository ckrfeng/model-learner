"""Optional CPU task representations; no downloads, agent control or ledger writes."""

from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from model_learner.commands.common import aware_time, write_json
from model_learner.commands.task_state import write_examples
from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    DataSourceKind,
    ResourceBudget,
)


def representation_fixture(
    destination: Annotated[
        Path, typer.Argument(help="New public synthetic representation input file.")
    ],
    seed: Annotated[int, typer.Option()] = 1,
    count: Annotated[int, typer.Option(min=1)] = 150,
    scenario: Annotated[
        str, typer.Option(help="state_signal or null_signal controlled scenario.")
    ] = "state_signal",
) -> None:
    """Generate public descriptions and simulated checkpoints without execution."""
    from model_learner.representation import generate_representation_fixture

    try:
        examples = generate_representation_fixture(
            seed=seed, count=count, scenario=scenario
        )
        write_examples(list(examples), destination)
    except (OSError, ValueError, ArithmeticError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(
        {"source_kind": "simulated", "count": len(examples), "path": destination}
    )


def representation_eval(
    input_file: Annotated[
        Path, typer.Option(help="JSON array of RepresentationExample v1.")
    ],
    source_kind: Annotated[DataSourceKind, typer.Option()],
    dataset_id: Annotated[str, typer.Option()],
    dataset_version: Annotated[str, typer.Option()],
    acceptance_id: Annotated[str, typer.Option()],
    acceptance_version: Annotated[str, typer.Option()],
    train_until: Annotated[str, typer.Option(help="Aware ISO frozen fit cutoff.")],
    evaluation_at: Annotated[str, typer.Option(help="Aware ISO scoring cutoff.")],
    checkpoint_offset_seconds: Annotated[float, typer.Option(min=0)] = 30,
    budget_file: Annotated[Path | None, typer.Option()] = None,
    model_path: Annotated[
        Path | None, typer.Option(help="Existing local CPU embedding bundle.")
    ] = None,
    model_sha256: Annotated[
        str | None, typer.Option(help="Expected immutable bundle SHA-256.")
    ] = None,
    model_revision: Annotated[
        str | None, typer.Option(help="Predeclared pretrained model revision.")
    ] = None,
    bootstrap_replicates: Annotated[int, typer.Option(min=100)] = 300,
    seed: Annotated[int, typer.Option()] = 1,
) -> None:
    """Compare initial features, execution state and optional local semantics."""
    from model_learner.representation import (
        evaluate_task_representation,
        load_representation_examples,
    )

    try:
        supplied = (model_path, model_sha256, model_revision)
        if any(value is not None for value in supplied) and not all(
            value is not None for value in supplied
        ):
            raise ValueError("all three model options are required together")
        examples = load_representation_examples(input_file)
        budget = (
            ResourceBudget.model_validate_json(budget_file.read_text())
            if budget_file is not None
            else None
        )
        encoder = None
        semantic_reason = None
        if model_path is not None:
            from model_learner.representation import (
                SemanticUnavailable,
                load_cpu_encoder,
            )

            try:
                encoder = load_cpu_encoder(
                    model_path, expected_sha256=model_sha256, revision=model_revision
                )
            except SemanticUnavailable as error:
                semantic_reason = str(error)
        result = evaluate_task_representation(
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
            encoder=encoder,
            semantic_unavailable_reason=semantic_reason,
            bootstrap_replicates=bootstrap_replicates,
            seed=seed,
        )
    except ValidationError as error:
        raise typer.BadParameter("invalid representation input or budget") from error
    except (OSError, ValueError, ArithmeticError) as error:
        raise typer.BadParameter(str(error)) from error
    write_json(result)
