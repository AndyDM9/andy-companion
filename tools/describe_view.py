"""Describe what Andy sees, when the person asks."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from andy_companion import vision
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class DescribeView(Tool):
    name = "describe_view"
    description = (
        "Only when the person asks what you can see, what something looks like, or what colour or kind of "
        "thing they are holding up, including a photograph printed on paper. Use this for 'look at this photo'; "
        "a photograph is not read_letter. Describe it in two or three plain sentences. Never say who a person is "
        "or guess anything about a person's health or mood. For reading letters or labels use read_letter."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"question": {"type": "string", "description": "What they asked about, in short."}},
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        if deps is None or not getattr(deps, "camera_enabled", False):
            return {"error": "My camera is off right now."}
        result = await asyncio.to_thread(vision.look, lambda: deps.reachy_mini.media.get_frame(),
                                         str(kwargs.get("question", "")))
        if "description" in result:
            result["note"] = "Seen through the camera just now; the picture was not kept."
        return result
