"""Public coding exercises with trusted acceptance and disposable workers."""

import json
from dataclasses import dataclass


@dataclass(frozen=True)
class TaskFixture:
    task_id: str
    version: str
    description: str
    artifact_name: str
    initial_source: str
    # Test name, positional arguments, expected primitive value, expected error.
    function: str
    checks: tuple[tuple[str, tuple, int | float | None, str | None], ...]

    @property
    def required_test_ids(self) -> tuple[str, ...]:
        return tuple(f"benchmark.{self.task_id}::{name}" for name, *_ in self.checks)


_TASKS = (
    TaskFixture(
        task_id="clamp",
        version="1",
        description=(
            "Implement clamp(value, lower, upper): return value bounded inclusively "
            "by lower and upper. Raise ValueError if lower > upper. Change only "
            "solution.py. Standard library only."
        ),
        artifact_name="solution.py",
        initial_source=(
            "def clamp(value, lower, upper):\n"
            "    raise NotImplementedError('implement clamp')\n"
        ),
        function="clamp",
        checks=(
            ("inside", (3, 1, 5), 3, None),
            ("below", (-3, 1, 5), 1, None),
            ("above", (8, 1, 5), 5, None),
            ("equal_bounds", (8, 2, 2), 2, None),
            ("floats", (0.5, -1.0, 1.0), 0.5, None),
            ("invalid_bounds", (1, 3, 2), None, "ValueError"),
        ),
    ),
    TaskFixture(
        task_id="duration",
        version="1",
        description=(
            "Implement duration_seconds(text) for nonnegative integer durations "
            "with one suffix s, m or h. Whitespace around text is allowed. Reject "
            "missing/unknown suffixes, negative and decimal values with ValueError. "
            "Change only solution.py. Standard library only."
        ),
        artifact_name="solution.py",
        initial_source=(
            "def duration_seconds(text):\n"
            "    raise NotImplementedError('implement duration_seconds')\n"
        ),
        function="duration_seconds",
        checks=(
            ("seconds", ("12s",), 12, None),
            ("minutes", ("2m",), 120, None),
            ("hours", ("3h",), 10800, None),
            ("whitespace_zero", (" 0m ",), 0, None),
            ("negative", ("-2s",), None, "ValueError"),
            ("decimal", ("1.5h",), None, "ValueError"),
            ("suffix", ("3d",), None, "ValueError"),
            ("empty", ("",), None, "ValueError"),
        ),
    ),
)


def list_tasks() -> tuple[TaskFixture, ...]:
    return _TASKS


def get_task(task_id: str) -> TaskFixture:
    for task in _TASKS:
        if task.task_id == task_id:
            return task
    raise ValueError("unknown public benchmark task")


_WORKER = """import contextlib
import importlib.util
import json
import os
import sys
request = json.loads(sys.argv[2])
spec = importlib.util.spec_from_file_location('candidate', sys.argv[1])
candidate = importlib.util.module_from_spec(spec)
# Candidate print output is not the protocol. Parent independently checks results.
with open(os.devnull, 'w') as sink, contextlib.redirect_stdout(sink):
    try:
        spec.loader.exec_module(candidate)
        value = getattr(candidate, request['function'])(*request['args'])
        response = (
            {'value': value} if type(value) in (int, float)
            else {'error': 'UnsupportedReturn'}
        )
    except Exception as error:
        response = {'error': type(error).__name__}
print(json.dumps(response, allow_nan=False))
"""


_CONTROLLER = """import json
import subprocess
import sys
import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

root = Path(__file__).resolve().parent
worker = WORKER
checks = CHECKS
cases = []
errors = 0
failed = 0
for name, args, expected, expected_error in checks:
    case = ET.Element('testcase', classname=CLASSNAME, name=name)
    request = json.dumps({'function': FUNCTION, 'args': args})
    # Worker import/calls happen in a fresh interpreter. It cannot monkeypatch
    # controller assertions, expected values or JUnit production in memory.
    with tempfile.TemporaryFile() as output:
        try:
            process = subprocess.run(
                [sys.executable, '-I', '-c', worker,
                 str(root / 'candidate.py'), request],
                cwd=root, env={}, stdout=output, stderr=subprocess.DEVNULL, timeout=5,
            )
            output.seek(0)
            contents = output.read(4097)
            if process.returncode != 0 or len(contents) > 4096:
                raise ValueError('invalid worker protocol')
            response = json.loads(contents)
            if expected_error is not None:
                passed = response == {'error': expected_error}
            else:
                passed = (
                    isinstance(response, dict) and set(response) == {'value'}
                    and type(response['value']) in (int, float)
                    and response['value'] == expected
                )
            if not passed:
                ET.SubElement(case, 'failure')
                failed += 1
        except (subprocess.TimeoutExpired, ValueError, OSError):
            ET.SubElement(case, 'error')
            errors += 1
    cases.append(case)
suite = ET.Element('testsuite', tests=str(len(cases)), failures=str(failed),
                   errors=str(errors), skipped='0')
suite.extend(cases)
with (root / 'report.xml').open('xb') as output:
    output.write(ET.tostring(suite, encoding='utf-8'))
raise SystemExit(1 if failed + errors else 0)
"""


def acceptance_source(task: TaskFixture) -> str:
    # JSON serialization is only for worker requests; these Python literals are
    # generated exclusively from the fixed public task definitions above.
    json.dumps(task.checks, allow_nan=False)
    return (
        _CONTROLLER.replace("WORKER", repr(_WORKER))
        .replace("CHECKS", repr(task.checks))
        .replace("CLASSNAME", repr(f"benchmark.{task.task_id}"))
        .replace("FUNCTION", repr(task.function))
    )
