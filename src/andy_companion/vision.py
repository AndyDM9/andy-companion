"""Andy's eyes: describe the camera picture with an NVIDIA Nemotron vision model on Nebius.

Two places, chosen by ANDY_VISION (PLAN B32):
- "token-factory", the default: NVIDIA Nemotron 3.5 Super VL on serverless Token Factory, with the same
  key as the conversation. Always on: nothing to start before a question, nothing paid while idle.
- "endpoint": NVIDIA Nemotron Nano 12B v2 VL on the person's own Nebius Serverless Endpoint
  (cloud/vision-endpoint.sh, ANDY_VISION_URL and ANDY_VISION_TOKEN): a smaller model on its own GPU,
  started before a demo and stopped after.
- "local": NVIDIA Cosmos Reason 2 2B served by vLLM on this computer (local-eyes/run.sh, decision 0015): no
  network, so a picture never leaves the house; slower and smaller.
- "off": no eyes.

ANDY_VISION_FALLBACK=local sends a picture to Cosmos here when the chosen eyes can't be reached (the network is
down, or the endpoint stopped), if it is running; otherwise nothing changes.

Used only when the person asks what Andy sees. The picture goes over HTTPS and is not kept there (the
account has zero data retention on) or here; the description comes back as text. People are never
identified.
"""

from __future__ import annotations

import base64
import json
import os
import socket
import urllib.error
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
LOCAL_MODEL = "cosmos-reason2"                          # local-eyes/run.sh's served name
LOCAL = "http://127.0.0.1:8095"
LOCAL_DEFAULT = "nvidia/Cosmos-Reason2-2B"              # ANDY_LOCAL_EYES_MODEL, read by local-eyes/run.sh too
NAMES = {"token-factory": "NVIDIA Nemotron 3.5 Super VL on Nebius Token Factory",
         "endpoint": "NVIDIA Nemotron Nano 12B v2 VL on a Nebius Serverless Endpoint",
         "local": "NVIDIA Cosmos Reason 2 2B on this computer"}
# The eyes that answered last ("" before any picture): the hood names these, so a fallback is never hidden.
_used = ""
PROMPT = ("You are the eyes of a home companion robot, talking to an older adult. {ask} If they ask about "
          "something they are holding or showing you, say first what that thing is, as specifically as you can "
          "(what it is, its colour, any words on it); look for the nearest thing, often in a hand. Never say where "
          "anything is in the picture. "
          "Otherwise describe what is in the picture in two or three short, plain sentences, most important first. "
          "Never say who a person is, or guess their age, health or mood; describe only what is there. If text is "
          "visible, mention it briefly. If the picture is too dark or blurry, say so.")
# The camera's view at 1280 across, and its middle at full detail beside it: shrunk to 768 across, a small toy held up
# became "a computer mouse" (2026-10-25). In a test, a toy gorilla 130 px tall in a 1920 px room was named 2 of 2 this
# way, 1 of 2 at 768; about 0.7 s more. A family photo is the whole picture, so it goes alone.
VIEW_WIDTH = 1280
MIDDLE = (0.25, 0.75, 0.2, 0.95)                       # left, right, top, bottom: where a thing held up usually is
MIDDLE_WIDTH = 1024
MIDDLE_NOTE = (" The second picture is the middle of the first at full detail: use it for small things and anything "
               "held up, and describe the scene once.")


class VisionError(Exception):
    pass


def choice() -> str:
    """Which eyes ANDY_VISION asks for: 'token-factory' (the default), 'endpoint', 'local' or 'off'."""
    c = os.environ.get("ANDY_VISION", "").strip().lower().replace("_", "-")
    return c if c in ("token-factory", "endpoint", "local", "off") else "token-factory"


def local_eyes() -> Dict[str, Any]:
    """Cosmos Reason 2 2B on this computer (local-eyes/run.sh): no token, and only ever this computer's address."""
    url = os.environ.get("ANDY_LOCAL_EYES_URL", LOCAL).rstrip("/")
    return {"name": "local", "url": url + "/v1/chat/completions", "token": "", "model": LOCAL_MODEL,
            "extra": {}, "may_be_stopped": True}


def fallback(e: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """The eyes to try when `e` can't be reached: Cosmos here, if ANDY_VISION_FALLBACK=local and `e` isn't it."""
    if os.environ.get("ANDY_VISION_FALLBACK", "").strip().lower() != "local" or (e or {}).get("name") == "local":
        return None
    return local_eyes()


def eyes() -> Optional[Dict[str, Any]]:
    """Where to send a picture: the full chat address, the bearer token, the model and any extra body
    fields; None when the eyes are off or their key is missing. The token is never logged or shown."""
    c = choice()
    if c == "local":
        return local_eyes()
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
    if e and e["name"] == "local":
        return f"NVIDIA {local_size()} on this computer"
    return NAMES[e["name"]] if e else "off"


def local_size() -> str:
    """Which Cosmos local-eyes/run.sh serves, in words: 'Cosmos Reason 2 2B' unless ANDY_LOCAL_EYES_MODEL says 8B."""
    model = os.environ.get("ANDY_LOCAL_EYES_MODEL", LOCAL_DEFAULT)
    return "Cosmos Reason 2 8B" if "8b" in model.lower() else "Cosmos Reason 2 2B"


def used() -> str:
    """Which eyes answered the last picture ('token-factory', 'endpoint' or 'local'), else the ones chosen."""
    return _used or choice()


def configured() -> bool:
    return eyes() is not None


def request(e: Dict[str, Any], content: List[Dict[str, Any]], max_tokens: int, temperature: float,
            extra: Optional[Dict[str, Any]] = None) -> urllib.request.Request:
    """One chat request to the eyes in `e`, with the picture in `content`."""
    body = {"model": e["model"], "max_tokens": max_tokens, "temperature": temperature,
            "messages": [{"role": "user", "content": content}], **e["extra"], **(extra or {})}
    headers = {"Content-Type": "application/json"}
    if e["token"]:
        headers["Authorization"] = f"Bearer {e['token']}"
    return urllib.request.Request(e["url"], method="POST", data=json.dumps(body).encode(), headers=headers)


def unavailable(err: BaseException) -> bool:
    """Whether a failed call means the eyes couldn't be reached (worth the fallback), not that they refused it."""
    if isinstance(err, urllib.error.HTTPError):
        return err.code in (502, 503, 504)
    return isinstance(err, (urllib.error.URLError, TimeoutError, ConnectionError, socket.timeout))


def answer(e: Dict[str, Any], content: List[Dict[str, Any]], max_tokens: int, temperature: float,
           extra: Optional[Dict[str, Any]] = None, opener: Optional[Callable] = None) -> str:
    """The reply's text from the eyes in `e`; if they can't be reached, from the fallback (Cosmos here), when it
    is set and running. Raises what the call raised. Never logs or echoes the request: it holds the picture."""
    global _used
    try:
        text = _ask(e, content, max_tokens, temperature, extra, opener)
        _used = e["name"]
        return text
    except Exception as err:
        f = fallback(e)
        if f is None or not unavailable(err) or (opener is None and not reachable(f["url"])):
            raise
        text = _ask(f, content, max_tokens, temperature, extra, opener)
        _used = f["name"]
        return text


def _ask(e: Dict[str, Any], content: List[Dict[str, Any]], max_tokens: int, temperature: float,
         extra: Optional[Dict[str, Any]], opener: Optional[Callable]) -> str:
    req = request(e, content, max_tokens, temperature, extra)
    with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT_S) as r:
        return str(json.loads(r.read())["choices"][0]["message"]["content"])


def here(url: str) -> bool:
    """Whether an address is this computer's own, where a picture travels no network at all."""
    return urlparse(url).hostname in ("127.0.0.1", "localhost", "::1")


def reachable(url: str, connect: Callable = socket.create_connection) -> bool:
    """Whether the endpoint takes a connection within CONNECT_S. Only a connection: nothing is sent."""
    parts = urlparse(url)
    try:
        connect((parts.hostname, parts.port or (80 if parts.scheme == "http" else 443)), timeout=CONNECT_S).close()
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
    if not e["url"].startswith("https://") and not here(e["url"]):   # never unencrypted over a network
        return "My eyes in the cloud need a secure (https) address."
    if e["may_be_stopped"] and opener is None and not reachable(e["url"]):   # an opener is a test's stand-in
        return SWITCHED_OFF
    return ""


def middle(frame: Any) -> Any:
    """The middle of a camera view (MIDDLE), at full resolution."""
    h, w = frame.shape[:2]
    left, right, top, bottom = MIDDLE
    return frame[int(h * top):int(h * bottom), int(w * left):int(w * right)]


def describe(frame: Any, question: str = "", opener: Optional[Callable] = None, close: bool = True) -> str:
    """What is in a picture, in a few sentences; with `close`, the camera's view sent with its middle at full detail."""
    e = eyes()
    why = ready(e, opener)
    if why:
        raise VisionError(why)
    pictures = [jpeg(frame, VIEW_WIDTH)] + ([jpeg(middle(frame), MIDDLE_WIDTH, 90)] if close else [])
    ask = f"They asked: {' '.join(question.split())[:200]}" if question.strip() else ""
    content = [{"type": "text", "text": PROMPT.format(ask=ask) + (MIDDLE_NOTE if close else "")}]
    content += [{"type": "image_url", "image_url": {"url": "data:image/jpeg;base64," + base64.b64encode(p).decode()}}
                for p in pictures]
    try:
        return " ".join(answer(e, content, 160, 0.2, opener=opener).split())[:800]
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
        description = describe(frame, question, opener)
    except VisionError as e:
        return {"error": str(e)}
    record_look(frame, description, used())
    return {"description": description}


def record_look(frame: Any, description: str, eyes_used: str, folder: Optional[str] = None) -> Optional[str]:
    """Testing only, like the finder's tries: when ANDY_FINDER_RECORD names a folder, keep what "what do you see?"
    sent (the view and its middle, as sent) and what the eyes said, to see why a thing wasn't recognised (2026-10-25).
    Never the person's words. Off by default; the doctor warns while it is on; delete the folder after looking."""
    import json
    import time
    from pathlib import Path

    folder = folder or os.environ.get("ANDY_FINDER_RECORD", "")
    if not folder:
        return None
    try:
        out = Path(folder).expanduser() / (time.strftime("look-%Y%m%d-%H%M%S") + f"-{int(time.time() * 1000) % 1000:03d}")
        out.mkdir(parents=True, exist_ok=True)
        os.chmod(out, 0o700)
        (out / "view.jpg").write_bytes(jpeg(frame, VIEW_WIDTH))
        (out / "middle.jpg").write_bytes(jpeg(middle(frame), MIDDLE_WIDTH, 90))
        (out / "look.json").write_text(json.dumps({"said": description, "eyes": eyes_used,
                                                   "size": list(frame.shape[:2])}, indent=1))
        return str(out)
    except Exception:          # recording is a help for testing, never a reason to fail the person
        return None


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
        return {"description": describe(frame, "This is a photo a family member sent.", opener, close=False),
                "how": PHOTO_HOW}
    except VisionError as e:
        return {"error": str(e)}
