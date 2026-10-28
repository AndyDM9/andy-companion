"""A Spanish household's settings and family pages (2026-10-28 review): the times and days on the settings page, what
waits to be said named rather than typed, every reason something can't be done, and the family page's first question,
all in Spanish. The person's own words stay as they are."""

import ast
import base64
import json
import urllib.error
import urllib.request
from pathlib import Path

import pytest

from andy_companion import board, kept, moments, reminders, screen_server, settings, setup_page, words

SRC = Path(__file__).resolve().parents[1] / "src/andy_companion"


@pytest.fixture(autouse=True)
def data(tmp_path, monkeypatch):
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(board, "PHOTOS", tmp_path / "photos")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(reminders, "STORE", tmp_path / "reminders.json")
    monkeypatch.setattr(moments, "FILE", tmp_path / "moments.json")
    monkeypatch.setattr(kept, "MEMORY_FILE", tmp_path / "memory.json")
    monkeypatch.setattr(screen_server, "_family_sends", screen_server.deque(maxlen=screen_server.FAMILY_PER_MINUTE))


@pytest.fixture
def server():
    httpd = screen_server.serve(host="127.0.0.1", port=0)
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    httpd.shutdown()


def post(url, body):
    req = urllib.request.Request(url, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=5) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def test_the_settings_page_lists_times_and_days_in_spanish():
    settings.update(language="es")
    reminders.add("Regar las plantas", at="09:30", repeat="daily")
    moments.add("El recital de Sofía", "today")
    board.share("Un paseo precioso")
    s = kept.summary()
    reminder, = s["reminder"]
    assert " de " in reminder["when"] and reminder["when"].endswith(" · cada día") and "am" not in reminder["when"]
    assert s["moment"][0]["when"] == "hoy"                                   # was "today"
    assert any(day in s["shared"][0]["when"] for day in words.DAYS["es"])     # "miércoles, 28 de octubre, 11:59"
    assert s["shared"][0]["text"] == "Un paseo precioso"                     # their own words, as they are
    settings.update(language="en")
    assert kept.summary()["moment"][0]["when"] == "today" and kept.summary()["reminder"][0]["when"].endswith(" · daily")


def test_what_waits_to_be_said_is_named_not_typed():
    board.looked("Anna", now=1000)
    board.family_message("Ben", link="https://example.org/fotos", now=1001)
    board.save_photo("Carla", png(), now=1002)
    board.family_message("Dora", "Llamo a las seis", now=1003)
    english = [x["text"] for x in kept.summary()["pending"]]
    assert english == ["Anna looked at the shared notes", "A link from Ben", "A photo from Carla", "Llamo a las seis"]
    settings.update(language="es")
    spanish = [x["text"] for x in kept.summary()["pending"]]
    assert spanish == ["Anna miró las notas compartidas", "Un enlace de Ben", "Una foto de Carla", "Llamo a las seis"]


def test_the_pages_are_told_why_in_spanish(server):
    settings.update(language="es")
    k, s = board.tokens()["family"], board.tokens()["setup"]
    code, out = post(f"{server}/api/family/suggest?k={k}",
                     {"name": "Ana", "what": "Ver https://example.org", "when": {"day": "tomorrow", "time": "10:00"}})
    assert code == 400 and out["error"] == "Una sugerencia no puede llevar un enlace. Envíe el enlace como mensaje."
    code, out = post(f"{server}/api/family/message?k={k}", {"name": "Ana", "text": "", "link": "https://" + "a" * 400})
    assert out["error"] == "Ese enlace es demasiado largo. Envíe una dirección web más corta, de hasta 300 caracteres."
    code, out = post(f"{server}/api/family/photo?k={k}", {"name": "Ana", "image": base64.b64encode(b"not a photo").decode()})
    assert code == 400 and out["error"] == "Envíe la foto como JPEG, PNG o WebP."
    code, out = post(f"{server}/api/setup?s={s}", {"name": "Ana", "settings": {"volume": 500}})
    assert code == 400 and out["error"] == "El volumen es un número del 10 al 100."
    code, out = post(f"{server}/api/setup?s={s}", {"name": "", "settings": {"volume": 50}})
    assert out["error"] == "Hace falta su nombre, para que Andy pueda decir quién lo cambió."
    for _ in range(screen_server.FAMILY_PER_MINUTE):
        post(f"{server}/api/family/look?k={k}", {"name": "Ana"})
    code, out = post(f"{server}/api/family/look?k={k}", {"name": "Ana"})
    assert code == 429 and out["error"] == "Es mucho a la vez; espere un minuto y pruebe otra vez."


def test_the_family_page_asks_in_the_households_language_on_a_first_visit(server):
    """The page learned the language only after the visit was told; a first visit asked for a name in English."""
    settings.update(language="es")
    for path in (f"/family?k={board.tokens()['family']}", f"/setup?s={board.tokens()['setup']}"):
        with urllib.request.urlopen(server + path, timeout=5) as r:
            assert '<html lang="es">' in r.read().decode(), path
    page = (SRC / "pages/family.html").read_text()
    assert 'lang = document.documentElement.lang === "es" ? "es" : "en"' in page and "andy-family-lang" not in page
    settings.update(language="en")
    with urllib.request.urlopen(server + f"/family?k={board.tokens()['family']}", timeout=5) as r:
        assert '<html lang="en">' in r.read().decode()


# Reasons that never reach the settings or family page: the loopback routes' own checks, and Andy's tools.
NOT_ON_A_PAGE = {"bad views", "not a picture", "bad choice", "bad state", "bad usage", "bad interruption", "bad turn",
                 "not an object", "Bad screen card", "Bad search progress", "Bad research result",
                 "Unknown transient operation", "What should I share?", "too long", "bad request"}


def reasons(module):
    """Every reason written as a plain string where it is raised (ValueError, InboxFull) or answered (_error)."""
    found = set()
    for node in ast.walk(ast.parse((SRC / module).read_text())):
        if isinstance(node, ast.Call) and node.args and isinstance(node.args[0], ast.Constant) \
                and isinstance(node.args[0].value, str):
            name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, "attr", "")
            if name in ("ValueError", "InboxFull", "_error"):
                found.add(node.args[0].value)
    return found - NOT_ON_A_PAGE


@pytest.mark.parametrize("module", ["board.py", "setup_page.py", "kept.py", "settings.py", "screen_server.py"])
def test_every_reason_a_page_can_show_has_its_spanish(module):
    for reason in reasons(module):
        assert reason in words.PROBLEMS_ES, reason


def test_reasons_with_numbers_or_their_own_words_have_their_spanish():
    general = words.PROBLEMS_ES["Something went wrong; please try again."]
    made = []
    for bad in ({"news_sources": "not a site"}, {"news_sources": [f"site{i}.org" for i in range(99)]},
                {"person_name": "R" * 99}, {"captions": "yes"}):
        with pytest.raises(ValueError) as e:
            setup_page.clean(bad)
        made.append(str(e.value))
    for bad in (lambda: board.family_message("Ana", link="https://" + "a" * 400),
                lambda: board.family_suggestion("Ana", "a" * 200, "mañana", 0)):
        with pytest.raises(ValueError) as e:
            bad()
        made.append(str(e.value))
    for reason in made + [board.INBOX_FULL, screen_server.READ_ONLY_ERROR]:
        spanish = words.problem(reason, "es")
        assert spanish != reason and spanish != general, reason
    assert words.problem('"no\\1 site" is not a web address. Use one per line, like wlrn.org.', "es").startswith("«no\\1 site»")
    assert words.problem("Choose a time.", "en") == "Choose a time."


def png():
    import cv2
    import numpy as np

    return cv2.imencode(".png", np.full((64, 64, 3), 120, np.uint8))[1].tobytes()
