"""Keep looking at the person while Andy talks, so the person feels spoken to.

Pollen pauses face tracking for the whole of Andy's reply (PR #381): on set_speaking(True), with a face
locked, it holds the head where it was (`_track_anchor`) at tracking weight 0, so dances and emotions
can play during the reply; the daemon's speech wobble composes on top either way. If the person moves
while Andy talks, the head stays where they were.

So, each control tick while Andy speaks: with no move playing, tracking keeps the head (weight 1,
no anchor), so it follows the face as it does while listening, the wobble still on top; while a move
plays (an emotion mid-reply), Pollen's way: hold the current look as the anchor at weight 0, so the move
shows; when it ends, tracking takes the head back. Seek keeps the head while it is searching, and
nothing changes when tracking is off or Andy is silent: set_speaking(False) is Pollen's as before.

ANDY_SPEAK_FOLLOW=off restores Pollen's pause.

`soften_look_up`: Pollen's recorded emotions tilt the head up to 22.5 degrees (attentive1, thoughtful1,
laughing1, welcoming2 ...), made for a robot sitting low and looking up at a person. With Andy at the
person's head height every pose sent is softened
above MAX_LOOK_UP (smoothly, so the gesture keeps its shape); looking down and turning are untouched.
Face tracking itself is the daemon's and isn't affected. ANDY_MAX_LOOK_UP_DEG=off sends poses as they are.
"""

from __future__ import annotations

import os
import math
import logging

logger = logging.getLogger("andy.gaze")

ENABLED = os.environ.get("ANDY_SPEAK_FOLLOW", "on").strip().lower() != "off"
SEEKING = ("TURN", "SCAN", "PERSON", "HOME")
_cap = os.environ.get("ANDY_MAX_LOOK_UP_DEG", "10").strip().lower()
MAX_LOOK_UP = None if _cap == "off" else math.radians(float(_cap))


def soften_look_up(pose, limit=None):
    """The head pose (4x4) with its upward pitch eased below `limit` (radians); positive pitch looks
    down, as in Pollen's create_head_pose (xyz Euler angles), so up is negative."""
    import numpy as np

    limit = MAX_LOOK_UP if limit is None else limit
    if limit is None or pose is None:
        return pose
    R = np.asarray(pose, dtype=float)[:3, :3]
    pitch = math.asin(max(-1.0, min(1.0, -R[2, 0])))
    if -pitch <= 0.0:
        return pose
    soft = -limit * math.tanh(-pitch / limit)
    if abs(soft - pitch) < 1e-6:
        return pose
    roll, yaw = math.atan2(R[2, 1], R[2, 2]), math.atan2(R[1, 0], R[0, 0])
    cr, sr, cp, sp, cy, sy = math.cos(roll), math.sin(roll), math.cos(soft), math.sin(soft), math.cos(yaw), math.sin(yaw)
    out = np.array(pose, dtype=float, copy=True)
    out[:3, :3] = (np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]])
                   @ np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]])
                   @ np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]]))
    return out


def _move_playing(manager) -> bool:
    from reachy_mini_conversation_app.moves import BreathingMove

    move = getattr(getattr(manager, "state", None), "current_move", None)
    return move is not None and not isinstance(move, BreathingMove)


def speaking_step(manager, face: bool, move_playing=None) -> None:
    """One control tick, after seek and idle.take_step."""
    state = manager.__dict__.setdefault("_andy_gaze", {"following": False})
    if not ENABLED or not getattr(manager, "_head_tracking", False) or not getattr(manager, "_is_speaking", False):
        state["following"] = False
        state["logged"] = False                       # once per reply in the log
        return
    seeker = manager.__dict__.get("_andy_seek")
    if seeker is not None and seeker.state in SEEKING:
        state["following"] = False                    # seek steers the head; it hands back when done
        return
    playing = _move_playing(manager) if move_playing is None else move_playing
    robot = manager.current_robot
    try:
        if playing:
            if state["following"]:
                # A gesture mid-reply: hold this look and let the move show, as Pollen does.
                if face:
                    manager._track_anchor = robot.get_current_head_pose()
                robot.start_head_tracking(weight=0.0)
                state["following"] = False
        elif not state["following"]:
            manager._track_anchor = None
            robot.start_head_tracking(weight=1.0)
            state["following"] = True
            if not state.get("logged"):
                logger.info("Following the face while speaking")
            state["logged"] = True
        if state["following"]:
            from andy_companion.body import looking_at
            looking_at.set("you", 1.0)                 # renewed every tick while it lasts
    except Exception as e:
        logger.warning("Following while speaking failed: %s", e)
