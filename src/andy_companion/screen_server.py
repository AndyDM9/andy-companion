"""Andy's screen (a TV or monitor beside Andy) and the family page, served from this computer.

    /screen?t=<screen token>    the day clock, what's next, and what Andy is showing now
    /family?k=<family token>    what the person chose to share; send Andy a message or a link
    /hood?t=<screen token>      under the hood: how long each part of Andy's recent turns took
    /setup?s=<setup token>      set Andy up: town, news sites, language, pace, volume, captions

Links carry random tokens (board.tokens()); `scripts/settings.py links` prints them. Standard
library only. Opening the family page tells the person who looked.
"""

from __future__ import annotations

import hmac
import json
import logging
import os
import threading
from collections import deque
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from andy_companion import board, clock, reminders

logger = logging.getLogger("andy.screen")
PAGES = Path(__file__).parent / "pages"
CAPTION_FOR_S = 20.0
# Andy's last spoken words, for the screen's captions. Memory only: never written to disk or logged.
_caption: Dict[str, Any] = {"text": "", "at": 0.0}


def set_caption(text: str, now: Optional[float] = None) -> None:
    import time as _t
    _caption["text"] = " ".join(str(text).split())[:400]
    _caption["at"] = now if now is not None else _t.time()


def caption(now: Optional[float] = None) -> str:
    import time as _t
    return _caption["text"] if (now if now is not None else _t.time()) - _caption["at"] <= CAPTION_FOR_S else ""


# Andy's recent turns as numbers and tool names only (turns.py), for /hood. Memory only.
_turns: "deque[Dict[str, Any]]" = deque(maxlen=40)


# This month's Tavily credits, as numbers (turns.tavily_usage_loop). Memory only.
_tavily: Dict[str, Any] = {}


def set_tavily(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("bad usage")
    by = data.get("by") if isinstance(data.get("by"), dict) else {}
    clean = {"plan": " ".join(str(data.get("plan", "")).split())[:40], "used": _ms(data.get("used")),
             "limit": _ms(data.get("limit")),
             "by": {k: _ms(by.get(k)) or 0 for k in ("search", "extract", "crawl", "map", "research")}}
    _tavily.clear()
    _tavily.update(clean)
    return clean


# Times the person talked over Andy and he stopped: how much of his reply was cut. Memory only.
_interrupts: "deque[Dict[str, int]]" = deque(maxlen=40)


def add_interrupt(data: Dict[str, Any]) -> Dict[str, int]:
    import time as _t

    cut = _ms(data.get("interrupt_ms"))
    if cut is None:
        raise ValueError("bad interruption")
    entry = {"at": int(_t.time()), "cut_ms": cut}
    _interrupts.append(entry)
    return entry


def _ms(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value) if 0 <= value < 600_000 else None


def add_turn(data: Dict[str, Any]) -> Dict[str, Any]:
    """Keep one turn, rebuilt from numbers and well-formed tool names so no words can ride along."""
    import time as _t
    from andy_companion.turns import TOOL_NAME

    reply = _ms(data.get("reply_ms"))
    if reply is None:
        raise ValueError("bad turn")
    tools = [{"name": t["name"], "ms": _ms(t.get("ms"))} for t in list(data.get("tools") or [])[:6]
             if isinstance(t, dict) and TOOL_NAME.match(str(t.get("name", ""))) and _ms(t.get("ms")) is not None]
    turn = {"at": int(_t.time()), "hearing_ms": _ms(data.get("hearing_ms")), "reply_ms": reply,
            "total_ms": _ms(data.get("total_ms")) if _ms(data.get("total_ms")) is not None else reply, "tools": tools}
    _turns.append(turn)
    return turn


def _median(values: List[int]) -> Optional[int]:
    values = sorted(v for v in values if v is not None)
    if not values:
        return None
    mid = len(values) // 2
    return values[mid] if len(values) % 2 else round((values[mid - 1] + values[mid]) / 2)


RESULTS = Path(__file__).resolve().parents[2] / "evals" / "results"


def _when(card: Dict[str, Any]) -> datetime:
    """When a scorecard ran. Older ones carry no zone: a Nebius job's clock is UTC, this computer's is local."""
    from datetime import timezone

    t = datetime.fromisoformat(str(card["ran"]))
    if t.tzinfo is None:
        t = t.replace(tzinfo=timezone.utc) if "Nebius" in str(card.get("ran_on", "")) else t.astimezone()
    return t


def proof(results: Path = RESULTS) -> Optional[Dict[str, Any]]:
    """The newest conversation-suite scorecard, as numbers (none in an installed app without evals/)."""
    best: Optional[Dict[str, Any]] = None
    for path in sorted(results.glob("*.json")) if results.is_dir() else []:
        try:
            card = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(card, dict) or "per_run" not in card or "ran" not in card:
            continue
        try:
            if best is None or _when(card) > _when(best):
                best = card
        except ValueError:
            continue
    if best is None:
        return None
    return {"suite": best.get("suite"), "per_run": best.get("per_run"), "total": best.get("total"),
            "judge": str(best.get("judge", "")).split("/")[-1], "ran": _when(best).astimezone().strftime("%Y-%m-%d"),
            "ran_on": best.get("ran_on", "this computer")}


def hood_state() -> Dict[str, Any]:
    turns = list(_turns)
    plain = [t for t in turns if not t["tools"]]
    return {
        "turns": list(reversed(turns[-8:])),
        "count": len(turns),
        "proof": proof(),
        "tavily": dict(_tavily) or None,
        "interruptions": {"count": len(_interrupts),
                          "last_cut_ms": _interrupts[-1]["cut_ms"] if _interrupts else None},
        "median": {"hearing_ms": _median([t["hearing_ms"] for t in turns]),
                   "reply_ms": _median([t["reply_ms"] for t in plain]),
                   "total_ms": _median([t["total_ms"] for t in plain])},
    }


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
    from andy_companion import settings

    return {"today": clock.today(now, settings.get().get("language", "en")), "hour": now.hour, "plan": plan}


def screen_state(now: Optional[datetime] = None) -> Dict[str, Any]:
    from andy_companion import settings

    state = today_plan(now)
    state["showing"] = board.showing()
    state["caption"] = caption() if settings.get().get("captions", True) else ""
    return state


def family_state() -> Dict[str, Any]:
    return {"shared": [{"id": s["id"], "note": s["note"],
                        "when": datetime.fromtimestamp(s["at"]).strftime("%A %-d %B, %-I:%M %p").replace("AM", "am").replace("PM", "pm")}
                       for s in reversed(board.shared())]}


def setup_state() -> Dict[str, Any]:
    from andy_companion import setup_page

    t = board.tokens()
    return {"settings": setup_page.state(),
            "links": {"screen": f"/screen?t={t['screen']}", "family": f"/family?k={t['family']}",
                      "hood": f"/hood?t={t['screen']}"}}


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
        if url.path == "/hood" and _ok(q.get("t"), "screen"):
            return self._page("hood.html")
        if url.path == "/api/hood" and _ok(q.get("t"), "screen"):
            return self._json(hood_state())
        if url.path == "/setup" and _ok(q.get("s"), "setup"):
            return self._page("setup.html")
        if url.path == "/api/setup" and _ok(q.get("s"), "setup"):
            return self._json(setup_state())
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
        local = self.client_address[0] in ("127.0.0.1", "::1")
        if url.path in ("/api/caption", "/api/turn") and _ok(q.get("t"), "screen") and local:
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json({"error": "too long"}, 413)
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(data, dict):
                    raise ValueError("not an object")
                if url.path == "/api/caption":
                    set_caption(data.get("text", ""))
                elif "interrupt_ms" in data:
                    add_interrupt(data)
                elif "tavily" in data:
                    set_tavily(data["tavily"])
                else:
                    add_turn(data)
            except (ValueError, TypeError, AttributeError):
                return self._json({"error": "bad request"}, 400)
            return self._json({"ok": True})
        if url.path.startswith("/api/setup") and _ok(q.get("s"), "setup"):
            length = int(self.headers.get("Content-Length") or 0)
            if length > MAX_BODY:
                return self._json({"error": "That is too long."}, 413)
            try:
                data = json.loads(self.rfile.read(length) or b"{}")
                if not isinstance(data, dict):
                    raise ValueError("Something went wrong; please try again.")
                from andy_companion import setup_page

                if url.path == "/api/setup":
                    changed = setup_page.apply(data.get("name", ""), data.get("settings") or {})
                    return self._json({"ok": True, "changed": changed, **setup_state()})
                if url.path == "/api/setup/new-family-link":
                    board.new_family_link()
                    return self._json({"ok": True, **setup_state()})
            except ValueError as e:
                return self._json({"error": str(e)}, 400)
            return self._send(404, b"Not found", "text/plain")
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
