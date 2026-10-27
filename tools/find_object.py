"""Find something in the room by looking around and pointing with the head (andy_companion.finder)."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import finder, vision
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class FindObject(Tool):
    name = "find_object"
    description = (
        "When the person asks to find, look for or search for an object, asks where it is or can't find it "
        "in the room (their watch, wristwatch, glasses, keys, phone, remote or cup), call this immediately "
        "in the same response with what: the thing in a few words. Call the tool before speaking; "
        "never only announce that you will look or give places to check instead of using the camera. "
        "You will turn your head around the room and point at it if you see it. Then follow "
        "'how'. Never for finding a person."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"what": {"type": "string", "description": "The thing to find, e.g. 'reading glasses'."}},
        "required": ["what"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        if deps is None or not getattr(deps, "camera_enabled", False):
            return {"error": "My camera is off right now, so I can't look around."}
        if not vision.configured():
            return {"error": "My eyes in the cloud are switched off right now, so I can't look around."}
        out = await finder.find(kwargs.get("what", ""), deps.reachy_mini, deps.movement_manager)
        return {k: v for k, v in out.items() if not k.startswith("_")}   # head angles are for Andy, not the model
