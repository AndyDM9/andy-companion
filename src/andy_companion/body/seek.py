"""Find the person again when face tracking loses them: turn toward their voice, or look around.

Pollen's daemon-side tracking recentres the head 2 s after the face is lost and, at full
weight, ignores head commands from the app; at weight 0 it stops detecting faces at all. So
while seeking, tracking runs at a tiny weight (SEEK_WEIGHT): faces are still detected, and the
app's head pose is what the robot follows. As soon as a face is seen again, full weight comes
back and Pollen's tracking takes over. This all runs in the one control loop (andy_companion.body.attach
wraps MovementManager's send point), never as a second controller.

On waking with nobody in view, it looks around once. Voice directions count only when the
microphones flag speech.

When no face is seen but a person is (back turned, across the room; andy_companion.body.person), it
follows the person: PERSON keeps the head turned toward them, and the body follows as usual.
While they are gone it looks around again every RESCAN_EVERY_S, for RESCAN_FOR_S after they were last
seen.

A second speaker (2026-10-20, PLAN B45, "turn to whoever speaks"): while Andy follows one face, speech from more than
SECOND_VOICE_DEG to the side for SECOND_VOICE_S, with Andy silent, turns the head to it (TURN, the old face no longer
ending the turn until it arrives); a face there and tracking takes the new person. Nobody there (the TV, a radio):
the head goes back to the first person and that direction is ignored for IGNORE_S. ANDY_TURN_TO_SPEAKER=off.

States: FOLLOW (normal) -> TURN (toward the direction a voice came from) or SCAN (one slow look
left and right) -> back to FOLLOW when a face is found, or HOME then REST (centre, normal
tracking) when the search ends empty. A new voice from out of view starts a new TURN.

Andy fell off the computer on 2026-10-07. Seek flapped PERSON -> REST -> PERSON every few seconds
on a flickering person detection, and every stand-down handed the head straight back to Pollen's
tracking at full weight, which with no face in view snaps it to the centre at once (and body
follow swung the body after it). So: HOME brings the head back to the centre at the seek rate,
still steering at SEEK_WEIGHT, and hands over only once it's there (also when Andy starts talking
mid-search); a person is followed only after PERSON_CONFIRM_S of steady sightings, and not again
for PERSON_COOLDOWN_S after a follow ended (a face or a voice still count at once).

On 2026-10-08 the log showed the look-around sweeping every minute for hours with the person in the room (195 a day): the camera saw their body now and then but not their face, and each sighting restarted
the 10-minute "away" window. So a person seen in the last PRESENT_S means they're here: no look-around
(the person follow and a voice still work). When they really is away it looks again after
RESCAN_AFTER_S (1, 2, 4 minutes), then stops until their face is seen again, and it sweeps at
scan_rate (25 degrees a second, about 9 s a look-around instead of 5).
"""

from __future__ import annotations

import os
import math
import logging
from typing import Optional
from dataclasses import dataclass, field

ENABLED = os.environ.get("ANDY_SEEK", "on").lower() != "off"
SEEK_WEIGHT = 0.01   # keeps face detection running while the app steers the head
HOME_TOLERANCE = math.radians(4)   # close enough to the centre to hand back to tracking
PERSON_CONFIRM_S = 1.5             # steady sightings before following a person (no flicker)
PERSON_GAP_S = 1.6                 # a longer gap between sightings starts the count again
PERSON_COOLDOWN_S = 20.0           # after a follow ends, no new person follow for this long
# Looking up for a face above the frame (2026-10-06, Andy sat low). Off since 2026-10-08: at the person's
# head height a missing face means they're side-on, not above, and Andy tilted up 28 degrees for nothing.
LOOK_UP = math.radians(float(os.environ.get("ANDY_SEEK_LOOK_UP_DEG", "0")))
PRESENT_S = 30.0                   # a person seen this recently is here: don't look around for them
# A "person" in one place, followed three times in ten minutes without a face ever showing, is not followed there for
# ten minutes, or until a face is seen. On 2026-10-28, with nobody home, a box at the edge of the view that never moved
# (a coat or a lamp) scored 0.48 to 0.52 against 0.45 needed, and Andy turned to it about every 25 s all evening.
FACELESS_FOLLOWS = 3
FACELESS_WINDOW_S = 600.0
STILL_IGNORE_S = 600.0
SAME_PLACE = math.radians(8)
# A follow that finds no face in a minute ends, and its direction is set aside at once: facing the still thing, the
# sighting held steady and the follow never ended (2026-10-28, nine minutes on it after the ten-minute pause).
PERSON_NO_FACE_S = 60.0
RESCAN_AFTER_S = (60.0, 120.0, 240.0)   # while they're away, look again after these waits, then stop


VOICE_HOLD_S = 1.5   # keep the last voiced direction through short pauses between words
SECOND_VOICE = os.environ.get("ANDY_TURN_TO_SPEAKER", "on").lower() not in ("off", "0", "false", "no")
SECOND_VOICE_DEG = 40.0      # a voice this far from the face Andy follows is someone else
SECOND_VOICE_S = 0.6         # ... heard for this long (one word is not a turn)
SECOND_COOLDOWN_S = 8.0      # at most one such turn in this long
IGNORE_S = 60.0              # a direction with nobody there (the TV) is not turned to again for this long


def voiced_angle(reading, held: Optional[tuple], now: float) -> tuple:
    """(angle or None, new held). The mic array reports (angle, speech_detected); without speech
    its angle is just the front (pi/2), which made seek think the voice was ahead (2026-10-06).
    Use voiced readings only, and keep the last one for VOICE_HOLD_S."""
    if reading and len(reading) > 1 and reading[1]:
        return float(reading[0]), (float(reading[0]), now)
    if held and now - held[1] <= VOICE_HOLD_S:
        return held[0], held
    return None, held


def voice_yaw(doa_angle: float) -> float:
    """Head-relative yaw of a voice from the mic array's angle (0 = left, pi/2 = front, pi = right;
    Pollen's examples/sound_doa.py). Positive yaw turns left."""
    return math.pi / 2 - doa_angle


@dataclass
class Decision:
    head_yaw: Optional[float] = None      # world yaw to steer the head to; None = leave the pose alone
    head_up: float = 0.0                  # extra upward tilt, radians (looking up for a face)
    weight: Optional[float] = None        # new tracking weight to request; None = no change


@dataclass
class Seek:
    lost_after: float = 3.0               # seconds without a face before seeking
    rate: float = math.radians(45)        # head turn speed toward a voice or home, per second
    scan_rate: float = math.radians(25)   # a slower sweep when looking around (2026-10-08)
    clamp: float = math.radians(150)      # furthest world yaw to look
    turn_hold: float = 3.0                # seconds to wait facing the voice before giving up
    scan_points: tuple = (math.radians(60), math.radians(-60), 0.0)
    state: str = "FOLLOW"
    _face_seen_at: Optional[float] = None
    _last_t: Optional[float] = None
    _cmd: float = 0.0                     # commanded head world yaw while seeking
    _goal: float = 0.0
    _arrived_at: Optional[float] = None
    _scan_index: int = 0
    _scanned_since_face: bool = False
    _heard_from: Optional[float] = None   # last voice yaw used, to avoid re-triggering on it
    _tracking_since: Optional[float] = None
    _woke_scan_done: bool = False         # one look-around after waking, before any face was seen
    person_rate: float = math.radians(60) # following a walking person
    person_lost_s: float = 3.0            # no person for this long: search (detections flicker up close)
    up_max: float = LOOK_UP                # how far to look up for a face above the frame
    up_rate: float = math.radians(15)
    _up: float = 0.0
    rescan_after: tuple = RESCAN_AFTER_S  # while they're away, look around again after these waits
    rescan_for: float = 600.0             # ... and only this long after they were last seen
    _rescans: int = 0                     # look-arounds since their face was last seen
    _person_seen_at: Optional[float] = None
    _person_streak_since: Optional[float] = None
    _person_cooldown_until: float = -1e18
    _speaking_before: bool = False
    _rested_at: Optional[float] = None
    _second_since: Optional[float] = None     # when a second voice started being heard
    _second_yaw: float = 0.0                  # its world yaw
    _second_cooldown_until: float = -1e18
    _for_voice: bool = False                  # the current TURN is toward a second speaker
    _return_to: float = 0.0                   # where the first person was, to go back if nobody is there
    _home_to: float = 0.0                     # where HOME goes (the centre, or back to the first person)
    _ignored: list = field(default_factory=list)   # (world yaw, until): directions with nobody there
    _follow_since: Optional[float] = None     # when the current person follow began
    _follow_yaw: float = 0.0                  # its world yaw
    _faceless: list = field(default_factory=list)  # (time, world yaw) of follows that never found a face
    _still: list = field(default_factory=list)     # (world yaw, until): a "person" there never had a face
    log: list = field(default_factory=list)

    def _start(self, state: str, goal: float, head_world_yaw: float) -> Decision:
        self.state, self._goal, self._arrived_at = state, max(-self.clamp, min(self.clamp, goal)), None
        if state == "PERSON":
            self._follow_since, self._follow_yaw = self._last_t, self._goal
        self._cmd = head_world_yaw
        self.log.append(state)
        return Decision(head_yaw=self._cmd, weight=SEEK_WEIGHT)

    def _stop(self, state: str) -> Decision:
        self.state = state
        self.log.append(state)
        self._for_voice, self._home_to = False, 0.0
        if state == "REST":
            self._rested_at = self._last_t
        return Decision(weight=1.0)

    def _note_faceless(self) -> None:
        """A person follow ended: if no face was seen during it, remember where; three there in ten minutes and that
        direction is still, not a person."""
        now = self._last_t or 0.0
        if self._follow_since is None or (self._face_seen_at is not None and self._face_seen_at >= self._follow_since):
            self._follow_since = None
            return
        yaw, self._follow_since = self._follow_yaw, None
        self._faceless = [(t, y) for t, y in self._faceless if now - t < FACELESS_WINDOW_S] + [(now, yaw)]
        if sum(abs(y - yaw) < SAME_PLACE for _, y in self._faceless) >= FACELESS_FOLLOWS:
            self._set_still(yaw, now, f"no face after {FACELESS_FOLLOWS} follows")

    def _set_still(self, yaw: float, now: float, why: str) -> None:
        self._still = [(y, until) for y, until in self._still if until > now] + [(yaw, now + STILL_IGNORE_S)]
        self._faceless = [(t, y) for t, y in self._faceless if abs(y - yaw) >= SAME_PLACE]
        self.log.append("STILL")
        logging.getLogger("andy.body").info("seek: %s toward %.0f degrees; left alone for %.0f minutes",
                                            why, math.degrees(yaw), STILL_IGNORE_S / 60)

    def _is_still(self, world_yaw: float, now: float) -> bool:
        return any(until > now and abs(world_yaw - y) < SAME_PLACE for y, until in self._still)

    def _second_voice(self, now: float, face: bool, head_world_yaw: float, user_speaking: bool, robot_speaking: bool,
                      doa_angle: Optional[float]) -> Optional[Decision]:
        """Turn to a second speaker: someone else talking well to the side while Andy follows a face."""
        if not (SECOND_VOICE and face and self.state == "FOLLOW" and user_speaking and not robot_speaking
                and doa_angle is not None):
            self._second_since = None
            return None
        voice = voice_yaw(doa_angle)
        world = head_world_yaw + voice
        self._ignored = [(y, t) for y, t in self._ignored if t > now]
        if abs(voice) < math.radians(SECOND_VOICE_DEG) or any(abs(world - y) < math.radians(20) for y, _ in self._ignored):
            self._second_since = None
            return None
        if self._second_since is None or abs(world - self._second_yaw) > math.radians(20):
            self._second_since, self._second_yaw = now, world
            return None
        if now - self._second_since < SECOND_VOICE_S or now < self._second_cooldown_until:
            return None
        self._second_since, self._second_cooldown_until = None, now + SECOND_COOLDOWN_S
        self._for_voice, self._return_to, self._heard_from = True, head_world_yaw, voice
        decision = self._start("TURN", world, head_world_yaw)
        self.log[-1] = "TURN"
        return decision

    def stand_down(self) -> None:
        """A search has the head (body.hold): drop the turn or follow under way, as when tracking is off. Frozen, it
        resumed after the search and snapped the head toward a voice from before it (2026-10-28 review)."""
        self.state, self._for_voice, self._home_to, self._arrived_at = "FOLLOW", False, 0.0, None
        self._second_since, self._tracking_since = None, None

    def _rest(self) -> Decision:
        """The search ended empty: bring the head home gently first (HOME), then REST."""
        return self._home()

    def _home(self) -> Decision:
        if self.state == "PERSON" or "PERSON" in self.log[-3:]:
            self._person_cooldown_until = (self._last_t or 0.0) + PERSON_COOLDOWN_S
            self._note_faceless()
        self.state, self._goal, self._arrived_at = "HOME", 0.0, None
        self.log.append("HOME")
        return Decision(head_yaw=self._cmd, head_up=self._up)

    def step(self, now: float, *, tracking: bool, face: bool, head_world_yaw: Optional[float],
             user_speaking: bool, robot_speaking: bool, move_playing: bool,
             doa_angle: Optional[float], person_yaw: Optional[float] = None,
             person_top: Optional[float] = None) -> Decision:
        dt = 0.0 if self._last_t is None else min(max(now - self._last_t, 0.0), 0.2)
        self._last_t = now
        stopped_speaking = self._speaking_before and not robot_speaking
        self._speaking_before = robot_speaking
        if face:
            self._face_seen_at = now
            self._scanned_since_face = False
            self._heard_from = None
            self._up = 0.0
            self._rescans = 0
            self._faceless, self._still = [], []          # someone is here: every direction may be a person again
        if person_yaw is not None and head_world_yaw is not None and self._is_still(head_world_yaw + person_yaw, now):
            person_yaw = person_top = None                # the still thing that looks like a person: not them
        if person_yaw is not None:
            if self._person_seen_at is None or now - self._person_seen_at > PERSON_GAP_S:
                self._person_streak_since = now
            self._person_seen_at = now
        seeking = self.state in ("TURN", "SCAN", "PERSON", "HOME")

        # Stand down whenever the normal behaviour should own the head. With tracking switched
        # off, don't ask for any weight: that would switch it back on.
        if not tracking:
            self.state = "FOLLOW"
            self._tracking_since = None
            return Decision()
        if self._tracking_since is None:
            self._tracking_since = now
        if move_playing or head_world_yaw is None:
            return self._stop("FOLLOW") if seeking else Decision()
        turned = self._second_voice(now, face, head_world_yaw, user_speaking, robot_speaking, doa_angle)
        if turned is not None:
            return turned
        # Turning to a second speaker, the first person's face is still in view at the start: only a face once
        # the head has arrived ends the turn (it is then the new person's).
        turning_away = self.state == "TURN" and self._for_voice and self._arrived_at is None
        if face and not turning_away:
            return self._stop("FOLLOW") if seeking else Decision()
        if robot_speaking and not (self.state == "TURN" and self._for_voice):   # answering the new speaker: keep turning
            # Not a snap back to the centre mid-search: bring the head home, then hand over.
            if not seeking:
                return Decision()
            if self.state != "HOME":
                return self._home()

        lost = self._face_seen_at is None or now - self._face_seen_at >= self.lost_after
        voice = voice_yaw(doa_angle) if (user_speaking and doa_angle is not None) else None
        new_voice = voice is not None and (self._heard_from is None or abs(voice - self._heard_from) > math.radians(20))

        if lost and new_voice and abs(voice) > math.radians(15) and not robot_speaking:
            self._heard_from = voice
            return self._start("TURN", head_world_yaw + voice, head_world_yaw)

        # A minute following with no face: a still thing, not a person (PERSON_NO_FACE_S).
        if (self.state == "PERSON" and self._follow_since is not None and now - self._follow_since >= PERSON_NO_FACE_S
                and (self._face_seen_at is None or self._face_seen_at < self._follow_since)):
            yaw, self._follow_since = self._follow_yaw, None
            self._set_still(yaw, now, "no face in a minute of following")
            return self._rest()
        # A person in view but no face: follow them (2026-10-06, "track me when I step away"),
        # once the sightings are steady and not right after a follow ended (2026-10-07).
        steady = (self._person_streak_since is not None and now - self._person_streak_since >= PERSON_CONFIRM_S
                  and now >= self._person_cooldown_until)
        if person_yaw is not None and self.state not in ("TURN", "HOME") and (self.state == "PERSON" or steady):
            goal = max(-self.clamp, min(self.clamp, head_world_yaw + person_yaw))
            if self.state != "PERSON":
                return self._start("PERSON", goal, head_world_yaw)
            if abs(person_yaw) > math.radians(4):              # deadband: don't jitter on a still person
                self._goal = goal
        if self.state == "PERSON":
            if self._person_seen_at is None or now - self._person_seen_at >= self.person_lost_s:
                if not self._scanned_since_face:
                    self._scanned_since_face = True
                    self._scan_index = 0
                    self.state, self._goal, self._arrived_at = "SCAN", self.scan_points[0], None
                    self.log.append("SCAN")
                else:
                    return self._rest()
            self._cmd += max(-self.person_rate * dt, min(self.person_rate * dt, self._goal - self._cmd))
            # Close up, the person fills the frame and the face is above it (2026-10-06, "I'm next
            # to them and they're searching"): look up until the face comes into view.
            if person_top is not None and person_top < 0.04:
                self._up = min(self.up_max, self._up + self.up_rate * dt)
            elif person_top is not None and person_top > 0.25:
                self._up = max(0.0, self._up - self.up_rate * dt)
            if self.state == "PERSON":
                return Decision(head_yaw=self._cmd, head_up=self._up)

        # Someone in view lately (no face: side on, too close, turned away) means they're here: no sweeping.
        here = self._person_seen_at is not None and now - self._person_seen_at < PRESENT_S
        # Away: look around again after 1, 2 and 4 minutes, then wait for their face.
        last_seen = max(t for t in (self._face_seen_at, self._person_seen_at, -1e18) if t is not None)
        if (self.state == "REST" and self._rested_at is not None and not here
                and self._rescans < len(self.rescan_after)
                and now - max(self._rested_at, self._person_seen_at or -1e18) >= self.rescan_after[self._rescans]
                and now - last_seen <= self.rescan_for):
            self._rescans += 1
            self._scan_index = 0
            return self._start("SCAN", self.scan_points[0], head_world_yaw)
        if (lost and not here and self.state in ("FOLLOW", "REST") and not self._scanned_since_face
                and self._face_seen_at is not None):
            self._scanned_since_face = True
            self._scan_index = 0
            return self._start("SCAN", self.scan_points[0], head_world_yaw)
        # Just woke (or tracking just came on) and nobody in view yet: look around once
        # (2026-10-06: they woke facing away and never searched, having never "lost" a face).
        if (self._face_seen_at is None and not self._woke_scan_done and not here and self.state in ("FOLLOW", "REST")
                and now - self._tracking_since >= self.lost_after):
            self._woke_scan_done = True
            self._scanned_since_face = True
            self._scan_index = 0
            return self._start("SCAN", self.scan_points[0], head_world_yaw)
        if not seeking:
            return Decision()

        if self.state == "HOME":
            step = self.rate * dt
            self._cmd += max(-step, min(step, self._home_to - self._cmd))
            self._up = max(0.0, self._up - self.up_rate * dt)
            if abs(self._cmd - self._home_to) <= HOME_TOLERANCE and self._up <= math.radians(2):
                return self._stop("REST")
            # Andy just stopped talking: Pollen's set_speaking(False) puts tracking back to full weight,
            # which snaps the head to the centre (review, 2026-10-07). Take it back at once.
            if stopped_speaking:
                return Decision(head_yaw=self._cmd, head_up=self._up, weight=SEEK_WEIGHT)
            return Decision(head_yaw=self._cmd, head_up=self._up)

        step = (self.scan_rate if self.state == "SCAN" else self.rate) * dt
        self._cmd += max(-step, min(step, self._goal - self._cmd))
        arrived = abs(self._goal - self._cmd) < 1e-3
        if arrived and self._arrived_at is None:
            self._arrived_at = now
        if self.state == "TURN" and arrived and self._for_voice and now - self._arrived_at >= self.turn_hold:
            # Nobody there (the TV, a radio): back to the first person, and leave that direction alone a while.
            self._ignored.append((self._goal, now + IGNORE_S))
            self.state, self._home_to, self._arrived_at = "HOME", self._return_to, None
            self._for_voice = False
            self.log.append("HOME")
            return Decision(head_yaw=self._cmd, head_up=self._up)
        if self.state == "TURN" and arrived and now - self._arrived_at >= self.turn_hold:
            if not self._scanned_since_face:
                self._scanned_since_face = True
                self._scan_index = 0
                self.state, self._goal, self._arrived_at = "SCAN", self.scan_points[0], None
                self.log.append("SCAN")
            else:
                return self._rest()
        elif self.state == "SCAN" and arrived:
            self._scan_index += 1
            if self._scan_index >= len(self.scan_points):
                return self._rest()
            self._goal, self._arrived_at = self.scan_points[self._scan_index], None
        self._up = max(0.0, self._up - self.up_rate * dt)        # level out while scanning or turning
        return Decision(head_yaw=self._cmd, head_up=self._up)
