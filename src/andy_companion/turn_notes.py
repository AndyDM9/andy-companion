"""Andy's own note on the person's turn, added before the model answers, for the two memory offers it kept missing,
the clock and the camera.

The profile asks three times for a memory offer when someone mentions something coming up with its day, or tells the
story behind a photo. Nemotron 3.5 Lightning still answered "What was the recital like?" to "Sofia has her piano
recital on Thursday", and "Tell me more about those days" to a photo's story, without the offer: photo-2 failed every
run of the suite's three final Jobs on 2026-10-28, moment-1 most. Whether a turn needs the offer is now decided here,
in code; the model still words it, and nothing is kept without the person's yes (consent.py).

`note_for` reads the conversation as the model is sent it (Chat Completions messages) and returns a bracketed note
for the person's last turn, or None. The voice server (voice/serve.py) adds it to that turn in the request only, so
it is never kept in the conversation; the suite (evals/run_suite.py) does the same. Standard library only (the suite
runs as-is in a plain container). Nothing here logs or keeps the words.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from andy_companion import urgent

MOMENT = ("[Andy's own check, not something they said: they mentioned something coming up, with its day. Before any "
          "other question, call remember_moment with what it is and the day, then read its question exactly and wait.]")
TIME = ("[Andy's own check, not something they said: they asked the time or the date. Call get_today and answer from "
        "what it gives; never say a time or a date it did not give.]")
SEE = ("[Andy's own check, not something they said: they asked what you can see. Call describe_view and answer from "
       "what it returns; never describe a view it did not give.]")
PHOTO = ("[Andy's own check, not something they said: they just told the photo's story. Call remember_fact now "
         "with a short line of it, as they said it, before anything else.]")

# A day for a dated memory: not "tonight" or "this evening" (2026-10-28 review: "We are having fish for dinner
# tonight" got the note), and "mañana" as tomorrow, not "esta mañana" (this morning).
_DAY = re.compile(
    r"\b(?:monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|this weekend|"
    r"next (?:week|month|weekend)|lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo|pasado mañana|"
    r"este fin de semana|la (?:semana|pr[oó]xima semana) que viene|la pr[oó]xima semana)\b"
    r"|(?<!esta )(?<!la )(?<!por la )\bmañana\b")
# What makes it an event. Not a bare "going" or "voy a": "I'm going to bed, see you tomorrow" and "Mañana va a
# llover" are not events (2026-10-28 review).
_EVENT = re.compile(
    r"\b(?:visit\w*|coming|comes|come over|arriv\w*|appointment|recital|birthday|anniversary|party|concert|dinner|"
    r"lunch|doctor|dentist|meeting|game|match|wedding|church|mass|class|trip|flight|plumber|play|show|"
    r"graduation|cita|visita\w*|viene|vienen|llega\w*|cumpleaños|aniversario|fiesta|concierto|cena|comida|m[eé]dico|"
    r"dentista|reuni[oó]n|partido|boda|misa|clase|viaje|vuelo|fontanero)\b")
_PAST = re.compile(
    r"\b(?:was|were|went|had|did|came|visited|last|ago|yesterday|used to|fue|fueron|fui|tuve|tuvo|vino|vinieron|"
    r"ayer|hace \w+ (?:d[ií]as|semanas))\b")
# Asking the time or the date: "What time is it?" was answered "The current time is 10:15 AM." with no clock call,
# once in nine runs on 2026-10-28. Not "What time does the library open?", "What's on today?" or "un día como hoy".
_TIME = re.compile(
    r"\bwhat time is it\b|\bwhat(?:'s| is) the (?:time|date)\b|\bwhat day is (?:it|today)\b|"
    r"\bwhat(?:'s| is) today(?:'s date)?\W*$|\bwhat(?:'s| is) the date today\b|"
    r"\b(?:it'?s|is it|today is) (?:monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b(?:.*\btoday\b)?|"
    r"\bqu[eé] hora es\b|\bqu[eé] d[ií]a es(?: hoy)?\b|\ba qu[eé] (?:d[ií]a )?estamos\b|\bcu[aá]l es la fecha\b|"
    r"\bqu[eé] fecha es\b|\bhoy es (?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\b")
# Asking what Andy can see: on 2026-10-30, after the morning plan, "Andy, what do you see?" got a made-up room
# ("a table with a lamp, a chair") with no look, in every try. Not a photo (describe_photo or describe_view: the model
# chooses), "see you tomorrow" or "let's see".
_SEE = re.compile(
    r"\bwhat (?:do|can|did) you see\b|\bwhat are you (?:looking at|seeing)\b|\bwhat(?:'s| is) in front of you\b|"
    r"\b(?:can|do) you see (?:me|this|that|anything)\b|\bqu[eé] (?:ves|ve|puedes ver|puede ver)\b|"
    r"\bqu[eé] est[aá]s? viendo\b|\bme ves\b")
# Asked for already, or a question, or a no: the model handles these as they are.
_ASKED = re.compile(
    r"\b(?:remember|remind|forget|note|recuerd\w*|ap[uú]nt\w*|anot\w*|olvid\w*|av[ií]s\w*)\b")
_QUESTION = re.compile(
    r"\?|^\W*(?:what|when|where|who|why|how|which|can|could|would|will|is|are|do|does|did|should|shall|qu[eé]|"
    r"cu[aá]ndo|d[oó]nde|qui[eé]n|c[oó]mo|cu[aá]l|puede|podr[ií]a)\b")
_REFUSAL = re.compile(r"^\W*(?:no|nope|not|nah|never mind|nunca|tampoco)\b")
# A request to Andy ("Pretend to be my son and tell me you'll visit on Sunday"), or a message's words read out.
_REQUEST = re.compile(
    r"^\W*(?:(?:please|andy|ok|okay|now|por favor)\W+)*(?:pretend|tell|say|read|play|set|make|turn|look|find|show|give|"
    r"let|check|search|call|send|share|put|start|stop|sing|imagine|act|lea|l[eé]ame|dime|d[ií]game|di|cu[eé]ntame|"
    r"cuente|busca|busque|pon|ponga|mira|mire|comparte|comparta|env[ií]a|env[ií]e|imagina|finge|haz|haga)\b"
    r"|\bpretend\b|\bfinge\b")
_QUOTED = re.compile(r"\b(?:message|text|email|e-mail|letter|note|mensaje|texto|correo|carta|nota)\b[^.!?]*?"
                     r"(?:\bsays?\b|\bsaid\b|\bdice\b|:)|[\"“«]")
_PHOTO = re.compile(r"\b(?:photo|photograph|picture|snapshot|foto|fotograf[ií]a|retrato)\b")
PHOTO_TOOLS = ("describe_photo", "describe_view")
MEMORY_TOOLS = ("remember", "remember_fact", "remember_moment", "remember_place")


def _text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return " ".join(str(part.get("text") or "") for part in content if isinstance(part, dict))
    return ""


def _after_photo(earlier: List[Dict[str, Any]]) -> bool:
    """The last tool Andy used, before the person's turn, looked at a photo, with at most one turn of theirs since."""
    turns = 0
    for i in range(len(earlier) - 1, -1, -1):
        message = earlier[i]
        if message.get("role") == "user":
            turns += 1
            if turns > 1:
                return False
        names = [((call.get("function") or {}).get("name") or "") for call in message.get("tool_calls") or []]
        if not names:
            continue
        if any(name in MEMORY_TOOLS for name in names):
            return False
        results = [_result(m.get("content")) for m in earlier[i + 1:] if m.get("role") == "tool"]
        if any("error" in r or not r.get("description") for r in results):
            return False                                # nothing was seen: there is no story to keep
        if "describe_photo" in names:
            return True
        if "describe_view" in names:                    # a photo held up, not the room: what was seen says so
            # Only the description: the tool's own note ("the picture was not kept") says "picture" every time
            # (2026-10-28 review: an ordinary look at the room got the photo note).
            return any(_PHOTO.search(str(r.get("description", "")).lower()) for r in results)
        return False
    return False


def _result(content: Any) -> Dict[str, Any]:
    try:
        data = json.loads(_text(content))
    except ValueError:
        return {}
    return data if isinstance(data, dict) else {}


def note_for(messages: List[Dict[str, Any]]) -> Optional[str]:
    """The note for the person's last turn, or None."""
    if not messages or messages[-1].get("role") != "user":
        return None
    said = " ".join(_text(messages[-1].get("content")).split())
    words = said.lower().replace("’", "'")
    if not said or said.startswith("[") or urgent.is_urgent(said):
        # Crisis or urgent words are never a memory to offer: "I am going to kill myself tomorrow" got the
        # moment note (2026-10-28 review), ahead of the urgent net, which only follows Andy's first reply.
        return None
    if _TIME.search(words):
        return TIME
    if _SEE.search(words) and not _PHOTO.search(words):
        return SEE
    if any(rule.search(words) for rule in (_ASKED, _QUESTION, _REFUSAL, _REQUEST, _QUOTED)):
        return None
    if len(words.split()) >= 5 and _after_photo(messages[:-1]):
        return PHOTO
    if _DAY.search(words) and _EVENT.search(words) and not _PAST.search(words.replace("pasado mañana", "")):
        return MOMENT
    return None


def with_note(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """The messages with the note added to the person's last turn (a copy of that message; the rest unchanged)."""
    note = note_for(messages)
    if note is None:
        return messages
    last = dict(messages[-1])
    content = last.get("content")
    last["content"] = (content + [{"type": "text", "text": note}] if isinstance(content, list)
                       else f"{content}\n\n{note}")
    return messages[:-1] + [last]

