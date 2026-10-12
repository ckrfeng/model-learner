"""Frozen authored speech-act/state experiment, separate from real evidence."""

from __future__ import annotations

import hashlib
import json
import math
import time
from collections import Counter, defaultdict

from model_learner.understanding.conversation_state import (
    INTENTS,
    Conversation,
    analyze,
    keyword_intent,
    rule_intent,
    tokens,
)


def _features(text: str, role: str) -> Counter:
    words = tokens(text)
    return Counter(
        [
            f"role={role}",
            *words,
            *(" ".join(p) for p in zip(words, words[1:], strict=False)),
        ]
    )


class NaiveBayes:
    """Multinomial unigram/bigram NB, Laplace smoothing, no external runtime.

    Low score margins abstain. Scores are uncalibrated, never confidence labels.
    Only explicitly supplied training text is fitted; evaluation is never fitted.
    """

    def __init__(self, training: list[dict]):
        self.counts = defaultdict(Counter)
        self.documents = Counter()
        vocabulary = set()
        for example in training:
            label = example["intent"]
            if label not in INTENTS:
                raise ValueError("unsupported training label")
            features = _features(example["text"], example["role"])
            self.counts[label].update(features)
            self.documents[label] += 1
            vocabulary.update(features)
        if not self.documents:
            raise ValueError("training examples required")
        self.vocabulary = vocabulary
        self.totals = {
            label: sum(counts.values()) for label, counts in self.counts.items()
        }

    def __call__(self, text: str, role: str) -> str:
        features = _features(text, role)
        scores = []
        for label in self.documents:
            score = math.log(self.documents[label] / self.documents.total())
            denominator = self.totals[label] + len(self.vocabulary)
            score += sum(
                n * math.log((self.counts[label][word] + 1) / denominator)
                for word, n in features.items()
                if word in self.vocabulary
            )
            scores.append((score, label))
        scores.sort(reverse=True)
        return (
            "ambiguous"
            if len(scores) > 1 and scores[0][0] - scores[1][0] < 0.7
            else scores[0][1]
        )


def state_signature(result: dict) -> dict:
    if not result["timeline"]:
        return {}
    state = result["timeline"][-1]["state"]
    by_id = {f["id"]: f for f in result["facts"]}
    output = {k: state[k] for k in ("task", "verification")}
    output["objective_message"] = (
        by_id[state["objective"]]["message"] if state["objective"] else None
    )
    for field in (
        "requirements",
        "exclusions",
        "decisions",
        "unresolved",
        "progress",
        "completion_claims",
    ):
        state_field = {
            "requirements": "requirement_evidence",
            "exclusions": "removal_evidence",
            "decisions": "decision_evidence",
            "completion_claims": "completion_reports",
        }.get(field, field)
        output[field] = [by_id[fid]["message"] for fid in state[state_field]]
    output["uncertainty_min"] = len(state["uncertainty"])
    return output


def evaluate(fixture: dict) -> dict:
    """Compare frozen classifiers on authored labels and complete final states."""
    if (
        not isinstance(fixture, dict)
        or fixture.get("format") != "conversation-state-evaluation/v1"
        or fixture.get("source_kind") != "simulated"
    ):
        raise ValueError("authored simulated evaluation required")
    nb = NaiveBayes(fixture["training"])
    variants = {"keyword": keyword_intent, "rules": rule_intent, "naive_bayes": nb}
    reports = {}
    for name, classifier in variants.items():
        started = time.perf_counter()
        confusion, errors, cases, field_counts = Counter(), Counter(), [], Counter()
        exact, count, correct = 0, 0, 0
        for case in fixture["evaluation"]:
            conversation = Conversation(
                messages=tuple(case["messages"]),
                checks=tuple(case["checks"]),
                source_kind="simulated",
            )
            result = analyze(conversation, classifier=classifier)
            predicted = [f["intent"] for f in result["facts"]]
            gold = case["intents"]
            if len(predicted) != len(gold):
                raise ValueError("evaluation requires one labeled clause per message")
            mismatches = []
            for index, (truth, guess) in enumerate(zip(gold, predicted, strict=True)):
                count += 1
                correct += truth == guess
                confusion[(truth, guess)] += 1
                if truth != guess:
                    category = (
                        "missed_ambiguity"
                        if truth == "ambiguous"
                        else "false_progress_or_completion"
                        if guess in {"progress", "completion_claim"}
                        else "missed_scope_change"
                        if truth
                        in {
                            "requirement_added",
                            "requirement_removed",
                            "requirement_revised",
                            "task_changed",
                            "decision_reversed",
                        }
                        else "false_scope_change"
                        if guess
                        in {
                            "requirement_added",
                            "requirement_removed",
                            "requirement_revised",
                            "task_changed",
                            "decision_reversed",
                        }
                        else "other_intent_error"
                    )
                    errors[category] += 1
                    mismatches.append(
                        {
                            "message": index,
                            "expected": truth,
                            "predicted": guess,
                            "category": category,
                        }
                    )
            signature = state_signature(result)
            wrong_fields = [
                k
                for k, v in case["final"].items()
                if (signature[k] < v if k == "uncertainty_min" else signature[k] != v)
            ]
            field_counts.update(k for k in case["final"] if k not in wrong_fields)
            exact += not wrong_fields
            cases.append(
                {
                    "id": case["id"],
                    "category": case["category"],
                    "intent_errors": mismatches,
                    "incorrect_state_fields": wrong_fields,
                }
            )
        f1 = []
        for label in INTENTS:
            tp = confusion[(label, label)]
            actual = sum(n for (truth, _), n in confusion.items() if truth == label)
            predicted_count = sum(
                n for (_, guess), n in confusion.items() if guess == label
            )
            if actual:
                f1.append(2 * tp / (actual + predicted_count))
        reports[name] = {
            "intent_correct": correct,
            "intent_count": count,
            "intent_accuracy": correct / count if count else None,
            "macro_f1_present_labels": sum(f1) / len(f1) if f1 else None,
            "exact_final_states": exact,
            "conversation_count": len(cases),
            "state_field_correct": dict(field_counts),
            "error_categories": dict(errors),
            "confusion": [
                {"expected": a, "predicted": b, "count": n}
                for (a, b), n in sorted(confusion.items())
            ],
            "cases": cases,
            "cpu_elapsed_seconds": time.perf_counter() - started,
        }
    return {
        "format": "conversation-state-evaluation-report/v1",
        "dataset_sha256": hashlib.sha256(
            json.dumps(fixture, sort_keys=True).encode()
        ).hexdigest(),
        "source_kind": "simulated",
        "label_provenance": fixture["label_provenance"],
        "training_examples": len(fixture["training"]),
        "variants": reports,
        "selection": "rules remain the default; this small authored test "
        "does not establish generalization",
        "limitations": [
            "Agent-authored manual labels are not independent human evaluation.",
            "Topic-separated training/test conversations still share authored "
            "cue vocabulary.",
            "Final states and clause intents do not measure every "
            "intermediate state or logical scope accuracy.",
            "No outcome prediction, embeddings, cloud calls or model routing.",
        ],
    }
