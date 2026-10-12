"""Source ordering, boundaries, missingness and private-content projection."""

import copy
import json
from pathlib import Path

import pytest

from model_learner.adapters.app_server import ConversationError
from model_learner.adapters.conversations import PRODUCTS, read_conversation

FIXTURE = Path(__file__).parents[1] / "fixtures/conversations/history.json"


class FixtureClient:
    def __init__(self, product="codex_desktop", data=None, count=3):
        self.data = data or json.loads(FIXTURE.read_text())
        self.data = copy.deepcopy(self.data)
        self.data["thread"]["originator"] = PRODUCTS[product]
        self.conversation_id = self.data["thread"]["id"]
        self.calls = []
        self.count = count

    def request(self, method, params):
        self.calls.append((method, params))
        assert params["threadId"] == self.conversation_id
        if method == "thread/read":
            assert params["includeTurns"] is False
            return {"thread": copy.deepcopy(self.data["thread"])}
        assert method == "thread/turns/list"
        index = int(params.get("cursor", "0"))
        turn = copy.deepcopy(self.data["turns"][(self.count - index - 1) % 3])
        if self.count > 3:
            turn["id"] = f"turn-{self.count - index - 1}"
        turn["itemsView"] = params["itemsView"]
        if params["itemsView"] == "notLoaded":
            turn["items"] = []
        return {
            "data": [turn],
            "nextCursor": str(index + 1) if index < self.count - 1 else None,
        }


@pytest.mark.parametrize("product", list(PRODUCTS))
def test_full_text_projection_order_and_exact_fidelity(product):
    client = FixtureClient(product)
    read = read_conversation(
        client, product_source=product, machine_id="fixture", read_text=True
    )
    assert [t["native_turn_id"] for t in read.metadata["turns"]] == [
        "turn-0",
        "turn-1",
        "turn-2",
    ]
    assert [t["source_page_index"] for t in read.metadata["turns"]] == [2, 1, 0]
    assert [t["source_turn_ordinal"] for t in read.metadata["turns"]] == [0, 1, 2]
    assert read.coverage()["roles_by_turn"] == [["user", "assistant"]] * 3
    assert read.metadata["turns"][0]["messages"][1]["source_item_ordinal"] == 2
    assert read.metadata["turns"][0]["excluded_nonmessage_items"] == 2
    assert read.metadata["turns"][0]["messages"][0]["excluded_nontext_parts"] == 1
    assert read.text["user-1"] == [
        client.data["turns"][1]["items"][0]["content"][0]["text"]
    ]
    assert read.text["agent-1"][0].endswith("  ")
    assert read.metadata["history_exhausted"] and not read.metadata["bounded_history"]
    projected = json.dumps(read.metadata)
    assert "PRIVATE_" not in projected
    assert "current-only" not in projected
    assert "Whitespace" not in projected
    assert "café" not in repr(read)
    assert read.metadata["historical_configuration"] is None
    assert all(
        m["timestamp"] is None for t in read.metadata["turns"] for m in t["messages"]
    )


def test_default_omits_items_server_side():
    client = FixtureClient()
    read = read_conversation(
        client, product_source="codex_desktop", machine_id="fixture"
    )
    assert read.text == {}
    assert all(
        params["itemsView"] == "notLoaded"
        for method, params in client.calls
        if method == "thread/turns/list"
    )
    assert all(
        t["messages"] is None and t["items_missingness"] == "not_requested"
        for t in read.metadata["turns"]
    )
    assert read.coverage()["messages"] is None


def test_native_order_does_not_sort_timestamps_or_ids():
    client = FixtureClient()
    client.data["turns"][0]["startedAt"] = 1900000000
    client.data["turns"][1]["startedAt"] = None
    read = read_conversation(
        client, product_source="codex_desktop", machine_id="fixture"
    )
    assert [t["native_turn_id"] for t in read.metadata["turns"]] == [
        "turn-0",
        "turn-1",
        "turn-2",
    ]
    assert read.metadata["turns"][1]["started_at_seconds"] is None


def test_bounded_history_preserves_continuation_and_missingness():
    read = read_conversation(
        FixtureClient(count=11), product_source="codex_desktop", machine_id="fixture"
    )
    assert len(read.metadata["turns"]) == 10
    assert read.metadata["bounded_history"] and not read.metadata["history_exhausted"]
    assert read.metadata["pages"][-1]["has_more"] is True
    assert read.metadata["original_history_complete"] is None


def test_explicit_truncation_survives_projection():
    client = FixtureClient()
    client.data["turns"][1]["truncated"] = True
    client.data["turns"][1]["items"][1]["isTruncated"] = True
    read = read_conversation(
        client, product_source="codex_desktop", machine_id="fixture", read_text=True
    )
    turn = read.metadata["turns"][1]
    assert turn["source_truncated"] is True
    assert turn["messages"][1]["source_truncated"] is True
    assert read.metadata["turns"][0]["source_truncated"] is None


@pytest.mark.parametrize(
    "field,value",
    [
        ("historyMode", "legacy"),
        ("source", "appServer"),
        ("threadSource", "subagent"),
        ("originator", "other"),
        ("id", "other"),
        ("createdAt", True),
        ("turns", [{}]),
        ("ephemeral", True),
    ],
)
def test_unsupported_thread_formats_rejected_without_echo(field, value):
    client = FixtureClient()
    client.data["thread"][field] = value
    with pytest.raises(ConversationError) as raised:
        read_conversation(client, product_source="codex_desktop", machine_id="fixture")
    assert "PRIVATE" not in str(raised.value)


@pytest.mark.parametrize(
    "mutation",
    [
        "duplicate_turn",
        "duplicate_message",
        "new_item",
        "bad_text",
        "wrong_view",
        "bad_duration",
        "text_limit",
    ],
)
def test_malformed_full_history_is_rejected(mutation):
    client = FixtureClient()
    if mutation == "duplicate_turn":
        client.data["turns"][0]["id"] = "turn-1"
    elif mutation == "duplicate_message":
        client.data["turns"][1]["items"][0]["id"] = "user-2"
    elif mutation == "new_item":
        client.data["turns"][1]["items"][0]["type"] = "futureUnsupportedItem"
    elif mutation == "bad_text":
        client.data["turns"][1]["items"][0]["content"][0]["text"] = None
    elif mutation == "bad_duration":
        client.data["turns"][1]["durationMs"] = -1
    elif mutation == "text_limit":
        client.data["turns"][1]["items"][1]["text"] = "x" * 65537
    else:
        original = client.request

        def request(method, params):
            result = original(method, params)
            if method == "thread/turns/list":
                result["data"][0]["itemsView"] = "summary"
            return result

        client.request = request
    with pytest.raises(ConversationError):
        read_conversation(
            client, product_source="codex_desktop", machine_id="fixture", read_text=True
        )


def test_bad_cursor_is_rejected():
    client = FixtureClient()
    original = client.request

    def request(method, params):
        result = original(method, params)
        if method == "thread/turns/list":
            result["nextCursor"] = "1"
        return result

    client.request = request
    with pytest.raises(ConversationError, match="repeated continuation"):
        read_conversation(client, product_source="codex_desktop", machine_id="fixture")
