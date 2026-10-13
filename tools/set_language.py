"""Speak and show the screen in English or Spanish, and keep it that way."""

from __future__ import annotations

from typing import Any, Dict

from andy_companion import settings
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class SetLanguage(Tool):
    name = "set_language"
    description = (
        "When the person asks you to speak Spanish or English (for example 'háblame en español'), or starts "
        "speaking to you in the other language and wants to stay in it. language: en or es. It also changes "
        "the screen and the daily plan, and is remembered."
    )
    parameters_schema = {"type": "object", "properties": {"language": {"type": "string", "enum": ["en", "es"]}},
                         "required": ["language"]}

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        try:
            settings.update(language=kwargs.get("language"))
        except ValueError as e:
            return {"error": str(e)}
        return {"language": kwargs.get("language"), "remembered": True}
