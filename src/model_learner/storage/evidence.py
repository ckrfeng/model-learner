"""Scoped evidence sidecars; existing JSONL and ledger semantics are unchanged.

Receipts establish first observation by this sidecar, never retroactive knowledge.
Only reviewed metadata-only records are supported; this is not a transcript export.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import replace
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from model_learner.adapters.codex import ADAPTER_VERSION, SOURCE, _supported_event
from model_learner.domain.models import (
    Attempt,
    DatasetReference,
    DataSourceKind,
    Event,
    Observation,
    Outcome,
    Run,
    RunSessionLink,
    Session,
    Task,
    TaskSessionLink,
    Verification,
    utc_now,
)
from model_learner.observations.resolution import (
    ResolutionSnapshot,
    resolve_assessment,
    resolve_real_observations,
)
from model_learner.storage.database import Database, Repository, StorageError
from model_learner.verification import validate_evidence

KINDS = (Task, Session, Run, Attempt, Event, Verification, Outcome, Observation)
TYPES = {kind.__name__: kind for kind in (*KINDS, TaskSessionLink, RunSessionLink)}
METADATA = {
    Task: {"junit_verifier", "file_digest_verifier"},
    Session: {"machine_id", "adapter_version", "native_timestamp_coverage"},
    Run: {"final_artifact_fingerprint", "boundary_source"},
    Attempt: {"configuration_provenance", "boundary_source", "declaration_source"},
    Outcome: {"assessment_method"},
    Verification: {
        "criterion",
        "binding",
        "test_results",
        "report_observed_sha256",
        "completeness_reasons",
        "capture_method",
        "binding_provenance",
        "content_retained",
        "actual_sha256",
    },
    Observation: {
        "builder_version",
        "session_ids",
        "event_ids",
        "attempt_ids",
        "measurement_sources",
        "configuration_provenance",
        "boundaries_source",
        "event_time_basis",
        "exclusions",
        "configuration_conflict_event_ids",
        "assessment_source",
        "supersedes_outcome_id",
        "cost_coverage",
        "latency_coverage",
    },
}


def key(record: BaseModel) -> str:
    if isinstance(record, TaskSessionLink):
        identity = f"{record.task_id}:{record.session_id}"
    elif isinstance(record, RunSessionLink):
        identity = f"{record.run_id}:{record.session_id}"
    else:
        identity = str(getattr(record, type(record).__name__.lower() + "_id"))
    return f"{type(record).__name__}:{identity}"


def _digest(record: BaseModel) -> str:
    return hashlib.sha256(
        json.dumps(
            record.model_dump(mode="json"), sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()


def _public(record: BaseModel) -> BaseModel:
    """Drop locators/prose; refuse unsupported metadata rather than alter evidence."""
    data = record.model_dump(mode="json")
    if isinstance(record, Task):
        data.update(description="Scoped task", workspace_id=None)
    if isinstance(record, Verification):
        data["artifact_reference"] = record.artifact_fingerprint
        report_digest = record.metadata.get("report_observed_sha256")
        data["report_reference"] = f"sha256:{report_digest}" if report_digest else None
    for field in ("note", "stop_reason"):
        if field in data:
            data[field] = None
    if type(record) in METADATA and set(data["metadata"]) - METADATA[type(record)]:
        raise ValueError("unsupported public metadata; review a sanitized source")
    if isinstance(record, (Run, Attempt)):
        # Preserve only reviewed categorical declarations verbatim. Other custom
        # declaration text needs separate review.
        declarations = {"boundary_source": ("human_declaration",)}
        if isinstance(record, Attempt):
            declarations["declaration_source"] = (
                "human",
                "explicit_human_authorized_operator_CLI_invocation",
            )
        if any(
            field in data["metadata"]
            and (
                type(record.metadata[field]) is not str
                or data["metadata"][field] not in expected
            )
            for field, expected in declarations.items()
        ):
            raise ValueError("unsupported public declaration metadata")
    if isinstance(record, Session) and record.metadata:
        if (
            record.source != SOURCE
            or record.metadata.get("adapter_version") != ADAPTER_VERSION
            or record.metadata.get("native_timestamp_coverage") != "unavailable"
            or not isinstance(record.metadata.get("machine_id"), str)
            or not record.metadata["machine_id"]
        ):
            raise ValueError("unsupported public session metadata")
    if isinstance(record, Event) and (record.payload or record.raw_payload):
        # Production capture stores its allowlisted metadata in payload AND
        # raw_payload by default. Preserve it for attribution conflict checks;
        # erasing native model/provider fields would change learning eligibility.
        payload = record.payload
        if (
            record.source != SOURCE
            or not _supported_event(record)
            or set(payload)
            != {
                "native",
                "capture_id",
                "sequence",
                "timestamp_basis",
                "native_observed_at",
                "redacted_fields",
            }
            or payload["native_observed_at"] is not None
            or payload["sequence"] < 1
            or not isinstance(payload["redacted_fields"], list)
            or any(not isinstance(field, str) for field in payload["redacted_fields"])
            or record.raw_payload not in (None, payload["native"])
        ):
            raise ValueError("public evidence requires supported metadata-only events")
    if isinstance(record, (Attempt, Observation)) and record.configuration.metadata:
        raise ValueError(
            "public evidence requires reviewed empty configuration metadata"
        )
    # Locators and credential-shaped values must never escape via opaque fields.
    # This conservative profile is supplemented by the repository privacy guard
    # and human review; arbitrary private text cannot be detected automatically.
    encoded = json.dumps(data)
    forbidden = (
        "/Users/",
        "/home/",
        "/private/",
        "Bearer ",
        "ghp_",
        "-----BEGIN",
        "https://",
        "http://",
        "\\\\",
    )
    if any(marker in encoded for marker in forbidden) or re.search(
        r"\bsk-[A-Za-z0-9_-]{16,}", encoded
    ):
        raise ValueError("unsupported public locator or credential-shaped content")
    return type(record).model_validate(data)


class Entry(BaseModel):
    model_config = ConfigDict(extra="forbid")
    record_type: str
    record: dict
    sha256: str
    received_at: datetime | None = None

    def parse(self) -> BaseModel:
        if self.record_type not in TYPES:
            raise ValueError("unsupported scoped record type")
        item = TYPES[self.record_type].model_validate(self.record)
        if _digest(item) != self.sha256:
            raise ValueError("scoped record digest mismatch")
        if _public(item) != item:
            raise ValueError("scoped record is not a public projection")
        if self.received_at is not None and self.received_at.utcoffset() is None:
            raise ValueError("receipt requires a timezone")
        return item


class EvidenceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["scoped-evidence/v1"] = "scoped-evidence/v1"
    task_id: UUID
    dataset: DatasetReference
    entries: tuple[Entry, ...]
    # Explicit final-artifact-to-attempt declaration; v1 supports one full segment.
    verification_attempts: dict[UUID, UUID] = Field(default_factory=dict)


class ReceiptBook(BaseModel):
    """Persist model_dump_json after capture; reload to preserve first receipt.

    The clock is read here, never derived from a record's source timestamp. Imported
    receipts are trusted declarations, not signed or independently attested time.
    """

    model_config = ConfigDict(extra="forbid")
    version: Literal["evidence-receipts/v1"] = "evidence-receipts/v1"
    receipts: dict[str, tuple[str, datetime]] = Field(default_factory=dict)

    def capture(self, bundle: EvidenceBundle) -> None:
        now = utc_now()
        for entry in bundle.entries:
            item = entry.parse()
            identifier = key(item)
            previous = self.receipts.get(identifier)
            if previous is not None and previous[0] != entry.sha256:
                raise ValueError("receipt identity rebound")
            self.receipts.setdefault(identifier, (entry.sha256, now))


def scoped_bundle(
    repository: Repository,
    *,
    task_id: UUID,
    dataset: DatasetReference,
    receipts: ReceiptBook | None = None,
) -> EvidenceBundle:
    """Collect only the selected task, its bounded events and explicit links.

    Absent receipts remain null. Exporting old records does not backdate receipt.
    Call ReceiptBook.capture when the selected evidence is actually first received.
    """
    task = repository.get(Task, task_id)
    if task is None:
        raise StorageError("unknown scoped task")
    runs = [r for r in repository.list_records(Run) if r.task_id == task_id]
    run_ids = {r.run_id for r in runs}
    task_links = repository.list_task_session_links(task_id)
    run_links = [
        link for r in runs for link in repository.list_run_session_links(r.run_id)
    ]
    session_ids = {link.session_id for link in (*task_links, *run_links)}
    sessions = [
        repository.get(Session, identifier)
        for identifier in sorted(session_ids, key=str)
    ]
    records = [task, *sessions, *runs]
    for kind in (Attempt, Event, Verification, Outcome, Observation):
        for item in repository.list_records(kind, source_kind=dataset.source_kind):
            if isinstance(item, Observation) and item.dataset != dataset:
                continue
            if isinstance(item, Event):
                belongs = item.run_id in run_ids or (
                    item.run_id is None
                    and any(
                        item.session_id == link.session_id
                        and r.run_id == link.run_id
                        and r.started_at is not None
                        and r.ended_at is not None
                        and r.started_at <= item.observed_at <= r.ended_at
                        for link in run_links
                        for r in runs
                    )
                )
            else:
                belongs = item.run_id in run_ids
            if belongs:
                records.append(item)
    records.extend((*task_links, *run_links))
    entries = []
    for record in records:
        item = _public(record)
        checksum = _digest(item)
        receipt = receipts.receipts.get(key(item)) if receipts else None
        if receipt and receipt[0] != checksum:
            raise ValueError("receipt identity rebound")
        entries.append(
            Entry(
                record_type=type(item).__name__,
                record=item.model_dump(mode="json"),
                sha256=checksum,
                received_at=receipt[1] if receipt else None,
            )
        )
    bindings = {}
    for verification in (r for r in records if isinstance(r, Verification)):
        candidates = [
            a
            for a in records
            if isinstance(a, Attempt) and a.run_id == verification.run_id
        ]
        if len(candidates) != 1:
            raise ValueError("portable verification requires one explicit full attempt")
        bindings[verification.verification_id] = candidates[0].attempt_id
    return EvidenceBundle(
        task_id=task_id,
        dataset=dataset,
        entries=tuple(entries),
        verification_attempts=bindings,
    )


def _replay(repository: Repository, bundle: EvidenceBundle) -> None:
    if bundle.dataset.source_kind is not DataSourceKind.REAL:
        raise ValueError(
            "scoped evidence v1 requires an explicit real-contract dataset"
        )
    records = [entry.parse() for entry in bundle.entries]
    if len({key(r) for r in records}) != len(records):
        raise ValueError("duplicate scoped identity")
    tasks = [r for r in records if isinstance(r, Task)]
    if len(tasks) != 1 or tasks[0].task_id != bundle.task_id:
        raise ValueError("bundle must contain exactly the selected task")
    if any(isinstance(r, Run) and r.task_id != bundle.task_id for r in records):
        raise ValueError("unrelated run in scope")
    # Repository APIs remain the authority for foreign keys and immutable records.
    order = (*KINDS[:2], TaskSessionLink, Run, RunSessionLink, *KINDS[3:])
    for kind in order:
        selected = [r for r in records if type(r) is kind]
        if kind is Outcome:
            selected.sort(key=lambda r: (r.recorded_at, str(r.outcome_id)))
            pending = selected[:]
            selected = []
            while pending:
                ready = [
                    r
                    for r in pending
                    if r.supersedes_outcome_id is None
                    or any(p.outcome_id == r.supersedes_outcome_id for p in selected)
                ]
                if not ready:
                    raise StorageError("dangling or cyclic assessment parent")
                selected.extend(ready)
                pending = [r for r in pending if r not in ready]
        for item in selected:
            if kind is TaskSessionLink:
                existing = [
                    r
                    for r in repository.list_task_session_links(item.task_id)
                    if r.session_id == item.session_id
                ]
                writer = repository.associate_session
            elif kind is RunSessionLink:
                existing = [
                    r
                    for r in repository.list_run_session_links(item.run_id)
                    if r.session_id == item.session_id
                ]
                writer = repository.associate_run_session
            else:
                previous = repository.get(kind, key(item).split(":", 1)[1])
                existing = [previous] if previous else []
                writer = repository.import_record
            if existing:
                if existing != [item]:
                    raise StorageError("scoped identity conflicts with existing record")
            elif writer(item) != item:
                raise StorageError(
                    "scoped stable identity conflicts with existing record"
                )
    for row in (r for r in records if isinstance(r, Observation)):
        for field, kind in (
            ("attempt_ids", Attempt),
            ("session_ids", Session),
            ("event_ids", Event),
        ):
            identifiers = row.metadata.get(field)
            if not isinstance(identifiers, list):
                raise ValueError("portable derivation requires explicit dependency IDs")
            for identifier in identifiers:
                dependency = repository.get(kind, identifier)
                if dependency is None:
                    raise StorageError("dangling observation dependency")
                if isinstance(dependency, Attempt) and dependency.run_id != row.run_id:
                    raise StorageError("foreign observation attempt")
                if isinstance(dependency, Session) and dependency.session_id not in {
                    link.session_id
                    for link in repository.list_run_session_links(row.run_id)
                }:
                    raise StorageError("foreign observation session")
                if isinstance(dependency, Event) and dependency.run_id not in (
                    None,
                    row.run_id,
                ):
                    raise StorageError("foreign observation event")
    runs = [r for r in records if isinstance(r, Run)]
    verifications = [r for r in records if isinstance(r, Verification)]
    if set(bundle.verification_attempts) != {v.verification_id for v in verifications}:
        raise ValueError("verification attempt binding missing or extraneous")
    for verification in verifications:
        run = repository.get(Run, verification.run_id)
        attempt = repository.get(
            Attempt, bundle.verification_attempts[verification.verification_id]
        )
        if (
            attempt is None
            or attempt.run_id != run.run_id
            or (attempt.started_at, attempt.ended_at) != (run.started_at, run.ended_at)
        ):
            raise ValueError("verification attempt binding mismatch")
        validate_evidence(repository, run, tasks[0], verification)
    for run in runs:
        state = resolve_assessment(
            repository.list_records(Outcome),
            run_id=run.run_id,
            cutoff=datetime.max.replace(tzinfo=UTC),
        )
        if state.issues:
            raise StorageError("conflicting assessment history")
    # Every exported record must be part of the selected closure, including links,
    # observations and shared-session events. A reconstruction must be self-contained.
    rebuilt = scoped_bundle(repository, task_id=bundle.task_id, dataset=bundle.dataset)
    if {key(e.parse()) for e in rebuilt.entries} != {key(r) for r in records}:
        raise ValueError("dangling or unrelated scoped record")


def import_bundle(repository: Repository, bundle: EvidenceBundle) -> None:
    """Validate an isolated reconstruction before idempotent replay.

    Use a disposable destination. Replay is not a concurrent transactional merge;
    destination identity conflicts are checked before any destination insertion.
    """
    bundle = EvidenceBundle.model_validate_json(bundle.model_dump_json())
    with TemporaryDirectory(prefix="model-learner-evidence-") as temporary:
        db = Database(Path(temporary) / "validate.sqlite")
        db.initialize()
        _replay(Repository(db), bundle)
    matched = 0
    for entry in bundle.entries:
        item = entry.parse()
        if isinstance(item, (TaskSessionLink, RunSessionLink)):
            links = (
                repository.list_task_session_links(item.task_id)
                if isinstance(item, TaskSessionLink)
                else repository.list_run_session_links(item.run_id)
            )
            previous = next((r for r in links if key(r) == key(item)), None)
        else:
            previous = repository.get(type(item), key(item).split(":", 1)[1])
        if previous is not None and previous != item:
            raise StorageError("scoped identity conflicts with existing record")
        matched += previous is not None
    # No partial merge into a live ledger: either empty or an exact scoped replay.
    counts = sum(
        len(repository.list_records(kind)) for kind in KINDS if kind is not Observation
    )
    counts += sum(
        len(repository.list_observations(source)) for source in DataSourceKind
    )
    primary_count = sum(
        e.record_type not in {"TaskSessionLink", "RunSessionLink"}
        for e in bundle.entries
    )
    if counts and (matched != len(bundle.entries) or counts != primary_count):
        raise StorageError("destination must be empty or an exact scoped replay")
    _replay(repository, bundle)


class _ReceivedView:
    """Read-only receipt gate in front of the existing historical resolver."""

    def __init__(self, bundle: EvidenceBundle, cutoff: datetime):
        if cutoff.utcoffset() is None:
            raise ValueError("cutoff requires a timezone")
        self.records = [
            e.parse()
            for e in bundle.entries
            if e.received_at is not None and e.received_at <= cutoff
        ]

    def get(self, kind, identifier):
        return next(
            (
                r
                for r in self.records
                if type(r) is kind and key(r) == f"{kind.__name__}:{identifier}"
            ),
            None,
        )

    def list_records(self, kind, **kwargs):
        return [r for r in self.records if type(r) is kind]

    def list_observations(self, source_kind, *, dataset_id=None):
        return [
            r
            for r in self.list_records(Observation)
            if r.source_kind == source_kind
            and (dataset_id is None or r.dataset.dataset_id == dataset_id)
        ]

    def list_task_session_links(self, task_id):
        return [r for r in self.list_records(TaskSessionLink) if r.task_id == task_id]

    def list_run_session_links(self, run_id):
        return [r for r in self.list_records(RunSessionLink) if r.run_id == run_id]


def resolve_bundle(bundle: EvidenceBundle, *, cutoff: datetime) -> ResolutionSnapshot:
    """Revalidate the bundle, then gate every dependency by its actual receipt.

    Null receipt means unavailable, even when source timestamps are ancient.
    Later corrections cannot replace earlier heads; a received correction with
    unavailable evidence fails closed instead of reverting to an earlier label.
    """
    with TemporaryDirectory(prefix="model-learner-asof-") as temporary:
        db = Database(Path(temporary) / "snapshot.sqlite")
        db.initialize()
        _replay(Repository(db), bundle)
    view = _ReceivedView(bundle, cutoff)
    snapshot = resolve_real_observations(view, dataset=bundle.dataset, cutoff=cutoff)
    return replace(
        snapshot,
        method="receipt-gated-" + snapshot.method,
        availability_limitations=(
            "Every record and association requires a non-null receipt "
            "at or before cutoff",
            "Declared source and assessment timestamps must also pass as-of checks",
            "Imported receipts are declarations, not authenticated time attestations",
        ),
    )
