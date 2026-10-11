"""Optional read-only suggestions over explicitly declared local descriptions."""

from enum import StrEnum
from pathlib import Path
from typing import Annotated
from uuid import UUID

import typer
from pydantic import ValidationError

from model_learner.commands.common import DEFAULT_DATABASE, repository, write_json
from model_learner.domain.models import Task
from model_learner.storage.database import StorageError


class RetrievalBackend(StrEnum):
    TEXT = "text"
    TFIDF = "tfidf"
    POTION = "potion"


def task_similar(
    task_id: Annotated[UUID, typer.Argument()],
    backend: Annotated[
        RetrievalBackend, typer.Option(help="Local text, TF-IDF or pinned Potion.")
    ] = RetrievalBackend.TFIDF,
    limit: Annotated[int, typer.Option(min=1, max=100)] = 5,
    model_path: Annotated[
        Path | None,
        typer.Option(help="Existing local Potion bundle; never downloaded."),
    ] = None,
    model_revision: Annotated[str | None, typer.Option()] = None,
    model_sha256: Annotated[str | None, typer.Option()] = None,
    database: Annotated[Path, typer.Option("--database", "-d")] = DEFAULT_DATABASE,
) -> None:
    """Suggest earlier declared tasks; scores never establish continuation."""
    from model_learner.representation.semantic import SemanticUnavailable
    from model_learner.understanding.retrieval import TaskText, build_retrieval_index

    try:
        supplied = (model_path, model_revision, model_sha256)
        if backend == RetrievalBackend.POTION:
            if not all(value is not None for value in supplied):
                raise ValueError(
                    "Potion requires model path, full revision and SHA-256"
                )
        elif any(value is not None for value in supplied):
            raise ValueError("model options require the potion backend")
        ledger = repository(database)
        task = ledger.get(Task, task_id)
        if task is None:
            raise ValueError("unknown task")
        if not task.description.strip() or len(task.description) > 4096:
            raise ValueError(
                "query description must be nonblank and at most 4096 characters"
            )
        candidates, exclusions = (
            [],
            {"created_after_query": 0, "unsupported_description": 0},
        )
        for candidate in ledger.list_tasks():
            if candidate.task_id == task_id:
                continue
            if candidate.created_at > task.created_at:
                exclusions["created_after_query"] += 1
            elif not candidate.description.strip() or len(candidate.description) > 4096:
                exclusions["unsupported_description"] += 1
            else:
                candidates.append(
                    TaskText(
                        task_id=str(candidate.task_id),
                        text=candidate.description,
                        source="declared",
                    )
                )
        context = {
            "task_id": task_id,
            "backend": backend,
            "candidate_scope": "declared tasks created no later than the query task",
            "candidate_count": len(candidates),
            "exclusions": exclusions,
            "input_source": (
                "explicitly declared Task.description; no transcript access"
            ),
            "identity_policy": (
                "distinct task IDs remain distinct; similarity creates no links"
            ),
        }
        encoder = None
        if backend == RetrievalBackend.POTION:
            from model_learner.representation.potion import (
                MODEL_ID,
                load_potion_encoder,
            )

            try:
                encoder = load_potion_encoder(
                    model_path, revision=model_revision, expected_sha256=model_sha256
                )
            except SemanticUnavailable as error:
                write_json(
                    {
                        **context,
                        "status": "semantic_unavailable",
                        "related_tasks": [],
                        "reason": str(error),
                        "provenance": {
                            "model_id": MODEL_ID,
                            "revision": model_revision,
                        },
                    }
                )
                return
        index = build_retrieval_index(
            tuple(candidates),
            method="embedding" if encoder else backend.value,
            encoder=encoder,
        )
        result = index.search(
            TaskText(task_id=str(task_id), text=task.description, source="declared"),
            k=limit,
        )
        write_json(
            {
                **context,
                "status": result.status,
                "unknown_candidate_count": result.unknown_candidate_count,
                "related_tasks": [
                    {
                        "task_id": hit.task_id,
                        "similarity_score": hit.score,
                        "provenance": "inferred_description_relatedness",
                        "continuation": "not_established_by_similarity",
                    }
                    for hit in result.hits
                ],
                "provenance": index.metadata,
            }
        )
    except ValidationError as error:
        raise typer.BadParameter("invalid declared task records") from error
    except (OSError, ValueError, StorageError) as error:
        raise typer.BadParameter(str(error)) from error
