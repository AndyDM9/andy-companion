"""Regression checks for the October 26 review, using invented data only."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

import pytest

from andy_companion import board, consent, kept, letters, screen_server


@pytest.mark.parametrize("words", ["Tell me a joke.", "I had dinner with my family.",
                                   "Send me the weather forecast.", "Let me think."])
def test_conversation_is_not_a_sharing_request(words):
    assert not consent.asked_to_share(words)


def proposal(state, name="share_with_family", args=None):
    args = args or {"note": "The recital went well"}
    state.hear("Please share that with my daughter")
    out = state.authorize(name, args)
    assert out["confirmation_needed"]
    return args, out


def test_sharing_requires_the_exact_readback_and_a_new_yes_and_is_one_use():
    state = consent.Confirmation()
    args, out = proposal(state)
    state.said(out["say"])
    assert state.authorize("share_with_family", args)["confirmation_needed"]  # still no yes
    state.said(out["say"])
    state.hear("Yes please")
    assert state.authorize("share_with_family", args) is None
    assert state.authorize("share_with_family", args)["shared"] is False


@pytest.mark.parametrize("change", ["payload", "tool", "expiry", "new_topic", "no_readback", "refusal"])
def test_a_yes_cannot_authorize_something_else(change):
    now = [100.0]
    state = consent.Confirmation(clock=lambda: now[0])
    args, out = proposal(state)
    if change != "no_readback":
        state.said(out["say"])
    if change == "expiry":
        now[0] += consent.CONFIRM_FOR_S + 1
    if change == "new_topic":
        state.hear("What is the weather?")
    state.hear("No thanks" if change == "refusal" else "Yes")
    name = "remember" if change == "tool" else "share_with_family"
    args = {"note": "A different note"} if change == "payload" else args
    assert state.authorize(name, args) is not None


def test_unrelated_yes_and_separate_conversation_do_not_release_a_write():
    a, b = consent.Confirmation(), consent.Confirmation()
    args, out = proposal(a)
    a.said(out["say"])
    b.hear("Yes")
    assert b.authorize("share_with_family", args)["shared"] is False
    a.hear("Yes")
    assert a.authorize("share_with_family", args) is None


@pytest.mark.parametrize("kind", ["medicine", "bill", "other"])
def test_medicine_instructions_cannot_hide_in_any_card_field(kind):
    instruction = "Example tablets: take two daily"
    raw = {"kind": kind, "suspicious": False, **{f: instruction for f in letters.FIELDS}}
    card = letters.card(raw, instruction)
    assert all(card[f] == "" for f in letters.FIELDS if f != "caution")
    assert "two" not in json.dumps(card)


def test_a_medicine_page_never_reaches_the_model_even_if_card_service_is_down(monkeypatch):
    called = []
    result = letters.for_andy({"text": "Pharmacy tablets: synthetic instructions", "words": 6},
                              summariser=lambda *a: called.append(a))
    assert not called and "text" not in result and result["medicine"]
    assert "synthetic instructions" not in json.dumps(result)
    assert "synthetic instructions" not in json.dumps(board.showing())


@pytest.mark.parametrize("text", ["Example 500mg", "Example 20ml", "Pastillas de ejemplo", "Example pills"])
def test_medicine_labels_are_detected_without_spaces_or_english_words(text):
    assert letters.medicine_page(text)


def test_screen_and_research_text_stay_off_disk_and_are_deleted(tmp_path, monkeypatch):
    for name in ("SCREEN", "INBOX", "SHARED", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / (name.lower() + ".json"))
    marker = "invented transient review text"
    board.show("check", "Receipt", [{"summary": marker}])
    board.research_ready(marker, "An invented answer", [], [])
    assert marker in json.dumps(board.showing())
    assert not board.SCREEN.exists() and not board.INBOX.exists()
    pending = kept.summary()["pending"]
    assert len(pending) == 1 and pending[0]["text"] == marker
    assert kept.delete("pending", pending[0]["id"])
    screen_server.set_caption(marker)
    kept.delete_everything()
    assert board.showing() is None and screen_server.caption() == ""
    assert not board.SCREEN.exists()


def test_actual_cross_process_board_transport_and_token_boundary(tmp_path, monkeypatch):
    for name in ("SCREEN", "INBOX", "SHARED", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / (name.lower() + ".json"))
    httpd = screen_server.serve("127.0.0.1", 0)
    try:
        port = httpd.server_address[1]
        env = {**os.environ, "ANDY_DATA_DIR": str(tmp_path), "ANDY_SCREEN_PORT": str(port),
               "PYTHONPATH": str(Path(__file__).resolve().parents[1] / "src")}
        code = """from andy_companion import board
board.show('letter', 'Invented letter', [{'summary':'temporary words'}])
board.research_ready('invented question', 'invented answer', [], [])
assert board.showing()['title'] == 'Invented letter'
assert board.next_for_person()['topic'] == 'invented question'
"""
        subprocess.run([sys.executable, "-c", code], env=env, check=True, capture_output=True, timeout=15)
        assert board.showing()["title"] == "Invented letter"
        assert not board.SCREEN.exists() and not board.INBOX.exists()
        req = urllib.request.Request(f"http://127.0.0.1:{port}/api/transient?t=wrong", data=b'{"action":"clear"}')
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req, timeout=2)
        assert e.value.code == 404 and board.showing() is not None
    finally:
        httpd.shutdown()
        httpd.server_close()


def test_journal_read_failures_cannot_be_a_clean_privacy_check(monkeypatch):
    path = Path(__file__).resolve().parents[1] / "scripts" / "doctor.py"
    spec = importlib.util.spec_from_file_location("doctor_review", path)
    doctor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(doctor)
    monkeypatch.setattr(doctor.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 1, "", "failed"))
    assert doctor.voice_log() is None
    assert doctor.lines_with_words("INFO: USER: invented words") == 1
    assert doctor.lines_with_words("2026-10-26 10:00:00,000 - Live: invented words") == 1
    def unavailable(*a, **k):
        raise OSError("unavailable")
    monkeypatch.setattr(doctor.subprocess, "run", unavailable)
    assert doctor.voice_log() is None


def test_a_running_research_cannot_repopulate_deleted_private_state(monkeypatch):
    import threading
    from andy_companion import looking, web
    monkeypatch.setattr(looking, "_stop", threading.Event())
    def stream(question, place, language, on_step, opener):
        on_step("planning", "")
        kept.delete_everything()
        on_step("writing", "")
        return {"say": "This must never be delivered", "sources": []}
    monkeypatch.setattr(web, "stream_research", stream)
    assert looking.run("Invented question") is None
    assert board.showing() is None and not board.pending_entries()


@pytest.mark.parametrize("language, starts", [("en", "It asks for gift cards"), ("es", "Pide tarjetas de regalo")])
def test_a_scam_about_medicine_still_gets_its_warning_and_no_page_text(language, starts):
    """2026-10-28 review: a Medicare 'prescription coverage' scam got only the medicine refusal, its signs dropped."""
    page = ("Your Medicare prescription coverage will be suspended within 24 hours. To keep your pharmacy benefits, "
            "pay the renewal fee with Google Play gift cards. Call 1-888-555-0199. Tablets 20mg daily.")
    called = []
    result = letters.for_andy({"text": page, "words": 30}, language, summariser=lambda *a: called.append(a))
    assert not called and "text" not in result and result["medicine"] and result["warning_signs"]
    assert result["say"].startswith(starts)
    assert "pharmac" in result["say"] or "farmac" in result["say"]
    shown = json.dumps(board.showing(), ensure_ascii=False)
    for words in ("Medicare", "Google Play", "20mg", "1-888", "renewal"):
        assert words not in json.dumps(result, ensure_ascii=False) and words not in shown
    assert ("Be careful" in shown or "Cuidado" in shown) and starts in shown


def test_a_medicine_page_without_signs_is_unchanged():
    result = letters.for_andy({"text": "Pharmacy tablets: synthetic instructions", "words": 6}, summariser=lambda *a: None)
    assert result["medicine"] and "warning_signs" not in result
    assert result["say"] == "I can't read medicine instructions. Please ask your pharmacist or doctor."
