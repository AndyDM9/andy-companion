"""Under the hood: how long each part of a spoken turn took, shown at /hood on the screen server.

Numbers and tool names only, never words or tool arguments. Each finished turn is sent to the
screen server on this computer, which keeps the last few in memory; nothing is written to disk
or logged.

A turn, as Pollen's conversation app reports it (`_mark_activity`):
- `user_speech_stopped`: the voice server's turn detection decided the person finished;
- `user_transcription_completed`: Parakeet's words arrived;
- `assistant_audio_delta`: the first sound of Andy's reply arrived;
- `assistant_transcript_done`: Andy's reply finished; the turn is sent.
Tools run between those (`ToolCallRoutine`), each timed by name.
"""

from __future__ import annotations

import json
import os
import re
import threading
import time
import urllib.request
from functools import wraps
from typing import Any, Callable, Dict, List, Optional

SCREEN = f"http://127.0.0.1:{os.environ.get('ANDY_SCREEN_PORT', '8090')}"
TOOL_NAME = re.compile(r"^[a-z][a-z0-9_]{0,39}$")

# Where each of Andy's tools runs, for the hood page: every tool in evals/tools.json (tests check it), in
# English and Spanish. A tool that reaches the network names the service; the rest run on this computer.
HERE = {"en": "on this computer", "es": "en esta computadora"}
WHERE: Dict[str, Dict[str, str]] = {
    "local_news": {"en": "Tavily search", "es": "búsqueda de Tavily"},
    "look_up": {"en": "Tavily search", "es": "búsqueda de Tavily"},
    "whats_on": {"en": "Tavily crawl of the town's events page, or search",
                 "es": "Tavily recorre la página de eventos del pueblo, o busca"},
    "read_link": {"en": "Tavily extract", "es": "Tavily extract (lee la página)"},
    "check_message": {"en": "Tavily (advanced) + Nemotron Lightning and Ultra, Token Factory",
                      "es": "Tavily (avanzada) + Nemotron Lightning y Ultra, Token Factory"},
    "look_into": {"en": "Tavily research, started now, answered later",
                  "es": "investigación de Tavily, empieza ahora, responde después"},
    "read_letter": {"en": "read on this computer + Nemotron Lightning card",
                    "es": "leída en esta computadora + tarjeta de Nemotron Lightning"},
    "on_this_day": {"en": "Wikipedia + Nemotron Lightning, Token Factory",
                    "es": "Wikipedia + Nemotron Lightning, Token Factory"},
    "think_it_through": {"en": "Nemotron 3 Ultra on Token Factory", "es": "Nemotron 3 Ultra en Token Factory"},
    "describe_view": {"en": "Nemotron 3.5 Super VL, Token Factory", "es": "Nemotron 3.5 Super VL, Token Factory"},
    "describe_photo": {"en": "Nemotron 3.5 Super VL, Token Factory", "es": "Nemotron 3.5 Super VL, Token Factory"},
    "find_object": {"en": "Nemotron 3.5 Super VL, Token Factory, four views at once, zoomed in, then a closer look",
                    "es": "Nemotron 3.5 Super VL, Token Factory, cuatro vistas a la vez, ampliadas, y una mirada más de cerca"},
    "weather": {"en": "National Weather Service (weather.gov)", "es": "Servicio Meteorológico Nacional (weather.gov)"},
    "content_safety": {"en": "Nemotron 3.5 Content Safety on Nebius, beside the reply",
                       "es": "Nemotron 3.5 Content Safety en Nebius, junto a la respuesta"},
}
LOCAL = ("head_tracking", "idle_do_nothing", "go_to_sleep", "remember", "forget", "get_today", "set_reminder",
         "list_reminders", "cancel_reminder", "quiet_for", "day_plan", "set_pace", "set_volume", "share_with_family",
         "remember_moment", "forget_moment", "what_you_remember", "captions", "set_language", "settings_code",
         "tell_joke", "story", "task_status")
WHERE.update({name: dict(HERE) for name in LOCAL})
# For the hood's tally: the tools that call a Nebius service (Token Factory or a Serverless Endpoint), Tavily,
# or the eyes. The conversation itself is on Token Factory every turn and is counted as turns.
ON_NEBIUS = frozenset({"check_message", "read_letter", "on_this_day", "think_it_through",
                       "describe_view", "describe_photo", "find_object"})
ON_TAVILY = frozenset({"local_news", "look_up", "whats_on", "read_link", "check_message", "look_into"})
EYES = frozenset({"describe_view", "describe_photo", "find_object"})
# Runs beside the reply rather than before it (guard.py), so it is not part of the wait for the first sound.
BESIDE = frozenset({"content_safety"})


def think_ms(turn: Dict[str, Any]) -> Optional[int]:
    """The reply's time less the tools Andy waited for: Nemotron 3.5 Lightning's calls and the voice starting."""
    reply = turn.get("reply_ms")
    if reply is None:
        return None
    waited = sum(t.get("ms") or 0 for t in turn.get("tools") or [] if t.get("name") not in BESIDE)
    return max(0, reply - waited)


# The eyes when ANDY_VISION chooses the person's own endpoint instead of Token Factory (vision.eyes).
ON_ENDPOINT = {"describe_view": {"en": "Nemotron Nano VL on our Nebius endpoint", "es": "Nemotron Nano VL en nuestro endpoint de Nebius"},
               "describe_photo": {"en": "Nemotron Nano VL on our Nebius endpoint", "es": "Nemotron Nano VL en nuestro endpoint de Nebius"},
               "find_object": {"en": "Nemotron Nano VL on our Nebius endpoint, four views at once, zoomed in, then a closer look",
                               "es": "Nemotron Nano VL en nuestro endpoint de Nebius, cuatro vistas a la vez, ampliadas, y una mirada más de cerca"}}


def where(language: str = "en") -> Dict[str, str]:
    """Each tool's place, in the household's language, with the eyes ANDY_VISION chose."""
    from andy_companion import vision

    lg = "es" if language == "es" else "en"
    places = {**WHERE, **(ON_ENDPOINT if vision.choice() == "endpoint" else {})}
    return {name: w[lg] for name, w in places.items()}


class TurnClock:
    """Turns one conversation's activity marks into finished turns of numbers."""

    def __init__(self, clock: Callable[[], float] = time.perf_counter, wall: Callable[[], float] = time.time):
        self.clock, self.wall = clock, wall
        self.last_voice = clock()          # the person last spoke (or Andy started), for quiet_for
        self.unanswered_since: Optional[float] = None   # first speech since Andy last answered
        self._reset()

    running: int = 0                     # tools running now, whatever the turn
    current_tool: str = ""               # the newest of them, by name, for the screen's state strip
    hearing: bool = False                # the person is speaking right now

    def thinking(self, longest_s: float = 20.0) -> bool:
        """Andy is working on an answer: words understood and no sound yet, or a tool running."""
        if self.running > 0:
            return True
        return self.heard is not None and self.first_sound is None and self.clock() - self.heard < longest_s

    def unanswered_for(self) -> Optional[float]:
        """Seconds the person has been heard with no answer from Andy (watchdog), or None."""
        if self.unanswered_since is None or self.clock() - self.last_voice > 30.0:
            return None                    # nobody has spoken for a while: nothing waiting
        return self.clock() - self.unanswered_since

    def quiet_for(self) -> float:
        """Seconds since the person last spoke to Andy (or since Andy started)."""
        return self.clock() - self.last_voice

    def _reset(self) -> None:
        self.stopped: Optional[float] = None
        self.heard: Optional[float] = None
        self.first_sound: Optional[float] = None
        self.tools: List[Dict[str, Any]] = []

    def tool(self, name: str, seconds: float) -> None:
        if self.heard is not None and TOOL_NAME.match(str(name)):
            self.tools.append({"name": name, "ms": round(seconds * 1000)})

    def mark(self, reason: str) -> Optional[Dict[str, Any]]:
        """Note one activity; returns the finished turn when Andy's reply ends."""
        now = self.clock()
        if reason == "user_speech_started":
            self.hearing = True
            self.last_voice = now
            if self.unanswered_since is None:
                self.unanswered_since = now
            self._reset()
        elif reason == "user_speech_stopped":
            self.hearing = False
            self._reset()
            self.stopped = now
        elif reason == "user_transcription_completed":
            self.hearing = False
            self.heard = now
            self.first_sound = None
            self.tools = []
        elif reason == "assistant_audio_delta":
            self.unanswered_since = None       # Andy is answering
            if self.heard is not None and self.first_sound is None:
                self.first_sound = now
        elif reason == "assistant_transcript_done":
            if self.heard is None or self.first_sound is None:
                return None
            turn = {
                "at": round(self.wall()),
                "hearing_ms": round((self.heard - self.stopped) * 1000) if self.stopped is not None else None,
                "reply_ms": round((self.first_sound - self.heard) * 1000),
                "total_ms": round((self.first_sound - (self.stopped if self.stopped is not None else self.heard)) * 1000),
                "tools": self.tools[:6],
            }
            self._reset()
            return turn
        return None


CLOCK = TurnClock()


def send(turn: Dict[str, Any], opener=None) -> None:
    from andy_companion import board

    req = urllib.request.Request(f"{SCREEN}/api/turn?t={board.tokens()['screen']}", method="POST",
                                 data=json.dumps(turn).encode(), headers={"Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=1):
            pass
    except Exception:
        pass   # the timings are a window for the curious, never a reason to stop


def tavily_usage_loop(every_s: float = 600.0, rounds: Optional[int] = None, sleep=time.sleep) -> None:
    """Every ten minutes, send this month's Tavily credits to the hood page (numbers only)."""
    from andy_companion import web

    done = 0
    while rounds is None or done < rounds:
        try:
            send({"tavily": web.usage()})
        except Exception:
            pass   # the page keeps the last numbers
        done += 1
        if rounds is None or done < rounds:
            sleep(every_s)


def interrupted(seconds_left: float) -> None:
    """The person talked over Andy and his voice stopped; tell the hood page how much was cut."""
    threading.Thread(target=send, args=({"interrupt_ms": round(seconds_left * 1000)},), daemon=True).start()


def install(handler_class=None, routine_class=None, clock: Optional[TurnClock] = None) -> bool:
    clock = clock or CLOCK
    if handler_class is None:
        from reachy_mini_conversation_app.conversation_handler import ConversationHandler

        handler_class = ConversationHandler
    if routine_class is None:
        from reachy_mini_conversation_app.tools.background_tool_manager import ToolCallRoutine

        routine_class = ToolCallRoutine
    previous = handler_class._mark_activity
    if getattr(previous, "_andy_turns", False):
        return False

    @wraps(previous)
    def mark(self, reason: str) -> None:
        previous(self, reason)
        try:
            turn = clock.mark(reason)
        except Exception:
            return
        if turn is not None:
            threading.Thread(target=send, args=(turn,), daemon=True).start()

    mark._andy_turns = True
    handler_class._mark_activity = mark

    run = routine_class.__call__

    @wraps(run)
    async def timed(self, *args, **kwargs):
        started = time.perf_counter()
        clock.running += 1
        clock.current_tool = str(getattr(self, "tool_name", ""))
        try:
            return await run(self, *args, **kwargs)
        finally:
            clock.running = max(0, clock.running - 1)
            clock.tool(getattr(self, "tool_name", ""), time.perf_counter() - started)

    routine_class.__call__ = timed
    return True
