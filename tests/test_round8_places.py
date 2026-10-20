"""Round 8, B46: "remember where I put it". Places are kept only after a yes (consent), as words, a head direction
and a time, never a picture; a find is remembered in memory only; asking again turns there first."""

import asyncio
import math
import time

import numpy as np
import pytest

from andy_companion import board, consent, finder, kept, places
from andy_companion.body import glance

T = time.time()          # places older than KEEP_DAYS are dropped, so tests use today's clock


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(places, "FILE", tmp_path / "places.json")
    for name in ("SCREEN", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.delenv("ANDY_FINDER_ZOOM", raising=False)


def test_a_place_is_kept_as_words_a_direction_and_a_time_and_names_match_loosely(tmp_path):
    item = places.keep("my house keys", "on the hall table", 0.4, 0.2, now=T + 0)
    assert set(item) == {"id", "what", "where", "at", "yaw", "pitch"}                     # never a picture
    assert oct((tmp_path / "places.json").stat().st_mode & 0o777) == "0o600"
    assert places.recall("keys", now=T + 1)["where"] == "on the hall table"
    places.keep("reading glasses", "on the shelf", now=T + 2)
    assert places.recall("my glasses", now=T + 3)["where"] == "on the shelf"
    places.keep("keys", "in the bowl", now=T + 4)                                            # one place per thing
    assert [p["where"] for p in places.kept() if "key" in p["what"]] == ["in the bowl"]
    assert places.forget("keys") == 1 and places.recall("keys") is None
    with pytest.raises(ValueError):
        places.keep("", "somewhere")


def test_a_find_is_remembered_in_memory_only_and_the_newer_wins(tmp_path):
    places.saw("glasses", "on the desk", 0.1, 0.3, now=T + 0)
    assert not (tmp_path / "places.json").exists()                                           # never written down
    assert places.recall("glasses", now=T + 1)["told"] is False
    places.keep("glasses", "on the shelf", 0.5, 0.2, now=T + 2)
    assert places.recall("glasses", now=T + 3)["where"] == "on the shelf"
    places.saw("glasses", "on the sofa", 0.7, 0.3, now=T + 4)
    assert places.recall("glasses", now=T + 5)["where"] == "on the sofa"
    assert places.recall("glasses", now=T + 4 + places.LAST_SEEN_S + 1)["where"] == "on the shelf"   # memory expires


def test_keeping_a_place_needs_a_yes_and_it_is_listed_and_deletable():
    assert "remember_place" in consent.SAVING
    places.keep("keys", "on the hall table", 0.4, 0.2)
    rows = kept.summary()["place"]
    assert rows and rows[0]["text"] == "keys: on the hall table"
    assert kept.delete("place", rows[0]["id"]) and places.kept() == []


class Media:
    def __init__(self, frames):
        self.frames, self.taken = list(frames), 0

    def get_frame(self):
        self.taken += 1
        return self.frames.pop(0) if self.frames else np.full((1080, 1920, 3), 20, np.uint8)


class Robot:
    def __init__(self, frames):
        self.media, self.manager = Media(frames), None

    def get_current_head_pose(self):
        moves = self.manager.moves if self.manager else []
        return moves[min(self.media.taken, len(moves) - 1)].end if moves else glance._pose(0, 0, 0, [0, 0, 0.01])

    def get_current_joint_positions(self):
        return [0.0] * 7, [-0.17, 0.17]


class Manager:
    def __init__(self):
        self.moves = []

    def queue_move(self, move):
        self.moves.append(move)


def run(frames, checker, asker):
    robot, manager, posted = Robot(frames), Manager(), []
    robot.manager = manager

    async def no_wait(seconds):
        return None

    out = asyncio.run(finder.find("my keys", robot, manager, asker=asker, checker=checker,
                                  poster=lambda *a: posted.append(a), queueable=lambda m: m, sleep=no_wait,
                                  clock=lambda: 0.0))
    return out, robot, manager, posted


EMPTY = np.full((1080, 1920, 3), 20, np.uint8)


def test_asking_again_turns_straight_to_where_they_were_left():
    places.keep("keys", "on the hall table", math.radians(30), math.radians(20))
    out, robot, manager, posted = run([EMPTY], lambda f, w: {"yes": True, "x": .5, "y": .5, "where": "on the hall table"},
                                      asker=lambda f, w: pytest.fail("no sweep when they are where they were left"))
    assert out["found"] and out["where_it_was"] and "where you left them" in out["say"]
    assert robot.media.taken == 1 and len(manager.moves) == 2                               # one closer look, then point
    assert math.degrees(glance._rpy(manager.moves[0].end)[2]) == pytest.approx(30, abs=0.01)
    assert posted[-1][1:] == ([True], 0)


def test_not_where_they_were_left_means_a_sweep_and_saying_so():
    places.keep("keys", "on the hall table", math.radians(30), math.radians(20))
    calls = []

    def asker(frame, what):
        calls.append(1)
        return {"seen": False, "x": .5, "y": .5, "where": ""}

    out, robot, manager, _ = run([EMPTY] * 5, lambda f, w: {"yes": False}, asker)
    assert not out["found"] and calls and "isn't where they left it" in out["how"] and "hall table" in out["how"]
    assert "_yaw" not in out
