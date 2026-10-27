"""Actual SDK tool dispatch with invented provider replies; no model, audio or robot."""
import asyncio
import importlib.util
import io
import json
from pathlib import Path

import pytest

core = pytest.importorskip('reachy_mini_conversation_app.tools.core_tools')
from reachy_mini_conversation_app.tools.background_tool_manager import ToolCallRoutine
from andy_companion import deeper, settings


@pytest.fixture
def dispatch(monkeypatch, tmp_path):
    path = Path(__file__).resolve().parents[1]/'tools'/'think_it_through.py'
    spec = importlib.util.spec_from_file_location('audited_think_tool', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(core, 'get_tools', lambda *a, **k: {'think_it_through': module.ThinkItThrough()})
    monkeypatch.setattr(settings, 'FILE', tmp_path/'settings.json')
    monkeypatch.setenv('NEBIUS_API_KEY', 'invented-not-used')

    def run(content, finish='stop'):
        payload = {'choices': [{'finish_reason': finish, 'message': {'content': content}}]}
        monkeypatch.setattr(deeper.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
        routine = ToolCallRoutine(tool_name='think_it_through',
                                  args_json_str=json.dumps({'question': 'An invented choice about a club meeting'}),
                                  deps=core.ToolDependencies(reachy_mini=None, movement_manager=None))
        return asyncio.run(routine(None))

    return run


@pytest.mark.parametrize('content,finish', [
    (None, 'stop'), ({'draft': 'invented-private-draft'}, 'stop'),
    ('<think>invented-private-draft', 'stop'), ('<think>invented-private-draft</think>', 'stop'),
    ('An unfinished invented answer', 'length'),
])
def test_bad_completion_cannot_become_a_tool_answer_for_speech(dispatch, content, finish):
    result = dispatch(content, finish)
    assert result.get('error') and 'answer' not in result
    assert 'invented-private-draft' not in json.dumps(result)


def test_completed_answer_still_dispatches_without_inline_reasoning(dispatch):
    result = dispatch('<think>invented-private-draft</think>Both meeting times could work. Choose the one that suits you.')
    assert result['answer'].startswith('Both meeting times')
    assert 'invented-private-draft' not in json.dumps(result) and '<think>' not in json.dumps(result)


@pytest.mark.parametrize('warnings', [[], [{'title': 'An invented warning', 'summary': 'An invented trick',
                                         'source': 'example.com', 'url': 'https://example.com/warning'}]])
def test_failed_classification_is_explicit_even_when_web_lookup_succeeded(monkeypatch, warnings):
    path = Path(__file__).resolve().parents[1]/'tools'/'check_message.py'
    spec = importlib.util.spec_from_file_location('audited_check_tool', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(core, 'get_tools', lambda *a, **k: {'check_message': module.CheckMessage()})
    monkeypatch.setenv('NEBIUS_API_KEY', 'invented-not-used')
    monkeypatch.setattr(module.web, 'traced', lambda task: (warnings, {}))
    shown = []
    monkeypatch.setattr(module.board, 'show', lambda *args, **kwargs: shown.append((args, kwargs)))
    payload = {'choices': [{'finish_reason': 'stop', 'message': {'content': '{}'}}]}
    monkeypatch.setattr(deeper.urllib.request, 'urlopen', lambda *a, **k: io.BytesIO(json.dumps(payload).encode()))
    routine = ToolCallRoutine(tool_name='check_message', args_json_str=json.dumps({'message': 'An invented ordinary message'}),
                              deps=core.ToolDependencies(reachy_mini=None, movement_manager=None))
    result = asyncio.run(routine(None))
    assert result['analysis_unavailable'] and 'scam_signs' not in result
    assert result['warnings'] == warnings and 'no sign' not in result['say'].lower()
    assert "couldn't finish" in result['say'] and "couldn't finish" in shown[0][0][1]
