"""Speak louder or quieter, and keep it that way."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from andy_companion import settings, volume
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class SetVolume(Tool):
    name = "set_volume"
    description = (
        "When the person asks you to speak louder or quieter, or names a volume. change is 'louder', "
        "'quieter', or a number from 10 to 100. It is remembered for later. Then say one short sentence "
        "at the new volume."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"change": {"type": "string", "description": "'louder', 'quieter', or a number 10-100."}},
        "required": ["change"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        change = str(kwargs.get("change", "")).strip().lower()
        try:
            current = await asyncio.to_thread(volume.current)
            target = settings.next_volume(current, change if change in ("louder", "quieter") else int(change))
            await asyncio.to_thread(volume.set_level, target)
        except ValueError:
            return {"error": "Say louder, quieter, or a number from 10 to 100."}
        except Exception as e:
            return {"error": f"The volume could not be changed ({type(e).__name__})."}
        settings.update(volume=target)
        at_max = target == 100 and change == "louder"
        return {"volume": target, "already_loudest": at_max, "remembered": True}
