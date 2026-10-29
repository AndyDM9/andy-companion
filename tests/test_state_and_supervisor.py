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


def _open(fd):
    import os
    try:
        os.fstat(fd)
        return True
    except OSError:
        return False


def test_a_stalled_sound_server_never_stops_the_wake_checks(monkeypatch):
    """parec gives nothing (a stalled sound server): the listener still asks, about once a second, whether a reminder
    has come due, and stops parec when it has. A plain read waited forever (2026-10-28 review)."""
    import os
    import resource
    import threading

    low_read, write_end = os.pipe()            # nothing is ever written: the pipe stays open and silent
    # The read end at a high, unused number: another test's file object, collected late, closes its own old number,
    # and once that number was this pipe's; the read then failed with "Bad file descriptor" (2026-10-28, 1 run in ~30).
    top = min(resource.getrlimit(resource.RLIMIT_NOFILE)[0], 1024) - 1  # select() takes numbers below 1024 only
    read_end = next(fd for fd in range(top, top - 200, -1) if not _open(fd))
    os.dup2(low_read, read_end)
    os.close(low_read)
    stopped, files = [], []

    class Parec:
        def __init__(self, *args, **kwargs):
            self.stdout = os.fdopen(read_end, "rb", buffering=0)
            files.append(self.stdout)

        def terminate(self):
            stopped.append(True)

        def wait(self, timeout=None):
            return 0

    monkeypatch.setattr(wake.subprocess, "Popen", Parec)
    asked, out = [], []
    rec = FakeRecognizer([])

    def reminder_due():
        asked.append(True)
        return len(asked) >= 2

    listener = threading.Thread(target=lambda: out.append(wake.heard(wake.mic_chunks("robot"), rec, reminder_due)),
                                daemon=True)
    listener.start()
    listener.join(timeout=6)
    try:
        assert not listener.is_alive() and out == [None]                 # it asked, and stopped listening
        assert len(asked) == 2 and stopped == [True]                     # parec is stopped too
    finally:
        os.close(write_end)                                              # lets a stuck read end, if there is one
        for f in files:                                                  # closed here, never later by number
            f.close()


def test_audio_comes_in_whole_chunks_however_the_pipe_splits_it():
    import os

    read_end, write_end = os.pipe()
    os.write(write_end, b"a" * (wake.CHUNK - 10))
    pipe = os.fdopen(read_end, "rb", buffering=0)
    chunks = wake.chunks_of(pipe, wait_s=0.05)
    assert next(chunks) == b""                                           # not a whole chunk yet: a moment to check
    os.write(write_end, b"b" * 10)
    assert next(chunks) == b"a" * (wake.CHUNK - 10) + b"b" * 10
    os.close(write_end)
    assert list(chunks) == []                                            # parec ended
    pipe.close()


def test_chimes_are_short_clean_wavs():
    for name in chimes.TUNES:
        data = chimes.wav_bytes(name)
        assert data[:4] == b"RIFF" and 2_000 < len(data) < 40_000


def test_no_chime_unless_awake():
    state.asleep()
    assert chimes.play("reminder", opener=lambda *a, **k: (_ for _ in ()).throw(AssertionError("played"))) is False


def test_only_an_explicit_wake_up_ends_a_quiet_spell():
    """'Good morning, Andy' said to another Andy woke the robot early from quiet (2026-10-13)."""
    assert wake.triggers_for("quiet") == wake.WAKE_UP
    assert not wake.is_trigger("good morning andy", wake.triggers_for("quiet"))
    assert not wake.is_trigger("i'm back andy", wake.triggers_for("quiet"))
    assert wake.is_trigger("andy wake up", wake.triggers_for("quiet"))
    assert wake.is_trigger("good morning andy", wake.triggers_for("asleep"))


def test_a_greeting_heard_while_quiet_does_not_wake():
    class Rec:
        def AcceptWaveform(self, data):
            return True

        def Result(self):
            return json.dumps({"text": "good morning andy"})

    assert wake.heard(iter([b"x"] * 20), Rec(), should_stop=lambda: False, triggers=wake.triggers_for("quiet")) is None


def test_face_following_is_on_from_the_start_in_code():
    """The greeting no longer asks the model for head_tracking: that left Andy waking in silence."""
    import re
    from pathlib import Path

    profile = (Path(__file__).resolve().parents[1] / "profiles/companion/profile.md").read_text()
    greeting = re.search(r'^greeting = "(.*)"$', profile, re.M).group(1)
    assert "head_tracking" not in greeting and "Call no tool" in greeting


def test_andy_wakes_in_spanish_with_the_same_rules():
    assert wake.is_trigger("andy despierta", wake.triggers_for("quiet", "es"))
    assert not wake.is_trigger("buenos días andy", wake.triggers_for("quiet", "es"))   # a greeting doesn't end quiet
    assert wake.is_trigger("buenos días andy", wake.triggers_for("asleep", "es"))

    class Rec:
        def __init__(self, text):
            self.text = text

        def AcceptWaveform(self, data):
            return True

        def Result(self):
            return json.dumps({"text": self.text})

    got = wake.heard(iter([b"x"]), Rec("[unk]"), should_stop=lambda: False,
                     also=[(Rec("andy despierta"), wake.triggers_for("asleep", "es"))])
    assert got == "phrase"


def test_the_spanish_phrases_reach_vosk_with_their_accents():
    # json.dumps escapes "días" as "d\\u00edas", which Vosk took as an unknown word (found 2026-10-14).
    from pathlib import Path
    src = (Path(__file__).resolve().parents[1] / "src/andy_companion/supervisor.py").read_text()
    assert "json.dumps(wake.GRAMMAR_ES, ensure_ascii=False)" in src
