"""Explicit local safetensors MiniLM CPU adapter. Never discover or fetch models."""

from __future__ import annotations

import hashlib
import importlib.metadata
import importlib.util
import json
import math
import os
import re
import resource
import stat
import sys
import tempfile
import time
from pathlib import Path

MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
FILES = ("config.json", "model.safetensors", "vocab.txt")
MAX_BUNDLE_BYTES = 300 * 1024 * 1024


class SemanticUnavailable(ValueError):
    """No approved local semantic backend; retain A/B and null C metrics."""


def peak_rss_bytes() -> int:
    value = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(value if sys.platform == "darwin" else value * 1024)


def _digest_bundle(path: Path, *, copy_to: Path | None = None) -> tuple[str, int]:
    digest, total = hashlib.sha256(), 0
    root = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        for name in FILES:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=root)
            with os.fdopen(fd, "rb") as stream:
                info = os.fstat(stream.fileno())
                limit = {
                    "config.json": 65536,
                    "vocab.txt": 2 * 1024 * 1024,
                    "model.safetensors": 256 * 1024 * 1024,
                }[name]
                size = info.st_size
                if not stat.S_ISREG(info.st_mode) or not 0 < size <= limit:
                    raise SemanticUnavailable("model file type/size is unsupported")
                if total + size > MAX_BUNDLE_BYTES:
                    raise SemanticUnavailable("model bundle exceeds 300 MiB")
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
                        if output:
                            output.write(block)
                    if count != size:
                        raise SemanticUnavailable("model file changed size while read")
                finally:
                    if output:
                        output.close()
                total += count
    finally:
        os.close(root)
    return digest.hexdigest(), total


class LocalCPUEncoder:
    """Frozen pretrained model; texts only, no outcome/state access."""

    def __init__(self, *, model, tokenizer, torch, metadata: dict):
        self._model, self._tokenizer, self._torch = model, tokenizer, torch
        self.metadata = metadata

    def encode(self, texts: tuple[str, ...]) -> tuple[tuple[float, ...], ...]:
        result = []
        for text in texts:
            if not isinstance(text, str) or not text.strip() or len(text) > 4096:
                raise ValueError(
                    "semantic input must be a bounded nonblank description"
                )
            inputs = self._tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=256,
                return_tensors="pt",
            )
            with self._torch.inference_mode():
                output = self._model(**inputs).last_hidden_state
                mask = (
                    inputs["attention_mask"].unsqueeze(-1).expand(output.size()).float()
                )
                pooled = (output * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
                vector = self._torch.nn.functional.normalize(pooled, p=2, dim=1)
            values = tuple(float(x) for x in vector[0].tolist())
            if len(values) != 384 or not all(math.isfinite(x) for x in values):
                raise SemanticUnavailable(
                    "semantic output dimension or finiteness invalid"
                )
            result.append(values)
        return tuple(result)


def load_cpu_encoder(
    path: str | Path,
    *,
    expected_sha256: str,
    revision: str,
) -> LocalCPUEncoder:
    """Load an operator-provisioned, pinned three-file all-MiniLM-L6-v2 bundle.

    The directory must contain only config.json, model.safetensors and vocab.txt.
    Digest concatenates sorted filename NUL size NUL content in FILES order.
    Snapshot to a private temp directory before verifying/loading; no pickle,
    model-supplied code, automatic classes, GPU, inference API or model download.
    Caller pins the claimed pretrained revision; a hash is not a provenance proof.
    """
    if not re.fullmatch(r"[0-9a-f]{64}", expected_sha256):
        raise SemanticUnavailable("model bundle requires a lowercase SHA-256 pin")
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise SemanticUnavailable("model revision requires a full commit identity")
    missing = [
        name
        for name in ("torch", "transformers", "safetensors")
        if importlib.util.find_spec(name) is None
    ]
    if missing:
        raise SemanticUnavailable(
            "local CPU runtime unavailable: " + ", ".join(missing)
        )
    source = Path(path).absolute()
    if any(p.is_symlink() for p in (source, *source.parents)):
        raise SemanticUnavailable("model path must not traverse symbolic links")
    if not source.is_dir() or sorted(p.name for p in source.iterdir()) != list(FILES):
        raise SemanticUnavailable(
            "model bundle must contain exactly the three safe files"
        )
    started = time.perf_counter()
    try:
        with tempfile.TemporaryDirectory(prefix="model-learner-cpu-") as temporary:
            snapshot = Path(temporary)
            actual, bundle_bytes = _digest_bundle(source, copy_to=snapshot)
            if actual != expected_sha256:
                raise SemanticUnavailable("model bundle differs from the approved hash")
            config = json.loads((snapshot / "config.json").read_text())
            expected = {
                "model_type": "bert",
                "hidden_size": 384,
                "num_hidden_layers": 6,
                "num_attention_heads": 12,
                "intermediate_size": 1536,
                "vocab_size": 30522,
                "max_position_embeddings": 512,
                "type_vocab_size": 2,
                "hidden_act": "gelu",
                "layer_norm_eps": 1e-12,
            }
            if not isinstance(config, dict) or any(
                config.get(k) != v for k, v in expected.items()
            ):
                raise SemanticUnavailable("unsupported pretrained MiniLM architecture")
            if any(k in config for k in ("auto_map", "quantization_config")):
                raise SemanticUnavailable(
                    "custom model code or quantization is unsupported"
                )
            # Explicit architecture/tokenizer avoid model-provided import paths.
            import torch
            from transformers import BertConfig, BertModel, BertTokenizer

            tokenizer = BertTokenizer(
                vocab_file=str(snapshot / "vocab.txt"), do_lower_case=True
            )
            model, loading = BertModel.from_pretrained(
                str(snapshot),
                # Do not pass arbitrary config keys through to the runtime.
                config=BertConfig(**expected),
                local_files_only=True,
                use_safetensors=True,
                token=False,
                weights_only=True,
                output_loading_info=True,
            )
            if any(
                loading.get(k)
                for k in (
                    "missing_keys",
                    "unexpected_keys",
                    "mismatched_keys",
                    "error_msgs",
                )
            ):
                raise SemanticUnavailable(
                    "pretrained weights are incomplete or incompatible"
                )
            model = model.to("cpu").eval()
            model.requires_grad_(False)
            parameter_bytes = sum(
                x.numel() * x.element_size() for x in model.parameters()
            )
        return LocalCPUEncoder(
            model=model,
            tokenizer=tokenizer,
            torch=torch,
            metadata={
                "model_id": MODEL_ID,
                "revision": revision,
                "bundle_sha256": actual,
                "bundle_bytes": bundle_bytes,
                "parameter_bytes": parameter_bytes,
                "device": "cpu",
                "dimensions": 384,
                "max_tokens": 256,
                "pooling": "attention-mask mean; L2 normalization",
                "batch_size": 1,
                "load_seconds": time.perf_counter() - started,
                "process_peak_rss_bytes_after_load": peak_rss_bytes(),
                "cpu_threads": torch.get_num_threads(),
                "runtime_versions": {
                    n: importlib.metadata.version(n)
                    for n in ("torch", "transformers", "safetensors")
                },
            },
        )
    except SemanticUnavailable:
        raise
    except (OSError, ValueError, ImportError, RuntimeError) as exc:
        raise SemanticUnavailable("local pinned model could not be loaded") from exc


def runtime_availability() -> dict:
    return {
        "available_packages": {
            n: importlib.util.find_spec(n) is not None
            for n in ("torch", "transformers", "safetensors")
        },
        "model_id": MODEL_ID,
        "estimated_parameter_bytes": 22_700_000 * 4,
        "estimate_basis": (
            "model card rounded 22.7M parameters at FP32; excludes runtime/activations"
        ),
        "actual_model_memory_bytes": None,
        "actual_load_seconds": None,
        "actual_inference_seconds": None,
        "automatic_download": False,
        "remote_inference": False,
        "logical_cpu_count": os.cpu_count(),
    }
