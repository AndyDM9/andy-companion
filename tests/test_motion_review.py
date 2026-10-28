"""2026-10-28 review of the head's motion, with fakes (no robot): each look holds past its longest wait and the next
replaces it in the same tick; one search at a time, and an old search never hands the head back during a new one;
turns go the direct way; a taught move eases back from where the head really is."""

import asyncio
import importlib.util
import math
import sys
from pathlib import Path

import numpy as np
import pytest

from andy_companion import board, finder, gestures
from andy_companion.body import glance, hold, look

sys.path.insert(0, str(Path(__file__).parent))
spec = importlib.util.spec_from_file_location("zoom_fakes", Path(__file__).parent / "test_round7_zoom.py")
zoom = importlib.util.module_from_spec(spec)
spec.loader.exec_module(zoom)


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.delenv("ANDY_FINDER_ZOOM", raising=False)


class Manager(zoom.Manager):
    """Pollen's queue: clear_move_queue then queue_move are applied in the same tick."""

    def __init__(self):
        super().__init__()
        self.log = []
        self._head_tracking = True

    def clear_move_queue(self):
        self.log.append("clear")

    def queue_move(self, move):
        self.log.append("move")
        super().queue_move(move)

    def set_head_tracking(self, on):
        self.log.append(f"tracking {on}")
        self._head_tracking = on


def search(manager, frames, checker, loop=None):
    robot = zoom.Robot(frames)
    robot.manager = manager

    async def no_wait(seconds):
        return None

    coro = finder.find("my glasses", robot, manager, asker=zoom.spot_asker, checker=checker, poster=lambda *a: None,
                       queueable=lambda m: m, sleep=no_wait, clock=lambda: 0.0)
    return coro if loop else asyncio.run(coro)


def test_each_look_holds_past_its_longest_wait_and_the_next_replaces_it_at_once():
    assert finder.HOLD_S >= finder.WAIT_ARRIVE_S + finder.SETTLE_S + 0.2
    assert finder.CLOSER_HOLD_S >= finder.WAIT_ARRIVE_S + finder.SETTLE_S + 0.2
    manager = Manager()
    out = search(manager, [zoom.EMPTY, zoom.EMPTY, zoom.frame_with_spot(0.7, 0.6), zoom.EMPTY,
                           zoom.frame_with_spot(0.5, 0.5, value=230)], lambda f, w: {"yes": True, "x": .5, "y": .5, "where": ""})
    assert out["found"]
    moves = [entry for entry in manager.log if entry in ("clear", "move")]
    # Holding still where the head was, four views, the closer look, the point: each replaces the last.
    assert moves == ["clear", "move"] * 7


def test_a_second_search_while_one_runs_is_told_to_wait():
    async def both():
        manager = Manager()
        gate = asyncio.Event()

        async def slow_checker_sleep(seconds):
            await gate.wait()

        robot = zoom.Robot([zoom.EMPTY] * 4)
        robot.manager = manager
        first = asyncio.create_task(finder.find("glasses", robot, manager, asker=zoom.spot_asker,
                                                checker=lambda f, w: {"yes": False}, poster=lambda *a: None,
                                                queueable=lambda m: m, sleep=slow_checker_sleep, clock=lambda: 0.0))
        await asyncio.sleep(0)
        second = await finder.find("keys", zoom.Robot([]), manager)
        gate.set()
        await first
        return second, manager
    second, manager = asyncio.run(both())
    assert second["busy"] and "already looking" in second["how"]


def test_an_old_search_never_hands_the_head_back_during_a_new_one():
    async def two():
        manager = Manager()
        timers = []
        loop = asyncio.get_running_loop()
        real_later = loop.call_later
        loop.call_later = lambda delay, fn: timers.append(fn)
        try:
            await search(manager, [zoom.EMPTY] * 4, lambda f, w: {"yes": False}, loop=True)
            assert not finder._searching["on"] and manager._head_tracking is False
            await search(manager, [zoom.EMPTY] * 4, lambda f, w: {"yes": False}, loop=True)
            first_back, second_back = timers
            first_back()                                  # the first search's hand-back, during the second's
            assert hold.active(manager) and manager._head_tracking is False
            second_back()                                 # the second hands it back, face following too
            assert not hold.active(manager) and manager._head_tracking is True
        finally:
            loop.call_later = real_later
    asyncio.run(two())


def test_a_turn_between_the_two_sides_goes_the_direct_way():
    start = glance._pose(0.0, 0.0, math.radians(94), [0.0, 0.0, 0.01])
    step = look.HoldLook(start, (0.0, 0.0), math.radians(-94), 0.0, 1.0)
    assert step.dyaw == pytest.approx(math.radians(-188))          # through the front, never behind
    near = look.HoldLook(glance._pose(0.0, 0.0, math.radians(10), [0.0, 0.0, 0.01]), (0.0, 0.0), math.radians(-20), 0.0, 1.0)
    assert near.dyaw == pytest.approx(math.radians(-30))


def test_a_taught_move_eases_back_from_where_the_head_is_now(monkeypatch):
    class Robot:
        def __init__(self):
            self.reads = 0

        def get_current_head_pose(self):
            self.reads += 1
            return np.eye(4) * self.reads                 # a different pose each read: the person was followed

        def get_current_joint_positions(self):
            return [0.0] * 7, [0.1, -0.1]

        def disable_motors(self, which):
            pass

        def enable_motors(self, which):
            pass

    homes = []
    monkeypatch.setattr(gestures, "Home", lambda head, last, start: homes.append(head) or ("home", head))
    monkeypatch.setattr(gestures, "RECORD_S", 0.0)
    robot, manager = Robot(), Manager()

    async def no_wait(seconds):
        return None

    try:
        asyncio.run(gestures.learn("wave", robot, manager, sleep=no_wait, queue=lambda m: m))
    except Exception:
        pass                                              # nothing recorded: what matters is where it eased from
    assert homes and homes[0][0][0] == 2.0            # read again when recording ended, not the start's pose 1
