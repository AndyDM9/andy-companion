"""What Andy's screen shows, what the person shares with family, and what family sends back.

Small owner-only files in Andy's folder, read by the screen server (screen_server.py):

- screen.json: what Andy is showing now (news, a look-up, a letter's summary). It expires after
  SHOW_FOR_S and is cleared, so the screen never becomes a record.
- shared.json: notes the person explicitly asked Andy to share with family. Nothing else is shared.
- inbox.json: messages and links family send to Andy, and who looked at the family page. The
  speaker says them to the person, then they are deleted: the person always hears who looked.
"""

from __future__ import annotations

import json
import os
import secrets
import tempfile
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from andy_companion.reminders import DATA_DIR

SCREEN = DATA_DIR / "screen.json"
SHARED = DATA_DIR / "shared.json"
INBOX = DATA_DIR / "inbox.json"
TOKENS = DATA_DIR / "tokens.json"
PHOTOS = DATA_DIR / "photos"
PHOTO_DAYS = 7
MAX_PHOTO_BYTES = 8 * 1024 * 1024
SHOW_FOR_S = 15 * 60
MAX_SHARED = 30
MAX_TEXT = 600
NAME_LEN = 40


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


# --- tokens: the screen link and the family link -------------------------------------------

def tokens() -> Dict[str, str]:
    data = _read(TOKENS, {})
    missing = [k for k in ("screen", "family", "setup") if not data.get(k)]
    if missing:
        for k in missing:                 # a new kind of link never changes the existing ones
            data[k] = secrets.token_urlsafe(12)
        _write(TOKENS, data)
    return data


def new_family_link() -> str:
    """Make a new family token, so an old link stops working."""
    data = tokens()
    data["family"] = secrets.token_urlsafe(12)
    _write(TOKENS, data)
    return data["family"]


# --- the screen -------------------------------------------------------------------------------

def show(kind: str, title: str, items: List[Dict[str, Any]], now: Optional[float] = None) -> None:
    """Put something on the screen beside Andy, for SHOW_FOR_S."""
    clean_items = [{k: _tidy(v, 300) for k, v in item.items() if k in ("title", "source", "summary", "when", "published")}
                   for item in items[:4]]
    _write(SCREEN, {"kind": _tidy(kind, 20), "title": _tidy(title, 80), "items": clean_items,
                    "at": now or time.time()})


def showing(now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    data = _read(SCREEN, None)
    if not data:
        return None
    if (now or time.time()) - data.get("at", 0) > SHOW_FOR_S:
        clear_screen()
        return None
    return data


def clear_screen() -> None:
    try:
        SCREEN.unlink()
    except FileNotFoundError:
        pass


# --- sharing with family ------------------------------------------------------------------------

def share(note: str, now: Optional[float] = None) -> Dict[str, Any]:
    note = _tidy(note)
    if not note:
        raise ValueError("What should I share?")
    items = _read(SHARED, [])
    item = {"id": secrets.token_hex(3), "note": note, "at": now or time.time()}
    _write(SHARED, (items + [item])[-MAX_SHARED:])
    return item


def shared() -> List[Dict[str, Any]]:
    return _read(SHARED, [])


def unshare(note_id: str) -> bool:
    items = _read(SHARED, [])
    kept = [i for i in items if i["id"] != note_id]
    if len(kept) == len(items):
        return False
    _write(SHARED, kept)
    return True


# --- what family send, and who looked -------------------------------------------------------

def _inbox_add(entry: Dict[str, Any]) -> None:
    items = _read(INBOX, [])
    _write(INBOX, (items + [entry])[-50:])


def family_message(name: str, text: str = "", link: str = "", now: Optional[float] = None) -> None:
    name, text, link = _tidy(name, NAME_LEN), _tidy(text), _tidy(link, 300)
    if not name or not (text or link):
        raise ValueError("A name and a message or link are needed.")
    if link and not link.startswith(("http://", "https://")):
        raise ValueError("A link starts with http:// or https://.")
    _inbox_add({"type": "message", "name": name, "text": text, "link": link, "at": now or time.time()})


def looked(name: str, now: Optional[float] = None) -> None:
    """Family opened the page. The person hears about it (once per name per hour)."""
    name = _tidy(name, NAME_LEN)
    if not name:
        raise ValueError("A name is needed.")
    now = now or time.time()
    recent = [e for e in _read(INBOX, []) if e["type"] == "look" and e["name"] == name and now - e["at"] < 3600]
    if not recent:
        _inbox_add({"type": "look", "name": name, "at": now})


def settings_changed(name: str, what: List[str], now: Optional[float] = None) -> None:
    """A helper changed Andy's settings on the setup page. The person hears who, and what."""
    name = _tidy(name, NAME_LEN)
    if not name or not what:
        raise ValueError("A name and what changed are needed.")
    _inbox_add({"type": "settings", "name": name, "what": [_tidy(w, 60) for w in what][:8], "at": now or time.time()})


def research_ready(topic: str, say: str, points: List[str], sources: List[Dict[str, Any]], failed: bool = False,
                   now: Optional[float] = None) -> None:
    """An answer Andy looked into is ready to say (looking.py); kept until said, like a family message."""
    _inbox_add({"type": "research", "topic": _tidy(topic, 120), "say": _tidy(say, 700),
                "points": [_tidy(p, 160) for p in points[:4]],
                "sources": [{"title": _tidy(s.get("title", ""), 140), "source": _tidy(s.get("source", ""), 60)}
                            for s in sources[:6]],
                "failed": bool(failed), "at": now or time.time()})


def next_for_person() -> Optional[Dict[str, Any]]:
    items = _read(INBOX, [])
    return items[0] if items else None


def delivered(entry: Dict[str, Any]) -> None:
    items = _read(INBOX, [])
    if entry in items:
        items.remove(entry)
        _write(INBOX, items)


# --- photos from family ---------------------------------------------------------------------

def save_photo(name: str, data: bytes, caption: str = "", now: Optional[float] = None) -> Dict[str, Any]:
    """Keep a photo family sent: decoded and re-encoded as a plain JPEG (which drops hidden data such
    as the place it was taken), at most 1600 pixels wide, deleted after PHOTO_DAYS."""
    import cv2
    import numpy as np

    name, caption = _tidy(name, NAME_LEN), _tidy(caption, 140)
    if not name:
        raise ValueError("A name is needed.")
    if not data or len(data) > MAX_PHOTO_BYTES:
        raise ValueError("The photo must be smaller than 8 MB.")
    img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if img is None or min(img.shape[:2]) < 32:
        raise ValueError("That file is not a photo Andy can show.")
    h, w = img.shape[:2]
    if w > 1600:
        img = cv2.resize(img, (1600, int(h * 1600 / w)), interpolation=cv2.INTER_AREA)
    ok, jpeg = cv2.imencode(".jpg", img, [int(cv2.IMWRITE_JPEG_QUALITY), 88])
    if not ok:
        raise ValueError("The photo could not be prepared.")
    PHOTOS.mkdir(parents=True, exist_ok=True, mode=0o700)
    photo_id = secrets.token_hex(6)
    path = PHOTOS / f"{photo_id}.jpg"
    path.write_bytes(jpeg.tobytes())
    os.chmod(path, 0o600)
    now = now or time.time()
    _inbox_add({"type": "photo", "name": name, "caption": caption, "photo": photo_id, "at": now})
    tidy_photos(now)
    return {"photo": photo_id}


def photo_path(photo_id: str) -> Optional[Path]:
    if not photo_id or not all(c in "0123456789abcdef" for c in photo_id) or len(photo_id) != 12:
        return None
    path = PHOTOS / f"{photo_id}.jpg"
    return path if path.is_file() else None


def tidy_photos(now: Optional[float] = None) -> int:
    now = now or time.time()
    gone = 0
    for p in PHOTOS.glob("*.jpg") if PHOTOS.is_dir() else []:
        if now - p.stat().st_mtime > PHOTO_DAYS * 86400:
            p.unlink()
            gone += 1
    return gone


def show_photo(photo_id: str, name: str, caption: str = "", now: Optional[float] = None) -> None:
    _write(SCREEN, {"kind": "photo", "title": f"A photo from {_tidy(name, NAME_LEN)}", "photo": photo_id,
                    "items": [{"summary": _tidy(caption, 140)}] if caption else [], "at": now or time.time()})
