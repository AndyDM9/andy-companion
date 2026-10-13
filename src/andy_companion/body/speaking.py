"""Whether Andy's voice is coming out of the speaker right now.

Pollen's app pushes the reply's audio to the robot as it arrives and the speaker plays it in real
time, so the voice keeps going for seconds after the server says the reply is done (the signals
the app has, response.done and set_speaking, end at generation; found 2026-10-07 when the palm
watch, keyed to them, looked for only a second or two per reply). The launcher reports each push
(`pushed`) and each barge-in (`cleared`); each chunk extends "talking until" by its own length.
"""

from __future__ import annotations

import time
import threading
from typing import Optional

TAIL_S = 0.3                  # the speaker's own buffer after the last sample

_lock = threading.Lock()
_until = 0.0


def pushed(samples: int, rate: float, now: Optional[float] = None) -> None:
    global _until
    if rate <= 0 or samples <= 0:
        return
    now = time.monotonic() if now is None else now
    with _lock:
        _until = max(_until, now) + samples / rate


def remaining(now: Optional[float] = None) -> float:
    """Seconds of Andy's voice still to play."""
    now = time.monotonic() if now is None else now
    with _lock:
        return max(0.0, _until - now)


def cleared() -> None:
    global _until
    with _lock:
        _until = 0.0


def speaking(now: Optional[float] = None) -> bool:
    now = time.monotonic() if now is None else now
    with _lock:
        return now < _until + TAIL_S
