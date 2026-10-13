import json
from datetime import datetime

import pytest

from andy_companion import chimes, reminders, state, supervisor, wake

NOW = datetime(2026, 10, 13, 14, 0)


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "FILE", tmp_path / "state.json")
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")


def test_awake_by_default():
    assert state.current(NOW)["mode"] == "awake"


def test_quiet_for_a_while_then_awake_again():
    until = state.quiet_for(60, now=NOW)
    assert until == datetime(2026, 10, 13, 15, 0)
    assert state.current(NOW)["mode"] == "quiet"
    assert supervisor.wake_reason(datetime(2026, 10, 13, 14, 30)) is None
    assert supervisor.wake_reason(datetime(2026, 10, 13, 15, 0)) == "quiet over"


@pytest.mark.parametrize("minutes", [0, -5, 24 * 60 + 1])
def test_quiet_refuses_odd_lengths(minutes):
    with pytest.raises(ValueError):
        state.quiet_for(minutes, now=NOW)


def test_asleep_until_woken():
    state.asleep()
    assert state.current(NOW)["mode"] == "asleep"
    assert supervisor.wake_reason(datetime(2026, 10, 14, 9, 0)) is None


def test_a_due_reminder_wakes_andy_from_sleep_or_quiet():
    state.asleep()
    reminders.add("call my daughter", at="14:30", now=NOW)
    assert supervisor.wake_reason(datetime(2026, 10, 13, 14, 29)) is None
    assert supervisor.wake_reason(datetime(2026, 10, 13, 14, 30)) == "reminder due"


def test_state_file_is_owner_only():
    import os
    import stat

    state.asleep()
    assert stat.S_IMODE(os.stat(state.FILE).st_mode) == 0o600


@pytest.mark.parametrize("mode, code, expected", [
    ("awake", 0, "sleep"),        # the app stopped itself: go_to_sleep
    ("quiet", 0, "wait"),         # quiet_for already set the mode
    ("awake", 1, "restart"),      # a crash: start again
    ("awake", -9, "restart"),
])
def test_after_the_app_exits(mode, code, expected):
    assert supervisor.after_exit(mode, code) == expected


def test_wake_phrases_only():
    assert wake.is_trigger("andy wake up")
    assert wake.is_trigger("  Andy   WAKE up ")
    assert not wake.is_trigger("andy")
    assert not wake.is_trigger("wake up")


class FakeRecognizer:
    def __init__(self, texts):
        self.texts = list(texts)

    def AcceptWaveform(self, data):
        return bool(self.texts)

    def Result(self):
        return json.dumps({"text": self.texts.pop(0)})


def test_listener_returns_on_the_phrase():
    rec = FakeRecognizer(["hello", "andy wake up"])
    assert wake.heard(iter([b"x"] * 10), rec, should_stop=lambda: False) == "phrase"


def test_listener_stops_when_told_to():
    rec = FakeRecognizer([])
    assert wake.heard(iter([b"x"] * 100), rec, should_stop=lambda: True, check_every=1) is None


def test_chimes_are_short_clean_wavs():
    for name in chimes.TUNES:
        data = chimes.wav_bytes(name)
        assert data[:4] == b"RIFF" and 2_000 < len(data) < 40_000


def test_no_chime_unless_awake():
    state.asleep()
    assert chimes.play("reminder", opener=lambda *a, **k: (_ for _ in ()).throw(AssertionError("played"))) is False
