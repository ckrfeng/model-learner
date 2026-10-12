# Selected conversation ingestion feasibility

Updated 2026-10-11 after separately approved selected-conversation reads. The
desktop's supported agent-mediated reader successfully returned three turns each
for the Codex CSV-parser test and ChatGPT Work Local scheduling-algorithms test.
Both responses report `kind: codex` and `hostId: local`; product surfaces remain
user-declared and transcript storage remains unknown. No adapter was implemented.

An ordinary Python process could invoke the installed supported app-server proxy,
but its default endpoint was absent. Independent programmatic access to either
selected history is therefore **unvalidated**, not impossible. The agent reader's
success does not establish a transport callable by Model Learner's Python CLI.
Automatic ingestion without an agent cannot yet be promised. The controlled-read
coverage below supersedes the earlier untested reader observations.

## Source and storage boundaries

The user confirms that Codex and ChatGPT/Work are modes of the same unified
ChatGPT desktop application on macOS, selected through its mode selector. This
establishes the intended product surfaces, not a shared conversation backend,
history store, supported API or device-only context. Both selected tests have
`codex://threads/` links; that shared navigation scheme supplies no backend proof.
Neither `~/Documents/Codex/` nor `~/.codex/` is established here as the storage
location of either selected history. Project working directories are not history
storage evidence. A default control-socket path likewise is not a transcript path.

Record the product surface, conversation backend, coordination location,
execution location and storage evidence separately. A local executor does not
establish local conversation storage. A Codex-backed local Work thread and a
ChatGPT-backed conversation using local tools require different treatment.

Official release notes describe local Work conversations remaining on the
computer and cloud Work conversations syncing across devices. They also describe
separate Codex history. This supports a local Work category, but does not promise
a complete locally readable transcript, a stable storage format or that every
conversation displayed in Work belongs to that category.
[Desktop history announcement](https://learn.chatgpt.com/docs/whats-new#july-13-17-2026).

Current Work documentation distinguishes local execution from cloud coordination
and explicitly warns against assuming device-only conversation/context storage.
Workspace retention rules and local artifact retention also differ. For an
individual selected chat, backend and mode evidence are still needed.
[Work overview](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-overview),
[Work local security](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security#data-handling-and-retention).

## Codex Desktop feasibility

Two supported candidates exist:

- The desktop exposes `read_thread(threadId, ...)`, described as reading recent
  status and turn summaries for a thread or chat, with cursors for older turns.
  Optional outputs and chat messages can be truncated. This is an available
  agent tool contract, not a promise of complete original messages or events.
  The controlled CSV-parser read below returned message-bearing structured items
  and explicit pagination, beyond what the short tool description guarantees.
- Public app-server documents `thread/read` without resuming or subscribing.
  `includeTurns=true` requests stored turns/items. Experimental
  `thread/turns/list` and `thread/items/list` support pagination; full item views
  must be requested where supported. `thread/list` defaults exclude `appServer`
  and can scan/repair metadata unless `useStateDbOnly=true` is used. Direct reads
  of a user-supplied ID avoid history enumeration.
  [Stored thread reads](https://learn.chatgpt.com/docs/app-server#read-a-stored-thread-without-resuming).

Public app-server is a documented protocol with read-only operations, within a
larger control API and experimental tooling. It is not a read-only server as a
whole. A future client needs an operation allowlist and must refuse execution,
resume, mutation and approval requests. Reachability of this desktop's actual
history through that protocol remains unestablished.

### Installed Codex schema evidence

Public schemas were generated from installed `codex-cli 0.162.0-alpha.17.2` into
`/private/tmp/model-learner-history-protocol-20261011`. These observations concern
schema definitions, not returned private data:

| Question | Installed schema evidence | Limit |
| --- | --- | --- |
| Selected conversation | `ThreadReadParams` requires `threadId`; optional `includeTurns` | Selected agent read succeeded; no selected app-server RPC tested |
| Messages | `ThreadItem` includes `userMessage.content`, `agentMessage.text`, phase and IDs | History may be partial; attachments need separate handling |
| Tool records | Command, file change, MCP, dynamic-tool and collaboration item variants expose IDs and statuses; some expose exits/durations | Persisted item state does not prove the original complete lifecycle event stream |
| Model metadata | Thread provider, nullable model and reasoning effort; CLI version | Model/effort descriptions explicitly mean current or latest persisted configuration, not per-turn execution telemetry |
| Timestamps | Thread creation/update seconds; nullable turn start/end seconds and duration milliseconds | Thread times are not message times; ordinary message variants have no timestamp field |
| Usage | Live token-usage notification has thread/turn IDs and counters | Stored `Turn` has no usage field; historical recovery is unestablished |
| Identity | Thread `id`; separate `sessionId` for a session tree | Neither is Model Learner's canonical task identity; use thread ID for conversation identity |
| Projects | Nullable native `projectId` | Native assignment is optional context, not a task association |
| Product origin | `originator`, nullable analytics `threadSource`, runtime `source` | No validated enum maps these to Work Local; `appServer` alone cannot distinguish the product surfaces |
| History mode | `legacy` or `paginated`; full hydration is deprecated for paginated history | Must detect capabilities and preserve cursors, page order and unsupported-method errors |

The protocol documents persisted local thread logs. No application database or
rollout was read. Desktop-specific completeness and any remote copies remain
unknown. An account export is not required by the documented local thread-read
protocol; it is not an established substitute for inaccessible Desktop history.

## ChatGPT Work Local feasibility

Work requires its own selected-source check. The exposed desktop `fork_thread`
contract explicitly distinguishes local Work tasks, which can be Codex tasks,
from ChatGPT-backed conversations, which cannot be forked by that tool even when
they use a local executor. This is evidence of differing backends, not permission
to fork or a history-export contract. No fork was performed.

The selected scheduling test succeeded through `read_thread`, returning structured
user/assistant message items, turn IDs/times and page direction. It reports
`kind: codex` on host `local`. That establishes the reader's backend classification
for this sample, not an API or storage mapping for every Work chat. Its actual
coverage is recorded below. The brief tool contract alone still cannot promise
verbatim fidelity, complete original events, model attribution or usage.

| Question | Work Local conclusion |
| --- | --- |
| Documented read-only access | Built-in desktop reader is available to this agent; public standalone Work history API not established |
| Selected existing conversations | Exact-ID agent read succeeded for the scheduling test; reader reports Codex kind/local host |
| Messages | Three user/assistant text pairs returned as message items; verbatim fidelity and complete source coverage are not independently established |
| Tool events | Optional truncated outputs are described; native calls, results and lifecycle provenance are not guaranteed |
| Model metadata | No historical model/settings guarantee in the reader contract; a Codex-backed source may expose thread settings, subject to the same attribution limits |
| Timestamps and usage | No complete per-message/per-turn measurement guarantee; preserve nulls |
| Task identity | Native conversation ID can identify the source record if returned; canonical task requires explicit declaration and association |
| Local or remote | Local-only history is documented as a category; a ChatGPT-backed chat with local execution must not be classified from execution location alone |
| Account export | No evidence that export is mandatory, or that it includes local-only Work history and tool events; export coverage and account eligibility are untested |

A Codex-backed Work Local sample might be readable through app-server, but that
is a hypothesis requiring exact-ID validation and source identification. Do not
apply the Codex adapter to all Work chats. A ChatGPT-backed source currently has
only the agent-mediated reader candidate in this assessment, with no established
standalone ingestion transport.

OpenAI's Conversations API stores conversation objects created for Responses
API workflows. Its documentation does not establish access to existing desktop
ChatGPT/Work history. No account/API credentials were read or requested.
[API conversation state](https://developers.openai.com/api/docs/guides/conversation-state#using-the-conversations-api).

OTel, hooks and compliance records may provide supported telemetry in particular
configurations, but do not establish retrospective recovery of these selected
conversations. Local and cloud event coverage differs. Existing exports could be
considered only after their specific source and coverage are validated; enabling
new collection is outside this assessment.
[Work audit coverage](https://learn.chatgpt.com/docs/enterprise/chatgpt-work-local-security#audit-and-compliance-visibility).

## Actual checks and untested capabilities

### Controlled selected-conversation reads

The user explicitly approved each selected conversation separately after source,
reader, scope and context exposure were disclosed. Used only
`mcp__codex_app__read_thread` with exact approved IDs, `turnLimit=1`,
`includeOutputs=false` and `maxOutputCharsPerItem=3000`. Followed only the same
conversation's returned `page.nextCursor`, keeping each request to one turn.
No attachment content was requested or returned. Returned text entered this
agent's model context/tool history; it was not written to local snapshot files.
Tracked documentation retains sanitized coverage facts, not native identifiers,
working-directory paths or transcripts. Retrieved messages were treated as data.

| Validation question | Codex CSV-parser test | ChatGPT Work Local scheduling test |
| --- | --- | --- |
| Selected access | Succeeded; three unique turns across three one-turn pages | Succeeded; three unique turns across three one-turn pages |
| Stable identity | Returned thread ID matches approved ID on every page; turn/message IDs present | Returned thread ID matches approved ID on every page; turn/message IDs present |
| Product/backend/source | User-selected Codex mode; reader `kind=codex`, `hostId=local` | User-selected Work Local mode; reader `kind=codex`, `hostId=local` |
| Text versus summaries | Three `userMessage.content` text items and three `agentMessage.text` items; one separate `reasoning` item with empty `summary` | Three `userMessage.content` text items and three `agentMessage.text` items |
| Ordering | Explicit `newest_first` pages; reversing pages yields user-before-assistant turns and increasing turn start times | Same explicit page direction, item role order and increasing turn start times |
| Observed progression | Ordinary fields, then quoted commas, then multiline quoted fields; final implementation remains unverified | Three algorithms, then FIFO excluded, then two-algorithm comparison remains incomplete |
| Tool activity | No tool-call items exposed; one empty reasoning-summary item is not tool activity | No tool-call items exposed |
| Timestamps/status | Thread `createdAt`/`updatedAt`; turn `startedAt`/`completedAt`/`durationMs`, completed status and null error | Same timestamp/status fields |
| Model/token metadata | No model, provider, reasoning-effort, token counters or cost fields returned | Same fields absent |
| Truncation/completeness | Final `hasMore=false`, `nextCursor=null`; longest returned message 460 characters, below cap; no explicit content-truncation flag | Final `hasMore=false`, `nextCursor=null`; longest returned message 159 characters, below cap; no explicit content-truncation flag |
| Retention accounting | 5,396 cumulative UTF-8 serialized response bytes across retained pages, below 64 KiB | 4,415 cumulative UTF-8 serialized response bytes across retained pages, below 64 KiB |
| Standalone Python selected access | Not established; supported proxy child failed at absent default endpoint before any conversation RPC | Same endpoint limit; Codex backend classification makes app-server a candidate, not a proven Work-history transport |
| Automatic ingestion/integration | No autonomous live-history adapter justified yet; selected-snapshot projection possible only through current agent path | Same limitation; preserve Work product declaration independently of Codex backend |

The first Work one-turn request reached the tool wrapper, but its byte-counting
helper failed before retaining/displaying the response. Retried that same initial
one-turn request; it did not expand scope. Counts above refer to the three retained
pages and three unique turns. Work had four reader invocations, Codex three.

These are message-bearing source records, not merely generated retrieval summaries;
they do not independently prove exact equivalence to the original UI transcript.
Exhausting the reader's visible cursor establishes only the end of its exposed
history, not a complete original conversation, hidden items or all historical
measurements. No truncation marker was observed; absence of one does not prove
lossless capture. Message timestamps, historical model settings, usage and cost
remain unknown. No exposed tool items does not establish zero original tool calls.
Thread/turn statuses and textual completion claims do not establish verification.
The reader's returned working directories describe project context, not transcript
storage; no transcript-storage location or cloud-copy behavior was established.

### Controlled validation follow-up: transport checks

The user supplied exact deep links for the Work Local scheduling-algorithms test
and Codex CSV-parser test. Those selections are user-declared sources; the later
approved reads above establish reader backend classification and returned fields,
while storage and standalone selected access remain unverified.
Separate approval requests identify the supported agent reader
`mcp__codex_app__read_thread`, disclose model-context/tool-history exposure and
specify one initial turn, outputs disabled, at most ten turns and 64 KiB retained
text per conversation, without attachments or control operations. Supplying a
link alone is not treated as read approval. Native identifiers and transcripts
are not reproduced in this tracked report.

Fresh public CLI help/version checks exited 0 on the installed
`0.162.0-alpha.17.2`. `codex app-server daemon version` again exited 1: its documented
default control socket was absent. An ordinary local `python3` process then invoked
the documented installed `codex app-server proxy` command through `subprocess.run`
with empty input and a ten-second timeout. The child exited 1 with zero stdout
bytes and a missing-socket diagnostic; the Python wrapper exited 0. No JSON-RPC
conversation request was sent. This demonstrates a callable proxy executable,
not successful history access or an API for the agent-only desktop reader.

Official App Server documentation defines JSONL over stdio and stored-thread reads
without resuming. Installed public schemas define exact-ID `thread/read` and
experimental paginated `thread/turns/list` / `thread/items/list`. These are supported
protocol candidates that a Python client can speak; access to the selected desktop
histories remains unestablished. `thread/read(includeTurns=true)` has no turn limit;
full history would violate the one-turn initial bound. Pagination can limit turns,
but the inspected request schemas have no tool-output/attachment suppression flag,
so protocol availability alone does not meet this validation's content limits.
[App Server transports and stored reads](https://learn.chatgpt.com/docs/app-server).

No daemon/server was started, alternate socket or storage root guessed, private
database/configuration/authentication secret inspected, or network traffic
intercepted. No supported standalone ChatGPT-backed Work history transport has
been established. A missing default endpoint does not prove other supported
endpoints cannot exist. Automatic selected-history ingestion cannot yet be promised
for either source; an agent snapshot handoff would still require an agent and does
not fulfill the requested independent local application requirement.

### Earlier feasibility checks

| Executed read-only check | Actual result |
| --- | --- |
| Repository audit | Read plan, instructions, status, prior Desktop feasibility, observation adapter/contracts, execution projections, text retrieval, annotations and CPU encoder |
| CLI location/version | Bundled ChatGPT executable; version `0.162.0-alpha.17.2`; exit 0 |
| Public app-server/proxy/daemon help | Exit 0; proxy and public schema generation advertised |
| Schema generation | Exit 0; public definitions generated outside Git |
| `codex app-server daemon version` | Exit 1; documented default control socket absent, `No such file or directory` |
| Desktop tool capability inspection | Read tool descriptions only; no thread listing, archive listing or conversation read |

Help/schema commands emitted a sandbox PATH-alias warning. This does not prove
history connectivity. The failed daemon query establishes an absent default
endpoint, not the absence of every supported desktop transport.

The earlier feasibility stage tested no real historical payload or pagination.
The approved follow-up above now validates bounded selected agent reads; archive
access, complete source coverage, usage/model attribution and standalone selected
history remain untested. Existing CLI smoke evidence establishes CLI capture only.
Repository regression results are recorded in `STATUS.md`; they are not Desktop
or Work integration validation.

## Shared representation proposal

Use an explicitly selected, versioned conversation snapshot before task
interpretation. This is a proposed format, not a delivered contract or migration.
Both sources should retain:

- Product source (`codex_desktop` or `chatgpt_work_local`), actual backend or
  `unknown`, adapter/interface versions, local opaque account/workspace/host scope,
  native conversation ID and separate native session-tree ID where present.
- Snapshot identity, retrieval receipt, completeness/truncation flags, selection
  scope and retained original cursor/turn/item/message IDs.
- Source-provided ordering and its basis, including page direction and branches
  where exposed. Flatten only an explicitly identified conversation path. Missing
  order is unknown; timestamps or UUIDs must not invent it.
- Native timestamps and units separately from retrieval/ingestion availability.
  Missing, not emitted, redacted, truncated and unsupported fields need distinct
  reasons. Import today does not make evidence available to earlier predictions.
- Original record kind, role/actor and observed tool status, exit, usage or model
  setting only at the scope actually supplied. A summary remains a summary;
  a historical item snapshot must not manufacture item-start/item-end events.
- Optional native project reference, privacy policy, retention choice, sanitized
  text locators/digests and excluded attachment/content indicators.

Normalize conversation identity into the existing `Session` concept, with a
source/backend/scope namespace to prevent cross-source collisions. Canonical
`Task` identity remains separately declared. Existing `TaskSessionLink` allows
many-to-many associations; bounded `Run` and `RunSessionLink` describe authorized
execution segments. The current overlap checks must continue protecting shared
conversations. Optional native project context can remain metadata until an
operator explicitly maps it to `Project`/`ProjectTaskLink`.

Related-topic, continuation and shared-capability suggestions stay inferred
records with supporting locators. They never create task links, merge IDs or
transfer success labels. A conversation title or first prompt is not an
automatically authoritative task objective. Select and review the relevant
message range; retain distinct objectives when a conversation contains several.

### Existing compatibility limits

`adapters/codex.py` accepts only `codex-exec-capture/v1` and identifies its source
as `codex.exec`. `execution/analyzer.py` checks that exact source and projection.
The real observation builder also requires explicitly linked Codex CLI sessions.
Renaming Desktop/Work snapshots to `codex.exec` would invent provenance and cannot
be used to obtain existing execution counts or learning eligibility.

The text path is reusable sooner: explicitly reviewed bounded text can enter
`TaskText`/`RetrievalIndex`; canonical objectives can enter `TaskDescription` once
a task is actually declared. `CheckpointSummary` supports explicit sanitized
author reports with availability receipts and scoped evidence references. It
does not automatically interpret conversation prose into phase/progress labels.
The annotation evaluation format requires project/family/lineage labels; optional
source projects must not be silently turned into these evaluation groups.

Historical snapshots are suitable first for retrospective text inspection.
Prospective task-state prediction requires honest earlier availability, task/run
scope and independent outcome evidence. Native message time alone cannot recover
those declarations. No such receipts may be backdated.

## Local understanding supported by the evidence

| Available material | Reusable capability | Remaining limit |
| --- | --- | --- |
| Reviewed objective excerpts | Token overlap, TF-IDF, optional pinned Potion related-text shortlist | Similarity is not identity or calibrated confidence |
| Reader-generated turn summaries | Search over the returned summaries, with summary provenance | Omitted details cannot be recovered or treated as original statements |
| Reviewed checkpoint reports | Reported obstacles and structured author hypotheses; deterministic comparisons | Free text is not already a validated phase, scope or difficulty classifier |
| Validated structured tool records | Observed activity/status counts and missingness after a source-specific projection is accepted | Stored terminal records cannot reconstruct unseen retries, lifecycle events or causes |
| Bound independent verifier evidence | Named acceptance results for the correct artifact/run | Chat claims that tests passed are not that evidence |

Reuse the existing optional `minishlab/potion-base-8M` CPU encoder with its already
approved local revision/bundle pins. It produces 256-dimensional static embeddings
over bounded text; the existing path accepts at most 4096 characters and truncates
model input to 256 tokens. It is suitable for relatedness experiments, not a
conversation reasoning engine. No larger model, download or fine-tuning is needed.

Existing synthetic retrieval evidence supports an optional shortlist with many
incorrect first results. Longitudinal classifications currently come from explicit
reports and deterministic rules; embeddings add diagnostic cosines. Complex
reasoning, actual progress, scope changes, causal failure explanations and
cross-conversation continuation remain unvalidated inference capabilities.

## Privacy and controlled validation proposal

### Obtaining the two selected identifiers

Follow-up discovery assessment on 2026-10-11 inspected supported tool contracts,
official documentation and the previously generated public protocol schemas only.
At that discovery stage neither test conversation had been identified or read;
the subsequently approved selected reads are recorded above.

The desktop `list_threads` tool has only a non-pinned result limit: it has no title
or source filter, returns all pinned chats and may include generated summaries.
It cannot provide the requested narrowly targeted metadata-only search. Filtering
its response afterward would not undo access to unrelated entries or summaries.

Public app-server `thread/list` supports an extracted-title `searchTerm`, a page
limit and source filters. `useStateDbOnly=true` avoids the default rollout
scan/metadata repair. However, the installed response schema requires `preview`,
described as usually the first user message, and the request has no field-selection
or preview-suppression parameter. Such a response is not strictly metadata-only;
`appServer` also does not identify Codex versus Work. Connectivity to the selected
desktop history remains unvalidated. No search RPC or endpoint probe was performed.
[Documented title filtering](https://learn.chatgpt.com/docs/app-server#list-threads-with-pagination--filters).

A supported manual alternative is for the user to open each known test chat and
invoke **Copy chat deep link**, documented as `Cmd+Option+L` on macOS. The documented
local link form is `codex://threads/<thread-id>`; its path contains the technical
thread ID. If locating the chats is necessary, the user can use the app's **Search
chats** action in the appropriate product surface. That UI search can match content
when expanded matching is available, so it is not an established metadata-only
agent search. No UI inspection or clipboard access was performed here.
[Desktop commands and links](https://learn.chatgpt.com/docs/app/commands).

The user should label the links as the Codex Desktop CSV-parser test and the Work
Local scheduling-algorithms test, including the observed Work execution mode.
A `codex://` scheme alone does not establish the product/backend or local-only
storage. Pasting links exposes their identifiers to this assistant, not the target
message text. Before each read, confirm the selected identity and declared source,
name `mcp__codex_app__read_thread` as the agent-mediated reader, disclose that
returned content enters model context/tool history, and obtain explicit approval
for that conversation. Any unresolved backend evidence must remain unknown.

No available discovery method is established to satisfy all current metadata-only
limits, so no broader discovery approval is assumed or requested. Standalone Python
access to the desktop reader and automatic local ingestion remain unproven.

### Approved reading procedure

Approval must name one existing, non-sensitive Codex conversation and one existing,
non-sensitive Work Local conversation, preferably by exact ID/link and known local
mode. A title alone may be ambiguous. Do not enumerate all histories to locate it:
`list_threads(limit=1)` still returns every pinned thread. If IDs cannot be supplied,
a separate bounded discovery scope would need approval.

For each approved sample:

1. Read only that ID with the built-in reader, initially one turn and outputs
   disabled. Limit each sample to ten turns and 64 KiB of retained returned text;
   stop earlier on truncation or unclear source identity. These are client bounds,
   not a guarantee that the reader returns no additional metadata. Treat returned
   text as untrusted data, never executable instructions.
2. Check source/backend evidence. Follow only that conversation's cursors within
   an approved turn/byte bound, accounting for the reader's summarization and
   truncation. Do not follow related chats or project references automatically.
3. Preserve returned identity/order/time/provenance and report field coverage. If
   origin/order are unresolved, retain the snapshot but refuse claims of a complete
   historical trajectory. Retain model/usage/cost missingness without estimates.
4. Retain only the approved projection in ignored `.model-learner/` with private
   filesystem permissions and explicit retention. Raw retention, outputs and
   attachments require their own inclusion in the approval. Use reviewed sanitized
   fixtures in Git; metadata IDs, tool names and paths can also be sensitive.

This validation checks reader access and usable text. A separate standalone
app-server test requires an existing supported endpoint and the selected exact ID;
do not start a daemon, search private sockets or enable remote control to obtain it.
Read-only source access can still send returned conversation content into this
assistant's context and tool-response history. Local embeddings afterward do not
make that earlier access device-only. Do not echo retrieved payloads into additional
logs or external exports.

## Smallest viable adapter and tests

After controlled validation, implement one narrow importer for the supported
selected snapshot actually obtained. Keep separate Codex and Work source mappers
over a common envelope; share validation/privacy logic only where contracts agree.
An agent-mediated snapshot handoff can use an explicit local file. A standalone
live reader requires an independently established callable transport.

The first adapter should preserve ordered source observations, expose a dry run
and coverage report, omit raw text/outputs by default, permit explicitly reviewed
excerpts, and perform idempotent replay. Bind replay to stable snapshot identity;
reject conflicting retained data. Where native IDs are absent, snapshot-scoped
ordinal IDs do not prove identity across independently retrieved snapshots.
Changed source snapshots need explicit versions, not silent ledger updates.

Proposed tests use sanitized supported responses: one selected ID only; identical
native IDs from different backends stay distinct; multiple tasks per conversation
and one task across conversations remain explicit; optional projects stay optional;
page direction/order and truncation survive; missing times/usage/configuration stay
null; summaries stay summaries; no synthetic lifecycle events; replay/conflict
handling; private payload omission and content-free diagnostics; no control RPC;
future receipts cannot enter earlier checkpoints; similarity creates no links or
outcomes. Each source needs its own approved real read in addition to fixtures.

Immediately usable without new integration: manually reviewed sanitized task
descriptions, related-text retrieval and explicit summary/annotation contracts.
Controlled reads now justify the shape of an agent-mediated selected-snapshot
projection over message items, page order, native IDs, turn times and missingness.
That handoff still requires an agent and does not fulfill the user's independent
local-application requirement; no adapter is implemented or authorized here.

For each tested source, the smallest independent integration candidate is a
bounded Python client over a user-provided supported existing App Server endpoint,
restricted to initialization and exact-ID stored-read/pagination operations. It
first needs selected-ID reachability and product/backend mapping validation, plus
a way to obey output/attachment exclusions; client-side filtering cannot be
represented as server-side suppression. Preserve the two product surfaces as
separate provenance even if both report Codex backend. Do not guess a storage
root or bypass the missing endpoint through private databases. Until those
conditions are established, automatic local ingestion remains unvalidated for
both sources. Complete historical event/measurement recovery, source-neutral
execution projection and prospective-learning eligibility also remain unproven.
Stop after this validation report; no adapter, new model, routing or Governor.
