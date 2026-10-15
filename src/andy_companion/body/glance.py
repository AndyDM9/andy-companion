"""Glance at the screen: when Andy puts something new on the TV, it turns its head to the screen for
a moment and back to the person, so the person's eyes follow it there.

ElliQ does this with the screen it is built beside; the gesture says "look, it's over here" without
words, and it is how people point things out to each other. Andy's screen is a TV whose place in the
room only the household knows, so the direction is a setting (`tv_yaw`, degrees, + to Andy's left;
`tv_height`: above, level or below), set on the settings page with a "Show me" check. Until it is
set, Andy never glances.

When: a card that is new on the screen (a different kind or title from the last; the research
card's progress updates are the same card), at most once every EVERY_S. Not while the person is
speaking (it waits up to WAIT_S for them to finish, then lets it go), not while another move plays,
not when Andy is asleep or quiet, not with face following off, and not with nobody around.

How: a move through Pollen's queue, marked as Andy's own head move, so face following lets go of
the head for it and takes it back afterwards (idle.take_step, release_step; gaze while Andy speaks).
The head turns with a minimum-jerk curve (peak speed under PEAK_RAD_S), holds, and comes back to
exactly where it was; both antennas lift a little while it looks. The body stays where it faces.

A thread reads the screen and the settings twice a second; the control loop only reads what the
thread saw, so no file is read at 100 Hz. Nothing is logged but the direction and the card's kind.

ANDY_GLANCE=off turns it off whatever the setting.
"""

from __future__ import annotations

import os
import math
import logging
import threading
import time
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger("andy.glance")

ENABLED = os.environ.get("ANDY_GLANCE", "on").strip().lower() not in ("off", "0", "false", "no")
EVERY_S = 20.0
WAIT_S = 6.0
POLL_S = 0.5
HOLD_S = 1.5
MIN_TURN_S = 0.6
PEAK_RAD_S = 1.5          # the head's top speed on the way; well inside what Pollen's own moves use
MAX_YAW_DEG = 120.0
HEIGHT_DEG = {"above": -12.0, "level": 0.0, "below": 12.0}   # positive pitch looks down
PERK_RAD = 0.15           # both antennas, mirrored, about 9 degrees


def direction(s: Optional[Dict[str, Any]] = None) -> Optional[Tuple[float, float]]:
    """(yaw, pitch) in radians for the TV, or None when it isn't set or glancing is off."""
    if s is None:
        from andy_companion import settings

        s = settings.get()
    if not ENABLED or not s.get("tv_glance", True) or s.get("tv_yaw") is None:
        return None
    try:
        yaw = max(-MAX_YAW_DEG, min(MAX_YAW_DEG, float(s["tv_yaw"])))
    except (TypeError, ValueError):
        return None
    return math.radians(yaw), math.radians(HEIGHT_DEG.get(s.get("tv_height") or "level", 0.0))


def card_key(showing: Optional[Dict[str, Any]]) -> Optional[str]:
    """What makes a card new: its kind and title (and the photo). Progress on the same card isn't."""
    if not showing:
        return None
    return f"{showing.get('kind', '')}|{showing.get('title', '')}|{showing.get('photo', '')}"


class Watcher:
    """Decides when to glance. Pure: fed what the screen shows and what Andy is doing."""

    def __init__(self) -> None:
        self.seen: Optional[str] = None
        self.started = False
        self.pending: Optional[float] = None
        self.last = -1e9

    def saw(self, key: Optional[str], now: float) -> None:
        if not self.started:                 # what was already on the screen at start isn't new
            self.started, self.seen = True, key
            return
        if key != self.seen:
            self.seen = key
            if key is not None:
                self.pending = now

    def ready(self, now: float, *, listening: bool, move_playing: bool, awake: bool) -> bool:
        if self.pending is None:
            return False
        if now - self.pending > WAIT_S or not awake:
            self.pending = None              # too late to point at it, or Andy is resting
            return False
        if listening or move_playing:
            return False                     # wait: never turn away while they talk
        self.pending = None
        if now - self.last < EVERY_S:
            return False
        self.last = now
        return True


def _ease(x: float) -> float:
    """Minimum jerk: smooth start and stop, no sudden speed."""
    x = max(0.0, min(1.0, x))
    return x * x * x * (10.0 + x * (-15.0 + 6.0 * x))


def _rpy(pose) -> Tuple[float, float, float]:
    R = pose[:3, :3]
    return (math.atan2(R[2, 1], R[2, 2]), math.asin(max(-1.0, min(1.0, -R[2, 0]))), math.atan2(R[1, 0], R[0, 0]))


def _pose(roll: float, pitch: float, yaw: float, xyz):
    import numpy as np

    cr, sr, cp, sp, cy, sy = math.cos(roll), math.sin(roll), math.cos(pitch), math.sin(pitch), math.cos(yaw), math.sin(yaw)
    out = np.eye(4)
    out[:3, :3] = (np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
                   @ np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
                   @ np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]]))
    out[:3, 3] = xyz
    return out


class Glance:
    """Turn to the TV, hold, and come back to the starting look."""

    andy_owns_head = True

    def __init__(self, start_pose, antennas: Tuple[float, float], tv: Tuple[float, float],
                 perk: float = PERK_RAD, roll: float = 0.0, hold_s: float = HOLD_S):
        """To (yaw, pitch) from `tv`, with `roll` (body.expressive's head tilt), and back; `perk` lifts the
        antennas while it looks (0 for none)."""
        import numpy as np

        self.start = np.array(start_pose, dtype=float)
        self.antennas = (float(antennas[0]), float(antennas[1]))
        self.r0, self.p0, self.y0 = _rpy(self.start)
        self.dyaw = (tv[0] - self.y0 + math.pi) % (2 * math.pi) - math.pi
        self.dpitch = tv[1] - self.p0
        self.droll = roll - self.r0
        self.perk, self.hold_s = float(perk), float(hold_s)
        # Minimum jerk peaks at 1.875 times the average speed.
        big = max(abs(self.dyaw), abs(self.dpitch))
        self.turn_s = max(MIN_TURN_S, 1.875 * big / PEAK_RAD_S)

    @property
    def duration(self) -> float:
        return 2 * self.turn_s + self.hold_s

    def weight(self, t: float) -> float:
        if t < self.turn_s:
            return _ease(t / self.turn_s)
        if t < self.turn_s + self.hold_s:
            return 1.0
        return 1.0 - _ease((t - self.turn_s - self.hold_s) / self.turn_s)

    def evaluate(self, t: float):
        import numpy as np

        w = self.weight(t)
        if w <= 0.0:
            head = self.start.copy()
        else:
            head = _pose(self.r0 + w * self.droll, self.p0 + w * self.dpitch, self.y0 + w * self.dyaw, self.start[:3, 3])
        lift = self.perk * w
        return head, np.array([self.antennas[0] - lift, self.antennas[1] + lift]), 0.0


def queueable(g: Glance) -> Any:
    """The glance as a Pollen Move (its queue takes only those)."""
    from reachy_mini.motion.move import Move

    class GlanceMove(Move):
        andy_owns_head = True

        @property
        def duration(self) -> float:
            return g.duration

        def evaluate(self, t: float):
            return g.evaluate(t)

    return GlanceMove()


# --- in the robot's process ----------------------------------------------------------------------

_seen: Dict[str, Any] = {"key": None, "tv": None, "awake": True, "fresh": False}
_thread: Optional[threading.Thread] = None


def _look_once() -> None:
    from andy_companion import board, settings, state

    s = settings.get()
    _seen["tv"] = direction(s)
    _seen["awake"] = state.current().get("mode", "awake") == "awake"
    _seen["key"] = card_key(board.showing())
    _seen["fresh"] = True


def watch() -> bool:
    """Start the thread that reads the screen and the settings. Once per process."""
    global _thread
    if not ENABLED or _thread is not None:
        return False

    def loop() -> None:
        while True:
            try:
                _look_once()
            except Exception:
                logger.debug("glance: could not read the screen", exc_info=True)
            time.sleep(POLL_S)

    _thread = threading.Thread(target=loop, name="andy-glance", daemon=True)
    _thread.start()
    return True


def step(manager, now: float, antennas, *, listening: bool, move_playing: bool, tracking: bool) -> bool:
    """One control tick: queue a glance when one is due. True when it queued one."""
    if not _seen["fresh"]:
        return False
    watcher = manager.__dict__.setdefault("_andy_glance", Watcher())
    watcher.saw(_seen["key"], now)
    tv = _seen["tv"]
    from andy_companion.body import presence

    awake = bool(_seen["awake"]) and tv is not None and tracking and presence.recent()
    if not watcher.ready(now, listening=listening, move_playing=move_playing, awake=awake):
        return False
    g = Glance(manager.current_robot.get_current_head_pose(), (float(antennas[0]), float(antennas[1])), tv)
    manager.queue_move(queueable(g))
    from andy_companion.body import looking_at
    looking_at.set("screen", float(getattr(g, "duration", 2.5)))
    logger.info("glance at the screen (%s), %.0f degrees", (_seen["key"] or "").split("|")[0],
                math.degrees(tv[0]))
    return True
