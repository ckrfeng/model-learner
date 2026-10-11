# Assessment of overconfidence under drift

The reported zero interval coverage is reproducible. It is a failure of the
constant-probability model after a large distribution change, rather than a
coverage calculation or future-label leakage defect. A recent decision-time
window improves forecasts after drift, but loses useful evidence when conditions
are stationary. The existing full-history estimator remains the default.

## Diagnosis before modification

Read and audited the existing estimator, numerical Beta implementation, frozen
evaluation, stress scenarios, simulator and tests. Re-executed the original frozen
experiment for seeds 0–19, 1,000 decisions, 600 training decisions and 400 held-out
decisions. The three audited scenarios produced these unpooled results:

| Frozen scenario | Brier | Latent-p coverage | Mean interval width |
| --- | ---: | ---: | ---: |
| Heterogeneous stationary (`balanced`) | 0.197198 | 0.968000 | 0.233307 |
| Homogeneous stationary | 0.216226 | 0.945250 | 0.246230 |
| Abrupt 0.9 → 0.2 at frozen split | 0.630445 | 0.000000 | 0.168369 |

All three aggregation levels (global, per-arm and unpooled) had zero coverage in
the original abrupt-drift scenario. Stationary unpooled coverage remains close to
95% in this finite experiment. The heterogeneous global estimator has only
0.233375 coverage despite pooled ECE 0.005608: a pooled average can be calibrated
while badly missing conditional configuration/group probabilities.

The existing metric computes `lower <= true_probability <= upper`, with the
simulator's known probability for each held-out decision. This is the correct
latent-probability check. The Beta interval targets a **fixed Bernoulli parameter**
conditional on the selected cell's constant-p model and its available labels. It
has 95% posterior mass under that model. It is neither a predictive interval for a
future binary result nor an interval with validated nominal coverage for a
changing current-time probability. After drift, the metric tests whether an old
fixed-p posterior still describes the new probability; zero is a useful diagnostic
of model misspecification. No finite continuous equal-tail Beta interval includes
p=0 or p=1; endpoint failures must not be interpreted as numerical bugs.

Coverage weights held-out assignments, with an additional equal-represented-cell
macro diagnostic. Repeated decisions reuse cell predictions, so 400 held-out
assignments are not 400 independent interval-coverage trials. Separate seeded
simulations provide replication. Posterior mass is not a universal fixed-parameter
frequentist coverage guarantee.

Temporal audit: fitting excludes decisions at or after the cutoff, records first
available after it, and verified labels available after it. Frozen held-out binary
scores use labels available by their later evaluation cutoff. Truth resides only
in the evaluator. There is no observed information leakage in this path; frozen
training simply cannot adapt, even after additional labels mature. The simulator
records its final immutable observation when verification arrives and does not
model interim assessment revisions. Real historical assessment resolution is a
separate workstream.

## Recent-window baseline and chronological comparison

`RecentWindowBetaBernoulli.fit(..., window_duration=timedelta(...))` retains the
same Beta(1,1) prior, eligibility, exact configuration/group cells and numerical
intervals. It uses decisions in `[cutoff - duration, cutoff)` and the same record
and label-availability cutoffs as full history. It deduplicates before filtering,
rejects unresolved conflicting experimental units, preserves unknown/censored
outcomes and null resources, and reports discarded observation/eligible-label
counts. An old run verified today cannot become recent evidence merely because
its label arrived recently. A window without available labels returns the prior.
No schema migration, estimator replacement or exponential weighting was needed.

A new pure `run_drift_suite()` evaluates both methods block-prequentially: fit at
each block start using information legally available then, freeze predictions
inside the block, and score outcomes after verification matures. Scoring labels
never feed back into earlier predictions. The same assignments and score cutoffs
apply to all baselines. Windows and cadence are declared before evaluation and are
not selected using the reported test results. Tests changing evaluator-only truth
preserve all predictions, training counts, Brier scores and calibration bins;
changing future outcomes leaves earlier block predictions unchanged.

The main experiment uses 20 independent seeds (0–19), 1,000 decisions spaced 60
seconds apart, evaluation beginning at decision 400, 50-decision refit blocks,
windows of 120 and 300 decision spacings, ten equal-width calibration bins, and
95% equal-tail Beta posterior intervals. Score labels mature at the last label's
record time. Seven scenarios are declared:

- Heterogeneous and homogeneous stationary probabilities, both balanced.
- Abrupt balanced 0.9 → 0.2 drift at decision 400.
- Gradual balanced drift from 0.9 to 0.2 between decisions 400 and 700.
- Abrupt drift with 85% independently missing labels (sparse verified evidence).
- Abrupt drift with arm assignments 98:1:1.
- Abrupt drift with verification delayed 150 decision spacings.

All keep the same arm/configuration identities through drift. Truth diagnostics
include executed decisions whose labels are unknown or pending; binary scores
include only verified, eligible, mature labels. In the main run there are 600
scored labels per seed in every scenario except sparse, where the actual label
counts vary by seed and remain explicit in the saved report. Calibration is ECE
computed from ten equal-width bins per seed, averaged equally across seeds. It is
a sample/bin-dependent descriptive measure and can conceal conditional errors.

## Actual main experiment — 2026-10-10

Each number below is an equal-seed mean. Coverage is empirical coverage of the
**decision-time latent probability**. There is no nominal nonstationary Bayesian
coverage claim. Tail coverage uses the last quarter of the scored decision span
(decisions 850–999). Reported widths remain available in the evidence artifact.

| Scenario | Baseline | Brier | ECE | Coverage | Tail coverage | Mean width |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| stationary | full_history | 0.194192 | 0.035466 | 0.965833 | 0.957333 | 0.225961 |
| stationary | recent_120 | 0.207131 | 0.068866 | 0.959667 | 0.952667 | 0.471425 |
| stationary | recent_300 | 0.198492 | 0.044529 | 0.955667 | 0.950333 | 0.320185 |
| homogeneous | full_history | 0.214616 | 0.045822 | 0.954583 | 0.949000 | 0.238519 |
| homogeneous | recent_120 | 0.227774 | 0.104458 | 0.959083 | 0.964667 | 0.489332 |
| homogeneous | recent_300 | 0.218846 | 0.073798 | 0.949083 | 0.947000 | 0.336314 |
| abrupt | full_history | 0.369329 | 0.440229 | 0.000000 | 0.000000 | 0.235734 |
| abrupt | recent_120 | 0.221218 | 0.165865 | 0.808667 | 0.972333 | 0.451975 |
| abrupt | recent_300 | 0.262737 | 0.234820 | 0.551917 | 0.952000 | 0.312709 |
| gradual | full_history | 0.351974 | 0.379013 | 0.103417 | 0.000000 | 0.210296 |
| gradual | recent_120 | 0.210493 | 0.120210 | 0.876833 | 0.972333 | 0.459487 |
| gradual | recent_300 | 0.244723 | 0.207037 | 0.443583 | 0.889000 | 0.311649 |
| sparse | full_history | 0.352703 | 0.412883 | 0.234833 | 0.336000 | 0.537301 |
| sparse | recent_120 | 0.243423 | 0.241188 | 0.940833 | 0.989000 | 0.795546 |
| sparse | recent_300 | 0.266235 | 0.264692 | 0.756833 | 0.951333 | 0.657316 |
| imbalanced | full_history | 0.371025 | 0.442353 | 0.015750 | 0.016667 | 0.152357 |
| imbalanced | recent_120 | 0.219452 | 0.151061 | 0.767333 | 0.963333 | 0.291524 |
| imbalanced | recent_300 | 0.263327 | 0.224993 | 0.523167 | 0.981667 | 0.201576 |
| delayed | full_history | 0.456481 | 0.528721 | 0.000000 | 0.000000 | 0.240590 |
| delayed | recent_120 | 0.250000 | 0.300500 | 1.000000 | 1.000000 | 0.950000 |
| delayed | recent_300 | 0.327954 | 0.317693 | 0.526083 | 0.962333 | 0.395620 |

Both recent windows improved Brier over full history in all 20 seeds of every
drifting scenario, and worsened it in all 20 seeds of both stationary scenarios.
The 120-step baseline's stationary Brier increase is about 0.013, and its interval
width roughly doubles. Full history is therefore still an appropriate stationary
reference; these experiments do not justify replacing it universally.

Under abrupt drift, full history remains misleadingly narrow and has zero
current-p coverage even as it incorporates new labels. Recent windows discard
stale evidence and recover useful late forecasts, but their whole-span coverage
is 0.808667 and 0.551917, far below a nominal 95% interpretation. Late empirical
coverage near 95% in these seeded simulations does not establish nominal coverage
during drift or real-world calibration.

Two findings limit what good-looking coverage means:

- The delayed scenario's 120-step window is **shorter than the 150-step label
  delay**. Every cell has zero available training labels at every prediction
  cutoff. Its interval is the unchanged [0.025, 0.975] prior, its prediction 0.5,
  its Brier exactly 0.25, and its current-p coverage 1.0. That coverage is vacuous
  evidence of adaptation. The 300-step window retains 151 labels at its final
  cutoff (the availability endpoint is inclusive).
- Sparse recent-120 coverage is 0.940833, but mean width is 0.795546 and final
  per-cell counts range from 0 to 6. It cannot sustain the declared adaptation
  threshold in any seed. Sparse high coverage largely reflects broad uncertainty,
  rather than accurate estimates. Imbalanced assignment also conceals rare-cell
  starvation: final per-cell counts include zero for both recent baselines, and
  assignment-weighted and macro-cell coverage differ materially.

## Adaptation speed and censoring

Recovery is the first block of **three consecutive blocks** with
assignment-weighted latent-p mean absolute error at most 0.1, measured after the
abrupt change or after gradual drift finishes. The following two blocks confirm
recovery retrospectively; this is an evaluator diagnostic, not a deployable
online detector. Resolution is 50 decisions; predictions are stale within a block
and gradual p can change during that block. Recovery depends on the assignments,
sample size, threshold and follow-up duration. It does not guarantee that rare
cells adapted. Means below include only recovered seeds and cannot be compared
without their recovered/censored denominators. Unobserved recovery remains null.

| Scenario | Full-history recovered | Recent-120 recovered / mean delay | Recent-300 recovered / mean delay |
| --- | ---: | ---: | ---: |
| Abrupt | 0/20 | 16/20; 281.25 decisions | 20/20; 300.00 decisions |
| Gradual | 0/20 | 10/20; 95.00 decisions | 6/20; 150.00 decisions |
| Sparse | 0/20 | 0/20; undefined | 3/20; 433.33 decisions |
| Imbalanced | 0/20 | 20/20; 147.50 decisions | 20/20; 295.00 decisions |
| Delayed | 0/20 | 0/20; undefined | 18/20; 355.56 decisions |

Abrupt scenarios have 600 decisions of follow-up; gradual has 300 after its
endpoint. The saved artifact includes follow-up and explicit censoring counts.
Zero recovery in full history within this horizon does not prove it can never
adapt; it still retains the 400 old high-probability trials. A small window can
shed old data quickly while failing the sustained threshold because cell estimates
remain noisy, as seen in the 16/20 versus 20/20 abrupt results.

## Window and sample-size sensitivity

Two additional 20-seed experiments use 240 decisions, preserving a 40% warm-up,
60% evaluation, 30% gradual transition and 15% delay as proportions of decision
count. One keeps fixed windows 120/300 and refit cadence 50, demonstrating that
recent-300 exactly equals full history when its window exceeds the entire data
span. There is no observed sustained recovery in this short experiment; only
three scoring blocks exist and the confirmation requirement limits observable
recovery. This is a finite-follow-up result.

The other uses approximately proportionate windows 29/72 and refits every 12
steps, matching the main experiment's 12%/30% horizons and 5% cadence while reducing
cell sample size. Counts, integer rounding and refit timing remain explicit.
These are controlled simulator comparisons, not a formal sample-complexity study.

| Scenario | 240 full Brier | 240 recent-29 | 240 recent-72 | 1,000 full Brier | 1,000 recent-120 | 1,000 recent-300 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| stationary | 0.206222 | 0.232399 | 0.219501 | 0.194192 | 0.207131 | 0.198492 |
| homogeneous | 0.224834 | 0.247511 | 0.237249 | 0.214616 | 0.227774 | 0.218846 |
| abrupt | 0.356845 | 0.224872 | 0.253312 | 0.369329 | 0.221218 | 0.262737 |
| gradual | 0.338226 | 0.219964 | 0.241122 | 0.351974 | 0.210493 | 0.244723 |
| sparse | 0.315819 | 0.249313 | 0.251395 | 0.352703 | 0.243423 | 0.266235 |
| imbalanced | 0.362333 | 0.213308 | 0.254433 | 0.371025 | 0.219452 | 0.263327 |
| delayed | 0.419695 | 0.250000 | 0.286937 | 0.456481 | 0.250000 | 0.327954 |

In proportionate-window abrupt drift, only 2/20 recent-29 and 7/20 recent-72
seeds meet the sustained adaptation threshold, compared with 16/20 and 20/20 at
1,000 decisions. Broad intervals can cover p despite insufficient labels for
accurate forecasts. In the main run's final stationary block, full-history cell
counts range 62–100, recent-120 counts 4–20, and recent-300 counts 14–41. Sparse
recent-120 retains only 14–28 verified labels in total, versus 123–176 for full
history. These counts explain why reducing the horizon trades stale bias against
variance and missing evidence.

## Reproduction and retained evidence

```python
from dataclasses import asdict
import json
from model_learner.learn.drift import run_drift_suite
from model_learner.learn.stress import reference_scenarios, run_stress_suite

main = run_drift_suite(
    seeds=range(20), count=1000, window_steps=(120, 300), refit_steps=50
)
short_fixed = run_drift_suite(
    seeds=range(20), count=240, window_steps=(120, 300), refit_steps=50
)
short_proportionate = run_drift_suite(
    seeds=range(20), count=240, window_steps=(29, 72), refit_steps=12
)
frozen = run_stress_suite(
    seeds=range(20),
    count=1000,
    scenarios=tuple(
        s
        for s in reference_scenarios()
        if s.name in ("balanced", "homogeneous", "drift")
    ),
)
print(json.dumps(asdict(main), allow_nan=False))
```

Executed with the existing Python 3.12.14 environment, without new dependencies.
The pure APIs do not write observations or inspect real data. CLI `learn drift`
provides the same investigation. Full reports preserve complete simulations,
seeds/fingerprints/datasets/cutoffs, per-block cells/counts/discarded evidence,
calibration bins, per-seed metrics/tail metrics, adaptation follow-up and censoring,
seed distributions and paired Brier differences. Standard deviations/Monte Carlo
standard errors describe variation under these synthetic scenarios, not real
performance confidence bounds. Duplicate seeds and windows are rejected.

[Condensed synthetic evidence](experiments/drift_reference.json) retains all three
experiment parameter sets and fingerprints, the original frozen diagnosis,
aggregate distributions, every seed's metric denominators and values, adaptation
censoring, final per-cell sample counts and discarded counts. Repeated simulation
configuration is factored into each scenario's template plus each run's seed and
dataset ID. Per-seed `metrics` and `tail_metrics` arrays follow the explicitly
stored `metric_columns` field. Full block traces and calibration bins are omitted
from this compact artifact and can be recreated with the APIs/CLI above.

## Limits and decision

Keep full history as the default and expose the recent window explicitly. No
exponential-weighted estimator is added: this straightforward baseline already
shows the tradeoff, and pseudo-count Bayesian coverage would need separate
validation. No inference from this experiment selects a window automatically or
changes a model/configuration. No AI Governor, routing or control is implemented.

Independent Bernoulli trials, independent assignments, MCAR missing labels and
outcome-independent fixed delays are favorable assumptions. These experiments do
not establish performance with correlated retries, biased verification delay,
selection confounding, real coding tasks or drift from changing task composition.
The sparse scenario varies verified-label density; total-decision sensitivity is
studied separately. Rare unobserved cells retain the prior. The new gradual
simulator field is optional and additive; existing seeded outcomes, fingerprints
and observation IDs remain unchanged when it is absent. Dataset identity includes
the simulator configuration; truth never becomes a learner feature.
