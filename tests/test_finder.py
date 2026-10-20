import asyncio
import json
import math
import urllib.error
import urllib.request

import numpy as np
import pytest

from andy_companion import board, finder, screen_server
from andy_companion.body import glance, look


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")


def pose(yaw_deg=0.0, pitch_deg=0.0):
    return glance._pose(0.0, math.radians(pitch_deg), math.radians(yaw_deg), [0.0, 0.0, 0.01])


class Media:
    def __init__(self):
        self.taken = 0

    def get_frame(self):
        self.taken += 1
        return np.full((480, 640, 3), self.taken * 20, dtype=np.uint8)   # each frame different


class Robot:
    """The head is where its last queued move ends: a robot that arrives (finder.arrive waits for it)."""

    def __init__(self):
        self.media = Media()
        self.manager = None

    def get_current_head_pose(self):
        moves = self.manager.moves if self.manager else []   # the move for the picture about to be taken
        return moves[min(self.media.taken, len(moves) - 1)].end if moves else pose()

    def get_current_joint_positions(self):
        return [0.0] * 7, [-0.17, 0.17]


class Manager:
    def __init__(self):
        self.moves = []

    def queue_move(self, move):
        self.moves.append(move)


def run_find(asker, poster=lambda views, seen, chosen: None):
    robot, manager = Robot(), Manager()
    robot.manager = manager

    async def no_wait(seconds):
        return None

    out = asyncio.run(finder.find("my reading glasses", robot, manager, asker=asker, poster=poster,
                                  queueable=lambda m: m, sleep=no_wait, clock=lambda: 0.0))
    return out, robot, manager


def test_the_model_s_answer_is_made_safe():
    assert finder.parse('{"seen": true, "x": 1.7, "where": "on the table"}') == {"seen": True, "x": 1.0, "y": 0.5,
                                                                                 "where": "on the table"}
    assert finder.parse('Sure! {"seen": "yes", "x": 0.2, "where": "shelf"}')["seen"] is False   # only a plain true
    assert finder.parse("I can't tell") == {"seen": False, "x": 0.5, "y": 0.5, "where": ""}
    assert finder.tidy_what("  My reading glasses? ") == "reading glasses"


def test_a_place_in_the_frame_becomes_a_head_angle():
    assert finder.target_yaw(0.3, 0.5) == pytest.approx(0.3)                                   # dead centre
    assert math.degrees(finder.target_yaw(0.0, 0.0)) == pytest.approx(40.5, abs=0.5)           # left edge: turn left
    assert finder.target_yaw(0.0, 1.0) == pytest.approx(-finder.target_yaw(0.0, 0.0))
    assert finder.best([{"seen": False, "x": 0.5}, {"seen": True, "x": 0.9}, {"seen": True, "x": 0.55}]) == 2
    assert finder.best([{"seen": False, "x": 0.5}]) is None


def test_andy_sweeps_finds_points_and_shows_what_it_saw(monkeypatch):
    monkeypatch.setenv("ANDY_FINDER_ZOOM", "off")            # one frame per view, as before zooming in (round 7)
    seen_frames, posted = [], []

    def asker(frame, what):
        seen_frames.append(int(frame[0, 0, 0]))
        assert what == "reading glasses"
        hit = int(frame[0, 0, 0]) == 60                        # the third frame
        return {"seen": hit, "x": 0.25 if hit else 0.5, "where": "on the table by the lamp" if hit else ""}

    out, robot, manager = run_find(asker, poster=lambda views, seen, chosen: posted.append((views, seen, chosen)))
    sweep, point = manager.moves[:4], manager.moves[4]
    assert len(manager.moves) == 5 and all(m.andy_owns_head for m in manager.moves)
    assert [round(math.degrees(glance._rpy(m.end)[2])) for m in sweep] == [55, 18, -18, -55]
    assert all(round(math.degrees(glance._rpy(m.end)[1])) == finder.PITCH_DEG for m in sweep)   # a little down
    assert sorted(seen_frames) == [20, 40, 60, 80]              # every frame read
    assert glance._rpy(point.end)[2] == pytest.approx(finder.target_yaw(math.radians(-18), 0.25))
    assert point.hold_s == finder.POINT_HOLD_S
    assert out["found"] and out["where"] == "on the table by the lamp"
    assert out["say"] == "I think I see your reading glasses, on the table by the lamp." and "left or right" in out["how"]
    views, seen, chosen = posted[0]                              # all four views to the screen, in the order Andy turned
    assert len(posted) == 1 and len(views) == 4 and all(v[:2] == b"\xff\xd8" for v in views)
    assert seen == [False, False, True, False] and chosen == 2
    shown = board.showing()
    assert shown["kind"] == "seen" and shown["title"] == "Your reading glasses"


def test_not_found_says_so_kindly_and_points_nowhere(monkeypatch):
    monkeypatch.setenv("ANDY_FINDER_ZOOM", "off")
    posted = []
    out, robot, manager = run_find(lambda f, w: {"seen": False, "x": 0.5, "where": ""},
                                   poster=lambda views, seen, chosen: posted.append((views, seen, chosen)))
    assert not out["found"] and "No guessing" in out["how"] and len(manager.moves) == 4
    # The screen shows where Andy looked: the four views, none seen, none chosen.
    assert len(posted) == 1 and len(posted[0][0]) == 4 and posted[0][1:] == ([False] * 4, None)
    shown = board.showing()
    assert shown["kind"] == "looked" and shown["title"] == "I couldn't see your reading glasses"


def test_eyes_switched_off_is_said_plainly():
    def asker(frame, what):
        raise finder.FinderError("My eyes are switched off right now, so I can't look around.")

    out, _, _ = run_find(asker)
    assert out == {"error": "My eyes are switched off right now, so I can't look around."}


def test_the_look_turns_gently_and_holds():
    step = look.HoldLook(pose(), (-0.17, 0.17), math.radians(55), math.radians(15), 1.1)
    ts = np.arange(0.0, step.duration, 0.01)
    yaws = [glance._rpy(step.evaluate(t)[0])[2] for t in ts]
    assert max(abs(a - b) for a, b in zip(yaws, yaws[1:])) / 0.01 <= glance.PEAK_RAD_S * 1.01
    assert yaws[-1] == pytest.approx(math.radians(55)) and step.evaluate(step.duration - 0.01)[2] == 0.0


def test_the_screen_keeps_the_views_in_memory_for_two_minutes():
    import base64

    httpd = screen_server.serve(host="127.0.0.1", port=0)
    try:
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        token = board.tokens()["screen"]

        def post(body, t=token):
            req = urllib.request.Request(f"{base}/api/views?t={t}", method="POST", data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())

        b64 = [base64.b64encode(b"\xff\xd8 view %d" % i).decode() for i in range(4)]
        assert post({"views": b64[:3] + [None], "seen": [False, True, False, False], "chosen": 1}) == {"ok": True}
        with urllib.request.urlopen(f"{base}/view?t={token}&i=1", timeout=5) as r:
            assert r.read() == b"\xff\xd8 view 1"
        for i in ("3", "4", "x"):                                 # no picture there, none at all, not a number
            with pytest.raises(urllib.error.HTTPError):
                urllib.request.urlopen(f"{base}/view?t={token}&i={i}", timeout=5)
        for bad in ({"views": [base64.b64encode(b"<html>").decode()], "seen": [False], "chosen": None},   # not a picture
                    {"views": b64 + b64[:1], "seen": [False] * 5, "chosen": None},                       # five views
                    {"views": b64, "seen": [False] * 4, "chosen": 0}):                                   # chose one not seen
            with pytest.raises(urllib.error.HTTPError):
                post(bad)
        with pytest.raises(urllib.error.HTTPError):
            post({"views": b64, "seen": [False] * 4, "chosen": None}, t="wrong")
        assert screen_server.views()["chosen"] == 1                   # the bad posts changed nothing
        assert screen_server.view(1, now=screen_server._views["at"] + screen_server.FRAME_FOR_S + 1) == b""
        assert screen_server._views["jpegs"] == []                    # forgotten, not only hidden
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(f"{base}/view?t=wrong&i=0", timeout=5)
    finally:
        httpd.shutdown()
        screen_server.forget_views()


def test_a_stopped_endpoint_is_said_at_once_not_after_the_read_timeout(monkeypatch):
    from andy_companion import vision

    def never(req, timeout=None):
        raise AssertionError("no request to an endpoint that takes no connection")

    monkeypatch.setenv("ANDY_VISION", "endpoint")
    monkeypatch.setenv("ANDY_VISION_URL", "https://eyes.example")
    monkeypatch.setenv("ANDY_VISION_TOKEN", "t")
    monkeypatch.setattr(vision, "reachable", lambda url: False)
    monkeypatch.setattr(urllib.request, "urlopen", never)
    with pytest.raises(finder.FinderError, match="switched off"):
        finder.ask(np.zeros((48, 64, 3), dtype=np.uint8), "glasses")


def test_a_try_is_kept_only_when_asked_and_scored_against_the_persons_labels(tmp_path, monkeypatch):
    import importlib.util
    import numpy as np
    from pathlib import Path

    frames = [np.zeros((8, 8, 3), dtype=np.uint8)] * 4
    results = [{"seen": False, "x": 0.5, "where": ""}, {"seen": True, "x": 0.4, "where": "on the table"},
               {"seen": False, "x": 0.5, "where": ""}, {"seen": False, "x": 0.5, "where": ""}]
    monkeypatch.delenv("ANDY_FINDER_RECORD", raising=False)
    assert finder.record("glasses", frames, results, 1, {"to_point": 4.2}) is None        # off by default
    kept = Path(finder.record("glasses", frames, results, 1, {"to_point": 4.2}, folder=str(tmp_path)))
    assert sorted(p.name for p in kept.iterdir()) == ["try.json", "view-0.jpg", "view-1.jpg", "view-2.jpg", "view-3.jpg"]
    assert oct(kept.stat().st_mode & 0o777) == "0o700"

    spec = importlib.util.spec_from_file_location("finder_eval", Path(finder.__file__).parents[2] / "evals" / "finder_eval.py")
    ev = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(ev)
    (tmp_path / "labels.csv").write_text(f"{kept.name},1 2\n")
    card = ev.score(ev.tries(tmp_path), ev.labels(tmp_path))
    assert card["in_sight"] == {"tries": 1, "right": 1, "right_95": [20.7, 100.0], "wrong_view": 0, "missed": 0}
    assert card["median_to_point_s"] == 4.2
    (tmp_path / "labels.csv").write_text(f"{kept.name},none\n")
    assert ev.score(ev.tries(tmp_path), ev.labels(tmp_path))["out_of_sight"]["pointed_at_nothing"] == 1
    assert "view-1.jpg" in ev.sheet(tmp_path).read_text()
