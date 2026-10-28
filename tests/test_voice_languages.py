"""2026-10-28 on the robot: two turns came out of Parakeet in Cyrillic (detected as Ukrainian and Russian) and Andy
answered one in Russian. Andy speaks English and Spanish: a transcript in another alphabet is taken as unclear, and
the turn's language stays English or Spanish. Latin-script words always pass untouched."""

import importlib.util
import logging
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EN = "[Andy couldn't make out these words: ask the person to say it again.]"
ES = "[Andy no entendió estas palabras: pídale a la persona que lo repita.]"


@pytest.fixture(scope="module")
def serve():
    spec = importlib.util.spec_from_file_location("andy_voice_serve_languages", ROOT / "voice" / "serve.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("text, language, last, want", [
    ("Проверь это сообщение, пожалуйста", "ru", "en", (EN, "en")),
    ("Енді, котра година", "uk", "es", (ES, "es")),
    ("Καλημέρα", "el", "en", (EN, "en")),
    ("Andy, what time is it?", "en", "en", ("Andy, what time is it?", "en")),
    ("Andy, ¿qué hora es?", "es", "en", ("Andy, ¿qué hora es?", "es")),
    ("Andy where are my glasses please", "pl", "en", ("Andy where are my glasses please", "en")),   # accented English
    ("", "en", "en", ("", "en")),
])
def test_only_english_and_spanish_reach_the_model(serve, text, language, last, want):
    assert serve.our_language(text, language, last) == want


def test_only_the_language_code_is_logged(serve, caplog):
    with caplog.at_level(logging.INFO, logger="andy.voice"):
        serve.our_language("Проверь это сообщение", "ru", "en")
        serve.our_language("Andy, hello", "en", "en")
    assert [r.getMessage() for r in caplog.records] == ["voice: a turn heard as ru was taken as unclear"]


def test_the_handler_is_wrapped_once_and_keeps_its_last_language(serve):
    class Handler:
        last_language = "es"

        def _process_nano_parakeet(self, audio):
            return audio, "ru"

    serve.only_our_languages(Handler)
    serve.only_our_languages(Handler)
    assert Handler()._process_nano_parakeet("Привет, Энди") == (ES, "es")
    assert Handler()._process_nano_parakeet("Hola Andy") == ("Hola Andy", "es")


def test_the_installed_speech_package_still_has_what_we_wrap():
    pytest.importorskip("speech_to_speech", reason="the voice environment is not installed here")
    from speech_to_speech.STT.parakeet_tdt_handler import ParakeetTDTSTTHandler
    assert callable(ParakeetTDTSTTHandler._process_nano_parakeet)
