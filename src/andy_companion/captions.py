"""Captions: what Andy says appears in large text on the screen beside it.

Only Andy's own words, never the person's. Sent to the screen server on this computer and kept in
its memory for three minutes (screen_server.CAPTION_FOR_S), long enough to read a story's part along
to the end; never written to disk or logged.
"""

from __future__ import annotations

import json
import os
import threading
import urllib.request
from functools import wraps

SCREEN = f"http://127.0.0.1:{os.environ.get('ANDY_SCREEN_PORT', '8090')}"


def send(text: str, opener=None) -> None:
    from andy_companion import board

    req = urllib.request.Request(f"{SCREEN}/api/caption?t={board.tokens()['screen']}", method="POST",
                                 data=json.dumps({"text": text}).encode(), headers={"Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=1):
            pass
    except Exception:
        pass   # captions are a help, never a reason to stop


def install(handler_class=None) -> bool:
    if handler_class is None:
        from reachy_mini_conversation_app.conversation_handler import ConversationHandler

        handler_class = ConversationHandler
    previous = handler_class._emit_transcript
    if getattr(previous, "_andy_captions", False):
        return False

    @wraps(previous)
    def emit(self, role: str, text: str, final: bool = True):
        previous(self, role, text, final)
        if role == "assistant" and final and str(text).strip():
            threading.Thread(target=send, args=(str(text),), daemon=True).start()
            try:
                from andy_companion.body import expressive

                expressive.heard_reply(str(text))     # a question tilts the head as it ends
            except Exception:
                pass

    emit._andy_captions = True
    handler_class._emit_transcript = emit
    return True
