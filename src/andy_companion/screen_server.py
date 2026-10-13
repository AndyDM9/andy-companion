"""Andy's screen (a TV or monitor beside Andy) and the family page, served from this computer.

    /screen?t=<screen token>    the day clock, what's next, and what Andy is showing now
    /family?k=<family token>    what the person chose to share; send Andy a message or a link

Links carry random tokens (board.tokens()); `scripts/settings.py links` prints them. Standard
library only. Opening the family page tells the person who looked.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import threading
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, Optional
from urllib.parse import parse_qs, urlparse

from andy_companion import board, clock, reminders

logger = logging.getLogger("andy.screen")
PAGES = Path(__file__).parent / "pages"
MAX_BODY = 4096
HEADERS = {
    "Content-Security-Policy": ("default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline' "
                                "https://fonts.googleapis.com; font-src https://fonts.gstatic.com; connect-src 'self'; "
                                "img-src 'self' data:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-store",
}


def today_plan(now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now()
    items = [r for r in reminders.pending() if datetime.fromtimestamp(r["due"]).date() == now.date()]
    plan = [{"time": datetime.fromtimestamp(r["due"]).strftime("%-I:%M %p").lower(), "what": r["text"],
             "done": r["due"] < now.timestamp()} for r in items]
    return {"today": clock.today(now), "hour": now.hour, "plan": plan}


def screen_state(now: Optional[datetime] = None) -> Dict[str, Any]:
    state = today_plan(now)
    state["showing"] = board.showing()
    return state


def family_state() -> Dict[str, Any]:
    return {"shared": [{"id": s["id"], "note": s["note"],
                        "when": datetime.fromtimestamp(s["at"]).strftime("%A %-d %B, %-I:%M %p").replace("AM", "am").replace("PM", "pm")}
                       for s in reversed(board.shared())]}


def _ok(token: Optional[str], kind: str) -> bool:
    return bool(token) and hmac.compare_digest(token, board.tokens()[kind])


class Handler(BaseHTTPRequestHandler):
    server_version = "Andy"
    sys_version = ""

    def log_message(self, fmt: str, *args: Any) -> None:     # no URLs (they hold tokens) in any log
        return

    def _send(self, code: int, body: bytes, kind: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", kind)
        self.send_header("Content-Length", str(len(body)))
        for k, v in HEADERS.items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def _json(self, data: Any, code: int = 200) -> None:
        self._send(code, json.dumps(data).encode(), "application/json")

    def _page(self, name: str) -> None:
        self._send(200, (PAGES / name).read_bytes(), "text/html; charset=utf-8")

    def do_GET(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path == "/screen" and _ok(q.get("t"), "screen"):
            return self._page("screen.html")
        if url.path == "/api/screen" and _ok(q.get("t"), "screen"):
            return self._json(screen_state())
        if url.path == "/family" and _ok(q.get("k"), "family"):
            return self._page("family.html")
        if url.path == "/api/family" and _ok(q.get("k"), "family"):
            return self._json(family_state())
        if url.path == "/photo" and _ok(q.get("t"), "screen"):
            path = board.photo_path(q.get("id", ""))
            if path is not None:
                return self._send(200, path.read_bytes(), "image/jpeg")
        return self._send(404, b"Not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if not url.path.startswith("/api/family/") or not _ok(q.get("k"), "family"):
            return self._send(404, b"Not found", "text/plain")
        length = int(self.headers.get("Content-Length") or 0)
        limit = board.MAX_PHOTO_BYTES * 4 // 3 + MAX_BODY if url.path == "/api/family/photo" else MAX_BODY
        if length > limit:
            return self._json({"error": "That is too long."}, 413)
        try:
            data = json.loads(self.rfile.read(length) or b"{}")
            if url.path == "/api/family/look":
                board.looked(data.get("name", ""))
                return self._json({"ok": True})
            if url.path == "/api/family/photo":
                import base64

                raw = str(data.get("image", ""))
                raw = raw.split(",", 1)[1] if raw.startswith("data:") else raw
                try:
                    blob = base64.b64decode(raw, validate=True)
                except ValueError:
                    raise ValueError("That file is not a photo Andy can show.") from None
                board.save_photo(data.get("name", ""), blob, data.get("caption", ""))
                return self._json({"ok": True})
            if url.path == "/api/family/message":
                board.family_message(data.get("name", ""), data.get("text", ""), data.get("link", ""))
                return self._json({"ok": True})
        except ValueError as e:
            return self._json({"error": str(e)}, 400)
        return self._send(404, b"Not found", "text/plain")


def serve(host: Optional[str] = None, port: Optional[int] = None) -> ThreadingHTTPServer:
    host = host if host is not None else os.environ.get("ANDY_SCREEN_HOST", "0.0.0.0")
    port = port if port is not None else int(os.environ.get("ANDY_SCREEN_PORT", "8090"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    threading.Thread(target=httpd.serve_forever, name="andy-screen", daemon=True).start()
    logger.info("Andy's screen is served on port %d", port)
    return httpd
