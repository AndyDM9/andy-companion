import io
import json

import numpy as np
import pytest

pytest.importorskip("cv2")

from andy_companion import vision  # noqa: E402

FRAME = np.full((480, 640, 3), 128, np.uint8)


class Opener:
    def __init__(self, reply="A cup of tea on a wooden table."):
        self.reply, self.requests = reply, []

    def __call__(self, req, timeout=None):
        self.requests.append((req.full_url, json.loads(req.data), dict(req.headers)))
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": self.reply}}]}).encode())


@pytest.fixture
def endpoint(monkeypatch):
    monkeypatch.setenv("ANDY_VISION_URL", "https://abc.endpoints.nebius.cloud")
    monkeypatch.setenv("ANDY_VISION_TOKEN", "secret-token")


def test_describes_with_the_picture_and_the_question(endpoint):
    op = Opener()
    text = vision.describe(FRAME, "what colour is the cup?", opener=op)
    url, body, headers = op.requests[0]
    assert text == "A cup of tea on a wooden table."
    assert url == "https://abc.endpoints.nebius.cloud/v1/chat/completions"
    assert headers["Authorization"] == "Bearer secret-token"
    parts = body["messages"][0]["content"]
    assert parts[1]["image_url"]["url"].startswith("data:image/jpeg;base64,")
    assert "what colour is the cup?" in parts[0]["text"] and "Never say who a person is" in parts[0]["text"]


def test_switched_off_without_an_endpoint(monkeypatch):
    monkeypatch.delenv("ANDY_VISION_URL", raising=False)
    assert "switched off" in vision.look(lambda: FRAME, opener=Opener())["error"]


def test_errors_never_echo_the_picture(endpoint):
    def broken(req, timeout=None):
        raise OSError(req.data[:100].decode(errors="ignore"))
    out = vision.look(lambda: FRAME, opener=broken)
    assert "error" in out and "base64" not in out["error"]


def test_large_pictures_are_made_smaller():
    big = np.full((1080, 1920, 3), 200, np.uint8)
    import cv2
    small = cv2.imdecode(np.frombuffer(vision.jpeg(big), np.uint8), cv2.IMREAD_COLOR)
    assert small.shape[1] == 768


def test_never_sends_over_plain_http(monkeypatch):
    monkeypatch.setenv("ANDY_VISION_URL", "192.0.2.10:8000")
    monkeypatch.setenv("ANDY_VISION_TOKEN", "secret-token")
    op = Opener()
    assert "secure" in vision.look(lambda: FRAME, opener=op)["error"] and op.requests == []


def test_a_stopped_endpoint_is_said_plainly(monkeypatch):
    import urllib.error

    monkeypatch.setenv("ANDY_VISION_URL", "https://eyes.example")
    monkeypatch.setenv("ANDY_VISION_TOKEN", "t")

    def stopped(req, timeout=None):
        raise urllib.error.HTTPError(req.full_url, 503, "Service Unavailable", {}, None)

    import numpy as np
    frame = np.zeros((48, 64, 3), dtype=np.uint8)
    out = vision.look(lambda: frame, "what do you see", opener=stopped)
    assert out == {"error": "My eyes are switched off right now, so I can't see. They can be turned on from the computer."}


def test_a_broken_camera_never_crashes_the_turn():
    def broken():
        raise RuntimeError("camera pipeline")
    assert vision.look(broken) == {"error": "My camera did not give a picture just now."}
