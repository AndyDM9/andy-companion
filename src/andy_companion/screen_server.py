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
import re
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


FONTS = {f"/fonts/atkinson-hyperlegible-{w}.woff2": f"fonts/atkinson-hyperlegible-{w}.woff2" for w in (400, 700)}

# What Andy's camera saw when it found something ("where are my glasses?"), for the screen. Memory
# only, for FRAME_FOR_S; never written to disk or logged. Posted by Andy's own process on this computer.
FRAME_FOR_S = 120
MAX_FRAME = 1_500_000
_frame: Dict[str, Any] = {"jpeg": b"", "at": 0.0}


def set_frame(jpeg: bytes, now: Optional[float] = None) -> None:
    import time as _t

    _frame["jpeg"] = bytes(jpeg)[:MAX_FRAME]
    _frame["at"] = now if now is not None else _t.time()


def frame(now: Optional[float] = None) -> bytes:
    import time as _t

    fresh = (now if now is not None else _t.time()) - _frame["at"] <= FRAME_FOR_S
    return _frame["jpeg"] if fresh and _frame["jpeg"].startswith(b"\xff\xd8") else b""


def caption(now: Optional[float] = None) -> str:
    import time as _t
    return _caption["text"] if (now if now is not None else _t.time()) - _caption["at"] <= CAPTION_FOR_S else ""


# Andy's recent turns as numbers and tool names only (turns.py), for /hood. Memory only.
_turns: "deque[Dict[str, Any]]" = deque(maxlen=40)


# What Andy is doing right now (live.py), refreshed several times a second. Memory only.
_live: Dict[str, Any] = {"state": "", "tool": "", "at": 0.0}
LIVE_STALE_S = 12.0


def set_live(data: Dict[str, Any], now: Optional[float] = None) -> None:
    import time as _t
    from andy_companion import live
    from andy_companion.turns import TOOL_NAME

    state = str(data.get("state", "")) if isinstance(data, dict) else ""
    tool = str(data.get("tool", "")) if isinstance(data, dict) else ""
    if state not in live.STATES or (tool and not TOOL_NAME.match(tool)):
        raise ValueError("bad state")
    _live.update(state=state, tool=tool, at=now if now is not None else _t.time())


def live_state(now: Optional[float] = None) -> Dict[str, Any]:
    """The state strip: quiet or asleep from the supervisor, else the app's live state, else 'away'."""
    import time as _t
    from andy_companion import settings, state, words

    now = now if now is not None else _t.time()
    language = settings.get().get("language", "en")
    mode = state.current()
    if mode["mode"] == "quiet":
        until = datetime.fromtimestamp(mode["until"]).strftime("%-I:%M %p").lower() if mode.get("until") else ""
        key, tool = "quiet", ""
    elif mode["mode"] == "asleep":
        key, tool, until = "asleep", "", ""
    elif _live["state"] and now - float(_live["at"]) <= LIVE_STALE_S:
        key, tool, until = _live["state"], _live["tool"], ""
    else:
        key, tool, until = "away", "", ""
    stage = {"hearing": "hear", "thinking": "think", "working": "tools", "speaking": "speak"}.get(key, "")
    return {"state": key, "tool": tool, "stage": stage, "label": words.state_label(key, tool, language, until)}


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


def _health() -> List[Dict[str, str]]:
    from andy_companion import health

    return health.tiles(float(_live["at"]), _weather["card"], _tavily)


def hood_state() -> Dict[str, Any]:
    turns = list(_turns)
    plain = [t for t in turns if not t["tools"]]
    return {
        "turns": list(reversed(turns[-8:])),
        "count": len(turns),
        "proof": proof(),
        "tavily": dict(_tavily) or None,
        "health": _health(),
        "interruptions": {"count": len(_interrupts),
                          "last_cut_ms": _interrupts[-1]["cut_ms"] if _interrupts else None},
        "median": {"hearing_ms": _median([t["hearing_ms"] for t in turns]),
                   "reply_ms": _median([t["reply_ms"] for t in plain]),
                   "total_ms": _median([t["total_ms"] for t in plain])},
    }


MAX_BODY = 4096
HEADERS = {
    "Content-Security-Policy": ("default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                                "font-src 'self'; connect-src 'self'; "
                                "img-src 'self' data:; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"),
    "Referrer-Policy": "no-referrer",
    "X-Content-Type-Options": "nosniff",
    "Cache-Control": "no-store",
}


# The weather tile on the screen: refreshed in the background every 30 minutes, never while a page waits.
WEATHER_EVERY_S = 1800
_weather: Dict[str, Any] = {"card": None, "at": 0.0, "busy": False}


def _refresh_weather() -> None:
    import time as _t
    from andy_companion import weather

    try:
        spot = weather.where()
        found = weather.forecast(spot["lat"], spot["lon"], periods=2)
        _weather["card"] = {"periods": [{"name": p["name"], "temperature": p.get("temperature", ""), "short": p.get("short", ""),
                                         "rain": p.get("rain")} for p in found["periods"]],
                            "alerts": found["alerts"][:1], "source": "weather.gov"}
    except Exception:
        pass   # keep the last card; a stale forecast is replaced on the next try
    finally:
        _weather["at"], _weather["busy"] = _t.time(), False


def weather_card(now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    import time as _t
    from andy_companion import settings

    now = now if now is not None else _t.time()
    if not settings.get().get("place"):
        return None
    if not _weather["busy"] and now - _weather["at"] >= WEATHER_EVERY_S:
        _weather["busy"] = True
        threading.Thread(target=_refresh_weather, name="andy-weather", daemon=True).start()
    card = _weather["card"]
    language = settings.get().get("language", "en")
    if card and language == "es":
        from andy_companion import words

        card = {**card, "periods": [{**p, "name": words.weather_period(p["name"], "es"), "short": words.sky(p["short"], "es")}
                                    for p in card["periods"]]}
    return card


def today_plan(now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now()
    items = [r for r in reminders.pending() if datetime.fromtimestamp(r["due"]).date() == now.date()]
    plan = [{"time": datetime.fromtimestamp(r["due"]).strftime("%-I:%M %p").lower(), "what": r["text"],
             "done": r["due"] < now.timestamp(), "due": int(r["due"])} for r in items]
    from andy_companion import settings

    return {"today": clock.today(now, settings.get().get("language", "en")), "hour": now.hour, "plan": plan}


def settings_qr(host: str) -> str:
    """The settings page's address as a QR code (an SVG data address), for the screen's two minutes."""
    import io
    import urllib.parse

    import segno

    url = f"http://{host}/setup?s={board.tokens()['setup']}"
    out = io.BytesIO()
    segno.make(url, error="m").save(out, kind="svg", scale=10, border=2, dark="#142339", light="#ffffff",
                                     xmldecl=False, svgns=True)
    return "data:image/svg+xml," + urllib.parse.quote(out.getvalue().decode())


def screen_state(now: Optional[datetime] = None, host: str = "") -> Dict[str, Any]:
    from andy_companion import settings

    state = today_plan(now)
    state["showing"] = board.showing()
    if state["showing"] and state["showing"].get("kind") == "code" and host:
        state["showing"] = {**state["showing"], "qr": settings_qr(host)}
    state["caption"] = caption() if settings.get().get("captions", True) else ""
    state["weather"] = weather_card()
    hour = (now or datetime.now()).hour
    s = settings.get()
    start, end = int(s.get("night_from", 21)), int(s.get("night_to", 7))
    state["night"] = (start <= hour or hour < end) if start > end else (start <= hour < end)
    state["idle_photo"] = board.idle_photo() if s.get("screen_photos", True) and not state["night"] else None
    state["calm"] = bool(s.get("screen_calm", False))
    return state


def family_state() -> Dict[str, Any]:
    return {"shared": [{"id": s["id"], "note": s["note"],
                        "when": datetime.fromtimestamp(s["at"]).strftime("%A %-d %B, %-I:%M %p").replace("AM", "am").replace("PM", "pm")}
                       for s in reversed(board.shared())]}


def setup_state() -> Dict[str, Any]:
    from andy_companion import setup_page

    t = board.tokens()
    from andy_companion import kept

    return {"settings": setup_page.state(), "kept": kept.summary(), "now": live_state(), "tavily": dict(_tavily) or None,
            "links": {"screen": f"/screen?t={t['screen']}", "family": f"/family?k={t['family']}",
                      "hood": f"/hood?t={t['screen']}"}}


def _ok(token: Optional[str], kind: str) -> bool:
    if not token:
        return False
    # Bytes, so a token with characters outside ASCII is simply wrong rather than an error.
    return hmac.compare_digest(token.encode("utf-8", "replace"), board.tokens()[kind].encode())


def _no_constant(name: str) -> None:
    raise ValueError("That is not a number.")


def _object(raw: bytes) -> dict:
    """A request body as a JSON object; anything else (a list, NaN, Infinity) is a ValueError."""
    data = json.loads(raw or b"{}", parse_constant=_no_constant)
    if not isinstance(data, dict):
        raise ValueError("Something went wrong; please try again.")
    return data


class Handler(BaseHTTPRequestHandler):
    timeout = 10        # a connection that stalls is dropped, so it can't hold a thread forever

    def _length(self) -> int:
        """The body's declared length; -1 (refused by every caller's range check) if it isn't a sane number."""
        try:
            length = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            return -1
        return length if length >= 0 else -1

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
            # The settings code points at this same address, as the screen reached it on the home network.
            host = self.headers.get("Host", "")
            return self._json(screen_state(host=host if re.fullmatch(r"[A-Za-z0-9.\-]+(:\d+)?", host) else ""))
        if url.path == "/api/state" and _ok(q.get("t"), "screen"):
            return self._json(live_state())
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
        if url.path in FONTS:           # Andy's own copy of its typeface; no token, nothing private
            return self._send(200, (PAGES / FONTS[url.path]).read_bytes(), "font/woff2")
        if url.path == "/frame" and _ok(q.get("t"), "screen"):
            data = frame()
            if data:
                return self._send(200, data, "image/jpeg")
            return self._send(404, b"Not found", "text/plain")
        if url.path == "/photo" and _ok(q.get("t"), "screen"):
            path = board.photo_path(q.get("id", ""))
            if path is not None:
                return self._send(200, path.read_bytes(), "image/jpeg")
        return self._send(404, b"Not found", "text/plain")

    def do_POST(self) -> None:  # noqa: N802
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        local = self.client_address[0] in ("127.0.0.1", "::1")
        if url.path == "/api/frame" and _ok(q.get("t"), "screen") and local:
            length = self._length()
            if not 0 < length <= MAX_FRAME:
                return self._json({"error": "too long"}, 413)
            data = self.rfile.read(length)
            if not data.startswith(b"\xff\xd8"):
                return self._json({"error": "not a picture"}, 400)
            set_frame(data)
            return self._json({"ok": True})
        if url.path in ("/api/caption", "/api/turn") and _ok(q.get("t"), "screen") and local:
            length = self._length()
            if not 0 <= length <= MAX_BODY:
                return self._json({"error": "too long"}, 413)
            try:
                data = _object(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("not an object")
                if url.path == "/api/caption":
                    set_caption(data.get("text", ""))
                elif "interrupt_ms" in data:
                    add_interrupt(data)
                elif "tavily" in data:
                    set_tavily(data["tavily"])
                elif "live" in data:
                    set_live(data["live"])
                else:
                    add_turn(data)
            except (ValueError, TypeError, AttributeError, OverflowError):
                return self._json({"error": "bad request"}, 400)
            return self._json({"ok": True})
        if url.path.startswith("/api/setup") and _ok(q.get("s"), "setup"):
            length = self._length()
            if not 0 <= length <= MAX_BODY:
                return self._json({"error": "That is too long."}, 413)
            try:
                data = _object(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Something went wrong; please try again.")
                from andy_companion import setup_page

                if url.path == "/api/setup":
                    changed = setup_page.apply(data.get("name", ""), data.get("settings") or {})
                    return self._json({"ok": True, "changed": changed, **setup_state()})
                if url.path in ("/api/setup/delete", "/api/setup/delete-all"):
                    from andy_companion import kept

                    name = " ".join(str(data.get("name", "")).split())[:board.NAME_LEN]
                    if not name:
                        raise ValueError("Your first name is needed, so Andy can tell them who deleted it.")
                    if url.path == "/api/setup/delete":
                        kind = str(data.get("kind", ""))
                        if not kept.delete(kind, str(data.get("id", ""))):
                            raise ValueError("That was already gone.")
                        counts = {kind: 1}
                    else:
                        counts = kept.delete_everything()
                    words = kept.words_for(counts)
                    if words:
                        board.kept_deleted(name, words)
                    return self._json({"ok": True, "deleted": words, **setup_state()})
                if url.path == "/api/setup/show-screen":
                    board.show_screen_check()
                    return self._json({"ok": True, **setup_state()})
                if url.path == "/api/setup/new-settings-link":
                    board.new_setup_link()
                    return self._json({"ok": True, "moved": True})
                if url.path == "/api/setup/new-family-link":
                    board.new_family_link()
                    return self._json({"ok": True, **setup_state()})
            except ValueError as e:
                return self._json({"error": str(e)}, 400)
            except (TypeError, AttributeError, OverflowError):
                return self._json({"error": "Something went wrong; please try again."}, 400)
            return self._send(404, b"Not found", "text/plain")
        if not url.path.startswith("/api/family/") or not _ok(q.get("k"), "family"):
            return self._send(404, b"Not found", "text/plain")
        length = self._length()
        limit = board.MAX_PHOTO_BYTES * 4 // 3 + MAX_BODY if url.path == "/api/family/photo" else MAX_BODY
        if not 0 <= length <= limit:
            return self._json({"error": "That is too long."}, 413)
        try:
            data = _object(self.rfile.read(length))
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
        except (TypeError, AttributeError, OverflowError):
            return self._json({"error": "Something went wrong; please try again."}, 400)
        return self._send(404, b"Not found", "text/plain")


def _housekeeping(every_s: float = 60.0, rounds: Optional[int] = None) -> None:
    """Expired cards leave the screen file and photos over a week old are deleted, even when no TV is open
    to ask for them (a letter card or a research question must never become a lasting record)."""
    import time as _t

    n = 0
    while rounds is None or n < rounds:
        n += 1
        try:
            board.showing()
            board.tidy_photos()
        except Exception:
            logger.debug("screen housekeeping failed", exc_info=True)
        _t.sleep(every_s)


def serve(host: Optional[str] = None, port: Optional[int] = None) -> ThreadingHTTPServer:
    host = host if host is not None else os.environ.get("ANDY_SCREEN_HOST", "0.0.0.0")
    port = port if port is not None else int(os.environ.get("ANDY_SCREEN_PORT", "8090"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    threading.Thread(target=httpd.serve_forever, name="andy-screen", daemon=True).start()
    threading.Thread(target=_housekeeping, name="andy-screen-tidy", daemon=True).start()
    logger.info("Andy's screen is served on port %d", port)
    return httpd
