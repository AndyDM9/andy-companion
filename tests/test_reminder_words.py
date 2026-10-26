"""A reminder's words keep only what to do; when is kept as its time (2026-10-25: "take a pill at eight o'clock in
the morning" on the TV beside "Tomorrow, 8:00 am")."""

import pytest

from andy_companion import reminders
from andy_companion.reminders import just_what


@pytest.mark.parametrize("said, kept", [
    ("take a pill at eight o'clock in the morning", "take a pill"),
    ("remind me to call my sister at four", "call my sister"),
    ("take my medicine at 8:00 am daily", "take my medicine"),
    ("water the plants every morning", "water the plants"),
    ("call the doctor tomorrow at 9am", "call the doctor"),
    ("feed the cat in 20 minutes", "feed the cat"),
    ("tomar la pastilla a las ocho de la mañana", "tomar la pastilla"),
    ("recuérdame que llame a mi hermana a las cuatro", "llame a mi hermana"),
    ("Call Rosa", "Call Rosa"),
    ("meeting at the bank", "meeting at the bank"),
    ("buy bread for tomorrow", "buy bread for tomorrow"),
    ("pack the bag before tonight", "pack the bag before tonight"),
    ("today", "today"),
])
def test_only_what_to_do_is_kept(said, kept):
    assert just_what(said) == kept


def test_a_reminder_set_with_the_time_in_its_words_shows_only_the_task(tmp_path, monkeypatch):
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")
    item = reminders.add("take a pill at eight o'clock in the morning", at="08:00", repeat="daily")
    assert item["text"] == "take a pill" and reminders.pending()[0]["text"] == "take a pill"
    # Kept in their words (said inside sentences: "at eight, take a pill"); lists show it in sentence case.
