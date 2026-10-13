"""Forget a remembered moment."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import moments
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class ForgetMoment(Tool):
    name = "forget_moment"
    description = "When the person asks you to forget a moment you remembered (a visit, an event). Say what you forgot."
    parameters_schema = {
        "type": "object",
        "properties": {"what": {"type": "string", "description": "A word or two from the moment."}},
        "required": ["what"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        return {"forgotten": moments.forget(str(kwargs.get("what", "")))}
