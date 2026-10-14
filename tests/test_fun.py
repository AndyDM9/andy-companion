import json
import math
import random

import pytest

from andy_companion import board, fun, stories
from andy_companion.body import giggle


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    monkeypatch.setattr(fun, "FILE", tmp_path / "fun.json")
    monkeypatch.setattr(stories, "BOOKMARK", tmp_path / "story.json")
    monkeypatch.setattr(board, "SCREEN", tmp_path / "screen.json")
    giggle._armed.update(at=None, heard=False)


# --- jokes and riddles ---------------------------------------------------------------------------

def test_no_joke_or_riddle_is_about_age_memory_health_bodies_or_death():
    words = r"\b(old|age|aging|ageing|senior|elderly|forget|memory|doctor|hospital|sick|ill|cold|pill|medicine|" \
            r"die|dead|death|ghost|skeleton|grave|dentures|gummy|fat|diet|wife|husband|blonde|lengua|viej|médico|muert)\b"
    # Topics, not words: a riddle's comb may have teeth and a needle an eye.
    import re
    for lang in ("en", "es"):
        for first, second in fun.JOKES[lang] + fun.RIDDLES[lang]:
            assert not re.search(words, (first + " " + second).lower()), (first, second)


def test_a_joke_is_not_told_again_for_a_month(monkeypatch):
    now = 1_000_000.0
    seen = set()
    for i in range(len(fun.JOKES["en"])):
        seen.add(fun.pick("joke", "en", now=now + i, rng=random.Random(i))["setup"])
    assert len(seen) == len(fun.JOKES["en"])                # every one before any repeats
    again = fun.pick("joke", "en", now=now + 100, rng=random.Random(0))
    assert again["setup"] == fun.JOKES["en"][0][0] or again["setup"] in seen   # the oldest told comes back first
    stored = json.loads(fun.FILE.read_text())
    assert set(stored) == {"joke-en"} and all(k.isdigit() for k in stored["joke-en"])   # numbers and times only


def test_a_riddle_comes_with_its_answer_and_a_kind_way_to_ask_it():
    r = fun.pick("riddle", "es")
    assert r["riddle"] and r["answer"] and "never a correction" in r["how"]
    j = fun.pick("joke", "en")
    assert j["setup"].endswith("?") and j["punchline"] and "Don't explain it" in j["how"]


# --- the wiggle after a punchline --------------------------------------------------------------------

def test_the_antennas_wiggle_once_the_punchline_has_been_said():
    t = [0.0]
    talking = [False]
    pushed = [0]
    g = giggle.Giggle(clock=lambda: t[0], talking=lambda now: talking[0], pushes=lambda: pushed[0])
    giggle._armed["pushes"] = 0
    giggle.arm(now=0.0)
    giggle._armed["pushes"] = 0
    out = []
    for i in range(400):                                    # 4 s at 100 Hz
        t[0] = i * 0.01
        talking[0] = 0.5 <= t[0] < 2.0                      # Andy says the joke from 0.5 s to 2 s
        if talking[0]:
            pushed[0] += 1                                   # its audio arrives as it plays
        out.append(g.step((-0.17, 0.17), True))
    moving = [i for i, p in enumerate(out) if p != (-0.17, 0.17)]
    assert moving and moving[0] * 0.01 >= 2.0               # only after the voice stops
    assert (moving[-1] - moving[0]) * 0.01 <= giggle.WIGGLE_S
    speeds = [abs(a[0] - b[0]) / 0.01 for a, b in zip(out, out[1:])]
    assert max(speeds) < 2.0 and out[-1] == (-0.17, 0.17)
    assert all(abs((p[0] + 0.17) - (p[1] - 0.17)) < 1e-9 for p in out)   # together, a wag


def test_no_wiggle_if_the_joke_was_never_said_or_they_start_talking():
    t = [0.0]
    g = giggle.Giggle(clock=lambda: t[0], talking=lambda now: False)
    giggle.arm(now=0.0)
    t[0] = giggle.ARM_FOR_S + 1
    assert g.step((0.0, 0.0), True) == (0.0, 0.0) and giggle._armed["at"] is None


# --- stories ---------------------------------------------------------------------------------------

def test_every_story_is_public_domain_and_named():
    for s in stories.library():
        year = int(s["from"].rsplit(", ", 1)[1])
        assert year < 1930 and s["author"] and s["paragraphs"]
        assert "gutenberg" not in json.dumps(s).lower() and "[illustration" not in json.dumps(s).lower()


def test_a_long_story_is_read_in_parts_that_end_on_a_paragraph():
    magi = stories.find("the gift of the magi")
    ps = stories.parts(magi)
    assert len(ps) > 5 and "\n\n".join(ps) == "\n\n".join(magi["paragraphs"])
    assert all(len(p.split()) >= stories.PART_WORDS // 3 for p in ps)
    assert ps[0].startswith("One dollar and eighty-seven cents") and ps[-1].endswith("They are the magi.")


def test_shall_i_go_on_and_the_bookmark_kept_for_another_day():
    first = stories.start("Gift of the Magi")
    assert first["part"] == 1 and first["more"] and "Shall I go on?" in first["how"]
    shown = board.showing()
    assert shown["kind"] == "story" and shown["title"] == "The Gift of the Magi"
    assert shown["items"][-1]["title"] == f"Part 1 of {first['of']}"
    assert stories.open_story() == {"title": "The Gift of the Magi", "next": 2, "of": first["of"]}
    second = stories.carry_on()
    assert second["part"] == 2 and second["text"] != first["text"]
    for _ in range(first["of"] - 2):
        last = stories.carry_on()
    assert not last["more"] and stories.open_story() is None


def test_tell_me_a_story_starts_a_short_fable_and_a_different_one_next_time():
    a, b = stories.start(), stories.start()
    assert a["of"] == b["of"] == 1 and a["title"] != b["title"] and a["author"] == "Aesop"
    assert stories.find("the camel")["title"] == "How the Camel Got His Hump"
    missing = stories.start("War and Peace")
    assert missing["not_found"] and len(missing["stories"]) == len(stories.library())


def test_a_story_about_something_is_made_up_and_said_to_be():
    out = stories.make_up("a cat who loves the sea")
    assert out["make_up"] and "a cat who loves the sea" in out["how"] and "made it up" in out["how"]
    assert board.showing() is None                          # nothing from the shelf on the screen


def test_audio_that_was_already_playing_when_the_joke_was_armed_doesn_t_count():
    t = [0.0]
    pushed = [5]                                             # "Sure, here's one!" already queued
    g = giggle.Giggle(clock=lambda: t[0], talking=lambda now: True, pushes=lambda: pushed[0])
    giggle._armed.update(at=0.0, heard=False, pushes=5)
    g.step((0.0, 0.0), True)
    assert not giggle._armed["heard"]                        # nothing new yet
    pushed[0] = 6
    g.step((0.0, 0.0), True)
    assert giggle._armed["heard"]                            # the joke's own audio
