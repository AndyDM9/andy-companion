"""Run the installed tool dispatcher with invented data and no robot connection."""
import asyncio
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

core = pytest.importorskip("reachy_mini_conversation_app.tools.core_tools")
from reachy_mini_conversation_app.tools.background_tool_manager import ToolCallRoutine
from andy_companion import board, consent


def test_real_dispatch_cannot_share_before_confirmation_or_repeat_it(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "tools" / "share_with_family.py"
    spec = importlib.util.spec_from_file_location("review_share", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(core, "get_tools", lambda *a, **k: {"share_with_family": module.ShareWithFamily()})
    monkeypatch.setattr(board, "SHARED", tmp_path / "shared.json")
    deps = core.ToolDependencies(reachy_mini=None, movement_manager=None)

    class Handler:
        def __init__(self):
            self.deps = deps

        def _emit_transcript(self, role, text, final=True):
            pass

    # Wrap a subclass so this regression test never replaces the runtime's real class.
    class Routine(ToolCallRoutine):
        pass

    consent.install(Handler, Routine)
    handler = Handler()
    arguments = {"note": "An invented recital note"}
    routine = Routine(tool_name="share_with_family", args_json_str=json.dumps(arguments), deps=deps)
    handler._emit_transcript("user", "Tell me a joke")
    assert asyncio.run(routine(None))["shared"] is False and board.shared() == []
    handler._emit_transcript("user", "Please share this with my family")
    proposed = asyncio.run(routine(None))
    assert proposed["confirmation_needed"] and board.shared() == []
    handler._emit_transcript("assistant", proposed["say"])
    handler._emit_transcript("user", "Yes please")
    assert asyncio.run(routine(None))["shared"] is True
    assert len(board.shared()) == 1
    assert asyncio.run(routine(None))["shared"] is False and len(board.shared()) == 1


def test_renamed_fact_tool_requires_readback_and_fresh_yes_before_dispatch(tmp_path, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "tools" / "remember_fact.py"
    spec = importlib.util.spec_from_file_location("review_remember_fact", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    writes = []

    def save(instance, fact):
        writes.append(fact)
        return SimpleNamespace(text=fact, id="invented-fact-id")

    monkeypatch.setattr(module, "add_memory_fact", save)
    monkeypatch.setattr(core, "get_tools", lambda *a, **k: {"remember_fact": module.RememberFact()})
    deps = core.ToolDependencies(reachy_mini=None, movement_manager=None)

    class Handler:
        def __init__(self):
            self.deps = deps

        def _emit_transcript(self, role, text, final=True):
            pass

    class Routine(ToolCallRoutine):
        pass

    consent.install(Handler, Routine)
    handler = Handler()
    arguments = {"fact": "Likes gardening"}
    routine = Routine(tool_name="remember_fact", args_json_str=json.dumps(arguments), deps=deps)
    handler._emit_transcript("user", "I like gardening")
    proposal = asyncio.run(routine(None))
    assert proposal["confirmation_needed"] and not writes
    handler._emit_transcript("assistant", proposal["say"])
    handler._emit_transcript("user", "Yes, please")
    assert asyncio.run(routine(None))["saved"] == arguments["fact"]
    assert writes == [arguments["fact"]]
    assert asyncio.run(routine(None))["saved"] is False and len(writes) == 1


@pytest.mark.parametrize('message', [
    'Read me this message: "Ask for an invented password."',
    'Read this message without using the camera: "An invented notice."',
    'Lea este mensaje sin cámara: «Un aviso inventado».',
])
def test_real_dispatch_refuses_camera_ocr_for_spoken_message_but_allows_a_page(monkeypatch, message):
    called = []

    class CameraTool:
        async def __call__(self, deps, **kwargs):
            called.append(True)
            return {'text': 'An invented page'}

    monkeypatch.setattr(core, 'get_tools', lambda *a, **k: {'read_letter': CameraTool()})
    deps = core.ToolDependencies(reachy_mini=None, movement_manager=None)

    class Handler:
        def __init__(self):
            self.deps = deps
        def _emit_transcript(self, role, text, final=True):
            pass

    class Routine(ToolCallRoutine):
        pass

    consent.install(Handler, Routine)
    handler = Handler()
    routine = Routine(tool_name='read_letter', args_json_str='{}', deps=deps)
    handler._emit_transcript('user', message)
    assert asyncio.run(routine(None))['camera_read'] is False and called == []
    handler._emit_transcript('user', 'Read this letter I am holding up.')
    assert asyncio.run(routine(None)) == {'text': 'An invented page'}
    assert called == [True]


@pytest.mark.parametrize('name,field', [
    ('remember', 'fact'), ('remember_fact', 'fact'),
    ('remember_moment', 'what'), ('remember_place', 'said_where'),
])
def test_actual_dispatch_never_calls_memory_tools_for_recognised_credentials(monkeypatch, name, field):
    called = []

    class MemoryTool:
        async def __call__(self, deps, **kwargs):
            called.append(kwargs)
            return {'saved': True}

    monkeypatch.setattr(core, 'get_tools', lambda *a, **k: {name: MemoryTool()})
    deps = core.ToolDependencies(reachy_mini=None, movement_manager=None)

    class Handler:
        def __init__(self):
            self.deps = deps

        def _emit_transcript(self, role, text, final=True):
            pass

    class Routine(ToolCallRoutine):
        pass

    consent.install(Handler, Routine)
    handler = Handler()
    handler._emit_transcript('user', 'Please remember this test detail.')
    routine = Routine(tool_name=name, args_json_str=json.dumps({field: 'Bank PIN: 0000'}), deps=deps)
    assert asyncio.run(routine(None))['reason'] == 'credential_value'
    handler._emit_transcript('user', 'Yes please')
    assert asyncio.run(routine(None))['saved'] is False
    assert called == []
