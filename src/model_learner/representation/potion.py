"""Explicit, pinned local Potion static embeddings; NumPy CPU inference only."""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import re
import stat
import tempfile
import time
from pathlib import Path

from model_learner.representation.semantic import (
    LocalCPUEncoder,
    SemanticUnavailable,
    peak_rss_bytes,
)

MODEL_ID = "minishlab/potion-base-8M"
MODEL_REVISION = "bf8b056651a2c21b8d2565580b8569da283cab23"
DIMENSIONS = 256
MAX_TOKENS = 256
MODEL2VEC_VERSION = "0.9.0"
FILES = ("config.json", "model.safetensors", "tokenizer.json")
FILE_SHA256 = {
    "config.json": "2a6ac0e9aaa356a68a5688070db78fc3a464fefe85d2f06a1905ce3718687553",
    "model.safetensors": (
        "f65d0f325faadc1e121c319e2faa41170d3fa07d8c89abd48ca5358d9a223de2"
    ),
    "tokenizer.json": (
        "e67e803f624fb4d67dea1c730d06e1067e1b14d830e2c2202569e3ef0f70bb50"
    ),
}
FILE_LIMITS = {
    "config.json": 65536,
    "model.safetensors": 40 * 1024 * 1024,
    "tokenizer.json": 2 * 1024 * 1024,
}
EXPECTED_CONFIG = {
    "model_type": "model2vec",
    "architectures": ["StaticModel"],
    "tokenizer_name": "baai/bge-base-en-v1.5",
    "apply_pca": 256,
    "apply_zipf": True,
    "hidden_dim": 256,
    "seq_length": 1000000,
    "normalize": True,
}
RUNTIME_PACKAGES = ("model2vec", "numpy", "safetensors", "tokenizers")


def _open_directory(path: Path) -> int:
    """Pin each path component without following symlinks, including parents."""
    descriptor = os.open("/", os.O_RDONLY | os.O_DIRECTORY)
    try:
        for component in path.parts[1:]:
            if component in (".", ".."):
                raise SemanticUnavailable("model path must be normalized")
            child = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                dir_fd=descriptor,
            )
            os.close(descriptor)
            descriptor = child
        return descriptor
    except BaseException:
        os.close(descriptor)
        raise


def digest_potion_bundle(
    path: str | Path, *, copy_to: Path | None = None
) -> tuple[str, int]:
    """Hash filename NUL size NUL contents in FILES order, with bounded copying."""
    root = _open_directory(Path(path).absolute())
    digest, total = hashlib.sha256(), 0
    try:
        if sorted(os.listdir(root)) != list(FILES):
            raise SemanticUnavailable("Potion bundle requires exactly three safe files")
        for name in FILES:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root)
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                size = info.st_size
                if not stat.S_ISREG(info.st_mode) or not 0 < size <= FILE_LIMITS[name]:
                    raise SemanticUnavailable("Potion model file type/size unsupported")
                digest.update(name.encode() + b"\0" + str(size).encode() + b"\0")
                count = 0
                output = (copy_to / name).open("xb") if copy_to else None
                try:
                    while block := stream.read(min(1024 * 1024, size - count + 1)):
                        count += len(block)
                        if count > size:
                            raise SemanticUnavailable(
                                "model file changed size while read"
                            )
                        digest.update(block)
                        if output is not None:
                            output.write(block)
                    if count != size:
                        raise SemanticUnavailable("model file changed size while read")
                finally:
                    if output is not None:
                        output.close()
                total += count
        return digest.hexdigest(), total
    finally:
        os.close(root)


def _json(data: str | bytes):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise SemanticUnavailable("duplicate model JSON keys unsupported")
            result[key] = value
        return result

    return json.loads(data, object_pairs_hook=unique_pairs)


def _validate_static_bundle(snapshot: Path) -> int:
    config = _json((snapshot / "config.json").read_bytes())
    if config != EXPECTED_CONFIG:
        raise SemanticUnavailable("unsupported pretrained Potion architecture")
    tokenizer = _json((snapshot / "tokenizer.json").read_bytes())
    wordpiece = tokenizer.get("model") if isinstance(tokenizer, dict) else None
    vocab = wordpiece.get("vocab") if isinstance(wordpiece, dict) else None
    if (
        not isinstance(wordpiece, dict)
        or wordpiece.get("type") != "WordPiece"
        or not isinstance(vocab, dict)
        or not 1 <= len(vocab) <= 40000
        or any(type(v) is not int for v in vocab.values())
        or set(vocab.values()) != set(range(len(vocab)))
        or wordpiece.get("unk_token") not in vocab
    ):
        raise SemanticUnavailable("unsupported Potion tokenizer vocabulary")
    # Inspect the bounded safetensors header before runtime allocates any arrays.
    weights = snapshot / "model.safetensors"
    with weights.open("rb") as stream:
        header_length = int.from_bytes(stream.read(8), "little")
        if not 1 <= header_length <= 65536:
            raise SemanticUnavailable("unsupported safetensors header size")
        header = _json(stream.read(header_length))
    parameter_bytes = len(vocab) * DIMENSIONS * 4
    expected = {
        "dtype": "F32",
        "shape": [len(vocab), DIMENSIONS],
        "data_offsets": [0, parameter_bytes],
    }
    if (
        not isinstance(header, dict)
        or set(header) - {"__metadata__"} != {"embeddings"}
        or header.get("embeddings") != expected
        or weights.stat().st_size != 8 + header_length + parameter_bytes
    ):
        raise SemanticUnavailable(
            "incomplete or incompatible Potion pretrained weights"
        )
    return len(vocab)


class PotionCPUEncoder(LocalCPUEncoder):
    """Frozen pretrained static model; bounded descriptions and CPU arrays only."""

    dimensions = DIMENSIONS

    def __init__(self, *, model, metadata: dict):
        self._model = model
        self.metadata = metadata

    def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        if not texts:
            return ()
        for text in texts:
            if not isinstance(text, str) or not text.strip() or len(text) > 4096:
                raise ValueError(
                    "semantic input must be a bounded nonblank description"
                )
        vectors = self._model.encode(
            list(texts),
            max_length=MAX_TOKENS,
            batch_size=1,
            use_multiprocessing=False,
            show_progress_bar=False,
        )
        if vectors.shape != (len(texts), DIMENSIONS):
            raise SemanticUnavailable("semantic output dimension invalid")
        result = tuple(tuple(float(x) for x in row) for row in vectors)
        for vector in result:
            norm = math.sqrt(sum(x * x for x in vector))
            if not all(math.isfinite(x) for x in vector) or not (
                norm == 0 or math.isclose(norm, 1, abs_tol=1e-5)
            ):
                raise SemanticUnavailable(
                    "semantic output finiteness/normalization invalid"
                )
        return result


def load_potion_encoder(
    path: str | Path, *, expected_sha256: str, revision: str
) -> PotionCPUEncoder:
    """Load only operator-approved pinned local safetensors, never a Hub loader.

    The caller supplies the approved downloaded bundle hash; a self-asserted hash
    and revision are not independent provenance evidence. Read a bounded private
    snapshot, reject other architectures and construct the audited StaticModel
    directly. There is no pickle, custom code, discovery, download or API call.
    """
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise SemanticUnavailable("Potion bundle requires a lowercase SHA-256 pin")
    if revision != MODEL_REVISION:
        raise SemanticUnavailable("Potion revision differs from approved full commit")
    started = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix="model-learner-potion-") as temporary:
            snapshot = Path(temporary)
            actual, bundle_bytes = digest_potion_bundle(path, copy_to=snapshot)
            if actual != expected_sha256:
                raise SemanticUnavailable("model bundle differs from the approved hash")
            for name in FILES:
                with (snapshot / name).open("rb") as stream:
                    file_digest = hashlib.file_digest(stream, "sha256").hexdigest()
                if file_digest != FILE_SHA256[name]:
                    raise SemanticUnavailable(
                        "Potion file differs from approved revision"
                    )
            vocabulary_size = _validate_static_bundle(snapshot)
            missing = [
                name
                for name in RUNTIME_PACKAGES
                if importlib.util.find_spec(name) is None
            ]
            if missing:
                raise SemanticUnavailable(
                    "local CPU runtime unavailable: " + ", ".join(missing)
                )
            versions = {
                name: importlib.metadata.version(name) for name in RUNTIME_PACKAGES
            }
            if versions["model2vec"] != MODEL2VEC_VERSION:
                raise SemanticUnavailable("unsupported model2vec runtime version")
            import numpy as np
            from model2vec import StaticModel
            from safetensors.numpy import load_file
            from tokenizers import Tokenizer

            tensors = load_file(str(snapshot / "model.safetensors"))
            vectors = tensors["embeddings"]
            if (
                vectors.shape != (vocabulary_size, DIMENSIONS)
                or vectors.dtype != np.dtype("float32")
                or not np.isfinite(vectors).all()
            ):
                raise SemanticUnavailable("invalid Potion embedding matrix")
            tokenizer = Tokenizer.from_file(str(snapshot / "tokenizer.json"))
            tokenizer.no_padding()
            tokenizer.no_truncation()
            if set(tokenizer.get_vocab().values()) != set(range(vocabulary_size)):
                raise SemanticUnavailable(
                    "tokenizer IDs disagree with pretrained weights"
                )
            vectors.setflags(write=False)
            model = StaticModel(
                vectors=vectors,
                tokenizer=tokenizer,
                config={"normalize": True},
                normalize=True,
            )
            parameter_bytes = vectors.nbytes
        return PotionCPUEncoder(
            model=model,
            metadata={
                "model_id": MODEL_ID,
                "revision": MODEL_REVISION,
                "license": "MIT",
                "bundle_sha256": actual,
                "bundle_bytes": bundle_bytes,
                "parameter_bytes": parameter_bytes,
                "device": "cpu",
                "dimensions": DIMENSIONS,
                "vocabulary_size": vocabulary_size,
                "max_tokens": MAX_TOKENS,
                "max_description_characters": 4096,
                "pooling": (
                    "static pretrained token mean; L2 normalization; UNK removed"
                ),
                "truncation": (
                    "first 256*median_token_length characters; first 256 tokens"
                ),
                "zero_vector_policy": "retain zero vector for no known tokens",
                "batch_size": 1,
                "multiprocessing": False,
                "remote_inference": False,
                "automatic_download": False,
                "load_seconds": time.perf_counter() - started,
                "process_peak_rss_bytes_after_load": peak_rss_bytes(),
                "runtime_versions": versions,
                "available_packages": dict.fromkeys(RUNTIME_PACKAGES, True),
                "estimated_parameter_bytes": parameter_bytes,
                "estimate_basis": "exact frozen F32 embedding table bytes",
            },
        )
    except SemanticUnavailable:
        raise
    except (OSError, ValueError, TypeError, KeyError, ImportError, RuntimeError) as exc:
        raise SemanticUnavailable(
            "local pinned Potion model could not be loaded"
        ) from exc
