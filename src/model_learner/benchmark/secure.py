"""Offline controller primitives; no agent backend or runtime attestation.

Only public task bytes and primitive function calls cross the synthetic worker
interface. Host-owned authentication keys, expected answers and reports do not.
The real benchmark gate remains unconditional in benchmark.isolation.
"""

import hashlib
import hmac
import io
import json
import math
import os
import secrets
import stat
import tarfile
from dataclasses import dataclass, field
from pathlib import Path
from uuid import UUID, uuid4

from model_learner.benchmark.fixtures import TaskFixture, get_task

VERSION = "offline-secure-controller/v1"
MAX_ARTIFACT_BYTES = 1024 * 1024
MAX_TRANSPORT_BYTES = MAX_ARTIFACT_BYTES + 32 * 1024
MAX_PROTOCOL_BYTES = 4096
MAX_TASK_BYTES = 16 * 1024


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _hex_digest(value: str) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and all(c in "0123456789abcdef" for c in value)
    )


def _json(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def _pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ValueError("duplicate protocol field")
        value[key] = item
    return value


def _read_json(data: bytes) -> object:
    if type(data) is not bytes or len(data) > MAX_PROTOCOL_BYTES:
        raise ValueError("protocol bytes exceed limit")
    try:
        return json.loads(
            data,
            object_pairs_hook=_pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(ValueError("nonfinite")),
        )
    except (UnicodeError, RecursionError, json.JSONDecodeError) as exc:
        raise ValueError("invalid primitive protocol") from exc


def _primitive(value: object, depth: int = 0) -> None:
    if depth > 8:
        raise ValueError("primitive nesting exceeds limit")
    if value is None or type(value) in (bool, int, str):
        return
    if type(value) is float and math.isfinite(value):
        return
    if type(value) in (list, tuple) and len(value) <= 128:
        for item in value:
            _primitive(item, depth + 1)
        return
    raise ValueError("unsupported primitive")


@dataclass(frozen=True)
class RunBinding:
    """Identifiers predeclared by the trusted controller, never worker supplied."""

    benchmark_id: UUID
    run_id: UUID
    task_id: UUID
    fixture_id: str
    fixture_sha256: str
    configuration_snapshot_id: str
    nonce: str = field(default_factory=lambda: secrets.token_hex(32))

    def __post_init__(self):
        for value in (self.benchmark_id, self.run_id, self.task_id):
            if type(value) is not UUID:
                raise ValueError("binding identifiers must be UUIDs")
        for value in (self.fixture_sha256, self.nonce):
            if not _hex_digest(value):
                raise ValueError("binding digest and nonce must be 64 lowercase hex")
        if not _hex_digest(self.configuration_snapshot_id):
            raise ValueError(
                "configuration snapshot must be its exact SHA-256 identifier"
            )
        get_task(self.fixture_id)

    def payload(self) -> dict:
        return {
            "benchmark_id": str(self.benchmark_id),
            "run_id": str(self.run_id),
            "task_id": str(self.task_id),
            "fixture_id": self.fixture_id,
            "fixture_sha256": self.fixture_sha256,
            "configuration_snapshot_id": self.configuration_snapshot_id,
            "nonce": self.nonce,
        }


def fixture_sha256(fixture: TaskFixture) -> str:
    return _digest(
        _json(
            {
                "id": fixture.task_id,
                "version": fixture.version,
                "description": fixture.description,
                "initial_source": fixture.initial_source,
                "function": fixture.function,
                "checks": fixture.checks,
            }
        )
    )


def public_task_envelope(fixture_id: str) -> bytes:
    """Construct from fixed public fixtures, not arbitrary caller metadata.

    Deliberately omit checks, expectations, fixture fingerprints, host paths,
    run authentication material, configuration metadata and environment.
    """
    fixture = get_task(fixture_id)
    data = _json(
        {
            "version": VERSION,
            "description": fixture.description,
            "files": {"solution.py": fixture.initial_source},
        }
    )
    if len(data) > MAX_TASK_BYTES:
        raise ValueError("public task envelope exceeds limit")
    return data


def extract_candidate(transport: bytes) -> bytes:
    """Accept only an uncompressed, single regular file; never extract paths.

    Reject metadata headers, links, sparse files, duplicate/trailing archives and
    nonzero padding. Hostile source is opaque bytes and never imported/executed.
    """
    if (
        type(transport) is not bytes
        or len(transport) > MAX_TRANSPORT_BYTES
        or len(transport) < 1536
        or len(transport) % 512
        or transport[156:157] not in (tarfile.REGTYPE, tarfile.AREGTYPE)
    ):
        raise ValueError("invalid bounded artifact transport")
    try:
        with tarfile.open(fileobj=io.BytesIO(transport), mode="r:") as archive:
            member = archive.next()
            if (
                member is None
                or member.name != "solution.py"
                or member.type not in (tarfile.REGTYPE, tarfile.AREGTYPE)
                or member.linkname
                or member.pax_headers
                or member.sparse is not None
                or member.offset != 0
                or member.offset_data != 512
                or not 0 <= member.size <= MAX_ARTIFACT_BYTES
            ):
                raise ValueError("artifact must be one bounded regular solution.py")
            end = 512 + member.size
            padded_end = 512 + ((member.size + 511) // 512) * 512
            if len(transport) < padded_end + 1024 or any(transport[end:]):
                raise ValueError("artifact has extra entries or nonzero trailing data")
            stream = archive.extractfile(member)
            if stream is None:
                raise ValueError("artifact missing")
            result = stream.read(MAX_ARTIFACT_BYTES + 1)
            if len(result) != member.size:
                raise ValueError("artifact size mismatch")
            return result
    except (tarfile.TarError, OSError) as exc:
        raise ValueError("invalid artifact archive") from exc


def _directory_fd(path: Path) -> int:
    """Pin each component, refusing symlink parents and relative paths."""
    path = Path(path)
    if not path.is_absolute() or ".." in path.parts:
        raise ValueError("control directory must be absolute without traversal")
    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    descriptor = os.open("/", flags)
    try:
        for part in path.parts[1:]:
            child = os.open(part, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


@dataclass(frozen=True)
class FrozenCandidate:
    contents: bytes = field(repr=False)
    sha256: str
    transport_sha256: str

    def __post_init__(self):
        if (
            type(self.contents) is not bytes
            or len(self.contents) > MAX_ARTIFACT_BYTES
            or not _hex_digest(self.sha256)
            or not _hex_digest(self.transport_sha256)
            or _digest(self.contents) != self.sha256
        ):
            raise ValueError("invalid or oversized frozen candidate bytes")

    def write_exclusive(self, control: Path) -> Path:
        """Write bytes to a pinned trusted control directory, with no overwrite.

        Requires an operator-owned directory inaccessible to workers. Mode 0400
        alone cannot stop its owner rewriting it; reread/hash checks remain needed.
        """
        if type(self.contents) is not bytes or _digest(self.contents) != self.sha256:
            raise ValueError("frozen candidate bytes changed")
        directory = _directory_fd(control)
        descriptor = None
        created = False
        try:
            descriptor = os.open(
                "candidate.py",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                0o400,
                dir_fd=directory,
            )
            created = True
            with os.fdopen(descriptor, "wb") as stream:
                descriptor = None
                stream.write(self.contents)
                stream.flush()
                os.fsync(stream.fileno())
            os.fsync(directory)
        except BaseException:
            if descriptor is not None:
                os.close(descriptor)
            if created:
                os.unlink("candidate.py", dir_fd=directory)
            raise
        finally:
            os.close(directory)
        return Path(control) / "candidate.py"

    def recheck(self, control: Path) -> None:
        directory = _directory_fd(control)
        try:
            descriptor = os.open(
                "candidate.py",
                os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK,
                dir_fd=directory,
            )
            with os.fdopen(descriptor, "rb") as stream:
                before = os.fstat(stream.fileno())
                if (
                    not stat.S_ISREG(before.st_mode)
                    or before.st_size > MAX_ARTIFACT_BYTES
                    or before.st_nlink != 1
                ):
                    raise ValueError("frozen artifact is not bounded regular file")
                contents = stream.read(MAX_ARTIFACT_BYTES + 1)
                after = os.fstat(stream.fileno())

                def identity(item):
                    return (
                        item.st_dev,
                        item.st_ino,
                        item.st_size,
                        item.st_mtime_ns,
                        item.st_ctime_ns,
                        item.st_nlink,
                    )

                entry = os.stat("candidate.py", dir_fd=directory, follow_symlinks=False)
                if (
                    identity(before) != identity(after)
                    or identity(after) != identity(entry)
                    or contents != self.contents
                ):
                    raise ValueError("frozen artifact changed")
        finally:
            os.close(directory)


@dataclass(frozen=True)
class SignedReceipt:
    """Controller authentication only; cannot attest an OS or provider boundary."""

    payload: bytes
    signature: str

    def as_dict(self) -> dict:
        return {"payload": json.loads(self.payload), "signature": self.signature}


class OfflineController:
    """Per-run synthetic controller with host-private, ephemeral signing material.

    It never launches candidates/agents, reads credentials, contacts a provider,
    or accepts a caller's claimed validation result. A worker gets only request().
    """

    def __init__(self, binding: RunBinding):
        self.binding = binding
        self.fixture = get_task(binding.fixture_id)
        if binding.fixture_sha256 != fixture_sha256(self.fixture):
            raise ValueError("binding fixture differs from trusted fixture")
        self.__key = secrets.token_bytes(32)
        self.__candidate = None
        self.__issued: dict[str, bytes] = {}
        self.__validated = False

    def _sign(self, purpose: str, evidence: dict) -> SignedReceipt:
        payload = _json(
            {
                "version": VERSION,
                "scope": "offline_synthetic_controller_only",
                "real_execution_ready": False,
                "binding": self.binding.payload(),
                "purpose": purpose,
                "evidence": evidence,
            }
        )
        return SignedReceipt(
            payload, hmac.new(self.__key, payload, "sha256").hexdigest()
        )

    def verify_receipt(self, receipt: SignedReceipt, *, purpose: str) -> dict:
        if (
            not _hex_digest(receipt.signature)
            or type(receipt.payload) is not bytes
            or len(receipt.payload) > MAX_PROTOCOL_BYTES
        ):
            raise ValueError("receipt exceeds limit")
        if not hmac.compare_digest(
            receipt.signature,
            hmac.new(self.__key, receipt.payload, "sha256").hexdigest(),
        ):
            raise ValueError("receipt authentication or run binding mismatch")
        value = json.loads(receipt.payload)
        if value["binding"] != self.binding.payload() or value["purpose"] != purpose:
            raise ValueError("receipt purpose or run binding mismatch")
        return value

    def import_candidate(
        self, transport: bytes
    ) -> tuple[FrozenCandidate, SignedReceipt]:
        if self.__candidate is not None:
            raise ValueError("candidate already imported for this run")
        contents = extract_candidate(transport)
        candidate = FrozenCandidate(contents, _digest(contents), _digest(transport))
        self.__candidate = candidate
        receipt = self._sign(
            "artifact_import",
            {
                "candidate_sha256": candidate.sha256,
                "transport_sha256": candidate.transport_sha256,
                "candidate_bytes": len(contents),
                "runtime_freeze_verified": False,
            },
        )
        return candidate, receipt

    def request(self, index: int) -> bytes:
        if self.__candidate is None or self.__validated:
            raise ValueError("candidate import must precede unfinished validation")
        if type(index) is not int or not 0 <= index < len(self.fixture.checks):
            raise ValueError("unknown request index")
        if str(index) in self.__issued:
            raise ValueError("request already issued")
        _, args, _, _ = self.fixture.checks[index]
        _primitive(args)
        data = _json(
            {
                "request_id": str(uuid4()),
                "function": self.fixture.function,
                "args": args,
            }
        )
        if len(data) > MAX_PROTOCOL_BYTES:
            raise ValueError("primitive request exceeds limit")
        self.__issued[str(index)] = data
        return data

    def validate(self, *, control: Path, responses: tuple[bytes, ...]) -> SignedReceipt:
        """Recheck frozen bytes and independently compare a complete response set.

        Calls expose each test's inputs, but no hidden expectations/names or host
        data. The transcript hash binds requests, responses and their ordering.
        This does not prove responses originated from candidate execution.
        """
        if self.__candidate is None or self.__validated:
            raise ValueError("validation unavailable or already finalized")
        if type(responses) is not tuple or len(responses) != len(self.fixture.checks):
            raise ValueError("complete bounded response set required")
        if len(self.__issued) != len(self.fixture.checks):
            raise ValueError("all requests must be issued by this controller")
        self.__candidate.recheck(control)
        passed = []
        transcript = []
        for index, (response, check) in enumerate(
            zip(responses, self.fixture.checks, strict=True)
        ):
            request = self.__issued[str(index)]
            request_id = json.loads(request)["request_id"]
            value = _read_json(response)
            if type(value) is not dict or value.get("request_id") != request_id:
                raise ValueError("response request binding mismatch")
            _, _, expected, expected_error = check
            if set(value) == {"request_id", "value"}:
                result = value["value"]
                if type(result) not in (int, float) or (
                    type(result) is float and not math.isfinite(result)
                ):
                    raise ValueError("response must be a finite number")
                passed.append(expected_error is None and result == expected)
            elif set(value) == {"request_id", "error"}:
                if type(value["error"]) is not str or value["error"] not in {
                    "ValueError",
                    "ZeroDivisionError",
                    "UnsupportedReturn",
                }:
                    raise ValueError("response error is not a supported primitive")
                passed.append(value["error"] == expected_error)
            else:
                raise ValueError("response has unsupported fields")
            transcript.append([request.decode("utf-8"), response.decode("utf-8")])
        self.__candidate.recheck(control)
        self.__validated = True
        return self._sign(
            "validation",
            {
                "candidate_sha256": self.__candidate.sha256,
                "transport_sha256": self.__candidate.transport_sha256,
                "transcript_sha256": _digest(_json(transcript)),
                "case_count": len(passed),
                "passed_count": sum(passed),
                "failed_count": len(passed) - sum(passed),
                "result": "pass" if all(passed) else "fail",
                "candidate_execution_attested": False,
            },
        )
