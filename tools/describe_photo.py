"""Describe a photo a family member sent, which is on Andy's screen."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from andy_companion import vision
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class DescribePhoto(Tool):
    name = "describe_photo"
    description = (
        "When you have just been told a family member sent a photo (you are given its photo_id), or the person "
        "asks about the photo on the screen. Say in one or two warm sentences what is in it. Never say who a "
        "person is unless the family member's words say so."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"photo_id": {"type": "string", "description": "The photo's id."}},
        "required": ["photo_id"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        return await asyncio.to_thread(vision.describe_photo, str(kwargs.get("photo_id", "")))
