import json
import urllib.error
import urllib.request

import pytest

from andy_companion import board, screen_server, settings, setup_page, speaker


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    from andy_companion import volume

    def never(*args, **kwargs):           # tests must never reach the real robot's speaker
        raise AssertionError("the test reached the robot's volume")

    monkeypatch.setattr(volume, "_call", never)


@pytest.fixture
def server():
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def post(server, path, body, token=None):
    req = urllib.request.Request(f"{server}{path}?s={token or board.tokens()['setup']}", method="POST",
                                 data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=5) as r:
        return json.loads(r.read())


def test_a_helper_sets_andy_up_and_the_person_is_told_who_changed_what(server):
    out = post(server, "/api/setup", {"name": "Anna", "settings": {
        "place": "Harbor Bay, Florida", "news_sources": "wlrn.org\nhttps://www.miamiherald.com/\nwlrn.org",
        "language": "es", "volume": 70, "captions": True}})
    assert out["changed"] == ["the town", "the local news sites", "the language", "the volume"]
    s = settings.get()
    assert s["place"] == "Harbor Bay, Florida" and s["language"] == "es" and s["volume"] == 70
    assert s["news_sources"] == ["wlrn.org", "https://www.miamiherald.com"]
    entry = board.next_for_person()
    assert entry["type"] == "settings" and entry["name"] == "Anna"
    frame = speaker.family_frame(entry)
    assert "Anna changed your settings: the town, the local news sites, the language, the volume" in frame
    assert "change anything back" in frame


def test_saving_what_is_already_set_tells_nobody_anything(server):
    post(server, "/api/setup", {"name": "Anna", "settings": {"pace": "normal", "captions": True, "place": ""}})
    assert board.next_for_person() is None


@pytest.mark.parametrize("bad, message", [
    ({"news_sources": "not a website"}, "not a web address"),
    ({"language": "fr"}, "English or Spanish"),
    ({"pace": "fast"}, "normal or slow"),
    ({"volume": 5}, "10 to 100"),
    ({"events_pages": "\n".join(f"site{i}.org" for i in range(21))}, "Up to 20"),
])
def test_bad_values_are_refused_with_a_plain_reason(server, bad, message):
    with pytest.raises(urllib.error.HTTPError) as e:
        post(server, "/api/setup", {"name": "Anna", "settings": bad})
    assert e.value.code == 400 and message in json.loads(e.value.read())["error"]
    assert board.next_for_person() is None


def test_a_name_is_needed(server):
    with pytest.raises(urllib.error.HTTPError) as e:
        post(server, "/api/setup", {"name": " ", "settings": {"pace": "slow"}})
    assert "first name" in json.loads(e.value.read())["error"]
    assert settings.get()["pace"] == "normal"


def test_the_setup_page_needs_its_own_token(server):
    t = board.tokens()
    for token in ("wrong", t["screen"], t["family"]):
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(f"{server}/api/setup?s={token}", timeout=5)
        with pytest.raises(urllib.error.HTTPError):
            post(server, "/api/setup", {"name": "Anna", "settings": {"pace": "slow"}}, token=token)
    assert settings.get()["pace"] == "normal"


def test_the_page_shows_the_links_and_a_new_family_link_replaces_the_old(server):
    with urllib.request.urlopen(f"{server}/setup?s={board.tokens()['setup']}", timeout=5) as r:
        assert "Andy's settings" in r.read().decode()
    old = board.tokens()["family"]
    out = post(server, "/api/setup/new-family-link", {})
    new = board.tokens()["family"]
    assert new != old and out["links"]["family"] == f"/family?k={new}"
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(f"{server}/api/family?k={old}", timeout=5)


def test_adding_the_setup_link_keeps_the_existing_links(tmp_path):
    board._write(board.TOKENS, {"screen": "S" * 16, "family": "F" * 16})
    t = board.tokens()
    assert t["screen"] == "S" * 16 and t["family"] == "F" * 16 and len(t["setup"]) >= 16


def test_reminders_memories_and_sharing_are_not_settings():
    assert set(setup_page.clean({"reminders": [1], "memory": "x", "shared": "y"})) == set()


def test_the_page_and_andy_each_say_it_in_their_own_voice(server):
    out = post(server, "/api/setup", {"name": "Anna", "settings": {"pace": "slow"}})
    assert out["changed"] == ["how fast Andy speaks"]
    assert "how fast I speak" in speaker.family_frame(board.next_for_person())


def test_the_settings_code_shows_for_two_minutes_and_points_at_this_address(server):
    import time
    board.show_settings_code(now=time.time())
    with urllib.request.urlopen(f"{server}/api/screen?t={board.tokens()['screen']}", timeout=5) as r:
        shown = json.loads(r.read())["showing"]
    assert shown["kind"] == "code" and shown["qr"].startswith("data:image/svg+xml,")
    assert board.showing(now=time.time() + board.CODE_FOR_S + 1) is None          # gone after two minutes


def test_the_gear_on_the_tv_shows_the_settings_code_with_the_screen_token_only(server):
    def press(token):
        req = urllib.request.Request(f"{server}/api/screen/settings-code?t={token}", method="POST", data=b"{}")
        with urllib.request.urlopen(req, timeout=5) as r:
            return json.loads(r.read())

    with pytest.raises(urllib.error.HTTPError):
        press("wrong")
    with pytest.raises(urllib.error.HTTPError):
        press(board.tokens()["setup"])
    assert board.showing() is None
    old = board.tokens()["setup"]
    assert press(board.tokens()["screen"]) == {"ok": True}
    assert board.showing()["kind"] == "code" and board.tokens()["setup"] != old


def test_a_new_settings_link_retires_the_old_one(server):
    old = board.tokens()["setup"]
    post(server, "/api/setup/new-settings-link", {})
    assert board.tokens()["setup"] != old
    with pytest.raises(urllib.error.HTTPError):
        urllib.request.urlopen(f"{server}/api/setup?s={old}", timeout=5)


def test_pressing_the_gear_again_keeps_the_code_already_up(server):
    def press():
        req = urllib.request.Request(f"{server}/api/screen/settings-code?t={board.tokens()['screen']}", method="POST", data=b"{}")
        urllib.request.urlopen(req, timeout=5).read()

    press()
    link = board.tokens()["setup"]
    press()
    assert board.tokens()["setup"] == link        # not retired again while its code is still on the TV


def test_the_night_clock_at_hours_while_asleep_or_never(monkeypatch):
    from andy_companion import screen_server, setup_page, state as andy_state

    assert setup_page.clean({"night_clock": "asleep"})["night_clock"] == "asleep"
    with pytest.raises(ValueError):
        setup_page.clean({"night_clock": "sometimes"})
    hours = {"night_clock": "hours", "night_from": 22, "night_to": 6}
    assert screen_server.night_now(hours, 23) and not screen_server.night_now(hours, 21)
    assert not screen_server.night_now({"night_clock": "off"}, 2)
    monkeypatch.setattr(andy_state, "current", lambda: {"mode": "asleep"})
    assert screen_server.night_now({"night_clock": "asleep"}, 14)          # asleep in the afternoon: night clock
    monkeypatch.setattr(andy_state, "current", lambda: {"mode": "awake"})
    assert not screen_server.night_now({"night_clock": "asleep"}, 23)       # awake at 11 pm: the full screen
