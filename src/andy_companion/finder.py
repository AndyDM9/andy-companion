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
CY = 542.0                                 # the middle of a 1080-line frame, for how far down something is
TILES = (3, 2)                             # columns and rows of the zoomed tiles in each view
OVERLAP = 0.15                             # so a thing on a tile's edge is whole in its neighbour
TILE_WIDTH, TILE_QUALITY = 1024, 90        # tiles are sent at their own size (never shrunk), JPEG quality 90
CLOSER_HOLD_S = 1.2                        # looking closer: the turn, then still for the close-up
CLOSE_UP = 0.5                             # the close-up: the middle half of the frame across and down
MAX_CLOSER = 2                             # sightings looked at closer before saying it couldn't be seen
SAME_PLACE_DEG = 6.0                       # sightings this close together are one thing
TIMEOUT_S = 40
VIEW_WIDTH, VIEW_QUALITY = 480, 70         # the TV's strip: small enough for four in memory, clear at a glance
ASK = ("You are the eyes of a home companion robot helping someone find their {what}. Look at this picture. "
       "Is their {what} visible? Answer as JSON: seen (true or false), x (where it is across the picture, "
       "0 at the left edge to 1 at the right edge), and where (a few plain words, like 'on the table by the "
       "lamp'), naming things near it and never left or right. Only say seen if you can actually see it. "
       "Never describe any person. Also give y, where it is down the picture, 0 at the top to 1 at the bottom.")
SCHEMA = {"type": "object", "additionalProperties": False, "required": ["seen", "x", "y", "where"],
          "properties": {"seen": {"type": "boolean"}, "x": {"type": "number"}, "y": {"type": "number"},
                         "where": {"type": "string"}}}
# Looking closer: one strict question about the close-up. Only "yes" counts (a model's own confidence is poorly
# calibrated, so a second look at a closer picture is the check, not a score).
CHECK = ("You are the eyes of a home companion robot. It has turned to look closely at something that may be the "
         "person's {what}. Look at this close-up. Is it clearly their {what}? Answer as JSON: answer ('yes', 'no' or "
         "'unsure'), x and y (where it is, 0 to 1 across and down), and where (a few plain words naming things near "
         "it, never left or right). Say yes only if you are sure. Never describe any person.")
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
    req = vision.request(e, [{"type": "text", "text": prompt.format(what=what)},
                             {"type": "image_url", "image_url": {"url": image}}], 120, 0,
                         {"response_format": {"type": "json_schema", "json_schema": {"name": name, "schema": schema}}})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT_S) as r:
            text = str(json.loads(r.read())["choices"][0]["message"]["content"])
    except Exception as e:   # never echo the request: it holds the picture
        if getattr(e, "code", None) in (404, 502, 503, 504):
            raise FinderError(SWITCHED_OFF) from None
        raise FinderError(f"My eyes in the cloud did not answer ({type(e).__name__}).") from None
    return parse_check(text) if check else parse(text)


def look_closer(frame: Any, what: str, opener: Optional[Callable] = None) -> Dict[str, Any]:
    """The close-up check: the middle of a frame taken with the head turned straight at a sighting."""
    return ask(close_up(frame), what, opener, check=True)


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
    return {"seen": data.get("seen") is True, "x": _unit(data.get("x", 0.5)), "y": _unit(data.get("y", 0.5)),
            "where": " ".join(str(data.get("where", "")).split())[:80]}


def parse_check(text: str) -> Dict[str, Any]:
    """The close-up's answer: yes only when the model said exactly "yes"."""
    data = _json(text)
    return {"yes": data.get("answer") == "yes", "x": _unit(data.get("x", 0.5)), "y": _unit(data.get("y", 0.5)),
            "where": " ".join(str(data.get("where", "")).split())[:80]}


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


def close_up(frame: Any, share: float = CLOSE_UP) -> Any:
    """The middle of the frame (`share` of it across and down), where the lens is sharpest."""
    h, w = frame.shape[:2]
    cw, ch = int(w * share), int(h * share)
    x0, y0 = (w - cw) // 2, (h - ch) // 2
    return frame[y0:y0 + ch, x0:x0 + cw]


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
    for (x0, y0, tw, th, _), a in zip(parts, said):
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


def target_pitch(sweep_pitch: float, y: float, fy: float = FX, cy: float = CY) -> float:
    """The head's pitch (positive is down) toward something at `y` (0 top .. 1 bottom) in a frame at `sweep_pitch`;
    kept within 35 degrees, inside the head's limits."""
    return max(math.radians(-35), min(math.radians(35), sweep_pitch + math.atan2(y * 2 * cy - cy, fy)))


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


async def find(what: str, robot: Any, manager: Any, *, asker: Callable = ask, checker: Callable = look_closer,
               poster: Callable = post_views, queueable: Optional[Callable] = None, sleep: Callable = asyncio.sleep,
               clock: Optional[Callable[[], float]] = None) -> Dict[str, Any]:
    """Sweep, look (zoomed in), look closer, point, show. Returns what Andy should say."""
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
    # All views (and all their tiles) are read at once: about one model call's time, not four or twenty-four.
    nothing = {"seen": False, "x": 0.5, "y": 0.5, "where": "", "sightings": []}

    async def none() -> Dict[str, Any]:
        return dict(nothing)

    answers = await asyncio.gather(*[asyncio.to_thread(read_view, f, what, asker) if f is not None else none()
                                     for f in frames], return_exceptions=True)
    for a in answers:
        if isinstance(a, FinderError):
            return {"error": str(a)}
    results = [a if isinstance(a, dict) else dict(nothing) for a in answers]

    # Every sighting as a head angle; the same thing seen from two neighbouring views is one place.
    places: List[Dict[str, Any]] = []
    for i, r in enumerate(results):
        for sgt in r.get("sightings") or ([r] if r.get("seen") else []):
            yaw, tilt = target_yaw(math.radians(SWEEP_DEG[i]), sgt["x"]), target_pitch(pitch, sgt.get("y", 0.5))
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
    looked_s = clock() - start

    chosen: Optional[Dict[str, Any]] = None
    closer: List[Dict[str, Any]] = []
    close_picture: Any = None
    if places and not zoom():                       # one shrunk frame per view, as before: the first sighting
        chosen = dict(places[0])
    for place in places[:MAX_CLOSER] if zoom() else []:
        # Look closer: the head straight at it, still, then the middle of a fresh frame, sharpest there.
        step = look.HoldLook(robot.get_current_head_pose(), antennas, place["yaw"], place["pitch"], CLOSER_HOLD_S)
        manager.queue_move(queueable(step))
        looking_at.set("room", step.duration + 0.5)
        began = clock()
        await sleep(max(0.0, began + step.turn_s + SETTLE_S - clock()))
        try:
            frame = robot.media.get_frame()
        except Exception:
            frame = None
        if frame is None:
            continue
        try:
            checked = await asyncio.to_thread(checker, frame.copy(), what)
        except FinderError as e:
            return {"error": str(e)}
        closer.append({"view": place["view"], "yes": bool(checked.get("yes"))})
        if checked.get("yes"):
            # Where it sits in the close-up (the middle CLOSE_UP of the frame), as a last small turn.
            fx = 0.5 + (checked.get("x", 0.5) - 0.5) * CLOSE_UP
            fy = 0.5 + (checked.get("y", 0.5) - 0.5) * CLOSE_UP
            chosen = dict(place, yaw=target_yaw(place["yaw"], fx), pitch=target_pitch(place["pitch"], fy),
                          where=checked.get("where") or place["where"])
            close_picture = close_up(frame.copy())
            break
    i = chosen["view"] if chosen else None
    logger.info("finder: %s", "found" if chosen else ("not confirmed up close" if places else "not found"))

    def show_views() -> None:     # first the views, then the card: the screen pairs a card with views just before it
        try:
            shown = list(frames)
            if i is not None and close_picture is not None:
                shown[i] = close_picture                 # the closer look, in place of the wide view it came from
            poster(views_for_screen(shown), [bool(r.get("seen")) for r in results], i)
        except Exception:
            pass   # the TV is a help, never a reason to stop

    seconds = {"to_answer": round(looked_s, 2)}
    if chosen is None:
        await asyncio.to_thread(record, what, frames, results, None, {**seconds, "closer": closer})
        await asyncio.to_thread(show_views)
        board.show("looked", f"I couldn't see your {what}", [])
        if places:
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
                            {**seconds, "to_point": round(clock() - start, 2), "closer": closer})
    await asyncio.to_thread(show_views)
    where = chosen["where"]
    board.show("seen", f"Your {what}", [{"summary": where}] if where else [])
    say = f"I think I see your {what}" + (f", {where}" if where else ", over there where I'm looking") + "."
    return {"found": True, "what": what, "where": where, "say": say, "looked_closer": bool(closer),
            "how": ("You are pointing at it with your head now, and the picture is on the screen. Say exactly the words in 'say', 'I think' included, "
                    "then that it's on the screen too. Never say left or right: they may be facing you.")}
