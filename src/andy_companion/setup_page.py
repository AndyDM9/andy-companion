"""The setup page's rules: what a helper may change, how it is checked, and telling the person.

    /setup?s=<setup token>      (scripts/settings.py links prints it; screen_server serves it)

A helper (often a son or daughter setting Andy up) gives their first name, then sets the town,
the local news sites, the pages for what's on, the language, the pace, the volume and the
captions. Every change is told to the person in Andy's own words at its next quiet moment
("Anna changed my settings: the town and the volume"), the way family visits are, so nothing about
Andy changes behind the person's back. Reminders, memories and what is shared are not here: those
are the person's to set, by talking to Andy.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List

from andy_companion import board, settings

# What each setting is called when Andy tells the person about a change (Andy's own voice).
NAMES = {"place": "the town", "news_sources": "the local news sites", "events_pages": "the pages for what's on",
         "language": "the language", "pace": "how fast I speak", "volume": "the volume", "captions": "the captions",
         "screen_photos": "family photos on the screen", "night_from": "when the screen dims at night",
         "night_to": "when the screen brightens in the morning", "screen_calm": "the calm screen",
         "tv_yaw": "where the screen is", "tv_height": "how high the screen is", "tv_glance": "glancing at the screen"}
# The same, as the helper's page says it.
SHOWN = {**NAMES, "pace": "how fast Andy speaks"}
SITE = re.compile(r"^(https?://)?([a-z0-9-]+\.)+[a-z]{2,}(/[^\s]*)?$", re.I)
MAX_SITES = 20


def state() -> Dict[str, Any]:
    s = settings.get()
    return {k: s[k] for k in NAMES}


def _sites(value: Any) -> List[str]:
    items = value.splitlines() if isinstance(value, str) else list(value or [])
    out: List[str] = []
    for item in items:
        site = str(item).strip().rstrip("/")
        if not site:
            continue
        if len(site) > 200 or not SITE.match(site):
            raise ValueError(f"\"{site[:60]}\" is not a web address. Use one per line, like wlrn.org.")
        if site not in out:
            out.append(site)
    if len(out) > MAX_SITES:
        raise ValueError(f"Up to {MAX_SITES} sites, please.")
    return out


def clean(data: Dict[str, Any]) -> Dict[str, Any]:
    """The changes asked for, checked. Unknown fields are ignored; a bad value raises ValueError."""
    out: Dict[str, Any] = {}
    if "place" in data:
        place = " ".join(str(data["place"] or "").split())[:120]
        out["place"] = place or None
    for key in ("news_sources", "events_pages"):
        if key in data:
            out[key] = _sites(data[key])
    if "language" in data:
        if data["language"] not in ("en", "es"):
            raise ValueError("The language is English or Spanish.")
        out["language"] = data["language"]
    if "pace" in data:
        if data["pace"] not in settings.PACES:
            raise ValueError("The pace is normal or slow.")
        out["pace"] = data["pace"]
    if "volume" in data and data["volume"] not in (None, ""):
        try:
            volume = int(data["volume"])
        except (TypeError, ValueError):
            raise ValueError("The volume is a number from 10 to 100.") from None
        if not 10 <= volume <= 100:
            raise ValueError("The volume is a number from 10 to 100.")
        out["volume"] = volume
    if "captions" in data:
        out["captions"] = bool(data["captions"])
    if "screen_photos" in data:
        out["screen_photos"] = bool(data["screen_photos"])
    if "screen_calm" in data:
        out["screen_calm"] = bool(data["screen_calm"])
    if "tv_yaw" in data:
        if data["tv_yaw"] in (None, ""):
            out["tv_yaw"] = None
        else:
            try:
                yaw = int(round(float(data["tv_yaw"])))
            except (TypeError, ValueError):
                raise ValueError("The screen's direction is a number of degrees from -120 to 120.") from None
            if not -120 <= yaw <= 120:
                raise ValueError("The screen's direction is a number of degrees from -120 to 120.")
            out["tv_yaw"] = yaw
    if "tv_height" in data:
        if data["tv_height"] not in ("above", "level", "below"):
            raise ValueError("The screen is above, level with or below Andy's eyes.")
        out["tv_height"] = data["tv_height"]
    if "tv_glance" in data:
        out["tv_glance"] = bool(data["tv_glance"])
    for key in ("night_from", "night_to"):
        if key in data:
            try:
                hour = int(data[key])
            except (TypeError, ValueError):
                raise ValueError("Night hours are from 0 to 23.") from None
            if not 0 <= hour <= 23:
                raise ValueError("Night hours are from 0 to 23.")
            out[key] = hour
    return out


def apply(name: str, data: Dict[str, Any]) -> List[str]:
    """Save the changes and tell the person who made them. Returns what changed, as the page says it."""
    name = " ".join(str(name or "").split())[:board.NAME_LEN]
    if not name:
        raise ValueError("Your first name is needed, so Andy can tell them who changed it.")
    wanted = clean(data)
    before = settings.get()
    changed = {k: v for k, v in wanted.items() if before.get(k) != v}
    if not changed:
        return []
    settings.update(**changed)
    words = [NAMES[k] for k in NAMES if k in changed]
    board.settings_changed(name, words)
    if "volume" in changed:
        try:
            from andy_companion import volume

            volume.set_level(changed["volume"])
        except Exception:
            pass   # applied when Andy next starts (volume.apply_saved)
    return [SHOWN[k] for k in NAMES if k in changed]
