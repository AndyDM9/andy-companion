"""The setup page's rules: what a helper may change, how it is checked, and telling the person.

    /setup?s=<setup token>      (scripts/settings.py links prints it; screen_server serves it)

A helper (often a son or daughter setting Andy up) gives their first name, then sets the person's first
name (optional: the phone pages say "What Andy remembers for Rosa" rather than "them"), the town,
the local news sites, the pages for what's on, the language, the pace, the volume and the
captions. Every change is told to the person in Andy's own words at its next quiet moment
("Anna changed my settings: the town and the volume"), the way family visits are, so nothing about
Andy changes behind the person's back. Reminders, memories and what is shared are not here: those
are the person's to set, by talking to Andy.
"""

from __future__ import annotations

import math
import re
import unicodedata
from typing import Any, Dict, List

from andy_companion import board, settings

# What each setting is called when Andy tells the person about a change (Andy's own voice).
NAMES = {"person_name": "your name", "place": "the town", "news_sources": "the local news sites", "events_pages": "the pages for what's on",
         "language": "the language", "pace": "how fast I speak", "volume": "the volume", "captions": "the captions",
         "screen_photos": "family photos on the screen",
         "screen_hints": "the ideas of what to ask me, on the screen", "night_from": "when the screen dims at night",
         "night_to": "when the screen brightens in the morning", "night_clock": "when the night clock shows",
         "screen_calm": "the calm screen",
         "tv_yaw": "where the screen is", "tv_height": "how high the screen is", "tv_glance": "glancing at the screen",
         "offers": "offering a story or a riddle in the afternoon", "greet_arrival": "welcoming you back"}
# The same, as the helper's page says it.
SHOWN = {**NAMES, "person_name": "the name these pages use", "pace": "how fast Andy speaks", "greet_arrival": "welcoming them back",
         "screen_hints": "the ideas of what to ask Andy, on the screen"}
# When the screen becomes the calm night clock (the founder, 2026-10-14: "from what time till what time,
# or maybe when Andy is sleeping").
NIGHT_CLOCK = ("hours", "asleep", "off")
SITE = re.compile(r"^(https?://)?([a-z0-9-]+\.)+[a-z]{2,}(/[^\s]*)?$", re.I)
MAX_SITES = 20
# The person's first name: letters, with single spaces, hyphens or apostrophes between them ("Anne-Marie",
# "O'Brien", "María José"); nothing that could carry markup or a number.
PERSON_NAME = re.compile(r"^[^\W\d_]+(?:[ '’-][^\W\d_]+)*$")
PERSON_NAME_LEN = 40


def state() -> Dict[str, Any]:
    s = settings.get()
    out = {k: s[k] for k in NAMES}
    out["events_suggestion"] = s.get("events_suggestion")
    return out


def suggest_events_page(place: str, finder=None) -> None:
    """In the background after the town is set: the town's events calendar, found on its own website with
    Tavily (a search, then map), offered on the setup page to add. Nothing is changed without the helper."""
    try:
        from andy_companion import web

        found = (finder or web.find_events_page)(place)
    except Exception:
        found = None
    settings.update(events_suggestion={**found, "for": place} if found else None)


def _sites(value: Any) -> List[str]:
    if value is None:
        items = []
    elif isinstance(value, str):
        items = value.splitlines()
    elif isinstance(value, list) and all(isinstance(item, str) for item in value):
        items = value
    else:
        raise ValueError("Use web addresses, one per line.")
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


def _integer(value: Any, message: str) -> int:
    """Accept whole numbers and the existing integer-text form, never truth values or fractions."""
    if type(value) is int:
        return value
    if isinstance(value, float) and math.isfinite(value) and value.is_integer():
        return int(value)
    if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]+", value.strip()):
        try:
            return int(value)
        except ValueError:
            pass
    raise ValueError(message)


def clean(data: Dict[str, Any]) -> Dict[str, Any]:
    """The changes asked for, checked. Unknown fields are ignored; a bad value raises ValueError."""
    if not isinstance(data, dict):
        raise ValueError("Settings must be an object of named choices.")
    out: Dict[str, Any] = {}
    if "person_name" in data:
        if data["person_name"] is not None and not isinstance(data["person_name"], str):
            raise ValueError("Their first name must be text.")
        person = unicodedata.normalize("NFC", " ".join(str(data["person_name"] or "").split()))
        if person and (len(person) > PERSON_NAME_LEN or not PERSON_NAME.match(person)):
            raise ValueError(f"Their first name can have letters, spaces, hyphens and apostrophes, up to "
                             f"{PERSON_NAME_LEN} in all.")
        out["person_name"] = person or None
    if "place" in data:
        if data["place"] is not None and not isinstance(data["place"], str):
            raise ValueError("The town must be text.")
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
        volume = _integer(data["volume"], "The volume is a number from 10 to 100.")
        if not 10 <= volume <= 100:
            raise ValueError("The volume is a number from 10 to 100.")
        out["volume"] = volume
    for key in ("captions", "screen_photos", "screen_hints", "screen_calm", "offers", "greet_arrival", "tv_glance"):
        if key in data:
            if type(data[key]) is not bool:
                raise ValueError(f"Choose on or off for {NAMES[key]}.")
            out[key] = data[key]
    if "tv_yaw" in data:
        if data["tv_yaw"] in (None, ""):
            out["tv_yaw"] = None
        else:
            try:
                if isinstance(data["tv_yaw"], bool) or not isinstance(data["tv_yaw"], (str, int, float)):
                    raise ValueError()
                degrees = float(data["tv_yaw"])
                if not math.isfinite(degrees):
                    raise ValueError()
                yaw = int(round(degrees))
            except (TypeError, ValueError, OverflowError):
                raise ValueError("The screen's direction is a number of degrees from -120 to 120.") from None
            if not -120 <= yaw <= 120:
                raise ValueError("The screen's direction is a number of degrees from -120 to 120.")
            out["tv_yaw"] = yaw
    if "tv_height" in data:
        if data["tv_height"] not in ("above", "level", "below"):
            raise ValueError("The screen is above, level with or below Andy's eyes.")
        out["tv_height"] = data["tv_height"]
    if "night_clock" in data:
        if data["night_clock"] not in NIGHT_CLOCK:
            raise ValueError("The night clock shows at the hours chosen, while Andy is asleep, or never.")
        out["night_clock"] = data["night_clock"]
    for key in ("night_from", "night_to"):
        if key in data:
            hour = _integer(data[key], "Night hours are from 0 to 23.")
            if not 0 <= hour <= 23:
                raise ValueError("Night hours are from 0 to 23.")
            out[key] = hour
    return out


def apply(name: str, data: Dict[str, Any]) -> List[str]:
    """Save the changes and tell the person who made them. Returns what changed, as the page says it."""
    if not isinstance(name, str):
        raise ValueError("Your first name is needed, so Andy can tell them who changed it.")
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
    if changed.get("place") and not settings.get()["events_pages"]:
        import threading

        threading.Thread(target=suggest_events_page, args=(changed["place"],), daemon=True).start()
    if "volume" in changed:
        try:
            from andy_companion import volume

            volume.set_level(changed["volume"])
        except Exception:
            pass   # applied when Andy next starts (volume.apply_saved)
    return [SHOWN[k] for k in NAMES if k in changed]
