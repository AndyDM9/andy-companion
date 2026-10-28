"""What Andy keeps about the person, for the settings page: every item listed, each deletable.

Reminders, remembered moments, remembered facts (Pollen's `remember`, kept in Andy's own file),
notes shared with family, and photos family sent. A helper deleting anything is told to the person
by Andy, like any change on the settings page. Settings and the screen's links are not here.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime
from typing import Any, Dict, List

from andy_companion import board, gestures, moments, places, reminders, settings
from andy_companion.privacy import MEMORY_FILE

KINDS = {"reminder": ("a reminder", "reminders"), "moment": ("a remembered moment", "remembered moments"),
         "fact": ("a remembered fact", "remembered facts"), "shared": ("a shared note", "shared notes"),
         "pending": ("a message waiting to be said", "messages waiting to be said"),
         "recovery": ("a saved reminder copy needing review", "saved reminder copies needing review"),
         "settings_recovery": ("a saved settings copy needing review", "saved settings copies needing review"),
         "photo": ("a photo from family", "photos from family"), "place": ("a remembered place", "remembered places"),
         "gesture": ("a move taught by hand", "moves taught by hand")}


def _facts() -> List[Dict[str, Any]]:
    try:
        data = json.loads(MEMORY_FILE.read_text())
    except (OSError, ValueError):
        return []
    return [f for f in data.get("facts", []) if isinstance(f, dict) and f.get("id")]


def _write_facts(facts: List[Dict[str, Any]]) -> None:
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=MEMORY_FILE.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump({"version": 1, "facts": facts}, f, ensure_ascii=False, indent=2)
    os.chmod(tmp, 0o600)
    os.replace(tmp, MEMORY_FILE)


def _when(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%a, %b %-d, %-I:%M %p").replace("AM", "am").replace("PM", "pm")


def summary() -> Dict[str, List[Dict[str, str]]]:
    photos = sorted(board.PHOTOS.glob("*.jpg"), key=lambda p: p.stat().st_mtime) if board.PHOTOS.is_dir() else []
    return {
        "reminder": [{"id": r["id"], "text": r["text"], "when": _when(r["due"]) + (" · daily" if r.get("repeat") == "daily" else "")}
                     for r in reminders.pending()],
        "moment": [{"id": m["id"], "text": m["what"], "when": moments.spoken_day(m["on"])}
                   for m in moments._load() if not moments._expired(m)],     # past ones too: kept a week to ask after
        "fact": [{"id": f["id"], "text": str(f.get("text", "")),
                  "when": _when(f["createdAt"] / 1000) if isinstance(f.get("createdAt"), (int, float)) else ""} for f in _facts()],
        "shared": [{"id": s["id"], "text": s["note"], "when": _when(s["at"])} for s in board.shared()],
        "photo": [{"id": p.stem, "text": "Photo", "when": _when(p.stat().st_mtime)} for p in photos],
        "place": [{"id": p["id"], "text": f"{p['what']}: {p['where']}", "when": _when(p["at"])} for p in places.kept()],
        # Moves taught by hand carry a name ("Sofia's wave"): listed and forgotten here too (2026-10-28 audit).
        "gesture": [{"id": name, "text": name, "when": _when(g["at"]) if isinstance(g.get("at"), (int, float)) else ""}
                    for name, g in gestures._load().items() if isinstance(g, dict)],
        "recovery": [{"id": r["id"], "text": "Saved reminder copy — could not be loaded", "when": _when(r["at"])}
                     for r in reminders.recovery_files()],
        "settings_recovery": [{"id": r["id"], "text": "Saved settings copy — could not be loaded", "when": _when(r["at"])}
                              for r in settings.recovery_files()],
        "pending": [{"id": e["id"], "text": str(e.get("topic") or e.get("text") or e.get("what") or e.get("caption") or e.get("type", "")),
                     "when": _when(e["at"])} for e in board.pending_entries()
                    if e.get("id") and e.get("type") not in board.KEPT_UNTIL_SAID],
    }


def delete(kind: str, item_id: str) -> bool:
    item_id = str(item_id)
    if kind == "reminder":
        return reminders.cancel(item_id)
    if kind == "recovery":
        return reminders.delete_recovery(item_id)
    if kind == "settings_recovery":
        return settings.delete_recovery(item_id)
    if kind == "moment":
        return moments.remove(item_id)          # by its exact id: never by words, which could match many
    if kind == "fact":
        with board.locked(MEMORY_FILE):     # Andy's own deletes, one at a time (Pollen's remember writes it too)
            facts = _facts()
            kept_facts = [f for f in facts if f["id"] != item_id]
            if len(kept_facts) == len(facts):
                return False
            _write_facts(kept_facts)
        return True
    if kind == "shared":
        return board.unshare(item_id)
    if kind == "place":
        return places.remove(item_id)
    if kind == "gesture":
        return gestures.remove(item_id)
    if kind == "pending":
        return board.delete_pending(item_id)
    if kind == "photo":
        path = board.photo_path(item_id)
        if path is None:
            return False
        path.unlink(missing_ok=True)
        path.with_suffix(".json").unlink(missing_ok=True)
        board.drop_photo_notes(item_id)
        return True
    raise ValueError("Unknown kind of item.")


def delete_everything() -> Dict[str, int]:
    """Everything listed, and what was waiting to be said: family messages and answers Andy looked into (they hold
    words too; 2026-10-25 review). The notes saying who changed or deleted what stay, so the person hears this one."""
    counts = {}
    for kind, items in summary().items():
        if kind == "pending":
            continue
        counts[kind] = sum(1 for it in items if delete(kind, it["id"]))
    counts["pending"] = board.clear_pending()
    board.clear_screen()
    board._transient("clear-private")
    places._last_seen.clear()
    return counts


def words_for(counts: Dict[str, int]) -> List[str]:
    """{"reminder": 1, "fact": 2} -> ["a reminder", "2 remembered facts"], for Andy to say."""
    out = []
    for kind, n in counts.items():
        if n:
            one, many = KINDS[kind]
            out.append(one if n == 1 else f"{n} {many}")
    return out
