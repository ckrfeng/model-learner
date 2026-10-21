"""Local availability of source-revalidated benchmark exports, never eligibility.

Only reviewed operator-owned sources are supported. Digests detect corruption and
identity rebinding, not authenticity. Persist the book after capture; serialized
receipts are local declarations, not externally authenticated historical time.
"""

import re
from datetime import datetime
from pathlib import Path
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, model_validator

from model_learner.benchmark import load_benchmark
from model_learner.benchmark.evidence import (
    BenchmarkEvidence,
    _digest,
    export_benchmark_evidence,
)
from model_learner.domain.models import (
    Attempt,
    DataSourceKind,
    Event,
    Outcome,
    ResourceBudget,
    Run,
    Session,
    Task,
    Verification,
    utc_now,
)
from model_learner.learn.estimator import require_aware
from model_learner.storage.database import Database, Repository
from model_learner.storage.evidence import key

Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


def _reviewed_identifier(value: str) -> str:
    # Conservative metadata profile, supplemented by human review/privacy guard.
    if re.search(r"(?:sk-|gh[pousr]_)[A-Za-z0-9_-]{16,}", value):
        raise ValueError("credential-shaped benchmark identifier")
    return value


Opaque = Annotated[
    str,
    Field(pattern=r"^[A-Za-z0-9_.:-]{1,160}$"),
    AfterValidator(_reviewed_identifier),
]
Kind = Literal[
    "Task",
    "Run",
    "Attempt",
    "Session",
    "TaskSessionLink",
    "RunSessionLink",
    "Event",
    "Verification",
    "Outcome",
    "Observation",
    "Configuration",
    "Acceptance",
]


class ReceiptModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, allow_inf_nan=False)


class Target(ReceiptModel):
    source_kind: Literal["benchmark"] = "benchmark"
    benchmark_id: UUID
    dataset_id: Opaque
    dataset_version: Opaque
    task_id: UUID
    run_id: UUID
    configuration_id: Digest
    acceptance_id: Opaque
    acceptance_version: Opaque
    acceptance_sha256: Digest
    resource_budget: ResourceBudget | None
    execution_origin: Literal["fixture", "real"]
    fixture_id: Opaque
    fixture_version: Opaque
    fixture_fingerprint: Digest


class SourceTime(ReceiptModel):
    field: Literal[
        "created_at",
        "started_at",
        "ended_at",
        "associated_at",
        "observed_at",
        "ingested_at",
        "recorded_at",
        "decision_at",
        "label_available_at",
    ]
    value: datetime

    @model_validator(mode="after")
    def aware(self):
        require_aware(self.value, "source time")
        return self


class RecordBinding(ReceiptModel):
    kind: Kind
    identity: Opaque
    sha256: Digest
    task_id: UUID | None = None
    run_id: UUID | None = None
    configuration_id: Digest | None = None
    acceptance_sha256: Digest | None = None
    source_times: tuple[SourceTime, ...] = ()

    @property
    def key(self) -> str:
        return f"{self.kind}:{self.identity}"


class VerificationReference(ReceiptModel):
    verification_id: UUID
    artifact_fingerprint: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    report_sha256: Digest | None
    verifier_type: Opaque
    verifier_version: Opaque | None


class BenchmarkReceiptBundle(ReceiptModel):
    version: Literal["benchmark-receipt-bundle/v1"] = "benchmark-receipt-bundle/v1"
    target: Target
    export_sha256: Digest
    exported_at: datetime
    observation_id: UUID
    attempt_id: UUID | None
    outcome_id: UUID | None
    supersedes_outcome_id: UUID | None
    # Copied audit fields only. This module never emits canonical observations.
    exporter_eligible: bool
    learning_exclusions: tuple[Opaque, ...]
    verification_references: tuple[VerificationReference, ...]
    records: tuple[RecordBinding, ...]
    unavailable_fields: tuple[Opaque, ...]
    content_sha256: Digest

    @model_validator(mode="after")
    def validate_bundle(self):
        require_aware(self.exported_at, "exported_at")
        if self.content_sha256 != _digest(
            self.model_dump(mode="json", exclude={"content_sha256"})
        ):
            raise ValueError("benchmark receipt bundle digest mismatch")
        records = {r.key: r for r in self.records}
        if len(records) != len(self.records):
            raise ValueError("duplicate benchmark record identity")
        target = self.target
        for record in self.records:
            if (
                record.task_id not in (None, target.task_id)
                or record.run_id not in (None, target.run_id)
                or record.configuration_id not in (None, target.configuration_id)
                or record.acceptance_sha256 not in (None, target.acceptance_sha256)
            ):
                raise ValueError("incompatible benchmark record association")
            # A missing required association cannot masquerade as full receipt
            # coverage. Optional canonical associations (e.g. Event.run_id) stay
            # optional; the source exporter checks their explicit session links.
            required_fields = {
                "Task": ("task_id", "acceptance_sha256"),
                "Run": ("task_id", "run_id"),
                "Attempt": ("run_id", "configuration_id"),
                "TaskSessionLink": ("task_id",),
                "RunSessionLink": ("run_id",),
                "Verification": ("task_id", "run_id", "acceptance_sha256"),
                "Outcome": ("run_id",),
                "Observation": (
                    "task_id",
                    "run_id",
                    "configuration_id",
                    "acceptance_sha256",
                ),
            }.get(record.kind, ())
            if any(getattr(record, field) is None for field in required_fields):
                raise ValueError("missing required benchmark record association")
        required = {
            f"Task:{target.task_id}",
            f"Run:{target.run_id}",
            f"Configuration:{target.configuration_id}",
            f"Acceptance:{target.acceptance_sha256}",
            f"Observation:{self.observation_id}",
        }
        if self.attempt_id is not None:
            required.add(f"Attempt:{self.attempt_id}")
        if self.outcome_id is not None:
            required.add(f"Outcome:{self.outcome_id}")
        if self.supersedes_outcome_id is not None:
            required.add(f"Outcome:{self.supersedes_outcome_id}")
        required.update(
            f"Verification:{r.verification_id}" for r in self.verification_references
        )
        if not required <= records.keys():
            raise ValueError("missing required benchmark record binding")
        if target.resource_budget is not None and (
            self.exporter_eligible
            or "budget_measurements_not_supported" not in self.learning_exclusions
        ):
            raise ValueError("benchmark budget eligibility boundary violated")
        return self


class FirstReceipt(ReceiptModel):
    sha256: Digest
    received_at: datetime | None = None

    @model_validator(mode="after")
    def aware(self):
        if self.received_at is not None:
            require_aware(self.received_at, "received_at")
        return self


class Availability(ReceiptModel):
    target: Target
    cutoff: datetime
    export_sha256: Digest
    available_records: tuple[tuple[str, str], ...]
    exclusions: tuple[tuple[str, str], ...]
    fully_available: bool
    unavailable_fields: tuple[Opaque, ...]
    exporter_eligible: bool
    learning_exclusions: tuple[Opaque, ...]


class BenchmarkReceiptBook(ReceiptModel):
    version: Literal["benchmark-first-receipts/v1"] = "benchmark-first-receipts/v1"
    target: Target
    receipts: dict[str, FirstReceipt] = Field(default_factory=dict)

    def capture(self, bundle: BenchmarkReceiptBundle) -> "BenchmarkReceiptBook":
        """Return a new book atomically; time comes only from this receiver's clock.

        Capture the exact retained export on replay, not a newly timestamped export
        with the same Observation ID. Changed immutable records must be rejected.
        """
        bundle, book = self._validated(bundle)
        now = utc_now()
        require_aware(now, "receiver clock")
        receipts = dict(book.receipts)
        for identity, digest in _members(bundle):
            previous = receipts.get(identity)
            if previous is not None and previous.sha256 != digest:
                raise ValueError("benchmark receipt identity rebound")
            if previous is None or previous.received_at is None:
                receipts[identity] = FirstReceipt(sha256=digest, received_at=now)
        return BenchmarkReceiptBook(target=book.target, receipts=receipts)

    def _validated(self, bundle):
        book = BenchmarkReceiptBook.model_validate_json(self.model_dump_json())
        bundle = BenchmarkReceiptBundle.model_validate_json(bundle.model_dump_json())
        if book.target != bundle.target:
            raise ValueError("benchmark receipt target mismatch")
        return bundle, book

    def as_of(
        self, bundle: BenchmarkReceiptBundle, *, cutoff: datetime
    ) -> Availability:
        """Audit one frozen export; not head selection, verification or learning."""
        require_aware(cutoff, "cutoff")
        bundle, book = self._validated(bundle)
        available, exclusions = [], []
        times = {r.key: r.source_times for r in bundle.records}
        for identity, digest in _members(bundle):
            receipt = book.receipts.get(identity)
            if receipt is not None and receipt.sha256 != digest:
                raise ValueError("benchmark receipt digest mismatch")
            if receipt is None or receipt.received_at is None:
                exclusions.append((identity, "missing_receipt"))
            elif receipt.received_at > cutoff:
                exclusions.append((identity, "received_after_cutoff"))
            elif any(t.value > cutoff for t in times.get(identity, ())):
                exclusions.append((identity, "source_time_after_cutoff"))
            elif identity.startswith("Export:") and bundle.exported_at > cutoff:
                exclusions.append((identity, "source_time_after_cutoff"))
            else:
                available.append((identity, digest))
        if bundle.attempt_id is None:
            exclusions.append(("Attempt", "attributed_attempt_unavailable"))
        if bundle.outcome_id is None:
            exclusions.append(("Outcome", "assessment_unavailable"))
        return Availability(
            target=bundle.target,
            cutoff=cutoff,
            export_sha256=bundle.export_sha256,
            available_records=tuple(sorted(available)),
            exclusions=tuple(sorted(exclusions)),
            fully_available=not exclusions,
            unavailable_fields=bundle.unavailable_fields,
            exporter_eligible=bundle.exporter_eligible,
            learning_exclusions=bundle.learning_exclusions,
        )


def _members(bundle):
    return [(r.key, r.sha256) for r in bundle.records] + [
        (f"Export:{bundle.export_sha256}", bundle.content_sha256)
    ]


def benchmark_receipt_bundle(
    root: Path, evidence: BenchmarkEvidence
) -> BenchmarkReceiptBundle:
    """Bind a retained export to its stopped, operator-owned source, read only.

    The exporter remains the authority for source verification and containment.
    Additional source records are hashed, never copied into this metadata sidecar.
    Source must be quiescent; this is not a concurrent live-ledger receiver.
    """
    evidence = BenchmarkEvidence.model_validate_json(evidence.model_dump_json())
    rebuilt = export_benchmark_evidence(
        root,
        checkpoints=evidence.requested_checkpoints,
        exported_at=evidence.exported_at,
        historical_cutoff=evidence.historical_cutoff,
    )
    if rebuilt != evidence:
        raise ValueError("receipt export disagrees with trusted benchmark source")
    prepared = load_benchmark(root)
    repository = Repository(Database(prepared.control / "ledger.sqlite3"))
    row = evidence.observation
    if row.source_kind is not DataSourceKind.BENCHMARK:
        raise ValueError("receipt requires benchmark source")
    task = repository.get(Task, row.task_id)
    run = repository.get(Run, row.run_id)
    acceptance_digest = _digest(task.acceptance_spec.model_dump(mode="json"))
    target = Target(
        benchmark_id=evidence.benchmark_id,
        dataset_id=row.dataset.dataset_id,
        dataset_version=row.dataset.dataset_version,
        task_id=row.task_id,
        run_id=row.run_id,
        configuration_id=row.configuration.configuration_id,
        acceptance_id=row.acceptance_spec.identifier,
        acceptance_version=row.acceptance_spec.version,
        acceptance_sha256=acceptance_digest,
        resource_budget=row.resource_budget,
        execution_origin=evidence.execution_origin,
        fixture_id=evidence.fixture_id,
        fixture_version=evidence.fixture_version,
        fixture_fingerprint=evidence.fixture_fingerprint,
    )
    records = [task, run, row]
    attempts = [a for a in repository.list_records(Attempt) if a.run_id == run.run_id]
    records.extend(attempts)
    # These are exact canonical source records, not sanitized Event projections.
    events = [repository.get(Event, e.event_id) for e in evidence.native_events]
    records.extend(events)
    sessions = {e.session_id for e in events}
    records.extend(repository.get(Session, s) for s in sorted(sessions, key=str))
    records.extend(
        link
        for link in repository.list_task_session_links(task.task_id)
        if link.session_id in sessions
    )
    records.extend(
        link
        for link in repository.list_run_session_links(run.run_id)
        if link.session_id in sessions
    )
    records.extend(
        repository.get(Verification, v.verification_id)
        for v in evidence.verification_bindings
    )
    outcome = repository.get(Outcome, row.outcome_id) if row.outcome_id else None
    current, seen = outcome, set()
    while current is not None:
        if current.run_id != run.run_id or current.outcome_id in seen:
            raise ValueError("invalid benchmark assessment ancestry")
        records.append(current)
        seen.add(current.outcome_id)
        parent = current.supersedes_outcome_id
        current = repository.get(Outcome, parent) if parent else None
        if parent and current is None:
            raise ValueError("missing benchmark assessment ancestor")
    bindings = []
    for record in records:
        if record is None:
            raise ValueError("missing benchmark source record")
        kind, identity = key(record).split(":", 1)
        configuration = getattr(record, "configuration", None)
        acceptance = getattr(record, "acceptance_spec", None)
        bindings.append(
            RecordBinding(
                kind=kind,
                identity=identity,
                sha256=_digest(record.model_dump(mode="json")),
                task_id=getattr(record, "task_id", None),
                run_id=getattr(record, "run_id", None),
                configuration_id=configuration.configuration_id
                if configuration
                else None,
                acceptance_sha256=_digest(acceptance.model_dump(mode="json"))
                if acceptance
                else None,
                source_times=tuple(
                    SourceTime(field=k, value=v)
                    for k, v in record.__dict__.items()
                    if isinstance(v, datetime)
                ),
            )
        )
    bindings.extend(
        (
            RecordBinding(
                kind="Configuration",
                identity=target.configuration_id,
                sha256=_digest(row.configuration.model_dump(mode="json")),
            ),
            RecordBinding(
                kind="Acceptance", identity=acceptance_digest, sha256=acceptance_digest
            ),
        )
    )
    values = dict(
        target=target,
        export_sha256=evidence.content_sha256,
        exported_at=evidence.exported_at,
        observation_id=row.observation_id,
        attempt_id=row.attempt_id,
        outcome_id=row.outcome_id,
        supersedes_outcome_id=outcome.supersedes_outcome_id if outcome else None,
        exporter_eligible=row.eligible_for_configuration_learning,
        learning_exclusions=tuple(row.metadata["exclusions"]),
        verification_references=tuple(
            VerificationReference(**v.model_dump(exclude={"observed_at", "result"}))
            for v in evidence.verification_bindings
        ),
        records=tuple(sorted(bindings, key=lambda r: r.key)),
        unavailable_fields=tuple(
            sorted(
                {
                    "verification_to_attempt_explicit_link",
                    "prospective_initial_scope_receipts",
                    "budget_measurement_coverage",
                    "authenticated_external_time",
                    *(
                        f"configuration_{field}"
                        for field in (
                            "model_version",
                            "reasoning_level",
                            "configuration_version",
                        )
                        if getattr(row.configuration, field) is None
                    ),
                    *(
                        f"observation_{field}"
                        for field in ("latency_seconds", "cost_usd")
                        if getattr(row, field) is None
                    ),
                    *(
                        f"attempt_{field}"
                        for field in ("latency_seconds", "cost_usd")
                        if any(getattr(a, field) is None for a in attempts)
                    ),
                }
            )
        ),
    )
    draft = BenchmarkReceiptBundle.model_construct(**values, content_sha256="")
    return BenchmarkReceiptBundle.model_validate(
        {
            **draft.model_dump(mode="json"),
            "content_sha256": _digest(
                draft.model_dump(mode="json", exclude={"content_sha256"})
            ),
        }
    )
