"""Benchmark staging must fail closed on path and trusted-input changes."""

import json
from pathlib import Path

import pytest

from model_learner.benchmark import (
    cleanup_benchmark,
    finalize_benchmark,
    list_tasks,
    load_benchmark,
    prepare_benchmark,
    snapshot_candidate,
)
from model_learner.domain.models import ExecutionConfiguration, utc_now


def prepare(tmp_path: Path, **overrides):
    protected = tmp_path / "protected"
    protected.mkdir(exist_ok=True)
    (protected / "source.py").write_text("public baseline\n")
    parent = tmp_path / "disposable"
    parent.mkdir(exist_ok=True)
    return prepare_benchmark(
        **(
            {
                "parent": parent,
                "task_id": "clamp",
                "configuration": ExecutionConfiguration(model="fixture-model"),
                "protected_repository": protected,
                "isolation_mechanism": "controlled fixture; no agent launched",
                "execution_origin": "fixture",
            }
            | overrides
        )
    )


def test_staging_is_reproducible_public_and_separate(tmp_path: Path) -> None:
    first = prepare(tmp_path)
    second = prepare(tmp_path)
    assert first.root != second.root
    assert first.fixture_fingerprint == second.fixture_fingerprint
    assert first.configuration == second.configuration
    assert first.dataset.source_kind.value == "benchmark"
    assert first.execution_origin == "fixture"
    assert first.protected_repository not in first.root.parents
    assert (first.workspace / "solution.py").read_bytes() == (
        second.workspace / "solution.py"
    ).read_bytes()
    assert not (first.workspace / "acceptance.py").exists()
    assert load_benchmark(first.root) == first
    assert {task.task_id for task in list_tasks()} == {"clamp", "duration"}
    cleanup_benchmark(first.root)
    assert not first.root.exists()
    assert second.root.exists()
    assert first.protected_repository.exists()


@pytest.mark.parametrize("placement", ["same", "inside", "ancestor", "symlink"])
def test_preparation_rejects_repository_overlapping_parents(
    tmp_path: Path, placement: str
) -> None:
    prepared = prepare(tmp_path)
    protected = prepared.protected_repository
    if placement == "same":
        parent = protected
    elif placement == "inside":
        parent = protected / "nested"
        parent.mkdir()
    elif placement == "ancestor":
        parent = tmp_path
    else:
        parent = tmp_path / "linked"
        parent.symlink_to(protected, target_is_directory=True)
    with pytest.raises(ValueError, match="separate"):
        prepare(tmp_path, parent=parent)


@pytest.mark.parametrize("name", ["solution.py", "control", "workspace"])
def test_symlink_inputs_are_refused(tmp_path: Path, name: str) -> None:
    prepared = prepare(tmp_path)
    if name == "solution.py":
        target = prepared.workspace / name
        target.unlink()
        target.symlink_to(prepared.protected_repository / "source.py")
    else:
        target = prepared.root / name
        target.rename(prepared.root / f"original-{name}")
        target.symlink_to(prepared.protected_repository, target_is_directory=True)
    with pytest.raises(ValueError, match="non-symlink|real directories"):
        snapshot_candidate(prepared.root)


def test_repository_mutation_prevents_snapshot_and_finalize(tmp_path: Path) -> None:
    prepared = prepare(tmp_path)
    start = utc_now()
    (prepared.protected_repository / "source.py").write_text("changed\n")
    with pytest.raises(ValueError, match="protected repository changed"):
        snapshot_candidate(prepared.root)
    with pytest.raises(ValueError, match="protected repository changed"):
        finalize_benchmark(
            prepared.root,
            started_at=start,
            ended_at=utc_now(),
            isolation_confirmed=True,
        )


@pytest.mark.parametrize("field", ["fixture", "acceptance", "criterion", "root"])
def test_trusted_mutations_rejected(tmp_path: Path, field: str) -> None:
    prepared = prepare(tmp_path)
    if field == "acceptance":
        (prepared.control / "acceptance.py").write_text("print('pass')\n")
    else:
        manifest = prepared.control / "manifest.json"
        data = json.loads(manifest.read_text())
        if field == "fixture":
            data["fixture_fingerprint"] = "a" * 64
        elif field == "criterion":
            data["task"]["metadata"]["junit_verifier"]["required_test_ids"] = ["x::y"]
        else:
            data["root"] = str(prepared.protected_repository)
        manifest.write_text(json.dumps(data))
    with pytest.raises(ValueError):
        load_benchmark(prepared.root)


def test_snapshot_is_exclusive_and_hash_bound(tmp_path: Path) -> None:
    prepared = prepare(tmp_path)
    start, end = utc_now(), utc_now()
    frozen = snapshot_candidate(prepared.root)
    with pytest.raises(FileExistsError):
        snapshot_candidate(prepared.root)
    frozen.chmod(0o600)
    frozen.write_text("tampered\n")
    with pytest.raises(ValueError, match="frozen candidate changed"):
        finalize_benchmark(
            prepared.root, started_at=start, ended_at=end, isolation_confirmed=True
        )


def test_no_containment_confirmation_or_running_state_is_refused(
    tmp_path: Path,
) -> None:
    prepared = prepare(tmp_path)
    start = utc_now()
    with pytest.raises(ValueError, match="containment"):
        finalize_benchmark(prepared.root, started_at=start, ended_at=utc_now())
    with pytest.raises(ValueError, match="stop the agent"):
        from model_learner.domain.models import RunState

        finalize_benchmark(
            prepared.root,
            started_at=start,
            ended_at=utc_now(),
            state=RunState.RUNNING,
            isolation_confirmed=True,
        )
