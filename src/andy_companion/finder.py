"""Find something in the room: "Andy, where did I leave my glasses?"

Andy looks around and points with its head. It sweeps the room, looking a little down at tables
and shelves (SWEEP_DEG, PITCH_DEG), with moves of its own (body.look), and takes a camera frame at
each stop. An NVIDIA Nemotron vision model on Nebius (vision.eyes: Nemotron 3.5 Super VL on Token Factory
by default, or Nano VL on the person's own Serverless Endpoint) reads each frame
for the thing, in parallel, as structured output: seen or not, where across the frame (0 left to
1 right), and a few words for where it is ("on the table by the lamp").

Andy then turns its head to it (the frame's direction, plus the thing's offset from the centre,
through the camera's intrinsics, as body.person does). It holds there while it says where, and the
TV shows what Andy looked at: the four views, numbered in the order Andy turned, the one it chose marked
and the "where" words under it; when nothing was found, the four views, each "not seen", so the person
sees where Andy looked.

Privacy: the frames go only to Nebius, which keeps nothing (zero data retention), and are not kept there. The views shown on the
TV are small (VIEW_WIDTH, VIEW_QUALITY), live in the screen server's memory for two minutes
(screen_server.FRAME_FOR_S) and are never written to disk. The model is told never to describe people.
Nothing is logged but whether it was found.

Measuring it (PLAN B11): only when ANDY_FINDER_RECORD names a folder, each try is kept there for scoring by
evals/finder_eval.py: the four views, what the model said of each, the view Andy chose and the times. It is
off by default and meant for the founder's own test sessions; delete the folder after scoring.
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
VIEW_WIDTH, VIEW_QUALITY = 480, 70         # the TV's strip: small enough for four in memory, clear at a glance
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
    """One frame, read by the eyes (vision.eyes) for the thing."""
    from andy_companion import vision

    e = vision.eyes()
    why = vision.ready(e, opener)
    if why:
        raise FinderError(SWITCHED_OFF if why == vision.SWITCHED_OFF else why)
    image = "data:image/jpeg;base64," + base64.b64encode(vision.jpeg(frame)).decode()
    req = vision.request(e, [{"type": "text", "text": ASK.format(what=what)},
                             {"type": "image_url", "image_url": {"url": image}}], 120, 0,
                         {"response_format": {"type": "json_schema", "json_schema": {"name": "found", "schema": SCHEMA}}})
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


def record(what: str, frames: List[Any], results: List[Dict[str, Any]], chosen: Optional[int],
           seconds: Dict[str, float], folder: Optional[str] = None) -> Optional[str]:
    """Keep one try for scoring, only when ANDY_FINDER_RECORD names a folder. Returns the try's folder."""
    import time
    from pathlib import Path

    folder = folder or os.environ.get("ANDY_FINDER_RECORD", "")
    if not folder:
        return None
    try:
        from andy_companion import vision

        out = Path(folder).expanduser() / (time.strftime("try-%Y%m%d-%H%M%S") + f"-{int(time.time() * 1000) % 1000:03d}")
        out.mkdir(parents=True, exist_ok=True)
        os.chmod(out, 0o700)
        for i, f in enumerate(frames):
            if f is not None:
                (out / f"view-{i}.jpg").write_bytes(vision.jpeg(f))
        (out / "try.json").write_text(json.dumps({"what": what, "sweep_deg": list(SWEEP_DEG), "results": results,
                                                  "chosen": chosen, "seconds": seconds}, indent=1))
        return str(out)
    except Exception as e:   # recording is a help for measuring, never a reason to fail the person
        logger.info("finder: could not record the try (%s)", type(e).__name__)
        return None


def views_for_screen(frames: List[Any]) -> List[Optional[bytes]]:
    """Each view as a small JPEG for the TV's strip (None where the camera gave no picture)."""
    from andy_companion import vision

    out: List[Optional[bytes]] = []
    for f in frames:
        try:
            out.append(None if f is None else vision.jpeg(f, VIEW_WIDTH, VIEW_QUALITY))
        except Exception:
            out.append(None)
    return out


def post_views(views: List[Optional[bytes]], seen: List[bool], chosen: Optional[int],
               opener: Optional[Callable] = None) -> None:
    """The views, in the order Andy turned, to the screen server's memory (this computer only), for the TV."""
    from andy_companion import board, captions

    body = {"views": [None if v is None else base64.b64encode(v).decode() for v in views], "seen": list(seen),
            "chosen": chosen}
    req = urllib.request.Request(f"{captions.SCREEN}/api/views?t={board.tokens()['screen']}", method="POST",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=2):
            pass
    except Exception:
        pass   # the TV is a help, never a reason to stop


async def find(what: str, robot: Any, manager: Any, *, asker: Callable = ask, poster: Callable = post_views,
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
    from andy_companion.body import looking_at
    looking_at.set("room", sum(step.duration for step in looks))
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
    looked_s = clock() - start
    logger.info("finder: %s", "found" if i is not None else "not found")

    def show_views() -> None:     # first the views, then the card: the screen pairs a card with views just before it
        try:
            poster(views_for_screen(frames), [bool(r.get("seen")) for r in results], i)
        except Exception:
            pass   # the TV is a help, never a reason to stop

    if i is None:
        await asyncio.to_thread(record, what, frames, results, None, {"to_answer": round(looked_s, 2)})
        await asyncio.to_thread(show_views)
        board.show("looked", f"I couldn't see your {what}", [])
        return {"found": False, "what": what, "looked": len(frames),
                "how": (f"Say kindly that you looked around but couldn't see their {what} from where you are, and "
                        "that the screen shows where you looked. Offer to look again if they move something or "
                        "hold it nearer, or suggest one likely place to check. No guessing.")}
    yaw = target_yaw(math.radians(SWEEP_DEG[i]), results[i]["x"])
    manager.queue_move(queueable(look.HoldLook(robot.get_current_head_pose(), antennas, yaw, pitch, POINT_HOLD_S)))
    looking_at.set("pointing", POINT_HOLD_S + 1.0)
    await asyncio.to_thread(record, what, frames, results, i,
                            {"to_answer": round(looked_s, 2), "to_point": round(clock() - start, 2)})
    await asyncio.to_thread(show_views)
    where = results[i]["where"]
    board.show("seen", f"Your {what}", [{"summary": where}] if where else [])
    say = f"I think I see your {what}" + (f", {where}" if where else ", over there where I'm looking") + "."
    return {"found": True, "what": what, "where": where, "say": say,
            "how": ("You are pointing at it with your head now, and the picture is on the screen. Say exactly the words in 'say', 'I think' included, "
                    "then that it's on the screen too. Never say left or right: they may be facing you.")}
