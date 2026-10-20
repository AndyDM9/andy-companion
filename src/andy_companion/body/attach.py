"""Attach Andy's body behaviours to Pollen's conversation app, without forking it.

Pollen's MovementManager sends every pose through one method, `_issue_control_command`. Wrapping
it lets Andy, on each control tick:
- find the person by voice direction, a look around or a person in view (seek, person);
- keep looking at the person while Andy speaks (gaze: Pollen pauses tracking during a reply);
- turn the body to face a person who has moved (body_follow);
- hand the head over to a calm idle moment and take it back (idle);
- soften upward looks (gaze);
- glance at the TV when something new shows on it (glance);
- a small antenna wiggle after a joke's punchline (giggle);
- a glance away while thinking and a head tilt on a question (expressive).

Anything of ours that fails falls back to Pollen's own command, so movement never stops.
"""

from __future__ import annotations

import logging
import time

logger = logging.getLogger("andy.body")


def seek_step(manager, now, head, tracking, head_world_yaw, move_playing):
    """One tick of seek: find the person by voice direction, a look around or a person in view.
    Returns the head pose to send (steered while seeking)."""
    import numpy as np

    from andy_companion.body import body_follow, person, presence, seek

    from andy_companion.body import hold

    if hold.active(manager):            # a search owns the head: no seeking, no weight asked for
        return head
    seeker = manager.__dict__.setdefault("_andy_seek", seek.Seek())
    cache = manager.__dict__.setdefault("_andy_seek_cache", {"t_face": -1e9, "face": False, "t_doa": -1e9, "doa": None,
                                                            "held": None})
    robot = manager.current_robot
    if tracking and now - cache["t_face"] >= 0.1:
        cache["t_face"] = now
        try:
            cache["face"] = bool(robot.get_tracked_face(wait=False).detected)
        except Exception:
            cache["face"] = False
    listening = bool(getattr(manager, "_is_listening", False))
    if tracking and listening and now - cache["t_doa"] >= 0.2:
        cache["t_doa"] = now
        try:
            cache["doa"], cache["held"] = seek.voiced_angle(robot.media.get_DoA(), cache["held"], now)
        except Exception:
            cache["doa"] = None
    if tracking and cache["face"]:
        cache["t_face_seen"] = now
    watcher = manager.__dict__.get("_andy_person")
    if watcher is None and person.ENABLED:
        def intrinsics():
            try:
                K = robot.media.camera.resized_K
                return float(K[0][0]), float(K[0][2])
            except Exception:
                return person.DEFAULT_FX, person.DEFAULT_CX
        # Look for a person only while tracking is on and no face has been seen for a second.
        watcher = person.PersonWatcher(
            lambda: robot.media.get_frame(),
            lambda: bool(getattr(manager, "_head_tracking", False)) and time.monotonic() - cache.get("t_face_seen", -1e9) > 1.0,
            intrinsics)
        manager.__dict__["_andy_person"] = watcher
    person_yaw = watcher.latest(time.monotonic()) if watcher is not None and tracking and not cache["face"] else None
    person_top = watcher.top_now(time.monotonic()) if person_yaw is not None else None
    if cache["face"] or person_yaw is not None or listening:
        presence.mark("face" if cache["face"] else "person" if person_yaw is not None else "voice")
    before = seeker.state
    decision = seeker.step(now, tracking=tracking, face=cache["face"], head_world_yaw=head_world_yaw,
                           user_speaking=listening, robot_speaking=bool(getattr(manager, "_is_speaking", False)),
                           move_playing=move_playing, doa_angle=cache["doa"] if listening else None,
                           person_yaw=person_yaw, person_top=person_top)
    if seeker.state != before:
        logger.info("seek %s -> %s", before, seeker.state)
    own_move = getattr(getattr(manager, "state", None), "current_move", None)
    if decision.weight is not None and not getattr(own_move, "andy_owns_head", False):
        try:
            robot.start_head_tracking(weight=decision.weight)
        except Exception:
            pass
    if decision.head_yaw is None:
        return head
    delta = decision.head_yaw - body_follow.head_yaw(head)
    c, s = np.cos(delta), np.sin(delta)
    turn = np.array([[c, -s, 0, 0], [s, c, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
    pose = turn @ head
    if decision.head_up:
        # Positive pitch about the head's own y axis looks down, so look up with a negative one.
        cu, su = np.cos(-decision.head_up), np.sin(-decision.head_up)
        tilt = np.array([[cu, 0, su, 0], [0, 1, 0, 0], [-su, 0, cu, 0], [0, 0, 0, 1]])
        pose = pose @ tilt
    return pose


def follow_with_body() -> bool:
    """Wrap MovementManager's single send point with Andy's body behaviours. Off with
    ANDY_BODY_FOLLOW=off."""
    from andy_companion import turns
    from andy_companion.body import body_follow, expressive, gaze, giggle, glance, idle, listening as ears, presence, seek, thinking

    if not body_follow.ENABLED:
        return False
    from reachy_mini_conversation_app import moves

    send = moves.MovementManager._issue_control_command
    if getattr(send, "_andy_body_follow", False):
        return True

    def issue_with_body_follow(self, head, antennas, body_yaw):
        # Pollen's loop has no try: an exception here would stop all movement for the session.
        try:
            return andy_step(self, head, antennas, body_yaw)
        except Exception:
            failed = self.__dict__.setdefault("_andy_step_failed", {"count": 0, "logged": -1e9})
            failed["count"] += 1
            if time.monotonic() - failed["logged"] >= 300:
                failed["logged"] = time.monotonic()
                logger.exception("Andy's movement step failed (%d times this session); using Pollen's command",
                                 failed["count"])
            return send(self, head, antennas, body_yaw)

    def andy_step(self, head, antennas, body_yaw):
        follower = self.__dict__.setdefault("_andy_follow", body_follow.BodyFollow())
        now = self._now()
        move = self.state.current_move
        move_owns_body = move is not None and not isinstance(move, moves.BreathingMove)
        tracking = bool(getattr(self, "_head_tracking", False))
        listening = bool(getattr(self, "_is_listening", False))
        yaw = follower.read_head_yaw(now, self.current_robot.get_current_head_pose) if tracking else None
        if glance.ENABLED:
            glance.step(self, now, antennas, listening=listening, move_playing=move_owns_body, tracking=tracking)
        if expressive.ENABLED:
            body_language = self.__dict__.setdefault("_andy_expressive", expressive.Expressive())
            body_language.step(self, (float(antennas[0]), float(antennas[1])), thinking=turns.CLOCK.thinking(),
                               listening=listening, move_playing=move_owns_body, tracking=tracking)
        # Andy's own head moves (idle moments): give the head back before seek, so seek's weight
        # wins on that tick; take it after seek, whose stand-down would undo it.
        idle.release_step(self, now)
        if seek.ENABLED:
            head = seek_step(self, now, head, tracking, yaw, move_owns_body)
        face = bool(self.__dict__.get("_andy_seek_cache", {}).get("face"))
        idle.take_step(self, face)
        # While Andy talks, keep following the face (Pollen pauses tracking for the whole reply).
        gaze.speaking_step(self, face, move_owns_body)
        if idle.enabled():
            flick = self.__dict__.setdefault("_andy_flick", idle.Flick(present=lambda: presence.recent(idle.PRESENT_WITHIN_S)))
            antennas = flick.step(now, (float(antennas[0]), float(antennas[1])), not move_owns_body and not listening)
        if ears.ENABLED:
            ear = self.__dict__.setdefault("_andy_ears", ears.Listening())
            antennas = ear.step(now, (float(antennas[0]), float(antennas[1])), listening and not move_owns_body)
        if thinking.ENABLED:
            thinker = self.__dict__.setdefault("_andy_thinking", thinking.Thinking())
            antennas = thinker.step(now, (float(antennas[0]), float(antennas[1])),
                                    turns.CLOCK.thinking() and not listening and not move_owns_body)
        if giggle.ENABLED:
            giggler = self.__dict__.setdefault("_andy_giggle", giggle.Giggle())
            antennas = giggler.step((float(antennas[0]), float(antennas[1])), not listening and not move_owns_body)
        head = gaze.soften_look_up(head)
        return send(self, head, antennas, follower.step(now, yaw, float(body_yaw), tracking, move_owns_body))

    issue_with_body_follow._andy_body_follow = True
    moves.MovementManager._issue_control_command = issue_with_body_follow
    glance.watch()
    return True


def track_speech_audio() -> bool:
    """Note how much of Andy's voice is still to play (andy_companion.body.speaking), by watching what
    Pollen's app pushes to the speaker and its barge-in clear. Observes only: every call goes through."""
    from andy_companion.body import speaking
    from reachy_mini.media.media_manager import MediaManager
    from reachy_mini_conversation_app.console import LocalStream

    push = MediaManager.push_audio_sample
    if getattr(push, "_andy_speaking", False):
        return True

    def push_and_note(self, data):
        result = push(self, data)
        try:
            rate = self.__dict__.get("_andy_rate")
            if not rate:
                rate = float(self.get_output_audio_samplerate())
                if rate > 0:
                    self.__dict__["_andy_rate"] = rate
            speaking.pushed(int(getattr(data, "shape", (len(data),))[0]), rate)
        except Exception:
            pass
        return result

    clear = LocalStream.clear_audio_queue

    def clear_and_note(self, *args, **kwargs):
        left = speaking.remaining()
        speaking.cleared()
        out = clear(self, *args, **kwargs)
        if left > 0.3:                    # the person talked over Andy: he stops and listens
            try:
                from andy_companion import turns

                turns.interrupted(left)
            except Exception:
                pass
        return out

    push_and_note._andy_speaking = True
    MediaManager.push_audio_sample = push_and_note
    LocalStream.clear_audio_queue = clear_and_note
    return True


def livelier_idle() -> bool:
    """Replace Pollen's idle action (a random dance, emotion or head turn, rage1 and dying1 among
    them) with a calm moment, at ANDY_IDLE's cadence. Never reaches the model. ANDY_IDLE=pollen keeps
    Pollen's own."""
    from andy_companion.body import idle
    from reachy_mini_conversation_app.conversation_handler import ConversationHandler

    if idle.CADENCE == "pollen" or getattr(ConversationHandler.send_idle_signal, "_andy_idle", False):
        return False
    ConversationHandler.IDLE_BEHAVIOR_THRESHOLD_S = idle.INTERVAL_S.get(idle.CADENCE, float("inf"))

    async def send_idle_signal(self, idle_duration: float) -> None:
        try:
            await idle.moment(self.deps.movement_manager, idle_duration)
        except Exception:
            logger.warning("idle moment skipped", exc_info=True)

    send_idle_signal._andy_idle = True
    ConversationHandler.send_idle_signal = send_idle_signal
    return True


def install() -> None:
    follow_with_body()
    track_speech_audio()
    livelier_idle()
    look_at_people_from_the_start()


def look_at_people_from_the_start() -> bool:
    """Follow faces as soon as movement starts, in code. The greeting used to ask the model to turn
    head_tracking on first; it then returned only that call and its next reply came back empty, so
    Andy woke in silence (2026-10-13). The model may still turn tracking off and on when asked."""
    from reachy_mini_conversation_app import moves

    start = moves.MovementManager.start
    if getattr(start, "_andy_tracking", False):
        return False

    def start_and_follow(self, *args, **kwargs):
        out = start(self, *args, **kwargs)
        try:
            self.set_head_tracking(True)
        except Exception:
            logger.warning("Could not turn face following on at start")
        return out

    start_and_follow._andy_tracking = True
    moves.MovementManager.start = start_and_follow
    return True
