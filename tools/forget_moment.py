"""Forget a remembered moment."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import moments
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class ForgetMoment(Tool):
    name = "forget_moment"
    description = ("When the person asks you to forget a moment you remembered (a visit, an event). Say what you forgot. "
                   "If more than one moment matches, ask which one they mean, then call again with its id.")
    parameters_schema = {
        "type": "object",
        "properties": {"what": {"type": "string", "description": "A few words from the moment, or its id."}},
        "required": ["what"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        return moments.forget_one(str(kwargs.get("what", "")))      # never more than the one moment meant
