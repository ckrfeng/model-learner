"""Synthetic offline stdio peer; never an agent executor."""

import copy
import json
import os
import sys
import time
from pathlib import Path

fixture = json.loads(Path(__file__).with_name("history.json").read_text())
mode = os.environ.get("MODEL_LEARNER_FIXTURE_MODE", "normal")

for line in sys.stdin:
    request = json.loads(line)
    method = request["method"]
    if method == "initialized":
        continue
    if mode == "timeout":
        time.sleep(2)
        break
    if mode == "eof":
        break
    if mode == "malformed":
        print("PRIVATE_MALFORMED_SENTINEL", flush=True)
        continue
    if mode == "oversized":
        print("x" * 65537, flush=True)
        continue
    if mode == "server_request":
        print(
            json.dumps(
                {
                    "method": "item/commandExecution/requestApproval",
                    "id": 500,
                    "params": {"command": "PRIVATE_COMMAND_SENTINEL"},
                }
            ),
            flush=True,
        )
        continue
    if mode == "rpc_error":
        print(
            json.dumps(
                {
                    "id": request["id"],
                    "error": {"code": -1, "message": "PRIVATE_RPC_SENTINEL"},
                }
            ),
            flush=True,
        )
        continue
    if method == "initialize":
        result = {"userAgent": "fixture-server"}
    elif method == "thread/read":
        thread = copy.deepcopy(fixture["thread"])
        thread["id"] = request["params"]["threadId"]
        thread["originator"] = os.environ.get(
            "MODEL_LEARNER_FIXTURE_ORIGINATOR", "Codex Desktop"
        )
        result = {"thread": thread}
    elif method == "thread/turns/list":
        index = int(request["params"].get("cursor", "0").split(":")[-1])
        prefix = os.environ.get("MODEL_LEARNER_FIXTURE_CURSOR_PREFIX", "")
        turn = copy.deepcopy(fixture["turns"][2 - index])
        view = request["params"]["itemsView"]
        turn["itemsView"] = view
        if view == "notLoaded":
            turn["items"] = []
        elif mode == "malformed_item_type":
            turn["items"][0]["type"] = ["PRIVATE_MALFORMED_TYPE_SENTINEL"]
        result = {
            "data": [turn],
            "nextCursor": prefix + str(index + 1) if index < 2 else None,
            "backwardsCursor": str(index),
        }
    else:
        raise RuntimeError("unexpected method in fake peer")
    identity = request["id"] + (100 if mode == "wrong_id" else 0)
    if mode == "notification":
        print(
            json.dumps(
                {
                    "method": "notification",
                    "params": {"private": "PRIVATE_NOTIFICATION_SENTINEL"},
                }
            ),
            flush=True,
        )
    print(json.dumps({"id": identity, "result": result}), flush=True)
