"""2026-10-25 on the robot: each research answer, as it was passed on, started the same research again (seven
times in five minutes), and "stop searching" had nothing to stop. An answer just told is never looked into again
by itself, and the person can stop a research."""

from pathlib import Path

import pytest

from andy_companion import board, looking, speaker, web

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "tvly-test")
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    looking._state.update(busy=False, day="", count=0, question="", answered_at=0.0, answered="", heard_at=0.0, run=0)
    looking._stop.clear()


def test_the_loop_seen_on_the_robot_cannot_happen():
    t = {"now": 1000.0}
    clock = lambda: t["now"]
    looking.answered("library card renewal emails", clock=clock)
    t["now"] += 1                                         # the model, a second after the answer was passed on
    assert looking.start("library card renewal emails", runner=lambda *a: None, clock=clock) == looking.JUST_ANSWERED
    assert looking.start("something else entirely", runner=lambda *a: None, clock=clock) == looking.JUST_ANSWERED
    t["now"] += 60                                        # a minute later: the same question, reworded, still no
    assert looking.start("renewal emails for the library card", runner=lambda *a: None, clock=clock) == looking.JUST_ANSWERED
    started = looking.start("the new bus routes", runner=lambda *a: None, clock=clock)   # something new: yes
    assert started["started"] is True
    looking._state.update(busy=False)
    t["now"] += looking.SAME_FOR_S                        # ten minutes on, asked again: yes
    assert looking.start("library card renewal emails", runner=lambda *a: None, clock=clock)["started"] is True


def test_the_answer_is_handed_over_as_finished():
    frame = speaker.research_frame({"topic": "bus routes", "say": "Routes 8 and 24 changed.",
                                    "sources": [{"source": "miamidade.gov"}]})
    assert "It is complete: do not call look_into, look_up or any other search for it." in frame
    assert "Tell the person you looked into" not in frame


def test_stop_closes_the_stream_and_nothing_is_said(monkeypatch):
    calls = {"steps": 0, "collected": 0}

    def stream(question, place, language, on_step, opener):
        on_step("planning", "")
        calls["steps"] += 1
        looking.stop()                                    # "stop searching", said while it runs
        on_step("searching", "3")                         # the next step closes the stream
        calls["steps"] += 1
        return {"say": "never said"}

    monkeypatch.setattr(web, "stream_research", stream)
    monkeypatch.setattr(looking, "_collect", lambda *a: calls.__setitem__("collected", 1))
    looking._state.update(busy=True)
    assert looking.run("library card renewal") is None
    assert calls == {"steps": 1, "collected": 0}          # stopped at once, and never started again another way
    assert board.next_for_person() is None and looking._state["busy"] is False
    assert issubclass(web.ResearchStopped, web.WebError)  # so the real stream passes it straight through


def test_stop_drops_an_answer_waiting_to_be_said_and_its_card():
    board.research_ready("bus routes", "Routes changed.", [], [])
    looking.show_progress("bus routes", [("Searching the web", "")])
    assert looking.stop() == looking.STOPPED
    assert board.next_for_person() is None and board.showing() is None
    assert looking.stop() == looking.NOTHING_TO_STOP


def test_the_tools_can_stop_it():
    look_into = (ROOT / "tools" / "look_into.py").read_text()
    assert '"stop": {"type": "boolean"' in look_into and "return looking.stop()" in look_into
    assert "await asyncio.to_thread(looking.stop)" in (ROOT / "tools" / "quiet_for.py").read_text()


def test_a_new_question_from_the_person_right_after_an_answer_is_theirs():
    """2026-10-28 review: within 30 s of an answer, the person's own next question was refused as 'just answered'."""
    t = {"now": 1000.0}
    clock = lambda: t["now"]
    looking.answered("the farmers market", clock=clock)
    t["now"] += 5
    assert looking.start("the bus routes", runner=lambda *a: None, clock=clock) == looking.JUST_ANSWERED  # the model
    looking.heard(clock=clock)                            # the person speaks
    t["now"] += 3
    assert looking.start("the bus routes", runner=lambda *a: None, clock=clock)["started"] is True
    looking._state.update(busy=False)
    assert looking.start("is the farmers market on", runner=lambda *a: None, clock=clock) == looking.JUST_ANSWERED


def test_after_a_failed_look_the_offered_retry_is_not_refused():
    t = {"now": 1000.0}
    clock = lambda: t["now"]
    looking.answered("the farmers market", clock=clock, failed=True)
    assert "Offer to try again" in speaker.research_frame({"topic": "the farmers market", "failed": True})
    t["now"] += 4
    looking.heard(clock=clock)                            # "yes, try again"
    t["now"] += 2
    assert looking.start("the farmers market", runner=lambda *a: None, clock=clock)["started"] is True


def test_stop_frees_andy_at_once_and_a_stopped_look_never_speaks_or_frees_the_next():
    import threading
    entered, release = threading.Event(), threading.Event()
    delivered = []

    def slow_research(question, place, language, on_step, opener):
        entered.set()
        release.wait(3)
        on_step("searching", "1")                         # its next step, after the stop and a new start
        return {"say": "old answer", "points": [], "sources": []}

    import pytest as _pytest
    mp = _pytest.MonkeyPatch()
    try:
        mp.setattr(web, "stream_research", slow_research)
        mp.setattr(board, "research_ready", lambda topic, say, *a, **k: delivered.append(say))
        first = looking.start("the old question", runner=None)
        assert first["started"] and entered.wait(3)
        assert looking.stop() == looking.STOPPED
        assert looking._state["busy"] is False             # at once, not at the stream's next event
        looking.heard()
        mp.setattr(web, "stream_research", lambda *a, **k: (_ for _ in ()).throw(web.ResearchStopped("held")))
        second = looking.start("a new question", runner=lambda *a: None)
        assert second["started"] is True and looking._state["busy"] is True
        release.set()
        for _ in range(100):
            if not any(t.name == "andy-looking" and t.is_alive() for t in threading.enumerate()):
                break
            threading.Event().wait(0.02)
        assert delivered == [] and looking._state["busy"] is True      # the old look neither spoke nor freed the new
    finally:
        release.set()
        mp.undo()


def test_research_progress_is_in_the_households_language():
    shown = []
    import pytest as _pytest
    mp = _pytest.MonkeyPatch()
    try:
        mp.setattr(board, "show", lambda kind, title, items, **k: shown.append((title, items)))
        looking.show_progress("el mercado", [("Buscando en la web", "2 búsquedas")], 3.0, 2, "es")
        looking.show_progress("the market", [("Searching the web", "2 searches")], 3.0, 2)
    finally:
        mp.undo()
    assert shown[0][0] == "Investigando: el mercado" and shown[1][0] == "Looking into: the market"
