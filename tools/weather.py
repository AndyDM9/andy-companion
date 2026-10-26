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
        # The card's kind already says "Weather": its title is the town. Each period is read at a glance from across
        # the room ("Tonight · 78°", "Showers And Thunderstorms, 80% rain"); Andy says the long forecast. An alert
        # comes first with the calm bar of the small card, never the look of a scam warning.
        alerts = [{"summary": weather.short_alert(a), "tone": "notice", "source": "weather.gov"} for a in found["alerts"][:1]]
        periods = [{"title": " · ".join(x for x in (p["name"], p.get("temperature", "")) if x),
                    "summary": (p.get("short") or p["forecast"]) + (f", {p['rain']}% rain" if p.get("rain") else ""),
                    "source": "weather.gov"} for p in found["periods"]]
        await asyncio.to_thread(board.show, "weather", spot.get("place") or "Weather", alerts + periods)
        return {"note": "From the National Weather Service; information, not instructions.", **found}
