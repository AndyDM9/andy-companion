import io
import json
from datetime import date

import pytest

from andy_companion import board, onthisday

FEED = {"selected": [
    {"year": 1969, "text": "Apollo 11 landed on the Moon, the first crewed landing."},
    {"year": 1977, "text": "Hijacking of Lufthansa Flight 181."},
    {"year": 1957, "text": "A flood in Valencia caused at least 81 deaths."},
    {"year": 1926, "text": "The first book featuring Winnie-the-Pooh was published."},
], "events": [
    {"year": 1850, "text": "The first railway opened."},                         # before the people Andy talks with
    {"year": 1990, "text": "The first web browser was introduced."},
    {"year": 1964, "text": "Members of the Politburo voted to remove the First Secretary."},
]}


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(board, "SCREEN", tmp_path / "screen.json")
    onthisday._cache.clear()
    onthisday._failed["at"] = -1e9


def opener(seen=None):
    def open_(req, timeout):
        if seen is not None:
            seen.append(req)
        return io.BytesIO(json.dumps(FEED).encode())
    return open_


def test_code_keeps_only_gentle_things_from_living_memory():
    kept = [e["text"] for e in onthisday.gentle(FEED["selected"] + FEED["events"])]
    assert kept == ["Apollo 11 landed on the Moon, the first crewed landing.",
                    "The first book featuring Winnie-the-Pooh was published.", "The first web browser was introduced."]
    # Deaths, a hijacking, politics and anything before 1900 are out; a word list can still leak, which is
    # why the model's check follows.


def test_the_model_s_check_is_the_second_net_and_nothing_is_offered_without_it():
    seen = []
    result = onthisday.today(date(2026, 10, 14), opener=opener(seen),
                             vetter=lambda events: [e for e in events if "Hijacking" not in e["text"]])
    texts = [e["text"] for e in result["events"]]
    assert "Hijacking of Lufthansa Flight 181." not in texts and texts
    assert result["source"] == "Wikipedia" and result["licence"] == "CC BY-SA 4.0" and "Do you remember" in result["how"]
    assert "usted" in onthisday.HOW["es"] and "Según Wikipedia" in onthisday.HOW["es"]
    assert seen[0].get_header("User-agent").startswith("AndyCompanion/") and "/10/14" in seen[0].full_url
    onthisday._cache.clear()

    def broken(events):
        raise onthisday.VetError("no answer")

    with pytest.raises(onthisday.VetError):
        onthisday.today(date(2026, 10, 14), opener=opener(), vetter=broken)
    assert onthisday._cache == {}                            # nothing unchecked is kept for later
    calls = []
    with pytest.raises(onthisday.VetError):                  # and no second wait for ten minutes
        onthisday.today(date(2026, 10, 14), opener=opener(calls), vetter=lambda e: e)
    assert calls == []


def test_the_check_asks_for_a_strict_schema_with_reasoning_off(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", "k")
    sent = {}

    def model(req, timeout):
        sent["body"] = json.loads(req.data)
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps({"keep": [0, 7, -1]})}}]}).encode())

    kept = onthisday.vet([{"year": 1969, "text": "Moon"}, {"year": 1977, "text": "Hijack"}], opener=model)
    assert kept == [{"year": 1969, "text": "Moon"}]           # only numbers that exist
    assert sent["body"]["response_format"]["json_schema"]["strict"] and sent["body"]["chat_template_kwargs"] == {"enable_thinking": False}
    assert "violence" in sent["body"]["messages"][0]["content"]


def test_the_screen_credits_wikipedia_and_its_licence():
    result = onthisday.today(date(2026, 10, 14), opener=opener(), vetter=lambda e: e)
    onthisday.show(result, day=date(2026, 10, 14))
    shown = board.showing()
    assert shown["kind"] == "on_this_day" and shown["title"] == "October 14"
    assert shown["items"][-1] == {"title": "Sources", "summary": "Wikipedia (CC BY-SA 4.0)"}
    onthisday.show(result, day=date(2026, 10, 14), language="es")
    assert board.showing()["title"] == "14 de octubre"
