"""What day and time it is. Andy calls this instead of guessing."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import clock
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class GetToday(Tool):
    name = "get_today"
    description = (
        "Get today's day, date and the time right now. Call this whenever the day, date, time or "
        "morning/afternoon/evening matters, and at the start of every conversation. Never guess."
    )
    parameters_schema = {"type": "object", "properties": {}}

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        return clock.today()
