# Operator-controlled coding-task evaluation

The benchmark harness stages two public standard-library Python tasks (`clamp`
and `duration`) in fresh disposable directories. It predeclares the task,
acceptance version, exact configuration snapshot, fixture digest and benchmark
dataset before execution. Each task changes one module. Acceptance covers the
named examples, not universal correctness or whole-project quality.

No benchmark API or CLI command launches a coding agent, shell, paid API or test
process. An operator separately chooses whether to spend money on an agent run,
then separately invokes the supplied acceptance controller. Repository tests run
only controlled public candidate fixtures. There are no real-agent performance
results in this delivery.

## Isolation contract

A disposable working directory **is not an OS sandbox**. Before starting a real
run, configure a container, VM or equivalent filesystem/process boundary:

1. Expose only the returned `workspace` directory as the agent's writable task
   mount. Do not mount the Model Learner repository or the sibling `control`
   directory into the agent environment. Deny host filesystem/process access.
   Use a clean agent configuration and only operator-selected credentials.
2. Capture agent stdout on the host through the existing metadata-only capture
   wrapper into an operator-owned file outside the repository and workspace.
   Do not hand the agent the destination or allow it to replace the wrapper.
3. Stop and reap the agent and its descendants before freezing the candidate.
   Record start/stop timestamps from the operator, including capture receipt times.
4. Run the acceptance controller around the frozen candidate in a separate
   constrained test environment with no repository mount, no network, no secrets,
   no access to host processes, and bounded CPU/memory/disk/process resources.
   Preserve operator ownership of the manifest, trusted acceptance source,
   snapshot receipt and evidence outputs. Candidate workers must not have access
   to the agent's credentialed environment.
5. Confirm that these boundaries held before finalization. `--isolation-confirmed`
   records an operator declaration; the harness cannot inspect or attest a VM or
   container policy. Do not assert it when containment was absent or uncertain.

The harness concretely rejects parent directories equal to, inside, or above the
protected repository after symlink resolution. All workspace, control, ledger,
report and snapshot writes occur outside that repository. Root/directory symlinks,
non-regular candidate inputs, altered trusted acceptance, changed fixture versions,
changed acceptance declarations and altered frozen candidates are rejected. A
read-only source-tree SHA-256 inventory is checked before snapshot and before and
after finalization. Source changes refuse a result; they cannot undo or prevent
writes by a misconfigured external agent. The source inventory excludes `.git`,
`.venv`, `.uv-cache`, `.tools`, `.model-learner`, `.pytest_cache`, `.ruff_cache`,
`__pycache__` and `.DS_Store`; OS containment, not this inventory, protects those
paths. Keep the source tree quiescent during an operator run.

The supplied acceptance controller never imports candidate code into its own
interpreter. Each test calls the candidate in a fresh Python `-I` worker with an
empty environment, five-second timeout and a bounded primitive JSON response.
The controller independently compares returned numeric values or exception types
to fixed expected results and writes JUnit in the control directory. Candidate
`print` output and agent self-report are not acceptance evidence. Monkeypatching
`builtins.eval` inside a candidate cannot patch controller assertions or report
production. Isolated Python mode is not an OS security boundary; resource limits
and denial of filesystem/process interference still belong to the operator.
Finite public tests are not an anti-cheating benchmark, and receipt/hash checks
are not cryptographic attestation of which code actually ran.

## Operator workflow

Inspect the available public tasks:

```sh
model-learner benchmark tasks
```

Create a configuration JSON outside Git, for example with declared `provider`,
`model`, `model_version`, `reasoning_level`, `harness`, `harness_version` and
`configuration_version`. Unknown fields remain null. Do not put credentials or
private transcripts in configuration metadata. Then prepare:

```sh
model-learner benchmark prepare clamp \
  --parent /private/tmp \
  --configuration-file /private/tmp/coding-configuration.json \
  --isolation-mechanism 'operator VM; only task workspace mounted' \
  --dataset-id public-coding --dataset-version 1 --execution-origin real
```

Use the canonical root returned by preparation in subsequent commands. The task
is in `ROOT/workspace/TASK.txt`; editable code is `ROOT/workspace/solution.py`.
Predeclared acceptance and manifest are in `ROOT/control`, outside the agent
mount. Preparation does not start the agent. Start a chosen agent only through
an explicit operator action after configuring containment, and select its working
directory as the disposable workspace. Capture emitted Codex CLI JSON using
`model-learner capture codex --source-version <actual-version>` into an
operator-owned external file. This wrapper only consumes an existing stream.
Keep receipt times, CLI version and exact declared model settings; do not infer
native duration, missing usage or unknown cost from wrapper completion.

After the externally launched agent stops:

```sh
model-learner benchmark snapshot ROOT
```

The operator must run `ROOT/control/acceptance.py` in the constrained test
environment using Python 3.12+ in isolated mode (`python -I ...`), exposing the
frozen `candidate.py` and trusted controller there. The script writes
`ROOT/control/report.xml` exclusively; retain the actual controller exit code
and completion/time receipt. Its only child processes are local Python candidate
workers. Do not let the coding agent generate the report or declare test success.

Finalize with actual operator receipts, for example:

```sh
model-learner benchmark finalize ROOT \
  --started-at 2026-10-10T12:00:00+00:00 \
  --ended-at 2026-10-10T12:01:00+00:00 \
  --capture /private/tmp/operator-capture.jsonl \
  --machine-id operator-machine \
  --test-completed --test-exit-code 0 \
  --test-generated-at 2026-10-10T12:02:00+00:00 \
  --isolation-confirmed
```

These timestamps are placeholders, not claimed executions. Start must follow
preparation; end must include the captured receipt range; the frozen snapshot and
independent test generation must follow the stopped agent. An actual exit of 1
with failing tests produces verified failure. Missing/skipped/malformed/partial
reports, unknown completion or unsuitable/contradictory exits remain unknown.
Omit test receipt options when tests were not independently run. An interrupted
agent can use `--state abandoned` or `--state unknown`; its execution state is
retained and its task assessment remains unknown, with test evidence retained
separately if available. No capture is also permitted and explicitly reported.

Finalization stores a metadata-only telemetry ledger, existing independently
bound JUnit verification, configuration-bearing attempt, assessment and
`result.json`. No learning observation is manufactured. The dataset always has
`source_kind=benchmark`, even for real coding-agent executions. Its ID is suffixed
with `:real` or `:fixture`, and execution origin is retained separately. Preserve
that distinction in downstream analysis. Emitted model/provider disagreements
produce an explicit configuration-conflict reason while retaining both native
telemetry and the predeclared configuration. Unknown money and duration are never
filled with zero. Diagnostics retain reason codes/counts, not raw private rows.

Evidence collection uses a private staging ledger; rejected or concurrently
changed evidence does not leave a partial run in the canonical ledger and can
be retried. Finalization is single-operator and locked against another finalizer.
File replacement across ledger/receipt/result is not a multi-file crash-atomic
transaction; a host crash during final publication may require manual inspection.
Exports and cleanup should wait for finalization to finish.

Save wanted metadata/evidence outside Git, then dispose explicitly:

```sh
model-learner benchmark cleanup ROOT
```

Cleanup removes both workspace and control, including capture, evidence and
ledger. An invalid or tampered root is refused; inspect and remove it manually
instead of bypassing validation with another directory. A new benchmark always
uses a new disposable root, so runs cannot inherit another candidate's artifacts.

## Python API

`prepare_benchmark`, `load_benchmark`, `snapshot_candidate`,
`finalize_benchmark`, `cleanup_benchmark` and `list_tasks` are exported by
`model_learner.benchmark`. Preparation requires an explicit protected repository
path and containment declaration; finalization requires explicit containment
confirmation. Predefined fixtures are the only supported task IDs. There is no
arbitrary execution-command API, routing, Governor, neural fine-tuning or cloud
synchronization. Larger repositories, multi-module submissions and stronger
execution attestation require a separately scoped increment.
