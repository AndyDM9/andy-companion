"""Where the person's things are (PLAN B46): "Andy, my keys are here."

Andy asks "Shall I remember where they are?"; only after a yes (consent.SAVING) it looks, and keeps the thing, the
direction its head turned to see it (yaw and pitch), its words for the place ("on the hall table") and when. Never
a picture. A later "where are my keys?" turns straight to that place first and checks up close (finder.find); if
they aren't there any more, Andy says so and looks around. Kept places are listed by what_you_remember and on the
settings page, each deletable, and forgotten on request (forget_place); each is dropped after KEEP_DAYS.

Separately, a thing Andy found when asked is remembered in memory only, for LAST_SEEN_S, so asking again soon turns
there first; it is never written down.
"""

from __future__ import annotations

import json
import os
import re
import secrets
import tempfile
import time
from typing import Any, Dict, List, Optional

from andy_companion.board import locked
from andy_companion.reminders import DATA_DIR

FILE = DATA_DIR / "places.json"
MAX_PLACES = 30
KEEP_DAYS = 30
LAST_SEEN_S = 6 * 3600
_last_seen: Dict[str, Dict[str, Any]] = {}


def _key(what: str) -> str:
    """The thing's name for matching: lower case, without my/the, its last word singular ("reading glasses" ->
    "glasses", "keys" -> "key"): so "my glasses" finds "my reading glasses"."""
    words = re.sub(r"[^\w\s]", " ", str(what or "").lower()).split()
    words = [w for w in words if w not in ("my", "the", "a", "an", "his", "her", "their", "mis", "mi", "las", "los", "el", "la")]
    if not words:
        return ""
    last = words[-1]
    if last.endswith("ses") or last in ("glasses", "lentes", "gafas"):
        return last
    return last[:-1] if last.endswith("s") and len(last) > 3 else last


def _load() -> List[Dict[str, Any]]:
    try:
        items = json.loads(FILE.read_text())
    except (OSError, ValueError):
        return []
    now = time.time()
    return [p for p in items if isinstance(p, dict) and now - float(p.get("at", 0)) < KEEP_DAYS * 86400]


def _save(items: List[Dict[str, Any]]) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=FILE.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(items, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, FILE)


def keep(what: str, where: str, yaw: Optional[float] = None, pitch: Optional[float] = None,
         now: Optional[float] = None) -> Dict[str, Any]:
    """Keep where a thing is (one place per thing: the newest replaces the last). Only after the person said yes."""
    what = " ".join(str(what or "").split())[:60]
    where = " ".join(str(where or "").split())[:120]
    if not _key(what) or not where:
        raise ValueError("I need to know what it is and where.")
    item = {"id": secrets.token_hex(3), "what": what, "where": where, "at": now or time.time(),
            "yaw": None if yaw is None else round(float(yaw), 4), "pitch": None if pitch is None else round(float(pitch), 4)}
    with locked(FILE):          # the settings page deletes from another process (2026-10-25 review)
        items = [p for p in _load() if _key(p["what"]) != _key(what)] + [item]
        _save(items[-MAX_PLACES:])
    return item


def kept() -> List[Dict[str, Any]]:
    return _load()


def remove(item_id: str) -> bool:
    with locked(FILE):
        items = _load()
        left = [p for p in items if p.get("id") != str(item_id)]
        if len(left) == len(items):
            return False
        _save(left)
    return True


def forget(what: str) -> int:
    """Forget where a thing is (kept and last seen). Returns how many places were forgotten."""
    key = _key(what)
    with locked(FILE):
        items = _load()
        left = [p for p in items if _key(p["what"]) != key]
        if len(left) != len(items):
            _save(left)
    seen = _last_seen.pop(key, None)
    return len(items) - len(left) + (1 if seen else 0)


def saw(what: str, where: str, yaw: float, pitch: float, now: Optional[float] = None) -> None:
    """A thing Andy found when asked: remembered in memory only, for LAST_SEEN_S."""
    key = _key(what)
    if key:
        _last_seen[key] = {"what": what, "where": where, "yaw": float(yaw), "pitch": float(pitch),
                           "at": now or time.time(), "told": False}


def recall(what: str, now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """Where to look first for a thing: the place the person had Andy keep, or where Andy last saw it (newer wins)."""
    key, now = _key(what), now or time.time()
    told = next((dict(p, told=True) for p in reversed(_load()) if _key(p["what"]) == key), None)
    seen = _last_seen.get(key)
    if seen and now - seen["at"] > LAST_SEEN_S:
        _last_seen.pop(key, None)
        seen = None
    if told and seen:
        return told if told["at"] >= seen["at"] else dict(seen)
    return told or (dict(seen) if seen else None)


def ago(at: float, now: Optional[float] = None) -> str:
    """'at 3:05 pm' today, 'yesterday', or 'on Tuesday', in plain words for Andy to say."""
    from datetime import datetime

    then, today = datetime.fromtimestamp(at), datetime.fromtimestamp(now or time.time())
    if then.date() == today.date():
        return "at " + then.strftime("%-I:%M %p").replace("AM", "am").replace("PM", "pm")
    if (today.date() - then.date()).days == 1:
        return "yesterday"
    return "on " + then.strftime("%A")
