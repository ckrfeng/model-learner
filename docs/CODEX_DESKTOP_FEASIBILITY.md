# Codex Desktop capture feasibility

For the 2026-10-11 assessment of selected existing conversations from both Codex
Desktop and ChatGPT Work Local, see
[selected conversation ingestion feasibility](CONVERSATION_INGESTION_FEASIBILITY.md).
The assessment below remains historical evidence about Desktop capture.

Assessed 2026-10-10 on macOS arm64 with installed
`codex-cli 0.162.0-alpha.17.2`. Workstream C is research-only. No desktop adapter,
hook, telemetry configuration, daemon, or agent-control integration was installed.

## Finding

There are documented observation candidates, but passive capture of this running
desktop application has not been established on this machine. Continue using
the existing explicit CLI stream capture for real observations. A desktop adapter
would currently overstate tested coverage and require a separate feasibility
check before implementation.

This assessment follows the M3-A source-validation requirement in
`MODEL_LEARNER_PLAN.md`: desktop data must not be assumed equivalent to CLI
events. It also preserves the product boundary: Model Learner records execution
and independently assesses outcomes; it does not start, resume, interrupt, route,
or change an agent.

## Interfaces and tradeoffs

| Candidate | Coverage | Reliability / integration difficulty | Privacy / boundary |
| --- | --- | --- | --- |
| Existing `codex exec --json` importer | Selected CLI workflow only; thread/item identity, turn/tool lifecycle and emitted usage | Already exercised locally; low incremental difficulty; receipt time is not execution time | Metadata projection exists; raw messages and tool contents remain opt-in |
| App-server stored-thread reads | Potential selected historical thread/turn/item metadata; actual Desktop visibility untested | Medium: reachable server, version compatibility, filters and pagination must be established | Read-only RPC subset can preserve observer role; responses contain private content requiring projection before persistence |
| App-server live notifications | Rich activity and usage for an integrated client | Higher: connection lifecycle, subscriptions, reconnect gaps and event deduplication; no passive Desktop tap demonstrated | Protocol includes control and approvals; a learner must never invoke them |
| Opt-in OpenTelemetry export | Prospective run/tool/model/usage telemetry; Desktop emission untested | Medium: local receiver, exporter configuration, batching, version fixtures and loss accounting | Prompt redaction alone does not sanitize tool output snippets |
| Lifecycle hooks | Prospective session/model/turn/tool metadata; Desktop behavior untested | Medium: trusted configuration, bounded spool, ordering and shutdown losses | Hooks can alter execution; a collector must emit no decisions/context and avoid transcript reads |
| SDK, cloud/API traces, screen recording | Other execution surfaces or visual actions | Do not establish local Desktop coverage | Starting agent workflows or recording the screen is outside a passive local collector |

The CLI documentation describes JSONL thread, turn and item events with usage on
turn completion. It provides a supported stream for a selected invocation,
rather than a Desktop-export promise. The repository's existing smoke evidence
is recorded in `STATUS.md` and `docs/CODEX_OBSERVATION.md`; this research did not
run another agent session. [Official non-interactive documentation](https://learn.chatgpt.com/docs/non-interactive-mode#make-output-machine-readable).

App-server documents JSON-RPC over stdio and Unix sockets, plus experimental
WebSockets. `thread/read` can retrieve stored history without resuming or
subscribing; `thread/list` supports filters and pagination. Its default sources
exclude `appServer`, so defaults are insufficient for a Desktop coverage test.
Item and token-usage notifications are available to connected clients. The docs
describe an application integration and mark the command/WebSocket transport
experimental; they do not establish a lossless passive observer of this Desktop
instance. [Official app-server documentation](https://learn.chatgpt.com/docs/app-server#read-a-stored-thread-without-resuming).

OTel export is opt-in. Documented metadata includes conversation identity, model,
version and settings; events include request/tool durations and response token
counts. Exporters batch asynchronously and flush on shutdown. A tool-result
event can contain an output snippet even with `log_user_prompt=false`.
Aggregated metrics are insufficient to reconstruct individual task outcomes.
A localhost receiver with an allowlist and missing-data accounting is a possible
future spike; this desktop's actual emission and delivery semantics remain
untested. [Official observability documentation](https://learn.chatgpt.com/docs/config-file/config-advanced#observability-and-telemetry).

Hooks document session/model metadata, turn/tool IDs on relevant events, and tool
inputs/results. Non-managed hooks require trust. Background hooks may complete
out of order and are canceled at session end. The documentation explicitly says
the format behind `transcript_path` is unstable. Metadata hooks could support a
future bounded observer, but tokens/native event timestamps are not promised by
their common input contract. Hook inputs may include private prompts, commands
and outputs. No hook was installed or trusted in this assessment.
[Official hook contracts](https://learn.chatgpt.com/docs/hooks#common-input-fields).

The SDK is intended to programmatically control Codex workflows; it does not
establish passive Desktop observation. [Official SDK documentation](https://learn.chatgpt.com/docs/codex-sdk).
Agents API trace export concerns API sessions and project permissions; no mapping
to the local desktop chats was established. [Official trace export documentation](https://developers.openai.com/api/docs/guides/agents-api/tracing).
Record & Replay captures a demonstrated macOS workflow into a skill, rather than
exporting agent execution telemetry. [Official Record & Replay documentation](https://learn.chatgpt.com/docs/extend/record-and-replay).

## Tested local evidence

Only public CLI help, version reporting and generated protocol schemas were
inspected. No private transcript, rollout file, SQLite database, authentication
file, or existing chat content was read or copied.

| Read-only / schema command | Actual result |
| --- | --- |
| `command -v codex` | Bundled executable under `/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex` |
| `codex --version` | Exit 0; `codex-cli 0.162.0-alpha.17.2` |
| `codex --help` / `codex agents --help` | Exit 0; `agents` advertises browsing a shared local app-server daemon; no browser was launched |
| `codex app-server --help` | Exit 0; stdio/Unix/WebSocket listeners and version-specific schema generation are exposed |
| `codex app-server proxy --help` | Exit 0; advertises stdio proxying to a running control socket and an explicit `--sock` option |
| `codex app-server daemon --help` | Exit 0; version command is available; start/restart/bootstrap were not invoked |
| `codex app-server daemon version` | Exit 1; default control socket was absent (`No such file or directory`) |
| `codex app-server generate-json-schema --out /private/tmp/model-learner-codex-protocol-20261010` | Exit 0; generated public protocol schemas only, outside the repository |

These invocations emitted a warning that PATH aliases could not be created under
the host sandbox. Successful help/schema commands remain valid observations.
The failed daemon version query establishes no reachable daemon at the public
default socket; it does not prove Desktop has no separate server or interface.
No private socket discovery or daemon startup was attempted.

Inspection of the **generated installed-version schema**, rather than any real
session, found:

- `ThreadReadParams` exposes only `threadId` and optional `includeTurns`.
- `Thread` requires identity, source/provider, CLI version, creation/update
  times and status. Model and reasoning effort are optional. It also exposes
  preview/path/cwd/Git metadata, which can be private.
- `Turn` requires ID, items and status. `startedAt`, `completedAt` and
  `durationMs` are nullable; timestamp descriptions specify Unix seconds.
  Its schema contains neither per-turn model fields nor token usage.
- Live `ThreadTokenUsageUpdatedNotification` requires thread and turn IDs and a
  breakdown with `last` and `total` counters. This proves a schema exists, not
  that historical reads recover those counters or this Desktop emits them.

Consequently, copying the thread's current model onto every historical turn
would invent attribution. Creation/update times cannot stand in for item event
times. Missing usage, per-turn configuration, cost, and acceptance evidence must
remain unknown. Native completed/failed turns are execution states, not verified
task labels. Task/session association remains an explicit ledger operation.

## Recommended next feasibility increment

For a separately approved desktop experiment, first establish whether a public
local transport can reach a deliberately created, sanitized desktop thread.
Inspect only that chosen thread through an allowlisted RPC client using
`initialize`, `thread/read`, and any strictly necessary list/pagination calls;
verify that a read does not resume work. Explicitly account for source filters,
archives, historical item availability, optional times/configuration, and usage
gaps. The documented default list can perform scan-and-repair, so investigate
`useStateDbOnly=true` before claiming listing has no persistence side effects.

If the public transport remains unavailable, prefer a scoped localhost OTel
experiment over reverse engineering app storage. A trusted project-local
metadata hook is another candidate when lifecycle coverage is enough, but needs
its own reliability/privacy fixture and no control output. These are proposed
spikes, not delivered integrations. Avoid global hooks or desktop settings
changes as part of the current workstream.

A later adapter should be accepted only after one real, sanitized desktop sample
demonstrates identity, field coverage, read-only behavior, privacy projection,
duplicate handling and gaps against the exact installed version. Until then,
report Desktop integration as **feasibility assessed; capture integration
unvalidated**, while the existing CLI source remains the supported real-data
path.
