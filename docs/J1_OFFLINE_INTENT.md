# J1 optional task-intent research: offline partial delivery

**PARTIAL. The adapter implements the supplied published Decisions examples and
passes offline tests. Live routing/spend controls remain BLOCKED. Jev accuracy
and calibration are unmeasured. Independent human gold review is pending.**

This optional experiment labels requested task intent and whether executable source
changes are explicitly needed. It may eventually support human review of task
statements. It supplies no evidence of improved task understanding, difficulty,
acceptance, coding-agent utility or model selection. Ordinary ingestion, learning
and advice do not import or enable it. There is no HTTP client, credential loader,
agent executor, enabling live function or second learner.

## Supplied official examples and remaining boundary

The coordinator supplied literal public examples from the
[official OpenRouter Jev guide](https://openrouter.ai/blog/insights/what-is-jev/),
plus the [TypeSafe provider page](https://openrouter.ai/provider/typesafe/) and
[model page](https://openrouter.ai/typesafe/jev-1.14/). These were supplied inline;
this executor did not fetch any page or make a network/DNS request. Earlier two
free authenticated GET preflights were performed by the coordinator before J1,
not repeated here. No credential, environment secret or local secret file was read.

The examples demonstrate POST `https://openrouter.ai/api/alpha/decisions`, model
`typesafe/jev-1.14`, string `state`, and `questions` keyed by question ID:

| Type | Request question fields | Answer fields, keyed by the same ID |
| --- | --- | --- |
| Choice | `type`, `instructions`, `criteria` object | `type`, `choice`, `probabilities`, `confidence` |
| Noul | `type`, `instructions` | `type`, `noul` (true probability) |
| Score | `type`, `instructions`, `criteria` array | `type`, `score`, `legend`, `probabilities`, `confidence` |

The shown response envelope contains `model`, `answers`, `usage`, `id`, `provider`.
Usage uses **`input_tokens`, `output_tokens`, `cost`**. Its demonstrated returned
model is `typesafe/jev-1.14-20261014`, provider `TypeSafe`. The provider/model pages
support provider slug `typesafe`. Published examples establish these demonstrated
shapes, not a complete normative JSON Schema, authenticated effective revision or
real performance. Public example-derived test constants have explicit provenance.

Crucially, none of the examples establishes whether Decisions accepts/enforces
`provider.only` or `allow_fallbacks`. `fixture_request` therefore serializes only
the three demonstrated top-level fields. It adds **no invented provider, token,
version, reasoning or local-schema fields**. Required policy remains TypeSafe only,
`allow_fallbacks=false`, zero retries; the fake transport checks that policy out of
band. This is **not** live route enforcement, and routing constraints are **not
claimed to survive provider-bound serialization**. `serialize_decisions` always
raises `ContractUnavailable` for live use. No real transport exists. The unresolved
routing/output/spend contract prevents promoting these fake-only bytes to a live
request. No guessed endpoint behavior, provider fallback or direct Jev API.

## Frozen data, rubric and baseline

`understanding/intent.py` freezes two questions under `task-intent/v1`:

- Primary intent: `bug_fix`, `new_feature`, `refactor`, `investigation`,
  `documentation`, `unclear`. Label requested work, never eventual edits or outcomes.
  Restore existing behavior = bug fix; add behavior = feature; reorganize executable
  implementation without behavior change = refactor; findings/explanation only =
  investigation; prose/illustrative examples only = documentation. An explicit
  dominant objective wins over subordinate tests/docs. Equal independent objectives,
  vague scope and insufficient context are unclear.
- Explicit executable-source changes: implementation, repair, executable test and
  code refactor requests are positive; investigation/explanation/prose/static data
  and illustrative documentation code are negative. Conditional future repair or
  unspecified improvement is ambiguous, never an invented implementation request.

`tests/fixtures/intent/` contains **24 newly authored fictional descriptions**,
8 development / 16 holdout, with separate reference labels, exact input/file hashes,
splits, question/baseline-source/metric versions. Manifest SHA-256 is
`31e5fe76d0306effdfe1ad7bba8318bc39c16207128ba8aeca3630e332d7a8c2`.
These references are **agent-authored drafts awaiting independent human review**,
not human gold or real personal evidence. Ambiguous binary references are null.
No private history, actual executions, source locators, hidden tests or credentials.

The fixed baseline uses first matching keywords in this order: investigation,
documentation, bug fix, refactor, new feature; otherwise unclear. Code probability
is 0 for investigation/documentation, .5 for unclear and 1 otherwise. Its actual
implementation hash and version are frozen. No usable task-intent baseline existed;
retrieval/state models answer different questions. The published wire mapping
preserves these frozen semantics and question IDs, with full rubric in instructions
and concise rubric-consistent descriptions for all six choice criteria. No rubric, baseline, input, reference,
manifest or holdout prediction changed after the wire examples arrived.

No baseline/mock/provider predictions were collected for holdout. Public label
storage does not enforce organizational blinding: future collectors must not
consult answers before freezing predictions. Post-holdout changes require a new
version and future untouched holdout. A synthetic score control tests parsing;
there is no unlabeled difficulty target or score-based evaluation claim.

Predictors receive descriptions only. Actual serialized bytes contain only state,
public questions and model: no case ID/split/reference label/outcome/source code/
hidden test. Choice options necessarily appear as public criteria. This projection
is not a general private-text sanitizer; use reviewed fictional text only. Reports
omit descriptions, reference rows, exception prose and source locators.

## Parser, accounting and bounds

`understanding/decisions_offline.py` implements
`openrouter-decisions-published-examples/v2`. The previous v1 wire definitions
are retained in ignored review evidence; the frozen internal questions/rubric and
dataset manifest remain byte-identical. Choice criteria now describe each
category rather than repeat its label. The parser-only score control has ordered
fictional tank levels (empty, partially filled, full), a matching instruction and
exact legend validation. Its original internal control ID/prompt/levels remain
unchanged; this wire clarification creates no research target. Unregistered
Choice/Score definitions reject rather than silently use placeholder criteria. Request serialization uses published
field names and object/array shapes. The parser rejects unsupported/missing/extra
fields, missing/extra/duplicate/mismatched answer IDs, wrong types, undeclared
choices, nonfinite/out-of-range values, invalid distribution totals, bad score
level keys/legend descriptions/weighted scores, malformed JSON/UTF-8, duplicate JSON keys
and nesting >32. Choice confidence is distinct from category probability; the
parser does not invent an equality rule. Local rounding tolerance is `1e-6`,
explicitly not claimed as an officially documented provider tolerance.

Requested model, reported model, unknown effective revision and reported provider
are separate. Exact requested and published returned identities are admitted;
unapproved model versions/providers reject rather than becoming ordinary success.
Returned generation IDs are bounded and retained. Mock null metadata preserves
unknown routing/model/ID; official sample metadata remains explicitly mocked when
parsed in tests. Provider timestamp/local receipt are null in deterministic mocks,
not invented historical measurements or live receipts. No natural-language reasoning.

`usage_projection` reads the supplied official example's `input_tokens`,
`output_tokens`, scalar `cost` only. Chat-completion token aliases and Jev-direct
`X-Jev-*` accounting are not substituted. Missing/malformed values stay null;
explicit zero remains zero. Reported USD is separate from null estimates. Mocked
usage/route fields never become real charges or verified live routing evidence.

Local limits: one or two distinct questions; description <=4096 UTF-8 bytes;
request <=16 KiB; input token plan <=20,000; output token plan <=512; response
<=32 KiB. Plans are not measured tokens or server-enforced token ceilings. No
undocumented token-limit fields are serialized. Byte ceilings/single-use counters
are not hard USD caps. Fake transport rejects incorrect origin/path/method,
redirect/non-200, substitutions, unverified provider fields and any second attempt.
Error/timeout/unknown settlement never triggers retry or automatic expansion.

## Evaluation and executable demo

`understanding/intent_evaluation.py` provides a development-only evaluator;
response overrides accept development IDs only. References join after prediction.
Predeclared metrics: accuracy over all cases, six-class macro F1, confusion matrix
including abstain column, missing/malformed rate, primary coverage/abstention;
binary accuracy at >=.5 and Brier with explicit known-reference/scorable counts;
usage/billing/route coverage, development versus untouched holdout. Null binary
references are excluded; missing values never become failure. `unclear` is a class,
not abstention. With n=16 holdout, future conclusions are exploratory.

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/intent_example.py
```

This loads frozen dev cases, calculates baseline, builds published-format typed
questions/request bytes, injects fake responses, parses and evaluates, and writes
`.model-learner/j1-offline-v1/synthetic-report.json` (ignored). Mock always chooses
unclear with binary probability .5, independently of input/reference. Mock accuracy
1/8 and Brier 1/4 establish plumbing against draft labels, **never Jev accuracy or
calibration**. The script compares actual existing W6A fictional canonical inputs,
Beta-Bernoulli estimates and full advice before/after; they remain identical and
advice abstains. No canonical record/schema/policy/adviser code changes.

Pinned `minishlab/potion-base-8M` support remains unchanged (revision
`bf8b056651a2c21b8d2565580b8569da283cab23`, existing verified hashes/model2vec
0.9.0 support). A rule baseline requires no weights, cache reads, downloads,
fine-tuning or dependency additions. Actual validation/inventory is in `STATUS.md`.

## Future packet and bounded human review

`readiness()` always returns false. Provider slug identity now has supplied page
evidence; endpoint filtering/fallback enforcement is still unverified. Also resolve
credential/account/key limits, remaining prepaid balance, exact model/pricing/
billing, output/response enforcement and an enforceable <=$1 exposure cap, then
separately authorize one request. Illustrative input pricing is not a verified
charge or hard cap. Only existing prepaid funds; no top-up/subscription/purchase.

If later approved: at most one POST for reviewed development input, zero retries,
no fallback/batch/expansion. Retain generation ID, requested/reported model/provider,
route evidence, actual input/output tokens and `usage.cost`, completion/error,
provider time if supplied and actual local receipt, with billing coverage. Stop
without retry on missing/ambiguous settlement, missing route/cost evidence,
timeout/error, substitution or cap breach. J1 has no path to execute this plan.

One possible future human-review experiment: an independent person labels these
24 descriptions using the rubric while blinded to baseline/mock outputs, then
records disagreements and any new frozen version before holdout collection.
**Not started.** W1–W3/W4A preparation/W6A/W6B status remains; external authorized
execution owns isolation, verification and termination. W4B/W5/full W6/W7 remain
incomplete. W4A coding/containment/600-second Option A gates are distinct; no J1
classification or mocked result counts as coding-agent evidence. Stop at J1.
