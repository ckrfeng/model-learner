"""Operator-controlled local coding evaluation; never launch an agent or process.

Disposable directories and integrity checks are not an operating-system sandbox.
Real agents and submitted Python must be run under operator-provided containment.
"""

import hashlib
import json
import os
import shutil
import sqlite3
import stat
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field

from model_learner.adapters.codex import ingest_codex_capture, read_codex_capture
from model_learner.benchmark.fixtures import acceptance_source, get_task, list_tasks
from model_learner.benchmark.isolation import require_supported_real_containment
from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    DatasetReference,
    ExecutionConfiguration,
    Outcome,
    Run,
    RunSessionLink,
    RunState,
    Session,
    Task,
    TaskSessionLink,
    Verification,
    utc_now,
)
from model_learner.storage.database import Database, Repository
from model_learner.verification import (
    JUnitReportBinding,
    assess_run,
    file_sha256,
    junit_criterion,
    verify_junit,
)
from model_learner.verification.junit import MAX_REPORT_BYTES

__all__ = [
    "BenchmarkResult",
    "PreparedBenchmark",
    "cleanup_benchmark",
    "finalize_benchmark",
    "list_tasks",
    "load_benchmark",
    "prepare_benchmark",
    "snapshot_candidate",
]

_IGNORED = {
    ".git",
    ".venv",
    ".uv-cache",
    ".tools",
    ".model-learner",
    ".pytest_cache",
    ".ruff_cache",
    "__pycache__",
    ".DS_Store",
}
MAX_ARTIFACT_BYTES = 1024 * 1024


class PreparedBenchmark(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    version: Literal["coding-benchmark/v1"] = "coding-benchmark/v1"
    benchmark_id: UUID = Field(default_factory=uuid4)
    root: Path
    protected_repository: Path
    repository_fingerprint: str
    fixture_id: str
    fixture_version: str
    fixture_fingerprint: str
    task: Task
    configuration: ExecutionConfiguration
    dataset: DatasetReference
    execution_origin: Literal["real", "fixture"]
    isolation_mechanism: str = Field(min_length=1)

    @property
    def workspace(self) -> Path:
        return self.root / "workspace"

    @property
    def control(self) -> Path:
        return self.root / "control"


class BenchmarkResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal["coding-benchmark-result/v1"] = "coding-benchmark-result/v1"
    benchmark_id: UUID
    dataset: DatasetReference
    execution_origin: Literal["real", "fixture"]
    configuration: ExecutionConfiguration
    run: Run
    outcome: Outcome
    verification: Verification | None
    telemetry_events: int
    telemetry_diagnostics: int
    reasons: tuple[str, ...]
    ledger: Path
    # Learning eligibility needs later temporal, attribution and budget validation.
    learning_observation_created: Literal[False] = False


def _digest(contents: bytes) -> str:
    return hashlib.sha256(contents).hexdigest()


def _fixture_fingerprint(task_id: str) -> str:
    fixture = get_task(task_id)
    return _digest(
        json.dumps(
            {
                "description": fixture.description,
                "source": fixture.initial_source,
                "acceptance": acceptance_source(fixture),
                "ids": fixture.required_test_ids,
                "version": fixture.version,
            },
            sort_keys=True,
        ).encode()
    )


def _regular(path: Path) -> None:
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("benchmark input must be a regular, non-symlink file")


def _repository_fingerprint(root: Path) -> str:
    if not root.is_dir():
        raise ValueError("protected repository must exist")
    entries = []

    def visit(directory: Path) -> None:
        for path in sorted(directory.iterdir()):
            if path.name in _IGNORED:
                continue
            if path.is_symlink():
                raise ValueError("protected source tree contains unsupported symlinks")
            if path.is_dir():
                visit(path)
            else:
                _regular(path)
                entries.append((path.relative_to(root).as_posix(), file_sha256(path)))

    visit(root)
    return _digest(json.dumps(entries, separators=(",", ":")).encode())


def _outside(path: Path, protected: Path) -> None:
    if path == protected or protected in path.parents or path in protected.parents:
        raise ValueError(
            "benchmark paths must be separate from the protected repository"
        )


def _write_json(path: Path, value: BaseModel | dict) -> None:
    data = (
        value.model_dump_json(indent=2)
        if isinstance(value, BaseModel)
        else json.dumps(value, indent=2, sort_keys=True)
    )
    with path.open("x") as stream:
        stream.write(data + "\n")


def prepare_benchmark(
    *,
    parent: Path,
    task_id: str,
    configuration: ExecutionConfiguration,
    protected_repository: Path,
    isolation_mechanism: str,
    dataset_id: str = "local-coding",
    dataset_version: str = "1",
    execution_origin: Literal["real", "fixture"] = "real",
) -> PreparedBenchmark:
    """Stage a fresh public task. No agent, tests, shell or paid API is launched."""
    fixture = get_task(task_id)
    parent = Path(parent).resolve(strict=True)
    protected = Path(protected_repository).resolve(strict=True)
    _outside(parent, protected)
    if not parent.is_dir() or not isolation_mechanism.strip():
        raise ValueError("an existing parent and declared containment are required")
    baseline = _repository_fingerprint(protected)
    root = Path(tempfile.mkdtemp(prefix="model-learner-benchmark-", dir=parent))
    try:
        workspace, control = root / "workspace", root / "control"
        workspace.mkdir()
        control.mkdir()
        task = Task(
            description=fixture.description,
            acceptance_spec=AcceptanceSpec(
                identifier=f"public-coding-{fixture.task_id}", version=fixture.version
            ),
            workspace_id=str(workspace),
            task_group=f"coding-{fixture.task_id}",
            metadata={
                "junit_verifier": junit_criterion(
                    required_test_ids=fixture.required_test_ids
                ),
                "source_kind": "benchmark",
                "execution_origin": execution_origin,
            },
        )
        prepared = PreparedBenchmark(
            root=root,
            protected_repository=protected,
            repository_fingerprint=baseline,
            fixture_id=fixture.task_id,
            fixture_version=fixture.version,
            fixture_fingerprint=_fixture_fingerprint(task_id),
            task=task,
            configuration=configuration,
            dataset=DatasetReference(
                source_kind="benchmark",
                dataset_id=f"{dataset_id}:{execution_origin}",
                dataset_version=dataset_version,
            ),
            execution_origin=execution_origin,
            isolation_mechanism=isolation_mechanism,
        )
        (workspace / fixture.artifact_name).write_text(fixture.initial_source)
        (workspace / "TASK.txt").write_text(fixture.description + "\n")
        (control / "acceptance.py").write_text(acceptance_source(fixture))
        _write_json(control / "manifest.json", prepared)
        database = Database(control / "ledger.sqlite3")
        database.initialize()
        Repository(database).create_task(task)
        return prepared
    except BaseException:
        shutil.rmtree(root)
        raise


def load_benchmark(root: Path) -> PreparedBenchmark:
    """Read an operator-owned manifest and recheck trust-sensitive paths/fixtures."""
    root = Path(root).absolute()
    if root.is_symlink() or root.resolve(strict=True) != root:
        raise ValueError("benchmark root must be canonical and non-symlink")
    if not root.name.startswith("model-learner-benchmark-"):
        raise ValueError("unsupported benchmark root")
    for name in ("control", "workspace"):
        path = root / name
        if path.is_symlink() or not path.is_dir():
            raise ValueError("benchmark directories must be real directories")
    manifest = root / "control/manifest.json"
    _regular(manifest)
    if manifest.stat().st_size > MAX_ARTIFACT_BYTES:
        raise ValueError("benchmark manifest exceeds the size limit")
    prepared = PreparedBenchmark.model_validate_json(manifest.read_text())
    if prepared.root != root:
        raise ValueError("benchmark manifest root does not match its directory")
    protected = prepared.protected_repository.resolve(strict=True)
    if protected != prepared.protected_repository:
        raise ValueError("protected repository path changed")
    _outside(root, protected)
    fixture = get_task(prepared.fixture_id)
    if prepared.fixture_version != fixture.version or (
        prepared.fixture_fingerprint != _fixture_fingerprint(fixture.task_id)
    ):
        raise ValueError("benchmark fixture version or content changed")
    expected = junit_criterion(required_test_ids=fixture.required_test_ids)
    if (
        prepared.task.metadata.get("junit_verifier") != expected
        or prepared.task.description != fixture.description
        or prepared.task.acceptance_spec.identifier
        != f"public-coding-{fixture.task_id}"
        or prepared.task.acceptance_spec.version != fixture.version
        or prepared.dataset.source_kind.value != "benchmark"
        or prepared.task.metadata.get("source_kind") != "benchmark"
        or prepared.task.metadata.get("execution_origin") != prepared.execution_origin
        or not prepared.dataset.dataset_id.endswith(":" + prepared.execution_origin)
    ):
        raise ValueError("benchmark acceptance or dataset declaration changed")
    acceptance = prepared.control / "acceptance.py"
    _regular(acceptance)
    if acceptance.read_bytes() != acceptance_source(fixture).encode():
        raise ValueError("trusted acceptance source changed")
    _regular(prepared.control / "ledger.sqlite3")
    return prepared


def _unchanged_repository(prepared: PreparedBenchmark) -> None:
    if _repository_fingerprint(prepared.protected_repository) != (
        prepared.repository_fingerprint
    ):
        raise ValueError("protected repository changed; benchmark result refused")


def snapshot_candidate(root: Path) -> Path:
    """After the externally launched agent stops, freeze its one declared module."""
    prepared = load_benchmark(root)
    _unchanged_repository(prepared)
    fixture = get_task(prepared.fixture_id)
    artifact = prepared.workspace / fixture.artifact_name
    _regular(artifact)
    if artifact.stat().st_size > MAX_ARTIFACT_BYTES:
        raise ValueError("candidate exceeds the size limit")
    digest = file_sha256(artifact)
    contents = artifact.read_bytes()
    if _digest(contents) != digest:
        raise ValueError("candidate changed while snapshotting")
    frozen = prepared.control / "candidate.py"
    with frozen.open("xb") as stream:
        stream.write(contents)
    _write_json(
        prepared.control / "snapshot.json",
        {"sha256": digest, "snapshotted_at": utc_now().isoformat()},
    )
    frozen.chmod(0o400)
    return frozen


def _finalize_benchmark(
    root: Path,
    *,
    started_at: datetime,
    ended_at: datetime,
    state: RunState = RunState.FINISHED,
    capture: Path | None = None,
    machine_id: str = "local-benchmark",
    test_completed: bool | None = None,
    test_exit_code: int | None = None,
    test_generated_at: datetime | None = None,
    isolation_confirmed: bool = False,
    _ledger: Path,
) -> tuple[BenchmarkResult, JUnitReportBinding | None]:
    """Collect external telemetry/tests once, never trusting agent self-report.

    The operator confirms its agent/test sandbox denied writes to the protected
    repository and agent writes to control. This is a declaration, not attestation.
    """
    prepared = load_benchmark(root)
    if isolation_confirmed is not True:
        raise ValueError("operator containment confirmation is required")
    _unchanged_repository(prepared)
    for time in (started_at, ended_at):
        if time.tzinfo is None or time.utcoffset() is None:
            raise ValueError("benchmark boundaries must include a timezone")
    if started_at < prepared.task.created_at or ended_at < started_at:
        raise ValueError("benchmark boundaries predate preparation or are reversed")
    if ended_at > utc_now():
        raise ValueError("stopped agent boundary is in the future")
    state = RunState(state)
    if state is RunState.RUNNING:
        raise ValueError("stop the agent before benchmark finalization")
    if (prepared.control / "result.json").exists():
        raise ValueError("benchmark has already been finalized")
    database = Database(_ledger)
    repository = Repository(database)
    if repository.list_records(Run):
        raise ValueError("benchmark ledger already contains a run")
    if repository.get(Task, prepared.task.task_id) != prepared.task:
        raise ValueError("predeclared benchmark task changed")
    reasons = []
    artifact = prepared.control / "candidate.py"
    fingerprint = None
    snapshot_at = None
    if artifact.exists():
        _regular(artifact)
        snapshot = prepared.control / "snapshot.json"
        _regular(snapshot)
        snapshot_data = json.loads(snapshot.read_text())
        if file_sha256(artifact) != snapshot_data["sha256"]:
            raise ValueError("frozen candidate changed")
        fingerprint = "sha256:" + snapshot_data["sha256"]
        snapshot_at = datetime.fromisoformat(snapshot_data["snapshotted_at"])
        if snapshot_at.tzinfo is None or snapshot_at < ended_at:
            raise ValueError("snapshot must follow the stopped agent")
    else:
        reasons.append("candidate_snapshot_missing")
    report = prepared.control / "report.xml"
    if report.exists():
        _regular(report)
        if report.stat().st_size > MAX_REPORT_BYTES:
            reasons.append("acceptance_report_too_large")
    else:
        reasons.append("acceptance_report_missing")
    binding = None
    run = Run(
        task_id=prepared.task.task_id,
        state=state,
        started_at=started_at,
        ended_at=ended_at,
        starting_state_fingerprint="sha256:"
        + _digest(get_task(prepared.fixture_id).initial_source.encode()),
        metadata={
            "final_artifact_fingerprint": fingerprint,
            "boundary_source": "external_operator_receipt",
            "benchmark_id": str(prepared.benchmark_id),
            "source_kind": "benchmark",
            "execution_origin": prepared.execution_origin,
            "isolation_mechanism": prepared.isolation_mechanism,
            "isolation_confirmation": "operator_declaration",
        },
    )
    if (
        fingerprint is not None
        and report.exists()
        and report.stat().st_size <= MAX_REPORT_BYTES
    ):
        binding = JUnitReportBinding(
            task_id=prepared.task.task_id,
            run_id=run.run_id,
            acceptance_spec=prepared.task.acceptance_spec,
            artifact_fingerprint=fingerprint,
            report_sha256=file_sha256(report),
            report_generated_at=test_generated_at or utc_now(),
            source="junit",
            execution_completed=test_completed,
            command_exit_code=test_exit_code,
        )
        if binding.report_generated_at < ended_at:
            raise ValueError("independent acceptance must follow the stopped agent")
        if snapshot_at is not None and binding.report_generated_at < snapshot_at:
            raise ValueError("independent acceptance must follow the frozen snapshot")
        if binding.report_generated_at > utc_now():
            raise ValueError("acceptance generation time is in the future")
    session_ids = []
    telemetry_events = diagnostics = 0
    if capture is not None:
        capture = Path(capture)
        _regular(capture)
        capture = capture.resolve(strict=True)
        _outside(capture, prepared.protected_repository)
        capture_digest = file_sha256(capture)
        batch = read_codex_capture(capture, machine_id=machine_id, retain_raw=False)
        for event in batch.events:
            native = event.payload.get("native", {})
            for native_field, declared in (
                ("model", prepared.configuration.model),
                ("model_provider", prepared.configuration.provider),
            ):
                observed = native.get(native_field)
                if (
                    declared is not None
                    and observed is not None
                    and observed != declared
                ):
                    reasons.append("configuration_declaration_conflicts_with_telemetry")
        if any(
            not started_at <= event.observed_at <= ended_at for event in batch.events
        ):
            raise ValueError(
                "captured events fall outside declared benchmark boundaries"
            )
        imported = ingest_codex_capture(
            repository, capture, machine_id=machine_id, retain_raw=False
        )
        if file_sha256(capture) != capture_digest:
            raise ValueError("capture changed while finalizing")
        telemetry_events = imported.events_inserted + imported.events_duplicate
        diagnostics = len(imported.diagnostics)
        session_ids = [session.session_id for session in batch.sessions]
        if diagnostics:
            reasons.append("telemetry_incomplete")
    if not telemetry_events:
        reasons.append("agent_telemetry_missing")
    repository.create_run(run)
    for session_id in session_ids:
        # A malformed capture can contain a session with no accepted events.
        if repository.get(Session, session_id) is None:
            continue
        repository.associate_session(
            TaskSessionLink(task_id=prepared.task.task_id, session_id=session_id)
        )
        repository.associate_run_session(
            RunSessionLink(run_id=run.run_id, session_id=session_id)
        )
    repository.create_attempt(
        Attempt(
            run_id=run.run_id,
            configuration=prepared.configuration,
            started_at=started_at,
            ended_at=ended_at,
            metadata={"configuration_provenance": "operator_predeclaration"},
        )
    )
    evidence = None
    if binding is not None:
        evidence = verify_junit(
            repository,
            run_id=run.run_id,
            artifact=artifact,
            report=report,
            binding=binding,
        )
        reasons.extend(evidence.metadata["completeness_reasons"])
    if state is not RunState.FINISHED:
        reasons.append("agent_execution_incomplete")
    outcome = assess_run(
        repository,
        run_id=run.run_id,
        verification_id=(
            evidence.verification_id
            if evidence is not None and state is RunState.FINISHED
            else None
        ),
    )
    _unchanged_repository(prepared)
    result = BenchmarkResult(
        benchmark_id=prepared.benchmark_id,
        dataset=prepared.dataset,
        execution_origin=prepared.execution_origin,
        configuration=prepared.configuration,
        run=run,
        outcome=outcome,
        verification=evidence,
        telemetry_events=telemetry_events,
        telemetry_diagnostics=diagnostics,
        reasons=tuple(sorted(set(reasons))),
        ledger=prepared.control / "ledger.sqlite3",
    )
    return result, binding


def finalize_benchmark(
    root: Path,
    *,
    started_at: datetime,
    ended_at: datetime,
    state: RunState = RunState.FINISHED,
    capture: Path | None = None,
    machine_id: str = "local-benchmark",
    test_completed: bool | None = None,
    test_exit_code: int | None = None,
    test_generated_at: datetime | None = None,
    isolation_confirmed: bool = False,
) -> BenchmarkResult:
    """Finalize in a private staging ledger; rejected evidence leaves no partial run."""
    prepared = load_benchmark(root)
    if prepared.execution_origin == "real":
        require_supported_real_containment()
    lock = prepared.control / "finalizing.lock"
    with lock.open("x"):
        pass
    try:
        with tempfile.TemporaryDirectory(
            prefix="finalizing-", dir=prepared.control
        ) as temp:
            stage = Path(temp)
            staging_ledger = stage / "ledger.sqlite3"
            # SQLite backup includes committed WAL data without raw file-copy races.
            source = sqlite3.connect(prepared.control / "ledger.sqlite3")
            destination = sqlite3.connect(staging_ledger)
            try:
                source.backup(destination)
            finally:
                destination.close()
                source.close()
            result, binding = _finalize_benchmark(
                root,
                started_at=started_at,
                ended_at=ended_at,
                state=state,
                capture=capture,
                machine_id=machine_id,
                test_completed=test_completed,
                test_exit_code=test_exit_code,
                test_generated_at=test_generated_at,
                isolation_confirmed=isolation_confirmed,
                _ledger=staging_ledger,
            )
            _write_json(stage / "result.json", result)
            if binding is not None:
                _write_json(stage / "binding.json", binding)
            # Single operator only: the lock prevents parallel finalizers.
            os.replace(staging_ledger, prepared.control / "ledger.sqlite3")
            if binding is not None:
                os.replace(stage / "binding.json", prepared.control / "binding.json")
            os.replace(stage / "result.json", prepared.control / "result.json")
            return result
    finally:
        lock.unlink()


def cleanup_benchmark(root: Path) -> None:
    """Explicitly dispose of one validated workspace/control tree, including data."""
    prepared = load_benchmark(root)
    shutil.rmtree(prepared.root)
