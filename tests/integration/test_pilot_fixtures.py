"""Exercise trusted controllers only with public hand-written local candidates."""

import subprocess
import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from model_learner.benchmark import cleanup_benchmark, prepare_benchmark
from model_learner.benchmark.fixtures import acceptance_source, get_task
from model_learner.benchmark.pilot import PILOT_TASK_IDS
from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    ExecutionConfiguration,
)
from model_learner.learn.task_state import evaluate_task_state

SOLUTION = Path(__file__).parents[1] / "fixtures/benchmark/pilot_solutions.py"


@pytest.mark.parametrize("task_id", PILOT_TASK_IDS)
@pytest.mark.parametrize("candidate", ["reference", "unimplemented", "wrong"])
def test_all_pilot_tasks_have_independent_acceptance(tmp_path, task_id, candidate):
    fixture = get_task(task_id)
    if candidate == "reference":
        source = SOLUTION.read_text()
    elif candidate == "unimplemented":
        source = fixture.initial_source
    else:
        source = f"def {fixture.function}(*args):\n    return 999999\n"
    (tmp_path / "candidate.py").write_text(source)
    (tmp_path / "acceptance.py").write_text(acceptance_source(fixture))
    process = subprocess.run(
        [sys.executable, "-I", str(tmp_path / "acceptance.py")],
        cwd=tmp_path,
        env={},
        capture_output=True,
        timeout=20,
        check=False,
    )
    report = ET.parse(tmp_path / "report.xml").getroot()
    assert tuple(
        f"{case.attrib['classname']}::{case.attrib['name']}" for case in report
    ) == (fixture.required_test_ids)
    assert len(report) == len(fixture.checks)
    assert report.attrib["errors"] == "0"
    if candidate == "reference":
        assert process.returncode == 0, process.stderr
        assert report.attrib["failures"] == "0"
    else:
        assert process.returncode == 1
        assert int(report.attrib["failures"]) == len(fixture.checks)


@pytest.mark.parametrize("task_id", PILOT_TASK_IDS)
def test_paired_preparation_retains_identical_inputs_and_separate_control(
    tmp_path, task_id
):
    protected, parent = tmp_path / "protected", tmp_path / "disposable"
    protected.mkdir()
    parent.mkdir()
    (protected / "source.py").write_text("public baseline\n")
    pair = [
        prepare_benchmark(
            parent=parent,
            protected_repository=protected,
            task_id=task_id,
            configuration=ExecutionConfiguration(
                model="controlled-model", reasoning_level=reasoning
            ),
            isolation_mechanism="controlled fixture; no real agent launched",
            execution_origin="fixture",
        )
        for reasoning in ("low", "medium")
    ]
    a, b = pair
    assert a.root != b.root
    assert a.fixture_fingerprint == b.fixture_fingerprint
    assert a.task.acceptance_spec == b.task.acceptance_spec
    assert a.configuration != b.configuration
    for name in ("TASK.txt", "solution.py"):
        assert (a.workspace / name).read_bytes() == (b.workspace / name).read_bytes()
    assert not (a.workspace / "acceptance.py").exists()
    assert not (b.workspace / "acceptance.py").exists()
    for prepared in pair:
        cleanup_benchmark(prepared.root)


def test_no_examples_reports_insufficient_benchmark_evidence_without_scores():
    start = datetime(2026, 1, 1, tzinfo=UTC)
    report = evaluate_task_state(
        (),
        dataset=DatasetReference(
            source_kind="benchmark", dataset_id="pilot:real", dataset_version="1"
        ),
        acceptance_spec=AcceptanceSpec(identifier="public-coding-clamp", version="1"),
        train_until=start,
        evaluation_at=start + timedelta(days=1),
    )
    assert report.training_count == report.scored_count == 0
    assert report.method["min_training"] == 30
    assert report.method["min_scored"] == 20
    assert all(
        row.status == "insufficient_data" and row.brier_score is None
        for row in report.variants
    )
    assert all(row.brier_improvement is None for row in report.comparisons)
