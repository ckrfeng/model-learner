"""Smoke tests for the installed package and its metadata."""

from importlib.metadata import version

import model_learner


def test_package_import_and_version() -> None:
    assert model_learner.__version__ == version("model-learner")
