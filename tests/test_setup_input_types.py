"""Invented setup requests against throwaway settings; no robot, web lookup or household data."""
import json
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from andy_companion import board, kept, screen_server, settings, setup_page, volume


@pytest.mark.parametrize("field", ["captions", "screen_photos", "screen_hints", "screen_calm", "offers",
                                   "greet_arrival", "tv_glance"])
@pytest.mark.parametrize("value", ["false", 0])
def test_switches_require_actual_json_booleans(field, value):
    with pytest.raises(ValueError, match="Choose on or off"):
        setup_page.clean({field: value})


@pytest.mark.parametrize("value", [True, False])
def test_real_switch_values_keep_their_meaning(value):
    data = {k: value for k in ("captions", "screen_photos", "screen_hints", "screen_calm", "offers",
                              "greet_arrival", "tv_glance")}
    assert setup_page.clean(data) == data


@pytest.mark.parametrize("field", ["volume", "night_from", "night_to"])
@pytest.mark.parametrize("value", [True, False, 12.8, "12.8", float("inf"), float("nan"), [], {}])
def test_integer_controls_do_not_truncate_or_accept_wrong_types(field, value):
    with pytest.raises(ValueError):
        setup_page.clean({field: value})


@pytest.mark.parametrize("data,expected", [({"volume": " 70 "}, {"volume": 70}),
    ({"volume": 70.0}, {"volume": 70}), ({"night_from": "22"}, {"night_from": 22}),
    ({"night_to": 7.0}, {"night_to": 7}), ({"tv_yaw": "-45.5"}, {"tv_yaw": -46}),
    ({"tv_yaw": 20.4}, {"tv_yaw": 20}), ({"tv_yaw": None}, {"tv_yaw": None}),
    ({"volume": None}, {}), ({"volume": ""}, {}),
    ({"place": None, "person_name": None}, {"place": None, "person_name": None}),
    ({"events_pages": None}, {"events_pages": []}), ({"events_pages": ""}, {"events_pages": []})])
def test_compatible_valid_numbers_and_empty_controls_remain_supported(data, expected):
    assert setup_page.clean(data) == expected


@pytest.mark.parametrize("value", [True, False, float("inf"), float("nan"), "Infinity", "NaN", [], {}, 10**400])
def test_screen_direction_rejects_nonfinite_or_wrong_types_with_plain_error(value):
    with pytest.raises(ValueError, match="number of degrees"):
        setup_page.clean({"tv_yaw": value})


@pytest.mark.parametrize("value", [True, 1, {}, ["example.org", 5], [None], [False]])
def test_site_lists_are_text_or_lists_of_text(value):
    with pytest.raises(ValueError, match="web addresses"):
        setup_page.clean({"events_pages": value})


@pytest.mark.parametrize("field", ["place", "person_name"])
@pytest.mark.parametrize("value", [True, ["invented"]])
def test_names_and_towns_cannot_be_coerced_from_other_json_types(field, value):
    with pytest.raises(ValueError, match="text"):
        setup_page.clean({field: value})


@pytest.mark.parametrize("value", [None, [], False, "captions", 5])
def test_settings_container_must_be_an_object(value):
    with pytest.raises(ValueError, match="object of named choices"):
        setup_page.clean(value)


@pytest.fixture
def isolated_setup(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    for key in ("INBOX", "TOKENS"):
        monkeypatch.setattr(board, key, tmp_path / (key.lower() + ".json"))
    monkeypatch.setattr(kept, "summary", lambda: {})
    effects = {"announcements": [], "volume": [], "lookup": []}
    monkeypatch.setattr(board, "settings_changed", lambda *args: effects["announcements"].append(args))
    monkeypatch.setattr(volume, "set_level", lambda *args: effects["volume"].append(args))
    monkeypatch.setattr(setup_page, "suggest_events_page", lambda *args: effects["lookup"].append(args))
    settings.update(pace="normal", captions=False)
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    try:
        yield f"http://127.0.0.1:{httpd.server_address[1]}/api/setup?s={board.tokens()['setup']}", effects
    finally:
        httpd.shutdown()
        httpd.server_close()


def post(url, body):
    request = Request(url, method="POST", data=json.dumps(body).encode(),
                      headers={"Content-Type": "application/json"})
    with urlopen(request, timeout=5) as response:
        return json.load(response)


@pytest.mark.parametrize("bad", [{"captions": "false"}, {"night_from": 22.8}, {"volume": 70.9},
    {"tv_yaw": "Infinity"}, {"events_pages": True}, {"person_name": ["invented"]}, None, [], False])
def test_bad_http_batch_changes_nothing_and_announces_nothing(isolated_setup, bad):
    url, effects = isolated_setup
    before = settings.FILE.read_bytes()
    changes = {"pace": "slow", "place": "Invented Town", **bad} if isinstance(bad, dict) else bad
    with pytest.raises(HTTPError) as error:
        post(url, {"name": "Demo Helper", "settings": changes})
    assert error.value.code == 400
    message = json.load(error.value)["error"]
    assert isinstance(message, str) and message != "Something went wrong; please try again."
    assert settings.FILE.read_bytes() == before
    assert effects == {"announcements": [], "volume": [], "lookup": []}


def test_valid_browser_types_save_once_and_keep_false(isolated_setup):
    url, effects = isolated_setup
    result = post(url, {"name": "Demo Helper", "settings": {"pace": "slow", "captions": False,
                   "night_from": 22, "night_to": 6, "tv_yaw": -45, "screen_photos": False}})
    assert result["ok"] and settings.get()["captions"] is False and settings.get()["screen_photos"] is False
    assert settings.get()["night_from"] == 22 and settings.get()["tv_yaw"] == -45
    assert len(effects["announcements"]) == 1 and not effects["volume"] and not effects["lookup"]


def test_missing_settings_remains_a_noop_and_nontext_helper_is_refused(isolated_setup):
    url, effects = isolated_setup
    assert post(url, {"name": "Demo Helper"})["changed"] == []
    with pytest.raises(HTTPError) as error:
        post(url, {"name": ["invented"], "settings": {"pace": "slow"}})
    assert error.value.code == 400 and settings.get()["pace"] == "normal"
    assert effects == {"announcements": [], "volume": [], "lookup": []}
