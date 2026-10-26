"""Remember a dated moment, only after the person says yes, so Andy can follow up."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import moments
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class RememberMoment(Tool):
    name = "remember_moment"
    description = (
        "When the person mentions something coming up or just happened with a day (a visit, an appointment, "
        "a grandchild's recital, a birthday), call this to prepare a proposal with what it is, in their words, "
        "and the day (today, tomorrow, a weekday, or YYYY-MM-DD). If confirmation_needed is returned, nothing "
        "was saved: read 'say' exactly, wait for a yes, then call again with the same arguments. "
        "You will bring it up on the day and ask how it went the day after. Never claim it is saved before success."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "what": {"type": "string", "description": "What it is, in their words."},
            "day": {"type": "string", "description": "today, tomorrow, a weekday, or YYYY-MM-DD."},
        },
        "required": ["what", "day"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        try:
            m = moments.add(kwargs.get("what", ""), kwargs.get("day", ""))
        except ValueError as e:
            return {"error": str(e)}
        return {"remembered": m["what"], "day": moments.spoken_day(m["on"])}
