"""Review integrity, leakage gates and exact retrieval-decision denominators."""

import json
from copy import deepcopy
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from model_learner.understanding.annotation_evaluation import evaluate_annotations
from model_learner.understanding.annotations import (
    AnnotationDataset,
    QueryJudgment,
    add_review,
    content_digest,
    freeze_annotations,
    load_annotations,
    load_json,
    prepare_annotations,
    set_judgment,
    write_annotations,
)


def seed():
    snapshots = []
    for split, texts in (
        (
            "development",
            (
                "beta repair",
                "beta documentation",
                "zeta",
                "repair beta",
                "documentation beta",
            ),
        ),
        ("test", ("alpha repair", "alpha docs", "other", "repair alpha", "docs alpha")),
    ):
        for number, text in enumerate(texts):
            snapshots.append(
                {
                    "example_id": f"{split}-{number}",
                    "role": "historical" if number < 3 else "query",
                    "description": text,
                    "split": split,
                    "project": split,
                    "family": split,
                    "lineage": split,
                    "available_at": "2026-01-01T00:00:00Z"
                    if number < 3
                    else "2026-01-02T00:00:00Z",
                    "origin": {
                        "source_ref": "constructed-test",
                        "source_sha256": "a" * 64,
                        "locator": f"{split}-{number}",
                        "authorship": "agent",
                    },
                }
            )
    return AnnotationDataset.model_validate(
        {
            "schema_version": "task-annotations/v1",
            "dataset_id": "unit-v1",
            "source_kind": "benchmark",
            "description": "Synthetic schema tests; no actual human-reviewed data.",
            "snapshots": snapshots,
        }
    )


def judgment(split, number):
    return QueryJudgment.model_validate(
        {
            "no_match": "no" if number == 3 else "yes",
            "rationale": "Synthetic test judgments.",
            "pairs": [
                {
                    "candidate_id": f"{split}-{candidate}",
                    "similarity": "relevant"
                    if candidate == 0 and number == 3
                    else "irrelevant",
                    "continuation": "unknown",
                    "scope_change": "unknown",
                    "difficulty_change": "unknown",
                    "hard_negative": candidate == 1,
                    "rationale": "Same wording may have a different objective.",
                    "evidence_refs": [f"{split}-{candidate}", f"{split}-{number}"],
                }
                for candidate in range(3)
            ],
        }
    )


def reviewed(dataset=None, *, author_kind="human", reviewer_kind="human"):
    dataset = dataset or seed()
    for split in ("development", "test"):
        for number in (3, 4):
            key = f"{split}-{number}"
            dataset = set_judgment(
                dataset,
                key,
                judgment(split, number),
                annotator="test-author",
                actor_kind=author_kind,
            )
            dataset = add_review(
                dataset,
                key,
                reviewer="test-reviewer",
                actor_kind=reviewer_kind,
                decision="accept",
                note="Synthetic test review, not real human data.",
            )
    return dataset


def frozen(dataset=None, **options):
    return freeze_annotations(
        dataset or reviewed(),
        backend="text",
        k=1,
        minimum_score=options.pop("minimum_score", 0.0),
        selection_note="Fixed synthetic protocol.",
        **options,
    )


def test_exact_precision_recall_fpr_and_no_match_denominators():
    dataset = frozen()
    result = evaluate_annotations(dataset)
    summary = result["summary"]
    assert summary["counts"] == {
        "tp": 1,
        "fp": 1,
        "fn": 0,
        "tn": 4,
        "unknown_label_pairs": 0,
        "unknown_label_returns": 0,
        "hard_negative_count": 2,
        "hard_negative_fp": 1,
    }
    assert summary["precision"] == 0.5
    assert summary["recall"] == 1
    assert summary["false_positive_rate"] == 0.2
    assert summary["hard_negative_false_positive_rate"] == 0.5
    assert summary["no_match_false_acceptance_rate"] == 1
    assert summary["coverage"] == 1
    assert summary["macro_precision_at_k"] == 0.5
    assert result["queries"][1]["recall"] is None
    assert result["dataset_sha256"] == content_digest(dataset)
    assert "model-utility prediction" in result["limitations"][-1]


def test_strict_threshold_and_all_abstain_do_not_get_retrieval_credit():
    result = evaluate_annotations(frozen(minimum_score=1.0))
    summary = result["summary"]
    assert summary["precision"] is None
    assert summary["recall"] == 0
    assert summary["false_positive_rate"] == 0
    assert summary["coverage"] == 0
    assert summary["abstention_rate"] == 1
    assert summary["match_abstention_rate"] == 1
    assert summary["no_match_false_acceptance_rate"] == 0
    assert {row["abstention_reason"] for row in result["queries"]} == {
        "score_threshold"
    }


def test_unknown_labels_are_excluded_and_unknown_representation_is_separate():
    data = seed().model_dump(mode="json")
    data["snapshots"][8]["description"] = "!!!"
    dataset = reviewed(AnnotationDataset.model_validate(data))
    result = evaluate_annotations(frozen(dataset))
    assert result["queries"][0]["query_status"] == "unknown"
    assert result["queries"][0]["recall"] == 0
    assert result["summary"]["unknown_representation_query_count"] == 1
    unknown = judgment("test", 4).model_dump(mode="json")
    unknown["no_match"] = "unknown"
    unknown["pairs"][1]["similarity"] = "unknown"
    unknown["pairs"][1]["hard_negative"] = False
    dataset = set_judgment(
        dataset,
        "test-4",
        QueryJudgment.model_validate(unknown),
        annotator="test-author",
        actor_kind="human",
    )
    dataset = add_review(
        dataset,
        "test-4",
        reviewer="test-reviewer",
        actor_kind="human",
        decision="accept",
        note="Test reviewed unknown.",
    )
    summary = evaluate_annotations(frozen(dataset))["summary"]
    assert summary["counts"]["unknown_label_returns"] == 1
    assert summary["counts"]["fp"] == 0
    assert summary["precision"] is None
    assert summary["no_match_false_acceptance_rate"] is None
    assert summary["unknown_no_match_query_count"] == 1


@pytest.mark.parametrize(
    "field",
    ["project", "family", "lineage", "description", "canonical_task_id", "origin"],
)
def test_cross_split_leakage_rejected(field):
    data = seed().model_dump(mode="json")
    if field == "canonical_task_id":
        data["snapshots"][0][field] = str(uuid4())
    data["snapshots"][5][field] = deepcopy(data["snapshots"][0][field])
    with pytest.raises(ValidationError, match="overlap"):
        AnnotationDataset.model_validate(data)


def test_future_candidate_and_fact_evidence_rejected():
    data = seed().model_dump(mode="json")
    data["snapshots"][0]["available_at"] = "2026-01-03T00:00:00Z"
    with pytest.raises(ValidationError, match="postdate"):
        reviewed(AnnotationDataset.model_validate(data))
    data = seed().model_dump(mode="json")
    data["snapshots"][0]["facts"] = [
        {
            "evidence_id": "fact",
            "statement": "Command exit zero.",
            "origin": deepcopy(data["snapshots"][0]["origin"]),
            "available_at": "2026-01-02T00:00:00Z",
            "source_kind": "simulated",
        }
    ]
    with pytest.raises(ValidationError, match="checkpoint"):
        AnnotationDataset.model_validate(data)


@pytest.mark.parametrize("value", ["test-author", " TEST-AUTHOR "])
def test_independent_review_disallows_self_review(value):
    dataset = reviewed()
    with pytest.raises(ValidationError, match="independent reviewer"):
        add_review(
            dataset,
            "test-3",
            reviewer=value,
            actor_kind="human",
            decision="accept",
            note="test",
        )


@pytest.mark.parametrize("author,reviewer", [("agent", "human"), ("human", "agent")])
def test_machine_authorship_or_review_is_never_human_annotation_evidence(
    author, reviewer
):
    with pytest.raises(ValueError, match="human"):
        frozen(reviewed(author_kind=author, reviewer_kind=reviewer))


def test_rejection_or_missing_annotation_prevents_freeze():
    dataset = add_review(
        reviewed(),
        "test-3",
        reviewer="third-reviewer",
        actor_kind="human",
        decision="reject",
        note="Unresolved disagreement.",
    )
    with pytest.raises(ValueError, match="rejected"):
        frozen(dataset)
    with pytest.raises(ValueError, match="all queries"):
        frozen(seed())


@pytest.mark.parametrize("change", ["labels", "description", "actor", "time"])
def test_context_bound_reviews_detect_edits(change):
    data = reviewed().model_dump(mode="json")
    if change == "labels":
        data["annotations"][0]["judgment"]["pairs"][0]["difficulty_change"] = "harder"
    elif change == "description":
        data["snapshots"][0]["description"] += " changed"
    elif change == "actor":
        data["annotations"][0]["actor_kind"] = "agent"
    else:
        data["annotations"][0]["annotated_at"] = "2026-01-03T00:00:00Z"
    with pytest.raises(ValidationError, match="context"):
        AnnotationDataset.model_validate(data)


def test_label_revision_invalidates_current_reviews_but_parent_is_retained(tmp_path):
    dataset = reviewed()
    old = content_digest(dataset)
    write_annotations(dataset, tmp_path / "old.json")
    revised = set_judgment(
        dataset,
        "test-3",
        judgment("test", 3),
        annotator="test-author",
        actor_kind="human",
    )
    assert revised.parent_sha256 == old
    assert not any(row.query_id == "test-3" for row in revised.reviews)
    assert load_annotations(tmp_path / "old.json") == dataset
    with pytest.raises(ValueError, match="accepting human"):
        frozen(revised)


def test_freeze_hash_and_exclusive_file_and_immutable_revisions(tmp_path):
    dataset = frozen()
    path = tmp_path / "frozen.json"
    write_annotations(dataset, path)
    assert load_annotations(path) == dataset
    with pytest.raises(FileExistsError):
        write_annotations(dataset, path)
    for field, value in (
        ("description", "Changed note"),
        ("protocol", {**dataset.protocol.model_dump(), "k": 2}),
    ):
        data = dataset.model_dump(mode="json")
        data[field] = value
        with pytest.raises(ValidationError):
            AnnotationDataset.model_validate(data)
    with pytest.raises(ValueError, match="immutable"):
        set_judgment(
            dataset, "test-3", judgment("test", 3), annotator="x", actor_kind="human"
        )
    with pytest.raises(ValueError, match="frozen"):
        evaluate_annotations(reviewed())


@pytest.mark.parametrize(
    "mutation",
    [
        "missing",
        "duplicate",
        "unknown_reference",
        "no_match",
        "hard_negative",
        "provenance",
    ],
)
def test_bad_labels_never_become_complete_negative_evidence(mutation):
    data = judgment("test", 3).model_dump(mode="json")
    if mutation == "missing":
        data["pairs"].pop()
    elif mutation == "duplicate":
        data["pairs"].append(deepcopy(data["pairs"][0]))
    elif mutation == "unknown_reference":
        data["pairs"][0]["evidence_refs"] = ["absent"]
    elif mutation == "no_match":
        data["no_match"] = "yes"
    elif mutation == "hard_negative":
        data["pairs"][0]["hard_negative"] = True
    else:
        data["pairs"][0]["provenance"] = "observed"
    with pytest.raises(ValidationError):
        set_judgment(
            seed(),
            "test-3",
            QueryJudgment.model_validate(data),
            annotator="test-author",
            actor_kind="human",
        )


def test_declared_task_identity_cannot_be_overridden_by_continuation_label():
    data = seed().model_dump(mode="json")
    data["snapshots"][5]["canonical_task_id"] = str(uuid4())
    data["snapshots"][8]["canonical_task_id"] = str(uuid4())
    label = judgment("test", 3).model_dump(mode="json")
    label["pairs"][0]["continuation"] = "yes"
    with pytest.raises(ValidationError, match="declared task IDs"):
        set_judgment(
            AnnotationDataset.model_validate(data),
            "test-3",
            QueryJudgment.model_validate(label),
            annotator="test-author",
            actor_kind="human",
        )


def test_labels_group_names_and_evidence_do_not_change_rankings():
    dataset = reviewed()
    before = evaluate_annotations(frozen(dataset))["queries"]
    value = dataset.model_dump(mode="json")
    value["reviews"] = []
    for row in value["snapshots"]:
        row["family"] += "-renamed"
    for annotation in value["annotations"]:
        for pair in annotation["judgment"]["pairs"]:
            pair["difficulty_change"] = "harder"
    changed = AnnotationDataset.model_validate(value)
    for annotation in changed.annotations:
        changed = add_review(
            changed,
            annotation.query_id,
            reviewer="test-reviewer",
            actor_kind="human",
            decision="accept",
            note="Test independent review.",
        )
    after = evaluate_annotations(frozen(changed))["queries"]
    assert [(row["returned_ids"], row["scores"]) for row in before] == [
        (row["returned_ids"], row["scores"]) for row in after
    ]


def test_load_rejects_duplicate_keys_unknown_schema_naive_times_and_oversize(tmp_path):
    path = tmp_path / "input.json"
    path.write_text('{"key": 1, "key": 2}')
    with pytest.raises(ValueError, match="duplicate"):
        load_json(path)
    path.write_bytes(b" " * (8 * 1024 * 1024 + 1))
    with pytest.raises(ValueError, match="size"):
        load_json(path)
    data = seed().model_dump(mode="json")
    data["schema_version"] = "task-annotations/v99"
    path.write_text(json.dumps(data))
    with pytest.raises(ValidationError):
        load_annotations(path)
    data["schema_version"] = "task-annotations/v1"
    data["snapshots"][0]["available_at"] = datetime(2026, 1, 1).isoformat()
    with pytest.raises(ValidationError):
        AnnotationDataset.model_validate(data)
    assert datetime.now(UTC).tzinfo is not None


def test_prepare_does_not_launder_labels_or_review_and_potion_requires_exact_pin():
    with pytest.raises(ValueError, match="unannotated"):
        prepare_annotations(reviewed(), dataset_id="next-v1")
    assert prepare_annotations(seed(), dataset_id="next-v1").dataset_id == "next-v1"
    for options in (
        {"model_revision": "unknown"},
        {"k": True},
        {"minimum_score": float("nan")},
    ):
        with pytest.raises((ValueError, TypeError)):
            freeze_annotations(reviewed(), selection_note="test", **options)
    with pytest.raises(ValidationError, match="pinned model"):
        freeze_annotations(reviewed(), backend="potion", selection_note="test")


def test_same_source_record_cannot_cross_splits_as_description_and_fact():
    data = seed().model_dump(mode="json")
    data["snapshots"][5]["facts"] = [
        {
            "evidence_id": "cross-role-fact",
            "statement": "Same source record in another role is still a shared cohort.",
            "origin": data["snapshots"][0]["origin"],
            "available_at": "2026-01-01T00:00:00Z",
            "source_kind": "benchmark",
        }
    ]
    with pytest.raises(ValidationError, match="overlap"):
        AnnotationDataset.model_validate(data)


def test_committed_seed_proposals_and_source_hashes_remain_pending():
    import hashlib
    from pathlib import Path

    root = Path(__file__).resolve().parents[2]
    path = root / "tests/fixtures/understanding/annotations/seed.json"
    dataset = load_annotations(path)
    assert len(dataset.snapshots) == 18
    assert not dataset.annotations and not dataset.reviews
    assert dataset.freeze is None and dataset.protocol is None
    assert {row.split for row in dataset.snapshots} == {"train", "development", "test"}
    for row in dataset.snapshots:
        for origin in [row.origin, *(fact.origin for fact in row.facts)]:
            assert origin.authorship == "agent"
            assert (
                hashlib.sha256((root / origin.source_ref).read_bytes()).hexdigest()
                == origin.source_sha256
            )
        if row.role == "query":
            label = QueryJudgment.model_validate(
                load_json(path.parent / "proposals" / f"{row.example_id}.json")
            )
            dataset = set_judgment(
                dataset,
                row.example_id,
                label,
                annotator="proposal-agent",
                actor_kind="agent",
            )
    assert len(dataset.annotations) == 9
    assert {row.judgment.no_match for row in dataset.annotations} == {"yes", "no"}
    assert {
        pair.scope_change for row in dataset.annotations for pair in row.judgment.pairs
    } >= {"expanded", "narrowed", "changed"}
    assert {
        pair.difficulty_change
        for row in dataset.annotations
        for pair in row.judgment.pairs
    } >= {"harder", "easier", "unknown"}
    assert {
        pair.continuation for row in dataset.annotations for pair in row.judgment.pairs
    } == {"yes", "no", "unknown"}
    assert any(
        pair.hard_negative for row in dataset.annotations for pair in row.judgment.pairs
    )
    with pytest.raises(ValueError, match="human"):
        freeze_annotations(dataset, selection_note="No fabricated human annotation.")


def test_potion_protocol_requires_matching_encoder_identity():
    from model_learner.representation.potion import MODEL_ID, MODEL_REVISION

    class Encoder:
        dimensions = 2
        metadata = {
            "model_id": MODEL_ID,
            "revision": MODEL_REVISION,
            "bundle_sha256": "b" * 64,
        }

        def encode(self, texts):
            return tuple((1.0, 0.0) for _ in texts)

    dataset = freeze_annotations(
        reviewed(),
        backend="potion",
        k=1,
        minimum_score=0.0,
        model_revision=MODEL_REVISION,
        model_sha256="b" * 64,
        selection_note="Synthetic encoder contract; not actual model accuracy.",
    )
    with pytest.raises(ValueError, match="explicitly loaded"):
        evaluate_annotations(dataset)
    encoder = Encoder()
    encoder.metadata = {**encoder.metadata, "bundle_sha256": "c" * 64}
    with pytest.raises(ValueError, match="identity"):
        evaluate_annotations(dataset, encoder=encoder)
    encoder.metadata = {**encoder.metadata, "bundle_sha256": "b" * 64}
    result = evaluate_annotations(dataset, encoder=encoder)
    assert result["retrieval_provenance"]["encoder"]["revision"] == MODEL_REVISION
    with pytest.raises(ValueError, match="does not use"):
        evaluate_annotations(frozen(), encoder=encoder)


def test_existing_local_potion_annotation_evaluation_if_explicitly_enabled(monkeypatch):
    import os
    import socket

    from model_learner.representation.potion import MODEL_REVISION, load_potion_encoder

    model_path = os.environ.get("MODEL_LEARNER_TEST_POTION_PATH")
    if not model_path:
        pytest.skip("explicit approved local Potion bundle required")

    def deny(*args, **kwargs):
        raise AssertionError("annotation evaluation attempted network access")

    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    model_sha256 = "930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2"
    dataset = freeze_annotations(
        reviewed(),
        backend="potion",
        k=1,
        minimum_score=0.0,
        model_revision=MODEL_REVISION,
        model_sha256=model_sha256,
        selection_note="Fixed contract rehearsal on synthetic test labels.",
    )
    encoder = load_potion_encoder(
        model_path, revision=MODEL_REVISION, expected_sha256=model_sha256
    )
    result = evaluate_annotations(dataset, encoder=encoder)
    assert result["summary"]["query_count"] == 2
    assert result["retrieval_provenance"]["encoder"]["bundle_sha256"] == model_sha256
