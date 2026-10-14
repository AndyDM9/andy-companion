"""After a joke's punchline: a small, happy wiggle of both antennas, once Andy's voice stops.

The joke tool arms it (`arm`); it waits for Andy to start speaking, then for the voice to stop (the
punchline is the end of the reply), then both antennas tilt together, side to side, for about a
second and settle. Amplitude 0.1 rad at 2 Hz under a smooth envelope: peak about 1.3 rad/s, under the
antennas' 2 rad/s and far from a button press. Antennas only. Stopped at once if the person starts
speaking (Pollen freezes the antennas then) or a move plays; forgotten if Andy hasn't spoken within
ARM_FOR_S. ANDY_GIGGLE=off turns it off.
"""

from __future__ import annotations

import math
import os
import time
from typing import Optional, Tuple

from andy_companion.body import speaking

ENABLED = os.environ.get("ANDY_GIGGLE", "on").strip().lower() not in ("off", "0", "false", "no")
ARM_FOR_S = 40.0
WIGGLE_S = 1.0
AMP_RAD = 0.1
FREQ_HZ = 2.0

_armed = {"at": None, "heard": False, "pushes": 0}


def arm(now: Optional[float] = None) -> None:
    _armed["at"] = time.monotonic() if now is None else now
    _armed["heard"] = False
    _armed["pushes"] = speaking.pushes()      # audio already queued ("Sure, here's one!") doesn't count


class Giggle:
    def __init__(self, clock=time.monotonic, talking=speaking.speaking, pushes=speaking.pushes) -> None:
        self.clock, self.talking, self.pushes = clock, talking, pushes
        self.start: Optional[float] = None

    def step(self, antennas: Tuple[float, float], free: bool) -> Tuple[float, float]:
        now = self.clock()
        if self.start is None and _armed["at"] is not None:
            if now - _armed["at"] > ARM_FOR_S:
                _armed["at"] = None                       # the joke was never told aloud
            elif self.talking(now) and self.pushes() > _armed["pushes"]:
                _armed["heard"] = True                    # the joke itself is playing
            elif _armed["heard"] and free:
                self.start, _armed["at"] = now, None      # the punchline has just ended
        if self.start is None:
            return antennas
        t = now - self.start
        if t >= WIGGLE_S or not free:
            self.start = None
            return antennas
        off = AMP_RAD * math.sin(math.pi * t / WIGGLE_S) * math.sin(2 * math.pi * FREQ_HZ * t)
        return float(antennas[0]) + off, float(antennas[1]) + off
