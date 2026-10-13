"""A deterministic net under the model for urgent words.

When the person says something like "my chest hurts" or "I can't breathe", Andy must tell them to
call 911. When they say they don't want to live, or that everyone would be better off without
them, Andy must give the 988 Suicide and Crisis Lifeline (call or text 988, any time, in English
or Spanish; 911 if in danger now). The model does so most of the time; this makes it every time.
After Andy's reply to such a sentence, if the reply did not name 911 (or 988), Andy is asked to say
one exact sentence, calmly, in the person's language. The words are looked at and dropped;
nothing is kept or logged. This is a prompt to reach help, not a promise to watch over anyone.
988 is the United States' line; another country needs its own (CRISIS_LINE).
"""

from __future__ import annotations

import asyncio
import logging
import re
from functools import wraps
from typing import Optional

logger = logging.getLogger("andy.urgent")

URGENT = [r"\bchest\b(\W+\w+){0,4}?\W+(pain|pains|hurt|hurts|hurting|tight|tightness|ache|aches|aching|pressure|burning)\b",
          r"\b(pain|pains|pressure|tightness|ache)\b(\W+\w+){0,3}?\W+(my |the )?chest\b", r"heart attack",
          r"can'?t breathe", r"cannot breathe", r"(trouble|difficulty) breathing", r"short of breath",
          r"i('ve| have)? fallen", r"i fell( down)? and can'?t get up", r"can'?t get up", r"(having|had|think it's) a stroke",
          r"face is drooping", r"can'?t (move|feel) my (arm|leg|face)", r"bleeding (a lot|badly|heavily)",
          r"passing out", r"(i )?fainted", r"choking",
          # Spanish
          r"\bme duele (mucho )?el pecho\b", r"dolor (en el|de) pecho", r"\bpecho\b(\W+\w+){0,3}?\W+(duele|apretado|presi[oó]n)",
          r"no puedo respirar", r"me falta (el )?aire", r"\bme ca[ií]\b", r"me he ca[ií]do", r"no me puedo levantar",
          r"ataque al coraz[oó]n", r"derrame( cerebral)?", r"me estoy ahogando", r"me desmay[eéó]"]
# Someone saying they do not want to live. Checked before the medical words; negations ("I don't
# want to die") are left alone, and grief or "dying to see them" never match.
CRISIS = [r"\b(want|wanna|wish) to die\b", r"\bwish i (was|were) dead\b", r"\bwish i wasn'?t (here|alive)\b",
          r"\b(don'?t|do not) want to (live|be alive)\b", r"\b(don'?t|do not) want to be here (anymore|any more|any longer)\b",
          r"\b(kill|hurt) myself\b", r"\b(end|take) my (own )?life\b", r"\bend it all\b",
          r"\b(better off|be better) without me\b", r"\bno (reason|point) (in |to )?(living|going on|being alive)\b",
          r"\bwhat'?s the point (of|in) (living|going on|being alive)\b",
          r"\b(feel|feeling|felt|am|i'?m) suicidal\b", r"\bthinking (about|of) (suicide|killing myself|ending (it|my life))\b",
          # Spanish
          r"\b(me )?quiero morir(me)?\b", r"\bno quiero (seguir )?viviendo\b", r"\bno quiero vivir\b",
          r"\bya no quiero estar aqu[ií]\b", r"\bquitarme la vida\b", r"\bmatarme\b", r"\bsuicidarme\b",
          r"\bestar[ií]an mejor sin m[ií]\b"]
SPANISH = re.compile(r"\b(me|el|la|los|las|no|que|tengo|un|una|al|del|en|mi|de|por|estoy|creo|ataque|dolor|puedo|pecho|"
                     r"duele|ca[ií]|respirar|levantar|coraz[oó]n|ahogando|desmay\w*|cocina|ahora|mucho|quiero|vivir|"
                     r"morir\w*|matarme|vida|sin|todos|estar[ií]an|pienso|veces|ya)\b")
NEGATION = re.compile(r"\b(no|not|don'?t|doesn'?t|didn'?t|never|without)\b[\w\s']{0,20}$")
SAID_911 = re.compile(r"\b(911|nine[- ]one[- ]one|emergency services|ambulance|ambulancia|emergencias)\b", re.I)
SAY = "Please call 911 now, or ask someone nearby to call for you."
CRISIS_LINE = "988"
SAY_CRISIS = ("I'm really glad you told me. You can call or text 988 any time, day or night, to talk with someone "
              "right now, and if you might be in danger, please call 911.")
SAY_CRISIS_ES = ("Me alegra mucho que me lo haya dicho. Puede llamar o enviar un mensaje al 988 a cualquier hora, "
                 "también en español, para hablar con alguien ahora mismo, y si está en peligro, llame al 911.")
SAY_ES = "Por favor, llame al 911 ahora, o pida a alguien cercano que llame por usted."
FRAME = ("[URGENT WORDS heard from the person just now; this is Andy's own check, not something they said.] "
         f"Say exactly this, calmly, and nothing else: {SAY}")
FRAME_ES = ("[URGENT WORDS heard from the person just now, in Spanish; this is Andy's own check, not something they "
            f"said.] Say exactly this, calmly, and nothing else: {SAY_ES}")


FRAME_CRISIS = ("[CRISIS WORDS heard from the person just now; this is Andy's own check, not something they said.] "
                "Stay warm and keep talking with them. Say this, gently, and nothing else for now: " + SAY_CRISIS)
FRAME_CRISIS_ES = ("[CRISIS WORDS heard from the person just now, in Spanish; this is Andy's own check, not something "
                   "they said.] Stay warm and keep talking with them. Say this, gently, and nothing else for now: "
                   + SAY_CRISIS_ES)
SAID_988 = re.compile(r"\b988\b|nine[- ]eight[- ]eight|nueve[- ]ocho[- ]ocho", re.I)


def _matches(patterns, text: str) -> bool:
    value = " ".join(str(text).lower().replace("’", "'").split())
    for pattern in patterns:
        for m in re.finditer(pattern, value):
            if not NEGATION.search(value[:m.start()]):
                return True
    return False


def is_crisis(text: str) -> bool:
    return _matches(CRISIS, text)


def is_urgent(text: str) -> bool:
    """Medical urgent words or crisis words: either way the net checks Andy's reply."""
    return is_crisis(text) or _matches(URGENT, text)


def crisis_frame_for(text: str) -> str:
    """The crisis sentence in the person's language, for words found by the second look (guard.py)."""
    return FRAME_CRISIS_ES if len(SPANISH.findall(str(text).lower())) >= 2 else FRAME_CRISIS


def frame_for(text: str) -> str:
    spanish = len(SPANISH.findall(str(text).lower())) >= 2
    if is_crisis(text):
        return FRAME_CRISIS_ES if spanish else FRAME_CRISIS
    return FRAME_ES if spanish else FRAME


# Words a Spanish 911 sentence has and an English one does not, to hear which language Andy used.
SPANISH_REPLY = re.compile(r"\b(llame|llamar|llama|ahora|usted|alguien|cercano|ayuda|emergencias|ambulancia|"
                           r"m[eé]dico|por favor)\b", re.I)


def needs_followup(reply: str, frame: str = FRAME) -> bool:
    """True unless Andy's reply already named 911 (for crisis words, 988 and 911), in Spanish when the
    person spoke Spanish."""
    reply = str(reply)
    if frame in (FRAME_CRISIS, FRAME_CRISIS_ES):
        # Both: 988 to talk with someone now, and 911 if they might be in danger (found missing in the suite).
        if not (SAID_988.search(reply) and SAID_911.search(reply)):
            return True
    elif not SAID_911.search(reply):
        return True
    return frame in (FRAME_ES, FRAME_CRISIS_ES) and not SPANISH_REPLY.search(reply)


def install(handler_class=None) -> bool:
    if handler_class is None:
        from reachy_mini_conversation_app.conversation_handler import ConversationHandler

        handler_class = ConversationHandler
    previous = handler_class._emit_transcript
    if getattr(previous, "_andy_urgent", False):
        return False

    @wraps(previous)
    def emit(self, role: str, text: str, final: bool = True):
        previous(self, role, text, final)
        if not final:
            return
        if role == "user":
            self._andy_urgent_pending = frame_for(text) if is_urgent(text) else False
            return
        if role == "assistant" and getattr(self, "_andy_urgent_pending", False):
            frame, self._andy_urgent_pending = self._andy_urgent_pending, False
            if needs_followup(text, frame):
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    return
                loop.create_task(_follow_up(self, frame))

    emit._andy_urgent = True
    handler_class._emit_transcript = emit
    return True


async def _follow_up(handler, frame: str = FRAME) -> None:
    done = getattr(handler, "_response_done_event", None)
    try:
        if done is not None:
            await asyncio.wait_for(done.wait(), timeout=20)
        await handler.say(frame)
        logger.info("Urgent-words follow-up said")
    except Exception as e:  # never the words, only the type
        logger.warning("Urgent-words follow-up failed: %s", type(e).__name__)
