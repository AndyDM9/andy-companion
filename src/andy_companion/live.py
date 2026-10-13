"""What Andy is doing right now, for the screen's state strip and the hood page's pipeline.

States, worked out from the same marks that time each turn (turns.TurnClock) and from whether
Andy's voice is still playing (body.speaking):
- ready: listening for you (the microphones are open, nothing is being said);
- hearing: you are speaking;
- thinking: your words are understood, no answer yet;
- working: a tool is running (its name only, so the screen can say "Looking that up");
- speaking: Andy's voice is playing.
Quiet and asleep come from the supervisor's state file on the screen server's side. Only the state
and a tool name ever leave this process; never words.
"""

from __future__ import annotations

import threading
import time
from typing import Callable, Dict, Optional

STATES = ("ready", "hearing", "thinking", "working", "speaking")
TICK_S = 0.15
HEARTBEAT_S = 5.0


def derive(clock, speaking_now: bool) -> Dict[str, str]:
    if speaking_now:
        return {"state": "speaking", "tool": ""}
    if clock.running > 0:
        return {"state": "working", "tool": clock.current_tool or ""}
    if clock.thinking():
        return {"state": "thinking", "tool": ""}
    if clock.hearing:
        return {"state": "hearing", "tool": ""}
    return {"state": "ready", "tool": ""}


def report_loop(send: Optional[Callable[[Dict], None]] = None, rounds: Optional[int] = None,
                sleep: Callable[[float], None] = time.sleep, now: Callable[[], float] = time.monotonic) -> None:
    """Send the state when it changes, and every few seconds so the screen knows Andy is alive."""
    from andy_companion import turns
    from andy_companion.body import speaking

    send = send or turns.send
    last: Optional[Dict[str, str]] = None
    sent_at = -1e9
    done = 0
    while rounds is None or done < rounds:
        try:
            state = derive(turns.CLOCK, speaking.speaking())
            if state != last or now() - sent_at >= HEARTBEAT_S:
                threading.Thread(target=send, args=({"live": state},), daemon=True).start()
                last, sent_at = state, now()
        except Exception:
            pass   # the strip is a help, never a reason to stop
        done += 1
        sleep(TICK_S)
