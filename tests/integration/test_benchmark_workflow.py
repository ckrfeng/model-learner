"""Only public controlled candidate code runs; never a coding agent or paid API."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

import model_learner.benchmark as benchmark
from model_learner.adapters.codex import capture_codex_stream
from model_learner.domain.models import (
    Attempt,
    Event,
    ExecutionConfiguration,
    Observation,
    OutcomeStatus,
    Run,
    RunState,
    VerificationStatus,
    utc_now,
)
from model_learner.storage.database import Database, Repository

FIXTURES = Path(__file__).parents[1] / "fixtures/benchmark"


def prepare(tmp_path: Path, task_id: str = "clamp"):
    protected = tmp_path / "protected"
    protected.mkdir()
    (protected / "README.md").write_text("public controlled source\n")
    parent = tmp_path / "disposable"
    parent.mkdir()
    return benchmark.prepare_benchmark(
        parent=parent,
        protected_repository=protected,
        task_id=task_id,
        configuration=ExecutionConfiguration(provider="fixture", model="fixture-model"),
        isolation_mechanism="controlled fixture code; no agent launched",
        execution_origin="fixture",
    )


def capture(prepared, *, native_model: str = "fixture-model", malformed=False):
    path = prepared.control / "capture.jsonl"
    with path.open("x") as stream:
        capture_codex_stream(
            [
                json.dumps(
                    {
                        "type": "thread.started",
                        "thread_id": "public-controlled-thread",
                        "model": native_model,
                        "model_provider": "fixture",
                    }
                ),
                json.dumps(
                    {
                        "type": "item.completed",
                        "item": {
                            "id": "public-item",
                            "type": "agent_message",
                            "text": "PRIVATE_SELF_REPORT_NOT_ACCEPTANCE",
                        },
                    }
                ),
                '{"type":"turn.completed","usage":{"input_tokens":30}}',
            ],
            stream,
            source_version="fixture-v1",
        )
        if malformed:
            stream.write('{"secret":"PRIVATE_MALFORMED"}\n')
    return path


def run_acceptance(prepared):
    return subprocess.run(
        [sys.executable, "-I", str(prepared.control / "acceptance.py")],
        cwd=prepared.control,
        env={},
        capture_output=True,
        timeout=15,
        check=False,
    )


@pytest.mark.parametrize("task_id", ["clamp", "duration"])
def test_fixture_task_to_independent_junit_and_preserved_telemetry(
    tmp_path: Path, task_id: str
) -> None:
    prepared = prepare(tmp_path, task_id)
    before = (prepared.protected_repository / "README.md").read_bytes()
    started = utc_now()
    (prepared.workspace / "solution.py").write_bytes(
        (FIXTURES / f"{task_id}_solution.py").read_bytes()
    )
    captured = capture(prepared)
    ended = utc_now()
    artifact = benchmark.snapshot_candidate(prepared.root)
    # Changes in the mutable workspace after freezing cannot change tested bytes.
    (prepared.workspace / "solution.py").write_text("raise RuntimeError('changed')\n")
    process = run_acceptance(prepared)
    assert process.returncode == 0, process.stderr
    result = benchmark.finalize_benchmark(
        prepared.root,
        started_at=started,
        ended_at=ended,
        capture=captured,
        test_completed=True,
        test_exit_code=process.returncode,
        test_generated_at=utc_now(),
        isolation_confirmed=True,
    )
    assert result.outcome.status is OutcomeStatus.SUCCESS
    assert result.outcome.verification_status is VerificationStatus.VERIFIED
    assert result.verification.artifact_reference == str(artifact)
    assert result.configuration == prepared.configuration
    assert result.telemetry_events == 3
    assert result.telemetry_diagnostics == 0
    assert not result.reasons
    assert result.dataset.dataset_id.endswith(":fixture")
    assert result.dataset.source_kind.value == "benchmark"
    assert not result.learning_observation_created
    repository = Repository(Database(result.ledger))
    assert len(repository.list_records(Event)) == 3
    assert repository.list_records(Attempt)[0].configuration == prepared.configuration
    assert repository.list_records(Observation, source_kind="benchmark") == []
    assert "PRIVATE" not in result.ledger.read_bytes().decode(errors="ignore")
    assert (prepared.protected_repository / "README.md").read_bytes() == before
    with pytest.raises(ValueError, match="already been finalized"):
        benchmark.finalize_benchmark(
            prepared.root, started_at=started, ended_at=ended, isolation_confirmed=True
        )


def test_agent_self_report_and_unimplemented_code_do_not_verify_success(
    tmp_path: Path,
) -> None:
    prepared = prepare(tmp_path)
    started = utc_now()
    captured = capture(prepared)
    ended = utc_now()
    benchmark.snapshot_candidate(prepared.root)
    process = run_acceptance(prepared)
    assert process.returncode == 1
    result = benchmark.finalize_benchmark(
        prepared.root,
        started_at=started,
        ended_at=ended,
        capture=captured,
        test_completed=True,
        test_exit_code=process.returncode,
        isolation_confirmed=True,
    )
    assert result.outcome.status is OutcomeStatus.FAILURE
    assert result.outcome.verification_status is VerificationStatus.VERIFIED


def test_candidate_cannot_monkeypatch_controller_acceptance(tmp_path: Path) -> None:
    prepared = prepare(tmp_path)
    (prepared.workspace / "solution.py").write_text(
        "import builtins\nbuiltins.eval = lambda *args, **kwargs: True\n"
    )
    started, ended = utc_now(), utc_now()
    benchmark.snapshot_candidate(prepared.root)
    process = run_acceptance(prepared)
    assert process.returncode == 1
    result = benchmark.finalize_benchmark(
        prepared.root,
        started_at=started,
        ended_at=ended,
        test_completed=True,
        test_exit_code=process.returncode,
        isolation_confirmed=True,
    )
    assert result.outcome.status is OutcomeStatus.FAILURE
    assert result.verification.metadata["test_results"]["counts"]["failures"] == 6


@pytest.mark.parametrize(
    "state", [RunState.FINISHED, RunState.UNKNOWN, RunState.ABANDONED]
)
def test_incomplete_or_unverifiable_runs_remain_unknown(
    tmp_path: Path, state: RunState
) -> None:
    prepared = prepare(tmp_path)
    started = utc_now()
    result = benchmark.finalize_benchmark(
        prepared.root,
        started_at=started,
        ended_at=utc_now(),
        state=state,
        isolation_confirmed=True,
    )
    assert result.run.state is state
    assert result.outcome.status is OutcomeStatus.UNKNOWN
    assert result.outcome.verification_status is VerificationStatus.UNVERIFIED
    assert result.verification is None
    assert "candidate_snapshot_missing" in result.reasons
    assert "acceptance_report_missing" in result.reasons
    assert "agent_telemetry_missing" in result.reasons
    if state is not RunState.FINISHED:
        assert "agent_execution_incomplete" in result.reasons


def test_bad_reports_and_attribution_conflicts_are_retained(tmp_path: Path) -> None:
    prepared = prepare(tmp_path)
    started = utc_now()
    captured = capture(prepared, native_model="different-model", malformed=True)
    ended = utc_now()
    benchmark.snapshot_candidate(prepared.root)
    (prepared.control / "report.xml").write_text("<malformed")
    result = benchmark.finalize_benchmark(
        prepared.root,
        started_at=started,
        ended_at=ended,
        capture=captured,
        test_completed=True,
        test_exit_code=0,
        isolation_confirmed=True,
    )
    assert result.outcome.status is OutcomeStatus.UNKNOWN
    assert "malformed_xml" in result.reasons
    assert "telemetry_incomplete" in result.reasons
    assert "configuration_declaration_conflicts_with_telemetry" in result.reasons
    assert result.configuration.model == "fixture-model"
    repository = Repository(Database(result.ledger))
    native = repository.list_records(Event)[0].payload["native"]
    assert native["model"] == "different-model"


def test_rejected_verifier_does_not_leave_partial_run_and_can_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prepared = prepare(tmp_path)
    (prepared.workspace / "solution.py").write_bytes(
        (FIXTURES / "clamp_solution.py").read_bytes()
    )
    started, ended = utc_now(), utc_now()
    benchmark.snapshot_candidate(prepared.root)
    assert run_acceptance(prepared).returncode == 0
    original = benchmark.verify_junit

    def reject(*args, **kwargs):
        raise ValueError("report changed while reading")

    monkeypatch.setattr(benchmark, "verify_junit", reject)
    options = {
        "started_at": started,
        "ended_at": ended,
        "test_completed": True,
        "test_exit_code": 0,
        "isolation_confirmed": True,
    }
    with pytest.raises(ValueError, match="report changed"):
        benchmark.finalize_benchmark(prepared.root, **options)
    repository = Repository(Database(prepared.control / "ledger.sqlite3"))
    assert repository.list_records(Run) == []
    assert repository.list_records(Attempt) == []
    assert not (prepared.control / "binding.json").exists()
    assert not (prepared.control / "result.json").exists()
    monkeypatch.setattr(benchmark, "verify_junit", original)
    result = benchmark.finalize_benchmark(prepared.root, **options)
    assert result.outcome.status is OutcomeStatus.SUCCESS
