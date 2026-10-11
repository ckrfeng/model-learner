"""Local adapter guards; synthetic protocol fixtures are not model evidence."""

import hashlib
import json
import math
import os
import socket
import sys
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from model_learner.representation import potion
from model_learner.representation.semantic import LocalCPUEncoder, SemanticUnavailable


def bundle(tmp_path, *, config=None, header=None):
    folder = tmp_path.resolve() / "potion"
    folder.mkdir()
    (folder / "config.json").write_text(json.dumps(config or potion.EXPECTED_CONFIG))
    tokenizer = {
        "model": {
            "type": "WordPiece",
            "unk_token": "[UNK]",
            "vocab": {"[UNK]": 0, "public": 1},
        }
    }
    (folder / "tokenizer.json").write_text(json.dumps(tokenizer))
    spec = header or {
        "embeddings": {
            "dtype": "F32",
            "shape": [2, 256],
            "data_offsets": [0, 2048],
        }
    }
    data = json.dumps(spec).encode()
    (folder / "model.safetensors").write_bytes(
        len(data).to_bytes(8, "little") + data + b"\0" * 2048
    )
    return folder


def load(folder, **changes):
    kwargs = {
        "expected_sha256": potion.digest_potion_bundle(folder)[0],
        "revision": potion.MODEL_REVISION,
    }
    kwargs.update(changes)
    # Protocol fixtures have explicit synthetic identities, never pretrained
    # provenance. Production always verifies the real approved upstream hashes.
    identities = {
        name: hashlib.sha256((folder / name).read_bytes()).hexdigest()
        for name in potion.FILES
    }
    with patch.object(potion, "FILE_SHA256", identities):
        return potion.load_potion_encoder(folder, **kwargs)


def test_self_asserted_hash_cannot_claim_pretrained_identity(tmp_path):
    folder = bundle(tmp_path)
    digest, _ = potion.digest_potion_bundle(folder)
    with pytest.raises(SemanticUnavailable, match="approved revision"):
        potion.load_potion_encoder(
            folder, expected_sha256=digest, revision=potion.MODEL_REVISION
        )


def test_digest_private_copy_and_hash_rejection(tmp_path):
    folder = bundle(tmp_path)
    snapshot = tmp_path.resolve() / "copy"
    snapshot.mkdir()
    digest = potion.digest_potion_bundle(folder, copy_to=snapshot)
    assert digest == potion.digest_potion_bundle(snapshot)
    with pytest.raises(SemanticUnavailable, match="approved hash"):
        load(folder, expected_sha256="0" * 64)
    with pytest.raises(SemanticUnavailable, match="SHA-256"):
        load(folder, expected_sha256="main")
    with pytest.raises(SemanticUnavailable, match="approved full commit"):
        load(folder, revision="main")


@pytest.mark.parametrize("kind", ["symlink", "fifo", "directory", "empty", "oversize"])
def test_hostile_file_types_are_rejected_without_reading(tmp_path, kind):
    folder = bundle(tmp_path)
    target = folder / "config.json"
    target.unlink()
    if kind == "symlink":
        target.symlink_to(folder / "tokenizer.json")
    elif kind == "fifo":
        os.mkfifo(target)
    elif kind == "directory":
        target.mkdir()
    elif kind == "empty":
        target.touch()
    else:
        target.write_bytes(b"x" * 65537)
    with pytest.raises((SemanticUnavailable, OSError)):
        potion.digest_potion_bundle(folder)


def test_symlink_parent_and_extra_pickle_file_rejected(tmp_path):
    folder = bundle(tmp_path)
    link = tmp_path.resolve() / "linked-parent"
    link.symlink_to(tmp_path.resolve(), target_is_directory=True)
    with pytest.raises(OSError):
        potion.digest_potion_bundle(link / "potion")
    (folder / "pytorch_model.bin").write_bytes(b"never load pickle")
    with pytest.raises(SemanticUnavailable, match="exactly three"):
        potion.digest_potion_bundle(folder)


def test_racing_size_is_bounded(tmp_path, monkeypatch):
    folder = bundle(tmp_path)
    actual = potion.os.fstat
    monkeypatch.setattr(
        potion.os,
        "fstat",
        lambda fd: SimpleNamespace(st_mode=actual(fd).st_mode, st_size=1),
    )
    with pytest.raises(SemanticUnavailable, match="changed size"):
        potion.digest_potion_bundle(folder)


@pytest.mark.parametrize(
    "alteration",
    ["architecture", "custom_code", "normalization", "duplicate_keys", "tokenizer_ids"],
)
def test_config_and_tokenizer_rejected_before_runtime(
    tmp_path, monkeypatch, alteration
):
    folder = bundle(tmp_path)
    config = dict(potion.EXPECTED_CONFIG)
    if alteration == "architecture":
        config["hidden_dim"] = 384
    elif alteration == "custom_code":
        config["auto_map"] = {"StaticModel": "evil.run"}
    elif alteration == "normalization":
        config["normalize"] = False
    if alteration == "duplicate_keys":
        (folder / "config.json").write_text('{"model_type":"a","model_type":"b"}')
    elif alteration == "tokenizer_ids":
        path = folder / "tokenizer.json"
        document = json.loads(path.read_text())
        document["model"]["vocab"]["public"] = 2
        path.write_text(json.dumps(document))
    else:
        (folder / "config.json").write_text(json.dumps(config))

    def forbidden_runtime(_):
        pytest.fail("invalid files reached runtime discovery")

    monkeypatch.setattr(potion.importlib.util, "find_spec", forbidden_runtime)
    with pytest.raises(SemanticUnavailable):
        load(folder)


@pytest.mark.parametrize(
    "header",
    [
        {
            "embeddings": {
                "dtype": "F32",
                "shape": [10**12, 256],
                "data_offsets": [0, 2048],
            }
        },
        {"embeddings": {"dtype": "F64", "shape": [2, 256], "data_offsets": [0, 2048]}},
        {"embeddings": {"dtype": "F32", "shape": [2, 384], "data_offsets": [0, 2048]}},
        {"embeddings": {"dtype": "F32", "shape": [2, 256], "data_offsets": [1, 2048]}},
        {"weights": {"dtype": "F32", "shape": [2, 256], "data_offsets": [0, 2048]}},
    ],
)
def test_incomplete_weights_rejected_before_runtime(tmp_path, monkeypatch, header):
    folder = bundle(tmp_path, header=header)
    monkeypatch.setattr(
        potion.importlib.util,
        "find_spec",
        lambda _: pytest.fail("incompatible tensor reached runtime discovery"),
    )
    with pytest.raises(SemanticUnavailable, match="incomplete or incompatible"):
        load(folder)


def test_huge_safetensors_header_is_bounded(tmp_path):
    folder = bundle(tmp_path)
    (folder / "model.safetensors").write_bytes((10**12).to_bytes(8, "little"))
    with pytest.raises(SemanticUnavailable, match="header size"):
        load(folder)


def test_missing_runtime_stays_optional(tmp_path, monkeypatch):
    folder = bundle(tmp_path)
    monkeypatch.setattr(potion.importlib.util, "find_spec", lambda _: None)
    with pytest.raises(SemanticUnavailable, match="CPU runtime unavailable"):
        load(folder)


def protocol_runtime(monkeypatch, *, finite=True, shape=(2, 256), version="0.9.0"):
    calls = []

    class Matrix:
        dtype = "float32"
        nbytes = 2048

        def setflags(self, **kw):
            calls.append(("setflags", kw))

    matrix = Matrix()
    matrix.shape = shape
    tokenizer = SimpleNamespace(
        get_vocab=lambda: {"[UNK]": 0, "public": 1},
        no_padding=lambda: calls.append(("padding_disabled",)),
        no_truncation=lambda: calls.append(("truncation_disabled",)),
    )

    class StaticModel:
        def __init__(self, **kw):
            calls.append(("constructor", kw))

        @classmethod
        def from_pretrained(cls, *args, **kw):
            pytest.fail("automatic pretrained loader must never be called")

    monkeypatch.setattr(potion.importlib.util, "find_spec", lambda _: object())
    monkeypatch.setattr(
        potion.importlib.metadata,
        "version",
        lambda name: version if name == "model2vec" else "test-only",
    )
    monkeypatch.setitem(
        sys.modules,
        "numpy",
        SimpleNamespace(
            dtype=lambda value: value,
            isfinite=lambda _: SimpleNamespace(all=lambda: finite),
        ),
    )
    monkeypatch.setitem(
        sys.modules, "model2vec", SimpleNamespace(StaticModel=StaticModel)
    )
    monkeypatch.setitem(sys.modules, "safetensors", SimpleNamespace())
    monkeypatch.setitem(
        sys.modules,
        "safetensors.numpy",
        SimpleNamespace(load_file=lambda _: {"embeddings": matrix}),
    )
    monkeypatch.setitem(
        sys.modules,
        "tokenizers",
        SimpleNamespace(Tokenizer=SimpleNamespace(from_file=lambda _: tokenizer)),
    )
    monkeypatch.setattr(
        socket.socket,
        "connect",
        lambda *args: pytest.fail("local loader must not connect to the network"),
    )
    return calls


def test_constructs_only_local_frozen_numpy_cpu_model(tmp_path, monkeypatch):
    folder = bundle(tmp_path)
    calls = protocol_runtime(monkeypatch)
    encoder = load(folder)
    assert isinstance(encoder, LocalCPUEncoder)
    assert encoder.metadata["model_id"] == potion.MODEL_ID
    assert encoder.metadata["revision"] == potion.MODEL_REVISION
    assert encoder.metadata["dimensions"] == 256
    assert encoder.metadata["device"] == "cpu"
    assert encoder.metadata["parameter_bytes"] == 2048
    assert encoder.metadata["load_seconds"] > 0
    assert encoder.metadata["automatic_download"] is False
    assert encoder.metadata["remote_inference"] is False
    assert calls[:3] == [
        ("padding_disabled",),
        ("truncation_disabled",),
        ("setflags", {"write": False}),
    ]
    assert calls[3][1]["normalize"] is True
    assert calls[3][1]["config"] == {"normalize": True}


@pytest.mark.parametrize(
    "change", [{"finite": False}, {"shape": (2, 384)}, {"version": "0.9.1"}]
)
def test_runtime_matrix_and_version_are_checked(tmp_path, monkeypatch, change):
    folder = bundle(tmp_path)
    protocol_runtime(monkeypatch, **change)
    with pytest.raises(SemanticUnavailable):
        load(folder)


class ProtocolVectors(list):
    @property
    def shape(self):
        return (len(self), len(self[0]) if self else 0)


def test_bounded_cpu_encode_and_empty_input():
    calls = []

    def encode(texts, **kw):
        calls.append((texts, kw))
        return ProtocolVectors([(1.0,) + (0.0,) * 255 for _ in texts])

    encoder = potion.PotionCPUEncoder(model=SimpleNamespace(encode=encode), metadata={})
    assert encoder.encode(()) == ()
    result = encoder.encode(("public coding task", "sanitized requirements"))
    assert len(result) == 2 and len(result[0]) == 256
    assert calls == [
        (
            ["public coding task", "sanitized requirements"],
            {
                "max_length": 256,
                "batch_size": 1,
                "use_multiprocessing": False,
                "show_progress_bar": False,
            },
        )
    ]
    for invalid in ("", " ", "x" * 4097, 1):
        with pytest.raises(ValueError, match="bounded nonblank"):
            encoder.encode((invalid,))
    assert len(calls) == 1


@pytest.mark.parametrize("vector", [(float("nan"),) * 256, (2.0,) * 256, (0.0,) * 384])
def test_invalid_output_dimensions_finiteness_and_normalization(vector):
    encoder = potion.PotionCPUEncoder(
        model=SimpleNamespace(encode=lambda *a, **kw: ProtocolVectors([vector])),
        metadata={},
    )
    with pytest.raises(SemanticUnavailable):
        encoder.encode(("public coding task",))


def test_unknown_token_zero_vector_policy_is_finite():
    encoder = potion.PotionCPUEncoder(
        model=SimpleNamespace(encode=lambda *a, **kw: ProtocolVectors([(0.0,) * 256])),
        metadata={},
    )
    assert all(math.isfinite(x) for x in encoder.encode(("unknown",))[0])


@pytest.mark.skipif(
    not os.environ.get("MODEL_LEARNER_TEST_POTION_PATH"),
    reason="explicit approved local pretrained model path required",
)
def test_actual_approved_pretrained_potion_cpu_without_network(monkeypatch):
    # Separately opt in to a real local pretrained integration; never download.
    path = os.environ["MODEL_LEARNER_TEST_POTION_PATH"]
    monkeypatch.setattr(
        socket.socket,
        "connect",
        lambda *args: pytest.fail("CPU inference attempted network access"),
    )
    digest, _ = potion.digest_potion_bundle(path)
    encoder = potion.load_potion_encoder(
        path, expected_sha256=digest, revision=potion.MODEL_REVISION
    )
    public_descriptions = (
        "Implement a bounded parser for public JSON metadata.",
        "Add independent tests for sorting a public list.",
    )
    first = encoder.encode(public_descriptions)
    assert first == encoder.encode(public_descriptions)
    assert len(first) == 2 and all(len(vector) == 256 for vector in first)
    assert first[0] != first[1]
    assert all(
        all(math.isfinite(x) for x in vector)
        and math.isclose(sum(x * x for x in vector), 1, abs_tol=1e-5)
        for vector in first
    )
    assert encoder._model.embedding.flags.writeable is False
    assert encoder._model.embedding.dtype.name == "float32"
    assert encoder.metadata["parameter_bytes"] == 30236672
    assert encoder.metadata["vocabulary_size"] == 29528
    assert encoder.metadata["dimensions"] == 256
    assert encoder.metadata["device"] == "cpu"
