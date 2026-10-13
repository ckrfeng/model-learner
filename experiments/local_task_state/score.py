"""Audit explicit AI semantic matches, never infer equivalence from overlap."""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter
from pathlib import Path

FAMILIES = {
    "requirements": {
        "requested_action",
        "requirement_added",
        "constraint",
        "requirement_revised",
    },
    "decisions": {"decision", "decision_reversed"},
    "reversals": {"decision_reversed"},
    "additions": {"requirement_added"},
    "removals": {"requirement_removed"},
    "revisions": {"requirement_revised"},
    "reinstatements": {"requirement_reinstated"},
    "failures": {"reported_failure"},
    "progress": {"reported_progress"},
    "completion": {"completion_claim"},
    "conditionals": {"conditional"},
    "references": {"earlier_reference"},
    "uncertainty": {"uncertainty"},
}


def ratio(numerator, denominator):
    return None if denominator == 0 else numerator / denominator


def score(reference: dict, predictions: list[dict], ledger: dict) -> dict:
    """Pairs are AI judgments. Check bijection, modes, family, source and links."""
    refs = {
        (c["conversation_id"], c["message_id"]): c for c in reference["checkpoints"]
    }
    if len(refs) != len(reference["checkpoints"]):
        raise ValueError("duplicate reference checkpoint")
    expected = {(*key, v) for key in refs for v in "ABC"}
    prediction_keys = [
        (c["conversation_id"], c["message_id"], c["variant"]) for c in predictions
    ]
    if (
        len(set(prediction_keys)) != len(prediction_keys)
        or set(prediction_keys) != expected
    ):
        raise ValueError(
            "prediction coverage must contain each checkpoint/variant once"
        )
    judgments = {
        (c["conversation_id"], c["message_id"], c["variant"]): c
        for c in ledger["checkpoints"]
    }
    if len(judgments) != len(ledger["checkpoints"]) or set(judgments) != expected:
        raise ValueError("ledger coverage must contain each checkpoint/variant once")
    totals = {v: Counter() for v in "ABC"}
    matches = {v: Counter() for v in "ABC"}
    times = {v: [] for v in "ABC"}
    for record in predictions:
        key = record["conversation_id"], record["message_id"]
        ref = refs[key]
        judgment = judgments[*key, record["variant"]]
        if type(judgment["objective_match"]) is not bool:
            raise ValueError("objective match flag must be boolean")
        if type(record["available"]) is not bool:
            raise ValueError("availability flag must be boolean")
        unparsed = judgment.get("unparsed_raw_events", 0)
        if type(unparsed) is not int or unparsed < 0:
            raise ValueError("unparsed event count must be a nonnegative integer")
        variant = record["variant"]
        t = totals[variant]
        m = matches[variant]
        times[variant].append(record["seconds"])
        t["checkpoints"] += 1
        t["objective_nonnull_reference"] += ref["objective"] is not None
        t["objective_null_reference"] += ref["objective"] is None
        t["unavailable"] += not record["available"]
        extraction = record.get("extraction") or {"objective": None, "events": []}
        t["objective_null_prediction"] += (
            record["available"] and extraction["objective"] is None
        )
        if judgment["objective_match"]:
            if not record["available"]:
                raise ValueError("unavailable objective cannot match")
            if (ref["objective"] is None) != (extraction["objective"] is None):
                raise ValueError("objective null mismatch")
            m["objectives"] += 1
            m["objective_null"] += ref["objective"] is None
        revents, pevents = ref["events"], extraction["events"]
        raw_events = record.get("raw", {}).get("events", pevents)
        t["invalid_events"] += len(extraction.get("invalid_events", []))
        t["valid_event_citations"] += len(pevents)
        t["raw_event_citations"] += len(pevents) + len(
            extraction.get("invalid_events", [])
        )
        t["raw_event_citations"] += judgment.get("unparsed_raw_events", 0)
        t["predicted_targets"] += sum(e["target"] is not None for e in raw_events)
        t["reference_targets"] += sum(e["target"] is not None for e in revents)
        t["reference_null_targets"] += sum(
            e["target"] is None
            and e["kind"]
            in {
                "requirement_removed",
                "requirement_revised",
                "requirement_reinstated",
                "decision_reversed",
                "earlier_reference",
            }
            for e in revents
        )
        pairs = judgment["pairs"]
        if len({p["prediction"] for p in pairs}) != len(pairs) or len(
            {p["reference"] for p in pairs}
        ) != len(pairs):
            raise ValueError("semantic pairs must be one-to-one")
        for pair in pairs:
            if type(pair["target_match"]) is not bool:
                raise ValueError("target match flag must be boolean")
            if any(
                type(pair[k]) is not int or pair[k] < 0
                for k in ("prediction", "reference")
            ):
                raise ValueError("pair indices must be nonnegative integers")
            if pair["prediction"] >= len(pevents) or pair["reference"] >= len(revents):
                raise ValueError("pair index outside event array")
            if not isinstance(pair.get("reason"), str) or not pair["reason"].strip():
                raise ValueError("semantic match requires a reason")
            p, r = pevents[pair["prediction"]], revents[pair["reference"]]
            if p["evidence"]["message_id"] != r["evidence"]["message_id"]:
                raise ValueError("wrong message attribution in match")
            if p["mode"] != r["mode"]:
                raise ValueError("mode mismatch cannot receive match credit")
            if p["kind"] != r["kind"] and not (
                p["kind"] in FAMILIES["requirements"]
                and r["kind"] in FAMILIES["requirements"]
            ):
                raise ValueError("unrelated event kinds cannot match")
            for family, kinds in FAMILIES.items():
                if p["kind"] in kinds and r["kind"] in kinds:
                    if (family == "requirements" and p["mode"] == "request") or (
                        family != "requirements" and p["kind"] == r["kind"]
                    ):
                        m[family] += 1
            m["semantic_events"] += 1
            if r["target"] is not None:
                t["recognized_reference_targets"] += 1
                if pair["target_match"]:
                    if not pair.get("target_reason"):
                        raise ValueError(
                            "target credit requires semantic evidence reason"
                        )
                    if (
                        p["target"] is None
                        or p["target"]["message_id"] != r["target"]["message_id"]
                    ):
                        raise ValueError("missing/wrong target message cannot match")
                    m["target_links"] += 1
            elif r["kind"] in {
                "requirement_removed",
                "requirement_revised",
                "requirement_reinstated",
                "decision_reversed",
                "earlier_reference",
            }:
                t["recognized_null_reference_targets"] += 1
                m["null_target_abstention"] += p["target"] is None
        for family, kinds in FAMILIES.items():

            def eligible(e, kinds=kinds, family=family):
                return e["kind"] in kinds and (
                    family != "requirements" or e["mode"] == "request"
                )

            t[family + "_predicted"] += sum(eligible(e) for e in raw_events)
            t[family + "_reference"] += sum(eligible(e) for e in revents)
            if family in {"failures", "completion"}:
                negative = not any(e["kind"] in kinds for e in revents)
                t[family + "_negative_checkpoints"] += negative
                t[family + "_false_positive_checkpoints"] += negative and any(
                    e["kind"] in kinds for e in raw_events
                )
        t["semantic_reference"] += len(revents)
        t["semantic_predicted"] += len(raw_events)
    if len(predictions) != 3 * len(refs):
        raise ValueError("missing prediction checkpoint")
    result = {}
    for variant in "ABC":
        t, m = totals[variant], matches[variant]
        latency = sorted(times[variant])
        result[variant] = {
            "counts": dict(t),
            "matches": dict(m),
            "families": {
                f: {
                    "matched": m[f],
                    "predicted": t[f + "_predicted"],
                    "reference": t[f + "_reference"],
                    "precision": ratio(m[f], t[f + "_predicted"]),
                    "recall": ratio(m[f], t[f + "_reference"]),
                }
                for f in FAMILIES
            },
            "objective_agreement": ratio(m["objectives"], t["checkpoints"]),
            "target_precision": ratio(m["target_links"], t["predicted_targets"]),
            "target_recovery": ratio(m["target_links"], t["reference_targets"]),
            "recognized_target_accuracy": ratio(
                m["target_links"], t["recognized_reference_targets"]
            ),
            "null_target_recovery": ratio(
                m["null_target_abstention"], t["reference_null_targets"]
            ),
            "recognized_null_target_correctness": ratio(
                m["null_target_abstention"], t["recognized_null_reference_targets"]
            ),
            "null_objective_correctness": ratio(
                m["objective_null"], t["objective_null_reference"]
            ),
            "citation_validity": ratio(
                t["valid_event_citations"], t["raw_event_citations"]
            ),
            "false_failure_events": t["failures_predicted"] - m["failures"],
            "false_completion_events": t["completion_predicted"] - m["completion"],
            "median_seconds": (
                latency[(len(latency) - 1) // 2] + latency[len(latency) // 2]
            )
            / 2,
            "p95_seconds": latency[math.ceil(0.95 * len(latency)) - 1],
            "latency_trials": len(latency),
        }
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference", type=Path, required=True)
    parser.add_argument("--predictions", type=Path, required=True)
    parser.add_argument("--ledger", type=Path, required=True)
    args = parser.parse_args()
    predictions = [
        r
        for p in sorted(args.predictions.glob("case-*.json"))
        for r in json.loads(p.read_text()).values()
    ]
    print(
        json.dumps(
            score(
                json.loads(args.reference.read_text()),
                predictions,
                json.loads(args.ledger.read_text()),
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
