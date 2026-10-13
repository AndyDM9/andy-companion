import asyncio
from datetime import datetime

import pytest

from andy_companion import dayplan, reminders, settings, speaker, voice_controls

NOW = datetime(2026, 10, 13, 8, 0)


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(speaker.chimes, "play", lambda name: None)


def test_the_day_with_nothing_planned():
    assert dayplan.say(NOW) == "Today is Tuesday 13 October. You have no reminders today."


def test_the_day_is_said_the_same_way_every_time():
    reminders.add("water the plants", at="17:00", now=NOW)
    reminders.add("call my daughter", at="14:30", now=NOW)
    first = dayplan.say(NOW)
    assert first == ("Today is Tuesday 13 October. You have 2 reminders today: at 14:30, call my daughter; "
                     "at 17:00, water the plants. The next one is at 14:30.")
    assert dayplan.say(NOW) == first


def test_tomorrows_reminders_are_not_today():
    reminders.add("dentist", at="07:00", now=NOW)   # 07:00 has passed: tomorrow
    assert "no reminders today" in dayplan.say(NOW)


def test_one_reminder_reads_naturally():
    reminders.add("call my daughter", at="14:30", now=NOW)
    assert "You have 1 reminder today: at 14:30, call my daughter." in dayplan.say(NOW)


def test_settings_default_and_stick():
    assert settings.get() == {"pace": "normal", "volume": None, "last_morning": None}
    settings.update(pace="slow", volume=70)
    assert settings.get()["pace"] == "slow" and settings.get()["volume"] == 70


def test_settings_refuse_odd_values():
    with pytest.raises(ValueError):
        settings.update(pace="very fast")
    with pytest.raises(ValueError):
        settings.update(volume=140)


def test_instructions_carry_the_pace():
    settings.update(pace="slow")
    extra = settings.instructions(NOW)
    assert "slowly" in extra and "Tuesday 13 October 2026" in extra


def test_volume_steps():
    assert settings.next_volume(80, "louder") == 95
    assert settings.next_volume(95, "louder") == 100
    assert settings.next_volume(20, "quieter") == 10
    assert settings.next_volume(10, "quieter") == 10
    assert settings.next_volume(50, 70) == 70


class FakeHandler:
    def __init__(self):
        self.said = []
        self._in_flight_tool_calls = set()
        self._response_done_event = asyncio.Event()
        self._response_done_event.set()

    def _is_connected(self):
        return True

    async def say(self, prompt):
        self.said.append(prompt)


def test_morning_plan_once_a_day_when_someone_is_here():
    reminders.add("call my daughter", at="14:30", now=NOW)
    h = FakeHandler()
    assert asyncio.run(speaker.tick(h, since=0, now_mono=100, now=NOW, present=True)) == 1
    assert "call my daughter" in h.said[0] and h.said[0].startswith("[MORNING")
    assert asyncio.run(speaker.tick(h, since=0, now_mono=200, now=NOW, present=True)) == 0


def test_no_morning_plan_before_six_or_with_nobody_around():
    h = FakeHandler()
    assert asyncio.run(speaker.tick(h, since=0, now_mono=100, now=datetime(2026, 10, 13, 5, 30), present=True)) == 0
    assert asyncio.run(speaker.tick(h, since=0, now_mono=100, now=NOW, present=False)) == 0
    assert asyncio.run(speaker.tick(h, since=0, now_mono=100, now=datetime(2026, 10, 13, 12, 30), present=True)) == 0


@pytest.mark.parametrize("text, command", [
    ("Goodnight.", ("go_to_sleep", {})),
    ("Andy, good night", ("go_to_sleep", {})),
    ("be quiet for 20 minutes", ("quiet_for", {"minutes": 20})),
    ("Andy, please be quiet for an hour", ("quiet_for", {"minutes": 60})),
    ("stay quiet for two hours", ("quiet_for", {"minutes": 120})),
    ("be quiet", ("quiet_for", {"minutes": 60})),
    ("Should I say goodnight?", None),
    ("I don't want you to be quiet", None),
    ("tell my grandson goodnight from me", None),
])
def test_exact_spoken_controls(text, command):
    assert voice_controls.parse(text) == command
