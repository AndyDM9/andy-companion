"""Set a reminder Andy says out loud when it is due."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import reminders
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class SetReminder(Tool):
    name = "set_reminder"
    description = (
        "Set a reminder that you will say out loud when it is due, only when the person asks. Use the "
        "person's own words for 'what', only what to do, without the time ('take a pill', not 'take a pill "
        "at eight'). Give either 'minutes' from now, or 'at' as HH:MM on a 24-hour "
        "clock (today, or tomorrow if that time has passed). Use repeat='daily' only if they ask for "
        "every day ('every morning at eight' is at='08:00', repeat='daily'; 'every evening at nine' is "
        "'21:00'). Don't ask for a name for it or for am/pm when the words say. A reminder to take their "
        "medicine is set like any other, in their words, with nothing about doses. Then confirm the time "
        "back in one short sentence."
    )
    parameters_schema = {
        "type": "object",
        "properties": {
            "what": {"type": "string", "description": "What to remind them of, in their words, without the time."},
            "minutes": {"type": "number", "description": "Minutes from now."},
            "at": {"type": "string", "description": "Time of day, HH:MM, 24-hour."},
            "repeat": {"type": "string", "enum": ["daily"], "description": "Only if they ask for every day."},
        },
        "required": ["what"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        try:
            item = reminders.add(kwargs.get("what", ""), kwargs.get("minutes"), kwargs.get("at"),
                                 kwargs.get("repeat"))
        except ValueError as e:
            return {"error": str(e)}
        when = reminders.spoken_time(item["due"])
        return {"set": True, "when": when, "daily": item["repeat"] == "daily", "id": item["id"]}
