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
_last = {"t": 0.0, "kind": None}


def mark(kind: str, now: Optional[float] = None) -> bool:
    now = now or time.time()
    if now - _last["t"] < EVERY_S:
        return False
    _last["t"], _last["kind"] = now, kind
    return True


def recent(max_age: float = FRESH_S, now: Optional[float] = None) -> bool:
    return (now or time.time()) - _last["t"] <= max_age
