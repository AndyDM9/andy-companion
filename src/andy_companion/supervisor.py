"""Keep Andy running, asleep or quiet, and wake it at the right moment.

    python -m andy_companion.supervisor      (scripts/andy runs it)

Awake: run the conversation app (scripts/run-robot.sh) and wait for it to stop.
- It stopped itself (exit 0) with the mode still awake: the person said goodnight (go_to_sleep);
  Andy is now asleep.
- It stopped itself while the mode is quiet: quiet_for asked it to.
- It crashed, or its watchdog asked for a restart (andy_companion.watchdog): start it again after a
  short pause, and log why.

Asleep or quiet: listen for a wake phrase (offline), and wake Andy when one is heard, when a
quiet spell ends, or when a reminder comes due, so a reminder is never missed because Andy slept.
A reminder only borrows Andy: once it has been said and no one has talked with Andy for a minute,
Andy goes back to sleep, or to what is left of the quiet spell (BackAfterReminder).

The supervisor hosts the screen server, so it reads the keys the screen's own features need (the
setup page's Tavily calendar search) from the private env file itself (app_mode.SUPERVISOR_KEYS).
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
from typing import Any, Callable, Dict, List, Optional

from andy_companion import chimes, reminders, screen_server, state, wake

logger = logging.getLogger("andy.supervisor")
ROOT = Path(__file__).resolve().parents[2]
RESTART_DELAY_S = 10.0
# A reminder that was already due, but not yet said, when the person said goodnight (or "be quiet") does
# not wake Andy straight back up: goodnight sticks for SETTLE_S. The reminder is not dropped, because a
# reminder is never missed for sleep: after SETTLE_S it wakes Andy, is said, and Andy goes back to sleep.
# A reminder that comes due after the goodnight wakes Andy at once, as before.
SETTLE_S = 10 * 60
# After a reminder woke Andy and was said: how long with no one talking with Andy before it goes back.
RESUME_IDLE_S = 60.0
POLL_S = 1.0


def after_exit(mode: str, code: int, restart_asked: bool = False) -> str:
    """What to do when the app stops: "sleep", "wait" (already quiet or asleep) or "restart"."""
    if code != 0 or restart_asked:
        return "restart"
    return "sleep" if mode == "awake" else "wait"


def reminders_to_wake(now: Optional[datetime] = None) -> List[Dict[str, Any]]:
    """The due reminders that may wake Andy now: all of them, except, for SETTLE_S after Andy went to sleep
    or quiet, those that were already due by then."""
    now = now or datetime.now()
    mode = state.current(now)
    if mode.get("unreadable"):
        return []
    since = mode.get("since") or 0
    settling = 0 <= now.timestamp() - since < SETTLE_S
    return [r for r in reminders.due(now) if not (settling and r["due"] <= since)]


def wake_reason(now: Optional[datetime] = None) -> Optional[str]:
    """Why Andy should wake now, or None."""
    now = now or datetime.now()
    s = state.current(now)
    if s["mode"] == "awake":
        return "awake"
    if s["mode"] == "quiet" and s.get("until") and now.timestamp() >= s["until"]:
        return "quiet over"
    if reminders_to_wake(now):
        return "reminder due"
    return None


def wake_up(reason: str, now: Optional[datetime] = None) -> None:
    """Wake Andy. Woken for a reminder, Andy remembers the sleep or quiet it came from, to go back to."""
    now = now or datetime.now()
    s = state.current(now)
    if s.get("unreadable") and reason != "wake phrase":
        return  # a stale automatic reason cannot override newly unreadable mode data
    if reason == "reminder due" and s["mode"] in ("asleep", "quiet"):
        ids = [r["id"] for r in reminders_to_wake(now)]
        state.awake(return_to={"mode": s["mode"], "until": s.get("until"), "reminders": ids})
    else:
        state.awake()


def go_back(back: Dict[str, Any], now: Optional[datetime] = None) -> str:
    """Return to the sleep or quiet a reminder woke Andy from; a quiet spell that has ended by now is over."""
    now = now or datetime.now()
    until = back.get("until")
    if back.get("mode") == "asleep":
        state.asleep(now)
        return "asleep"
    if back.get("mode") == "quiet" and isinstance(until, (int, float)) and until > now.timestamp():
        state.quiet_until(until, now)
        return "quiet"
    state.awake()
    return "awake"


class BackAfterReminder:
    """Watches the app while it runs after a reminder woke Andy. When every reminder that woke it has been said
    (deleted, or a daily one moved on) and no one has talked with Andy for RESUME_IDLE_S, it puts the mode back
    and answers True, and the supervisor stops the app. Talking with Andy keeps it awake until the talk ends.
    A goodnight or "be quiet" in the meantime replaces return_to; the person asked for the quiet or sleep the
    reminder interrupted, and can end it with the wake phrase as usual."""

    def __init__(self, clock: Callable[[], float] = time.time) -> None:
        self.clock = clock
        self.said_at: Optional[float] = None
        self.busy_at = 0.0

    def __call__(self) -> bool:
        now = self.clock()
        s = state.current()
        if s.get("unreadable"):
            return True  # the existing app stops through its normal process-control path
        back = s.get("return_to")
        if s["mode"] != "awake" or not isinstance(back, dict):
            self.said_at = None
            return False
        waiting = {r["id"] for r in reminders.due(datetime.fromtimestamp(now))}
        if waiting & set(back.get("reminders") or []):
            self.said_at = None
            return False
        if self.said_at is None:
            self.said_at = now
        live = screen_server._live            # the app's live state, reported to the screen in this process
        if live["state"] not in ("", "ready") and now - float(live["at"]) <= screen_server.LIVE_STALE_S:
            self.busy_at = now
        if now - max(self.said_at, self.busy_at) < RESUME_IDLE_S:
            return False
        went = go_back(back, datetime.fromtimestamp(now))
        logger.info("The reminder was said; back to %s", went)
        return went != "awake"


def run_app(should_stop: Optional[Callable[[], bool]] = None, poll_s: float = POLL_S) -> int:
    """Run the app until it stops. When should_stop() answers True, stop it the way Ctrl+C does and return 0:
    a stop the supervisor chose is never taken for a crash."""
    # The app hears Ctrl-C (SIGINT) even when Andy was started in the background, where it would be ignored.
    proc = subprocess.Popen([str(ROOT / "scripts" / "run-robot.sh"), *sys.argv[1:]],
                            # In the child before exec: only a signal reset. Kept as it has run on the robot since 2026-10-14.
                            preexec_fn=lambda: signal.signal(signal.SIGINT, signal.SIG_DFL))  # noqa: PLW1509
    try:
        while True:
            try:
                return proc.wait(timeout=poll_s if should_stop else None)
            except subprocess.TimeoutExpired:
                pass
            try:
                stop = should_stop is not None and should_stop()
            except Exception:
                logger.debug("supervisor check failed", exc_info=True)
                stop = False
            if stop:
                proc.send_signal(signal.SIGINT)
                try:
                    proc.wait(timeout=30)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                return 0
    except KeyboardInterrupt:
        proc.send_signal(signal.SIGINT)
        try:
            proc.wait(timeout=30)
        except (KeyboardInterrupt, subprocess.TimeoutExpired):   # a second stop signal, or a stuck app
            proc.kill()
            proc.wait()
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
    model_es = None
    try:
        # Spanish too, for a Spanish speaker (fetched then, about 40 MB) or once its model is here.
        from andy_companion import settings
        if settings.get().get("language") == "es" or (wake.MODEL_DIR.parent / wake.MODEL_ES).is_dir():
            model_es = Model(str(wake.ensure_model("es")))
    except Exception as e:
        logger.info("Spanish wake phrase unavailable (%s)", type(e).__name__)
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
        saved = state.current()
        mode = "quiet" if saved.get("unreadable") else saved["mode"]  # require an explicit wake, not a greeting
        also = [(KaldiRecognizer(model_es, wake.RATE, json.dumps(wake.GRAMMAR_ES, ensure_ascii=False)), wake.triggers_for(mode, "es"))] \
            if model_es is not None else []
        if wake.heard(wake.mic_chunks(source), recognizer, should_stop=lambda: wake_reason() is not None,
                      triggers=wake.triggers_for(mode), also=also) == "phrase":
            return "wake phrase"


def main() -> int:
    os.umask(0o077)              # the screen's files, photos and notes: the owner's alone (privacy.owner_only_files)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s | %(message)s")
    from andy_companion import app_mode

    loaded = app_mode.load_env(app_mode.SUPERVISOR_KEYS)      # names only in the log, never values
    logger.info("From the env file: %s", ", ".join(loaded) or "nothing new")
    reason = wake_reason() if state.current()["mode"] != "awake" else None
    if reason is not None:
        wake_up(reason)
    try:
        screen_server.serve()          # the screen and the family page stay up, asleep or awake
    except OSError as e:
        logger.warning("Andy's screen could not start (%s)", type(e).__name__)
    while True:
        mode = state.current()["mode"]
        if mode == "awake":
            code = run_app(should_stop=BackAfterReminder())
            from andy_companion import watchdog

            why = watchdog.take_request()
            after = state.current()
            action = "wait" if after.get("unreadable") else after_exit(after["mode"], code, restart_asked=why is not None)
            logger.info("App stopped (code %s): %s%s", code, action, f" ({why})" if why else "")
            if action == "restart":
                time.sleep(RESTART_DELAY_S)
                continue
            if action == "sleep":
                state.asleep()
            if not after.get("unreadable"):
                chimes.play("sleep", force=True)
            continue
        reason = wait_asleep()
        logger.info("Waking: %s", reason)
        wake_up(reason)
        chimes.play("wake", force=True)


def stopped() -> int:
    """A stop asked for (Ctrl-C, or the service manager's SIGINT) is a clean exit, not a failure, so
    `systemctl --user stop andy` leaves the service stopped rather than failed."""
    logger.info("Stopped")
    return 0


def stop_on_signals() -> None:
    """Ctrl-C and SIGTERM both stop Andy the same clean way (the app first). Started in the background a
    program ignores Ctrl-C, and SIGTERM would otherwise end the supervisor and leave the app running: on
    2026-10-14 two copies left that way by a test script kept running beside the service."""
    def stop(signum, frame):
        raise KeyboardInterrupt
    signal.signal(signal.SIGINT, signal.default_int_handler)
    signal.signal(signal.SIGTERM, stop)


if __name__ == "__main__":
    os.environ.setdefault("PYTHONUNBUFFERED", "1")
    stop_on_signals()
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        sys.exit(stopped())
