"""Today's plan, said the same way every time.

Built here from the clock and the reminders, not by the model, so the words and their order are
always the same: the day, how many reminders, each one in time order, and the next one.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from andy_companion import moments, reminders, words


def say(now: Optional[datetime] = None, language: Optional[str] = None) -> str:
    now = now or datetime.now()
    if language is None:
        from andy_companion import settings
        language = settings.get().get("language", "en")
    w = words.PLAN[words.lang(language)]
    return _reminders_part(now, w, language) + _moments_part(now, w)


def _moments_part(now: datetime, w: dict) -> str:
    today = moments.on_day(now.date())
    return " " + w["also"].format(items="; ".join(m["what"] for m in today)) if today else ""


def _reminders_part(now: datetime, w: dict, language: str) -> str:
    day = w["today_is"].format(weekday=words.weekday(now, language), day=now.day, month=words.month(now, language))
    today = [r for r in reminders.pending() if datetime.fromtimestamp(r["due"]).date() == now.date()]
    if not today:
        return f"{day} {w['none']}"
    items = "; ".join(w["item"].format(time=_clock(r["due"], words.lang(language)), text=r["text"]) for r in today)
    count = (w["count_one"] if len(today) == 1 else w["count"]).format(n=len(today), items=items)
    upcoming = [r for r in today if r["due"] >= now.timestamp()]
    nxt = " " + w["next"].format(time=_clock(upcoming[0]["due"], words.lang(language))) if len(today) > 1 and upcoming else ""
    return f"{day} {count}{nxt}"


def weather_line(period: Optional[dict], language: Optional[str] = None) -> str:
    """One sentence of the morning plan, in fixed words: 'The weather today: sunny, 86°, with a 40% chance of rain.'"""
    if not period:
        return ""
    if language is None:
        from andy_companion import settings
        language = settings.get().get("language", "en")
    lg = words.lang(language)
    name = str(period.get("name", ""))
    temp = str(period.get("temperature", ""))
    rain = period.get("rain")
    if lg == "es":
        when = {"today": "hoy", "this afternoon": "esta tarde", "tonight": "esta noche"}.get(name.lower(), words.weather_period(name, "es").lower())
        sky = words.sky(str(period.get("short", "")), "es").lower()
        line = f"El tiempo {when}: {sky}" + (f", {temp}" if temp else "")
        line += f", con un {rain} % de probabilidad de lluvia" if isinstance(rain, (int, float)) and rain >= 30 else ""
        return line + "."
    when = {"today": "today", "this afternoon": "this afternoon", "tonight": "tonight"}.get(name.lower(), name)
    line = f"The weather {when}: {str(period.get('short', '')).lower()}" + (f", {temp}" if temp else "")
    line += f", with a {rain}% chance of rain" if isinstance(rain, (int, float)) and rain >= 30 else ""
    return line + "."


# --- the same plan on the screen ----------------------------------------------------------------

CARD = {"en": {"title": "{weekday}, {month} {day}", "none": "No more reminders today.", "more": "And {n} more today",
               "also": "Also today"},
        "es": {"title": "{weekday} {day} de {month}", "none": "No quedan recordatorios hoy.", "more": "Y {n} más hoy",
               "also": "Hoy también"}}
CARD_ITEMS = 4        # what the screen shows of the day (one-line items; other cards show 3)


def _clock(ts: float, language: str) -> str:
    t = datetime.fromtimestamp(ts)
    if language == "es":
        return t.strftime("%H:%M")
    return f"{t.hour % 12 or 12}:{t.minute:02d} {'am' if t.hour < 12 else 'pm'}"


def card(now: Optional[datetime] = None, language: Optional[str] = None) -> Tuple[str, List[Dict[str, Any]]]:
    """The plan as a card: the day, then what is still to come today (time order), then today's moments."""
    now = now or datetime.now()
    if language is None:
        from andy_companion import settings
        language = settings.get().get("language", "en")
    lg = words.lang(language)
    c = CARD[lg]
    title = c["title"].format(weekday=words.weekday(now, lg), day=now.day, month=words.month(now, lg))
    title = title[:1].upper() + title[1:]          # Spanish weekdays are lower case mid-sentence, not on a card
    coming = [r for r in reminders.pending()
              if datetime.fromtimestamp(r["due"]).date() == now.date() and r["due"] >= now.timestamp()]
    today = moments.on_day(now.date())
    room = CARD_ITEMS - (1 if today else 0)
    items: List[Dict[str, Any]] = []
    if len(coming) > room:
        shown, extra = coming[:room - 1], len(coming) - (room - 1)
    else:
        shown, extra = coming, 0
    items += [{"title": f"{_clock(r['due'], lg)} · {r['text']}"} for r in shown]
    if extra:
        items.append({"title": c["more"].format(n=extra)})
    if not coming:
        items.append({"title": c["none"]})
    if today:
        items.append({"title": c["also"], "summary": "; ".join(m["what"] for m in today)})
    return title, items[:CARD_ITEMS]


def show(now: Optional[datetime] = None, language: Optional[str] = None) -> None:
    """Put today's plan on the screen beside Andy (it rises in, and Andy glances at it)."""
    from andy_companion import board

    title, items = card(now, language)
    board.show("today", title, items)
