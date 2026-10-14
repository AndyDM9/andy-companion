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
    as quiet still; the supervisor ends it (so it can wake Andy). Asleep and quiet also carry "since",
    when they began; awake after a reminder woke Andy carries "return_to", the mode to go back to."""
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
    now = now or datetime.now()
    until = now + timedelta(minutes=float(minutes))
    quiet_until(until.timestamp(), now)
    return until


def quiet_until(until: float, now: Optional[datetime] = None) -> None:
    _write({"mode": "quiet", "until": until, "since": (now or datetime.now()).timestamp()})


def asleep(now: Optional[datetime] = None) -> None:
    _write({"mode": "asleep", "until": None, "since": (now or datetime.now()).timestamp()})


def awake(return_to: Optional[Dict[str, Any]] = None) -> None:
    """Awake. return_to (set only by the supervisor when a reminder wakes Andy) is the quiet or sleep to go
    back to once the reminder is said; any later change of mode (goodnight, be quiet) replaces it."""
    _write({"mode": "awake", "until": None, **({"return_to": return_to} if return_to else {})})


def install_sleep_tool(tool_class=None) -> bool:
    """"Go to sleep" means asleep, whatever came before. Pollen's go_to_sleep only stops the app, and the
    supervisor then keeps the mode it finds: after "be quiet" that was quiet, which ends by itself, so on
    2026-10-13 "be quiet" then "go to sleep" would have woken Andy ten minutes later. Asleep first."""
    if tool_class is None:
        from reachy_mini_conversation_app.tools.go_to_sleep import GoToSleep as tool_class
    original = tool_class.__call__
    if getattr(original, "_andy_asleep", False):
        return False

    async def go_to_sleep(self, deps, **kwargs):
        try:
            asleep()
        except Exception:
            pass
        return await original(self, deps, **kwargs)

    go_to_sleep._andy_asleep = True
    tool_class.__call__ = go_to_sleep
    return True
