"""Is Andy awake, asleep, or quiet until a given time? One small owner-only file.

The supervisor reads it to decide what to do when the app stops, and when to wake Andy.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from andy_companion.reminders import DATA_DIR

FILE = DATA_DIR / "state.json"
MAX_QUIET_MIN = 24 * 60


def _write(data: Dict[str, Any]) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=FILE.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, FILE)


def current(now: Optional[datetime] = None) -> Dict[str, Any]:
    """{"mode": "awake" | "asleep" | "quiet", "until": timestamp or None}. An expired quiet reads
    as quiet still; the supervisor ends it (so it can wake Andy)."""
    try:
        data = json.loads(FILE.read_text())
        if data.get("mode") in ("awake", "asleep", "quiet"):
            return data
    except (OSError, ValueError):
        pass
    return {"mode": "awake", "until": None}


def quiet_for(minutes: float, now: Optional[datetime] = None) -> datetime:
    if not 0 < float(minutes) <= MAX_QUIET_MIN:
        raise ValueError("Quiet can last from 1 minute to a day.")
    until = (now or datetime.now()) + timedelta(minutes=float(minutes))
    _write({"mode": "quiet", "until": until.timestamp()})
    return until


def asleep() -> None:
    _write({"mode": "asleep", "until": None})


def awake() -> None:
    _write({"mode": "awake", "until": None})
