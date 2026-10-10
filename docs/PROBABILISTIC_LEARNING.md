# First probabilistic learning slice

This implements the M2 simulator and transparent fixed-prior reference learner.
It predicts the probability of one specified binary acceptance target under one
specified resource budget. It does not select configurations or control agents.

## Simulator

`model_learner.simulate.generate(SimulationConfig(...))` returns a Pydantic
`SimulationResult` containing `observations` and a separate `truth` artifact.
The observations use the unchanged M1.1 `Observation` contract, carry the explicit
`simulated` dataset ID/version, and can be persisted with `Repository.add_observation`
or the existing JSONL importer. Truth is never included in observation metadata,
configuration snapshots, JSONL training rows, or estimator arguments.

The three generic configurations are `arm-a`, `arm-b`, `arm-c`; the four explicit
task groups are `group-a` through `group-d`. Their configuration IDs include the
synthetic provider, model version and harness version. All generated rows have
the acceptance specification `simulated-binary-success`, version `1`, and no
resource budget. The observed Bernoulli draw is synthetic verified success/failure;
it is not real verification evidence. Missing labels remain unverified `unknown`.

Configuration supports a seed, count, aware start time, observation spacing,
verification delay, independent missing-label/resource probabilities, assignment
weights for imbalance/sparse groups, a 4 × 3 probability matrix, and an optional
single drift index with a second probability matrix. Cost and latency follow
nonnegative lognormal distributions with per-arm arithmetic means and configurable
log standard deviation. Missing measurements are `null`; an explicitly configured
measured zero remains zero. Costs include unsuccessful and unlabelled executions.

These are independent experimental runs; retries, selection confounding, correlated
outcomes, and resource/outcome dependence are not simulated. Missingness is completely
at random. No calibration claim extends beyond these assumptions. Equal seeds and
configuration produce identical records; extending only `count` preserves the prefix.
A fingerprint of the generation scenario forms stable source-record IDs. Change the
dataset ID/version when changing a scenario; cohort management is explicit.

Truth is serialized separately with `result.truth.model_dump_json()` and read with
`SimulationTruth.model_validate_json(...)`. It records the dataset, scenario
fingerprint, source-record identifiers, latent probabilities and realized binary
draws (including outcomes hidden from training). Keep this evaluator artifact
separate from observation exports. Config/result serialization uses normal Pydantic
`model_dump`/`model_dump_json` methods.

## Estimator

```python
from datetime import timedelta
from model_learner.domain.models import AcceptanceSpec
from model_learner.learn import BetaBernoulli
from model_learner.simulate import SimulationConfig, generate

result = generate(SimulationConfig(seed=1, count=100))
target = AcceptanceSpec(identifier="simulated-binary-success", version="1")
learner = BetaBernoulli.fit(
    result.observations,
    dataset=result.truth.dataset,
    cutoff=result.observations[-1].recorded_at + timedelta(seconds=1),
    acceptance_spec=target,
)
prediction = learner.predict(result.observations[0].configuration, "group-a")
```

Training requires an explicit dataset source kind, ID and version, acceptance ID
and version, resource budget, and aware cutoff. Acceptance descriptions do not
define separate targets; the identifier/version does. Different acceptance
versions, budgets, datasets, and configuration snapshots are filtered separately.
`resource_budget=None` selects the cohort with no declared budget; it does not
silently pool runs with declared budgets. It gives no guarantee for a new budget.
Legacy schema-1 rows cannot train.

Only eligible, single-configuration, verified success/failure labels count, for
all source kinds. A row must have a decision strictly before cutoff and both
its recorded and label-availability times at or before cutoff. Later knowledge
cannot improve an earlier prediction. The estimator does not use outcome-time
metadata or simulator truth as features. It treats eligible rows as independent
trials and does not learn difficulty, causal superiority, drift or budget effects.

Exact stable-key reimports count once; first record time wins. Conflicting
observation IDs or different derivations for the same run (or non-real source
record) raise `ValueError`. Assessment revisions must be resolved explicitly
before fitting; there is no automatic revision-selection policy in this slice.
The default posterior is `Beta(1 + successes, 1 + failures)` for each exact
configuration × task group. Unknown labels do not increase failures. Unseen
cells return the unchanged uniform prior, probability 0.5 and interval [0.025,
0.975]. Reports include posterior mean/variance, counts, equal-tail 95% credible
intervals, and descriptive measured resource means/ranges plus missingness counts.
The interval describes uncertainty about a latent probability, not a 95% chance
that an individual execution succeeds.

Intervals use a standard-library continued-fraction incomplete-beta CDF and
bisection quantiles. This first numerical implementation supports shape parameters
at least 0.5 and a posterior shape sum at most 100,000. Optional fixed priors
are restricted accordingly, avoiding untested extreme shape concentrations and
double-precision endpoint collapse. Optional credible interval mass is supported
only in [0.5, 0.999]; the default is 0.95. Thus the default prior supports at most 99,998
verified trials per fitted cell. Unsupported sizes/priors raise `ValueError`;
nonconvergence raises `ArithmeticError`, never a fabricated interval. This boundary
is checked before prediction and covered by numerical regression tests. Large-scale
numerical work is deferred.

## Evaluation

`model_learner.learn.evaluate(...)` takes the same explicit dataset/acceptance/budget
selector, `train_until`, `evaluation_at`, and optional `SimulationTruth`. It freezes
the chronological training prefix at `train_until`. Held-out decisions start at
that timestamp; no held-out outcome updates the model. Scoring uses only verified,
eligible held-out labels whose records and labels are available by `evaluation_at`.
Reporting future final outcomes does not leak them into the prefix. The API requires
both aware cutoffs; evaluation time cannot precede training time.

All three comparisons use the same Beta(1,1) prior:

- `global`: all selected configurations and groups share a posterior.
- `per_arm`: each exact configuration pools task groups.
- `unpooled`: configuration × group; this is the main learner reference.

No hierarchical learner is implied by these baseline comparisons. Reports contain
Brier score, natural-log loss, equal-width calibration bins with their actual
denominators, training counts, held-out/excluded counts and resource coverage.
Empty score sets yield `null`, never zero error. Separate truth comparisons include
MAE/RMSE against latent simulator probabilities, interval coverage/width and grouped
configuration/group summaries. Coverage is weighted by held-out assignment frequency,
so repeated predictions are not independent coverage experiments. It does not prove
frequentist coverage or real-world calibration, especially after drift.

Truth must match the selected simulated dataset and observation source IDs;
duplicate/unmatched identifiers or a conflicting scored realization fail. Partial
truth is permitted with explicit missing-truth counts. True hidden outcomes do not
enter binary label scoring or training. Changing evaluator probabilities changes
truth metrics only. Resource summaries use available observations, including failed
and unknown executions, and describe measured values rather than imputing missing
costs. Public prediction/evaluation summaries are dataclasses suitable for
`dataclasses.asdict`; selector and time fields in evaluation are JSON-ready.

Next work can broaden simulator stress tests and evaluate multiple seeds, then add
hierarchical pooling only under a separate approved milestone. Real data needs
explicit task/run linking and trustworthy verification before it can train.
