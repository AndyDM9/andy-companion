"""Keep preflight failures visible without hardware, provider keys or transcript data."""

import importlib.util
from pathlib import Path
import socket
import subprocess
import time

import pytest


@pytest.fixture
def doctor():
    spec = importlib.util.spec_from_file_location("doctor_preflight", Path(__file__).resolve().parents[1] /
                                                  "scripts" / "doctor.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_configured_voice_port_is_probed_instead_of_default(doctor, monkeypatch):
    monkeypatch.delenv("HF_REALTIME_WS_URL", raising=False)
    with socket.socket() as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        assert doctor.voice_reachable({"ANDY_VOICE_URL": f"ws://127.0.0.1:{port}/v1/realtime"})
    assert not doctor.voice_reachable({"ANDY_VOICE_URL": f"ws://127.0.0.1:{port}/v1/realtime"})


@pytest.mark.parametrize("url,expected", [
    ("ws://voice.example/v1/realtime", ("voice.example", 80)),
    ("wss://voice.example/v1/realtime", ("voice.example", 443)),
    ("ws://[::1]:9876/v1/realtime", ("::1", 9876)),
])
def test_upstream_voice_override_has_app_precedence(doctor, monkeypatch, url, expected):
    monkeypatch.setenv("HF_REALTIME_WS_URL", url)
    calls = []

    def connect(address, timeout):
        calls.append((address, timeout))
        return socket.socket()  # Context manager only; no outside connection.

    monkeypatch.setattr(doctor.socket, "create_connection", connect)
    assert doctor.voice_reachable({"ANDY_VOICE_URL": "ws://ignored.example:8765"})
    assert calls == [(expected, 3)]


@pytest.mark.parametrize("url", ["", "http://voice.example", "ws:///path", "ws://[bad", "ws://voice.example:bad"])
def test_bad_voice_addresses_fail_without_printing_values(doctor, monkeypatch, capsys, url):
    monkeypatch.setenv("HF_REALTIME_WS_URL", url)
    assert not doctor.voice_reachable({})
    assert capsys.readouterr() == ("", "")


@pytest.mark.parametrize("result", [
    subprocess.CompletedProcess([], 1, "", "permission denied"),
    subprocess.CompletedProcess([], 0, "", "process information unavailable"),
    OSError("ss unavailable"),
    subprocess.TimeoutExpired("ss", 5),
])
def test_failed_connection_inspection_is_unknown_not_clear(doctor, monkeypatch, result):
    def run(*args, **kwargs):
        if isinstance(result, Exception):
            raise result
        return result

    monkeypatch.setattr(doctor.subprocess, "run", run)
    assert doctor.other_robot_apps() is None


def test_a_connection_with_hidden_process_ownership_is_unknown(doctor):
    visible = '0 0 127.0.0.1:1234 127.0.0.1:8000 users:(("python",pid=42,fd=5))'
    hidden = "0 0 127.0.0.1:1235 127.0.0.1:8000"
    assert doctor.other_robot_apps(visible, lambda pid: ("andy.service", True)) == []
    assert doctor.other_robot_apps(visible + "\n" + hidden, lambda pid: ("andy.service", True)) is None
    assert doctor.other_robot_apps("") == []


def test_unknown_ownership_is_a_failed_live_check(doctor, monkeypatch, tmp_path, capsys):
    from andy_companion import settings, watchdog

    health = tmp_path / "health.json"
    health.write_text('{"at": ' + str(time.time()) + ', "drops_last_min": 0}')
    monkeypatch.setattr(watchdog, "HEALTH", health)
    monkeypatch.setattr(settings, "get", lambda: {"tv_yaw": 0})
    monkeypatch.setattr(doctor, "other_robot_apps", lambda: None)
    monkeypatch.setattr(doctor, "voice_log", lambda: "")
    monkeypatch.setattr(doctor.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0))
    doctor.live({"ANDY_VISION": "off"})
    ownership = next(result for result in doctor.results if result[0] == "Only Andy drives the robot")
    assert ownership[1] is False
    assert "could not identify every robot connection" in capsys.readouterr().out
