"""Under the hood, after the design review of 2026-10-14: where each tool runs, the latest turn's split, the
session tally, the page in Spanish, and a kind page for a link that no longer opens."""

import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from andy_companion import board, screen_server, settings, turns

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    screen_server._turns.clear()
    screen_server._interrupts.clear()
    screen_server._tavily.clear()
    for k in screen_server._tally:
        screen_server._tally[k] = 0


@pytest.fixture
def server(monkeypatch):
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    monkeypatch.setattr(turns, "SCREEN", f"http://127.0.0.1:{httpd.server_address[1]}")
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def hood(server):
    with urllib.request.urlopen(f"{server}/api/hood?t={board.tokens()['hood']}", timeout=5) as r:
        return json.loads(r.read())


def fetch_error(url):
    with pytest.raises(urllib.error.HTTPError) as e:
        urllib.request.urlopen(url, timeout=5)
    return e.value.code, e.value.headers.get("Content-Type", ""), e.value.read().decode()


def tool_names():
    tools = json.loads((ROOT / "evals" / "tools.json").read_text())
    tools = tools if isinstance(tools, list) else tools.get("tools", [])
    return [t.get("name") or t["function"]["name"] for t in tools]


NETWORK = {"local_news", "look_up", "whats_on", "read_link", "check_message", "look_into", "read_letter", "on_this_day",
           "think_it_through", "describe_view", "describe_photo", "find_object", "weather", "remember_place"}


def test_every_tool_says_where_it_runs_in_both_languages():
    names = tool_names()
    assert len(names) == 37
    for lang in ("en", "es"):
        where = turns.where(lang)
        for name in names:
            assert where.get(name), (name, lang)
            if name in NETWORK:
                assert where[name] != turns.HERE[lang], (name, lang)
            else:
                assert where[name] == turns.HERE[lang], (name, lang)


def test_the_flagship_tools_name_their_services(monkeypatch):
    monkeypatch.delenv("ANDY_VISION", raising=False)
    w = turns.where("en")
    assert w["find_object"] == "Nemotron 3.5 Super VL, Token Factory, four views at once, zoomed in, then a closer look"
    assert "Tavily (advanced)" in w["check_message"] and "Ultra" in w["check_message"]
    assert w["read_letter"] == "read on this computer + Nemotron Lightning card"
    assert w["on_this_day"].startswith("Wikipedia + Nemotron")
    assert "Super VL" in w["describe_view"] and "Super VL" in w["describe_photo"]
    monkeypatch.setenv("ANDY_VISION", "endpoint")
    assert turns.where("es")["find_object"].startswith("Nemotron Nano VL en nuestro endpoint")
    assert "Ultra" in w["think_it_through"] and "Tavily research" in w["look_into"]
    assert "weather.gov" in w["weather"]


def test_the_latest_turn_is_split_into_nemotron_and_each_tool(server):
    turns.send({"hearing_ms": 80, "reply_ms": 5000, "total_ms": 5080,
                "tools": [{"name": "find_object", "ms": 4200}, {"name": "content_safety", "ms": 300}]})
    s = hood(server)
    latest = s["turns"][0]
    assert latest["think_ms"] == 800                         # the reply less the tool Andy waited for
    assert "VL" in s["where"]["find_object"] and "four views" in s["where"]["find_object"]
    turns.send({"hearing_ms": 60, "reply_ms": 900, "total_ms": 960, "tools": [{"name": "content_safety", "ms": 400}]})
    s = hood(server)
    assert s["turns"][0]["think_ms"] == 900                  # the second look runs beside the reply, not before it
    assert s["median"]["total_ms"] == 960                    # so that turn counts as one without a tool


def test_tools_that_ran_side_by_side_never_make_nemotron_negative():
    assert turns.think_ms({"reply_ms": 1000, "tools": [{"name": "look_up", "ms": 900}, {"name": "weather", "ms": 800}]}) == 0
    assert turns.think_ms({"reply_ms": None, "tools": []}) is None


def test_the_tally_counts_since_andy_started_beyond_the_recent_turns(server):
    turns.send({"hearing_ms": 50, "reply_ms": 800, "total_ms": 850, "tools": []})
    turns.send({"hearing_ms": 50, "reply_ms": 3000, "total_ms": 3050,
                "tools": [{"name": "check_message", "ms": 2000}, {"name": "content_safety", "ms": 200}]})
    turns.send({"hearing_ms": 50, "reply_ms": 5000, "total_ms": 5050, "tools": [{"name": "find_object", "ms": 4000}]})
    turns.send({"hearing_ms": 50, "reply_ms": 2000, "total_ms": 2050, "tools": [{"name": "look_up", "ms": 1000}]})
    assert hood(server)["tally"] == {"turns": 4, "nebius": 2, "tavily": 2, "eyes": 1}
    for _ in range(45):                                      # more than the 40 recent turns kept
        screen_server.add_turn({"reply_ms": 700, "tools": []})
    s = hood(server)
    assert s["tally"]["turns"] == 49 and s["count"] == 40


def test_the_tally_and_split_carry_numbers_and_names_only(server):
    turns.send({"hearing_ms": 50, "reply_ms": 900, "total_ms": 950, "words": "my bank PIN",
                "tools": [{"name": "look_up", "ms": 300, "query": "my bank PIN"}]})
    assert "PIN" not in json.dumps(hood(server))


def test_the_hood_page_draws_the_waterfall_and_says_it():
    page = (ROOT / "src" / "andy_companion" / "pages" / "hood.html").read_text()
    assert 'id="fall"' in page and "function drawFall" in page
    assert "each time he stopped" not in page and "each time it stopped" in page
    assert "Nebius Token Factory" in page and "Since Andy started" in page
    assert "powered by" not in page.lower()
    for word in ("seniors", "elderly"):
        assert word not in page.lower()


def test_the_hood_is_in_spanish_when_the_household_is(server):
    t = board.tokens()["hood"]
    with urllib.request.urlopen(f"{server}/hood?t={t}", timeout=5) as r:
        assert '<html lang="en">' in r.read().decode()
    settings.update(language="es")
    with urllib.request.urlopen(f"{server}/hood?t={t}", timeout=5) as r:
        page = r.read().decode()
    assert '<html lang="es">' in page and "Por dentro" in page
    s = hood(server)
    assert s["language"] == "es" and "cuatro vistas a la vez" in s["where"]["find_object"]


@pytest.mark.parametrize("path,key,words", [
    ("/setup", "s", "This settings link has been replaced"),
    ("/family", "k", "This family link has been replaced"),
    ("/hood", "t", "the gear on Andy's screen opens Under the hood"),
])
def test_an_old_link_gets_a_kind_page_not_a_bare_not_found(server, path, key, words):
    code, kind, body = fetch_error(f"{server}{path}?{key}=old-token-abc123")
    assert code == 404 and kind.startswith("text/html")
    assert words.lower() in body.lower() and "old-token-abc123" not in body
    assert "{{" not in body
    code, _, body = fetch_error(f"{server}{path}")              # no token at all: the same kind page
    assert code == 404 and words.lower() in body.lower()


def test_the_settings_page_says_how_to_get_a_new_code(server):
    _, _, body = fetch_error(f"{server}/setup?s=wrong")
    assert "Andy, show the settings code" in body and "camera at the TV" in body


def test_an_old_link_is_in_spanish_when_the_household_is(server):
    settings.update(language="es")
    _, _, body = fetch_error(f"{server}/family?k=wrong")
    assert 'lang="es"' in body and "Este enlace familiar ha sido reemplazado" in body
    _, _, body = fetch_error(f"{server}/setup?s=wrong")
    assert "muestra el código de ajustes" in body


def test_the_kind_page_escapes_what_it_fills_in():
    page = screen_server.expired_page("/hood", "en").decode()
    assert "Andy's screen" in page and "<h1>This link has been replaced.</h1>" in page
    original = screen_server.EXPIRED["/hood"]
    try:
        screen_server.EXPIRED["/hood"] = {"en": ("<b>", "<script>", "a & b")}
        page = screen_server.expired_page("/hood", "en").decode()
        assert "<script>" not in page and "&lt;script&gt;" in page and "a &amp; b" in page
    finally:
        screen_server.EXPIRED["/hood"] = original


def test_other_addresses_and_apis_keep_a_plain_not_found(server):
    for path in ("/api/setup?s=wrong", "/api/family?k=wrong", "/api/hood?t=wrong", "/nothing-here"):
        code, kind, body = fetch_error(f"{server}{path}")
        assert code == 404 and kind.startswith("text/plain") and body == "Not found"
