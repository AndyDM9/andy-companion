"""Round 8, B45: turning to whoever speaks. While Andy follows one face, speech well to the side for long enough turns
the head to it; a face there and tracking takes the new person; nobody there and the head goes back."""

import math

import pytest

from andy_companion.body import seek

LEFT = 0.0          # the mic array's angle: 0 = left (head-relative yaw +90 degrees), pi/2 = front, pi = right
FRONT = math.pi / 2


def tick(sk, t, *, face=True, speaking=True, robot=False, doa=LEFT, yaw=0.0, moving=False):
    return sk.step(t, tracking=True, face=face, head_world_yaw=yaw, user_speaking=speaking, robot_speaking=robot,
                   move_playing=moving, doa_angle=doa if speaking else None)


def test_a_voice_well_to_the_side_turns_the_head_after_a_moment():
    sk = seek.Seek()
    tick(sk, 0.0)
    assert sk.state == "FOLLOW"
    d = tick(sk, 0.3)
    assert sk.state == "FOLLOW" and d.head_yaw is None                     # one word is not a turn
    d = tick(sk, 0.7)
    assert sk.state == "TURN" and sk._goal == pytest.approx(math.radians(90)) and d.weight == seek.SEEK_WEIGHT


def test_the_person_in_front_talking_never_turns_it_and_andy_talking_never_does():
    sk = seek.Seek()
    for t in (0.0, 0.5, 1.0, 1.5):
        tick(sk, t, doa=FRONT)
    assert sk.state == "FOLLOW"
    sk = seek.Seek()
    for t in (0.0, 0.5, 1.0, 1.5):
        tick(sk, t, robot=True)
    assert sk.state == "FOLLOW"


def test_the_first_face_does_not_end_the_turn_but_a_face_on_arrival_does():
    sk = seek.Seek()
    tick(sk, 0.0); tick(sk, 0.7)
    assert sk.state == "TURN"
    tick(sk, 0.8, speaking=False)                                           # the old face, still in view: keep turning
    assert sk.state == "TURN"
    t = 0.8
    while sk._arrived_at is None and t < 5:
        t += 0.05
        tick(sk, t, face=False, speaking=False)
    d = tick(sk, t + 0.1, face=True, speaking=False)                        # the new person's face
    assert sk.state == "FOLLOW" and d.weight == 1.0


def test_nobody_there_goes_back_and_that_direction_is_left_alone():
    sk = seek.Seek()
    tick(sk, 0.0, yaw=0.2); tick(sk, 0.7, yaw=0.2)
    assert sk.state == "TURN"
    t = 0.7
    for _ in range(400):                                                    # turn, wait, no face: back home
        t += 0.05
        tick(sk, t, face=False, speaking=False, yaw=sk._cmd)
        if sk.state != "TURN":
            break
    assert sk.state == "HOME" and sk._home_to == pytest.approx(0.2)
    for _ in range(400):
        t += 0.05
        tick(sk, t, face=False, speaking=False, yaw=sk._cmd)
        if sk.state != "HOME":
            break
    assert sk.state == "REST" and sk._cmd == pytest.approx(0.2, abs=math.radians(4))
    # The same direction again (the TV): left alone for a minute.
    tick(sk, t + 1, yaw=0.2); tick(sk, t + 2, yaw=0.2)
    assert sk.state in ("REST", "FOLLOW")


def test_answering_the_new_speaker_does_not_send_the_head_home_and_it_can_be_switched_off(monkeypatch):
    sk = seek.Seek()
    tick(sk, 0.0); tick(sk, 0.7)
    tick(sk, 0.8, face=False, speaking=False, robot=True)
    assert sk.state == "TURN"
    monkeypatch.setattr(seek, "SECOND_VOICE", False)
    sk = seek.Seek()
    tick(sk, 0.0); tick(sk, 0.7); tick(sk, 1.4)
    assert sk.state == "FOLLOW"
