# Offline secure execution-boundary components

Delivered 2026-10-11. **Real coding-agent execution remains disabled.** These
components implement useful controller-side transport, byte freezing and
run-bound receipt checks. They do not establish a credential relay, a hostile
runtime freeze or an isolated candidate executor. No real/paid agent, provider
request, software installation or global configuration change was performed.

## Scope and actual behavior

`model_learner.benchmark.secure` is optional and independent of the existing
benchmark evidence exporter and probabilistic learner. The existing unconditional
`require_supported_real_containment()` gate is unchanged. No new receipt is
accepted by real finalization or converted into a verified learner observation.

- `public_task_envelope()` builds an allowlisted envelope from a fixed public
  fixture: version, public task description and initial `solution.py` bytes. It
  accepts no arbitrary configuration metadata, environment, credentials,
  controller/report path, test identities, expectations or private transcripts.
- `extract_candidate()` accepts at most 1 MiB candidate bytes in a bounded,
  uncompressed tar transport (1 MiB + 32 KiB maximum). Only a single regular
  `solution.py` at the archive root is accepted. Links, devices, FIFOs,
  directories, traversal, metadata/PAX headers, sparse files, duplicate entries,
  nonzero padding and trailing archives are refused. It parses bytes in memory
  and never extracts archive paths or imports/executes candidate code.
- `FrozenCandidate` retains immutable Python bytes with candidate and transport
  SHA-256 hashes. Construction checks the size and byte digest. Exclusive
  file creation uses a pinned directory descriptor and refuses symlink parents
  and existing output; modes and archive metadata are not trusted or preserved.
  The controller rereads the current bounded, non-symlink, singly linked regular
  file before and after validation, checking content and stable file identity,
  size, modification/change times and directory entry identity.
- `OfflineController.request()` sends only a fresh random request ID, a fixed
  public function name and bounded primitive arguments. Expected answers, named
  tests, acceptance source, receipt key and host paths remain in the controller.
  Individual case inputs necessarily become visible to the worker making that
  call. This is input/expectation separation, not secret public-fixture tests.
- Responses are at most 4096 bytes each and must contain exactly the matching
  request ID plus a finite integer/float value or allowlisted error name.
  Boolean values, unexpected fields, duplicate JSON fields, wrong/reordered IDs,
  unsupported/nested outputs and nonfinite values fail closed. Actual numeric
  answer mismatch produces a failed comparison; missing or malformed evidence
  produces no validation receipt.
- Per-run receipts authenticate the exact task, benchmark, run, fixture contents,
  configuration snapshot identifier and fresh nonce. The host generates an
  ephemeral HMAC-SHA-256 key, never includes it in envelopes/requests/receipts,
  and does not read any provider credential. Import receipts bind both candidate
  and transport hashes. Validation receipts bind those hashes, the complete
  ordered request/response transcript hash and controller-computed comparison
  counts. They reject tamper, wrong purpose and other-run/other-controller replay;
  a run cannot import a second candidate or finalize validation twice.

Authentication establishes that this in-memory trusted controller issued a
receipt. Verification of an already issued receipt can be repeated intentionally;
there is no replay-as-new-run/validation operation. Keys are not persisted, so
receipts cannot be independently authenticated after their controller is gone or
transferred to another process/machine. These local receipt checks are not a
public signing or durable evidence-ingestion contract.

## Credential and filesystem trust assumptions

The controller and its directory must be owned by the operator and inaccessible
to agent/candidate processes. Empty worker environments and allowlisted payloads
reduce accidental credential transfer; they do **not** isolate host credentials,
files, keychain access, processes, sockets or memory from code running with host
privileges. Same-user hostile code could inspect the controller or retrieve its
HMAC key. Mode 0400 cannot prevent the file owner from changing a candidate.

Directory descriptors prevent a symlink substitution redirecting that file
operation. They do not make a returned lexical pathname immutable if another
process renames a parent directory. Reread checks detect many mutations but are
not a substitute for denying hostile access to the directory. This module cannot
prove that a runtime's process tree stopped before bytes were transported.

All receipts state `scope=offline_synthetic_controller_only` and
`real_execution_ready=false`. Artifact imports state
`runtime_freeze_verified=false`; validation states
`candidate_execution_attested=false`. Even a passing result proves only the
controller's comparisons of submitted protocol responses. It cannot establish
that a candidate executed, its runtime was contained or its provider credential
was isolated. No caller flag or synthetic receipt can unlock real execution.

## Validation performed

The integration rehearsal launches only a fixed harmless Python worker under
`-I` with an empty environment. It directly implements public clamp operations;
it never imports candidate source. Parent environment variables containing
explicitly public synthetic credential canaries are absent in the worker. The
worker sees only the primitive request. The frozen artifact is deliberately a
non-Python marker. Six valid response comparisons pass and receipts remain
ineligible for real execution. A second rehearsal rejects response replay to a
new request. No arbitrary hostile worker is launched on the host.

Unit tests use hostile archives/files/protocol bytes: traversal, symlinks and
hard links, FIFO/device/sparse/metadata headers, duplicate/trailing entries,
oversized content, mutated candidate bytes, receipt tamper, other-run replay,
missing requests, reordered responses, injected fields, nonfinite/boolean
values, unsupported error bodies and duplicate JSON keys. Huge bounded integers
are handled without float-conversion overflow. Documentation records final
actual test results through `STATUS.md`.

## Remaining blockers for one safe real execution

The existing validated offline Docker experiment uses network none and contains
only its fixed synthetic shell. It supplies neither an agent-capable runtime nor
a provider protocol relay. Installing a provider token inside an agent container
or supplying it through environment/configuration would violate the required
credential separation. No acceptable exact-agent credential mechanism was
established in this scope; no paid/network execution was attempted.

A real backend still must demonstrate an agent boundary with zero host shares or
credential access, a bounded operator-side provider relay/spend cap, and actual
limits and whole-boundary cleanup. Artifact transport must freeze or destroy all
hostile writers **before** reading candidate bytes, using a trusted exporter that
cannot be replaced by candidate code. Acceptance must use a separate,
credential-free, network-disabled candidate-only boundary while expected answers
and the report producer remain outside it. The controller must attest that exact
runtime/image/policy, effective limits, positive controls, denied-access probes,
freeze-before-read and cleanup to the predeclared real run. Current synthetic
HMAC receipts attest none of these.

Until those exact-runtime mechanisms and authorization are available, keep the
real gate unconditional. Do not run the existing host acceptance worker against
hostile candidate code or relabel a real execution as a fixture. Stop after the
requested workstreams; the project remains observational and predictive.
