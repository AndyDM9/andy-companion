"""Keep Andy answering: notice the ways it stopped on 2026-10-13, recover, and say so in the log.

- **The microphone dropping audio.** When the robot's audio pipeline falls behind (the desktop busy with
  other work), GStreamer warns "Can't record audio fast enough" and every transcript afterwards comes
  back empty, so Andy hears nothing it can answer. The pipeline doesn't recover by itself. With
  DROPS_PER_MIN or more such warnings in a minute, the app asks the supervisor for a restart
  (a marker file with the reason) and stops itself; the supervisor starts it again.
- **Speech without an answer.** If people keep talking near Andy (a TV, a radio) for UNANSWERED_S with
  no reply from Andy, that is logged once, with the likely cause. A restart wouldn't help, so none is
  made; the voice server's turn cap (voice/serve.py) keeps one turn from growing for ever.

`health.json` holds counts and times only (never words): drops in the last minute, seconds since Andy
last answered, restarts asked for. The health check (scripts/health.py) reads it. ANDY_WATCHDOG=off
turns the restart off; the counting and the health file stay.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import tempfile
import threading
import time
from collections import deque
from typing import Callable, Optional

from andy_companion.reminders import DATA_DIR

logger = logging.getLogger("andy.watchdog")

RESTART = os.environ.get("ANDY_WATCHDOG", "on").strip().lower() not in ("off", "0", "false", "no")
DROPS_PER_MIN = 20
GRACE_S = 60.0                    # no restart in the first minute after start
UNANSWERED_S = 120.0
CHECK_S = 5.0
REQUEST = DATA_DIR / "restart-request"
HEALTH = DATA_DIR / "health.json"
DROP_TEXT = "record audio fast enough"
AUDIO_LOGGER = "reachy_mini.media.audio_gstreamer"


class DropCounter(logging.Handler):
    """Counts the audio pipeline's 'can't keep up' warnings; keeps their times only."""

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        super().__init__(level=logging.WARNING)
        self.clock = clock
        self.times: deque = deque(maxlen=1000)

    def emit(self, record: logging.LogRecord) -> None:
        try:
            if DROP_TEXT in record.getMessage():
                self.times.append(self.clock())
        except Exception:
            pass

    def last_minute(self, now: Optional[float] = None) -> int:
        now = self.clock() if now is None else now
        return sum(1 for t in self.times if now - t <= 60.0)


def _write(path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    fd, tmp = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
    with os.fdopen(fd, "w") as f:
        f.write(data if isinstance(data, str) else json.dumps(data))
    os.chmod(tmp, 0o600)
    os.replace(tmp, path)


def take_request() -> Optional[str]:
    """The supervisor's side: why a restart was asked for (and clear it), or None."""
    try:
        reason = REQUEST.read_text().strip()
    except OSError:
        return None
    REQUEST.unlink(missing_ok=True)
    return reason or "asked by the app"


class Watchdog:
    def __init__(self, counter: DropCounter, clock: Callable[[], float] = time.monotonic,
                 stop: Optional[Callable[[], None]] = None) -> None:
        self.counter, self.clock = counter, clock
        self.started = clock()
        self.stop = stop or (lambda: os.kill(os.getpid(), signal.SIGINT))   # Pollen's app stops cleanly on Ctrl+C
        self.asked = 0
        self.warned_unanswered = -1e9

    def check(self, now: Optional[float] = None) -> Optional[str]:
        """One look; returns 'restart' or 'unanswered' when it acts."""
        from andy_companion import turns

        now = self.clock() if now is None else now
        drops = self.counter.last_minute(now)
        unanswered = turns.CLOCK.unanswered_for()
        try:
            _write(HEALTH, {"at": round(time.time()), "drops_last_min": drops,
                            "unanswered_s": round(unanswered) if unanswered is not None else None,
                            "restarts_asked": self.asked})
        except OSError:
            pass
        if drops >= DROPS_PER_MIN and now - self.started >= GRACE_S and RESTART and not self.asked:
            self.asked += 1
            reason = f"the microphone dropped audio {drops} times in a minute"
            logger.warning("Restarting Andy's app: %s", reason)
            _write(REQUEST, reason)
            self.stop()
            return "restart"
        if unanswered is not None and unanswered >= UNANSWERED_S and now - self.warned_unanswered >= 300:
            self.warned_unanswered = now
            logger.warning("Andy has heard speech for %.0f s without answering: a TV or radio nearby?", unanswered)
            return "unanswered"
        return None


def install() -> Watchdog:
    counter = DropCounter()
    logging.getLogger(AUDIO_LOGGER).addHandler(counter)
    dog = Watchdog(counter)

    def loop() -> None:
        while True:
            time.sleep(CHECK_S)
            try:
                if dog.check() == "restart":
                    return
            except Exception:
                logger.debug("watchdog check failed", exc_info=True)

    threading.Thread(target=loop, name="andy-watchdog", daemon=True).start()
    return dog
