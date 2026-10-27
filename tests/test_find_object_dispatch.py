"""Real SDK tool entrypoint with invented watches and mocked hardware/vision only."""
import asyncio
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip('reachy_mini_conversation_app.tools.core_tools')


@pytest.fixture
def tool():
    path = Path(__file__).resolve().parents[1] / 'tools/find_object.py'
    spec = importlib.util.spec_from_file_location('find_dispatch_review', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('result', [
    {'found': True, 'what': 'wristwatch', 'say': 'An invented result.', '_yaw': .2, '_pitch': .1},
    {'found': False, 'what': 'wristwatch', 'how': 'An invented absence.'},
    {'error': 'An invented camera failure.'},
])
def test_a_watch_reaches_the_finder_and_its_actual_result_is_returned(tool, monkeypatch, result):
    robot, manager = object(), object()
    calls = []

    async def find(what, got_robot, got_manager):
        calls.append((what, got_robot, got_manager))
        return result

    monkeypatch.setattr(tool.vision, 'configured', lambda: True)
    monkeypatch.setattr(tool.finder, 'find', find)
    deps = SimpleNamespace(camera_enabled=True, reachy_mini=robot, movement_manager=manager)
    out = asyncio.run(tool.FindObject()(deps, what='wristwatch'))
    assert calls == [('wristwatch', robot, manager)]
    assert out == {k: v for k, v in result.items() if not k.startswith('_')}


@pytest.mark.parametrize('camera,eyes', [(False, True), (True, False)])
def test_unavailable_camera_or_eyes_explains_why_the_robot_cannot_search(tool, monkeypatch, camera, eyes):
    monkeypatch.setattr(tool.vision, 'configured', lambda: eyes)

    async def unexpected(*args, **kwargs):
        raise AssertionError('Finder must not run without its prerequisites')

    monkeypatch.setattr(tool.finder, 'find', unexpected)
    out = asyncio.run(tool.FindObject()(SimpleNamespace(camera_enabled=camera), what='wristwatch'))
    assert 'error' in out and 'found' not in out
