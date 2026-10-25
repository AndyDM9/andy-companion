"""Andy keeps following the face while they talks; a gesture mid-reply still gets the head."""

from types import SimpleNamespace

from andy_companion.body import gaze, seek


class Robot:
    def __init__(self):
        self.weights = []

    def start_head_tracking(self, weight=1.0):
        self.weights.append(weight)

    def get_current_head_pose(self):
        return "pose-now"


def manager(speaking=True, tracking=True, anchor="pollen-anchor"):
    return SimpleNamespace(_head_tracking=tracking, _is_speaking=speaking, _track_anchor=anchor,
                           current_robot=Robot(), state=SimpleNamespace(current_move=None))


def test_while_talking_tracking_keeps_the_head_instead_of_pollens_pause():
    m = manager()
    gaze.speaking_step(m, face=True, move_playing=False)
    assert m.current_robot.weights == [1.0] and m._track_anchor is None
    gaze.speaking_step(m, face=True, move_playing=False)
    assert m.current_robot.weights == [1.0], "once, not every tick"


def test_a_gesture_mid_reply_holds_the_look_then_tracking_takes_back():
    m = manager()
    gaze.speaking_step(m, face=True, move_playing=False)
    gaze.speaking_step(m, face=True, move_playing=True)
    assert m.current_robot.weights == [1.0, 0.0] and m._track_anchor == "pose-now", "the emotion shows"
    gaze.speaking_step(m, face=True, move_playing=True)
    assert m.current_robot.weights == [1.0, 0.0]
    gaze.speaking_step(m, face=True, move_playing=False)
    assert m.current_robot.weights == [1.0, 0.0, 1.0] and m._track_anchor is None


def test_hands_off_when_silent_tracking_off_or_seeking():
    for m in (manager(speaking=False), manager(tracking=False)):
        gaze.speaking_step(m, face=True, move_playing=False)
        assert m.current_robot.weights == [] and m._track_anchor == "pollen-anchor"
    m = manager()
    m._andy_seek = seek.Seek(state="HOME")
    gaze.speaking_step(m, face=False, move_playing=False)
    assert m.current_robot.weights == [], "seek eases the head home first, then hands back"


def test_off_switch_restores_pollens_pause(monkeypatch):
    monkeypatch.setattr(gaze, "ENABLED", False)
    m = manager()
    gaze.speaking_step(m, face=True, move_playing=False)
    assert m.current_robot.weights == [] and m._track_anchor == "pollen-anchor"


def test_the_launcher_calls_it_each_tick():
    from pathlib import Path

    text = (Path(__file__).resolve().parents[2] / "src" / "andy_companion" / "body" / "attach.py").read_text()
    assert "gaze.speaking_step(self" in text


def _pose(roll, pitch, yaw):
    import math
    import numpy as np
    r, p, y = (math.radians(a) for a in (roll, pitch, yaw))
    Rz = np.array([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]])
    Ry = np.array([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]])
    Rx = np.array([[1, 0, 0], [0, math.cos(r), -math.sin(r)], [0, math.sin(r), math.cos(r)]])
    out = np.eye(4)
    out[:3, :3] = Rz @ Ry @ Rx
    out[:3, 3] = (0.001, 0.002, 0.01)
    return out


def _angles(pose):
    import math
    R = pose[:3, :3]
    return (math.degrees(math.atan2(R[2, 1], R[2, 2])), math.degrees(math.asin(-R[2, 0])),
            math.degrees(math.atan2(R[1, 0], R[0, 0])))


def test_pollens_look_up_is_softened_below_ten_degrees():
    """2026-10-08: thoughtful1, attentive1 and others tilt up 22.5 degrees: at head height, the ceiling."""
    import math
    import numpy as np
    limit = math.radians(10)
    roll, pitch, yaw = _angles(gaze.soften_look_up(_pose(3, -22.5, 30), limit))
    assert -10 < pitch < -9, "still a look up, a small one"
    assert abs(roll - 3) < 1e-6 and abs(yaw - 30) < 1e-6, "turning and tilting untouched"
    _, small, _ = _angles(gaze.soften_look_up(_pose(0, -3, 0), limit))
    assert abs(small + 3) < 0.1, "small nods keep their size"
    down = _pose(0, 15, -20)
    assert np.allclose(gaze.soften_look_up(down, limit), down), "looking down untouched"
    assert np.allclose(gaze.soften_look_up(_pose(0, -22.5, 0), limit)[:3, 3], (0.001, 0.002, 0.01))


def test_the_person_follow_no_longer_looks_up_at_head_height():
    assert seek.Seek().up_max == 0.0


def test_following_a_face_may_look_up_and_only_a_playing_move_is_capped():
    """The founder stood up and Andy couldn't look up at them (2026-10-25): tracking is never capped."""
    import math
    import numpy as np
    up = _pose(0, -25, 0)
    limit = math.radians(10)
    assert np.allclose(gaze.look_up_cap(up, False, limit), up)                       # following a face
    _, pitch, _ = _angles(gaze.look_up_cap(up, True, limit))                         # an emotion playing
    assert -10.0 - 1e-6 <= pitch < 0
