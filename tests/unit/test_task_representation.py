"""Public fixture evaluation and negative input/model-boundary checks."""

import json
from dataclasses import asdict
from datetime import UTC, datetime, timedelta

import pytest
from pydantic import ValidationError

from model_learner.domain.models import OutcomeStatus
from model_learner.learn.task_state import _features
from model_learner.representation import (
    RepresentationExample,
    SemanticUnavailable,
    TaskDescription,
    evaluate_task_representation,
    generate_representation_fixture,
    load_cpu_encoder,
    load_representation_examples,
    representation_features,
)
from model_learner.representation.semantic import (
    FILES,
    LocalCPUEncoder,
    _digest_bundle,
)

START = datetime(2026, 1, 1, tzinfo=UTC)


@pytest.fixture(scope="module")
def rows():
    return generate_representation_fixture(seed=3, count=150)


def evaluate(rows, **kwargs):
    return evaluate_task_representation(
        rows,
        dataset=rows[0].state.observation.dataset,
        acceptance_spec=rows[0].state.observation.acceptance_spec,
        train_until=START + timedelta(seconds=180 * 90),
        evaluation_at=START + timedelta(seconds=180 * 150),
        bootstrap_replicates=100,
        **kwargs,
    )


def replace_row(example, **changes):
    value = example.model_dump()
    value["state"]["observation"].update(changes, stable_key=None)
    if "task_id" in changes:
        value["description"]["task_id"] = changes["task_id"]
        value["state"]["checkpoint"]["task_id"] = changes["task_id"]
    return RepresentationExample.model_validate(value)


def test_existing_features_preserved_and_final_fields_excluded(rows):
    example = rows[0]
    assert representation_features(example, include_state=False) == _features(
        example.state, ("initial",)
    )
    assert representation_features(example, include_state=True) == _features(
        example.state, ("initial", "metrics", "state")
    )
    changed = replace_row(example, outcome_status=OutcomeStatus.FAILURE)
    assert representation_features(
        changed, include_state=True
    ) == representation_features(example, include_state=True)
    assert all(
        not n.startswith(("semantic:", "task_id", "description", "label"))
        for n in representation_features(example, include_state=True)
    )


def test_common_cohort_and_no_fabricated_semantic_result(rows):
    result = evaluate(rows)
    a, b, c = result.variants
    assert result.training_count >= 80 and result.scored_count >= 50
    assert result.training_family_count == result.scored_family_count == 6
    assert a.status == b.status == "evaluated"
    assert [r for r, _ in a.predictions] == [r for r, _ in b.predictions]
    assert c.status == "semantic_unavailable" and c.brier_score is None
    assert c.predictions == () and c.brier_interval.lower is None
    assert result.comparisons[1].interpretation == "semantic_unavailable"
    assert result.comparisons[0].task_count == result.scored_task_count
    assert result.overhead["semantic"]["actual_inference_seconds"] is None
    assert result.overhead["semantic"]["actual_model_memory_bytes"] is None
    assert result.overhead["semantic"]["estimated_parameter_bytes"] == 90_800_000
    for name in ("A_existing", "B_execution_state"):
        profile = result.overhead["feature_profiles"][name]
        assert profile["reference_fit_seconds"] > 0
        assert profile["reference_scoring_seconds"] > 0
        assert profile["feature_python_object_bytes"] > 0
    assert all(
        sum(x.count for x in v.calibration) == result.scored_count for v in (a, b)
    )
    assert result.comparisons[0].brier_improvement > 0.05
    # Report contains no descriptions or transcript bodies.
    assert rows[0].description.text not in json.dumps(asdict(result))


def test_reproducible_statistics_input_order_and_fixture(rows):
    assert generate_representation_fixture(seed=3, count=150) == rows
    first, second = evaluate(rows), evaluate(tuple(reversed(rows)))
    assert first.variants == second.variants
    assert first.comparisons == second.comparisons
    assert first.cohort_sha256 == second.cohort_sha256


def test_test_outcomes_not_used_for_prediction_or_training(rows):
    changed = tuple(
        replace_row(
            e,
            outcome_status=OutcomeStatus.FAILURE
            if e.state.observation.outcome_status is OutcomeStatus.SUCCESS
            else OutcomeStatus.SUCCESS,
        )
        if i >= 90 and e.state.observation.outcome_status is not OutcomeStatus.UNKNOWN
        else e
        for i, e in enumerate(rows)
    )
    before, after = evaluate(rows), evaluate(changed)
    assert [v.predictions for v in before.variants] == [
        v.predictions for v in after.variants
    ]
    assert before.variants[1].brier_score != after.variants[1].brier_score


def test_future_duplicate_does_not_rewrite_or_conflict(rows):
    future = replace_row(rows[0], recorded_at=START + timedelta(days=30))
    report = evaluate((*rows, future))
    assert report.variants == evaluate(rows).variants
    assert report.exclusions["example_not_available"] == 1
    with pytest.raises(ValueError, match="conflicting"):
        evaluate(
            (
                *rows,
                replace_row(
                    rows[0],
                    outcome_status=OutcomeStatus.SUCCESS
                    if rows[0].state.observation.outcome_status is OutcomeStatus.FAILURE
                    else OutcomeStatus.FAILURE,
                ),
            )
        )


def test_wrong_horizon_known_label_and_unavailable_checkpoint_inputs(rows):
    wrong = rows[0].model_copy(
        update={
            "state": rows[0].state.model_copy(
                update={
                    "checkpoint": rows[0].state.checkpoint.model_copy(
                        update={
                            "checkpoint": rows[0].state.checkpoint.checkpoint
                            + timedelta(seconds=1)
                        }
                    )
                }
            )
        }
    )
    known = replace_row(rows[1], label_available_at=rows[1].state.checkpoint.checkpoint)
    late = rows[2].model_copy(
        update={
            "state": rows[2].state.model_copy(
                update={
                    "inputs_available_at": rows[2].state.checkpoint.checkpoint
                    + timedelta(seconds=1)
                }
            )
        }
    )
    result = evaluate((wrong, known, late, *rows[3:]))
    assert result.exclusions["wrong_checkpoint_horizon"] == 1
    assert result.exclusions["label_known_at_checkpoint"] == 1
    assert result.exclusions["checkpoint_inputs_unavailable"] == 1
    delayed = replace_row(
        rows[0],
        recorded_at=START + timedelta(days=30),
        label_available_at=START + timedelta(days=30),
    )
    assert (
        evaluate((delayed, *rows[1:])).training_count
        == evaluate(rows).training_count - 1
    )


def test_description_receipt_future_hash_private_and_identity_rejected(rows):
    value = rows[0].model_dump()
    value["description"]["available_at"] += timedelta(seconds=1)
    changed = RepresentationExample.model_validate(value)
    assert (
        evaluate((changed, *rows[1:])).exclusions["description_unavailable_at_decision"]
        == 1
    )
    for field, invalid in (
        ("text", "Changed"),
        ("source", "private_transcript"),
        ("task_id", rows[1].description.task_id),
    ):
        value = rows[0].model_dump()
        value["description"][field] = invalid
        with pytest.raises(ValidationError):
            RepresentationExample.model_validate(value)
    value = rows[0].description.model_dump()
    value["available_at"] = datetime(2026, 1, 1)
    with pytest.raises(ValidationError, match="timezone"):
        TaskDescription.model_validate(value)


def test_retries_families_and_identical_descriptions_never_cross_partitions(rows):
    retry = replace_row(rows[100], task_id=rows[0].description.task_id)
    retry = retry.model_copy(update={"description": rows[0].description})
    family = rows[101].model_copy(
        update={
            "description": rows[101].description.model_copy(
                update={"task_family": rows[0].description.task_family}
            )
        }
    )
    copied = rows[102].model_copy(
        update={
            "description": rows[102].description.model_copy(
                update={
                    "text": rows[0].description.text,
                    "text_sha256": rows[0].description.text_sha256,
                }
            )
        }
    )
    result = evaluate((*rows[:100], retry, family, copied, *rows[103:]))
    assert result.exclusions["task_overlaps_training"] == 1
    assert result.exclusions["family_overlaps_training"] == 1
    assert result.exclusions["description_overlaps_training"] == 1
    removed = sum(
        e.state.observation.outcome_status is not OutcomeStatus.UNKNOWN
        for e in rows[100:103]
    )
    assert result.scored_count == evaluate(rows).scored_count - removed


def test_sparse_and_single_class_and_family_pseudoreplication(rows):
    assert all(v.status == "insufficient_data" for v in evaluate(rows[:10]).variants)
    oneclass = tuple(
        replace_row(e, outcome_status=OutcomeStatus.SUCCESS)
        if e.state.observation.outcome_status is not OutcomeStatus.UNKNOWN
        else e
        for e in rows
    )
    assert all(v.brier_score is None for v in evaluate(oneclass).variants)
    onefamily = tuple(
        e.model_copy(
            update={
                "description": e.description.model_copy(
                    update={"task_family": "train" if i < 90 else "test"}
                )
            }
        )
        for i, e in enumerate(rows)
    )
    assert all(v.status == "insufficient_data" for v in evaluate(onefamily).variants)


def test_optional_semantic_plumbing_is_only_a_protocol_test(rows):
    # Not a pretrained embedding or evidence artifact: only check cohort/shape
    # and failure behavior when an explicit encoder returns protocol values.
    class ProtocolStub(LocalCPUEncoder):
        def __init__(self):
            self.metadata = {"model_id": "protocol-test-only", "parameter_bytes": None}

        def encode(self, texts):
            return tuple((1.0,) + (0.0,) * 383 for _ in texts)

    result = evaluate(rows, encoder=ProtocolStub())
    assert len({tuple(r for r, _ in v.predictions) for v in result.variants}) == 1
    assert result.variants[1].predictions == result.variants[2].predictions

    class InvalidStub(ProtocolStub):
        def encode(self, texts):
            return ((float("nan"),),)

    result = evaluate(rows, encoder=InvalidStub())
    assert result.variants[2].brier_score is None
    assert result.overhead["semantic"]["reason"] == "local_semantic_encoding_failed"
    with pytest.raises(ValueError, match="explicit local"):
        evaluate(rows, encoder=object())


def test_json_roundtrip_and_extra_field_rejection(rows, tmp_path):
    file = tmp_path / "public.json"
    file.write_text(json.dumps([e.model_dump(mode="json") for e in rows[:3]]))
    assert load_representation_examples(file) == rows[:3]
    value = rows[0].model_dump(mode="json")
    value["raw_transcript"] = "unallowed"
    file.write_text(json.dumps([value]))
    with pytest.raises(ValidationError):
        load_representation_examples(file)


def safe_bundle(tmp_path):
    folder = tmp_path / "model"
    folder.mkdir()
    for name in FILES:
        (folder / name).write_bytes(b"public test file")
    return folder


def test_bundle_digest_copy_and_safe_file_refusal(tmp_path):
    folder = safe_bundle(tmp_path)
    snapshot = tmp_path / "copy"
    snapshot.mkdir()
    receipt = _digest_bundle(folder, copy_to=snapshot)
    assert _digest_bundle(snapshot) == receipt
    (folder / "vocab.txt").unlink()
    (folder / "vocab.txt").symlink_to(snapshot / "vocab.txt")
    with pytest.raises(OSError):
        _digest_bundle(folder)


def test_bundle_limits_special_files_and_no_network_runtime(tmp_path, monkeypatch):
    import os

    from model_learner.representation import semantic

    folder = safe_bundle(tmp_path)
    (folder / "config.json").write_bytes(b"x" * 65537)
    with pytest.raises(SemanticUnavailable, match="type/size"):
        _digest_bundle(folder)
    (folder / "config.json").unlink()
    os.mkfifo(folder / "config.json")
    with pytest.raises(SemanticUnavailable, match="type/size"):
        _digest_bundle(folder)
    monkeypatch.setattr(semantic.importlib.util, "find_spec", lambda _: None)
    with pytest.raises(SemanticUnavailable, match="runtime unavailable"):
        load_cpu_encoder(folder, expected_sha256="a" * 64, revision="b" * 40)


def test_model_pins_architecture_and_pickle_rejected_before_runtime(
    tmp_path, monkeypatch
):
    from model_learner.representation import semantic

    monkeypatch.setattr(semantic.importlib.util, "find_spec", lambda _: object())
    folder = safe_bundle(tmp_path)
    (folder / "config.json").write_text(json.dumps({"type_vocab_size": 10**12}))
    digest, _ = _digest_bundle(folder)
    with pytest.raises(SemanticUnavailable, match="architecture"):
        load_cpu_encoder(folder, expected_sha256=digest, revision="a" * 40)
    with pytest.raises(SemanticUnavailable, match="approved hash"):
        load_cpu_encoder(folder, expected_sha256="0" * 64, revision="a" * 40)
    (folder / "pytorch_model.bin").write_bytes(b"never execute pickle")
    with pytest.raises(SemanticUnavailable, match="exactly"):
        load_cpu_encoder(folder, expected_sha256=digest, revision="a" * 40)
    with pytest.raises(SemanticUnavailable, match="SHA-256"):
        load_cpu_encoder(folder, expected_sha256="main", revision="a" * 40)


def test_changed_file_size_is_bounded_even_after_stat(tmp_path, monkeypatch):
    from model_learner.representation import semantic

    folder = safe_bundle(tmp_path)
    actual = semantic.os.fstat

    def smaller(fd):
        value = actual(fd)
        from types import SimpleNamespace

        return SimpleNamespace(st_mode=value.st_mode, st_size=1)

    monkeypatch.setattr(semantic.os, "fstat", smaller)
    with pytest.raises(SemanticUnavailable, match="changed size"):
        _digest_bundle(folder)


def test_missing_pretrained_weights_rejected_without_claiming_model_validation(
    tmp_path, monkeypatch
):
    import sys
    from types import SimpleNamespace

    from model_learner.representation import semantic

    folder = safe_bundle(tmp_path)
    config = dict(
        model_type="bert",
        hidden_size=384,
        num_hidden_layers=6,
        num_attention_heads=12,
        intermediate_size=1536,
        vocab_size=30522,
        max_position_embeddings=512,
        type_vocab_size=2,
        hidden_act="gelu",
        layer_norm_eps=1e-12,
    )
    (folder / "config.json").write_text(json.dumps(config))
    digest, _ = _digest_bundle(folder)
    calls = []

    def load(*args, **kwargs):
        calls.append(kwargs)
        return object(), {"missing_keys": ["embeddings.word_embeddings.weight"]}

    # Protocol-only test; the real transformers/torch integration remains unrun.
    monkeypatch.setattr(semantic.importlib.util, "find_spec", lambda _: object())
    monkeypatch.setitem(sys.modules, "torch", SimpleNamespace())
    monkeypatch.setitem(
        sys.modules,
        "transformers",
        SimpleNamespace(
            BertConfig=lambda **kw: kw,
            BertTokenizer=lambda **kw: object(),
            BertModel=SimpleNamespace(from_pretrained=load),
        ),
    )
    with pytest.raises(SemanticUnavailable, match="incomplete"):
        load_cpu_encoder(folder, expected_sha256=digest, revision="a" * 40)
    assert calls[0]["local_files_only"] and calls[0]["use_safetensors"]
    assert calls[0]["token"] is False and calls[0]["output_loading_info"]
