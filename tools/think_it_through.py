"""Hand a hard question to NVIDIA Nemotron 3 Ultra and speak its considered answer."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from andy_companion import deeper, settings, web
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class ThinkItThrough(Tool):
    name = "think_it_through"
    description = (
        "When the person asks you to help them think something through: a decision, a dilemma, weighing two "
        "options, or a hard question about life that deserves care (for example 'Should I move closer to my "
        "daughter?'). A bigger model thinks it over for a few seconds; then tell them its answer in your own "
        "warm words, briefly. Not for quick facts (look_up), the news, or medical, legal or money decisions "
        "about them (suggest the right person)."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"question": {"type": "string", "description": "Their question, with what they told you about it."},
                       "language": {"type": "string", "enum": ["en", "es"], "description": "The language they are speaking."}},
        "required": ["question"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        language = web.chosen_language(kwargs.get("language"), settings.get()["language"])
        try:
            answer = await asyncio.to_thread(deeper.think, str(kwargs.get("question", "")), language)
        except deeper.DeeperError as e:
            return {"error": str(e)}
        return {"answer": answer, "thought_by": "NVIDIA Nemotron 3 Ultra",
                "note": "Say this in your own words, briefly and warmly; it is help to think, not a decision."}
