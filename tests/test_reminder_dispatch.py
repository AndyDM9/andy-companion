"""Installed SDK dispatch, invented reminder arguments and a temporary store; no robot."""
import asyncio
import importlib.util
import json
from datetime import datetime
from pathlib import Path

import pytest

core = pytest.importorskip('reachy_mini_conversation_app.tools.core_tools')
from reachy_mini_conversation_app.tools.background_tool_manager import ToolCallRoutine
from andy_companion import reminders


@pytest.fixture
def dispatch(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / 'tools' / 'set_reminder.py'
    spec = importlib.util.spec_from_file_location('audited_set_reminder', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(reminders, 'STORE', tmp_path / 'reminders.json')
    monkeypatch.setattr(core, 'get_tools', lambda *a, **k: {'set_reminder': module.SetReminder()})

    def run(arguments):
        routine = ToolCallRoutine(tool_name='set_reminder', args_json_str=json.dumps(arguments),
                                  deps=core.ToolDependencies(reachy_mini=None, movement_manager=None))
        return asyncio.run(routine(None))

    return run


@pytest.mark.parametrize('arguments', [
    {'minutes': 1, 'at': '08:00', 'repeat': 'daily'},
    {'minutes': True}, {'minutes': {'invented': 'private argument'}},
    {'at': '08:0'}, {'minutes': 1, 'repeat': 'daily'},
])
def test_bad_tool_arguments_return_a_fixed_error_without_persisting(dispatch, arguments):
    result = dispatch({'what': 'Water the invented plant', **arguments})
    assert result.get('error') and not result.get('set')
    assert 'private argument' not in json.dumps(result)
    assert not reminders.STORE.exists()


def test_valid_daily_clock_time_is_still_set_through_the_real_dispatcher(dispatch):
    result = dispatch({'what': 'Water the invented plant', 'at': '08:00', 'repeat': 'daily'})
    assert result['set'] is True and result['daily'] is True
    item, = reminders.pending()
    assert item['id'] == result['id'] and datetime.fromtimestamp(item['due']).strftime('%H:%M') == '08:00'
