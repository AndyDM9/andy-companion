"""Finding the person again: turn toward a voice, or look around once, then hand back to tracking."""

import math

import numpy as np

from andy_companion.body import seek
from andy_companion.body.seek import SEEK_WEIGHT, Seek, voice_yaw

DEG = math.radians


def tick(s, t, **kw):
    args = dict(tracking=True, face=False, head_world_yaw=0.0, user_speaking=False,
                robot_speaking=False, move_playing=False, doa_angle=None)
    args.update(kw)
    return s.step(t, **args)


def run(s, t0, seconds, dt=0.05, **kw):
    t, out = t0, []
    while t < t0 + seconds:
        out.append(tick(s, t, **kw))
        t += dt
    return out, t


def test_voice_direction_convention():
    assert math.isclose(voice_yaw(0.0), DEG(90))          # left
    assert math.isclose(voice_yaw(math.pi / 2), 0.0)      # front
    assert math.isclose(voice_yaw(math.pi), DEG(-90))     # right


def test_turns_toward_a_voice_out_of_view_then_hands_back_on_a_face():
    s = Seek()
    _, t = run(s, 0, 1, face=True)                        # seen, then lost
    _, t = run(s, t, 3.5)
    first = tick(s, t, user_speaking=True, doa_angle=DEG(30))   # voice ~60° to the left
    assert s.state == "TURN" and first.weight == SEEK_WEIGHT
    out, t = run(s, t + 0.05, 1.0)
    assert DEG(35) < out[-1].head_yaw <= DEG(45) * 1.1, "turning left at about 45°/s"
    back = tick(s, t, face=True)
    assert s.state == "FOLLOW" and back.weight == 1.0


def test_one_look_around_after_losing_someone_then_rest():
    s = Seek()
    _, t = run(s, 0, 1, face=True)
    out, t = run(s, t, 15)
    assert s.log.count("SCAN") == 1 and s.state == "REST"
    assert out[-1].weight == 1.0 or any(d.weight == 1.0 for d in out), "normal tracking restored"
    out, t = run(s, t, 10)
    assert s.log.count("SCAN") == 1, "no endless scanning"


def test_nobody_ever_seen_means_one_look_around_not_a_loop():
    """Changed 2026-10-06 at the person's request: on waking they look around once."""
    s = Seek()
    run(s, 0, 30)
    assert s.log.count("SCAN") == 1 and s.state == "REST"


def test_small_voice_angles_dont_trigger_a_turn():
    s = Seek()
    _, t = run(s, 0, 1, face=True)
    _, t = run(s, t, 3.5)
    s.log.clear()
    tick(s, t, user_speaking=True, doa_angle=DEG(85))     # 5° off centre
    assert "TURN" not in s.log


def test_when_andy_speaks_mid_search_the_head_comes_home_gently_then_hands_back():
    """2026-10-07: standing down at full weight snapped the head to the centre; Andy fell off the computer."""
    s = Seek()
    _, t = run(s, 0, 1, face=True)
    _, t = run(s, t, 3.5)
    assert s.state == "SCAN"
    d = tick(s, t, robot_speaking=True)
    assert s.state == "HOME" and d.weight is None, "still steering, no hand-over yet"
    out, t = run(s, t + 0.05, 5, robot_speaking=True)
    yaws = [d.head_yaw for d in out if d.head_yaw is not None]
    assert all(abs(b - a) <= DEG(45) * 0.05 + 1e-9 for a, b in zip(yaws, yaws[1:])), "no jumps"
    assert s.state == "REST" and any(d.weight == 1.0 for d in out)
    assert abs(yaws[-1]) <= seek.HOME_TOLERANCE + DEG(45) * 0.05, "handed back within one step of the centre"


def test_never_switches_tracking_back_on():
    s = Seek()
    _, t = run(s, 0, 1, face=True)
    _, t = run(s, t, 3.5)
    d = tick(s, t, tracking=False)
    assert s.state == "FOLLOW" and d.weight is None


def test_launcher_steers_the_head_while_seeking():

    from andy_companion.body import attach as rj

    class Face:
        detected = False

    class Media:
        @staticmethod
        def get_DoA():
            return (DEG(0), True)                         # hard left

    class Robot:
        media = Media()
        weights = []

        def get_tracked_face(self, wait=False):
            return Face()

        def start_head_tracking(self, weight):
            self.weights.append(weight)

    class Manager:
        _is_listening = True
        _is_speaking = False
        current_robot = Robot()

    m = Manager()
    m._andy_seek = Seek()
    m._andy_seek._face_seen_at = -10.0                  # lost long ago
    head = np.eye(4)
    for i in range(11):                                   # 1 s of control-loop ticks
        out = rj.seek_step(m, i * 0.1, head, True, 0.0, False)
    from andy_companion.body.body_follow import head_yaw
    assert m.current_robot.weights == [SEEK_WEIGHT]
    assert head_yaw(out) > DEG(30), "head steered left toward the voice"



def test_on_waking_with_nobody_in_view_he_looks_around_once():
    s = seek.Seek()
    common = dict(tracking=True, face=False, head_world_yaw=0.0, user_speaking=False, robot_speaking=False,
                  move_playing=False, doa_angle=None)
    assert s.step(0.0, **common).head_yaw is None
    assert s.step(2.0, **common).head_yaw is None, "give the face tracker a moment first"
    d = s.step(3.1, **common)
    assert s.state == "SCAN" and d.weight == seek.SEEK_WEIGHT
    t = 3.1
    while s.state in ("SCAN", "HOME") and t < 60:
        t += 0.1
        s.step(t, **common)
    assert s.state == "REST"
    for _ in range(50):
        t += 0.1
        s.step(t, **common)
    assert s.state == "REST", "only once, not over and over"


def test_voice_direction_counts_only_when_speech_is_detected():
    import math
    assert seek.voiced_angle((math.pi / 2, False), None, 0.0) == (None, None), "silence reports the front"
    angle, held = seek.voiced_angle((0.4, True), None, 1.0)
    assert angle == 0.4 and held == (0.4, 1.0)
    assert seek.voiced_angle((math.pi / 2, False), held, 2.0)[0] == 0.4, "held through a short pause"
    assert seek.voiced_angle((math.pi / 2, False), held, 3.0)[0] is None, "not for ever"


def _common(**kw):
    base = dict(tracking=True, face=False, head_world_yaw=0.0, user_speaking=False, robot_speaking=False,
                move_playing=False, doa_angle=None, person_yaw=None)
    base.update(kw)
    return base


def test_a_person_without_a_face_is_followed_and_handed_back_to_the_face():
    import math
    s = seek.Seek()
    s.step(0.0, **_common(face=True))
    t, yaw = 0.0, 0.0
    for _ in range(40):                                   # they turn away and walk to the robot's left
        t += 0.1
        d = s.step(t, **_common(head_world_yaw=yaw, person_yaw=math.radians(30) - yaw))
        if d.head_yaw is not None:
            yaw = d.head_yaw
    assert s.state == "PERSON" and abs(yaw - math.radians(30)) < math.radians(2), "turned toward them"
    d = s.step(t + 0.1, **_common(face=True, head_world_yaw=yaw))
    assert s.state == "FOLLOW" and d.weight == 1.0, "their face again: Pollen's tracking takes over"


def test_a_person_lost_leads_to_a_look_around_then_rest_then_periodic_looks():
    import math
    s = seek.Seek()
    s.step(0.0, **_common(face=True))
    t = 0.0
    while t < seek.PERSON_CONFIRM_S + 0.3:                # steady sightings first
        t += 0.1
        s.step(t, **_common(person_yaw=math.radians(20)))
    assert s.state == "PERSON"
    while s.state in ("PERSON", "SCAN", "HOME") and t < 60:
        t += 0.1
        s.step(t, **_common())
    assert s.state == "REST" and "SCAN" in s.log
    rested = t
    while t < rested + seek.PRESENT_S:                    # they were seen just now: they're here, no sweep
        t += 0.5
        s.step(t, **_common())
        assert s.state == "REST"
    while t < rested + s.rescan_after[0] + 3.2 and s.state == "REST":
        t += 0.5
        s.step(t, **_common())
    assert s.state == "SCAN", "looks again a minute or so later"
    s2 = seek.Seek(rescan_for=30.0)
    s2.step(0.0, **_common(face=True))
    t = 0.0
    while t < 200:
        t += 0.5
        s2.step(t, **_common())
    assert s2.log.count("SCAN") <= 2, "not for ever once they're been gone a long while"


def test_the_watcher_keeps_following_the_same_person():
    from andy_companion.body import person

    class Fake:
        def __init__(self, boxes):
            self.boxes = boxes
        def detect(self, frame):
            return self.boxes
    left, right = (100, 0, 300, 600, 0.9), (1600, 0, 1900, 900, 0.95)      # right one is bigger
    w = person.PersonWatcher.__new__(person.PersonWatcher)
    w._get_frame, w._intrinsics, w._latest = (lambda: np.zeros((1080, 1920, 3))), (lambda: (1116.0, 960.0)), None
    w.top = None
    w._detector = Fake([left, right])
    first = w.look_once(0.0)
    assert first < 0, "with no history: the biggest, nearest person (on their right)"
    w._latest = (person.bearing(left, 1116.0, 960.0), 0.0)
    assert w.look_once(0.2) > 0, "with history: the same person as before"
    assert w.latest(0.5) is not None and w.latest(5.0) is None



def test_close_up_he_looks_up_for_the_face_above_the_frame():
    import math
    s = seek.Seek(up_max=math.radians(25))           # ANDY_SEEK_LOOK_UP_DEG=25: Andy sitting low
    s.step(0.0, **_common(face=True))
    t, d = 0.0, None
    for _ in range(30):                                   # the person's outline touches the top edge
        t += 0.1
        d = s.step(t, **_common(person_yaw=0.0, person_top=0.0))
    assert s.state == "PERSON" and math.radians(20) < d.head_up <= s.up_max
    for _ in range(30):                                   # the head is in view now (top well inside)
        t += 0.1
        d = s.step(t, **_common(person_yaw=0.0, person_top=0.4))
    assert d.head_up < math.radians(5)
    s.step(t + 0.1, **_common(face=True))
    assert s._up == 0.0


def test_the_person_watch_backs_off_when_nobody_is_around():
    from andy_companion.body import person
    assert person.period((0.0, 100.0), 110.0) == person.PERIOD_S, "following: often"
    assert person.period((0.0, 100.0), 200.0) == person.IDLE_PERIOD_S
    assert person.period((0.0, 100.0), 100.0 + 3600) == person.AWAY_PERIOD_S
    assert person.period(None, 5.0) == person.AWAY_PERIOD_S, "never seen anyone yet"
    assert person.PERIOD_S >= 0.7, "about 1.4 checks a second at most"


def test_a_sighting_stays_fresh_until_the_next_look():
    from andy_companion.body import person
    assert person.FRESH_S > person.PERIOD_S + 0.15, "between two looks they must not seem lost"


def test_a_whole_search_never_jumps_and_hands_back_only_at_the_centre():
    import math
    s = seek.Seek()
    s.step(0.0, **_common(face=True))
    t, cmds, handed = 0.0, [], []
    while t < 40:
        t += 0.05
        d = s.step(t, **_common())
        if d.head_yaw is not None:
            cmds.append(d.head_yaw)
        if d.weight == 1.0:
            handed.append(cmds[-1] if cmds else 0.0)
    assert "SCAN" in s.log and "HOME" in s.log and s.state == "REST"
    assert all(abs(b - a) <= math.radians(45) * 0.05 + 1e-9 for a, b in zip(cmds, cmds[1:]))
    assert handed and all(abs(y) <= seek.HOME_TOLERANCE for y in handed)


def test_a_flickering_person_is_not_followed():
    import math
    s = seek.Seek()
    s.step(0.0, **_common(face=True))
    t = 4.0
    for _ in range(20):                                  # one sighting every 2 s: the fall's pattern
        s.step(t, **_common(person_yaw=math.radians(25)))
        for _ in range(19):
            t += 0.1
            s.step(t, **_common())
        t += 0.1
    assert "PERSON" not in s.log


def test_after_a_follow_ends_he_waits_before_following_again():
    import math
    s = seek.Seek()
    s.step(0.0, **_common(face=True))
    t = 0.0
    while t < 2.0:
        t += 0.1
        s.step(t, **_common(person_yaw=math.radians(20)))
    assert s.state == "PERSON"
    while s.state != "REST" and t < 60:
        t += 0.1
        s.step(t, **_common())
    ended = t
    while t < ended + 5:
        t += 0.1
        s.step(t, **_common(person_yaw=math.radians(20)))
    assert s.state == "REST", "not straight back to following"
    while t < ended + seek.PERSON_COOLDOWN_S + 3:
        t += 0.1
        s.step(t, **_common(person_yaw=math.radians(20)))
    assert s.state == "PERSON", "after the pause, a steady person is followed again"


def test_when_andy_stops_talking_mid_home_the_head_keeps_easing_home():
    """Review, 2026-10-07: Pollen's set_speaking(False) restores full weight, which snapped the head."""
    s = Seek()
    _, t = run(s, 0, 1, face=True)
    _, t = run(s, t, 5.5)                                    # well into the scan: about 60 degrees out
    assert s.state == "SCAN" and s._cmd > DEG(45)
    tick(s, t, robot_speaking=True)
    assert s.state == "HOME"
    run(s, t + 0.05, 0.3, robot_speaking=True)
    d = tick(s, t + 0.4)                                    # they stopped talking, head not home yet
    assert s.state == "HOME" and d.weight == SEEK_WEIGHT, "seek takes the head back on that tick"
    d2 = tick(s, t + 0.45)
    assert d2.weight is None, "once, not every tick"


def _gone(s, t, until, **kw):
    while t < until:
        t += 0.5
        s.step(t, **_common(**kw))
    return t


def test_a_person_glimpsed_now_and_then_stops_the_sweeping():
    """2026-10-08: the camera saw their body every few minutes but not their face; each sighting
    restarted the away window and they swept every minute for hours (195 a day)."""
    s = seek.Seek()
    s.step(0.0, **_common(face=True))
    t = 0.0
    for _ in range(30):                                   # half an hour, a glimpse every minute
        t = _gone(s, t, t + 59.5)
        t += 0.5
        s.step(t, **_common(person_yaw=math.radians(30)))
    assert s.log.count("SCAN") <= 1, "only the first look after their face went"


def test_away_it_looks_again_after_one_two_and_four_minutes_then_stops():
    s = seek.Seek(rescan_for=3600.0)
    s.step(0.0, **_common(face=True))
    t = _gone(s, 0.0, 1800.0)
    assert s.log.count("SCAN") == 1 + len(seek.RESCAN_AFTER_S), "the first look plus three, not one a minute"
    s.step(t + 0.5, **_common(face=True))
    assert s._rescans == 0, "their face again starts the count over"


def test_the_look_around_sweeps_slower_than_a_turn_to_a_voice():
    s = seek.Seek()
    s.step(0.0, **_common(face=True))
    t = 0.0
    while s.state != "SCAN":
        t += 0.05
        s.step(t, **_common())
    start = s._cmd
    t += 1.0
    s.step(t, **_common())
    swept = abs(s._cmd - start)
    assert swept <= s.scan_rate * 1.0 + 1e-6 and s.scan_rate < s.rate


def _follow_until_rest(s, t, yaw, limit=60):
    """A steady sighting at world yaw `yaw` with no face, until the follow ends and Andy rests."""
    while s.state != "PERSON" and t < limit:
        t += 0.1
        s.step(t, **_common(person_yaw=yaw))
    while s.state != "REST" and t < limit:
        t += 0.1
        s.step(t, **_common())
    return t


def test_a_still_thing_that_looks_like_a_person_is_left_alone():
    """2026-10-28, nobody home: a box at the edge of the view that never moved (0.48 to 0.52, with 0.45 needed) and
    Andy turned to it about every 25 s all evening. Three follows there with no face: that direction is left alone,
    a person elsewhere is still followed, and a face makes every direction count again."""
    import math
    s = seek.Seek()
    s.step(0.0, **_common(face=True))
    t = 0.0
    for _ in range(seek.FACELESS_FOLLOWS):
        t = _follow_until_rest(s, t, math.radians(30), limit=t + 120)
        t += seek.PERSON_COOLDOWN_S + 1
    assert "STILL" in s.log
    end = t + 10
    while t < end:
        t += 0.1
        s.step(t, **_common(person_yaw=math.radians(30)))
    assert s.state == "REST", "the still thing is not followed again"
    end = t + 5
    while t < end:
        t += 0.1
        s.step(t, **_common(person_yaw=math.radians(-40)))
    assert s.state == "PERSON", "someone elsewhere still is"
    s.step(t + 0.1, **_common(face=True))
    assert s._still == [] and s._faceless == []


def test_a_person_whose_face_shows_is_never_taken_for_a_still_thing():
    import math
    s = seek.Seek()
    s.step(0.0, **_common(face=True))
    t = 0.0
    for _ in range(seek.FACELESS_FOLLOWS + 1):
        while s.state != "PERSON" and t < 400:
            t += 0.1
            s.step(t, **_common(person_yaw=math.radians(30)))
        t += 0.1
        s.step(t, **_common(face=True))                   # they turn round: a face
        while s.state != "REST" and t < 400:
            t += 0.1
            s.step(t, **_common())
        t += seek.PERSON_COOLDOWN_S + 1
    assert "STILL" not in s.log and s._still == []
