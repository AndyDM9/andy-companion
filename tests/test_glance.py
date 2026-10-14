import importlib.util
import json
import math
import urllib.request

import numpy as np
import pytest

from andy_companion import board, screen_server, settings, setup_page
from andy_companion.body import glance, presence

TICK = 0.01


def pose(yaw_deg=0.0, pitch_deg=0.0, z=0.01):
    return glance._pose(0.0, math.radians(pitch_deg), math.radians(yaw_deg), [0.0, 0.0, z])


def yaw_of(p):
    return glance._rpy(p)[2]


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")


# --- where the screen is ---------------------------------------------------------------------------

def test_no_glance_until_the_screen_s_place_is_set():
    assert glance.direction({"tv_yaw": None}) is None
    assert glance.direction({"tv_yaw": 40, "tv_glance": False}) is None
    yaw, pitch = glance.direction({"tv_yaw": 40, "tv_height": "above"})
    assert yaw == pytest.approx(math.radians(40)) and pitch == pytest.approx(math.radians(-12))   # up is negative
    assert glance.direction({"tv_yaw": 400})[0] == pytest.approx(math.radians(glance.MAX_YAW_DEG))


def test_the_settings_page_checks_the_screen_s_place():
    assert setup_page.clean({"tv_yaw": "45", "tv_height": "below", "tv_glance": True}) == \
        {"tv_yaw": 45, "tv_height": "below", "tv_glance": True}
    assert setup_page.clean({"tv_yaw": None}) == {"tv_yaw": None}
    for bad in ({"tv_yaw": 200}, {"tv_yaw": "left"}, {"tv_height": "ceiling"}):
        with pytest.raises(ValueError):
            setup_page.clean(bad)


# --- when ------------------------------------------------------------------------------------------

def free(w, now):
    return w.ready(now, listening=False, move_playing=False, awake=True)


def test_a_new_card_is_glanced_at_once_and_its_progress_is_not():
    w = glance.Watcher()
    w.saw("weather|Weather|", 0.0)                      # already showing when Andy started: not new
    assert not free(w, 0.1)
    w.saw("research|Looking into: the market|", 30.0)
    assert free(w, 30.1)
    w.saw("research|Looking into: the market|", 31.0)   # the same card, with a new step
    assert not free(w, 31.1)


def test_never_while_the_person_speaks_and_not_long_after():
    w = glance.Watcher()
    w.saw(None, 0.0)
    w.saw("look_up|What I found|", 10.0)
    assert not w.ready(11.0, listening=True, move_playing=False, awake=True)
    assert not w.ready(12.0, listening=False, move_playing=True, awake=True)
    assert free(w, 13.0)                                # they stopped: now
    w.saw("news|Local news|", 50.0)
    assert not w.ready(51.0, listening=True, move_playing=False, awake=True)
    assert not free(w, 50.0 + glance.WAIT_S + 0.1)      # too late to point at it: let go


def test_at_most_one_glance_in_a_while_and_none_when_resting():
    w = glance.Watcher()
    w.saw(None, 0.0)
    w.saw("a|1|", 100.0)
    assert free(w, 100.0)
    w.saw("b|2|", 105.0)
    assert not free(w, 105.0)                           # too soon after the last
    w.saw("c|3|", 200.0)
    assert not w.ready(200.0, listening=False, move_playing=False, awake=False)
    assert not free(w, 201.0)                           # dropped, not saved for later


# --- how -------------------------------------------------------------------------------------------

def test_the_glance_turns_to_the_screen_holds_and_comes_back_exactly():
    start = pose(yaw_deg=-20, pitch_deg=3)
    g = glance.Glance(start, (-0.17, 0.17), (math.radians(70), math.radians(-12)))
    ts = np.arange(0.0, g.duration + TICK / 2, TICK)
    heads = [g.evaluate(t) for t in ts]
    first, last = heads[0], heads[-1]
    assert np.allclose(first[0], start) and np.allclose(last[0], start)
    held = g.evaluate(g.turn_s + glance.HOLD_S / 2)
    roll, pitch, yaw = glance._rpy(held[0])
    assert yaw == pytest.approx(math.radians(70)) and pitch == pytest.approx(math.radians(-12)) and roll == pytest.approx(0)
    assert np.allclose(held[0][:3, 3], start[:3, 3])    # turns in place; doesn't move the head
    yaws = [yaw_of(h[0]) for h in heads]
    speed = max(abs(a - b) for a, b in zip(yaws, yaws[1:])) / TICK
    assert speed <= glance.PEAK_RAD_S * 1.01            # gentle, however far the screen is
    assert held[1][1] - 0.17 == pytest.approx(glance.PERK_RAD)          # antennas perk up, mirrored
    assert held[1][0] + 0.17 == pytest.approx(-glance.PERK_RAD)
    assert tuple(last[1]) == pytest.approx((-0.17, 0.17)) and all(h[2] == 0.0 for h in heads)   # body stays


def test_the_short_way_round():
    g = glance.Glance(pose(yaw_deg=170), (0.0, 0.0), (math.radians(-170), 0.0))
    assert g.dyaw == pytest.approx(math.radians(20))


class Robot:
    def __init__(self):
        self.head = pose(yaw_deg=-10)

    def get_current_head_pose(self):
        return self.head


class Manager:
    def __init__(self):
        self.current_robot = Robot()
        self.queued = []

    def queue_move(self, move):
        self.queued.append(move)


def test_in_the_movement_loop_a_new_card_queues_one_glance_of_andy_s_own(monkeypatch):
    monkeypatch.setattr(glance, "queueable", lambda g: g)
    monkeypatch.setattr(glance, "_seen", {"key": None, "tv": (math.radians(45), 0.0), "awake": True, "fresh": True})
    monkeypatch.setattr(presence, "recent", lambda *a, **k: True)   # someone is here
    m = Manager()
    glance.step(m, 0.0, (-0.17, 0.17), listening=False, move_playing=False, tracking=True)
    glance._seen["key"] = "look_up|What I found|"
    assert glance.step(m, 1.0, (-0.17, 0.17), listening=False, move_playing=False, tracking=True)
    assert not glance.step(m, 1.01, (-0.17, 0.17), listening=False, move_playing=False, tracking=True)
    assert len(m.queued) == 1 and m.queued[0].andy_owns_head
    # With face following off (the person turned it off, or Andy is asleep) there is no glance.
    m2 = Manager()
    glance._seen["key"] = None
    glance.step(m2, 0.0, (0, 0), listening=False, move_playing=False, tracking=False)
    glance._seen["key"] = "news|Local news|"
    assert not glance.step(m2, 1.0, (0, 0), listening=False, move_playing=False, tracking=False)


def test_the_thread_reads_the_screen_the_settings_and_whether_andy_rests(monkeypatch, tmp_path):
    from andy_companion import state

    monkeypatch.setattr(state, "FILE", tmp_path / "state.json")
    monkeypatch.setattr(glance, "_seen", {"key": None, "tv": None, "awake": True, "fresh": False})
    settings.update(tv_yaw=-60, tv_height="level")
    board.show("weather", "Weather", [])
    glance._look_once()
    assert glance._seen["key"] == "weather|Weather|" and glance._seen["tv"][0] == pytest.approx(math.radians(-60))
    assert glance._seen["awake"] and glance._seen["fresh"]


@pytest.mark.skipif(importlib.util.find_spec("reachy_mini") is None, reason="needs the robot's environment")
def test_pollen_s_queue_takes_the_glance():
    from reachy_mini.motion.move import Move

    move = glance.queueable(glance.Glance(pose(), (0.0, 0.0), (0.5, 0.0)))
    assert isinstance(move, Move) and move.andy_owns_head and move.duration > 2


# --- the check on the settings page ----------------------------------------------------------------

def test_save_and_show_me_puts_a_check_card_on_the_screen():
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    try:
        base = f"http://127.0.0.1:{httpd.server_address[1]}"

        def post(path, body):
            req = urllib.request.Request(f"{base}{path}?s={board.tokens()['setup']}", method="POST",
                                         data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())

        out = post("/api/setup", {"name": "Anna", "settings": {"tv_yaw": 50, "tv_height": "above"}})
        assert out["changed"] == ["where the screen is", "how high the screen is"]
        post("/api/setup/show-screen", {})
        card = board.showing()
        assert card["kind"] == "where" and card["until"] - card["at"] == board.CHECK_FOR_S
        assert glance.card_key(card) == "where|Andy looks here|"
    finally:
        httpd.shutdown()
