"""Round 6, the TV's design pass (2026-10-20): Andy drawn small in the state pill doing what the robot does, warnings
that look like warnings at 7:1 in every part of the day, the card as the thing to read, the scam receipt never cut,
and the demo able to hold one scene."""

import importlib.util
import re
from datetime import date
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "src/andy_companion/pages/screen.html").read_text()
THEMES = re.findall(r'(:root|body\[data-part="\w+"\])\s*\{([^}]*--ground[^}]*)\}', PAGE)
BASE = dict(re.findall(r"--([\w-]+):\s*([^;]+);", THEMES[0][1]))


def lum(h):
    c = [int(h.strip().lstrip("#")[i:i + 2], 16) / 255 for i in (0, 2, 4)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    hi, lo = sorted((lum(a), lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


@pytest.mark.parametrize("name, body", THEMES, ids=[n for n, _ in THEMES])
def test_a_warning_reads_at_7_to_1_in_every_part_of_the_day(name, body):
    t = {**BASE, **dict(re.findall(r"--([\w-]+):\s*([^;]+);", body))}
    assert contrast(t["warn"], t["warn-on"]) >= 7.0, (name, "the band")
    for fg in ("ink", "soft", "mark", "hush"):                 # the card's own text on its solid wash
        assert contrast(t[fg], t["warn-wash"]) >= 7.0, (name, fg)
    assert contrast(t["mark"], t["warn-wash"]) >= 7.0          # the receipt's numbered discs


def test_every_part_of_the_day_sets_its_own_warning_colours():
    for name, body in THEMES:
        assert "--warn:" in body and "--warn-on:" in body and "--warn-wash:" in body, name


def test_a_warning_is_a_solid_band_never_glass():
    assert re.search(r"\.found\.warn \{ background: var\(--warn-wash\); -webkit-backdrop-filter: none; backdrop-filter: none; \}", PAGE)
    assert ".found.warn-title h2, .item.caution:not(.step) { background: var(--warn); color: var(--warn-on);" in PAGE
    assert '$("found").classList.toggle("warn", !!showing.lead || caution)' in PAGE
    assert '$("found").classList.toggle("warn-title", showing.kind === "check" && !!showing.lead)' in PAGE


def test_andy_is_drawn_in_the_state_pill_and_moves_as_the_robot_does():
    pill = re.search(r'<p class="state glass" id="state"[^>]*>(.*?)</p>', PAGE, re.S).group(1)
    for part in ('class="andy"', 'class="ant ant-l"', 'class="ant ant-r"', 'class="head"', 'class="eyes"', 'id="state-label"', 'id="looking"'):
        assert part in pill, part
    assert 'class="orb"' not in PAGE                            # the dot it replaced
    for state in ("hearing", "thinking", "asleep", "quiet"):    # lifted, leaning, drooped (and eyes shut asleep)
        assert f'.state[data-state="{state}"] .ant-l' in PAGE, state
    assert '.state[data-state="asleep"] .eyes { transform: scaleY(.18); }' in PAGE
    # Moving only when motion is welcome; the poses themselves are the state, so they stay without it.
    motion = PAGE[PAGE.index("@keyframes ponder") - 2600:PAGE.index("@keyframes ponder")]
    assert "prefers-reduced-motion: no-preference" in motion and "animation: sway-l" in motion
    assert ".andy .ant, .andy .eyes { transform-box: view-box; }" in PAGE      # Chromium 85 has transform-box


def test_the_receipt_is_never_cut_off_and_never_loses_a_step():
    assert "text-overflow: ellipsis; min-width: 0; }" not in PAGE.split(".item.step.short1 > :last-child")[1][:200]
    assert ".item.step.short1 > :last-child { display: -webkit-box; -webkit-line-clamp: 2;" in PAGE
    assert 'if (el.classList.contains("step")) continue;' in PAGE


def test_beside_a_card_the_caption_keeps_to_two_lines_and_the_card_takes_the_width():
    assert "body.has-showing { --cap-block: calc(var(--cap-size) * 1.28 * 2 + 3vh); }" in PAGE
    assert "body.has-showing .caption { -webkit-line-clamp: 2; }" in PAGE
    assert 'const lines = document.body.classList.contains("has-showing") ? 2 : 3;' in PAGE
    assert "body.has-showing .below { grid-template-columns: minmax(0, .6fr) minmax(0, 1.4fr); }" in PAGE
    assert "body:not(.has-showing):not(.has-photo) .below { align-content: center; }" in PAGE


def load_demo():
    spec = importlib.util.spec_from_file_location("demo_screen_for_tests", ROOT / "scripts" / "demo_screen.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_the_demo_names_the_real_coming_saturdays_and_can_hold_one_scene():
    demo = load_demo()
    assert demo.coming_saturdays(date(2026, 10, 20)) == (date(2026, 10, 24), date(2026, 11, 7))
    sat, first = demo.coming_saturdays(date(2026, 10, 31))   # 10-31 is a Saturday, not a first one
    assert sat == date(2026, 10, 31) and first == date(2026, 11, 7)
    sat, first = demo.coming_saturdays(date(2026, 11, 2))    # 11-07 would be a first Saturday: the next one
    assert sat == date(2026, 11, 14) and first == date(2026, 12, 5)
    assert demo.spoken(date(2026, 11, 7)) == "November 7"
    src = (ROOT / "scripts" / "demo_screen.py").read_text()
    assert 'hold = os.environ.get("ANDY_DEMO_SCENE", "")' in src and "October 17" not in src
