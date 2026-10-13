"""Show the settings code on the screen, so a helper's phone opens Andy's settings without typing a link."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import board
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class SettingsCode(Tool):
    name = "settings_code"
    description = (
        "When someone asks to see the settings code, or to set Andy up or change Andy's settings from a phone. "
        "Shows a code on the screen for two minutes: scanning it with a phone camera opens Andy's settings. "
        "Say that, and that the code disappears in two minutes."
    )
    parameters_schema = {"type": "object", "properties": {}}

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        board.show_settings_code()
        return {"shown": True, "for_minutes": 2}
