"""Round 8, B47: teach Andy a move by hand. Antennas only; the motors come back on with a move already playing from
where the hand left them; what was taught is trimmed, smoothed and never faster than MAX_RAD_S."""

import asyncio
import math

import numpy as np
import pytest

from andy_companion import gestures


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(gestures, "FILE", tmp_path / "gestures.json")


def wave(n=120, dt=1 / 30, still=10, amp=0.6, hz=1.0):
    pts = []
    for i in range(n):
        t = i * dt
        moving = still <= i < n - still
        a = amp * math.sin(2 * math.pi * hz * (t - still * dt)) if moving else 0.0
        pts.append((t, -0.17 + a, 0.17 - a))
    return pts


def test_a_taught_move_is_trimmed_smoothed_and_never_too_fast():
    gentle = gestures.clean(wave(amp=0.3, hz=0.5))                       # slow enough to play as taught
    assert gentle[0][0] == 0.0 and gentle[-1][0] < 120 / 30             # the still ends cut
    pts = gestures.clean(wave())
    speeds = [max(abs(b[1] - a[1]), abs(b[2] - a[2])) / (b[0] - a[0]) for a, b in zip(pts, pts[1:], strict=False)]
    assert max(speeds) <= gestures.MAX_RAD_S + 1e-6
    fast = gestures.clean(wave(amp=1.5, hz=3.0))                          # flicked: slowed down to the cap
    speeds = [max(abs(b[1] - a[1]), abs(b[2] - a[2])) / (b[0] - a[0]) for a, b in zip(fast, fast[1:], strict=False)]
    assert max(speeds) <= gestures.MAX_RAD_S + 1e-6
    assert gestures.clean(wave(amp=0.02)) is None and gestures.clean([(0, 0, 0)] * 30) is None   # nothing taught


def test_moves_are_kept_by_name_found_by_their_words_and_forgotten(tmp_path):
    gestures.keep("Sofia's wave", gestures.clean(wave()))
    assert oct((tmp_path / "gestures.json").stat().st_mode & 0o777) == "0o600"
    assert gestures.names() == ["Sofia's wave"] and gestures.find_name("the wave") == "Sofia's wave"
    assert gestures.find_name("sofia's WAVE") == "Sofia's wave" and gestures.find_name("a dance") is None
    assert gestures.forget("Sofia's wave") and gestures.names() == []


def test_playing_eases_in_from_where_the_antennas_are_and_back_with_the_head_still():
    pts = gestures.clean(wave())
    head = np.eye(4)
    play = gestures.Play(pts, head, (0.0, 0.0))
    h, a, body = play.evaluate(0.0)
    assert np.allclose(h, head) and np.allclose(a, [0.0, 0.0]) and body == 0.0
    assert np.allclose(play.evaluate(gestures.EASE_S)[1], pts[0][1:])
    assert np.allclose(play.evaluate(play.duration)[1], [0.0, 0.0])
    home = gestures.Home(head, (0.5, -0.5), (-0.17, 0.17))
    assert np.allclose(home.evaluate(0.0)[1], [0.5, -0.5]) and np.allclose(home.evaluate(gestures.HOME_S)[1], [-0.17, 0.17])


class Robot:
    def __init__(self, path):
        self.path, self.t, self.log = path, 0.0, []

    def get_current_head_pose(self):
        return np.eye(4)

    def get_current_joint_positions(self):
        i = min(int(self.t * 30), len(self.path) - 1)
        return [0.0] * 7, [self.path[i][1], self.path[i][2]]

    def disable_motors(self, ids):
        self.log.append(("off", tuple(ids)))

    def enable_motors(self, ids):
        self.log.append(("on", tuple(ids)))


class Manager:
    def __init__(self, robot):
        self.robot, self.moves = robot, []

    def queue_move(self, move):
        self.robot.log.append(("move", type(move).__name__))
        self.moves.append(move)


def run_learn(path):
    robot = Robot(path)
    manager = Manager(robot)

    async def fake_sleep(seconds):
        robot.t += seconds

    out = asyncio.run(gestures.learn("Sofia's wave", robot, manager, sleep=fake_sleep, clock=lambda: robot.t,
                                     queue=lambda m: m))
    return out, robot, manager


def test_learning_turns_only_the_antennas_soft_and_brings_them_home_before_the_motors():
    out, robot, manager = run_learn(wave(n=200))
    assert out["learned"] and out["name"] == "Sofia's wave" and gestures.names() == ["Sofia's wave"]
    assert robot.log[0] == ("off", ("left_antenna", "right_antenna"))        # the head's motors never go off
    on = robot.log.index(("on", ("left_antenna", "right_antenna")))
    assert robot.log[on - 1] == ("move", "Home")                              # the move home is playing first
    assert isinstance(manager.moves[0], gestures.Home) and isinstance(manager.moves[-1], gestures.Play)   # then shown
    home = manager.moves[0]
    path = wave(n=200)
    left = path[int(gestures.RECORD_S * 30) - 1]                              # where the hand left them, at the end
    assert np.allclose(home.evaluate(0.0)[1], left[1:], atol=0.1)


def test_no_movement_keeps_nothing_and_the_motors_still_come_back():
    out, robot, manager = run_learn([(0.0, -0.17, 0.17)] * 200)
    assert out == {"learned": False} and gestures.names() == []
    assert ("on", ("left_antenna", "right_antenna")) in robot.log and len(manager.moves) == 1
