"""Round 4, from Devpost's judging session (PLAN B24 to B30): the scam receipt's action first, "Try asking" on the
TV, the public read-only demo of the screens and its Hugging Face Space, and the chart drawn from the scorecard."""

import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from andy_companion import board, screen_server, settings, setup_page

ROOT = Path(__file__).resolve().parents[1]
SCREEN = (ROOT / "src/andy_companion/pages/screen.html").read_text()
SETUP = (ROOT / "src/andy_companion/pages/setup.html").read_text()


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")


# --- B24: what to do, first ---------------------------------------------------------------------------------

def test_a_card_can_lead_with_one_line_of_what_to_do():
    board.show("check", "Be careful: a known scam", [{"title": "The sign", "summary": "x", "tone": "caution"}],
               lead="  Don't reply,\n pay or give any details. " + "x" * 200)
    lead = board.showing()["lead"]
    assert lead.startswith("Don't reply, pay or give any details.") and len(lead) == 120
    board.show("news", "Local news", [])
    assert "lead" not in board.showing()


def test_the_tv_shows_the_lead_under_the_title_and_redraws_when_it_changes():
    assert SCREEN.index('id="found-h"') < SCREEN.index('id="found-lead"') < SCREEN.index('id="items"')
    assert '$("found-lead").hidden = !showing.lead;' in SCREEN
    assert '(showing.lead || "")' in SCREEN.split("const contentKey", 1)[1].split(";", 1)[0]


# --- B25: "Try asking" --------------------------------------------------------------------------------------

def test_try_asking_is_on_by_default_and_a_helper_can_turn_it_off():
    assert settings.get()["screen_hints"] is True
    assert screen_server.screen_state()["hints"] is True
    assert setup_page.clean({"screen_hints": False}) == {"screen_hints": False}
    settings.update(screen_hints=False)
    assert screen_server.screen_state()["hints"] is False
    assert 'id="screen_hints"' in SETUP and 'screen_hints: box("screen_hints", true)' in SETUP
    assert "las ideas de qué decirle a Andy, en la pantalla" in SETUP


def test_try_asking_shows_only_when_the_screen_is_quiet_and_andy_is_waiting():
    body = SCREEN.split("function showAsk()", 1)[1].split("\n  }\n", 1)[0]
    for condition in ("lastS.hints", "!lastS.showing", "!lastS.night", 'liveNow === "ready"', '"has-caption"',
                      '"menu-open"', '"offline-on"'):
        assert condition in body, condition
    assert "20000" in body                                    # one idea at a time, a new one every 20 s


def test_every_idea_is_something_andy_can_do_in_both_languages():
    en = SCREEN.split('ask: { label: "Try asking:"', 1)[1].split("] }", 1)[0]
    es = SCREEN.split('ask: { label: "Pruebe a decir:"', 1)[1].split("] }", 1)[0]
    assert en.count("“") == es.count("“") == 9
    for idea in ("Where did I leave my glasses?", "Can you read this letter for me?", "Does this message look like a scam?"):
        assert idea in en
    assert "¿Dónde dejé mis lentes?" in es and "¿Este mensaje parece una estafa?" in es


# --- B26: the public demo -----------------------------------------------------------------------------------

def test_read_only_takes_nothing_and_the_front_page_is_served(monkeypatch):
    monkeypatch.setattr(screen_server, "READ_ONLY", True)
    monkeypatch.setattr(screen_server, "INDEX", b"<h1>front</h1>")
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    try:
        url = f"http://127.0.0.1:{httpd.server_address[1]}"
        with urllib.request.urlopen(url + "/", timeout=5) as r:
            assert r.read() == b"<h1>front</h1>"
        req = urllib.request.Request(f"{url}/api/family/message?k={board.tokens()['family']}", method="POST",
                                     data=json.dumps({"text": "hello"}).encode(), headers={"Content-Type": "application/json"})
        with pytest.raises(urllib.error.HTTPError) as e:
            urllib.request.urlopen(req, timeout=5)
        assert e.value.code == 403 and "nothing you send is kept" in json.loads(e.value.read())["error"]
        assert not board.SHARED.exists() or "hello" not in board.SHARED.read_text()
    finally:
        httpd.shutdown()


def test_andy_s_own_server_has_no_front_page_and_is_not_read_only():
    assert screen_server.READ_ONLY is False and screen_server.INDEX is None
    assert "frame-ancestors 'none'" in screen_server.HEADERS["Content-Security-Policy"]


def test_the_demo_front_page_lists_the_four_pages():
    code = ("import shutil, sys; sys.argv = ['demo']; sys.path.insert(0, 'scripts'); import demo_screen; "
            "print(demo_screen.index_page().decode()); shutil.rmtree(demo_screen.DATA)")
    page = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True, timeout=60, check=True).stdout
    for href in ("/screen?t=demo-screen", "/hood?t=demo-hood", "/family?k=demo-family", "/setup?s=demo-setup"):
        assert f'href="{href}"' in page
    assert "Nothing you type on these pages is sent or kept." in page and "built with NVIDIA Nemotron" in page
    assert "powered by" not in page.lower()


def test_the_public_switch_is_read_only_never_a_night_clock_and_framed_only_by_hugging_face():
    src = (ROOT / "scripts/demo_screen.py").read_text()
    block = src.split("    if PUBLIC:", 1)[1].split("screen_server.INDEX", 1)[0]
    assert "screen_server.READ_ONLY = True" in block and 'night_clock="off"' in block
    assert "frame-ancestors https://huggingface.co" in block
    assert '"0.0.0.0" if PUBLIC else "127.0.0.1"' in src


def test_the_space_holds_only_the_demo(tmp_path):
    docker = (ROOT / "space/Dockerfile").read_text()
    assert "ghcr.io/astral-sh/uv:0.12.20" in docker and "--frozen" in docker and '"--public"' in docker
    assert "EXPOSE 7860" in docker and "USER user" in docker
    card = (ROOT / "space/README.md").read_text().split("---")[1]
    assert "sdk: docker" in card and "app_port: 7860" in card
    short = next(line for line in card.splitlines() if line.startswith("short_description:")).split(":", 1)[1].strip()
    assert len(short) <= 60
    out = tmp_path / "space"
    subprocess.run(["bash", str(ROOT / "scripts/space.sh"), "build", str(out)], cwd=ROOT, check=True,
                   capture_output=True, timeout=60)
    names = {p.relative_to(out).parts[0] for p in out.iterdir()}
    assert names == {"Dockerfile", "README.md", "pyproject.toml", "uv.lock", "LICENSE", "scripts", "src"}
    assert [p.name for p in (out / "scripts").iterdir()] == ["demo_screen.py"]
    assert not list(out.rglob(".env")) and not list(out.rglob("__pycache__"))
    again = subprocess.run(["bash", str(ROOT / "scripts/space.sh"), "build", str(out)], cwd=ROOT, capture_output=True, timeout=60)
    assert again.returncode == 1                         # never into a folder that has something in it


# --- B30: the chart -----------------------------------------------------------------------------------------

def test_the_chart_is_drawn_from_the_scorecard_and_is_up_to_date():
    sys.path.insert(0, str(ROOT / "scripts"))
    try:
        import make_charts
    finally:
        sys.path.pop(0)
    svg = make_charts.scam_chart(json.loads(make_charts.SCORECARD.read_text()))
    for figure in (">53.3<", ">55.7<", ">60<", ">24<", ">58<"):
        assert figure in svg
    assert "<title" in svg and "<desc" in svg                   # read by a screen reader as words
    assert make_charts.OUT.read_text() == svg                   # the committed chart is the scorecard's
