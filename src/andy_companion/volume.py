"""The robot's speaker volume, through the Reachy Mini daemon (`/api/volume`)."""

from __future__ import annotations

import json
import urllib.request
from typing import Optional

from andy_companion import settings

DAEMON = "http://127.0.0.1:8000"


def _call(path: str, body: Optional[dict] = None) -> dict:
    req = urllib.request.Request(DAEMON + path, method="POST" if body is not None else "GET",
                                 data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read() or b"{}")


def current() -> int:
    return int(_call("/api/volume/current").get("volume", 80))


def set_level(level: int) -> None:
    _call("/api/volume/set", {"volume": int(level)})


def apply_saved() -> bool:
    """At startup: the volume the person chose last time."""
    level = settings.get()["volume"]
    if level is None:
        return False
    try:
        set_level(level)
        return True
    except Exception:
        return False
