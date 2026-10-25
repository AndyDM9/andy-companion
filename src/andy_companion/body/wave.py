"""Wave, and Andy waves back with its antennas (PLAN B49).

Presence without words: someone waves at Andy, and its antennas wave back. Nothing is said and nothing is kept.

Seeing a wave, with no new model (OpenCV, which Andy already has): while Andy follows a face, a thread looks at
the camera WATCH_HZ times a second, small and grey, and compares each picture with the last. A wave is motion in a
zone beside the face at about shoulder height (either side) whose middle keeps changing direction: REVERSALS or
more within WINDOW_S, the zone moving in most of those pictures, while the face's own zone stays still (walking or
leaning moves the face too: not a wave). Not while Andy speaks, during a search (body.hold), or within COOLDOWN_S
of the last wave back. The face's place comes from the daemon's tracking (x, y from -1 to 1).

Waving back: both antennas sway together for WAVE_S, AMP_RAD at WAVE_HZ under a smooth envelope (peak about
1.8 rad/s, under the antennas' 2 rad/s, as giggle.py keeps them), the head untouched. ANDY_WAVE=off turns it off.
"""

from __future__ import annotations

import logging
import math
import os
import threading
import time
from collections import deque
from typing import Any, Callable, Dict, Optional, Tuple

import numpy as np

logger = logging.getLogger("andy.wave")

ENABLED = os.environ.get("ANDY_WAVE", "on").strip().lower() not in ("off", "0", "false", "no")
# ANDY_WAVE_DEBUG=1: every DEBUG_EVERY_S, why no wave was seen, in counts only (never a picture), for tuning on the
# robot (2026-10-25: the founder's waves weren't answered after the first two).
DEBUG = os.environ.get("ANDY_WAVE_DEBUG", "").strip().lower() in ("1", "on", "yes", "true")
DEBUG_EVERY_S = 5.0
WATCH_HZ = 8.0
SMALL = (320, 180)                 # the pictures compared, grey: cheap, and enough for a hand
DIFF = 25                          # brightness change that counts as motion
# Tuned on the robot (2026-10-25, ANDY_WAVE_DEBUG): a real wave moved the face's zone in a third of the pictures (the
# person sways, the head follows them), and wiping the count each time left it at 1 swing of 3. Now a picture with
# some face motion is skipped, only a large one (walking, leaning) starts again, and two swings in 2.5 s will do.
WINDOW_S = 2.5
REVERSALS = 2
MOVING_SHARE = 0.6                 # of the pictures in the window, the zone moving in this many
ZONE_MOTION = 0.04                 # share of a zone's pixels moving, to count as moving
FACE_STILL = 0.08                  # the face's zone moving less than this: a picture to read
FACE_MOVED = 0.3                   # more than this: the person moved (walking, leaning), not a hand: start again
COOLDOWN_S = 20.0
# Bigger and longer since the founder missed it on the robot (2026-10-25): about 29 degrees, two swings in 3.4 s,
# the peak still about 1.7 rad/s, under the antennas' 2.
WAVE_S, WAVE_HZ, AMP_RAD, EASE_S = 3.4, 0.55, 0.5, 0.45


def zones(face_x: float, face_y: float, w: int, h: int) -> dict:
    """Pixel boxes (x0, y0, x1, y1) in a w x h picture: the face, and a zone each side of it at shoulder height."""
    cx, cy = (face_x + 1) / 2 * w, (face_y + 1) / 2 * h
    fw, fh = 0.12 * w, 0.2 * h

    def box(x0, y0, x1, y1):
        return int(max(0, x0)), int(max(0, y0)), int(min(w, x1)), int(min(h, y1))

    return {"face": box(cx - fw / 2, cy - fh / 2, cx + fw / 2, cy + fh / 2),
            "left": box(cx - 0.42 * w, cy - 0.25 * h, cx - 0.09 * w, cy + 0.3 * h),
            "right": box(cx + 0.09 * w, cy - 0.25 * h, cx + 0.42 * w, cy + 0.3 * h)}


class WaveDetector:
    """Feed it pictures with the face's place; it says when it has seen a wave."""

    def __init__(self) -> None:
        self.previous: Optional[np.ndarray] = None
        self.seen: deque = deque()          # (time, side moving, its middle x) per picture, for WINDOW_S
        self.why = ""                       # the last picture's verdict, for ANDY_WAVE_DEBUG
        self.turns = 0

    def reset(self) -> None:
        self.previous = None
        self.seen.clear()

    def feed(self, frame: np.ndarray, face_x: float, face_y: float, now: float) -> bool:
        import cv2

        grey = cv2.cvtColor(cv2.resize(frame, SMALL, interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY)
        previous, self.previous = self.previous, grey
        if previous is None:
            return False
        if np.array_equal(grey, previous):             # the camera hadn't a new picture yet: nothing to compare
            self.why = "same picture as before"
            return False
        moving = cv2.absdiff(grey, previous) > DIFF
        z = zones(face_x, face_y, SMALL[0], SMALL[1])

        def share(b):
            x0, y0, x1, y1 = b
            return float(moving[y0:y1, x0:x1].mean()) if x1 > x0 and y1 > y0 else 0.0

        face = share(z["face"])
        if face > FACE_MOVED:                          # the person moved, not only a hand: start again
            self.seen.clear()
            self.why = "person moved"
            return False
        if face > FACE_STILL:                          # a sway, or the head following them: skip this picture only
            self.why = "face area moved"
            return False
        best = max(("left", "right"), key=lambda k: share(z[k]))
        middle = None
        if share(z[best]) >= ZONE_MOTION:
            x0, y0, x1, y1 = z[best]
            ys, xs = np.nonzero(moving[y0:y1, x0:x1])
            middle = float(xs.mean()) + x0 if len(xs) else None
        self.why = "hand motion" if middle is not None else "still"
        self.seen.append((now, best if middle is not None else None, middle))
        while self.seen and now - self.seen[0][0] > WINDOW_S:
            self.seen.popleft()
        return self.waving()

    def waving(self) -> bool:
        if len(self.seen) < 4:
            return False
        sides = [s for _, s, _ in self.seen if s]
        if not sides or len(sides) < MOVING_SHARE * len(self.seen):
            return False
        side = max(set(sides), key=sides.count)
        xs = [m for _, s, m in self.seen if s == side and m is not None]
        turns, last = 0, 0.0
        for a, b in zip(xs, xs[1:], strict=False):
            step = b - a
            if abs(step) < 1.0:
                continue
            if last and (step > 0) != (last > 0):
                turns += 1
            last = step
        self.turns = turns
        return turns >= REVERSALS


class WaveBack:
    """The antennas' wave, laid over whatever they were doing, for WAVE_S."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self.clock, self.started = clock, None

    def start(self) -> None:
        self.started = self.clock()

    def active(self) -> bool:
        return self.started is not None and self.clock() - self.started < WAVE_S

    def step(self, antennas: Tuple[float, float]) -> Tuple[float, float]:
        if not self.active():
            return antennas
        t = self.clock() - self.started
        env = min(1.0, t / EASE_S, (WAVE_S - t) / EASE_S)
        env = env * env * (3 - 2 * env)
        sway = AMP_RAD * env * math.sin(2 * math.pi * WAVE_HZ * t)
        return antennas[0] + sway, antennas[1] + sway


class WaveWatcher:
    """A background thread: while `active()`, watch for a wave beside the tracked face; `wave_back()` is called on one."""

    def __init__(self, get_frame: Callable[[], Any], get_face: Callable[[], Any], active: Callable[[], bool],
                 wave_back: Callable[[], None], clock: Callable[[], float] = time.monotonic) -> None:
        self._get_frame, self._get_face, self._active, self._wave_back, self._clock = (
            get_frame, get_face, active, wave_back, clock)
        self.detector, self.last = WaveDetector(), -1e9
        self.counts: Dict[str, int] = {}
        self.most_turns, self.counted_since = 0, clock()
        self._stop = threading.Event()
        self.thread = threading.Thread(target=self._run, name="andy-wave", daemon=True)
        self.thread.start()

    def _count(self, why: str, now: float) -> None:
        """ANDY_WAVE_DEBUG: tally why, and log the tally every DEBUG_EVERY_S (counts only)."""
        if not DEBUG:
            return
        self.counts[why] = self.counts.get(why, 0) + 1
        self.most_turns = max(self.most_turns, self.detector.turns)
        if now - self.counted_since >= DEBUG_EVERY_S:
            logger.info("wave watch: %s; most swings %d of %d", ", ".join(f"{k} {v}" for k, v in sorted(self.counts.items())),
                        self.most_turns, REVERSALS)
            self.counts, self.most_turns, self.counted_since = {}, 0, now

    def look_once(self) -> bool:
        now = self._clock()
        if not self._active() or now - self.last < COOLDOWN_S:
            self._count("paused (speaking, listening, a move, tracking off)" if not self._active() else "resting", now)
            self.detector.reset()
            return False
        face = self._get_face()
        if not getattr(face, "detected", False) or face.x is None or face.y is None:
            self._count("no face", now)
            self.detector.reset()
            return False
        frame = self._get_frame()
        if frame is None:
            self._count("no picture", now)
            return False
        seen = self.detector.feed(frame, float(face.x), float(face.y), now)
        self._count(self.detector.why or "first picture", now)
        if seen:
            self.last = now
            self.detector.reset()
            logger.info("wave: waving back")
            self._wave_back()
            return True
        return False

    def _run(self) -> None:
        while not self._stop.is_set():
            try:
                self.look_once()
            except Exception:
                self.detector.reset()
            self._stop.wait(1.0 / WATCH_HZ)

    def stop(self) -> None:
        self._stop.set()


def step(manager: Any, antennas: Tuple[float, float], *, tracking: bool, speaking: bool, move_playing: bool) -> Tuple[float, float]:
    """One control tick: start the watcher once, and lay the wave back over the antennas while it plays."""
    from andy_companion.body import hold, looking_at

    waver = manager.__dict__.setdefault("_andy_wave", WaveBack())
    if "_andy_wave_watch" not in manager.__dict__:
        robot = manager.current_robot
        state = manager.__dict__.setdefault("_andy_wave_state", {"free": False})

        def back() -> None:
            waver.start()
            looking_at.set("wave", WAVE_S)

        manager.__dict__["_andy_wave_watch"] = WaveWatcher(
            lambda: robot.media.get_frame(), lambda: robot.get_tracked_face(wait=False),
            lambda: bool(state["free"]), back)
    manager.__dict__["_andy_wave_state"]["free"] = tracking and not speaking and not move_playing and not hold.active(manager)
    return waver.step(antennas)
