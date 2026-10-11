"""Opt-in actual boundary test; ordinary test runs never launch Docker."""

import os

import pytest

from model_learner.benchmark.isolation import require_supported_real_containment
from model_learner.benchmark.offline import (
    SUPPORTED_SYNTHETIC_IMAGE,
    probe_offline_isolation,
)


def test_offline_diagnostic_cannot_unlock_real_collection():
    result = probe_offline_isolation()
    assert result.real_execution_ready is False
    with pytest.raises(ValueError, match="no supported verified containment"):
        require_supported_real_containment()


@pytest.mark.skipif(
    os.environ.get("MODEL_LEARNER_OFFLINE_DOCKER_TEST") != "1",
    reason="actual Docker Desktop experiment requires explicit opt-in",
)
def test_actual_docker_offline_boundary_and_watchdog():
    result = probe_offline_isolation(SUPPORTED_SYNTHETIC_IMAGE)
    assert result.status == "validated", result.model_dump_json()
    assert result.checks and all(result.checks.values())
    assert result.host_mounts == ()
    assert result.artifact_sha256 is not None
    assert (
        result.artifact_extraction == "controller_tar_stream_after_fixed_worker_ready"
    )
    assert result.checks["pids_cap_enforced"]
    assert result.checks["workspace_size_enforced"]
    assert result.checks["watchdog_deadline_enforced"]
    assert result.checks["watchdog_descendants_destroyed"]
    assert result.real_execution_ready is False
    with pytest.raises(ValueError, match="no supported verified containment"):
        require_supported_real_containment()
