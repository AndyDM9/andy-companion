"""Reminders at the times the person chooses, in their own words.

Kept in Andy's own owner-only file. A one-off reminder is deleted once Andy has said it; a daily
one moves to the same time the next day. Nothing else about the conversation is stored.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import logging
import os
import secrets
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

DATA_DIR = Path(os.environ.get("ANDY_DATA_DIR", Path.home() / ".local" / "share" / "andy-companion"))
STORE = DATA_DIR / "reminders.json"
MAX_TEXT = 200
REPEATS = (None, "daily")


def _load() -> List[Dict[str, Any]]:
    """The reminders; a file that can't be read as them is set aside (never overwritten) and Andy starts afresh."""
    try:
        items = json.loads(STORE.read_text())
    except FileNotFoundError:
        return []
    except (OSError, ValueError):            # ValueError covers a broken file and bad UTF-8 (2026-10-25 review)
        items = None
    if isinstance(items, list):
        return items
    with contextlib.suppress(OSError):
        aside = STORE.with_name(f"reminders.unreadable-{int(time.time())}.json")
        os.replace(STORE, aside)
        logging.getLogger("andy.reminders").warning("The reminders file couldn't be read; set aside as %s", aside.name)
    return []


def _save(items: List[Dict[str, Any]]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=STORE.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(items, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, STORE)


@contextmanager
def _locked() -> Iterator[None]:
    STORE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(STORE.with_suffix(".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


def due_time(minutes: Optional[float] = None, at: Optional[str] = None, now: Optional[datetime] = None) -> datetime:
    """In N minutes, or at HH:MM (today, or tomorrow if that time has passed)."""
    now = now or datetime.now()
    if minutes is not None:
        if not 0 < float(minutes) <= 7 * 24 * 60:
            raise ValueError("Minutes must be between 1 and a week.")
        return now + timedelta(minutes=float(minutes))
    if at:
        try:
            hour, minute = (int(x) for x in str(at).strip().split(":"))
            when = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            raise ValueError("Say the time as HH:MM, for example 17:30.") from None
        return when if when > now else when + timedelta(days=1)
    raise ValueError("Say when: in how many minutes, or at what time.")


def add(text: str, minutes: Optional[float] = None, at: Optional[str] = None,
        repeat: Optional[str] = None, now: Optional[datetime] = None) -> Dict[str, Any]:
    text = " ".join(str(text).split())[:MAX_TEXT]
    if not text:
        raise ValueError("What should I remind you about?")
    if repeat not in REPEATS:
        raise ValueError("A reminder can be once or daily.")
    if repeat == "daily" and not at:
        raise ValueError("A daily reminder needs a time of day.")
    when = due_time(minutes, at, now)
    item = {"id": secrets.token_hex(3), "text": text, "due": when.timestamp(), "repeat": repeat,
            "created": time.time()}
    with _locked():
        items = _load()
        items.append(item)
        _save(items)
    return item


def pending() -> List[Dict[str, Any]]:
    return sorted(_load(), key=lambda r: r["due"])


def due(now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    cutoff = (now or datetime.now()).timestamp()
    return [r for r in pending() if r["due"] <= cutoff]


def cancel(reminder_id: str) -> bool:
    with _locked():
        items = _load()
        kept = [r for r in items if r["id"] != reminder_id]
        if len(kept) == len(items):
            return False
        _save(kept)
    return True


def said(reminder_id: str, now: Optional[datetime] = None) -> None:
    """Andy has said it: delete a one-off reminder; move a daily one to its next time."""
    now = now or datetime.now()
    with _locked():
        items = _load()
        kept = []
        for r in items:
            if r["id"] != reminder_id:
                kept.append(r)
            elif r.get("repeat") == "daily":
                when = datetime.fromtimestamp(r["due"])
                while when <= now:
                    when += timedelta(days=1)
                kept.append({**r, "due": when.timestamp()})
        _save(kept)


def spoken_time(ts: float, now: Optional[datetime] = None) -> str:
    now = now or datetime.now()
    when = datetime.fromtimestamp(ts)
    if when.date() == now.date():
        day = "today"
    elif when.date() == (now + timedelta(days=1)).date():
        day = "tomorrow"
    else:
        day = "on " + when.strftime("%A")
    return f"{when.strftime('%H:%M')} {day}"
