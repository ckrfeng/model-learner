# Selected conversation ingestion feasibility

Updated 2026-10-11 after the approved minimal importer and complete exposed
three-turn validation. **A standalone selected-ID importer is implemented**, using
temporary `codex app-server --listen stdio://` processes and documented read-only
RPCs. Both selected Codex-backed tests expose three turns and six user/assistant
messages. Exact text matches across two independent reads; original UI verbatim
fidelity remains unverified. No model invocation or running desktop daemon is
needed. Product source remains separate from backend and storage-location evidence.

Default reads omit turn items server-side and retain metadata only. Explicit text
reads use full view and retain text only in Python memory unless a separate storage
opt-in is supplied. **There is no server-side message-only filter**: other item
content can be returned before local exclusion. Live validation retained only
metadata in ignored local storage; opt-in text retention was tested exclusively
with authored sanitized fixtures. Earlier experiments below are historical;
delivered behavior and final validation are recorded in the last section.
The earlier proxy failure concerned only an absent default daemon endpoint.
The standalone findings below supersede earlier endpoint-based limitations.

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
resume, mutation and approval requests. Independent stdio reachability of the
selected CSV-parser thread and its three turn records is now validated. Complete
original message coverage and historical measurements remain unproven; all three
exposed turns have now been validated for both samples through the importer.

### Installed Codex schema evidence

Public schemas were generated from installed `codex-cli 0.162.0-alpha.17.2` into
`/private/tmp/model-learner-history-protocol-20261011`. These observations concern
schema definitions, not returned private data:

| Question | Installed schema evidence | Limit |
| --- | --- | --- |
| Selected conversation | `ThreadReadParams` requires `threadId`; optional `includeTurns` | Agent read and independent stdio metadata/paginated-turn reads succeeded for both tests |
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
| Documented read-only access | Agent reader succeeded; independent public App Server stdio metadata/turn reads succeeded for this Codex-backed Work test |
| Selected existing conversations | Exact-ID agent and standalone reads succeeded; App Server reports originator `codex_work_desktop` |
| Messages | Three user/assistant text pairs returned as message items; verbatim fidelity and complete source coverage are not independently established |
| Tool events | Optional truncated outputs are described; native calls, results and lifecycle provenance are not guaranteed |
| Model metadata | No historical model/settings guarantee in the reader contract; a Codex-backed source may expose thread settings, subject to the same attribution limits |
| Timestamps and usage | No complete per-message/per-turn measurement guarantee; preserve nulls |
| Task identity | Native conversation ID can identify the source record if returned; canonical task requires explicit declaration and association |
| Local or remote | Local-only history is documented as a category; a ChatGPT-backed chat with local execution must not be classified from execution location alone |
| Account export | No evidence that export is mandatory, or that it includes local-only Work history and tool events; export coverage and account eligibility are untested |

The selected Codex-backed Work Local sample is now independently readable through
App Server for metadata and turn records. This is sample-specific evidence; do not
apply it to all Work chats or infer shared storage from the mode selector. A
ChatGPT-backed source still has no established standalone history transport here.

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
| Standalone Python selected access | Later independent stdio experiment below succeeds for selected thread/turn metadata; message bodies untested | Same later success for this Codex-backed Work sample |
| Automatic ingestion/integration | Later stdio evidence justifies narrow metadata ingestion; full text ingestion needs further validation | Same scope; preserve Work product declaration independently of Codex backend |

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

This earlier stage tested a proxy to an existing daemon, not an independent stdio
server. The later approved stdio result below supersedes its selected-access limit.

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

At that stage no daemon/server was started, alternate socket or storage root
guessed, private database/configuration/authentication secret inspected, or network traffic
intercepted. No supported standalone ChatGPT-backed Work history transport has
been established. A missing default endpoint does not prove other supported
endpoints cannot exist. Automatic selected-history ingestion cannot yet be promised
for either source; an agent snapshot handoff would still require an agent and does
not fulfill the requested independent local application requirement.

### Approved independent Python stdio experiment

The user explicitly approved launching a bounded temporary server and reading
these two exact selections, with private content excluded from terminal output,
reports, Git and model context. Used existing **Python 3.9.6 standard library** and
the installed **Codex CLI 0.162.0-alpha.17.2**, without another runtime or package.
Exact child command:

```text
/Applications/ChatGPT.app/Contents/Resources/codex-cli/CodexCLI.app/Contents/MacOS/codex app-server --listen stdio://
```

Transport was newline-delimited JSON over Python-created subprocess stdin/stdout
pipes. Sent `initialize` with client metadata and `experimentalApi=true`, waited
for its successful response, then sent `initialized`. No authentication secret
was inspected. Sent **both** exact-ID `thread/read(includeTurns=false)` requests
before pagination. Metadata responses contain preview text even though turns
are excluded; Python received that privately and emitted only coverage facts.

Next sent `thread/turns/list(limit=1, sortDirection=desc, itemsView=notLoaded)` per
selected ID. Each initial page had one turn. A second bounded run followed only
those selected turn cursors, still one turn per request, until three unique turns
and null continuation cursors per conversation. `itemsView=notLoaded` omitted
all items server-side. Installed request schemas expose no message-type,
attachment or tool-output filter, so `summary`, `full` and `thread/items/list`
were not used. Client-side filtering would not prevent initial retrieval.
[Documented stdio, handshake and stored-history pagination](https://learn.chatgpt.com/docs/app-server).

| Validation | Codex CSV-parser test | Work Local scheduling test |
| --- | --- | --- |
| Independent thread read | Success; returned ID equals approved ID | Success; returned ID equals approved ID |
| Backend/source fields | `originator="Codex Desktop"`, `source="vscode"`, `threadSource="user"` | `originator="codex_work_desktop"`, `source="vscode"`, `threadSource="user"` |
| History/runtime | `historyMode="paginated"`, status `notLoaded`, metadata read has empty turns | Same |
| Turn availability | Three unique persisted turn records, one per page | Same |
| Comparison to agent reader | Latest turn ID and all three start/completion/duration tuples match | Same |
| Order/completeness | Descending pagination; reversing pages produces increasing start times; final cursor null | Same |
| Text availability | Nonempty thread preview received privately; message items intentionally omitted | Same |
| Model fields | `model="gpt-6.1-sol"`, `modelProvider="openai"`, `reasoningEffort="high"` | Same |
| Time/identity fields | Thread creation/update/recency, fields for sessionId/path/projectId; turn ID/rootTurnId/status/error/start/completion/duration | Same |
| Missing/excluded fields | No thread/turn token or usage fields; no message items, message timestamps or tool events fetched | Same |
| Truncation | No explicit turn-truncation field; end of exposed pagination only; preview truncation/fidelity unknown | Same |
| Expanded-run response accounting | 2,705 UTF-8 bytes total, including metadata response and three turn pages | 2,725 UTF-8 bytes total |

Across both successful stdio runs, cumulative response accounting was 4,390 bytes
for Codex and 4,430 bytes for Work, well below 64 KiB each; repeated initial pages
still covered only three unique turns. One-turn pages are server-limited; ten-turn
and retained-text ceilings were enforced by the temporary client. No raw response
files were produced. The one-off probe lived outside Git and was removed after
execution; it is not a Model Learner adapter or retained test fixture.

The `source=vscode` value is a returned runtime/source classification, not evidence
that the user opened VS Code. Preserve it alongside product originator and the
earlier agent reader's `kind=codex`/`hostId=local`; these fields have different
semantics. This Work test demonstrates independent access to one Codex-backed
Work record, not all Work records or every backend. API-returned native paths
were not opened or used to inspect storage. No history directory was guessed.

Thread model/effort fields describe current/latest persisted settings under the
public schema; they do not attribute each historical turn to that configuration.
No token/cost measurements were recovered; opaque extra/environment fields were
not interpreted, and optional field presence does not prove populated values.
The null final cursor exhausts exposed turn pagination but does not establish
complete original messages, branches,
hidden events, tool activity, model changes or usage. Message items were omitted
deliberately, not absent from the original conversation. Preview text alone is
not a full conversation or a validated text-ingestion projection.

Read-only behavior was checked through the sent-method allowlist: only
`initialize`, `initialized`, `thread/read` and `thread/turns/list`; unexpected
server-initiated client requests would stop the probe. There was no thread listing,
resume/start, turn execution, mutation, tool execution, private database/rollout
parsing, credential inspection or socket discovery. The server returned
`notLoaded` status after metadata reads. No model inference operation was sent.
This is an RPC behavior check, not an audit proving the server performs zero
incidental filesystem writes during startup.

The enclosing execution sandbox initially blocked server initialization with an
`Operation not permitted` diagnostic; a diagnostic-only retry also exited 1 before
any conversation RPC. The same approved supported stdio experiment then ran with
scoped execution-sandbox escalation. Both successful server processes shut down
on stdin EOF and exited **0**, with termination confirmed. No persistent daemon,
new runtime, application setting change or unsupported access method was added.

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
The approved follow-ups above now validate bounded selected agent reads and
independent selected metadata/turn reads. Archive access, complete source coverage,
historical usage/model attribution and standalone message bodies remain untested.
Existing CLI smoke evidence establishes CLI capture only.
Repository regression results are recorded in `STATUS.md`; they are not Desktop
or Work integration validation.

### Approved selective text validation: one full turn per source

The user separately approved one full-view turn from each of the same two exact
test conversations and required another approval before importer implementation.
Rechecked the installed **Codex CLI 0.162.0-alpha.17.2** public schemas and official
[App Server documentation](https://learn.chatgpt.com/docs/app-server#list-thread-turns).
`thread/turns/list` supports `notLoaded`, `summary` and `full`; summary is a display
summary, while full includes every available persisted item for the requested
turn. `thread/items/list` supports a turn restriction and item pagination but no
message-type filter. Neither request schema provides attachment, reasoning or
tool-output suppression. Client filtering does not prevent server retrieval.
`thread/items/list` and summary view were inspected, not invoked.

An ordinary Python 3.9.6 standard-library process launched a bounded temporary
`codex app-server --listen stdio://` subprocess. It completed the documented
handshake with experimental pagination enabled, then issued exact-ID
`thread/read(includeTurns=false)` and
`thread/turns/list(limit=1, sortDirection=desc, itemsView=full)` per selection.
Only the latest exposed turn was fetched; no continuation cursor was followed.
The allowlist remained `initialize`, `initialized`, `thread/read` and
`thread/turns/list`. Server-initiated requests were prohibited; one notification
was discarded without displaying its payload. Scoped execution-sandbox escalation
was used for the already approved temporary process, as required in the prior
experiment. The server exited **0** on stdin EOF; the probe exited **0**.

| Sanitized coverage | Codex test | Work Local test |
| --- | --- | --- |
| Identity/product checks | Returned thread ID matches selection; originator matches `Codex Desktop` | Returned ID matches selection; originator matches `codex_work_desktop` |
| Other source/history checks | `source=vscode`, `threadSource=user`, paginated history | Same |
| Requested/returned scope | One latest turn; returned `itemsView=full`; older-turn cursor present | Same |
| Source item ordering | User ordinal 0, assistant ordinal 1; unique native message IDs | Same |
| User text field | One nonempty string, 117 characters / UTF-8 bytes | One nonempty string, 135 characters / UTF-8 bytes |
| Assistant text field | One nonempty string, 460 characters / UTF-8 bytes | One nonempty string, 144 characters / UTF-8 bytes |
| In-memory extracted text | 577 UTF-8 bytes | 279 UTF-8 bytes |
| Metadata plus full-turn serialized response bytes | 2,625 | 2,327 |
| Turn times | Start, completion and duration populated | Same |
| Message timestamps | Absent; remain unknown | Same |
| Other item / non-text user-part counts | Zero / zero in this returned turn | Zero / zero in this returned turn |
| Explicit message truncation marker | None exposed | None exposed |

The probe extracted only `userMessage.content` parts with `type=text` and
`agentMessage.text`, preserving strings without normalization or clipping. Local
JSON round-trip equality passed for all four strings; this checks extraction,
not fidelity to the original UI. No original-message baseline was supplied for
independent equality testing. The Codex assistant length agrees with the earlier
reader's reported 460-character maximum; matching length does not prove matching
content. Latest user text differs from thread preview for both, which is expected
for a preview usually drawn from the first user message, not a fidelity failure.

No response body, preview, extracted text, native ID, returned path or native error
was printed or written to a file. Bodies remained in Python memory. The temporary
probe source was removed after execution. Ten-turn / 64-KiB ceilings were enforced;
actual scope was one turn per conversation. Zero ignored items in these selected
turns does not promise exclusion or absence elsewhere. No execution, resume,
mutation, unrelated enumeration, task association or learning record was produced.

Supported standalone message-text access is established for one exposed turn per
sample. Full three-turn text history, independent verbatim fidelity, historical
model/usage/cost attribution and other Work backends remain unvalidated. No
importer or fixture is implemented. Next gate: user approval for the minimal
importer and bounded three-turn validation of these same two selections.

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
limits, so no broader discovery approval is assumed or requested. The later
independent stdio experiment validates selected metadata ingestion without making
the agent-only desktop reader callable by Python.

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

This validation checks reader access and usable text. A standalone app-server
test requires separate explicit process/read approval and the selected exact ID.
The user approved the independent temporary stdio subprocess experiment above;
an existing daemon socket is not required. Do not start a persistent daemon,
search private sockets or enable remote control to obtain access.
Read-only source access can still send returned conversation content into this
assistant's context and tool-response history. Local embeddings afterward do not
make that earlier access device-only. Do not echo retrieved payloads into additional
logs or external exports.

## Delivered minimal importer and three-turn validation

The user approved implementation, metadata-only live storage, complete exposed
three-turn validation for both selections, sanitized fixture text retention, full
checks and independent review. The delivered code uses existing `Session` and
immutable `Event` records; no schema migration or dependency was added.

- `adapters/app_server.py` implements the documented JSONL stdio handshake and
  exact-ID read subset. The unchanged allowlist permits only `initialize`,
  `initialized`, `thread/read(includeTurns=false)` and `thread/turns/list`.
  Requests have one selected UUID, one turn per descending page, at most ten pages,
  a timeout and a cumulative 64-KiB wire ceiling. It ignores notification bodies,
  rejects server-initiated requests and suppresses native error text. Each server
  terminates after its selected read; no persistent daemon, execution or mutation.
- `adapters/conversations.py` validates the two product-specific originators over
  the shared, observed Codex backend. Only the tested `vscode`/`user`/`paginated`
  source shape is supported. Other origins, history formats and unexpected item
  formats fail closed. `Session` identity includes source, backend, product,
  machine scope and native conversation ID, independently of task identity.
- The versioned `codex-conversation-snapshot/v1` payload is one historical snapshot,
  not a reconstruction of original execution events. It retains native thread/tree,
  turn and exposed message IDs; reverses descending pages for source turn order;
  preserves native item ordinals and timestamp units. Retrieval receipts stay
  distinct from original times. Thread update time never becomes conversation end
  time. Missing message times/configuration/usage/cost remain unknown. Bounded
  history, unrequested items, retention-disabled text, non-text exclusion counts
  and explicit truncation markers remain visible. No marker means unknown fidelity.
- Default reads use `notLoaded`. Full-item reads are explicit and extract only
  user text parts and assistant text without normalization. Preview, title, paths,
  current model settings, raw responses and other item bodies are omitted from
  storage. Opt-in retains only message strings. The database must be untracked and
  ignored under the workspace's `.model-learner/`; symlinks/public paths are
  rejected, with private directory/database permissions.
- `Repository.add_session_snapshot` performs atomic creation/replay with integrity
  checks. A deterministic content identity covers retained facts and retention/view
  policy, independent of receipt time and opaque cursor strings. Identical replay
  preserves the first receipt. Changed facts append an explicit immutable snapshot
  version. Unsupported/colliding persisted rows are rejected transactionally.
- `import conversation` exposes selected ID, declared source and machine identity;
  optional `--read-text` keeps text in memory, and separate `--retain-text` stores
  it locally. `sessions` and `session show` inspect imported snapshots with explicit
  unknowns. No automatic task/project/run links, verifications, outcomes or learning
  observations are created. Existing CLI execution projections reject this source.

### Actual live evidence

Used Python **3.12.14**, installed CLI **0.162.0-alpha.17.2** and the existing local
environment. Four approved temporary servers performed two fresh full-view reads
per selection. Each read fetched three one-turn pages, ending at a null cursor;
all server processes exited **0**. Execution-sandbox escalation covered only the
approved bounded subprocess experiment. Private responses and diagnostics stayed
in Python memory. The temporary validation script was removed after use.

| Sanitized live evidence | Codex test | Work Local test |
| --- | --- | --- |
| Identity and product/source validation | Passed | Passed |
| Exposed history | Three unique turns, six unique messages | Same |
| Message roles per source-ordered turn | User then assistant, all three turns | Same |
| Native turn times | All start/completion/duration fields populated; starts increase | Same |
| User/assistant UTF-8 bytes, oldest to newest | 159/234, 96/464, 117/460 | 159/105, 120/78, 135/144 |
| Extracted text in memory per read | 1,530 bytes | 741 bytes |
| Wire bytes across two fresh reads, including handshake/notifications | 11,712 | 9,856 |
| Exact text equality across fresh reads | All six strings matched | Same |
| Latest-turn lengths vs approved one-turn probe | Matched | Matched |
| First user text vs thread preview | Not equal; preview is not an exact baseline | Same |
| Ignored non-message item counts, oldest to newest | 0, 1, 0 | 0, 0, 0 |
| User non-text parts | Zero exposed | Zero exposed |
| Explicit turn truncation markers | None exposed | None exposed |
| Initial import / fresh replay | One metadata snapshot / zero new snapshots | Same |

The ignored private ledger contains exactly two sessions and two metadata
snapshots. Every retained message text field is null, every raw payload is null,
and no recovered live string appears in canonical event JSON or SQLite bytes.
There are zero task/run/verification/outcome/real-learning records. No live text was
retained. These checks cover the client's storage, not incidental App Server
startup writes or existing source storage. Native paths were not followed.

All three exposed turns and repeatable text are validated for these two samples.
Original UI verbatim fidelity is still **unverified**: no independent original
baseline was supplied, and preview equality failed. Current full-view Codex turn 2
exposes 464 assistant bytes; the earlier agent reader reported a 460-character
maximum across its view. Different interface coverage cannot establish original
equality or explain that difference without another baseline. Do not infer hidden
history completeness from exhausted cursors. No absence-of-original-tools claim
follows from the small exposed item counts.

### Checks and independent review

Sanitized authored fixtures and an offline fake stdio peer exercise both source
originators, exact Unicode/newline/trailing-space fidelity, exclusions, nullable
timestamps, truncation, native order, bounds, malformed formats, private diagnostics,
storage restrictions, atomic rollback, fresh replay and text opt-in. Independent
review ran **41 focused tests**, then rechecked the varying-cursor regression
(**1 passed**). Both findings were fixed: untrusted types receive content-free
rejection, and opaque transport tokens cannot change snapshot identity. The final
review reported **no remaining actionable findings** in scope and accessed no live
conversation or existing private ledger.

- `uv run pytest`: **805 passed, 7 skipped in 48.43s**. Optional host/model checks
  remain disabled; this task invoked no new model or real agent execution.
- `uv run ruff check .`: passed.
- `uv run ruff format --check .`: passed, **162 files formatted**.
- `git diff --check`: passed.

Used existing repository-local uv/cache paths. Full/summary content filtering,
ChatGPT-backed Work history, every Work source/storage mode, original lossless
coverage, historical model attribution, usage/cost recovery and retrospective
verified-success eligibility remain unsupported or unestablished. Summary view
and `thread/items/list` were schema-inspected, not runtime-validated. There is no
global scanning, project grouping, routing, Governor, new CPU model, fine-tuning or
cloud inference. Stop after this importer; no later milestone is started.
