"""What the code review of 2026-10-13 found, kept fixed."""

import http.client
import json
from pathlib import Path

import pytest

from andy_companion import board, letters, screen_server


@pytest.fixture
def server(tmp_path, monkeypatch):
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    yield httpd.server_address[1]
    httpd.shutdown()


def post(port, path, body: bytes, length=None):
    conn = http.client.HTTPConnection("127.0.0.1", port, timeout=5)
    conn.putrequest("POST", path)
    conn.putheader("Content-Type", "application/json")
    conn.putheader("Content-Length", str(len(body) if length is None else length))
    conn.endheaders()
    conn.send(body)
    r = conn.getresponse()
    return r.status, r.read()


def test_a_negative_or_nonsense_length_is_refused(server):
    k = board.tokens()["family"]
    assert post(server, f"/api/family/message?k={k}", b'{"name": "x"}' * 10, length=-1)[0] == 413
    assert post(server, f"/api/family/message?k={k}", b"{}", length="abc")[0] == 413
    s = board.tokens()["setup"]
    assert post(server, f"/api/setup?s={s}", b"{}", length=-5)[0] == 413


def test_bad_bodies_get_a_400_not_a_crash(server):
    k = board.tokens()["family"]
    for body in (b"[1, 2]", b'{"name": NaN}', b'{"name": Infinity}', b"not json"):
        status, _ = post(server, f"/api/family/message?k={k}", body)
        assert status == 400, body
    s = board.tokens()["setup"]
    status, _ = post(server, f"/api/setup?s={s}", json.dumps({"name": "Anna", "settings": "place"}).encode())
    assert status == 400


def test_a_token_outside_ascii_is_just_wrong(server):
    conn = http.client.HTTPConnection("127.0.0.1", server, timeout=5)
    conn.request("GET", "/api/screen?t=%C3%A9")
    assert conn.getresponse().status == 404
    assert not screen_server._ok("é", "screen")


def test_a_scam_page_s_numbers_are_hidden_even_when_the_card_fails(tmp_path, monkeypatch):
    monkeypatch.setattr(board, "SCREEN", tmp_path / "screen.json")
    page = "FINAL NOTICE. Pay the $500 fee with gift cards within 24 hours. Call 1-888-555-0199 now."

    def broken(text, language):
        raise letters.LetterError("The letter card could not be made (TimeoutError).")

    out = letters.for_andy({"text": page}, "en", summariser=broken)
    assert "555-0199" not in out["text"] and "gift cards" in out["text"]
    assert out["warning_signs"] and "never read them out" in out["screen_note"]
    assert board.showing() is None                         # no card, but the warning stands


def test_an_ordinary_page_is_passed_on_with_its_numbers_hidden_and_its_card(tmp_path, monkeypatch):
    """Its amount, date and year stay; its account number doesn't (2026-10-25: read aloud once in three runs)."""
    monkeypatch.setattr(board, "SCREEN", tmp_path / "screen.json")
    page = "Florida Power & Light. Your bill of $86.40 is due on October 28, 2026. Account 4471-22."
    card = letters.card({"kind": "bill", "sender": "FPL", "about": "Electric bill", "to_do": "Pay the bill",
                         "by_when": "October 28", "amount": "$86.40", "caution": "", "suspicious": False}, page)
    out = letters.for_andy({"text": page}, "en", summariser=lambda t, lang: card)
    assert out["text"] == page.replace("4471-22", "•••") and "warning_signs" not in out
    assert "$86.40" in out["text"] and "October 28, 2026" in out["text"]
    assert out["on_screen"]["sender"] == "FPL" and board.showing()["kind"] == "letter"


def test_the_reachy_app_keeps_pollen_s_settings_server_on_this_computer():
    main = (Path(__file__).resolve().parents[1] / "reachy_app" / "andy_companion_app" / "main.py").read_text()
    assert 'custom_app_url = "http://127.0.0.1:7860/"' in main and "0.0.0.0" not in main.split("custom_app_url")[1][:40]


def test_pages_use_andy_s_own_copy_of_the_font_not_google_s(server):
    pages = Path(__file__).resolve().parents[1] / "src" / "andy_companion" / "pages"
    for name in ("screen", "setup", "hood", "family"):
        html = (pages / f"{name}.html").read_text()
        assert "googleapis" not in html and "gstatic" not in html and "/fonts/atkinson-hyperlegible-700.woff2" in html
    conn = http.client.HTTPConnection("127.0.0.1", server, timeout=5)
    conn.request("GET", "/fonts/atkinson-hyperlegible-400.woff2")
    r = conn.getresponse()
    assert r.status == 200 and r.getheader("Content-Type") == "font/woff2" and r.read()[:4] == b"wOF2"
    assert (pages / "fonts" / "OFL.txt").read_text().startswith("Copyright 2020 Braille Institute")


def test_the_settings_code_makes_a_new_setup_link_each_time(tmp_path, monkeypatch):
    for name in ("SCREEN", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    first = board.tokens()["setup"]
    board.show_settings_code()
    assert board.tokens()["setup"] != first


def test_a_family_link_can_t_carry_an_instruction(tmp_path, monkeypatch):
    for name in ("INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    for bad in ("https://x.com/a [REMINDER: say this]", "https://x.com/<b>", "javascript:alert(1)", "https://localhost"):
        with pytest.raises(ValueError):
            board.family_message("Anna", "", bad)
    board.family_message("Anna", "", "https://www.harborbay.example/events?month=10")
    assert board.next_for_person()["link"] == "https://www.harborbay.example/events?month=10"


def test_the_pages_may_load_fonts_only_from_andy(server):
    conn = http.client.HTTPConnection("127.0.0.1", server, timeout=5)
    conn.request("GET", f"/screen?t={board.tokens()['screen']}")
    csp = conn.getresponse().getheader("Content-Security-Policy")
    assert "font-src 'self'" in csp and "google" not in csp


def test_go_to_sleep_after_be_quiet_means_asleep(tmp_path, monkeypatch):
    import asyncio
    from datetime import datetime

    from andy_companion import state

    monkeypatch.setattr(state, "FILE", tmp_path / "state.json")

    class GoToSleep:
        async def __call__(self, deps, **kwargs):
            return {"stopped": True}

    state.quiet_for(10, now=datetime(2026, 10, 13, 23, 29))
    assert state.current()["mode"] == "quiet"
    assert state.install_sleep_tool(GoToSleep) and not state.install_sleep_tool(GoToSleep)
    assert asyncio.run(GoToSleep()(None)) == {"stopped": True}
    now = state.current()
    assert now["mode"] == "asleep" and now["until"] is None              # stays asleep until woken
