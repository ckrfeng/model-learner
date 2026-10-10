"""M1.1 storage/JSONL integrate with the pure learner without schema changes."""

from datetime import UTC, datetime, timedelta
from pathlib import Path

from model_learner.domain.models import (
    AcceptanceSpec,
    Attempt,
    AttributionStatus,
    DatasetReference,
    ExecutionConfiguration,
    Observation,
    Outcome,
    Run,
    Task,
    Verification,
)
from model_learner.learn import BetaBernoulli, evaluate
from model_learner.simulate import SimulationConfig, generate
from model_learner.storage.database import Database, Repository
from model_learner.storage.jsonl import export_jsonl, import_jsonl


def repository(path: Path) -> Repository:
    database = Database(path)
    database.initialize()
    return Repository(database)


def test_simulation_reimport_storage_and_jsonl_leave_predictions_identical(
    tmp_path: Path,
) -> None:
    result = generate(SimulationConfig(seed=10, count=30, unknown_probability=0.2))
    first = repository(tmp_path / "first.sqlite")
    for row in result.observations:
        first.add_observation(row)
        first.add_observation(row)
    rows = first.list_observations(
        "simulated", dataset_id=result.truth.dataset.dataset_id
    )
    assert len(rows) == 30
    assert sorted(item.stable_key for item in rows) == sorted(
        item.stable_key for item in result.observations
    )
    jsonl = tmp_path / "observations.jsonl"
    assert export_jsonl(first, Observation, jsonl, source_kind="simulated") == 30
    assert "success_probability" not in jsonl.read_text()
    second = repository(tmp_path / "second.sqlite")
    assert import_jsonl(second, jsonl) == 30
    assert import_jsonl(second, jsonl) == 30
    assert len(second.list_observations("simulated")) == 30
    kwargs = dict(
        dataset=result.truth.dataset,
        cutoff=result.observations[-1].recorded_at,
        acceptance_spec=AcceptanceSpec(
            identifier="simulated-binary-success", version="1"
        ),
    )
    generated = BetaBernoulli.fit(result.observations, **kwargs)
    restored = BetaBernoulli.fit(second.list_observations("simulated"), **kwargs)
    assert generated.training_summary == restored.training_summary
    for row in result.observations:
        assert generated.predict(row.configuration, row.task_group) == restored.predict(
            row.configuration, row.task_group
        )


def test_multiple_dataset_versions_remain_separate_in_storage_and_evaluation(
    tmp_path: Path,
) -> None:
    first = generate(SimulationConfig(count=20, dataset_version="1"))
    second = generate(SimulationConfig(count=20, dataset_version="2"))
    store = repository(tmp_path / "mixed.sqlite")
    for row in (*first.observations, *second.observations):
        store.add_observation(row)
    all_rows = store.list_observations("simulated")
    kwargs = dict(
        dataset=first.truth.dataset,
        train_until=first.observations[10].decision_at,
        evaluation_at=first.observations[-1].recorded_at,
        acceptance_spec=AcceptanceSpec(
            identifier="simulated-binary-success", version="1"
        ),
        truth=first.truth,
    )
    report = evaluate(all_rows, **kwargs)
    direct = evaluate(first.observations, **kwargs)
    assert report.baselines == direct.baselines
    assert report.exclusions["other_dataset"] == 20
    assert store.list_observations("real") == []


def test_verified_real_evidence_is_learnable_without_mixing_simulator_rows(
    tmp_path: Path,
) -> None:
    store = repository(tmp_path / "real.sqlite")
    decision = datetime(2026, 1, 1, tzinfo=UTC)
    label_at = decision + timedelta(minutes=1)
    target = AcceptanceSpec(identifier="fixture-tests", version="1")
    task = store.create_task(
        Task(
            description="Synthetic ledger fixture, not a captured execution",
            acceptance_spec=target,
            created_at=decision,
        )
    )
    run = store.create_run(Run(task_id=task.task_id, started_at=decision))
    configuration = ExecutionConfiguration(provider="fixture", model="arm-a")
    attempt = store.create_attempt(
        Attempt(run_id=run.run_id, configuration=configuration, started_at=decision)
    )
    evidence = store.add_verification(
        Verification(
            task_id=task.task_id,
            run_id=run.run_id,
            acceptance_spec=target,
            verifier_type="fixture",
            result="pass",
            observed_at=label_at,
        )
    )
    outcome = store.add_outcome(
        Outcome(
            run_id=run.run_id,
            status="success",
            verification_status="verified",
            evidence_ids=(evidence.verification_id,),
            assessment_source="fixture",
            recorded_at=label_at,
        )
    )
    dataset = DatasetReference(
        source_kind="real", dataset_id="fixture-real-contract", dataset_version="1"
    )
    observation = Observation(
        source_kind="real",
        dataset=dataset,
        task_group="fixture-group",
        configuration=configuration,
        task_id=task.task_id,
        run_id=run.run_id,
        attempt_id=attempt.attempt_id,
        outcome_id=outcome.outcome_id,
        outcome_status="success",
        verification_status="verified",
        evidence_ids=(evidence.verification_id,),
        acceptance_spec=target,
        attribution_status=AttributionStatus.SINGLE_CONFIGURATION,
        eligible_for_configuration_learning=True,
        decision_at=decision,
        label_available_at=label_at,
        recorded_at=label_at,
    )
    store.add_observation(observation)
    synthetic = generate(SimulationConfig(count=4))
    for row in synthetic.observations:
        store.add_observation(row)
    model = BetaBernoulli.fit(
        [*store.list_observations("real"), *store.list_observations("simulated")],
        dataset=dataset,
        cutoff=label_at,
        acceptance_spec=target,
    )
    assert model.predict(configuration, "fixture-group").success_probability == 2 / 3
    assert model.training_summary.eligible_label_count == 1
    assert model.training_summary.excluded["other_dataset"] == 4
