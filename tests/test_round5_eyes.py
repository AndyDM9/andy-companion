"""Round 5, B32: the eyes on serverless Token Factory (NVIDIA Nemotron 3.5 Super VL) by default, the person's
own endpoint (Nano VL) when ANDY_VISION says so, and no eyes at all when it says off."""

import io
import json

import numpy as np
import pytest

pytest.importorskip("cv2")

from andy_companion import finder, vision  # noqa: E402

FRAME = np.full((48, 64, 3), 90, np.uint8)


class Opener:
    def __init__(self, reply):
        self.reply, self.requests = reply, []

    def __call__(self, req, timeout=None):
        self.requests.append((req.full_url, json.loads(req.data), dict(req.headers)))
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": self.reply}}]}).encode())


@pytest.fixture
def token_factory(monkeypatch):
    for k in ("ANDY_VISION", "ANDY_VISION_MODEL", "NEBIUS_BASE_URL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("NEBIUS_API_KEY", "nb-key")
    monkeypatch.setenv("ANDY_VISION_URL", "https://stopped-endpoint.example")   # set, but not chosen
    monkeypatch.setenv("ANDY_VISION_TOKEN", "endpoint-token")


def test_token_factory_is_the_default_with_super_vl_and_no_reasoning(token_factory, monkeypatch):
    monkeypatch.setattr(vision, "reachable", lambda url: (_ for _ in ()).throw(AssertionError("no check needed")))
    op = Opener("A cup on a table.")
    assert vision.describe(FRAME, "what is this?", opener=op) == "A cup on a table."
    url, body, headers = op.requests[0]
    assert url == "https://api.tokenfactory.nebius.com/v1/chat/completions"
    assert body["model"] == "nvidia/Nemotron-3.5-Super-VL"
    assert body["chat_template_kwargs"] == {"enable_thinking": False}
    assert headers["Authorization"] == "Bearer nb-key"
    assert vision.name() == "NVIDIA Nemotron 3.5 Super VL on Nebius Token Factory"


def test_the_finder_asks_token_factory_for_structured_output(token_factory):
    op = Opener('{"seen": true, "x": 0.2, "where": "on the table by the lamp"}')
    out = finder.ask(FRAME, "glasses", opener=op)
    assert out == {"seen": True, "x": 0.2, "y": 0.5, "where": "on the table by the lamp"}
    body = op.requests[0][1]
    assert body["response_format"]["json_schema"]["schema"] == finder.SCHEMA
    assert body["chat_template_kwargs"] == {"enable_thinking": False} and body["temperature"] == 0


def test_the_endpoint_when_chosen(token_factory, monkeypatch):
    monkeypatch.setenv("ANDY_VISION", "endpoint")
    op = Opener("A chair.")
    vision.describe(FRAME, opener=op)
    url, body, headers = op.requests[0]
    assert url == "https://stopped-endpoint.example/v1/chat/completions" and body["model"] == vision.MODEL
    assert "chat_template_kwargs" not in body and headers["Authorization"] == "Bearer endpoint-token"
    assert "Nano 12B v2 VL" in vision.name()


def test_off_and_missing_key_mean_no_eyes(token_factory, monkeypatch):
    monkeypatch.setenv("ANDY_VISION", "off")
    assert not vision.configured() and vision.name() == "off"
    assert "switched off" in vision.look(lambda: FRAME, opener=Opener("x"))["error"]
    monkeypatch.delenv("ANDY_VISION")
    monkeypatch.delenv("NEBIUS_API_KEY")
    assert not vision.configured()
    with pytest.raises(finder.FinderError, match="switched off"):
        finder.ask(FRAME, "keys", opener=Opener("{}"))


def test_an_unknown_choice_falls_back_to_the_default(token_factory, monkeypatch):
    monkeypatch.setenv("ANDY_VISION", "Token_Factory")
    assert vision.choice() == "token-factory"
    monkeypatch.setenv("ANDY_VISION", "laser-eyes")
    assert vision.choice() == "token-factory"


def test_the_key_never_appears_in_an_error(token_factory):
    def broken(req, timeout=None):
        raise OSError(req.headers.get("Authorization", ""))
    out = vision.look(lambda: FRAME, opener=broken)
    assert "nb-key" not in out["error"] and "base64" not in out["error"]


def test_a_photo_comes_with_how_to_talk_about_it_and_the_suite_uses_the_same_words(token_factory, monkeypatch, tmp_path):
    import importlib.util
    from pathlib import Path

    import cv2

    from andy_companion import board

    photo = tmp_path / "p1.jpg"
    cv2.imwrite(str(photo), FRAME)
    monkeypatch.setattr(board, "photo_path", lambda pid: photo if pid == "p1" else None)
    out = vision.describe_photo("p1", opener=Opener("Two women on a beach."))
    assert out == {"description": "Two women on a beach.", "how": vision.PHOTO_HOW}
    assert "one open question" in vision.PHOTO_HOW and "only after a yes" in vision.PHOTO_HOW
    spec = importlib.util.spec_from_file_location("run_suite", Path(vision.__file__).parents[2] / "evals" / "run_suite.py")
    suite = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(suite)
    assert suite.PHOTO_HOW == vision.PHOTO_HOW


def test_the_profile_keeps_a_photo_story_only_with_a_yes():
    from pathlib import Path

    text = (Path(vision.__file__).parents[2] / "profiles" / "companion" / "profile.md").read_text()
    assert '"Shall I keep that' in text and "only after a yes, use remember" in text
    assert "Share it with family only\n  if they ask." in text
