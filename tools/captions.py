"""Turn the captions on Andy's screen on or off."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import settings
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class Captions(Tool):
    name = "captions"
    description = "When the person asks to show or hide the words you say on the screen (captions). on: true or false."
    parameters_schema = {"type": "object", "properties": {"on": {"type": "boolean"}}, "required": ["on"]}

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        settings.update(captions=bool(kwargs.get("on", True)))
        return {"captions": bool(kwargs.get("on", True)), "remembered": True}
