"""What Andy's screen shows, what the person shares with family, and what family sends back.

The current card and research answers live in the screen server's memory only. The
conversation app reaches them through authenticated loopback HTTP (transient.py).
The previous screen.json is removed on startup, never read or migrated.

Owner-only files in Andy's folder:
- shared.json: notes the person explicitly asked Andy to share with family. Nothing else is shared.
- inbox.json: messages, links and reminder suggestions family send to Andy, and who looked at the family
  page. The speaker says them to the person, then they are deleted: the person always hears who looked.
"""

from __future__ import annotations

import contextlib
import fcntl

import json
import re
import os
import secrets
import struct
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Iterator
from urllib.parse import urlparse

from andy_companion.reminders import DATA_DIR
from andy_companion import transient

SCREEN = DATA_DIR / "screen.json"  # legacy cleanup only; never written
SHARED = DATA_DIR / "shared.json"
INBOX = DATA_DIR / "inbox.json"
TOKENS = DATA_DIR / "tokens.json"
PHOTOS = DATA_DIR / "photos"
PHOTO_DAYS = 7
MAX_PHOTOS = 60                 # kept at once; the oldest go first (2026-10-25 review)
MAX_PHOTO_BYTES = 8 * 1024 * 1024
# A photo's size is read from its header before it is decoded: a small file can claim a huge picture (a few KB of
# PNG decode to gigabytes), and OpenCV's own limit is fixed once it has loaded (2026-10-25 review). One at a time.
MAX_PHOTO_PIXELS = 40_000_000
_decoding = threading.BoundedSemaphore(1)
SHOW_FOR_S = 5 * 60            # then the screen goes back to the day and family photos
MAX_SHARED = 30
MAX_TEXT = 600
NAME_LEN = 40
_screen = None
_research = []
_generation = 0
_transient_lock = threading.RLock()
SEARCH_FOR_S = 45             # a stalled or cancelled finder cannot leave a permanent working card
SEARCH_STAGES = ("scanning", "reading", "closer", "remembered")


def transient_action(action: str, data: Any = None) -> Any:
    """Allowlisted operations; the HTTP boundary accepts only this computer and its token."""
    global _screen, _generation
    with _transient_lock:
        if action == "show":
            if not isinstance(data, dict) or not isinstance(data.get("at"), (int, float)):
                raise ValueError("Bad screen card")
            _screen = data
        elif action == "showing":
            now = float(data) if data is not None else time.time()
            if _screen and (now - _screen.get("at", 0) > SHOW_FOR_S or
                            (_screen.get("until") and now > _screen["until"])):
                _screen = None
            return {k: v for k, v in _screen.items() if k != "search_id"} if _screen else None
        elif action == "search-start":
            now = time.time()
            key = secrets.token_hex(16)
            _screen = {"kind": "search", "title": "", "items": [], "at": now, "until": now + SEARCH_FOR_S,
                       "search_id": key, "stage": "scanning", "captured": 0}
            return key
        elif action in ("search-step", "search-end"):
            if not isinstance(data, dict):
                raise ValueError("Bad search progress")
            if not _screen or _screen.get("search_id") != data.get("id") or not data.get("id"):
                return None             # another card, a clear, or a newer search owns the screen now
            if action == "search-end" or time.time() > _screen["until"]:
                _screen = None
            else:
                stage, captured = data.get("stage"), data.get("captured")
                if stage not in SEARCH_STAGES or type(captured) is not int or not 0 <= captured <= 4:
                    raise ValueError("Bad search progress")
                _screen.update(stage=stage, captured=captured, until=time.time() + SEARCH_FOR_S)
        elif action == "clear":
            _screen = None
        elif action == "clear-private":
            from andy_companion import screen_server
            _screen = None
            _research.clear()
            _generation += 1
            screen_server.set_caption("")
            screen_server.forget_views()
        elif action == "research":
            if not isinstance(data, dict) or data.get("type") != "research":
                raise ValueError("Bad research result")
            data = {**data, "id": secrets.token_hex(8)}
            _research.append(data)
            del _research[:-MAX_INBOX]
        elif action == "research-list":
            return list(_research)
        elif action == "generation":
            return _generation
        elif action == "research-delete":
            before = len(_research)
            _research[:] = [e for e in _research if data is not None and e["id"] != data]
            return before - len(_research)
        else:
            raise ValueError("Unknown transient operation")
    return None


def _transient(action: str, data: Any = None, default=None):
    try:
        return transient.call(action, data)
    except transient.Unavailable:
        return default


def _read(path: Path, default: Any) -> Any:
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def _write(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def _tidy(text: Any, limit: int = MAX_TEXT) -> str:
    return " ".join(str(text or "").split())[:limit]


def _link(url: Any) -> str:
    """A source's address for the screen, kept only whole: https, a host, no spaces, at most 300 characters."""
    value = str(url or "")
    parts = urlparse(value)
    if parts.scheme != "https" or not parts.netloc or len(value) > 300 or re.search(r"[\s\"'<>]", value):
        return ""
    return value


# --- tokens: the screen, family, settings and under-the-hood links ----------------------------

def tokens() -> Dict[str, str]:
    """One random token per link. The hood has its own (2026-10-14): with the screen's, a /hood link shared
    for its timings would also read the screen's captions and reminders and could show the settings code."""
    data = _read(TOKENS, {})
    missing = [k for k in ("screen", "family", "setup", "hood") if not data.get(k)]
    if missing:
        for k in missing:                 # a new kind of link never changes the existing ones
            data[k] = secrets.token_urlsafe(12)
        _write(TOKENS, data)
    return data


def new_setup_link() -> str:
    """Make a new settings token, so an old settings link or code stops working."""
    data = tokens()
    data["setup"] = secrets.token_urlsafe(12)
    _write(TOKENS, data)
    return data["setup"]


def new_family_link() -> str:
    """Make a new family token, so an old link stops working."""
    data = tokens()
    data["family"] = secrets.token_urlsafe(12)
    _write(TOKENS, data)
    return data["family"]


# --- the screen -------------------------------------------------------------------------------

def show(kind: str, title: str, items: List[Dict[str, Any]], now: Optional[float] = None,
         how: Optional[Dict[str, Any]] = None, lead: str = "") -> None:
    """Put something on the screen beside Andy, for SHOW_FOR_S. `how`: how it was found (web.traced), names
    and numbers only, shown in small type under the sources. `lead`: what to do, in one line under the title,
    above the reasons (the scam receipt: the action first, the evidence after)."""
    clean_items = [{k: _tidy(v, 300) for k, v in item.items() if k in ("title", "source", "summary", "when", "published", "tone")}
                   for item in items[:4]]
    for clean, item in zip(clean_items, items, strict=False):        # a source's page, so the line can be a link
        link = _link(item.get("url"))
        if link:
            clean["url"] = link
    card = {"kind": _tidy(kind, 20), "title": _tidy(title, 80), "items": clean_items, "at": now or time.time()}
    if lead:
        card["lead"] = _tidy(lead, 120)
    if how:
        credits = how.get("credits")
        card["how"] = {"calls": [_tidy(c, 12) for c in how.get("calls", [])][:4], "depth": _tidy(how.get("depth", ""), 12),
                       "credits": credits if isinstance(credits, (int, float)) else None,
                       "seconds": float(how.get("seconds") or 0)}
        if isinstance(how.get("sites"), int) and not isinstance(how.get("sites"), bool) and 0 < how["sites"] < 1000:
            card["how"]["sites"] = how["sites"]
    _transient("show", card)


def showing(now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    return _transient("showing", now)


def start_search() -> Optional[str]:
    """A transient, text-free progress card; its private ID prevents late updates replacing a newer card."""
    return _transient("search-start")


def search_step(key: Optional[str], stage: str, captured: int = 0) -> None:
    _transient("search-step", {"id": key, "stage": stage, "captured": captured})


def end_search(key: Optional[str]) -> None:
    _transient("search-end", {"id": key})


CODE_FOR_S = 120


def show_settings_code(now: Optional[float] = None) -> None:
    """The settings QR code on the screen for two minutes only: the code gives control of Andy. Each time it
    is shown the setup link is made new, so a phone that saw an old code has no way in (review 2026-10-13)."""
    now = now or time.time()
    new_setup_link()
    _transient("show", {"kind": "code", "title": "Andy's settings", "items": [], "at": now, "until": now + CODE_FOR_S})


def code_shown(now: Optional[float] = None) -> None:
    """The settings code was shown from the TV's menu (anyone with the screen can): the person is told, as for every
    change, since scanning it gives control of Andy for two minutes (2026-10-25 review, decision 0009)."""
    _inbox_add({"type": "code", "name": "the TV", "at": now or time.time()})


CHECK_FOR_S = 20


def show_screen_check(now: Optional[float] = None) -> None:
    """A card for checking where the screen is: Andy glances at it when it appears (body.glance)."""
    now = now or time.time()
    _transient("show", {"kind": "where", "title": "Andy looks here", "items": [], "at": now, "until": now + CHECK_FOR_S})


def clear_screen() -> None:
    _transient("clear")
    try:
        SCREEN.unlink()
    except FileNotFoundError:
        pass


# --- sharing with family ------------------------------------------------------------------------

def share(note: str, now: Optional[float] = None) -> Dict[str, Any]:
    note = _tidy(note)
    if not note:
        raise ValueError("What should I share?")
    item = {"id": secrets.token_hex(3), "note": note, "at": now or time.time()}
    with locked(SHARED):        # the settings page deletes from another process (2026-10-25 review)
        _write(SHARED, (_read(SHARED, []) + [item])[-MAX_SHARED:])
    return item


def shared() -> List[Dict[str, Any]]:
    return _read(SHARED, [])


def unshare(note_id: str) -> bool:
    with locked(SHARED):
        items = _read(SHARED, [])
        kept = [i for i in items if i["id"] != note_id]
        if len(kept) == len(items):
            return False
        _write(SHARED, kept)
    return True


# --- what family send, and who looked -------------------------------------------------------

@contextlib.contextmanager
def locked(path: Path) -> Iterator[None]:
    """One writer at a time for a file both of Andy's processes change (the screen server and the robot's
    speaker both write the inbox): without it, one's read-change-write loses the other's (review 2026-10-13)."""
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    with open(path.with_suffix(".lock"), "a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(lock, fcntl.LOCK_UN)


MAX_INBOX = 50
MAX_LOOKS = 20                 # "looked" notes waiting at once: visits alone never fill the inbox
# The person always hears who changed or deleted what (decision 0009): those notes are never pushed out by others.
KEPT_UNTIL_SAID = ("settings", "deleted", "code")
INBOX_FULL = "Andy has a lot waiting to be passed on. Please try again later."
LOOK_EVERY_S = 3600
_looks: Dict[str, float] = {}  # who looked, and when (the screen server's memory): once per name per hour, said or not


class InboxFull(ValueError):
    """What family send waits to be said; once MAX_INBOX things wait, a new one is refused. The oldest used to be
    dropped instead, so one link holder sending a lot pushed out what other relatives had sent (2026-10-28 review)."""


def _ordinary(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [e for e in items if e.get("type") not in KEPT_UNTIL_SAID]


def _inbox_room() -> None:
    if len(_ordinary(_read(INBOX, []))) >= MAX_INBOX:
        raise InboxFull(INBOX_FULL)


def _inbox_add(entry: Dict[str, Any]) -> None:
    """Add an entry. A change notice always goes in; anything else is refused once MAX_INBOX ordinary entries wait
    (InboxFull), and nothing already waiting is ever dropped."""
    with locked(INBOX):
        items = _read(INBOX, [])
        if entry.get("type") not in KEPT_UNTIL_SAID and len(_ordinary(items)) >= MAX_INBOX:
            raise InboxFull(INBOX_FULL)
        _write(INBOX, items + [{**entry, "id": secrets.token_hex(8)}])


MAX_LINK = 300


def family_message(name: str, text: str = "", link: str = "", now: Optional[float] = None) -> None:
    if len(" ".join(str(link or "").split())) > MAX_LINK:   # never cut short into a broken address (2026-10-28 review)
        raise ValueError(f"That link is too long. Send a shorter web address, up to {MAX_LINK} characters.")
    name, text, link = _tidy(name, NAME_LEN), _tidy(text), _tidy(link, MAX_LINK)
    if not name or not (text or link):
        raise ValueError("A name and a message or link are needed.")
    if link and (any(ch in link for ch in " []<>\"'") or not re.match(r"^https?://[A-Za-z0-9.-]+\.[A-Za-z]{2,}(?::\d+)?(/|$)", link)):
        raise ValueError("That link doesn't look right. Send a web address that starts with https://.")
    if link and not link.startswith(("http://", "https://")):
        raise ValueError("A link starts with http:// or https://.")
    _inbox_add({"type": "message", "name": name, "text": text, "link": link, "at": now or time.time()})


SUGGEST_TEXT = 120
# A suggestion is set with set_reminder, which takes a time at most a week ahead (reminders.due_time): a
# suggestion further out could never be set, so the family page offers today, tomorrow or a weekday.
SUGGEST_DAYS = 7
_LINKISH = re.compile(r"https?:|www\.|\b[a-z0-9-]+\.(com|net|org|info|biz|io|co|ly|me|app|xyz|us|uk|es|gov|edu)\b", re.I)


def family_suggestion(name: str, what: str, when_text: str, due_ts: float, now: Optional[float] = None) -> Dict[str, Any]:
    """Family suggest a reminder (B21). It is only passed on: Andy asks the person, and sets it only after their
    yes. Family are never told the answer, so nothing here reports on the person."""
    name, what, when_text = _tidy(name, NAME_LEN), _tidy(what, MAX_TEXT), _tidy(when_text, 60)
    if not name or not what:
        raise ValueError("A name and what to remind them about are needed.")
    if len(what) > SUGGEST_TEXT:
        raise ValueError(f"Keep it short: up to {SUGGEST_TEXT} characters.")
    if _LINKISH.search(what):
        raise ValueError("A suggestion can't carry a link. Send a link as a message instead.")
    now = time.time() if now is None else now
    try:
        due = float(due_ts)
    except (TypeError, ValueError):
        raise ValueError("Choose a day and a time.") from None
    if due <= now + 60:
        raise ValueError("Choose a time later than now.")
    if due > now + SUGGEST_DAYS * 86400:
        raise ValueError("Choose a time within the next week.")
    entry = {"type": "suggestion", "name": name, "what": what, "when": when_text, "due": due, "at": now}
    _inbox_add(entry)
    return entry


def suggestion_from_page(name: str, what: str, when: Any, now: Optional[float] = None) -> Dict[str, Any]:
    """What the family page posts ({"day": "today" | "tomorrow" | "0".."6" (Monday first), "time": "HH:MM"}),
    turned into a time on Andy's own clock, then family_suggestion. The route /api/family/suggest calls this."""
    if not isinstance(when, dict):
        raise ValueError("Choose a day and a time.")
    day, clock = str(when.get("day", "")).strip().lower(), str(when.get("time", "")).strip()
    match = re.fullmatch(r"([01]?\d|2[0-3]):([0-5]\d)", clock)
    if not match:
        raise ValueError("Choose a time.")
    from datetime import timedelta

    now = time.time() if now is None else now
    today = datetime.fromtimestamp(now).replace(hour=int(match.group(1)), minute=int(match.group(2)), second=0, microsecond=0)
    if day == "today":
        due = today
    elif day == "tomorrow":
        due = today + timedelta(days=1)
    elif day in ("0", "1", "2", "3", "4", "5", "6"):
        due = today + timedelta(days=(int(day) - today.weekday()) % 7)
        if due.timestamp() <= now + 60:           # that weekday is today and the time has passed: next week
            due += timedelta(days=7)
    else:
        raise ValueError("Choose a day.")
    return family_suggestion(name, what, f"{due:%A} {due:%H:%M}", due.timestamp(), now)


def looked(name: str, now: Optional[float] = None) -> None:
    """Family opened the page. The person hears about it once per name per hour, said or not: only unsaid looks were
    checked, so each visit after Andy had said the last one added another (2026-10-28 review). With MAX_LOOKS
    waiting, a new name is refused like a full inbox, so visits under many names can't fill it."""
    name = _tidy(name, NAME_LEN)
    if not name:
        raise ValueError("A name is needed.")
    now = now or time.time()
    key = name.casefold()
    with locked(INBOX):
        for who, at in list(_looks.items()):
            if not 0 <= now - at < LOOK_EVERY_S:
                del _looks[who]
        items = _read(INBOX, [])
        looks = [e for e in items if e.get("type") == "look"]
        if key in _looks or any(str(e.get("name", "")).casefold() == key and isinstance(e.get("at"), (int, float))
                                and 0 <= now - e["at"] < LOOK_EVERY_S for e in looks):
            return
        if len(looks) >= MAX_LOOKS or len(_ordinary(items)) >= MAX_INBOX:
            raise InboxFull(INBOX_FULL)
        _write(INBOX, items + [{"type": "look", "name": name, "at": now, "id": secrets.token_hex(8)}])
        _looks[key] = now


def settings_changed(name: str, what: List[str], now: Optional[float] = None) -> None:
    """A helper changed Andy's settings on the setup page. The person hears who, and what."""
    name = _tidy(name, NAME_LEN)
    if not name or not what:
        raise ValueError("A name and what changed are needed.")
    _inbox_add({"type": "settings", "name": name, "what": [_tidy(w, 60) for w in what][:8], "at": now or time.time()})


def kept_deleted(name: str, what: List[str], now: Optional[float] = None) -> None:
    """A helper deleted things Andy keeps, on the settings page. The person hears who, and what."""
    name = _tidy(name, NAME_LEN)
    if not name or not what:
        raise ValueError("A name and what was deleted are needed.")
    _inbox_add({"type": "deleted", "name": name, "what": [_tidy(w, 60) for w in what][:8], "at": now or time.time()})


def research_ready(topic: str, say: str, points: List[str], sources: List[Dict[str, Any]], failed: bool = False,
                   now: Optional[float] = None) -> None:
    """An answer Andy looked into is ready to say (looking.py); kept until said, like a family message."""
    _transient("research", {"type": "research", "topic": _tidy(topic, 120), "say": _tidy(say, 700),
                "points": [_tidy(p, 160) for p in points[:4]],
                "sources": [{"title": _tidy(s.get("title", ""), 140), "source": _tidy(s.get("source", ""), 60)}
                            for s in sources[:6]],
                "failed": bool(failed), "at": now or time.time()})


def drop_pending(kind: str) -> int:
    """Drop what is waiting to be said of one kind (a research answer the person asked Andy to stop)."""
    transient_dropped = _transient("research-delete", default=0) if kind == "research" else 0
    with locked(INBOX):
        items = _read(INBOX, [])
        kept = [e for e in items if e.get("type") != kind]
        _write(INBOX, kept)
    return len(items) - len(kept) + transient_dropped


def clear_pending() -> int:
    """Drop what is waiting to be said (messages, photos' notes, suggestions, answers), keeping change notices."""
    transient_dropped = _transient("research-delete", default=0)
    with locked(INBOX):
        items = _read(INBOX, [])
        kept = [e for e in items if e.get("type") in KEPT_UNTIL_SAID]
        _write(INBOX, kept)
    return len(items) - len(kept) + transient_dropped


def next_for_person() -> Optional[Dict[str, Any]]:
    items = pending_entries()
    return items[0] if items else None


def pending_entries() -> List[Dict[str, Any]]:
    return sorted(_read(INBOX, []) + _transient("research-list", default=[]), key=lambda e: e.get("at", 0))


def delete_pending(item_id: str) -> bool:
    if not item_id:
        return False
    if _transient("research-delete", item_id, 0):
        return True
    with locked(INBOX):
        items = _read(INBOX, [])
        keep = [e for e in items if e.get("id") != item_id or e.get("type") in KEPT_UNTIL_SAID]
        if len(items) == len(keep):
            return False
        _write(INBOX, keep)
    return True


def drop_photo_notes(photo_id: str) -> int:
    """A deleted photo's announcement goes with it: Andy never speaks of a picture that is gone (2026-10-28 review)."""
    with locked(INBOX):
        items = _read(INBOX, [])
        keep = [e for e in items if not (e.get("type") == "photo" and e.get("photo") == photo_id)]
        if len(keep) != len(items):
            _write(INBOX, keep)
    return len(items) - len(keep)


def purge_legacy_transients() -> None:
    """Remove the previous disk-backed card and research results, without reading or logging their words."""
    SCREEN.unlink(missing_ok=True)
    with locked(INBOX):
        items = _read(INBOX, [])
        if any(e.get("type") == "research" for e in items):
            _write(INBOX, [e for e in items if e.get("type") != "research"])


def delivered(entry: Dict[str, Any]) -> None:
    if entry.get("type") == "research" and entry.get("id"):
        _transient("research-delete", entry["id"])
        return
    with locked(INBOX):
        items = _read(INBOX, [])
        if entry in items:
            items.remove(entry)
            _write(INBOX, items)


# --- photos from family ---------------------------------------------------------------------

def save_photo(name: str, data: bytes, caption: str = "", now: Optional[float] = None) -> Dict[str, Any]:
    """Keep a photo family sent: decoded and re-encoded as a plain JPEG (which drops hidden data such
    as the place it was taken), at most 1600 pixels wide, deleted after PHOTO_DAYS."""
    os.environ.setdefault("OPENCV_IO_MAX_IMAGE_PIXELS", str(MAX_PHOTO_PIXELS))   # if cv2 hasn't loaded yet
    import cv2
    import numpy as np

    name, caption = _tidy(name, NAME_LEN), _tidy(caption, 140)
    if not name:
        raise ValueError("A name is needed.")
    if not data or len(data) > MAX_PHOTO_BYTES:
        raise ValueError("The photo must be smaller than 8 MB.")
    _inbox_room()                         # a photo that can't be announced is never kept
    size = image_size(data)
    if size is None:
        raise ValueError("Send the photo as a JPEG, PNG or WebP.")
    if size[0] * size[1] > MAX_PHOTO_PIXELS:
        raise ValueError("That photo is too large to show; send a smaller copy.")
    with _decoding:
        try:
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        except cv2.error:
            img = None
    if img is None or min(img.shape[:2]) < 32:
        raise ValueError("That file is not a photo Andy can show.")
    h, w = img.shape[:2]
    if w > 1600:
        img = cv2.resize(img, (1600, int(h * 1600 / w)), interpolation=cv2.INTER_AREA)
    ok, jpeg = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    if not ok:
        raise ValueError("The photo could not be prepared.")
    now = now or time.time()
    photo_id = _store_photo(jpeg.tobytes(), {"name": name, "caption": caption, "at": now})
    try:
        _inbox_add({"type": "photo", "name": name, "caption": caption, "photo": photo_id, "at": now})
    except InboxFull:                     # filled while it was being prepared
        (PHOTOS / f"{photo_id}.jpg").unlink(missing_ok=True)
        (PHOTOS / f"{photo_id}.json").unlink(missing_ok=True)
        raise
    tidy_photos(now)
    return {"photo": photo_id}


def image_size(data: bytes) -> Optional[tuple]:
    """(width, height) from a JPEG, PNG or WebP file's header, without decoding it; None for anything else."""
    try:
        if data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR":
            return struct.unpack(">II", data[16:24])
        if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            chunk = data[12:16]
            if chunk == b"VP8X":
                return 1 + int.from_bytes(data[24:27], "little"), 1 + int.from_bytes(data[27:30], "little")
            if chunk == b"VP8L":
                bits = int.from_bytes(data[21:25], "little")
                return 1 + (bits & 0x3FFF), 1 + ((bits >> 14) & 0x3FFF)
            if chunk == b"VP8 ":
                w, h = struct.unpack("<HH", data[26:30])
                return w & 0x3FFF, h & 0x3FFF
            return None
        if data[:2] == b"\xff\xd8":
            i = 2
            while i + 9 < len(data):
                if data[i] != 0xFF:
                    return None
                marker = data[i + 1]
                if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:      # no length: skip the marker
                    i += 2
                    continue
                length = struct.unpack(">H", data[i + 2:i + 4])[0]
                if 0xC0 <= marker <= 0xCF and marker not in (0xC4, 0xC8, 0xCC):   # a frame header: its size
                    h, w = struct.unpack(">HH", data[i + 5:i + 9])
                    return w, h
                i += 2 + length
    except struct.error:
        return None
    return None


def _store_photo(jpeg: bytes, meta: Dict[str, Any]) -> str:
    """Keep a prepared JPEG, owner-only, with who sent it (for the idle screen)."""
    PHOTOS.mkdir(parents=True, exist_ok=True, mode=0o700)
    photo_id = secrets.token_hex(6)
    path = PHOTOS / f"{photo_id}.jpg"
    path.write_bytes(jpeg)
    os.chmod(path, 0o600)
    _write(PHOTOS / f"{photo_id}.json", meta)
    return photo_id


def add_sample_photo(jpeg: bytes, credit: str, now: Optional[float] = None) -> str:
    """A sample landscape to see how the idle screen flows: marked as a sample, never announced."""
    return _store_photo(jpeg, {"name": "Sample", "caption": _tidy(credit, 140), "at": now or time.time(), "sample": True})


def remove_sample_photos() -> int:
    gone = 0
    for meta_path in PHOTOS.glob("*.json") if PHOTOS.is_dir() else []:
        if (_read(meta_path, {}) or {}).get("sample"):
            meta_path.with_suffix(".jpg").unlink(missing_ok=True)
            meta_path.unlink(missing_ok=True)
            gone += 1
    return gone


def photo_path(photo_id: str) -> Optional[Path]:
    if not photo_id or not all(c in "0123456789abcdef" for c in photo_id) or len(photo_id) != 12:
        return None
    path = PHOTOS / f"{photo_id}.jpg"
    return path if path.is_file() else None


def tidy_photos(now: Optional[float] = None) -> int:
    """Delete photos older than PHOTO_DAYS, and the oldest beyond MAX_PHOTOS."""
    now = now or time.time()
    gone = 0
    photos = sorted(PHOTOS.glob("*.jpg"), key=lambda p: p.stat().st_mtime) if PHOTOS.is_dir() else []
    for i, p in enumerate(photos):
        if now - p.stat().st_mtime > PHOTO_DAYS * 86400 or i < len(photos) - MAX_PHOTOS:
            p.unlink(missing_ok=True)
            p.with_suffix(".json").unlink(missing_ok=True)
            gone += 1
    return gone


IDLE_PHOTO_S = 180


def _language() -> str:
    """The household's language for words the screen shows (2026-10-28 review: a Spanish household saw English)."""
    try:
        from andy_companion import settings
        return "es" if settings.get().get("language") == "es" else "en"
    except Exception:
        return "en"


def idle_photo(now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """The family photo for the screen while Andy is idle: each kept photo in turn, three minutes each."""
    now = time.time() if now is None else now
    photos = sorted(PHOTOS.glob("*.jpg"), key=lambda p: p.stat().st_mtime) if PHOTOS.is_dir() else []
    if not photos:
        return None
    pick = photos[int(now // IDLE_PHOTO_S) % len(photos)]
    meta = _read(pick.with_suffix(".json"), {}) or {}
    from andy_companion import words
    when = words.weekday(datetime.fromtimestamp(meta.get("at") or pick.stat().st_mtime), _language())
    return {"photo": pick.stem, "name": _tidy(meta.get("name", ""), NAME_LEN), "caption": _tidy(meta.get("caption", ""), 140),
            "when": when, "sample": bool(meta.get("sample"))}


def show_photo(photo_id: str, name: str, caption: str = "", now: Optional[float] = None) -> None:
    title = ("Una foto de {name}" if _language() == "es" else "A photo from {name}").format(name=_tidy(name, NAME_LEN))
    _transient("show", {"kind": "photo", "title": title, "photo": photo_id,
                    "items": [{"summary": _tidy(caption, 140)}] if caption else [], "at": now or time.time()})
