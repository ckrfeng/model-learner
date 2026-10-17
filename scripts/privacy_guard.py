#!/usr/bin/env python3
"""Local, content-free Git privacy validation using only the standard library."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import subprocess
import sys
from collections import Counter
from collections.abc import Iterator
from dataclasses import dataclass
from pathlib import PurePosixPath

MAX_BLOB_BYTES = 5 * 1024 * 1024
ALLOWLIST_PATH = "scripts/privacy_fixture_allowlist.json"
PRIVATE_DIRECTORIES = frozenset(
    {
        ".model-learner",
        ".venv",
        ".uv-cache",
        ".tools",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        ".cache",
        ".codex",
        ".claude",
        ".chatgpt",
        ".aws",
        ".ssh",
        ".azure",
        "credentials",
        "secrets",
        "data",
        "spool",
        "logs",
        "raw",
        "transcripts",
        "private",
        "private-data",
        "private-research",
        "private-evaluations",
        "session-dumps",
        "imported-sessions",
        "model-cache",
        "model-weights",
        "node_modules",
    }
)
ARTIFACT_SUFFIXES = (
    ".db",
    ".sqlite",
    ".sqlite3",
    ".log",
    ".sock",
    ".socket",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
    ".safetensors",
    ".gguf",
    ".ggml",
    ".pt",
    ".pth",
    ".ckpt",
    ".onnx",
    ".h5",
    ".pkl",
    ".pickle",
    ".joblib",
    ".tmp",
    ".temp",
    ".swp",
)
SECRET_PATTERNS = {
    "provider credential": re.compile(
        rb"(?<![A-Za-z0-9])(?:gh[pousr]_[A-Za-z0-9]{30,}"
        rb"|github_pat_[A-Za-z0-9_]{60,}|sk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,}"
        rb"|(?:AKIA|ASIA)[A-Z0-9]{16}|AIza[A-Za-z0-9_-]{35}"
        rb"|xox[baprs]-[A-Za-z0-9-]{20,})(?![A-Za-z0-9])"
    ),
    "private key": re.compile(
        rb"-----BEGIN (?:RSA |EC |OPENSSH |DSA |ENCRYPTED )?PRIVATE KEY-----"
    ),
    "credential URL": re.compile(rb"https?://[^\s/@:]+:[^\s/@]+@"),
    "authorization credential": re.compile(
        rb"(?i)authorization[\"']?\s*[:=]\s*[\"']?"
        rb"(?:Bearer|Basic)\s+[A-Za-z0-9_+/=.-]{20,}"
    ),
}
ASSIGNMENT = re.compile(
    rb"(?i)(?:[\"']?\b(?:api[_-]?key|access[_-]?token|client[_-]?secret|"
    rb"secret[_-]?(?:key|access[_-]?key)|password|passwd|auth[_-]?token)"
    rb"[\"']?)\s*[:=]\s*[\"']([^\"'\r\n]{20,})[\"']"
)


@dataclass(frozen=True)
class Entry:
    path: str
    oid: str
    mode: str


class GuardError(Exception):
    """An inspection could not complete; never include Git stderr or file text."""


def git(*args: str) -> bytes:
    result = subprocess.run(
        ["git", "--no-replace-objects", *args],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    if result.returncode:
        raise GuardError(
            "Git inspection failed; check repository/reference availability"
        )
    return result.stdout


def index_entries() -> list[Entry]:
    entries = []
    for row in git("ls-files", "--stage", "-z").split(b"\0"):
        if not row:
            continue
        meta, path = row.split(b"\t", 1)
        mode, oid, stage = meta.decode("ascii").split()
        if stage != "0":
            raise GuardError(
                "Unmerged index entries; resolve conflicts before committing"
            )
        entries.append(Entry(os.fsdecode(path), oid, mode))
    return entries


def tree_entries(revision: str) -> list[Entry]:
    # Resolve first: never interpret user input as ls-tree flags/pathspecs.
    tree = git("rev-parse", "--verify", "--end-of-options", revision + "^{tree}")
    entries = []
    for row in git("ls-tree", "-rz", tree.decode().strip()).split(b"\0"):
        if row:
            meta, path = row.split(b"\t", 1)
            mode, _, oid = meta.decode("ascii").split()
            entries.append(Entry(os.fsdecode(path), oid, mode))
    return entries


class Blobs:
    """Read immutable objects through one Git process, never following symlinks."""

    def __init__(self) -> None:
        self.process = subprocess.Popen(
            ["git", "--no-replace-objects", "cat-file", "--batch"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
        )
        self.cache: dict[str, bytes | None] = {}

    def read(self, oid: str) -> bytes | None:
        if oid in self.cache:
            return self.cache[oid]
        assert self.process.stdin is not None and self.process.stdout is not None
        self.process.stdin.write(oid.encode("ascii") + b"\n")
        self.process.stdin.flush()
        header = self.process.stdout.readline().split()
        if len(header) != 3 or header[1] != b"blob":
            raise GuardError("A required Git blob is unavailable")
        size = int(header[2])
        # Drain oversized blobs in bounded chunks; reject, never silently skip them.
        if size > MAX_BLOB_BYTES:
            remaining = size
            while remaining:
                part = self.process.stdout.read(min(remaining, 65536))
                if not part:
                    raise GuardError("Incomplete Git blob read")
                remaining -= len(part)
            data = None
        else:
            data = self.process.stdout.read(size)
            if len(data) != size:
                raise GuardError("Incomplete Git blob read")
        if self.process.stdout.read(1) != b"\n":
            raise GuardError("Invalid Git blob response")
        self.cache[oid] = data
        return data

    def close(self) -> None:
        if self.process.stdin:
            self.process.stdin.close()
        if self.process.stdout:
            self.process.stdout.close()
        self.process.wait()


def path_reasons(path: str) -> set[str]:
    parts = PurePosixPath(path.casefold()).parts
    name = parts[-1]
    reasons = set()
    if any(part in PRIVATE_DIRECTORIES for part in parts[:-1]):
        reasons.add("private data, credentials or cache directory")
    if name == ".env" or (name.startswith(".env.") and name != ".env.example"):
        reasons.add("local environment/credential file")
    if (
        name in {".ds_store", ".netrc", ".npmrc", ".pypirc", "auth.json", "cookies.txt"}
        or name.startswith(("config.local.", "rollout-", "session-dump", "transcript-"))
        or name in {"id_rsa", "id_ed25519", "credentials.json", "service-account.json"}
    ):
        reasons.add("local metadata, session or authentication file")
    if name.endswith(ARTIFACT_SUFFIXES) or re.search(
        r"\.(?:db|sqlite|sqlite3)-.+$", name
    ):
        reasons.add("local database, log, credential, model or temporary artifact")
    return reasons


def secret_reasons(data: bytes) -> set[str]:
    reasons = {
        label for label, pattern in SECRET_PATTERNS.items() if pattern.search(data)
    }
    for match in ASSIGNMENT.finditer(data):
        value = match.group(1)
        # Templates remain allowed; provider tokens above never get exemptions.
        if any(
            marker in value.lower()
            for marker in (
                b"example",
                b"placeholder",
                b"change_me",
                b"your_",
                b"${",
                b"<",
                b"dummy",
            )
        ):
            continue
        counts = Counter(value)
        entropy = -sum(
            (n / len(value)) * math.log2(n / len(value)) for n in counts.values()
        )
        if entropy >= 4 and len(counts) >= 12 and not any(c in value for c in b" /\\"):
            reasons.add("high-entropy credential assignment")
    return reasons


def json_nodes(data: bytes) -> Iterator[dict]:
    """Inspect actual structured data, avoiding code that merely names JSON fields."""
    stripped = data.lstrip()
    if not stripped.startswith((b"{", b"[")):
        return
    try:
        roots = [json.loads(stripped)]
    except (ValueError, RecursionError):
        roots = []
        for line in stripped.splitlines():
            try:
                roots.append(json.loads(line))
            except (ValueError, RecursionError):
                continue
    pending = list(roots)
    while pending:
        node = pending.pop()
        if isinstance(node, dict):
            yield node
            pending.extend(node.values())
        elif isinstance(node, list):
            pending.extend(node)


def raw_session(data: bytes) -> bool:
    """Recognize structured native histories and conversation text in any extension."""
    return any(
        node.get("type") in ("session_meta", "response_item", "event_msg")
        or node.get("format") == "codex-exec-capture/v1"
        or ("thread" in node and "turns" in node)
        or (
            node.get("role") in ("user", "assistant", "system", "developer")
            and any(k in node for k in ("content", "text", "parts"))
        )
        for node in json_nodes(data)
    )


def content_reasons(data: bytes) -> set[str]:
    reasons = secret_reasons(data)
    if data.startswith(b"SQLite format 3\0"):
        reasons.add("SQLite database content")
    if b"\0" in data:
        reasons.add("unreviewed binary content")
        # Also inspect common UTF-16 encodings for recognizable credentials.
        reasons.update(secret_reasons(data.replace(b"\0", b"")))
    if data.startswith(b"version https://git-lfs.github.com/spec/v1"):
        reasons.add("uninspected Git LFS payload")
    if raw_session(data):
        reasons.add("raw session/conversation format without reviewed fixture digest")
    if any(
        node.get("type") == "service_account" and "private_key" in node
        for node in json_nodes(data)
    ):
        reasons.add("service-account credential")
    return reasons


def fixture_allowlist(entries: list[Entry], blobs: Blobs) -> dict[str, str]:
    entry = next((e for e in entries if e.path == ALLOWLIST_PATH), None)
    if entry is None:
        return {}
    data = blobs.read(entry.oid)
    try:
        values = json.loads(data) if data is not None else None
        if not isinstance(values, dict) or any(
            not isinstance(path, str)
            or (
                not path.startswith("tests/fixtures/")
                and path != "experiments/local_task_state/holdout_sources.json"
            )
            or ".." in PurePosixPath(path).parts
            or not isinstance(digest, str)
            or not re.fullmatch(r"[0-9a-f]{64}", digest)
            for path, digest in values.items()
        ):
            raise ValueError
    except (ValueError, TypeError):
        raise GuardError("Invalid reviewed-fixture digest policy") from None
    return values


def inspect(entry: Entry, blobs: Blobs, allowed: dict[str, str]) -> set[str]:
    reasons = path_reasons(entry.path) | secret_reasons(os.fsencode(entry.path))
    if entry.mode not in ("100644", "100755"):
        return reasons | {"unreviewed symlink, submodule or special entry"}
    data = blobs.read(entry.oid)
    if data is None:
        return reasons | {"blob exceeds 5 MiB inspection limit"}
    reasons.update(content_reasons(data))
    if allowed.get(entry.path) == hashlib.sha256(data).hexdigest():
        # Fixture exemptions cover structure only, never secrets/path/binary rules.
        reasons.discard(
            "raw session/conversation format without reviewed fixture digest"
        )
    return reasons


def identifier(path: str) -> str:
    if secret_reasons(os.fsencode(path)):
        return "redacted-file-id:" + hashlib.sha256(os.fsencode(path)).hexdigest()[:16]
    return json.dumps(path, ensure_ascii=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--staged", action="store_true", help="validate the entire Git index"
    )
    group.add_argument(
        "--tree", metavar="REV", help="validate a committed tree (CI: HEAD)"
    )
    args = parser.parse_args()
    blobs = None
    try:
        entries = tree_entries(args.tree) if args.tree else index_entries()
        blobs = Blobs()
        allowed = fixture_allowlist(entries, blobs)
        failed = 0
        for entry in entries:
            reasons = inspect(entry, blobs, allowed)
            if reasons:
                failed += 1
                print(f"REJECT {identifier(entry.path)}: {', '.join(sorted(reasons))}")
        print(f"Privacy guard: {len(entries)} files inspected; {failed} rejected.")
        return 1 if failed else 0
    except (GuardError, OSError, ValueError, RecursionError):
        print("Privacy guard could not complete inspection; commit/check blocked.")
        return 2
    finally:
        if blobs is not None:
            blobs.close()


if __name__ == "__main__":
    sys.exit(main())
