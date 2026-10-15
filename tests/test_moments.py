import os
import stat
from datetime import date, datetime

import pytest

from andy_companion import dayplan, moments, reminders, speaker

TUE = date(2026, 10, 13)


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(moments, "FILE", tmp_path / "moments.json")
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")
    monkeypatch.setattr(speaker.settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(speaker.board, "INBOX", tmp_path / "inbox.json")


@pytest.mark.parametrize("said, expected", [
    ("today", TUE), ("tomorrow", date(2026, 10, 14)), ("Thursday", date(2026, 10, 15)),
    ("on Tuesday", date(2026, 10, 20)), ("next friday", date(2026, 10, 16)), ("2026-11-02", date(2026, 11, 2)),
])
def test_days_as_people_say_them(said, expected):
    assert moments.parse_day(said, TUE) == expected


def test_unclear_days_are_refused():
    with pytest.raises(ValueError):
        moments.parse_day("sometime soon", TUE)


def test_a_moment_is_kept_privately_and_forgotten_on_request():
    m = moments.add("Sofia's piano recital", "Thursday", TUE)
    assert stat.S_IMODE(os.stat(moments.FILE).st_mode) == 0o600
    assert moments.upcoming(TUE)[0]["what"] == "Sofia's piano recital"
    assert moments.forget("recital") == 1 and moments.upcoming(TUE) == []
    assert m["on"] == "2026-10-15"


def test_moments_go_a_week_after_their_day():
    moments.add("dentist", "2026-10-01", date(2026, 9, 30))
    moments.add("lunch with Rosa", "2026-10-10", date(2026, 9, 30))
    assert moments.tidy(TUE) == 1
    assert [m["what"] for m in moments._load()] == ["lunch with Rosa"]


def test_the_day_plan_includes_todays_moments():
    moments.add("Anna visits", "today", TUE)
    plan = dayplan.say(datetime(2026, 10, 13, 9, 0))
    assert "Today is also: Anna visits." in plan


def test_the_morning_after_andy_asks_how_it_went():
    moments.add("Sofia's piano recital", "2026-10-12", TUE)

    class H:
        def __init__(self):
            import asyncio
            self.said = []
            self._in_flight_tool_calls = set()
            self._response_done_event = asyncio.Event()
            self._response_done_event.set()

        def _is_connected(self):
            return True

        async def say(self, text):
            self.said.append(text)

    import asyncio
    h = H()
    asyncio.run(speaker.tick(h, since=0, now_mono=100, now=datetime(2026, 10, 13, 8, 30), present=True))
    assert "Yesterday was: Sofia's piano recital" in h.said[0] and "ask how it went" in h.said[0]


def test_spoken_days():
    assert moments.spoken_day("2026-10-13", TUE) == "today"
    assert moments.spoken_day("2026-10-12", TUE) == "yesterday"
    assert moments.spoken_day("2026-10-16", TUE) == "Friday, October 16"


def test_andy_starts_every_conversation_knowing_what_it_remembers():
    """It sometimes said 'nothing' without looking (suite, 2026-10-13); now the list is in its instructions."""
    from andy_companion import recall, settings

    assert "No moments yet." in settings.instructions()
    moments.add("Sofia's piano recital", "Thursday")
    extra = settings.instructions()
    assert "## WHAT YOU REMEMBER" in extra and "- Sofia's piano recital, " in extra
    assert recall.block([("the plumber", "on Monday")]).endswith("- the plumber, on Monday")


def test_forgetting_needs_words_that_point_to_one_moment():
    """Found by the audit on 2026-10-14: forget("") forgot every moment, and forget("the") every one with "the"."""
    moments.add("Sofia's piano recital", "Thursday", TUE)
    moments.add("the plumber comes", "Friday", TUE)
    moments.add("the dentist", "Friday", TUE)
    for words in ("", "  ", "the", "a", "re", "the moment"):
        assert moments.forget(words) == 0
    assert moments.forget("cital") == 0                          # part of a word is not a word
    assert len(moments._load()) == 3
    assert moments.forget("Sofia") == 1                          # a whole word, even before "'s"
    assert [m["what"] for m in moments._load()] == ["the plumber comes", "the dentist"]


def test_when_several_moments_match_none_is_forgotten_and_andy_can_ask_which():
    a = moments.add("lunch with Rosa", "Thursday", TUE)
    b = moments.add("Rosa's birthday", "Friday", TUE)
    out = moments.forget_one("Rosa", TUE)
    assert out["forgotten"] == 0 and [w["id"] for w in out["which"]] == [a["id"], b["id"]]
    assert out["which"][0] == {"id": a["id"], "what": "lunch with Rosa", "day": "Thursday, October 15"}
    assert moments.forget("Rosa") == 0 and len(moments._load()) == 2
    assert moments.forget_one(b["id"]) == {"forgotten": 1, "what": "Rosa's birthday"}       # then by its id
    assert moments.forget_one("birthday")["forgotten"] == 0 and "say" in moments.forget_one("")
    assert moments.remove(a["id"]) and not moments.remove(a["id"])


def test_a_day_said_in_spanish_is_understood():
    from datetime import date
    wed = date(2026, 10, 14)
    assert moments.parse_day("hoy", wed) == wed and moments.parse_day("mañana", wed) == date(2026, 10, 15)
    assert moments.parse_day("el lunes", wed) == date(2026, 10, 19)
    assert moments.parse_day("el próximo miércoles", wed) == date(2026, 10, 21)
    assert moments.parse_day("on Friday", wed) == date(2026, 10, 16)
