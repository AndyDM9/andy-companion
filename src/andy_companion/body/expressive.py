"""Conversational body language, from studies of people and robots: a glance away while thinking, and
a head tilt on a question.

- **Thinking:** people look away, often up and to the side, when they think before answering. In
  Andrist, Mutlu and Gleicher's measurements (IVA 2013; HRI 2014, on a NAO robot) a robot that did so
  seemed more thoughtful and held the floor better. When Andy has understood the person and no answer
  has started after THINK_AFTER_S (a tool running, or the bigger model thinking), it looks about
  THINK_YAW_DEG to one side and a little up, holds, and comes back to the person. Once per turn, at
  most once in THINK_EVERY_S, alternating sides. Lightning's usual 0.6 to 0.8 s replies never trigger
  it.
- **A question:** a head tilt of about 10 degrees made robots seem more human-like, with no rise in
  eeriness (Mara and Appel 2015). When Andy's reply ends with a question, the head tilts TILT_DEG as
  the last words play, holds briefly, and straightens: a small "over to you". At most once in
  TILT_EVERY_S.

Both are moves of Andy's own through Pollen's queue (body.glance's curve and speed limit, no antenna
perk), so face following lets go and takes the head back; neither plays while the person speaks, while
another move plays, or with face following off. The model never chooses a movement (moves it chose
were removed from the profile on 2026-10-13 after a hard head move). Nodding while the person speaks
is left out until it is checked on the robot that motor sound doesn't reach the microphones.
ANDY_EXPRESSIVE=off turns both off.
"""

from __future__ import annotations

import math
import os
import time
from typing import Callable, Optional

from andy_companion.body import speaking

ENABLED = os.environ.get("ANDY_EXPRESSIVE", "on").strip().lower() not in ("off", "0", "false", "no")
THINK_AFTER_S = 0.8
THINK_YAW_DEG = 14.0
THINK_UP_DEG = 8.0
THINK_HOLD_S = 1.2
THINK_EVERY_S = 20.0
TILT_DEG = 10.0
TILT_HOLD_S = 1.4
TILT_EVERY_S = 15.0
TILT_WHEN_LEFT_S = 0.8          # start the tilt as the last words play
QUESTION_FOR_S = 30.0

_question = {"at": None}


def heard_reply(text: str, now: Optional[float] = None) -> None:
    """Andy's whole reply, as the captions get it: a question arms the tilt."""
    if str(text or "").rstrip().rstrip('"\'»”').endswith(("?", "؟")):
        _question["at"] = time.monotonic() if now is None else now


class Expressive:
    def __init__(self, clock: Callable[[], float] = time.monotonic,
                 voice_left: Callable[[], float] = speaking.remaining) -> None:
        self.clock, self.voice_left = clock, voice_left
        self.think_since: Optional[float] = None
        self.thought_this_turn = False
        self.last_think = -1e9
        self.last_tilt = -1e9
        self.side = 1.0

    def step(self, manager, antennas, *, thinking: bool, listening: bool, move_playing: bool,
             tracking: bool, queueable: Optional[Callable] = None) -> Optional[str]:
        """One control tick; returns 'think' or 'tilt' when it queues one."""
        from andy_companion.body import glance

        now = self.clock()
        queueable = queueable or glance.queueable
        if not thinking:
            self.think_since, self.thought_this_turn = None, False
        elif self.think_since is None:
            self.think_since = now
        free = tracking and not listening and not move_playing
        if not free:
            return None
        robot = manager.current_robot
        if (thinking and not self.thought_this_turn and now - self.think_since >= THINK_AFTER_S
                and now - self.last_think >= THINK_EVERY_S):
            start = robot.get_current_head_pose()
            _, pitch, yaw = glance._rpy(start)
            g = glance.Glance(start, antennas, (yaw + self.side * math.radians(THINK_YAW_DEG),
                                                pitch - math.radians(THINK_UP_DEG)), perk=0.0, hold_s=THINK_HOLD_S)
            manager.queue_move(queueable(g))
            self.thought_this_turn, self.last_think, self.side = True, now, -self.side
            return "think"
        asked = _question["at"]
        if asked is not None:
            if now - asked > QUESTION_FOR_S:
                _question["at"] = None
            elif 0.0 < self.voice_left() <= TILT_WHEN_LEFT_S and now - self.last_tilt >= TILT_EVERY_S:
                start = robot.get_current_head_pose()
                _, pitch, yaw = glance._rpy(start)
                g = glance.Glance(start, antennas, (yaw, pitch), perk=0.0, roll=math.radians(TILT_DEG) * self.side,
                                  hold_s=TILT_HOLD_S)
                manager.queue_move(queueable(g))
                _question["at"], self.last_tilt = None, now
                return "tilt"
        return None
