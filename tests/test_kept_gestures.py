"""2026-10-28 audit: moves taught by hand carry a name ("Sofia's wave") and were kept in gestures.json, but the
settings page's "What Andy remembers" did not list them and "delete everything" left them. Now they are listed,
deleted one by one by their exact name, and included in deleting everything."""

import pytest

from andy_companion import board, gestures, kept, moments, places, settings
from andy_companion.privacy import MEMORY_FILE  # noqa: F401  (kept reads it; pointed at tmp below)

POINTS = [(0.0, 0.1, -0.1), (0.5, 0.4, -0.4), (1.0, 0.1, -0.1)]


@pytest.fixture(autouse=True)
def store(tmp_path, monkeypatch):
    monkeypatch.setattr(gestures, "FILE", tmp_path / "gestures.json")
    monkeypatch.setattr(board, "_transient", lambda *args, **kwargs: kwargs.get("default"))
    for name in ("SCREEN", "SHARED", "INBOX", "TOKENS"):
        monkeypatch.setattr(board, name, tmp_path / f"{name.lower()}.json")
    monkeypatch.setattr(board, "PHOTOS", tmp_path / "photos")
    monkeypatch.setattr(settings, "FILE", tmp_path / "settings.json")
    monkeypatch.setattr(moments, "FILE", tmp_path / "moments.json")
    monkeypatch.setattr(places, "FILE", tmp_path / "places.json")
    monkeypatch.setattr(kept, "MEMORY_FILE", tmp_path / "memory.json")


def test_taught_moves_are_listed_with_their_names():
    gestures.keep("Sofia's wave", POINTS)
    rows = kept.summary()["gesture"]
    assert [r["id"] for r in rows] == ["Sofia's wave"] and rows[0]["text"] == "Sofia's wave" and rows[0]["when"]
    assert kept.words_for({"gesture": 1}) == ["a move taught by hand"]
    assert kept.words_for({"gesture": 2}) == ["2 moves taught by hand"]


def test_a_move_is_deleted_only_by_its_exact_name():
    gestures.keep("Sofia's wave", POINTS)
    gestures.keep("the happy dance", POINTS)
    assert not kept.delete("gesture", "wave")                   # words that would match loosely delete nothing
    assert kept.delete("gesture", "Sofia's wave")
    assert gestures.names() == ["the happy dance"]
    assert not kept.delete("gesture", "Sofia's wave")           # already gone


def test_deleting_everything_includes_taught_moves():
    gestures.keep("Sofia's wave", POINTS)
    gestures.keep("the happy dance", POINTS)
    counts = kept.delete_everything()
    assert counts["gesture"] == 2 and gestures.names() == [] and kept.summary()["gesture"] == []


def test_an_older_or_odd_gestures_file_still_lists_safely(tmp_path):
    gestures.FILE.write_text('{"old move": {"points": [[0, 0, 0]]}, "broken": 3}')
    assert kept.summary()["gesture"] == [{"id": "old move", "text": "old move", "when": ""}]


def test_the_settings_page_shows_the_kind_in_both_languages():
    from pathlib import Path
    page = (Path(kept.__file__).parent / "pages" / "setup.html").read_text()
    assert '"gesture"' in page.split("const KEPT = [", 1)[1].split("]", 1)[0]
    assert '"k_gesture": "Moves taught by hand"' in page and '"k_gesture": "Movimientos enseñados a mano"' in page
