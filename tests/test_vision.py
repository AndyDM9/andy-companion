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
    monkeypatch.setenv("ANDY_VISION", "endpoint")
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
    monkeypatch.setenv("ANDY_VISION", "endpoint")
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
    monkeypatch.setenv("ANDY_VISION", "endpoint")
    monkeypatch.setenv("ANDY_VISION_URL", "192.0.2.10:8000")
    monkeypatch.setenv("ANDY_VISION_TOKEN", "secret-token")
    op = Opener()
    assert "secure" in vision.look(lambda: FRAME, opener=op)["error"] and op.requests == []


def test_a_stopped_endpoint_is_said_plainly(monkeypatch):
    import urllib.error

    monkeypatch.setenv("ANDY_VISION", "endpoint")
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


def test_a_stopped_endpoint_that_does_not_answer_is_said_at_once(endpoint, monkeypatch):
    """Between demos the endpoint is stopped; a question must not wait the full read timeout for it."""
    import urllib.request

    def never(req, timeout=None):
        raise AssertionError("no request to an endpoint that takes no connection")

    monkeypatch.setattr(vision, "reachable", lambda url: False)
    monkeypatch.setattr(urllib.request, "urlopen", never)
    assert vision.look(lambda: FRAME) == {"error": vision.SWITCHED_OFF}


def test_a_running_endpoint_keeps_its_long_read_timeout(endpoint, monkeypatch):
    import urllib.request

    waits = []

    def running(req, timeout=None):
        waits.append(timeout)
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": "A cup."}}]}).encode())

    monkeypatch.setattr(vision, "reachable", lambda url: True)
    monkeypatch.setattr(urllib.request, "urlopen", running)
    assert vision.describe(FRAME) == "A cup." and waits == [vision.TIMEOUT_S]


def test_reachable_only_connects_and_gives_up_quickly():
    import socket

    listening = socket.socket()
    listening.bind(("127.0.0.1", 0))
    listening.listen(1)
    port = listening.getsockname()[1]
    try:
        assert vision.reachable(f"https://127.0.0.1:{port}")
    finally:
        listening.close()
    assert not vision.reachable(f"https://127.0.0.1:{port}")          # nothing listening any more
    seen = []

    def slow(address, timeout=None):
        seen.append((address, timeout))
        raise TimeoutError
    assert not vision.reachable("https://eyes.example", connect=slow)
    assert seen == [(("eyes.example", 443), vision.CONNECT_S)] and vision.CONNECT_S <= 5


def test_a_photo_that_cannot_be_read_is_said_plainly(tmp_path, monkeypatch):
    from andy_companion import board

    broken = tmp_path / "photo.jpg"
    broken.write_bytes(b"not a picture")
    monkeypatch.setattr(board, "photo_path", lambda photo_id: broken)
    assert vision.describe_photo("p1", opener=Opener()) == {"error": "I couldn't open that photo."}
