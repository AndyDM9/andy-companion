"""Round 9 (B51 to B53): judging without a robot. The demo's front page shows the simulated search's film, served by
the screen server's media route; the simulation fetches Pollen's scene itself, checked against PyPI's checksum."""

import importlib.util
import math
import urllib.request
from pathlib import Path

import pytest

from andy_companion import board, screen_server

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")


def test_the_screen_server_serves_only_the_media_it_was_given(monkeypatch):
    monkeypatch.setattr(screen_server, "MEDIA", {"/media/sim-search.mp4": (b"\x00\x00\x00 ftypisom film", "video/mp4")})
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    try:
        base = f"http://127.0.0.1:{httpd.server_address[1]}"
        with urllib.request.urlopen(f"{base}/media/sim-search.mp4", timeout=5) as r:
            assert r.read().endswith(b"film") and r.headers["Content-Type"] == "video/mp4"
            assert "media-src 'self'" in r.headers["Content-Security-Policy"]
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(f"{base}/media/other.mp4", timeout=5)
    finally:
        httpd.shutdown()


def test_the_front_page_shows_the_film_when_there_is_one(monkeypatch):
    spec = importlib.util.spec_from_file_location("demo_for_judges", ROOT / "scripts" / "demo_screen.py")
    demo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(demo)
    monkeypatch.setattr(screen_server, "MEDIA", {})
    assert b"<video" not in demo.index_page()
    monkeypatch.setattr(screen_server, "MEDIA", {"/media/sim-search.mp4": (b"x", "video/mp4")})
    page = demo.index_page().decode()
    assert '<video src="/media/sim-search.mp4"' in page and "muted" in page and "in simulation" in page
    assert (ROOT / "docs/images/sim-search.mp4").stat().st_size < 3_000_000
    assert (ROOT / "docs/images/sim-search.gif").stat().st_size < 5_000_000


def test_the_simulation_s_camera_and_scoring_are_right():
    pytest.importorskip("mujoco")
    import numpy as np

    spec = importlib.util.spec_from_file_location("finder_sim_for_tests", ROOT / "sim" / "finder_sim.py")
    fs = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fs)
    import mujoco
    q = fs.camera_quat(0.0, 0.0)
    m = np.zeros(9)
    mujoco.mju_quat2Mat(m, q)
    assert np.allclose(m.reshape(3, 3)[:, 2], [-1, 0, 0], atol=1e-9)        # looking along +x: the camera's -z
    assert fs.angle_between((0.1, 0.2), (0.1, 0.2)) == pytest.approx(0.0, abs=1e-6)
    assert fs.angle_between((0.0, 0.0), (math.radians(10), 0.0)) == pytest.approx(10.0)
    rows = [{"present": True, "pointed": True, "found": True, "error_deg": 1.0, "seconds": 3.0},
            {"present": False, "pointed": False, "found": False, "error_deg": None, "seconds": 3.0}]
    s = fs.summary(rows)
    assert (s["pointed"], s["present"], s["false_finds"], s["absent"]) == (1, 1, 0, 1)


def test_the_doctor_says_finder_tries_are_kept_before_filming(monkeypatch):
    spec = importlib.util.spec_from_file_location("doctor_for_tests", ROOT / "scripts" / "doctor.py")
    doctor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(doctor)
    monkeypatch.delenv("ANDY_FINDER_RECORD", raising=False)
    assert doctor.finder_recording({}) == ""
    assert doctor.finder_recording({"ANDY_FINDER_RECORD": " /home/x/andy-finder-tries "}) == "/home/x/andy-finder-tries"
    monkeypatch.setenv("ANDY_FINDER_RECORD", "/elsewhere")
    assert doctor.finder_recording({}) == "/elsewhere"


def test_the_hood_says_its_turns_are_samples_only_in_the_demo(monkeypatch):
    monkeypatch.setattr(screen_server, "INDEX", None)
    assert screen_server.hood_state()["sample"] is False
    monkeypatch.setattr(screen_server, "INDEX", b"<p>the demo</p>")
    assert screen_server.hood_state()["sample"] is True
    page = (ROOT / "src/andy_companion/pages/hood.html").read_text()
    assert "s.sample ? ui.sampleLede : ui.lede" in page and page.count("sampleLede:") == 2
