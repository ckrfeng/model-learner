"""Frozen A/B/C evaluation; common chronological task/family-disjoint cohort."""

from __future__ import annotations

import hashlib
import json
import math
import platform
import random
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timedelta
from statistics import fmean

from model_learner.domain.models import (
    AcceptanceSpec,
    AttributionStatus,
    DatasetReference,
    DataSourceKind,
    OutcomeStatus,
    ResourceBudget,
)
from model_learner.execution.analyzer import extract_execution_checkpoints
from model_learner.learn.estimator import label_exclusion, matches_target, require_aware
from model_learner.learn.evaluation import CalibrationBin
from model_learner.learn.task_state import Interval, PairedComparison, VariantResult
from model_learner.representation.inputs import (
    RepresentationExample,
    representation_features,
)
from model_learner.representation.semantic import (
    LocalCPUEncoder,
    SemanticUnavailable,
    peak_rss_bytes,
    runtime_availability,
)


@dataclass(frozen=True)
class RepresentationReport:
    version: str
    dataset: dict
    acceptance_spec: dict
    resource_budget: dict | None
    train_until: str
    evaluation_at: str
    checkpoint_offset_seconds: float
    training_count: int
    scored_count: int
    training_task_count: int
    scored_task_count: int
    training_family_count: int
    scored_family_count: int
    exclusions: dict[str, int]
    cohort_sha256: str
    variants: tuple[VariantResult, ...]
    comparisons: tuple[PairedComparison, ...]
    overhead: dict
    method: dict
    limitations: tuple[str, ...]


def _cohort(
    examples,
    *,
    dataset,
    acceptance_spec,
    resource_budget,
    train_until,
    evaluation_at,
    checkpoint_offset_seconds,
):
    exclusions, visible, seen = Counter(), [], {}
    task_receipts = {}
    for supplied in examples:
        # Revalidation rejects stale model_copy values, mutated descriptions and
        # bypassed identity receipts before any extraction or encoding.
        example = RepresentationExample.model_validate(supplied.model_dump())
        state, description = example.state, example.description
        row, point = state.observation, state.checkpoint
        if row.dataset != dataset or row.source_kind != dataset.source_kind:
            exclusions["other_dataset"] += 1
            continue
        if not matches_target(row, acceptance_spec, resource_budget):
            exclusions["other_target_or_budget"] += 1
            continue
        cutoff = train_until if row.decision_at < train_until else evaluation_at
        if row.decision_at > evaluation_at or point.checkpoint > cutoff:
            exclusions["checkpoint_after_cutoff"] += 1
            continue
        if (
            row.recorded_at > cutoff
            or max(state.initial_available_at, state.inputs_available_at) > cutoff
        ):
            exclusions["example_not_available"] += 1
            continue
        if description.available_at > row.decision_at:
            exclusions["description_unavailable_at_decision"] += 1
            continue
        if point.analyzer_version != "codex-execution-checkpoints/v1":
            raise ValueError("unsupported checkpoint analyzer version")
        unit = str(row.run_id)
        if unit in seen:
            if seen[unit] != example:
                raise ValueError("conflicting checkpoints/descriptions for one run")
            exclusions["duplicate_run"] += 1
            continue
        seen[unit] = example
        receipt = (description.task_family, description.text_sha256, description.source)
        if row.task_id in task_receipts and task_receipts[row.task_id] != receipt:
            raise ValueError("conflicting descriptions for one task")
        task_receipts[row.task_id] = receipt
        if point.checkpoint != row.decision_at + timedelta(
            seconds=checkpoint_offset_seconds
        ):
            exclusions["wrong_checkpoint_horizon"] += 1
        elif state.initial_available_at > row.decision_at:
            exclusions["initial_information_unavailable"] += 1
        elif state.inputs_available_at > point.checkpoint:
            exclusions["checkpoint_inputs_unavailable"] += 1
        elif (
            row.label_available_at is not None
            and row.label_available_at <= point.checkpoint
        ):
            exclusions["label_known_at_checkpoint"] += 1
        elif (
            row.attribution_status is not AttributionStatus.SINGLE_CONFIGURATION
            or row.configuration.model is None
        ):
            exclusions["incomplete_or_mixed_attribution"] += 1
        elif (
            dataset.source_kind is not DataSourceKind.SIMULATED and state.events is None
        ):
            exclusions["checkpoint_event_evidence_required"] += 1
        else:
            if state.events is not None:
                bounded = [
                    e
                    for e in state.events
                    if e.observed_at >= row.decision_at
                    and (e.run_id is None or e.run_id == row.run_id)
                ]
                rebuilt = extract_execution_checkpoints(
                    bounded, session_id=point.session_id, checkpoints=[point.checkpoint]
                )[0]
                if rebuilt.facts != point.facts:
                    raise ValueError(
                        "checkpoint facts disagree with bounded event evidence"
                    )
            visible.append(example)
    initial = [e for e in visible if e.state.observation.decision_at < train_until]
    task_ids = {e.description.task_id for e in initial}
    families = {e.description.task_family for e in initial}
    hashes = {e.description.text_sha256 for e in initial}
    training, scored = [], []
    for example in visible:
        row, description = example.state.observation, example.description
        is_training = row.decision_at < train_until
        if not is_training:
            reason = (
                "task_overlaps_training"
                if description.task_id in task_ids
                else "family_overlaps_training"
                if description.task_family in families
                else "description_overlaps_training"
                if description.text_sha256 in hashes
                else None
            )
            if reason:
                exclusions[reason] += 1
                continue
        reason = label_exclusion(row)
        if reason:
            exclusions[("training_" if is_training else "score_") + reason] += 1
        elif row.label_available_at is None or row.label_available_at > (
            train_until if is_training else evaluation_at
        ):
            exclusions["label_unavailable"] += 1
        elif (
            dataset.source_kind is not DataSourceKind.SIMULATED and not row.evidence_ids
        ):
            exclusions["independent_verified_evidence_required"] += 1
        else:
            (training if is_training else scored).append(example)

    def key(e):
        return (e.state.observation.decision_at, str(e.state.observation.run_id))

    return sorted(training, key=key), sorted(scored, key=key), dict(exclusions)


@dataclass(frozen=True)
class _Fit:
    names: tuple[str, ...]
    means: tuple[float, ...]
    scales: tuple[float, ...]
    weights: tuple[float, ...]

    def vector(self, features):
        return [1.0] + [
            (features.get(n, 0.0) - m) / s
            for n, m, s in zip(self.names, self.means, self.scales, strict=True)
        ]

    def predict(self, features):
        return _sigmoid(
            sum(w * x for w, x in zip(self.weights, self.vector(features), strict=True))
        )


def _sigmoid(value):
    if value >= 0:
        return 1 / (1 + math.exp(-value))
    exp = math.exp(value)
    return exp / (1 + exp)


def _fit(features, labels):
    names = tuple(sorted(set().union(*(x.keys() for x in features))))
    means = tuple(fmean(x.get(n, 0.0) for x in features) for n in names)
    scales = tuple(
        max(1.0, math.sqrt(fmean((x.get(n, 0.0) - m) ** 2 for x in features)))
        for n, m in zip(names, means, strict=True)
    )
    base = _Fit(names, means, scales, ())
    vectors = [base.vector(x) for x in features]
    weights = [0.0] * (len(names) + 1)
    step = 1 / (0.25 * max(sum(x * x for x in v) for v in vectors) + 0.05)
    for _ in range(400):
        gradient = [0.0] * len(weights)
        for vector, label in zip(vectors, labels, strict=True):
            error = (
                _sigmoid(sum(w * x for w, x in zip(weights, vector, strict=True)))
                - label
            )
            for i, x in enumerate(vector):
                gradient[i] += error * x / len(labels)
        for i in range(len(weights)):
            weights[i] -= step * (gradient[i] + (0.05 * weights[i] if i else 0))
    return _Fit(names, means, scales, tuple(weights))


def _interval(values):
    method = "95% percentile held-out family bootstrap, conditional on frozen fit"
    if not values:
        return Interval(None, None, method)
    values.sort()

    def q(p):
        position = (len(values) - 1) * p
        low = int(position)
        return values[low] + (position - low) * (
            values[min(low + 1, len(values) - 1)] - values[low]
        )

    return Interval(q(0.025), q(0.975), method)


def _feature_bytes(features):
    # Shallow object census with per-entry values/keys, not total process RAM.
    return sys.getsizeof(features) + sum(
        sys.getsizeof(x)
        + sum(sys.getsizeof(k) + sys.getsizeof(v) for k, v in x.items())
        for x in features
    )


def evaluate_task_representation(
    examples: list[RepresentationExample] | tuple[RepresentationExample, ...],
    *,
    dataset: DatasetReference,
    acceptance_spec: AcceptanceSpec,
    train_until: datetime,
    evaluation_at: datetime,
    checkpoint_offset_seconds: float = 30,
    resource_budget: ResourceBudget | None = None,
    encoder: LocalCPUEncoder | None = None,
    semantic_unavailable_reason: str | None = None,
    bootstrap_replicates: int = 300,
    seed: int = 1,
) -> RepresentationReport:
    """No adaptive choice, probabilistic learner modification or ledger writes."""
    for n, t in (("train_until", train_until), ("evaluation_at", evaluation_at)):
        require_aware(t, n)
    if evaluation_at <= train_until:
        raise ValueError("evaluation_at must follow train_until")
    if not math.isfinite(checkpoint_offset_seconds) or checkpoint_offset_seconds <= 0:
        raise ValueError("checkpoint offset must be finite and positive")
    if (
        isinstance(bootstrap_replicates, bool)
        or not isinstance(bootstrap_replicates, int)
        or bootstrap_replicates < 100
    ):
        raise ValueError("bootstrap_replicates must be an integer at least 100")
    if isinstance(seed, bool) or not isinstance(seed, int):
        raise ValueError("seed must be an integer")
    if encoder is not None and not isinstance(encoder, LocalCPUEncoder):
        raise ValueError(
            "semantic encoder must be the explicit local pretrained CPU adapter"
        )
    training, scored, exclusions = _cohort(
        examples,
        dataset=dataset,
        acceptance_spec=acceptance_spec,
        resource_budget=resource_budget,
        train_until=train_until,
        evaluation_at=evaluation_at,
        checkpoint_offset_seconds=checkpoint_offset_seconds,
    )
    all_rows = training + scored
    groups = {
        "A_existing": ("initial",),
        "B_execution_state": ("initial", "metrics", "state"),
        "C_cpu_semantic": ("initial", "metrics", "state", "semantic"),
    }
    features, profiles = {}, {}
    rss_before = peak_rss_bytes()
    for name in ("A_existing", "B_execution_state"):
        started = time.perf_counter()
        features[name] = [
            representation_features(e, include_state=name != "A_existing")
            for e in all_rows
        ]
        elapsed = time.perf_counter() - started
        profiles[name] = {
            "feature_extraction_seconds": elapsed,
            "seconds_per_checkpoint": elapsed / len(all_rows) if all_rows else None,
            "feature_python_object_bytes": _feature_bytes(features[name]),
        }
    semantic = runtime_availability()
    semantic.update(
        status="unavailable",
        reason=semantic_unavailable_reason or "no_explicit_local_model",
    )
    if encoder is not None and all_rows:
        started = time.perf_counter()
        try:
            encoder.encode((all_rows[0].description.text,))
            warmup = time.perf_counter() - started
            started = time.perf_counter()
            vectors = encoder.encode(tuple(e.description.text for e in all_rows))
            elapsed = time.perf_counter() - started
            if len(vectors) != len(all_rows) or any(
                len(v) != 384 or not all(math.isfinite(x) for x in v) for v in vectors
            ):
                raise SemanticUnavailable("invalid semantic output shape or values")
            features["C_cpu_semantic"] = [
                dict(base, **{f"semantic:{i}": x for i, x in enumerate(v)})
                for base, v in zip(features["B_execution_state"], vectors, strict=True)
            ]
            semantic.update(
                encoder.metadata,
                status="available",
                reason=None,
                warmup_seconds=warmup,
                inference_seconds=elapsed,
                seconds_per_description=elapsed / len(all_rows),
                actual_model_memory_bytes=encoder.metadata.get("parameter_bytes"),
                actual_load_seconds=encoder.metadata.get("load_seconds"),
                actual_inference_seconds=elapsed,
            )
            profiles["C_cpu_semantic"] = {
                "feature_python_object_bytes": _feature_bytes(
                    features["C_cpu_semantic"]
                )
            }
        except (SemanticUnavailable, ValueError, RuntimeError):
            semantic.update(reason="local_semantic_encoding_failed")
    train_families = {e.description.task_family for e in training}
    score_families = sorted({e.description.task_family for e in scored})
    sufficient = (
        len(training) >= 30
        and len(scored) >= 20
        and len(train_families) >= 5
        and len(score_families) >= 5
        and len({e.state.observation.outcome_status for e in training}) == 2
    )
    labels = [
        int(e.state.observation.outcome_status is OutcomeStatus.SUCCESS)
        for e in all_rows
    ]
    positions = {
        f: [i for i, e in enumerate(scored) if e.description.task_family == f]
        for f in score_families
    }
    rng = random.Random(seed)
    bootstrap = (
        [
            [
                i
                for f in rng.choices(score_families, k=len(score_families))
                for i in positions[f]
            ]
            for _ in range(bootstrap_replicates)
        ]
        if sufficient
        else []
    )
    variants, losses = [], {}
    for name, group in groups.items():
        matrix = features.get(name)
        status = (
            "insufficient_data"
            if not sufficient
            else "evaluated"
            if matrix is not None
            else "semantic_unavailable"
        )
        started = time.perf_counter()
        fit = (
            _fit(matrix[: len(training)], labels[: len(training)])
            if sufficient and matrix is not None
            else None
        )
        fit_seconds = time.perf_counter() - started if fit else None
        started = time.perf_counter()
        predictions = [fit.predict(x) for x in matrix[len(training) :]] if fit else []
        scoring_seconds = time.perf_counter() - started if fit else None
        profiles.setdefault(name, {}).update(
            reference_fit_seconds=fit_seconds,
            reference_scoring_seconds=scoring_seconds,
            reference_seconds_per_checkpoint=scoring_seconds / len(scored)
            if scoring_seconds is not None and scored
            else None,
        )
        loss = [
            (p - y) ** 2
            for p, y in zip(
                predictions,
                labels[len(training) : len(training) + len(predictions)],
                strict=True,
            )
        ]
        losses[name] = loss
        bins = []
        for i in range(5):
            members = [
                (p, y)
                for p, y in zip(
                    predictions,
                    labels[len(training) : len(training) + len(predictions)],
                    strict=True,
                )
                if min(int(p * 5), 4) == i
            ]
            bins.append(
                CalibrationBin(
                    i / 5,
                    (i + 1) / 5,
                    len(members),
                    fmean(p for p, _ in members) if members else None,
                    fmean(y for _, y in members) if members else None,
                )
            )
        variants.append(
            VariantResult(
                name,
                group,
                status,
                len(training),
                len(scored),
                len({e.description.task_id for e in scored}),
                len(fit.names) if fit else 0,
                fmean(loss) if loss else None,
                _interval(
                    [fmean(loss[i] for i in sample) for sample in bootstrap]
                    if loss
                    else []
                ),
                tuple(bins),
                tuple(
                    (str(e.state.observation.run_id), p)
                    for e, p in zip(
                        scored[: len(predictions)], predictions, strict=True
                    )
                ),
            )
        )
    comparisons = []
    for reference, candidate in (
        ("A_existing", "B_execution_state"),
        ("B_execution_state", "C_cpu_semantic"),
    ):
        differences = (
            [a - b for a, b in zip(losses[reference], losses[candidate], strict=True)]
            if losses[reference] and losses[candidate]
            else []
        )
        interval = _interval(
            [fmean(differences[i] for i in sample) for sample in bootstrap]
            if differences
            else []
        )
        interpretation = (
            "insufficient_data"
            if not sufficient
            else "semantic_unavailable"
            if not differences
            else "conditional held-out evidence on this dataset"
            if interval.lower is not None and interval.lower > 0
            else "no resolved held-out improvement"
        )
        comparisons.append(
            PairedComparison(
                reference,
                candidate,
                len(scored),
                len({e.description.task_id for e in scored}),
                fmean(differences) if differences else None,
                interval,
                interpretation,
            )
        )
    binding = {
        "train": [e.model_dump(mode="json") for e in training],
        "score": [e.model_dump(mode="json") for e in scored],
    }
    return RepresentationReport(
        "task-representation-report/v1",
        dataset.model_dump(mode="json"),
        acceptance_spec.model_dump(mode="json", exclude={"description"}),
        resource_budget.model_dump(mode="json") if resource_budget else None,
        train_until.isoformat(),
        evaluation_at.isoformat(),
        checkpoint_offset_seconds,
        len(training),
        len(scored),
        len({e.description.task_id for e in training}),
        len({e.description.task_id for e in scored}),
        len(train_families),
        len(score_families),
        exclusions,
        hashlib.sha256(
            json.dumps(binding, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        tuple(variants),
        tuple(comparisons),
        {
            "feature_profiles": profiles,
            "semantic": semantic,
            "process_peak_rss_bytes_before_features": rss_before,
            "process_peak_rss_bytes_after_features": peak_rss_bytes(),
            "rss_basis": (
                "whole-process lifetime high-water mark; not incremental "
                "per-component RAM"
            ),
        },
        {
            "model": "fixed L2 logistic reference; ridge=0.05; 400 full-batch steps",
            "preprocessing": (
                "training-only vocabulary and mean/std; scale floor 1; log1p counts"
            ),
            "min_training": 30,
            "min_scored": 20,
            "min_families_per_partition": 5,
            "seed": seed,
            "bootstrap_replicates": bootstrap_replicates,
            "split": (
                "chronological; disjoint task/family identities and exact "
                "description hashes"
            ),
            "feature_groups": groups,
            "runtime": {
                "python": platform.python_version(),
                "system": platform.system(),
                "machine": platform.machine(),
            },
            "semantic_training": (
                "frozen pretrained encoder; no fine-tuning; reference predictor "
                "fitted on training partition only"
            ),
        },
        (
            (
                "Public/sanitized source and timestamp receipts are operator "
                "declarations, not automatic privacy/provenance attestations."
            ),
            (
                "Real/benchmark observations require previously independently "
                "resolved labels; this portable input is not ledger attestation."
            ),
            (
                "Final outcomes, tests, terminal state and final resource totals "
                "are excluded from predictors."
            ),
            (
                "Bootstrap conditions on frozen fits and samples held-out "
                "families; it omits training/time dependence uncertainty."
            ),
            (
                "Missing labels/descriptions may select a nonrepresentative "
                "common cohort; no causal or real utility claim."
            ),
            (
                "Model provisioning/runtime are optional; null C scores never "
                "imply zero overhead or a semantic improvement."
            ),
        ),
    )
