"""Frozen v1 data checker; reads one selected artifact, never candidate code.

Operator-controlled immutable parent directories are a precondition. Observed
symlink checks and bounded no-follow open are not a hostile filesystem sandbox.
Only main() writes an explicitly selected, exclusively created report.
"""

import argparse
import hashlib
import json
import os
import stat
import tomllib
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET

VERSION = "w4b-p0-toml-checker/1"
MAX_BYTES = 8192
CASE_NAMES = (
    "artifact_regular",
    "toml_parse",
    "package_metadata",
    "python_requirement",
    "build_system",
    "cli_entry",
    "dev_requirements",
    "lint_format",
    "preservation",
)
REQUIRED_IDS = tuple(f"w4b_p0_v1::{name}" for name in CASE_NAMES)


def _read(artifact: Path) -> bytes:
    path = artifact.absolute()
    for component in (*reversed(path.parents), path):
        if component.is_symlink():
            raise ValueError("symlink")
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    with os.fdopen(fd, "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode) or before.st_size > MAX_BYTES:
            raise ValueError("not_bounded_regular_file")
        data = stream.read(MAX_BYTES + 1)
        after = os.fstat(stream.fileno())
    current = path.lstat()
    fields = ("st_dev", "st_ino", "st_mode", "st_size", "st_mtime_ns", "st_ctime_ns")
    if len(data) > MAX_BYTES or any(
        getattr(before, key) != getattr(after, key)
        or getattr(after, key) != getattr(current, key)
        for key in fields
    ):
        raise ValueError("artifact_changed_or_oversized")
    return data


def _equal(actual, expected):
    # JSON preserves bool/int distinctions which Python equality would erase.
    try:
        return json.dumps(actual, sort_keys=True, allow_nan=False) == json.dumps(
            expected, sort_keys=True, allow_nan=False
        )
    except (TypeError, ValueError):
        # Valid TOML dates/times and nonfinite floats are outside this contract.
        return False


@dataclass(frozen=True)
class CheckResult:
    artifact_sha256: str | None
    cases: tuple[bool, ...]
    report: bytes

    @property
    def passed(self) -> bool:
        return all(self.cases)

    @property
    def report_sha256(self) -> str:
        return hashlib.sha256(self.report).hexdigest()


def check(artifact: Path) -> CheckResult:
    """Read just artifact; return deterministic bounded JUnit and exact hashes."""
    results = [False] * len(CASE_NAMES)
    digest = None
    parsed = None
    try:
        data = _read(artifact)
        digest = hashlib.sha256(data).hexdigest()
        results[0] = True
        parsed = tomllib.loads(data.decode("utf-8"))
        pending = [(parsed, 0)]
        while pending:
            node, depth = pending.pop()
            if depth > 16:
                raise ValueError("unsupported_nesting")
            children = node.values() if isinstance(node, dict) else node
            if isinstance(node, (dict, list)):
                pending.extend((child, depth + 1) for child in children)
        results[1] = True
    except (OSError, ValueError, UnicodeError, RecursionError):
        parsed = None
    if parsed is not None:
        project = parsed.get("project", {})
        tool = parsed.get("tool", {})
        if not isinstance(project, dict):
            project = {}
        if not isinstance(tool, dict):
            tool = {}
        metadata = {
            key: project.get(key)
            for key in ("name", "version", "description", "dependencies")
        }
        results[2] = _equal(
            metadata,
            {
                "name": "signal-note",
                "version": "0.2.0",
                "description": "Fictional offline note formatter.",
                "dependencies": [],
            },
        )
        results[3] = project.get("requires-python") == ">=3.12,<3.14"
        results[4] = _equal(
            parsed.get("build-system"),
            {"requires": ["hatchling>=1.27,<2"], "build-backend": "hatchling.build"},
        ) and _equal(
            tool.get("hatch"),
            {"build": {"targets": {"wheel": {"packages": ["src/signal_note"]}}}},
        )
        results[5] = _equal(
            project.get("scripts"), {"signal-note": "signal_note.cli:main"}
        )
        results[6] = _equal(
            project.get("optional-dependencies"),
            {"dev": ["pytest>=8,<9", "ruff>=0.12,<1"]},
        )
        results[7] = _equal(
            tool.get("ruff"),
            {
                "target-version": "py312",
                "line-length": 88,
                "lint": {"select": ["E", "F", "I", "UP", "B"]},
                "format": {"quote-style": "double", "indent-style": "space"},
            },
        )
        results[8] = (
            set(parsed) == {"project", "build-system", "tool"}
            and set(project)
            == {
                "name",
                "version",
                "description",
                "requires-python",
                "dependencies",
                "scripts",
                "optional-dependencies",
            }
            and set(tool) == {"signal_note", "hatch", "ruff"}
            and _equal(
                tool.get("signal_note"),
                {
                    "default_style": "compact",
                    "retention_days": 7,
                    "labels": {"team": "fictional", "channel": "local"},
                },
            )
        )
    suite = ET.Element(
        "testsuite",
        name=VERSION,
        tests=str(len(results)),
        failures=str(results.count(False)),
        errors="0",
        skipped="0",
    )
    for name, passed in zip(CASE_NAMES, results, strict=True):
        case = ET.SubElement(suite, "testcase", classname="w4b_p0_v1", name=name)
        if not passed:
            ET.SubElement(case, "failure", message="frozen data criterion unsatisfied")
    report = ET.tostring(suite, encoding="utf-8", xml_declaration=True) + b"\n"
    return CheckResult(digest, tuple(results), report)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("artifact", type=Path)
    parser.add_argument("--report", required=True, type=Path)
    args = parser.parse_args()
    result = check(args.artifact)
    with args.report.open("xb") as stream:
        stream.write(result.report)
    print(
        json.dumps(
            {
                "checker": VERSION,
                "passed": result.passed,
                "artifact_sha256": result.artifact_sha256,
                "report_sha256": result.report_sha256,
                "required_ids": REQUIRED_IDS,
            },
            sort_keys=True,
        )
    )
    return 0 if result.passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
