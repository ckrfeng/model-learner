# Selected conversation ingestion feasibility

Assessed 2026-10-11. Model Learner can investigate selected existing Codex Desktop
and ChatGPT Work Local conversations through supported readers. Neither source
has been validated for historical ingestion in this assessment. No conversation
was selected or read, and no integration was implemented.

The smallest next step is an approved read of one non-sensitive conversation per
source through the desktop's built-in reader. This can establish partial text
availability. Full ordered history, execution events and historical measurements
need separate evidence before an adapter promises them. A supported reader inside
an agent session does not establish an interface callable by Model Learner's
standalone Python CLI.

## Source and storage boundaries

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
| Selected conversation | `ThreadReadParams` requires `threadId`; optional `includeTurns` | No selected Desktop ID tested |
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

The exposed `read_thread` contract accepts one thread or chat ID and documents
older-turn cursors. It is therefore a supported candidate for a selected Work
read in this environment. Its summary/truncation contract cannot establish exact
original messages, tool arguments/results, event timing, model attribution or
usage. There is no response schema in that tool description promising these
fields, and no Work conversation was read to inspect actual coverage.

| Question | Work Local conclusion |
| --- | --- |
| Documented read-only access | Built-in desktop reader is available to this agent; public standalone Work history API not established |
| Selected existing conversations | Reader accepts an exact ID; success for a selected local Work conversation is untested |
| Messages | Chat text/turn summaries are described; exact/full message coverage is untested |
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

No real historical payload, ordering, pagination, archive access, identity mapping,
timestamp coverage, usage, model changes or privacy projection was tested for
either source. Existing CLI smoke evidence establishes selected CLI capture only.
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
Ready to propose after validation: a selected-snapshot text adapter. Still blocked:
validated Desktop/Work ingestion, a standalone Work history transport, complete
historical event/measurement recovery, general source-neutral execution projection
and retrospective prospective-learning eligibility. No implementation of those
features is authorized by this assessment.
