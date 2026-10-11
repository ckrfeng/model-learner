# Offline benchmark evidence pipeline

The `benchmark-evidence/v1` export connects finalized benchmark receipts to the
existing immutable `Observation` contract. It executes no agent, candidate,
acceptance process or provider request. Real-origin export remains behind the
existing fail-closed containment gate. Synthetic/native-format receipt fixtures
and handwritten public candidates exercise the offline pipeline only.

An eligible `benchmark` row in a dataset ending in `:fixture` is **algorithm
rehearsal evidence, never a measurement of a real model's performance or utility**.
Fixture receipt source versions and execution origin remain explicit. There is
no relabeling as `real`, no suite-level acceptance target, and no pooling across
incompatible fixture targets.

## Export and import

```sh
model-learner benchmark evidence-export ROOT --output evidence.json \
  --checkpoint 2026-10-11T00:00:30Z
model-learner init --database observations.sqlite3
model-learner benchmark evidence-import evidence.json --root ROOT \
  --database observations.sqlite3
```

The root must be the retained trusted operator-owned benchmark source, outside
the candidate mount. Export files are audit artifacts; keep them outside Git and
outside agent mounts. A content digest detects corruption, **not authenticity**.
Import requires the trusted root and rederives the entire export against its
manifest, finalized result and source ledger. This includes source task identity,
exact configuration, native telemetry disagreements, live candidate fingerprint
and independent report hash. Candidate/report/result inputs must be regular
non-symlink files; report and manifest bounds also follow benchmark validation.

The Python APIs are `export_benchmark_evidence(root, checkpoints=(),
historical_cutoff=None)` and `import_benchmark_evidence(repository, evidence,
root=root)` in `model_learner.benchmark.evidence`.

The envelope retains:

- Explicit benchmark, task, run, attempt and selected assessment identities; exact
  acceptance specification and budget; fixture family/version/fingerprint and
  `fixture`/`real` origin; exact configuration including harness versions.
- Native event IDs, receipt timestamps, **original ingestion timestamps**, source,
  emitter and adapter versions and allowlisted native structural observations.
  Safe redaction field names/counts preserve omission coverage.
  Raw payloads, agent prose, commands, outputs and arbitrary event metadata are
  omitted. Independent labels never come from an agent report.
- Audit-only artifact/report fingerprint bindings, independent verifier identity,
  result and observation time. Hidden case IDs, checks, report body and candidate
  contents are omitted. Independent verification is retained for interrupted
  runs even when the unknown assessment deliberately cites no evidence.
- Requested checkpoint times and explicit missing-session coverage reasons.
  Linked session projections use both event receipt and ingestion availability
  and the actual task/run association time. Verification/test state is never
  supplied to checkpoint construction.

Unknown/censored assessments have no binary label availability. Interrupted
execution, absent native telemetry, incomplete attribution, declaration/native
conflicts and missing independent evidence remain visible and ineligible. Single
operator-predeclared configuration coverage, a known model/provider/harness and
harness version, complete native capture and independently verified artifact-bound
binary evidence are necessary for eligibility. Unknown optional configuration
versions remain unknown inside the exact snapshot; they are never invented.
Nonempty arbitrary configuration metadata is rejected in this narrow export to
prevent hidden-label/private-content channels while preserving exact configuration
identity; configuration snapshots are never rewritten to make them acceptable.
Native structural allowlisting is not semantic redaction of caller-supplied IDs.

Benchmark resource telemetry has no sufficiently attributed measurement contract
in this slice: costs and native durations remain null, and declared resource
budgets prevent eligibility rather than treating missing measurements as zero.

Import records actual import availability. Reimporting the same derivation returns
the original row without changing its timestamp or adding a trial. Destination
replay checks and insertion share one `BEGIN IMMEDIATE` transaction; a conflicting
derivation for the same run/assessment is rejected before a destination write.
The native audit envelope remains the retained evidence source; import inserts a
learning observation and does not copy source native records into a different
ledger under fabricated ingestion receipts.

## Historical cutoffs and evaluation limits

`--historical-cutoff` selects the visible head of the existing append-only
assessment chain. A future verification, event ingestion or assessment cannot
supply historical evidence. An unavailable/conflicting assessment becomes unknown;
there is no fallback to an older binary label. Export time and later import time
remain actual availability, so a posthoc export cannot become a historically
available training row merely by choosing an earlier cutoff.

The existing exact-target Beta-Bernoulli learner accepts an eligible fixture
observation in its explicit fixture dataset. Its default evidence requirements,
cutoffs and target/budget filters remain unchanged. Revised assessments are
retained as distinct derivations. The existing learner rejects multiple different
derivations for the same run: evaluate one explicitly selected immutable revision
per run in a snapshot; do not feed the complete revision history as independent
trials. This slice does not extend the real-only historical resolution CLI to
benchmark histories.

**All exported checkpoints have `eligible_for_task_state=false`.** The current
benchmark ledger is finalized after execution, and lacks an attested prospective
initial/configuration/run-scope receipt contract. Audit projections report
unavailable event/scope coverage instead of backdating ingestion or associations.
No `TaskStateExample` is manufactured. A separately scoped prospective collector
is still required before the real pilot can supply eligible state examples.

Each fixture keeps its distinct exact target. Fixture family identity is retained
for dependence auditing, but the current evaluator clusters task UUIDs and does
not model family reuse. The pilot's 16/8 split remains below the 30/20 row floors
and its four held-out families below the five-cluster floor. No statistical floor
is reduced, no common target is invented, and these checks do not establish
predictive improvement or causal model comparisons.

## Validation

Owned unit and integration coverage uses synthetic receipt fixtures and frozen
public bytes; it launches no candidate or agent. Tests cover event privacy,
artifact/report bindings, unknown/incomplete/configuration conflicts, checkpoint
unavailability, no-session checkpoint requests, historical/future exclusion,
revision heads, honest import availability, idempotence, source tampering,
corruption, conflicting replay and existing exact-target learner consumption.
Coordinator integration additionally exercises the public handwritten candidate
through the existing acceptance/finalization workflow. None of this attests real
agent containment or real model performance.
