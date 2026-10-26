"""Remember where something is, only after the person said yes (andy_companion.places; PLAN B46)."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import finder, places, vision
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class RememberPlace(Tool):
    name = "remember_place"
    description = (
        "When the person tells you where they are putting or have put something ('my keys are here', 'I'm leaving "
        "my glasses on the shelf'), call this first to prepare a proposal with "
        "what (the thing, in a few words) and said_where (their own words for the place, if they said any). You "
        "look to see it and keep where it is only when authorized. If confirmation_needed is returned, nothing "
        "was saved: read 'say' exactly, wait for a yes, and call again unchanged. Later you look there first."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "what": {"type": "string", "description": "The thing, e.g. 'house keys'."},
            "said_where": {"type": "string", "description": "Their words for the place, if any, e.g. 'on the hall table'."},
        },
        "required": ["what"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        what = finder.tidy_what(kwargs.get("what", ""))
        said = " ".join(str(kwargs.get("said_where", "")).split())[:120]
        seen: Dict[str, Any] = {}
        if deps is not None and getattr(deps, "camera_enabled", False) and vision.configured():
            seen = await finder.find(what, deps.reachy_mini, deps.movement_manager)
        try:
            if seen.get("found"):
                places.keep(what, seen.get("where") or said, seen.get("_yaw"), seen.get("_pitch"))
                return {"kept": True, "what": what, "where": seen.get("where") or said,
                        "how": "Say you'll remember where they are, in a few words, naming the place."}
            if said:
                places.keep(what, said)
                return {"kept": True, "what": what, "where": said,
                        "how": "Say you couldn't see them from where you are, but you'll remember what they said."}
        except ValueError as e:
            return {"error": str(e)}
        return {"kept": False, "how": "Say kindly you couldn't see them from here; ask them to tell you where they are, "
                                      "or to hold them up so you can see them."}
