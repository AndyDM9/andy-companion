"""Find something in the room: "Andy, where did I leave my glasses?"

Andy looks around and points with its head. It sweeps the room, looking a little down at tables
and shelves (SWEEP_DEG, PITCH_DEG), with moves of its own (body.look), and takes a camera frame at
each stop. An NVIDIA Nemotron vision model on Nebius (vision.eyes: Nemotron 3.5 Super VL on Token Factory
by default, or Nano VL on the person's own Serverless Endpoint) reads each frame
for the thing, in parallel, as structured output: seen or not, where across the frame (0 left to
1 right), and a few words for where it is ("on the table by the lamp").

Zooming in (PLAN B44, 2026-10-20): each view is read as six overlapping tiles at the camera's full resolution
(3 across, 2 down), never shrunk, since a pair of glasses across a room is 50 to 80 pixels wide in a 1080p frame and
a 768-pixel copy loses it: at the desk, the shrunk frame found a real pair of reading glasses in 0 of 9 frames, the
tiles in 9 of 9, with no false sighting in 9 frames without them (evals/zoom_check.py). Then Andy looks closer: it
turns its head straight at the best sighting, lets the picture settle, and asks again about a close-up from the
middle of the lens, where it is sharpest; only a plain "yes" there counts, and a "no" moves on to the next sighting
(the peripheral-then-foveal search of robot vision, and Zoom-Refine's crop-and-check for vision models). No
sharpening or "enhance": the research found no gain for these models, and more real pixels beat filters.
ANDY_FINDER_ZOOM=off goes back to one shrunk frame per view, for comparison.

Andy then turns its head to it (the frame's direction, plus the thing's offset from the centre,
through the camera's intrinsics, as body.person does). It holds there while it says where, and the
TV shows what Andy looked at: the four views, numbered in the order Andy turned, the one it chose marked
and the "where" words under it; when nothing was found, the four views, each "not seen", so the person
sees where Andy looked.

Privacy: the frames go only to Nebius, which keeps nothing (zero data retention), and are not kept there. The views shown on the
TV are small (VIEW_WIDTH, VIEW_QUALITY), live in the screen server's memory for two minutes
(screen_server.FRAME_FOR_S) and are never written to disk. The model is told never to describe people.
Nothing is logged but whether it was found, how many places and closer looks, and the time.

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
CY = 542.0                                 # the middle of a 1080-line frame, for how far down something is
TILES = (3, 2)                             # columns and rows of the zoomed tiles in each view
OVERLAP = 0.15                             # so a thing on a tile's edge is whole in its neighbour
TILE_WIDTH, TILE_QUALITY = 1024, 90        # tiles are sent at their own size (never shrunk), JPEG quality 90
CLOSER_HOLD_S = 1.2                        # looking closer: the turn, then still for the close-up
CLOSE_UP = 0.5                             # the close-up: the middle half of the frame across and down
MAX_CLOSER = 2                             # sightings looked at closer before saying it couldn't be seen
SAME_PLACE_DEG = 6.0                       # sightings this close together are one thing
ARRIVED_DEG = 2.5                          # the head is where it was sent when within this of it
REACH_YAW_DEG, REACH_PITCH_DEG = 60.0, 35.0  # where the head can turn without the body (Pollen: 65 from the body)
# Past the head's reach Andy turns its body to look (2026-10-25): Pollen's kinematics keep the head within 65 degrees of
# the base by turning the base (automatic body yaw, the daemon's default, up to 160), so a look sent further turns the
# whole robot. At home every miss was a chair about 74 degrees to the side, seen by the sweep but looked at and pointed
# at from 60 (2026-10-20). Covers all the sweep sees (about 95); ANDY_FINDER_TURN=off keeps the head's own reach.
TURN_YAW_DEG = 110.0
WAIT_ARRIVE_S, POLL_S = 1.5, 0.1           # how long to wait for a head that started its move late
VIEW_WIDTH, VIEW_QUALITY = 480, 70         # the TV's strip: small enough for four in memory, clear at a glance
ASK = ("You are the eyes of a home companion robot helping someone find their {what}. Look at this picture. "
       "Is their {what} visible? Answer as JSON: seen (true or false), x (where it is across the picture, "
       "0 at the left edge to 1 at the right edge), and where (a few plain words, like 'on the table by the "
       "lamp'), naming things near it and never left or right. Only say seen if you can actually see it. "
       "Never describe any person. Also give y, where it is down the picture, 0 at the top to 1 at the bottom. "
       "Only the real thing in the room counts: a picture of it on a TV, monitor, phone, screen or photo is not it.")
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["seen", "x", "y", "where"],
          "properties": {"seen": {"type": "boolean"}, "x": {"type": "number"}, "y": {"type": "number"},
                         "where": {"type": "string"}}}
# Looking closer: one strict question about the close-up. Only "yes" counts (a model's own confidence is poorly
# calibrated, so a second look at a closer picture is the check, not a score).
CHECK = ("You are the eyes of a home companion robot. It has turned to look closely at something that may be the "
         "person's {what}. Look at this close-up. Is it clearly their {what}? Answer as JSON: answer ('yes', 'no' or "
         "'unsure'), x and y (where it is, 0 to 1 across and down), and where (a few plain words naming things near "
         "it, never left or right). Say yes only if you are sure. A picture of it on a TV, monitor, phone, screen or "
         "photo is not it: say no. Never describe any person.")
CHECK_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["answer", "x", "y", "where"],
                "properties": {"answer": {"type": "string", "enum": ["yes", "no", "unsure"]}, "x": {"type": "number"},
                               "y": {"type": "number"}, "where": {"type": "string"}}}


class FinderError(Exception):
    pass


SWITCHED_OFF = "My eyes are switched off right now, so I can't look around."


def tidy_what(what: Any) -> str:
    what = " ".join(str(what or "").split())[:60].strip(" .?!")
    return re.sub(r"^(my|the|a|an|his|her|their)\s+", "", what, flags=re.I) or "things"


def zoom() -> bool:
    """Zoomed tiles and a closer look (the default), or one shrunk frame per view (ANDY_FINDER_ZOOM=off)."""
    return os.environ.get("ANDY_FINDER_ZOOM", "on").strip().lower() not in ("off", "0", "no", "false")


def turn() -> bool:
    """Turning the body to look past the head's reach (the default), or the head alone (ANDY_FINDER_TURN=off)."""
    return os.environ.get("ANDY_FINDER_TURN", "on").strip().lower() not in ("off", "0", "no", "false")


def yaw_reach_deg() -> float:
    """How far to the side Andy looks closer and points: with its body (TURN_YAW_DEG), or its head alone."""
    return TURN_YAW_DEG if turn() else REACH_YAW_DEG


def aim(place: Dict[str, Any]) -> tuple:
    """Where to look for a place (yaw, pitch, radians): straight at it, as far as Andy can turn and tilt. The robot,
    the simulation (sim/finder_sim.py) and its film (sim/replay.py) all aim this way."""
    return within(place["yaw"], yaw_reach_deg()), within(place["pitch"], REACH_PITCH_DEG)


def ask(frame: Any, what: str, opener: Optional[Callable] = None, check: bool = False) -> Dict[str, Any]:
    """One picture (a tile, or a close-up when `check`), read by the eyes (vision.eyes) for the thing."""
    from andy_companion import vision

    e = vision.eyes()
    why = vision.ready(e, opener)
    if why:
        raise FinderError(SWITCHED_OFF if why == vision.SWITCHED_OFF else why)
    picture = vision.jpeg(frame, TILE_WIDTH, TILE_QUALITY) if zoom() else vision.jpeg(frame)
    image = "data:image/jpeg;base64," + base64.b64encode(picture).decode()
    prompt, schema, name = (CHECK, CHECK_SCHEMA, "closer") if check else (ASK, SCHEMA, "found")
    try:
        text = vision.answer(e, [{"type": "text", "text": prompt.format(what=what)},
                                 {"type": "image_url", "image_url": {"url": image}}], 120, 0,
                             {"response_format": {"type": "json_schema", "json_schema": {"name": name, "schema": schema}}},
                             opener)
    except Exception as e:   # never echo the request: it holds the picture
        if getattr(e, "code", None) in (404, 502, 503, 504):
            raise FinderError(SWITCHED_OFF) from None
        raise FinderError(f"My eyes in the cloud did not answer ({type(e).__name__}).") from None
    return parse_check(text) if check else parse(text)


def look_closer(picture: Any, what: str, opener: Optional[Callable] = None) -> Dict[str, Any]:
    """The close-up check, on a close-up already cut (close_up) from a frame taken with the head turned at a sighting."""
    return ask(picture, what, opener, check=True)


# A sighting described as on a screen is a picture, not the thing: Andy's own TV shows the last close-up for two
# minutes, and the founder's recorded try saw glasses "in the calendar widget on the screen" (2026-10-20). Only *on*
# or *in* a screen or picture counts: until 2026-10-25 any mention did, so real glasses "near the keyboard, phone and
# headphones", or in front of the monitors, were thrown away, in the sweep and up close (the founder's desk).
_SHOWN_ON = (r"(?:screen|monitor|tv|television|display|widget|photo|photograph|picture|poster|wallpaper|video|"
             r"(?:phone|tablet|laptop|computer)(?:'s)?\s+screen)")
ON_SCREEN = re.compile(r"\b(?:on|in|inside|within|displayed on|shown on|showing on)\s+(?:the\s+|a\s+|an\s+|its\s+|your\s+)?"
                       r"(?:\w+\s+){0,2}?" + _SHOWN_ON + r"s?\b(?!\s*(?:desk|table|stand|shelf|cabinet))"
                       r"|\b(?:image|photo|picture|reflection) of\b|\bon[- ]screen\b|\bdisplayed\b", re.I)


def on_screen(where: str) -> bool:
    return bool(ON_SCREEN.search(where or ""))


def _unit(value: Any) -> float:
    try:
        return min(1.0, max(0.0, float(value)))
    except (TypeError, ValueError):
        return 0.5


def _json(text: str) -> Dict[str, Any]:
    match = re.search(r"\{.*\}", text, re.S)
    try:
        data = json.loads(match.group(0) if match else text)
    except (ValueError, AttributeError):
        return {}
    return data if isinstance(data, dict) else {}


def parse(text: str) -> Dict[str, Any]:
    """The model's JSON, made safe: x and y within 0..1, a short 'where', seen only if said plainly."""
    data = _json(text)
    where = " ".join(str(data.get("where", "")).split())[:80]
    return {"seen": data.get("seen") is True and not on_screen(where), "x": _unit(data.get("x", 0.5)),
            "y": _unit(data.get("y", 0.5)), "where": where}


def parse_check(text: str) -> Dict[str, Any]:
    """The close-up's answer: yes only when the model said exactly "yes"."""
    data = _json(text)
    where = " ".join(str(data.get("where", "")).split())[:80]
    return {"yes": data.get("answer") == "yes" and not on_screen(where), "x": _unit(data.get("x", 0.5)),
            "y": _unit(data.get("y", 0.5)), "where": where}


def tiles(frame: Any, cols: int = TILES[0], rows: int = TILES[1], overlap: float = OVERLAP) -> List[tuple]:
    """The frame as overlapping tiles at full resolution: (left, top, width, height, picture), left to right, top
    to bottom. A tile is cols minus the overlaps wide, so neighbours share `overlap` of a tile."""
    h, w = frame.shape[:2]
    tw = int(round(w / (cols - (cols - 1) * overlap))) if cols > 1 else w
    th = int(round(h / (rows - (rows - 1) * overlap))) if rows > 1 else h
    out = []
    for r in range(rows):
        for c in range(cols):
            x0 = int(round(c * (w - tw) / (cols - 1))) if cols > 1 else 0
            y0 = int(round(r * (h - th) / (rows - 1))) if rows > 1 else 0
            out.append((x0, y0, tw, th, frame[y0:y0 + th, x0:x0 + tw]))
    return out


def close_up(frame: Any, share: float = CLOSE_UP, at: tuple = (0.5, 0.5)) -> Any:
    """`share` of the frame across and down, centred on `at` (x, y, 0..1; the middle by default, where the lens is
    sharpest), kept inside the frame."""
    return frame[_close_box(frame, share, at)]


def _close_box(frame: Any, share: float = CLOSE_UP, at: tuple = (0.5, 0.5)) -> tuple:
    h, w = frame.shape[:2]
    cw, ch = int(w * share), int(h * share)
    x0 = int(min(max(at[0] * w - cw / 2, 0), w - cw))
    y0 = int(min(max(at[1] * h - ch / 2, 0), h - ch))
    return slice(y0, y0 + ch), slice(x0, x0 + cw)


def read_view(frame: Any, what: str, asker: Callable) -> Dict[str, Any]:
    """One view read as zoomed tiles, all at once; the sightings in the whole frame's terms (x, y 0..1), the same
    thing seen in two overlapping tiles counted once, with how many tiles saw it."""
    from concurrent.futures import ThreadPoolExecutor

    h, w = frame.shape[:2]
    parts = tiles(frame) if zoom() else [(0, 0, w, h, frame)]
    with ThreadPoolExecutor(len(parts)) as pool:
        said = list(pool.map(lambda p: asker(p[4], what), parts))
    errors = [a for a in said if isinstance(a, FinderError)]
    if errors:
        raise errors[0]
    sightings: List[Dict[str, Any]] = []
    for (x0, y0, tw, th, _), a in zip(parts, said, strict=True):
        if not a.get("seen"):
            continue
        gx, gy = (x0 + a["x"] * tw) / w, (y0 + a.get("y", 0.5) * th) / h
        inner = min(a["x"], 1 - a["x"], a.get("y", 0.5), 1 - a.get("y", 0.5))   # how far from the tile's edges
        same = next((s for s in sightings if abs(s["x"] - gx) < 0.06 and abs(s["y"] - gy) < 0.1), None)
        if same:
            same["tiles"] += 1
            if inner > same["inner"]:       # a thing cut by one tile's edge is whole in its neighbour: keep that one
                same.update(x=gx, y=gy, inner=inner, where=a.get("where") or same["where"])
            same["where"] = same["where"] or a.get("where", "")
        else:
            sightings.append({"x": gx, "y": gy, "where": a.get("where", ""), "tiles": 1, "inner": inner})
    sightings.sort(key=lambda s: (-s["tiles"], abs(s["x"] - 0.5)))
    top = sightings[0] if sightings else None
    return {"seen": top is not None, "x": top["x"] if top else 0.5, "y": top["y"] if top else 0.5,
            "where": top["where"] if top else "", "sightings": sightings}


def quiet_tracking(robot: Any) -> None:
    """The camera's own face tracking off, directly: a weight handed to it by another behaviour on the tick a search
    began would otherwise pull the head toward the person for the whole search."""
    try:
        robot.stop_head_tracking()
    except Exception:
        pass


def head_angles(robot: Any) -> Optional[tuple]:
    """Where the head is now: (yaw, pitch) in radians, or None if the robot can't say."""
    from andy_companion.body import glance

    try:
        _, p, y = glance._rpy(robot.get_current_head_pose())
        return float(y), float(p)
    except Exception:
        return None


async def arrive(robot: Any, yaw: float, pitch: float, sleep: Callable) -> Optional[tuple]:
    """Wait (up to WAIT_ARRIVE_S) until the head is where it was sent, then return where it is. A move can start late
    (the head finishing what it was doing), and a picture taken on the way reads the room from the wrong angle:
    the founder's first recorded try, 2026-10-20, took its first view about 18 degrees short."""
    now = head_angles(robot)
    for _ in range(int(WAIT_ARRIVE_S / POLL_S)):
        if now is None or (abs(math.degrees(now[0] - yaw)) <= ARRIVED_DEG and abs(math.degrees(now[1] - pitch)) <= ARRIVED_DEG):
            break
        await sleep(POLL_S)
        now = head_angles(robot)
    return now


def target_pitch(sweep_pitch: float, y: float, fy: float = FX, cy: float = CY, reach: bool = True) -> float:
    """The head's pitch (positive is down) toward something at `y` (0 top .. 1 bottom) in a frame at `sweep_pitch`;
    kept within the head's reach unless `reach` is False (the direction itself, for working out where it shows)."""
    p = sweep_pitch + math.atan2(y * 2 * cy - cy, fy)
    return within(p, REACH_PITCH_DEG) if reach else p


def within(angle: float, limit_deg: float) -> float:
    return max(-math.radians(limit_deg), min(math.radians(limit_deg), angle))


def where_in_view(yaw: float, pitch: float, head_yaw: float, head_pitch: float,
                  fx: float = FX, cx: float = CX, cy: float = CY) -> tuple:
    """Where a direction (yaw, pitch) shows in a frame taken with the head at (head_yaw, head_pitch): (x, y), 0..1
    across and down; the inverse of target_yaw and target_pitch. Used when the head could not turn all the way."""
    x = (cx - fx * math.tan(yaw - head_yaw)) / (2 * cx)
    y = (cy + fx * math.tan(pitch - head_pitch)) / (2 * cy)
    return x, y


def target_yaw(sweep_yaw: float, x: float, fx: float = FX, cx: float = CX) -> float:
    """The head's world yaw toward something at `x` (0 left .. 1 right) in a frame taken at `sweep_yaw`."""
    return sweep_yaw + math.atan2(cx - x * 2 * cx, fx)


def best(results: List[Dict[str, Any]]) -> Optional[int]:
    """The frame that sees it most squarely (nearest the middle, where the view is sharpest)."""
    seen = [i for i, r in enumerate(results) if r.get("seen")]
    return min(seen, key=lambda i: abs(results[i]["x"] - 0.5)) if seen else None


def record(what: str, frames: List[Any], results: List[Dict[str, Any]], chosen: Optional[int],
           seconds: Dict[str, Any], folder: Optional[str] = None, poses: Optional[List[Any]] = None,
           close_ups: Optional[List[Any]] = None) -> Optional[str]:
    """Keep one try for scoring, only when ANDY_FINDER_RECORD names a folder: the views and close-ups at full size
    (re-reading them zoomed in needs every pixel), where the head really was for each, and what was said. Returns
    the try's folder."""
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
                (out / f"view-{i}.jpg").write_bytes(vision.jpeg(f, f.shape[1], TILE_QUALITY))
        for i, f in enumerate(close_ups or []):
            if f is not None:
                (out / f"closer-{i}.jpg").write_bytes(vision.jpeg(f, f.shape[1], TILE_QUALITY))
        (out / "try.json").write_text(json.dumps({"what": what, "sweep_deg": list(SWEEP_DEG), "results": results,
                                                  "chosen": chosen, "seconds": seconds, "poses_deg": poses or []},
                                                 indent=1))
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


BACK_TO_FACE_S = 1.0                       # after the last look, face following comes back


async def closer_look(robot: Any, manager: Any, antennas: tuple, place: Dict[str, Any], what: str, checker: Callable,
                      queueable: Callable, sleep: Callable) -> Optional[Dict[str, Any]]:
    """One closer look at a place (yaw and pitch: where the thing should be): Andy turned straight at it, its body too
    when it is past the head's reach (aim; 2026-10-20: a chair 74 degrees to the side), still, then the strict question
    about a close-up of a fresh frame around where it should show from there. Returns the frame, the close-up's box,
    where the head really was and the answer; None when the camera gave no picture. Raises FinderError."""
    from andy_companion.body import look, looking_at

    to = aim(place)
    quiet_tracking(robot)
    step = look.HoldLook(robot.get_current_head_pose(), antennas, to[0], to[1], CLOSER_HOLD_S)
    manager.queue_move(queueable(step))
    looking_at.set(place.get("noticed", "closer"), step.duration + 0.5)
    await sleep(step.turn_s)
    there = await arrive(robot, *to, sleep)
    await sleep(SETTLE_S)
    try:
        frame = robot.media.get_frame()
    except Exception:
        frame = None
    if frame is None:
        return None
    frame = frame.copy()
    head = there if there and abs(math.degrees(there[0] - to[0])) < 25 else to   # the head's own angles
    box = _close_box(frame, CLOSE_UP, where_in_view(place["yaw"], place["pitch"], *head))
    checked = await asyncio.to_thread(checker, frame[box].copy(), what)
    return {"frame": frame, "box": box, "head": head, "checked": checked}


def confirmed_place(place: Dict[str, Any], look_: Dict[str, Any]) -> Dict[str, Any]:
    """Where the thing sits in the close-up, back to the whole frame, as the head angles to point (as far as Andy
    turns, aim)."""
    frame, box, head, checked = look_["frame"], look_["box"], look_["head"], look_["checked"]
    h, w = frame.shape[:2]
    fx = (box[1].start + checked.get("x", 0.5) * (box[1].stop - box[1].start)) / w
    fy = (box[0].start + checked.get("y", 0.5) * (box[0].stop - box[0].start)) / h
    # Where it is, in words: the wider view's (it saw what is around it; a close-up has less to name, and in the
    # simulation called a croissant "potato"), the close-up's only when the wider view said nothing.
    return dict(place, yaw=within(target_yaw(head[0], fx), yaw_reach_deg()), pitch=target_pitch(head[1], fy),
                where=place.get("where") or checked.get("where", ""))


async def find(what: str, robot: Any, manager: Any, **kw: Any) -> Dict[str, Any]:
    """Sweep, look (zoomed in), look closer, point, show. Returns what Andy should say.

    Face following is off for the whole search and comes back after Andy has pointed (2026-10-20, the founder's
    recorded tries: Pollen hands the head back to face tracking as Andy finishes saying "let me have a look
    around", mid-sweep, and one view came out pointed at the founder, the close-ups at the wrong places). It comes
    back only if it was on, once the last look has played out."""
    from andy_companion.body import hold
    from andy_companion import board

    tracking = bool(getattr(manager, "_head_tracking", False)) and hasattr(manager, "set_head_tracking")
    hold.begin(manager)                  # seek, face following, the glance and idle hand-back stand down
    if tracking:
        manager.set_head_tracking(False)
    quiet_tracking(robot)
    out: Dict[str, Any] = {}
    search = None
    try:
        await asyncio.to_thread(board.clear_screen)
        starting = asyncio.create_task(asyncio.to_thread(board.start_search))
        try:
            search = await asyncio.shield(starting)
        except asyncio.CancelledError:
            # The HTTP thread can finish after cancellation. Learn its ID before cleanup, so it cannot
            # create a working card after the cancelled search has already tried to remove it.
            search = await starting
            raise

        async def progress(stage: str, captured: int = 0) -> None:
            await asyncio.to_thread(board.search_step, search, stage, captured)

        hint = None
        if zoom():
            from andy_companion import places

            hint = places.recall(tidy_what(what))
        if hint and hint.get("yaw") is not None:          # where it was: look there first, then around
            await progress("remembered")
            out = await where_it_was(tidy_what(what), robot, manager, hint, **kw)
            if out.get("found") or out.get("error"):
                return out
        out = await _find(what, robot, manager, progress=progress, **kw)
        if hint and "how" in out:
            out["how"] = out["how"] + " " + moved_note(hint, bool(out.get("found")))
        return out
    finally:
        await asyncio.to_thread(board.end_search, search)
        back = BACK_TO_FACE_S + (POINT_HOLD_S if out.get("found") else 0.0)

        def face_back() -> None:
            hold.end(manager)
            if tracking:
                try:
                    manager.set_head_tracking(True)
                except Exception:
                    pass   # following the face again is a help, never a reason to fail

        try:
            asyncio.get_running_loop().call_later(back, face_back)
        except RuntimeError:
            face_back()


def merge_places(results: List[Dict[str, Any]], poses: List[tuple]) -> List[Dict[str, Any]]:
    """Every sighting as a head angle (from where the head really was for its view); the same thing seen from two
    neighbouring views is one place. The most tiles first, then the most central. Used by the robot and by the
    simulation (sim/finder_sim.py), so both run the same search."""
    places: List[Dict[str, Any]] = []
    for i, r in enumerate(results):
        for sgt in r.get("sightings") or ([r] if r.get("seen") else []):
            yaw, tilt = target_yaw(poses[i][0], sgt["x"]), target_pitch(poses[i][1], sgt.get("y", 0.5), reach=False)
            same = next((pl for pl in places if abs(math.degrees(pl["yaw"] - yaw)) < SAME_PLACE_DEG
                         and abs(math.degrees(pl["pitch"] - tilt)) < SAME_PLACE_DEG), None)
            if same:
                same["tiles"] += sgt.get("tiles", 1)
                if abs(sgt["x"] - 0.5) < abs(same["x"] - 0.5):        # keep the view that saw it most squarely
                    same.update(view=i, x=sgt["x"], where=sgt.get("where") or same["where"])
            else:
                places.append({"view": i, "x": sgt["x"], "yaw": yaw, "pitch": tilt, "where": sgt.get("where", ""),
                               "tiles": sgt.get("tiles", 1)})
    places.sort(key=lambda pl: (-pl["tiles"], abs(pl["x"] - 0.5)))
    return places


def moved_note(hint: Dict[str, Any], found: bool) -> str:
    """What Andy says about where the thing was before (B46): moved, or not where it was left."""
    from andy_companion import places

    who = "where they left it" if hint.get("told") else "where you saw it"
    when = places.ago(float(hint.get("at", 0)))
    if found:
        return f"Mention briefly that it has moved since {when}: it was {hint.get('where', '')} ({who})."
    return f"Say that it isn't {who} {when} ({hint.get('where', '')}) any more."


async def where_it_was(what: str, robot: Any, manager: Any, hint: Dict[str, Any], *, checker: Callable = look_closer,
                       poster: Callable = post_views, queueable: Optional[Callable] = None,
                       sleep: Callable = asyncio.sleep, **_: Any) -> Dict[str, Any]:
    """Look first where the thing was (B46): the place the person had Andy keep, or where Andy last saw it. One
    closer look, a few seconds instead of a sweep. Found: point and say so. Not there: an empty dict, and the sweep
    follows."""
    from andy_companion import board, places
    from andy_companion.body import look, looking_at

    queueable = queueable or look.queueable
    try:
        antennas = tuple(float(a) for a in robot.get_current_joint_positions()[1][:2])
    except Exception:
        antennas = (0.0, 0.0)
    place = {"view": 0, "x": 0.5, "yaw": float(hint["yaw"]), "pitch": float(hint["pitch"]), "where": hint.get("where", ""),
             "tiles": 1, "noticed": "remembered"}
    try:
        got = await closer_look(robot, manager, antennas, place, what, checker, queueable, sleep)
    except FinderError as e:
        return {"error": str(e)}
    logger.info("finder: %s where it was", "found" if got and got["checked"].get("yes") else "not")
    if not got or not got["checked"].get("yes"):
        return {}
    chosen = confirmed_place(place, got)
    manager.queue_move(queueable(look.HoldLook(robot.get_current_head_pose(), antennas, chosen["yaw"], chosen["pitch"],
                                               POINT_HOLD_S)))
    looking_at.set("pointing", POINT_HOLD_S + 1.0)
    try:
        from andy_companion import outline
        picture = await asyncio.to_thread(outline.draw, got["frame"][got["box"]], what,
                                         (got["checked"].get("x", 0.5), got["checked"].get("y", 0.5)))
        poster(views_for_screen([picture]), [True], 0)
    except Exception:
        pass   # the TV is a help, never a reason to stop
    where = chosen["where"] or hint.get("where", "")
    await asyncio.to_thread(board.show, "seen", f"Your {what}", [{"summary": where}] if where else [])
    places.saw(what, where, chosen["yaw"], chosen["pitch"])
    kept = "where you left them" if hint.get("told") else "where I last saw them"
    say = f"They're still {kept}" + (f", {where}" if where else "") + "."
    return {"found": True, "what": what, "where": where, "say": say, "looked_closer": True, "where_it_was": True,
            "_yaw": chosen["yaw"], "_pitch": chosen["pitch"],
            "how": ("You are pointing at it with your head now, and the picture is on the screen. Say exactly the words "
                    "in 'say', then that it's on the screen too. Never say left or right: they may be facing you.")}


async def _find(what: str, robot: Any, manager: Any, *, asker: Callable = ask, checker: Callable = look_closer,
                poster: Callable = post_views, queueable: Optional[Callable] = None, sleep: Callable = asyncio.sleep,
                clock: Optional[Callable[[], float]] = None, progress: Optional[Callable] = None) -> Dict[str, Any]:
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
    try:   # the TV shows the last search's close-up for two minutes: clear it, or Andy finds the picture
        poster([None] * len(SWEEP_DEG), [False] * len(SWEEP_DEG), None)
    except Exception:
        pass
    pose = robot.get_current_head_pose()
    start = clock()
    from andy_companion.body import looking_at
    nothing = {"seen": False, "x": 0.5, "y": 0.5, "where": "", "sightings": []}

    async def none() -> Dict[str, Any]:
        return dict(nothing)

    # Each view is read (its six tiles at once) as soon as it is taken, while the head turns to the next, so the
    # reading is done about when the sweep is (2026-10-20: reading after the sweep made a search about 14 s).
    # One move at a time (2026-10-20: queued all at once and timed by the clock, the pictures fell out of step with
    # the head and came out blurred): send it, wait for the head to say it has arrived, let it settle, take the
    # picture, then the next. Each look holds long enough for that; the next starts when it ends.
    frames: List[Any] = []
    reading: List[Any] = []
    poses: List[tuple] = []          # where the head really was for each view (yaw, pitch, radians)
    for deg in SWEEP_DEG:
        if progress:
            await progress("scanning", sum(f is not None for f in frames))
        sent = (math.radians(deg), pitch)
        quiet_tracking(robot)
        step = look.HoldLook(pose, antennas, sent[0], sent[1], HOLD_S)
        manager.queue_move(queueable(step))
        looking_at.set("room", step.duration + 1.0)
        await sleep(step.turn_s)
        there = await arrive(robot, *sent, sleep)
        await sleep(SETTLE_S)
        pose = step.end
        # The head's own angles, when it says them and they are near where it was sent; otherwise where it was sent.
        poses.append(there if there and abs(math.degrees(there[0] - sent[0])) < 25 else sent)
        try:
            frame = robot.media.get_frame()
            frames.append(None if frame is None else frame.copy())
        except Exception:
            frames.append(None)
        f = frames[-1]
        reading.append(asyncio.ensure_future(asyncio.to_thread(read_view, f, what, asker) if f is not None else none()))
    if not any(f is not None for f in frames):
        for task in reading:
            task.cancel()
        return {"error": "My camera did not give a picture just now."}
    if progress:
        await progress("reading", sum(f is not None for f in frames))
    answers = await asyncio.gather(*reading, return_exceptions=True)
    for a in answers:
        if isinstance(a, FinderError):
            return {"error": str(a)}
    results = [a if isinstance(a, dict) else dict(nothing) for a in answers]

    places = merge_places(results, poses)
    looked_s = clock() - start

    chosen: Optional[Dict[str, Any]] = None
    closer: List[Dict[str, Any]] = []
    close_picture: Any = None
    close_point = (0.5, 0.5)
    close_ups: List[Any] = []
    if places and not zoom():                       # one shrunk frame per view, as before: the first sighting
        chosen = dict(places[0])
    for place in places[:MAX_CLOSER] if zoom() else []:
        if progress:
            await progress("closer", sum(f is not None for f in frames))
        try:
            got = await closer_look(robot, manager, antennas, place, what, checker, queueable, sleep)
        except FinderError as e:
            return {"error": str(e)}
        if got is None:
            continue
        close_ups.append(got["frame"][got["box"]].copy())
        closer.append({"view": place["view"], "yes": bool(got["checked"].get("yes"))})
        if got["checked"].get("yes"):
            chosen = confirmed_place(place, got)
            close_picture = got["frame"][got["box"]].copy()
            close_point = (got["checked"].get("x", 0.5), got["checked"].get("y", 0.5))
            break
    i = chosen["view"] if chosen else None
    # Numbers only, never pictures or words: how many places were seen, how many closer looks, how long.
    logger.info("finder: %s (%d place%s seen, %d closer look%s, %.1f s)",
                "found" if chosen else ("no closer picture" if places and not closer
                                        else "not confirmed up close" if places else "not found"),
                len(places), "" if len(places) == 1 else "s", len(closer), "" if len(closer) == 1 else "s",
                clock() - start)

    def show_views() -> None:     # first the views, then the card: the screen pairs a card with views just before it
        try:
            shown = list(frames)
            if i is not None and close_picture is not None:
                shown[i] = close_picture  # confirmed close-up, optionally outlined on this display copy
            poster(views_for_screen(shown), [bool(r.get("seen")) for r in results], i)
        except Exception:
            pass   # the TV is a help, never a reason to stop

    seconds = {"to_answer": round(looked_s, 2)}
    if chosen is None:
        await asyncio.to_thread(record, what, frames, results, None, {**seconds, "closer": closer}, None,
                                [[round(math.degrees(a), 1) for a in ps] for ps in poses], close_ups)
        await asyncio.to_thread(show_views)
        await asyncio.to_thread(board.show, "looked", f"I couldn't see your {what}", [])
        if places and not closer:   # the camera gave no picture at any closer look: nothing was ruled out
            how = (f"Say kindly that you thought you saw something like their {what}, but your camera didn't give a "
                   "picture when you turned to look closer, so you can't be sure, and that the screen shows where you "
                   "looked. Offer to look again. Never say it wasn't them. No guessing.")
        elif places:
            how = (f"Say kindly that you thought you saw something like their {what}, but when you looked closer it "
                   "wasn't them, and that the screen shows where you looked. Offer to look again if they move "
                   "something or hold it nearer. No guessing.")
        else:
            how = (f"Say kindly that you looked around but couldn't see their {what} from where you are, and "
                   "that the screen shows where you looked. Offer to look again if they move something or hold it "
                   "nearer, or suggest one likely place to check. No guessing.")
        return {"found": False, "what": what, "looked": len(frames), "how": how}
    manager.queue_move(queueable(look.HoldLook(robot.get_current_head_pose(), antennas, chosen["yaw"], chosen["pitch"],
                                               POINT_HOLD_S)))
    looking_at.set("pointing", POINT_HOLD_S + 1.0)
    await asyncio.to_thread(record, what, frames, results, i,
                            {**seconds, "to_point": round(clock() - start, 2), "closer": closer}, None,
                            [[round(math.degrees(a), 1) for a in ps] for ps in poses], close_ups)
    if close_picture is not None:
        from andy_companion import outline
        # The worker only returns pixels. If cancelled while it waits for a mask, it cannot publish later.
        close_picture = await asyncio.to_thread(outline.draw, close_picture, what, close_point)
    await asyncio.to_thread(show_views)
    where = chosen["where"]
    await asyncio.to_thread(board.show, "seen", f"Your {what}", [{"summary": where}] if where else [])
    say = f"I think I see your {what}" + (f", {where}" if where else ", over there where I'm looking") + "."
    from andy_companion import places as kept_places
    kept_places.saw(what, where, chosen["yaw"], chosen["pitch"])     # in memory only: asked again soon, look there first
    return {"found": True, "what": what, "where": where, "say": say, "looked_closer": bool(closer),
            "_yaw": chosen["yaw"], "_pitch": chosen["pitch"],
            "how": ("You are pointing at it with your head now, and the picture is on the screen. Say exactly the words in 'say', 'I think' included, "
                    "then that it's on the screen too. Never say left or right: they may be facing you.")}
