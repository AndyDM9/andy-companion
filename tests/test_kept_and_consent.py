import asyncio
import json
import urllib.error
import urllib.request

import pytest

from andy_companion import board, consent, kept, moments, reminders, screen_server, settings, speaker


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
    assert counts == {"reminder": 1, "moment": 1, "fact": 0, "shared": 1, "photo": 1, "place": 0, "recovery": 0, "pending": 0}
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


def test_owner_page_lists_and_deletes_a_preserved_copy_without_showing_its_contents():
    reminders.STORE.write_text('[{"text":"invented private damaged reminder"}]')
    httpd = screen_server.serve(host='127.0.0.1', port=0)
    try:
        base = f'http://127.0.0.1:{httpd.server_address[1]}'
        token = board.tokens()['setup']
        with urllib.request.urlopen(f'{base}/api/setup?s={token}', timeout=5) as response:
            raw = response.read()
        result = json.loads(raw)
        assert b'invented private damaged reminder' not in raw
        copy, = result['kept']['recovery']
        body = {'name': 'Invented Helper', 'kind': 'recovery', 'id': copy['id']}
        request = urllib.request.Request(f'{base}/api/setup/delete?s={token}', method='POST',
                                         data=json.dumps(body).encode())
        with urllib.request.urlopen(request, timeout=5) as response:
            deleted = json.load(response)
        assert deleted['kept']['recovery'] == []
        assert deleted['deleted'] == ['a saved reminder copy needing review']
        assert not reminders.recovery_files()
        notice = board.next_for_person()
        assert notice['type'] == 'deleted'
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
            self.args_json_str = json.dumps({"note": "The recital went well"})

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


@pytest.mark.parametrize("words", [
    "No, please do not remember that", "Please don't", "No thanks", "Not now", "Forget it", "Please don't remember that",
    "Do you remember my sister's name?", "I can't remember where I put my glasses", "Remember when we went to Cuba?",
    "I remember my mother singing", "Ok so I was thinking about lunch tomorrow with my sister",
    "Please turn the volume down", "Please remind me to take out the bins",
    "Si mañana llueve", "Si viene mi hija, avísame", "No gracias", "Mejor no", "No, no lo recuerdes", "Olvídalo",
])
def test_a_no_a_question_or_a_conditional_is_not_consent(words):
    """Found by the audit on 2026-10-14: "please", "ok", "si" or "remember" anywhere let a save through."""
    assert consent.asked(words) is False


@pytest.mark.parametrize("words", [
    "Sure", "Of course", "Okay", "Yeah go ahead", "please", "Sí", "Si", "Si.", "Sí, por favor", "Sí, apúntalo",
    "Andy, remember that Rosa comes on Friday", "Can you remember that for me?", "Remember, the dentist is on Tuesday",
    "Por favor, recuérdalo", "Recuerda que mañana viene Rosa", "No te olvides de la cita del martes",
])
def test_a_clear_yes_or_a_request_is_consent(words):
    assert consent.asked(words) is True


def test_a_moment_deleted_on_the_settings_page_goes_by_its_id_alone(tmp_path):
    a = moments.add("Lunch with Rosa", "tomorrow")
    b = moments.add("Rosa's birthday", "tomorrow")
    assert kept.delete("moment", "") is False and kept.delete("moment", "rosa") is False
    assert len(kept.summary()["moment"]) == 2
    assert kept.delete("moment", a["id"]) and [m["id"] for m in kept.summary()["moment"]] == [b["id"]]


@pytest.mark.parametrize("words", ["Okay, so my sister is coming Friday.", "Please, my hip hurts today",
                                   "Sure, my grandson Tom visited yesterday", "Bueno, pues mi nieto se casa",
                                   "Yes, and then we went to the market"])
def test_a_yes_that_starts_a_new_sentence_is_not_consent(words):
    from andy_companion import consent
    assert consent.asked(words) is False          # Parakeet writes commas (2026-10-14 review)


@pytest.mark.parametrize("words", ["Yes, please do", "Sure, go ahead", "Sí, gracias", "Yes, thank you Andy", "Okay."])
def test_a_yes_with_a_short_closer_is_consent(words):
    from andy_companion import consent
    assert consent.asked(words) is True


@pytest.mark.parametrize("words, ok", [
    ("Yes", True), ("Yes please", True), ("Sí, por favor", True), ("Sure, go ahead", True),
    ("Please share that with my daughter", True), ("Share it with the family", True), ("Tell my son I'm feeling better", True),
    ("Can you send that to my family?", True), ("Compártelo con mi familia", True), ("Díselo a mi hija", True),
    ("No", False), ("No, don't share that", False), ("Not now", False), ("Mejor no", False),
    ("My daughter is coming on Friday", False), ("I had a lovely walk today", False), ("", False),
])
def test_sharing_needs_a_yes_or_a_plain_request(words, ok):
    assert consent.asked_to_share(words) is ok


def test_the_gate_stops_an_unasked_share():
    class Handler:
        def _emit_transcript(self, role, text, final=True):
            pass

    ran = []

    class Routine:
        def __init__(self, name):
            self.tool_name = name

        async def __call__(self, manager):
            ran.append(self.tool_name)
            return {"shared": True}

    consent.install(Handler, Routine)
    h = Handler()
    h._emit_transcript("user", "My granddaughter's recital went really well")
    assert asyncio.run(Routine("share_with_family")(None)) == consent.NOT_SHARED and ran == []
    h._emit_transcript("user", "Yes, please")                  # unrelated yes is not permission
    assert asyncio.run(Routine("share_with_family")(None)) == consent.NOT_SHARED


def test_delete_everything_also_clears_what_was_waiting_to_be_said(tmp_path, monkeypatch):
    monkeypatch.setattr(board, "INBOX", tmp_path / "inbox.json")
    board.family_message("Anna", "Call me tonight")
    board.research_ready("Is the market on Saturday?", "Not this week.", [], [])
    board.settings_changed("Leo", ["volume"])
    counts = kept.delete_everything()
    assert counts["pending"] == 2 and kept.words_for({"pending": 2}) == ["2 messages waiting to be said"]
    assert [e["type"] for e in board._read(board.INBOX, [])] == ["settings"]      # who changed what is still said
