"""Be quiet for a while: Andy rests, stops listening, and comes back by itself."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from andy_companion import state
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies

STOP_AFTER_S = 8.0  # time to say the confirmation before resting


class QuietFor(Tool):
    name = "quiet_for"
    description = (
        "When the person asks you to be quiet, stop listening, or leave them in peace for a while, "
        "rest for that many minutes (1 to 1440). Say in one short sentence until what time, and that "
        "they can wake you sooner by saying 'Andy, wake up'. Reminders still come on time."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"minutes": {"type": "number", "description": "How long to stay quiet, in minutes."}},
        "required": ["minutes"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        try:
            until = state.quiet_for(kwargs.get("minutes", 0))
        except ValueError as e:
            return {"error": str(e)}
        if deps.go_to_sleep is not None:
            async def rest() -> None:
                await asyncio.sleep(STOP_AFTER_S)
                await asyncio.to_thread(deps.go_to_sleep)
            asyncio.get_running_loop().create_task(rest())
        return {"quiet_until": until.strftime("%H:%M"), "wake_phrase": "Andy, wake up"}
