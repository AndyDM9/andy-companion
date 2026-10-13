"""Today's plan, said the same way every time.

Built here from the clock and the reminders, not by the model, so the words and their order are
always the same: the day, how many reminders, each one in time order, and the next one.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from andy_companion import moments, reminders


def say(now: Optional[datetime] = None) -> str:
    now = now or datetime.now()
    return _reminders_part(now) + _moments_part(now)


def _moments_part(now: datetime) -> str:
    today = moments.on_day(now.date())
    return f" Today is also: {'; '.join(m['what'] for m in today)}." if today else ""


def _reminders_part(now: datetime) -> str:
    day = f"Today is {now.strftime('%A')} {now.day} {now.strftime('%B')}."
    today = [r for r in reminders.pending() if datetime.fromtimestamp(r["due"]).date() == now.date()]
    if not today:
        return f"{day} You have no reminders today."
    items = "; ".join(f"at {datetime.fromtimestamp(r['due']).strftime('%H:%M')}, {r['text']}" for r in today)
    count = f"{len(today)} reminder{'s' if len(today) != 1 else ''}"
    upcoming = [r for r in today if r["due"] >= now.timestamp()]
    nxt = f" The next one is at {datetime.fromtimestamp(upcoming[0]['due']).strftime('%H:%M')}." if len(today) > 1 and upcoming else ""
    return f"{day} You have {count} today: {items}.{nxt}"
