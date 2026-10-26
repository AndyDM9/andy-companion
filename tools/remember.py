"""Andy's explicit memory tool, with the same store as Pollen's memory module."""
from __future__ import annotations

from reachy_mini_conversation_app.memory import add_memory_fact
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class Remember(Tool):
    name = "remember"
    description = (
        "Keep one short fact only when asked or confirmed. An explicit request to remember can be saved directly. "
        "Otherwise call once to prepare a proposal. If confirmation_needed is returned, nothing was saved: "
        "read 'say' exactly, wait for a yes, then call again with the same fact. Never save silently. "
        "Never keep passwords, payment details or medicine instructions. Never claim success before the tool reports it."
    )
    parameters_schema = {"type": "object", "properties": {
        "fact": {"type": "string", "description": "One short fact in the person's words."}}, "required": ["fact"]}

    async def __call__(self, deps: ToolDependencies, **kwargs):
        fact = kwargs.get("fact")
        if not isinstance(fact, str) or not fact.strip() or len(fact) > 200:
            return {"error": "One short fact, at most 200 characters, is needed."}
        stored = add_memory_fact(deps.instance_path, fact)
        if stored is None:
            return {"error": "Nothing was saved."}
        return {"saved": stored.text, "memory_id": stored.id}
