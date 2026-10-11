"""Local annotation files, human review and frozen task-retrieval evaluation."""

from enum import StrEnum
from json import JSONDecodeError
from pathlib import Path
from typing import Annotated

import typer
from pydantic import ValidationError

from model_learner.commands.common import write_json
from model_learner.commands.understanding import RetrievalBackend

annotation_app = typer.Typer(
    help="Collect, review and evaluate local task-understanding annotations.",
    no_args_is_help=True,
)


class ActorKind(StrEnum):
    HUMAN = "human"
    AGENT = "agent"


class ReviewDecision(StrEnum):
    ACCEPT = "accept"
    REJECT = "reject"


class EvaluationSplit(StrEnum):
    TRAIN = "train"
    DEVELOPMENT = "development"
    TEST = "test"


def _invalid_annotation(error: Exception) -> typer.BadParameter:
    if isinstance(error, (ValidationError, JSONDecodeError, UnicodeError)):
        return typer.BadParameter("invalid annotation JSON or schema")
    return typer.BadParameter(str(error))


@annotation_app.command("prepare")
def prepare(
    source: Annotated[Path, typer.Argument()],
    destination: Annotated[Path, typer.Argument()],
    dataset_id: Annotated[str, typer.Option(help="New versioned dataset identity.")],
) -> None:
    """Create an annotation collection from an unlabeled local seed."""
    from model_learner.understanding.annotations import (
        load_annotations,
        prepare_annotations,
        write_annotations,
    )

    try:
        dataset = prepare_annotations(load_annotations(source), dataset_id=dataset_id)
        write_annotations(dataset, destination)
        write_json({"status": "prepared", "dataset_id": dataset.dataset_id})
    except (OSError, ValueError, UnicodeError) as error:
        raise _invalid_annotation(error) from error


@annotation_app.command("show")
def show(
    source: Annotated[Path, typer.Argument()],
    query_id: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Display supplied snapshots and judgments without model scores or ranks."""
    from model_learner.understanding.annotations import load_annotations

    try:
        dataset = load_annotations(source)
        data = dataset.model_dump(mode="json")
        if query_id is not None:
            query = next(
                (
                    row
                    for row in data["snapshots"]
                    if row["example_id"] == query_id and row["role"] == "query"
                ),
                None,
            )
            if query is None:
                raise ValueError("unknown query identifier")
            data["snapshots"] = [
                row
                for row in data["snapshots"]
                if row["example_id"] == query_id
                or (row["role"] == "historical" and row["split"] == query["split"])
            ]
            data["annotations"] = [
                row for row in data["annotations"] if row["query_id"] == query_id
            ]
            data["reviews"] = [
                row for row in data["reviews"] if row["query_id"] == query_id
            ]
        write_json(data)
    except (OSError, ValueError, UnicodeError) as error:
        raise _invalid_annotation(error) from error


@annotation_app.command("label")
def label(
    source: Annotated[Path, typer.Argument()],
    query_id: Annotated[str, typer.Argument()],
    label_file: Annotated[Path, typer.Argument()],
    annotator: Annotated[str, typer.Option(help="Caller-attested annotator identity.")],
    actor_kind: Annotated[
        ActorKind, typer.Option(help="Explicit identity attestation.")
    ],
    output: Annotated[
        Path, typer.Option(help="New annotation file; never overwritten.")
    ],
) -> None:
    """Attach a supplied judgment; labels never establish ledger relationships."""
    from model_learner.understanding.annotations import (
        QueryJudgment,
        load_annotations,
        load_json,
        set_judgment,
        write_annotations,
    )

    try:
        judgment = QueryJudgment.model_validate(load_json(label_file))
        dataset = set_judgment(
            load_annotations(source),
            query_id,
            judgment,
            annotator=annotator,
            actor_kind=actor_kind.value,
        )
        write_annotations(dataset, output)
        write_json({"status": "labeled", "query_id": query_id})
    except (OSError, ValueError, UnicodeError) as error:
        raise _invalid_annotation(error) from error


@annotation_app.command("review")
def review(
    source: Annotated[Path, typer.Argument()],
    query_id: Annotated[str, typer.Argument()],
    reviewer: Annotated[str, typer.Option(help="Caller-attested reviewer identity.")],
    actor_kind: Annotated[
        ActorKind, typer.Option(help="Explicit identity attestation.")
    ],
    decision: Annotated[ReviewDecision, typer.Option()],
    note: Annotated[str, typer.Option(help="Independent review rationale.")],
    output: Annotated[
        Path, typer.Option(help="New annotation file; never overwritten.")
    ],
) -> None:
    """Record acceptance or rejection by an independently declared reviewer."""
    from model_learner.understanding.annotations import (
        add_review,
        load_annotations,
        write_annotations,
    )

    try:
        dataset = add_review(
            load_annotations(source),
            query_id,
            reviewer=reviewer,
            actor_kind=actor_kind.value,
            decision=decision.value,
            note=note,
        )
        write_annotations(dataset, output)
        write_json({"status": "reviewed", "query_id": query_id, "decision": decision})
    except (OSError, ValueError, UnicodeError) as error:
        raise _invalid_annotation(error) from error


@annotation_app.command("freeze")
def freeze(
    source: Annotated[Path, typer.Argument()],
    destination: Annotated[Path, typer.Argument()],
    selection_note: Annotated[
        str, typer.Option(help="Prospective selection rationale.")
    ],
    backend: Annotated[RetrievalBackend, typer.Option()] = RetrievalBackend.TFIDF,
    k: Annotated[int, typer.Option(min=1, max=100)] = 3,
    minimum_score: Annotated[float, typer.Option(min=-1, max=1)] = 0.0,
    model_revision: Annotated[str | None, typer.Option()] = None,
    model_sha256: Annotated[str | None, typer.Option()] = None,
) -> None:
    """Lock reviewed data and an evaluation protocol before held-out ranking."""
    from model_learner.understanding.annotations import (
        freeze_annotations,
        load_annotations,
        write_annotations,
    )

    try:
        dataset = freeze_annotations(
            load_annotations(source),
            backend=backend.value,
            k=k,
            minimum_score=minimum_score,
            selection_note=selection_note,
            model_revision=model_revision,
            model_sha256=model_sha256,
        )
        write_annotations(dataset, destination)
        write_json({"status": "frozen", "dataset_id": dataset.dataset_id})
    except (OSError, ValueError, UnicodeError) as error:
        raise _invalid_annotation(error) from error


@annotation_app.command("evaluate")
def evaluate(
    source: Annotated[Path, typer.Argument()],
    output: Annotated[Path, typer.Option(help="New report file; never overwritten.")],
    split: Annotated[EvaluationSplit, typer.Option()] = EvaluationSplit.TEST,
    model_path: Annotated[
        Path | None,
        typer.Option(help="Existing local Potion bundle; never downloaded."),
    ] = None,
) -> None:
    """Measure retrieval and abstention under the frozen human-review protocol."""
    import json

    from model_learner.representation.semantic import SemanticUnavailable
    from model_learner.understanding.annotation_evaluation import evaluate_annotations
    from model_learner.understanding.annotations import load_annotations

    try:
        dataset = load_annotations(source)
        if dataset.freeze is None or dataset.protocol is None:
            raise ValueError("evaluation requires a frozen protocol")
        encoder = None
        if dataset.protocol.backend == "potion":
            if model_path is None:
                raise ValueError(
                    "Potion requires an explicit existing local model path"
                )
            from model_learner.representation.potion import load_potion_encoder

            encoder = load_potion_encoder(
                model_path,
                revision=dataset.protocol.model_revision,
                expected_sha256=dataset.protocol.model_sha256,
            )
        elif model_path is not None:
            raise ValueError("model path requires the potion backend")
        report = evaluate_annotations(dataset, split=split.value, encoder=encoder)
        serialized = json.dumps(report, indent=2, allow_nan=False) + "\n"
        with output.open("x", encoding="utf-8") as handle:
            handle.write(serialized)
        write_json({"status": "evaluated", "split": split})
    except (OSError, ValueError, UnicodeError, SemanticUnavailable) as error:
        raise _invalid_annotation(error) from error
