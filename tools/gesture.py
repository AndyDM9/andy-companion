"""Moves taught by hand with Andy's antennas, learned and played back (andy_companion.gestures; PLAN B47)."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from andy_companion import gestures
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class Gesture(Tool):
    name = "gesture"
    description = (
        "Moves someone teaches you with your antennas. When they want to teach you one ('learn a new move', 'let me "
        "teach you Sofia's wave'), first say 'Move my antennas gently now; I'll remember for six seconds', then call "
        "this with action 'learn' and a short name (theirs, or 'my move'): your antennas go soft while they move them, "
        "then you play it back. To do one you learned ('do Sofia's wave'): action 'do' and its name. 'list' to say "
        "which moves you know, 'forget' to drop one. Only your antennas move; never your head."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "action": {"type": "string", "enum": ["learn", "do", "list", "forget"]},
            "name": {"type": "string", "description": "The move's name, e.g. \"Sofia's wave\"."},
        },
        "required": ["action"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        action, name = kwargs.get("action", "list"), gestures.tidy_name(kwargs.get("name", ""))
        if action == "list":
            return {"moves": gestures.names()}
        if action == "forget":
            return {"forgotten": gestures.forget(name), "name": name}
        if deps is None or getattr(deps, "reachy_mini", None) is None:
            return {"error": "I can't move right now."}
        if action == "do":
            out = gestures.do(name, deps.reachy_mini, deps.movement_manager)
            if not out["done"]:
                return {**out, "how": "Say you haven't learned that one yet, and which moves you know, if any."}
            return {**out, "how": "Say only one short word as you do it, like 'There!'"}
        out = await gestures.learn(name, deps.reachy_mini, deps.movement_manager, sleep=asyncio.sleep)
        if not out["learned"]:
            return {**out, "how": "Say you didn't feel your antennas move; offer to try again, moving them a little more."}
        return {**out, "how": "Say you've learned it, name it, and that you just showed it; they can ask for it any time."}
