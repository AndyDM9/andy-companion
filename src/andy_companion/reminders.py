"""Reminders at the times the person chooses, in their own words.

Kept in Andy's own owner-only file. A one-off reminder is deleted once Andy has said it; a daily
one moves to the same time the next day. Nothing else about the conversation is stored.
"""

from __future__ import annotations

import contextlib
import fcntl
import json
import logging
import math
import os
import re
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


def _timestamp(value: Any) -> bool:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return False
    try:
        if not math.isfinite(value):
            return False
        datetime.fromtimestamp(value)
        return True
    except (OverflowError, OSError, ValueError):
        return False


def _valid(items: Any) -> bool:
    if not isinstance(items, list):
        return False
    seen = set()
    for item in items:
        if not isinstance(item, dict):
            return False
        identifier, text = item.get("id"), item.get("text")
        if (not isinstance(identifier, str) or not identifier.strip() or len(identifier) > 64
                or identifier in seen or not isinstance(text, str) or not text.strip() or len(text) > MAX_TEXT
                or not _timestamp(item.get("due")) or item.get("repeat") not in REPEATS
                or ("created" in item and not _timestamp(item["created"]))):
            return False
        seen.add(identifier)
    return True


def _load() -> List[Dict[str, Any]]:
    """The reminders; a file that can't be read as them is set aside (never overwritten) and Andy starts afresh."""
    try:
        items = json.loads(STORE.read_text())
    except FileNotFoundError:
        return []
    except (OSError, ValueError):            # ValueError covers a broken file and bad UTF-8 (2026-10-25 review)
        items = None
    if _valid(items):
        return items
    aside = None
    try:
        # Reserve a unique destination: two damaged files in one second must not overwrite each other.
        fd, name = tempfile.mkstemp(dir=STORE.parent, prefix=f"{STORE.stem}.unreadable-{int(time.time())}-", suffix=".json")
        aside = Path(name)
        os.close(fd)
        os.replace(STORE, aside)
    except OSError:
        if aside is not None and STORE.exists():
            with contextlib.suppress(OSError):
                aside.unlink(missing_ok=True)
        raise ValueError("The reminders could not be read or preserved. No reminder changes were made.") from None
    logging.getLogger("andy.reminders").warning("The reminders file couldn't be read; set aside as %s", aside.name)
    return []


def _save(items: List[Dict[str, Any]]) -> None:
    STORE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=STORE.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(items, f, allow_nan=False)
        os.chmod(tmp, 0o600)
        os.replace(tmp, STORE)
    finally:
        with contextlib.suppress(OSError):
            os.unlink(tmp)


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
    if minutes is not None and at is not None:
        raise ValueError("Choose one reminder time: minutes from now or a clock time, not both.")
    if minutes is not None:
        try:
            amount = float(minutes)
        except (TypeError, ValueError, OverflowError):
            raise ValueError("Minutes must be a number greater than zero and at most one week.") from None
        if isinstance(minutes, bool) or not math.isfinite(amount) or not 0 < amount <= 7 * 24 * 60:
            raise ValueError("Minutes must be a number greater than zero and at most one week.")
        return now + timedelta(minutes=amount)
    if at:
        try:
            if not isinstance(at, str) or not re.fullmatch(r"\d{1,2}:\d{2}", at.strip()):
                raise ValueError
            hour, minute = (int(x) for x in at.strip().split(":"))
            when = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
        except ValueError:
            raise ValueError("Say the time as HH:MM, for example 17:30.") from None
        return when if when > now else when + timedelta(days=1)
    raise ValueError("Say when: in how many minutes, or at what time.")


# When it is due is kept as a time, so the words keep only what to do: "take a pill at eight o'clock in the morning"
# was shown as "take a pill at eight o'clock in the…" beside "Tomorrow, 8:00 am" (2026-10-25). Only a time, a part
# of the day or a repeat at the very end (or "remind me to" at the start) is taken off, and never all the words.
_NUM = (r"(?:\d{1,2}(?::\d{2})?|one|two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|noon|midnight|"
        r"una|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez|once|doce|mediod[ií]a|medianoche)")
_TAIL = re.compile(
    r"[\s,]+(?:"
    r"(?:at|by|around|about)\s+" + _NUM + r"(?:\s*(?:o'?clock|thirty|fifteen|forty[- ]five))?(?:\s*[ap]\.?\s?m\.?)?"
    r"|" + r"\d{1,2}(?::\d{2})?\s*[ap]\.?\s?m\.?"
    r"|in\s+the\s+(?:morning|afternoon|evening)|at\s+night|tonight|today|tomorrow(?:\s+(?:morning|afternoon|evening|night))?"
    r"|this\s+(?:morning|afternoon|evening)|(?:every|each)\s+(?:day|morning|afternoon|evening|night)|daily"
    r"|in\s+(?:\d+|a|an|one|two|three|five|ten|fifteen|twenty|thirty|forty[- ]five)\s+(?:minutes?|hours?)"
    r"|a\s+las?\s+" + _NUM + r"(?:\s+y\s+(?:media|cuarto))?|(?:de|por)\s+la\s+(?:mañana|tarde|noche)"
    r"|todos\s+los\s+d[ií]as|cada\s+(?:d[ií]a|mañana|tarde|noche)|a\s+diario|hoy|mañana|esta\s+(?:mañana|tarde|noche)"
    r"|en\s+\d+\s+(?:minutos?|horas?)"
    r")[\s.,!]*$", re.I)
_KEEPS = re.compile(r"\b(?:for|until|till|before|after|from|since|para|hasta|antes\s+de|desde|del?)\s*$", re.I)
_HEAD = re.compile(r"^(?:please\s+)?(?:remind\s+me\s+(?:to|about|that)|recu[eé]rdame(?:\s+que)?)\s+", re.I)


def just_what(text: str) -> str:
    """'remind me to take a pill at eight o'clock in the morning' -> 'take a pill'."""
    out = _HEAD.sub("", text)
    for _ in range(4):
        shorter = _TAIL.sub("", out)
        if shorter == out or _KEEPS.search(shorter):     # "buy bread for tomorrow": the time is part of what to do
            break
        out = shorter
    out = out.strip(" ,.")
    return out if len(out) >= 3 else text


def add(text: str, minutes: Optional[float] = None, at: Optional[str] = None,
        repeat: Optional[str] = None, now: Optional[datetime] = None) -> Dict[str, Any]:
    text = just_what(" ".join(str(text).split())[:MAX_TEXT])
    if not text:
        raise ValueError("What should I remind you about?")
    if repeat not in REPEATS:
        raise ValueError("A reminder can be once or daily.")
    if repeat == "daily" and not at:
        raise ValueError("A daily reminder needs a time of day.")
    when = due_time(minutes, at, now)
    item = {"text": text, "due": when.timestamp(), "repeat": repeat,
            "created": time.time()}
    with _locked():
        items = _load()
        identifiers = {r["id"] for r in items}
        for _ in range(8):
            item["id"] = secrets.token_hex(3)
            if item["id"] not in identifiers:
                break
        else:
            raise ValueError("A reminder identifier could not be created. No new reminder was saved.")
        items.append(item)
        _save(items)
    return item


def pending() -> List[Dict[str, Any]]:
    with _locked():
        return sorted(_load(), key=lambda r: r["due"])


def recovery_files() -> List[Dict[str, Any]]:
    """Metadata only, so preserved data can be reviewed/deleted without displaying its contents."""
    with _locked():
        return [{"id": p.name, "at": p.stat().st_mtime}
                for p in sorted(STORE.parent.glob(f"{STORE.stem}.unreadable-*.json")) if p.is_file()]


def delete_recovery(identifier: str) -> bool:
    with _locked():
        for path in STORE.parent.glob(f"{STORE.stem}.unreadable-*.json"):
            if path.name == identifier and path.is_file():
                path.unlink()
                return True
    return False


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
