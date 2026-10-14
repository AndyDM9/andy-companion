"""Has someone been here lately? One timestamp, kept in memory only.

Andy's movement loop marks presence when it sees a face, sees a person (andy_companion.body.person)
or hears someone speaking; idle moments only play when someone is around. No image, audio or
identity is kept, and nothing is written to disk.
"""

from __future__ import annotations

import time
from typing import Optional

EVERY_S = 10.0
FRESH_S = 90.0
AWAY_S = 2 * 3600.0          # nobody seen for this long, then someone is: an arrival
_last = {"t": 0.0, "kind": None}
_seen = {"t": None, "arrived": None}     # a face or a person (not a voice: a TV talks too)


def mark(kind: str, now: Optional[float] = None) -> bool:
    now = now or time.time()
    if kind in ("face", "person"):
        if _seen["t"] is not None and now - _seen["t"] >= AWAY_S:
            _seen["arrived"] = now
        _seen["t"] = now
    if now - _last["t"] < EVERY_S:
        return False
    _last["t"], _last["kind"] = now, kind
    return True


def recent(max_age: float = FRESH_S, now: Optional[float] = None) -> bool:
    return (now or time.time()) - _last["t"] <= max_age


def arrived(within: float = 60.0, now: Optional[float] = None) -> bool:
    """Someone was seen in the last `within` seconds after nobody had been seen for AWAY_S."""
    a = _seen["arrived"]
    return a is not None and (now or time.time()) - a <= within


def greeted() -> None:
    _seen["arrived"] = None
