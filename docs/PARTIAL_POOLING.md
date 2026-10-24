# Finite hierarchical partial pooling (M6-A)

Direct library API: `model_learner.learn.partial_pooling.PartialPoolingRequest`
and `partial_pool`. Model version: `finite-hierarchical-beta-binomial/v1`.
This standalone increment does not change the existing BetaBernoulli estimator,
A/B/C forecasts, advisory outputs, CLI, or decision policies.

## Model and sharing

Each domain has independent hyperparameters: mu is uniform on {1/4, 1/2, 3/4}
and kappa independently uniform on {2, 8, 32}. Each of nine states has prior
weight 1/9. Given a domain's state, each exact configuration × narrow task group
has its own rate theta ~ Beta(mu*kappa, (1-mu)*kappa). Binary labels are
conditionally Bernoulli. Cells retain separate success/failure sufficient
statistics; conditional independence does not imply marginal independence.

A domain is an explicitly declared configuration family × broad task family in
one dataset/source/version, acceptance identifier/version and resource budget.
The unchanged CompatibilityPolicy validator permits explicitly compatible
harness-version sharing. Different model, effort, model version, configuration
version or behavioral settings cannot share merely by reusing a family name.
Distinct domains learn independent hyperweights. Empty cells contribute one to
the likelihood, so enumerating them does not change the posterior.

For state h, a=mu*kappa and b=(1-mu)*kappa:

```text
log L_h = sum_cells [log B(a+s,b+f) - log B(a,b)]
w_h proportional to (1/9) L_h
p(theta_q | data) = sum_h w_h Beta(a+s_q,b+f_q)
E(theta_q) = sum_h w_h m_h
Var(theta_q) = sum_h w_h Var_h + sum_h w_h (m_h - E(theta_q))^2
```

Log-Beta terms use lgamma and ordered fsum, followed by stable log-sum-exp
normalization. Omitted binomial constants cancel between states; no general
model-comparison score is exposed. All representable weights participate; no
plug-in hyperparameter, selected state, fitted Beta, or effective observation
count replaces the mixture. Predictive success probability is its mean.

## Explicit evidence boundary

The target Task's evidence is excluded across all arms. Only policy-admitted
source task/configuration snapshots, exact narrow groups, matching target and
budget, eligible verified binary outcomes and available timestamps contribute.
Decision time must be strictly before cutoff; recorded and label times may equal
cutoff. Duplicate experimental units count once; conflicting derivations fail
closed. Request/nested snapshots and input rows are revalidated without mutation.
After configuration-ID admission, each source configuration must equal its frozen
policy snapshot, including schema version and metadata values. Same-ID aliases
are refused rather than normalized.

Real-contract input accepts scoped EvidenceBundle objects only and calls the
existing receipt resolver at cutoff. Missing/late receipts cannot train the
model. Receipt/assessment exclusions and availability limitations are propagated;
imported receipts remain declarations, not authenticated historical attestations.
Simulated rows use declared timestamps only. Benchmark inputs are refused.
No default database, path, clock, execution, or provider connection is selected.

## Invocation and result

With an explicit Task, candidate snapshot tuple, validated CompatibilityPolicy
and timezone-aware cutoff already constructed:

```python
from model_learner.learn.partial_pooling import PartialPoolingRequest, partial_pool

request = PartialPoolingRequest(
    task=target_task,
    candidates=candidate_snapshots,
    policy=compatibility_policy,
    cutoff=cutoff,
    credible_mass=0.95,
)
# simulated_rows must explicitly belong to the policy's simulated dataset.
result = partial_pool(request, observations=simulated_rows)
# For a real dataset instead: partial_pool(request, bundles=scoped_bundles)
serialized = result.model_dump_json()
```

Results are recursively immutable, serializable Pydantic contracts. Identities,
domains, cells and evidence references are sorted. Cells include direct counts,
opaque references and marginal summaries; domains include distinct label and
populated-cell counts, nine weights, mu/kappa marginals, edge mass, underflow
count and effective hyperstate count 1/sum(w²). This last quantity counts supported
states, never observations. Candidate IDs identify predictions at the target's
group; populated source cells are also reported. An empty cell is `prior-only`
when its domain has no labels, or `borrowing` when peers supply labels.

Dataset/acceptance/budget fields use immutable tuples of key/value pairs.
Configuration output projects identity labels, omitting arbitrary metadata and
Task prose. Unsafe categorical labels are refused with fixed diagnostics. UUID references
must be built-in UUID values and are emitted canonically; UUID subclasses are
refused with a fixed diagnostic, including target and all evidence identifiers.
Cost and latency are not inferred. No selected configuration or utility policy
is returned. Callers retain responsibility for reviewing categorical labels.

## Numerical support and limitations

Each domain supports at most 256 populated cells and 10,000 eligible independent
labels. Exceeding either bound refuses the calculation without truncation.
Every Beta component enforces the existing shapes >=0.5 and total <=100,000.
Weights must be finite, nonnegative and sum to one within 1e-12.

Equal-tail intervals invert the actual mixture CDF using the unchanged Beta CDF.
Credible mass defaults to 0.95, supported range [0.5, 0.999]. Bisection allows at
most 64 iterations, requiring bracket width <=1e-12 and absolute CDF residual
<=1e-9 at each reported endpoint. Results expose width, residual and iterations.
CDF nonconvergence, nonfinite values and exhausted tolerances propagate errors;
there is no normal approximation or changed-model retry. Variance uses squared
mean deviations; only a negative total within 1e-14 could be clamped to zero.
Hyperparameter inference is an exact finite sum and needs no MCMC, optimizer or
continuous-grid convergence claim. CDF evaluation/inversion has separate limits.
Intervals describe latent theta, not a continuous interval for a binary outcome.

This coarse proper prior restricts population mean/concentration support. High
edge mass warns about prior-support sensitivity, even when numerics succeed.
Edge mass is already substantial under the prior. Exposing it is not a trigger
to extend support or proof of a well-calibrated continuous model.

## Synthetic acceptance examples

Cold: mean 1/2, variance 133/1782, nine equal weights; this is not Beta(1,1).
One direct success: mean 1157/1782, variance 83125/1587762. One failure reflects
the mean with equal variance. An empty compatible peer cell after one success
has mean 7/12 and zero direct observations; a different domain remains at 1/2.
Two separate one-label success/failure cells leave kappa's marginal uniform;
putting both labels in one cell updates kappa by kappa/(kappa+1).

Fixed sparse examples show peer successes raising and peer failures lowering a
sparse cell's mean. Two abundant opposing cells retain rates above 0.9 and below
0.1, while the unchanged global/per-arm references equal 0.5. Tests compare
rational moments, known Beta quantiles and independent transformed-density
Simpson integration at 4096/8192 panels, as well as fictional receipt contracts.
These are numerical/engineering acceptance checks, not measured model utility,
superiority or calibration. Multi-seed/selection-confounding/held-out evaluation
remains M6-B; utility policies and recorded shadow choice remain M7. Separate
W4A600s/W4B/custom-transport gates remain open.
