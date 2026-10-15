"""What Andy's head is turned to right now, for the TV's line under its state ("Looking at you").

The behaviours that move the head say so for as long as their move lasts: following the person's face
while speaking (gaze.py), a glance at the screen (glance.py), the room search and pointing (finder.py).
Only one of a few names ever leaves this process, never a picture, a position or a person.
"""

from __future__ import annotations

import time
from typing import Optional

TARGETS = ("you", "screen", "room", "pointing")
_now = {"what": "", "until": 0.0}


def set(what: str, for_s: float, now: Optional[float] = None) -> None:     # noqa: A001 - the module's verb
    if what in TARGETS:
        t = time.monotonic() if now is None else now
        _now.update(what=what, until=t + max(0.0, float(for_s)))


def current(now: Optional[float] = None) -> str:
    t = time.monotonic() if now is None else now
    return _now["what"] if t <= _now["until"] else ""


def clear() -> None:
    _now.update(what="", until=0.0)
