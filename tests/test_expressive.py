import math

import pytest

from andy_companion.body import expressive, glance


def pose(yaw_deg=0.0, pitch_deg=0.0):
    return glance._pose(0.0, math.radians(pitch_deg), math.radians(yaw_deg), [0.0, 0.0, 0.01])


class Robot:
    def get_current_head_pose(self):
        return pose(yaw_deg=-10)


class Manager:
    def __init__(self):
        self.current_robot = Robot()
        self.moves = []

    def queue_move(self, move):
        self.moves.append(move)


@pytest.fixture(autouse=True)
def reset():
    expressive._question["at"] = None


def make(left=lambda: 0.0):
    t = [0.0]
    body = expressive.Expressive(clock=lambda: t[0], voice_left=left)
    return body, t


def tick(body, m, **kw):
    args = dict(thinking=False, listening=False, move_playing=False, tracking=True, queueable=lambda g: g)
    args.update(kw)
    return body.step(m, (-0.17, 0.17), **args)


def test_a_quick_answer_never_looks_away_a_slow_one_does_once():
    body, t = make()
    m = Manager()
    assert tick(body, m, thinking=True) is None
    t[0] = 0.6
    assert tick(body, m, thinking=True) is None                  # Lightning's usual reply: nothing
    t[0] = 0.9
    assert tick(body, m, thinking=True) == "think"
    t[0] = 2.0
    assert tick(body, m, thinking=True) is None                  # once per turn
    g = m.moves[0]
    roll, pitch, yaw = glance._rpy(g.start)
    held = g.evaluate(g.turn_s + 0.1)[0]
    _, p2, y2 = glance._rpy(held)
    assert math.degrees(y2 - yaw) == pytest.approx(expressive.THINK_YAW_DEG)   # to the side
    assert math.degrees(p2 - pitch) == pytest.approx(-expressive.THINK_UP_DEG) # and a little up
    assert g.perk == 0.0 and g.evaluate(g.duration)[0] == pytest.approx(g.start)   # back to the person


def test_never_while_they_speak_or_another_move_plays_and_not_too_often():
    body, t = make()
    m = Manager()
    tick(body, m, thinking=True)
    t[0] = 1.0
    assert tick(body, m, thinking=True, listening=True) is None
    assert tick(body, m, thinking=True, move_playing=True) is None
    assert tick(body, m, thinking=True, tracking=False) is None
    assert tick(body, m, thinking=True) == "think"
    tick(body, m, thinking=False)                                  # the answer started; a new turn
    t[0] = 5.0
    tick(body, m, thinking=True)
    t[0] = 6.0
    assert tick(body, m, thinking=True) is None                    # within THINK_EVERY_S
    t[0] = 30.0
    tick(body, m, thinking=False)
    tick(body, m, thinking=True)
    t[0] = 31.0
    assert tick(body, m, thinking=True) == "think"
    yaws = [math.degrees(glance._rpy(g.evaluate(g.turn_s + 0.1)[0])[2] - glance._rpy(g.start)[2]) for g in m.moves]
    assert yaws[0] == pytest.approx(-yaws[1])                      # the other side next time


def test_a_question_tilts_the_head_as_its_last_words_play():
    left = [3.0]
    body, t = make(left=lambda: left[0])
    m = Manager()
    expressive.heard_reply("I'm glad. What was the bakery like?")
    assert tick(body, m) is None                                   # most of the question still to come
    left[0] = 0.6
    assert tick(body, m) == "tilt"
    g = m.moves[0]
    roll = glance._rpy(g.evaluate(g.turn_s + 0.1)[0])[0]
    assert abs(math.degrees(roll)) == pytest.approx(expressive.TILT_DEG)
    assert g.evaluate(g.duration)[0] == pytest.approx(g.start)     # straight again
    expressive.heard_reply("That's lovely.")                       # not a question: no tilt
    t[0] = 100.0
    assert tick(body, m) is None and len(m.moves) == 1


def test_a_question_mark_inside_quotes_still_counts_and_stale_questions_expire():
    expressive.heard_reply('Shall I say "how are you?"')
    assert expressive._question["at"] is not None
    left = [0.5]
    body, t = make(left=lambda: left[0])
    expressive._question["at"] = 0.0
    t[0] = expressive.QUESTION_FOR_S + 1
    assert tick(body, Manager()) is None and expressive._question["at"] is None
