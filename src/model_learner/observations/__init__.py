"""Evidence-linked real observations, with explicit quality and missingness."""

from collections import Counter
from collections.abc import Iterable
from datetime import datetime
from uuid import UUID

from model_learner.adapters.codex import SOURCE
from model_learner.domain.models import (
    Attempt,
    AttributionStatus,
    DatasetReference,
    DataSourceKind,
    Event,
    ExecutionConfiguration,
    Observation,
    Outcome,
    OutcomeStatus,
    Provenance,
    Run,
    Session,
    Task,
    Verification,
    VerificationStatus,
    utc_now,
)
from model_learner.storage.database import Repository, StorageError
from model_learner.verification import validate_evidence


def _attribution(run: Run, attempts: list[Attempt]) -> AttributionStatus:
    if len({item.configuration.configuration_id for item in attempts}) > 1:
        return AttributionStatus.MIXED_CONFIGURATION
    if not attempts or run.started_at is None or run.ended_at is None:
        return AttributionStatus.INCOMPLETE
    boundary = run.started_at
    for item in attempts:
        if (
            item.started_at != boundary
            or item.ended_at is None
            or item.ended_at < boundary
            or item.configuration.model is None
            or item.metadata.get("configuration_provenance") != "human_declaration"
        ):
            return AttributionStatus.INCOMPLETE
        boundary = item.ended_at
    if boundary != run.ended_at:
        return AttributionStatus.INCOMPLETE
    return AttributionStatus.SINGLE_CONFIGURATION


def derive_real_observation(
    repository: Repository,
    *,
    run_id: UUID,
    outcome_id: UUID,
    dataset: DatasetReference,
    recorded_at: datetime | None = None,
    task_group: str | None = None,
    historical_cutoff: datetime | None = None,
    historical_attempt_ids: Iterable[UUID] | None = None,
) -> Observation:
    """Derive one assessment without changing the append-only ledger.

    Only full manually declared segment coverage with one exact configuration,
    independently hashed final evidence, and a verified binary outcome is
    eligible. Captured native completion and tool failures never supply labels.
    """
    if historical_attempt_ids is not None and historical_cutoff is None:
        raise ValueError("historical attempt selection requires a historical cutoff")
    if dataset.source_kind is not DataSourceKind.REAL:
        raise ValueError("real observation builder requires a real dataset")
    run = repository.get(Run, run_id)
    outcome = repository.get(Outcome, outcome_id)
    if run is None or outcome is None:
        raise StorageError("unknown run or outcome")
    if outcome.run_id != run_id:
        raise ValueError("outcome belongs to a different run")
    task = repository.get(Task, run.task_id)
    if task is None:  # pragma: no cover - repository foreign-key guarantee
        raise StorageError("unknown task")
    if run.started_at is None or run.ended_at is None:
        raise ValueError("real observation requires a bounded run")
    time = recorded_at or utc_now()
    if time.tzinfo is None or time.utcoffset() is None:
        raise ValueError("observation timestamp requires a timezone")
    if time < outcome.recorded_at:
        raise ValueError("observation timestamp must follow its assessment")
    if outcome.recorded_at < run.ended_at:
        raise ValueError("assessment must follow the declared run end")
    if historical_cutoff is not None:
        if historical_cutoff.tzinfo is None or historical_cutoff.utcoffset() is None:
            raise ValueError("historical cutoff requires a timezone")
        if time != historical_cutoff:
            raise ValueError("historical derivation timestamp must equal its cutoff")
        if task.created_at > historical_cutoff or run.ended_at > historical_cutoff:
            raise ValueError("task or completed run unavailable at cutoff")
        task_links = {
            link.session_id
            for link in repository.list_task_session_links(task.task_id)
            if link.task_id == task.task_id and link.associated_at <= historical_cutoff
        }
        session_ids_at_cutoff = {
            link.session_id
            for link in repository.list_run_session_links(run_id)
            if link.associated_at <= historical_cutoff and link.session_id in task_links
        }
        sessions = [
            session
            for session in repository.list_records(Session)
            if session.session_id in session_ids_at_cutoff
        ]
    else:
        sessions = repository.list_sessions_for_run(run_id)
    if not sessions or any(session.source != SOURCE for session in sessions):
        raise ValueError("real builder requires explicitly linked Codex CLI sessions")
    session_ids = {session.session_id for session in sessions}
    events = [
        event
        for event in repository.list_records(Event)
        if event.session_id in session_ids
        and event.source == SOURCE
        and event.provenance is Provenance.OBSERVED
        and run.started_at <= event.observed_at <= run.ended_at
        and (historical_cutoff is None or event.ingested_at <= historical_cutoff)
    ]
    if not events:
        raise ValueError("no captured events inside the declared run boundaries")
    if any(event.ingested_at > time for event in events):
        raise ValueError("observation timestamp must follow capture ingestion")
    if historical_attempt_ids is None:
        selected_attempts = [
            item for item in repository.list_records(Attempt) if item.run_id == run_id
        ]
    else:
        identifiers = tuple(historical_attempt_ids)
        if len(set(identifiers)) != len(identifiers):
            raise ValueError("historical attempt proof contains duplicate identities")
        selected_attempts = []
        for identifier in identifiers:
            item = repository.get(Attempt, identifier)
            if item is None or item.run_id != run_id:
                raise ValueError(
                    "historical attempt proof references missing or foreign attempt"
                )
            selected_attempts.append(item)
    attempts = sorted(
        selected_attempts,
        key=lambda item: (
            item.started_at is None,
            item.started_at or run.started_at,
            str(item.attempt_id),
        ),
    )
    attribution = _attribution(run, attempts)
    telemetry_conflicts = []
    for event in events:
        native = event.payload.get("native", {})
        if not isinstance(native, dict):
            continue
        # A receipt time is not an exact native configuration boundary. Check
        # emitted dimensions against any declared segment covering that receipt,
        # retaining uncertainty instead of choosing which source to believe.
        covering = [
            item
            for item in attempts
            if item.started_at is not None
            and item.ended_at is not None
            and item.started_at <= event.observed_at <= item.ended_at
        ]
        for emitted, dimension in (("model", "model"), ("model_provider", "provider")):
            value = native.get(emitted)
            if isinstance(value, str) and value and covering:
                if all(
                    getattr(item.configuration, dimension) != value for item in covering
                ):
                    telemetry_conflicts.append(str(event.event_id))
    if telemetry_conflicts and attribution is not AttributionStatus.MIXED_CONFIGURATION:
        attribution = AttributionStatus.INCOMPLETE
    configuration = (
        attempts[0].configuration
        if attribution is AttributionStatus.SINGLE_CONFIGURATION
        else ExecutionConfiguration()
    )
    evidence = []
    if historical_cutoff is not None:
        # Even a partial/unverified claim cannot expose future evidence IDs as a
        # learner derivation. Do not fall back to an earlier binary assessment.
        for identifier in outcome.evidence_ids:
            item = repository.get(Verification, identifier)
            if item is None or item.observed_at > historical_cutoff:
                raise ValueError("assessment evidence unavailable at cutoff")
            if item.observed_at > outcome.recorded_at:
                raise ValueError("assessment predates its verification evidence")
    if outcome.verification_status is VerificationStatus.VERIFIED:
        if not outcome.evidence_ids:
            raise ValueError("verified assessment requires evidence")
        for identifier in outcome.evidence_ids:
            item = repository.get(Verification, identifier)
            if item is None:
                raise StorageError("unknown verification evidence")
            validate_evidence(repository, run, task, item)
            if item.result.value not in ("pass", "fail"):
                raise ValueError(
                    "verified assessment cannot use indeterminate evidence"
                )
            if item.observed_at > outcome.recorded_at:
                raise ValueError("assessment predates its verification evidence")
            evidence.append(item)
        expected_status = (
            OutcomeStatus.SUCCESS
            if all(item.result.value == "pass" for item in evidence)
            else OutcomeStatus.FAILURE
        )
        if outcome.status is not expected_status:
            raise ValueError("assessment status contradicts verification evidence")
    eligible = (
        attribution is AttributionStatus.SINGLE_CONFIGURATION
        and outcome.verification_status is VerificationStatus.VERIFIED
        and outcome.status in (OutcomeStatus.SUCCESS, OutcomeStatus.FAILURE)
    )
    exclusions = []
    if attribution is not AttributionStatus.SINGLE_CONFIGURATION:
        exclusions.append(attribution.value)
    if outcome.verification_status is not VerificationStatus.VERIFIED:
        exclusions.append("unverified_outcome")
    if outcome.status not in (OutcomeStatus.SUCCESS, OutcomeStatus.FAILURE):
        exclusions.append("no_binary_label")
    if telemetry_conflicts:
        exclusions.append("declared_configuration_conflicts_with_native_telemetry")
    # Costs are unknown unless every included segment provides that measurement.
    cost = (
        sum(item.cost_usd for item in attempts)
        if attempts and all(item.cost_usd is not None for item in attempts)
        else None
    )
    latency = (
        sum(item.latency_seconds for item in attempts)
        if attempts and all(item.latency_seconds is not None for item in attempts)
        else None
    )
    if attribution is not AttributionStatus.SINGLE_CONFIGURATION:
        # Partial segment resources are not complete run resources.
        cost = None
        latency = None
    budget = run.resource_budget
    if budget is not None:
        tokens = (
            sum(item.input_tokens + item.output_tokens for item in attempts)
            if attribution is AttributionStatus.SINGLE_CONFIGURATION
            and attempts
            and all(
                item.input_tokens is not None and item.output_tokens is not None
                for item in attempts
            )
            else None
        )
        for dimension, maximum, actual in (
            ("cost", budget.max_cost_usd, cost),
            ("tokens", budget.max_tokens, tokens),
            ("duration", budget.max_duration_seconds, latency),
        ):
            if maximum is not None and (actual is None or actual > maximum):
                exclusions.append(
                    f"budget_{dimension}_{'unknown' if actual is None else 'exceeded'}"
                )
                eligible = False
    label_at = (
        None
        if outcome.status in (OutcomeStatus.UNKNOWN, OutcomeStatus.CENSORED)
        else outcome.recorded_at
    )
    observation = Observation(
        source_kind=DataSourceKind.REAL,
        dataset=dataset,
        task_group=task_group or task.task_group or "__ungrouped__",
        configuration=configuration,
        task_id=task.task_id,
        run_id=run_id,
        attempt_id=(
            attempts[0].attempt_id
            if attribution is AttributionStatus.SINGLE_CONFIGURATION
            else None
        ),
        outcome_id=outcome_id,
        outcome_status=outcome.status,
        verification_status=outcome.verification_status,
        evidence_ids=outcome.evidence_ids,
        acceptance_spec=task.acceptance_spec,
        resource_budget=run.resource_budget,
        attribution_status=attribution,
        eligible_for_configuration_learning=eligible,
        decision_at=run.started_at,
        label_available_at=label_at,
        recorded_at=time,
        cost_usd=cost,
        latency_seconds=latency,
        metadata={
            "builder_version": "real-task-workflow/v1",
            "session_ids": sorted(str(identifier) for identifier in session_ids),
            "event_ids": sorted(str(event.event_id) for event in events),
            "attempt_ids": [str(item.attempt_id) for item in attempts],
            "measurement_sources": [item.measurement_source for item in attempts],
            "configuration_provenance": (
                "human_declaration"
                if attribution is AttributionStatus.SINGLE_CONFIGURATION
                else "incomplete_or_mixed"
            ),
            "boundaries_source": "human_declaration",
            "event_time_basis": "observer_receipt",
            "exclusions": exclusions,
            "configuration_conflict_event_ids": sorted(set(telemetry_conflicts)),
            "assessment_source": outcome.assessment_source,
            "supersedes_outcome_id": (
                str(outcome.supersedes_outcome_id)
                if outcome.supersedes_outcome_id is not None
                else None
            ),
            "cost_coverage": sum(item.cost_usd is not None for item in attempts),
            "latency_coverage": sum(
                item.latency_seconds is not None for item in attempts
            ),
        },
    )
    return observation


def build_real_observation(
    repository: Repository,
    *,
    run_id: UUID,
    outcome_id: UUID,
    dataset: DatasetReference,
    recorded_at: datetime | None = None,
    task_group: str | None = None,
) -> Observation:
    """Persist an exact assessment derivation idempotently, retaining history."""
    return repository.add_observation(
        derive_real_observation(
            repository,
            run_id=run_id,
            outcome_id=outcome_id,
            dataset=dataset,
            recorded_at=recorded_at,
            task_group=task_group,
        )
    )


def data_quality_report(observations: Iterable[Observation]) -> dict[str, object]:
    """Describe retained derivations, not independent trials or causal rates."""
    rows = list(observations)
    counts = Counter()
    for row in rows:
        counts[f"outcome:{row.outcome_status}"] += 1
        counts[f"verification:{row.verification_status}"] += 1
        counts[f"attribution:{row.attribution_status}"] += 1
        counts["eligible"] += row.eligible_for_configuration_learning
        counts["unknown_cost"] += row.cost_usd is None
        counts["unknown_latency"] += row.latency_seconds is None
        counts["human_assessed"] += (
            row.metadata.get("assessment_source") == "human_assessment"
        )
    return {
        "observation_count": len(rows),
        "unit": "assessment_derivation",
        "datasets": sorted(
            {
                (
                    row.source_kind.value,
                    row.dataset.dataset_id,
                    row.dataset.dataset_version,
                )
                for row in rows
                if row.dataset is not None
            }
        ),
        "counts": dict(sorted(counts.items())),
    }
