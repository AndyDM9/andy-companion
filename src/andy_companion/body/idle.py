"""Livelier idle (research 2026-10-06, ability #7): calm moments instead of Pollen's random ones,
and small antenna flicks in between.

Pollen's app runs an idle action after 3 minutes without conversation, every 3 minutes: 60% nothing,
otherwise a random dance, a random emotion from its curated list (which includes rage1, dying1 and
scared1) or a 40-degree head turn. The launcher replaces that (andy_companion.body.attach,
`livelier_idle`) with a moment from MOMENTS: a look around, an attentive glance, a look up, a calm
breath, or a yawn (likelier late at night or after a long quiet spell). Nothing during a focus
session or when nobody has been seen for a while. The moves are Pollen's own recorded emotions,
played through its movement queue; face following hands the head over for the move and takes it
back afterwards (`take_step`, `release_step`), as Pollen does while Andy speaks.

Between moments, now and then one antenna flicks (`Flick`): small, smooth and slower than the
antenna buttons' press threshold, only while nothing else is shown with the antennas.

ANDY_IDLE: calm (default), lively, off (stay still apart from breathing), pollen (Pollen's own).
"""

from __future__ import annotations

import os
import time
import random
import asyncio
import logging
from typing import Any, Callable, Iterable, Optional, Tuple

logger = logging.getLogger("andy.idle")

CADENCE = os.environ.get("ANDY_IDLE", "calm").strip().lower()
INTERVAL_S = {"calm": 300.0, "lively": 120.0}       # Pollen's own is 180 s
if CADENCE not in (*INTERVAL_S, "off", "pollen"):
    logger.warning("ANDY_IDLE=%r isn't calm, lively, off or pollen: using calm", CADENCE)
    CADENCE = "calm"
NOTHING = {"calm": 0.4, "lively": 0.15}             # the chance an idle turn stays still anyway
FLICK_EVERY_S = {"calm": (60.0, 150.0), "lively": (20.0, 60.0)}
PRESENT_WITHIN_S = 600.0                            # someone seen or heard in the last 10 minutes

EMOTIONS = "pollen-robotics/reachy-mini-emotions-library"
# Pollen's recorded moves (descriptions from the library's metadata), weighted.
MOMENTS = {"attentive1": 3, "curious1": 2, "thoughtful1": 2, "serenity1": 2, "tired1": 1}
YAWN, YAWN_LATE_WEIGHT = "tired1", 4

FLICK_RAD = 0.22          # about 13 degrees
FLICK_UP_S = 0.2          # peak speed ~1.7 rad/s: under robot_state's 2 rad/s, far from a button press
FLICK_DOWN_S = 0.4


def enabled() -> bool:
    return CADENCE in INTERVAL_S


def pick(idle_s: float, available: Iterable[str], *, hour: Optional[int] = None, present: Optional[bool] = None,
         focus: Optional[bool] = None, rng: Any = random) -> Optional[str]:
    """The moment to play now, or None to stay still."""
    from andy_companion.body import presence

    if not enabled():
        return None
    if focus:
        return None
    if not (presence.recent(PRESENT_WITHIN_S) if present is None else present):
        return None
    if rng.random() < NOTHING[CADENCE]:
        return None
    weights = dict(MOMENTS)
    hour = time.localtime().tm_hour if hour is None else hour
    if idle_s > 1200 or hour >= 22 or hour < 6:
        weights[YAWN] = YAWN_LATE_WEIGHT
    names = [n for n in weights if n in set(available)]
    if not names:
        return None
    return rng.choices(names, weights=[weights[n] for n in names], k=1)[0]


_library = None


def library():
    """Pollen's emotions library, from the local Hugging Face cache (loaded once)."""
    global _library
    if _library is None:
        from reachy_mini.motion.recorded_move import RecordedMoves

        _library = RecordedMoves(EMOTIONS)
    return _library


def idle_move(name: str, moves_library) -> Any:
    from reachy_mini_conversation_app.dance_emotion_moves import EmotionQueueMove

    move = EmotionQueueMove(name, moves_library)
    move.andy_owns_head = True               # take_step knows it's ours
    return move


async def moment(manager, idle_s: float, rng: Any = random, load: Optional[Callable[[], Any]] = None) -> Optional[str]:
    """Pollen's idle turn, Andy's way: queue one calm moment, or nothing."""
    moves_library = await asyncio.to_thread(load or library)
    name = pick(idle_s, moves_library.list_moves(), rng=rng)
    if name is None:
        logger.info("idle turn after %.0f s: still", idle_s)
        return None
    manager.queue_move(idle_move(name, moves_library))
    logger.info("idle moment %s after %.0f s", name, idle_s)
    return name


RELEASE_AFTER_S = 0.2      # a one-tick gap between two of Andy's moves isn't the end (finder: scan, then point)


def _owns_head(manager) -> bool:
    return bool(getattr(manager.state.current_move, "andy_owns_head", False))


def release_step(manager, now: float) -> None:
    """Each movement tick, BEFORE seek: once none of Andy's own head moves has played for
    RELEASE_AFTER_S, face following gets the head back (weight 1), so seek's own weight on the same
    tick wins. If Andy is speaking, Pollen's end of speech hands it back instead."""
    state = manager.__dict__.setdefault("_andy_idle_handoff", {"owned": False, "gone_since": None})
    if _owns_head(manager) or not state["owned"]:
        state["gone_since"] = None
        return
    if state["gone_since"] is None:
        state["gone_since"] = now
    if now - state["gone_since"] < RELEASE_AFTER_S:
        return
    state["owned"], state["gone_since"] = False, None
    if getattr(manager, "_head_tracking", False) and not getattr(manager, "_is_speaking", False):
        manager._track_anchor = None
        manager.current_robot.start_head_tracking(weight=_weight_seek_wants(manager))


def _weight_seek_wants(manager) -> float:
    """Back to what seek holds now: it may have started searching during the release grace (robot,
    2026-10-07: seek's 0.01 at the end of a move was overwritten with 1)."""
    from andy_companion.body import seek

    seeker = manager.__dict__.get("_andy_seek")
    return seek.SEEK_WEIGHT if seeker is not None and seeker.state in ("TURN", "SCAN", "PERSON", "HOME") else 1.0


def take_step(manager, face: bool) -> None:
    """Each movement tick, AFTER seek (which stands down to weight 1 on the tick a move starts):
    while one of Andy's own head moves plays (an idle moment, the finder's look-around; marked
    `andy_owns_head`), face following lets go of the head, holding the look at the person as an
    anchor, as Pollen does while Andy speaks."""
    state = manager.__dict__.setdefault("_andy_idle_handoff", {"owned": False, "gone_since": None})
    if state["owned"] or not _owns_head(manager):
        return
    if not getattr(manager, "_head_tracking", False) or getattr(manager, "_is_speaking", False):
        return
    state["owned"] = True
    robot = manager.current_robot
    if face:
        manager._track_anchor = robot.get_current_head_pose()
    robot.start_head_tracking(weight=0.0)


class Flick:
    """Now and then, one antenna twitches out and back."""

    def __init__(self, rng: Any = random, present: Optional[Callable[[], bool]] = None):
        self.rng = rng
        self.present = present
        self.next_at: Optional[float] = None
        self.start: Optional[float] = None
        self.side, self.sign = 0, 1.0

    def _schedule(self, now: float) -> None:
        lo, hi = FLICK_EVERY_S[CADENCE]
        self.next_at = now + self.rng.uniform(lo, hi)

    def step(self, now: float, antennas: Tuple[float, float], allowed: bool) -> Tuple[float, float]:
        if not enabled():
            return antennas
        if self.start is None:
            if self.next_at is None:
                self._schedule(now)
            if now < self.next_at:
                return antennas
            if not allowed:
                return antennas                # wait until the antennas are free
            self._schedule(now)
            present = self.present
            if present is not None and not present():
                return antennas                # nobody to see it: skip this one
            self.start, self.side, self.sign = now, self.rng.choice((0, 1)), self.rng.choice((-1.0, 1.0))
        t = now - self.start
        if t >= FLICK_UP_S + FLICK_DOWN_S or not allowed:
            # Stopped early if the antennas are needed (they start talking: Pollen freezes them where
            # they are, which mustn't be mid-flick).
            self.start = None
            return antennas
        # Smoothstep out, smoothstep back: no jumps.
        x = t / FLICK_UP_S if t < FLICK_UP_S else 1.0 - (t - FLICK_UP_S) / FLICK_DOWN_S
        offset = self.sign * FLICK_RAD * x * x * (3.0 - 2.0 * x)
        out = [float(antennas[0]), float(antennas[1])]
        out[self.side] += offset
        return out[0], out[1]
