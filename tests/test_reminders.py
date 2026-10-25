import os
import stat
from datetime import datetime

import pytest

from andy_companion import reminders

NOW = datetime(2026, 10, 13, 12, 50)


@pytest.fixture
def store(tmp_path, monkeypatch):
    path = tmp_path / "reminders.json"
    monkeypatch.setattr(reminders, "STORE", path)
    return path


def test_due_time_at_a_clock_time_later_today():
    assert reminders.due_time(at="17:30", now=NOW) == datetime(2026, 10, 13, 17, 30)


def test_due_time_at_a_clock_time_already_passed_is_tomorrow():
    assert reminders.due_time(at="09:00", now=NOW) == datetime(2026, 10, 14, 9, 0)


def test_due_time_in_minutes():
    assert reminders.due_time(minutes=20, now=NOW) == datetime(2026, 10, 13, 13, 10)


@pytest.mark.parametrize("bad", [{"minutes": 0}, {"minutes": 99999}, {"at": "25:00"}, {"at": "noon"}, {}])
def test_due_time_refuses_what_it_cannot_understand(bad):
    with pytest.raises(ValueError):
        reminders.due_time(now=NOW, **bad)


def test_add_list_and_cancel(store):
    item = reminders.add("call my daughter", at="17:30", now=NOW)
    assert [r["id"] for r in reminders.pending()] == [item["id"]]
    assert reminders.cancel(item["id"]) is True
    assert reminders.pending() == []
    assert reminders.cancel(item["id"]) is False


def test_store_is_readable_only_by_its_owner(store):
    reminders.add("water the plants", minutes=5, now=NOW)
    assert stat.S_IMODE(os.stat(store).st_mode) == 0o600


def test_text_is_tidied_and_capped(store):
    item = reminders.add("  call   my\n daughter  " + "x" * 500, minutes=5, now=NOW)
    assert item["text"].startswith("call my daughter ")
    assert len(item["text"]) <= reminders.MAX_TEXT


def test_empty_text_is_refused(store):
    with pytest.raises(ValueError):
        reminders.add("   ", minutes=5, now=NOW)


def test_one_off_reminder_is_deleted_once_said(store):
    item = reminders.add("stand up", minutes=1, now=NOW)
    due = reminders.due(now=datetime(2026, 10, 13, 12, 52))
    assert [r["id"] for r in due] == [item["id"]]
    reminders.said(item["id"], now=datetime(2026, 10, 13, 12, 52))
    assert reminders.pending() == []


def test_daily_reminder_moves_to_the_next_day_once_said(store):
    item = reminders.add("take my vitamins", at="13:00", repeat="daily", now=NOW)
    reminders.said(item["id"], now=datetime(2026, 10, 13, 13, 0, 30))
    (left,) = reminders.pending()
    assert datetime.fromtimestamp(left["due"]) == datetime(2026, 10, 14, 13, 0)


def test_not_due_before_its_time(store):
    reminders.add("call my daughter", at="17:30", now=NOW)
    assert reminders.due(now=datetime(2026, 10, 13, 17, 29)) == []


def test_unknown_repeat_is_refused(store):
    with pytest.raises(ValueError):
        reminders.add("x", at="10:00", repeat="hourly", now=NOW)


def test_spoken_time():
    assert reminders.spoken_time(datetime(2026, 10, 13, 17, 30).timestamp(), now=NOW) == "17:30 today"
    assert reminders.spoken_time(datetime(2026, 10, 14, 9, 0).timestamp(), now=NOW) == "09:00 tomorrow"
    assert reminders.spoken_time(datetime(2026, 10, 16, 9, 0).timestamp(), now=NOW) == "09:00 on Friday"


def test_an_unreadable_reminders_file_is_set_aside_never_overwritten(tmp_path, monkeypatch):
    store = tmp_path / "reminders.json"
    monkeypatch.setattr(reminders, "STORE", store)
    store.write_bytes(b'[{"text": "call Rosa", "due": 17')          # cut off part-way
    assert reminders._load() == []
    aside = list(tmp_path.glob("reminders.unreadable-*.json"))
    assert len(aside) == 1 and aside[0].read_bytes().startswith(b'[{"text": "call Rosa"') and not store.exists()
