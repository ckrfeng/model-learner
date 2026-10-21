"""Reviewed synthetic W4A preparation only; no agents, private ledgers or Git writes.

The public manifest contains hashes and proposed settings, never hidden solutions.
Protected acceptance is deliberately outside this committed test suite.
"""

import ast
import hashlib
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import pytest

from model_learner.domain.models import (
    AcceptanceSpec,
    DatasetReference,
    ExecutionConfiguration,
    Observation,
    ResourceBudget,
)
from model_learner.learn.estimator import BetaBernoulli
from model_learner.learn.prospective import (
    CompatibilityPolicy,
    ConfigurationMember,
    TaskMember,
    forecast,
)

ROOT = Path(__file__).resolve().parents[2]
MANIFEST = ROOT / "docs/experiments/w4a_preparation.json"
START = datetime(2026, 1, 1, tzinfo=UTC)
CUTOFF = START + timedelta(hours=1)
PRIOR_TASK = UUID(int=701)


def manifest():
    return json.loads(MANIFEST.read_text())


def scenario():
    m = manifest()
    configs = [ExecutionConfiguration(**a["configuration"]) for a in m["arms"]]
    dataset = DatasetReference(
        source_kind="simulated",
        dataset_id="w4a-public-policy-check",
        dataset_version="1",
    )
    target = AcceptanceSpec(
        **{k: m["acceptance"][k] for k in ("identifier", "version")}
    )
    budget = ResourceBudget(max_duration_seconds=600)
    task_id = UUID(m["task"]["task_id"])
    policy = CompatibilityPolicy(
        "w4a-synthetic-check/v1",
        START,
        dataset.model_dump_json(),
        target.model_dump_json(),
        budget.model_dump_json(),
        tuple(
            ConfigurationMember(c.model_dump_json(), a["configuration_family"])
            for c, a in zip(configs, m["arms"], strict=True)
        ),
        tuple(
            TaskMember(str(t), "transactional-dag", "graph-state-machines")
            for t in (task_id, PRIOR_TASK)
        ),
    )
    return configs, dataset, target, budget, task_id, policy


def test_starting_source_and_instructions_match_frozen_hashes():
    files = manifest()["public_starting_files"]
    assert set(files) == {"tests/fixtures/w4a/TASK.md", "tests/fixtures/w4a/planner.py"}
    for rel, expected in files.items():
        path = ROOT / rel
        assert path.is_file() and not path.is_symlink()
        assert hashlib.sha256(path.read_bytes()).hexdigest() == expected
    module = ast.parse((ROOT / "tests/fixtures/w4a/planner.py").read_text())
    # Opening/importing the starter has no I/O, subprocesses or launcher hooks.
    assert all(isinstance(n, (ast.Expr, ast.ClassDef)) for n in module.body)
    assert all(
        isinstance(n.value, ast.Constant)
        for n in module.body
        if isinstance(n, ast.Expr)
    )


def test_no_implicit_launch_or_false_enforcement():
    m = manifest()
    assert m["launch_authorized"] is False
    assert m["auto_execute"] is False
    assert m["model_executions"] == m["ledger_writes"] == 0
    assert m["verdict"] == "PARTIAL"
    assert m["containment"]["read_denial"] == "unproven"
    assert m["resources"]["wall_stop_enforced_for_agents"] is False
    assert m["resources"]["token_ceiling"] is None
    assert m["resources"]["dollar_ceiling"] is None
    assert m["forecast_design"]["cutoff"] is None
    assert m["forecast_design"]["dataset"]["source_kind"] == "benchmark"
    assert m["forecast_design"]["preparation_source_kind"] == "simulated"


def test_exact_model_effort_and_task_associations():
    m = manifest()
    configs, *_ = scenario()
    assert [(c.model, c.reasoning_level) for c in configs] == [
        ("gpt-6-luna", "low"),
        ("gpt-6.1-sol", "low"),
        ("gpt-6.1-sol", "high"),
    ]
    assert len({c.configuration_id for c in configs}) == 3
    assert len({a["configuration_family"] for a in m["arms"]}) == 3
    for arm, config in zip(m["arms"], configs, strict=True):
        assert arm["task_id"] == m["task"]["task_id"]
        assert config.model_version is None
        assert arm["requested_effort_supported"]
        assert arm["authenticated_availability"] == "unknown"
        assert config.model in arm["launch_argv_proposal"]
        assert (
            f'model_reasoning_effort="{config.reasoning_level}"'
            in arm["launch_argv_proposal"]
        )


def test_acceptance_identity_and_protected_source_separation():
    m = manifest()
    ids = m["acceptance"]["required_test_ids"]
    assert len(ids) == len(set(ids)) == 15
    assert all(x.startswith("test_acceptance.Acceptance::test_") for x in ids)
    assert all(p.startswith("protected/") for p in m["protected_files"])
    assert {Path(p).name for p in m["public_starting_files"]} == {
        "TASK.md",
        "planner.py",
    }
    assert m["initial_git"]["pre_existing_edits"] == []
    assert m["initial_git"]["staged"] == []


def test_proposed_settings_have_six_prior_only_predictors_without_writes():
    configs, dataset, target, budget, task_id, policy = scenario()
    for i, config in enumerate(configs):
        result = forecast(
            [],
            policy=policy,
            task_id=task_id,
            run_id=UUID(int=800 + i),
            configuration=config,
            cutoff=CUTOFF,
        )
        assert all(
            p.probability == 0.5 and not p.evidence_keys for p in result.predictions
        )
        for aggregation in ("global", "per_arm", "unpooled"):
            posterior = BetaBernoulli.fit(
                [],
                dataset=dataset,
                cutoff=CUTOFF,
                acceptance_spec=target,
                resource_budget=budget,
                aggregation=aggregation,
            ).predict(config, "transactional-dag")
            assert posterior.success_probability == 0.5
            assert posterior.sample_count == 0
            assert posterior.lower == pytest.approx(0.025)
            assert posterior.upper == pytest.approx(0.975)


@pytest.mark.parametrize(
    "leak", ["target-task", "future-decision", "future-label", "future-record"]
)
def test_same_task_and_future_evidence_excluded_for_all_arms(leak):
    configs, dataset, target, budget, task_id, policy = scenario()
    values = dict(
        source_kind="simulated",
        dataset=dataset,
        source_record_id="w4a-synthetic-leak",
        task_id=PRIOR_TASK,
        run_id=UUID(int=900),
        task_group="transactional-dag",
        configuration=configs[0],
        acceptance_spec=target,
        resource_budget=budget,
        attribution_status="single_configuration",
        eligible_for_configuration_learning=True,
        outcome_status="success",
        verification_status="verified",
        decision_at=START + timedelta(seconds=1),
        recorded_at=START + timedelta(seconds=2),
        label_available_at=START + timedelta(seconds=2),
    )
    if leak == "target-task":
        values["task_id"] = task_id
    else:
        field = {
            "future-decision": "decision_at",
            "future-label": "label_available_at",
            "future-record": "recorded_at",
        }[leak]
        values[field] = CUTOFF + timedelta(seconds=1)
        values["recorded_at"] = CUTOFF + timedelta(seconds=2)
        if leak == "future-decision":
            values["label_available_at"] = CUTOFF + timedelta(seconds=2)
    row = Observation(**values)
    for i, config in enumerate(configs):
        kwargs = dict(
            policy=policy,
            task_id=task_id,
            run_id=UUID(int=800 + i),
            configuration=config,
            cutoff=CUTOFF,
        )
        assert (
            forecast([row], **kwargs).predictions == forecast([], **kwargs).predictions
        )
        # Baselines need the SAME explicit target-task exclusion before fit;
        # the bare estimator does not know which task is held out.
        eligible_universe = [r for r in [row] if r.task_id != task_id]
        for aggregation in ("global", "per_arm"):
            posterior = BetaBernoulli.fit(
                eligible_universe,
                dataset=dataset,
                cutoff=CUTOFF,
                acceptance_spec=target,
                resource_budget=budget,
                aggregation=aggregation,
            ).predict(config, "transactional-dag")
            assert posterior.sample_count == 0
