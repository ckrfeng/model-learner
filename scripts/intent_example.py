"""J1 fictional offline demo. No HTTP, credentials, model downloads or ledger writes.

Run .venv/bin/python -B scripts/intent_example.py from the repository root.
The report is written only under ignored .model-learner/j1-offline-v1/.
"""

import json
from pathlib import Path

from advisory_example import example

from model_learner.learn.advisory import advise
from model_learner.learn.estimator import BetaBernoulli
from model_learner.understanding.intent import digest
from model_learner.understanding.intent_evaluation import evaluate_development


def demo(root: Path) -> dict:
    payload = example(with_evidence=True)
    before_input = payload.model_dump_json()
    before_advice = advise(payload.request, observations=payload.observations)

    def estimate():
        return BetaBernoulli.fit(
            payload.observations,
            dataset=payload.observations[0].dataset,
            cutoff=payload.request.cutoff,
            acceptance_spec=payload.request.task.acceptance_spec,
            resource_budget=payload.request.task.resource_budget,
        ).predict(payload.request.candidates[0], payload.request.task.task_group)

    before_estimate = estimate()
    report = evaluate_development(root)
    after_advice = advise(payload.request, observations=payload.observations)
    assert before_input == payload.model_dump_json()
    assert before_advice == after_advice
    assert before_estimate == estimate()
    report["learner_isolation"] = {
        "fictional_canonical_input_unchanged": True,
        "advisory_unchanged": True,
        "beta_bernoulli_unchanged": True,
        "advice_sha256": digest(before_advice),
        "advisory_status": after_advice["advisory"]["status"],
    }
    return report


if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[1]
    result = demo(repository / "tests/fixtures/intent")
    output = repository / ".model-learner/j1-offline-v1/synthetic-report.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print("PARTIAL: fictional local plumbing passed; official wire contract blocked.")
    print("8 development cases; 16 untouched holdout; zero paid requests.")
    print("Report: .model-learner/j1-offline-v1/synthetic-report.json")
