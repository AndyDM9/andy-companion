"""While Andy searches for something (finder.find), the head is the search's alone: seek, face following while
Andy speaks, the glance at the TV and the idle hand-back all stand down until the search has pointed.

Why (2026-10-20, the founder's recorded tries): with face following switched off for a search, seek could still be
turning toward the person on the tick the search began, and on standing down it handed the head back to the camera's
face tracking at full weight; nothing switched that off, so three of four views pointed back at the person's desk.
"""

from __future__ import annotations

from typing import Any

KEY = "_andy_searching"


def begin(manager: Any) -> None:
    try:
        manager.__dict__[KEY] = True
    except Exception:
        pass


def end(manager: Any) -> None:
    try:
        manager.__dict__[KEY] = False
    except Exception:
        pass


def active(manager: Any) -> bool:
    return bool(getattr(manager, "__dict__", {}).get(KEY))
