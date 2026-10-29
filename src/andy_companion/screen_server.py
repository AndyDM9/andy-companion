"""Andy's screen (a TV or monitor beside Andy) and the family page, served from this computer.

    /screen?t=<screen token>    the day clock, what's next, and what Andy is showing now
    /family?k=<family token>    what the person chose to share; send Andy a message or a link
    /hood?t=<hood token>        under the hood: how long each part of Andy's recent turns took
    /setup?s=<setup token>      set Andy up: town, news sites, language, pace, volume, captions

Links carry random tokens (board.tokens()); `scripts/settings.py links` prints them. Standard
library only. Opening the family page tells the person who looked.
"""

from __future__ import annotations

import base64
import contextlib
import binascii
import hmac
import ipaddress
import json
import logging
import os
import re
import threading
from collections import deque
from datetime import datetime, timedelta
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import parse_qs, urlparse

from andy_companion import board, clock, reminders

logger = logging.getLogger("andy.screen")
PAGES = Path(__file__).parent / "pages"
CAPTION_FOR_S = 180.0      # long enough for a story's part to be read along to the end
# Andy's last spoken words, for the screen's captions. Memory only: never written to disk or logged.
_caption: Dict[str, Any] = {"text": "", "at": 0.0}


def set_caption(text: str, now: Optional[float] = None) -> None:
    import time as _t
    _caption["text"] = " ".join(str(text).split())[:2000]
    _caption["at"] = now if now is not None else _t.time()


FONTS = {f"/fonts/atkinson-hyperlegible-{w}.woff2": f"fonts/atkinson-hyperlegible-{w}.woff2" for w in (400, 700)}

# What Andy looked at when it searched for something ("where are my glasses?"), for the screen: up to four
# small views in the order Andy turned, which one it chose, and which ones the model said it saw the thing
# in. Memory only, for FRAME_FOR_S, then forgotten; never written to disk or logged. Posted by Andy's own
# process on this computer (finder.post_views).
FRAME_FOR_S = 120
MAX_VIEWS = 4
MAX_VIEW = 400_000                          # a 480 px view at quality 70 is about 30 KB
MAX_VIEWS_BODY = MAX_VIEWS * (MAX_VIEW * 4 // 3 + 8) + 1024
_views: Dict[str, Any] = {"jpegs": [], "seen": [], "chosen": None, "at": 0.0}


def set_views(jpegs: List[Optional[bytes]], seen: List[bool], chosen: Optional[int], now: Optional[float] = None) -> None:
    """Keep one search's views. A view may be None (the camera gave no picture at that stop)."""
    import time as _t

    jpegs, seen = list(jpegs), list(seen)
    if not 0 < len(jpegs) <= MAX_VIEWS or len(seen) != len(jpegs):
        raise ValueError("bad views")
    for j in jpegs:
        if j is not None and not (isinstance(j, (bytes, bytearray)) and 0 < len(j) <= MAX_VIEW and bytes(j).startswith(b"\xff\xd8")):
            raise ValueError("not a picture")
    if not all(isinstance(s, bool) for s in seen):
        raise ValueError("bad views")
    if chosen is not None and (isinstance(chosen, bool) or not isinstance(chosen, int) or not 0 <= chosen < len(jpegs)
                               or jpegs[chosen] is None or not seen[chosen]):
        raise ValueError("bad choice")
    _views.update(jpegs=[None if j is None else bytes(j) for j in jpegs], seen=seen, chosen=chosen,
                  at=now if now is not None else _t.time())


def forget_views() -> None:
    _views.update(jpegs=[], seen=[], chosen=None, at=0.0)


def _fresh_views(now: Optional[float]) -> bool:
    import time as _t

    if not _views["jpegs"]:
        return False
    if (now if now is not None else _t.time()) - _views["at"] > FRAME_FOR_S:
        forget_views()                     # gone from memory, not only from the screen
        return False
    return True


def views(now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """What the TV needs to lay out the strip (no pictures): None once the two minutes are up."""
    if not _fresh_views(now):
        return None
    return {"at": _views["at"], "pictures": [j is not None for j in _views["jpegs"]], "seen": list(_views["seen"]),
            "chosen": _views["chosen"]}


def view(i: int, now: Optional[float] = None) -> bytes:
    if not _fresh_views(now) or not 0 <= i < len(_views["jpegs"]):
        return b""
    return _views["jpegs"][i] or b""


def caption(now: Optional[float] = None) -> str:
    import time as _t
    return _caption["text"] if (now if now is not None else _t.time()) - _caption["at"] <= CAPTION_FOR_S else ""


# Andy's recent turns as numbers and tool names only (turns.py), for /hood. Memory only.
_turns: "deque[Dict[str, Any]]" = deque(maxlen=40)


# What Andy is doing right now (live.py), refreshed several times a second. Memory only.
_live: Dict[str, Any] = {"state": "", "tool": "", "looking": "", "at": 0.0}
LIVE_STALE_S = 12.0


def set_live(data: Dict[str, Any], now: Optional[float] = None) -> None:
    import time as _t
    from andy_companion import live
    from andy_companion.turns import TOOL_NAME

    from andy_companion.body.looking_at import TARGETS

    state = str(data.get("state", "")) if isinstance(data, dict) else ""
    tool = str(data.get("tool", "")) if isinstance(data, dict) else ""
    looking = str(data.get("looking", "") or "") if isinstance(data, dict) else ""
    if state not in live.STATES or (tool and not TOOL_NAME.match(tool)) or (looking and looking not in TARGETS):
        raise ValueError("bad state")
    _live.update(state=state, tool=tool, looking=looking, at=now if now is not None else _t.time())


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
    looking = _live.get("looking", "") if key not in ("quiet", "asleep", "away") else ""
    return {"state": key, "tool": tool, "stage": stage, "label": words.state_label(key, tool, language, until),
            "looking": looking}


# This month's Tavily credits, as numbers (turns.tavily_usage_loop). Memory only.
_tavily: Dict[str, Any] = {}


def set_tavily(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("bad usage")
    by = data.get("by") if isinstance(data.get("by"), dict) else {}
    clean = {"plan": " ".join(str(data.get("plan", "")).split())[:40], "used": _ms(data.get("used")),
             "limit": _ms(data.get("limit")), "paygo": _ms(data.get("paygo")),
             "by": {k: _ms(by.get(k)) or 0 for k in ("search", "extract", "crawl", "map", "research")}}
    _tavily.clear()
    _tavily.update(clean)
    return clean


# Times the person talked over Andy and it stopped: how much of its reply was cut. Memory only.
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
    if data.get("eyes") in EYES_NAMES:
        _eyes["used"] = data["eyes"]
    _turns.append(turn)
    _count(turn)
    return turn


# Since Andy started (this process): counts only, for the hood's tally line. Memory only; the recent turns
# above keep 40, these keep counting.
_tally: Dict[str, int] = {"turns": 0, "nebius": 0, "tavily": 0, "eyes": 0}
# Which eyes answered Andy's last look, as its turn said (decision 0015): the hood names them, so Cosmos on this
# computer answering for Token Factory is never passed off as Token Factory. One of three names, nothing else.
EYES_NAMES = ("token-factory", "endpoint", "local")
_eyes: Dict[str, str] = {"used": ""}


def _count(turn: Dict[str, Any]) -> None:
    from andy_companion.turns import EYES, ON_NEBIUS, ON_TAVILY

    _tally["turns"] += 1
    for t in turn["tools"]:
        _tally["nebius"] += t["name"] in ON_NEBIUS
        _tally["tavily"] += t["name"] in ON_TAVILY
        _tally["eyes"] += t["name"] in EYES


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


# Model ids as people read them; an id not listed is shown with its dashes as spaces.
MODEL_NAMES = {"Nemotron-3-Ultra-550b-a55b": "Nemotron 3 Ultra", "Nemotron-3_5-Lightning": "Nemotron 3.5 Lightning"}


def model_name(model_id: Any) -> str:
    short = str(model_id or "").split("/")[-1]
    return MODEL_NAMES.get(short, short.replace("-", " ").replace("_", "."))


def _on_nebius(card: Dict[str, Any]) -> bool:
    return "Nebius" in str(card.get("ran_on", ""))


def proof(results: Path = RESULTS) -> Optional[Dict[str, Any]]:
    """The newest conversation-suite scorecard that ran as a Nebius Serverless Job, as the README and the video
    say; the newest of any when none did (none in an installed app without evals/)."""
    cards: List[Dict[str, Any]] = []
    for path in sorted(results.glob("*.json")) if results.is_dir() else []:
        try:
            card = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if not isinstance(card, dict) or "per_run" not in card or "ran" not in card:
            continue
        try:
            _when(card)
        except (ValueError, TypeError):
            continue
        cards.append(card)
    pool = [c for c in cards if _on_nebius(c)] or cards
    if not pool:
        return None
    best = max(pool, key=_when)
    return {"suite": best.get("suite"), "per_run": best.get("per_run"), "total": best.get("total"),
            "judge": model_name(best.get("judge")), "ran": _when(best).astimezone().strftime("%Y-%m-%d"),
            "ran_on": best.get("ran_on", "this computer")}


# In the public demo there is no robot or voice server, which is not a fault: amber "does not answer" tiles made the
# demo look broken (2026-10-28 design review), so there they read as not part of the demo, in grey.
NOT_IN_DEMO = {"Robot": "Not in this demo: no robot here", "Voice": "Not in this demo: no voice server here"}


def _health() -> List[Dict[str, str]]:
    from andy_companion import health

    tiles = health.tiles(float(_live["at"]), _weather["card"], _tavily)
    if INDEX is None:
        return tiles
    return [health.tile(t["name"], "off", NOT_IN_DEMO[t["name"]]) if t.get("name") in NOT_IN_DEMO else t for t in tiles]


def _language() -> str:
    from andy_companion import settings

    try:
        return "es" if settings.get().get("language") == "es" else "en"
    except Exception:
        return "en"


def hood_state() -> Dict[str, Any]:
    from andy_companion import vision
    from andy_companion.turns import BESIDE, think_ms, where

    turns = list(_turns)
    plain = [t for t in turns if not [x for x in t["tools"] if x["name"] not in BESIDE]]
    language = _language()
    return {
        # Each turn with its split: Nemotron's part (the reply less the tools Andy waited for), computed here.
        "turns": [{**t, "think_ms": think_ms(t)} for t in reversed(turns[-8:])],
        "count": len(turns),
        # The demo of the screens (it has its own front page): its turns are samples, not this robot's.
        "sample": INDEX is not None,
        "language": language,
        "where": where(language, _eyes["used"]),
        "eyes": vision.choice(),
        "tally": dict(_tally),
        "proof": proof(),
        "tavily": dict(_tavily) or None,
        "health": _health(),
        # What Andy is doing with its head and why, as the TV says it (body.looking_at's names only).
        "noticed": live_state().get("looking", ""),
        "interruptions": {"count": len(_interrupts),
                          "last_cut_ms": _interrupts[-1]["cut_ms"] if _interrupts else None},
        "median": {"hearing_ms": _median([t["hearing_ms"] for t in turns]),
                   "reply_ms": _median([t["reply_ms"] for t in plain]),
                   "total_ms": _median([t["total_ms"] for t in plain])},
    }


MAX_BODY = 4096
MAX_SETUP_BODY = 16384          # the settings page: two lists of 20 sites of 200 characters fit (review)
HEADERS = {
    "Content-Security-Policy": ("default-src 'none'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; "
                                "font-src 'self'; connect-src 'self'; "
                                "img-src 'self' data:; media-src 'self'; base-uri 'none'; form-action 'self'; frame-ancestors 'none'"),
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
                            "alerts": [weather.short_alert(a) for a in found["alerts"][:1]], "source": "weather.gov"}
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
    pending = reminders.pending()
    items = [r for r in pending if datetime.fromtimestamp(r["due"]).date() == now.date()]
    plan = [{"time": datetime.fromtimestamp(r["due"]).strftime("%-I:%M %p").lower(), "what": r["text"],
             "done": r["due"] < now.timestamp(), "due": int(r["due"])} for r in items]
    # Nothing left today: tomorrow's first, so a reminder set this evening for the morning shows it was set
    # (2026-10-25: "every morning at eight" left the card saying "Nothing planned today").
    tomorrow = None
    if not any(p["due"] >= now.timestamp() for p in plan):
        nxt = sorted((r for r in pending if datetime.fromtimestamp(r["due"]).date() == (now + timedelta(days=1)).date()),
                     key=lambda r: r["due"])
        if nxt:
            tomorrow = {"time": datetime.fromtimestamp(nxt[0]["due"]).strftime("%-I:%M %p").lower(), "what": nxt[0]["text"],
                        "daily": nxt[0].get("repeat") == "daily"}
    from andy_companion import settings

    return {"today": clock.today(now, settings.get().get("language", "en")), "hour": now.hour, "plan": plan,
            "tomorrow": tomorrow}


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


LOOPBACK = re.compile(r"(localhost|127(\.\d{1,3}){3}|\[::1\])(:\d+)?", re.I)


def lan_host() -> str:
    """This computer's address on the home network, as `scripts/settings.py links` prints it."""
    import socket

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("192.0.2.1", 9))          # no packet is sent; this finds the local address
            return s.getsockname()[0]
    except OSError:
        return "localhost"


def qr_host(host: str) -> str:
    """Where the settings code should point: the address the screen was reached at, unless that is this
    computer's own loopback (a TV browser on this computer), which a phone can't reach: then the home network's."""
    if LOOPBACK.fullmatch(host):
        port = host.rsplit(":", 1)[1] if re.search(r":\d+$", host) else ""
        return lan_host() + (f":{port}" if port else "")
    return host if re.fullmatch(r"[A-Za-z0-9.\-]+(:\d+)?", host) else ""


def night_now(s: Dict[str, Any], hour: int) -> bool:
    """Whether the screen is the calm night clock: at the hours chosen, while Andy is asleep, or never."""
    mode = s.get("night_clock", "hours")
    if mode == "off":
        return False
    if mode == "asleep":
        from andy_companion import state as andy_state
        try:
            return andy_state.current()["mode"] == "asleep"
        except Exception:
            return False
    start, end = int(s.get("night_from", 21)), int(s.get("night_to", 7))
    return (start <= hour or hour < end) if start > end else (start <= hour < end)


def screen_state(now: Optional[datetime] = None, host: str = "") -> Dict[str, Any]:
    from andy_companion import settings

    state = today_plan(now)
    # The gear menu's way to the hood page: the hood has its own token, which the screen learns here.
    state["links"] = {"hood": f"/hood?t={board.tokens()['hood']}"}
    state["showing"] = board.showing()
    if state["showing"] and state["showing"].get("kind") == "code" and host:
        state["showing"] = {**state["showing"], "qr": settings_qr(host)}
    state["views"] = views_for(state["showing"])
    state["caption"] = caption() if settings.get().get("captions", True) else ""
    state["caption_at"] = _caption["at"] if state["caption"] else None
    import time as _t

    state["server_now"] = _t.time()        # the TV works out the caption's age from this, not its own clock
    # The page's version: when Andy's screen is updated, a TV left open reloads itself (no remote needed).
    state["page_version"] = int((PAGES / "screen.html").stat().st_mtime)
    state["weather"] = weather_card()
    hour = (now or datetime.now()).hour
    s = settings.get()
    state["night"] = night_now(s, hour)
    state["idle_photo"] = board.idle_photo() if s.get("screen_photos", True) and not state["night"] else None
    state["calm"] = bool(s.get("screen_calm", False))
    state["hints"] = bool(s.get("screen_hints", True))
    return state


def views_for(showing: Optional[Dict[str, Any]], now: Optional[float] = None) -> Optional[Dict[str, Any]]:
    """The views go with the card of the same search only: the finder posts them a moment before it puts the
    card up, so an older search's views never sit under a newer card."""
    v = views(now)
    if not v or not showing or showing.get("kind") not in VIEW_KINDS:
        return None
    return v if -5 <= float(showing.get("at", 0)) - v["at"] <= 60 else None


VIEW_KINDS = ("seen", "looked")


def family_state() -> Dict[str, Any]:
    """What family see: only what the person shared, with the household's language and the name the
    settings page gave (so the page can say "Hello" in Spanish, and "Rosa" rather than "they")."""
    from andy_companion import settings, words

    chosen = settings.get()
    lg = "es" if chosen.get("language") == "es" else "en"

    def when(at: float) -> str:
        dt = datetime.fromtimestamp(at)
        clock = dt.strftime("%H:%M") if lg == "es" else dt.strftime("%-I:%M %p").replace("AM", "am").replace("PM", "pm")
        return f"{words.date_shown(dt, lg, with_weekday=True)}, {clock}"

    return {"shared": [{"id": s["id"], "note": s["note"], "when": when(s["at"])} for s in reversed(board.shared())],
            "language": lg, "person_name": chosen.get("person_name") or None}


def setup_state() -> Dict[str, Any]:
    from andy_companion import setup_page

    t = board.tokens()
    from andy_companion import kept

    return {"settings": setup_page.state(), "kept": kept.summary(), "now": live_state(), "tavily": dict(_tavily) or None,
            "links": {"screen": f"/screen?t={t['screen']}", "family": f"/family?k={t['family']}",
                      "hood": f"/hood?t={t['hood']}"}}


# The kind page for a page link whose token no longer opens it. The token is never echoed back.
EXPIRED = {
    "/setup": {"en": ("Settings link replaced", "This settings link has been replaced.",
                      "Ask Andy: \u201cAndy, show the settings code\u201d, and point your phone's camera at the TV."),
               "es": ("Enlace de ajustes reemplazado", "Este enlace de ajustes ha sido reemplazado.",
                      "Pídale a Andy: «Andy, muestra el código de ajustes», y apunte la cámara de su teléfono a la televisión.")},
    "/family": {"en": ("Family link replaced", "This family link has been replaced.",
                       "Ask whoever set up Andy for the new one."),
                "es": ("Enlace familiar reemplazado", "Este enlace familiar ha sido reemplazado.",
                       "Pida el nuevo a quien configuró a Andy.")},
    "/screen": {"en": ("Screen link replaced", "This screen link has been replaced.",
                       "On the computer beside Andy, open the new screen link on this TV."),
                "es": ("Enlace de pantalla reemplazado", "Este enlace de pantalla ha sido reemplazado.",
                       "En el ordenador junto a Andy, abra el nuevo enlace de pantalla en esta televisión.")},
    "/hood": {"en": ("Link replaced", "This link has been replaced.",
                     "The gear on Andy's screen opens Under the hood."),
              "es": ("Enlace reemplazado", "Este enlace ha sido reemplazado.",
                     "El engranaje en la pantalla de Andy abre «Por dentro».")},
}


def expired_page(path: str, language: Optional[str] = None) -> bytes:
    import html

    lg = language if language in ("en", "es") else _language()
    title, head, line = EXPIRED[path][lg]
    page = (PAGES / "expired.html").read_text()
    for key, value in (("lang", lg), ("title", title), ("head", head), ("line", line)):
        page = page.replace("{{" + key + "}}", html.escape(value, quote=False))   # text, and lang in ""
    return page.encode()


def _replaced(path: str, q: Dict[str, str]) -> str:
    """The page ("/setup", "/family" or "/screen") whose API this address is, when its token does not open it; else
    ""."""
    for page, key, kind in (("/setup", "s", "setup"), ("/family", "k", "family"), ("/screen", "t", "screen")):
        if (path == "/api" + page or path.startswith("/api" + page + "/")) and not _ok(q.get(key), kind):
            return page
    return ""


def _ok(token: Optional[str], kind: str) -> bool:
    if not token:
        return False
    # Bytes, so a token with characters outside ASCII is simply wrong rather than an error.
    return hmac.compare_digest(token.encode("utf-8", "replace"), board.tokens()[kind].encode())


def _no_constant(name: str) -> None:
    raise ValueError("That is not a number.")


def _object(raw: bytes) -> dict:
    """A request body as a JSON object; anything else (a list, NaN, Infinity) is a ValueError, in plain words."""
    try:
        data = json.loads(raw or b"{}", parse_constant=_no_constant)
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise ValueError("Something went wrong; please try again.") from None
    if not isinstance(data, dict):
        raise ValueError("Something went wrong; please try again.")
    return data


# The public demo of the screens (scripts/demo_screen.py --public, PLAN B26): every page opens on sample data,
# and nothing a visitor sends is taken, so nothing one visitor types can reach another. Never set on a robot.
READ_ONLY = False
READ_ONLY_ERROR = "This is a public demo with sample data: nothing you send is kept or shown to anyone."
# The demo's own front page at "/", listing the four pages; Andy's real server has none.
INDEX: Optional[bytes] = None
# Files the demo's front page shows (scripts/demo_screen.py: the simulated search's film), by path; empty on the robot.
MEDIA: Dict[str, Tuple[bytes, str]] = {}


# Andy's pages are for the home: the TV, the family's phones on its Wi-Fi, a helper beside the robot. They are served
# on the home network over plain HTTP behind long per-page tokens, and a visitor from anywhere else is refused, so a
# computer with a public address (a cloud machine) never serves them to the internet (2026-10-25 review). 100.64/10 is
# allowed too: a home VPN such as Tailscale gives its devices those addresses.
_HOME_RANGES = (ipaddress.ip_network("100.64.0.0/10"),)


def home_network(host: str) -> bool:
    """Whether a client's address is this computer, the home network, or a home VPN."""
    try:
        ip = ipaddress.ip_address(host.split("%", 1)[0])
    except ValueError:
        return False
    if getattr(ip, "ipv4_mapped", None):
        ip = ip.ipv4_mapped
    return ip.is_loopback or ip.is_private or ip.is_link_local or any(ip in net for net in _HOME_RANGES)


# What family send (messages, photos, suggestions, "looked"): at most FAMILY_PER_MINUTE a minute, so the link can't
# flood Andy's inbox or disk (2026-10-25 review). In memory only.
FAMILY_PER_MINUTE = 20
_family_sends: "deque[float]" = deque(maxlen=FAMILY_PER_MINUTE)
_family_lock = threading.Lock()


def family_allowed(now: Optional[float] = None) -> bool:
    import time as _t

    now = _t.monotonic() if now is None else now
    with _family_lock:
        if len(_family_sends) == FAMILY_PER_MINUTE and now - _family_sends[0] < 60:
            return False
        _family_sends.append(now)
        return True


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
        body = (PAGES / name).read_bytes()
        # The household's language in the page itself: the TV's Spanish menu opens the hood, and the family page asks
        # for a name in it on a first visit, before anything is asked of Andy (2026-10-28 review: it asked in English).
        if name in ("hood.html", "family.html", "setup.html") and _language() == "es":
            body = body.replace(b'<html lang="en">', b'<html lang="es">', 1)
        self._send(200, body, "text/html; charset=utf-8")

    def _expired(self, path: str) -> None:
        """A page link that no longer opens (replaced, or mistyped): a kind page saying what to do, still a 404."""
        self._send(404, expired_page(path), "text/html; charset=utf-8")

    def _error(self, reason: str, code: int) -> None:
        """Why the settings or family page's request can't be done, in the household's language (words.problem)."""
        from andy_companion import words

        self._json({"error": words.problem(reason, _language())}, code)

    def _gone(self, page: str) -> None:
        """A page already open when its link was replaced asks with the old token: 410 and the kind page's words, in
        the household's language, for the page to show. A plain 404 read "Andy's computer did not answer. Is it on?"
        on the settings page (2026-10-28 review). The token is never echoed."""
        _, head, line = EXPIRED[page][_language()]
        self._json({"error": f"{head} {line}", "gone": True}, 410)

    def do_GET(self) -> None:  # noqa: N802
        self._guarded(self._get)

    def do_POST(self) -> None:  # noqa: N802
        self._guarded(self._post)

    def _guarded(self, route: Callable[[], None]) -> None:
        """Only the home network (the public demo excepted), and an error answers 500 with nothing in the log but
        its kind: never the address or the body, which hold tokens and words."""
        if not READ_ONLY and not home_network(str(self.client_address[0])):
            return self._send(403, b"Andy's pages open only on the home network.", "text/plain; charset=utf-8")
        try:
            route()
        except (BrokenPipeError, ConnectionResetError, TimeoutError):
            return                       # the visitor went away, or stalled past the timeout
        except Exception as e:
            logger.warning("screen request failed: %s", type(e).__name__)
            with contextlib.suppress(Exception):
                self._send(500, b"Something went wrong; please try again.", "text/plain; charset=utf-8")

    def _get(self) -> None:
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if url.path == "/" and INDEX is not None:
            return self._send(200, INDEX, "text/html; charset=utf-8")
        if url.path in MEDIA:
            body, kind = MEDIA[url.path]
            return self._send(200, body, kind)
        if url.path == "/screen" and _ok(q.get("t"), "screen"):
            return self._page("screen.html")
        if url.path == "/api/screen" and _ok(q.get("t"), "screen"):
            # The settings code points at this same address, as the screen reached it on the home network.
            return self._json(screen_state(host=qr_host(self.headers.get("Host", ""))))
        if url.path == "/api/state" and (_ok(q.get("t"), "screen") or _ok(q.get("t"), "hood")):
            return self._json(live_state())      # the state strip, on both pages: a label, nothing private
        # The hood takes only its own token: its link is the one shown to the curious, so it must not open
        # the screen's captions and reminders, or the settings code (review, 2026-10-14).
        if url.path == "/hood" and _ok(q.get("t"), "hood"):
            return self._page("hood.html")
        if url.path == "/api/hood" and _ok(q.get("t"), "hood"):
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
        if url.path in EXPIRED:
            return self._expired(url.path)
        if _replaced(url.path, q):              # the settings or family page's questions, with a token that failed
            return self._gone(_replaced(url.path, q))
        if url.path == "/view" and _ok(q.get("t"), "screen"):
            try:
                data = view(int(q.get("i", "")))
            except ValueError:
                data = b""
            if data:
                return self._send(200, data, "image/jpeg")
            return self._send(404, b"Not found", "text/plain")
        if url.path == "/photo" and _ok(q.get("t"), "screen"):
            path = board.photo_path(q.get("id", ""))
            if path is not None:
                return self._send(200, path.read_bytes(), "image/jpeg")
        return self._send(404, b"Not found", "text/plain")

    def _post(self) -> None:
        url = urlparse(self.path)
        q = {k: v[0] for k, v in parse_qs(url.query).items()}
        if READ_ONLY:
            # Opening the family page is let through so a visitor sees the sample notes, but the name is never
            # read or kept: "Anna looked" would show one visitor's words to the next.
            if url.path == "/api/family/look" and _ok(q.get("k"), "family"):
                return self._json({"ok": True})
            return self._error(READ_ONLY_ERROR, 403)
        local = self.client_address[0] in ("127.0.0.1", "::1")
        if url.path == "/api/transient" and _ok(q.get("t"), "screen") and local:
            length = self._length()
            if not 0 < length <= 16384:
                return self._json({"error": "too long"}, 413)
            try:
                data = _object(self.rfile.read(length))
                value = board.transient_action(str(data.get("action", "")), data.get("data"))
            except (ValueError, TypeError, OverflowError):
                return self._json({"error": "bad request"}, 400)
            return self._json({"value": value})
        if url.path == "/api/screen/settings-code" and _ok(q.get("t"), "screen"):
            # The gear on the TV: the QR code appears, for two minutes. Each new code retires the settings
            # link, so a code already up stays: pressing again can't keep cancelling a helper's link.
            showing = board.showing()
            if not (showing and showing.get("kind") == "code"):
                board.show_settings_code()
                board.code_shown()
            return self._json({"ok": True})
        if url.path == "/api/views" and _ok(q.get("t"), "screen") and local:
            length = self._length()
            if not 0 < length <= MAX_VIEWS_BODY:
                return self._json({"error": "too long"}, 413)
            try:
                data = _object(self.rfile.read(length))
                pictures = data.get("views")
                if not isinstance(pictures, list) or len(pictures) > MAX_VIEWS:
                    raise ValueError("bad views")
                set_views([None if p is None else base64.b64decode(str(p), validate=True) for p in pictures],
                          data.get("seen") or [], data.get("chosen"))
            except (ValueError, TypeError, AttributeError, binascii.Error):
                return self._json({"error": "bad request"}, 400)
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
            if not 0 <= length <= MAX_SETUP_BODY:
                return self._error("That is too long.", 413)
            try:
                data = _object(self.rfile.read(length))
                if not isinstance(data, dict):
                    raise ValueError("Something went wrong; please try again.")
                from andy_companion import setup_page

                if url.path == "/api/setup":
                    changed = setup_page.apply(data.get("name", ""), data.get("settings", {}))
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
                return self._error(str(e), 400)
            except (TypeError, AttributeError, OverflowError):
                return self._error("Something went wrong; please try again.", 400)
            return self._send(404, b"Not found", "text/plain")
        if _replaced(url.path, q):
            return self._gone(_replaced(url.path, q))
        if url.path.startswith("/api/family/") and _ok(q.get("k"), "family") and not family_allowed():
            return self._error("That's a lot at once; please wait a minute and try again.", 429)
        if not url.path.startswith("/api/family/") or not _ok(q.get("k"), "family"):
            return self._send(404, b"Not found", "text/plain")
        length = self._length()
        limit = board.MAX_PHOTO_BYTES * 4 // 3 + MAX_BODY if url.path == "/api/family/photo" else MAX_BODY
        if not 0 <= length <= limit:
            return self._error("That is too long.", 413)
        try:
            data = _object(self.rfile.read(length))
            if url.path == "/api/family/look":
                board.looked(data.get("name", ""))
                return self._json({"ok": True})
            if url.path == "/api/family/photo":
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
            if url.path == "/api/family/suggest":
                # A reminder family suggest: Andy asks the person, and sets it only after their yes. The answer
                # is never sent back to the family (that would report on the person).
                board.suggestion_from_page(data.get("name", ""), data.get("what", ""), data.get("when"))
                return self._json({"ok": True})
        except ValueError as e:
            return self._error(str(e), 400)
        except (TypeError, AttributeError, OverflowError):
            return self._error("Something went wrong; please try again.", 400)
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
            views()                         # what Andy looked at is forgotten after two minutes, TV or not
        except Exception:
            logger.debug("screen housekeeping failed", exc_info=True)
        _t.sleep(every_s)


def serve(host: Optional[str] = None, port: Optional[int] = None) -> ThreadingHTTPServer:
    from andy_companion import transient

    host = host if host is not None else os.environ.get("ANDY_SCREEN_HOST", "0.0.0.0")
    port = port if port is not None else int(os.environ.get("ANDY_SCREEN_PORT", "8090"))
    httpd = ThreadingHTTPServer((host, port), Handler)
    transient.owner = True
    board.purge_legacy_transients()
    # A short poll, so stopping the server (tests, the demo) takes a twentieth of a second, not half of one.
    threading.Thread(target=lambda: httpd.serve_forever(poll_interval=0.05), name="andy-screen", daemon=True).start()
    threading.Thread(target=_housekeeping, name="andy-screen-tidy", daemon=True).start()
    logger.info("Andy's screen is served on port %d", port)
    return httpd
