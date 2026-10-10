"""Deterministic checks do not execute commands or retain artifact contents."""

import hashlib
from pathlib import Path

import pytest

from model_learner.observations import data_quality_report
from model_learner.verification import (
    digest_criterion,
    file_sha256,
    validate_fingerprint,
)


@pytest.mark.parametrize("invalid", ["", "a" * 63, "A" * 64, "x" * 64, None])
def test_digest_criterion_rejects_invalid_digest(invalid: str) -> None:
    with pytest.raises(ValueError, match="64 lowercase"):
        digest_criterion(invalid)


@pytest.mark.parametrize("invalid", [None, "a" * 64, "sha1:" + "a" * 64])
def test_artifact_fingerprint_requires_algorithm(invalid: str) -> None:
    with pytest.raises(ValueError, match="sha256"):
        validate_fingerprint(invalid)


def test_file_hash_is_exact_bytes_and_read_only(tmp_path: Path) -> None:
    artifact = tmp_path / "answer.txt"
    contents = b"private example\n\x00"
    artifact.write_bytes(contents)
    stat = artifact.stat()
    assert file_sha256(artifact) == hashlib.sha256(contents).hexdigest()
    assert artifact.read_bytes() == contents
    assert artifact.stat().st_mtime_ns == stat.st_mtime_ns
    assert digest_criterion(file_sha256(artifact)) == {
        "version": "file-sha256/v1",
        "expected_sha256": hashlib.sha256(contents).hexdigest(),
    }
    with pytest.raises(ValueError, match="regular file"):
        file_sha256(tmp_path)


def test_empty_data_quality_is_explicit() -> None:
    assert data_quality_report([]) == {
        "observation_count": 0,
        "unit": "assessment_derivation",
        "datasets": [],
        "counts": {},
    }


def test_hash_rejects_file_modified_during_read(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    artifact = tmp_path / "changing.txt"
    artifact.write_bytes(b"initial")
    real_digest = hashlib.file_digest

    def mutate_after_read(file, algorithm):
        result = real_digest(file, algorithm)
        artifact.write_bytes(b"changed bytes")
        return result

    monkeypatch.setattr(hashlib, "file_digest", mutate_after_read)
    with pytest.raises(ValueError, match="changed while hashing"):
        file_sha256(artifact)
