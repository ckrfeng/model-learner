# Multi-seed statistical evaluation

This increment evaluates the existing fixed-prior Beta-Bernoulli learner. It adds
no model selection, agent control, adaptive estimator, or complex ML method.
Simulation truth remains evaluator-only and never enters fitting or binary scoring.

## Reproduce the evaluation

```python
from dataclasses import asdict
import json
from model_learner.learn import run_stress_suite

report = run_stress_suite(
    seeds=range(20), count=1000, train_fraction=0.6, calibration_bins=10
)
print(json.dumps(asdict(report), indent=2, allow_nan=False))
```

The API is pure: it neither opens SQLite nor persists observations. Each scenario
and seed receives an explicit separate simulated dataset identity. Reports retain
the seed, complete simulation configuration, scenario fingerprint, exact cutoffs,
per-seed training/held-out/exclusion denominators, baseline metrics, calibration
bins, and all 12 unpooled cell predictions. Missing cells remain visible with their
zero training count, unchanged prior, and broad interval. Unknown truth coverage
for cells with no held-out records is `null`, rather than fabricated success.
Distinct integer seeds and distinct scenario names are required; duplicate seeds
cannot count as additional experiments. Dataclass reports support `asdict` and
standard JSON serialization with `allow_nan=False`.

`reference_scenarios(count=..., train_fraction=...)` builds eight deterministic
scenario specifications. `run_stress_suite(scenarios=..., seeds=...)` also accepts
explicit `StressScenario` objects containing a `SimulationConfig`, `train_count`,
and optional `evaluation_delay_seconds`. Explicit scenarios supersede the default
count and fraction. A null evaluation delay waits until all final records mature;
an explicit delay measures evaluation time from the last execution decision.
Training always freezes at `start_at + train_count * spacing_seconds`.

The default scenarios are:

| Scenario | Data-generating assumption |
| --- | --- |
| balanced | Equal assignments; the original heterogeneous 4 × 3 probabilities. |
| homogeneous | Every cell has success probability 0.7; pooling is appropriate. |
| sparse | At most 48 observations; group weights 17:1:1:1. |
| imbalanced | Model-arm weights 98:1:1; rare configurations receive few labels. |
| drift | Probability drops from 0.9 to 0.2 exactly at the training split, retaining the same configuration identities. |
| missing | Independent 80% completely-at-random missing outcomes. |
| delayed_pending | Labels/records arrive after a delay of one quarter of the total decision span; evaluation is 30 seconds after the last decision. |
| delayed_mature | Same delay; evaluate after all final records mature, keeping the earlier training cutoff frozen. |

All comparisons use the same Beta(1,1) prior and 95% equal-tail interval: global,
per exact configuration (`per_arm`), and configuration × task group (`unpooled`,
the current estimator). They share the same available training prefix and held-out
labels. A paired comparison reports unpooled minus baseline Brier score for each
seed, its descriptive distribution, and counts of wins/ties; negative is better.
It does not demand that any estimator win on every small random sample.

## Denominators and interpretation

Seed metric distributions contain the number of seeds with a defined metric,
arithmetic mean, sample standard deviation, standard error, minimum, and maximum.
The standard error describes Monte Carlo variation across distinct simulated
seeds; it is not a confidence bound on real performance or a calibration test.
One defined seed has no estimable deviation/standard error. Empty scores are null.

Across-seed pooled Brier/log loss and calibration bins weight *available binary
labels*. Their denominators are explicit and can differ by seed after missingness.
Seed means weight each defined seed equally. Equal-width-bin expected calibration
error (ECE) is the count-weighted absolute difference between predicted and observed
success within a bin. Both pooled ECE and per-seed ECE distributions are reported;
pooled ECE can cancel errors across seeds and does not measure individual-cell
calibration. ECE also depends on sample size and binning.

Latent truth coverage/width and probability RMSE use known simulator probabilities,
including simulated unknown outcomes if their observation record is available.
Coverage is checked against the probability, not the future Bernoulli result.
Assignment-weighted coverage gives each visible held-out execution equal weight.
Macro-cell coverage averages configuration × group coverage equally within each
seed, among cells represented in visible held-out records. The report also counts
represented seed/cell pairs. Neither reports full-grid coverage for unobserved
cells. Repeated predictions within a cell and cells within a seed are dependent;
only the seeds provide independent repeated simulations under these assumptions.

The simulator's immutable labelled row is recorded when the verification label
arrives. Before then, it is excluded as `held_out_not_available`, rather than
counted as a failure or scored using future knowledge. This harness evaluates
final-row availability; it does not create interim ledger revisions. Missing
outcomes are unverified unknown rows, excluded from binary fitting/scoring while
remaining available for resource summaries and simulator-truth diagnostics.

## Actual results — 2026-10-10

Executed with Python 3.12.14 using seeds 0–19, count 1,000 (sparse capped at 48),
60% training split, 10 calibration bins, and the scenario defaults above.
The table uses equal-seed mean Brier scores, unpooled assignment-weighted truth
coverage/width, and pooled-label unpooled ECE. All intervals have nominal 95% mass.

| Scenario | Global Brier | Per-arm Brier | Unpooled Brier | Unpooled coverage | Mean width | Pooled ECE | Total scored labels |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| balanced | 0.222457 | 0.210658 | 0.197198 | 0.968000 | 0.233307 | 0.024615 | 8,000 |
| homogeneous | 0.211467 | 0.212014 | 0.216226 | 0.945250 | 0.246230 | 0.051725 | 8,000 |
| sparse | 0.180222 | 0.186033 | 0.181211 | 0.970000 | 0.550253 | 0.089171 | 400 |
| imbalanced | 0.249787 | 0.249737 | 0.212721 | 0.949750 | 0.160130 | 0.015651 | 8,000 |
| drift | 0.648683 | 0.644913 | 0.630445 | 0.000000 | 0.168369 | 0.685845 | 8,000 |
| missing | 0.222951 | 0.217914 | 0.210133 | 0.961000 | 0.476929 | 0.060676 | 1,637 |
| delayed_pending | 0.219073 | 0.208337 | 0.194550 | 0.953667 | 0.300211 | 0.032945 | 3,000 |
| delayed_mature | 0.222518 | 0.211620 | 0.198934 | 0.957750 | 0.301433 | 0.030572 | 8,000 |

Concrete failures and limits surfaced by this run:

- **Drift breaks the stationary estimator.** Despite 600 verified training labels
  per seed, the unpooled intervals cover none of the new 0.2 probabilities. The
  0.168369 mean width accompanies large error, so narrow intervals do not establish
  current accuracy. The estimator has no drift adaptation, and the harness does
  not silently change configuration versions to hide the failure.
- **Unpooled estimation wastes evidence when cells truly match.** In the
  homogeneous case, global Brier is 0.211467 versus unpooled 0.216226. Mean global
  interval width is 0.073168 versus unpooled 0.246230. This is concrete evidence for
  studying partial pooling in a separately approved increment, while balanced
  heterogeneity shows why unconditional global pooling is inappropriate.
- **Marginal calibration can hide severe conditional error.** In balanced data,
  global pooled ECE is only 0.005608, yet global cell-probability coverage is
  0.233375 (macro-cell coverage 0.233333). A good average calibration number does
  not validate predictions for a particular configuration/task group.
- **Sparse/imbalanced averages conceal starvation.** Sparse data has 28 training
  labels per seed and 4–8 prior-only cells. Imbalanced data has 1–6 prior-only
  cells despite 600 total training labels. The full grid preserves their broad
  prior intervals; unpooled assignment-weighted mean width 0.160130 in imbalanced
  data is dominated by the common arm, not evidence about all arms.
- **Missing outcomes reduce evidence, not success probability by definition.**
  The 80%-missing scenario retains only 86–145 training labels per seed and has
  substantially wider unpooled intervals. Neither the hidden successes nor hidden
  failures become learner labels. Outcome-dependent missingness could still bias
  results; this simulator does not test that assumption.
- **Waiting changes evaluation evidence, not past predictions.** Delayed scenarios
  have 351 available training labels per seed. Pending evaluation scores 150
  held-out labels per seed; mature evaluation scores 400. Training predictions
  are identical. These score changes reflect a different scored cohort, not a
  model improved using later labels.

Deterministic tests cover analytic score/calibration aggregation, independent-seed
reproducibility, explicit dataset separation, prior-only cells, missing/empty
metrics, weighted denominators, future-label isolation, delayed maturity, rare-arm
uncertainty, and a known drift counterexample. An additional 12-seed stationary
regression exercises both favorable and unfavorable pooling cases without claiming
that pooled estimates must win on every sample or guarantee exact 95% coverage.

## Remaining limits and next increment

This suite tests independent Bernoulli trials, completely-at-random missingness,
and assignment independent of task difficulty/outcome. Correlated retries,
selection confounding, outcome-dependent missingness/delays, and real model changes
remain outside its claims. Extreme probability endpoints 0/1 are outside any
finite continuous equal-tail Beta interval; this is not evidence of a numerical
failure. Existing numerical shape/sample-size limits still apply.

No simulation result establishes real-world calibration. The current reference
handles stationary sparse uncertainty honestly but fails decisively after abrupt
untracked drift. A useful next statistical increment is a transparent recent-window
baseline with explicit discarded-evidence counts, evaluated on both stationary
and drifting scenarios. Partial pooling should also be evaluated against these
favorable and unfavorable scenarios before replacing the reference; neither
change is implemented here.
