import json
import threading
import time
import urllib.error
import urllib.request

import pytest

from andy_companion import board, captions, screen_server, settings


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    screen_server.set_caption("", now=0)


@pytest.fixture
def server(monkeypatch):
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    monkeypatch.setattr(captions, "SCREEN", f"http://127.0.0.1:{httpd.server_address[1]}")
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def screen(server):
    with urllib.request.urlopen(f"{server}/api/screen?t={board.tokens()['screen']}", timeout=5) as r:
        return json.loads(r.read())


def test_andys_words_reach_the_screen_and_fade(server):
    captions.send("It's time to call Rosa.")
    assert screen(server)["caption"] == "It's time to call Rosa."
    screen_server._caption["at"] -= screen_server.CAPTION_FOR_S + 1
    assert screen(server)["caption"] == ""


def test_a_whole_reply_is_kept_with_when_it_was_sent(server):
    # The screen pages through all of it at reading pace, timed from caption_at, so a TV that opens
    # mid-story does not start again (the founder saw only the last sentence, 2026-10-14).
    story = "A Lion lay asleep in the forest. " * 40
    captions.send(story)
    shown = screen(server)
    assert shown["caption"] == " ".join(story.split())[:2000] and len(shown["caption"]) > 1000
    assert abs(shown["caption_at"] - time.time()) < 5
    screen_server._caption["at"] -= screen_server.CAPTION_FOR_S + 1
    assert screen(server)["caption_at"] is None


def test_captions_can_be_turned_off(server):
    settings.update(captions=False)
    captions.send("Hello")
    assert screen(server)["caption"] == ""


def test_a_caption_needs_the_screen_token(server):
    req = urllib.request.Request(f"{server}/api/caption?t=wrong", method="POST", data=b'{"text":"x"}')
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(req, timeout=5)


def test_only_andys_words_are_captioned():
    sent = []

    class Handler:
        def _emit_transcript(self, role, text, final=True):
            pass

    import andy_companion.captions as c
    original = c.send
    c.send = lambda text, opener=None: sent.append(text)
    try:
        captions.install(Handler)
        h = Handler()
        h._emit_transcript("user", "my private words", True)
        h._emit_transcript("assistant", "Good afternoon!", True)
        h._emit_transcript("assistant", "partial", False)
        time.sleep(0.1)
    finally:
        c.send = original
    assert sent == ["Good afternoon!"]


def test_captions_never_touch_the_disk(server, tmp_path):
    captions.send("A private sentence")
    assert not any("A private sentence" in p.read_text(errors="ignore") for p in tmp_path.rglob("*") if p.is_file())
