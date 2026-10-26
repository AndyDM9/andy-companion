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
    assert dayplan.say(NOW) == "Today is Tuesday, October 13. You have no reminders today."


def test_the_day_is_said_the_same_way_every_time():
    reminders.add("water the plants", at="17:00", now=NOW)
    reminders.add("call my daughter", at="14:30", now=NOW)
    first = dayplan.say(NOW)
    assert first == ("Today is Tuesday, October 13. You have 2 reminders today: at 2:30 pm, call my daughter; "
                     "at 5:00 pm, water the plants. The next one is at 2:30 pm.")   # times as people say them
    assert dayplan.say(NOW) == first


def test_tomorrows_reminders_are_not_today():
    reminders.add("dentist", at="07:00", now=NOW)   # 07:00 has passed: tomorrow
    assert "no reminders today" in dayplan.say(NOW)


def test_one_reminder_reads_naturally():
    reminders.add("call my daughter", at="14:30", now=NOW)
    assert "You have 1 reminder today: at 2:30 pm, call my daughter." in dayplan.say(NOW)


def test_settings_default_and_stick():
    assert settings.get() == {"pace": "normal", "volume": None, "last_morning": None, "place": None,
                            "news_sources": [], "events_pages": [], "captions": True, "language": "en",
                              "coords": None, "screen_photos": True, "screen_hints": True, "night_from": 21, "night_to": 7, "night_clock": "hours",
                              "screen_calm": False, "tv_yaw": None, "tv_height": "level", "tv_glance": True,
                              "offers": True, "last_offer": None, "events_suggestion": None,
                              "greet_arrival": True, "last_greeting": None, "person_name": None}
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
    assert "slowly" in extra and "Tuesday, October 13, 2026" in extra


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


def test_the_plan_is_on_the_screen_too(monkeypatch, tmp_path):
    monkeypatch.setattr(speaker.board, "SCREEN", tmp_path / "screen.json")
    from andy_companion import moments

    reminders.add("water the plants", at="17:00", now=NOW)
    reminders.add("call my daughter", at="14:30", now=NOW)
    moments.add("Sofia's piano recital", "today", today=NOW.date())
    title, items = dayplan.card(NOW)
    assert title == "Tuesday, October 13"
    assert items == [{"title": "2:30 pm · call my daughter"}, {"title": "5:00 pm · water the plants"},
                     {"title": "Also today", "summary": "Sofia's piano recital"}]
    h = FakeHandler()
    asyncio.run(speaker.tick(h, since=0, now_mono=100, now=NOW, present=True))
    shown = speaker.board.showing()
    assert shown["kind"] == "today" and shown["items"][0]["title"].endswith("call my daughter")


def test_a_full_day_fits_the_card_and_says_how_many_more():
    for at in ("09:00", "10:00", "11:00", "12:00", "13:00"):
        reminders.add(f"thing number {at}", at=at, now=NOW)
    _, items = dayplan.card(NOW)
    assert [i["title"] for i in items] == ["9:00 am · thing number 09:00", "10:00 am · thing number 10:00",
                                           "11:00 am · thing number 11:00", "And 2 more today"]
    _, items = dayplan.card(datetime(2026, 10, 13, 13, 30))
    assert items == [{"title": "No more reminders today."}]


def test_the_card_in_spanish():
    reminders.add("llamar a Rosa", at="14:30", now=NOW)
    title, items = dayplan.card(NOW, "es")
    assert title == "Martes 13 de octubre" and items == [{"title": "14:30 · llamar a Rosa"}]


def test_one_gentle_offer_in_the_afternoon_when_it_has_been_quiet(monkeypatch):
    from andy_companion import turns

    monkeypatch.setattr(turns.CLOCK, "quiet_for", lambda: 3 * 3600)
    afternoon = datetime(2026, 10, 13, 15, 0)
    h = FakeHandler()
    settings.update(last_morning=afternoon.date().isoformat())          # the morning plan is done
    assert asyncio.run(speaker.tick(h, since=0, now_mono=100, now=afternoon, present=True)) == 1
    assert h.said[0].startswith("[ANDY'S OWN IDEA") and "Of course" in h.said[0]
    assert asyncio.run(speaker.tick(h, since=0, now_mono=200, now=afternoon, present=True)) == 0   # once a day


def test_no_offer_when_off_too_soon_after_talking_nobody_here_or_not_afternoon(monkeypatch):
    from andy_companion import turns

    afternoon = datetime(2026, 10, 13, 15, 0)
    settings.update(last_morning=afternoon.date().isoformat())
    h = FakeHandler()
    monkeypatch.setattr(turns.CLOCK, "quiet_for", lambda: 600)           # they spoke ten minutes ago
    assert asyncio.run(speaker.offer(h, afternoon, present=True)) == 0
    monkeypatch.setattr(turns.CLOCK, "quiet_for", lambda: 3 * 3600)
    assert asyncio.run(speaker.offer(h, afternoon, present=False)) == 0
    assert asyncio.run(speaker.offer(h, datetime(2026, 10, 13, 19, 0), present=True)) == 0
    settings.update(offers=False)
    assert asyncio.run(speaker.offer(h, afternoon, present=True)) == 0 and h.said == []


def test_the_quiet_clock_restarts_when_the_person_speaks():
    from andy_companion import turns

    t = [100.0]
    clock = turns.TurnClock(clock=lambda: t[0])
    t[0] = 5000.0
    assert clock.quiet_for() == 4900.0
    clock.mark("user_speech_started")
    assert clock.quiet_for() == 0.0


def test_someone_coming_in_after_hours_away_is_welcomed_back_once(monkeypatch):
    from andy_companion.body import presence

    monkeypatch.setattr(presence, "_seen", {"t": None, "arrived": None})
    day = datetime(2026, 10, 14, 15, 0)
    t = day.timestamp()
    presence.mark("face", now=t - 3 * 3600)              # seen this morning, then nobody
    presence.mark("voice", now=t - 60)                   # a TV talking is not someone coming in
    assert not presence.arrived(now=t)
    presence.mark("face", now=t)
    assert presence.arrived(now=t)
    h = FakeHandler()
    assert asyncio.run(speaker.welcome_back(h, day, since=0.0, now_mono=3600.0)) == 1
    assert "Welcome them back" in h.said[0] and "Don't ask where" in h.said[0]
    assert asyncio.run(speaker.welcome_back(h, day, since=0.0, now_mono=3600.0)) == 0      # once per arrival


def test_no_welcome_at_night_too_soon_after_starting_or_when_off(monkeypatch):
    from andy_companion.body import presence

    def arrive(at):
        monkeypatch.setattr(presence, "_seen", {"t": at - 3 * 3600, "arrived": None})
        presence.mark("person", now=at)

    h = FakeHandler()
    night = datetime(2026, 10, 14, 22, 30)
    arrive(night.timestamp())
    assert asyncio.run(speaker.welcome_back(h, night, since=0.0, now_mono=3600.0)) == 0
    day = datetime(2026, 10, 14, 15, 0)
    arrive(day.timestamp())
    assert asyncio.run(speaker.welcome_back(h, day, since=0.0, now_mono=60.0)) == 0      # Andy just started
    settings.update(greet_arrival=False)
    arrive(day.timestamp())
    assert asyncio.run(speaker.welcome_back(h, day, since=0.0, now_mono=3600.0)) == 0 and h.said == []


def test_spoken_controls_in_spanish():
    from andy_companion import voice_controls
    parse = voice_controls.parse
    assert parse("Buenas noches, Andy") == ("go_to_sleep", {})
    assert parse("Andy, a dormir") == ("go_to_sleep", {})
    assert parse("Silencio, por favor") == ("quiet_for", {"minutes": 60})
    assert parse("Silencio por una hora") == ("quiet_for", {"minutes": 60})
    assert parse("Silencio durante veinte minutos") == ("quiet_for", {"minutes": 20})
    assert parse("Quédate en silencio por media hora") == ("quiet_for", {"minutes": 30})
    assert parse("¿Por qué dijiste buenas noches?") is None             # a question is never a control
    assert parse("No te quedes en silencio") is None
