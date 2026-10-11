"""Reproduce frozen retrieval comparisons with fresh, network-disabled CPU workers.

Explicit fixture/model paths only. No discovery, download or outcome labels.
"""

from __future__ import annotations

import argparse
import json
import math
import platform
import socket
import subprocess
import sys
import time
from pathlib import Path
from statistics import fmean, median

from model_learner.representation.potion import MODEL_REVISION, load_potion_encoder
from model_learner.representation.semantic import peak_rss_bytes
from model_learner.understanding.evaluation import (
    evaluate_retrieval,
    load_retrieval_dataset,
)
from model_learner.understanding.retrieval import TaskText, build_retrieval_index


def _samples(values: list[float]) -> dict:
    ordered = sorted(values)
    return {
        "sample_count": len(values),
        "median_seconds": median(values),
        "mean_seconds": fmean(values),
        "p95_seconds": ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)],
    }


def _worker(args) -> dict:
    attempts = []

    def deny(*unused_args, **unused_kwargs):
        attempts.append(True)
        raise RuntimeError("network disabled during semantic retrieval experiment")

    socket.create_connection = deny
    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    dataset, digest = load_retrieval_dataset(
        args.dataset, expected_sha256=args.dataset_sha256
    )
    before_load = peak_rss_bytes()
    encoder = None
    load_seconds = None
    first_encode_seconds = None
    encode_latency = None
    if args.method == "embedding":
        began = time.perf_counter()
        encoder = load_potion_encoder(
            args.model_path,
            expected_sha256=args.bundle_sha256,
            revision=MODEL_REVISION,
        )
        load_seconds = time.perf_counter() - began
        began = time.perf_counter()
        encoder.encode((dataset.candidates[0].text,))
        first_encode_seconds = time.perf_counter() - began
    reports = {
        split: evaluate_retrieval(
            dataset, method=args.method, split=split, encoder=encoder
        )
        for split in ("development", "test")
    }
    test_candidates = tuple(row for row in dataset.candidates if row.split == "test")
    test_queries = tuple(row for row in dataset.queries if row.split == "test")
    index = build_retrieval_index(
        tuple(
            TaskText(task_id=row.task_id, text=row.text, source="public")
            for row in test_candidates
        ),
        method=args.method,
        encoder=encoder,
    )
    samples = []
    for _ in range(5):
        for query in test_queries:
            declaration = TaskText(
                task_id=query.task_id, text=query.text, source="public"
            )
            began = time.perf_counter()
            index.search(declaration, k=3, minimum_score=None)
            samples.append(time.perf_counter() - began)
    if encoder is not None:
        samples_encode = []
        for _ in range(5):
            for row in (*test_candidates, *test_queries):
                began = time.perf_counter()
                encoder.encode((row.text,))
                samples_encode.append(time.perf_counter() - began)
        encode_latency = _samples(samples_encode)
    if attempts:
        raise ValueError("CPU evaluation attempted a network connection")
    return {
        "dataset_sha256": digest,
        "method": args.method,
        "reports": reports,
        "resources": {
            "basis": "fresh worker; five warm serial passes; OS caches not cleared",
            "query_search_latency": _samples(samples),
            "query_search_latency_basis": (
                "includes query representation, cosine/overlap scoring and sorting "
                "36 candidates; excludes candidate indexing and model load"
            ),
            "model_load_seconds": load_seconds,
            "model_load_basis": (
                "imports, bounded snapshot/hash validation and model construction; "
                "null for lexical methods"
            ),
            "first_description_encode_seconds": first_encode_seconds,
            "warm_single_description_encode_latency": encode_latency,
            "encoder_metadata": encoder.metadata if encoder is not None else None,
            "whole_process_peak_rss_bytes_before_load": before_load,
            "whole_process_peak_rss_bytes_after_measurements": peak_rss_bytes(),
            "rss_basis": (
                "whole worker process lifetime high-water; not incremental model RAM"
            ),
            "network_connection_attempts": len(attempts),
            "platform": {
                "system": platform.system(),
                "machine": platform.machine(),
                "python": platform.python_version(),
            },
        },
    }


def run_experiment(args) -> dict:
    """Fresh baseline and embedding processes; fixed dataset and rankings replay."""
    load_retrieval_dataset(args.dataset, expected_sha256=args.dataset_sha256)
    environment = {
        "PATH": str(Path(sys.executable).parent) + ":/usr/bin:/bin",
        "HF_HUB_OFFLINE": "1",
        "TOKENIZERS_PARALLELISM": "false",
        "OPENBLAS_NUM_THREADS": "1",
        "OMP_NUM_THREADS": "1",
        "MKL_NUM_THREADS": "1",
        "VECLIB_MAXIMUM_THREADS": "1",
        "NUMEXPR_NUM_THREADS": "1",
    }
    workers = []
    replay_fingerprints = {}
    methods = ("text", "tfidf", "embedding") if args.model_path else ("text", "tfidf")
    for method in methods:
        for _ in range(args.repetitions):
            command = [
                sys.executable,
                "-m",
                "model_learner.understanding.experiment",
                "--worker",
                "--dataset",
                str(args.dataset.absolute()),
                "--dataset-sha256",
                args.dataset_sha256,
                "--method",
                method,
            ]
            if args.model_path:
                command += [
                    "--model-path",
                    str(args.model_path.absolute()),
                    "--bundle-sha256",
                    args.bundle_sha256,
                ]
            completed = subprocess.run(
                command,
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if completed.returncode:
                raise ValueError("semantic retrieval experiment worker failed")
            worker = json.loads(completed.stdout)
            # Repetitions measure overhead, not new accuracy samples. Require
            # reported top hits/relevant ranks/metrics to replay without timings.
            fingerprint = {
                split: {
                    "metrics": report["metrics"],
                    "by_family": report["by_family"],
                    "queries": [
                        {
                            key: value
                            for key, value in row.items()
                            if key != "query_seconds"
                        }
                        for row in report["queries"]
                    ],
                }
                for split, report in worker["reports"].items()
            }
            if (
                method in replay_fingerprints
                and fingerprint != replay_fingerprints[method]
            ):
                raise ValueError("retrieval ranks or metrics changed between workers")
            replay_fingerprints[method] = fingerprint
            workers.append(worker)
    return {
        "experiment_version": "semantic-retrieval/v1",
        "dataset_sha256": args.dataset_sha256,
        "repetitions": args.repetitions,
        "methods": list(methods),
        "thread_limits_requested": True,
        "socket_connections_blocked_in_workers": True,
        "limitations": (
            "descriptive six-family authored test fixture; correlated rewrites; "
            "not independent human-adjudicated data, population inference, "
            "continuation classification or agent-success prediction"
        ),
        "workers": workers,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", type=Path, required=True)
    parser.add_argument("--dataset-sha256", required=True)
    parser.add_argument("--model-path", type=Path)
    parser.add_argument("--bundle-sha256")
    parser.add_argument("--repetitions", type=int, default=3)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--method", choices=("text", "tfidf", "embedding"), help=argparse.SUPPRESS
    )
    args = parser.parse_args()
    if not 1 <= args.repetitions <= 10:
        parser.error("repetitions must be between 1 and 10")
    if bool(args.model_path) != bool(args.bundle_sha256):
        parser.error("model path and approved bundle digest must be supplied together")
    if args.worker:
        if args.method is None or (
            args.method == "embedding" and args.model_path is None
        ):
            parser.error("worker requires a method and embedding requires local model")
        print(json.dumps(_worker(args)))
        return
    if args.output is None:
        parser.error("parent experiment requires an output path")
    if args.output.exists():
        parser.error("refusing to overwrite experiment output")
    result = run_experiment(args)
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print("Frozen semantic retrieval experiment completed.")


if __name__ == "__main__":
    main()
