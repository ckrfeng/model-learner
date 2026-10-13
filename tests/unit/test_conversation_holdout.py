import copy
import hashlib
import importlib.util
import json
from pathlib import Path

import pytest

from model_learner.understanding.conversation_holdout import (
    _matches,
    evaluate_holdout,
    frozen_backend,
)
from model_learner.understanding.conversation_state import (
    Conversation,
    Message,
    analyze,
    from_read,
    rule_intent,
)

FIXTURES = Path(__file__).parents[1] / "fixtures/conversation_state"


def small_dataset():
    return {
        "format": "conversation-state-holdout/v1",
        "source_kind": "simulated",
        "label_provenance": "scorer test only",
        "cases": [
            {
                "id": "scorer-test",
                "category": "scorer-test",
                "messages": [{"role": "user", "text": "Build a lamp.", "turn": 1}],
                "checks": [],
                "events": [
                    {
                        "message": 0,
                        "start": 0,
                        "end": 13,
                        "label": "objective",
                        "targets": [],
                    }
                ],
                "objectives": [{"after_message": 0, "message": 0}],
                "verification": [{"after_message": 0, "expected": "unknown"}],
                "uncertainty": [],
            }
        ],
    }


def test_archive_hashes_and_frozen_backend():
    directory = FIXTURES / "frozen_v1"
    manifest = json.loads((directory / "manifest.json").read_text())
    for original, expected in manifest["files"].items():
        assert (
            hashlib.sha256((directory / Path(original).name).read_bytes()).hexdigest()
            == expected
        )
    backend = frozen_backend(directory)
    assert backend.rule_intent("I am researching batteries.", "user") == "other"
    assert backend.rule_intent("I am studying batteries.", "user") == "objective"


def test_archived_diagnostic_replay_binds_archived_rules():
    directory = FIXTURES / "frozen_v1"
    backend = frozen_backend(directory)
    spec = importlib.util.spec_from_file_location(
        "frozen_evaluation", directory / "conversation_evaluation.py"
    )
    evaluator = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(evaluator)
    for name in (
        "INTENTS",
        "Conversation",
        "analyze",
        "keyword_intent",
        "rule_intent",
        "tokens",
    ):
        setattr(evaluator, name, getattr(backend, name))
    report = evaluator.evaluate(json.loads((directory / "evaluation.json").read_text()))
    for variant in report["variants"].values():
        variant.pop("cpu_elapsed_seconds")
    assert report == json.loads((directory / "reference.json").read_text())


def test_alignment_is_one_to_one_and_segmentation_tolerant():
    facts = [{"message": 0, "span": [0, 25], "intent": "requirement_added"}]
    events = [
        {"message": 0, "start": 0, "end": 10, "label": "requirement_added"},
        {"message": 0, "start": 11, "end": 25, "label": "requirement_removed"},
    ]
    assert _matches(facts, events) == {0: 0}
    assert _matches(facts * 2, events) in ({0: 0}, {1: 0})
    # Maximum matching must reassign a broad span to preserve a narrow match.
    events[1]["label"] = "requirement_added"
    facts.append({"message": 0, "span": [0, 10], "intent": "requirement_added"})
    assert _matches(facts, events) == {1: 0, 0: 1}
    # Detection of a scope edit and its exact subtype are separate measurements.
    facts = [{"message": 0, "span": [0, 10], "intent": "requirement_revised"}]
    events = [{"message": 0, "start": 0, "end": 10, "label": "requirement_added"}]
    assert _matches(facts, events) == {}
    assert _matches(facts, events, group_requirements=True) == {0: 0}


def test_metrics_do_not_mutate_labels_and_empty_denominators_are_unknown():
    dataset = small_dataset()
    before = copy.deepcopy(dataset)
    report = evaluate_holdout(dataset)
    assert dataset == before
    assert report["metrics"]["initial_objective_accuracy"]["rate"] == 1
    assert report["metrics"]["requirements"]["precision"] is None
    assert report["metrics"]["target_links"]["recall"] is None
    assert report["metrics"]["incorrect_verified_claims"] == 0
    # A second semantic act cannot disappear because the model has one intent.
    dataset["cases"][0]["events"].append(
        {
            "message": 0,
            "start": 0,
            "end": 13,
            "label": "requirement_added",
            "targets": [],
        }
    )
    report = evaluate_holdout(dataset)
    assert report["metrics"]["requirements"]["missed"] == 1


@pytest.mark.parametrize("invalid", ["source", "span", "target", "checkpoint"])
def test_invalid_reference_is_rejected(invalid):
    dataset = small_dataset()
    case = dataset["cases"][0]
    if invalid == "source":
        dataset["source_kind"] = "real"
    elif invalid == "span":
        case["events"][0]["end"] = 100
    elif invalid == "target":
        case["events"][0]["targets"] = [0]
    else:
        case["objectives"] = []
    with pytest.raises(ValueError):
        evaluate_holdout(dataset)


@pytest.mark.parametrize(
    "verb",
    [
        "researching",
        "evaluating",
        "analyzing",
        "planning",
        "translating",
        "exploring",
        "investigating",
        "explaining",
        "designing",
        "making",
        "summarizing",
        "understanding",
    ],
)
def test_existing_objective_vocabulary_progressive_forms(verb):
    assert rule_intent(f"I am {verb} the exercise.", "user") == "objective"
    assert rule_intent(f"Maybe I am {verb} the exercise.", "user") == "ambiguous"
    assert rule_intent(f"I am {verb} the exercise?", "user") == "ambiguous"
    assert rule_intent(f"I am {verb} the exercise.", "assistant") == "other"


def test_user_supplied_scheduling_sentence_survives_bridge_and_establishes_objective():
    from types import SimpleNamespace

    text = (
        "I'm researching three task-scheduling algorithms: FIFO, "
        "shortest-job-first, and round-robin."
    )
    # Public user-supplied wording, not a retained read of the original source.
    read = SimpleNamespace(
        metadata={
            "items_view": "full",
            "turns": [
                {
                    "messages": [
                        {"role": "user", "native_message_id": "synthetic-message"}
                    ]
                }
            ],
        },
        text={"synthetic-message": [text]},
    )
    conversation = from_read(read)
    assert conversation.messages[0].text == text
    report = analyze(conversation)
    assert report["facts"][0]["text"] == text
    assert report["timeline"][0]["state"]["objective"] == report["facts"][0]["id"]
    assert report["timeline"][0]["state"]["verification"] == "unknown"


def test_multiple_change_candidates_remain_candidates_and_carry_uncertainty():
    conversation = Conversation(
        messages=tuple(
            Message(role="user", text=text, turn=i + 1)
            for i, text in enumerate(
                [
                    "Build an exercise.",
                    "Include a size filter.",
                    "Include a color filter.",
                    "Remove that filter.",
                ]
            )
        )
    )
    report = analyze(conversation)
    removal = report["facts"][-1]
    assert removal["links"] == [report["facts"][1]["id"], report["facts"][2]["id"]]
    assert {"evidence": removal["id"], "reason": "change_target_ambiguous"} in report[
        "timeline"
    ][-1]["state"]["uncertainty"]
    assert len(report["timeline"][-1]["state"]["requirement_evidence"]) == 3


def test_all_emitted_links_count_even_when_predicted_intent_is_wrong():
    dataset = small_dataset()
    case = dataset["cases"][0]
    for i, (text, label) in enumerate(
        [
            ("Use a paper shade.", "decision"),
            ("Use a larger paper shade.", "requirement_added"),
        ],
        start=1,
    ):
        case["messages"].append({"role": "user", "text": text, "turn": i + 1})
        case["events"].append(
            {"message": i, "start": 0, "end": len(text), "label": label, "targets": []}
        )
        case["objectives"].append({"after_message": i, "message": 0})
        case["verification"].append({"after_message": i, "expected": "unknown"})
    links = evaluate_holdout(dataset)["metrics"]["target_links"]
    assert links["predicted"] == links["false_positive"] == 1
    assert links["true_positive"] == 0


@pytest.mark.parametrize("dataset_name", ["holdout_v1", "post_holdout_v1"])
def test_frozen_labels_and_audited_reports_reproduce(dataset_name):
    path = FIXTURES / f"{dataset_name}.json"
    manifest = json.loads((FIXTURES / f"{dataset_name}_manifest.json").read_text())
    assert hashlib.sha256(path.read_bytes()).hexdigest() == manifest["file_sha256"]
    dataset = json.loads(path.read_text())
    backend = frozen_backend(FIXTURES / "frozen_v1")
    suffix = "_audited" if dataset_name == "holdout_v1" else ""
    reference = json.loads(
        (FIXTURES / f"{dataset_name}_baseline{suffix}.json").read_text()
    )
    assert evaluate_holdout(dataset, backend=backend) == reference
    revised = json.loads((FIXTURES / f"{dataset_name}_revised.json").read_text())
    assert evaluate_holdout(dataset) == revised
    revision = json.loads((FIXTURES / "revision_v1_manifest.json").read_text())
    assert revised["backend_sha256"] == revision["backend_sha256"]
