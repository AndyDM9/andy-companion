"""Andy's screen is read from across a room by older adults: every text colour must reach WCAG AAA
(7:1) against the worst case behind it, in every part of the day (WAI guidance on older users).

The screen is glass over a living scene, so "behind it" is not one colour. Checked for each text:
the plain background; the background under each drifting light at full strength; the worst possible
family photo behind the glass (pure black on a light screen, pure white on a dark one) at the strength
the theme allows; and the glass tint composited over each of those, for text on cards.
"""

import re
from pathlib import Path

import pytest

PAGE = (Path(__file__).resolve().parents[1] / "src/andy_companion/pages/screen.html").read_text()
THEMES = re.findall(r'(:root|body\[data-part="\w+"\])\s*\{([^}]*--ground[^}]*)\}', PAGE)
BASE = dict(re.findall(r"--([\w-]+):\s*([^;]+);", THEMES[0][1]))


def rgb(hex_colour):
    h = hex_colour.strip().lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def rgba(value):
    value = value.strip()
    if value.startswith("#"):
        return rgb(value), 1.0
    parts = [p.strip() for p in re.match(r"rgba\(([^)]*)\)", value).group(1).split(",")]
    return [int(p) / 255 for p in parts[:3]], float(parts[3])


def blend(fg, alpha, bg):
    return [alpha * f + (1 - alpha) * b for f, b in zip(fg, bg)]


def luminance(c):
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_all_four_parts_of_the_day_are_defined():
    assert [name for name, _ in THEMES] == [':root', 'body[data-part="afternoon"]', 'body[data-part="evening"]',
                                           'body[data-part="night"]']


@pytest.mark.parametrize("name, body", THEMES, ids=[n for n, _ in THEMES])
def test_every_text_colour_reaches_7_to_1_against_the_worst_case_behind_it(name, body):
    t = {**BASE, **dict(re.findall(r"--([\w-]+):\s*([^;]+);", body))}
    ground = rgb(t["ground"])
    dark = luminance(ground) < 0.2
    behind = [ground] + [blend(rgb(t[g]), float(t["glow-a"]), ground) for g in ("glow1", "glow2", "glow3")]
    behind.append(blend([1, 1, 1] if dark else [0, 0, 0], float(t["photo-a"]), ground))
    glass, alpha = rgba(t["glass"])
    cards = [blend(glass, alpha, b) for b in behind] + [rgb(t["panel"])]          # the solid panel, when calm
    for fg in ("ink", "soft"):                                                      # the clock, on the scene
        for b in behind:
            assert contrast(rgb(t[fg]), b) >= 7.0, (name, fg, "scene")
    for fg in ("ink", "soft", "mark", "hush"):                                      # text on glass cards
        for b in cards:
            assert contrast(rgb(t[fg]), b) >= 7.0, (name, fg, "card")
    assert contrast(rgb(t["ground"]), rgb(t["ink"])) >= 7.0                         # the caption's reversed colours


def test_calm_and_reduced_transparency_give_solid_panels():
    assert "prefers-reduced-transparency: reduce" in PAGE and "body.calm .glass" in PAGE
    assert "@supports not" in PAGE                                                  # old TV browsers: solid panels
    assert PAGE.count("prefers-reduced-motion: no-preference") >= 4                 # motion only when welcome


def test_the_screen_never_shows_the_persons_words():
    assert '"user"' not in PAGE and "transcript" not in PAGE.lower()


def test_glass_follows_apple_s_rules_where_they_help_reading():
    # Concentric corners: the photo's radius is the frame's radius less the frame's padding.
    pad = re.search(r"\.family \{[^}]*padding: ([\d.]+vh)", PAGE).group(1)
    assert f"border-radius: calc(var(--r) - {pad})" in PAGE
    # More contrast asked for: solid panels and an outline (Increase Contrast, iOS 26).
    assert "prefers-contrast: more" in PAGE
    # The captions are running text: never on glass.
    assert 'class="caption"' in PAGE and not re.search(r'class="caption[^"]*glass', PAGE)
    # Calm motion: no easing that overshoots (a bounce), so nothing springs past where it rests.
    for curve in re.findall(r"cubic-bezier\(([^)]*)\)", PAGE):
        y1, y2 = float(curve.split(",")[1]), float(curve.split(",")[3])
        assert 0 <= y1 <= 1 and 0 <= y2 <= 1, curve


def test_the_page_runs_on_a_2022_tv():
    # Chromium 85: no `inset` shorthand (87); the light's angle animates through @property (85).
    assert not re.search(r"[\s;{]inset\s*:", PAGE)
    assert "@property --light" in PAGE


def test_the_light_on_the_glass_follows_the_sun():
    body = re.search(r"function lightAngle\(hhmm\) \{(.*?)\n  \}", PAGE, re.S).group(1)
    assert "100 +" in body and "160" in body and "return 180" in body
