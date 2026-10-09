"""Exercise CLI behavior and the installed console entry point."""

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
