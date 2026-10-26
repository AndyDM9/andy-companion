"""Look into a question that needs more than one search; Andy tells the answer when it is ready."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import looking, settings, web
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class LookInto(Tool):
    name = "look_into"
    description = (
        "When the person asks you to look into, find out about, or research something that needs more than a "
        "quick answer: a change in their town, how a service works, comparing options, the background to a news "
        "story. It runs for a minute or two in the background: say you will look into it and tell them when it's "
        "ready, then carry on. It does the searching: call no other search tool for the same question. "
        "For a quick fact use look_up instead. Never for medical, legal or money decisions "
        "about them: suggest the right person instead. When they ask you to stop looking, stop searching or "
        "never mind, call it with stop=true: it stops at once and nothing of it is said."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"question": {"type": "string", "description": "What to look into, in their words."},
                       "language": {"type": "string", "enum": ["en", "es"],
                                    "description": "The language the person is speaking to you."},
                       "stop": {"type": "boolean", "description": "True when they ask you to stop looking into it."}},
        "required": ["question"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        if kwargs.get("stop"):
            return looking.stop()
        s = settings.get()
        return looking.start(str(kwargs.get("question", "")), s["place"] or "",
                             web.chosen_language(kwargs.get("language"), s["language"]))
