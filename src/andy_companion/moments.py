"""Moments: dated things the person agreed Andy may remember, so Andy can follow up.

"Sofia's recital is on Thursday." Andy asks "Shall I remember that?"; only after a yes is it kept,
with its date. On the day it is part of the plan; the day after, Andy may ask how it went. Each
moment is deleted a week after its date, or at once when the person asks. Nothing else from the
conversation is kept: this is consent-based continuity, not a recording.
"""

from __future__ import annotations

import json
import os
import secrets
import tempfile
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from andy_companion.reminders import DATA_DIR

FILE = DATA_DIR / "moments.json"
MAX_TEXT = 160
KEEP_DAYS = 7
MAX_MOMENTS = 40


def _load() -> List[Dict[str, Any]]:
    try:
        return json.loads(FILE.read_text())
    except (OSError, ValueError):
        return []


def _save(items: List[Dict[str, Any]]) -> None:
    FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=FILE.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(items, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, FILE)


def parse_day(value: str, today: Optional[date] = None) -> date:
    today = today or date.today()
    v = " ".join(str(value).lower().split())
    if v in ("today", ""):
        return today
    if v == "tomorrow":
        return today + timedelta(days=1)
    names = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    if v.removeprefix("on ").removeprefix("next ") in names:
        ahead = (names.index(v.removeprefix("on ").removeprefix("next ")) - today.weekday()) % 7
        return today + timedelta(days=ahead or 7)
    try:
        return date.fromisoformat(v)
    except ValueError:
        raise ValueError("Say the day as today, tomorrow, a weekday, or a date like 2026-10-16.") from None


def add(what: str, day: str, today: Optional[date] = None) -> Dict[str, Any]:
    text = " ".join(str(what).split())[:MAX_TEXT]
    if not text:
        raise ValueError("What should I remember?")
    on = parse_day(day, today)
    items = [m for m in _load() if not _expired(m, today)]
    item = {"id": secrets.token_hex(3), "what": text, "on": on.isoformat()}
    _save((items + [item])[-MAX_MOMENTS:])
    return item


def _expired(m: Dict[str, Any], today: Optional[date] = None) -> bool:
    return date.fromisoformat(m["on"]) + timedelta(days=KEEP_DAYS) < (today or date.today())


def tidy(today: Optional[date] = None) -> int:
    items = _load()
    kept = [m for m in items if not _expired(m, today)]
    if len(kept) != len(items):
        _save(kept)
    return len(items) - len(kept)


def on_day(day: date) -> List[Dict[str, Any]]:
    return [m for m in _load() if m["on"] == day.isoformat()]


def upcoming(today: Optional[date] = None, days: int = 14) -> List[Dict[str, Any]]:
    today = today or date.today()
    return sorted((m for m in _load() if today <= date.fromisoformat(m["on"]) <= today + timedelta(days=days)),
                  key=lambda m: m["on"])


def forget(text_or_id: str) -> int:
    key = " ".join(str(text_or_id).lower().split())
    items = _load()
    kept = [m for m in items if m["id"] != key and key not in m["what"].lower()]
    if len(kept) != len(items):
        _save(kept)
    return len(items) - len(kept)


def spoken_day(on: str, today: Optional[date] = None) -> str:
    today = today or date.today()
    d = date.fromisoformat(on)
    if d == today:
        return "today"
    if d == today + timedelta(days=1):
        return "tomorrow"
    if d == today - timedelta(days=1):
        return "yesterday"
    return d.strftime("%A %-d %B")
