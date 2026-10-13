import asyncio
import json
import urllib.error
import urllib.request

import pytest

from andy_companion import board, consent, kept, moments, privacy, reminders, screen_server, settings, speaker


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(board, "PHOTOS", tmp_path / "photos")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")
    monkeypatch.setattr(moments, "FILE", tmp_path / "moments.json")
    monkeypatch.setattr(kept, "MEMORY_FILE", tmp_path / "memory.json")
    consent.heard("")


def fill(tmp_path):
    reminders.add("Call Rosa", minutes=30)
    moments.add("Sofia's piano recital", "tomorrow")
    kept._write_facts([{"id": "m_1", "text": "Likes the window seat", "createdAt": 1791900000000}])
    board.share("A lovely walk this morning")
    (tmp_path / "photos").mkdir()
    (tmp_path / "photos" / "abc123def456.jpg").write_bytes(b"jpeg")


def test_everything_andy_keeps_is_listed(tmp_path):
    fill(tmp_path)
    s = kept.summary()
    assert [x["text"] for x in s["reminder"]] == ["Call Rosa"]
    assert [x["text"] for x in s["moment"]] == ["Sofia's piano recital"]
    assert [x["text"] for x in s["fact"]] == ["Likes the window seat"]
    assert [x["text"] for x in s["shared"]] == ["A lovely walk this morning"]
    assert [x["id"] for x in s["photo"]] == ["abc123def456"]


def test_each_item_can_be_deleted_and_everything_at_once(tmp_path):
    fill(tmp_path)
    fact = kept.summary()["fact"][0]["id"]
    assert kept.delete("fact", fact) and kept.summary()["fact"] == []
    assert json.loads((tmp_path / "memory.json").read_text())["version"] == 1      # Pollen's format kept
    counts = kept.delete_everything()
    assert counts == {"reminder": 1, "moment": 1, "fact": 0, "shared": 1, "photo": 1}
    assert all(not v for v in kept.summary().values())
    assert kept.words_for(counts) == ["a reminder", "a remembered moment", "a shared note", "a photo from family"]


def test_the_settings_page_deletes_and_andy_tells_the_person(tmp_path):
    fill(tmp_path)
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    try:
        url = f"http://127.0.0.1:{httpd.server_address[1]}"
        token = board.tokens()["setup"]

        def post(path, body):
            req = urllib.request.Request(f"{url}{path}?s={token}", method="POST", data=json.dumps(body).encode())
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())

        out = post("/api/setup/delete", {"name": "Anna", "kind": "reminder", "id": kept.summary()["reminder"][0]["id"]})
        assert out["deleted"] == ["a reminder"] and out["kept"]["reminder"] == []
        frame = speaker.family_frame(board.next_for_person())
        assert "Anna deleted from what you keep: a reminder" in frame
        with pytest.raises(urllib.error.HTTPError):
            post("/api/setup/delete-all", {"name": ""})          # a name is needed
        assert post("/api/setup/delete-all", {"name": "Anna"})["deleted"]
        with pytest.raises(urllib.error.HTTPError):
            urllib.request.urlopen(urllib.request.Request(f"{url}/api/setup/delete-all?s=wrong", method="POST", data=b"{}"))
    finally:
        httpd.shutdown()


@pytest.mark.parametrize("words, ok", [
    ("Please remember that I like the window seat", True), ("Yes please", True), ("Sí, claro", True),
    ("Don't forget my sister's birthday is Friday", True), ("My granddaughter has a recital on Thursday", False),
    ("I might have to send a video to Nvidia by the 30th", False), ("", False),
])
def test_saving_needs_the_person_to_have_asked(words, ok):
    assert consent.asked(words) is ok


def test_the_gate_stops_an_unasked_save_and_lets_an_asked_one_through():
    class Handler:
        def _emit_transcript(self, role, text, final=True):
            pass

    ran = []

    class Routine:
        def __init__(self, name):
            self.tool_name = name

        async def __call__(self, manager):
            ran.append(self.tool_name)
            return {"saved": True}

    consent.install(Handler, Routine)
    h = Handler()
    h._emit_transcript("user", "I might have to send a video to Nvidia by the 30th")
    assert asyncio.run(Routine("remember")(None)) == consent.NOT_SAVED and ran == []
    assert asyncio.run(Routine("get_today")(None)) == {"saved": True}               # other tools untouched
    h._emit_transcript("user", "Yes, please remember that")
    assert asyncio.run(Routine("remember_moment")(None)) == {"saved": True}
