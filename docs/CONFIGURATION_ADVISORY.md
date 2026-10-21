# W6A offline configuration advisory

`model-learner learn advise --input-file INPUT.json` prints
`configuration-advisory/v1` JSON. It never opens the default database, updates a
learner, records a forecast, launches an agent or selects an execution arm.
The public library entry point is
`model_learner.learn.advisory.advise(AdvisoryRequest, observations=(), bundles=())`.
`AdvisoryInput` defines the versioned command envelope; serialize it with
`model_dump_json()`. The request includes an explicit Task, candidate configuration
snapshots, frozen `CompatibilityPolicy`, and timezone-aware cutoff. The policy
binds the dataset/source kind, acceptance version, budget and predeclared task/
configuration universe. The target Task must match that contract exactly.

The older `learn predict` command calculates one configuration/group and does not
provide this multi-candidate Task exclusion, frozen universe or receipt-input
interface. W6A reuses its estimator, the existing prospective `forecast` and the
W2/W3 scoped resolver. No estimator, canonical record or schema was changed.

## Calculations and human interpretation

Every candidate has six reference estimates, each calculated with Beta(1,1):

| Predictor | Eligible source membership |
| --- | --- |
| `fixed_prior` | Empty; always 0.5, zero labels, conditional 95% interval [0.025, 0.975]. |
| `global` | All admitted configurations/tasks matching the target; intentional cross-arm baseline pooling. |
| `per_arm` | Exact configuration across admitted task groups. |
| `A` | Exact configuration and narrow group. |
| `B` | Declared compatible configuration family and narrow group. |
| `C` | Declared compatible configuration family and broad task family. |

A/B/C use the existing prospective adapter without new learning algorithms.
The existing compatibility validator preserves model, effort and behavioral
identity; it permits only explicitly admitted harness-version transfer. Global
pooling is a descriptive comparator, never a declaration of arm compatibility.
Every predictor has the same dataset/version, acceptance/budget, cutoff and
target-Task exclusions. All existing attempts of the target, including paired
arms, are excluded. Outcomes and post-execution features are never target inputs.
Duplicate immutable observations count once; conflicting experimental-unit
derivations fail closed instead of becoming additional labels.

Output includes target identities, candidate model/effort/version declarations,
policy version/fingerprint, estimator/forecast versions, conditional statistical
intervals, successes/failures, eligible counts, and source observation/stable-key/
Run/Attempt/Outcome/Verification references where present. Resource summaries
describe **eligible evidence for that estimate**, with known/missing counts.
Missing cost/latency means/minima/maxima and unavailable token measurements are
null. Declared model/harness versions do not prove an effective backend revision;
the latter remains null with a basis. No process wall time is canonical latency.

Estimation, descriptive comparison and model preference are separate. This first
interface implements only `abstain-only/v1`, always returning an understandable
reason and null selected configuration. Supplying an unapproved `decision_policy`
returns `unsupported_decision_policy` and leaves valid estimates visible. No
minimum-label rule or ranking policy is silently adopted. W1's five-label proposal
was a planning assumption, not a proven model-selection threshold. Conditional
posterior intervals establish neither superiority, calibration nor causal utility.

## Evidence availability and boundaries

For `real` contracts, provide `bundles` of the existing `EvidenceBundle` type,
one complete scoped snapshot per admitted prior Task. Raw caller-asserted real
observations are rejected. Each bundle is revalidated through `resolve_bundle`
at the cutoff, including existing independent verification, assessment-head,
persisted derivation, explicit Attempt binding and receipt gates. That resolver
uses disposable temporary SQLite for validation; the source ledger/bundle is
unchanged. Byte-identical duplicate bundles are harmless; conflicting snapshots
of one Task are rejected. Retain the exact input to reproduce previously issued
advice. Later corrections do not overwrite earlier input or issued advice.

Null or late receipts exclude evidence even when source timestamps are old.
Declared source timestamps must also pass. The output records the receipt method,
limitations, resolution exclusions and missing/late receipt-entry counts, even
when absent receipts hide a whole Run. Counts of receipt entries are dependency
diagnostics, not counts of independent trials. Imported receipt clocks/hashes are
declarations, not externally authenticated historical time. Unadmitted and target
Task bundles are excluded before resolution and are not exported as source rows.

For `simulated` inputs, provide fictional observations explicitly; the output says
`declared-source-timestamps-only/v1`. Eligibility flags exercise the synthetic
statistical contract, not independent verification of real model performance.
Source kinds/datasets are never pooled, and W1 aggregate reconciliation cannot be
supplied as row-level real evidence. A missing/invalid frozen target or candidate
raises a validation error rather than manufacturing a target probability.

`benchmark` resolution is deliberately unsupported by this advisory. Submitted
benchmark rows yield prior-only estimates and explicit exclusions. Any non-null
benchmark budget retains `budget_measurements_not_supported`. A W4A.2 bundle's
`fully_available` receipt coverage cannot establish verification completeness,
explicit Verification-to-Attempt binding, prospective scope availability or
resource coverage. This restriction also applies to an exporter-eligible,
unbudgeted row: receipt-aware benchmark learning needs separately scoped work.
No benchmark-to-real wrapper or declared-time fallback exists here.

The output omits task prose, arbitrary metadata, raw events/transcripts, source
locators, report contents and unrelated records. Projected identity labels use a
conservative public identifier profile; prose, filesystem paths and recognized
credential-shaped labels are rejected. Identity labels still require human
review before sharing; this is not a general secret sanitizer. The command's
validation error deliberately does not echo input payloads. Exact source hashes
and opaque identifiers support audit, not authentication.

## Executable fictional example

With the existing installed environment, from the repository root:

```sh
.venv/bin/python -B scripts/advisory_example.py
.venv/bin/python -B scripts/advisory_example.py --with-evidence
.venv/bin/python -B scripts/advisory_example.py --with-evidence --input \
  > /tmp/w6a-fictional-input.json
.venv/bin/model-learner learn advise --input-file /tmp/w6a-fictional-input.json
```

The script writes no files itself. Its three configurations are fictional Sol
Low, Sol High and a distinct fictional lower model; these labels assert no actual
provider availability or performance. All evidence has `source_kind=simulated`.
The second invocation declares one prior success for Low and one prior failure
for High, from different fictional Tasks, with the same acceptance and no active
resource budget. It calls the actual estimators; probabilities are not prefilled.

| Example | Low A/B/C (labels) | High A/B/C (labels) | Lower A/B/C (labels) | Global |
| --- | --- | --- | --- | --- |
| Cold start | 0.5 (0) | 0.5 (0) | 0.5 (0) | 0.5 (0) |
| Fictional prior evidence | 2/3 (1 success) | 1/3 (1 failure) | 0.5 (0) | 0.5 (1 success, 1 failure) |

In this example per-arm equals A/B/C, because each family/group has only its own
arm's evidence; the fixed prior remains 0.5. The success interval is approximately
[0.158114, 0.987421], the failure interval [0.012579, 0.841886], and the global
Beta(2,2) interval [0.094299, 0.905701]. All are calculated conditional 95%
posterior intervals. Cost, time, tokens and effective backend revision are
unknown. JSON lists exactly which source identities each estimate admitted.
Both examples abstain: the cold start also lacks evidence, and neither has an
approved model-selection policy. A human sees useful uncertain estimates without
an authoritative preference.

## Acceptance coverage and stopping point

Run `tests/unit/test_advisory.py` and `tests/integration/test_advisory.py` using
the installed pytest environment. Fixtures are fictional and temporary. The
integration suite reuses W2's independent JUnit pass/fail/unknown evidence and the
W4A.2 synthetic benchmark exporter; it does not rerun containment experiments.

| Required cases | Automated evidence |
| --- | --- |
| 1–5 prior/success/failure/unknown/configuration distinction | Cold-start, parametrized binary/unknown cases, distinct-model/effort/runtime test and receipt-gated pass/fail test. |
| 6–10 target exclusion/late receipt/corrections/replay/mismatch | Paired-arm exclusion, future source times, late/null receipts, invalidation history, duplicate observations/bundles, target/dataset/budget/configuration checks. |
| 11–13 benchmark/resources/comparators | Actual fictional budgeted benchmark with complete receipts remains excluded; known/null resource checks; hand-calculated six-policy counts/probabilities. |
| 14–18 determinism/read-only/privacy/abstention/invocation | Reordered deterministic rows; source SQLite/sidecar byte hashes; prose/path/scope projection; unsupported-policy abstention; real/simulated CLI and executable example. |

No arbitrary task-description predictor, general historical-ledger import,
benchmark learning resolver, decision policy, live routing or shadow-decision
persistence is implemented. W6A stops at the offline advisory. W4B/W5, full W6,
and W7 are not completed by this increment. The consolidated next human decisions
are in [the real-execution decision register](REAL_DATA_READINESS.md#w6a-real-execution-decision-register--2026-10-21).
