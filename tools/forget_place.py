"""Forget where something is (andy_companion.places; PLAN B46)."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import places
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class ForgetPlace(Tool):
    name = "forget_place"
    description = ("When the person asks you to forget where something is ('forget where my keys are'). Say what "
                   "you forgot.")
    parameters_schema = {
        "type": "object",
        "properties": {"what": {"type": "string", "description": "The thing, e.g. 'keys'."}},
        "required": ["what"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        n = places.forget(str(kwargs.get("what", "")))
        return {"forgotten": n > 0, "what": kwargs.get("what", "")}
