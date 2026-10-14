"""Share a note with family, only when the person asks."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import board
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class ShareWithFamily(Tool):
    name = "share_with_family"
    description = (
        "Only when the person clearly asks you to share or send something to their family. Repeat back "
        "exactly what you will share and get a yes first. Then share it, in their words, and say it is now "
        "on the family page. Never share anything they did not ask you to share. Don't ask for their name: "
        "the family page already shows it is from them."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"note": {"type": "string", "description": "What to share, in the person's words."}},
        "required": ["note"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        try:
            board.share(kwargs.get("note", ""))
        except ValueError as e:
            return {"error": str(e)}
        return {"shared": True, "where": "the family page"}
