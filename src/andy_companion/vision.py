"""Andy's eyes: describe the camera picture with an NVIDIA Nemotron vision model on Nebius.

Two places, chosen by ANDY_VISION (PLAN B32):
- "token-factory", the default: NVIDIA Nemotron 3.5 Super VL on serverless Token Factory, with the same
  key as the conversation. Always on: nothing to start before a question, nothing paid while idle.
- "endpoint": NVIDIA Nemotron Nano 12B v2 VL on the person's own Nebius Serverless Endpoint
  (cloud/vision-endpoint.sh, ANDY_VISION_URL and ANDY_VISION_TOKEN): a smaller model on its own GPU,
  started before a demo and stopped after.
- "off": no eyes.

Used only when the person asks what Andy sees. The picture goes over HTTPS and is not kept there (the
account has zero data retention on) or here; the description comes back as text. People are never
identified.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import urllib.request
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import urlparse

from andy_companion import reading

TIMEOUT_S = 40
# Between demos the endpoint is stopped, and a stopped one may not answer at all: without this, a question
# would wait the full TIMEOUT_S. A running endpoint connects in well under a second.
CONNECT_S = 3.0
MODEL = "nemotron-vl"                                   # the endpoint's served name (cloud/vision-endpoint.sh)
TOKEN_FACTORY_MODEL = "nvidia/Nemotron-3.5-Super-VL"
TOKEN_FACTORY = "https://api.tokenfactory.nebius.com/v1/"
NAMES = {"token-factory": "NVIDIA Nemotron 3.5 Super VL on Nebius Token Factory",
         "endpoint": "NVIDIA Nemotron Nano 12B v2 VL on a Nebius Serverless Endpoint"}
PROMPT = ("You are the eyes of a home companion robot, talking to an older adult. Describe what is in "
          "this picture in two or three short, plain sentences, most important first. {ask} Never say "
          "who a person is, or guess their age, health or mood; describe only what is there. If text is "
          "visible, mention it briefly. If the picture is too dark or blurry, say so.")


class VisionError(Exception):
    pass


def choice() -> str:
    """Which eyes ANDY_VISION asks for: 'token-factory' (the default), 'endpoint' or 'off'."""
    c = os.environ.get("ANDY_VISION", "").strip().lower().replace("_", "-")
    return c if c in ("token-factory", "endpoint", "off") else "token-factory"


def eyes() -> Optional[Dict[str, Any]]:
    """Where to send a picture: the full chat address, the bearer token, the model and any extra body
    fields; None when the eyes are off or their key is missing. The token is never logged or shown."""
    c = choice()
    if c == "endpoint":
        url, token = os.environ.get("ANDY_VISION_URL", ""), os.environ.get("ANDY_VISION_TOKEN", "")
        if not (url and token):
            return None
        return {"name": c, "url": url.rstrip("/") + "/v1/chat/completions", "token": token, "model": MODEL,
                "extra": {}, "may_be_stopped": True}
    key = os.environ.get("NEBIUS_API_KEY", "")
    if c == "off" or not key:
        return None
    base = os.environ.get("NEBIUS_BASE_URL", TOKEN_FACTORY).rstrip("/")
    return {"name": c, "url": base + "/chat/completions", "token": key,
            "model": os.environ.get("ANDY_VISION_MODEL", TOKEN_FACTORY_MODEL),
            # Super VL reasons first unless told not to: a plain answer is what a question in a room needs.
            "extra": {"chat_template_kwargs": {"enable_thinking": False}}, "may_be_stopped": False}


def name() -> str:
    """The eyes in use, in words, for the hood page and the doctor ('off' when there are none)."""
    e = eyes()
    return NAMES[e["name"]] if e else "off"


def configured() -> bool:
    return eyes() is not None


def request(e: Dict[str, Any], content: List[Dict[str, Any]], max_tokens: int, temperature: float,
            extra: Optional[Dict[str, Any]] = None) -> urllib.request.Request:
    """One chat request to the eyes in `e`, with the picture in `content`."""
    body = {"model": e["model"], "max_tokens": max_tokens, "temperature": temperature,
            "messages": [{"role": "user", "content": content}], **e["extra"], **(extra or {})}
    return urllib.request.Request(e["url"], method="POST", data=json.dumps(body).encode(),
                                  headers={"Authorization": f"Bearer {e['token']}", "Content-Type": "application/json"})


def reachable(url: str, connect: Callable = socket.create_connection) -> bool:
    """Whether the endpoint takes a connection within CONNECT_S. Only a connection: nothing is sent."""
    parts = urlparse(url)
    try:
        connect((parts.hostname, parts.port or 443), timeout=CONNECT_S).close()
    except (OSError, ValueError, TypeError):
        return False
    return True


SWITCHED_OFF = "My eyes are switched off right now, so I can't see. They can be turned on from the computer."
# How to talk about a photo (PLAN B35): one open question, and a story kept only after a yes.
PHOTO_HOW = ("Say in one or two warm sentences what is in it, then ask one open question about it: where it was taken, or "
             "what was happening. Offer nothing else yet. When they tell you its story, say one warm sentence about it, then "
             "ask 'Shall I keep that story?'; only after a yes, use remember with one short line in their words.")


def jpeg(frame: Any, width: int = 768, quality: int = 85) -> bytes:
    import cv2

    h, w = frame.shape[:2]
    if w > width:
        frame = cv2.resize(frame, (width, int(h * width / w)), interpolation=cv2.INTER_AREA)
    ok, data = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
    if not ok:
        raise VisionError("The picture could not be prepared.")
    return data.tobytes()


def ready(e: Optional[Dict[str, Any]], opener: Optional[Callable] = None) -> str:
    """Why a picture can't be sent now ('' when it can): eyes off, an address that isn't https, or an endpoint
    that is stopped between demos (said at once, not after TIMEOUT_S)."""
    if e is None:
        return "My eyes in the cloud are switched off right now."
    if not e["url"].startswith("https://"):   # the token and the picture never travel unencrypted
        return "My eyes in the cloud need a secure (https) address."
    if e["may_be_stopped"] and opener is None and not reachable(e["url"]):   # an opener is a test's stand-in
        return SWITCHED_OFF
    return ""


def describe(frame: Any, question: str = "", opener: Optional[Callable] = None) -> str:
    e = eyes()
    why = ready(e, opener)
    if why:
        raise VisionError(why)
    image = "data:image/jpeg;base64," + base64.b64encode(jpeg(frame)).decode()
    ask = f"They asked: {' '.join(question.split())[:200]}" if question.strip() else ""
    req = request(e, [{"type": "text", "text": PROMPT.format(ask=ask)},
                      {"type": "image_url", "image_url": {"url": image}}], 160, 0.2)
    try:
        with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT_S) as r:
            data = json.loads(r.read())
        return " ".join(str(data["choices"][0]["message"]["content"]).split())[:800]
    except Exception as e:   # never echo the request: it holds the picture
        if getattr(e, "code", None) in (404, 502, 503, 504):   # a stopped endpoint answers like this
            raise VisionError(SWITCHED_OFF) from None
        raise VisionError(f"My eyes in the cloud did not answer ({type(e).__name__}).") from None


def look(get_frame: Callable[[], Any], question: str = "", opener: Optional[Callable] = None) -> dict:
    try:
        frame = reading.best_frame(get_frame)
    except Exception:   # the camera itself failed: say so plainly, never crash the turn
        return {"error": "My camera did not give a picture just now."}
    if frame is None:
        return {"error": "The camera did not give a picture."}
    try:
        return {"description": describe(frame, question, opener)}
    except VisionError as e:
        return {"error": str(e)}


def describe_photo(photo_id: str, opener: Optional[Callable] = None) -> dict:
    """Describe a photo family sent (already on Andy's computer), with the same endpoint."""
    import cv2

    from andy_companion import board

    path = board.photo_path(photo_id)
    if path is None:
        return {"error": "I can't find that photo any more."}
    frame = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if frame is None:   # imread gives None, not an error, for a file it cannot read
        return {"error": "I couldn't open that photo."}
    try:
        return {"description": describe(frame, "This is a photo a family member sent.", opener), "how": PHOTO_HOW}
    except VisionError as e:
        return {"error": str(e)}
