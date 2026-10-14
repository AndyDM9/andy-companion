"""Find something in the room: "Andy, where did I leave my glasses?"

Andy looks around and points with its head. It sweeps the room, looking a little down at tables
and shelves (SWEEP_DEG, PITCH_DEG), with moves of its own (body.look), and takes a camera frame at
each stop. NVIDIA Nemotron Nano VL, on the person's own Nebius Serverless Endpoint, reads each frame
for the thing, in parallel, as structured output: seen or not, where across the frame (0 left to
1 right), and a few words for where it is ("on the table by the lamp").

Andy then turns its head to it (the frame's direction, plus the thing's offset from the centre,
through the camera's intrinsics, as body.person does). It holds there while it says where, and the
TV shows the frame it was seen in.

Privacy: the frames go only to the person's own endpoint and are not kept there. The one shown on the
TV lives in the screen server's memory for two minutes (screen_server.FRAME_FOR_S) and is never
written to disk. The model is told never to describe people. Nothing is logged but whether it was
found.
"""

from __future__ import annotations

import asyncio
import base64
import json
import logging
import math
import os
import re
import urllib.request
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger("andy.finder")

SWEEP_DEG = (55.0, 18.0, -18.0, -55.0)     # left to right, Pollen's convention (positive is left)
PITCH_DEG = 15.0                           # a little down, where things are put down
HOLD_S = 1.1
SETTLE_S = 0.6                             # into the hold, before the frame is taken
POINT_HOLD_S = 3.5
FX, CX = 1116.0, 953.0                     # body.person's defaults: about 81 degrees across
TIMEOUT_S = 40
ASK = ("You are the eyes of a home companion robot helping someone find their {what}. Look at this picture. "
       "Is their {what} visible? Answer as JSON: seen (true or false), x (where it is across the picture, "
       "0 at the left edge to 1 at the right edge), and where (a few plain words, like 'on the table by the "
       "lamp'), naming things near it and never left or right. Only say seen if you can actually see it. "
       "Never describe any person.")
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["seen", "x", "where"],
          "properties": {"seen": {"type": "boolean"}, "x": {"type": "number"}, "where": {"type": "string"}}}


class FinderError(Exception):
    pass


SWITCHED_OFF = "My eyes are switched off right now, so I can't look around."


def tidy_what(what: Any) -> str:
    what = " ".join(str(what or "").split())[:60].strip(" .?!")
    return re.sub(r"^(my|the|a|an|his|her|their)\s+", "", what, flags=re.I) or "things"


def ask(frame: Any, what: str, opener: Optional[Callable] = None) -> Dict[str, Any]:
    """One frame, read by Nemotron Nano VL for the thing."""
    from andy_companion import vision

    if not vision.configured():
        raise FinderError("My eyes in the cloud are switched off right now.")
    url = os.environ["ANDY_VISION_URL"].rstrip("/")
    if not url.startswith("https://"):
        raise FinderError("My eyes in the cloud need a secure (https) address.")
    if opener is None and not vision.reachable(url):   # stopped between demos: say so now, not after TIMEOUT_S
        raise FinderError(SWITCHED_OFF)
    image = "data:image/jpeg;base64," + base64.b64encode(vision.jpeg(frame)).decode()
    body = {"model": vision.MODEL, "max_tokens": 120, "temperature": 0,
            "messages": [{"role": "user", "content": [{"type": "text", "text": ASK.format(what=what)},
                                                      {"type": "image_url", "image_url": {"url": image}}]}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "found", "schema": SCHEMA}}}
    req = urllib.request.Request(url + "/v1/chat/completions", method="POST", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['ANDY_VISION_TOKEN']}",
                                          "Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT_S) as r:
            text = str(json.loads(r.read())["choices"][0]["message"]["content"])
    except Exception as e:   # never echo the request: it holds the picture
        if getattr(e, "code", None) in (404, 502, 503, 504):
            raise FinderError(SWITCHED_OFF) from None
        raise FinderError(f"My eyes in the cloud did not answer ({type(e).__name__}).") from None
    return parse(text)


def parse(text: str) -> Dict[str, Any]:
    """The model's JSON, made safe: x within 0..1, a short 'where', seen only if said plainly."""
    match = re.search(r"\{.*\}", text, re.S)
    try:
        data = json.loads(match.group(0) if match else text)
    except (ValueError, AttributeError):
        return {"seen": False, "x": 0.5, "where": ""}
    try:
        x = min(1.0, max(0.0, float(data.get("x", 0.5))))
    except (TypeError, ValueError):
        x = 0.5
    return {"seen": data.get("seen") is True, "x": x, "where": " ".join(str(data.get("where", "")).split())[:80]}


def target_yaw(sweep_yaw: float, x: float, fx: float = FX, cx: float = CX) -> float:
    """The head's world yaw toward something at `x` (0 left .. 1 right) in a frame taken at `sweep_yaw`."""
    return sweep_yaw + math.atan2(cx - x * 2 * cx, fx)


def best(results: List[Dict[str, Any]]) -> Optional[int]:
    """The frame that sees it most squarely (nearest the middle, where the view is sharpest)."""
    seen = [i for i, r in enumerate(results) if r.get("seen")]
    return min(seen, key=lambda i: abs(results[i]["x"] - 0.5)) if seen else None


def post_frame(jpeg: bytes, opener: Optional[Callable] = None) -> None:
    """The frame to the screen server's memory (this computer only), for the TV."""
    from andy_companion import board, captions

    req = urllib.request.Request(f"{captions.SCREEN}/api/frame?t={board.tokens()['screen']}", method="POST",
                                 data=jpeg, headers={"Content-Type": "image/jpeg"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=2):
            pass
    except Exception:
        pass   # the TV is a help, never a reason to stop


async def find(what: str, robot: Any, manager: Any, *, asker: Callable = ask, poster: Callable = post_frame,
               queueable: Optional[Callable] = None, sleep: Callable = asyncio.sleep,
               clock: Optional[Callable[[], float]] = None) -> Dict[str, Any]:
    """Sweep, look, point, show. Returns what Andy should say."""
    import time

    from andy_companion import board
    from andy_companion.body import look

    queueable = queueable or look.queueable
    clock = clock or time.monotonic
    what = tidy_what(what)
    try:
        antennas = tuple(float(a) for a in robot.get_current_joint_positions()[1][:2])
    except Exception:
        antennas = (0.0, 0.0)
    pitch = math.radians(PITCH_DEG)
    pose = robot.get_current_head_pose()
    looks = []
    for deg in SWEEP_DEG:
        step = look.HoldLook(pose, antennas, math.radians(deg), pitch, HOLD_S)
        looks.append(step)
        pose = step.end
    start = clock()
    for step in looks:
        manager.queue_move(queueable(step))
    frames: List[Any] = []
    elapsed = 0.0
    for step in looks:
        when = start + elapsed + step.turn_s + SETTLE_S
        await sleep(max(0.0, when - clock()))
        try:
            frame = robot.media.get_frame()
            frames.append(None if frame is None else frame.copy())
        except Exception:
            frames.append(None)
        elapsed += step.duration
    if not any(f is not None for f in frames):
        return {"error": "My camera did not give a picture just now."}
    # All frames are read at once: about one model call's time, not four.
    nothing = {"seen": False, "x": 0.5, "where": ""}

    async def none() -> Dict[str, Any]:
        return dict(nothing)

    answers = await asyncio.gather(*[asyncio.to_thread(asker, f, what) if f is not None else none() for f in frames],
                                   return_exceptions=True)
    for a in answers:
        if isinstance(a, FinderError):
            return {"error": str(a)}
    results = [a if isinstance(a, dict) else dict(nothing) for a in answers]
    i = best(results)
    logger.info("finder: %s", "found" if i is not None else "not found")
    if i is None:
        return {"found": False, "what": what, "looked": len(frames),
                "how": (f"Say kindly that you looked around but couldn't see their {what} from where you are. "
                        "Offer to look again if they move something or hold it nearer, or suggest one likely "
                        "place to check. No guessing.")}
    yaw = target_yaw(math.radians(SWEEP_DEG[i]), results[i]["x"])
    manager.queue_move(queueable(look.HoldLook(robot.get_current_head_pose(), antennas, yaw, pitch, POINT_HOLD_S)))
    try:
        from andy_companion import vision

        poster(vision.jpeg(frames[i]))
    except Exception:
        pass
    where = results[i]["where"]
    board.show("seen", f"Your {what}", [{"summary": where}] if where else [])
    say = f"I think I see your {what}" + (f", {where}" if where else ", over there where I'm looking") + "."
    return {"found": True, "what": what, "where": where, "say": say,
            "how": ("You are pointing at it with your head now, and the picture is on the screen. Say exactly the words in 'say', 'I think' included, "
                    "then that it's on the screen too. Never say left or right: they may be facing you.")}
