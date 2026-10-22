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

`rehearse` accepts only the exact existing offline FakeTransport and frozen input.
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
