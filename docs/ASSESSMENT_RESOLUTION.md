# Historical assessment resolution

Assessments are immutable append-only records. The read-only resolver selects
one assessment state per run at an explicit timezone-aware cutoff; it never
rewrites or deletes an original outcome, verification, capture or observation.

`resolve_assessment(outcomes, run_id=..., cutoff=...)` includes outcomes whose
`recorded_at <= cutoff`. A valid state has one root, one complete unbranched
supersession chain and one head. Equal revision timestamps are allowed: lineage,
not UUID or import order, determines the head. Missing/unavailable parents,
foreign-run parents, revisions before their parent, cycles, branching revisions,
multiple roots and conflicting identities fail closed with deterministic issue
codes. Identical replays do not duplicate records. A future branch cannot
invalidate an earlier valid state, and a parent recorded after the cutoff is
indistinguishable from a missing parent at that cutoff.

The latest visible head remains authoritative even if its state is unknown or
censored. A prior successful label is never a fallback. Unknown and censored
observations have no binary label availability and cannot train configuration
estimates. Completed capture events themselves supply no task label.

`resolve_real_observations(repository, dataset=..., cutoff=..., run_ids=...)`
rebuilds at most one observation per resolved run without persisting anything.
The dataset must be explicitly real. Optional run IDs constrain the cohort and
are deduplicated. Resolution checks task creation, completed run boundaries,
task/session and run/session association times, event observation and ingestion,
and the selected assessment's deterministic verification evidence. Future events
and associations are excluded. Evidence must be available by the cutoff and by
the assessment, bound to the exact run/artifact/acceptance specification, and
consistent with its verified binary label. Incomplete or mixed attribution,
contradictory native configuration, missing resources under a declared budget,
and unknown/censored/unverified assessments retain their existing exclusions.
Unavailable evidence or capture yields a run exclusion, never a substitute label.
Repeated snapshots have deterministic identities and ordering.

`derive_real_observation` provides the existing builder's derivation without a
write. `build_real_observation` retains its current API and idempotent persistence
of exact assessment derivations; it intentionally preserves all revisions.
Historical callers should use the resolver before learning, rather than feeding
all preserved derivations into an estimator as independent trials.

`resolve_observation_revisions(observations, outcomes, dataset=..., cutoff=...)`
selects visible persisted derivations in an existing cohort. It returns the
unique stable derivation matching the resolved head, deduplicating identical
keys and retaining the earliest declared availability. Different derivations
for one selected head fail closed. A head with no visible derivation is excluded.
This helper checks lineage and observation/label availability; it does not
independently revalidate capture or deterministic evidence. Use the repository
resolver for that stronger check.

## Limits of historical availability

M1.1 stores declaration/execution times but no receipt timestamp for `Run` or
`Attempt`, and `Verification` has observation time but no ingestion timestamp.
The resolver cannot prove when a backdated declaration or verification was
actually received. `Outcome.recorded_at`, `Observation.recorded_at`, task creation
and association times are also trusted declared timestamps, not SQLite insertion
receipts. A caller must not interpret this as forensic receipt-time reconstruction.
`ResolutionSnapshot.method` and `availability_limitations` report these limits.

Learning eligibility in a repository snapshot therefore additionally requires a
unique matching persisted builder derivation with `recorded_at <= cutoff`. Its
stable key binds the exact attribution, events, evidence, target and label, and
its `attempt_ids` bind the immutable declaration set to reconstruct. Later
untimestamped attempts are excluded from that earlier set; missing, foreign or
malformed attempt references fail closed. The existing explicit task-group
override is preserved from that unique derivation. Conflicting persisted head
derivations fail closed. A purely retrospective
row lacking that availability proof retains the assessment with incomplete
attribution, no current attempt IDs or configuration, and becomes ineligible
with `historical_derivation_availability_unknown`. Later changes to declarations
cannot borrow an earlier clean derivation's eligibility or alter its selected
attempt set. This conservatively
withholds learning instead of asserting that untimestamped attribution was known.
The proof still depends on the honesty of the existing declared record timestamps.

When there is no persisted builder derivation available at the cutoff, exact
historical attribution remains unavailable. Declaration receipt contracts would
allow more complete reconstruction in a separately approved schema change. The
original persisted derivations remain available for audit; this work does not
alter shared domain contracts or migrations.
