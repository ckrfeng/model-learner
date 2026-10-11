"""Deterministic, read-only reconstruction of append-only assessment history.

Timestamp availability follows the existing ledger contracts. No new labels are
inferred and no original record is rewritten by these functions.
"""

import json
from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from uuid import NAMESPACE_URL, UUID, uuid5

from model_learner.domain.models import (
    DatasetReference,
    DataSourceKind,
    Observation,
    Outcome,
    Run,
)
from model_learner.storage.database import Repository, StorageError


@dataclass(frozen=True)
class AssessmentResolution:
    """Visible ledger state for a run; integrity issues prevent selection."""

    run_id: UUID
    cutoff: datetime
    outcome: Outcome | None
    visible_outcome_ids: tuple[UUID, ...]
    issues: tuple[str, ...] = ()


@dataclass(frozen=True)
class ResolutionExclusion:
    run_id: UUID
    reasons: tuple[str, ...]


@dataclass(frozen=True)
class ResolutionSnapshot:
    """At most one independent learner row per run in one explicit dataset."""

    cutoff: datetime
    dataset: DatasetReference
    observations: tuple[Observation, ...]
    assessments: tuple[AssessmentResolution, ...]
    exclusions: tuple[ResolutionExclusion, ...]
    method: str = "declared-timestamp-as-of; persisted-derivation-required-for-learning"
    availability_limitations: tuple[str, ...] = (
        "Run and Attempt lack declaration receipt timestamps",
        "Verification lacks ingestion receipt timestamp",
        "Outcome/Observation recorded_at are trusted declared availability times",
    )


def _aware(cutoff: datetime) -> None:
    if cutoff.tzinfo is None or cutoff.utcoffset() is None:
        raise ValueError("historical cutoff requires a timezone")


def _real_dataset(dataset: DatasetReference) -> None:
    if dataset.source_kind is not DataSourceKind.REAL:
        raise ValueError("assessment resolution requires a real dataset")


def resolve_assessment(
    outcomes: Iterable[Outcome], *, run_id: UUID, cutoff: datetime
) -> AssessmentResolution:
    """Select the head of a single complete, unbranched visible revision chain.

    Multiple independent roots and branches are conflicts even if their labels
    agree. Future records do not participate in validation. A visible revision
    pointing to an unavailable parent is invalid rather than retroactively valid.
    UUID ordering supplies stable diagnostics, never an arbitrary label tie-break.
    """
    _aware(cutoff)
    variants: dict[UUID, dict[str, Outcome]] = defaultdict(dict)
    for item in outcomes:
        if item.recorded_at <= cutoff:
            records = variants[item.outcome_id]
            if not any(previous == item for previous in records.values()):
                canonical = json.dumps(item.model_dump(mode="json"), sort_keys=True)
                records[canonical] = item
    by_id = {
        identifier: records[min(records)] for identifier, records in variants.items()
    }
    conflicting_ids = {
        identifier for identifier, records in variants.items() if len(records) > 1
    }
    visible = {
        identifier: min(
            (item for item in records.values() if item.run_id == run_id),
            key=lambda item: item.model_dump_json(),
        )
        for identifier, records in variants.items()
        if any(item.run_id == run_id for item in records.values())
    }
    issues: set[str] = set()
    if conflicting_ids & set(visible):
        issues.add("conflicting_outcome_identity")
    children: dict[UUID, list[UUID]] = defaultdict(list)
    roots = []
    for item in visible.values():
        parent_id = item.supersedes_outcome_id
        if parent_id is None:
            roots.append(item.outcome_id)
            continue
        parent = by_id.get(parent_id)
        if parent is None:
            issues.add("missing_or_unavailable_parent")
        elif parent.run_id != run_id:
            issues.add("foreign_parent")
        elif parent.recorded_at > item.recorded_at:
            issues.add("revision_predates_parent")
        if parent_id in conflicting_ids:
            issues.add("conflicting_outcome_identity")
        children[parent_id].append(item.outcome_id)
    if any(len(items) > 1 for items in children.values()):
        issues.add("branching_supersession")
    if len(roots) > 1:
        issues.add("multiple_assessment_roots")
    # Follow each ancestry with path-local marks, including self-reference.
    # Iterative traversal also handles long imported histories without recursion.
    checked: set[UUID] = set()
    for identifier in visible:
        path: set[UUID] = set()
        cursor: UUID | None = identifier
        while cursor in visible and cursor not in checked:
            if cursor in path:
                issues.add("cyclic_supersession")
                break
            path.add(cursor)
            cursor = visible[cursor].supersedes_outcome_id
        checked.update(path)
    heads = [item for identifier, item in visible.items() if identifier not in children]
    if visible and not issues and (len(roots) != 1 or len(heads) != 1):
        issues.add("incomplete_revision_chain")
    selected = heads[0] if visible and not issues else None
    return AssessmentResolution(
        run_id=run_id,
        cutoff=cutoff,
        outcome=selected,
        visible_outcome_ids=tuple(sorted(visible, key=str)),
        issues=tuple(sorted(issues)),
    )


def resolve_observation_revisions(
    observations: Iterable[Observation],
    outcomes: Iterable[Outcome],
    *,
    dataset: DatasetReference,
    cutoff: datetime,
) -> ResolutionSnapshot:
    """Resolve visible persisted derivations without fabricating their provenance.

    This function checks revision and observation availability. Evidence and
    attribution integrity remain the responsibility of the ledger/deriver. Use
    ``resolve_real_observations`` to revalidate deterministic evidence and capture.
    A head without a visible derivation is excluded; old labels are not fallback.
    """
    _aware(cutoff)
    _real_dataset(dataset)
    history = tuple(outcomes)
    cohorts: dict[UUID, list[Observation]] = defaultdict(list)
    for row in observations:
        if (
            row.dataset == dataset
            and row.source_kind is DataSourceKind.REAL
            and row.run_id is not None
            and row.recorded_at <= cutoff
            and row.decision_at <= cutoff
            and (row.label_available_at is None or row.label_available_at <= cutoff)
        ):
            cohorts[row.run_id].append(row)
    rows, assessments, exclusions = [], [], []
    for run_id, cohort in sorted(cohorts.items(), key=lambda item: str(item[0])):
        state = resolve_assessment(history, run_id=run_id, cutoff=cutoff)
        assessments.append(state)
        if state.outcome is None:
            exclusions.append(
                ResolutionExclusion(run_id, state.issues or ("no_visible_assessment",))
            )
            continue
        candidates: dict[str | None, Observation] = {}
        for row in sorted(
            cohort, key=lambda row: (row.recorded_at, str(row.observation_id))
        ):
            if row.outcome_id == state.outcome.outcome_id:
                candidates.setdefault(row.stable_key, row)
        if len(candidates) != 1:
            reason = (
                "no_visible_head_derivation"
                if not candidates
                else "conflicting_head_derivations"
            )
            exclusions.append(ResolutionExclusion(run_id, (reason,)))
            continue
        row = next(iter(candidates.values()))
        if (
            row.outcome_status != state.outcome.status
            or row.verification_status != state.outcome.verification_status
            or row.evidence_ids != state.outcome.evidence_ids
        ):
            exclusions.append(
                ResolutionExclusion(run_id, ("derivation_mismatches_head",))
            )
            continue
        rows.append(row)
    return ResolutionSnapshot(
        cutoff, dataset, tuple(rows), tuple(assessments), tuple(exclusions)
    )


def resolve_real_observations(
    repository: Repository,
    *,
    dataset: DatasetReference,
    cutoff: datetime,
    run_ids: Iterable[UUID] | None = None,
    task_group: str | None = None,
) -> ResolutionSnapshot:
    """Rebuild one evidence-checked snapshot row per resolved run, without writes.

    Availability is enforced where contracts have timestamps: assessments,
    verification observation, capture observation/ingestion, task creation and
    explicit task/run session associations. Immutable run/attempt declarations
    and verification records have no receipt timestamps in M1.1; this is an
    as-of reconstruction using their declared times, not proof of receipt then.
    Learning eligibility additionally requires a matching persisted derivation
    with recorded_at <= cutoff; without it, attribution availability is unknown.
    """
    from model_learner.observations import derive_real_observation

    _aware(cutoff)
    _real_dataset(dataset)
    history = repository.list_records(Outcome)
    identifiers = (
        {run.run_id for run in repository.list_records(Run)}
        if run_ids is None
        else set(run_ids)
    )
    persisted: dict[UUID, list[Observation]] = defaultdict(list)
    for row in repository.list_observations(
        DataSourceKind.REAL, dataset_id=dataset.dataset_id
    ):
        if (
            row.dataset == dataset
            and row.recorded_at <= cutoff
            and row.run_id is not None
        ):
            persisted[row.run_id].append(row)
    rows, assessments, exclusions = [], [], []
    for run_id in sorted(identifiers, key=str):
        state = resolve_assessment(history, run_id=run_id, cutoff=cutoff)
        assessments.append(state)
        if state.outcome is None:
            exclusions.append(
                ResolutionExclusion(run_id, state.issues or ("no_visible_assessment",))
            )
            continue
        head_derivations: dict[str | None, Observation] = {}
        for row in sorted(
            persisted[run_id],
            key=lambda row: (row.recorded_at, str(row.observation_id)),
        ):
            if row.outcome_id == state.outcome.outcome_id:
                head_derivations.setdefault(row.stable_key, row)
        if len(head_derivations) > 1:
            exclusions.append(
                ResolutionExclusion(run_id, ("conflicting_head_derivations",))
            )
            continue
        proof = next(iter(head_derivations.values()), None)
        declared_group = task_group or (proof.task_group if proof is not None else None)
        # Untimestamped present-day attempts are not historical evidence. Without
        # an immutable prior proof retain unknown attribution, not current IDs.
        attempt_ids: tuple[UUID, ...] = ()
        if proof is not None:
            raw_ids = proof.metadata.get("attempt_ids")
            if (
                proof.metadata.get("builder_version") != "real-task-workflow/v1"
                or not isinstance(raw_ids, list)
                or any(not isinstance(identifier, str) for identifier in raw_ids)
            ):
                exclusions.append(
                    ResolutionExclusion(
                        run_id, ("historical_attribution_proof_invalid",)
                    )
                )
                continue
            try:
                attempt_ids = tuple(UUID(identifier) for identifier in raw_ids)
            except ValueError:
                exclusions.append(
                    ResolutionExclusion(
                        run_id, ("historical_attribution_proof_invalid",)
                    )
                )
                continue
        try:
            row = derive_real_observation(
                repository,
                run_id=run_id,
                outcome_id=state.outcome.outcome_id,
                dataset=dataset,
                recorded_at=cutoff,
                task_group=declared_group,
                historical_cutoff=cutoff,
                historical_attempt_ids=attempt_ids,
            )
        except (ValueError, StorageError) as error:
            exclusions.append(ResolutionExclusion(run_id, (str(error),)))
            continue
        if proof is None or (
            row.eligible_for_configuration_learning
            and row.stable_key != proof.stable_key
        ):
            values = row.model_dump()
            values["eligible_for_configuration_learning"] = False
            values["stable_key"] = None
            values["metadata"]["exclusions"].append(
                "historical_derivation_availability_unknown"
            )
            row = Observation.model_validate(values)
        # Pure snapshots must have repeatable identity too, rather than uuid4.
        row = row.model_copy(
            update={
                "observation_id": uuid5(
                    NAMESPACE_URL, f"model-learner:{row.stable_key}"
                )
            }
        )
        rows.append(row)
    return ResolutionSnapshot(
        cutoff, dataset, tuple(rows), tuple(assessments), tuple(exclusions)
    )
