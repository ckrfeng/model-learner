"""Optional local description retrieval, separate from identity and outcomes.

Callers explicitly supply declared, public or sanitized text and select their historical
candidate cohort. Nothing here reads transcripts, ledger rows, labels or links.
Scores measure text relatedness, never continuation, success or confidence.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, StrictStr

MAX_TASKS = 10_000
MAX_DIMENSIONS = 4096
Method = Literal["text", "tfidf", "embedding"]


class TaskText(BaseModel):
    """An explicit description declaration; source is a caller attestation.

    Declared text may be private and remains local. This contract does not
    automatically sanitize arbitrary text. Missing, blank
    and punctuation-only descriptions have unknown representations.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)
    task_id: StrictStr = Field(min_length=1, max_length=128, pattern=r"\S")
    text: StrictStr | None = Field(default=None, max_length=4096)
    source: Literal["declared", "public", "sanitized"]


class DescriptionEncoder(Protocol):
    """The existing LocalCPUEncoder / PotionCPUEncoder interface."""

    dimensions: int
    metadata: dict

    def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]: ...


@dataclass(frozen=True)
class RetrievalHit:
    task_id: str
    score: float


@dataclass(frozen=True)
class RetrievalResult:
    method: Method
    status: Literal["ok", "unknown", "no_match", "empty"]
    hits: tuple[RetrievalHit, ...]
    candidate_count: int
    unknown_candidate_count: int


_EXPLANATIONS = {
    "text": "Jaccard overlap of lowercase alphanumeric token sets (0 to 1).",
    "tfidf": (
        "Cosine similarity of token counts weighted by corpus-only smoothed IDF "
        "(0 to 1); the corpus fixes weights, with no outcome labels."
    ),
    "embedding": (
        "Cosine similarity of frozen local CPU description embeddings (-1 to 1)."
    ),
}


def _tokens(text: str | None) -> tuple[str, ...]:
    return tuple(re.findall(r"[^\W_]+", text.casefold())) if text else ()


def _normalize_sparse(vector: dict[str, float]) -> dict[str, float] | None:
    norm = math.sqrt(math.fsum(value * value for value in vector.values()))
    return {key: value / norm for key, value in vector.items()} if norm else None


def _embedding_vectors(
    encoder: DescriptionEncoder, texts: tuple[str, ...]
) -> tuple[tuple[float, ...] | None, ...]:
    dimensions = encoder.dimensions
    if type(dimensions) is not int or not 1 <= dimensions <= MAX_DIMENSIONS:
        raise ValueError("encoder dimensions must be bounded positive integers")
    output = encoder.encode(texts)
    if len(output) != len(texts):
        raise ValueError("encoder output count does not match descriptions")
    result = []
    for row in output:
        if len(row) != dimensions:
            raise ValueError("encoder output dimensions do not match declaration")
        if any(isinstance(value, (bool, str, bytes)) for value in row):
            raise ValueError("encoder output must contain finite numeric values")
        try:
            values = tuple(float(value) for value in row)
        except (TypeError, ValueError, OverflowError) as exc:
            raise ValueError(
                "encoder output must contain finite numeric values"
            ) from exc
        if not all(math.isfinite(value) for value in values):
            raise ValueError("encoder output must contain finite numeric values")
        # hypot avoids overflow/underflow for finite unnormalized protocol outputs.
        norm = math.hypot(*values)
        if not math.isfinite(norm):
            raise ValueError("encoder output norm must be finite")
        result.append(tuple(value / norm for value in values) if norm else None)
    return tuple(result)


class RetrievalIndex:
    """A bounded in-memory index. No imports of optional model runtimes.

    IDs determine self exclusion and tie order only. Source attestations and
    model identity are provenance, never ranking features. Descriptions remain
    in memory; results and metadata do not include the supplied text.
    """

    def __init__(
        self,
        tasks: tuple[TaskText, ...],
        *,
        method: Method,
        encoder: DescriptionEncoder | None = None,
    ):
        if method not in _EXPLANATIONS:
            raise ValueError("unknown retrieval method")
        if len(tasks) > MAX_TASKS or any(not isinstance(x, TaskText) for x in tasks):
            raise ValueError("retrieval requires a bounded collection of TaskText")
        if len({task.task_id for task in tasks}) != len(tasks):
            raise ValueError("retrieval task identifiers must be unique")
        if method == "embedding" and encoder is None:
            raise ValueError("embedding retrieval requires an explicit local encoder")
        if method != "embedding" and encoder is not None:
            raise ValueError("lexical retrieval does not use an encoder")
        self.method = method
        self._encoder = encoder
        self._tasks = tuple(sorted(tasks, key=lambda task: task.task_id))
        self._idf: dict[str, float] = {}
        tokens = tuple(_tokens(task.text) for task in self._tasks)
        self._vectors: dict[str, dict | frozenset | tuple | None] = {}
        self.metadata = {
            "version": "task-description-retrieval/v1",
            "method": method,
            "score_explanation": _EXPLANATIONS[method]
            + " Relatedness is an inference; it does not establish task identity, "
            "continuation, verification or outcome success.",
            "corpus_size": len(tasks),
            "source_counts": {
                source: sum(task.source == source for task in tasks)
                for source in ("declared", "public", "sanitized")
            },
            "tokenization": "Unicode alphanumeric tokens; casefold; no stemming",
        }
        if method == "tfidf":
            known = [terms for terms in tokens if terms]
            document_frequency = Counter(term for terms in known for term in set(terms))
            self._idf = {
                term: math.log((1 + len(known)) / (1 + count)) + 1
                for term, count in document_frequency.items()
            }
            self.metadata["idf_fit"] = "supplied nonempty candidate corpus only"
        if method == "embedding":
            assert encoder is not None
            if type(encoder.dimensions) is not int or not (
                1 <= encoder.dimensions <= MAX_DIMENSIONS
            ):
                raise ValueError("encoder dimensions must be bounded positive integers")
            valid = [
                task for task, terms in zip(self._tasks, tokens, strict=True) if terms
            ]
            vectors = _embedding_vectors(encoder, tuple(task.text for task in valid))
            self._vectors = dict(
                zip((task.task_id for task in valid), vectors, strict=True)
            )
            self._vectors.update(
                (task.task_id, None)
                for task in self._tasks
                if task.task_id not in self._vectors
            )
            # Only the existing loader's model identity enters report provenance.
            self.metadata["encoder"] = {
                key: encoder.metadata.get(key)
                for key in (
                    "model_id",
                    "revision",
                    "bundle_sha256",
                    "device",
                    "dimensions",
                )
            }
        else:
            self._vectors = {
                task.task_id: self._lexical_vector(terms)
                for task, terms in zip(self._tasks, tokens, strict=True)
            }
        self.metadata["unknown_candidate_count"] = sum(
            vector is None for vector in self._vectors.values()
        )

    def _lexical_vector(self, terms: tuple[str, ...]) -> dict | frozenset | None:
        if not terms:
            return None
        if self.method == "text":
            return frozenset(terms)
        return _normalize_sparse(
            {
                term: count * self._idf[term]
                for term, count in Counter(terms).items()
                if term in self._idf
            }
        )

    def search(
        self,
        query: TaskText,
        *,
        k: int = 5,
        minimum_score: float | None = 0.0,
    ) -> RetrievalResult:
        """Rank eligible descriptions; ties use IDs, never input order.

        Default strictly-positive filtering avoids presenting arbitrary zero
        matches as associations. Evaluation may explicitly request all known
        scores with minimum_score=None. Unknown vectors are never zero scores.
        """
        if not isinstance(query, TaskText):
            raise ValueError("query must be an explicit TaskText")
        if type(k) is not int or not 1 <= k <= MAX_TASKS:
            raise ValueError("retrieval k must be a bounded positive integer")
        if minimum_score is not None and (
            isinstance(minimum_score, bool)
            or not isinstance(minimum_score, (int, float))
            or not math.isfinite(minimum_score)
            or not -1 <= minimum_score <= 1
        ):
            raise ValueError("minimum score must be finite and between -1 and 1")
        candidates = {
            key: vector for key, vector in self._vectors.items() if key != query.task_id
        }
        unknown = sum(vector is None for vector in candidates.values())

        def result(status, hits=()):
            return RetrievalResult(self.method, status, hits, len(candidates), unknown)

        if not candidates:
            return result("empty")
        if unknown == len(candidates):
            return result("unknown")
        terms = _tokens(query.text)
        if not terms:
            return result("unknown")
        if self.method == "embedding":
            assert self._encoder is not None
            vector = _embedding_vectors(self._encoder, (query.text,))[0]
        else:
            vector = self._lexical_vector(terms)
        if vector is None:
            return result("unknown")
        hits = []
        for key, candidate in candidates.items():
            if candidate is None:
                continue
            if self.method == "text":
                score = len(vector & candidate) / len(vector | candidate)
            elif self.method == "tfidf":
                score = math.fsum(
                    value * candidate.get(term, 0) for term, value in vector.items()
                )
            else:
                score = math.fsum(a * b for a, b in zip(vector, candidate, strict=True))
            score = min(1.0, max(-1.0, score))
            if minimum_score is None or score > minimum_score:
                hits.append(RetrievalHit(key, score))
        hits.sort(key=lambda hit: (-hit.score, hit.task_id))
        return result("ok" if hits else "no_match", tuple(hits[:k]))


def build_retrieval_index(
    tasks: tuple[TaskText, ...],
    *,
    method: Method = "text",
    encoder: DescriptionEncoder | None = None,
) -> RetrievalIndex:
    return RetrievalIndex(tasks, method=method, encoder=encoder)
