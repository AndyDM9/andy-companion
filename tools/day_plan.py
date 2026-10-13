"""Today's plan, the same words every time."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import dayplan
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class DayPlan(Tool):
    name = "day_plan"
    description = (
        "When the person asks what is on today, what's next, or what they have to do, get today's plan "
        "and read its 'say' text exactly as written, word for word, so it always sounds the same."
    )
    parameters_schema = {"type": "object", "properties": {}}

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        return {"say": dayplan.say()}
