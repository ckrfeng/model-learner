"""Reproduce the fixed synthetic C experiment in fresh, network-disabled workers."""

import argparse
import json
import socket
import subprocess
import sys
import time
from dataclasses import asdict
from datetime import UTC, datetime, timedelta
from pathlib import Path
from statistics import fmean, median

from model_learner.representation import (
    evaluate_task_representation,
    generate_representation_fixture,
)
from model_learner.representation.potion import (
    MODEL_ID,
    MODEL_REVISION,
    load_potion_encoder,
)
from model_learner.representation.semantic import peak_rss_bytes


def _worker(path: Path, digest: str, seed: int, scenario: str) -> dict:
    attempts = []

    def deny(*args, **kwargs):
        attempts.append(True)
        raise RuntimeError("network disabled during CPU semantic evaluation")

    socket.create_connection = deny
    socket.socket.connect = deny
    socket.socket.connect_ex = deny
    before_load = peak_rss_bytes()
    encoder = load_potion_encoder(path, expected_sha256=digest, revision=MODEL_REVISION)
    rows = generate_representation_fixture(seed=seed, count=150, scenario=scenario)
    start = datetime(2026, 1, 1, tzinfo=UTC)
    report = evaluate_task_representation(
        rows,
        dataset=rows[0].state.observation.dataset,
        acceptance_spec=rows[0].state.observation.acceptance_spec,
        train_until=start + timedelta(seconds=180 * 90),
        evaluation_at=start + timedelta(seconds=180 * 150),
        bootstrap_replicates=300,
        seed=seed,
        encoder=encoder,
        semantic_model_id=MODEL_ID,
    )
    if any(v.status != "evaluated" for v in report.variants):
        raise ValueError("actual pretrained A/B/C evaluation did not complete")
    scored_units = {unit for unit, _ in report.variants[2].predictions}
    texts = tuple(
        e.description.text
        for e in rows
        if str(e.state.observation.run_id) in scored_units
    )
    samples = []
    for _ in range(5):
        for text in texts:
            began = time.perf_counter()
            encoder.encode((text,))
            samples.append(time.perf_counter() - began)
    samples.sort()
    value = asdict(report)
    for variant in value["variants"]:
        variant.pop("predictions")
    value["overhead"]["fresh_process_measurement"] = {
        "peak_rss_bytes_before_model_load": before_load,
        "peak_rss_bytes_after_all_measurements": peak_rss_bytes(),
        "rss_basis": (
            "whole fresh worker process lifetime high-water mark; "
            "not incremental model RAM"
        ),
        "network_connections_attempted": len(attempts),
        "single_description_latency": {
            "basis": (
                "five serial passes over the same scored public descriptions "
                "after evaluation warmup"
            ),
            "sample_count": len(samples),
            "median_seconds": median(samples),
            "p95_seconds": samples[int((len(samples) - 1) * 0.95)],
            "mean_seconds": fmean(samples),
        },
    }
    if attempts:
        raise ValueError("CPU inference attempted network access")
    return value


def run_experiment(path: Path, digest: str, reference: dict) -> dict:
    """Reuse original data/settings and refuse publication if any A/B metric changes."""
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
    scenarios = {}
    for scenario in ("state_signal", "null_signal"):
        reports = []
        for seed in range(5):
            completed = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "model_learner.representation.potion_experiment",
                    "--worker",
                    "--model-path",
                    str(path),
                    "--bundle-sha256",
                    digest,
                    "--seed",
                    str(seed),
                    "--scenario",
                    scenario,
                ],
                env=environment,
                capture_output=True,
                text=True,
                timeout=60,
                check=False,
            )
            if completed.returncode:
                raise ValueError("fixed CPU evaluation worker failed")
            report = json.loads(completed.stdout)
            previous = reference["scenarios"][scenario]["reports"][seed]
            for key in (
                "cohort_sha256",
                "training_count",
                "scored_count",
                "exclusions",
                "training_family_count",
                "scored_family_count",
            ):
                if report[key] != previous[key]:
                    raise ValueError(
                        "evaluation cohort changed from the frozen reference"
                    )
            if report["variants"][:2] != previous["variants"][:2] or (
                report["comparisons"][0] != previous["comparisons"][0]
            ):
                raise ValueError("A/B predictive baseline changed")
            reports.append(report)
        scenarios[scenario] = {
            "mean_A_brier": fmean(r["variants"][0]["brier_score"] for r in reports),
            "mean_B_brier": fmean(r["variants"][1]["brier_score"] for r in reports),
            "mean_C_brier": fmean(r["variants"][2]["brier_score"] for r in reports),
            "mean_B_minus_C": fmean(
                r["comparisons"][1]["brier_improvement"] for r in reports
            ),
            "reports": reports,
        }
    return {
        "version": "potion-cpu-synthetic-experiment/v1",
        "model_id": MODEL_ID,
        "model_revision": MODEL_REVISION,
        "bundle_sha256": digest,
        "source_kind": "simulated",
        "seeds": list(range(5)),
        "count_per_seed": 150,
        "train_fraction": 0.6,
        "scenarios": scenarios,
        "interpretation": (
            "Synthetic integration and predictive rehearsal only. Descriptions have no "
            "designed semantic outcome signal. Equal-seed means are descriptive; "
            "per-seed family intervals condition on fixed fits. No real-world claim."
        ),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model-path", type=Path, required=True)
    parser.add_argument("--bundle-sha256", required=True)
    parser.add_argument("--reference", type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--worker", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument(
        "--seed", type=int, choices=range(5), default=1, help=argparse.SUPPRESS
    )
    parser.add_argument(
        "--scenario",
        choices=("state_signal", "null_signal"),
        default="state_signal",
        help=argparse.SUPPRESS,
    )
    args = parser.parse_args()
    if args.worker:
        print(
            json.dumps(
                _worker(args.model_path, args.bundle_sha256, args.seed, args.scenario),
                allow_nan=False,
            )
        )
        return
    if args.reference is None or args.output is None:
        parser.error("--reference and a new --output file are required")
    if args.output.exists():
        parser.error("output exists; refusing overwrite")
    report = run_experiment(
        args.model_path, args.bundle_sha256, json.loads(args.reference.read_text())
    )
    with args.output.open("x") as output:
        json.dump(report, output, indent=2, sort_keys=True, allow_nan=False)
        output.write("\n")
    print(json.dumps({"output": str(args.output), "source_kind": "simulated"}))


if __name__ == "__main__":
    main()
