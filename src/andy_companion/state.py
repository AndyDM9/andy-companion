"""Is Andy awake, asleep, or quiet until a given time? One small owner-only file.

The supervisor reads it to decide what to do when the app stops, and when to wake Andy.
"""

from __future__ import annotations

import json
import contextlib
import logging
import math
import os
import tempfile
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from andy_companion.reminders import DATA_DIR

FILE = DATA_DIR / "state.json"
MAX_QUIET_MIN = 24 * 60
_last_warning = None


def _timestamp(value: Any) -> bool:
    if type(value) not in (int, float) or not 0 <= value <= 253402300799:
        return False
    try:
        if not math.isfinite(value):
            return False
        datetime.fromtimestamp(value)
        return True
    except (OverflowError, OSError, ValueError):
        return False


def _checked(data: Any, *, returning: bool = False) -> Dict[str, Any]:
    """Only supported control metadata; a reminder return state cannot nest another return state."""
    keys = {"mode", "until", "reminders"} if returning else {"mode", "until", "since", "return_to"}
    if not isinstance(data, dict) or data.keys() - keys:
        raise ValueError("Saved mode has unsupported fields.")
    mode, until = data.get("mode"), data.get("until")
    if mode not in (("quiet", "asleep") if returning else ("awake", "quiet", "asleep")):
        raise ValueError("Saved mode is not supported.")
    if (mode == "quiet" and (not _timestamp(until) or until <= 0)) or (mode != "quiet" and until is not None):
        raise ValueError("Saved mode deadline is not supported.")
    out = {**data, "until": until}
    if "since" in data and not _timestamp(data["since"]):
        raise ValueError("Saved mode timestamp is not supported.")
    if returning:
        ids = data.get("reminders", [])
        if not isinstance(ids, list) or not all(isinstance(v, str) and 0 < len(v) <= 64 for v in ids):
            raise ValueError("Saved reminder return state is not supported.")
    elif "return_to" in data:
        if mode != "awake":
            raise ValueError("Saved reminder return state is not supported.")
        out["return_to"] = _checked(data["return_to"], returning=True)
    return out


def _write(data: Dict[str, Any]) -> None:
    from andy_companion import board

    data = _checked(data)
    with board.locked(FILE):
        fd, tmp = tempfile.mkstemp(dir=FILE.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, allow_nan=False)
            os.replace(tmp, FILE)  # mkstemp is already owner-only
        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp)


def current(now: Optional[datetime] = None) -> Dict[str, Any]:
    """{"mode": "awake" | "asleep" | "quiet", "until": timestamp or None}. An expired quiet reads
    as quiet still; the supervisor ends it (so it can wake Andy). Asleep and quiet also carry "since",
    when they began; awake after a reminder woke Andy carries "return_to", the mode to go back to.
    An existing unreadable file stays untouched and returns asleep/unreadable until an explicit mode
    change. Automatic wakes are paused; the supervisor's explicit wake listener remains available.
    A missing file keeps the normal first-run awake default.
    """
    global _last_warning
    try:
        data = _checked(json.loads(FILE.read_text()))
    except FileNotFoundError:
        _last_warning = None
        return {"mode": "awake", "until": None}
    except (OSError, ValueError, RecursionError):
        try:
            stat = FILE.stat()
            key = (FILE, stat.st_mtime_ns, stat.st_size)
        except OSError:
            key = (FILE, None, None)
        if key != _last_warning:
            logging.getLogger("andy.state").warning("Saved mode could not be read; staying asleep until an explicit wake or mode change.")
            _last_warning = key
        return {"mode": "asleep", "until": None, "unreadable": True}
    _last_warning = None
    return data


def quiet_for(minutes: float, now: Optional[datetime] = None) -> datetime:
    try:
        if isinstance(minutes, bool) or not isinstance(minutes, (str, int, float)):
            raise ValueError()
        minutes = float(minutes)
        if not math.isfinite(minutes) or not 0 < minutes <= MAX_QUIET_MIN:
            raise ValueError()
    except (TypeError, ValueError, OverflowError):
        raise ValueError("Quiet needs a positive duration up to one day.") from None
    now = now or datetime.now()
    until = now + timedelta(minutes=minutes)
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
