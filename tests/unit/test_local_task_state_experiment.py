"""Evidence and privacy regressions for the isolated experiment."""

import importlib.util
import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

spec = importlib.util.spec_from_file_location(
    "local_task_state_experiment",
    Path(__file__).resolve().parents[2] / "experiments/local_task_state/extract.py",
)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)
Citation = module.Citation
locate = module.locate
structure_extract = module.structure_extract
units = module.units
validate_output = module.validate_output


def test_structure_preserves_code_lists_wrapping_and_offsets():
    text = (
        "Please draft a notice:\n- keep names private\n\nA wrapped\n"
        'question?\n\n```json\n{"state":"done"}\n```'
    )
    parsed = units(text)
    assert [u["type"] for u in parsed] == ["prose", "list", "prose", "code"]
    assert text[parsed[2]["start"] : parsed[2]["end"]] == "A wrapped\nquestion?"
    result = structure_extract([{"id": "u1", "role": "user", "turn": 1, "text": text}])
    assert not any(e["kind"] == "completion_claim" for e in result["events"])


def test_conditional_permission_never_becomes_failure_report():
    text = "Please repair it only if the check fails."
    raw = structure_extract([{"id": "u1", "role": "user", "turn": 1, "text": text}])
    assert any(e["kind"] == "conditional" for e in raw["events"])
    assert not any(e["kind"] == "reported_failure" for e in raw["events"])


def test_exact_quote_occurrence_and_no_fuzzy_repair():
    messages = [{"id": "u1", "role": "user", "turn": 1, "text": "écho écho"}]
    assert locate(Citation(message_id="u1", quote="écho", occurrence=1), messages)[
        "span"
    ] == [5, 9]
    with pytest.raises(ValueError):
        locate(Citation(message_id="u1", quote="echo", occurrence=0), messages)


def test_invalid_local_and_future_evidence_is_retained_as_missingness():
    messages = [
        {"id": "u1", "role": "user", "turn": 1, "text": "Old"},
        {"id": "u2", "role": "user", "turn": 2, "text": "New"},
    ]
    citation = {"message_id": "u2", "quote": "New", "occurrence": 0}
    event = {
        "kind": "requirement_revised",
        "summary": "change",
        "mode": "request",
        "evidence": citation,
        "target": citation,
        "condition": None,
    }
    result = validate_output({"objective": None, "events": [event]}, messages)
    assert result["events"] == []
    assert len(result["invalid_events"]) == 1
    assert result["independent_verification"] is None
    event["target"] = None
    assert (
        validate_output({"objective": None, "events": [event]}, messages)["events"][0][
            "target"
        ]
        is None
    )
    with pytest.raises(ValidationError):
        validate_output({"objective": None, "events": [], "verified": True}, messages)


def test_scoring_counts_invalid_citations_and_rejects_duplicate_matches():
    score_spec = importlib.util.spec_from_file_location(
        "local_task_state_scoring",
        Path(__file__).resolve().parents[2] / "experiments/local_task_state/score.py",
    )
    scoring = importlib.util.module_from_spec(score_spec)
    score_spec.loader.exec_module(scoring)
    evidence = {"message_id": "u1", "quote": "missing", "occurrence": 0}
    event = {
        "kind": "requirement_added",
        "summary": "keep color",
        "mode": "request",
        "evidence": evidence,
        "target": None,
        "condition": None,
    }
    reference = {
        "checkpoints": [
            {
                "conversation_id": "c",
                "message_id": "u1",
                "objective": None,
                "events": [event],
            }
        ]
    }
    predictions = [
        {
            "conversation_id": "c",
            "message_id": "u1",
            "variant": v,
            "available": True,
            "seconds": 1,
            "raw": {"objective": None, "events": [event]},
            "extraction": {
                "objective": None,
                "events": [],
                "invalid_events": [{"event": event}],
            },
        }
        for v in "ABC"
    ]
    ledger = {
        "checkpoints": [
            {
                "conversation_id": "c",
                "message_id": "u1",
                "variant": v,
                "objective_match": True,
                "pairs": [],
            }
            for v in "ABC"
        ]
    }
    measured = scoring.score(reference, predictions, ledger)
    assert measured["A"]["families"]["requirements"]["predicted"] == 1
    assert measured["A"]["families"]["requirements"]["precision"] == 0
    assert measured["A"]["target_precision"] is None
    predictions[0]["extraction"]["events"] = [event]
    ledger["checkpoints"][0]["pairs"] = [
        {"prediction": 0, "reference": 0, "target_match": False}
    ] * 2
    with pytest.raises(ValueError, match="one-to-one"):
        scoring.score(reference, predictions, ledger)
    ledger["checkpoints"][0]["pairs"] = [
        {"prediction": -1, "reference": 0, "target_match": False, "reason": "test"}
    ]
    with pytest.raises(ValueError, match="nonnegative"):
        scoring.score(reference, predictions, ledger)
    ledger["checkpoints"][0]["pairs"] = []
    ledger["checkpoints"][0]["objective_match"] = "true"
    with pytest.raises(ValueError, match="boolean"):
        scoring.score(reference, predictions, ledger)
    ledger["checkpoints"][0]["objective_match"] = True
    duplicate = [predictions[0], predictions[0], predictions[2]]
    with pytest.raises(ValueError, match="coverage"):
        scoring.score(reference, duplicate, ledger)


def test_runtime_http_refuses_redirects(monkeypatch):
    import importlib

    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]))
    runner = importlib.import_module("experiments.local_task_state.run")
    observed = []

    def opener(*handlers):
        observed.extend(handlers)
        raise RuntimeError("stop before socket access")

    monkeypatch.setattr(runner.urllib.request, "build_opener", opener)
    with pytest.raises(RuntimeError, match="before socket"):
        runner.request("http://127.0.0.1:18743/health")
    with pytest.raises(ValueError, match="redirects"):
        observed[1].redirect_request(None, None, 302, "", {}, "https://example.com")
