import pytest
"""The body turns to face the tracked person: gently, within limits, and not against moves."""

import math

import numpy as np

from andy_companion.body.body_follow import BodyFollow, head_yaw

DEG = math.radians


def pose(yaw_deg, roll_deg=0.0, pitch_deg=0.0):
    r, p, y = DEG(roll_deg), DEG(pitch_deg), DEG(yaw_deg)
    rx = np.array([[1, 0, 0], [0, math.cos(r), -math.sin(r)], [0, math.sin(r), math.cos(r)]])
    ry = np.array([[math.cos(p), 0, math.sin(p)], [0, 1, 0], [-math.sin(p), 0, math.cos(p)]])
    rz = np.array([[math.cos(y), -math.sin(y), 0], [math.sin(y), math.cos(y), 0], [0, 0, 1]])
    m = np.eye(4)
    m[:3, :3] = rz @ ry @ rx  # scipy "xyz" extrinsic
    return m


def run(f, seconds, yaw_deg, tracking=True, move=False, pose_body=0.0, dt=0.01, t0=0.0):
    t, out = t0, 0.0
    for _ in range(int(seconds / dt)):
        out = f.step(t, None if yaw_deg is None else DEG(yaw_deg), pose_body, tracking, move)
        t += dt
    return out, t


def test_head_yaw_matches_pollens_convention():
    assert math.isclose(head_yaw(pose(30)), DEG(30), abs_tol=1e-9)
    assert math.isclose(head_yaw(pose(-50, roll_deg=10, pitch_deg=15)), DEG(-50), abs_tol=1e-9)


def test_small_head_turns_leave_the_body_still():
    out, _ = run(BodyFollow(), 3, 10)          # 0.6 * 10 = 6° < 8° hysteresis
    assert out == 0.0


def test_body_turns_toward_a_person_off_to_the_side():
    out, _ = run(BodyFollow(), 5, 40)          # target 24°
    assert math.isclose(out, DEG(24), abs_tol=DEG(0.5))


def test_turning_is_rate_limited():
    out, _ = run(BodyFollow(), 0.5, 90)        # 30°/s for 0.5 s
    assert out <= DEG(15) + 1e-6


def test_body_is_capped():
    out, _ = run(BodyFollow(), 20, 300)
    assert math.isclose(out, DEG(120), abs_tol=1e-6)


def test_moves_play_relative_to_the_facing_angle_and_freeze_it():
    f = BodyFollow()
    facing, t = run(f, 5, 40)
    during, t = run(f, 2, -40, move=True, pose_body=DEG(5), t0=t)
    assert math.isclose(during, facing + DEG(5), abs_tol=1e-9), "emotion offset added, facing unchanged"


def test_glides_back_to_centre_when_tracking_stops():
    f = BodyFollow()
    _, t = run(f, 5, 40)
    out, _ = run(f, 0.2, None, tracking=False, t0=t)
    assert 0 < out < DEG(24), "moving back, not snapping"
    out, _ = run(f, 5, None, tracking=False, t0=t + 0.2)
    assert out == 0.0


def test_launcher_wraps_the_single_send_point():
    pytest.importorskip("reachy_mini_conversation_app")
    import importlib.util
    from pathlib import Path
    from reachy_mini_conversation_app import moves

    from andy_companion.body import attach as rj
    assert rj.follow_with_body()
    assert getattr(moves.MovementManager._issue_control_command, "_andy_body_follow", False)
    assert rj.follow_with_body(), "installing twice doesn't wrap twice"
