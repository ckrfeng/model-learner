"""W3: wholly fictional offline execution, with real local pytest verification.

Native-like messages and source are authored here, never copied from a session.
The real-contract dataset exists only in disposable pytest directories; it is not
real model telemetry, a simulator benchmark, or a performance experiment.
"""

import hashlib
import json
import math
import os
import runpy
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import timedelta
from pathlib import Path
from uuid import UUID, uuid4

import pytest
from pydantic import TypeAdapter
from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    DatasetReference,
    Event,
    ExecutionConfiguration,
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
from model_learner.learn.estimator import BetaBernoulli
from model_learner.learn.prospective import (
    CompatibilityPolicy,
    ConfigurationMember,
    TaskMember,
    canonical,
    forecast,
    freeze,
    score_frozen,
)
from model_learner.observations import build_real_observation, derive_real_observation
from model_learner.observations.resolution import resolve_real_observations
from model_learner.storage import evidence as portable
from model_learner.storage.database import Database, Repository
from model_learner.verification import (
    JUnitReportBinding,
    assess_run,
    file_sha256,
    junit_criterion,
    verify_junit,
)

DATASET = DatasetReference(
    source_kind="real", dataset_id="fictional-w3-only", dataset_version="1"
)
CONFIG = ExecutionConfiguration(
    provider="fictional",
    model="fictional-coder",
    reasoning_level="low",
    harness="codex.exec",
    harness_version="synthetic-v1",
)
SPEC = AcceptanceSpec(identifier="fictional-increment", version="1")
TEST_SOURCE = """from candidate import increment

def test_positive():
    assert increment(3) == 4

def test_negative():
    assert increment(-2) == -1
"""
REQUIRED = ["test_acceptance::test_positive", "test_acceptance::test_negative"]


def repository(path):
    db = Database(path)
    db.initialize()
    return Repository(db)


def cli(*args, input=None):
    result = CliRunner().invoke(app, list(map(str, args)), input=input)
    assert result.exit_code == 0, result.output
    return json.loads(result.output)


@dataclass
class Lifecycle:
    repo: Repository
    task: Task
    directory: Path
    run_id: UUID
    contract: str
    run: Run | None = None
    attempt: Attempt | None = None
    session: Session | None = None
    binding: JUnitReportBinding | None = None

    @property
    def artifact(self):
        return self.directory / "candidate.py"

    @property
    def report(self):
        return self.directory / "report.xml"


def prepare(repo, directory):
    directory.mkdir()
    (directory / "test_acceptance.py").write_text(TEST_SOURCE)
    task = repo.create_task(
        Task(
            description="Fictional integer increment",
            created_at=utc_now(),
            acceptance_spec=SPEC,
            task_group="fictional-arithmetic",
            metadata={"junit_verifier": junit_criterion(required_test_ids=REQUIRED)},
        )
    )
    return Lifecycle(
        repo, task, directory, uuid4(), canonical(task.model_dump(mode="json"))
    )


def execute(case, *, broken=False, emitted_model=None):
    """Consume synthetic stdin through both production capture/import CLI paths."""
    start = utc_now()
    native = [
        {"type": "thread.started", "thread_id": f"fictional-{case.run_id}"},
        {"type": "turn.started"},
        {
            "type": "item.completed",
            "item": {
                "id": "fictional-command",
                "type": "command_execution",
                "status": "completed",
                "exit_code": 0,
            },
        },
        {
            "type": "item.completed",
            "item": {
                "id": "fictional-completion",
                "type": "agent_message",
                "text": "Fictional completion claim; not acceptance evidence.",
            },
        },
        {"type": "turn.completed", "usage": {"input_tokens": 12, "output_tokens": 4}},
    ]
    if emitted_model:
        native[1]["model"] = emitted_model
    capture = case.directory / "capture.jsonl"
    captured = cli(
        "capture",
        "codex",
        capture,
        "--source-version",
        "synthetic-v1",
        input="\n".join(json.dumps(row) for row in native) + "\n",
    )
    assert captured["accepted"] == 5 and not captured["diagnostics"]
    case.artifact.write_text(
        "def increment(value):\n    return value + " + ("2" if broken else "1") + "\n"
    )
    end = utc_now()
    imported = cli(
        "import",
        "codex",
        capture,
        "--machine-id",
        "fictional-machine",
        "--database",
        case.repo.database.path,
    )
    assert imported["events_inserted"] == 5 and not imported["diagnostics"]
    case.session = next(
        s
        for s in case.repo.list_records(Session)
        if s.native_session_id == f"fictional-{case.run_id}"
    )
    case.repo.associate_session(
        TaskSessionLink(
            task_id=case.task.task_id,
            session_id=case.session.session_id,
        )
    )
    case.run = case.repo.create_run(
        Run(
            run_id=case.run_id,
            task_id=case.task.task_id,
            state="finished",
            started_at=start,
            ended_at=end,
            metadata={
                "final_artifact_fingerprint": "sha256:" + file_sha256(case.artifact)
            },
        )
    )
    case.repo.associate_run_session(
        RunSessionLink(
            run_id=case.run_id,
            session_id=case.session.session_id,
        )
    )
    case.attempt = case.repo.create_attempt(
        Attempt(
            run_id=case.run_id,
            configuration=CONFIG,
            started_at=start,
            ended_at=end,
            metadata={"configuration_provenance": "human_declaration"},
        )
    )
    return case


def run_acceptance(case):
    """Run the frozen independent tests locally; never a coding/model subprocess."""
    before = file_sha256(case.artifact)
    result = subprocess.run(
        [
            sys.executable,
            "-B",
            "-m",
            "pytest",
            "-q",
            "-c",
            "/dev/null",
            "--rootdir",
            str(case.directory),
            "--confcutdir",
            str(case.directory),
            "-p",
            "no:cacheprovider",
            "--junitxml",
            str(case.report),
            str(case.directory / "test_acceptance.py"),
        ],
        cwd=case.directory,
        capture_output=True,
        text=True,
        timeout=30,
        env={
            **os.environ,
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_ADDOPTS": "",
        },
    )
    assert result.returncode in (0, 1), result.stdout + result.stderr
    assert file_sha256(case.artifact) == before
    assert (case.directory / "test_acceptance.py").read_text() == TEST_SOURCE
    case.binding = JUnitReportBinding(
        task_id=case.task.task_id,
        run_id=case.run_id,
        acceptance_spec=SPEC,
        artifact_fingerprint="sha256:" + before,
        report_sha256=file_sha256(case.report),
        report_generated_at=utc_now(),
        source="pytest-junit",
        execution_completed=True,
        command_exit_code=result.returncode,
    )
    return result.returncode


def verify(case):
    return verify_junit(
        case.repo,
        run_id=case.run_id,
        artifact=case.artifact,
        report=case.report,
        binding=case.binding,
    )


def assess(case, evidence=None, previous=None, *, persist=True):
    outcome = assess_run(
        case.repo,
        run_id=case.run_id,
        verification_id=evidence.verification_id if evidence else None,
        supersedes_outcome_id=previous.outcome_id if previous else None,
    )
    builder = build_real_observation if persist else derive_real_observation
    row = builder(
        case.repo, run_id=case.run_id, outcome_id=outcome.outcome_id, dataset=DATASET
    )
    return outcome, row


def receive(case, book=None):
    book = book or portable.ReceiptBook()
    book.capture(
        portable.scoped_bundle(case.repo, task_id=case.task.task_id, dataset=DATASET)
    )
    return portable.scoped_bundle(
        case.repo, task_id=case.task.task_id, dataset=DATASET, receipts=book
    ), book


def policy_for(*cases):
    return CompatibilityPolicy(
        version="fictional-w3/v1",
        declared_at=utc_now(),
        dataset_json=DATASET.model_dump_json(),
        acceptance_json=SPEC.model_dump_json(),
        budget_json="null",
        configurations=(ConfigurationMember(CONFIG.model_dump_json(), "fictional"),),
        tasks=tuple(
            TaskMember(str(c.task.task_id), c.task.task_group, "fictional")
            for c in cases
        ),
    )


def prediction(rows, policy, case, cutoff):
    return forecast(
        rows,
        policy=policy,
        task_id=case.task.task_id,
        run_id=case.run_id,
        configuration=CONFIG,
        cutoff=cutoff,
    )


def test_p1_through_p10_complete_lifecycle(tmp_path):
    repo = repository(tmp_path / "ledger.sqlite")
    previous = prepare(repo, tmp_path / "previous")
    target = prepare(repo, tmp_path / "target")
    subsequent = prepare(repo, tmp_path / "subsequent")
    policy = policy_for(previous, target, subsequent)
    execute(previous)
    assert run_acceptance(previous) == 0
    assess(previous, verify(previous))
    prior_bundle, _ = receive(previous)
    cutoff = utc_now()
    prior = portable.resolve_bundle(prior_bundle, cutoff=cutoff)
    issued = prediction(prior.observations, policy, target, cutoff)
    frozen = tmp_path / "forecast.json"
    checksum = freeze(frozen, issued)
    original = frozen.read_bytes()
    assert not any(o.run_id == target.run_id for o in repo.list_records(Outcome))
    assert repo.get(Run, target.run_id) is None
    for p in issued.predictions:
        assert (p.successes, p.failures, p.probability) == (1, 0, 2 / 3)
        assert p.lower == pytest.approx(math.sqrt(0.025))
        assert p.upper == pytest.approx(math.sqrt(0.975))
        assert p.evidence_runs == (str(previous.run_id),)
        assert p.evidence_keys == (prior.observations[0].stable_key,)
    execute(target)
    unknown, unverified = assess(target)
    assert unverified.outcome_status.value == "unknown"
    with pytest.raises(ValueError, match="verified binary"):
        score_frozen(frozen, checksum, unverified)
    assert run_acceptance(target) == 0
    evidence = verify(target)
    outcome, row = assess(target, evidence, unknown, persist=False)
    assert outcome.status.value == "success"
    assert row.eligible_for_configuration_learning
    assert row.evidence_ids == (evidence.verification_id,)
    assert row.attempt_id == target.attempt.attempt_id
    assert row.configuration == CONFIG
    assert row.metadata["configuration_provenance"] == "human_declaration"
    assert row.cost_usd is row.latency_seconds is CONFIG.model_version is None
    assert (
        canonical(repo.get(Task, target.task.task_id).model_dump(mode="json"))
        == target.contract
    )
    assert target.task.created_at < cutoff < target.run.started_at
    assert row.metadata["session_ids"] == [str(target.session.session_id)]
    events = [
        e for e in repo.list_records(Event) if e.session_id == target.session.session_id
    ]
    assert set(row.metadata["event_ids"]) == {str(e.event_id) for e in events}
    assert all(e.payload["native_observed_at"] is None for e in events)
    assert all(e.payload["timestamp_basis"] == "capture_receipt" for e in events)
    assert all(e.observed_at <= e.ingested_at <= row.recorded_at for e in events)
    assert events[-1].payload["native"]["usage"] == {
        "input_tokens": 12,
        "output_tokens": 4,
    }
    assert "Fictional completion claim" not in canonical(
        [e.model_dump(mode="json") for e in events]
    )
    assert evidence.metadata["report_observed_sha256"] == target.binding.report_sha256
    assert evidence.artifact_fingerprint == target.binding.artifact_fingerprint
    assert evidence.task_id == target.task.task_id and evidence.run_id == target.run_id
    assert evidence.acceptance_spec == SPEC
    # Score a resolved verified derivation before recording its learning row.
    assert (
        len(
            [
                o
                for o in repo.list_records(Observation, source_kind="real")
                if o.run_id == target.run_id
            ]
        )
        == 1
    )
    scores = score_frozen(frozen, checksum, row)
    assert scores["A"]["brier_score"] == pytest.approx(1 / 9)
    assert scores["A"]["log_loss"] == pytest.approx(-math.log(2 / 3))
    assert repo.add_observation(row) == row
    bundle, book = receive(target)
    assert bundle.verification_attempts == {
        evidence.verification_id: target.attempt.attempt_id
    }
    restored_bundle = portable.EvidenceBundle.model_validate_json(
        bundle.model_dump_json()
    )
    restored = repository(tmp_path / "restored.sqlite")
    portable.import_bundle(restored, restored_bundle)
    first = {
        kind: restored.list_records(kind, source_kind="real") for kind in portable.KINDS
    }
    portable.import_bundle(restored, restored_bundle)
    assert first == {
        kind: restored.list_records(kind, source_kind="real") for kind in portable.KINDS
    }
    replay = cli(
        "import",
        "codex",
        target.directory / "capture.jsonl",
        "--machine-id",
        "fictional-machine",
        "--database",
        repo.database.path,
    )
    assert replay["events_inserted"] == 0 and replay["events_duplicate"] == 5
    assert not replay["diagnostics"]
    assert (
        build_real_observation(
            repo, run_id=target.run_id, outcome_id=outcome.outcome_id, dataset=DATASET
        )
        == row
    )
    assert (
        portable.scoped_bundle(
            restored, task_id=target.task.task_id, dataset=DATASET, receipts=book
        )
        == bundle
    )
    now = utc_now()
    current = portable.resolve_bundle(restored_bundle, cutoff=now)
    assert len(current.observations) == 1
    resolved = current.observations[0]
    assert resolved.stable_key == row.stable_key
    assert resolved.evidence_ids == row.evidence_ids
    assert resolved.cost_usd is None and resolved.latency_seconds is None
    assert len(restored.list_records(Outcome)) == 2
    assert restored.list_run_session_links(
        target.run_id
    ) == repo.list_run_session_links(target.run_id)
    assert restored.list_task_session_links(
        target.task.task_id
    ) == repo.list_task_session_links(target.task.task_id)
    after = prediction(
        [*prior.observations, resolved, resolved], policy, subsequent, now
    )
    for p in after.predictions:
        assert (p.successes, p.failures, p.probability) == (2, 0, 3 / 4)
        assert p.lower == pytest.approx(0.025 ** (1 / 3))
        assert p.upper == pytest.approx(0.975 ** (1 / 3))
    assert dict(after.exclusions)["duplicate"] == 1
    assert issued.policy_fingerprint == policy.fingerprint
    assert (issued.dataset_json, issued.acceptance_json, issued.budget_json) == (
        DATASET.model_dump_json(),
        SPEC.model_dump_json(),
        "null",
    )
    assert issued.configuration_id == CONFIG.configuration_id
    # Reconstruct the original membership using saved scoped evidence and cutoff.
    reloaded_prior = portable.EvidenceBundle.model_validate_json(
        prior_bundle.model_dump_json()
    )
    reloaded_policy = TypeAdapter(CompatibilityPolicy).validate_json(
        TypeAdapter(CompatibilityPolicy).dump_json(policy)
    )
    rebuilt = prediction(
        portable.resolve_bundle(reloaded_prior, cutoff=cutoff).observations,
        reloaded_policy,
        target,
        cutoff,
    )
    assert rebuilt == issued
    assert json.loads(original) == json.loads(canonical(asdict(rebuilt)))
    assert not portable.resolve_bundle(restored_bundle, cutoff=cutoff).observations
    same_task = prediction([resolved], policy, target, now)
    assert dict(same_task.exclusions)["prediction_task"] == 1
    assert all(not p.evidence_keys for p in same_task.predictions)
    assert frozen.read_bytes() == original
    assert hashlib.sha256(original).hexdigest() == checksum


def test_receipt_snapshot_describes_actual_gate(tmp_path):
    case = execute(prepare(repository(tmp_path / "db.sqlite"), tmp_path / "case"))
    assess(case)
    # Empty-receipt legacy fixture also checks that descriptive metadata does not
    # claim receipt gating for callers of the legacy resolver.
    legacy = resolve_real_observations(case.repo, dataset=DATASET, cutoff=utc_now())
    assert legacy.method.startswith("declared-timestamp-as-of")
    bundle, _ = receive(case)
    state = portable.resolve_bundle(bundle, cutoff=utc_now())
    assert state.method.startswith("receipt-gated-declared-timestamp-as-of")
    assert (
        "Imported receipts are declarations, not authenticated time attestations"
        in state.availability_limitations
    )


def test_adapter_event_is_portable_without_erasing_attribution(tmp_path):
    case = execute(
        prepare(repository(tmp_path / "db.sqlite"), tmp_path / "case"),
        emitted_model="fictional-conflicting-model",
    )
    event = next(
        e for e in case.repo.list_records(Event) if e.event_type == "turn.started"
    )
    assert portable._public(event) == event


def test_receipt_metadata_without_adapter_dependency(tmp_path):
    repo = repository(tmp_path / "db.sqlite")
    task = repo.create_task(
        Task(description="Fictional empty scope", acceptance_spec=SPEC)
    )
    bundle = portable.scoped_bundle(repo, task_id=task.task_id, dataset=DATASET)
    snapshot = portable.resolve_bundle(bundle, cutoff=utc_now())
    assert snapshot.method.startswith("receipt-gated-declared-timestamp-as-of")


def fit(rows, cutoff=None):
    return BetaBernoulli.fit(
        rows, dataset=DATASET, cutoff=cutoff or utc_now(), acceptance_spec=SPEC
    ).predict(CONFIG, "fictional-arithmetic")


@pytest.mark.parametrize("broken", [False, True], ids=["P7-success", "N1-failure"])
def test_verified_label_counts_once(tmp_path, broken):
    case = execute(
        prepare(repository(tmp_path / "db.sqlite"), tmp_path / "case"), broken=broken
    )
    assert run_acceptance(case) == int(broken)
    _, row = assess(case, verify(case))
    assert row.outcome_status.value == ("failure" if broken else "success")
    assert row.eligible_for_configuration_learning
    bundle, _ = receive(case)
    snapshot = portable.resolve_bundle(bundle, cutoff=utc_now())
    posterior = fit([*snapshot.observations, *snapshot.observations])
    assert posterior.sample_count == 1
    assert (posterior.alpha, posterior.beta) == ((1, 2) if broken else (2, 1))
    assert posterior.success_probability == pytest.approx(1 / 3 if broken else 2 / 3)
    expected = (
        (1 - math.sqrt(0.975), 1 - math.sqrt(0.025))
        if broken
        else (math.sqrt(0.025), math.sqrt(0.975))
    )
    assert (posterior.lower, posterior.upper) == pytest.approx(expected)


def test_n2_completion_without_verification_is_unknown(tmp_path):
    case = execute(prepare(repository(tmp_path / "db.sqlite"), tmp_path / "case"))
    _, row = assess(case)
    assert row.outcome_status.value == "unknown"
    assert row.verification_status.value == "unverified"
    assert (
        row.label_available_at is None and not row.eligible_for_configuration_learning
    )
    assert fit([row]).sample_count == 0
    assert not case.repo.list_records(Verification)


@pytest.mark.parametrize(
    "field",
    ["artifact_fingerprint", "report_sha256", "acceptance_spec", "task_id", "run_id"],
)
def test_n3_mismatched_binding_rejected(tmp_path, field):
    case = execute(prepare(repository(tmp_path / "db.sqlite"), tmp_path / "case"))
    run_acceptance(case)
    values = case.binding.model_dump()
    if field == "acceptance_spec":
        values[field]["version"] = "wrong"
    elif field.endswith("_id"):
        values[field] = uuid4()
    else:
        values[field] = (
            "sha256:" if field == "artifact_fingerprint" else ""
        ) + "0" * 64
    case.binding = JUnitReportBinding.model_validate(values)
    with pytest.raises(ValueError):
        verify(case)
    assert not case.repo.list_records(Verification)


@pytest.mark.parametrize(
    "xml",
    [
        '<testsuite tests="1" failures="0" errors="0" skipped="0">'
        '<testcase classname="test_acceptance" name="test_positive"/></testsuite>',
        '<testsuite tests="2" failures="0" errors="0" skipped="1">'
        '<testcase classname="test_acceptance" name="test_positive"/>'
        '<testcase classname="test_acceptance" name="test_negative">'
        "<skipped/></testcase></testsuite>",
        "<testsuite",
        "<unsupported-format/>",
    ],
    ids=["missing-test", "skipped-test", "malformed", "unsupported"],
)
def test_n4_incomplete_report_cannot_learn(tmp_path, xml):
    case = execute(prepare(repository(tmp_path / "db.sqlite"), tmp_path / "case"))
    run_acceptance(case)
    # Deliberate synthetic corruption of a real report, with a matching digest:
    # rejection must follow completeness semantics, not only hash mismatch.
    case.report.write_text(xml)
    case.binding = case.binding.model_copy(
        update={"report_sha256": file_sha256(case.report)}
    )
    evidence = verify(case)
    assert evidence.result.value == "indeterminate"
    _, row = assess(case, evidence)
    assert (
        row.outcome_status.value == "unknown"
        and not row.eligible_for_configuration_learning
    )
    bundle, _ = receive(case)
    assert (
        fit(portable.resolve_bundle(bundle, cutoff=utc_now()).observations).sample_count
        == 0
    )


def test_n5_late_receipt_excluded_from_earlier_prediction(tmp_path, monkeypatch):
    repo = repository(tmp_path / "db.sqlite")
    previous = execute(prepare(repo, tmp_path / "previous"))
    target = prepare(repo, tmp_path / "target")
    run_acceptance(previous)
    assess(previous, verify(previous))
    policy = policy_for(previous, target)
    cutoff = utc_now()
    late = cutoff + timedelta(hours=1)
    monkeypatch.setattr(portable, "utc_now", lambda: late)
    bundle, _ = receive(previous)
    assert all(e.received_at == late for e in bundle.entries)
    assert all(e.observed_at < cutoff for e in repo.list_records(Event))
    early = portable.resolve_bundle(bundle, cutoff=cutoff)
    assert not early.observations
    issued = prediction(early.observations, policy, target, cutoff)
    assert all(
        (p.probability, p.successes, p.failures, p.evidence_keys) == (0.5, 0, 0, ())
        for p in issued.predictions
    )
    later = prediction(
        portable.resolve_bundle(bundle, cutoff=late).observations, policy, target, late
    )
    assert all(p.probability == 2 / 3 for p in later.predictions)


def test_n6_correction_changes_current_head_not_frozen_forecast(tmp_path):
    repo = repository(tmp_path / "db.sqlite")
    previous = execute(prepare(repo, tmp_path / "previous"))
    target = prepare(repo, tmp_path / "target")
    policy = policy_for(previous, target)
    run_acceptance(previous)
    old, _ = assess(previous, verify(previous))
    bundle, book = receive(previous)
    cutoff = utc_now()
    issued = prediction(
        portable.resolve_bundle(bundle, cutoff=cutoff).observations,
        policy,
        target,
        cutoff,
    )
    path = tmp_path / "frozen.json"
    checksum = freeze(path, issued)
    saved = path.read_bytes()
    # A valid later retraction to unknown needs no fabricated failing report.
    correction, row = assess(previous, previous=old)
    assert correction.supersedes_outcome_id == old.outcome_id
    updated, _ = receive(previous, book)
    current = portable.resolve_bundle(updated, cutoff=utc_now())
    assert current.assessments[0].outcome.outcome_id == correction.outcome_id
    assert current.observations[0].outcome_status.value == "unknown"
    assert fit(current.observations).sample_count == 0
    reconstructed = prediction(
        portable.resolve_bundle(updated, cutoff=cutoff).observations,
        policy,
        target,
        cutoff,
    )
    assert reconstructed == issued
    assert path.read_bytes() == saved and hashlib.sha256(saved).hexdigest() == checksum
    assert not row.eligible_for_configuration_learning


def test_n8_configuration_conflict_survives_portable_replay(tmp_path):
    case = execute(
        prepare(repository(tmp_path / "db.sqlite"), tmp_path / "case"),
        emitted_model="fictional-other-model",
    )
    run_acceptance(case)
    _, row = assess(case, verify(case))
    reason = "declared_configuration_conflicts_with_native_telemetry"
    assert reason in row.metadata["exclusions"]
    assert row.attribution_status.value == "incomplete"
    assert not row.eligible_for_configuration_learning
    bundle, _ = receive(case)
    restored = portable.resolve_bundle(bundle, cutoff=utc_now()).observations[0]
    assert reason in restored.metadata["exclusions"]
    assert (
        restored.metadata["configuration_conflict_event_ids"]
        == row.metadata["configuration_conflict_event_ids"]
    )
    assert fit([restored]).sample_count == 0


def test_n9_unrelated_task_is_excluded_from_bundle_and_forecast(tmp_path):
    repo = repository(tmp_path / "db.sqlite")
    unrelated = execute(prepare(repo, tmp_path / "unrelated"))
    selected = execute(prepare(repo, tmp_path / "selected"))
    target = prepare(repo, tmp_path / "target")
    for case in (unrelated, selected):
        run_acceptance(case)
        assess(case, verify(case))
    bundle, _ = receive(selected)
    assert str(unrelated.task.task_id) not in bundle.model_dump_json()
    assert str(unrelated.run_id) not in bundle.model_dump_json()
    other_bundle, _ = receive(unrelated)
    policy = policy_for(selected, target)
    cutoff = utc_now()
    rows = [
        *portable.resolve_bundle(bundle, cutoff=cutoff).observations,
        *portable.resolve_bundle(other_bundle, cutoff=cutoff).observations,
    ]
    issued = prediction(rows, policy, target, cutoff)
    assert dict(issued.exclusions)["not_admitted_by_policy"] == 1
    assert all(p.evidence_runs == (str(selected.run_id),) for p in issued.predictions)


@pytest.mark.parametrize(
    "field",
    [
        "bytes",
        "task_id",
        "run_id",
        "configuration_id",
        "acceptance_json",
        "dataset_json",
        "budget_json",
    ],
)
def test_n10_frozen_tampering_prevents_scoring(tmp_path, field):
    repo = repository(tmp_path / "db.sqlite")
    case = prepare(repo, tmp_path / "case")
    policy = policy_for(case)
    issued = prediction([], policy, case, utc_now())
    path = tmp_path / "frozen.json"
    checksum = freeze(path, issued)
    execute(case)
    run_acceptance(case)
    _, row = assess(case, verify(case))
    values = asdict(issued)
    if field == "bytes":
        path.chmod(0o600)
        path.write_text(path.read_text() + " ")
    else:
        if field == "acceptance_json":
            values[field] = SPEC.model_copy(
                update={"version": "wrong"}
            ).model_dump_json()
        elif field == "dataset_json":
            values[field] = DATASET.model_copy(
                update={"dataset_id": "wrong"}
            ).model_dump_json()
        elif field == "budget_json":
            values[field] = '{"max_tokens":100}'
        else:
            values[field] = str(uuid4())
        # Even a separately hashed forecast for a different target cannot score
        # this observation. The original file/digest remain unchanged.
        path = tmp_path / "wrong-binding.json"
        payload = canonical(values) + "\n"
        path.write_text(payload)
        checksum = hashlib.sha256(payload.encode()).hexdigest()
    with pytest.raises(
        ValueError, match="digest mismatch|forecast execution|target, dataset or budget"
    ):
        score_frozen(path, checksum, row)


@pytest.mark.parametrize(
    "mutation",
    [
        "payload-extra",
        "native-text",
        "raw-text",
        "wrong-source",
        "wrong-version",
        "native-time",
        "session-extra",
    ],
)
def test_capture_projection_rejects_unsupported_content(tmp_path, mutation):
    case = execute(prepare(repository(tmp_path / "db.sqlite"), tmp_path / "case"))
    event = case.repo.list_records(Event)[0]
    values = event.model_dump()
    if mutation == "session-extra":
        values = case.session.model_dump()
        values["metadata"]["private_note"] = "fictional text"
        record = Session.model_validate(values)
    else:
        if mutation == "payload-extra":
            values["payload"]["private_note"] = "fictional text"
        elif mutation == "native-text":
            values["payload"]["native"]["text"] = "fictional text"
        elif mutation == "raw-text":
            values["raw_payload"]["text"] = "fictional text"
        elif mutation == "wrong-source":
            values["source"] = "unsupported"
        elif mutation == "wrong-version":
            values["adapter_version"] = "unsupported"
        else:
            values["payload"]["native_observed_at"] = utc_now().isoformat()
        record = Event.model_validate(values)
    with pytest.raises(ValueError, match="unsupported|metadata-only"):
        portable._public(record)


def test_metadata_bundle_passes_pure_privacy_screen(tmp_path):
    case = execute(prepare(repository(tmp_path / "db.sqlite"), tmp_path / "case"))
    run_acceptance(case)
    assess(case, verify(case))
    bundle, book = receive(case)
    reloaded = portable.ReceiptBook.model_validate_json(book.model_dump_json())
    reloaded.capture(bundle)
    assert reloaded == book
    guard = runpy.run_path(str(Path(__file__).parents[2] / "scripts/privacy_guard.py"))
    assert not guard["secret_reasons"](bundle.model_dump_json().encode())
    assert not guard["content_reasons"](bundle.model_dump_json().encode())
