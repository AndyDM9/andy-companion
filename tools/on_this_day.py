"""On this day: something gentle that happened today in years gone by (andy_companion.onthisday)."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from andy_companion import onthisday, settings
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class OnThisDay(Tool):
    name = "on_this_day"
    description = (
        "When the person asks what happened on this day, wants something to talk about, or says yes when you "
        "offer a bit of history. Gives a few gentle things that happened on today's date in years gone by, from "
        "Wikipedia. language: the language you are speaking now. Then follow 'how'."
    )
    parameters_schema = {"type": "object", "properties": {"language": {"type": "string", "enum": ["en", "es"]}}}

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        try:
            result = await asyncio.to_thread(onthisday.today, language=kwargs.get("language") or "en")
        except Exception:
            return {"error": "Nothing from today's date just now. Offer something else to talk about."}
        try:
            onthisday.show(result, language=settings.get()["language"])
        except Exception:
            pass
        return result
