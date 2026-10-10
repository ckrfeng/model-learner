# Codex local observation: first slice

This adapter consumes the documented JSONL output of `codex exec --json`. It
never starts Codex, changes its model, installs hooks, edits Codex configuration,
or constructs tasks, runs, verifications, outcomes, or learning observations.
Model Learner observes; agent control belongs to a future AI Governor.

## Source investigation and choice

The [official non-interactive mode documentation](https://learn.chatgpt.com/docs/non-interactive-mode)
describes thread/turn lifecycle events, item lifecycle events, and token usage.
Items include command executions, MCP tools, file changes, and other activity.
Its example does not supply timestamps, provider/model/reasoning configuration,
prices, or unique event IDs. The importer preserves these limits explicitly.

The [official advanced configuration documentation](https://learn.chatgpt.com/docs/config-file/config-advanced)
describes opt-in OpenTelemetry export, with conversation/model metadata and tool
measurements. That is a useful future candidate, but a local receiver/exporter
and config change are unnecessary for this first stream importer. No telemetry
settings were changed.

The [official Codex platform overview](https://developers.openai.com/blog/codex-as-a-platform)
also describes app-server and SDK integration. Those are application integration
surfaces, rather than a documented passive tap into this running desktop chat.
Desktop session rollout records were inspected read-only using only structural
keys/counts. Their format differed from exec JSON and contained private content.
They are not treated as a supported import format. This implementation therefore
captures explicitly selected CLI workflows, not arbitrary existing desktop
activity. No native desktop transcript was copied into the repository.

Local `codex exec --help` confirmed `--json`, `--ephemeral`, and `--sandbox` on
installed `codex-cli 0.162.0-alpha.17.2` (macOS arm64, 2026-10-10). A bounded,
read-only smoke invocation with the sanitized prompt
`Reply exactly telemetry-smoke; do not use tools or change files` was initially
blocked by the host sandbox (`Operation not permitted`, zero JSON events). The
coordinator's authorized execution outside that host sandbox succeeded with exit
0, four native events, one session, and no import diagnostics. Replaying that
capture inserted no additional events. This validates a real CLI path only.
Neither a successful process exit nor the response was made into a task label.

`tests/fixtures/codex/real_smoke_capture.jsonl` derives from that actual capture:
thread/capture identities and receipt timestamps are replaced with neutral
fixture values, private message content is omitted, and measured usage is
retained. The coordinator buffered native stdout before receipt-envelope capture;
those times therefore observe the buffered records rather than live emission.
They cannot support execution-latency claims. `exec_capture.jsonl` remains a
synthetic reconstruction of documented event shapes for richer tool/error tests.

## Capture and import

The coordinator-owned CLI exposes an explicit stdin capture and local import:

```sh
codex exec --json --sandbox read-only "<your approved task>" |
  model-learner capture codex .model-learner/session.capture.jsonl \
    --source-version '<codex --version output>'
model-learner import codex .model-learner/session.capture.jsonl \
  --machine-id '<local machine identifier>' --database .model-learner/learner.sqlite3
model-learner sessions --database .model-learner/learner.sqlite3
model-learner session show '<session UUID>' --database .model-learner/learner.sqlite3
```

Initialize the database first with the existing `model-learner init` command.
The capture command consumes the already running stream; the adapter does not
choose or launch a workflow. The Python interfaces are `capture_codex_stream`,
`read_codex_capture`, `ingest_codex_capture`, and `summarize_session`, in
`model_learner.adapters.codex`. They remain independently testable without the CLI.

Each project-owned `codex-exec-capture/v1` envelope contains a capture identity,
line sequence, timezone-aware observer receipt time, emitter version, native
event metadata, and the names of omitted fields. Native JSONL imported without
this envelope is rejected: using import time would invent an execution time.
`source_version="unknown"` is valid when the emitter version was not recorded;
the adapter never reads today's installed version and assigns it to old data.
An optional import version can fill an unknown version before first persistence;
it cannot contradict a known captured version or rewrite already stored events.

Every canonical event is observed provenance. `Event.observed_at` means receipt
time, with `payload.timestamp_basis="capture_receipt"` and
`payload.native_observed_at=null`. Source timestamps and actual session
start/end remain unknown. Receipt spans are not reported as execution latency.
Item IDs remain in native metadata; they are not invented unique event IDs.

Capture ID plus sequence distinguish identical emitted events. Identity does not
depend on usage, timestamp, or emitter-version values. Reimporting the same
envelope reproduces stable event and session identities; changing those retained
source facts produces a conflict diagnostic and preserves the first observation.
A new independent
capture of the same stream is not globally deduplicated: the native stream lacks
unique IDs for all events. Machine identity distinguishes independent ledgers.
Use a consistent machine ID when replaying local captures.

Malformed records produce line-number diagnostics without reproducing their
contents. Valid records may still be imported; the report identifies rejected
records. Unknown native event types retain safe metadata instead of crashing.
Imports use existing M1.1 Session/Event persistence and require no contract or
migration change. Native sessions never imply declared tasks or run boundaries.

## Privacy and summaries

Default capture and import use a metadata allowlist. Prompt/message text,
reasoning content, commands/arguments, file paths, tool output/results, error
messages, and arbitrary unknown values are omitted. Native thread/item identity,
event/item type, tool name/server, lifecycle status, exit code, and supported
token counters remain available. Omitted field names record missingness; their
values cannot be recovered. Safe raw metadata is retained in `raw_payload`.

The Python capture API's `retain_raw=True` and import CLI's `--retain-raw` are
explicit retention options for potentially private native content. They do not
perform full-content redaction and should be used only with approved local
retention. Default capture already removes content, so enabling raw retention
only during import cannot restore it. Reimporting existing immutable events
cannot upgrade their retained payloads. Keep captures/databases under ignored
`.model-learner/`; never commit real private traces.

Summaries rebuild event counts, item activity, turn completion/failure counts,
and recorded token usage from retained events. An item appearing at both start
and completion counts once within a capture. Missing item IDs are separately
reported. Token fields retain `null` when unavailable, including reasoning usage;
recorded zero remains zero. Per-field coverage and completed-turn denominators
identify partial totals. Cached input is a subset measurement, not added again
to input tokens. Failed turns with no recorded usage contribute no guessed
tokens. Prices, execution latency, native times, and verification remain unknown.
Any source-emitted model/provider metadata is retained; no model/provider is
inferred from installed defaults or the account. Turn completion and tool exit
code zero do not constitute verified success.

Valid ledger events from a manual importer or a different adapter version remain
in the timeline and total/type counts. `unsupported_event_count` identifies rows
that cannot contribute to this version's configuration/resource summaries;
`supported_event_count` identifies the summary denominator.

Tests cover metadata privacy, unknown/malformed events, missing measurements,
receipt-time semantics, replay, distinct identical native events, source/session
identity, ledger integration, absence of outcomes, and M1 JSONL round trips.
Next real-data work is investigating a supported desktop/app-server export or
opt-in telemetry path with sufficient
native timestamps and configuration information. Automatic desktop observation,
background collection, task/run attribution, and verification are not delivered
by this slice.
