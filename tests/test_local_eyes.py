"""Decision 0015: NVIDIA Cosmos Reason 2 on this computer, as eyes chosen with ANDY_VISION=local or as the fallback
(ANDY_VISION_FALLBACK=local) when the eyes in the cloud can't be reached; and the hood names the eyes that answered."""

import io
import json
import urllib.error
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("cv2")

from andy_companion import finder, turns, vision  # noqa: E402

FRAME = np.full((48, 64, 3), 90, np.uint8)
ROOT = Path(__file__).resolve().parent.parent


class Opener:
    """Answers like the eyes; `down` makes every call to that address fail as `down` says."""

    def __init__(self, reply, down=None):
        self.reply, self.down, self.requests = reply, down or {}, []

    def __call__(self, req, timeout=None):
        self.requests.append((req.full_url, json.loads(req.data), dict(req.headers)))
        for host, err in self.down.items():
            if host in req.full_url:
                raise err
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": self.reply}}]}).encode())


@pytest.fixture
def eyes(monkeypatch):
    for k in ("ANDY_VISION", "ANDY_VISION_MODEL", "NEBIUS_BASE_URL", "ANDY_VISION_FALLBACK", "ANDY_LOCAL_EYES_URL", "ANDY_LOCAL_EYES_MODEL"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.setenv("NEBIUS_API_KEY", "nb-key")
    monkeypatch.setattr(vision, "_used", "")


OFFLINE = {"tokenfactory": urllib.error.URLError("no route to host")}


def test_local_when_chosen_stays_on_this_computer_with_no_token(eyes, monkeypatch):
    monkeypatch.setenv("ANDY_VISION", "local")
    op = Opener("A cup on a table.")
    assert vision.describe(FRAME, opener=op) == "A cup on a table."
    url, body, headers = op.requests[0]
    assert url == "http://127.0.0.1:8095/v1/chat/completions" and body["model"] == "cosmos-reason2"
    assert "Authorization" not in headers and "chat_template_kwargs" not in body
    assert vision.name() == "NVIDIA Cosmos Reason 2 2B on this computer" and vision.used() == "local"
    monkeypatch.setenv("ANDY_LOCAL_EYES_MODEL", "nvidia/Cosmos-Reason2-8B")      # served by run.sh from the same setting
    assert vision.name() == "NVIDIA Cosmos Reason 2 8B on this computer"


def test_plain_http_is_allowed_only_to_this_computer(eyes, monkeypatch):
    monkeypatch.setenv("ANDY_VISION", "local")
    monkeypatch.setenv("ANDY_LOCAL_EYES_URL", "http://192.168.1.20:8095")
    with pytest.raises(vision.VisionError, match="secure"):
        vision.describe(FRAME, opener=Opener("x"))
    assert vision.here("http://localhost:8095/v1") and not vision.here("http://10.0.0.2:8095")


def test_fallback_cannot_bypass_the_primary_transport_rule(eyes, monkeypatch):
    monkeypatch.setenv("ANDY_VISION_FALLBACK", "local")
    monkeypatch.setenv("ANDY_LOCAL_EYES_URL", "http://192.168.1.20:8095")
    op = Opener("must not be sent", down=OFFLINE)
    with pytest.raises(vision.VisionError):
        vision.describe(FRAME, opener=op)
    assert len(op.requests) == 1
    assert "tokenfactory" in op.requests[0][0]


@pytest.mark.parametrize("mode", ["local", "token-factory"])
def test_local_label_cannot_send_pictures_to_a_remote_https_host(eyes, monkeypatch, mode):
    monkeypatch.setenv("ANDY_VISION", mode)
    monkeypatch.setenv("ANDY_VISION_FALLBACK", "local")
    monkeypatch.setenv("ANDY_LOCAL_EYES_URL", "https://remote.example.invalid")
    op = Opener("must not be sent", down=OFFLINE)
    with pytest.raises(vision.VisionError):
        vision.describe(FRAME, opener=op)
    assert not any("remote.example.invalid" in url for url, _, _ in op.requests)


def test_stopped_optional_endpoint_goes_directly_to_ready_local_eyes(eyes, monkeypatch):
    monkeypatch.setenv("ANDY_VISION", "endpoint")
    monkeypatch.setenv("ANDY_VISION_URL", "https://endpoint.example.invalid")
    monkeypatch.setenv("ANDY_VISION_TOKEN", "invented-endpoint-token")
    monkeypatch.setenv("ANDY_VISION_FALLBACK", "local")
    monkeypatch.setattr(vision, "reachable", lambda url: "127.0.0.1:8095" in url)
    op = Opener("A cup on the table.")
    monkeypatch.setattr(vision.urllib.request, "urlopen", op)
    assert vision.describe(FRAME) == "A cup on the table."
    assert len(op.requests) == 1 and op.requests[0][0].startswith("http://127.0.0.1:8095/")
    assert "Authorization" not in op.requests[0][2] and vision.used() == "local"


@pytest.mark.parametrize("provider,falls_back", [("endpoint", True), ("token-factory", False)])
def test_only_optional_endpoint_404_is_treated_as_stopped(eyes, monkeypatch, provider, falls_back):
    monkeypatch.setenv("ANDY_VISION", provider)
    monkeypatch.setenv("ANDY_VISION_URL", "https://endpoint.example.invalid")
    monkeypatch.setenv("ANDY_VISION_TOKEN", "invented-endpoint-token")
    monkeypatch.setenv("ANDY_VISION_FALLBACK", "local")
    host = "endpoint.example.invalid" if provider == "endpoint" else "tokenfactory"
    op = Opener("A cup.", down={host: urllib.error.HTTPError("u", 404, "not found", {}, None)})
    if falls_back:
        assert vision.describe(FRAME, opener=op) == "A cup." and vision.used() == "local"
    else:
        with pytest.raises(vision.VisionError):
            vision.describe(FRAME, opener=op)
        assert len(op.requests) == 1


def test_offline_the_fallback_answers_and_the_hood_says_so(eyes, monkeypatch):
    monkeypatch.setenv("ANDY_VISION_FALLBACK", "local")
    op = Opener("A pair of glasses on a chair.", down=OFFLINE)
    assert vision.describe(FRAME, opener=op) == "A pair of glasses on a chair."
    assert [u for u, _, _ in op.requests] == ["https://api.tokenfactory.nebius.com/v1/chat/completions",
                                              "http://127.0.0.1:8095/v1/chat/completions"]
    assert "Authorization" not in op.requests[1][2]                # the Token Factory key never goes to it
    assert vision.used() == "local"
    assert turns.where()["describe_view"] == "Cosmos Reason 2 2B, on this computer"
    monkeypatch.setenv("ANDY_LOCAL_EYES_MODEL", "nvidia/Cosmos-Reason2-8B")    # the hood names the model served
    assert turns.where()["find_object"].startswith("Cosmos Reason 2 8B, on this computer, four views")
    vision.describe(FRAME, opener=Opener("A cup."))                  # back online: the cloud's name again
    assert turns.where()["describe_view"] == "Nemotron 3.5 Super VL, Token Factory"


def test_the_finder_falls_back_with_the_same_structured_question(eyes, monkeypatch):
    monkeypatch.setenv("ANDY_VISION_FALLBACK", "local")
    op = Opener('{"seen": true, "x": 0.3, "where": "on the chair"}', down=OFFLINE)
    assert finder.ask(FRAME, "glasses", opener=op)["where"] == "on the chair"
    cloud, here = op.requests[0][1], op.requests[1][1]
    assert here["response_format"] == cloud["response_format"] and here["model"] == "cosmos-reason2"


@pytest.mark.parametrize("err, falls_back", [
    (urllib.error.URLError("no route"), True),
    (TimeoutError(), True),
    (urllib.error.HTTPError("u", 503, "unavailable", {}, None), True),
    (urllib.error.HTTPError("u", 401, "unauthorised", {}, None), False),     # refused, not unreachable
    (urllib.error.HTTPError("u", 400, "bad request", {}, None), False),
])
def test_only_unreachable_eyes_fall_back(eyes, monkeypatch, err, falls_back):
    monkeypatch.setenv("ANDY_VISION_FALLBACK", "local")
    op = Opener("A cup.", down={"tokenfactory": err})
    if falls_back:
        assert vision.describe(FRAME, opener=op) == "A cup."
    else:
        with pytest.raises(vision.VisionError):
            vision.describe(FRAME, opener=op)
        assert len(op.requests) == 1


def test_without_the_fallback_nothing_changes(eyes):
    op = Opener("A cup.", down=OFFLINE)
    with pytest.raises(vision.VisionError, match="did not answer"):
        vision.describe(FRAME, opener=op)
    assert len(op.requests) == 1


def test_a_fallback_that_isnt_running_is_not_tried(eyes, monkeypatch):
    monkeypatch.setenv("ANDY_VISION_FALLBACK", "local")
    monkeypatch.setattr(vision, "reachable", lambda url: False)
    calls = []

    def urlopen(req, timeout=None):
        calls.append(req.full_url)
        raise urllib.error.URLError("no route")

    monkeypatch.setattr(vision.urllib.request, "urlopen", urlopen)
    with pytest.raises(urllib.error.URLError):
        vision.answer(vision.eyes(), [{"type": "text", "text": "hi"}], 10, 0)
    assert calls == ["https://api.tokenfactory.nebius.com/v1/chat/completions"]


def test_the_server_listens_only_here_and_logs_no_requests():
    command = (ROOT / "local-eyes" / "run.sh").read_text().split("\nexec ", 1)[1]
    assert "--host 127.0.0.1" in command and '"${ANDY_LOCAL_EYES_MODEL:-nvidia/Cosmos-Reason2-2B}"' in command
    assert "--served-model-name cosmos-reason2" in command and "--enable-log-requests" not in command


def test_andys_process_loads_the_offline_eyes_settings_and_the_supervisor_the_models_name():
    from andy_companion import app_mode

    assert {"ANDY_VISION_FALLBACK", "ANDY_LOCAL_EYES_URL", "ANDY_LOCAL_EYES_MODEL"} <= set(app_mode.APP_KEYS)
    assert "ANDY_LOCAL_EYES_MODEL" in app_mode.SUPERVISOR_KEYS and "ANDY_VISION_FALLBACK" not in app_mode.SUPERVISOR_KEYS


def test_a_turn_that_looked_tells_the_screen_which_eyes_answered(eyes, monkeypatch):
    # Andy's process: the turn says which eyes answered, by name only.
    monkeypatch.setattr(vision, "_used", "local")
    t = iter(range(100))
    clock = turns.TurnClock(clock=lambda: next(t), wall=lambda: 0)
    for reason in ("user_speech_stopped", "user_transcription_completed"):
        clock.mark(reason)
    clock.tool("find_object", 4.8)
    clock.mark("assistant_audio_delta")
    turn = clock.mark("assistant_transcript_done")
    assert turn["eyes"] == "local"

    # The supervisor's process, where the screen runs and vision.used() never saw the fallback.
    from andy_companion import screen_server

    monkeypatch.setattr(vision, "_used", "")
    monkeypatch.setattr(screen_server, "_eyes", {"used": ""})
    monkeypatch.setattr(screen_server, "_turns", type(screen_server._turns)(maxlen=40))
    monkeypatch.setenv("ANDY_LOCAL_EYES_MODEL", "nvidia/Cosmos-Reason2-8B")
    assert screen_server.hood_state()["where"]["find_object"].startswith("Nemotron 3.5 Super VL")
    screen_server.add_turn(json.loads(json.dumps(turn)))
    assert screen_server.hood_state()["where"]["find_object"].startswith("Cosmos Reason 2 8B, on this computer")
    screen_server.add_turn({**turn, "eyes": "Cosmos Reason 2 8B, said a stranger"})    # not one of the names: ignored
    assert screen_server._eyes["used"] == "local"
    screen_server.add_turn({**turn, "eyes": "token-factory"})                          # back online
    assert screen_server.hood_state()["where"]["find_object"].startswith("Nemotron 3.5 Super VL")
