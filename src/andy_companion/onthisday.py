"""On this day: a gentle, dated thing that happened today in years gone by, to talk about.

From Wikipedia's "On this day" feed (en.wikipedia.org/api/rest_v1/feed/onthisday; free, no key, with
a User-Agent naming the project, as Wikimedia asks). Wikipedia's text is CC BY-SA 4.0: Andy says
"according to Wikipedia", and the screen names Wikipedia and the licence. Andy saying it in its own
words (or in Spanish) is an adaptation, which the licence allows with that credit.

Only gentle things are chosen, twice over:
- in code: firsts, openings, launches, records, films, songs, books, flights and space, from 1900 to
  2010 (within the lifetimes of the people Andy talks with), with words for death, war, violence,
  disasters, politics, religion or illness ruled out;
- then Nemotron 3.5 Lightning reads the shortlist against the same rule (structured output, once a
  day, cached), because a word list always leaks ("Hijacking of Lufthansa Flight 181" passed on
  "Flight", 2026-10-13). If that check can't be made, nothing is offered.
Andy invites a memory of the time with an open question, never "Do you remember". See decision 0006.
"""

from __future__ import annotations

import json
import os
import random
import re
import time
import urllib.request
from datetime import date
from typing import Any, Callable, Dict, List, Optional

FEED = "https://en.wikipedia.org/api/rest_v1/feed/onthisday/all/{month:02d}/{day:02d}"
USER_AGENT = "AndyCompanion/0.1 (https://github.com/AndyDM9/andy-companion)"
TIMEOUT_S = 5
RETRY_AFTER_S = 600                        # after a failure, don't make the person wait again for ten minutes
PICK = 3
YEARS = (1900, 2010)
CREDIT = {"source": "Wikipedia", "licence": "CC BY-SA 4.0", "url": "https://en.wikipedia.org/wiki/Wikipedia:Selected_anniversaries"}

DARK = re.compile(
    r"\b(kill|killed|killing|dies|died|death|deaths|dead|murder|war|wars|battle|attack|bomb|terror|shoot|shot|massacre|genocide|"
    r"invasion|invade|army|military|troops|soldier|navy|crash|disaster|earthquake|flood|hurricane|tornado|tsunami|fire|"
    r"explosion|explosiv|detonat|sink|sank|wreck|riot|execut|assassin|hostage|kidnap|arrest|trial|prison|convict|sentenced|"
    r"strike|protest|revolution|coup|election|president|prime minister|party|parliament|communist|nazi|fascis|king|queen|"
    r"emperor|church|pope|religio|islam|christian|jewish|buddh|hindu|god|slave|racis|caste|abortion|nuclear|weapon|missile|"
    r"bomber|fortress|disease|epidemic|pandemic|virus|cancer|famine|poverty|scandal|fraud|sex|lgbt|gay|lesbian|refugee|"
    r"deport|ill-fated|forcibl|exclud|injur|wound|accident|collapse|toxic|spill|fail|lost|missing|underwear|hijack|"
    r"politburo|secretary|minister|government|senate|congress|vote|voted|treaty|independence|liberation|militant)", re.I)
GOOD = re.compile(
    r"\b(first|opens|opened|opening|launch|launched|launches|record|premiere|premiered|released|release|published|invent|"
    r"invented|patent|discovered|discover|won|wins|world series|olympic|landed|landing|flight|flew|broadcast|aired|album|"
    r"film|song|musical|novel|book|magazine|television|radio|bridge|highway|railway|tunnel|museum|park|zoo|space|orbit|"
    r"moon|satellite|telescope|exhibition|festival|completed|founded|introduced|unveiled)\b", re.I)

HOW = {"en": ("Begin with 'According to Wikipedia'. Choose one, the one most likely to interest them, and say it "
              "simply with its year, in a sentence or two, no list. Then ask one open question that invites a memory "
              "of the time, like 'What was that time like for you?' Never 'Do you remember…'. Offer another only if "
              "they'd like one."),
       "es": ("Answer in Spanish, with 'usted'. Begin with 'Según Wikipedia'. Choose one, the one most likely to "
              "interest them, and say it simply with its year, in a sentence or two, no list. Then ask one open "
              "question that invites a memory of the time, like '¿Cómo era aquella época para usted?' Never ask "
              "whether they remember it. Offer another only if they'd like one.")}


def gentle(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out, seen = [], set()
    for e in events:
        text = " ".join(str(e.get("text", "")).split())
        try:
            year = int(e.get("year"))
        except (TypeError, ValueError):
            continue
        if not (YEARS[0] <= year <= YEARS[1]) or DARK.search(text) or not GOOD.search(text) or text in seen:
            continue
        seen.add(text)
        out.append({"year": year, "text": text[:240]})
    return out


def fetch(day: date, opener: Optional[Callable] = None) -> List[Dict[str, Any]]:
    req = urllib.request.Request(FEED.format(month=day.month, day=day.day), headers={"User-Agent": USER_AGENT})
    with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT_S) as r:
        data = json.loads(r.read())
    return [e for key in ("selected", "events") for e in data.get(key, [])]


VET = ("These are things that happened on today's date in years gone by. A home companion robot will chat "
       "about one with an older adult. Keep only those that are cheerful or neutral to talk about: an "
       "invention, a first, a record, a sports win, a film, song or book, a building or bridge opening, a flight "
       "or space mission that went well. Leave out anything that involves violence, crime, hijacking, death, "
       "war or the military, disasters or accidents, politics, protest or government, religion, illness, or "
       "a group of people being treated badly, even in passing. Return the numbers to keep.")
VET_SCHEMA = {"type": "object", "additionalProperties": False, "required": ["keep"],
              "properties": {"keep": {"type": "array", "items": {"type": "integer"}}}}


class VetError(Exception):
    pass


def vet(events: List[Dict[str, Any]], opener: Optional[Callable] = None) -> List[Dict[str, Any]]:
    """The shortlist as a model reads it against the rule; raises VetError if it can't be read."""
    if not events:
        return []
    key = os.environ.get("NEBIUS_API_KEY", "")
    if not key:
        raise VetError("no Token Factory key")
    base = os.environ.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/").rstrip("/")
    listing = "\n".join(f"{i}. {e['year']}: {e['text']}" for i, e in enumerate(events))
    body = {"model": os.environ.get("ANDY_MODEL", "nvidia/Nemotron-3_5-Lightning"), "temperature": 0, "max_tokens": 200,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "system", "content": VET}, {"role": "user", "content": listing}],
            "response_format": {"type": "json_schema", "json_schema": {"name": "vet", "schema": VET_SCHEMA, "strict": True}}}
    req = urllib.request.Request(base + "/chat/completions", method="POST", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=8) as r:
            keep = json.loads(json.loads(r.read())["choices"][0]["message"]["content"])["keep"]
    except Exception as e:
        raise VetError(type(e).__name__) from None
    return [events[i] for i in sorted({int(i) for i in keep}) if 0 <= int(i) < len(events)]


_cache: Dict[str, List[Dict[str, Any]]] = {}
_failed = {"at": -1e9}


def today(day: Optional[date] = None, opener: Optional[Callable] = None, rng: Any = None,
          vetter: Optional[Callable] = None, language: str = "en") -> Dict[str, Any]:
    day = day or date.today()
    key = day.isoformat()
    if key not in _cache:
        if time.time() - _failed["at"] < RETRY_AFTER_S:
            raise VetError("tried a moment ago")
        try:
            shortlist = gentle(fetch(day, opener))
            kept = (vetter or vet)(shortlist)      # VetError: nothing is offered, and nothing cached
        except Exception:
            _failed["at"] = time.time()
            raise
        _cache.clear()
        _cache[key] = kept
    found = list(_cache[key])
    if not found:
        return {"events": [], "say": "Nothing gentle came up for today. Offer something else to talk about.", **CREDIT}
    rng = rng or random.Random(key)
    picks = rng.sample(found, min(PICK, len(found)))
    picks.sort(key=lambda e: e["year"])
    return {"events": picks, "how": HOW["es" if language == "es" else "en"], **CREDIT}


def show(result: Dict[str, Any], day: Optional[date] = None, language: str = "en", now: Optional[float] = None) -> None:
    """The picks on the screen under today's date, credited to Wikipedia with its licence."""
    from andy_companion import board, words

    day = day or date.today()
    lg = words.lang(language)
    title = f"{day.day} de {words.month(day, lg)}" if lg == "es" else f"{words.month(day, lg)} {day.day}"
    items = [{"title": str(e["year"]), "summary": e["text"]} for e in result["events"][:PICK]]
    if items:
        items.append({"title": "Sources", "summary": f"Wikipedia ({result['licence']})"})
        board.show("on_this_day", title, items, now=now or time.time())
