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
