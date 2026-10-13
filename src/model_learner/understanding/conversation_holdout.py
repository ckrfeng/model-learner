"""Small, span-aligned synthetic holdout audit; no training or live reads."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import sys
from collections import Counter
from pathlib import Path

from model_learner.understanding import conversation_state

REQUIREMENTS = {"requirement_added", "requirement_removed", "requirement_revised"}
DECISIONS = {"decision", "decision_reversed"}
CHANGES = REQUIREMENTS | DECISIONS | {"task_changed"}


def frozen_backend(directory: Path):
    """Load the archived rule module only after checking its frozen digest."""
    manifest = json.loads((directory / "manifest.json").read_text())
    path = directory / "conversation_state.py"
    expected = manifest["files"][
        "src/model_learner/understanding/conversation_state.py"
    ]
    if hashlib.sha256(path.read_bytes()).hexdigest() != expected:
        raise ValueError("frozen rule digest mismatch")
    spec = importlib.util.spec_from_file_location("frozen_conversation_state", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _overlap(fact: dict, event: dict) -> bool:
    return fact["message"] == event["message"] and max(
        fact["span"][0], event["start"]
    ) < min(fact["span"][1], event["end"])


def _matches(
    facts: list[dict], events: list[dict], *, group_requirements=False
) -> dict[int, int]:
    """Maximum one-to-one label/span alignment, independent of clause splitting.

    A multi-act gold sentence can have several labels. One primary model intent
    cannot satisfy all of them; these misses are reported, never silently dropped.
    """
    owners = {}

    def label(value):
        return (
            "requirement_change"
            if group_requirements and value in REQUIREMENTS
            else value
        )

    def visit(pi, seen):
        for gi, event in enumerate(events):
            if (
                gi not in seen
                and label(facts[pi]["intent"]) == label(event["label"])
                and _overlap(facts[pi], event)
            ):
                seen.add(gi)
                if gi not in owners or visit(owners[gi], seen):
                    owners[gi] = pi
                    return True
        return False

    for pi in range(len(facts)):
        visit(pi, set())
    return {pi: gi for gi, pi in owners.items()}


def _ratio(correct: int, count: int) -> dict:
    return {
        "correct": correct,
        "count": count,
        "rate": correct / count if count else None,
    }


def _pr(tp: int, predicted: int, gold: int) -> dict:
    return {
        "true_positive": tp,
        "predicted": predicted,
        "reference": gold,
        "false_positive": predicted - tp,
        "missed": gold - tp,
        "precision": tp / predicted if predicted else None,
        "recall": tp / gold if gold else None,
    }


def evaluate_holdout(dataset: dict, *, backend=conversation_state) -> dict:
    """Reference labels must be frozen before calling this function.

    Objective/checkpoint accuracy and target edges are separate from intent
    recognition. Counts are descriptive, not independent Bernoulli trials.
    """
    if (
        dataset.get("format") != "conversation-state-holdout/v1"
        or dataset.get("source_kind") != "simulated"
        or not dataset.get("cases")
    ):
        raise ValueError("nonempty simulated holdout required")
    counts, labels, reports = Counter(), {}, []
    for case in dataset["cases"]:
        messages, events = case["messages"], case["events"]
        for gi, event in enumerate(events):
            if (
                event["label"] not in conversation_state.INTENTS
                or not 0 <= event["message"] < len(messages)
                or not 0
                <= event["start"]
                < event["end"]
                <= len(messages[event["message"]]["text"])
                or any(
                    not 0 <= target < gi or events[target]["message"] > event["message"]
                    for target in event.get("targets", [])
                )
            ):
                raise ValueError("invalid reference event or target")
        for field in ("objectives", "verification"):
            if [row["after_message"] for row in case[field]] != list(
                range(len(messages))
            ):
                raise ValueError("every checkpoint requires a reference label")
        result = backend.analyze(
            backend.Conversation(
                messages=tuple(messages),
                checks=tuple(case["checks"]),
                source_kind="simulated",
            )
        )
        facts = result["facts"]
        by_id = {fact["id"]: fact for fact in facts}
        by_id_index = {fact["id"]: pi for pi, fact in enumerate(facts)}
        matches = _matches(facts, events)
        family_matches = _matches(facts, events, group_requirements=True)
        counts["requirement_detection"] += sum(
            events[gi]["label"] in REQUIREMENTS for gi in family_matches.values()
        )
        choice_facts = [
            {**f, "intent": "decision"} for f in facts if f["intent"] in DECISIONS
        ]
        choice_regions = {
            (e["message"], e["start"], e["end"]): {**e, "label": "decision"}
            for e in events
            if e["label"] in DECISIONS
        }
        counts["decision_regions"] += len(choice_regions)
        counts["decision_region_detection"] += len(
            _matches(choice_facts, list(choice_regions.values()))
        )
        matched_gold = set(matches.values())
        counts["facts"] += len(facts)
        counts["events"] += len(events)
        counts["aligned"] += len(matches)
        errors = []
        for label in conversation_state.INTENTS:
            tp = sum(events[gi]["label"] == label for gi in matches.values())
            pred = sum(f["intent"] == label for f in facts)
            gold = sum(e["label"] == label for e in events)
            labels.setdefault(label, Counter()).update(tp=tp, predicted=pred, gold=gold)
        for pi, fact in enumerate(facts):
            a, b = fact["span"]
            counts["valid_spans"] += (
                messages[fact["message"]]["text"][a:b] == fact["text"]
                and messages[fact["message"]]["role"] == fact["role"]
            )
            if pi in matches:
                event = events[matches[pi]]
                counts["exact_aligned_spans"] += [a, b] == [
                    event["start"],
                    event["end"],
                ]
            if pi not in matches:
                errors.append(
                    {
                        "kind": "unmatched_prediction",
                        "fact": fact,
                        "overlapping_reference": [
                            e for e in events if _overlap(fact, e)
                        ],
                    }
                )
            if fact["links"]:
                counts["predicted_links"] += len(fact["links"])
                targets = (
                    events[matches[pi]].get("targets", []) if pi in matches else []
                )
                used = set()
                for fid in fact["links"]:
                    target = next(
                        (
                            gi
                            for gi in targets
                            if gi not in used and matches.get(by_id_index[fid]) == gi
                        ),
                        None,
                    )
                    if target is not None:
                        used.add(target)
                        counts["correct_links"] += 1
        counts["reference_links"] += sum(len(e.get("targets", [])) for e in events)
        for gi, event in enumerate(events):
            if gi not in matched_gold:
                errors.append({"kind": "missed_reference", "event": event})
        objective_errors, verification_errors = [], []
        for row in case["objectives"]:
            mi = row["after_message"]
            fid = result["timeline"][mi]["state"]["objective"]
            fact = by_id.get(fid)
            good = (
                fact is None
                if row["message"] is None
                else (
                    fact is not None
                    and fact["message"] == row["message"]
                    and any(
                        e["label"] in {"objective", "task_changed"}
                        and _overlap(fact, e)
                        for e in events
                    )
                )
            )
            counts["objective_checkpoints"] += 1
            counts["correct_objective_checkpoints"] += good
            if not good:
                objective_errors.append(
                    {
                        "after_message": mi,
                        "expected": row["message"],
                        "predicted": fact["message"] if fact else None,
                    }
                )
        first = case["objectives"][0]
        counts["initial_objectives"] += first["message"] is not None
        counts["correct_initial_objectives"] += first[
            "message"
        ] is not None and not any(e["after_message"] == 0 for e in objective_errors)
        for row in case["verification"]:
            mi = row["after_message"]
            predicted = result["timeline"][mi]["state"]["verification"]
            counts["verification_checkpoints"] += 1
            counts["correct_verification_checkpoints"] += predicted == row["expected"]
            counts["false_verified"] += (
                predicted == "verified" and row["expected"] != "verified"
            )
            counts["missed_verified"] += (
                predicted != "verified" and row["expected"] == "verified"
            )
            if predicted != row["expected"]:
                verification_errors.append({**row, "predicted": predicted})
        for row in case["uncertainty"]:
            if row["required"]:
                mi = row["message"]
                counts["required_uncertainty"] += 1
                counts["present_uncertainty"] += any(
                    by_id[u["evidence"]]["message"] == mi
                    for u in result["timeline"][mi]["state"]["uncertainty"]
                )
        reports.append(
            {
                "id": case["id"],
                "category": case["category"],
                "errors": errors,
                "objective_errors": objective_errors,
                "verification_errors": verification_errors,
                "predictions": facts,
            }
        )

    def group(names):
        return _pr(
            *(sum(labels[n][key] for n in names) for key in ("tp", "predicted", "gold"))
        )

    return {
        "format": "conversation-state-holdout-report/v1",
        "source_kind": "simulated",
        "label_provenance": dataset["label_provenance"],
        "backend_sha256": hashlib.sha256(
            Path(backend.__file__).read_bytes()
        ).hexdigest(),
        "dataset_sha256": hashlib.sha256(
            json.dumps(dataset, sort_keys=True).encode()
        ).hexdigest(),
        "conversation_count": len(reports),
        "metrics": {
            "initial_objective_accuracy": _ratio(
                counts["correct_initial_objectives"], counts["initial_objectives"]
            ),
            "objective_checkpoint_accuracy": _ratio(
                counts["correct_objective_checkpoints"], counts["objective_checkpoints"]
            ),
            "requirements": group(REQUIREMENTS),
            "requirement_change_detection": _pr(
                counts["requirement_detection"],
                sum(labels[n]["predicted"] for n in REQUIREMENTS),
                sum(labels[n]["gold"] for n in REQUIREMENTS),
            ),
            "decisions": group(DECISIONS),
            "decision_region_detection": _pr(
                counts["decision_region_detection"],
                sum(labels[n]["predicted"] for n in DECISIONS),
                counts["decision_regions"],
            ),
            "decision_reversals": group({"decision_reversed"}),
            "changes": group(CHANGES),
            "completion_claims": group({"completion_claim"}),
            "abstention": group({"ambiguous"}),
            "required_uncertainty_coverage": _ratio(
                counts["present_uncertainty"], counts["required_uncertainty"]
            ),
            "source_span_role_integrity": _ratio(
                counts["valid_spans"], counts["facts"]
            ),
            "exact_spans_among_aligned_intents": _ratio(
                counts["exact_aligned_spans"], counts["aligned"]
            ),
            "target_links": _pr(
                counts["correct_links"],
                counts["predicted_links"],
                counts["reference_links"],
            ),
            "verification_checkpoint_accuracy": _ratio(
                counts["correct_verification_checkpoints"],
                counts["verification_checkpoints"],
            ),
            "incorrect_verified_claims": counts["false_verified"],
            "missed_verified_checkpoints": counts["missed_verified"],
        },
        "per_label": {
            label: _pr(c["tp"], c["predicted"], c["gold"])
            for label, c in labels.items()
        },
        "cases": reports,
        "limitations": [
            "Independent blind agent labels, not human annotation or population "
            "ground truth.",
            "Overlap alignment tolerates segmentation differences; exact spans "
            "reported separately.",
            "Multi-act labels expose single-intent limitations; checkpoint "
            "references audit state separately.",
            "Source span integrity does not establish semantic correctness; "
            "target candidates are scored separately.",
            "Synthetic checks attest a named checkpoint only; no real outcomes "
            "or predictive benefit.",
        ],
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("dataset", type=Path)
    parser.add_argument("--frozen", type=Path)
    args = parser.parse_args()
    backend = frozen_backend(args.frozen) if args.frozen else conversation_state
    print(
        json.dumps(
            evaluate_holdout(json.loads(args.dataset.read_text()), backend=backend),
            indent=2,
        )
    )
