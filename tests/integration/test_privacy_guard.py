"""Exercise the real index, committed trees and hooks using public synthetic data."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[2]
GUARD = ROOT / "scripts/privacy_guard.py"


def run(repo: Path, *args: str, env: dict[str, str] | None = None):
    return subprocess.run(
        args, cwd=repo, capture_output=True, text=True, check=False, env=env
    )


def git(repo: Path, *args: str):
    result = run(repo, "git", *args)
    assert result.returncode == 0, result.stderr
    return result


@pytest.fixture
def repo(tmp_path: Path) -> Path:
    git(tmp_path, "init", "-q")
    git(tmp_path, "config", "user.name", "Synthetic Privacy Test")
    git(tmp_path, "config", "user.email", "test@example.invalid")
    git(tmp_path, "config", "commit.gpgsign", "false")
    git(tmp_path, "config", "core.hooksPath", ".githooks")
    return tmp_path


def stage(repo: Path, path: str, content: str | bytes) -> Path:
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(content.encode() if isinstance(content, str) else content)
    git(repo, "add", "-f", "--", path)
    return target


def check(repo: Path, *args: str):
    return run(repo, sys.executable, str(GUARD), *(args or ("--staged",)))


@pytest.mark.parametrize(
    ("path", "content"),
    [
        ("src/ordinary.py", "def answer():\n    return 42\n"),
        ("docs/guide.md", "# Public guide\nKeep private data locally.\n"),
        ("tests/fixtures/synthetic.json", '{"source_kind":"simulated","count":3}'),
        (".env.example", 'API_KEY="<your-api-key>"\nPASSWORD="change_me"\n'),
        ("tests/fixtures/example.csv", "kind,value\nsimulated,3\n"),
        ("spaces and\ttabs\n雪.py", "answer = 42\n"),
    ],
)
def test_safe_source_docs_fixtures_and_names(repo, path, content):
    stage(repo, path, content)
    result = check(repo)
    assert result.returncode == 0, result.stdout
    assert "1 files inspected; 0 rejected" in result.stdout


def test_guard_and_its_synthetic_test_source_are_accepted(repo):
    stage(repo, "scripts/privacy_guard.py", GUARD.read_bytes())
    stage(repo, "tests/integration/test_privacy_guard.py", Path(__file__).read_bytes())
    assert check(repo).returncode == 0


@pytest.mark.parametrize(
    "path",
    [
        ".model-learner/annotations/private.md",
        ".venv/local.py",
        ".uv-cache/cache",
        ".tools/local",
        ".mypy_cache/local",
        "private-evaluations/results.json",
        "session-dumps/session.json",
        "transcripts/session.txt",
        "credentials/file",
        ".codex/sessions/session.jsonl",
        ".aws/credentials",
        ".ssh/id_ed25519",
        ".env",
        "nested/.env.production",
        "ledger.sqlite",
        "ledger.sqlite3",
        "ledger.db",
        "ledger.sqlite3-wal",
        "ledger.db-shm",
        "local.safetensors",
        "local.gguf",
        "trace.log",
        "auth.json",
        "cookies.txt",
        ".DS_Store",
        "rollout-example.jsonl",
        "secrets/with spaces\n雪.txt",
    ],
)
def test_force_added_prohibited_paths_preserve_local_data(repo, path):
    gitignore = repo / ".gitignore"
    shutil.copyfile(ROOT / ".gitignore", gitignore)
    target = repo / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("harmless synthetic private artifact")
    assert run(repo, "git", "check-ignore", "--", path).returncode == 0
    git(repo, "add", "-f", "--", path)
    before = (target.read_bytes(), target.stat().st_mtime_ns)
    result = check(repo)
    assert result.returncode == 1
    assert "REJECT" in result.stdout
    assert (target.read_bytes(), target.stat().st_mtime_ns) == before
    assert "harmless synthetic private artifact" not in result.stdout + result.stderr


def synthetic_token() -> str:
    # Construct only a public canary; no literal provider token in the test source.
    return "gh" + "p_" + "Ab9X" * 10


@pytest.mark.parametrize("path", ["ordinary.py", "notes.md", ".env.example"])
def test_secret_in_any_public_file_is_rejected_without_value(repo, path):
    token = synthetic_token()
    stage(repo, path, f'TOKEN = "{token}"\n')
    result = check(repo)
    assert result.returncode == 1
    assert "provider credential" in result.stdout
    assert token not in result.stdout + result.stderr


@pytest.mark.parametrize(
    "content",
    [
        b"SQLite format 3\0" + b"synthetic" * 10,
        b"public\0binary",
        b"version https://git-lfs.github.com/spec/v1\noid sha256:synthetic\nsize 1\n",
        '{"role":"user","content":"PUBLIC SYNTHETIC MESSAGE"}',
        '{"type":"session_meta","payload":{"id":"synthetic"}}\n',
        '{"type":"service_account","private_key":"synthetic"}',
    ],
)
def test_content_not_extension_controls_rejection(repo, content):
    stage(repo, "innocent.txt", content)
    result = check(repo)
    assert result.returncode == 1
    assert "PUBLIC SYNTHETIC MESSAGE" not in result.stdout + result.stderr


def test_index_bytes_are_checked_instead_of_worktree(repo):
    token = synthetic_token()
    file = stage(repo, "source.py", f'TOKEN = "{token}"\n')
    file.write_text("safe = True\n")
    assert check(repo).returncode == 1
    git(repo, "add", "source.py")
    file.write_text(f'TOKEN = "{token}"\n')
    assert check(repo).returncode == 0


def test_replacement_objects_cannot_hide_published_blob_bytes(repo):
    stage(repo, "unsafe.py", f'TOKEN = "{synthetic_token()}"\n')
    unsafe_oid = git(repo, "rev-parse", ":unsafe.py").stdout.strip()
    stage(repo, "safe.py", "safe = True\n")
    safe_oid = git(repo, "rev-parse", ":safe.py").stdout.strip()
    git(repo, "replace", unsafe_oid, safe_oid)
    assert check(repo).returncode == 1
    git(repo, "commit", "-qm", "Synthetic replaced blob")
    assert check(repo, "--tree", "HEAD").returncode == 1


def test_entire_index_checks_previously_committed_files(repo):
    stage(repo, "safe.py", "safe = True\n")
    git(repo, "commit", "-qm", "Synthetic safe commit")
    assert check(repo).returncode == 0
    stage(repo, "local.sqlite", "synthetic artifact")
    git(repo, "commit", "-qm", "Synthetic prohibited commit")
    stage(repo, "safe.py", "safe = False\n")
    assert check(repo).returncode == 1
    git(repo, "rm", "--cached", "local.sqlite")
    assert check(repo).returncode == 0
    assert (repo / "local.sqlite").exists()


def test_committed_tree_validation_catches_hook_bypass(repo):
    stage(repo, "safe.py", "safe = True\n")
    git(repo, "commit", "-qm", "Synthetic baseline")
    baseline = git(repo, "rev-parse", "HEAD").stdout.strip()
    stage(repo, ".model-learner/local.txt", "public canary")
    git(repo, "commit", "-qm", "Synthetic hook bypass")
    assert check(repo, "--tree", "HEAD").returncode == 1
    assert check(repo, "--tree", baseline).returncode == 0
    git(repo, "rm", "--cached", ".model-learner/local.txt")
    assert check(repo, "--tree", "HEAD").returncode == 1


def test_hook_blocks_commit_and_runs_from_worktree_root(repo):
    (repo / "scripts").mkdir()
    shutil.copyfile(GUARD, repo / "scripts/privacy_guard.py")
    (repo / ".githooks").mkdir()
    shutil.copyfile(ROOT / ".githooks/pre-commit", repo / ".githooks/pre-commit")
    (repo / ".githooks/pre-commit").chmod(0o755)
    stage(repo, "safe.py", "safe = True\n")
    git(repo, "commit", "-qm", "Synthetic hook pass")
    baseline = git(repo, "rev-parse", "HEAD").stdout
    stage(repo, ".env", 'PASSWORD="dummy"\n')
    nested = repo / "nested"
    nested.mkdir()
    result = run(nested, "git", "commit", "-qm", "Synthetic hook rejection")
    assert result.returncode != 0
    assert git(repo, "rev-parse", "HEAD").stdout == baseline
    assert "dummy" not in result.stdout + result.stderr


def test_reviewed_fixture_digest_does_not_exempt_secrets(repo):
    content = '{"role":"user","content":"Public synthetic fixture"}'
    path = "tests/fixtures/conversation.json"
    stage(repo, path, content)
    policy = {path: hashlib.sha256(content.encode()).hexdigest()}
    stage(repo, "scripts/privacy_fixture_allowlist.json", json.dumps(policy))
    assert check(repo).returncode == 0
    modified = content.replace("Public synthetic fixture", synthetic_token())
    stage(repo, path, modified)
    policy[path] = hashlib.sha256(modified.encode()).hexdigest()
    stage(repo, "scripts/privacy_fixture_allowlist.json", json.dumps(policy))
    assert check(repo).returncode == 1


def test_fixture_policy_is_read_from_index(repo):
    content = '{"role":"user","content":"Public synthetic fixture"}'
    path = "tests/fixtures/conversation.json"
    stage(repo, path, content)
    policy_file = stage(repo, "scripts/privacy_fixture_allowlist.json", "{}")
    policy_file.write_text(
        json.dumps({path: hashlib.sha256(content.encode()).hexdigest()})
    )
    assert check(repo).returncode == 1


@pytest.mark.parametrize("mode", ["120000", "160000"])
def test_special_entries_fail_closed(repo, mode):
    stage(repo, "safe.py", "safe = True\n")
    git(repo, "commit", "-qm", "Synthetic baseline")
    oid = git(repo, "rev-parse", "HEAD" if mode == "160000" else "HEAD:safe.py")
    git(
        repo,
        "update-index",
        "--add",
        "--cacheinfo",
        mode,
        oid.stdout.strip(),
        "special",
    )
    assert check(repo).returncode == 1


def test_invalid_policy_reference_and_oversized_blob_fail_closed(repo):
    stage(repo, "scripts/privacy_fixture_allowlist.json", "[]")
    assert check(repo).returncode == 2
    git(repo, "rm", "--cached", "scripts/privacy_fixture_allowlist.json")
    assert check(repo, "--tree", "missing-reference").returncode == 2
    stage(repo, "large.txt", b"x" * (5 * 1024 * 1024 + 1))
    assert check(repo).returncode == 1


def test_secret_in_filename_is_redacted(repo):
    token = synthetic_token()
    stage(repo, f"{token}.txt", "public canary")
    result = check(repo)
    assert result.returncode == 1
    assert "redacted-file-id:" in result.stdout
    assert token not in result.stdout + result.stderr


@pytest.mark.skipif(os.name == "nt", reason="POSIX filenames only")
def test_non_utf8_filename(repo):
    # Some macOS/sandbox filesystems reject these names. Git's index supports them.
    result = subprocess.run(
        ["git", "hash-object", "-w", "--stdin"],
        cwd=repo,
        input=b"safe = True\n",
        capture_output=True,
        check=True,
    )
    subprocess.run(
        ["git", "update-index", "-z", "--index-info"],
        cwd=repo,
        input=b"100644 " + result.stdout.strip() + b"\tpublic-\xff.py\0",
        capture_output=True,
        check=True,
    )
    assert check(repo).returncode == 0
