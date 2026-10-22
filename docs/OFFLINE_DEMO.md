# W7A newcomer offline demo

Learn how captured execution metadata, declared acceptance, artifact verification,
receipt-aware outcomes, frozen forecasts and later advice fit together. This is
an executable **fictional** W6B workflow, not an actual coding-agent run or a
measurement of any model's performance. W7A passes only offline usability/replay;
the plan's real end-to-end acceptance remains **integration pending**.

## Run

From this repository checkout, use an already installed development environment:
Python 3.12+ and this package's existing dependencies in `.venv`. For initial
installation see [README](../README.md#local-installation); installation may need
network access. The demo itself needs no network, credentials, model assets,
agent/runtime installation or paid calls, and installs nothing.

```sh
.venv/bin/python -B scripts/external_handoff_example.py
```

Exit 0 prints calculated JSON with `origin: fictional-offline-only`,
`eligible_outcomes: 2`, and `forecast_probabilities: [0.5, 0.6666666666666666]`.
A/B/C scores are Brier 0.25 / log loss ln(2) for the success, then Brier 4/9 /
log loss ln(3) for the failure. IDs, timestamps and hashes vary per fresh run.
The script creates temporary storage, checks a replay and removes that storage.
A refusal exits nonzero without printing the evidence contents.

## Retain, inspect and replay

Choose a new ignored directory. Existing directories are refused, including a
previous successful run. A failed run can leave partial evidence; preserve it for
inspection and choose another new directory when rerunning.

```sh
.venv/bin/python -B scripts/external_handoff_example.py \
  --output-directory .model-learner/w7a-demo
.venv/bin/python -B scripts/external_handoff_example.py \
  --replay-directory .model-learner/w7a-demo
.venv/bin/model-learner learn advise \
  --input-file .model-learner/w7a-demo/advisory-input.json
```

Replay prints the same summary and checks retained files without altering them.
It reconstructs disposable SQLite ledgers in temporary storage and imports each
resolved bundle twice, preserving its exact scoped identities and joins. It uses
original receipt times; it does not recapture evidence or regenerate forecasts.
The advisory command prints the retained `advisory.json` result: two eligible
labels, mean 0.5 for global/per-arm/A/B/C and an explicit abstention. No automatic
configuration selection occurs.

| Retained file | Inspect for |
| --- | --- |
| `intake.json`, `policy.json` | Three declared Tasks, configuration, reviewed source digest and compatibility policy. |
| `forecast-0.json`, `forecast-1.json`, adjacent `.sha256` files | Original pre-outcome probabilities, cutoffs, Run IDs and evidence membership. |
| Each `handoff-N/execution.json`, `execution-receipts.json` | Execution-only producer metadata and receiver first receipts. |
| Each `handoff-N/answer.txt`, `independent.xml` | Exact stopped data and the reviewed data-only verifier's complete report. |
| Each `handoff-N/resolved.json`, `receipts.json` | Bound verification, outcome, observation, associations and retained availability. |
| `advisory-input.json`, `advisory.json`, `summary.json` | Reloadable advice inputs, abstention, calculated scores and summary. |

Retain the entire directory and the exact source checkout for independent local
review/replay. The source hash deliberately refuses a changed fixture script.
Generated SQLite ledgers and `capture.jsonl` are additional inspection artifacts;
replay uses serialized scoped evidence as authority, not those convenience copies.
Keep all generated artifacts in ignored local storage; do not commit them. Do not
point this fictional demo at private sessions or arbitrary external submissions.

## What the checks establish

Replay checks serialized intake/evidence/receipt consistency; artifact and JUnit
bindings through the existing verifier; one eligible verified fictional success
and one failure; historical forecasts reconstructed only from evidence available
at each original cutoff; original forecast checksums and scores; and identical
later advice/summary. It detects missing or changed checked evidence. The existing
W6B tests additionally check two learner trials after duplicate replay and the
broader negative verification/availability contracts. See the
[W6B runbook and readiness matrix](EXTERNAL_EVIDENCE_HANDOFF.md) for the full
operator sequence, trust boundaries and acceptance evidence.

All events and data are newly authored fictional fixtures. Dataset
`synthetic-w6b-disposable-only` uses `source_kind=real` solely to exercise existing
real-contract APIs in disposable storage; this is never real execution evidence.
The bounded verifier compares data with `42` plus newline; the second artifact is
intentionally wrong. It executes no candidate code. Cost, native latency, tokens
and effective backend revision stay unknown.

A checksum establishes content identity, **not external authenticity**. Matching
hashes and self-consistent declarations cannot authenticate an external process,
model, verifier independence or historical receipt time. The reviewed local
fixture supplies the trust here; replay is not a hardened intake service.
Real external coding-agent/configuration evidence, protected independent verifier,
whole-boundary termination and resource coverage remain unproven by this demo.
Duration Option A, W4A's 600-second limit and its blocked execution gates remain
unchanged. W4B/W5/full W6/full W7 and real working-v1 integration are incomplete.
Stop at W7A; no further milestone or real execution is authorized here.
