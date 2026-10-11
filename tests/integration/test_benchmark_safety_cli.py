"""Diagnostic CLI cannot authorize real execution or conceal unavailable probes."""

import json

import pytest
from typer.testing import CliRunner

from model_learner.benchmark.isolation import ContainmentProbe
from model_learner.cli import app
from model_learner.domain.models import utc_now


@pytest.mark.parametrize(
    "status,exit_code", [("probe_passed", 0), ("unavailable", 1), ("failed", 1)]
)
def test_probe_cli_reports_actual_readiness(monkeypatch, status, exit_code):
    result = ContainmentProbe(
        status=status,
        reason="controlled_probe_receipt",
        platform="controlled",
        observed_at=utc_now().isoformat(),
    )
    monkeypatch.setattr(
        "model_learner.benchmark.isolation.probe_macos_containment", lambda: result
    )
    invocation = CliRunner().invoke(app, ["benchmark", "isolation-probe"])
    assert invocation.exit_code == exit_code
    receipt = json.loads(invocation.output)
    assert receipt["status"] == status
    assert receipt["real_execution_ready"] is False
