"""Metric validity, frozen relevance provenance and annotation leakage guards."""

import copy
import hashlib
import json
import math
import os
from pathlib import Path

import pytest

from model_learner.understanding.evaluation import (
    RetrievalDataset,
    evaluate_retrieval,
    load_retrieval_dataset,
    ranking_metrics,
)

FIXTURES = Path(__file__).parents[1] / "fixtures" / "understanding"


def fixture():
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    return load_retrieval_dataset(
        FIXTURES / "retrieval_v1.json", expected_sha256=manifest["sha256"]
    )[0]


def test_frozen_dataset_manifest_counts_and_independent_annotation():
    dataset = fixture()
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    assert manifest["frozen_before_encoder_execution"]
    assert manifest["no_test_threshold_selection"]
    assert len(dataset.queries) == 16
    assert len(dataset.candidates) == 48
    assert "Codex agent" in dataset.provenance["label_method"]
    assert "no evaluated-encoder-derived" in dataset.provenance["label_method"]
    assert {row.case_kind for row in dataset.candidates} == {
        "relevant-paraphrase",
        "related-independent",
        "wording-trap",
        "same-project",
        "domain-neighbor",
        "scope-diverged",
    }
    assert all(len(query.relevant_task_ids) == 2 for query in dataset.queries)
    assert all(candidate.judgment_rationale for candidate in dataset.candidates)
    assert (
        hashlib.sha256((FIXTURES / "retrieval_v1.json").read_bytes()).hexdigest()
        == manifest["sha256"]
    )


def test_fixture_tamper_is_rejected_before_encoding(tmp_path):
    path = tmp_path / "data.json"
    path.write_bytes((FIXTURES / "retrieval_v1.json").read_bytes() + b" ")
    manifest = json.loads((FIXTURES / "manifest.json").read_text())
    with pytest.raises(ValueError, match="frozen dataset hash"):
        load_retrieval_dataset(path, expected_sha256=manifest["sha256"])


def test_duplicate_json_keys_are_rejected(tmp_path):
    path = tmp_path / "data.json"
    path.write_text('{"schema_version":1,"schema_version":1}')
    with pytest.raises(ValueError, match="duplicate evaluation JSON"):
        load_retrieval_dataset(path)


@pytest.mark.parametrize("field", ["family", "project", "rewrite_group"])
def test_development_test_annotation_cohorts_cannot_overlap(field):
    value = fixture().model_dump(mode="json")
    development = next(row for row in value["queries"] if row["split"] == "development")
    test = next(row for row in value["queries"] if row["split"] == "test")
    test[field] = development[field]
    with pytest.raises(ValueError, match=f"{field} overlap"):
        RetrievalDataset.model_validate(value)


@pytest.mark.parametrize("mode", ["foreign-split", "absent", "duplicate", "query-self"])
def test_invalid_relevance_targets_fail(mode):
    value = fixture().model_dump(mode="json")
    query = next(row for row in value["queries"] if row["split"] == "test")
    if mode == "foreign-split":
        query["relevant_task_ids"] = [value["candidates"][0]["task_id"]]
    elif mode == "absent":
        query["relevant_task_ids"] = ["no-such-candidate"]
    elif mode == "duplicate":
        query["relevant_task_ids"] *= 2
    else:
        value["candidates"][0]["task_id"] = query["task_id"]
    with pytest.raises(ValueError):
        RetrievalDataset.model_validate(value)


def test_binary_ranking_metrics_exact_denominators_and_missing_slots():
    metrics = ranking_metrics(("negative", "a", "b"), frozenset({"a", "b"}), k=3)
    assert metrics["precision_at_3"] == 2 / 3
    assert metrics["recall_at_3"] == 1
    assert metrics["mrr"] == 0.5
    assert metrics["ndcg_at_3"] == pytest.approx(
        (1 / math.log2(3) + 0.5) / (1 + 1 / math.log2(3))
    )
    truncated = ranking_metrics(("a",), frozenset({"a", "b"}), k=3)
    assert truncated["precision_at_3"] == 1 / 3
    assert truncated["recall_at_3"] == 0.5
    assert ranking_metrics((), frozenset({"a"}), k=3) == {
        "precision_at_3": 0,
        "recall_at_3": 0,
        "ndcg_at_3": 0,
        "mrr": 0,
    }


@pytest.mark.parametrize("k", [0, -1, True, 1.5])
def test_invalid_metric_k_fails(k):
    with pytest.raises(ValueError):
        ranking_metrics(("a",), frozenset({"a"}), k=k)


def test_metric_invalid_labels_and_duplicate_rank_fail():
    with pytest.raises(ValueError):
        ranking_metrics(("a",), frozenset(), k=1)
    with pytest.raises(ValueError):
        ranking_metrics(("a", "a"), frozenset({"a"}), k=1)


def test_label_edits_change_metrics_without_changing_text_rankings():
    dataset = fixture()
    before = evaluate_retrieval(dataset, method="tfidf")
    value = copy.deepcopy(dataset.model_dump(mode="json"))
    # Deliberately contradict relevance, retaining all actual ranking inputs.
    for query in value["queries"]:
        if query["split"] == "test":
            query["relevant_task_ids"] = [query["family"] + "-c3"]
    after = evaluate_retrieval(RetrievalDataset.model_validate(value), method="tfidf")
    assert [q["top_hits"] for q in before["queries"]] == [
        q["top_hits"] for q in after["queries"]
    ]
    assert before["metrics"] != after["metrics"]
    assert after["methodology"]["labels_used_in_ranking"] is False


def test_candidate_family_project_and_rationale_do_not_affect_ranking():
    dataset = fixture()
    before = evaluate_retrieval(dataset, method="text")
    value = copy.deepcopy(dataset.model_dump(mode="json"))
    for candidate in value["candidates"]:
        candidate["family"] = candidate["split"] + "-arbitrary-family"
        candidate["project"] = candidate["split"] + "-arbitrary-project"
        candidate["judgment_rationale"] = "Annotation hidden from retriever."
    after = evaluate_retrieval(RetrievalDataset.model_validate(value), method="text")
    assert before["metrics"] == after["metrics"]
    assert [q["top_hits"] for q in before["queries"]] == [
        q["top_hits"] for q in after["queries"]
    ]


class ZeroEncoder:
    dimensions = 2
    metadata = {"model_id": "protocol-only-zero-encoder"}

    def encode(self, texts):
        return tuple((0.0, 0.0) for _ in texts)


def test_unknown_embeddings_are_missing_ranks_not_arbitrary_zero_score_matches():
    result = evaluate_retrieval(fixture(), method="embedding", encoder=ZeroEncoder())
    assert result["unknown_query_count"] == 12
    assert result["unknown_candidate_count"] == 36
    assert result["top1_false_association_count"] == 0
    assert result["top1_no_result_count"] == 12
    assert all(value == 0 for value in result["metrics"].values())
    assert all(
        all(rank is None for rank in row["relevant_ranks"].values())
        for row in result["queries"]
    )


@pytest.mark.parametrize("method", ["text", "tfidf"])
def test_frozen_reference_lexical_metrics_and_rankings_reproduce(method):
    reference = json.loads((FIXTURES / "reference.json").read_text())
    expected = next(
        worker for worker in reference["workers"] if worker["method"] == method
    )["reports"]["test"]
    actual = evaluate_retrieval(fixture(), method=method)
    assert actual["metrics"] == expected["metrics"]
    assert [q["top_hits"] for q in actual["queries"]] == [
        q["top_hits"] for q in expected["queries"]
    ]
    assert actual["query_count"] == 12
    assert actual["family_count"] == actual["project_count"] == 6
    assert actual["candidate_count"] == 36


def test_actual_potion_relevance_metrics_match_frozen_reference():
    path = os.environ.get("MODEL_LEARNER_TEST_POTION_PATH")
    if path is None:
        pytest.skip("explicit local Potion test path not supplied")
    from model_learner.representation.potion import MODEL_REVISION, load_potion_encoder

    encoder = load_potion_encoder(
        path,
        expected_sha256="930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2",
        revision=MODEL_REVISION,
    )
    reference = json.loads((FIXTURES / "reference.json").read_text())
    expected = next(
        worker for worker in reference["workers"] if worker["method"] == "embedding"
    )["reports"]["test"]
    actual = evaluate_retrieval(fixture(), method="embedding", encoder=encoder)
    assert actual["metrics"] == expected["metrics"]
    assert [q["top_hits"] for q in actual["queries"]] == [
        q["top_hits"] for q in expected["queries"]
    ]
