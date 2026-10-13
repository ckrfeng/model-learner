"""Frozen serial comparison; model input is source-only and loopback-only."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import resource
import signal
import subprocess
import time
import urllib.error
import urllib.request
from datetime import UTC, datetime
from pathlib import Path

from experiments.local_task_state.extract import (
    Extraction,
    frozen_extract,
    structure_extract,
    validate_output,
)

HERE = Path(__file__).resolve().parent
SETTINGS = {
    "seed": 20261013,
    "temperature": 0.0,
    "top_k": 1,
    "max_tokens": 3072,
    "cache_prompt": False,
    "stream": False,
}


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, data):
    with path.open("x") as handle:
        os.chmod(path, 0o600)
        json.dump(data, handle, indent=2, ensure_ascii=False)


def request(url, data=None, timeout=180):
    body = None if data is None else json.dumps(data).encode()
    req = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}
    )

    # Ignore all proxy environment variables; no source text can leave loopback.
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            raise ValueError("redirects are prohibited")

    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
    with opener.open(req, timeout=timeout) as response:
        return json.load(response)


def model_request(messages, port):
    return request(
        f"http://127.0.0.1:{port}/v1/chat/completions",
        {
            **SETTINGS,
            "messages": [
                {"role": "system", "content": (HERE / "prompt.txt").read_text()},
                {
                    "role": "user",
                    "content": json.dumps({"messages": messages}, ensure_ascii=False),
                },
            ],
            "response_format": {
                "type": "json_schema",
                "json_schema": {
                    "name": "task_state",
                    "strict": True,
                    "schema": Extraction.model_json_schema(),
                },
            },
        },
    )


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--sources", type=Path, required=True)
    parser.add_argument("--freeze", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--runtime", type=Path, required=True)
    parser.add_argument("--weights", type=Path, required=True)
    parser.add_argument("--port", type=int, default=18743)
    args = parser.parse_args()
    freeze = json.loads(args.freeze.read_text())
    for filename, expected in freeze["files_sha256"].items():
        if digest(Path(filename)) != expected:
            raise ValueError("freeze integrity mismatch")
    if str(args.sources.resolve()) not in freeze["files_sha256"]:
        raise ValueError("source is not frozen")
    if digest(args.weights) != freeze["weights_sha256"]:
        raise ValueError("weight integrity mismatch")
    if digest(args.runtime) != freeze["runtime_sha256"]:
        raise ValueError("runtime integrity mismatch")
    source = json.loads(args.sources.read_text())
    all_ids = []
    for conversation in source["conversations"]:
        turns = []
        for message in conversation["messages"]:
            if message["role"] != "user" or type(message["turn"]) is not int:
                raise ValueError("source must contain user messages with integer turns")
            if not isinstance(message["text"], str) or not isinstance(
                message["id"], str
            ):
                raise ValueError("source text and identity must be strings")
            all_ids.append(message["id"])
            turns.append(message["turn"])
        if turns != sorted(turns) or any(t < 1 for t in turns):
            raise ValueError("source turns must be chronological and positive")
    if len(set(all_ids)) != len(all_ids):
        raise ValueError("source message identities must be unique")
    args.out.mkdir(mode=0o700)
    command = [
        str(args.runtime.resolve()),
        "-m",
        str(args.weights.resolve()),
        "--device",
        "none",
        "-ngl",
        "0",
        "--no-kv-offload",
        "-t",
        "6",
        "-tb",
        "6",
        "-c",
        "8192",
        "-np",
        "1",
        "--host",
        "127.0.0.1",
        "--port",
        str(args.port),
        "--no-cache-prompt",
        "--no-context-shift",
        "--no-webui",
        "--no-slots",
        "--reasoning",
        "off",
    ]
    env = {k: v for k, v in os.environ.items() if not k.startswith("LLAMA_")}
    env["GGML_METAL_DISABLE"] = "1"
    started = time.perf_counter()
    started_at = datetime.now(UTC).isoformat()
    log = (args.out / "runtime.log").open("x")
    os.chmod(args.out / "runtime.log", 0o600)
    process = subprocess.Popen(command, stdout=log, stderr=log, env=env)
    try:
        deadline = time.monotonic() + 60
        while True:
            if process.poll() is not None:
                raise RuntimeError("local runtime exited before readiness")
            try:
                request(f"http://127.0.0.1:{args.port}/health", timeout=1)
                break
            except (urllib.error.URLError, TimeoutError):
                if time.monotonic() >= deadline:
                    raise RuntimeError("local runtime startup timeout") from None
                time.sleep(0.1)
        load_seconds = time.perf_counter() - started
        for ci, conversation in enumerate(source["conversations"]):
            for mi, _ in enumerate(conversation["messages"]):
                messages = conversation["messages"][: mi + 1]
                out_of_bounds = (
                    len(messages) > 128
                    or sum(len(m["text"].encode()) for m in messages) > 65536
                    or any(len(m["text"]) > 16384 for m in messages)
                )
                rows = {}
                for variant, extract in (
                    ("A", frozen_extract),
                    ("B", structure_extract),
                    ("C", None),
                ):
                    began = time.perf_counter()
                    row = {
                        "variant": variant,
                        "conversation_id": conversation["id"],
                        "message_id": messages[-1]["id"],
                        "available": False,
                        "source_kind": source["source_kind"],
                        "input_sha256": hashlib.sha256(
                            json.dumps(messages, sort_keys=True).encode()
                        ).hexdigest(),
                    }
                    try:
                        if out_of_bounds:
                            raise ValueError(
                                "source bounds exceeded; no clipping permitted"
                            )
                        if variant == "C":
                            response = model_request(messages, args.port)
                            row["runtime_response"] = response
                            row["finish_reason"] = response["choices"][0][
                                "finish_reason"
                            ]
                            if row["finish_reason"] != "stop":
                                raise ValueError("generation incomplete")
                            raw = json.loads(
                                response["choices"][0]["message"]["content"]
                            )
                        else:
                            raw = (
                                extract(messages, source_kind=source["source_kind"])
                                if variant == "A"
                                else extract(messages)
                            )
                        row["raw"] = raw
                        row["extraction"] = validate_output(raw, messages)
                        row["available"] = True
                    except (
                        ValueError,
                        urllib.error.URLError,
                        TimeoutError,
                        KeyError,
                    ) as error:
                        row["error_type"] = type(error).__name__
                        # No private diagnostic text in terminal output.
                    row["seconds"] = time.perf_counter() - began
                    rows[variant] = row
                write(
                    args.out / f"case-{ci + 1:02d}-checkpoint-{mi + 1:02d}.json", rows
                )
                print(
                    f"case {ci + 1} checkpoint {mi + 1}: saved A/B/C; "
                    f"C {rows['C']['seconds']:.2f}s",
                    flush=True,
                )
    finally:
        if process.poll() is None:
            process.send_signal(signal.SIGINT)
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
        log.close()
        write(
            args.out / "resources.json",
            {
                "command": command,
                "settings": SETTINGS,
                "runtime_exit": process.returncode,
                "load_seconds": locals().get("load_seconds"),
                "peak_runtime_rss_bytes": resource.getrusage(
                    resource.RUSAGE_CHILDREN
                ).ru_maxrss,
                "driver_peak_rss_bytes": resource.getrusage(
                    resource.RUSAGE_SELF
                ).ru_maxrss,
                "method": (
                    "macOS getrusage; one runtime child in a fresh "
                    "driver process; ru_maxrss bytes"
                ),
                "started_at": started_at,
                "finished_at": datetime.now(UTC).isoformat(),
                "freeze_sha256": digest(args.freeze),
                "sources_sha256": digest(args.sources),
            },
        )


if __name__ == "__main__":
    main()
