import io
import json
import time

import pytest

from andy_companion import health, state


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(state, "FILE", tmp_path / "state.json")
    state.awake()
    health._cache.update(local=[], cloud=[], local_at=0.0, cloud_at=0.0, busy=False)


def test_the_robot_tile_reads_the_daemon():
    ok = lambda url, timeout=None: io.BytesIO(json.dumps({"state": "running", "version": "1.12.0rc1"}).encode())
    assert health.daemon(ok) == {"name": "Robot", "status": "ok", "detail": "Daemon running, version 1.12.0rc1"}

    def down(url, timeout=None):
        raise OSError("refused")
    assert health.daemon(down)["status"] == "warn"


def test_andy_tile_says_quiet_asleep_or_silent():
    now = 1000.0
    assert health.mode_and_app(now - 2, now)[0]["detail"] == "Awake and listening"
    assert health.mode_and_app(now - 60, now)[0]["status"] == "warn"
    state.quiet_for(30)
    assert "wake listener" in health.mode_and_app(now, now)[0]["detail"]


class Run:
    def __init__(self, states):
        self.states = states

    def __call__(self, cmd, **kw):
        name = cmd[cmd.index("--name") + 1]
        return type("R", (), {"stdout": json.dumps({"status": {"state": self.states[name]}})})()


def test_nebius_endpoints_say_whether_they_cost_money(monkeypatch):
    monkeypatch.setattr(health.shutil, "which", lambda name: "/usr/bin/nebius")
    tiles = health.cloud(Run({"andy-vision": "RUNNING", "andy-guard": "STOPPED"}))
    assert [t["detail"] for t in tiles] == ["Running (it costs while on)", "Stopped (no cost)"]
    monkeypatch.setattr(health.shutil, "which", lambda name: None)
    assert {t["status"] for t in health.cloud()} == {"unknown"}


def test_tiles_refresh_in_the_background_and_never_hold_up_the_page(monkeypatch):
    monkeypatch.setattr(health, "daemon", lambda: health.tile("Robot", "ok", "Daemon running"))
    monkeypatch.setattr(health, "voice", lambda: health.tile("Voice", "ok", "ready"))
    monkeypatch.setattr(health, "cloud", lambda: [health.tile("Eyes on Nebius", "off", "Stopped (no cost)")])
    health.tiles(time.time(), None, {"used": 950, "limit": 1000})                    # starts the refresh; never waits
    for _ in range(100):
        if health._cache["local"]:
            break
        time.sleep(0.01)
    names = {t["name"]: t for t in health.tiles(time.time(), None, {"used": 950, "limit": 1000})}
    assert names["Tavily"]["status"] == "warn" and names["Weather"]["status"] == "unknown"
    assert names["Eyes on Nebius"]["detail"] == "Stopped (no cost)"


def test_pay_as_you_go_past_the_plan_is_said_plainly_not_as_a_warning(monkeypatch):
    """2026-10-28 on the robot's hood page: "4964 of 1000 credits" in yellow, read as a fault; pay as you go was on."""
    monkeypatch.setattr(health, "daemon", lambda: health.tile("Robot", "ok", "Daemon running"))
    monkeypatch.setattr(health, "voice", lambda: health.tile("Voice", "ok", "ready"))
    monkeypatch.setattr(health, "cloud", lambda: [])
    health._refresh(time.time(), None, {"used": 4964, "limit": 1000, "paygo": 3964}, False)
    tavily = next(t for t in health._cache["local"] if t["name"] == "Tavily")
    assert tavily["status"] == "ok" and tavily["detail"] == "4,964 credits this month, 1,000 in the plan and 3,964 pay as you go"
    health._refresh(time.time(), None, {"used": 950, "limit": 1000, "paygo": None}, False)
    tavily = next(t for t in health._cache["local"] if t["name"] == "Tavily")
    assert tavily["status"] == "warn" and tavily["detail"] == "950 of 1,000 credits this month"
