"""Cancel a reminder."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import reminders
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class CancelReminder(Tool):
    name = "cancel_reminder"
    description = (
        "Cancel a reminder the person no longer wants. Call list_reminders first to find its id, "
        "and confirm which one you cancelled."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"id": {"type": "string", "description": "The reminder's id from list_reminders."}},
        "required": ["id"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        return {"cancelled": reminders.cancel(str(kwargs.get("id", "")))}
