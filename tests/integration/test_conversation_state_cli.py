import json
from pathlib import Path

from typer.testing import CliRunner

from model_learner.cli import app

FIXTURE = Path(__file__).parents[1] / "fixtures/conversation_state/evaluation.json"


def test_stdin_demo_is_opted_in_redacted_and_writes_nothing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    raw = json.dumps(
        {
            "messages": [
                {"role": "user", "text": "Build a PRIVATE_PARSER.", "turn": 1},
                {"role": "assistant", "text": "Done.", "turn": 1},
            ]
        }
    )
    runner = CliRunner()
    denied = runner.invoke(app, ["task", "conversation-state"], input=raw)
    assert denied.exit_code == 2
    assert "--text-opt-in" in denied.output
    for options, text in [([], False), (["--emit-text"], True)]:
        result = runner.invoke(
            app, ["task", "conversation-state", "--text-opt-in", *options], input=raw
        )
        assert result.exit_code == 0, result.output
        payload = json.loads(result.output)
        assert payload["text_emitted"] == text
        assert ("PRIVATE_PARSER" in result.output) == text
        assert payload["timeline"][-1]["state"]["verification"] == "unknown"
    assert list(tmp_path.iterdir()) == []


def test_invalid_private_input_is_not_echoed():
    r = CliRunner().invoke(
        app,
        ["task", "conversation-state", "--text-opt-in"],
        input='{"PRIVATE_SECRET":true}',
    )
    assert r.exit_code == 2
    assert "PRIVATE_SECRET" not in r.output


def test_installed_evaluation_command():
    r = CliRunner().invoke(app, ["learn", "conversation-state-eval", str(FIXTURE)])
    assert r.exit_code == 0, r.output
    assert json.loads(r.output)["variants"]["rules"]["intent_count"] == 54
    demo = FIXTURE.with_name("demo.json").read_text()
    r = CliRunner().invoke(
        app, ["task", "conversation-state", "--text-opt-in"], input=demo
    )
    assert r.exit_code == 0, r.output
    result = json.loads(r.output)
    assert result["source_kind"] == "simulated"
    assert result["timeline"][-1]["state"]["verification"] == "verified"
    assert all(c["state"]["verification"] == "unknown" for c in result["timeline"][:-1])
    reversal = next(f for f in result["facts"] if f["intent"] == "decision_reversed")
    assert reversal["links"]


def test_existing_importer_bridge(tmp_path, monkeypatch):
    import sys

    peer = Path(__file__).parents[1] / "fixtures/conversations/app_server.py"
    executable = tmp_path / "fixture-codex"
    executable.write_text(
        f"#!{sys.executable}\nimport runpy\n"
        f'runpy.run_path({str(peer)!r},run_name="__main__")\n'
    )
    executable.chmod(0o700)
    result = CliRunner().invoke(
        app,
        [
            "task",
            "conversation-state",
            "--text-opt-in",
            "--conversation-id",
            "00000000-0000-4000-8000-000000000001",
            "--product-source",
            "codex_desktop",
            "--machine-id",
            "fixture",
            "--codex-executable",
            str(executable),
        ],
    )
    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["coverage"]["messages"] == 6
    assert len(payload["timeline"]) == 6
    assert "PRIVATE_" not in result.output
    assert not (tmp_path / ".model-learner").exists()


def test_invalid_fixture_root_is_content_free(tmp_path):
    fixture = tmp_path / "invalid.json"
    fixture.write_text("null")
    result = CliRunner().invoke(app, ["learn", "conversation-state-eval", str(fixture)])
    assert result.exit_code == 2
    assert "invalid authored evaluation" in result.output
