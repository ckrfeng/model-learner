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
    TaskFixture(
        task_id="ceil_div",
        version="1",
        description=(
            "Implement ceil_div(n, d) for integers: the mathematical ceiling of "
            "n / d without floating point. Signed operands are supported; zero "
            "divisor raises ZeroDivisionError. Change only solution.py. "
            "Standard library only."
        ),
        artifact_name="solution.py",
        initial_source="def ceil_div(n, d):\n    raise NotImplementedError\n",
        function="ceil_div",
        checks=(
            ("positive", (7, 3), 3, None),
            ("exact", (6, 3), 2, None),
            ("negative_n", (-7, 3), -2, None),
            ("negative_d", (7, -3), -2, None),
            ("both_negative", (-7, -3), 3, None),
            ("zero", (0, 5), 0, None),
            ("large", (10**30 + 1, 10**15), 10**15 + 1, None),
            ("zero_divisor", (1, 0), None, "ZeroDivisionError"),
        ),
    ),
    TaskFixture(
        task_id="first_index",
        version="1",
        description=(
            "Implement first_index(values, target) in O(log n) time for a sorted "
            "list of integers. Return the first matching index or -1 if absent. "
            "Duplicates and an empty list are valid. Change only solution.py. "
            "Standard library only. Named acceptance tests check returned values; "
            "they do not establish asymptotic complexity."
        ),
        artifact_name="solution.py",
        initial_source=(
            "def first_index(values, target):\n    raise NotImplementedError\n"
        ),
        function="first_index",
        checks=(
            ("empty", ([], 2), -1, None),
            ("one", ([2], 2), 0, None),
            ("duplicates", ([1, 2, 2, 2, 4], 2), 1, None),
            ("last", ([-4, 0, 7], 7), 2, None),
            ("missing_between", ([1, 3, 5], 4), -1, None),
            ("missing_lower", ([1, 3], -2), -1, None),
            ("missing_upper", ([1, 3], 4), -1, None),
        ),
    ),
    TaskFixture(
        task_id="interval_length",
        version="1",
        description=(
            "Implement interval_length(intervals): total length of the union of "
            "half-open integer intervals [start, end), given as pairs in any "
            "order. Empty and zero-length intervals contribute zero. Overlapping "
            "and touching intervals merge; start > end raises ValueError. "
            "Change only solution.py. Standard library only."
        ),
        artifact_name="solution.py",
        initial_source=(
            "def interval_length(intervals):\n    raise NotImplementedError\n"
        ),
        function="interval_length",
        checks=(
            ("empty", ([],), 0, None),
            ("overlap", ([[1, 5], [3, 8]],), 7, None),
            ("disjoint", ([[7, 9], [1, 4]],), 5, None),
            ("touching", ([[1, 3], [3, 5]],), 4, None),
            ("nested_duplicate", ([[1, 8], [2, 3], [1, 8]],), 7, None),
            ("negative_zero", ([[-3, 1], [2, 2]],), 4, None),
            ("reversed", ([[3, 2]],), None, "ValueError"),
        ),
    ),
    TaskFixture(
        task_id="hex_integer",
        version="1",
        description=(
            "Implement hex_integer(text): parse ASCII hexadecimal digits with "
            "an optional leading + or -, optional 0x/0X prefix, and surrounding "
            "whitespace. Letters a-f/A-F are valid. Reject empty digits, internal "
            "whitespace, underscores and other characters with ValueError. "
            "Change only solution.py. Standard library only."
        ),
        artifact_name="solution.py",
        initial_source="def hex_integer(text):\n    raise NotImplementedError\n",
        function="hex_integer",
        checks=(
            ("plain", ("Af",), 175, None),
            ("prefix", ("0X10",), 16, None),
            ("signed", (" -0xF ",), -15, None),
            ("positive_zero", ("+00",), 0, None),
            ("empty", ("",), None, "ValueError"),
            ("prefix_only", ("0x",), None, "ValueError"),
            ("underscore", ("1_f",), None, "ValueError"),
            ("internal_space", ("a b",), None, "ValueError"),
            ("bad_digit", ("gh",), None, "ValueError"),
        ),
    ),
    TaskFixture(
        task_id="median",
        version="1",
        description=(
            "Implement median(values) for an unsorted list of finite integers or "
            "floats. Return the central value for odd length, the arithmetic mean "
            "of the two central values for even length. Empty lists raise "
            "ValueError. Change only solution.py. Standard library only."
        ),
        artifact_name="solution.py",
        initial_source="def median(values):\n    raise NotImplementedError\n",
        function="median",
        checks=(
            ("one", ([7],), 7, None),
            ("odd_unsorted", ([9, 1, 3],), 3, None),
            ("even_unsorted", ([8, 2, 4, 1],), 3, None),
            ("negative", ([-3, -1, -5, -2],), -2.5, None),
            ("duplicates", ([4, 4, 4],), 4, None),
            ("floats", ([0.25, 1.25],), 0.75, None),
            ("empty", ([],), None, "ValueError"),
        ),
    ),
    TaskFixture(
        task_id="edit_distance",
        version="1",
        description=(
            "Implement edit_distance(a, b): Levenshtein distance between two "
            "strings, with insertion, deletion and substitution each costing one. "
            "Characters are case-sensitive Python string characters, including "
            "Unicode. Change only solution.py. Standard library only."
        ),
        artifact_name="solution.py",
        initial_source="def edit_distance(a, b):\n    raise NotImplementedError\n",
        function="edit_distance",
        checks=(
            ("empty", ("", ""), 0, None),
            ("insertions", ("", "abc"), 3, None),
            ("deletions", ("abc", ""), 3, None),
            ("identity", ("same", "same"), 0, None),
            ("classic", ("kitten", "sitting"), 3, None),
            ("case", ("A", "a"), 1, None),
            ("unicode", ("café", "cafe"), 1, None),
        ),
    ),
    TaskFixture(
        task_id="components",
        version="1",
        description=(
            "Implement components(n, edges): count connected components in an "
            "undirected graph with integer vertices 0..n-1 and edge pairs. "
            "Self-loops and duplicate edges are allowed. Negative n or any "
            "endpoint outside the vertex range raises ValueError. Empty graph "
            "has zero components. Change only solution.py. Standard library only."
        ),
        artifact_name="solution.py",
        initial_source="def components(n, edges):\n    raise NotImplementedError\n",
        function="components",
        checks=(
            ("empty", (0, []), 0, None),
            ("isolated", (4, []), 4, None),
            ("chain", (4, [[0, 1], [1, 2], [2, 3]]), 1, None),
            ("two_groups", (5, [[0, 1], [1, 2], [3, 4]]), 2, None),
            ("duplicates_loops", (3, [[0, 0], [0, 1], [1, 0]]), 2, None),
            ("bad_endpoint", (2, [[0, 2]]), None, "ValueError"),
            ("negative_endpoint", (2, [[-1, 0]]), None, "ValueError"),
            ("negative_n", (-1, []), None, "ValueError"),
        ),
    ),
    TaskFixture(
        task_id="unique_window",
        version="1",
        description=(
            "Implement unique_window(text): length of the longest contiguous "
            "substring with no repeated Python string characters. Empty string "
            "returns zero; comparison is case-sensitive. Change only solution.py. "
            "Standard library only."
        ),
        artifact_name="solution.py",
        initial_source="def unique_window(text):\n    raise NotImplementedError\n",
        function="unique_window",
        checks=(
            ("empty", ("",), 0, None),
            ("all_unique", ("abcde",), 5, None),
            ("repeated", ("aaaa",), 1, None),
            ("classic", ("abcabcbb",), 3, None),
            ("overlap", ("abba",), 2, None),
            ("middle", ("pwwkew",), 3, None),
            ("unicode_case", ("éAéa",), 3, None),
        ),
    ),
    TaskFixture(
        task_id="rpn",
        version="1",
        description=(
            "Implement rpn(tokens): evaluate reverse Polish expressions of signed "
            "ASCII integer strings and operators + - * /. Division truncates "
            "toward zero without floating point. Zero division raises "
            "ZeroDivisionError; invalid tokens, too few operands, or a final "
            "stack size other than one raise ValueError. Change only solution.py. "
            "Standard library only."
        ),
        artifact_name="solution.py",
        initial_source="def rpn(tokens):\n    raise NotImplementedError\n",
        function="rpn",
        checks=(
            ("single", (["-3"],), -3, None),
            ("order", (["7", "2", "-"],), 5, None),
            ("mixed", (["2", "3", "+", "4", "*"],), 20, None),
            ("negative_division", (["-7", "3", "/"],), -2, None),
            ("signed_division", (["7", "-3", "/"],), -2, None),
            ("large", ([str(10**30 + 1), "1", "/"],), 10**30 + 1, None),
            ("zero_division", (["1", "0", "/"],), None, "ZeroDivisionError"),
            ("underflow", (["1", "+"],), None, "ValueError"),
            ("leftover", (["1", "2"],), None, "ValueError"),
            ("invalid", (["1_0"],), None, "ValueError"),
            ("empty", ([],), None, "ValueError"),
        ),
    ),
    TaskFixture(
        task_id="balanced_span",
        version="1",
        description=(
            "Implement balanced_span(text): length of the longest contiguous "
            "substring that is a well-formed sequence of parentheses. Empty "
            "string returns zero. Any character other than ( or ) raises "
            "ValueError. Change only solution.py. Standard library only."
        ),
        artifact_name="solution.py",
        initial_source="def balanced_span(text):\n    raise NotImplementedError\n",
        function="balanced_span",
        checks=(
            ("empty", ("",), 0, None),
            ("pair", ("()",), 2, None),
            ("nested", ("(()())",), 6, None),
            ("prefix", ("(()",), 2, None),
            ("split", (")()())",), 4, None),
            ("suffix", ("()(())(",), 6, None),
            ("none", (")))(((",), 0, None),
            ("invalid", ("(x)",), None, "ValueError"),
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
