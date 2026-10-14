"""The person's own settings that stick: speaking pace and volume. One owner-only file.

Pace has no switch in the voice pipeline, so it goes into Andy's instructions at the start of
every conversation (`instructions`), together with today's date.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, Optional, Union

from andy_companion import clock
from andy_companion.reminders import DATA_DIR

FILE = DATA_DIR / "settings.json"
PACES = ("normal", "slow")
DEFAULTS: Dict[str, Any] = {"pace": "normal", "volume": None, "last_morning": None,
                            "place": None, "news_sources": [], "events_pages": [], "captions": True, "language": "en",
                            "coords": None, "screen_photos": True, "night_from": 21, "night_to": 7,
                            "screen_calm": False, "tv_yaw": None, "tv_height": "level", "tv_glance": True}
STEP = 15


def get() -> Dict[str, Any]:
    try:
        data = json.loads(FILE.read_text())
    except (OSError, ValueError):
        data = {}
    return {**DEFAULTS, **{k: v for k, v in data.items() if k in DEFAULTS}}


def update(**changes: Any) -> Dict[str, Any]:
    if "pace" in changes and changes["pace"] not in PACES:
        raise ValueError("Pace is normal or slow.")
    if "language" in changes and changes["language"] not in ("en", "es"):
        raise ValueError("Language is en or es.")
    if "volume" in changes and changes["volume"] is not None and not 0 <= int(changes["volume"]) <= 100:
        raise ValueError("Volume is from 0 to 100.")
    data = {**get(), **changes}
    FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=FILE.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, FILE)
    return data


def next_volume(current: int, change: Union[str, int]) -> int:
    if change == "louder":
        return min(100, int(current) + STEP)
    if change == "quieter":
        return max(10, int(current) - STEP)
    return max(0, min(100, int(change)))


def instructions(now: Optional[datetime] = None) -> str:
    """Lines added to Andy's instructions at the start of each conversation."""
    today = clock.today(now)
    lines = [f"## TODAY\nAt the start of this conversation it is {today['weekday']} {today['date']}, "
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
        return original(*args, **kwargs) + "\n\n" + instructions()

    with_settings._andy_settings = True
    hr.get_session_instructions = with_settings
