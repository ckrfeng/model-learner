"""W6A synthetic-only real-contract/CLI tests in disposable storage.

Reuses the reviewed W2 independent JUnit pass/fail/unknown fixture and W4A.2
fictional benchmark exporter. No agent, historical ledger, network or Git writes.
"""

import hashlib
import json
from uuid import UUID

import pytest
from typer.testing import CliRunner

from model_learner.cli import app
from model_learner.domain.models import (
    ExecutionConfiguration,
    Outcome,
    ResourceBudget,
    Task,
    utc_now,
)
from model_learner.learn.advisory import AdvisoryInput, AdvisoryRequest, advise
from model_learner.learn.prospective import (
    CompatibilityPolicy,
    ConfigurationMember,
    TaskMember,
)
from model_learner.storage import evidence as portable
from tests.integration import test_portable_evidence as w2
from tests.integration.test_portable_evidence import (
    CUTOFF,
    DATASET,
    LATE,
    START,
    bundle_for,
)
from tests.unit.test_advisory import predictions, request
from tests.unit.test_prospective import row


@pytest.fixture
def portable_scenario(tmp_path):
    return w2.scenario.__wrapped__(tmp_path)


def real_request(scenario, cutoff=CUTOFF):
    _, prior, _, _, attempts, *_ = scenario
    configurations = tuple(
        {a.configuration.configuration_id: a.configuration for a in attempts}.values()
    )
    task = Task(
        task_id=UUID(int=900),
        description="Fictional W6A held-out target",
        acceptance_spec=prior.acceptance_spec,
        task_group=prior.task_group,
        created_at=START,
    )
    policy = CompatibilityPolicy(
        "w6a-fictional/v1",
        START,
        DATASET.model_dump_json(),
        prior.acceptance_spec.model_dump_json(),
        "null",
        tuple(
            ConfigurationMember(c.model_dump_json(), str(i))
            for i, c in enumerate(configurations)
        ),
        tuple(
            TaskMember(str(t.task_id), t.task_group, "fictional") for t in (prior, task)
        ),
    )
    return AdvisoryRequest(
        task=task, candidates=configurations, policy=policy, cutoff=cutoff
    )


def test_receipt_gated_success_failure_and_unknown(portable_scenario, monkeypatch):
    bundle = bundle_for(portable_scenario, monkeypatch)
    earlier = advise(real_request(portable_scenario), bundles=[bundle])
    current = advise(real_request(portable_scenario, LATE), bundles=[bundle])
    assert predictions(earlier)["A"]["probability"] == 2 / 3
    assert predictions(earlier, 1)["A"]["probability"] == 0.5
    assert predictions(current, 1)["A"]["probability"] == 1 / 3
    assert current["eligible_source_count"] == 2
    assert current["exclusions"]["missing_or_nonbinary_label"] == 1
    evidence = predictions(current)["A"]["evidence"]
    assert len(evidence) == 1 and evidence[0]["verification_ids"]
    assert current["availability"]["method"] == "receipt-gated-scoped-resolution/v1"


@pytest.mark.parametrize("receipt", ["late", "missing"])
def test_receipt_not_source_time_controls_availability(
    portable_scenario, monkeypatch, receipt
):
    bundle = bundle_for(portable_scenario, monkeypatch)
    bundle = bundle.model_copy(
        update={
            "entries": tuple(
                e.model_copy(
                    update={"received_at": LATE if receipt == "late" else None}
                )
                for e in bundle.entries
            )
        }
    )
    result = advise(real_request(portable_scenario), bundles=[bundle])
    assert result["eligible_source_count"] == 0
    assert predictions(result)["A"]["probability"] == 0.5
    assert result["exclusions"][f"{receipt}_receipt_entries"] == len(bundle.entries)


def test_correction_changes_current_not_earlier_advice(portable_scenario, monkeypatch):
    from model_learner.observations import build_real_observation

    repo, task, _, runs, _, _, corrected = portable_scenario
    original = bundle_for(portable_scenario, monkeypatch)
    early = advise(real_request(portable_scenario), bundles=[original])
    invalidation = repo.add_outcome(
        Outcome(
            run_id=runs[0].run_id,
            status="unknown",
            verification_status="unverified",
            assessment_source="human",
            recorded_at=LATE,
            supersedes_outcome_id=corrected[0].outcome_id,
        )
    )
    build_real_observation(
        repo,
        run_id=runs[0].run_id,
        outcome_id=invalidation.outcome_id,
        dataset=DATASET,
        recorded_at=LATE,
    )
    # Preserve existing first receipts and receive only new records now.
    book = portable.ReceiptBook(
        receipts={
            portable.key(e.parse()): (e.sha256, e.received_at) for e in original.entries
        }
    )
    monkeypatch.setattr(portable, "utc_now", lambda: LATE)
    book.capture(portable.scoped_bundle(repo, task_id=task.task_id, dataset=DATASET))
    latest = portable.scoped_bundle(
        repo, task_id=task.task_id, dataset=DATASET, receipts=book
    )
    assert advise(real_request(portable_scenario), bundles=[latest]) == early | {
        "exclusions": advise(real_request(portable_scenario), bundles=[latest])[
            "exclusions"
        ]
    }
    assert (
        predictions(advise(real_request(portable_scenario, LATE), bundles=[latest]))[
            "A"
        ]["probability"]
        == 0.5
    )
    assert advise(real_request(portable_scenario), bundles=[original]) == early


def test_real_raw_rows_rejected_even_if_caller_says_eligible(portable_scenario):
    repo, *_ = portable_scenario
    with pytest.raises(ValueError, match="receipt evidence"):
        advise(
            real_request(portable_scenario), observations=repo.list_observations("real")
        )


def test_duplicate_bundle_replay_and_conflicting_snapshots(
    portable_scenario, monkeypatch
):
    bundle = bundle_for(portable_scenario, monkeypatch)
    req = real_request(portable_scenario)
    result = advise(req, bundles=[bundle, bundle])
    assert result["eligible_source_count"] == 1
    assert result["exclusions"]["duplicate_bundle"] == 1
    different = bundle.model_copy(update={"entries": bundle.entries[:-1]})
    with pytest.raises(ValueError, match="conflicting evidence snapshots"):
        advise(req, bundles=[bundle, different])


def test_read_only_source_database_and_bundle(portable_scenario, monkeypatch, tmp_path):
    bundle = bundle_for(portable_scenario, monkeypatch)
    source = tmp_path / "source.sqlite"

    def files():
        return {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in source.parent.glob("source.sqlite*")
        }

    before = files()
    encoded = bundle.model_dump_json()
    first = advise(real_request(portable_scenario), bundles=[bundle])
    assert advise(real_request(portable_scenario), bundles=[bundle]) == first
    assert files() == before
    assert bundle.model_dump_json() == encoded


def test_privacy_projection_and_scope(portable_scenario, monkeypatch):
    _, _, unrelated, *_ = portable_scenario
    result = advise(
        real_request(portable_scenario),
        bundles=[bundle_for(portable_scenario, monkeypatch)],
    )
    output = json.dumps(result)
    assert str(unrelated.task_id) not in output
    for value in (
        "artifact-0.txt",
        "report-0.xml",
        "Fictional selected task",
        "fixture::case",
        "native_session_id",
        "source_path",
    ):
        assert value not in output


def test_complete_benchmark_receipts_never_upgrade_budgeted_evidence(
    tmp_path, monkeypatch
):
    import model_learner.benchmark.receipts as receipts
    from model_learner.benchmark.evidence import export_benchmark_evidence
    from model_learner.benchmark.receipts import (
        BenchmarkReceiptBook,
        benchmark_receipt_bundle,
    )
    from tests.integration.test_benchmark_evidence import fixture

    prepared, _, _ = fixture(
        tmp_path,
        resource_budget=ResourceBudget(max_duration_seconds=600),
        configuration=ExecutionConfiguration(
            provider="fixture",
            model="fixture-model",
            harness="fixture-harness",
            harness_version="1",
            reasoning_level="low",
        ),
    )
    exported = export_benchmark_evidence(prepared.root)
    bundle = benchmark_receipt_bundle(prepared.root, exported)
    now = utc_now()
    monkeypatch.setattr(receipts, "utc_now", lambda: now)
    view = (
        BenchmarkReceiptBook(target=bundle.target)
        .capture(bundle)
        .as_of(bundle, cutoff=now)
    )
    assert view.fully_available
    assert "budget_measurements_not_supported" in view.learning_exclusions
    target = Task(
        task_id=UUID(int=901),
        description="Fictional benchmark target",
        acceptance_spec=prepared.task.acceptance_spec,
        task_group=prepared.task.task_group,
        resource_budget=exported.observation.resource_budget,
        created_at=START,
    )
    policy = CompatibilityPolicy(
        "w6a-benchmark/v1",
        START,
        prepared.dataset.model_dump_json(),
        target.acceptance_spec.model_dump_json(),
        target.resource_budget.model_dump_json(),
        (ConfigurationMember(prepared.configuration.model_dump_json(), "fixture"),),
        tuple(
            TaskMember(str(t.task_id), t.task_group, "fixture")
            for t in (target, prepared.task)
        ),
    )
    req = AdvisoryRequest(
        task=target, policy=policy, candidates=(prepared.configuration,), cutoff=now
    )
    report = advise(req, observations=[exported.observation])
    assert report["eligible_source_count"] == 0
    assert report["exclusions"]["budget_measurements_not_supported"] == 1
    assert predictions(report)["A"]["probability"] == 0.5
    assert report["resource_budget"]["max_duration_seconds"] == 600


@pytest.mark.parametrize("has_evidence", [False, True])
def test_cli_complete_versioned_invocation(tmp_path, has_evidence):
    payload = AdvisoryInput(
        request=request(), observations=(row(1),) if has_evidence else ()
    )
    path = tmp_path / "input.json"
    path.write_text(payload.model_dump_json())
    before = path.read_bytes()
    result = CliRunner().invoke(app, ["learn", "advise", "--input-file", str(path)])
    assert result.exit_code == 0, result.output
    output = json.loads(result.output)
    assert output["version"] == "configuration-advisory/v1"
    assert predictions(output)["A"]["probability"] == (2 / 3 if has_evidence else 0.5)
    assert output["advisory"]["status"] == "abstain"
    assert path.read_bytes() == before
    assert set(p.name for p in tmp_path.iterdir()) == {"input.json"}


def test_cli_invalid_contract_does_not_echo_payload(tmp_path):
    path = tmp_path / "invalid.json"
    path.write_text(
        json.dumps({"fictional-private-marker": "fictional-payload-marker"})
    )
    result = CliRunner().invoke(app, ["learn", "advise", "--input-file", str(path)])
    assert result.exit_code != 0
    assert "fictional-payload-marker" not in result.output


def test_real_cli_uses_receipt_resolver(tmp_path, portable_scenario, monkeypatch):
    payload = AdvisoryInput(
        request=real_request(portable_scenario),
        bundles=(bundle_for(portable_scenario, monkeypatch),),
    )
    path = tmp_path / "real-contract-input.json"
    path.write_text(payload.model_dump_json())
    result = CliRunner().invoke(app, ["learn", "advise", "--input-file", str(path)])
    assert result.exit_code == 0, result.output
    assert json.loads(result.output) == advise(payload.request, bundles=payload.bundles)


def test_public_executable_example_calculates_both_cases():
    from scripts.advisory_example import example

    cold = example()
    prior = example(with_evidence=True)
    report = advise(prior.request, observations=prior.observations)
    assert all(
        predictions(advise(cold.request), i)["A"]["probability"] == 0.5
        for i in range(3)
    )
    assert [predictions(report, i)["A"]["probability"] for i in range(3)] == [
        2 / 3,
        1 / 3,
        0.5,
    ]
