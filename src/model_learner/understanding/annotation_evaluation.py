"""Frozen retrieval decisions against separately human-reviewed task judgments.

This evaluates a shortlist policy only. Continuation, scope and difficulty are
annotation targets, not predictions manufactured from retrieval scores.
"""

from __future__ import annotations

from collections import Counter
from statistics import fmean

from model_learner.understanding.annotations import (
    AnnotationDataset,
    Split,
    content_digest,
    digest,
    require_reviewed,
)
from model_learner.understanding.retrieval import (
    DescriptionEncoder,
    TaskText,
    build_retrieval_index,
)


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _summarize(rows: list[dict]) -> dict:
    counts = Counter()
    for row in rows:
        counts.update(row["counts"])
    match = [row for row in rows if row["no_match_label"] == "no"]
    no_match = [row for row in rows if row["no_match_label"] == "yes"]
    supported_no_match = [row for row in no_match if row["query_status"] != "unknown"]
    accepted = sum(bool(row["returned_ids"]) for row in rows)
    no_match_accepted = sum(bool(row["returned_ids"]) for row in no_match)
    return {
        "query_count": len(rows),
        "counts": dict(counts),
        "precision": _ratio(counts["tp"], counts["tp"] + counts["fp"]),
        "recall": _ratio(counts["tp"], counts["tp"] + counts["fn"]),
        "false_positive_rate": _ratio(counts["fp"], counts["fp"] + counts["tn"]),
        "hard_negative_false_positive_rate": _ratio(
            counts["hard_negative_fp"], counts["hard_negative_count"]
        ),
        "coverage": _ratio(accepted, len(rows)),
        "abstention_rate": _ratio(len(rows) - accepted, len(rows)),
        "match_query_count": len(match),
        "match_abstention_rate": _ratio(
            sum(not row["returned_ids"] for row in match), len(match)
        ),
        "no_match_query_count": len(no_match),
        "no_match_false_acceptance_rate": _ratio(no_match_accepted, len(no_match)),
        "no_match_abstention_rate": _ratio(
            len(no_match) - no_match_accepted, len(no_match)
        ),
        "representable_no_match_query_count": len(supported_no_match),
        "representable_no_match_false_acceptance_rate": _ratio(
            sum(bool(row["returned_ids"]) for row in supported_no_match),
            len(supported_no_match),
        ),
        "unknown_no_match_query_count": sum(
            row["no_match_label"] == "unknown" for row in rows
        ),
        "unknown_representation_query_count": sum(
            row["query_status"] == "unknown" for row in rows
        ),
        "macro_precision_at_k": fmean(row["precision_at_k"] for row in rows)
        if rows
        else None,
        "macro_recall_on_known_targets": (
            fmean(row["recall"] for row in rows if row["recall"] is not None)
            if any(row["recall"] is not None for row in rows)
            else None
        ),
    }


def evaluate_annotations(
    dataset: AnnotationDataset,
    *,
    split: Split = "test",
    encoder: DescriptionEncoder | None = None,
) -> dict:
    # Revalidate caller-created objects and freeze before any encoding.
    dataset = AnnotationDataset.model_validate(dataset.model_dump(mode="json"))
    if dataset.freeze is None or dataset.protocol is None:
        raise ValueError("evaluation requires a frozen human-reviewed dataset")
    require_reviewed(dataset)
    if split not in ("train", "development", "test"):
        raise ValueError("unsupported evaluation split")
    protocol = dataset.protocol
    if protocol.backend == "potion":
        if encoder is None:
            raise ValueError(
                "Potion evaluation requires the explicitly loaded local encoder"
            )
        from model_learner.representation.potion import MODEL_ID

        if (
            encoder.metadata.get("revision") != protocol.model_revision
            or encoder.metadata.get("bundle_sha256") != protocol.model_sha256
            or encoder.metadata.get("model_id") != MODEL_ID
        ):
            raise ValueError("encoder identity differs from frozen protocol")
    elif encoder is not None:
        raise ValueError("lexical evaluation does not use an encoder")
    candidates = tuple(
        row
        for row in dataset.snapshots
        if row.split == split and row.role == "historical"
    )
    queries = tuple(
        row for row in dataset.snapshots if row.split == split and row.role == "query"
    )
    if not candidates or not queries:
        raise ValueError("evaluation split requires queries and historical candidates")
    index = build_retrieval_index(
        tuple(
            TaskText(task_id=row.example_id, text=row.description, source="sanitized")
            for row in candidates
        ),
        method="embedding" if protocol.backend == "potion" else protocol.backend,
        encoder=encoder,
    )
    annotations = {row.query_id: row.judgment for row in dataset.annotations}
    rows = []
    target_coverage = {
        field: Counter()
        for field in ("continuation", "scope_change", "difficulty_change")
    }
    for query in queries:
        judgment = annotations[query.example_id]
        result = index.search(
            TaskText(
                task_id=query.example_id, text=query.description, source="sanitized"
            ),
            k=protocol.k,
            minimum_score=protocol.minimum_score,
        )
        returned = {hit.task_id for hit in result.hits}
        counts = Counter(
            {
                key: 0
                for key in (
                    "tp",
                    "fp",
                    "fn",
                    "tn",
                    "unknown_label_pairs",
                    "unknown_label_returns",
                    "hard_negative_count",
                    "hard_negative_fp",
                )
            }
        )
        for pair in judgment.pairs:
            selected = pair.candidate_id in returned
            if pair.similarity == "unknown":
                counts["unknown_label_pairs"] += 1
                counts["unknown_label_returns"] += int(selected)
            else:
                positive = pair.similarity == "relevant"
                counts[
                    "tp"
                    if positive and selected
                    else "fn"
                    if positive
                    else "fp"
                    if selected
                    else "tn"
                ] += 1
            counts["hard_negative_count"] += int(pair.hard_negative)
            counts["hard_negative_fp"] += int(pair.hard_negative and selected)
            for field in target_coverage:
                target_coverage[field][getattr(pair, field)] += 1
        rows.append(
            {
                "query_id": query.example_id,
                "family": query.family,
                "no_match_label": judgment.no_match,
                "query_status": result.status,
                "abstention_reason": (
                    None
                    if result.hits
                    else "unknown_representation"
                    if result.status == "unknown"
                    else "empty_history"
                    if result.status == "empty"
                    else "score_threshold"
                ),
                "unknown_candidate_count": result.unknown_candidate_count,
                "returned_ids": [hit.task_id for hit in result.hits],
                "scores": [hit.score for hit in result.hits],
                "counts": dict(counts),
                "precision": _ratio(counts["tp"], counts["tp"] + counts["fp"]),
                "precision_at_k": counts["tp"] / protocol.k,
                "recall": _ratio(counts["tp"], counts["tp"] + counts["fn"]),
            }
        )
    families = sorted({row["family"] for row in rows})
    return {
        "schema_version": "task-annotation-evaluation/v1",
        "dataset_id": dataset.dataset_id,
        "dataset_sha256": content_digest(dataset),
        "source_kind": dataset.source_kind,
        "split": split,
        "protocol": protocol.model_dump(mode="json"),
        "candidate_corpus_sha256": digest(
            [
                {"example_id": row.example_id, "description": row.description}
                for row in candidates
            ]
        ),
        "retrieval_provenance": index.metadata,
        "summary": _summarize(rows),
        "families": {
            family: _summarize([row for row in rows if row["family"] == family])
            for family in families
        },
        "queries": rows,
        "annotation_target_coverage": {
            field: dict(counts) for field, counts in target_coverage.items()
        },
        "identity_policy": (
            "Explicit canonical task identity remains authoritative; "
            "no links are created."
        ),
        "limitations": [
            "Human identities and review independence are local operator "
            "attestations, not authentication.",
            "Unknown similarity labels are excluded from confusion denominators "
            "and reported separately.",
            "Unknown representations are operational abstentions, "
            "not calibrated no-match recognition.",
            "Precision@k counts known relevant slots over k; "
            "unknown/missing slots receive no credit.",
            "Continuation, scope and apparent difficulty are reviewed labels only; "
            "no classifier is evaluated.",
            "Correlated query rewrites are not independent samples; "
            "no population accuracy or confidence claim.",
            "Retrieval accuracy is not evidence of better model-utility prediction.",
        ],
    }
