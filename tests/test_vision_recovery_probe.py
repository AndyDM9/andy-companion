"""Probe resource cleanup and privacy without a camera, model service or robot controller."""
import importlib.util
import json
import os
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("vision_recovery_probe", ROOT / "scripts/check_vision_recovery.py")
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)


class Camera:
    def __init__(self, frames):
        self.frames, self.closed = iter(frames), False
    def open(self):
        pass
    def read(self):
        return next(self.frames, None)
    def close(self):
        self.closed = True


@pytest.fixture
def local(monkeypatch):
    monkeypatch.setattr(probe.vision, "reachable", lambda url: False)
    monkeypatch.setattr(probe.vision, "used", lambda: "local")
    monkeypatch.setenv("ANDY_LOCAL_EYES_URL", "http://127.0.0.1:8095")
    monkeypatch.setattr(probe.app_mode, "read_env", lambda names: {})


def test_waits_for_next_frame_closes_reader_and_never_returns_description(local):
    camera = Camera([None, np.zeros((24, 32, 3), dtype=np.uint8)])
    now = [0.0]
    def pause(seconds):
        now[0] += seconds
    def describe(frame, **kwargs):
        assert camera.closed
        now[0] += 1.5
        return "Invented private description must not appear in metadata."
    with probe.isolated_settings():
        result = probe.probe(lambda: camera, describe, lambda: now[0], pause)
    assert result["frame_shape"] == [24, 32, 3] and result["vision_seconds"] == 1.5
    assert result["acquisition_seconds"] == 0.03
    assert "private description" not in json.dumps(result)


def test_read_timeout_closes_reader_without_inference(local):
    now = [0]
    camera = Camera([])
    def pause(seconds):
        now[0] += 1
    with probe.isolated_settings(), pytest.raises(TimeoutError):
        probe.probe(lambda: camera, lambda *a, **k: pytest.fail("No frame should reach inference"), lambda: now[0], pause)
    assert camera.closed


def test_remote_local_setting_is_refused_before_camera_opens(local, monkeypatch):
    monkeypatch.setenv("ANDY_LOCAL_EYES_URL", "https://remote.example.invalid")
    with probe.isolated_settings(), pytest.raises(ValueError):
        probe.probe(lambda: pytest.fail("Remote destination must be refused before capture"))


def test_settings_are_restored_even_after_failure(local, monkeypatch):
    monkeypatch.setenv("ANDY_VISION", "token-factory")
    monkeypatch.delenv("ANDY_VISION_URL", raising=False)
    with pytest.raises(RuntimeError), probe.isolated_settings():
        assert os.environ["ANDY_VISION_URL"] == "https://127.0.0.1:1"
        raise RuntimeError("invented failure")
    assert os.environ["ANDY_VISION"] == "token-factory" and "ANDY_VISION_URL" not in os.environ


def test_cli_does_not_echo_error_text_or_write_a_result_on_failure(local, monkeypatch, tmp_path, capsys):
    def fail():
        raise ValueError("invented private description")
    monkeypatch.setattr(probe, "probe", fail)
    output = tmp_path / "result.json"
    assert probe.main(["--out", str(output)]) == 1
    assert "private description" not in capsys.readouterr().out
    assert not output.exists()
