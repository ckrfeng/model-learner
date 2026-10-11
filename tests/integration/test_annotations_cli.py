"""Local annotation collection is explicit, reviewable and ledger-independent."""

import json

import pytest
from typer.testing import CliRunner

from model_learner.cli import app


def invoke(*arguments):
    return CliRunner().invoke(app, ["annotation", *(str(x) for x in arguments)])


@pytest.mark.parametrize(
    "command", ["prepare", "show", "label", "review", "freeze", "evaluate"]
)
def test_annotation_commands_are_documented(command):
    result = invoke(command, "--help")
    assert result.exit_code == 0, result.output
    assert "Usage:" in result.output


@pytest.mark.parametrize("command", ["label", "review"])
def test_actor_kind_requires_explicit_caller_attestation(command, tmp_path):
    arguments = [command, tmp_path / "source.json", "query"]
    if command == "label":
        arguments += [tmp_path / "judgment.json", "--annotator", "human-reviewer"]
    else:
        arguments += [
            "--reviewer",
            "human-reviewer",
            "--decision",
            "accept",
            "--note",
            "reviewed",
        ]
    result = invoke(*arguments, "--output", tmp_path / "output.json")
    assert result.exit_code == 2
    assert "--actor-kind" in result.output
    assert not (tmp_path / "output.json").exists()


def seed_file(tmp_path):
    """Simulated identities test review gates without human accuracy claims."""
    import hashlib

    from model_learner.understanding.annotations import AnnotationDataset

    examples = (
        ("h-dev-1", "historical", "development", "Repair retry delivery locking"),
        ("h-dev-2", "historical", "development", "Document retry delivery locking"),
        ("q-dev-1", "query", "development", "Retry delivery locking needs repair"),
        ("h-test-1", "historical", "test", "Repair parser malformed input crash"),
        ("h-test-2", "historical", "test", "Document parser malformed input examples"),
        ("q-test-1", "query", "test", "Repair parser malformed input crash safely"),
        ("q-test-2", "query", "test", "Add keyboard dialog focus loop"),
    )
    value = {
        "schema_version": "task-annotations/v1",
        "dataset_id": "cli-seed/v1",
        "source_kind": "simulated",
        "description": "CLI contract rehearsal with simulated reviewer identities.",
        "snapshots": [
            {
                "example_id": example_id,
                "role": role,
                "description": description,
                "split": split,
                "project": split,
                "family": split,
                "lineage": split,
                "available_at": "2026-01-01T00:00:00Z",
                "origin": {
                    "source_ref": "test_annotations_cli.py",
                    "source_sha256": hashlib.sha256(example_id.encode()).hexdigest(),
                    "locator": example_id,
                    "authorship": "agent",
                },
            }
            for example_id, role, split, description in examples
        ],
    }
    seed = tmp_path / "seed.json"
    seed.write_text(
        AnnotationDataset.model_validate(value).model_dump_json(), encoding="utf-8"
    )
    return seed


def judgment_file(tmp_path, query_id):
    from model_learner.understanding.annotations import QueryJudgment

    prefix = "dev" if query_id == "q-dev-1" else "test"
    no_match = query_id == "q-test-2"
    value = {
        "no_match": "yes" if no_match else "no",
        "rationale": "Human identity is simulated for this CLI contract test.",
        "pairs": [
            {
                "candidate_id": f"h-{prefix}-{index}",
                "similarity": "relevant"
                if index == 1 and not no_match
                else "irrelevant",
                "continuation": "unknown",
                "scope_change": "unknown",
                "difficulty_change": "unknown",
                "hard_negative": index == 2 and not no_match,
                "rationale": "Compare repair, documentation and focus objectives.",
                "evidence_refs": [query_id, f"h-{prefix}-{index}"],
            }
            for index in (1, 2)
        ],
    }
    path = tmp_path / f"{query_id}-judgment.json"
    path.write_text(
        QueryJudgment.model_validate(value).model_dump_json(), encoding="utf-8"
    )
    return path


def collect(tmp_path, *, review_actor="human", decision="accept"):
    source = seed_file(tmp_path)
    prepared = tmp_path / "prepared.json"
    result = invoke("prepare", source, prepared, "--dataset-id", "cli-reviewed/v1")
    assert result.exit_code == 0, result.output
    source = prepared
    for query_id in ("q-dev-1", "q-test-1", "q-test-2"):
        labeled = tmp_path / f"{query_id}-labeled.json"
        result = invoke(
            "label",
            source,
            query_id,
            judgment_file(tmp_path, query_id),
            "--annotator",
            "simulated-labeler",
            "--actor-kind",
            "human",
            "--output",
            labeled,
        )
        assert result.exit_code == 0, result.output
        reviewed = tmp_path / f"{query_id}-reviewed.json"
        result = invoke(
            "review",
            labeled,
            query_id,
            "--reviewer",
            "simulated-reviewer",
            "--actor-kind",
            review_actor,
            "--decision",
            decision,
            "--note",
            "Reviewed descriptions and explicit evidence references.",
            "--output",
            reviewed,
        )
        assert result.exit_code == 0, result.output
        source = reviewed
    return source


def freeze_file(source, destination, *options):
    return invoke(
        "freeze",
        source,
        destination,
        "--k",
        "1",
        "--minimum-score",
        "0.05",
        "--selection-note",
        "Prospective fixed threshold for CLI contract test.",
        *options,
    )


@pytest.mark.parametrize("backend", ["text", "tfidf"])
def test_full_annotation_cli_flow_and_no_model_or_ledger_access(
    tmp_path, monkeypatch, backend
):
    import socket

    from model_learner.storage.database import Database
    from model_learner.understanding.annotations import load_annotations

    def deny(*args, **kwargs):
        raise AssertionError("annotation flow attempted ledger or network access")

    monkeypatch.setattr(Database, "connection", deny)
    monkeypatch.setattr(socket, "create_connection", deny)
    monkeypatch.setattr(socket.socket, "connect", deny)
    monkeypatch.setattr(socket.socket, "connect_ex", deny)
    source = collect(tmp_path)
    result = invoke("show", source, "--query-id", "q-test-1")
    assert result.exit_code == 0, result.output
    displayed = json.loads(result.output)
    assert {row["example_id"] for row in displayed["snapshots"]} == {
        "q-test-1",
        "h-test-1",
        "h-test-2",
    }
    assert {row["query_id"] for row in displayed["annotations"]} == {"q-test-1"}
    assert "similarity_score" not in result.output
    assert "rank" not in result.output
    frozen = tmp_path / "frozen.json"
    result = freeze_file(source, frozen, "--backend", backend)
    assert result.exit_code == 0, result.output
    assert load_annotations(frozen).protocol.backend == backend
    report_path = tmp_path / "report.json"
    result = invoke("evaluate", frozen, "--output", report_path)
    assert result.exit_code == 0, result.output
    report = json.loads(report_path.read_text(encoding="utf-8"))
    summary = report["summary"]
    assert summary["query_count"] == 2
    assert summary["precision"] == summary["recall"] == 1.0
    assert summary["false_positive_rate"] == 0.0
    assert summary["coverage"] == summary["abstention_rate"] == 0.5
    assert summary["no_match_query_count"] == 1
    assert summary["no_match_abstention_rate"] == 1.0
    assert summary["hard_negative_false_positive_rate"] == 0.0
    assert report["source_kind"] == "simulated"
    assert report["split"] == "test"
    assert report["protocol"]["backend"] == backend
    assert not (tmp_path / ".model-learner").exists()


@pytest.mark.parametrize("actor,decision", [("agent", "accept"), ("human", "reject")])
def test_machine_or_rejected_reviews_cannot_freeze(tmp_path, actor, decision):
    source = collect(tmp_path, review_actor=actor, decision=decision)
    output = tmp_path / "blocked.json"
    result = freeze_file(source, output)
    assert result.exit_code == 2
    assert not output.exists()


def test_self_review_is_rejected_before_output_creation(tmp_path):
    source = seed_file(tmp_path)
    labeled = tmp_path / "labeled.json"
    result = invoke(
        "label",
        source,
        "q-dev-1",
        judgment_file(tmp_path, "q-dev-1"),
        "--annotator",
        "simulated-labeler",
        "--actor-kind",
        "human",
        "--output",
        labeled,
    )
    assert result.exit_code == 0, result.output
    output = tmp_path / "reviewed.json"
    result = invoke(
        "review",
        labeled,
        "q-dev-1",
        "--reviewer",
        "simulated-labeler",
        "--actor-kind",
        "human",
        "--decision",
        "accept",
        "--note",
        "Self review.",
        "--output",
        output,
    )
    assert result.exit_code == 2
    assert not output.exists()


@pytest.mark.parametrize(
    "malformed",
    [
        {"private": "PRIVATE_ANNOTATION_PAYLOAD"},
        {"schema_version": "PRIVATE_ANNOTATION_PAYLOAD"},
    ],
)
def test_invalid_schema_diagnostic_does_not_echo_content(tmp_path, malformed):
    source = tmp_path / "invalid.json"
    source.write_text(json.dumps(malformed), encoding="utf-8")
    for command in (
        ("show", source),
        ("prepare", source, tmp_path / "prepared.json", "--dataset-id", "new/v1"),
    ):
        result = invoke(*command)
        assert result.exit_code == 2
        assert "invalid annotation JSON or schema" in result.output
        assert "PRIVATE_ANNOTATION_PAYLOAD" not in result.output
    assert not (tmp_path / "prepared.json").exists()


def test_invalid_judgment_diagnostic_and_unknown_query_preserve_files(tmp_path):
    source = seed_file(tmp_path)
    label = tmp_path / "private-judgment.json"
    label.write_text('{"no_match":"PRIVATE_ANNOTATION_PAYLOAD"}', encoding="utf-8")
    output = tmp_path / "output.json"
    result = invoke(
        "label",
        source,
        "q-dev-1",
        label,
        "--annotator",
        "simulated-labeler",
        "--actor-kind",
        "human",
        "--output",
        output,
    )
    assert result.exit_code == 2
    assert "PRIVATE_ANNOTATION_PAYLOAD" not in result.output
    assert not output.exists()
    assert invoke("show", source, "--query-id", "missing").exit_code == 2


def test_outputs_are_exclusive_and_frozen_edits_are_rejected(tmp_path):
    from model_learner.understanding.annotations import load_annotations

    source = collect(tmp_path)
    frozen = tmp_path / "frozen.json"
    assert freeze_file(source, frozen).exit_code == 0
    original = frozen.read_bytes()
    assert freeze_file(source, frozen).exit_code == 2
    assert frozen.read_bytes() == original
    output = tmp_path / "edit.json"
    result = invoke(
        "label",
        frozen,
        "q-test-1",
        judgment_file(tmp_path, "q-test-1"),
        "--annotator",
        "different-labeler",
        "--actor-kind",
        "human",
        "--output",
        output,
    )
    assert result.exit_code == 2
    assert not output.exists()
    report = tmp_path / "report.json"
    report.write_text("preserve output", encoding="utf-8")
    assert invoke("evaluate", frozen, "--output", report).exit_code == 2
    assert report.read_text(encoding="utf-8") == "preserve output"
    data = load_annotations(frozen).model_dump(mode="json")
    data["snapshots"][0]["description"] += " edited"
    tampered = tmp_path / "tampered.json"
    tampered.write_text(json.dumps(data), encoding="utf-8")
    assert invoke("show", tampered).exit_code == 2


def test_evaluation_requires_freeze_and_explicit_local_potion_path(tmp_path):
    source = seed_file(tmp_path)
    output = tmp_path / "report.json"
    assert invoke("evaluate", source, "--output", output).exit_code == 2
    assert not output.exists()
    reviewed = collect(tmp_path)
    lexical = tmp_path / "lexical-frozen.json"
    assert freeze_file(reviewed, lexical).exit_code == 0
    assert (
        invoke(
            "evaluate", lexical, "--model-path", tmp_path, "--output", output
        ).exit_code
        == 2
    )
    assert not output.exists()


def test_potion_evaluation_never_discovers_or_downloads_a_model(tmp_path, monkeypatch):
    from model_learner.representation import potion

    def deny(*args, **kwargs):
        raise AssertionError("absent explicit model path must not invoke loader")

    reviewed = collect(tmp_path)
    frozen = tmp_path / "potion-frozen.json"
    result = freeze_file(
        reviewed,
        frozen,
        "--backend",
        "potion",
        "--model-revision",
        potion.MODEL_REVISION,
        "--model-sha256",
        "0" * 64,
    )
    assert result.exit_code == 0, result.output
    monkeypatch.setattr(potion, "load_potion_encoder", deny)
    output = tmp_path / "report.json"
    result = invoke("evaluate", frozen, "--output", output)
    assert result.exit_code == 2
    assert "explicit existing local model path" in result.output
    assert not output.exists()


@pytest.mark.parametrize(
    "contents",
    [
        b'{"PRIVATE_ANNOTATION_PAYLOAD":',
        b'{"description": "\xffPRIVATE_ANNOTATION_PAYLOAD"}',
    ],
)
def test_invalid_json_or_encoding_errors_do_not_echo_content(tmp_path, contents):
    source = tmp_path / "malformed.json"
    source.write_bytes(contents)
    result = invoke("show", source)
    assert result.exit_code == 2
    assert "invalid annotation JSON or schema" in result.output
    assert "PRIVATE_ANNOTATION_PAYLOAD" not in result.output


def test_relabeling_clears_prior_reviews_before_reassessment(tmp_path):
    from model_learner.understanding.annotations import load_annotations

    source = collect(tmp_path)
    output = tmp_path / "relabeled.json"
    result = invoke(
        "label",
        source,
        "q-test-1",
        judgment_file(tmp_path, "q-test-1"),
        "--annotator",
        "different-simulated-labeler",
        "--actor-kind",
        "human",
        "--output",
        output,
    )
    assert result.exit_code == 0, result.output
    data = load_annotations(output)
    assert {row.query_id for row in data.reviews} == {"q-dev-1", "q-test-2"}
    assert data.parent_sha256 is not None
    assert freeze_file(output, tmp_path / "blocked-freeze.json").exit_code == 2
    assert not (tmp_path / "blocked-freeze.json").exists()


def test_unfrozen_potion_protocol_is_rejected_before_model_loading(
    tmp_path, monkeypatch
):
    from model_learner.representation import potion
    from model_learner.understanding.annotations import load_annotations

    source = seed_file(tmp_path)
    data = load_annotations(source).model_dump(mode="json")
    data["protocol"] = {
        "backend": "potion",
        "k": 1,
        "minimum_score": 0.05,
        "selection_note": "Unfrozen protocol is not eligible for evaluation.",
        "model_revision": potion.MODEL_REVISION,
        "model_sha256": "0" * 64,
    }
    source.write_text(json.dumps(data), encoding="utf-8")

    def deny(*args, **kwargs):
        raise AssertionError("unfrozen protocol must not invoke model loader")

    monkeypatch.setattr(potion, "load_potion_encoder", deny)
    output = tmp_path / "report.json"
    result = invoke("evaluate", source, "--model-path", tmp_path, "--output", output)
    assert result.exit_code == 2
    assert "frozen protocol" in result.output
    assert not output.exists()
