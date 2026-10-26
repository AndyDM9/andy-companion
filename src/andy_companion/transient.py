"""Private, memory-only board state, owned by the screen server.

The conversation app and supervisor are separate processes. Their transient cards and
research answers cross loopback HTTP, never a file. No payload or address is logged.
"""
from __future__ import annotations

import json
import os
import urllib.request

owner = False


class Unavailable(Exception):
    pass


def call(action: str, data=None):
    from andy_companion import board

    if owner:
        return board.transient_action(action, data)
    port = int(os.environ.get("ANDY_SCREEN_PORT", "8090"))
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}/api/transient?t={board.tokens()['screen']}",
        data=json.dumps({"action": action, "data": data}).encode(),
        headers={"Content-Type": "application/json"}, method="POST")
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return json.load(response)["value"]
    except Exception:
        raise Unavailable("The local screen server is unavailable.") from None
