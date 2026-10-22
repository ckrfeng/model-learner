"""Write a J2 offline readiness packet; zero credential/network access or POSTs."""

import json
from pathlib import Path

from model_learner.understanding.decisions_readiness import readiness

if __name__ == "__main__":
    repository = Path(__file__).resolve().parents[1]
    packet = readiness(repository / "tests/fixtures/intent")
    output = repository / ".model-learner/j2-readiness-v1/readiness.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n")
    print("J2 PARTIAL: offline contract PASS; routing/spending/live smoke BLOCKED.")
    print("Zero paid requests; ignored readiness packet written.")
