"""Fictional real-contract M6-A evidence, reusing synthetic portable fixtures only."""

import hashlib

import pytest

from model_learner.learn.partial_pooling import PartialPoolingRequest, partial_pool
from tests.integration import test_portable_evidence as portable
from tests.integration.test_advisory import real_request
from tests.integration.test_portable_evidence import CUTOFF, LATE, bundle_for


@pytest.fixture
def scenario(tmp_path):
    return portable.scenario.__wrapped__(tmp_path)


def request(scenario, cutoff=CUTOFF):
    return PartialPoolingRequest(
        **real_request(scenario, cutoff).model_dump(exclude={"decision_policy"})
    )


def test_receipt_complete_earlier_later_and_source_bytes(
    scenario, monkeypatch, tmp_path
):
    bundle = bundle_for(scenario, monkeypatch)
    source_files = sorted(tmp_path.glob("source.sqlite*"))
    before = {p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in source_files}
    encoded = bundle.model_dump_json()
    early = partial_pool(request(scenario), bundles=[bundle])
    later = partial_pool(request(scenario, LATE), bundles=[bundle])
    assert early.eligible_source_count == 1
    assert later.eligible_source_count == 2
    assert sum(c.successes for c in later.cells) == 1
    assert sum(c.failures for c in later.cells) == 1
    assert dict(later.exclusions)["missing_or_nonbinary_label"] == 1
    assert early.availability_method == "receipt-gated-scoped-resolution/v1"
    assert all(c.evidence[0].verification_ids for c in later.cells if c.evidence)
    assert partial_pool(request(scenario), bundles=[bundle]) == early
    assert bundle.model_dump_json() == encoded
    assert {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in tmp_path.glob("source.sqlite*")
    } == before
    output = early.model_dump_json()
    for marker in (
        "artifact-0.txt",
        "report-0.xml",
        "Fictional selected task",
        "fixture::case",
        "source_path",
        "native_session_id",
    ):
        assert marker not in output


@pytest.mark.parametrize("kind", ["missing", "late"])
def test_missing_or_late_receipts_never_train(scenario, monkeypatch, kind):
    bundle = bundle_for(scenario, monkeypatch)
    changed = bundle.model_copy(
        update={
            "entries": tuple(
                e.model_copy(
                    update={"received_at": None if kind == "missing" else LATE}
                )
                for e in bundle.entries
            )
        }
    )
    result = partial_pool(request(scenario), bundles=[changed])
    assert result.eligible_source_count == 0
    assert dict(result.exclusions)[f"{kind}_receipt_entries"] == len(bundle.entries)
    assert all(
        c.status == "prior-only" and c.posterior.mean == 0.5 for c in result.cells
    )
    assert result.availability_limitations


def test_raw_real_rows_malformed_and_conflicting_bundles_fail_closed(
    scenario, monkeypatch
):
    repo, *_ = scenario
    with pytest.raises(ValueError, match="scoped receipt evidence"):
        partial_pool(request(scenario), observations=repo.list_observations("real"))
    bundle = bundle_for(scenario, monkeypatch)
    different = bundle.model_copy(update={"entries": bundle.entries[:-1]})
    with pytest.raises(ValueError, match="conflicting evidence"):
        partial_pool(request(scenario), bundles=[bundle, different])
    entry = bundle.entries[0].model_copy(update={"sha256": "0" * 64})
    malformed = bundle.model_copy(update={"entries": (entry, *bundle.entries[1:])})
    with pytest.raises(ValueError, match="digest mismatch"):
        partial_pool(request(scenario), bundles=[malformed])
    once = partial_pool(request(scenario), bundles=[bundle])
    replay = partial_pool(request(scenario), bundles=[bundle, bundle])
    assert once.cells == replay.cells and once.domains == replay.domains
    assert dict(replay.exclusions)["duplicate_bundle"] == 1


def test_bundle_dataset_and_target_admission(scenario, monkeypatch):
    bundle = bundle_for(scenario, monkeypatch)
    req = request(scenario)
    other = bundle.model_copy(
        update={
            "dataset": bundle.dataset.model_copy(
                update={"dataset_version": "unadmitted"}
            )
        }
    )
    result = partial_pool(req, bundles=[other])
    assert dict(result.exclusions) == {"other_dataset_bundle": 1}
    # Reusing the actual source Task as prediction target excludes all its arms.
    source = scenario[1]
    target_request = PartialPoolingRequest(
        task=source, candidates=req.candidates, policy=req.policy, cutoff=req.cutoff
    )
    result = partial_pool(target_request, bundles=[bundle])
    assert result.eligible_source_count == 0
    assert dict(result.exclusions) == {"unadmitted_or_target_task_bundle": 1}
