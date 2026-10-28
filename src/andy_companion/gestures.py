"""Teach Andy a move by hand (PLAN B47): "Andy, learn Sofia's wave."

Andy's two antennas go limp (their motors off, the head's stay on: a limp head could drop), the person moves them
for RECORD_S, and Andy keeps the movement, then plays it back; "Andy, do Sofia's wave" plays it again, any time.
Puppetry, the way Pollen's Marionette records the robot by hand, kept to the antennas.

How it stays gentle:
- Before the motors come back on, a move that starts exactly where the hand left the antennas is already playing,
  so they don't snap to an old target; it eases them home.
- What was recorded is trimmed of the still parts at either end, smoothed, and slowed down if any part is faster
  than the antennas' MAX_RAD_S (giggle.py keeps them under 2 rad/s, far from a button press).
- Playing back eases in from where the antennas are and back to where they were; the head holds still meanwhile.

Kept on this computer (gestures.json, owner-only): each gesture's name and its antenna angles over time; nothing
from the camera or the microphones.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

from andy_companion.reminders import DATA_DIR

FILE = DATA_DIR / "gestures.json"
ANTENNAS = ["left_antenna", "right_antenna"]
RECORD_S = 6.0
RATE_HZ = 30.0
MAX_RAD_S = 1.8               # under the antennas' 2 rad/s
STILL_RAD = 0.03              # less than this from the start counts as not moving yet
MIN_RANGE_RAD = 0.15          # less movement than this all through: nothing was taught
EASE_S = 0.5                  # into the gesture from where the antennas are, and back out
HOME_S = 1.0                  # after recording, the antennas eased back to where they were
MAX_GESTURES = 12

Point = Tuple[float, float, float]      # (seconds, left, right)


def _load() -> Dict[str, Any]:
    try:
        data = json.loads(FILE.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data: Dict[str, Any]) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=FILE.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, FILE)


def tidy_name(name: Any) -> str:
    return " ".join(str(name or "").split())[:40].strip(" .?!") or "my move"


def names() -> List[str]:
    return list(_load())


def find_name(name: str) -> Optional[str]:
    """The kept gesture a name means: exactly, or by its words ("the wave" finds "Sofia's wave")."""
    data = _load()
    key = next((k for k in data if k.lower() == tidy_name(name).lower()), None)
    if key is None:                     # "the wave" finds "Sofia's wave"
        words = set(tidy_name(name).lower().replace("'s", "").split()) - {"the", "a", "my", "your", "move", "dance"}
        key = next((k for k in data if words and words <= set(k.lower().replace("'s", "").split())), None)
    return key


def get(name: str) -> Optional[List[Point]]:
    key = find_name(name)
    return [tuple(p) for p in _load()[key]["points"]] if key else None


def forget(name: str) -> bool:
    data = _load()
    key = find_name(name)
    if key is None:
        return False
    del data[key]
    _save(data)
    return True


def remove(key: str) -> bool:
    """Forget one gesture by its exact kept name (the settings page's delete): never by words, which could match
    another."""
    data = _load()
    if key not in data:
        return False
    del data[key]
    _save(data)
    return True


def keep(name: str, points: List[Point]) -> None:
    data = _load()
    data.pop(next((k for k in data if k.lower() == tidy_name(name).lower()), ""), None)
    data[tidy_name(name)] = {"points": [[round(t, 3), round(a, 4), round(b, 4)] for t, a, b in points], "at": time.time()}
    while len(data) > MAX_GESTURES:
        data.pop(next(iter(data)))
    _save(data)


def clean(samples: List[Point]) -> Optional[List[Point]]:
    """What the hand did, made safe to play: the still parts at either end cut, smoothed over three samples, time
    stretched so nothing is faster than MAX_RAD_S, starting at 0 s. None when there was no real movement."""
    if len(samples) < 3:
        return None
    l0, r0 = samples[0][1], samples[0][2]
    moving = [i for i, (_, a, b) in enumerate(samples) if max(abs(a - l0), abs(b - r0)) > STILL_RAD]
    if not moving:
        return None
    lo, hi = max(0, moving[0] - 1), min(len(samples), moving[-1] + 2)
    part = samples[lo:hi]
    span = max(max(p[1] for p in part) - min(p[1] for p in part), max(p[2] for p in part) - min(p[2] for p in part))
    if span < MIN_RANGE_RAD:
        return None
    smooth = []
    for i in range(len(part)):
        win = part[max(0, i - 1):i + 2]
        smooth.append((part[i][0], sum(p[1] for p in win) / len(win), sum(p[2] for p in win) / len(win)))
    t0 = smooth[0][0]
    fastest = max((max(abs(b[1] - a[1]), abs(b[2] - a[2])) / max(b[0] - a[0], 1e-3)
                   for a, b in zip(smooth, smooth[1:], strict=False)), default=0.0)
    stretch = max(1.0, fastest / MAX_RAD_S)
    return [((t - t0) * stretch, a, b) for t, a, b in smooth]


def _at(points: List[Point], t: float) -> Tuple[float, float]:
    if t <= points[0][0]:
        return points[0][1], points[0][2]
    for a, b in zip(points, points[1:], strict=False):
        if t <= b[0]:
            w = (t - a[0]) / max(b[0] - a[0], 1e-6)
            return a[1] + w * (b[1] - a[1]), a[2] + w * (b[2] - a[2])
    return points[-1][1], points[-1][2]


def _ease(x: float) -> float:
    x = min(1.0, max(0.0, x))
    return x * x * (3 - 2 * x)


class Play:
    """A gesture as a move: ease from `antennas_now` to its start, play it, ease back; the head held at `head`."""

    andy_owns_head = True

    def __init__(self, points: List[Point], head: Any, antennas_now: Tuple[float, float]):
        self.points, self.head, self.home = points, head, (float(antennas_now[0]), float(antennas_now[1]))
        self.length = points[-1][0]

    @property
    def duration(self) -> float:
        return EASE_S + self.length + EASE_S

    def antennas(self, t: float) -> Tuple[float, float]:
        first, last = self.points[0], self.points[-1]
        if t < EASE_S:
            w = _ease(t / EASE_S)
            return self.home[0] + w * (first[1] - self.home[0]), self.home[1] + w * (first[2] - self.home[1])
        if t < EASE_S + self.length:
            return _at(self.points, t - EASE_S)
        w = _ease((t - EASE_S - self.length) / EASE_S)
        return last[1] + w * (self.home[0] - last[1]), last[2] + w * (self.home[1] - last[2])

    def evaluate(self, t: float):
        import numpy as np

        return np.array(self.head, dtype=float), np.array(self.antennas(t)), 0.0


def queueable(play: Any) -> Any:
    """A Play (or Home) as a Pollen Move (its queue takes only those)."""
    from reachy_mini.motion.move import Move

    class GestureMove(Move):
        andy_owns_head = True

        @property
        def duration(self) -> float:
            return play.duration

        def evaluate(self, t: float):
            return play.evaluate(t)

    return GestureMove()


class Home:
    """From where the hand left the antennas back to where they were, over HOME_S; the head held at `head`."""

    andy_owns_head = True

    def __init__(self, head: Any, from_: Tuple[float, float], to: Tuple[float, float]):
        self.head, self.from_, self.to = head, from_, to

    @property
    def duration(self) -> float:
        return HOME_S

    def evaluate(self, t: float):
        import numpy as np

        w = _ease(t / HOME_S)
        antennas = (self.from_[0] + w * (self.to[0] - self.from_[0]), self.from_[1] + w * (self.to[1] - self.from_[1]))
        return np.array(self.head, dtype=float), np.array(antennas), 0.0


async def learn(name: str, robot: Any, manager: Any, *, sleep: Callable, clock: Callable[[], float] = time.monotonic,
                queue: Callable = queueable) -> Dict[str, Any]:
    """Antennas limp for RECORD_S while the person moves them; then home gently, motors on, the gesture kept and
    played back once. Returns what happened."""
    head = robot.get_current_head_pose()
    start = tuple(float(a) for a in robot.get_current_joint_positions()[1][:2])
    samples: List[Point] = []
    robot.disable_motors(ANTENNAS)
    try:
        began = clock()
        while clock() - began < RECORD_S:
            try:
                a = robot.get_current_joint_positions()[1]
                samples.append((clock() - began, float(a[0]), float(a[1])))
            except Exception:
                pass
            await sleep(1.0 / RATE_HZ)
    finally:
        # A move starting where the hand left them, playing before the motors come back: no snap.
        last = (samples[-1][1], samples[-1][2]) if samples else start
        try:
            manager.queue_move(queue(Home(head, last, start)))
            await sleep(0.15)
        finally:                    # whatever happened, the antennas never stay limp (2026-10-25 review)
            robot.enable_motors(ANTENNAS)
    points = clean(samples)
    if points is None:
        return {"learned": False}
    keep(name, points)
    await sleep(HOME_S)
    manager.queue_move(queue(Play(points, robot.get_current_head_pose(), start)))
    return {"learned": True, "name": tidy_name(name), "seconds": round(points[-1][0], 1)}


def do(name: str, robot: Any, manager: Any, queue: Callable = queueable) -> Dict[str, Any]:
    key = find_name(name)
    if key is None:
        return {"done": False, "known": names()}
    antennas = tuple(float(a) for a in robot.get_current_joint_positions()[1][:2])
    manager.queue_move(queue(Play(get(key), robot.get_current_head_pose(), antennas)))
    return {"done": True, "name": key}

