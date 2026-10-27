"""Invented settings in temporary files only; no household data, hardware or provider calls."""
import concurrent.futures
import json
import os
import stat
import urllib.error
import urllib.request

import pytest

from andy_companion import board, kept, moments, places, reminders, screen_server, settings, speaker


@pytest.fixture
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    return settings.FILE


BAD = [None, [], False, "invented private setting", 1,
       {"pace": []}, {"language": {}}, {"volume": True}, {"volume": 50.5}, {"volume": 101},
       {"volume": "invented private setting"}, {"volume": float("nan")},
       {"night_from": True}, {"night_to": 24}, {"night_from": "21"},
       {"tv_yaw": float("inf")}, {"tv_yaw": 121}, {"tv_yaw": True},
       {"tv_height": "invented"}, {"night_clock": None}, {"place": []}, {"person_name": {}},
       {"news_sources": "invented.example"}, {"events_pages": [None]},
       {"last_morning": "2026-02-30"}, {"last_offer": True},
       {"last_greeting": "invented"}, {"last_greeting": 1e300}, {"last_greeting": True},
       {"coords": []}, {"coords": {"place": "Invented town", "lat": 91, "lon": 0}},
       {"coords": {"place": "Invented town", "lat": 0, "lon": float("nan")}},
       {"coords": {"place": "Invented town", "lat": False, "lon": 0}},
       {"events_suggestion": "invented"}, {"events_suggestion": {"site": "invented.example"}}]
BAD += [{key: "false"} for key in ("captions", "screen_photos", "screen_hints", "screen_calm",
                                    "tv_glance", "offers", "greet_arrival")]


@pytest.mark.parametrize("data", BAD)
def test_invalid_store_is_preserved_whole_and_only_metadata_is_exposed(store, data, caplog):
    payload = json.dumps(data).encode()
    store.write_bytes(payload)
    os.chmod(store, 0o644)
    assert settings.get() == settings.DEFAULTS
    copies = settings.recovery_files()
    assert len(copies) == 1 and not store.exists()
    path = store.parent / copies[0]["id"]
    assert path.read_bytes() == payload and stat.S_IMODE(path.stat().st_mode) == 0o600
    assert set(copies[0]) == {"id", "at"} and "invented private setting" not in caplog.text
    assert settings.get() == settings.DEFAULTS and len(settings.recovery_files()) == 1


@pytest.mark.parametrize("payload", [b'{broken', b'\xff\xfe', b''])
def test_bad_json_and_encoding_survive_the_next_save(store, payload):
    store.write_bytes(payload)
    settings.update(pace="slow")
    copy, = settings.recovery_files()
    assert (store.parent / copy["id"]).read_bytes() == payload
    assert settings.get()["pace"] == "slow"


def test_older_partial_file_and_integer_text_volume_remain_usable(store):
    data = {"pace": "slow", "volume": "70", "obsolete": {"ignored": True}}
    store.write_text(json.dumps(data))
    result = settings.get()
    assert result["pace"] == "slow" and result["volume"] == 70 and result["captions"] is True
    assert "obsolete" not in result and not settings.recovery_files()
    assert json.loads(store.read_text()) == data  # a read never rewrites a valid legacy file


def test_complete_current_schema_round_trips_including_internal_caches(store):
    changes = {**settings.DEFAULTS, "volume": 0, "tv_yaw": -45.5, "last_morning": "2026-10-27",
               "last_offer": "2026-10-26", "last_greeting": 1793000000.5,
               "coords": {"place": "Invented town", "lat": 25.1, "lon": -80.1},
               "events_suggestion": {"site": "https://invented.example", "page": "https://invented.example/events",
                                     "for": "Invented town"}}
    assert settings.update(**changes) == changes and settings.get() == changes
    assert stat.S_IMODE(store.stat().st_mode) == 0o600


def test_default_lists_are_independent_between_reads(store):
    settings.get()["news_sources"].append("invented.example")
    assert settings.get()["news_sources"] == settings.DEFAULTS["news_sources"] == []


@pytest.mark.parametrize("changes", [value for value in BAD if isinstance(value, dict)] + [{"unknown": 1}])
def test_bad_direct_update_refused_before_touching_even_an_unreadable_original(store, changes):
    original = b'invented unreadable original'
    store.write_bytes(original)
    with pytest.raises(ValueError) as error:
        settings.update(**changes)
    assert "invented" not in str(error.value) and store.read_bytes() == original
    assert list(store.parent.glob("settings.unreadable-*")) == []


def test_unique_recovery_names_and_failed_preservation_prevent_data_loss(store, monkeypatch):
    monkeypatch.setattr(settings.time, "time", lambda: 123)
    for payload in (b'first invented original', b'second invented original'):
        store.write_bytes(payload)
        settings.get()
    paths = list(store.parent.glob("settings.unreadable-*"))
    assert {p.read_bytes() for p in paths} == {b'first invented original', b'second invented original'}
    store.write_bytes(b'third invented original')
    replace = settings.os.replace

    def fail_source(src, dst):
        if src == store:
            raise OSError("invented private failure")
        return replace(src, dst)

    monkeypatch.setattr(settings.os, "replace", fail_source)
    with pytest.raises(ValueError, match="No settings changes") as error:
        settings.update(pace="slow")
    assert "invented" not in str(error.value) and store.read_bytes() == b'third invented original'
    assert set(store.parent.glob("settings.unreadable-*")) == set(paths)


def test_failed_atomic_save_leaves_original_and_no_temp_copy(store, monkeypatch):
    settings.update(pace="slow")
    original = store.read_bytes()

    def fail(*args):
        raise OSError("invented failure")

    monkeypatch.setattr(settings.os, "replace", fail)
    with pytest.raises(OSError):
        settings.update(language="es")
    assert store.read_bytes() == original and list(store.parent.glob("*.tmp")) == []


def test_a_directory_at_the_settings_path_is_left_intact(store):
    store.mkdir(mode=0o700)
    (store / "invented.txt").write_text("invented original")
    with pytest.raises(ValueError, match="No settings changes"):
        settings.update(pace="slow")
    assert stat.S_IMODE(store.stat().st_mode) == 0o700
    assert (store / "invented.txt").read_text() == "invented original"
    assert list(store.parent.glob("settings.unreadable-*")) == []


def test_parallel_first_reads_recover_once_and_updates_do_not_lose_other_fields(store):
    store.write_bytes(b'invented unreadable original')
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        results = list(pool.map(lambda _: settings.get(), range(6)))
        list(pool.map(lambda item: settings.update(**item), [{"pace": "slow"}, {"language": "es"}, {"captions": False}]))
    assert all(r == settings.DEFAULTS for r in results) and len(settings.recovery_files()) == 1
    result = settings.get()
    assert (result["pace"], result["language"], result["captions"]) == ("slow", "es", False)


def test_authenticated_http_lists_deletes_and_announces_copies_without_contents(store, tmp_path, monkeypatch):
    for key in ("TOKENS", "SHARED", "INBOX"):
        monkeypatch.setattr(board, key, tmp_path / (key.lower() + ".json"))
    monkeypatch.setattr(board, "PHOTOS", tmp_path / "photos")
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")
    monkeypatch.setattr(moments, "FILE", tmp_path / "moments.json")
    monkeypatch.setattr(places, "FILE", tmp_path / "places.json")
    monkeypatch.setattr(kept, "MEMORY_FILE", tmp_path / "memory.json")
    store.write_text('{"person_name": ["invented private content"]}')
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    base = f"http://127.0.0.1:{httpd.server_address[1]}"
    token = board.tokens()["setup"]

    def call(path, body=None, auth=token):
        request = urllib.request.Request(f"{base}{path}?s={auth}",
                                         data=None if body is None else json.dumps(body).encode())
        with urllib.request.urlopen(request, timeout=5) as response:
            return json.load(response)

    try:
        result = call("/api/setup")
        assert result["settings"]["person_name"] is None and "invented private content" not in json.dumps(result)
        saved, = result["kept"]["settings_recovery"]
        body = {"name": "Invented Helper", "kind": "settings_recovery", "id": saved["id"]}
        with pytest.raises(urllib.error.HTTPError) as error:
            call("/api/setup/delete", body, auth="wrong")
        assert error.value.code == 404 and len(settings.recovery_files()) == 1
        outside = tmp_path / "outside.json"
        outside.write_text("invented")
        assert not kept.delete("settings_recovery", "../outside.json") and outside.exists()
        result = call("/api/setup/delete", body)
        assert result["kept"]["settings_recovery"] == []
        assert "a saved settings copy needing review" in speaker.family_frame(board.next_for_person())
        store.write_text('["another invented original"]')
        result = call("/api/setup/delete-all", {"name": "Invented Helper"})
        assert result["kept"]["settings_recovery"] == [] and not settings.recovery_files()
        assert "a saved settings copy needing review" in result["deleted"]
    finally:
        httpd.shutdown()
        httpd.server_close()
