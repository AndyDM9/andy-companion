"""Keep Andy running, asleep or quiet, and wake it at the right moment.

    python -m andy_companion.supervisor      (scripts/andy runs it)

Awake: run the conversation app (scripts/run-robot.sh) and wait for it to stop.
- It stopped itself (exit 0) with the mode still awake: the person said goodnight (go_to_sleep);
  Andy is now asleep.
- It stopped itself while the mode is quiet: quiet_for asked it to.
- It crashed: start it again after a short pause.

Asleep or quiet: listen for a wake phrase (offline), and wake Andy when one is heard, when a
quiet spell ends, or when a reminder comes due, so a reminder is never missed because Andy slept.
"""

from __future__ import annotations

import json
import logging
import os
import signal
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

from andy_companion import chimes, reminders, screen_server, state, wake

logger = logging.getLogger("andy.supervisor")
ROOT = Path(__file__).resolve().parents[2]
RESTART_DELAY_S = 10.0


def after_exit(mode: str, code: int) -> str:
    """What to do when the app stops: "sleep", "wait" (already quiet or asleep) or "restart"."""
    if code != 0:
        return "restart"
    return "sleep" if mode == "awake" else "wait"


def wake_reason(now: Optional[datetime] = None) -> Optional[str]:
    """Why Andy should wake now, or None."""
    now = now or datetime.now()
    s = state.current(now)
    if s["mode"] == "awake":
        return "awake"
    if s["mode"] == "quiet" and s.get("until") and now.timestamp() >= s["until"]:
        return "quiet over"
    if reminders.due(now):
        return "reminder due"
    return None


def run_app() -> int:
    proc = subprocess.Popen([str(ROOT / "scripts" / "run-robot.sh"), *sys.argv[1:]])
    try:
        return proc.wait()
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        proc.wait(timeout=30)
        raise


def wait_asleep() -> str:
    """Listen for a wake phrase while asleep or quiet; return why Andy wakes."""
    try:
        from vosk import KaldiRecognizer, Model, SetLogLevel

        SetLogLevel(-1)
        model = Model(str(wake.ensure_model()))
    except Exception as e:  # no microphone model: still wake on time and for reminders
        logger.warning("Wake phrase unavailable (%s); waking on time and for reminders only", type(e).__name__)
        model = None
    while True:
        reason = wake_reason()
        if reason:
            return reason
        source = wake.mic_source() if model is not None else None
        if source is None:
            time.sleep(5)
            continue
        from vosk import KaldiRecognizer

        recognizer = KaldiRecognizer(model, wake.RATE, json.dumps(wake.GRAMMAR))
        triggers = wake.triggers_for(state.current()["mode"])
        if wake.heard(wake.mic_chunks(source), recognizer, should_stop=lambda: wake_reason() is not None,
                      triggers=triggers) == "phrase":
            return "wake phrase"


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    if state.current()["mode"] != "awake" and wake_reason() is not None:
        state.awake()
    try:
        screen_server.serve()          # the screen and the family page stay up, asleep or awake
    except OSError as e:
        logger.warning("Andy's screen could not start (%s)", type(e).__name__)
    while True:
        mode = state.current()["mode"]
        if mode == "awake":
            code = run_app()
            action = after_exit(state.current()["mode"], code)
            logger.info("App stopped (code %s): %s", code, action)
            if action == "restart":
                time.sleep(RESTART_DELAY_S)
                continue
            if action == "sleep":
                state.asleep()
            chimes.play("sleep", force=True)
            continue
        reason = wait_asleep()
        logger.info("Waking: %s", reason)
        state.awake()
        chimes.play("wake", force=True)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    sys.exit(main())
