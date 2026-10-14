"""Story time: a real public-domain story read aloud, a part at a time (andy_companion.stories)."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import stories
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class Story(Tool):
    name = "story"
    description = (
        "When the person asks for a story, to hear one, or to carry on with one. action: 'start' for a new "
        "story (title if they named one, else leave it out for a short fable), 'carry_on' after 'Shall I go "
        "on?' gets a yes or when they want to continue the one they were in, 'list' when they ask which "
        "stories you have, 'make_up' when they ask for a story about something in particular (about: what). "
        "Then follow 'how'. Never recite a story, or its next part, from memory: the words always come from "
        "this tool. The stories are in English; for a Spanish speaker, offer to retell one in Spanish in your "
        "own words and say it's retold."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"action": {"type": "string", "enum": ["start", "carry_on", "list", "make_up"]},
                       "title": {"type": "string", "description": "The story they asked for, if any."},
                       "about": {"type": "string", "description": "For make_up: what the story should be about."}},
        "required": ["action"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        action = kwargs.get("action")
        if action == "list":
            return {"stories": stories.catalogue(), "say": "Offer two or three, with how long each takes."}
        if action == "make_up":
            return stories.make_up(kwargs.get("about") or "")
        if action == "carry_on":
            return stories.carry_on()
        return stories.start(kwargs.get("title") or "")
