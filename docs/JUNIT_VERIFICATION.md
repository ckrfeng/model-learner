# Read-only coding-task verification

The JUnit verifier imports an existing pytest/JUnit XML report. It does not run
pytest, accept a command, control an agent, or read agent success claims. A
completed Codex execution is still unverified until independent evidence is
associated and assessed.

Declare acceptance before the run using task metadata:

```python
from model_learner.verification import junit_criterion

metadata = {
    "junit_verifier": junit_criterion(
        required_test_ids=[
            "tests.test_calculator::test_add",
            "tests.test_calculator::test_divide[positive]",
            "tests.test_calculator::test_divide[negative]",
        ]
    )
}
```

Identities combine the report's `classname` and `name` with `::`. Parameterized
test names are retained, including names containing `::`; classnames containing
that delimiter are unsupported. Required identities must be nonempty and unique.
Additional reported tests are allowed, but every reported test must pass for
success. The acceptance target identifies this declared test set, not universal
code correctness or test quality.

Each task supports one verifier criterion. Tasks declaring both file-digest and
JUnit verifier keys are rejected; conjunctions of multiple acceptance checks are
not implemented. Report generation must follow task creation so that tests do
not retroactively establish acceptance declared after the observed report.

An external operator supplies a JSON receipt described by `JUnitReportBinding`:

| Field | Meaning |
| --- | --- |
| `task_id`, `run_id` | Exact declared coding task and bounded execution |
| `acceptance_spec` | Complete matching acceptance-spec record |
| `artifact_fingerprint` | `sha256:<digest>` of the run's declared final artifact |
| `report_sha256` | SHA-256 of the exact XML bytes |
| `report_generated_at` | Aware external report-generation timestamp, no earlier than run start or task creation and no later than observation |
| `source` | `pytest-junit` or `junit`; agent reports are unsupported |
| `execution_completed` | `true`, `false`, or unknown/null |
| `command_exit_code` | Independently recorded integer exit code or unknown/null |

The receipt must come from an independent test harness or operator. Hashes bind
the supplied report and artifact snapshots; they cannot prove that the tests
were actually executed against those bytes. Receipt source, timestamps, completion
and exit code remain external declarations. The verifier does not authenticate a
harness, reconstruct a working tree, certify the reported tests, or verify a Git
commit. Supply a stable file artifact or independently created archive/manifest
whose bytes identify the tested code. Metadata-only Codex capture cannot supply
this association by itself.

```python
from model_learner.verification import JUnitReportBinding, verify_junit, assess_run

binding = JUnitReportBinding.model_validate_json(receipt_path.read_text())
evidence = verify_junit(
    repository,
    run_id=run_id,
    report=report_path,
    artifact=artifact_path,
    binding=binding,
)
outcome = assess_run(
    repository, run_id=run_id, verification_id=evidence.verification_id
)
```

Reports must use the unnamespaced `testsuites`/`testsuite` dialect emitted by
pytest, with `testcase` children, explicit nonnegative suite counts for tests,
failures, errors and skipped cases, and optional aggregate wrapper counts.
Nested suites are supported up to a bounded XML depth. Each case is identified
by a nonempty classname/name; absent failure/error/skipped elements mean passed
only in a supported structure and independently confirmed complete process.
Duplicate case identities, conflicting status elements, unsupported structures
or `status`/`result` attributes prevent a passing assessment. DTDs/entities and
UTF-16/32 XML are unsupported; reports are limited to 10 MiB. No new dependencies
are needed.

The verifier checks task/run/spec/artifact/report association before persisting
evidence. Wrong hashes, stale specifications, foreign receipts, future generation
times and changing artifacts/reports raise errors. Missing report files, empty or
malformed XML, counter discrepancies, missing required cases, skipped cases,
unknown completion/exit status and abnormal or contradictory exit codes yield
`indeterminate` evidence. The supported exit convention is 0 for no failure/error
and 1 for test failures/errors, matching pytest; other producer conventions remain
indeterminate. Incomplete reports remain indeterminate even when they contain an
observed failure. Assessment preserves their evidence IDs but yields unknown and
unverified; it cannot create an eligible binary learning label.

Complete passing reports yield verified success; complete reports with failures
or errors and matching exit status yield one verified failure for the task run.
Internal tests are case-level evidence, not separate failed tasks.

Persistence preserves counts, per-case identities/statuses, report digest/path,
criterion, receipt, verifier version, observation time, provenance and explicit
completeness reasons. Failure messages, tracebacks, commands, stdout, stderr and
XML bodies are omitted. Test identities and local paths are retained metadata
and should themselves be sanitized before sharing. Evidence is append-only;
assessments can explicitly supersede prior unknown assessments without editing
them. The projected metadata is trusted ledger content, not a signed attestation;
validation detects inconsistent counts/policy/bindings but cannot detect an
entire consistently fabricated XML report or ledger projection.

Execution analysis can use the pure
`verification.junit.validate_junit_evidence(run, task, evidence)` helper to check
stored projection associations and receive `JUnitSummary` counts/cases. Parsing
and evidence validation are read-only. The `tests/fixtures/junit` reports are
hand-authored sanitized pytest examples; integration tests join them to existing
controlled Codex capture and verify the real-ledger builder contracts. Those
fixtures do not demonstrate independently verified real-world coding quality.
