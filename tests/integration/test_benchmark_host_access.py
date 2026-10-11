"""Demonstrate current worker access using only public synthetic host canaries."""

import subprocess
import sys
from xml.etree import ElementTree as ET

from model_learner.benchmark.fixtures import acceptance_source, get_task


def test_python_isolated_worker_can_read_and_write_outside_task_directory(tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "synthetic-host"
    workspace.mkdir()
    outside.mkdir()
    private_canary = outside / "private-canary.txt"
    source_canary = outside / "source-canary.txt"
    private_canary.write_text("public synthetic private canary\n")
    source_canary.write_text("public synthetic source baseline\n")
    # Trusted test code touches only the two synthetic files created above.
    # Returning correct answers does not stop these outside-directory accesses.
    (workspace / "candidate.py").write_text(
        "from pathlib import Path\n"
        f"assert Path({str(private_canary)!r}).read_text() == "
        "'public synthetic private canary\\n'\n"
        f"Path({str(source_canary)!r}).write_text('public synthetic changed\\n')\n"
        "def clamp(value, lower, upper):\n"
        "    if lower > upper:\n"
        "        raise ValueError\n"
        "    return min(upper, max(lower, value))\n"
    )
    (workspace / "acceptance.py").write_text(acceptance_source(get_task("clamp")))
    completed = subprocess.run(
        [sys.executable, "-I", str(workspace / "acceptance.py")],
        cwd=workspace,
        env={},
        capture_output=True,
        timeout=15,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    report = ET.parse(workspace / "report.xml").getroot()
    assert report.attrib["failures"] == report.attrib["errors"] == "0"
    assert private_canary.read_text() == "public synthetic private canary\n"
    assert source_canary.read_text() == "public synthetic changed\n"
