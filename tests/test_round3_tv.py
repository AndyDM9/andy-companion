"""Round 3 on the TV (PLAN B19, B20): what Andy looked at when it searched for something, and the scam check's
receipt; and the card kinds the family side puts up (a family note, a suggestion)."""

import asyncio
import base64
import builtins
import importlib.util
import io
import json
import logging
import re
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from andy_companion import board, finder, scamcheck, screen_server, settings, web

ROOT = Path(__file__).resolve().parents[1]
PAGE = (ROOT / "src/andy_companion/pages/screen.html").read_text()
JPEG = b"\xff\xd8 a small view"


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    screen_server.forget_views()
    yield
    screen_server.forget_views()


# --- B19: what Andy looked at -------------------------------------------------------------------------------

def test_the_views_live_in_memory_for_two_minutes_then_are_forgotten():
    screen_server.set_views([JPEG, None, JPEG, JPEG], [False, False, True, True], 2, now=1000)
    v = screen_server.views(now=1000 + 60)
    assert v == {"at": 1000, "pictures": [True, False, True, True], "seen": [False, False, True, True], "chosen": 2}
    assert screen_server.view(0, now=1060) == JPEG and screen_server.view(1, now=1060) == b""
    assert screen_server.view(9, now=1060) == b""
    assert screen_server.views(now=1000 + screen_server.FRAME_FOR_S + 1) is None
    assert screen_server._views["jpegs"] == []                     # the pictures themselves are gone
    assert screen_server.view(0, now=1001) == b""                  # and don't come back


def test_the_views_are_capped_in_number_size_and_kind():
    big = b"\xff\xd8" + b"x" * screen_server.MAX_VIEW
    for jpegs, seen, chosen in [([JPEG] * 5, [False] * 5, None),      # more than four
                               ([], [], None),                         # none
                               ([big], [True], 0),                     # too big
                               ([b"<html>"], [False], None),           # not a picture
                               ([JPEG, JPEG], [True], None),           # seen doesn't match
                               ([JPEG, None], [False, True], 1),       # chose a view with no picture
                               ([JPEG, JPEG], [True, False], 1),       # chose one not seen
                               ([JPEG], [1], None),                    # seen isn't true or false
                               ([JPEG], [True], True)]:                # a choice that isn't a number
        with pytest.raises(ValueError):
            screen_server.set_views(jpegs, seen, chosen)
    assert screen_server.views() is None
    assert screen_server.MAX_VIEWS == 4 and screen_server.MAX_VIEW <= 400_000


def test_the_views_never_touch_the_disk_or_the_log(monkeypatch, caplog):
    def no_disk(*args, **kwargs):
        raise AssertionError("written to disk")

    real_open = builtins.open

    def open_for_reading_only(file, mode="r", *args, **kwargs):
        if any(c in mode for c in "wax+"):
            no_disk()
        return real_open(file, mode, *args, **kwargs)

    monkeypatch.setattr(builtins, "open", open_for_reading_only)
    monkeypatch.setattr(Path, "write_bytes", no_disk)
    monkeypatch.setattr(Path, "write_text", no_disk)
    with caplog.at_level(logging.DEBUG):
        screen_server.set_views([JPEG] * 4, [True, False, False, False], 0)
        assert screen_server.view(0) == JPEG and screen_server.views()["chosen"] == 0
    assert not caplog.records


def test_the_views_go_only_with_the_card_of_the_same_search():
    screen_server.set_views([JPEG] * 4, [False, True, False, False], 1, now=1000)
    seen = {"kind": "seen", "title": "Your glasses", "items": [], "at": 1001}
    assert screen_server.views_for(seen, now=1002)["chosen"] == 1
    assert screen_server.views_for({**seen, "kind": "looked"}, now=1002) is not None
    assert screen_server.views_for({**seen, "kind": "news"}, now=1002) is None          # another card: no views
    assert screen_server.views_for({**seen, "at": 1000 + 90}, now=1100) is None         # a later search's card
    assert screen_server.views_for(None, now=1002) is None


def test_the_screen_state_carries_the_views_with_the_card(monkeypatch):
    monkeypatch.setattr(screen_server, "weather_card", lambda now=None: None)
    screen_server.set_views([JPEG] * 4, [False] * 4, None)
    board.show("looked", "I couldn't see your glasses", [])
    state = screen_server.screen_state()
    assert state["views"]["pictures"] == [True] * 4 and state["views"]["chosen"] is None
    assert "jpegs" not in json.dumps(state) and "\\u00ff" not in json.dumps(state)     # no picture in the JSON


class Robot:
    class Media:
        n = 0

        def get_frame(self):
            self.n += 1
            return np.full((1080, 1920, 3), self.n * 30, dtype=np.uint8)

    media = Media()

    def get_current_head_pose(self):
        from andy_companion.body import glance

        return glance._pose(0.0, 0.0, 0.0, [0.0, 0.0, 0.01])

    def get_current_joint_positions(self):
        return [0.0] * 7, [0.0, 0.0]


def test_the_finder_posts_all_four_small_views_to_the_screen(monkeypatch):
    import cv2

    monkeypatch.setenv("ANDY_FINDER_ZOOM", "off")   # the views as posted; zooming in and its closer look: test_round7_zoom

    sent = []

    def opener(req, timeout=None):
        sent.append((req.full_url, json.loads(req.data)))
        return io.BytesIO(b'{"ok": true}')

    posted = []

    def poster(views, seen, chosen):
        posted.append((views, seen, chosen))
        finder.post_views(views, seen, chosen, opener=opener)

    def asker(frame, what):
        hit = int(frame[0, 0, 0]) == 60
        return {"seen": hit, "x": 0.5, "where": "on the shelf" if hit else ""}

    async def no_wait(s):
        return None

    class Manager:
        def queue_move(self, move):
            pass

    Robot.Media.n = 0
    robot = Robot()
    robot.media = Robot.Media()
    out = asyncio.run(finder.find("glasses", robot, Manager(), asker=asker, poster=poster, queueable=lambda m: m,
                                  sleep=no_wait, clock=lambda: 0.0))
    assert out["found"]
    assert sent[0][1]["views"] == [None] * 4                    # the TV cleared first (round 7)
    url, body = sent[-1]
    assert "/api/views?t=" + board.tokens()["screen"] in url
    assert body["seen"] == [False, True, False, False] and body["chosen"] == 1 and len(body["views"]) == 4
    for b64 in body["views"]:
        picture = cv2.imdecode(np.frombuffer(base64.b64decode(b64), np.uint8), cv2.IMREAD_COLOR)
        assert picture.shape[1] == finder.VIEW_WIDTH == 480                        # small: 480 px across
        assert len(base64.b64decode(b64)) < screen_server.MAX_VIEW
    screen_server.set_views([base64.b64decode(b) for b in body["views"]], body["seen"], body["chosen"])
    assert screen_server.views()["chosen"] == 1                                    # the server takes what was sent


def test_the_tv_draws_the_views_as_a_numbered_strip():
    assert "/frame?" not in PAGE                                         # the old single frame is gone
    strip = re.search(r"function viewStrip\(v, showing\) \{(.*?)\n  \}", PAGE, re.S).group(1)
    assert '"/view?t=" + encodeURIComponent(token) + "&i=" + i' in strip
    assert 'make("span", "n", String(i + 1))' in strip                  # numbered in the order Andy turned
    assert 'chosen ? " chosen"' in strip and 'beside.append(make("p", "where", where || ui.seenHere));' in strip
    assert "img.onerror" in strip                                        # forgotten views: no broken image
    assert 'const VIEW_KINDS = ["seen", "looked"];' in PAGE
    # The selected frame is painted inside the picture; an outside shadow is clipped by #items.
    assert ".view.chosen .pic::after { border: 4px solid var(--mark); }" in PAGE
    # 2026-10-25: four views with "seen here too" under each narrow one ran into their numbers. The chosen view is
    # large with the words beside it; the number sits on each picture; every label under a view is one line.
    assert "pic.append(make(\"span\", \"n\", String(i + 1)));" in strip
    assert ".view .n { position: absolute;" in PAGE
    assert "white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }" in PAGE.split(".view figcaption {")[1][:200]
    assert '.views.has-chosen .view.chosen { flex: none; width: var(--cw, 56%); }' in PAGE
    assert 'views.style.setProperty("--cw", w + "%")' in PAGE
    assert "padding-top: 56.25%" in PAGE and not re.search(r"aspect-ratio\s*:", PAGE)   # Chromium 85 has none
    ui = PAGE[PAGE.index("const UI = {"):PAGE.index("let ui = UI.en;")]
    for key in ("order", "seenHere", "seenToo", "notSeen", "noPicture", "looked"):
        assert len(re.findall(rf"\b{key}: \"", ui)) == 2, key                    # in English and in Spanish
    assert "left" not in re.search(r'order: "([^"]*)"', PAGE).group(1).lower()


# --- B20: the scam check's receipt -------------------------------------------------------------------------

@pytest.fixture
def check_message(monkeypatch):
    core = types.ModuleType("reachy_mini_conversation_app.tools.core_tools")
    core.Tool, core.ToolDependencies = type("Tool", (), {}), object
    for name in ("reachy_mini_conversation_app", "reachy_mini_conversation_app.tools"):
        monkeypatch.setitem(sys.modules, name, types.ModuleType(name))
    monkeypatch.setitem(sys.modules, core.__name__, core)
    spec = importlib.util.spec_from_file_location("andy_tool_check_message_r3", ROOT / "tools" / "check_message.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    def run(message):
        return asyncio.run(module.CheckMessage()(None, message=message))
    run.module = module
    return run


SCAM = ("URGENT from Prize Center: you WON $25,000! Call 1-888-555-0199 or 305 555 0142 now, pay the fee at "
        "www.prize-claims.example or bit.ly/win25 and email claims@prize-center.example with your account 4417123456789113.")
EVIDENCE = "Call 1-888-555-0199 or 305 555 0142 now, pay the fee at www.prize-claims.example or bit.ly/win25 and email claims@prize-center.example"
WARNING = {"source": "consumer.ftc.gov", "title": "Fake prize, sweepstakes, and lottery scams", "summary": "…",
           "url": "https://consumer.ftc.gov/articles/fake-prize-sweepstakes-and-lottery-scams"}
HOW = {"calls": ["search"], "depth": "advanced", "seconds": 2.4, "credits": 2}


def no_message_numbers_links_or_emails(card, message=SCAM):
    # The warning's own address (its "url", a Tavily result's) is the one link allowed, and never the message's.
    card = {**card, "items": [{k: v for k, v in it.items() if k != "url"} for it in card["items"]]}
    text = json.dumps({k: card[k] for k in ("title", "items")}, ensure_ascii=False)
    for run in re.findall(r"\d+", message):                             # none of the message's numbers, anywhere
        assert not re.search(rf"(?<!\d){run}(?!\d)", text) or run in ("3", "5"), (run, text)   # model names: "3", "3.5"
    quoted = json.dumps([card["title"]] + card["items"][:2], ensure_ascii=False)
    assert not re.search(r"\d", quoted), quoted                         # no digit at all in the sign or the warning
    assert not re.search(r"www\.|https?:|bit\.ly|\.com|\.org|@", text), text


def test_a_match_shows_the_three_step_receipt(check_message, monkeypatch):
    monkeypatch.setattr(web, "traced", lambda f: (f(), HOW))
    monkeypatch.setattr(web, "check_message", lambda text: [WARNING])
    monkeypatch.setattr(scamcheck, "verdict", lambda message, found: {
        "scam_signs": True, "sign": "a fee to receive a prize, refund or inheritance", "evidence": EVIDENCE,
        "source": "consumer.ftc.gov", "matched": ["consumer.ftc.gov"],
        "matched_warnings": [{"title": WARNING["title"], "source": "consumer.ftc.gov", "url": WARNING["url"]}]})
    out = check_message(SCAM)
    assert out["scam_signs"] is True and "consumer.ftc.gov warns" in out["say"]
    card = board.showing()
    assert card["kind"] == "check" and card["title"] == "Be careful: a known scam"
    assert card["lead"] == "Don't reply, pay or give any details. Check with family first."     # what to do, first (B24)
    steps = card["items"]
    assert [s["title"] for s in steps] == ["The sign", "The warning", "Why it matches"]
    assert all(s["tone"] == "caution" for s in steps)
    assert steps[0]["summary"] == "A fee to receive a prize, refund or inheritance: “Call … or … now, pay the fee at … or … and email …”"
    assert steps[1]["summary"] == "consumer.ftc.gov: Fake prize, sweepstakes, and lottery scams"
    assert steps[1]["url"] == WARNING["url"] and "url" not in steps[0] and "url" not in steps[2]   # the source, a link
    assert steps[2]["summary"] == "NVIDIA Nemotron 3 Ultra compared them: the same trick, not just the same topic."
    assert card["how"]["calls"] == ["search"] and card["how"]["credits"] == 2      # the how line stays
    no_message_numbers_links_or_emails(card)


def test_a_sign_without_a_warning_online_says_so_and_explains_the_sign_alone(check_message, monkeypatch):
    monkeypatch.setattr(web, "traced", lambda f: (f(), HOW))
    monkeypatch.setattr(web, "check_message", lambda text: [WARNING])
    monkeypatch.setattr(scamcheck, "verdict", lambda message, found: {
        "scam_signs": True, "sign": "payment by gift card, wire or crypto", "evidence": "pay with gift cards to 305-555-0142",
        "source": "", "matched": [], "matched_warnings": []})
    check_message("Grandma, pay with gift cards to 305-555-0142 today")
    steps = board.showing()["items"]
    assert steps[0]["summary"] == "Payment by gift card, wire or crypto: “pay with gift cards to …”"
    assert steps[1]["summary"] == "No warning about this was found online."
    assert steps[2]["title"] == "Why it's a sign" and "Nemotron 3.5 Lightning" in steps[2]["summary"]
    no_message_numbers_links_or_emails(board.showing(), "Grandma, pay with gift cards to 305-555-0142 today")


def test_a_sign_while_the_web_is_down_says_the_warnings_were_not_checked(check_message, monkeypatch):
    def down(f):
        raise web.WebError("The web did not answer (URLError).")

    monkeypatch.setattr(web, "traced", down)
    monkeypatch.setattr(scamcheck, "verdict", lambda message, found: {
        "scam_signs": True, "sign": "pressure to act now", "evidence": "act now", "source": "", "matched": [],
        "matched_warnings": []})
    out = check_message("Act now or lose it")
    assert out["web_unavailable"] is True
    assert board.showing()["items"][1]["summary"] == "The warnings online couldn't be checked just now."


def test_the_receipt_is_in_spanish_when_andy_speaks_spanish(check_message, monkeypatch):
    settings.update(language="es")
    monkeypatch.setattr(web, "traced", lambda f: (f(), HOW))
    monkeypatch.setattr(web, "check_message", lambda text: [WARNING])
    monkeypatch.setattr(scamcheck, "verdict", lambda message, found: {
        "scam_signs": True, "sign": "a relative or friend in trouble asking for money", "evidence": "necesito dinero",
        "source": "consumer.ftc.gov", "matched": ["consumer.ftc.gov"],
        "matched_warnings": [{"title": "Estafas de familiares", "source": "consumer.ftc.gov"}]})
    check_message("Abuela, necesito dinero")
    card = board.showing()
    assert card["title"] == "Cuidado: una estafa conocida"
    assert card["lead"] == "No responda, no pague ni dé ningún dato. Consúltelo antes con la familia."
    assert [s["title"] for s in card["items"]] == ["La señal", "El aviso", "Por qué coinciden"]


def test_the_no_sign_and_web_unavailable_cards_are_kept(check_message, monkeypatch):
    monkeypatch.setattr(web, "traced", lambda f: (f(), HOW))
    monkeypatch.setattr(web, "check_message", lambda text: [])
    monkeypatch.setattr(scamcheck, "verdict", lambda message, found: {
        "scam_signs": False, "sign": "none", "evidence": "", "source": "", "matched": [], "matched_warnings": []})
    check_message("The pharmacy says your prescription is ready.")
    assert board.showing()["title"] == "No sign of a known kind of scam" and len(board.showing()["items"]) == 1
    assert "lead" not in board.showing()                 # only a scam sign leads with what to do


@pytest.mark.parametrize("said, kept", [
    ("Call 1-888-555-0199 now", "Call … now"),
    ("call five five five one two one two today", "call … today"),
    ("visit www.prize.com or bit.ly/abc", "visit … or …"),
    ("go to prize help dot com", "go to prize …"),
    ("email claims@prize-center.example", "email …"),
    ("1-888-555-0199", ""),
    ("Grandma, I'm in jail and need bail money", "Grandma, I'm in jail and need bail money"),
])
def test_the_quote_keeps_the_words_and_drops_every_number_link_and_email(check_message, said, kept):
    assert check_message.module.quoted(said) == kept


def test_the_verdict_names_the_matched_warnings_titles(monkeypatch):
    monkeypatch.setenv("NEBIUS_API_KEY", "k")
    answers = iter([{"sign": "none", "evidence": "", "source": ""}, {"matches": [2]}])

    def opener(req, timeout):
        return io.BytesIO(json.dumps({"choices": [{"message": {"content": json.dumps(next(answers))}}]}).encode())

    warnings = [{"source": "bbb.org", "title": "Charity scams", "summary": "…"},
                {"source": "consumer.ftc.gov", "title": "  Wrong number   texts ", "summary": "A friendly stranger…",
                 "url": "https://consumer.ftc.gov/wrong-number"}]
    v = scamcheck.verdict("Hi, is this Margaret? Wrong number.", warnings, opener=opener)
    assert v["matched_warnings"] == [{"title": "Wrong number texts", "source": "consumer.ftc.gov",
                                      "url": "https://consumer.ftc.gov/wrong-number"}]


def test_the_screen_keeps_a_source_link_only_whole_and_https():
    good = "https://consumer.ftc.gov/consumer-alerts/2021/04/dont-open-your-door-grandparent-scams"
    board.show("check", "Warnings", [{"title": "a", "url": good}, {"title": "b", "url": "http://x.org/a"},
                                     {"title": "c", "url": "javascript:alert(1)"}, {"title": "d", "url": "https://x.org/a b"},
                                     ])
    assert [it.get("url") for it in board.showing()["items"]] == [good, None, None, None]
    board.show("check", "Warnings", [{"title": "e", "url": "https://x.org/" + "a" * 300}])
    assert "url" not in board.showing()["items"][0]


def test_the_tv_links_the_line_that_names_the_source_and_never_by_html():
    assert 'const linked = /^https:\\/\\//.test(it.url || "") ? (steps || !it.title ? "summary" : "title") : "";' in PAGE
    assert 'a.href = url; a.target = "_blank"; a.rel = "noopener noreferrer"; a.tabIndex = -1;' in PAGE
    assert "a.textContent = p.textContent" in PAGE and "innerHTML" not in PAGE


def test_the_tv_numbers_a_receipt_s_steps_in_the_caution_look():
    assert 'showing.kind === "check" && showing.items.length > 1 && showing.items.every((it) => it.tone === "caution")' in PAGE
    assert 'make("span", "num", String(n + 1))' in PAGE
    assert re.search(r"\.item\.step \.num \{[^}]*background: var\(--mark\); color: var\(--panel\)", PAGE)


# --- The family side's cards, drawn here --------------------------------------------------------------------

def test_the_tv_has_words_for_a_family_note_and_a_suggestion():
    assert 'note: "Family note", suggestion: "Suggested reminder"' in PAGE
    assert 'note: "Nota de la familia", suggestion: "Recordatorio sugerido"' in PAGE
    assert 'if (it.when) body.append(make("p", "when", it.when));' in PAGE      # the note's time
