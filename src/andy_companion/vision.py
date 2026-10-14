"""Andy's eyes: describe the camera picture with NVIDIA Nemotron Nano VL on the person's own Nebius
Serverless Endpoint (cloud/vision-endpoint.sh).

Used only when the person asks what Andy sees. The picture goes to that endpoint over HTTPS and is
not kept there or here; the description comes back as text. People are never identified.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import urllib.request
from typing import Any, Callable, Optional
from urllib.parse import urlparse

from andy_companion import reading

TIMEOUT_S = 40
# Between demos the endpoint is stopped, and a stopped one may not answer at all: without this, a question
# would wait the full TIMEOUT_S. A running endpoint connects in well under a second.
CONNECT_S = 3.0
MODEL = "nemotron-vl"
PROMPT = ("You are the eyes of a home companion robot, talking to an older adult. Describe what is in "
          "this picture in two or three short, plain sentences, most important first. {ask} Never say "
          "who a person is, or guess their age, health or mood; describe only what is there. If text is "
          "visible, mention it briefly. If the picture is too dark or blurry, say so.")


class VisionError(Exception):
    pass


def configured() -> bool:
    return bool(os.environ.get("ANDY_VISION_URL") and os.environ.get("ANDY_VISION_TOKEN"))


def reachable(url: str, connect: Callable = socket.create_connection) -> bool:
    """Whether the endpoint takes a connection within CONNECT_S. Only a connection: nothing is sent."""
    parts = urlparse(url)
    try:
        connect((parts.hostname, parts.port or 443), timeout=CONNECT_S).close()
    except (OSError, ValueError, TypeError):
        return False
    return True


SWITCHED_OFF = "My eyes are switched off right now, so I can't see. They can be turned on from the computer."


def jpeg(frame: Any, width: int = 768) -> bytes:
    import cv2

    h, w = frame.shape[:2]
    if w > width:
        frame = cv2.resize(frame, (width, int(h * width / w)), interpolation=cv2.INTER_AREA)
    ok, data = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 85])
    if not ok:
        raise VisionError("The picture could not be prepared.")
    return data.tobytes()


def describe(frame: Any, question: str = "", opener: Optional[Callable] = None) -> str:
    if not configured():
        raise VisionError("My eyes in the cloud are switched off right now.")
    url = os.environ["ANDY_VISION_URL"].rstrip("/")
    if not url.startswith("https://"):   # the token and the picture never travel unencrypted
        raise VisionError("My eyes in the cloud need a secure (https) address.")
    if opener is None and not reachable(url):   # an opener is a test's stand-in for the network
        raise VisionError(SWITCHED_OFF)
    image = "data:image/jpeg;base64," + base64.b64encode(jpeg(frame)).decode()
    ask = f"They asked: {' '.join(question.split())[:200]}" if question.strip() else ""
    body = {"model": MODEL, "max_tokens": 160, "temperature": 0.2,
            "messages": [{"role": "user", "content": [{"type": "text", "text": PROMPT.format(ask=ask)},
                                                      {"type": "image_url", "image_url": {"url": image}}]}]}
    req = urllib.request.Request(url + "/v1/chat/completions", method="POST", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['ANDY_VISION_TOKEN']}",
                                          "Content-Type": "application/json"})
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
        return {"description": describe(frame, "This is a photo a family member sent.", opener)}
    except VisionError as e:
        return {"error": str(e)}
