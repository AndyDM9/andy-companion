"""The person's own settings that stick: speaking pace and volume. One owner-only file.

Pace has no switch in the voice pipeline, so it goes into Andy's instructions at the start of
every conversation (`instructions`), together with today's date.
"""

from __future__ import annotations

import contextlib
import copy
import json
import logging
import math
import os
import tempfile
import time
from datetime import date, datetime
from pathlib import Path
from typing import Any, Dict, Optional, Union

from andy_companion import clock
from andy_companion.reminders import DATA_DIR

FILE = DATA_DIR / "settings.json"
PACES = ("normal", "slow")
DEFAULTS: Dict[str, Any] = {"pace": "normal", "volume": None, "last_morning": None,
                            "place": None, "news_sources": [], "events_pages": [], "captions": True, "language": "en",
                            "coords": None, "screen_photos": True, "screen_hints": True, "night_from": 21, "night_to": 7,
                            "night_clock": "hours",
                            "screen_calm": False, "tv_yaw": None, "tv_height": "level", "tv_glance": True,
                            "offers": True, "last_offer": None, "events_suggestion": None,
                            "greet_arrival": True, "last_greeting": None, "person_name": None}
STEP = 15


def _number(value: Any, low: float, high: float) -> bool:
    return type(value) in (int, float) and low <= value <= high and math.isfinite(value)


def _checked(data: Any) -> Dict[str, Any]:
    """Validate known stored fields, including caches. Missing/unknown fields keep older files readable."""
    if not isinstance(data, dict):
        raise ValueError("Settings must be an object.")
    out = {k: v for k, v in data.items() if k in DEFAULTS}
    for key, value in out.items():
        if key in ("pace", "language", "night_clock", "tv_height"):
            valid = isinstance(value, str) and value in {
                "pace": PACES, "language": ("en", "es"), "night_clock": ("hours", "asleep", "off"),
                "tv_height": ("above", "level", "below")}[key]
        elif type(DEFAULTS[key]) is bool:
            valid = type(value) is bool
        elif key in ("news_sources", "events_pages"):
            valid = isinstance(value, list) and len(value) <= 20 and all(isinstance(v, str) for v in value)
        elif key in ("place", "person_name"):
            valid = value is None or isinstance(value, str)
        elif key in ("last_morning", "last_offer"):
            valid = value is None
            if isinstance(value, str):
                valid = date.fromisoformat(value).isoformat() == value
        elif key == "last_greeting":
            valid = value is None or _number(value, 0, 253402300799)
        elif key == "volume":
            # Earlier direct updates accepted integer text. Read it without treating booleans as numbers.
            if isinstance(value, str):
                value = int(value)
                out[key] = value
            valid = value is None or (type(value) is int and 0 <= value <= 100)
        elif key in ("night_from", "night_to"):
            valid = type(value) is int and 0 <= value <= 23
        elif key == "tv_yaw":
            valid = value is None or _number(value, -120, 120)
        elif key == "coords":
            valid = value is None or (isinstance(value, dict) and isinstance(value.get("place"), str)
                                     and _number(value.get("lat"), -90, 90) and _number(value.get("lon"), -180, 180))
        elif key == "events_suggestion":
            valid = value is None or (isinstance(value, dict) and all(
                isinstance(value.get(k), str) for k in ("site", "page", "for")))
        else:
            valid = False
        if not valid:
            raise ValueError("A saved setting has an unsupported value.")
    return out


def _load() -> Dict[str, Any]:
    """Called under the settings lock. Preserve the entire original before using fresh defaults."""
    try:
        data = _checked(json.loads(FILE.read_text()))
    except FileNotFoundError:
        data = {}
    except (OSError, ValueError):
        aside = None
        try:
            fd, name = tempfile.mkstemp(dir=FILE.parent, prefix=f"{FILE.stem}.unreadable-{int(time.time())}-", suffix=".json")
            aside = Path(name)
            os.close(fd)
            os.chmod(FILE, 0o600)
            os.replace(FILE, aside)
        except OSError:
            if aside is not None:
                with contextlib.suppress(OSError):
                    aside.unlink(missing_ok=True)
            raise ValueError("Settings could not be read or preserved. No settings changes were made.") from None
        logging.getLogger("andy.settings").warning("Unreadable settings preserved as %s; using defaults", aside.name)
        data = {}
    return {**copy.deepcopy(DEFAULTS), **data}


def get() -> Dict[str, Any]:
    from andy_companion import board

    with board.locked(FILE):
        return _load()


def update(**changes: Any) -> Dict[str, Any]:
    try:
        if changes.keys() - DEFAULTS.keys():
            raise ValueError()
        changes = _checked(changes)
    except (ValueError, OverflowError):
        raise ValueError("Settings changes have an unsupported field or value.") from None
    from andy_companion import board

    with board.locked(FILE):          # the setup page and the speaker both change settings
        data = {**_load(), **changes}
        fd, tmp = tempfile.mkstemp(dir=FILE.parent, suffix=".tmp")
        try:
            with os.fdopen(fd, "w") as f:
                json.dump(data, f, allow_nan=False)
            os.chmod(tmp, 0o600)
            os.replace(tmp, FILE)
        finally:
            with contextlib.suppress(OSError):
                os.unlink(tmp)
    return data


def recovery_files() -> list[Dict[str, Any]]:
    """Only metadata leaves the owner-only data directory, never the unreadable contents."""
    from andy_companion import board

    with board.locked(FILE):
        _load()
        return [{"id": p.name, "at": p.stat().st_mtime}
                for p in sorted(FILE.parent.glob(f"{FILE.stem}.unreadable-*.json")) if p.is_file()]


def delete_recovery(identifier: str) -> bool:
    from andy_companion import board

    with board.locked(FILE):
        for path in FILE.parent.glob(f"{FILE.stem}.unreadable-*.json"):
            if path.name == identifier and path.is_file():
                path.unlink()
                return True
    return False


def next_volume(current: int, change: Union[str, int]) -> int:
    if change == "louder":
        return min(100, int(current) + STEP)
    if change == "quieter":
        return max(10, int(current) - STEP)
    return max(0, min(100, int(change)))


def instructions(now: Optional[datetime] = None) -> str:
    """Lines added to Andy's instructions at the start of each conversation."""
    today = clock.today(now)
    lines = [f"## TODAY\nAt the start of this conversation it is {today['weekday']}, {today['date']}, "
             f"{today['time']}. Call get_today for the time later on."]
    from andy_companion import moments, recall

    lines.append(recall.block((m["what"], moments.spoken_day(m["on"])) for m in moments.upcoming(days=60)))
    from andy_companion import words

    language = get()["language"]
    lines.append(f"## GREETING\nWhen you wake, say exactly: {words.greeting(now or datetime.now(), language)}")
    if language == "es":
        lines.append("## LANGUAGE\nThe person chose Spanish: answer in Spanish, unless they speak to you in English.")
    else:
        lines.append("## LANGUAGE\nThe person chose English: answer in the language they speak to you.")
    from andy_companion import stories

    reading = stories.open_story()
    if reading:
        lines.append(f"## A STORY IN PROGRESS\nLast time you were reading \"{reading['title']}\" together and stopped "
                     f"before part {reading['next']} of {reading['of']}. If they'd like to carry on, use story "
                     "with action carry_on. Mention it only if it fits the moment.")
    if get()["pace"] == "slow":
        lines.append("## PACE\nThe person asked you to speak slowly: use short sentences, simple words, "
                     "and one idea at a time. Keep to this until they ask otherwise.")
    return "\n\n".join(lines)


def install() -> None:
    """Add today's date and the chosen pace to Andy's instructions at the start of each conversation."""
    from reachy_mini_conversation_app import huggingface_realtime as hr

    original = hr.get_session_instructions
    if getattr(original, "_andy_settings", False):
        return

    def with_settings(*args, **kwargs) -> str:
        base = original(*args, **kwargs)
        try:
            return base + "\n\n" + instructions()
        except Exception:      # a broken settings or moments file must never stop a conversation starting
            import logging

            logging.getLogger("andy.settings").warning("Andy's own instructions could not be added", exc_info=True)
            return base

    with_settings._andy_settings = True
    hr.get_session_instructions = with_settings
