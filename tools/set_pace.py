"""Speak slowly or at a normal pace, and keep it that way."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import settings
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class SetPace(Tool):
    name = "set_pace"
    description = (
        "When the person asks you to speak more slowly (pace='slow') or normally again (pace='normal'). "
        "It is remembered for every later conversation. From now on, speak at that pace."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"pace": {"type": "string", "enum": ["slow", "normal"]}},
        "required": ["pace"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        try:
            settings.update(pace=kwargs.get("pace"))
        except ValueError as e:
            return {"error": str(e)}
        return {"pace": kwargs.get("pace"), "remembered": True}
