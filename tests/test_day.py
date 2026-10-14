import asyncio
from datetime import datetime

import pytest

from andy_companion import dayplan, reminders, settings, speaker, voice_controls

NOW = datetime(2026, 10, 13, 8, 0)


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    from andy_companion import moments

    monkeypatch.setattr(moments, "FILE", tmp_path / "moments.json")
    monkeypatch.setattr(speaker.board, "INBOX", tmp_path / "inbox.json")
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
    assert settings.get() == {"pace": "normal", "volume": None, "last_morning": None, "place": None,
                            "news_sources": [], "events_pages": [], "captions": True, "language": "en",
                              "coords": None, "screen_photos": True, "night_from": 21, "night_to": 7}
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


def test_the_plan_in_spanish_uses_fixed_spanish_words():
    reminders.add("llamar a Rosa", at="17:00", now=NOW)
    plan = dayplan.say(datetime(2026, 10, 13, 9, 0), language="es")
    assert plan == "Hoy es martes 13 de octubre. Tiene 1 recordatorio hoy: a las 17:00, llamar a Rosa."


def test_language_setting_is_checked():
    with pytest.raises(ValueError):
        settings.update(language="fr")
    settings.update(language="es")
    assert "Hoy es" in dayplan.say(datetime(2026, 10, 13, 9, 0))


def test_the_screen_words_follow_the_language():
    from andy_companion import clock
    shown = clock.today(datetime(2026, 10, 13, 15, 0), "es")["shown"]
    assert shown["weekday"] == "martes" and shown["today"] == "Hoy" and shown["part_of_day"] == "tarde"


def test_andy_wakes_with_fixed_words_for_the_time_and_language():
    """Left to the model, the greeting mixed languages and said 'Buenos días' in the evening."""
    from datetime import datetime as dt

    from andy_companion import words

    assert words.greeting(dt(2026, 10, 13, 9), "en") == "Good morning! I'm Andy, your robot companion, here to help with your day."
    assert words.greeting(dt(2026, 10, 13, 18), "en").startswith("Good evening!")
    assert words.greeting(dt(2026, 10, 13, 15), "es") == "¡Buenas tardes! Soy Andy, su compañero robot, para ayudarle con su día."
    assert words.greeting(dt(2026, 10, 13, 21), "es").startswith("¡Buenas noches!")
    assert "robot" in words.INTRO["en"] and "robot" in words.INTRO["es"]       # honest from the first sentence
    assert "When you wake, say exactly: Good morning! I'm Andy" in settings.instructions(NOW)
    settings.update(language="es")
    assert "say exactly: ¡Buenos días! Soy Andy" in settings.instructions(NOW)


@pytest.mark.parametrize("en, es", [
    ("Mostly Clear", "Mayormente despejado"),
    ("Sunny then Slight Chance Showers And Thunderstorms", "Soleado, con leve posibilidad de chubascos y tormentas"),
    ("Chance Rain Showers", "Posibilidad de chubascos"),
    ("Thunderstorms Likely", "Probables tormentas"),
    ("Partly Cloudy", "Parcialmente nublado"),
    ("Blowing Dust", "Ver el pronóstico"),
])
def test_the_weather_in_spanish_is_built_from_its_parts(en, es):
    from andy_companion import words

    assert words.sky(en, "es") == es
    assert words.sky(en, "en") == en


def test_weather_periods_in_spanish():
    from andy_companion import words

    assert words.weather_period("Tonight", "es") == "Esta noche"
    assert words.weather_period("Wednesday", "es") == "Miércoles"
    assert words.weather_period("Wednesday Night", "es") == "Miércoles por la noche"
    assert words.weather_period("Columbus Day", "es") == "Columbus Day"


@pytest.mark.parametrize("period, lang, line", [
    ({"name": "Today", "short": "Sunny", "temperature": "86°", "rain": 10}, "en", "The weather today: sunny, 86°."),
    ({"name": "This Afternoon", "short": "Chance Showers And Thunderstorms", "temperature": "88°", "rain": 40}, "en",
     "The weather this afternoon: chance showers and thunderstorms, 88°, with a 40% chance of rain."),
    ({"name": "Today", "short": "Mostly Sunny", "temperature": "86°", "rain": 50}, "es",
     "El tiempo hoy: mayormente soleado, 86°, con un 50 % de probabilidad de lluvia."),
    (None, "en", ""),
])
def test_the_morning_plan_has_the_weather_in_fixed_words(period, lang, line):
    from andy_companion import dayplan

    assert dayplan.weather_line(period, lang) == line
