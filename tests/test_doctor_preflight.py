"""Keep preflight failures visible without hardware, provider keys or transcript data."""

import importlib.util
import json
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
    health.write_text('{"at": ' + str(time.time()) + ', "drops_last_min": 0, "unanswered_s": null}')
    monkeypatch.setattr(watchdog, "HEALTH", health)
    monkeypatch.setattr(settings, "get", lambda: {"tv_yaw": 0})
    monkeypatch.setattr(doctor, "other_robot_apps", lambda: None)
    monkeypatch.setattr(doctor, "voice_log", lambda: "")
    monkeypatch.setattr(doctor.subprocess, "run", lambda *a, **k: subprocess.CompletedProcess([], 0))
    doctor.live({"ANDY_VISION": "off"})
    ownership = next(result for result in doctor.results if result[0] == "Only Andy drives the robot")
    assert ownership[1] is False
    assert "could not identify every robot connection" in capsys.readouterr().out


def test_vision_preflight_calls_the_configured_model_without_requiring_catalogue_membership(doctor, monkeypatch):
    import json

    def inference(url, body, headers, timeout):
        assert url == 'https://example.invalid/v1/chat/completions'
        assert body['model'] == 'invented-model-not-in-catalogue'
        assert body['max_tokens'] == 8 and timeout == 15
        assert body['messages'] == [{'role': 'user', 'content': 'Say: ready.'}]
        assert 'image' not in json.dumps(body)
        assert headers['Authorization'] == 'Bearer invented-private-value'
        return 200, json.dumps({'choices': [{'message': {'content': 'invented provider answer'}}]}).encode()

    monkeypatch.setattr(doctor, 'http', inference)
    ok, detail = doctor.vision_model_probe({'NEBIUS_BASE_URL': 'https://example.invalid/v1/',
                                          'ANDY_VISION_MODEL': 'invented-model-not-in-catalogue',
                                          'NEBIUS_API_KEY': 'invented-private-value'})
    assert ok and 'text-only' in detail and 'invented provider answer' not in detail


@pytest.mark.parametrize('answer', ['', '   ', None, False])
def test_vision_preflight_rejects_empty_or_nontext_answers(doctor, monkeypatch, answer):
    import json

    monkeypatch.setattr(doctor, 'http', lambda *a, **k: (200, json.dumps({'choices': [{'message': {'content': answer}}]}).encode()))
    assert doctor.vision_model_probe({}) == (False, 'unusable final reply')


@pytest.mark.parametrize('status', [401, 404, 502])
def test_vision_preflight_keeps_http_failures_visible_without_returning_payloads(doctor, monkeypatch, status):
    import urllib.error

    def fail(*args, **kwargs):
        raise urllib.error.HTTPError('https://example.invalid/?key=invented-private-value', status,
                                     'invented private provider body', {}, None)

    monkeypatch.setattr(doctor, 'http', fail)
    assert doctor.vision_model_probe({}) == (False, f'HTTP {status}')


def test_vision_preflight_does_not_expose_transport_error_text(doctor, monkeypatch):
    def fail(*args, **kwargs):
        raise TimeoutError('invented private request text')
    monkeypatch.setattr(doctor, 'http', fail)
    assert doctor.vision_model_probe({}) == (False, 'TimeoutError')


def test_vision_preflight_rejects_a_malformed_success_body(doctor, monkeypatch):
    monkeypatch.setattr(doctor, 'http', lambda *a, **k: (200, b'{}'))
    assert doctor.vision_model_probe({}) == (False, 'unusable final reply')


def test_vision_preflight_rejects_a_non_success_http_response(doctor, monkeypatch):
    monkeypatch.setattr(doctor, 'http', lambda *a, **k: (202, b'{}'))
    assert doctor.vision_model_probe({}) == (False, 'HTTP 202')


@pytest.fixture
def live_fixture(doctor, monkeypatch, tmp_path):
    from andy_companion import settings, state, watchdog

    health = tmp_path / 'health.json'
    health.write_text(json.dumps({'at': time.time(), 'drops_last_min': 0, 'unanswered_s': None}))
    monkeypatch.setattr(watchdog, 'HEALTH', health)
    monkeypatch.setattr(state, 'FILE', tmp_path / 'state.json')
    monkeypatch.setattr(settings, 'get', lambda: {'tv_yaw': 0})
    monkeypatch.setattr(doctor, 'other_robot_apps', lambda: [])
    monkeypatch.setattr(doctor, 'voice_log', lambda: '')
    monkeypatch.setattr(doctor.subprocess, 'run', lambda *a, **k: subprocess.CompletedProcess([], 0))
    monkeypatch.setattr(doctor.os, 'getloadavg', lambda: (0, 0, 0))
    monkeypatch.delenv('ANDY_FINDER_RECORD', raising=False)
    return health


@pytest.mark.parametrize('payload', [
    [], None, 'invented-private-value', {},
    {'at': 'invented-private-value', 'drops_last_min': 0, 'unanswered_s': None},
    {'at': True, 'drops_last_min': 0, 'unanswered_s': None},
    {'at': float('nan'), 'drops_last_min': 0, 'unanswered_s': None},
    {'at': float('inf'), 'drops_last_min': 0, 'unanswered_s': None},
    {'at': 10**400, 'drops_last_min': 0, 'unanswered_s': None},
    {'at': 1, 'drops_last_min': 'invented-private-value', 'unanswered_s': None},
    {'at': 1, 'drops_last_min': -1, 'unanswered_s': None},
    {'at': 1, 'drops_last_min': False, 'unanswered_s': None},
    {'at': 1, 'drops_last_min': 0.5, 'unanswered_s': None},
    {'at': 1, 'drops_last_min': 0, 'unanswered_s': -1},
    {'at': 1, 'drops_last_min': 0, 'unanswered_s': False},
    {'at': 1, 'drops_last_min': 0, 'unanswered_s': float('nan')},
    {'at': 1, 'drops_last_min': 0, 'unanswered_s': 'invented-private-value'},
])
def test_bad_health_fails_both_checks_without_crash_or_echo(doctor, live_fixture, capsys, payload):
    live_fixture.write_text(json.dumps(payload))
    doctor.live({'ANDY_VISION': 'off'})
    checks = {r[0]: r[1] for r in doctor.results}
    assert checks['Microphone audio'] is False and checks['Nothing talking over Andy'] is False
    assert 'invented-private-value' not in capsys.readouterr().out


@pytest.mark.parametrize('kind', ['vision', 'text'])
@pytest.mark.parametrize('message,finish', [
    ({'content': 'invented-private-value'}, 'length'),
    ({'content': 'invented-private-value'}, 'content_filter'),
    ({'content': 'invented-private-value'}, None),
    ({'content': 'invented-private-value', 'refusal': 'invented-private-value'}, 'stop'),
    ({'content': 'invented-private-value', 'tool_calls': [{'id': 'invented'}]}, 'stop'),
    ({'content': '<think>invented-private-value'}, 'stop'),
    ({'content': '<think>invented-private-value</think>'}, 'stop'),
    ({'content': ''}, 'stop'),
    ({'content': None}, 'stop'),
])
def test_incomplete_probe_reply_is_not_a_pass(doctor, live_fixture, monkeypatch, capsys, kind, message, finish):
    payload = {'choices': [{'finish_reason': finish, 'message': message}]}
    monkeypatch.setattr(doctor, 'http', lambda *a, **k: (200, json.dumps(payload).encode()))
    if kind == 'vision':
        ok, detail = doctor.vision_model_probe({})
        assert ok is False and 'invented-private-value' not in detail
    else:
        doctor.live({'ANDY_VISION': 'off', 'NEBIUS_API_KEY': 'invented-private-key'})
        check = next(r for r in doctor.results if r[0] == 'Nemotron replies quickly')
        assert check[1] is False
    assert 'invented-private-value' not in capsys.readouterr().out


@pytest.mark.parametrize('raw', [b'', b'{', b'\xff', b'[' * 1200, b'{"at": 1, "drops_last_min": 0}'])
def test_unreadable_health_is_preserved_and_later_checks_continue(doctor, live_fixture, capsys, raw):
    live_fixture.write_bytes(raw)
    doctor.live({'ANDY_VISION': 'off'})
    assert live_fixture.read_bytes() == raw
    assert next(r for r in doctor.results if r[0] == 'Microphone audio')[1] is False
    assert next(r for r in doctor.results if r[0] == 'Nothing talking over Andy')[1] is False
    assert next(r for r in doctor.results if r[0] == 'Finder tries not kept')[1] is True


def test_missing_health_is_unknown_without_creating_file(doctor, live_fixture):
    live_fixture.unlink()
    doctor.live({'ANDY_VISION': 'off'})
    assert not live_fixture.exists()
    assert next(r for r in doctor.results if r[0] == 'Microphone audio')[1] is False
    assert next(r for r in doctor.results if r[0] == 'Nothing talking over Andy')[1] is False


@pytest.mark.parametrize('age,drops,unanswered,audio_ok,unanswered_ok', [
    (0, 0, None, True, True), (0, 0, 0, True, True),
    (-0.6, 0, None, True, True), (29.9, 0, None, True, True),
    (30, 0, None, False, False), (-2, 0, None, False, False),
    (0, 1, None, False, True), (0, 0, 2, True, False),
])
def test_health_requires_current_counts_and_allows_watchdog_rounding(
        doctor, live_fixture, monkeypatch, age, drops, unanswered, audio_ok, unanswered_ok):
    monkeypatch.setattr(time, 'time', lambda: 1000)
    live_fixture.write_text(json.dumps({'at': 1000 - age, 'drops_last_min': drops, 'unanswered_s': unanswered,
                                       'extra': 'invented-private-value'}))
    doctor.live({'ANDY_VISION': 'off'})
    assert next(r for r in doctor.results if r[0] == 'Microphone audio')[1] is audio_ok
    assert next(r for r in doctor.results if r[0] == 'Nothing talking over Andy')[1] is unanswered_ok


@pytest.mark.parametrize('status,raw', [(202, b'{}'), (200, b'{}'), (200, b'[]'), (200, b'{'), (200, b'\xff')])
def test_text_probe_rejects_non_success_and_malformed_bodies(doctor, live_fixture, monkeypatch, status, raw):
    monkeypatch.setattr(doctor, 'http', lambda *a, **k: (status, raw))
    doctor.live({'ANDY_VISION': 'off', 'NEBIUS_API_KEY': 'invented-private-key'})
    assert next(r for r in doctor.results if r[0] == 'Nemotron replies quickly')[1] is False


@pytest.mark.parametrize('duration,ok', [(0.2, True), (1.5, False), (2.0, False)])
def test_text_probe_requires_usable_reply_and_monotonic_latency(doctor, live_fixture, monkeypatch, capsys, duration, ok):
    ticks = iter([10, 10 + duration])
    monkeypatch.setattr(time, 'monotonic', lambda: next(ticks))
    def answer(url, body, headers, timeout):
        assert body['model'] == 'nvidia/Nemotron-3_5-Lightning' and body['max_tokens'] == 8
        assert body['messages'] == [{'role': 'user', 'content': 'Say: ready.'}] and timeout == 15
        assert headers['Authorization'] == 'Bearer invented-private-key'
        return 200, json.dumps({'choices': [{'finish_reason': 'stop', 'message': {'content': 'invented-private-value'}}]}).encode()
    monkeypatch.setattr(doctor, 'http', answer)
    doctor.live({'ANDY_VISION': 'off', 'NEBIUS_API_KEY': 'invented-private-key'})
    assert next(r for r in doctor.results if r[0] == 'Nemotron replies quickly')[1] is ok
    assert 'invented-private-value' not in capsys.readouterr().out


def test_endpoint_catalogue_does_not_claim_inference(doctor, live_fixture, monkeypatch, capsys):
    def catalogue(url, body=None, headers=None, timeout=None):
        assert url == 'https://endpoint.invalid/v1/models' and body is None
        return 200, b'{}'
    monkeypatch.setattr(doctor, 'http', catalogue)
    doctor.live({'ANDY_VISION': 'off', 'ANDY_GUARD_URL': 'https://endpoint.invalid'})
    result = next(r for r in doctor.results if r[0] == 'Second look endpoint catalogue')
    assert result[1] is True and result[2] == 'model catalogue reachable; inference not tested'
