"""The TV screen, from a design review (2026-10-14): the found card's attribution clear of the caption, a remote
that can reach Settings, a clock that keeps running without the server, a solid menu over a scrim, and the
date and part of the day in the words people in Florida read."""

import json
import re
import shutil
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from andy_companion import words

PAGE = (Path(__file__).resolve().parents[1] / "src/andy_companion/pages/screen.html").read_text()


def test_the_how_line_sits_at_the_top_of_the_card_and_the_card_keeps_clear_of_the_caption():
    found = re.search(r'<section class="found[^>]*>(.*?)</section>', PAGE, re.S).group(1)
    assert found.index('id="found-how"') < found.index('id="found-h"')           # beside the kind, above the title
    assert re.search(r'<div class="top"><p class="kind" id="found-kind"></p><p class="how" id="found-how"', found)
    # While a caption shows, the card's foot is three caption lines and their padding clear of it.
    assert "--cap-block: calc(var(--cap-size) * 1.28 * 3 + 3vh)" in PAGE
    assert "body.has-caption:not(.showing-code) .found { padding-bottom: calc(var(--cap-block)" in PAGE
    # Its list gives way a whole line at a time, a warning last.
    assert "function fitItems()" in PAGE and 'classList.contains("caution")' in PAGE


def test_a_tv_remote_can_reach_settings_and_stays_in_the_menu():
    keys = PAGE[PAGE.index('document.addEventListener("keydown"'):]
    assert 'a === document.body' in keys and '$("gear").focus()' in keys            # the first arrow or OK
    assert '"ArrowDown"' in PAGE and '"Enter"' in keys
    assert 'e.key === "Tab"' in keys and "e.shiftKey ? prev : next" in keys        # Tab goes round the menu
    assert '"Escape", "Backspace"' in PAGE and "openMenu(false)" in keys
    # A ring a 2022 TV draws: Chromium 85 has no :focus-visible, so the ring is on :focus.
    assert ".gear:focus, .menu button:focus { outline: 4px solid var(--mark)" in PAGE


def test_the_menu_is_a_solid_panel_over_a_scrim():
    assert 'class="scrim" id="scrim"' in PAGE and "body.menu-open .scrim { display: block; }" in PAGE
    scrim_z = int(re.search(r"\.scrim \{[^}]*z-index: (\d+)", PAGE).group(1))
    menu_z = int(re.search(r"\.menu \{[^}]*z-index: (\d+)", PAGE).group(1))
    assert scrim_z < menu_z
    assert re.search(r"\.menu\.glass \{ background: var\(--panel\); -webkit-backdrop-filter: none; backdrop-filter: none; \}", PAGE)


def test_the_clock_keeps_running_and_the_screen_says_when_andy_cannot_be_reached():
    assert "s.server_now * 1000 - Date.now()" in PAGE                               # the server's clock, not the TV's
    assert "setInterval(everySecond, 1000)" in PAGE and "renderClock();" in PAGE
    assert "const OFFLINE_AFTER_MS = 10000;" in PAGE
    assert "body.offline-on .below { opacity:" in PAGE
    assert 'pill.dataset.state = "away"' in PAGE
    offline = re.search(r"\.offline \{([^}]*)\}", PAGE).group(1)
    assert "font-size: clamp(19px, 1.9vw, 32px)" in offline and "font-size: 20px" not in offline
    assert re.search(r"signal: ctl \? ctl\.signal", PAGE)                            # a dead request is given up


def _js_list(name, lg):
    block = re.search(lg + r": \{ days: (\[[^\]]*\]),\s*months: (\[[^\]]*\]),\s*parts: (\{[^}]*\})", PAGE)
    days, months, parts = block.groups()
    parts = json.loads(re.sub(r"(\w+):", r'"\1":', parts))
    return {"days": json.loads(days), "months": json.loads(months), "parts": parts}[name]


@pytest.mark.parametrize("lg", ["en", "es"])
def test_the_screen_s_clock_words_are_words_py_s(lg):
    assert _js_list("days", lg) == words.DAYS[lg]
    assert _js_list("months", lg) == words.MONTHS[lg]
    assert _js_list("parts", lg) == words.PARTS_SHOWN[lg]


def test_dates_are_in_the_order_people_in_florida_read_them():
    wed = datetime(2026, 10, 14, 9, 41)
    assert words.date_shown(wed, "en") == "October 14"
    assert words.date_shown(wed, "en", with_weekday=True) == "Wednesday, October 14"
    assert words.date_shown(wed, "es") == "14 de octubre"
    assert words.date_shown(wed, "es", with_weekday=True) == "miércoles, 14 de octubre"


@pytest.mark.parametrize("hour, en, es", [(9, "morning", "por la mañana"), (14, "afternoon", "por la tarde"),
                                          (18, "evening", "por la tarde"), (20, "evening", "por la noche"),
                                          (23, "night", "por la noche"), (3, "night", "por la noche")])
def test_the_part_of_day_never_reads_as_tomorrow(hour, en, es):
    at = datetime(2026, 10, 14, hour, 0)
    assert words.part_shown(at, "en") == en and words.part_shown(at, "es") == es
    assert "mañana" != words.part_shown(at, "es")


@pytest.mark.skipif(not shutil.which("node"), reason="node is not installed")
def test_the_page_s_own_date_and_part_of_day_match_words_py():
    """Runs the page's clock functions in node and compares them with words.py, hour by hour for two days."""
    script = PAGE[PAGE.index("<script>") + len("<script>"):PAGE.index("</script>")]
    pieces = [re.search(r"  const WORDS = \{.*?\n  \};", script, re.S).group(0),
              re.search(r"  function dateShown\(.*?\n  \}", script, re.S).group(0),
              re.search(r"  function partOfDay\(.*?\n  \}", script, re.S).group(0)]
    start = datetime(2026, 12, 31, 0, 30)
    times = [start + timedelta(hours=h) for h in range(48)]
    probe = "\n".join(pieces) + f"""
    const out = [];
    for (const iso of {json.dumps([t.isoformat() for t in times])}) {{
      const d = new Date(iso + "Z"), h = d.getUTCHours(), part = partOfDay(h);
      for (const lg of ["en", "es"]) {{
        const said = lg === "es" && part === "evening" && h >= 20 ? WORDS.es.parts.night : WORDS[lg].parts[part];
        out.push([dateShown(d, lg, false), dateShown(d, lg, true), said]);
      }}
    }}
    console.log(JSON.stringify(out));
    """
    got = json.loads(subprocess.run(["node", "-e", probe], capture_output=True, text=True, check=True, timeout=30).stdout)
    want = [[words.date_shown(t, lg), words.date_shown(t, lg, with_weekday=True), words.part_shown(t, lg)]
            for t in times for lg in ("en", "es")]
    assert got == want
    # The page itself chooses the Spanish evening's words the same way the probe does.
    assert 'lg === "es" && part === "evening" && h >= 20 ? WORDS.es.parts.night : WORDS[lg].parts[part]' in PAGE


def test_no_words_the_screen_must_never_use():
    lower = PAGE.lower()
    assert "senior" not in lower and "elderly" not in lower
