"""Round 7, B44: finding small things by zooming in. Each view is read as six overlapping tiles at full resolution,
sightings are merged into head angles, and Andy looks closer (head straight at it, a close-up from the middle of
the lens) before pointing; only a plain "yes" up close counts."""

import asyncio
import math

import numpy as np
import pytest

from andy_companion import board, finder
from andy_companion.body import glance


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.delenv("ANDY_FINDER_ZOOM", raising=False)


def pose(yaw_deg=0.0, pitch_deg=0.0):
    return glance._pose(0.0, math.radians(pitch_deg), math.radians(yaw_deg), [0.0, 0.0, 0.01])


def frame_with_spot(x, y, value=200, w=1920, h=1080):
    """A dark frame with one bright square (the 'glasses') at x, y (0..1)."""
    f = np.full((h, w, 3), 20, np.uint8)
    cx, cy = int(x * w), int(y * h)
    f[cy - 20:cy + 20, cx - 30:cx + 30] = value
    return f


def spot_asker(frame, what):
    """Sees the bright square when it is in the tile, and says where in the tile."""
    ys, xs = np.where(frame[..., 0] > 150)
    if not len(xs):
        return {"seen": False, "x": 0.5, "y": 0.5, "where": ""}
    return {"seen": True, "x": float(xs.mean()) / frame.shape[1], "y": float(ys.mean()) / frame.shape[0],
            "where": "on the coffee table"}


def test_six_overlapping_tiles_cover_the_whole_frame_at_full_size():
    f = np.zeros((1080, 1920, 3), np.uint8)
    parts = finder.tiles(f)
    assert len(parts) == 6
    assert {(p[2], p[3]) for p in parts} == {(711, 584)}                      # never shrunk
    assert min(p[0] for p in parts) == 0 and max(p[0] + p[2] for p in parts) == 1920
    assert min(p[1] for p in parts) == 0 and max(p[1] + p[3] for p in parts) == 1080
    lefts = sorted({p[0] for p in parts})
    assert lefts[1] < lefts[0] + 711 and lefts[2] < lefts[1] + 711          # neighbours overlap
    assert finder.close_up(f).shape[:2] == (540, 960)                         # the middle half each way


def test_a_view_maps_tile_sightings_back_to_the_frame_and_counts_one_thing_once():
    f = frame_with_spot(0.5, 0.5)          # the middle: inside several overlapping tiles
    out = finder.read_view(f, "glasses", spot_asker)
    assert out["seen"] and len(out["sightings"]) == 1
    assert out["x"] == pytest.approx(0.5, abs=0.01) and out["y"] == pytest.approx(0.5, abs=0.01)
    assert out["sightings"][0]["tiles"] >= 2
    out = finder.read_view(frame_with_spot(0.1, 0.85), "glasses", spot_asker)
    assert out["x"] == pytest.approx(0.1, abs=0.01) and out["y"] == pytest.approx(0.85, abs=0.01)
    assert not finder.read_view(np.full((1080, 1920, 3), 20, np.uint8), "glasses", spot_asker)["seen"]


def test_a_view_reads_its_six_tiles_at_once_and_stops_on_switched_off_eyes():
    calls = []

    def asker(frame, what):
        calls.append(frame.shape[:2])
        return {"seen": False, "x": 0.5, "y": 0.5, "where": ""}

    finder.read_view(np.zeros((1080, 1920, 3), np.uint8), "glasses", asker)
    assert calls == [(584, 711)] * 6

    def off(frame, what):
        raise finder.FinderError(finder.SWITCHED_OFF)

    with pytest.raises(finder.FinderError):
        finder.read_view(np.zeros((1080, 1920, 3), np.uint8), "glasses", lambda f, w: off(f, w))


def test_only_a_plain_yes_up_close_counts_and_pitch_goes_down_for_lower_things():
    assert finder.parse_check('{"answer": "yes", "x": 0.4, "y": 0.6, "where": "by the lamp"}')["yes"] is True
    for said in ('{"answer": "unsure", "x": 0.5, "y": 0.5, "where": ""}', '{"answer": "Yes"}', "yes", "{}"):
        assert finder.parse_check(said)["yes"] is False, said
    p0 = math.radians(15)
    assert finder.target_pitch(p0, 0.5) == pytest.approx(p0)
    assert finder.target_pitch(p0, 0.9) > p0 > finder.target_pitch(p0, 0.1)        # lower in the picture: further down
    assert finder.target_pitch(p0, 1.0) <= math.radians(35)


class Media:
    def __init__(self, frames):
        self.frames, self.taken = list(frames), 0

    def get_frame(self):
        self.taken += 1
        return self.frames.pop(0) if self.frames else np.full((1080, 1920, 3), 20, np.uint8)


class Robot:
    """The head is where its last queued move ends: a robot that arrives (finder.arrive waits for it)."""

    def __init__(self, frames):
        self.media = Media(frames)
        self.manager = None

    def now_move(self):
        """The move the head is in for the picture about to be taken (one per picture: four views, then closer looks)."""
        moves = self.manager.moves if self.manager else []
        return moves[min(self.media.taken, len(moves) - 1)] if moves else None

    def get_current_head_pose(self):
        m = self.now_move()
        return m.end if m else pose()

    def get_current_joint_positions(self):
        return [0.0] * 7, [-0.17, 0.17]


class Manager:
    def __init__(self):
        self.moves = []

    def queue_move(self, move):
        self.moves.append(move)


def run(frames, checker, asker=spot_asker):
    robot, manager, posted = Robot(frames), Manager(), []
    robot.manager = manager

    async def no_wait(seconds):
        return None

    out = asyncio.run(finder.find("my glasses", robot, manager, asker=asker, checker=checker,
                                  poster=lambda views, seen, chosen: posted.append((views, seen, chosen)),
                                  queueable=lambda m: m, sleep=no_wait, clock=lambda: 0.0))
    return out, robot, manager, posted


EMPTY = np.full((1080, 1920, 3), 20, np.uint8)


def test_andy_looks_closer_then_points_and_the_tv_shows_the_close_up():
    sweep = [EMPTY, EMPTY, frame_with_spot(0.7, 0.6), EMPTY]     # seen in the third view, a little low and right
    close = frame_with_spot(0.5, 0.5, value=230)                 # the close-up, taken with the head turned at it
    checks = []

    def checker(frame, what):
        checks.append(frame.shape[:2])
        return {"yes": True, "x": 0.5, "y": 0.5, "where": "on the coffee table, by the remote"}

    out, robot, manager, posted = run(sweep + [close], checker)
    assert out["found"] and out["looked_closer"] and out["where"] == "on the coffee table"   # the wider view's words
    assert robot.media.taken == 5 and checks == [(540, 960)]              # four views, then one close-up
    sweep_moves, closer, point = manager.moves[:4], manager.moves[4], manager.moves[5]
    assert len(manager.moves) == 6 and closer.hold_s == finder.CLOSER_HOLD_S and point.hold_s == finder.POINT_HOLD_S
    assert [round(math.degrees(glance._rpy(m.end)[2])) for m in sweep_moves] == [55, 18, -18, -55]
    want_yaw = finder.target_yaw(math.radians(-18), 0.7)
    assert glance._rpy(closer.end)[2] == pytest.approx(want_yaw, abs=0.01)
    assert glance._rpy(closer.end)[1] > math.radians(finder.PITCH_DEG)   # lower than the sweep: it was low in view
    assert posted[0] == ([None] * 4, [False] * 4, None)          # the TV cleared first: no old close-up to find
    views, seen, chosen = posted[-1]
    assert chosen == 2 and seen == [False, False, True, False]
    import cv2
    shown = cv2.imdecode(np.frombuffer(views[2], np.uint8), cv2.IMREAD_COLOR)
    assert shown.shape[1] == finder.VIEW_WIDTH and shown[shown.shape[0] // 2, shown.shape[1] // 2, 0] > 200   # the close-up


def test_a_no_up_close_moves_on_and_then_says_it_was_not_them():
    sweep = [frame_with_spot(0.3, 0.5), EMPTY, frame_with_spot(0.7, 0.5), EMPTY]   # two places
    asked = []

    def checker(frame, what):
        asked.append(1)
        return {"yes": False, "x": 0.5, "y": 0.5, "where": ""}

    out, robot, manager, posted = run(sweep, checker)
    assert not out["found"] and len(asked) == finder.MAX_CLOSER == 2
    assert "looked closer" in out["how"] and "No guessing" in out["how"]
    assert len(manager.moves) == 4 + 2                                    # the sweep, two closer looks, no point
    assert posted[-1][2] is None and board.showing()["kind"] == "looked"


def test_nothing_seen_means_no_closer_look_and_switched_off_eyes_up_close_are_said():
    out, robot, manager, _ = run([EMPTY] * 4, lambda f, w: {"yes": True, "x": .5, "y": .5, "where": ""})
    assert not out["found"] and len(manager.moves) == 4 and "couldn't see" in out["how"]

    def off(frame, what):
        raise finder.FinderError(finder.SWITCHED_OFF)

    out, *_ = run([EMPTY, frame_with_spot(0.5, 0.5), EMPTY, EMPTY], off)
    assert out == {"error": finder.SWITCHED_OFF}


def test_zoom_off_goes_back_to_one_frame_per_view_and_no_closer_look(monkeypatch):
    monkeypatch.setenv("ANDY_FINDER_ZOOM", "off")
    calls = []

    def asker(frame, what):
        calls.append(frame.shape[:2])
        return spot_asker(frame, what)

    out, robot, manager, _ = run([EMPTY, frame_with_spot(0.5, 0.5), EMPTY, EMPTY],
                                 lambda f, w: pytest.fail("no closer look with zoom off"), asker=asker)
    assert out["found"] and calls == [(1080, 1920)] * 4 and len(manager.moves) == 5


def test_a_head_that_starts_late_is_waited_for_and_its_real_angle_is_used():
    """The founder's first recorded try: the first view was taken about 18 degrees short of where it was sent."""
    class LateRobot(Robot):
        def __init__(self, frames):
            super().__init__(frames)
            self.asked = 0

        def get_current_head_pose(self):
            self.asked += 1
            m = self.now_move()
            if not m:
                return pose()
            yaw, pitch = glance._rpy(m.end)[2], glance._rpy(m.end)[1]
            if self.asked <= 3:                                     # still on its way for the first three looks
                return pose(math.degrees(yaw) - 18, math.degrees(pitch))
            return m.end

    robot, manager, waits = LateRobot([EMPTY, EMPTY, EMPTY, EMPTY]), Manager(), []
    robot.manager = manager

    async def counting_wait(seconds):
        waits.append(seconds)

    asyncio.run(finder.find("glasses", robot, manager, asker=spot_asker, checker=lambda f, w: {"yes": False},
                            poster=lambda *a: None, queueable=lambda m: m, sleep=counting_wait, clock=lambda: 0.0))
    assert waits.count(finder.POLL_S) >= 2                           # it waited for the head to arrive


def test_a_view_seen_short_of_where_it_was_sent_is_read_from_where_the_head_really_was():
    class ShortRobot(Robot):
        def get_current_head_pose(self):
            m = self.now_move()
            if not m:
                return pose()
            yaw, pitch = glance._rpy(m.end)[2], glance._rpy(m.end)[1]
            return pose(math.degrees(yaw) - 10, math.degrees(pitch))  # always 10 degrees short (inside 25)

    robot, manager = ShortRobot([EMPTY, EMPTY, frame_with_spot(0.5, 0.5), EMPTY]), Manager()
    robot.manager = manager

    async def no_wait(seconds):
        return None

    asyncio.run(finder.find("glasses", robot, manager, asker=spot_asker, checker=lambda f, w: {"yes": False},
                            poster=lambda *a: None, queueable=lambda m: m, sleep=no_wait, clock=lambda: 0.0))
    closer = manager.moves[4]
    assert math.degrees(glance._rpy(closer.end)[2]) == pytest.approx(-18 - 10, abs=0.5)   # from the real -28, not -18


def test_a_recorded_try_keeps_full_size_views_the_close_up_and_where_the_head_was(tmp_path):
    import json

    import cv2

    frames = [frame_with_spot(0.5, 0.5)] * 4
    out = finder.record("glasses", frames, [{"seen": False}] * 4, None, {"to_answer": 9.0}, folder=str(tmp_path),
                        poses=[[55.0, 15.0], [18.0, 15.0], [-18.0, 15.0], [-55.0, 15.0]],
                        close_ups=[finder.close_up(frames[0])])
    from pathlib import Path
    kept = Path(out)
    assert cv2.imread(str(kept / "view-0.jpg")).shape[:2] == (1080, 1920)                   # every pixel, for re-reading
    assert cv2.imread(str(kept / "closer-0.jpg")).shape[:2] == (540, 960)
    assert json.loads((kept / "try.json").read_text())["poses_deg"][0] == [55.0, 15.0]


def test_face_following_is_off_for_the_whole_search_and_comes_back_after_the_point(monkeypatch):
    monkeypatch.setattr(finder, "POINT_HOLD_S", 0.05)       # the same order of events, without waiting 4.5 s
    monkeypatch.setattr(finder, "BACK_TO_FACE_S", 0.05)
    """The founder's recorded tries: face tracking took the head back mid-sweep and one view pointed at him."""
    class TrackingManager(Manager):
        def __init__(self):
            super().__init__()
            self._head_tracking, self.switched = True, []

        def set_head_tracking(self, enabled):
            self.switched.append(enabled)
            self._head_tracking = enabled

    robot, manager = Robot([EMPTY, EMPTY, frame_with_spot(0.5, 0.5), EMPTY, frame_with_spot(0.5, 0.5)]), TrackingManager()
    robot.manager = manager

    async def go():
        async def no_wait(seconds):
            return None
        out = await finder.find("glasses", robot, manager, asker=spot_asker,
                                checker=lambda f, w: {"yes": True, "x": .5, "y": .5, "where": "on the chair"},
                                poster=lambda *a: None, queueable=lambda m: m, sleep=no_wait, clock=lambda: 0.0)
        assert manager.switched == [False]                       # off for the search, not yet back
        await asyncio.sleep(finder.BACK_TO_FACE_S + finder.POINT_HOLD_S + 0.2)
        return out

    out = asyncio.run(go())
    assert out["found"] and manager.switched == [False, True]   # back after the point


def test_face_following_that_was_off_stays_off():
    class OffManager(Manager):
        _head_tracking = False

        def set_head_tracking(self, enabled):
            raise AssertionError("not touched when it was off")

    robot, manager = Robot([EMPTY] * 4), OffManager()
    robot.manager = manager

    async def no_wait(seconds):
        return None

    asyncio.run(finder.find("glasses", robot, manager, asker=spot_asker, checker=lambda f, w: {"yes": False},
                            poster=lambda *a: None, queueable=lambda m: m, sleep=no_wait, clock=lambda: 0.0))


def test_where_a_direction_shows_in_a_view_is_the_inverse_of_the_aim():
    for x, y in ((0.5, 0.5), (0.2, 0.8), (0.9, 0.1)):
        yaw = finder.target_yaw(math.radians(30), x)
        pitch = finder.target_pitch(math.radians(15), y, reach=False)
        bx, by = finder.where_in_view(yaw, pitch, math.radians(30), math.radians(15))
        assert bx == pytest.approx(x, abs=1e-6) and by == pytest.approx(y, abs=1e-6)
    f = np.zeros((1080, 1920, 3), np.uint8)
    rows, cols = finder._close_box(f, 0.5, (0.02, 0.98))                      # kept inside the frame
    assert (rows.start, rows.stop, cols.start, cols.stop) == (540, 1080, 0, 960)


def test_something_past_the_heads_reach_is_looked_at_from_as_far_as_it_turns():
    """The founder's chair: about 74 degrees to Andy's left, past the head's 65."""
    sweep = [frame_with_spot(0.15, 0.85), EMPTY, EMPTY, EMPTY]       # far left and low in the first view (55 deg)
    seen_at = []

    def checker(picture, what):
        seen_at.append(picture.shape[:2])
        return {"yes": True, "x": 0.5, "y": 0.5, "where": "on the chair"}

    out, robot, manager, _ = run(sweep + [EMPTY], checker)
    closer = manager.moves[4]
    yaw, pitch = glance._rpy(closer.end)[2], glance._rpy(closer.end)[1]
    assert math.degrees(yaw) == pytest.approx(finder.REACH_YAW_DEG, abs=0.01)          # as far as it can
    assert math.degrees(pitch) <= finder.REACH_PITCH_DEG + 1e-6
    assert out["found"] and seen_at == [(540, 960)]
    assert math.degrees(glance._rpy(manager.moves[5].end)[2]) <= finder.REACH_YAW_DEG + 1e-6   # it points within reach


def test_the_sweep_sends_one_move_per_picture():
    taken_with_moves = []

    class Counting(Robot):
        def get_current_head_pose(self):
            if self.manager:
                taken_with_moves.append((self.media.taken, len(self.manager.moves)))
            return super().get_current_head_pose()

    robot, manager = Counting([EMPTY] * 4), Manager()
    robot.manager = manager

    async def no_wait(seconds):
        return None

    asyncio.run(finder.find("glasses", robot, manager, asker=spot_asker, checker=lambda f, w: {"yes": False},
                            poster=lambda *a: None, queueable=lambda m: m, sleep=no_wait, clock=lambda: 0.0))
    # Whenever the head was asked where it is during the sweep, the moves sent were one more than the pictures taken.
    during = [(t, m) for t, m in taken_with_moves if 1 <= m <= 4 and t < 4]
    assert during and all(m == t + 1 for t, m in during)
