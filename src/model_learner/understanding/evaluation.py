"""Independent constructed relevance evaluation; never outcome prediction.

Labels enter metrics only after ranking. Candidate family/project annotations do
not enter the retrieval index. Development and test have disjoint annotation
cohorts; same-family query-to-candidate matching is the target, not training.
"""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections import Counter
from pathlib import Path
from statistics import fmean
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictStr, model_validator

from model_learner.understanding.retrieval import (
    DescriptionEncoder,
    Method,
    TaskText,
    build_retrieval_index,
)

Split = Literal["development", "test"]


class _FrozenRecord(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class RetrievalCandidate(_FrozenRecord):
    task_id: StrictStr = Field(min_length=1, max_length=128)
    text: StrictStr = Field(min_length=1, max_length=4096)
    split: Split
    family: StrictStr = Field(min_length=1)
    project: StrictStr = Field(min_length=1)
    case_kind: StrictStr = Field(min_length=1)
    judgment_rationale: StrictStr = Field(min_length=1)


class RetrievalQuery(_FrozenRecord):
    task_id: StrictStr = Field(min_length=1, max_length=128)
    text: StrictStr = Field(min_length=1, max_length=4096)
    split: Split
    family: StrictStr = Field(min_length=1)
    project: StrictStr = Field(min_length=1)
    rewrite_group: StrictStr = Field(min_length=1)
    relevant_task_ids: tuple[StrictStr, ...] = Field(min_length=1)


class RetrievalDataset(_FrozenRecord):
    schema_version: Literal[1]
    dataset_id: StrictStr = Field(min_length=1)
    provenance: dict
    candidates: tuple[RetrievalCandidate, ...] = Field(min_length=1, max_length=10_000)
    queries: tuple[RetrievalQuery, ...] = Field(min_length=1, max_length=10_000)

    @model_validator(mode="after")
    def valid_cohorts(self):
        candidate_ids = {row.task_id for row in self.candidates}
        query_ids = {row.task_id for row in self.queries}
        if len(candidate_ids) != len(self.candidates) or len(query_ids) != len(
            self.queries
        ):
            raise ValueError("dataset task identifiers must be unique")
        if candidate_ids & query_ids:
            raise ValueError("evaluation queries must be separate from candidate IDs")
        lookup = {row.task_id: row for row in self.candidates}
        for row in (*self.candidates, *self.queries):
            # Reuse the production text boundary without exposing annotations.
            TaskText(task_id=row.task_id, text=row.text, source="public")
            if not row.text.strip():
                raise ValueError("evaluation text must be nonblank")
        for query in self.queries:
            if len(set(query.relevant_task_ids)) != len(query.relevant_task_ids):
                raise ValueError("duplicate relevance labels")
            if any(
                key not in lookup or lookup[key].split != query.split
                for key in query.relevant_task_ids
            ):
                raise ValueError("relevance label refers outside the split corpus")
        for attribute in ("family", "project", "rewrite_group"):
            cohorts = []
            for split in ("development", "test"):
                rows = (
                    self.queries
                    if attribute == "rewrite_group"
                    else (
                        *self.candidates,
                        *self.queries,
                    )
                )
                cohorts.append(
                    {getattr(row, attribute) for row in rows if row.split == split}
                )
            if cohorts[0] & cohorts[1]:
                raise ValueError(f"development/test {attribute} overlap")
        return self


def load_retrieval_dataset(
    path: str | Path, *, expected_sha256: str | None = None
) -> tuple[RetrievalDataset, str]:
    """Load explicitly supplied constructed data; a manifest pin protects freeze."""
    boundary = 4 * 1024 * 1024
    with Path(path).open("rb") as stream:
        data = stream.read(boundary + 1)
    if len(data) > boundary:
        raise ValueError("retrieval evaluation fixture exceeds size boundary")
    digest = hashlib.sha256(data).hexdigest()
    if expected_sha256 is not None and digest != expected_sha256:
        raise ValueError("retrieval fixture differs from frozen dataset hash")

    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate evaluation JSON keys")
            result[key] = value
        return result

    value = json.loads(data, object_pairs_hook=unique_pairs)
    return RetrievalDataset.model_validate(value), digest


def ranking_metrics(
    ranked_ids: tuple[str, ...], relevant_ids: frozenset[str], *, k: int
) -> dict[str, float]:
    """Binary relevance. Missing ranks receive no credit; no fabricated labels."""
    if type(k) is not int or k < 1:
        raise ValueError("metric k must be a positive integer")
    if not relevant_ids or len(set(ranked_ids)) != len(ranked_ids):
        raise ValueError("metrics require nonempty relevance and unique rankings")
    gains = [int(task_id in relevant_ids) for task_id in ranked_ids[:k]]
    found = sum(gains)
    dcg = math.fsum(gain / math.log2(rank + 2) for rank, gain in enumerate(gains))
    ideal = math.fsum(
        1 / math.log2(rank + 2) for rank in range(min(k, len(relevant_ids)))
    )
    reciprocal = next(
        (
            1 / rank
            for rank, key in enumerate(ranked_ids, start=1)
            if key in relevant_ids
        ),
        0.0,
    )
    return {
        f"precision_at_{k}": found / k,
        f"recall_at_{k}": found / len(relevant_ids),
        f"ndcg_at_{k}": dcg / ideal,
        "mrr": reciprocal,
    }


def evaluate_retrieval(
    dataset: RetrievalDataset,
    *,
    method: Method,
    split: Split = "test",
    encoder: DescriptionEncoder | None = None,
    ks: tuple[int, ...] = (1, 3),
) -> dict:
    """Rank within a fixed split without consulting relevance/family/project labels.

    Scores are not calibrated association or continuation probabilities. Full
    known rankings remove threshold selection from this first experiment;
    unknown representations have empty ranks and receive zero retrieval credit.
    """
    if split not in ("development", "test"):
        raise ValueError("unsupported evaluation split")
    if (
        not ks
        or len(set(ks)) != len(ks)
        or any(type(k) is not int or k < 1 for k in ks)
    ):
        raise ValueError("evaluation k values must be unique positive integers")
    candidates = tuple(row for row in dataset.candidates if row.split == split)
    queries = tuple(row for row in dataset.queries if row.split == split)
    if not candidates or not queries:
        raise ValueError("evaluation split requires candidates and queries")
    if max(ks) > len(candidates):
        raise ValueError("evaluation k exceeds candidate pool size")
    started = time.perf_counter()
    index = build_retrieval_index(
        tuple(
            TaskText(task_id=row.task_id, text=row.text, source="public")
            for row in candidates
        ),
        method=method,
        encoder=encoder,
    )
    build_seconds = time.perf_counter() - started
    rows = []
    candidate_lookup = {row.task_id: row for row in candidates}
    for query in queries:
        started = time.perf_counter()
        result = index.search(
            TaskText(task_id=query.task_id, text=query.text, source="public"),
            k=len(candidates),
            minimum_score=None,
        )
        elapsed = time.perf_counter() - started
        rank = tuple(hit.task_id for hit in result.hits)
        metrics = {}
        for k in ks:
            metrics.update(
                ranking_metrics(rank, frozenset(query.relevant_task_ids), k=k)
            )
        rows.append(
            {
                "query_id": query.task_id,
                "family": query.family,
                "status": result.status,
                "known_rank_count": len(rank),
                "metrics": metrics,
                "relevant_ranks": {
                    key: rank.index(key) + 1 if key in rank else None
                    for key in query.relevant_task_ids
                },
                "top_hits": [
                    {"task_id": hit.task_id, "score": hit.score}
                    for hit in result.hits[: max(ks)]
                ],
                "top1_is_relevant": bool(rank and rank[0] in query.relevant_task_ids),
                "top1_negative_case_kind": (
                    (
                        candidate_lookup[rank[0]].case_kind
                        if candidate_lookup[rank[0]].family == query.family
                        else "other-family"
                    )
                    if rank and rank[0] not in query.relevant_task_ids
                    else None
                ),
                "query_seconds": elapsed,
            }
        )

    def aggregate(items):
        return {
            key: fmean(row["metrics"][key] for row in items)
            for key in items[0]["metrics"]
        }

    return {
        "dataset_id": dataset.dataset_id,
        "method": method,
        "split": split,
        "query_count": len(queries),
        "candidate_count": len(candidates),
        "family_count": len({row.family for row in queries}),
        "project_count": len({row.project for row in queries}),
        "unknown_query_count": sum(row["status"] == "unknown" for row in rows),
        "unknown_candidate_count": index.metadata["unknown_candidate_count"],
        "top1_false_association_count": sum(
            row["top1_negative_case_kind"] is not None for row in rows
        ),
        "top1_no_result_count": sum(not row["top_hits"] for row in rows),
        "top1_negative_case_counts": dict(
            sorted(
                Counter(
                    row["top1_negative_case_kind"]
                    for row in rows
                    if row["top1_negative_case_kind"] is not None
                ).items()
            )
        ),
        "metrics": aggregate(rows),
        "by_family": {
            family: aggregate([row for row in rows if row["family"] == family])
            for family in sorted({row.family for row in queries})
        },
        "queries": rows,
        "index_build_seconds": build_seconds,
        "index_metadata": index.metadata,
        "methodology": {
            "labels_used_in_ranking": False,
            "full_known_ranking": True,
            "tie_rule": "descending score, ascending candidate task ID",
            "precision_denominator": "requested k, including missing retrieval slots",
            "recall_denominator": "all independently authored relevant candidates",
            "aggregation": "macro query mean; two correlated rewrites per family",
            "uncertainty": (
                "no population confidence interval; purposive test families"
            ),
            "not_measured": [
                "agent outcome success",
                "continuation",
                "classification",
                "scope evolution",
            ],
        },
    }
