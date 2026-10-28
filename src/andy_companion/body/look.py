"""Look somewhere and hold: the head turns to a direction and stays there for a while.

The finder ("where are my glasses?") queues a few of these to sweep the room and one more to point at
what it found. Each turns from the pose the previous one ended in, with the same minimum-jerk curve and
speed limit as the glance (body.glance), and holds; Pollen's queue plays them back to back, so the head
stays Andy's own for the whole sweep and face following takes it back after the last (idle.release_step).
The body stays where it faces. Antennas are held where they were.
"""

from __future__ import annotations

import math
from typing import Any, Tuple

from andy_companion.body.glance import MIN_TURN_S, PEAK_RAD_S, _ease, _pose, _rpy

MAX_YAW_RAD = math.radians(150)


class HoldLook:
    """From `start_pose` to (yaw, pitch), then hold for `hold_s`."""

    andy_owns_head = True

    def __init__(self, start_pose, antennas: Tuple[float, float], yaw: float, pitch: float, hold_s: float):
        import numpy as np

        self.start = np.array(start_pose, dtype=float)
        self.antennas = (float(antennas[0]), float(antennas[1]))
        self.r0, self.p0, self.y0 = _rpy(self.start)
        yaw = max(-MAX_YAW_RAD, min(MAX_YAW_RAD, yaw))
        # The direct way round: both ends face forward, so never through behind the robot (2026-10-28 review: +94 to
        # -94 degrees went +172, past straight behind). Only a reading beyond the head's own range is wrapped.
        raw = yaw - self.y0
        self.dyaw = raw if abs(raw) <= 2 * MAX_YAW_RAD else (raw + math.pi) % (2 * math.pi) - math.pi
        self.dpitch = pitch - self.p0
        self.droll = -self.r0
        self.turn_s = max(MIN_TURN_S, 1.875 * max(abs(self.dyaw), abs(self.dpitch)) / PEAK_RAD_S)
        self.hold_s = float(hold_s)
        self.end = _pose(0.0, pitch, self.y0 + self.dyaw, self.start[:3, 3])

    @property
    def duration(self) -> float:
        return self.turn_s + self.hold_s

    def evaluate(self, t: float):
        import numpy as np

        w = _ease(t / self.turn_s) if t < self.turn_s else 1.0
        head = _pose(self.r0 + w * self.droll, self.p0 + w * self.dpitch, self.y0 + w * self.dyaw, self.start[:3, 3])
        return head, np.array(self.antennas), 0.0


def queueable(look: HoldLook) -> Any:
    """The look as a Pollen Move (its queue takes only those)."""
    from reachy_mini.motion.move import Move

    class HoldLookMove(Move):
        andy_owns_head = True

        @property
        def duration(self) -> float:
            return look.duration

        def evaluate(self, t: float):
            return look.evaluate(t)

    return HoldLookMove()
