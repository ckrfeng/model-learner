# J2 bounded Decisions readiness

J2 is **PARTIAL**. Offline contract validation passes. Full contract readiness is
PARTIAL; routing, spending and the live smoke are BLOCKED. Zero paid POSTs, free
GETs, network requests or credential reads occurred. The existing user-confirmed
account spending limit does not establish remaining prepaid funds or an enforceable
per-request exposure strictly below $1. No top-up, purchase or subscription.

## Evidence and frozen packet

Only the captured public examples described in [J1](J1_OFFLINE_INTENT.md) were
used. They demonstrate `https://openrouter.ai/api/alpha/decisions`, requested
`typesafe/jev-1.14`, returned `typesafe/jev-1.14-20261014`, provider `TypeSafe`, and
the typed fields. They do not document enforcement of `provider.only`,
`allow_fallbacks`, output ceilings or a dollar ceiling for Decisions. No guessed
routing/token fields, endpoint probes or contract discovery were added.

`decisions_readiness.frozen_request` validates the existing manifest and input file
hashes and selects only `dev-01` using its exact description digest. It never reads
the draft reference-label file. Wire bytes contain only the published model, state
and frozen questions; case identity, split and reference labels stay local. Other
inputs are not classified. J1's 24 cases, rubric, baseline and evidence are unchanged.

The separate versioned protocol records TypeSafe-only, fallback false, zero retries,
one paid POST maximum, cumulative input planning of 4,096 tokens (ceiling 20,000),
output planning of 256 (ceiling 512), exposure strictly below $1 and the overall
$15 existing-prepaid ceiling. These local plans are **not provider enforcement**.
Request/protocol hashes bind the exact offline packet. No score/difficulty target,
training, local model download or canonical outcome/advice integration is introduced.

## Fail-closed gates

`readiness` has no caller evidence overrides and always returns false with exact
blocker categories. The conditional J2 authorization is recorded as present; it
is not sufficient to clear routing or spending. Numeric budget checks reject
missing/nonfinite/nonpositive funds or exposure, exposure >=$1, insufficient
existing funds, or invalid token plans. Even passing numeric values cannot enable
live use or establish that the provider enforces them.

Missing evidence remains:

- Decisions TypeSafe-only and no-fallback enforcement.
- Provider enforcement of conservative output bounds.
- Current pricing, billing/settlement, remaining prepaid balance, and an enforceable
  exposure strictly below $1 and within the existing funds / $15 overall ceiling.
- A validated safe local credential/transport path and an armed durable live
  one-shot marker before transmission.

No authenticated GET was necessary: account evidence could not resolve the
undocumented routing/output enforcement gates. `.env.local` was never opened.
`refuse_live` always raises before credential/network access. There is no live
transport, arbitrary URL parameter, retry path or account-information artifact.
Resolving these prerequisites requires a later explicitly directed step; J2 stops
here. No next workstream is started.

## Mock rehearsal and receipts

`rehearse` accepts only the exact existing offline FakeTransport or the exact
offline MockHTTPTransport described below, and the same frozen input.
Before mock dispatch it exclusively creates a fixed `mock-attempt-consumed.json`
with mode 0600, syncs the file, then syncs its directory. A pre-existing, partial or
symlink marker refuses dispatch. Sync failure refuses dispatch and retains the
marker. Timeout, rejection, malformed/mismatched model/provider or ambiguous
response consumes the mock attempt permanently in that directory. No retry.
This rehearsal marker is distinct from an unarmed live marker; it supplies no
live-call protection or authorization. Tests use disposable temporary directories.

Sanitized mock receipts contain UTC start/end times, protocol/request/response
hashes where available, parsed typed predictions and confidence, reported metadata
and usage where valid. Error prose/raw response bytes are omitted. Reported mock
cost remains separate from null actual billed cost, and routing verification stays
false even when sample metadata says TypeSafe. Unknown cost is not zero. Invalid
or over-plan results remain mocked error/ambiguous and cannot update verified
outcomes, observations, estimates or advisory results. One future development
result would not establish Jev accuracy or calibration; no holdout predictions or
human-gold review took place.

Run the offline packet writer from the repository root:

```sh
PYTHONDONTWRITEBYTECODE=1 .venv/bin/python -B scripts/decisions_readiness_example.py
```

It writes only ignored `.model-learner/j2-readiness-v1/readiness.json`; it does not
dispatch even a mock or consume any live marker. Actual test results and the
unchanged Git baseline are recorded in `STATUS.md`. No staging, commit, push,
merge, history change, coding agent or historical experiment rerun is part of J2.

## Bounded offline HTTP-envelope seam — 2026-10-23

The previous fake checked status/redirect policy through caller arguments but had
no explicit response-envelope object: body bytes alone could not exercise missing
Content-Type, duplicate headers, encoding/length contradictions or returned route
metadata. `understanding/decisions_transport.py` adds that missing local seam;
it does not add an HTTP client, discover provider fields or implement live transport.

`ResponseFixture` requires explicit origin, path, status, redirect state, headers
and body. These are newly authored synthetic DEVELOPMENT fixtures, not network
captures, signed receipts or proof of the declared route. The exact
`MockHTTPTransport` consumes one in-memory attempt, validates the envelope, and
reuses J1's existing request/model/question, no-fallback/provider and usage
controls. J2's existing frozen `dev-01` request, durable mock marker, answer parser,
accounting checks, error handling and sanitized receipts are reused unchanged.
No new reference labels, holdout predictions or task examples are introduced.

This deliberately small **local fixture dialect** admits exactly:

- Existing HTTPS Decisions origin/path, status integer 200, redirect state false.
  An alternate origin, path/query, redirect or error status refuses.
- Bounded bytes (existing 32 KiB ceiling), up to 16 explicit header pairs,
  case-insensitive distinct names and at most 256 printable ASCII value characters.
- Required Content-Type `application/json`, optionally `; charset=utf-8`;
  optional Content-Encoding `identity` and optional matching decimal Content-Length.
  Other headers (including Location), duplicate names, compressed encoding,
  missing media type and contradictory lengths refuse. This is not a complete
  provider HTTP schema or a validated production parser.

Successful envelope validation still requires the existing full typed Decisions
body contract. HTTP success alone supplies no classification, routing proof or
verified outcome. Existing example model/provider declarations remain declarations;
missing actual usage/cost remains unknown. The wire body still contains only the
existing published `model`, `state` and `questions`; no invented provider-routing,
fallback, output-limit or spending fields are serialized.

New receipts add `transport_contract="decisions-offline-http-envelope/v1"` and
`evidence_class="synthetic_development_http_fixture"`. They retain `mode=mock_only`,
zero paid POSTs, false routing verification and null actual billed cost. Raw headers,
response bodies and exception prose are omitted. Rejected envelope/transport errors
yield no prediction; the mock marker remains consumed. A syntactically accepted
response can have a digest without yielding a valid typed prediction. Neither
success nor error receipts can be used as an Observation, Verification or advisory
input; no outcome, learner, forecast, evidence eligibility or advisory code changed.

Reproduce the deterministic offline integration using the installed environment:

```sh
PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  .venv/bin/python -B -m pytest -q -p no:cacheprovider \
  tests/unit/test_decisions_transport.py \
  tests/unit/test_decisions_readiness.py tests/unit/test_intent_offline.py
```

This exercises actual local fixture processing end to end, not external provider
execution. All 60 new controls and the 144 existing J1/J2 controls pass. Actual
regression/lint/privacy results and Git inventory are recorded in STATUS.

`readiness` stays false and `refuse_live` still always raises. Subclasses/arbitrary
clients are rejected before marker creation. No `.env.local` or environment credential
value is loaded; no private history, source code or hidden holdout is supplied as
classification input or transmitted.
No endpoint/provider availability, authenticated dashboard/configuration or account
probe was necessary for this seam, so no new URL/key information is requested.

Live blockers listed above remain: provider identity and exact route enforcement,
no-fallback/output ceilings, secure credential transport, current funds/pricing/
settlement and bounded exposure, then separately gated live one-shot controls.
Existing conditional paid-use authorization is preserved for later separately
authorized dispatch; this increment authorizes no paid smoke, retry, fallback,
purchase or allowance assumption. Optional coding-agent sandbox readiness is
independent of this offline classification work. Stop at this bounded increment;
W4A/W4B coding/containment/duration and final real E2E acceptance remain open.

## Official live-gate review — 2026-10-23

**BLOCKED before dispatch; no paid smoke or authenticated account request.**
The human's bounded one-attempt authorization remains valid. Technical prerequisites
are still missing; another spending approval is not the blocker. No new client,
mock abstraction, route substitution or gate override was implemented.

Current public documentation improves on J1/J2's captured examples. The official
[Decisions reference](https://openrouter.ai/docs/api/api-reference/alphadecisions/submit-a-decisions-request)
lists the existing POST endpoint, required model/state/questions, optional provider
routing preferences, bearer authentication and typed response with model/usage;
provider and generation ID are also described. Its example usage includes input
tokens, output tokens and cost. No Decisions output-limit parameter was found in
that reference. This establishes published fields, not a successful current call
or completeness of every undocumented capability.

The official [provider-selection guide](https://openrouter.ai/docs/guides/routing/provider-selection)
documents provider `only` and `allow_fallbacks=false`; account and request
allowlists intersect. Together with the Decisions provider field, this supports
the intended routing controls at the documentation level. It does not establish
the actual selected key/account policy, an authenticated TypeSafe route or
execution identity. The current frozen fake-only request still omits routing
fields and cannot be sent as an approved live request unchanged.

The [Jev 1.14 model page](https://openrouter.ai/typesafe/jev-1.14) lists TypeSafe,
262,144-token context and prices of $0.042 per million input tokens / $0 output.
That listing is not a measurement of this account's availability, a settled charge
or proof that one request fits the approved ceiling. The dedicated public model
endpoints URL could not be retrieved through the browsing tool; no authenticated
substitute or alternate provider/model was tried.

| Gate | Established now | Exact missing evidence |
| --- | --- | --- |
| Provider/route | Intended OpenRouter Decisions endpoint and `typesafe/jev-1.14`; documented routing controls | Non-secret evidence tying the selected credential/account to the exact allowed TypeSafe route and no-fallback policy; a supported live request contract incorporating those controls. |
| Output exposure | Frozen public development input and two fixed typed questions; existing local response-size bound | Endpoint-specific supported output cap, or a documented finite-output guarantee sufficient for the approved conservative bound. Local read limits and post-response rejection do not constrain provider work. |
| Spend | Published model price; existing one-attempt authorization, $1 ceiling and lesser of remaining prepaid or $15 total | Current selected-key/account remaining balance, applicable limits/usage and enforcement that bounds this one request and total exposure. No 400-million-token allowance assumed. |
| Credential transport | `.env.local` is an ignored regular file, not a symlink; metadata only inspected | Credential availability, account/provider identity and approved secret-safe loading/transport remain unverified. Presence is not a valid-key check. Metadata showed group/other mode bits; ACL/effective access was not assessed and permissions were not changed. |
| Result receipt | Published model/provider/usage/cost fields | An actual response and billing/settlement basis, obtainable only after all pre-dispatch gates pass. No receipt or charge was fabricated. |

The [spend-controls guide](https://openrouter.ai/docs/guides/best-practices/spend-controls)
describes workspace/guardrail checks and ownership-dependent attribution. The
[shared-key cap guide](https://openrouter.ai/docs/guides/best-practices/capping-shared-agent-keys)
describes key credit limits, reset windows, BYOK inclusion and rejection after a
configured limit is reached. Neither proves that the locally selected key has
those controls or current funds. No key-limit/account setting was changed.

Needed next: official endpoint-specific output/enforcement evidence and non-secret
selected-account/key metadata confirming identity, route policy, remaining funds
and applicable exposure cap, plus a reviewed secure credential mechanism. Obtain
that through a secure operator/provider workflow; never paste a key into chat.
No credential was loaded, no account/dashboard endpoint authenticated, no input
was submitted and no live one-shot marker was armed or consumed. Only public
documentation was browsed; searches outside official sources were not used as
technical evidence. Prior frozen datasets, wire hashes and all trust rules remain
unchanged. Optional coding-agent sandbox approval is unrelated to these blockers.

Execution stopped at these missing facts as required. J2 still refuses live use;
no advisory/utility learning record was created. Exact checks, repository state
and the documentation-only commit proposal are in STATUS.
