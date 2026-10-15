"""The tools' own glue around the web: what Andy is told when a lookup works, finds nothing, or fails.

The tools import the conversation app's Tool base class, which runs only on the robot; a stand-in
for it is enough here, because the glue under test is the tool's own code.
"""

import asyncio
import importlib.util
import sys
import types
from pathlib import Path

import pytest

from andy_companion import board, scamcheck, web

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def check_message(tmp_path, monkeypatch):
    for name in ("SCREEN", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    core = types.ModuleType("reachy_mini_conversation_app.tools.core_tools")
    core.Tool, core.ToolDependencies = type("Tool", (), {}), object
    for name in ("reachy_mini_conversation_app", "reachy_mini_conversation_app.tools"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setitem(sys.modules, core.__name__, core)
    spec = importlib.util.spec_from_file_location("andy_tool_check_message", ROOT / "tools" / "check_message.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def run(message="You've won! Pay the fee to claim it."):
        return asyncio.run(module.CheckMessage()(None, message=message))
    return run


NO_SIGN = {"scam_signs": False, "sign": "none", "evidence": "", "source": "", "matched": []}


def down(text):
    raise web.WebError("The web did not answer (URLError).")


def test_when_the_web_lookup_fails_andy_never_says_no_sign(check_message, monkeypatch):
    """Without the warnings, "no sign of a known scam" would be false comfort."""
    monkeypatch.setattr(web, "check_message", down)
    monkeypatch.setattr(scamcheck, "verdict", lambda message, found: dict(NO_SIGN))
    out = check_message()
    assert out["web_unavailable"] is True and "scam_signs" not in out
    assert "couldn't check the scam warnings online" in out["say"] and "best not to reply, pay or give any details" in out["say"]
    assert "no sign" not in out["say"].lower()
    assert board.showing()["title"] != "No sign of a known kind of scam"


def test_when_both_checks_fail_andy_still_says_to_be_careful(check_message, monkeypatch):
    def broken(message, found):
        raise scamcheck.ScamCheckError("The scam check could not be made (OSError).")

    monkeypatch.setattr(web, "check_message", down)
    monkeypatch.setattr(scamcheck, "verdict", broken)
    out = check_message()
    assert out["web_unavailable"] is True and "best not to reply, pay or give any details" in out["say"]


def test_a_sign_in_the_message_is_still_said_when_the_web_is_down(check_message, monkeypatch):
    monkeypatch.setattr(web, "check_message", down)
    monkeypatch.setattr(scamcheck, "verdict", lambda message, found: {
        **NO_SIGN, "scam_signs": True, "sign": "a fee to receive a prize, refund or inheritance", "evidence": "Pay the fee"})
    out = check_message()
    assert out["scam_signs"] is True and out["web_unavailable"] is True and "sign of a known kind of scam" in out["say"]


def test_no_sign_with_the_warnings_in_hand_is_said_as_before(check_message, monkeypatch):
    monkeypatch.setattr(web, "check_message", lambda text: [])
    monkeypatch.setattr(scamcheck, "verdict", lambda message, found: dict(NO_SIGN))
    out = check_message("The pharmacy says your prescription is ready.")
    assert out["scam_signs"] is False and "web_unavailable" not in out and "no sign" in out["say"]
