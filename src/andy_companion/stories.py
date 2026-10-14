"""Story time: Andy reads a real story aloud, a part at a time, and keeps your place.

The stories (`story_texts.json`) are public domain: Aesop's fables as told in The Aesop for Children
(1919), O. Henry's The Gift of the Magi (1906) and two of Kipling's Just So Stories (1902), from
Project Gutenberg's texts. A long story is read in parts of about PART_WORDS words (a minute and a
half aloud), ending on a paragraph, and Andy asks "Shall I go on?" between parts. The bookmark (which
story, which part) is kept, so "Let's carry on with the story" works another day. The screen shows a
"Story time" card with the title, the author, where it's from and the part.

Andy may also make a story up when asked for one about something; then it says it made it up.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional

from andy_companion.reminders import DATA_DIR

TEXTS = Path(__file__).with_name("story_texts.json")
BOOKMARK = DATA_DIR / "story.json"
PART_WORDS = 220
WORDS_PER_MINUTE = 140

HOW = ("Read 'text' aloud exactly as written, word for word, at an easy pace, with feeling but no voices or "
       "sound effects. Say the title and author first only when 'part' is 1. Afterwards: if there is more, ask "
       "'Shall I go on?' and wait; if they want to stop, say you'll keep their place. At the end, let the story "
       "settle; you might ask what they thought of it.")


@lru_cache(maxsize=1)
def library() -> List[Dict[str, Any]]:
    return json.loads(TEXTS.read_text())["stories"]


def parts(story: Dict[str, Any]) -> List[str]:
    """The story in parts of about PART_WORDS words, each ending on a paragraph."""
    out: List[str] = []
    current: List[str] = []
    words = 0
    for para in story["paragraphs"]:
        current.append(para)
        words += len(para.split())
        if words >= PART_WORDS:
            out.append("\n\n".join(current))
            current, words = [], 0
    if current:
        # A short tail joins the part before it rather than standing alone.
        if out and words < PART_WORDS // 3:
            out[-1] += "\n\n" + "\n\n".join(current)
        else:
            out.append("\n\n".join(current))
    return out


def minutes(story: Dict[str, Any]) -> int:
    return max(1, round(sum(len(p.split()) for p in story["paragraphs"]) / WORDS_PER_MINUTE))


def find(title: str) -> Optional[Dict[str, Any]]:
    want = " ".join(str(title or "").lower().replace("the ", " ").split())
    if not want:
        return None
    for s in library():
        name = " ".join(s["title"].lower().replace("the ", " ").split())
        if want in name or name in want:
            return s
    words = set(want.split()) - {"a", "and", "of", "his", "how", "got", "story"}
    best = max(library(), key=lambda s: len(words & set(s["title"].lower().split())))
    return best if words & set(best["title"].lower().split()) else None


def catalogue() -> List[Dict[str, Any]]:
    return [{"title": s["title"], "author": s["author"], "minutes": minutes(s)} for s in library()]


def _bookmark() -> Dict[str, Any]:
    try:
        data = json.loads(BOOKMARK.read_text())
        return data if isinstance(data, dict) else {}
    except (OSError, ValueError):
        return {}


def _save(data: Dict[str, Any]) -> None:
    BOOKMARK.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=BOOKMARK.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        json.dump(data, f)
    os.chmod(tmp, 0o600)
    os.replace(tmp, BOOKMARK)


def _part(story: Dict[str, Any], n: int, now: Optional[float] = None) -> Dict[str, Any]:
    ps = parts(story)
    n = max(1, min(n, len(ps)))
    more = n < len(ps)
    data = _bookmark()
    if more:
        data.update(story=story["id"], next=n + 1, at=now or time.time())
    else:
        for key in ("story", "next", "at"):
            data.pop(key, None)
    _save(data)
    show(story, n, len(ps))
    return {"title": story["title"], "author": story["author"], "from": story["from"], "part": n, "of": len(ps),
            "more": more, "text": ps[n - 1], "how": HOW}


def start(title: str = "", now: Optional[float] = None) -> Dict[str, Any]:
    story = find(title) if title else None
    if title and story is None:
        return {"not_found": title, "stories": catalogue(),
                "say": "That one isn't in your story shelf. Offer two or three of these, or to make one up."}
    if story is None:                     # "Tell me a story": a short one to begin with
        fables = [s for s in library() if len(parts(s)) == 1]
        told = _bookmark().get("last_short", -1)
        i = (told + 1) % len(fables)
        data = _bookmark()
        data["last_short"] = i
        _save(data)
        story = fables[i]
    return _part(story, 1, now)


def carry_on(now: Optional[float] = None) -> Dict[str, Any]:
    mark = _bookmark()
    story = next((s for s in library() if s["id"] == mark.get("story")), None)
    if story is None:
        return {"no_story_open": True, "stories": catalogue(),
                "say": "There's no story to carry on. Offer to start one."}
    return _part(story, int(mark.get("next", 1)), now)


MAKE_UP = ("Make up a short, gentle story about {about} now (under two minutes aloud: a beginning, a small "
           "happening, a warm ending; nothing frightening or sad) and tell it straight away. Say plainly that you "
           "made it up, for example 'Here's a little story I've made up for you.'")


def make_up(about: str) -> Dict[str, Any]:
    """A story about something in particular is Andy's own; this only says how to tell it."""
    about = " ".join(str(about or "").split())[:120] or "something gentle"
    return {"make_up": True, "about": about, "how": MAKE_UP.format(about=about)}


def open_story() -> Optional[Dict[str, Any]]:
    """The story with a bookmark in it, for Andy's instructions: 'you were in the middle of …'."""
    mark = _bookmark()
    story = next((s for s in library() if s["id"] == mark.get("story")), None)
    if story is None:
        return None
    return {"title": story["title"], "next": mark.get("next"), "of": len(parts(story))}


def show(story: Dict[str, Any], n: int, total: int) -> None:
    from andy_companion import board

    items = [{"title": f"by {story['author']}", "summary": f"From {story['from']}. Public domain."}]
    if total > 1:
        items.append({"title": f"Part {n} of {total}"})
    board.show("story", story["title"], items)
