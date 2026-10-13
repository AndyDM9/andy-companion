"""The reminders that are waiting."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import reminders
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class ListReminders(Tool):
    name = "list_reminders"
    description = "List the reminders that are waiting, with their times, when the person asks what reminders they have."
    parameters_schema = {"type": "object", "properties": {}}

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        items = reminders.pending()
        return {"reminders": [{"id": r["id"], "what": r["text"], "when": reminders.spoken_time(r["due"]),
                               "daily": r.get("repeat") == "daily"} for r in items]}
