"""Invented saved modes, stubbed processes and wake inputs; no robot, audio, provider or household data."""
import json
import logging
import stat
import sys
import threading
from datetime import datetime
from types import SimpleNamespace

import pytest

from andy_companion import app_mode, chimes, health, reminders, screen_server, state, supervisor, wake, watchdog

NOW = datetime(2026, 10, 27, 12)
STAMP = NOW.timestamp()
BAD = [None, [], False, 1, "invented private value", {}, {"mode": []}, {"mode": "invented private value"},
       {"mode": "quiet", "until": "invented private value"}, {"mode": "quiet", "until": None},
       {"mode": "quiet", "until": True}, {"mode": "quiet", "until": float("inf")},
       {"mode": "quiet", "until": float("nan")}, {"mode": "quiet", "until": 0},
       {"mode": "awake", "until": STAMP}, {"mode": "asleep", "since": True},
       {"mode": "asleep", "since": 1e300}, {"mode": "awake", "extra": "invented private value"},
       {"mode": "awake", "return_to": []}, {"mode": "awake", "return_to": {"mode": "awake"}},
       {"mode": "asleep", "return_to": {"mode": "asleep"}},
       {"mode": "awake", "return_to": {"mode": "quiet", "until": "invented private value"}},
       {"mode": "awake", "return_to": {"mode": "asleep", "reminders": [None]}},
       {"mode": "awake", "return_to": {"mode": "asleep", "reminders": "invented private value"}},
       {"mode": "awake", "return_to": {"mode": "asleep", "return_to": {}}}]


@pytest.fixture(autouse=True)
def isolated(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "FILE", tmp_path / "state.json")
    monkeypatch.setattr(state, "_last_warning", None)
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")


@pytest.mark.parametrize("data", BAD)
def test_invalid_saved_modes_are_preserved_and_do_not_wake_for_due_reminders(data, caplog):
    original = json.dumps(data).encode()
    state.FILE.write_bytes(original)
    reminders.add("Invented task", minutes=1, now=NOW)
    with caplog.at_level(logging.WARNING):
        assert state.current() == {"mode": "asleep", "until": None, "unreadable": True}
        assert supervisor.wake_reason(datetime(2026, 10, 27, 12, 2)) is None
        assert supervisor.reminders_to_wake(datetime(2026, 10, 27, 12, 2)) == []
    assert state.FILE.read_bytes() == original
    assert "invented private value" not in caplog.text
    assert len([r for r in caplog.records if r.name == "andy.state"]) == 1
    assert supervisor.BackAfterReminder()() is True


@pytest.mark.parametrize("payload", [b"{broken", b"\xff", b""])
def test_invalid_json_encoding_and_empty_mode_file_pause_without_discard(payload):
    state.FILE.write_bytes(payload)
    assert state.current()["unreadable"] is True and state.FILE.read_bytes() == payload


def test_missing_file_and_legacy_modes_remain_usable():
    assert state.current() == {"mode": "awake", "until": None}
    for mode in ("awake", "asleep"):
        state.FILE.write_text(json.dumps({"mode": mode}))
        assert state.current() == {"mode": mode, "until": None}
    state.FILE.write_text(json.dumps({"mode": "quiet", "until": STAMP}))
    assert supervisor.wake_reason(NOW) == "quiet over"


@pytest.mark.parametrize("reason", ["quiet over", "reminder due", "awake"])
def test_an_automatic_reason_cannot_replace_mode_that_became_invalid(reason):
    state.FILE.write_text('["invented private value"]')
    before = state.FILE.read_bytes()
    supervisor.wake_up(reason, NOW)
    assert state.FILE.read_bytes() == before and state.current()["unreadable"]


def test_explicit_wake_or_mode_change_restores_valid_state():
    state.FILE.write_text('[]')
    supervisor.wake_up("wake phrase", NOW)
    assert state.current() == {"mode": "awake", "until": None}
    assert stat.S_IMODE(state.FILE.stat().st_mode) == 0o600
    state.FILE.write_text('[]')
    state.quiet_for("5", NOW)
    assert state.current()["mode"] == "quiet" and "unreadable" not in state.current()
    state.FILE.write_text('[]')
    state.asleep(NOW)
    assert state.current() == {"mode": "asleep", "until": None, "since": STAMP}


@pytest.mark.parametrize("minutes", [True, False, None, {}, [], float("inf"), float("nan"), 10**1000,
                                     "invented private value", 0, -1, 1441])
def test_bad_quiet_duration_never_changes_existing_state(minutes):
    state.asleep(NOW)
    before = state.FILE.read_bytes()
    with pytest.raises(ValueError) as error:
        state.quiet_for(minutes, NOW)
    assert "invented private value" not in str(error.value)
    assert state.FILE.read_bytes() == before


@pytest.mark.parametrize("until", [True, None, [], "invented private value", float("nan"), 1e300, 0])
def test_bad_absolute_quiet_deadline_never_writes(until):
    with pytest.raises(ValueError) as error:
        state.quiet_until(until, NOW)
    assert not state.FILE.exists() and "invented private value" not in str(error.value)


def test_valid_reminder_return_state_survives_and_wrong_state_is_refused_before_writing():
    back = {"mode": "quiet", "until": STAMP + 600, "reminders": ["invented1"]}
    state.awake(return_to=back)
    assert state.current()["return_to"] == back
    before = state.FILE.read_bytes()
    with pytest.raises(ValueError):
        state.awake(return_to={"mode": "asleep", "reminders": [{}]})
    assert state.FILE.read_bytes() == before


def test_failed_atomic_save_keeps_original_and_removes_temp_file(tmp_path, monkeypatch):
    state.asleep(NOW)
    before = state.FILE.read_bytes()

    def fail(*args):
        raise OSError("invented write failure")

    monkeypatch.setattr(state.os, "replace", fail)
    with pytest.raises(OSError):
        state.awake()
    assert state.FILE.read_bytes() == before and not list(tmp_path.glob("*.tmp"))


def test_unreadable_mode_is_visible_in_health_and_the_status_strip_does_not_crash():
    state.FILE.write_text('{"mode":"quiet","until":"invented private value"}')
    tiles = health.mode_and_app(live_at=0, now=STAMP)
    assert tiles[0]["status"] == "warn" and "unreadable" in tiles[0]["detail"]
    assert "invented private value" not in json.dumps(tiles)
    assert screen_server.live_state(now=STAMP)["state"] == "asleep"


def test_corrupt_mode_uses_explicit_wake_triggers_without_opening_audio(tmp_path, monkeypatch):
    state.FILE.write_text('[]')
    monkeypatch.setitem(sys.modules, "vosk", SimpleNamespace(Model=lambda path: object(),
                        KaldiRecognizer=lambda *args: object(), SetLogLevel=lambda value: None))
    monkeypatch.setattr(wake, "ensure_model", lambda *args: tmp_path / "invented-model")
    monkeypatch.setattr(wake, "MODEL_DIR", tmp_path / "absent-model")
    monkeypatch.setattr(wake, "mic_source", lambda: "invented input")
    monkeypatch.setattr(wake, "mic_chunks", lambda source: iter(()))
    seen = []

    def heard(*args, **kwargs):
        seen.append(kwargs["triggers"])
        return "phrase"

    monkeypatch.setattr(wake, "heard", heard)
    assert supervisor.wait_asleep() == "wake phrase" and seen == [wake.WAKE_UP]


def test_existing_app_stops_and_stays_stopped_after_invalid_mode_even_on_crash(monkeypatch):
    class Waiting(Exception):
        pass

    state.awake()
    monkeypatch.setattr(app_mode, "load_env", lambda names: [])
    monkeypatch.setattr(screen_server, "serve", lambda: None)
    monkeypatch.setattr(watchdog, "take_request", lambda: "invented restart request")
    events = []

    def run_app(should_stop):
        events.append("app")
        state.FILE.write_text('["invented private value"]')
        assert should_stop() is True
        return 1

    monkeypatch.setattr(supervisor, "run_app", run_app)
    monkeypatch.setattr(supervisor, "wait_asleep", lambda: (_ for _ in ()).throw(Waiting()))
    monkeypatch.setattr(supervisor.time, "sleep", lambda seconds: pytest.fail("Do not schedule a restart"))
    monkeypatch.setattr(chimes, "play", lambda *args, **kwargs: events.append("chime"))
    with pytest.raises(Waiting):
        supervisor.main()
    assert events == ["app"] and state.current()["unreadable"] is True


@pytest.mark.parametrize("screen", [False, True])
@pytest.mark.parametrize("initial", ["asleep", "quiet", "unreadable"])
def test_dashboard_start_resets_stale_mode_but_supervised_install_preserves_it(monkeypatch, screen, initial):
    from andy_companion import captions, consent, guard, live, privacy, settings, speaker, turns, urgent, voice_controls, volume
    from andy_companion.body import attach as body

    if initial == "unreadable":
        state.FILE.write_text('[]')
    elif initial == "quiet":
        state.quiet_for(30, NOW)
    else:
        state.asleep(NOW)
    before = state.FILE.read_bytes()
    monkeypatch.setattr(app_mode, "load_env", lambda names: [])
    monkeypatch.setattr(app_mode, "configure_env", lambda: None)
    for module in (privacy, body, settings, voice_controls, urgent, guard, consent, captions, turns):
        monkeypatch.setattr(module, "install", lambda: None)
    monkeypatch.setattr(speaker, "attach", lambda: None)
    monkeypatch.setattr(volume, "apply_saved", lambda: None)
    monkeypatch.setattr(state, "install_sleep_tool", lambda: None)
    monkeypatch.setattr(watchdog, "install", lambda **kwargs: None)
    monkeypatch.setattr(live, "report_loop", lambda: None)
    monkeypatch.setattr(threading, "Thread", lambda *args, **kwargs: SimpleNamespace(start=lambda: None))
    monkeypatch.setattr(screen_server, "serve", lambda: None)
    app_mode.install(screen=screen)
    if screen:
        assert state.current() == {"mode": "awake", "until": None}
    else:
        assert state.FILE.read_bytes() == before
