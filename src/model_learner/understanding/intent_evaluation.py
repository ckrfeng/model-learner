"""Frozen fictional development evaluation only; no holdout prediction entry point."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from model_learner.understanding.decisions_offline import (
    WIRE_VERSION,
    FakeTransport,
    fixture_request,
    parse_fixture_response,
    readiness,
    usage_projection,
)
from model_learner.understanding.intent import (
    BASELINE_SHA256,
    BASELINE_VERSION,
    LABELS,
    QUESTIONS,
    VERSION,
    Intent,
    Prediction,
    Strict,
    baseline,
    canonical,
    digest,
)

MANIFEST_SHA256 = "31e5fe76d0306effdfe1ad7bba8318bc39c16207128ba8aeca3630e332d7a8c2"


class Case(Strict):
    id: str
    split: str
    description: str
    input_sha256: str


class Reference(Strict):
    id: str
    intent: Intent
    executable_changes: bool | None


def load_development(root: Path) -> tuple[tuple[Case, Reference], ...]:
    """Validate frozen identities; expose only dev text/reference pairs to harness."""
    raw = (root / "manifest.json").read_bytes()
    if hashlib.sha256(raw).hexdigest() != MANIFEST_SHA256:
        raise ValueError("frozen manifest changed; new evaluation version required")
    manifest = json.loads(raw)
    if manifest["questions_sha256"] != digest(
        [q.model_dump(mode="json") for q in QUESTIONS]
    ):
        raise ValueError("frozen questions changed")
    if (
        manifest["baseline_version"] != BASELINE_VERSION
        or manifest["baseline_sha256"] != BASELINE_SHA256
    ):
        raise ValueError("frozen baseline changed")
    data = {}
    for name, expected in manifest["files"].items():
        if name not in {"inputs.json", "reference_labels.json"}:
            raise ValueError("unexpected frozen file")
        payload = (root / name).read_bytes()
        if hashlib.sha256(payload).hexdigest() != expected:
            raise ValueError("frozen dataset changed")
        data[name] = json.loads(payload)
    cases = tuple(Case.model_validate(c) for c in data["inputs.json"])
    references = tuple(
        Reference.model_validate(r) for r in data["reference_labels.json"]
    )
    ids = {c.id for c in cases}
    if (
        len(cases) != 24
        or len(ids) != 24
        or {r.id for r in references} != ids
        or len(references) != 24
    ):
        raise ValueError("invalid frozen case identities")
    if {s: sum(c.split == s for c in cases) for s in manifest["splits"]} != manifest[
        "splits"
    ]:
        raise ValueError("invalid frozen split")
    if len({c.description for c in cases}) != 24 or any(
        hashlib.sha256(c.description.encode()).hexdigest() != c.input_sha256
        for c in cases
    ):
        raise ValueError("invalid frozen input hashes")
    mapping = {r.id: r for r in references}
    return tuple((c, mapping[c.id]) for c in cases if c.split == "development")


def metrics(
    references: tuple[Reference, ...], predictions: dict[str, Prediction | None]
) -> dict:
    """All-six-class macro F1; abstentions count as FN in primary metrics.

    Primary accuracy denominator is all reference cases. Binary metrics use known
    binary references with available probabilities only (threshold >= .5). Missing
    binary values are excluded with explicit denominators, never scored as false.
    """
    ids = {r.id for r in references}
    if not references or len(ids) != len(references) or not set(predictions) <= ids:
        raise ValueError(
            "distinct nonempty reference IDs and matching predictions required"
        )
    matrix = {truth: {pred: 0 for pred in (*LABELS, "abstain")} for truth in LABELS}
    correct = covered = binary_correct = 0
    briers = []
    for reference in references:
        prediction = predictions.get(reference.id)
        label = prediction.intent if prediction else None
        matrix[reference.intent][label or "abstain"] += 1
        covered += label is not None
        correct += label == reference.intent
        probability = prediction.code_probability if prediction else None
        if reference.executable_changes is not None and probability is not None:
            binary_correct += (probability >= 0.5) == reference.executable_changes
            briers.append((probability - reference.executable_changes) ** 2)
    f1s = []
    for label in LABELS:
        tp = matrix[label][label]
        fp = sum(matrix[t][label] for t in LABELS if t != label)
        fn = sum(v for p, v in matrix[label].items() if p != label)
        f1s.append(2 * tp / (2 * tp + fp + fn) if 2 * tp + fp + fn else 0.0)
    count = len(references)
    return {
        "version": "intent-metrics/v1",
        "n": count,
        "primary_intent_accuracy": correct / count,
        "macro_f1_all_six_classes": sum(f1s) / len(LABELS),
        "confusion_matrix": matrix,
        "primary_coverage": covered / count,
        "primary_abstention_rate": 1 - covered / count,
        "missing_or_malformed_rate": sum(
            predictions.get(r.id) is None for r in references
        )
        / count,
        "binary_reference_count": sum(
            r.executable_changes is not None for r in references
        ),
        "binary_scorable_count": len(briers),
        "binary_accuracy_at_0_5": binary_correct / len(briers) if briers else None,
        "binary_brier": sum(briers) / len(briers) if briers else None,
    }


def mock_response() -> bytes:
    """Same fixed answers for every task, chosen without labels or input text."""
    return canonical(
        {
            "model": None,
            "provider": None,
            "usage": None,
            "id": None,
            "answers": {
                QUESTIONS[0].id: {
                    "type": "choice",
                    "choice": "unclear",
                    "confidence": 1.0,
                    "probabilities": {
                        label: float(label == "unclear") for label in LABELS
                    },
                },
                QUESTIONS[1].id: {"type": "noul", "noul": 0.5},
            },
        }
    )


def evaluate_development(
    root: Path, *, responses: dict[str, bytes | Exception] | None = None
) -> dict:
    pairs = load_development(root)
    if responses is not None and not set(responses) <= {c.id for c, _ in pairs}:
        raise ValueError("only frozen development case IDs permitted")
    # Predictors get descriptions only. References are joined after collection.
    baseline_predictions, mocked_predictions, receipts = {}, {}, []
    for case, _reference in pairs:
        baseline_predictions[case.id] = baseline(case.description)
        transport = FakeTransport(
            mock_response()
            if responses is None
            else responses.get(case.id, ValueError("missing fixture response"))
        )
        try:
            response = transport.send(fixture_request(case.description))
            prediction, receipt = parse_fixture_response(response)
        except (ValueError, OSError):
            prediction = None
            # Never echo untrusted exception prose or rejected provider content.
            receipt = {
                "completion": "mocked_error_or_malformed",
                "requested_model": "typesafe/jev-1.14",
                "reported_model": None,
                "reported_provider": None,
                "effective_model_revision": None,
                "routing_status": "unknown",
                **usage_projection(None),
            }
        mocked_predictions[case.id] = prediction
        receipts.append(
            {
                "case_id": case.id,
                "input_sha256": case.input_sha256,
                "local_attempts": transport.calls,
                **receipt,
            }
        )
    references = tuple(r for _, r in pairs)
    return {
        "version": "j1-fictional-evaluation/v1",
        "status": "PARTIAL",
        "question_contract": VERSION,
        "baseline_version": BASELINE_VERSION,
        "manifest_sha256": MANIFEST_SHA256,
        "split": "development",
        "reference_status": "authored_fictional; independent_human_review_pending",
        "holdout": {
            "n": 16,
            "predictions_collected": 0,
            "status": "untouched",
            "interpretation": "future conclusions exploratory",
        },
        "baseline": metrics(references, baseline_predictions),
        "mocked_local_fixture": metrics(references, mocked_predictions),
        "external_model_evidence": (
            "none; mocked plumbing is not Jev accuracy/calibration"
        ),
        "wire_contract_status": "published examples implemented; live routing blocked",
        "wire_version": WIRE_VERSION,
        "billing_coverage": {
            "n": len(receipts),
            "known_cost": sum(r["reported_cost_usd"] is not None for r in receipts),
            "known_usage": sum(
                r["input_tokens"] is not None and r["output_tokens"] is not None
                for r in receipts
            ),
            "known_route": sum(r["reported_provider"] is not None for r in receipts),
            "paid_requests": 0,
            "reported_cost_usd": None,
        },
        "receipts": receipts,
        "live_readiness": readiness(),
    }
