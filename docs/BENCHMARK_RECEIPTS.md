# W4A.2 benchmark first-receipt provenance

Receipt-only offline increment, 2026-10-21. A receipt establishes local availability
of exact evidence; it does not establish execution, independent authenticity,
verification validity, statistical eligibility or externally authenticated time.
The W4A target remains `ResourceBudget(max_duration_seconds=600)`. W4B is blocked
by the containment, isolated-verifier and whole-process-tree stop gaps documented
in [W4A_CONTAINMENT.md](W4A_CONTAINMENT.md).

## Reproduced gap and additive contract

Before production changes, a fictional `clamp` benchmark used the supported
preparation, capture/import, Run/Attempt, bound synthetic JUnit, assessment and
export contracts in disposable storage. Its complete report produced a verified
synthetic success. With a 600-second budget, the exporter still returned
`eligible_for_configuration_learning=False` and
`budget_measurements_not_supported`. An assertion requiring `first_receipts` in
the export failed: neither old source times nor export time reconstruct the first
receiver receipt of every dependency. The actual failing report is retained in
the new ignored `.model-learner/w4a2-receipts-v1/gap-before.xml` and accompanying
text. No private ledger, agent execution or actual candidate verification occurred.
The report is a fictional verification-input fixture, not model-performance data.

`src/model_learner/benchmark/receipts.py` adds three narrow operations:

1. `benchmark_receipt_bundle(root, retained_export)` revalidates the exact existing
   `BenchmarkEvidence` against its trusted, finalized source through the existing
   exporter, including its unchanged real-execution containment gate. It hashes
   relevant canonical source records and retains only identities, digests, source
   times, safe associations and artifact/report digest references. It writes no
   canonical records and runs no candidate, verifier or agent.
2. `book.capture(bundle)` returns a new `BenchmarkReceiptBook` using the current
   receiver clock. Identical captures preserve the first timestamp and membership.
   Rebinding an immutable identity to different content fails atomically. Capture
   has no caller-supplied timestamp argument. Assign and persist the returned book.
3. `book.as_of(bundle, cutoff=...)` audits the availability of that exact retained
   export. Every source record, the bundle/export binding and every source time
   must pass the cutoff. Missing/null receipt, late receipt and future source time
   have distinct exclusions. It returns no canonical Observation or learner input.

For reviewed permitted benchmark input, retain the export and bundle alongside the
book in ignored local storage. Illustrative Python (no CLI/automatic intake added):

```python
export = export_benchmark_evidence(root)
bundle = benchmark_receipt_bundle(root, export)
book = BenchmarkReceiptBook(target=bundle.target).capture(bundle)
# Persist bundle.model_dump_json() and book.model_dump_json() locally.
restored = BenchmarkReceiptBundle.model_validate_json(bundle.model_dump_json())
book = BenchmarkReceiptBook.model_validate_json(book.model_dump_json())
view = book.as_of(restored, cutoff=forecast_cutoff)
assert book.capture(restored) == book
```

Capture the **same retained export** on replay. A fresh export changes its
Observation `recorded_at` even when its deterministic Observation ID is unchanged;
that is conflicting exact content and the receipt book refuses it. Do not erase
or backdate the first receipt to accommodate a fresh export. An actual assessment
revision has its own Outcome and derived Observation identities and can be captured
in the same target book. The source must be quiescent; concurrent source mutation,
live-ledger merging and multi-writer persistence are unsupported.

## Versioned sidecar fields and limits

| Structure | Version / retained fields |
| --- | --- |
| Bundle | `benchmark-receipt-bundle/v1`; exact export digest, export time, target, available Attempt/Outcome/Observation IDs, immediate supersedes ID, source bindings, verification references, copied exporter eligibility/exclusions, unknown fields and bundle digest. |
| Target | `source_kind=benchmark`, dataset ID/version, benchmark/Task/Run IDs, requested configuration ID, acceptance ID/version/exact digest, unchanged budget, fixture identity/version/fingerprint, fixture-versus-real execution origin. |
| Source binding | Type + original immutable identity, SHA-256 of exact canonical JSON source record, available Task/Run/configuration/acceptance associations and separately named source times. Task, Run, Attempt, Session, explicit links, bounded Event, Verification, selected Outcome ancestry and exact exported Observation are covered. Configuration/acceptance snapshots have separate content bindings. |
| Book | `benchmark-first-receipts/v1`; one exact target and identity-to-digest/first-receiver-time map. Explicit null receipt is unavailable. |
| Availability | Exact target/export/cutoff, available identity/digest membership, explicit exclusions, `fully_available` for that bundle's receipt coverage, copied learning exclusions and unsupported/missing fields. |

Canonical JSON hashing reuses the exporter's sorted, compact JSON SHA-256 rule.
The bundle digest covers all its metadata; capture binds the export identity to
that exact bundle digest as well as binding each source identity to its own digest.
Unsupported versions, malformed digests, digest disagreement, missing required
bindings/associations and incompatible task/run/configuration/acceptance/target
associations fail closed. Dataset/version mismatches cannot share a book. Source
revalidation is authoritative at construction; imported serialized declarations
are not signed provenance. Replacing both metadata and checksums is outside the
integrity guarantee, as in W2. Independently retain reviewed frozen digests.

`fully_available` means all **declared evidence records in this exact bundle**
have receipts and source times by cutoff. It makes no claim about a relationship
that the source cannot establish. In particular:

- Verification-to-Attempt has no explicit canonical link here. Retain
  `verification_to_attempt_explicit_link` as unavailable; do not infer it merely
  from a passing report or a single complete segment.
- Initial prospective scope receipts and complete resource-measurement coverage
  remain unsupported. This post-finalization receiver cannot establish initial
  knowledge in an earlier execution. Unknown configuration versions, canonical
  latency and cost are reported explicitly when absent.
- Missing attributed Attempt or assessment identity produces an availability
  exclusion. A known unknown assessment can be available while remaining unverified
  and statistically ineligible. Timeout/abandonment does not create verified failure.
- Existing Outcome supersession is retained, including ancestors and source times.
  A later correction has its own first receipt. Replaying the earlier exact bundle
  at its earlier cutoff is unchanged. This module audits snapshots; it does not
  select a current assessment head or let a received incomplete correction fall
  back to an old success. The exporter remains the assessment-selection authority.
- Availability diagnostics may list excluded identities and copied exporter facts
  for audit. Only `available_records` declares membership; diagnostics are not
  prospective predictor features. No forecast/estimator integration is added.

The sidecar omits raw conversation/capture payloads, task prose, hidden test names
or source, candidate bytes, report XML, arbitrary metadata and filesystem paths.
Opaque public identifiers are narrowly validated; recognizable credential forms
are rejected. This is a reviewed metadata contract, not an automatic sanitizer
for arbitrary private input. Human review and repository privacy checks remain
necessary. Source records are hashed exactly without copying their private fields;
sidecar hashes cannot reconstruct canonical records by themselves.

## Offline acceptance coverage

All new tests use fictional data in disposable storage and call the supported
exporter/sidecar APIs. No real-source wrapper or W2 REAL-only resolver is used.

| Cases | Executable coverage in `tests/integration/test_benchmark_receipts.py` |
| --- | --- |
| A–C | Exact benchmark/dataset/target/configuration/acceptance identities; local initial receipt; immutable replay and no count growth. |
| D / R12 | Conflicting identity, exact digest mismatch, invalid receipt/bundle versions and naive timestamps reject; original book unchanged. |
| E–G | Old source times with late first arrival; absent/null/late receipt for each of 13 dependency kinds; required record/association removal rejects. |
| H | Append-only correction preserves earlier cutoff; new revision/parent identities retained; missing verification prevents complete revision availability. |
| I | Task, Run, dataset/version, configuration, acceptance and evidence/export/artifact mismatches reject. |
| J–L | 600-second exclusion preserved; no canonical latency or charge fabrication; synthetic timeout remains unknown/unverified/ineligible. |
| M | Prose, hidden tests, raw data, artifact/report paths and unrelated Task omitted; unsafe public identifiers rejected; pure privacy screening passes. |
| N | Existing benchmark exporter, W2 receipts, W3 lifecycle, budget/learning, assessment and prospective regression suites exercised unchanged. |
| O | Bundle/book JSON reload reproduces cutoff membership, digests, exclusions, unknowns and counts; replay remains idempotent. |

Initial implementation testing exposed an incorrect expectation that the fixture
fingerprint had a `sha256:` prefix; the existing exporter uses a bare digest.
Corrected the sidecar to match the actual interface. That failed run remains in
the ignored reports. Required validation totals and skipped tests are recorded in
STATUS; no completed runtime diagnostics or historical experiments were repeated.

## Duration policy decision only

The following comparison does not implement or approve a new target. Recommend
**Option A** conservatively: retain existing semantics and missing-measurement
ineligibility while the W4A 600-second proposal stays unchanged.

| Option | Outcome estimated | Required measurements | Existing support / missing work |
| --- | --- | --- | --- |
| A — existing canonical semantics | Acceptance success within the declared budget under current observation rules. | Complete attributed `Attempt.latency_seconds`; valid verification and configuration coverage. Unknown duration stays unknown. | Canonical ResourceBudget and ordinary observation rules already exist. Benchmark exporter deliberately excludes every non-null budget; valid benchmark measurement integration remains missing. |
| B — versioned process-elapsed benchmark target | Acceptance success within a separately named externally controlled execution interval. Native inference latency stays separate. | Verified whole-tree boundary; monotonic clock and explicit start/stop endpoints; proven complete termination/cancellation receipt; coverage and missingness rules; independent acceptance. | Identity/digest/receipt fields can retain supporting metadata. Whole-tree stop, isolated runtime/verifier, measurement policy, revised forecast/acceptance target and human approval are missing. Root process elapsed time is insufficient. |
| C — duration as safety control, new statistical target | Acceptance success under a separately approved target that does not claim the original duration-budget estimand. | Valid independent acceptance, declared safety stop/exposure accounting and explicitly defined treatment of incomplete/censored executions. | A nullable budget exists for genuinely different targets. It cannot silently replace W4A's 600-second budget. New versioned experiment/forecast/acceptance contract and human approval are required. |

| Option | Historical compatibility | Bias/leakage risk | Smallest prospective acceptance test | Schema implications |
| --- | --- | --- | --- | --- |
| A | Only records with actual complete accepted measurements; receipts cannot repair missing latency or historical availability. Current budgeted benchmark rows stay ineligible. | Selecting measured/finished rows can favor easy executions; retain missingness and exclusions. Never derive timing from future outcomes. | One fictional verified budgeted outcome with missing latency remains excluded; later test measured eligible/exceeded/missing cases only under a separately authorized benchmark measurement adapter. | No change to keep current behavior. Future adapter feasibility requires review; none implemented here. |
| B | Existing process durations are incompatible unless boundary, clock, endpoints, complete stop and prospective receipt coverage actually satisfy the new policy. No retrospective conversion. | Root-only timing understates exposure; missing cleanup and selective timeout removal bias results. Freeze interval and target before outcomes. | In an approved whole-tree runtime, one finite completion plus one owned descendant timeout; exact start/stop/termination receipts; incomplete stop stays unknown. Freeze new target before either case. | A separate versioned benchmark sidecar/target may suffice. Multiple first-class duration bases would require an explicit canonical schema decision; migration is not authorized. |
| C | Original 600-second observations cannot be relabeled. A new prospective cohort is safest; reuse requires explicit compatibility and original availability evidence. | Excluding timeouts or dropping the budget after seeing results changes the estimand and creates survivorship bias. | Freeze the new success target and safety-stop rules before one completion and one timeout; retain both with predeclared unknown/censor treatment. | Existing nullable-budget models may represent the new approved target without migration; versioned protocol/forecast/acceptance identities still need review. Canonical semantic changes require separate approval. |

No option solves runtime security. The smallest next action is a human review of
the duration/coverage target and a supported containment/verifier/process-tree
boundary before any separately authorized W4B preparation or measured execution.
