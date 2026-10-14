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
    screen_server._interrupts.clear()
    screen_server._tavily.clear()


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
    with urllib.request.urlopen(f"{server}/api/hood?t={board.tokens()['hood']}", timeout=5) as r:
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
    with urllib.request.urlopen(f"{server}/hood?t={board.tokens()['hood']}", timeout=5) as r:
        page = r.read().decode()
    assert "Under the hood" in page and "Nebius Token Factory" in page


def test_the_hood_has_its_own_token_and_it_opens_nothing_else(server):
    """A /hood link shared for its timings used to carry the screen's token, so it could read the captions and
    reminders and put the settings code (full control of Andy) on the TV (review, 2026-10-14)."""
    t = board.tokens()
    assert t["hood"] != t["screen"]
    for path in ("/hood", "/api/hood"):                                  # the screen's token no longer opens it
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(f"{server}{path}?t={t['screen']}", timeout=5)
        assert e.value.code == 404
    for path in ("/screen", "/api/screen", "/frame", "/photo"):           # and the hood's opens only the hood
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(f"{server}{path}?t={t['hood']}", timeout=5)
    for path in ("/api/screen/settings-code", "/api/caption", "/api/turn"):
        req = urllib.request.Request(f"{server}{path}?t={t['hood']}", method="POST", data=b"{}")
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(req, timeout=5)
    assert board.showing() is None
    with urllib.request.urlopen(f"{server}/api/state?t={t['hood']}", timeout=5) as r:   # the hood's state strip
        assert "label" in json.loads(r.read())


def test_the_screen_learns_the_hood_link_and_the_hood_goes_back_only_to_the_screen(server):
    t = board.tokens()
    with urllib.request.urlopen(f"{server}/api/screen?t={t['screen']}", timeout=5) as r:
        assert json.loads(r.read())["links"] == {"hood": f"/hood?t={t['hood']}"}
    from pathlib import Path

    pages = Path(__file__).resolve().parents[1] / "src" / "andy_companion" / "pages"
    hood_page = (pages / "hood.html").read_text()
    assert "/screen?t=" not in hood_page and "history.back()" in hood_page    # never the hood's token on /screen
    assert 'id="back-row" hidden' in hood_page and 'params.get("from") === "screen"' in hood_page
    screen_page = (pages / "screen.html").read_text()
    assert 'hoodLink + "&from=screen"' in screen_page and "/hood?t=" not in screen_page


def test_the_hood_shows_the_newest_suite_scorecard(tmp_path, monkeypatch):
    monkeypatch.setenv("TZ", "America/New_York")
    import time
    time.tzset()
    (tmp_path / "old.json").write_text(json.dumps({"ran": "2026-10-12T10:00:00", "per_run": [40], "total": 44}))
    (tmp_path / "new.json").write_text(json.dumps({"ran": "2026-10-13T18:00:00", "per_run": [57, 56, 56], "total": 57,
                                                   "suite": "2026-10-13k", "judge": "nvidia/Nemotron-3-Ultra-550b-a55b"}))
    (tmp_path / "other.json").write_text(json.dumps({"ran": "2026-10-14", "rows": []}))   # not a scorecard
    (tmp_path / "broken.json").write_text("{")
    # A job's naive time is UTC: 2026-10-13T20:00 UTC is 16:00 in Miami, older than the local 18:00 run.
    (tmp_path / "job.json").write_text(json.dumps({"ran": "2026-10-13T20:00:00", "per_run": [33], "total": 36,
                                                   "ran_on": "Nebius Serverless Job, cpu-d3 2vcpu-8gb"}))
    p = screen_server.proof(tmp_path)
    assert p == {"suite": "2026-10-13k", "per_run": [57, 56, 56], "total": 57, "judge": "Nemotron-3-Ultra-550b-a55b",
                 "ran": "2026-10-13", "ran_on": "this computer"}
    assert screen_server.proof(tmp_path / "missing") is None


def test_talking_over_andy_shows_on_the_hood_page(server):
    turns.send({"interrupt_ms": 2400})
    turns.send({"interrupt_ms": 900, "text": "my words"})
    s = hood(server)
    assert s["interruptions"] == {"count": 2, "last_cut_ms": 900}
    assert "my words" not in json.dumps(s)


def test_a_bad_interruption_is_refused(server):
    req = urllib.request.Request(f"{server}/api/turn?t={board.tokens()['screen']}", method="POST",
                                 data=b'{"interrupt_ms": "lots"}')
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(req, timeout=5)


def test_how_much_of_andys_voice_is_left():
    from andy_companion.body import speaking

    speaking.cleared()
    speaking.pushed(48000, 16000, now=10.0)          # three seconds of voice pushed at t=10
    assert speaking.remaining(now=11.0) == 2.0
    speaking.cleared()
    assert speaking.remaining(now=11.0) == 0.0


def test_tavily_credits_reach_the_hood_page_as_numbers_only(server, monkeypatch):
    from andy_companion import web

    monkeypatch.setattr(web, "usage", lambda opener=None: {"plan": "Researcher", "used": 84, "limit": 1000,
                                                           "by": {"search": 79, "extract": 5, "query": "my words"}})
    turns.tavily_usage_loop(rounds=1)
    t = hood(server)["tavily"]
    assert t == {"plan": "Researcher", "used": 84, "limit": 1000,
                 "by": {"search": 79, "extract": 5, "crawl": 0, "map": 0, "research": 0}}


def test_usage_reads_the_account_and_tags_the_project(monkeypatch):
    import io

    from andy_companion import web

    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    seen = {}

    def opener(req, timeout=None):
        seen["method"], seen["project"] = req.get_method(), req.headers.get("X-project-id")
        return io.BytesIO(json.dumps({"account": {"current_plan": "Researcher", "plan_usage": 84, "plan_limit": 1000,
                                                  "search_usage": 79, "extract_usage": 5}}).encode())

    assert web.usage(opener)["used"] == 84
    assert seen == {"method": "GET", "project": None}           # the account's month, not one project's
    web.look_up("library hours", opener=lambda req, timeout=None: (seen.update(tag=req.headers.get("X-project-id"))
                                                                    or io.BytesIO(b'{"results": []}')))
    assert seen["tag"] == "andy-companion"                      # every search is tagged
