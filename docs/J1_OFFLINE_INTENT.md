# J1 optional task-intent research: offline partial delivery

**Verdict: PARTIAL. Local fictional evaluation passes; the official OpenRouter
Decisions wire adapter is BLOCKED. Live accuracy and calibration are unmeasured.**

This optional experiment labels the *requested task*: primary intent and whether
executable source changes are explicitly required. It may eventually support
human review of task descriptions. It supplies no evidence of better task
understanding, difficulty, acceptance, coding-agent utility or model selection.
Ordinary ingestion, learning and advice never import or enable it. There is no
live transport, HTTP client, credential loader, agent executor or second learner.

## Evidence boundary and why the adapter is incomplete

The dispatch fixes HTTPS `https://openrouter.ai`, `POST /api/alpha/decisions`,
model `typesafe/jev-1.14`, intended provider TypeSafe, credential *name*
`OPENROUTER_API_KEY`, no retries and `provider.allow_fallbacks=false`. It does
not supply the official alpha request/response field definitions, supported
provider slug, documented float tolerance or complete usage/routing contract.
Repository inspection found no existing Jev/TypeSafe/Decisions implementation or
captured official schema. The coordinator's J1 folder contained a baseline only.
No network request is permitted in J1, so official documentation was not fetched.
The earlier two authenticated GETs belong to the coordinator's supplied preflight
account; this executor did not repeat them or inspect their credential.

`serialize_decisions` therefore raises `ContractUnavailable` unconditionally.
No unverified `provider.only=["typesafe"]` is emitted. A future wire adapter must
be implemented against reviewed captured official examples, including typed
questions/answers, supported provider routing and billing. The existing local
fixture shapes **must not be presented as the official Decisions API**. Provider
slug, exact version/pricing, actual balance and account/key limits are unknown.
Credential-file presence reported by the coordinator is not readiness evidence;
no credential or environment secret was read here.

## Delivered code and frozen data

- `understanding/intent.py`: two frozen questions, precise mixed-intent/code-change
  rubric, strict local question/prediction models and a fixed lexical baseline.
  Six intent labels: `bug_fix`, `new_feature`, `refactor`, `investigation`,
  `documentation`, `unclear`. Label requested work, never eventual edits. Explicit
  dominant intent wins; equal unrelated objectives and vague requests are unclear.
  Executable implementation/tests/repair/refactor are positive; prose, illustrative
  documentation code and investigation only are negative; conditional or vague
  work is ambiguous. The score control is fictional, without a difficulty target.
- `understanding/decisions_offline.py`: explicitly marked `j1-local-fixture/v1`
  serialization, fixed target metadata, fallback disabled, null unverified provider
  slug; single-use fake bytes transport; strict local typed parser and provisional
  usage projection; unconditional future-readiness blockers. No real transport can
  be selected or injected. The fake validates the actual bytes by rebuilding the
  frozen envelope and rejecting substitutions, redirects, wrong targets and retry.
- `understanding/intent_evaluation.py`: frozen loader, reproducible deterministic
  comparison, development-only fake evaluation, error/missingness accounting and
  sanitized report. Overrides accept only development IDs and fake response bytes
  or exceptions. No holdout evaluation entry point exists.
- `tests/fixtures/intent/{inputs,reference_labels,manifest}.json` and `README.md`:
  **24 distinct newly authored fictional cases**, split 8 development / 16 holdout;
  exact input hashes, separate rubric reference labels, schema/baseline/metric
  versions, question hash and actual baseline source hash. The loader pins manifest
  SHA-256 `31e5fe76d0306effdfe1ad7bba8318bc39c16207128ba8aeca3630e332d7a8c2`.
  Labels are **agent-authored reference judgments awaiting independent human
  review**, not human gold. Two ambiguous code-change references are null.
- `scripts/intent_example.py` and `tests/unit/test_intent_offline.py`: executable
  example and acceptance checks, using real evaluator/parser/baseline code and
  existing advisory/estimator interfaces.

The baseline uses the first matching keyword group in this frozen order:
investigation, documentation, bug fix, refactor, new feature; otherwise unclear.
Its code probability is 0 for investigation/documentation, 0.5 for unclear and 1
otherwise. It is deliberately simple and can miss paraphrases and mixed intent.
No existing task-intent baseline was found. Existing retrieval/task-state models
answer different questions. Pinned `minishlab/potion-base-8M` support remains
unchanged (revision `bf8b056651a2c21b8d2565580b8569da283cab23`, verified hashes and
model2vec 0.9.0 support in `representation/potion.py`). No download, inference,
cache read, fine-tuning or dependency change was necessary for a rule baseline.

Predictors receive descriptions only. The actual local serialized request has
only the description, public questions, fixed target and bounds: no case ID,
split, reference label, holdout answer, Task/Run/Observation, code or hidden tests.
Choice options are necessarily public question labels; their presence is not a
reference-label leak. The serializer is a narrow projection, not an arbitrary
private-text sanitizer. Only reviewed fictional text is appropriate. Reports omit
all descriptions, reference rows, exception prose and source locators.

The holdout was authored and frozen but **no holdout baseline or mock predictions
were collected**. Public labels and a local API cannot enforce organizational
blinding. Future collectors must not consult answers before freezing predictions.
Changing questions, rubric, baseline or labels after holdout results requires a
new evaluation version and future untouched holdout. No post-result tuning here.

## Parser, accounting and limits

Local parsing rejects missing/extra/duplicate/mismatched answer IDs, unsupported
fields (including reasoning), wrong types, undeclared labels, invalid distributions,
contradictory choice/confidence, score levels/weighted mean, nonfinite/range errors,
duplicate JSON keys, malformed UTF-8/JSON and nesting beyond 32. Answer order can
vary. The local distribution tolerance is `1e-6`; this is **not asserted to be the
provider's documented tolerance**. A new official parser may need different rules.
Local score semantics do not establish official score semantics.

Request bounds: two fixed production-intent questions, description <=4096 UTF-8
bytes, serialized envelope <=16 KiB, input token plan <=20,000, output token plan
<=512, response <=32 KiB. Token plans are not measured tokens or provider-enforced
limits. They and the single-use counter are **not hard USD caps**.

The provisional projection recognizes only scalar `usage.cost` as reported USD
and OpenRouter-style `prompt_tokens` / `completion_tokens`. This field mapping is
unverified for the alpha endpoint and must be checked against its official schema.
Missing/malformed values stay null; explicit zero remains zero. Unknown is never
imputed as free. Cost estimates are separate and null; no Jev-direct `X-Jev-*`
header is used. Requested model, returned model and unknown effective revision
remain separate. Unexpected reported model/provider rejects the whole local
response; null routing stays unknown, never successful route confirmation.
Mocked route/cost declarations cannot become real billing evidence. Generation
ID, provider time and local receipt are null in this deterministic fixture.

## Evaluation and demonstration

Predeclared metrics (`intent-metrics/v1`): primary accuracy over all cases,
all-six-class macro F1 (zero for undefined class F1), confusion matrix with an
abstain column, primary coverage/abstention, missing/malformed rate; binary accuracy
at >=0.5 and Brier on known references with probabilities. Binary denominators
and ambiguous-reference exclusions are explicit. Probability 0.5 is a valid
uncertain binary forecast, not a missing prediction. `unclear` is a class distinct
from abstention. Usage/billing/route coverage are reported separately by split.
With n=16 holdout, eventual conclusions are exploratory.

Run from the checkout using the installed environment (no installation needed):

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/intent_example.py
```

The script loads only development cases into predictors, runs the baseline,
builds both questions and actual local fixture bytes, injects fixed mock responses
independent of inputs/references, strictly parses them and writes a sanitized
versioned report under ignored `.model-learner/j1-offline-v1/synthetic-report.json`.
Mock always chooses unclear with binary probability 0.5. Development mock accuracy
1/8 and Brier 1/4 are **plumbing checks against draft references, not Jev accuracy
or calibration**. The report compares the existing W6A fictional input and full
advisory before/after; exact inputs, estimates and advice hashes stay identical,
including abstention. Classification has no access to canonical outcomes or data.

Actual acceptance results, exclusions and file inventory are in `STATUS.md`.
Tests independently check metric arithmetic and error reports, label separation
against actual serialization, all local typed shapes, target/fallback/model/provider
substitutions, bounds, no retries after timeout/error, absent credential/network
access, version/digest integrity, untouched holdout and unchanged learning/advice.
These do **not** establish exact official wire compatibility or live readiness.

## Future one-request packet; no execution authorized here

`readiness()` always returns false. Resolve every listed blocker before separately
authorizing a live smoke: captured official schema/tolerance; supported TypeSafe
slug and exact route; credential/account/key limits; remaining existing prepaid
balance; exact model/pricing/billing terms; an enforceable <=$1 total exposure cap;
and explicit one-request intent. A local counter, serialized size or illustrative
input price ($0.00084 for 20,000 tokens in the dispatch) is not spend enforcement
or verified current pricing. No purchase, top-up, subscription or provider fallback.

Later scope, if approved: at most **one POST** for a reviewed development example,
no retry/fallback/batch/automatic expansion; conservative output and bounded request/
response; existing prepaid funds only. Capture generation ID, requested/reported
model/provider, routing evidence, measured input/output tokens, `usage.cost` if
actually provided, completion/error, provider timestamp and actual local receipt,
and billing coverage. Missing/ambiguous settlement, missing route/cost evidence,
timeout/error, cap breach or substitution means stop without retry. J1 implements
only an offline packet; there is no enabling function or credential discovery.

One bounded possible next human-review experiment: an independent person labels
these 24 fictional descriptions using the written rubric while blinded to baseline
and mock outputs, then compares judgments to the draft references. Record disagreement
and any new frozen version before any authorized holdout collection. **Not started.**

W1–W3, W4A preparation, W6A and W6B status is unchanged. External approved
execution owns isolation, independent verification and termination. W4B/W5/full
W6/W7 remain incomplete. W4A's coding/containment/600-second Option A gates are
separate; no J1 label or mock report counts as coding-agent evidence. Stop at J1.
