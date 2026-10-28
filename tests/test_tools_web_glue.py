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
    run.module = module
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


def test_the_tv_says_checking_at_once_and_the_verdict_replaces_it(check_message, monkeypatch):
    """2026-10-28, on the robot: about five silent seconds while the warnings were looked up. The TV now says so at
    once; the verdict's card comes after it."""
    from andy_companion import scamcheck
    titles = []
    real_show = board.show
    monkeypatch.setattr(board, "show", lambda kind, title, *a, **k: titles.append((kind, title)) or real_show(kind, title, *a, **k))
    monkeypatch.setattr(web, "check_message", lambda text: [])
    monkeypatch.setattr(scamcheck, "verdict", lambda *a, **k: dict(NO_SIGN))
    check_message("The pharmacy says your prescription is ready.")
    assert titles[0] == ("check", "Checking this message") and titles[-1] == ("check", "No sign of a known kind of scam")


def test_a_screen_that_fails_never_stops_the_check(check_message, monkeypatch):
    from andy_companion import scamcheck
    calls = []
    def flaky(kind, title, *a, **k):
        calls.append(title)
        if len(calls) == 1:
            raise OSError("screen down")
    monkeypatch.setattr(board, "show", flaky)
    monkeypatch.setattr(web, "check_message", lambda text: [])
    monkeypatch.setattr(scamcheck, "verdict", lambda *a, **k: dict(NO_SIGN))
    out = check_message("The pharmacy says your prescription is ready.")
    assert out["scam_signs"] is False and calls[-1] == "No sign of a known kind of scam"


def test_the_same_message_checked_again_soon_is_answered_from_the_first_check(check_message, monkeypatch):
    """2026-10-28, on the robot: the model called check_message twice in one turn, 12.8 s before Andy spoke."""
    from andy_companion import scamcheck
    looked = []
    monkeypatch.setattr(web, "check_message", lambda text: looked.append(text) or [])
    monkeypatch.setattr(scamcheck, "verdict", lambda *a, **k: dict(NO_SIGN))
    first = check_message("Pay the fee with gift cards today.")
    again = check_message("pay the fee with gift cards today")              # case and punctuation aside, the same
    assert len(looked) == 1 and again["already_checked"] and again["scam_signs"] is first["scam_signs"]
    assert "Do not check it again" in again["note"] and "already_checked" not in first
    check_message("A different message about a parcel.")
    assert len(looked) == 2


def test_a_failed_check_is_never_reused_and_old_ones_expire(check_message, monkeypatch):
    from andy_companion import scamcheck
    module = check_message.module
    looked = []
    def flaky(text):
        looked.append(text)
        if len(looked) == 1:
            raise web.WebError("The web did not answer (URLError).")
        return []
    monkeypatch.setattr(web, "check_message", flaky)
    monkeypatch.setattr(scamcheck, "verdict", lambda *a, **k: dict(NO_SIGN))
    assert check_message("Pay the fee with gift cards today.")["web_unavailable"]
    assert "web_unavailable" not in check_message("Pay the fee with gift cards today.")   # tried again, and it worked
    clock = [module.time.monotonic() + module.AGAIN_S + 1]
    monkeypatch.setattr(module.time, "monotonic", lambda: clock[0])
    check_message("Pay the fee with gift cards today.")                              # two minutes on: checked afresh
    assert len(looked) == 3 and not module._recent.get("pay the fee with gift cards today", (0, {}))[1].get("already_checked")


def test_a_spanish_household_sees_the_scam_cards_in_spanish(check_message, monkeypatch):
    """2026-10-28 review: the checking, no-sign and failure cards were English on a Spanish household's TV."""
    from andy_companion import scamcheck, settings
    titles = []
    real_show = board.show
    monkeypatch.setattr(board, "show", lambda kind, title, items, *a, **k: titles.append((title, items)) or real_show(kind, title, items, *a, **k))
    monkeypatch.setattr(settings, "get", lambda: {"language": "es"})
    monkeypatch.setattr(web, "check_message", lambda text: [])
    monkeypatch.setattr(scamcheck, "verdict", lambda *a, **k: dict(NO_SIGN))
    check_message("La farmacia dice que su receta está lista.")
    assert titles[0][0] == "Revisando este mensaje" and titles[-1][0] == "Sin señales de una estafa conocida"
    assert titles[-1][1][0]["title"].startswith("Si tiene dudas")
