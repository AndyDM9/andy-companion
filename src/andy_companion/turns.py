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
