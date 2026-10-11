"""Offline, source-revalidated benchmark exports; never execute candidates/agents."""

import hashlib
import json
import stat
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, ConfigDict, model_validator

from model_learner.adapters.codex import SOURCE, _metadata
from model_learner.benchmark import BenchmarkResult, load_benchmark
from model_learner.benchmark.isolation import require_supported_real_containment
from model_learner.domain.models import (
    Attempt,
    AttributionStatus,
    DataSourceKind,
    Event,
    Observation,
    Outcome,
    OutcomeStatus,
    Provenance,
    Run,
    RunState,
    Task,
    Verification,
    VerificationStatus,
    utc_now,
)
from model_learner.execution.analyzer import extract_execution_checkpoints
from model_learner.execution.models import ExecutionCheckpoint
from model_learner.learn.estimator import require_aware
from model_learner.observations.resolution import resolve_assessment
from model_learner.storage.database import Database, Repository
from model_learner.verification import file_sha256, validate_evidence
from model_learner.verification.junit import MAX_REPORT_BYTES


class EvidenceProjection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)


class VerificationBinding(EvidenceProjection):
    """Audit-only independent evidence, excluding hidden test names and contents."""

    verification_id: UUID
    artifact_fingerprint: str
    report_sha256: str | None
    verifier_type: str
    verifier_version: str | None
    observed_at: datetime
    result: str


class BenchmarkCheckpoint(EvidenceProjection):
    """Audit projection, never an attested prospective training example."""

    checkpoint: ExecutionCheckpoint
    association_available_at: datetime
    eligible_for_task_state: Literal[False] = False
    reasons: tuple[str, ...]


class BenchmarkEvidence(EvidenceProjection):
    version: Literal["benchmark-evidence/v1"] = "benchmark-evidence/v1"
    benchmark_id: UUID
    fixture_id: str
    fixture_version: str
    fixture_fingerprint: str
    execution_origin: Literal["fixture", "real"]
    exported_at: datetime
    historical_cutoff: datetime | None = None
    observation: Observation
    native_events: tuple[Event, ...]
    verification_bindings: tuple[VerificationBinding, ...]
    checkpoints: tuple[BenchmarkCheckpoint, ...]
    requested_checkpoints: tuple[datetime, ...]
    checkpoint_reasons: tuple[str, ...]
    limitations: tuple[str, ...] = (
        "Export/import timestamps are actual availability, never backdated ingestion.",
        "Run/attempt declarations and verification lack ingestion receipts.",
        "Checkpoints are audit projections; prospective scope receipts are absent.",
        "Fixture families remain dependent; task UUIDs do not model that dependence.",
        "Exact targets are preserved; different fixture targets cannot be pooled.",
    )
    content_sha256: str

    @model_validator(mode="after")
    def validate_digest(self) -> "BenchmarkEvidence":
        require_aware(self.exported_at, "exported_at")
        if self.historical_cutoff is not None:
            require_aware(self.historical_cutoff, "historical_cutoff")
        if self.content_sha256 != _digest(
            self.model_dump(mode="json", exclude={"content_sha256"})
        ):
            raise ValueError("benchmark evidence content digest mismatch")
        return self


def _digest(value: dict) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


def _regular(path: Path, max_bytes: int = 1024 * 1024) -> None:
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode):
        raise ValueError("evidence input must be a regular non-symlink file")
    if info.st_size > max_bytes:
        raise ValueError("evidence input exceeds the size limit")


def _native_projection(event: Event) -> Event:
    native, _ = _metadata(event.payload.get("native", {}))
    redacted = event.payload.get("redacted_fields", [])
    known_omissions = {
        "text",
        "item.text",
        "item.command",
        "item.arguments",
        "item.output",
        "item.stdout",
        "item.stderr",
        "item.content",
        "item.error",
    }
    redaction_count = len(redacted) if isinstance(redacted, list) else None
    payload = {
        "native": native,
        "capture_id": event.payload.get("capture_id"),
        "sequence": event.payload.get("sequence"),
        "timestamp_basis": "capture_receipt",
        "native_observed_at": None,
        "redacted_fields": sorted(
            {
                name
                for name in redacted
                if isinstance(name, str) and name in known_omissions
            }
        )
        if isinstance(redacted, list)
        else [],
        "redacted_field_count": redaction_count,
    }
    return Event.model_validate(
        {**event.model_dump(), "payload": payload, "raw_payload": None}
    )


def export_benchmark_evidence(
    root: Path,
    *,
    checkpoints: tuple[datetime, ...] = (),
    exported_at: datetime | None = None,
    historical_cutoff: datetime | None = None,
) -> BenchmarkEvidence:
    """Derive one visible revision from a finalized, operator-owned source ledger.

    This retains posthoc evidence honestly. A historical cutoff filters labels,
    observed/ingested events and scope links; recorded_at remains actual export
    time. No artifact/report contents, hidden case IDs, agent prose or arbitrary
    metadata are exported. Source files are read only, never executed.
    """
    now = utc_now()
    time = exported_at or now
    require_aware(time, "exported_at")
    if time > now:
        raise ValueError("exported_at cannot be in the future")
    cutoff = historical_cutoff or time
    require_aware(cutoff, "historical_cutoff")
    if cutoff > time:
        raise ValueError("historical cutoff cannot follow export")
    for point in checkpoints:
        require_aware(point, "checkpoint")
        if point > cutoff:
            raise ValueError("checkpoint cannot follow evidence cutoff")
    prepared = load_benchmark(root)
    if prepared.configuration.metadata:
        raise ValueError(
            "benchmark export requires empty arbitrary configuration metadata"
        )
    if prepared.execution_origin == "real":
        require_supported_real_containment()
    result_path = prepared.control / "result.json"
    _regular(result_path)
    if result_path.stat().st_size > 1024 * 1024:
        raise ValueError("result must be a bounded regular file")
    result = BenchmarkResult.model_validate_json(result_path.read_text())
    repository = Repository(Database(prepared.control / "ledger.sqlite3"))
    run = repository.get(Run, result.run.run_id)
    if (
        result.benchmark_id != prepared.benchmark_id
        or result.dataset != prepared.dataset
        or result.execution_origin != prepared.execution_origin
        or result.configuration != prepared.configuration
        or run != result.run
        or run is None
        or run.task_id != prepared.task.task_id
        or repository.get(Task, run.task_id) != prepared.task
        or run.metadata.get("benchmark_id") != str(prepared.benchmark_id)
        or run.metadata.get("execution_origin") != prepared.execution_origin
        or repository.get(Outcome, result.outcome.outcome_id) != result.outcome
    ):
        raise ValueError("benchmark result disagrees with source ledger/manifest")
    if run.started_at is None or run.ended_at is None or run.ended_at > cutoff:
        raise ValueError("export requires a bounded stopped run available at cutoff")
    if prepared.task.created_at > cutoff:
        raise ValueError("task unavailable at cutoff")
    resolution = resolve_assessment(
        repository.list_records(Outcome), run_id=run.run_id, cutoff=cutoff
    )
    outcome = resolution.outcome
    reasons = list(resolution.issues)
    if outcome is None:
        reasons.append("assessment_unavailable_or_conflicted")
    task_links = {
        link.session_id: link
        for link in repository.list_task_session_links(run.task_id)
    }
    run_links = repository.list_run_session_links(run.run_id)
    associations = {
        link.session_id: max(
            link.associated_at, task_links[link.session_id].associated_at
        )
        for link in run_links
        if link.session_id in task_links
    }
    all_events = [
        _native_projection(event)
        for event in repository.list_records(Event)
        if event.session_id in associations
        and event.source == SOURCE
        and event.provenance is Provenance.OBSERVED
        and event.run_id in (None, run.run_id)
        and run.started_at <= event.observed_at <= run.ended_at
        and event.observed_at <= cutoff
        and event.ingested_at <= cutoff
    ]
    events = [event for event in all_events if associations[event.session_id] <= cutoff]
    events.sort(key=lambda event: (event.observed_at, str(event.event_id)))
    attempts = sorted(
        [
            item
            for item in repository.list_records(Attempt)
            if item.run_id == run.run_id
        ],
        key=lambda item: (
            item.started_at is None,
            item.started_at or run.started_at,
            str(item.attempt_id),
        ),
    )
    attribution = AttributionStatus.SINGLE_CONFIGURATION
    if len({item.configuration.configuration_id for item in attempts}) > 1:
        attribution = AttributionStatus.MIXED_CONFIGURATION
    elif (
        len(attempts) != 1
        or attempts[0].configuration != prepared.configuration
        or attempts[0].started_at != run.started_at
        or attempts[0].ended_at != run.ended_at
        or attempts[0].metadata.get("configuration_provenance")
        != "operator_predeclaration"
        or prepared.configuration.model is None
        or not events
    ):
        attribution = AttributionStatus.INCOMPLETE
    conflicts = []
    for event in events:
        for field, declared in (
            ("model", prepared.configuration.model),
            ("model_provider", prepared.configuration.provider),
        ):
            native = event.payload["native"].get(field)
            if native is not None and declared != native:
                conflicts.append(str(event.event_id))
    if conflicts:
        attribution = AttributionStatus.INCOMPLETE
        reasons.append("configuration_conflicts_with_native_telemetry")
    # Finalization diagnostics are label-time information, not checkpoint inputs.
    if result.telemetry_diagnostics:
        attribution = AttributionStatus.INCOMPLETE
        reasons.append("telemetry_incomplete")
    if attribution is not AttributionStatus.SINGLE_CONFIGURATION:
        reasons.append(attribution.value)
    visible_evidence = {
        item.verification_id: item
        for item in repository.list_records(Verification)
        if item.run_id == run.run_id
        and item.task_id == run.task_id
        and item.observed_at <= cutoff
    }
    if outcome is not None:
        for identifier in outcome.evidence_ids:
            evidence = visible_evidence.get(identifier)
            if evidence is None or evidence.observed_at > outcome.recorded_at:
                raise ValueError(
                    "assessment evidence unavailable or assessment predates evidence"
                )
    bindings = []
    # Keep independent evidence even when an interrupted/unknown assessment
    # deliberately does not cite it. Audit evidence never upgrades that label.
    for identifier, evidence in sorted(
        visible_evidence.items(), key=lambda pair: str(pair[0])
    ):
        validate_evidence(repository, run, prepared.task, evidence)
        artifact = prepared.control / "candidate.py"
        _regular(artifact)
        if "sha256:" + file_sha256(artifact) != evidence.artifact_fingerprint:
            raise ValueError("frozen artifact no longer matches independent evidence")
        report_digest = evidence.metadata.get("report_observed_sha256")
        if evidence.verifier_type == "junit-xml":
            report = prepared.control / "report.xml"
            _regular(report, MAX_REPORT_BYTES)
            if file_sha256(report) != report_digest:
                raise ValueError("report no longer matches independent evidence")
        bindings.append(
            VerificationBinding(
                verification_id=identifier,
                artifact_fingerprint=evidence.artifact_fingerprint,
                report_sha256=report_digest,
                verifier_type=evidence.verifier_type,
                verifier_version=evidence.verifier_version,
                observed_at=evidence.observed_at,
                result=evidence.result.value,
            )
        )
    label_bindings = [
        binding
        for binding in bindings
        if outcome is not None and binding.verification_id in outcome.evidence_ids
    ]
    status = outcome.status if outcome is not None else OutcomeStatus.UNKNOWN
    verification_status = (
        outcome.verification_status
        if outcome is not None
        else VerificationStatus.UNVERIFIED
    )
    independently_verified = (
        outcome is not None
        and outcome.assessment_source != "agent_report"
        and verification_status is VerificationStatus.VERIFIED
        and bool(label_bindings)
        and all(binding.result in ("pass", "fail") for binding in label_bindings)
    )
    if independently_verified:
        expected = (
            OutcomeStatus.SUCCESS
            if all(binding.result == "pass" for binding in label_bindings)
            else OutcomeStatus.FAILURE
        )
        if status is not expected:
            raise ValueError("assessment contradicts independent evidence")
    eligible = (
        attribution is AttributionStatus.SINGLE_CONFIGURATION
        and independently_verified
        and status in (OutcomeStatus.SUCCESS, OutcomeStatus.FAILURE)
        and run.state is RunState.FINISHED
    )
    for dimension in ("model", "provider", "harness", "harness_version"):
        value = getattr(prepared.configuration, dimension)
        if value is None or not value.strip():
            eligible = False
            reasons.append(f"configuration_{dimension}_unknown")
    if not independently_verified:
        reasons.append("independent_verified_binary_label_missing")
    if run.state is not RunState.FINISHED:
        reasons.append("execution_incomplete")
    # A declared budget needs independently attributed resource coverage; current
    # benchmark finalization does not provide that contract. Do not invent it.
    if run.resource_budget is not None:
        eligible = False
        reasons.append("budget_measurements_not_supported")
    observation = Observation(
        source_kind=DataSourceKind.BENCHMARK,
        dataset=prepared.dataset,
        source_record_id=str(prepared.benchmark_id),
        task_group=prepared.task.task_group or "__ungrouped__",
        configuration=prepared.configuration,
        task_id=run.task_id,
        run_id=run.run_id,
        attempt_id=attempts[0].attempt_id
        if attribution is AttributionStatus.SINGLE_CONFIGURATION
        else None,
        outcome_id=outcome.outcome_id if outcome is not None else None,
        outcome_status=status,
        verification_status=verification_status,
        evidence_ids=outcome.evidence_ids if outcome is not None else (),
        acceptance_spec=prepared.task.acceptance_spec,
        resource_budget=run.resource_budget,
        attribution_status=attribution,
        eligible_for_configuration_learning=eligible,
        decision_at=run.started_at,
        label_available_at=outcome.recorded_at
        if outcome is not None
        and status not in (OutcomeStatus.UNKNOWN, OutcomeStatus.CENSORED)
        else None,
        recorded_at=time,
        metadata={
            "builder_version": "benchmark-evidence/v1",
            "execution_origin": prepared.execution_origin,
            "fixture_id": prepared.fixture_id,
            "fixture_version": prepared.fixture_version,
            "fixture_fingerprint": prepared.fixture_fingerprint,
            "configuration_provenance": "operator_predeclaration",
            "boundary_source": "external_operator_receipt",
            "event_ids": [str(event.event_id) for event in events],
            "configuration_conflict_event_ids": sorted(set(conflicts)),
            "exclusions": sorted(set(reasons)),
            "assessment_source": outcome.assessment_source
            if outcome is not None
            else None,
        },
    )
    observation = Observation.model_validate(
        {
            **observation.model_dump(),
            "observation_id": uuid5(NAMESPACE_URL, observation.stable_key),
        }
    )
    projections = []
    for session_id, available in sorted(
        associations.items(), key=lambda pair: str(pair[0])
    ):
        for point in extract_execution_checkpoints(
            all_events,
            session_id=session_id,
            checkpoints=checkpoints,
            task=prepared.task,
            run=run,
            association_available_at=available,
            # Hidden acceptance and future labels never enter this projection.
        ):
            gaps = ["prospective_initial_and_scope_receipts_unavailable"]
            if available > point.checkpoint:
                gaps.append("association_unavailable_at_checkpoint")
            if run.ended_at < point.checkpoint:
                gaps.append("run_ended_before_checkpoint")
            if not point.facts.event_count:
                gaps.append("no_events_available_at_checkpoint")
            projections.append(
                BenchmarkCheckpoint(
                    checkpoint=point,
                    association_available_at=available,
                    reasons=tuple(gaps),
                )
            )
    checkpoint_reasons = (
        ("no_linked_session_for_checkpoints",)
        if checkpoints and not associations
        else ()
    )
    values = dict(
        version="benchmark-evidence/v1",
        benchmark_id=prepared.benchmark_id,
        fixture_id=prepared.fixture_id,
        fixture_version=prepared.fixture_version,
        fixture_fingerprint=prepared.fixture_fingerprint,
        execution_origin=prepared.execution_origin,
        exported_at=time,
        historical_cutoff=historical_cutoff,
        observation=observation,
        native_events=tuple(events),
        verification_bindings=tuple(bindings),
        checkpoints=tuple(projections),
        requested_checkpoints=tuple(checkpoints),
        checkpoint_reasons=checkpoint_reasons,
    )
    # Construct defaults before computing canonical content, without validating a
    # placeholder digest as though it were evidence.
    draft = BenchmarkEvidence.model_construct(**values, content_sha256="")
    return BenchmarkEvidence.model_validate(
        {
            **draft.model_dump(mode="json"),
            "content_sha256": _digest(
                draft.model_dump(mode="json", exclude={"content_sha256"})
            ),
        }
    )


def import_benchmark_evidence(
    repository: Repository, evidence: BenchmarkEvidence, *, root: Path
) -> Observation:
    """Revalidate an export against its trusted source before idempotent import.

    Content hashes detect damage, not authenticity. Requiring the trusted source
    root prevents caller-created benchmark labels from bypassing ledger checks.
    Imported observation availability is the actual import time; original capture
    ingestion receipts remain in the audit export and are never rewritten.
    """
    evidence = BenchmarkEvidence.model_validate_json(evidence.model_dump_json())
    times = evidence.requested_checkpoints
    rebuilt = export_benchmark_evidence(
        root,
        checkpoints=times,
        exported_at=evidence.exported_at,
        historical_cutoff=evidence.historical_cutoff,
    )
    if rebuilt != evidence:
        raise ValueError("export disagrees with trusted source evidence")
    row = evidence.observation
    imported = Observation.model_validate(
        {**row.model_dump(), "recorded_at": utc_now()}
    )
    # Reserve the destination write transaction before checking replay so two
    # concurrent imports cannot race a conflicting derivation into this ledger.
    with repository.database.connection() as connection:
        connection.execute("BEGIN IMMEDIATE")
        records = connection.execute(
            "SELECT data FROM observations WHERE source_kind = 'benchmark' "
            "AND dataset_id = ?",
            (row.dataset.dataset_id,),
        ).fetchall()
        for record in records:
            prior = Observation.model_validate_json(record["data"])
            if prior.dataset != row.dataset or prior.run_id != row.run_id:
                continue
            if prior.outcome_id == row.outcome_id:
                if prior.stable_key != row.stable_key:
                    raise ValueError("conflicting benchmark derivation replay")
                if prior.model_dump(exclude={"recorded_at"}) != row.model_dump(
                    exclude={"recorded_at"}
                ):
                    raise ValueError("conflicting benchmark observation replay")
                return prior
        connection.execute(
            "INSERT INTO observations "
            "(observation_id, stable_key, source_kind, dataset_id, dataset_version, "
            "task_group, recorded_at, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(imported.observation_id),
                imported.stable_key,
                "benchmark",
                imported.dataset.dataset_id,
                imported.dataset.dataset_version,
                imported.task_group,
                imported.recorded_at.isoformat(),
                repository._json(imported),
            ),
        )
    return imported
