"""Listening ears: while the person speaks, both antennas lift a little and hold, like a listener's
attention, and settle back when they stop.

Pollen's app freezes the antennas while the person speaks (so motion never sounds like speech); this
adds a small, steady offset on top of that freeze: no movement while it holds, only the half-second
blend in and out, slower than the antennas' own limits. Antennas only, never the head. It mirrors the
two antennas (breathing's shape), unlike the thinking lean, which tilts them together.

ANDY_LISTENING=off turns it off; ANDY_LISTENING_SIGN=-1 flips the direction if, on a given robot, the
antennas go down instead of up.
"""

from __future__ import annotations

import os
from typing import Optional, Tuple

ENABLED = os.environ.get("ANDY_LISTENING", "on").strip().lower() not in ("off", "0", "false", "no")
SIGN = -1.0 if os.environ.get("ANDY_LISTENING_SIGN", "1").strip() == "-1" else 1.0
LIFT_RAD = 0.25            # about 14 degrees each
BLEND_S = 0.5


class Listening:
    def __init__(self) -> None:
        self.weight = 0.0
        self.last: Optional[float] = None

    def step(self, now: float, antennas: Tuple[float, float], active: bool) -> Tuple[float, float]:
        dt = 0.0 if self.last is None else max(0.0, min(now - self.last, 0.1))
        self.last = now
        target = 1.0 if active else 0.0
        if self.weight < target:
            self.weight = min(target, self.weight + dt / BLEND_S)
        elif self.weight > target:
            self.weight = max(target, self.weight - dt / BLEND_S)
        if self.weight <= 0.0:
            return antennas
        w = self.weight * self.weight * (3.0 - 2.0 * self.weight)
        lift = SIGN * LIFT_RAD * w
        # Mirrored, as breathing's sway: the left antenna's angle is the right one's negative.
        return float(antennas[0]) - lift, float(antennas[1]) + lift
