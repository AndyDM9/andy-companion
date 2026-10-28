"""While a search runs, the head is the search's alone (body.hold): seek, face following while speaking, the glance
at the TV and the idle hand-back stand down, and the camera's face tracking is switched off directly."""

import asyncio

import numpy as np

from andy_companion import finder
from andy_companion.body import attach, gaze, glance, hold


class NoRobot:
    def __getattr__(self, name):
        raise AssertionError(f"the robot was touched during a search: {name}")


class Manager:
    def __init__(self):
        self.current_robot = NoRobot()
        self._head_tracking, self._is_speaking = True, True
        self.moves = []

    def queue_move(self, move):
        self.moves.append(move)


def test_the_other_head_behaviours_stand_down_during_a_search():
    m = Manager()
    hold.begin(m)
    head = np.eye(4)
    assert attach.seek_step(m, 0.0, head, True, 0.0, False) is head        # seek: nothing asked of the robot
    gaze.speaking_step(m, face=True, move_playing=False)                    # face following while speaking: nothing
    glance._seen.update(fresh=True)
    assert glance.step(m, 0.0, (0.0, 0.0), listening=False, move_playing=False, tracking=True) is False
    hold.end(m)
    assert not hold.active(m)


def test_a_search_holds_the_head_switches_camera_tracking_off_and_gives_it_back():
    class Robot:
        def __init__(self):
            self.stopped = 0
            self.media = self

        def stop_head_tracking(self):
            self.stopped += 1

        def get_frame(self):
            return np.full((1080, 1920, 3), 20, np.uint8)

        def get_current_head_pose(self):
            return np.eye(4)

        def get_current_joint_positions(self):
            return [0.0] * 7, [-0.17, 0.17]

    class TrackingManager:
        def __init__(self):
            self._head_tracking, self.switched, self.moves, self.during = True, [], [], []

        def set_head_tracking(self, enabled):
            self.switched.append(enabled)

        def queue_move(self, move):
            self.during.append(hold.active(self))
            self.moves.append(move)

    robot, manager = Robot(), TrackingManager()

    async def go():
        async def no_wait(seconds):
            return None
        await finder.find("glasses", robot, manager, asker=lambda f, w: {"seen": False, "x": .5, "y": .5, "where": ""},
                          checker=lambda f, w: {"yes": False}, poster=lambda *a: None, queueable=lambda m: m,
                          sleep=no_wait, clock=lambda: 0.0)
        assert hold.active(manager) and manager.switched == [False]
        await asyncio.sleep(finder.BACK_TO_FACE_S + 0.2)

    asyncio.run(go())
    assert manager.during and all(manager.during)                          # every move made while the search held it
    assert robot.stopped >= 1 + len(finder.SWEEP_DEG)                       # at the start and before each picture
    assert not hold.active(manager) and manager.switched == [False, True]


def test_a_search_starting_mid_turn_holds_the_head_where_it_is_and_nothing_stale_resumes():
    """Seek was turning toward a second voice when a search began. Held, it stopped steering and the head jumped toward
    the middle; after the search the frozen turn resumed and snapped the head from where it pointed (2026-10-28
    review). Now seek stands down under the hold, and the search's first move holds the head where it is."""
    import math
    import types

    from andy_companion.body import person, seek

    class Face:
        detected = False

    class Robot:
        class media:
            @staticmethod
            def get_DoA():
                return (math.pi / 2 - math.radians(60), True)        # a voice 60 degrees to the left

        def get_tracked_face(self, wait=False):
            return Face()

        def start_head_tracking(self, weight=1.0):
            pass

    class Mgr:
        def __init__(self):
            self.current_robot = Robot()
            self._head_tracking, self._is_listening, self._is_speaking = True, True, False
            self.state = types.SimpleNamespace(current_move=None)

    def yaw_deg(pose):
        return math.degrees(math.atan2(pose[1, 0], pose[0, 0]))

    enabled, person.ENABLED = person.ENABLED, False
    try:
        m = Mgr()
        s = m.__dict__.setdefault("_andy_seek", seek.Seek())
        s.state, s._cmd, s._goal, s._for_voice, s._arrived_at, s._return_to = "TURN", math.radians(40), math.radians(60), True, None, 0.0
        neutral = glance._pose(0, 0, 0, [0, 0, 0])
        assert abs(yaw_deg(attach.seek_step(m, 100.0, neutral, True, math.radians(40), False)) - 40) < 1   # turning
        hold.begin(m)
        m._head_tracking = False
        attach.seek_step(m, 100.01, neutral, False, math.radians(40), False)
        assert s.state == "FOLLOW"                                           # the turn is dropped, not frozen
        hold.end(m)
        m._head_tracking, m._is_listening, m._is_speaking = True, False, True
        pointing = glance._pose(0, 0, math.radians(-50), [0, 0, 0])
        out = attach.seek_step(m, 125.0, pointing, True, math.radians(-50), False)
        assert abs(yaw_deg(out) + 50) < 0.5 and s.state == "FOLLOW"           # was 49: the stale turn snapped back
    finally:
        person.ENABLED = enabled

    class SearchRobot:
        def __init__(self):
            self.media = self

        def stop_head_tracking(self):
            pass

        def get_frame(self):
            return np.full((1080, 1920, 3), 20, np.uint8)

        def get_current_head_pose(self):
            return glance._pose(0, 0, math.radians(40), [0, 0, 0])          # where seek's turn had got to

        def get_current_joint_positions(self):
            return [0.0] * 7, [-0.17, 0.17]

    class Queue:
        def __init__(self):
            self._head_tracking, self.log = True, []

        def set_head_tracking(self, enabled):
            pass

        def clear_move_queue(self):
            self.log.append(("clear", hold.active(self)))

        def queue_move(self, move):
            self.log.append((move, hold.active(self)))

    q = Queue()

    async def go():
        async def no_wait(seconds):
            return None
        await finder.find("glasses", SearchRobot(), q, asker=lambda f, w: {"seen": False, "x": .5, "y": .5, "where": ""},
                          checker=lambda f, w: {"yes": False}, poster=lambda *a: None, queueable=lambda m: m,
                          sleep=no_wait, clock=lambda: 0.0)
        await asyncio.sleep(finder.BACK_TO_FACE_S + 0.2)

    asyncio.run(go())
    (cleared, held_then), (first, held_after) = q.log[:2]
    assert cleared == "clear" and held_then is False and held_after is False     # before the hold began
    for t in (0.0, first.turn_s / 2, first.duration):
        assert abs(yaw_deg(first.evaluate(t)[0]) - 40) < 0.5                     # held where the head was
    assert abs(yaw_deg(q.log[3][0].end) - finder.SWEEP_DEG[0]) < 0.5             # then the sweep, from there
