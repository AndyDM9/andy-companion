"""Andy's screen is read from across a room by older adults: every text colour must reach WCAG AAA
(7:1) against its background, in every part of the day (WAI guidance on older users)."""

import re
from pathlib import Path

import pytest

PAGE = (Path(__file__).resolve().parents[1] / "src/andy_companion/pages/screen.html").read_text()
THEMES = re.findall(r'(:root|body\[data-part="\w+"\])\s*\{([^}]*--ground[^}]*)\}', PAGE)


def luminance(hex_colour):
    channels = [int(hex_colour[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    channels = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in channels]
    return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def test_all_four_parts_of_the_day_are_defined():
    assert [name for name, _ in THEMES] == [':root', 'body[data-part="afternoon"]', 'body[data-part="evening"]',
                                           'body[data-part="night"]']


@pytest.mark.parametrize("name, body", THEMES, ids=[n for n, _ in THEMES])
def test_every_text_colour_reaches_7_to_1(name, body):
    tokens = dict(re.findall(r"--(\w+):\s*(#[0-9a-fA-F]{6})", body))
    for fg in ("ink", "soft", "mark", "hush"):
        for bg in ("ground", "panel"):
            assert contrast(tokens[fg], tokens[bg]) >= 7.0, (name, fg, bg)
    assert contrast(tokens["ground"], tokens["ink"]) >= 7.0          # the caption's reversed colours


def test_the_screen_never_shows_the_persons_words():
    assert '"user"' not in PAGE and "transcript" not in PAGE.lower()
