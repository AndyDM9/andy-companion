"""Real SDK reader entrypoint with invented pages and mocked camera/OCR; no robot connection."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip('reachy_mini_conversation_app.tools.core_tools')


@pytest.fixture
def reader():
    spec = importlib.util.spec_from_file_location('reader_dispatch_audit', Path(__file__).resolve().parents[1] / 'tools/read_letter.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_camera_off_returns_a_reason_without_reading(reader, monkeypatch):
    def unexpected(*args):
        raise AssertionError('Camera-disabled request must not read a frame')
    monkeypatch.setattr(reader.reading, 'read', unexpected)
    assert 'error' in asyncio.run(reader.ReadLetter()(SimpleNamespace(camera_enabled=False)))


def test_unreadable_page_returns_the_tools_adjustment_request(reader, monkeypatch):
    result = {'text': '', 'ask': 'Hold the invented test page closer.'}
    frame = object()
    def read(capture):
        assert capture() is frame
        return result
    monkeypatch.setattr(reader.reading, 'read', read)
    deps = SimpleNamespace(camera_enabled=True, reachy_mini=SimpleNamespace(media=SimpleNamespace(get_frame=lambda: frame)))
    assert asyncio.run(reader.ReadLetter()(deps)) == result


def test_readable_page_goes_through_the_existing_card_and_number_filter(reader, monkeypatch):
    from andy_companion import letters
    calls = []
    def card(result, language):
        calls.append((result.copy(), language))
        return {'text': 'An invented masked bill.', 'on_screen': {'sender': 'Invented Electric'}}
    monkeypatch.setattr(reader.reading, 'read', lambda capture: {'text': 'Invented bill 0000-1234'})
    monkeypatch.setattr(letters, 'for_andy', card)
    deps = SimpleNamespace(camera_enabled=True, reachy_mini=SimpleNamespace(media=SimpleNamespace(get_frame=lambda: None)))
    out = asyncio.run(reader.ReadLetter()(deps))
    assert calls and 'not sent or kept' in calls[0][0]['note']
    assert out == {'text': 'An invented masked bill.', 'on_screen': {'sender': 'Invented Electric'}}
