"""Fresh fictional canaries; negative controls, never a sandbox or agent launcher.

All contents are authored here. No private files, sockets, credentials, protected
W4A source or external network facilities are read. Passing means the documented
same-user boundary FAILURE was reproduced, not that containment passed.
"""

import json
import subprocess
import sys

import pytest

from model_learner.benchmark.isolation import require_supported_real_containment

CATEGORIES = (
    "hidden-tests",
    "reference-oracle",
    "other-arm",
    "forecasts",
    "private-evidence",
    "fake-credentials",
    "unrelated-host",
)


def test_same_user_can_read_all_seven_categories_and_escape_workspace(tmp_path):
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()
    for name in ("TASK.md", "planner.py"):
        (workspace / name).write_text("# public fictional starting file\n")
    for category in CATEGORIES:
        (outside / category).write_text("fictional canary\n")
    (workspace / "outside-link").symlink_to(outside / CATEGORIES[0])
    script = """
import json, subprocess, sys
from pathlib import Path
categories = json.loads(sys.argv[1])
assert all(Path(name).read_text() for name in ('TASK.md', 'planner.py'))
Path('allowed-output').write_text('fictional output')
assert all((Path('../outside') / name).read_text() == 'fictional canary\\n'
           for name in categories)
Path('../outside/forbidden-output').write_text('fictional output')
assert Path('outside-link').read_text() == 'fictional canary\\n'
child = subprocess.run(
    [sys.executable, '-I', '-c',
     "from pathlib import Path; assert Path('../outside/hidden-tests').read_text()"],
    env={}, timeout=3, check=False)
assert child.returncode == 0
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, json.dumps(CATEGORIES)],
        cwd=workspace,
        env={},
        stdin=subprocess.DEVNULL,
        capture_output=True,
        timeout=5,
    )
    assert result.returncode == 0, result.stderr
    assert (workspace / "allowed-output").is_file()
    assert (outside / "forbidden-output").is_file()
    assert all(
        (outside / name).read_text() == "fictional canary\n" for name in CATEGORIES
    )


def test_negative_controls_cannot_authorize_real_collection():
    with pytest.raises(ValueError, match="no supported verified containment"):
        require_supported_real_containment()
