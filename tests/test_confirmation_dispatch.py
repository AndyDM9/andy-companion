"""Run the installed tool dispatcher with invented data and no robot connection."""
import asyncio
import importlib.util
import json
from pathlib import Path

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
