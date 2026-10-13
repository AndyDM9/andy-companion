import json
import urllib.request

import pytest

from andy_companion import board, live, screen_server, settings, state, turns, words


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(state, "FILE", tmp_path / "state.json")
    state.awake()
    screen_server._live.update(state="", tool="", at=0.0)


def test_the_state_follows_the_turn():
    ticks = [100.0]
    clock = turns.TurnClock(clock=lambda: ticks[0])
    assert live.derive(clock, False)["state"] == "ready"
    clock.mark("user_speech_started")
    assert live.derive(clock, False)["state"] == "hearing"
    clock.mark("user_speech_stopped")
    clock.mark("user_transcription_completed")
    assert live.derive(clock, False)["state"] == "thinking"
    clock.running, clock.current_tool = 1, "weather"
    assert live.derive(clock, False) == {"state": "working", "tool": "weather"}
    clock.running = 0
    assert live.derive(clock, True)["state"] == "speaking"


def test_changes_are_sent_and_a_heartbeat_keeps_the_screen_sure():
    sent = []
    t = [0.0]

    def tick(s):
        t[0] += 1.0

    live.report_loop(send=sent.append, rounds=12, sleep=tick, now=lambda: t[0])
    import time
    time.sleep(0.05)
    assert sent and all(x == {"live": {"state": "ready", "tool": ""}} for x in sent)
    assert 2 <= len(sent) <= 4                       # first, then about every 5 s, not every tick


def test_the_strip_says_what_andy_is_doing_in_words():
    screen_server.set_live({"state": "working", "tool": "look_up"})
    assert screen_server.live_state()["label"] == "Looking that up"
    assert screen_server.live_state()["stage"] == "tools"
    settings.update(language="es")
    assert screen_server.live_state()["label"] == "Buscando"


def test_quiet_and_asleep_win_and_silence_reads_as_away():
    screen_server.set_live({"state": "ready", "tool": ""}, now=1000.0)
    assert screen_server.live_state(now=1000.0 + screen_server.LIVE_STALE_S + 1)["state"] == "away"
    state.quiet_for(30)
    s = screen_server.live_state()
    assert s["state"] == "quiet" and s["label"].startswith("Quiet until ") and "Andy, wake up" in s["label"]
    state.asleep()
    assert screen_server.live_state()["label"] == words.STATE["en"]["asleep"]


def test_only_known_states_and_tool_names_are_kept():
    for bad in ({"state": "plotting"}, {"state": "working", "tool": "my bank PIN"}, "text"):
        with pytest.raises(ValueError):
            screen_server.set_live(bad)


def test_the_state_is_served_with_the_screen_token():
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    try:
        url = f"http://127.0.0.1:{httpd.server_address[1]}"
        screen_server.set_live({"state": "speaking", "tool": ""})
        with urllib.request.urlopen(f"{url}/api/state?t={board.tokens()['screen']}", timeout=5) as r:
            assert json.loads(r.read())["label"] == "Speaking"
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(f"{url}/api/state?t=wrong", timeout=5)
    finally:
        httpd.shutdown()
