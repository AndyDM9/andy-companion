"""Livelier idle: calm moments instead of Pollen's random ones, and antenna flicks (2026-10-07)."""

import asyncio
import importlib.util
import random
from pathlib import Path
from types import SimpleNamespace

import pytest

from andy_companion.body import idle

ALL = list(idle.MOMENTS) + ["rage1", "dying1", "scared1"]


def pick(**kw):
    args = dict(present=True, focus=False, hour=14, rng=random.Random(1))
    args.update(kw)
    return idle.pick(30.0 if "idle_s" not in kw else kw.pop("idle_s"), ALL, **{k: v for k, v in args.items() if k != "idle_s"})


def test_only_calm_moments_never_pollens_rage_or_dying():
    seen = {pick(rng=random.Random(i)) for i in range(300)}
    assert seen - {None} <= set(idle.MOMENTS) and None in seen and len(seen - {None}) >= 4


def test_still_in_focus_with_nobody_around_or_turned_off(monkeypatch):
    assert all(pick(focus=True, rng=random.Random(i)) is None for i in range(50))
    assert all(pick(present=False, rng=random.Random(i)) is None for i in range(50))
    monkeypatch.setattr(idle, "CADENCE", "off")
    assert all(pick(rng=random.Random(i)) is None for i in range(50))


def test_yawns_are_likelier_late_at_night():
    day = sum(pick(hour=14, rng=random.Random(i)) == idle.YAWN for i in range(600))
    night = sum(pick(hour=23, rng=random.Random(i)) == idle.YAWN for i in range(600))
    assert night > 2 * day > 0


def test_only_moves_the_library_has():
    assert idle.pick(30, ["curious1"], present=True, focus=False, hour=12, rng=SimpleNamespace(
        random=lambda: 0.99, choices=random.Random(0).choices)) == "curious1"
    assert idle.pick(30, ["rage1"], present=True, focus=False, hour=12, rng=SimpleNamespace(random=lambda: 0.99)) is None


class Library:
    def list_moves(self):
        return ALL

    def get(self, name):
        return SimpleNamespace(duration=4.0, evaluate=lambda t: (None, None, None))


def test_a_moment_is_queued_as_ours(monkeypatch):
    pytest.importorskip("reachy_mini_conversation_app")
    monkeypatch.setattr(idle, "pick", lambda idle_s, available, **kw: "curious1")
    queued = []
    name = asyncio.run(idle.moment(SimpleNamespace(queue_move=queued.append), 400.0, load=Library))
    assert name == "curious1" and queued[0].andy_owns_head and queued[0].emotion_name == "curious1"
    monkeypatch.setattr(idle, "pick", lambda idle_s, available, **kw: None)
    assert asyncio.run(idle.moment(SimpleNamespace(queue_move=queued.append), 400.0, load=Library)) is None and len(queued) == 1


class Robot:
    def __init__(self):
        self.weights = []

    def get_current_head_pose(self):
        return "pose-at-them"

    def start_head_tracking(self, weight):
        self.weights.append(weight)


def manager(move=None, tracking=True, speaking=False):
    return SimpleNamespace(state=SimpleNamespace(current_move=move), _head_tracking=tracking, _is_speaking=speaking,
                           _track_anchor=None, current_robot=Robot())


def tick(m, now, face=True, seek_weight=None):
    """andy_step's order: release, seek (which may set a weight), take."""
    idle.release_step(m, now)
    if seek_weight is not None:
        m.current_robot.start_head_tracking(seek_weight)
    idle.take_step(m, face)


def test_face_following_lets_go_for_the_move_and_takes_the_head_back():
    m = manager(move=SimpleNamespace(andy_owns_head=True))
    tick(m, 0.0)
    assert m._track_anchor == "pose-at-them" and m.current_robot.weights == [0.0]
    tick(m, 0.1)
    assert m.current_robot.weights == [0.0], "once, not every tick"
    m.state.current_move = None
    tick(m, 0.2)
    assert m.current_robot.weights == [0.0], "a one-tick gap isn't the end"
    tick(m, 0.5)
    assert m._track_anchor is None and m.current_robot.weights == [0.0, 1.0]


def test_the_head_goes_back_to_what_seek_wants_if_it_started_searching():
    from andy_companion.body import seek
    m = manager(move=SimpleNamespace(andy_owns_head=True))
    m.__dict__["_andy_seek"] = SimpleNamespace(state="FOLLOW")
    tick(m, 0.0)
    m.state.current_move = None
    m.__dict__["_andy_seek"].state = "SCAN"
    tick(m, 0.1)
    tick(m, 0.5)
    assert m.current_robot.weights == [0.0, seek.SEEK_WEIGHT]


def test_seek_standing_down_on_the_first_tick_doesnt_undo_the_handoff():
    m = manager(move=SimpleNamespace(andy_owns_head=True))
    tick(m, 0.0, seek_weight=1.0)
    assert m.current_robot.weights[-1] == 0.0, "the head is ours for the move (audit, 2026-10-07)"


def test_a_scan_then_a_pointing_move_is_one_handoff():
    m = manager(move=SimpleNamespace(andy_owns_head=True))
    tick(m, 0.0)
    m.state.current_move = None
    tick(m, 0.016)
    m.state.current_move = SimpleNamespace(andy_owns_head=True)
    tick(m, 0.033)
    assert m.current_robot.weights == [0.0]


def test_if_andy_starts_talking_pollen_hands_the_head_back_not_us():
    m = manager(move=SimpleNamespace(andy_owns_head=True))
    tick(m, 0.0, face=False)
    assert m._track_anchor is None and m.current_robot.weights == [0.0], "no face: the move plays from where it is"
    m._is_speaking, m.state.current_move = True, None
    tick(m, 0.1)
    tick(m, 0.5)
    assert m.current_robot.weights == [0.0]


def test_other_moves_and_no_tracking_are_left_alone():
    for m in (manager(move=SimpleNamespace()), manager(move=SimpleNamespace(andy_owns_head=True), tracking=False),
              manager(move=SimpleNamespace(andy_owns_head=True), speaking=True)):
        tick(m, 0.0)
        tick(m, 1.0)
        assert m.current_robot.weights == [] and m._track_anchor is None


def run_flick(flick, allowed=lambda t: True, seconds=400.0, hz=60.0):
    base, out, t = (-0.17, 0.17), [], 0.0
    while t < seconds:
        out.append((t, flick.step(t, base, allowed(t))))
        t += 1.0 / hz
    return base, out


def test_a_flick_is_small_smooth_and_returns_home():
    base, out = run_flick(idle.Flick(rng=random.Random(3)))
    moved = [(t, a) for t, a in out if a != base]
    assert moved, "at least one flick in 400 s"
    assert max(max(abs(a[0] - base[0]), abs(a[1] - base[1])) for _, a in moved) <= idle.FLICK_RAD + 1e-9
    speeds = [max(abs(b[1][i] - a[1][i]) for i in (0, 1)) * 60 for a, b in zip(out, out[1:])]
    assert max(speeds) < 2.0, "slower than robot_state's antenna limit and far from a button press"
    assert out[-1][1] == base


def test_a_flick_stops_when_he_starts_talking():
    flick = idle.Flick(rng=random.Random(3))
    base, out = run_flick(flick)
    start = next(t for t, a in out if a != base)
    flick2 = idle.Flick(rng=random.Random(3))
    _, out2 = run_flick(flick2, allowed=lambda t: t < start + 0.1)
    assert all(a == base for t, a in out2 if t >= start + 0.1)


def test_no_flick_while_the_antennas_are_busy_or_nobody_is_there():
    _, out = run_flick(idle.Flick(rng=random.Random(3)), allowed=lambda t: False)
    assert all(a == (-0.17, 0.17) for _, a in out)
    _, out = run_flick(idle.Flick(rng=random.Random(3), present=lambda: False))
    assert all(a == (-0.17, 0.17) for _, a in out)


def test_the_launcher_replaces_pollens_idle_action(monkeypatch):
    pytest.importorskip("reachy_mini_conversation_app")
    from reachy_mini_conversation_app.conversation_handler import ConversationHandler

    from andy_companion.body import attach
    monkeypatch.setattr(ConversationHandler, "send_idle_signal", ConversationHandler.send_idle_signal)
    monkeypatch.setattr(ConversationHandler, "IDLE_BEHAVIOR_THRESHOLD_S", 180.0)
    monkeypatch.setattr(idle, "CADENCE", "calm")
    assert attach.livelier_idle() and ConversationHandler.IDLE_BEHAVIOR_THRESHOLD_S == 300.0
    calls = []

    async def fake_moment(mm, idle_s, **kw):
        calls.append((mm, idle_s))
    monkeypatch.setattr(idle, "moment", fake_moment)
    handler = SimpleNamespace(deps=SimpleNamespace(movement_manager="mm"))
    asyncio.run(ConversationHandler.send_idle_signal(handler, 301.0))
    assert calls == [("mm", 301.0)]


@pytest.mark.parametrize("cadence, threshold", [("off", float("inf")), ("lively", 120.0)])
def test_cadence_setting(monkeypatch, cadence, threshold):
    pytest.importorskip("reachy_mini_conversation_app")
    from reachy_mini_conversation_app.conversation_handler import ConversationHandler

    from andy_companion.body import attach
    monkeypatch.setattr(ConversationHandler, "send_idle_signal", ConversationHandler.send_idle_signal)
    monkeypatch.setattr(ConversationHandler, "IDLE_BEHAVIOR_THRESHOLD_S", 180.0)
    monkeypatch.setattr(idle, "CADENCE", cadence)
    attach.livelier_idle()
    assert ConversationHandler.IDLE_BEHAVIOR_THRESHOLD_S == threshold
