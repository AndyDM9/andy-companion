import asyncio
import json
import urllib.error
import urllib.request

import pytest

from andy_companion import board, screen_server, settings, turns


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    screen_server._turns.clear()


@pytest.fixture
def server(monkeypatch):
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    monkeypatch.setattr(turns, "SCREEN", f"http://127.0.0.1:{httpd.server_address[1]}")
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


class Ticks:
    def __init__(self):
        self.now = 100.0

    def __call__(self):
        return self.now


def run(clock, ticks, steps):
    out = None
    for at, reason in steps:
        ticks.now = at
        out = clock.mark(reason) or out
    return out


def test_a_turn_is_measured_from_the_end_of_the_words_to_the_first_sound():
    ticks = Ticks()
    clock = turns.TurnClock(clock=ticks, wall=lambda: 1_000)
    turn = run(clock, ticks, [(100.0, "user_speech_started"), (102.0, "user_speech_stopped"),
                              (102.3, "user_transcription_completed"), (102.5, "response_created"),
                              (103.1, "assistant_audio_delta"), (103.4, "assistant_audio_delta"),
                              (104.0, "assistant_transcript_done")])
    assert turn == {"at": 1_000, "hearing_ms": 300, "reply_ms": 800, "total_ms": 1100, "tools": []}


def test_a_reply_nobody_asked_for_is_not_a_turn():
    """A reminder Andy says on its own has no words before it to time from."""
    ticks = Ticks()
    clock = turns.TurnClock(clock=ticks)
    assert run(clock, ticks, [(100.0, "say"), (100.5, "assistant_audio_delta"), (101.0, "assistant_transcript_done")]) is None


def test_speaking_over_andy_starts_a_new_turn():
    ticks = Ticks()
    clock = turns.TurnClock(clock=ticks)
    run(clock, ticks, [(100.0, "user_speech_stopped"), (100.2, "user_transcription_completed"), (100.4, "user_speech_started")])
    assert run(clock, ticks, [(101.0, "assistant_audio_delta"), (101.5, "assistant_transcript_done")]) is None


def test_tools_are_timed_by_name_only():
    ticks = Ticks()
    clock = turns.TurnClock(clock=ticks)
    run(clock, ticks, [(100.0, "user_speech_stopped"), (100.2, "user_transcription_completed")])
    clock.tool("local_news", 1.234)
    clock.tool("My PIN is 1234", 0.1)          # never a name; never kept
    turn = run(clock, ticks, [(102.0, "assistant_audio_delta"), (102.5, "assistant_transcript_done")])
    assert turn["tools"] == [{"name": "local_news", "ms": 1234}]


def test_install_times_turns_and_tools_without_arguments():
    sent = []

    class Handler:
        def _mark_activity(self, reason):
            self.last = reason

    class Routine:
        tool_name = "look_up"
        args_json_str = '{"query": "my daughter Sofia"}'

        async def __call__(self, manager):
            return {"ok": True}

    ticks = Ticks()
    clock = turns.TurnClock(clock=ticks)
    original = turns.send
    turns.send = lambda turn, opener=None: sent.append(turn)
    try:
        assert turns.install(Handler, Routine, clock) is True
        assert turns.install(Handler, Routine, clock) is False
        h = Handler()
        for at, reason in [(100.0, "user_speech_stopped"), (100.2, "user_transcription_completed")]:
            ticks.now = at
            h._mark_activity(reason)
        assert asyncio.run(Routine()(None)) == {"ok": True}
        for at, reason in [(101.0, "assistant_audio_delta"), (101.2, "assistant_transcript_done")]:
            ticks.now = at
            h._mark_activity(reason)
        assert h.last == "assistant_transcript_done"          # Pollen's own method still runs
        import time
        for _ in range(50):
            if sent:
                break
            time.sleep(0.01)
    finally:
        turns.send = original
    assert len(sent) == 1 and sent[0]["tools"][0]["name"] == "look_up"
    assert "Sofia" not in json.dumps(sent)


def hood(server):
    with urllib.request.urlopen(f"{server}/api/hood?t={board.tokens()['screen']}", timeout=5) as r:
        return json.loads(r.read())


def test_turns_reach_the_hood_page_with_medians(server):
    for total in (900, 1100, 1300):
        turns.send({"hearing_ms": 200, "reply_ms": total - 200, "total_ms": total, "tools": []})
    turns.send({"hearing_ms": 200, "reply_ms": 5000, "total_ms": 5200, "tools": [{"name": "describe_view", "ms": 3500}]})
    s = hood(server)
    assert s["count"] == 4
    assert s["median"] == {"hearing_ms": 200, "reply_ms": 900, "total_ms": 1100}   # tool turns kept out of the median
    assert s["turns"][0]["tools"] == [{"name": "describe_view", "ms": 3500}]


def test_the_hood_keeps_numbers_and_names_and_nothing_else(server):
    turns.send({"hearing_ms": 200, "reply_ms": 700, "total_ms": 900, "text": "my bank PIN",
                "tools": [{"name": "look_up", "ms": 10, "args": "my bank PIN"}, {"name": "my bank PIN", "ms": 1}]})
    assert "PIN" not in json.dumps(hood(server))


def test_a_turn_needs_the_screen_token(server):
    req = urllib.request.Request(f"{server}/api/turn?t=wrong", method="POST", data=b'{"reply_ms": 1}')
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(req, timeout=5)
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(f"{server}/hood?t=wrong", timeout=5)


def test_a_bad_turn_is_refused(server):
    for body in (b'{"reply_ms": "soon"}', b'[1, 2]', b'{"reply_ms": -5}'):
        req = urllib.request.Request(f"{server}/api/turn?t={board.tokens()['screen']}", method="POST", data=body)
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req, timeout=5)
        assert e.value.code == 400
    assert hood(server)["count"] == 0


def test_the_hood_page_is_served(server):
    with urllib.request.urlopen(f"{server}/hood?t={board.tokens()['screen']}", timeout=5) as r:
        page = r.read().decode()
    assert "Under the hood" in page and "Nebius Token Factory" in page
