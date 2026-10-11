"""Local review artifacts, never canonical task identity or learner observations."""

from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from pydantic import (
    AwareDatetime,
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    StrictStr,
    model_validator,
)

Text = Annotated[StrictStr, Field(min_length=1, max_length=4096, pattern=r"\S")]
Identifier = Annotated[StrictStr, Field(min_length=1, max_length=128, pattern=r"\S")]
Digest = Annotated[StrictStr, Field(pattern=r"^[a-f0-9]{64}$")]
Split = Literal["train", "development", "test"]
ActorKind = Literal["human", "agent"]


class Record(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class Origin(Record):
    source_ref: Text
    source_sha256: Digest
    locator: Text
    authorship: Literal["human", "agent", "source"]


class Fact(Record):
    evidence_id: Identifier
    statement: Text
    origin: Origin
    available_at: AwareDatetime
    source_kind: Literal["real", "simulated", "benchmark"]
    provenance: Literal["observed"] = "observed"


class TaskSnapshot(Record):
    example_id: Identifier
    role: Literal["historical", "query"]
    description: Text
    split: Split
    project: Identifier
    family: Identifier
    lineage: Identifier
    available_at: AwareDatetime
    canonical_task_id: UUID | None = None
    origin: Origin
    facts: tuple[Fact, ...] = Field(default=(), max_length=100)


class PairJudgment(Record):
    candidate_id: Identifier
    similarity: Literal["relevant", "irrelevant", "unknown"]
    continuation: Literal["yes", "no", "unknown"]
    scope_change: Literal["unchanged", "expanded", "narrowed", "changed", "unknown"]
    difficulty_change: Literal["easier", "same", "harder", "unknown"]
    hard_negative: bool = Field(strict=True)
    rationale: Text
    evidence_refs: tuple[Identifier, ...] = Field(min_length=1, max_length=100)
    provenance: Literal["inferred"] = "inferred"

    @model_validator(mode="after")
    def negative_is_known(self):
        if self.hard_negative and self.similarity != "irrelevant":
            raise ValueError("hard negatives must be explicitly irrelevant")
        if len(set(self.evidence_refs)) != len(self.evidence_refs):
            raise ValueError("duplicate evidence references")
        return self


class QueryJudgment(Record):
    no_match: Literal["yes", "no", "unknown"]
    rationale: Text
    pairs: tuple[PairJudgment, ...] = Field(min_length=1, max_length=10_000)
    provenance: Literal["inferred"] = "inferred"

    @model_validator(mode="after")
    def complete_no_match(self):
        labels = {pair.similarity for pair in self.pairs}
        if self.no_match == "yes" and labels != {"irrelevant"}:
            raise ValueError("no-match requires every candidate explicitly irrelevant")
        if self.no_match == "no" and "relevant" not in labels:
            raise ValueError("match requires at least one relevant candidate")
        if self.no_match == "unknown" and "relevant" in labels:
            raise ValueError("known relevance cannot have unknown no-match status")
        if self.no_match == "unknown" and "unknown" not in labels:
            raise ValueError("fully negative judgments require explicit no-match")
        if len({pair.candidate_id for pair in self.pairs}) != len(self.pairs):
            raise ValueError("duplicate candidate judgments")
        return self


class Annotation(Record):
    query_id: Identifier
    annotator: Identifier
    actor_kind: ActorKind
    annotated_at: AwareDatetime
    judgment: QueryJudgment


class Review(Record):
    query_id: Identifier
    reviewer: Identifier
    actor_kind: ActorKind
    reviewed_at: AwareDatetime
    decision: Literal["accept", "reject"]
    note: Text
    annotation_sha256: Digest


class Protocol(Record):
    backend: Literal["text", "tfidf", "potion"]
    k: Annotated[StrictInt, Field(ge=1, le=100)]
    minimum_score: float = Field(strict=True, ge=-1, le=1, allow_inf_nan=False)
    selection_note: Text
    model_revision: StrictStr | None = None
    model_sha256: Digest | None = None

    @model_validator(mode="after")
    def pinned_backend(self):
        if self.backend == "potion":
            from model_learner.representation.potion import MODEL_REVISION

            if self.model_revision != MODEL_REVISION or self.model_sha256 is None:
                raise ValueError(
                    "Potion protocol requires existing pinned model identity"
                )
        elif self.model_revision is not None or self.model_sha256 is not None:
            raise ValueError("model identity options require Potion")
        return self


class Freeze(Record):
    frozen_at: AwareDatetime
    content_sha256: Digest


class AnnotationDataset(Record):
    schema_version: Literal["task-annotations/v1"]
    dataset_id: Identifier
    source_kind: Literal["real", "simulated", "benchmark"]
    description: Text
    snapshots: tuple[TaskSnapshot, ...] = Field(min_length=1, max_length=10_000)
    annotations: tuple[Annotation, ...] = Field(default=(), max_length=10_000)
    reviews: tuple[Review, ...] = Field(default=(), max_length=20_000)
    protocol: Protocol | None = None
    freeze: Freeze | None = None
    parent_sha256: Digest | None = None

    @model_validator(mode="after")
    def valid_dataset(self):
        snapshots = {row.example_id: row for row in self.snapshots}
        if len(snapshots) != len(self.snapshots):
            raise ValueError("snapshot identifiers must be unique")
        evidence_ids = [
            fact.evidence_id for row in self.snapshots for fact in row.facts
        ]
        if (
            len(set(evidence_ids)) != len(evidence_ids)
            or set(evidence_ids) & snapshots.keys()
        ):
            raise ValueError("evidence identifiers must be unique and separate")
        # Split keys represent connected cohorts, never features for ranking.
        owners: dict[tuple, str] = {}
        for row in self.snapshots:
            keys = [
                (field, getattr(row, field))
                for field in ("project", "family", "lineage")
            ] + [
                ("description", " ".join(row.description.casefold().split())),
                ("source", row.origin.source_sha256, row.origin.locator),
            ]
            if row.canonical_task_id is not None:
                keys.append(("task", row.canonical_task_id))
            for fact in row.facts:
                if fact.available_at > row.available_at:
                    raise ValueError(
                        "facts must be available at the snapshot checkpoint"
                    )
                keys.append(("source", fact.origin.source_sha256, fact.origin.locator))
            for key in keys:
                if key in owners and owners[key] != row.split:
                    raise ValueError("train/development/test group or source overlap")
                owners[key] = row.split
        annotations = {row.query_id: row for row in self.annotations}
        if len(annotations) != len(self.annotations):
            raise ValueError("one current annotation per query is required")
        for annotation in self.annotations:
            query = snapshots.get(annotation.query_id)
            if query is None or query.role != "query":
                raise ValueError("annotation must refer to a query snapshot")
            candidates = {
                row.example_id: row
                for row in self.snapshots
                if row.role == "historical" and row.split == query.split
            }
            if {pair.candidate_id for pair in annotation.judgment.pairs} != set(
                candidates
            ):
                raise ValueError("judgments must cover every candidate in the split")
            if any(
                row.available_at > query.available_at for row in candidates.values()
            ):
                raise ValueError(
                    "historical candidates cannot postdate query checkpoint"
                )
            if annotation.annotated_at < query.available_at:
                raise ValueError("annotation cannot predate query availability")
            for pair in annotation.judgment.pairs:
                candidate = candidates[pair.candidate_id]
                allowed = {query.example_id, candidate.example_id} | {
                    fact.evidence_id for row in (query, candidate) for fact in row.facts
                }
                if not set(pair.evidence_refs) <= allowed:
                    raise ValueError(
                        "judgment evidence must refer to its query or candidate"
                    )
                # Declaration identity wins over a contrary inferred annotation.
                if (
                    query.canonical_task_id is not None
                    and candidate.canonical_task_id is not None
                ):
                    same = query.canonical_task_id == candidate.canonical_task_id
                    if not same and pair.continuation == "yes":
                        raise ValueError(
                            "continuation cannot override distinct declared task IDs"
                        )
        review_keys = set()
        for review in self.reviews:
            annotation = annotations.get(review.query_id)
            if annotation is None or (
                review.reviewer.strip().casefold()
                == annotation.annotator.strip().casefold()
            ):
                raise ValueError(
                    "review requires an independent reviewer and annotation"
                )
            if review.reviewed_at < annotation.annotated_at:
                raise ValueError("review cannot predate annotation")
            if review.annotation_sha256 != annotation_digest(self, annotation):
                raise ValueError("review does not match current annotation and context")
            key = (review.query_id, review.reviewer.strip().casefold())
            if key in review_keys:
                raise ValueError("one current review per reviewer/query is required")
            review_keys.add(key)
        if self.freeze is not None:
            if self.protocol is None:
                raise ValueError("frozen annotations require a protocol")
            require_reviewed(self)
            if any(row.reviewed_at > self.freeze.frozen_at for row in self.reviews):
                raise ValueError("freeze cannot predate reviews")
            if self.freeze.content_sha256 != content_digest(self):
                raise ValueError("frozen annotation content hash mismatch")
        return self


def digest(value) -> str:
    return hashlib.sha256(
        json.dumps(
            value,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
            allow_nan=False,
        ).encode("utf-8")
    ).hexdigest()


def content_digest(dataset: AnnotationDataset) -> str:
    return digest(dataset.model_dump(mode="json", exclude={"freeze"}))


def annotation_digest(dataset: AnnotationDataset, annotation: Annotation) -> str:
    return digest(
        {
            "context": dataset.model_dump(
                mode="json",
                exclude={
                    "annotations",
                    "reviews",
                    "protocol",
                    "freeze",
                    "parent_sha256",
                },
            ),
            "annotation": annotation.model_dump(mode="json"),
        }
    )


def require_reviewed(dataset: AnnotationDataset) -> None:
    queries = {row.example_id for row in dataset.snapshots if row.role == "query"}
    if not queries or queries != {row.query_id for row in dataset.annotations}:
        raise ValueError("all queries require annotations before freeze/evaluation")
    for annotation in dataset.annotations:
        if annotation.actor_kind != "human":
            raise ValueError("human-authored labels are required for evaluation")
        reviews = [
            row for row in dataset.reviews if row.query_id == annotation.query_id
        ]
        if any(row.decision == "reject" for row in reviews):
            raise ValueError("unresolved rejected review prevents freeze/evaluation")
        if not any(
            row.actor_kind == "human" and row.decision == "accept" for row in reviews
        ):
            raise ValueError("independent accepting human review required")


def load_json(path: str | Path) -> dict:
    with Path(path).open("rb") as stream:
        data = stream.read(8 * 1024 * 1024 + 1)
    if len(data) > 8 * 1024 * 1024:
        raise ValueError("annotation file exceeds size boundary")

    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON keys")
            result[key] = value
        return result

    return json.loads(data, object_pairs_hook=unique_pairs)


def load_annotations(path: str | Path) -> AnnotationDataset:
    return AnnotationDataset.model_validate(load_json(path))


def write_annotations(dataset: AnnotationDataset, path: str | Path) -> None:
    checked = AnnotationDataset.model_validate(dataset.model_dump(mode="json"))
    serialized = checked.model_dump_json(indent=2) + "\n"
    if len(serialized.encode("utf-8")) > 8 * 1024 * 1024:
        raise ValueError("annotation file exceeds size boundary")
    with Path(path).open("x", encoding="utf-8") as stream:
        stream.write(serialized)


def _revised(dataset: AnnotationDataset, **updates) -> AnnotationDataset:
    if dataset.freeze is not None:
        raise ValueError("frozen dataset is immutable; collect a new dataset version")
    value = dataset.model_dump(mode="json")
    value.update(updates, parent_sha256=content_digest(dataset))
    return AnnotationDataset.model_validate(value)


def prepare_annotations(
    dataset: AnnotationDataset, *, dataset_id: str
) -> AnnotationDataset:
    if dataset.annotations or dataset.reviews or dataset.protocol or dataset.freeze:
        raise ValueError("prepare requires an unannotated seed")
    return _revised(dataset, dataset_id=dataset_id)


def set_judgment(
    dataset: AnnotationDataset,
    query_id: str,
    judgment: QueryJudgment,
    *,
    annotator: str,
    actor_kind: ActorKind,
) -> AnnotationDataset:
    annotation = Annotation(
        query_id=query_id,
        annotator=annotator,
        actor_kind=actor_kind,
        annotated_at=datetime.now(UTC),
        judgment=judgment,
    )
    return _revised(
        dataset,
        annotations=[
            row.model_dump(mode="json")
            for row in dataset.annotations
            if row.query_id != query_id
        ]
        + [annotation.model_dump(mode="json")],
        reviews=[
            row.model_dump(mode="json")
            for row in dataset.reviews
            if row.query_id != query_id
        ],
        protocol=None,
    )


def add_review(
    dataset: AnnotationDataset,
    query_id: str,
    *,
    reviewer: str,
    actor_kind: ActorKind,
    decision: Literal["accept", "reject"],
    note: str,
) -> AnnotationDataset:
    annotation = next(
        (row for row in dataset.annotations if row.query_id == query_id), None
    )
    if annotation is None:
        raise ValueError("query has no annotation to review")
    review = Review(
        query_id=query_id,
        reviewer=reviewer,
        actor_kind=actor_kind,
        reviewed_at=datetime.now(UTC),
        decision=decision,
        note=note,
        annotation_sha256=annotation_digest(dataset, annotation),
    )
    return _revised(
        dataset,
        reviews=[
            row.model_dump(mode="json")
            for row in dataset.reviews
            if (row.query_id, row.reviewer.strip().casefold())
            != (query_id, reviewer.strip().casefold())
        ]
        + [review.model_dump(mode="json")],
        protocol=None,
    )


def freeze_annotations(
    dataset: AnnotationDataset,
    *,
    backend="tfidf",
    k=3,
    minimum_score=0.0,
    selection_note: str,
    model_revision=None,
    model_sha256=None,
) -> AnnotationDataset:
    require_reviewed(dataset)
    splits = {row.split for row in dataset.snapshots if row.role == "query"}
    if not {"development", "test"} <= splits:
        raise ValueError("freeze requires independent development and test queries")
    protocol = Protocol(
        backend=backend,
        k=k,
        minimum_score=minimum_score,
        selection_note=selection_note,
        model_revision=model_revision,
        model_sha256=model_sha256,
    )
    revised = _revised(dataset, protocol=protocol.model_dump(mode="json"))
    value = revised.model_dump(mode="json")
    value["freeze"] = Freeze(
        frozen_at=datetime.now(UTC), content_sha256=content_digest(revised)
    ).model_dump(mode="json")
    return AnnotationDataset.model_validate(value)
