"""Round 3 on the TV (PLAN B23): the line saying what Andy's head is turned to, and the running count of sites
read while Andy looks something up."""

import re
from pathlib import Path

import pytest

from andy_companion import board, live, looking, screen_server, settings, state, turns
from andy_companion.body import looking_at

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "src/andy_companion/pages/screen.html").read_text()


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(state, "FILE", tmp_path / "state.json")
    state.awake()
    looking_at.clear()
    screen_server._live.update(state="", tool="", looking="", at=0.0)
    yield
    looking_at.clear()


# --- "Andy is looking at…" ----------------------------------------------------------------------------------

def test_a_move_says_what_the_head_is_turned_to_for_as_long_as_it_lasts():
    looking_at.set("screen", 2.5, now=100.0)
    assert looking_at.current(now=101.0) == "screen"
    assert looking_at.current(now=102.6) == ""
    looking_at.set("my neighbour's window", 5.0, now=200.0)       # only the few known names
    assert looking_at.current(now=200.0) == ""


def test_the_live_state_carries_it_only_when_there_is_something_to_say():
    clock = turns.TurnClock(clock=lambda: 100.0)
    assert "looking" not in live.derive(clock, True)
    assert live.derive(clock, True, "you") == {"state": "speaking", "tool": "", "looking": "you"}


def test_the_screen_keeps_only_the_known_names_and_hides_it_when_andy_is_not_there():
    with pytest.raises(ValueError):
        screen_server.set_live({"state": "speaking", "tool": "", "looking": "the kitchen at 4 pm"})
    screen_server.set_live({"state": "speaking", "tool": "", "looking": "you"})
    assert screen_server.live_state()["looking"] == "you"
    state.quiet_for(30)
    assert screen_server.live_state()["looking"] == ""
    state.awake()
    screen_server.set_live({"state": "ready", "tool": ""})
    assert screen_server.live_state()["looking"] == ""


def test_the_page_shows_the_line_in_both_languages_and_hides_it_when_empty():
    assert 'id="looking"' in PAGE and ".looking:empty" in PAGE
    for words in ("Looking at you", "Looking at the screen", "Looking around the room", "Pointing at what it found",
                  "Mirándole a usted", "Mirando la pantalla", "Buscando por la habitación", "Señalando lo que encontró"):
        assert words in PAGE
    assert re.search(r'text\(\$\("looking"\), \(ui\.looking && ui\.looking\[s\.looking\]\) \|\| ""\)', PAGE)


# --- The running count of sites read ------------------------------------------------------------------------

def test_the_card_carries_the_count_and_the_screen_says_it():
    looking.show_progress("bus routes", [("Searching", "new bus routes")], 4.2, sites=6)
    how = board.showing()["how"]
    assert how["sites"] == 6 and how["seconds"] == 4.2
    for bad in (True, "6", -1, 5000):
        board.show("research", "x", [], how={"calls": ["research"], "sites": bad})
        assert "sites" not in board.showing()["how"]
    assert 'site: "site read", sites: "sites read"' in PAGE
    assert 'site: "sitio leído", sites: "sitios leídos"' in PAGE
    assert "h.sites === 1 ? ui.site : ui.sites" in PAGE
