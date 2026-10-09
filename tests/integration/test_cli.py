"""Exercise CLI behavior and the installed console entry point."""

import json
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from model_learner import __version__
from model_learner.cli import app

runner = CliRunner()


def test_help() -> None:
    result = runner.invoke(app, ["--help"])

    assert result.exit_code == 0
    assert "model-learner" in result.output
    assert "--help" in result.output
    assert "--version" in result.output


def test_version() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert result.output.strip() == f"model-learner {__version__}"


def test_no_arguments_shows_help() -> None:
    result = runner.invoke(app, [])

    assert result.exit_code == 2
    assert "Usage:" in result.output


@pytest.mark.parametrize("arguments", [["--unknown-option"], ["learn"]])
def test_invalid_arguments(arguments: list[str]) -> None:
    result = runner.invoke(app, arguments)

    assert result.exit_code == 2
    assert "Error" in result.output


@pytest.mark.parametrize("flag", ["--help", "--version"])
def test_installed_entry_point(flag: str, tmp_path: Path) -> None:
    executable = Path(sys.executable).parent / "model-learner"
    result = subprocess.run(
        [str(executable), flag],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    if flag == "--version":
        assert result.stdout.strip() == f"model-learner {__version__}"
    else:
        assert "--version" in result.stdout
    assert list(tmp_path.iterdir()) == []


def test_m1_task_and_session_workflow(tmp_path: Path) -> None:
    database = tmp_path / "learner.sqlite3"

    initialized = runner.invoke(app, ["init", "--database", str(database)])
    task_result = runner.invoke(
        app,
        [
            "task",
            "create",
            "parser repair",
            "--acceptance-id",
            "pytest",
            "--acceptance-version",
            "1",
            "--database",
            str(database),
        ],
    )
    session_result = runner.invoke(
        app,
        [
            "session",
            "register",
            "--source",
            "codex",
            "--native-session-id",
            "thread-1",
            "--database",
            str(database),
        ],
    )

    assert initialized.exit_code == 0, initialized.output
    assert task_result.exit_code == 0, task_result.output
    assert session_result.exit_code == 0, session_result.output
    task = json.loads(task_result.output)
    session = json.loads(session_result.output)
    attached = runner.invoke(
        app,
        [
            "task",
            "attach-session",
            task["task_id"],
            session["session_id"],
            "--database",
            str(database),
        ],
    )
    listed = runner.invoke(app, ["task", "list", "--database", str(database)])
    shown = runner.invoke(
        app,
        [
            "records",
            "show",
            "session",
            session["session_id"],
            "--database",
            str(database),
        ],
    )

    assert attached.exit_code == 0, attached.output
    assert listed.exit_code == 0, listed.output
    assert json.loads(listed.output)[0]["task_id"] == task["task_id"]
    assert shown.exit_code == 0, shown.output
    assert json.loads(shown.output)["native_session_id"] == "thread-1"
