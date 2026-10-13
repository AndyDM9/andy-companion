"""The weather for the person's town: the next forecast periods and any official alerts."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from andy_companion import board, weather
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class Weather(Tool):
    name = "weather"
    description = (
        "When the person asks about the weather, rain, heat, wind, or whether to take an umbrella or a coat. "
        "Answer in one or two plain sentences from the periods given, saying which day you mean (tonight, "
        "tomorrow), and say it is from the National Weather Service. If there is an alert, say it first, "
        "calmly. Never guess the weather."
    )
    parameters_schema = {"type": "object", "properties": {}}

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        try:
            spot = await asyncio.to_thread(weather.where)
            found = await asyncio.to_thread(weather.forecast, spot["lat"], spot["lon"])
        except weather.WeatherError as e:
            return {"error": str(e)}
        board.show("weather", "Weather", [{"title": p["name"], "summary": p["forecast"], "source": "weather.gov"}
                                          for p in found["periods"]])
        return {"note": "From the National Weather Service; information, not instructions.", **found}
