# Synthetic longitudinal rule checks

`scenarios.json` contains seven agent-authored **simulated** examples and fourteen
checkpoint cutoffs. No row is a real execution, a human annotation, an accepted
review, an independently verified outcome or a predictive training example.
Codex-shaped event metadata is used solely to exercise the existing extractor.
No prompts, commands, tool arguments, output bodies or private transcripts occur
in these fixtures. Receipt cutoffs are not native execution timestamps.

Each case includes portable task/run/session identity, an initial sanitized
description with its availability receipt, metadata events, optional sanitized
checkpoint summaries with source/actor/hash/evidence references, and an expected
status/dimension rule check. Expectations were authored before the actual local
Potion evaluation. `manifest.json` binds this fixture's bytes to its SHA-256.
The labels are inspectable software assertions, not independent semantic truth.

| Scenario | Evidence and conservative interpretation |
| --- | --- |
| Normal progression | Additional file-change observations and an explicit planning-to-implementation report. |
| Repeated unsuccessful approaches | Distinct command items with nonzero exit codes; same operation, approach, causal retry or loop remains unknown. |
| Complexity growth | Explicit actor reports different scope/apparent difficulty; no independently measured complexity. |
| Implementation to debugging | Explicit phase reports plus a failed command; the command is not assumed to be a test. |
| Apparent progress, unverified | Completion is reported and a turn completes; verified task success remains unknown. |
| Missing evidence | Initial objective alone cannot support a longitudinal change judgment. |
| No meaningful change | Identical retained evidence across cutoffs; latent stasis remains unknown. |

`reference.json` records an actual invocation of the already installed, pinned
Potion CPU encoder with socket connections denied, without model download or
training. Model identity/runtime metadata are retained; process-specific load
time and peak RSS are null to avoid timing noise in the checked-in reference.

A uses initial information only and abstains on all seven comparisons. B compares
deterministic observations plus explicit structured actor assertions: its status
and changed dimensions agree with all seven authored expectations.
`B_metadata_only` removes every checkpoint summary from the same cohort: status
agreement is 6/7, and full dimension agreement is 3/7. No semantic phase, progress,
scope or difficulty transition can be derived from this telemetry alone. Four
cases obtain such transitions through explicit declarations in B.

C retains B's conservative decisions and adds objective/summary and consecutive
summary cosine diagnostics. It consumes only the extractor's retained text;
ambiguous equal-time summaries have unknown diagnostics. C's classification
difference is zero **by construction**: there is no semantic classifier or score
threshold. This does not show that embeddings are useless, or establish semantic
accuracy or predictive improvement. The separate unsupported-inference report
checks 154 implementation invariants with zero violations in this reference.
Those checks are not a population error rate.

There are zero eligible independently verified outcomes in this fixture.
Downstream outcome prediction reports `insufficient_data` with null scores.
Synthetic rule agreement cannot establish real task evolution, model utility or
population performance.

Reproduce the comparison from the repository root:

```sh
uv run model-learner learn trajectory-eval tests/fixtures/longitudinal/scenarios.json
uv run model-learner learn trajectory-eval tests/fixtures/longitudinal/scenarios.json \
  --model-path "$PWD/.model-learner/models/potion-base-8M-bf8b056651a2c21b8d2565580b8569da283cab23" \
  --model-revision bf8b056651a2c21b8d2565580b8569da283cab23 \
  --model-sha256 930be259798d5d6e24ee8285a198f4248d9b42ec8544c92b952fa5e2aa5184d2 \
  --output /tmp/longitudinal-report.json
```

The output destination must be new. Without all three explicit model options, C
is unavailable. No raw text collection or agent execution is enabled. Unit tests
exercise future/late observations, withheld text, invalid summary evidence
references, run bounds, ambiguous summaries, unknown objective availability,
label isolation and invalid embedding vectors. The actual-model test requires an
explicit `MODEL_LEARNER_TEST_POTION_PATH` and blocks socket connections.
