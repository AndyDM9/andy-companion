"""The supervisor's own process: the keys it reads from the env file, and how a due reminder borrows Andy
from sleep or quiet and gives it back (review, 2026-10-14)."""

import logging
import os
import stat
from datetime import datetime, timedelta

import pytest

from andy_companion import app_mode, reminders, screen_server, setup_page, settings, state, supervisor, web

NOW = datetime(2026, 10, 13, 22, 0)
SECRET = "tvly-not-a-real-key-123"


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "FILE", tmp_path / "state.json")
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setitem(screen_server._live, "state", "")
    monkeypatch.setitem(screen_server._live, "at", 0.0)


@pytest.fixture
def env_file(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text(f"# keys\nNEBIUS_API_KEY=nb-not-real\nexport TAVILY_API_KEY=\"{SECRET}\"\nANDY_GUARD_TOKEN=g\n")
    os.chmod(path, 0o600)
    monkeypatch.setenv("ANDY_ENV_FILE", str(path))
    unset(monkeypatch, *app_mode.APP_KEYS)
    return path


def unset(monkeypatch, *names):
    """Unset for this test, and unset again afterwards whatever the code under test loads."""
    for name in names:
        monkeypatch.setenv(name, "")
        monkeypatch.delenv(name)


# --- the env file ---------------------------------------------------------------------------------

def test_the_setup_page_s_calendar_search_sees_the_key_in_the_supervisor(env_file, monkeypatch, caplog):
    """/api/setup runs in the supervisor, which used to have no Tavily key: web._key() raised, setup_page swallowed
    it, and the town's events calendar was never found under scripts/andy."""
    seen = []

    def find(place):
        seen.append(web._key())                 # raises WebError without the key
        return {"url": "https://town.example/events", "title": "Events"}

    monkeypatch.setattr(web, "find_events_page", find)
    setup_page.suggest_events_page("Springfield, Illinois")
    assert seen == [] and settings.get().get("events_suggestion") is None        # before: no key, nothing found

    class Started(Exception):
        pass

    def serve():
        setup_page.suggest_events_page("Springfield, Illinois")
        raise Started

    monkeypatch.setattr(screen_server, "serve", serve)
    with caplog.at_level(logging.INFO), pytest.raises(Started):
        supervisor.main()
    assert seen == [SECRET]
    assert settings.get()["events_suggestion"]["url"] == "https://town.example/events"
    assert SECRET not in caplog.text and "TAVILY_API_KEY" in caplog.text          # names in the log, never values
    assert "NEBIUS_API_KEY" not in os.environ          # the supervisor takes only what its own features need


def test_the_env_file_never_overrides_what_is_already_set(env_file, monkeypatch):
    monkeypatch.setenv("TAVILY_API_KEY", "from-the-shell")
    assert app_mode.load_env(app_mode.APP_KEYS) == ["NEBIUS_API_KEY", "ANDY_GUARD_TOKEN"]
    assert os.environ["TAVILY_API_KEY"] == "from-the-shell" and os.environ["ANDY_GUARD_TOKEN"] == "g"


def test_no_env_file_loads_nothing(tmp_path, monkeypatch):
    monkeypatch.setenv("ANDY_ENV_FILE", str(tmp_path / "missing"))
    unset(monkeypatch, *app_mode.APP_KEYS)
    assert app_mode.load_env(app_mode.APP_KEYS) == [] and "TAVILY_API_KEY" not in os.environ


def test_the_app_reads_every_key_run_robot_passes_on():
    """The dashboard app has no run-robot.sh, so app_mode must load the same names itself."""
    import re
    from pathlib import Path

    script = (Path(__file__).resolve().parents[1] / "scripts" / "run-robot.sh").read_text()
    passed = set(re.findall(r"s/\^([A-Z_]+)=//p", script))
    assert passed and passed <= set(app_mode.APP_KEYS)


# --- a reminder borrows Andy, then gives it back -----------------------------------------------------

class Clock:
    def __init__(self, at):
        self.t = at.timestamp()

    def __call__(self):
        return self.t


def borrow(mode_setter, due_at):
    mode_setter()
    reminders.add("take the evening tablets", at=due_at.strftime("%H:%M"), now=NOW)
    reason = supervisor.wake_reason(due_at)
    assert reason == "reminder due"
    supervisor.wake_up(reason, due_at)
    s = state.current()
    assert s["mode"] == "awake" and s["return_to"]["reminders"]
    return s["return_to"]


def test_after_a_reminder_wakes_andy_from_quiet_it_goes_back_to_the_rest_of_the_quiet():
    until = state.quiet_for(120, now=NOW)                       # quiet till midnight
    due_at = NOW + timedelta(minutes=30)
    back = borrow(lambda: None, due_at)
    assert back["mode"] == "quiet" and back["until"] == until.timestamp()
    clock = Clock(due_at)
    watch = supervisor.BackAfterReminder(clock)
    assert watch() is False                                     # not said yet
    for r in reminders.due(due_at):
        reminders.said(r["id"], now=due_at)
    clock.t += 30
    assert watch() is False and state.current()["mode"] == "awake"   # said: a minute's grace for a reply
    clock.t += supervisor.RESUME_IDLE_S
    assert watch() is True
    s = state.current()
    assert s["mode"] == "quiet" and s["until"] == until.timestamp() and "return_to" not in s
    assert supervisor.wake_reason(datetime.fromtimestamp(clock.t)) is None        # the quiet holds


def test_after_a_reminder_wakes_andy_from_sleep_it_goes_back_to_sleep():
    due_at = NOW + timedelta(minutes=30)
    borrow(lambda: state.asleep(NOW), due_at)
    clock = Clock(due_at)
    watch = supervisor.BackAfterReminder(clock)
    for r in reminders.due(due_at):
        reminders.said(r["id"], now=due_at)
    watch()
    clock.t += supervisor.RESUME_IDLE_S
    assert watch() is True and state.current()["mode"] == "asleep"


def test_talking_with_andy_after_the_reminder_keeps_it_awake_until_the_talk_ends():
    due_at = NOW + timedelta(minutes=30)
    borrow(lambda: state.asleep(NOW), due_at)
    clock = Clock(due_at)
    watch = supervisor.BackAfterReminder(clock)
    for r in reminders.due(due_at):
        reminders.said(r["id"], now=due_at)
    watch()
    clock.t += supervisor.RESUME_IDLE_S - 5
    screen_server._live.update(state="hearing", at=clock.t)
    assert watch() is False
    clock.t += supervisor.RESUME_IDLE_S - 1
    screen_server._live.update(state="ready", at=clock.t)
    assert watch() is False and state.current()["mode"] == "awake"
    clock.t += 2
    assert watch() is True and state.current()["mode"] == "asleep"


def test_a_quiet_spell_that_ended_meanwhile_leaves_andy_awake():
    state.quiet_for(40, now=NOW)
    due_at = NOW + timedelta(minutes=30)
    borrow(lambda: None, due_at)
    clock = Clock(due_at + timedelta(minutes=15))               # the quiet ended at 22:40
    watch = supervisor.BackAfterReminder(clock)
    for r in reminders.due(due_at):
        reminders.said(r["id"], now=due_at)
    watch()
    clock.t += supervisor.RESUME_IDLE_S
    assert watch() is False
    s = state.current()
    assert s["mode"] == "awake" and "return_to" not in s


def test_a_goodnight_while_the_reminder_is_awake_replaces_the_way_back():
    due_at = NOW + timedelta(minutes=30)
    borrow(lambda: state.quiet_for(120, now=NOW), due_at)
    state.asleep(due_at)                                        # "goodnight" before the reminder was said
    assert "return_to" not in state.current()
    assert supervisor.BackAfterReminder(Clock(due_at))() is False


def test_goodnight_while_a_reminder_is_due_but_unsaid_sticks_for_the_settle_window():
    """Goodnight bounced straight back awake when a reminder was due but not yet said (review, 2026-10-14)."""
    reminders.add("lock the back door", at="21:58", now=NOW - timedelta(minutes=5))
    state.asleep(NOW)                                          # goodnight at 22:00; the reminder was due at 21:58
    assert supervisor.wake_reason(NOW + timedelta(seconds=5)) is None
    assert supervisor.wake_reason(NOW + timedelta(seconds=supervisor.SETTLE_S - 1)) is None
    assert supervisor.wake_reason(NOW + timedelta(seconds=supervisor.SETTLE_S)) == "reminder due"   # never dropped


def test_a_reminder_that_comes_due_after_goodnight_wakes_andy_at_once():
    state.asleep(NOW)
    reminders.add("call my daughter", at="22:05", now=NOW)
    assert supervisor.wake_reason(NOW + timedelta(minutes=5)) == "reminder due"


def test_the_supervisor_stops_the_app_when_told_and_it_is_not_a_crash(tmp_path, monkeypatch):
    """No robot here: a stand-in for run-robot.sh that only waits."""
    script = tmp_path / "scripts" / "run-robot.sh"
    script.parent.mkdir()
    script.write_text("#!/bin/sh\nexec sleep 30\n")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    monkeypatch.setattr(supervisor, "ROOT", tmp_path)
    monkeypatch.setattr(supervisor.sys, "argv", ["supervisor"])
    asks = []

    def should_stop():
        asks.append(1)
        return len(asks) >= 2

    assert supervisor.run_app(should_stop=should_stop, poll_s=0.05) == 0
    assert supervisor.after_exit("asleep", 0) == "wait"


def test_the_wake_phrase_module_is_not_shadowed():
    assert supervisor.wake.__name__ == "andy_companion.wake" and callable(supervisor.wake.ensure_model)


def test_sigterm_and_ctrl_c_stop_the_supervisor_the_same_clean_way():
    import signal
    from andy_companion import supervisor

    before = signal.getsignal(signal.SIGINT), signal.getsignal(signal.SIGTERM)
    try:
        supervisor.stop_on_signals()
        handler = signal.getsignal(signal.SIGTERM)
        try:
            handler(signal.SIGTERM, None)
            raise AssertionError("SIGTERM should stop like Ctrl-C")
        except KeyboardInterrupt:
            pass
        assert signal.getsignal(signal.SIGINT) is signal.default_int_handler
    finally:
        signal.signal(signal.SIGINT, before[0])
        signal.signal(signal.SIGTERM, before[1])
