import importlib.util
import json
import logging
from pathlib import Path

import numpy as np
import pytest

from andy_companion import supervisor, turns, watchdog


@pytest.fixture(autouse=True)
def files(tmp_path, monkeypatch):
    monkeypatch.setattr(watchdog, "REQUEST", tmp_path / "restart-request")
    monkeypatch.setattr(watchdog, "HEALTH", tmp_path / "health.json")
    monkeypatch.setattr(turns, "CLOCK", turns.TurnClock(clock=lambda: 0.0))


def drop(counter, n, at):
    rec = logging.LogRecord(watchdog.AUDIO_LOGGER, logging.WARNING, "", 0,
                            "Warning: gst-core-error-quark: Can't record audio fast enough (13)", None, None)
    for _ in range(n):
        counter.clock = lambda: at
        counter.emit(rec)


def test_a_minute_of_dropped_audio_asks_for_a_restart_once():
    t = [0.0]
    counter = watchdog.DropCounter(clock=lambda: t[0])
    stopped = []
    dog = watchdog.Watchdog(counter, clock=lambda: t[0], stop=lambda: stopped.append(True))
    drop(counter, 25, 10.0)
    assert dog.check(10.0) is None and not stopped               # the first minute after start: grace
    t[0] = 70.0
    drop(counter, 25, 70.0)
    assert dog.check(70.0) == "restart" and stopped == [True]
    assert watchdog.REQUEST.read_text().startswith("the microphone dropped audio")
    assert dog.check(71.0) != "restart"                          # asked once
    health = json.loads(watchdog.HEALTH.read_text())
    assert health["drops_last_min"] >= 25 and health["restarts_asked"] == 1 and set(health) == {
        "at", "drops_last_min", "unanswered_s", "restarts_asked"}  # counts and times only


def test_a_few_drops_are_left_alone():
    counter = watchdog.DropCounter(clock=lambda: 100.0)
    dog = watchdog.Watchdog(counter, clock=lambda: 100.0, stop=lambda: pytest.fail("no restart"))
    dog.started = 0.0
    drop(counter, 5, 100.0)
    assert dog.check(100.0) is None


def test_the_supervisor_restarts_when_asked_and_says_why():
    watchdog._write(watchdog.REQUEST, "the microphone dropped audio 30 times in a minute")
    why = watchdog.take_request()
    assert why.startswith("the microphone") and not watchdog.REQUEST.exists()
    assert supervisor.after_exit("awake", 0, restart_asked=True) == "restart"     # not "sleep"
    assert supervisor.after_exit("awake", 0) == "sleep" and watchdog.take_request() is None


def test_speech_without_an_answer_is_noticed_and_an_answer_clears_it():
    t = [0.0]
    clock = turns.TurnClock(clock=lambda: t[0])
    clock.mark("user_speech_started")
    t[0] = 100.0
    clock.mark("user_speech_started")
    assert clock.unanswered_for() == 100.0
    clock.mark("assistant_audio_delta")
    assert clock.unanswered_for() is None
    t[0] = 200.0                                                  # silence for a while: nothing waiting
    clock.mark("user_speech_started")
    t[0] = 300.0
    assert clock.unanswered_for() is None


def test_the_voice_server_caps_a_turn():
    path = Path(__file__).resolve().parents[1] / "voice" / "serve.py"
    spec = importlib.util.spec_from_file_location("andy_voice_serve", path)
    serve = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(serve)

    class VAD:
        sample_rate = 16000
        _speculative_audio_prefix = None

        def _should_reopen_current_turn(self, audio_start_ms):
            return True

    serve.cap_turns(VAD, max_turn_s=40)
    v = VAD()
    assert v._should_reopen_current_turn(0) is True
    v._speculative_audio_prefix = np.zeros(16000 * 39, dtype=np.float32)
    assert v._should_reopen_current_turn(0) is True
    v._speculative_audio_prefix = np.zeros(16000 * 41, dtype=np.float32)
    assert v._should_reopen_current_turn(0) is False             # a new turn instead


def test_the_voice_server_takes_its_key_from_the_environment_never_the_command_line():
    # A command line is readable by every process on this shared computer (`ps`); found 2026-10-14.
    path = Path(__file__).resolve().parents[1] / "voice" / "serve.py"
    spec = importlib.util.spec_from_file_location("andy_voice_serve_key", path)
    serve = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(serve)
    argv = ["speech-to-speech", "serve", "--responses_api_stream"]
    assert serve.key_from_environment(argv, {"NEBIUS_API_KEY": "k"})[-2:] == ["--responses_api_api_key", "k"]
    assert serve.key_from_environment(argv, {}) == argv
    given = argv + ["--responses_api_api_key=x"]
    assert serve.key_from_environment(given, {"NEBIUS_API_KEY": "k"}) == given
    run = (path.parent / "run.sh").read_text()
    assert "--responses_api_api_key" not in run and "export NEBIUS_API_KEY" in run


def test_without_a_supervisor_the_watchdog_only_logs(caplog):
    """The dashboard app has no supervisor: stopping it would leave Andy off until someone pressed start."""
    t = [70.0]
    counter = watchdog.DropCounter(clock=lambda: t[0])
    dog = watchdog.Watchdog(counter, clock=lambda: t[0], stop=lambda: pytest.fail("no stop without a supervisor"),
                            supervised=False)
    dog.started = 0.0
    drop(counter, 25, 70.0)
    with caplog.at_level(logging.WARNING, logger="andy.watchdog"):
        assert dog.check(70.0) == "unsupervised"
        assert dog.check(75.0) is None                                  # said once
    assert "no supervisor" in caplog.text and not watchdog.REQUEST.exists()
    assert json.loads(watchdog.HEALTH.read_text())["restarts_asked"] == 0


def test_the_dashboard_app_s_watchdog_is_unsupervised():
    source = (Path(__file__).resolve().parents[1] / "src" / "andy_companion" / "app_mode.py").read_text()
    assert "watchdog.install(supervised=not screen)" in source


def test_the_voice_server_uses_the_first_gpu_unless_told_otherwise():
    """A judge's computer with one GPU has only GPU 0; the founder's sets ANDY_VOICE_GPU=1 in the env file."""
    run = (Path(__file__).resolve().parents[1] / "voice" / "run.sh").read_text()
    assert 'CUDA_VISIBLE_DEVICES="${ANDY_VOICE_GPU:-0}"' in run
    assert run.index(". \"$ENV_FILE\"") < run.index("CUDA_VISIBLE_DEVICES")      # the env file can choose
