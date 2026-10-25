"""The date and time in words Andy can say. Andy never guesses the day; it asks this."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional


def part_of_day(now: datetime) -> str:
    if 5 <= now.hour < 12:
        return "morning"
    if 12 <= now.hour < 17:
        return "afternoon"
    if 17 <= now.hour < 22:
        return "evening"
    return "night"


def today(now: Optional[datetime] = None, language: str = "en") -> Dict[str, str]:
    from andy_companion import words

    now = now or datetime.now()
    weekday = now.strftime("%A")
    date = f"{now.strftime('%B')} {now.day}, {now.year}"      # "October 14, 2026", as said in the US
    time = now.strftime("%H:%M")
    out = {
        "weekday": weekday,
        "date": date,
        "time": time,
        "part_of_day": part_of_day(now),
        "say": f"It is {weekday}, {date}, and the time is {time}.",
    }
    if words.lang(language) == "es":
        out["shown"] = {"weekday": words.weekday(now, "es"), "date": f"{now.day} de {words.month(now, 'es')}",
                        "part_of_day": words.PARTS["es"][part_of_day(now)], "today": "Hoy",
                        "empty": "Nada para hoy. Pídale a Andy que le recuerde algo.", "from": "De",
                        "tomorrow": "Mañana", "daily": "todos los días"}
    else:
        out["shown"] = {"weekday": weekday, "date": f"{now.strftime('%B')} {now.day}",
                        "part_of_day": part_of_day(now), "today": "Today",
                        "empty": "Nothing planned today. Ask Andy to remind you of something.", "from": "From",
                        "tomorrow": "Tomorrow", "daily": "every day"}
    return out
