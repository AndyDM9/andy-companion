"""Thinking: the antennas show that Andy is working on an answer, so the gap never looks dead.

From the moment the person's words are understood until Andy's first sound, and while a tool runs
(a web search or a look through the camera can take four or five seconds), both antennas lean
slowly to one side and back. It is the antennas only, never the head, so it cannot tip the robot,
and it is slower than the antennas' own limits. It blends in and out over half a second, so
nothing jumps, and it never acts while the person is speaking (Pollen freezes the antennas then)
or while one of Pollen's moves owns the body.

When Andy is thinking comes from `andy_companion.turns` (the same marks that time each turn).
ANDY_THINKING=off turns it off.
"""

from __future__ import annotations

import math
import os
from typing import Optional, Tuple

ENABLED = os.environ.get("ANDY_THINKING", "on").strip().lower() not in ("off", "0", "false", "no")
LEAN_RAD = 0.30            # about 17 degrees each way
LEAN_HZ = 0.4              # one slow lean and back every 2.5 s; peak speed ~0.75 rad/s
BLEND_S = 0.5


class Thinking:
    def __init__(self) -> None:
        self.weight = 0.0
        self.last: Optional[float] = None
        self.started: Optional[float] = None

    def step(self, now: float, antennas: Tuple[float, float], active: bool) -> Tuple[float, float]:
        dt = 0.0 if self.last is None else max(0.0, min(now - self.last, 0.1))
        self.last = now
        if active and self.started is None:
            self.started = now
        target = 1.0 if active else 0.0
        if self.weight < target:
            self.weight = min(target, self.weight + dt / BLEND_S)
        elif self.weight > target:
            self.weight = max(target, self.weight - dt / BLEND_S)
        if self.weight <= 0.0:
            self.started = None
            return antennas
        # Smoothstep the blend weight; the lean starts from zero, so it never jumps.
        w = self.weight * self.weight * (3.0 - 2.0 * self.weight)
        lean = LEAN_RAD * math.sin(2.0 * math.pi * LEAN_HZ * (now - (self.started or now)))
        # The same offset on both antennas: they lean together, unlike breathing's mirrored sway.
        return float(antennas[0]) + w * lean, float(antennas[1]) + w * lean
