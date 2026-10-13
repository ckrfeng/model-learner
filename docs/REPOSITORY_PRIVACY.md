# Repository privacy safeguards

Source code, public implementation documentation, schemas and documented synthetic
fixtures belong in Git. Private conversations, imported histories, annotations,
research worksheets, execution traces, local databases, evaluation reports and
model weights belong in ignored local storage, preferably `.model-learner/`.
An artifact's extension or a `source_kind` declaration cannot prove it is public.
Never copy actual secrets or private messages into a test, issue or audit report.

## Local checks and installation

From the repository root, with Git and Python 3.12 or newer installed:

```sh
git config --local core.hooksPath .githooks
git config --local --get core.hooksPath
python3 scripts/privacy_guard.py --staged
```

The executable `.githooks/pre-commit` invokes the guard and propagates its exit
status. Installation affects this repository only and must be repeated in new
clones. Review any existing `core.hooksPath` before replacing it; integrate the
guard into an existing hook if necessary. No global hook is installed.

The staged check inspects **every entry in the index**, not only changed paths and
not working-tree bytes. This catches unchanged prohibited tracked files as well
as `git add -A`, `git add -f`, and a secret staged before the working copy was
sanitized. Staged deletion of a prohibited file is permitted and never deletes
its local copy. Checks only read Git objects/index metadata; they never modify
the index, worktree or local private data. Git's object read machinery is used;
this is not an execution sandbox for an untrusted Git installation/configuration.

```sh
python3 scripts/privacy_guard.py --tree HEAD
uv run pytest tests/integration/test_privacy_guard.py
```

Tree mode is the CI entry point. Failures list escaped file identifiers and risk
categories; detected values and content snippets are never emitted. Recognizable
secrets in filenames produce hashed identifiers. Exit 1 means policy rejection;
exit 2 means inspection could not complete. Both block the hook/CI check.

## Detection policy and reviewed fixtures

`scripts/privacy_guard.py` uses the Python standard library; there is no service,
AI API, paid scanner or added runtime dependency. It rejects:

- Explicit private, credential, session and cache directories and filenames;
  databases and sidecars, logs, model weights and temporary/credential artifacts.
- SQLite headers even under innocuous extensions, NUL-containing binary content,
  blobs over 5 MiB, symlinks/submodules and LFS pointers with uninspected payloads.
- Recognizable GitHub, OpenAI, AWS, Google and Slack token shapes, private-key
  headers, credential-bearing HTTP URLs, literal authorization credentials,
  service-account credentials and high-entropy literal credential assignments.
- Structured conversation messages, supported native history shapes and Codex
  capture/session formats in any extension, except exact reviewed fixture digests.

`.env.example` with placeholders is allowed, but all content checks still apply.
Neither test paths nor ordinary `.json`, `.jsonl`, `.csv`, `.md` or `.txt` extensions
provide a blanket exemption. Seventeen existing conversation/capture fixtures have
documented synthetic or sanitized provenance and exact SHA-256 digests in
`scripts/privacy_fixture_allowlist.json`. These exemptions cover only recognized
session structure; they cannot waive secret, path, size or binary checks.
The policy itself is read from the index or committed tree being checked.

If a legitimate synthetic fixture changes, review its complete contents and
provenance before updating its digest. Review policy/guard/workflow changes with
the same care as source changes. Never automatically generate exemptions for
unknown files or use an exemption to retain private data. New raw-format fixtures
require the same review. The guard cannot verify authorship from a hash.

Secret recognition is deliberately limited: arbitrary passwords, novel provider
formats, encoded/encrypted secrets and private prose can evade detection. Native
format detection cannot recognize every transcript representation. A file under
an allowed path can still be private. Human staged review and artifact discipline
remain necessary. No scanner can guarantee that future accidental commits are
impossible. A larger local scanner could broaden token coverage, but introduces
installation, rule/update and false-positive maintenance; none was installed in
this audit. No repository content is sent to a scanning service.

## CI enforcement

`.github/workflows/privacy.yml` runs the committed-tree check for pull requests
and pushes with read-only repository permission and no persisted checkout
credentials. It uses only Git/Python available on the GitHub runner. The checkout
action is pinned to a commit. The normal GitHub CI runner receives the repository
as any repository workflow does; it is not a third-party scanning service.

Require **Repository privacy / Privacy guard** through GitHub branch protection
or rulesets and ensure bypass privileges match the repository policy. This audit
does not change GitHub settings. Hooks can be bypassed or uninstalled; CI alone
does not stop a direct push from publishing content before a failed check runs.
Review changes to the guard, digest policy and workflow; CI executes repository
code, so a contributor who changes those files can weaken enforcement unless
review/settings protect them. This workflow validates the final tree, not every
commit in a push/PR. Earlier commits containing subsequently deleted secrets need
an independent history audit. Checks cannot revoke secrets or remove pushed data.

## Sanitized audit — 2026-10-13

The initial checkout was on `main`, with **233 tracked files and zero staged
changes**. `HEAD` was `8a0eac7cc4e6f52265621f65ea91f63527a02e8b`. The only initial
working-tree change was a modified `.DS_Store`. One GitHub remote was configured;
its fetch/push URLs contained no HTTP credential authority. No URL is reproduced
here. Existing hooks were inactive sample files; there was no repository privacy
workflow, hook or dedicated policy. No tracked symlink, submodule or LFS pointer
was found. The repository was neither shallow nor configured as a partial clone.

Every available tracked path/blob was scanned locally. The historical inventory
covered **25 reachable commits, 233 unique historical paths, 339 unique blobs,
343 path/blob/mode combinations and 7,312,448 blob bytes**. All 28 locally available references (one branch, two remote-tracking refs and
25 Codex checkpoint/capture refs) were included.
All 25 commits are reachable from cached `origin` history. There were no tags or
historical-only deleted paths in that inventory. Commit metadata/messages were
also checked for recognized secrets without displaying their contents.

Content scanning used the guard's token, credential, native conversation and
artifact checks, supplemented by broad local review searches for literal
credential assignments, personal home paths, emails and conversation schemas.
Nineteen paths received broad screening flags. Review of source/schema context,
fixture provenance and exact fixture digests resolved the synthetic conversation
and credential-canary matches. Two files remain confirmed hygiene/privacy
findings; no credential or raw private transcript exposure was confirmed:

| File identifier | Finding | Reversible preventive change | Historical risk |
| --- | --- | --- | --- |
| `.DS_Store` | Finder binary metadata was tracked despite its ignore rule. Two historical blobs occur in 24 commits. | Removed from the real index with `git rm --cached`; the modified local file's bytes, size and modification time were verified unchanged. | Finder metadata can disclose filenames/layout. Both versions remain in history. No home path or known private-directory name was detected in these versions. Detailed metadata interpretation remains a human review item if stronger historical cleanup is desired. |
| `docs/HUMAN_REVIEW_BATCH.md` | One personal absolute home-directory reference in public developer documentation. | Replaced the checkout prefix with `/absolute/path/to/model-learner`. | Earlier versions retain the identifying path. The original value is omitted from this report. |

Both affected histories are reachable from cached `origin/main`, which is
evidence that the local remote-tracking snapshot contains them. Live GitHub
availability/public visibility was **not independently verified**. No fetch,
remote API read or external scanner was performed. Unfetched/deleted GitHub
branches/tags, forks, release assets, pull-request-only references, reflog-only
or unreachable objects, and external copies are outside this audit's coverage.
Deleting a current file cannot remove those earlier copies. Repository commit
author identities are also ordinary public Git metadata; they were not rewritten.

Initial metadata inventory counted **6,635 ignored files**, including local
research/data, environments, tools and caches. Their private contents were not
scanned or copied into Git. New ignore rules were checked against tracked paths;
only the already-ignored tracked `.DS_Store` required untracking. No dataset,
credential, model or private transcript was staged for testing or deleted.

No credential rotation is indicated by these findings. If a later local or
remote audit identifies an actual secret, revoke/rotate it with operator approval
before considering history cleanup, then investigate where it was used/copied.
For the two current findings, approve a normal preventive commit first. Optional
history rewriting requires a separate decision after reviewing metadata risk and
coordinating all refs/clones/forks; no history rewrite is proposed automatically.
Keep any detailed sensitive follow-up evidence in ignored private storage.

## Delivered safeguards and validation

The changes add private/cache/credential/model ignore rules, the standard-library
index/tree guard, exact digest policy for 17 existing public fixtures, executable
pre-commit hook, push/PR CI workflow, permanent AGENTS policy and this developer
documentation. Local `core.hooksPath` is now `.githooks`; global configuration was
not changed. The actual index currently contains only the `.DS_Store` deletion.
Until the new reviewed digest policy is staged, the new guard correctly rejects
17 session-format fixtures in that index. The proposed complete security tree was validated in a temporary Git index and
tree: **238 files inspected, zero rejected** in each mode. Its files were not
staged in this checkout.

| Check | Actual result |
| --- | --- |
| Full `uv run --no-sync pytest` | 927 passed, 7 existing opt-in skips in 90.74 s; included 53 privacy tests and concurrently present unrelated experiment tests. |
| Final focused privacy suite | 55 passed in 10.28 s after the replacement-object and source-acceptance regressions; independent reviewer also ran all 55 successfully. |
| Ruff lint / formatting | Passed; final results recorded in `STATUS.md`. |
| `git diff --check` | Passed. |
| Private-data preservation | `.DS_Store` preserved exactly; synthetic rejection tests check local bytes/mtime and no emitted canary content. Guard performs no writes. |
| Independent security review | Found and reproduced one replacement-ref bypass. Fixed by disabling replacement refs on every Git read, with staged/tree regression tests. A proposed-tree check also caught a service-account field-name false positive in
synthetic source; structural JSON detection and a source-acceptance regression
fixed it. Independent final recheck found no remaining blockers. |

The isolated tests cover normal code/docs/CSV/JSON fixtures, placeholder
`.env.example`, force-added ignored/private files, SQLite paths/headers, dummy
`.env`, provider-shaped canaries in arbitrary files, native sessions, digest
exceptions, index/worktree disagreement, previously committed violations,
committed-tree validation, actual hook rejection, symlinks, submodules, LFS,
oversized/invalid policy/reference failures, filename redaction and filenames
with spaces, tabs, newlines, Unicode and non-UTF-8 bytes. The last case inserts an
index entry directly because the local filesystem rejects that synthetic name.

## Recommended preventive commit

Suggested title: `Add repository privacy guard and sanitized audit policy`.
Only the following scoped changes belong in this commit. Review and stage them
explicitly after approval; the `.DS_Store` deletion is already staged:

```sh
git add -- .gitignore AGENTS.md README.md STATUS.md \
  docs/HUMAN_REVIEW_BATCH.md docs/REPOSITORY_PRIVACY.md \
  scripts/privacy_guard.py scripts/privacy_fixture_allowlist.json \
  .githooks/pre-commit .github/workflows/privacy.yml \
  tests/integration/test_privacy_guard.py
python3 scripts/privacy_guard.py --staged
git diff --cached --stat
git diff --cached --check
```

Do not include unrelated experiment files that appeared concurrently or anything
under ignored private storage. Review the staged patch locally, without copying
private contents into a report. This audit does not commit, push, fetch, rotate
credentials, change historical references, or modify GitHub protection settings.
