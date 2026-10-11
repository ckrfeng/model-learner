"""Retrieval contract tests; protocol fixtures make no pretrained accuracy claims."""

from dataclasses import asdict

import pytest
from pydantic import ValidationError

from model_learner.understanding import TaskText, build_retrieval_index


def description(task_id, text, source="public"):
    return TaskText(task_id=task_id, text=text, source=source)


class ProtocolEncoder:
    dimensions = 2
    metadata = {
        "model_id": "protocol-fixture",
        "revision": "fixture-only",
        "device": "cpu",
        "dimensions": 2,
        "private_text": "never emitted",
    }

    def __init__(self, vectors=None):
        self.vectors = vectors or {
            "race": (2.0, 0.0),
            "concurrent": (3.0, 0.0),
            "render": (0.0, 1.0),
            "opposite": (-1.0, 0.0),
            "unrecognized": (0.0, 0.0),
        }
        self.calls = []

    def encode(self, texts):
        self.calls.append(texts)
        return tuple(self.vectors[text] for text in texts)


@pytest.mark.parametrize("method", ["text", "tfidf", "embedding"])
def test_rankings_are_deterministic_and_exclude_self(method):
    tasks = (
        description("z", "race"),
        description("self", "race"),
        description("a", "race"),
        description("unrelated", "render"),
    )
    options = {"encoder": ProtocolEncoder()} if method == "embedding" else {}
    index = build_retrieval_index(tasks, method=method, **options)
    forward = index.search(description("self", "race"))
    reverse = build_retrieval_index(tuple(reversed(tasks)), method=method, **options)
    assert forward == reverse.search(description("self", "race"))
    assert [hit.task_id for hit in forward.hits] == ["a", "z"]
    assert [hit.score for hit in forward.hits] == pytest.approx([1, 1])
    assert forward.candidate_count == 3
    assert forward.unknown_candidate_count == 0


def test_text_baseline_is_token_jaccard_without_semantic_claims():
    index = build_retrieval_index((description("history", "Fix RACE race"),))
    result = index.search(description("query", "race condition"))
    assert result.hits[0].score == pytest.approx(1 / 3)
    assert "does not establish task identity" in index.metadata["score_explanation"]
    assert index.search(description("query", "concurrent updates")).status == "no_match"


def test_tfidf_weights_rare_corpus_terms_and_does_not_refit_queries():
    index = build_retrieval_index(
        (
            description("rare", "shared rare"),
            description("shared-1", "shared"),
            description("shared-2", "shared"),
        ),
        method="tfidf",
    )
    first = index.search(description("query", "shared rare"))
    index.search(description("other", "outofvocabulary"))
    assert index.search(description("query", "shared rare")) == first
    assert first.hits[0].task_id == "rare"
    assert first.hits[1].score < 2**-0.5
    assert index.metadata["idf_fit"] == "supplied nonempty candidate corpus only"


def test_embedding_protocol_cosine_and_explicit_full_ranking():
    encoder = ProtocolEncoder()
    index = build_retrieval_index(
        (
            description("related", "concurrent"),
            description("orthogonal", "render"),
            description("opposed", "opposite"),
        ),
        method="embedding",
        encoder=encoder,
    )
    query = description("query", "race")
    assert [hit.task_id for hit in index.search(query).hits] == ["related"]
    full = index.search(query, minimum_score=None)
    assert [hit.task_id for hit in full.hits] == ["related", "orthogonal", "opposed"]
    assert [hit.score for hit in full.hits] == pytest.approx([1, 0, -1])
    assert "private_text" not in index.metadata["encoder"]
    assert index.metadata["encoder"]["revision"] == "fixture-only"


@pytest.mark.parametrize("text", [None, "", " \t", "!?_"])
@pytest.mark.parametrize("method", ["text", "tfidf", "embedding"])
def test_missing_descriptions_are_unknown_and_not_encoded(text, method):
    encoder = ProtocolEncoder()
    options = {"encoder": encoder} if method == "embedding" else {}
    index = build_retrieval_index(
        (description("known", "race"), description("missing", text)),
        method=method,
        **options,
    )
    result = index.search(description("query", text), minimum_score=None)
    assert result.status == "unknown"
    assert result.hits == ()
    assert result.unknown_candidate_count == 1
    if method == "embedding":
        assert encoder.calls == [("race",)]


def test_zero_embeddings_are_unknown_never_zero_negative_evidence():
    index = build_retrieval_index(
        (description("missing", "unrecognized"), description("known", "render")),
        method="embedding",
        encoder=ProtocolEncoder(),
    )
    assert index.search(description("query", "unrecognized")).status == "unknown"
    result = index.search(description("query", "race"), minimum_score=None)
    assert result.unknown_candidate_count == 1
    assert [hit.task_id for hit in result.hits] == ["known"]


@pytest.mark.parametrize("method", ["text", "tfidf", "embedding"])
def test_empty_and_unknown_corpora_are_distinct(method):
    options = {"encoder": ProtocolEncoder()} if method == "embedding" else {}
    query = description("query", "race")
    assert (
        build_retrieval_index((), method=method, **options).search(query).status
        == "empty"
    )
    unknown = build_retrieval_index(
        (description("missing", None),), method=method, **options
    ).search(query)
    assert unknown.status == "unknown"
    assert unknown.unknown_candidate_count == 1


@pytest.mark.parametrize(
    "vector", [(float("nan"), 0), (float("inf"), 0), (1,), (True, 0), ("1", 0)]
)
def test_invalid_embedding_vectors_fail_closed(vector):
    with pytest.raises(ValueError, match="encoder output"):
        build_retrieval_index(
            (description("candidate", "bad"),),
            method="embedding",
            encoder=ProtocolEncoder({"bad": vector}),
        )


def test_encoder_batch_and_dimension_bounds_fail_closed():
    encoder = ProtocolEncoder()
    encoder.dimensions = 4097
    with pytest.raises(ValueError, match="dimensions"):
        build_retrieval_index((), method="embedding", encoder=encoder)
    encoder.dimensions = 2
    encoder.encode = lambda texts: ()
    with pytest.raises(ValueError, match="count"):
        build_retrieval_index(
            (description("candidate", "race"),), method="embedding", encoder=encoder
        )


def test_optional_encoder_is_explicit_and_lexical_needs_no_runtime():
    with pytest.raises(ValueError, match="explicit local encoder"):
        build_retrieval_index((), method="embedding")
    with pytest.raises(ValueError, match="does not use an encoder"):
        build_retrieval_index((), encoder=ProtocolEncoder())
    with pytest.raises(ValueError, match="unknown retrieval method"):
        build_retrieval_index((), method="unsupported")


def test_bounded_inputs_reject_hidden_label_fields_and_duplicates():
    with pytest.raises(ValidationError):
        description("query", "a" * 4097)
    with pytest.raises(ValidationError):
        description(" ", "race")
    with pytest.raises(ValidationError):
        TaskText(task_id="query", text="race", source="raw")
    with pytest.raises(ValidationError):
        TaskText(task_id="query", text="race", source="public", outcome="success")
    with pytest.raises(ValueError, match="unique"):
        build_retrieval_index((description("a", "race"), description("a", "render")))
    with pytest.raises(ValueError, match="bounded"):
        build_retrieval_index(tuple(description(str(i), None) for i in range(10001)))


@pytest.mark.parametrize("k", [0, -1, 10001, True, 1.5])
def test_search_k_is_bounded(k):
    with pytest.raises(ValueError, match="k must"):
        build_retrieval_index(()).search(description("query", "race"), k=k)


@pytest.mark.parametrize("threshold", [float("nan"), float("inf"), 2, -2, True, "0"])
def test_score_threshold_is_finite_and_bounded(threshold):
    with pytest.raises(ValueError, match="minimum score"):
        build_retrieval_index(()).search(
            description("query", "race"), minimum_score=threshold
        )


def test_output_contains_ids_and_scores_only_without_text_or_identity_mutations():
    task = description("different-task", "confidential objective", source="declared")
    index = build_retrieval_index((task,))
    result = index.search(description("query", "confidential objective"))
    assert asdict(result)["hits"] == ({"task_id": "different-task", "score": 1},)
    assert "confidential objective" not in repr(asdict(result)) + repr(index.metadata)
    assert task.task_id == "different-task"
    assert index.metadata["source_counts"]["declared"] == 1
