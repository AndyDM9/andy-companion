"""A joke or a riddle from Andy's chosen set (andy_companion.fun), never the same one soon."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import fun
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class TellJoke(Tool):
    name = "tell_joke"
    description = (
        "When the person asks for a joke, something funny, or a riddle, or says yes when you offer one. "
        "Never make up a joke yourself: use this, so it is always a kind one. kind: 'joke' or 'riddle'. "
        "language: the language you are speaking now. Then follow 'how'."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"kind": {"type": "string", "enum": ["joke", "riddle"]},
                       "language": {"type": "string", "enum": ["en", "es"]}},
        "required": ["kind"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        out = fun.pick(kwargs.get("kind", "joke"), kwargs.get("language") or "en")
        if "punchline" in out:
            try:
                from andy_companion.body import giggle

                giggle.arm()                  # the antennas wiggle once the punchline has been said
            except Exception:
                pass
        return out
