"""Everything Andy remembers about the person, so they always know, and can ask Andy to forget."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import moments, places
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class WhatYouRemember(Tool):
    name = "what_you_remember"
    description = (
        "When the person asks what you remember about them, or what you know. Tell them everything listed, "
        "plainly, and that they can ask you to forget any of it. To forget a moment use forget_moment; a "
        "fact, forget; where something is, forget_place."
    )
    parameters_schema = {"type": "object", "properties": {}}

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        facts = []
        try:
            from reachy_mini_conversation_app import memory
            facts = [f.text for f in memory.list_memory_facts()]
        except Exception:
            facts = []
        return {"facts": facts,
                "moments": [{"what": m["what"], "day": moments.spoken_day(m["on"])} for m in moments.upcoming(days=60)],
                "places": [{"what": p["what"], "where": p["where"], "when": places.ago(p["at"])} for p in places.kept()],
                "note": "This is everything Andy keeps about the person, besides their reminders and settings."}
