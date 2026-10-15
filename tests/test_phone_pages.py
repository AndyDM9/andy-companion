"""The two phone pages, settings (setup.html) and family (family.html): Andy Glass on a phone, readable by anyone.

Checked from the pages' own source: every text colour at 7:1 against what is behind it (the solid panel,
the fields, and the page with each of the soft lights at full strength), every field's outline at 3:1, the
round corners and type sizes from the design review, the English and Spanish string tables, no browser
pop-ups, and the words we never use.
"""

import json
import re
from pathlib import Path

import pytest

from andy_companion import setup_page

PAGES = Path(__file__).resolve().parents[1] / "src/andy_companion/pages"
SOURCES = {name: (PAGES / name).read_text() for name in ("setup.html", "family.html")}


def rgb(hex_colour):
    h = hex_colour.strip().lstrip("#")
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)]


def luminance(c):
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b):
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def blend(fg, alpha, bg):
    return [alpha * f + (1 - alpha) * b for f, b in zip(fg, bg)]


def themes(page):
    """The light tokens (:root) and the dark ones (inside prefers-color-scheme: dark), each complete."""
    blocks = re.findall(r":root\s*\{([^}]*--ground[^}]*)\}", SOURCES[page])
    assert len(blocks) == 2, "a light and a dark theme"
    light = dict(re.findall(r"--([\w-]+):\s*([^;]+);", blocks[0]))
    dark = {**light, **dict(re.findall(r"--([\w-]+):\s*([^;]+);", blocks[1]))}
    return {"light": light, "dark": dark}


CASES = [(page, theme) for page in SOURCES for theme in ("light", "dark")]


@pytest.mark.parametrize("page, theme", CASES)
def test_every_text_colour_reaches_7_to_1_against_everything_behind_it(page, theme):
    t = themes(page)[theme]
    ground = rgb(t["ground"])
    lit = [ground] + [blend(rgb(t[g]), float(t["glow-a"]), ground) for g in ("glow1", "glow2", "glow3")]
    behind = lit + [rgb(t["panel"]), rgb(t["field"])] + ([rgb(t["chosen"])] if "chosen" in t else [])
    for text in ("ink", "soft", "mark", "error"):
        worst = min(contrast(rgb(t[text]), b) for b in behind)
        assert worst >= 7, f"{page} {theme}: --{text} is {worst:.2f}:1 at worst"
    assert contrast(rgb(t["on-mark"]), rgb(t["mark"])) >= 7          # a button's words on its colour
    if "on-error" in t:
        assert contrast(rgb(t["on-error"]), rgb(t["error"])) >= 7    # a deletion waiting for its second tap
    assert contrast(rgb(t["ground"]), rgb(t["ink"])) >= 7            # the save bar: the TV's caption colours


@pytest.mark.parametrize("page, theme", CASES)
def test_every_field_outline_reaches_3_to_1(page, theme):
    t = themes(page)[theme]
    for behind in ("panel", "field", "ground"):
        assert contrast(rgb(t["line"]), rgb(t[behind])) >= 3, f"{page} {theme}: --line on --{behind}"


@pytest.mark.parametrize("page", SOURCES)
def test_the_tv_s_round_corners_lit_edge_mark_and_type(page):
    src = SOURCES[page]
    t = themes(page)["light"]
    assert 16 <= int(t["r"].rstrip("px")) <= 20 and 16 <= int(t["r-in"].rstrip("px")) <= 20
    assert "inset 0 1px 0 var(--shine)" in src                      # the panels' lit top edge
    assert 'class="orb"' in src and ">Andy</p>" in src              # the Andy mark
    assert "/fonts/atkinson-hyperlegible-400.woff2" in src
    for rule in ("hint", "when"):                                    # small print is never under 17px
        sizes = re.findall(r"\." + rule + r"\b[^{]*\{[^}]*font-size:\s*(\d+)px", src)
        assert sizes and all(int(s) >= 17 for s in sizes), rule
    assert "backdrop-filter" not in src                              # no text on see-through glass


def test_checkboxes_keep_their_size_and_targets_are_big_enough():
    src = SOURCES["setup.html"]
    assert re.search(r"\.choices input \{[^}]*flex: none", src)
    for page, src in SOURCES.items():
        heights = [int(h) for h in re.findall(r"min-height:\s*(\d+)px", src)]
        assert heights and min(h for h in heights if h >= 40) >= 48, page


@pytest.mark.parametrize("page", SOURCES)
def test_no_browser_pop_ups(page):
    script = SOURCES[page].split("<script>", 1)[1]
    assert not re.search(r"\b(alert|confirm|prompt)\(", script)


def table(page):
    return json.loads(re.search(r'<script type="application/json" id="ui">(.*?)</script>', SOURCES[page], re.S).group(1))


@pytest.mark.parametrize("page", SOURCES)
def test_english_and_spanish_say_the_same_things(page):
    ui = table(page)
    assert set(ui["en"]) == set(ui["es"])
    used = set(re.findall(r'data-t[pa]?="(\w+)"', SOURCES[page]))
    used |= set(re.findall(r'\bt\("(\w+)"[,)]', SOURCES[page]))
    assert used <= set(ui["en"]), used - set(ui["en"])
    for key, value in ui["es"].items():
        if isinstance(value, str):
            assert not re.search(r"\b(tú|tu|puedes|eliges)\b", value), f"{key}: usted, not tú"


def test_every_change_the_settings_page_reports_has_its_spanish():
    spanish = table("setup.html")["es"]["changed"]
    assert set(setup_page.SHOWN.values()) <= set(spanish), set(setup_page.SHOWN.values()) - set(spanish)


@pytest.mark.parametrize("page", SOURCES)
def test_the_words_we_never_use(page):
    words = re.sub(r"<style>.*?</style>", "", SOURCES[page], flags=re.S).lower()
    for banned in (r"\bseniors?\b", r"\belderly\b", r"\bsafe(ty|ly)?\b(?!-)", r"\bmonitor(ing|s|ed)\b", r"check on",
                   r"peace of mind", r"\blonel", r"\bwhere (they|she|he) (is|are)\b", r"\bis home\b"):
        assert not re.search(banned, words), banned


def test_the_family_page_learns_the_households_language_and_the_persons_name(tmp_path, monkeypatch):
    from andy_companion import board, screen_server, settings
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    board.share("I had a lovely walk by the sea.")
    out = screen_server.family_state()
    assert out["language"] == "en" and out["person_name"] is None and "," in out["shared"][0]["when"]
    settings.update(language="es", person_name="Rosa")
    out = screen_server.family_state()
    assert out["language"] == "es" and out["person_name"] == "Rosa"
    assert " de " in out["shared"][0]["when"] and "am" not in out["shared"][0]["when"]   # "miércoles, 14 de octubre, 21:05"
