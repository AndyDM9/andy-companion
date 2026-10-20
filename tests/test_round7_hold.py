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
