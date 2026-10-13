"""A deterministic net under the model for urgent words.

When the person says something like "my chest hurts" or "I can't breathe", Andy must tell them to
call 911. The model does so most of the time; this makes it every time. After Andy's reply to such
a sentence, if the reply did not mention 911, Andy is asked to say it once, calmly. The words are
looked at and dropped; nothing is kept or logged. This is a prompt to call for help, not a promise
to watch over anyone.
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
SPANISH = re.compile(r"\b(me|el|la|los|las|no|que|tengo|un|una|al|del|en|mi|de|por|estoy|creo|ataque|dolor|puedo|pecho|"
                     r"duele|ca[ií]|respirar|levantar|coraz[oó]n|ahogando|desmay\w*|cocina|ahora|mucho)\b")
NEGATION = re.compile(r"\b(no|not|don'?t|doesn'?t|didn'?t|never|without)\b[\w\s']{0,20}$")
SAID_911 = re.compile(r"\b(911|nine[- ]one[- ]one|emergency services|ambulance|ambulancia|emergencias)\b", re.I)
SAY = "Please call 911 now, or ask someone nearby to call for you."
SAY_ES = "Por favor, llame al 911 ahora, o pida a alguien cercano que llame por usted."
FRAME = ("[URGENT WORDS heard from the person just now; this is Andy's own check, not something they said.] "
         f"Say exactly this, calmly, and nothing else: {SAY}")
FRAME_ES = ("[URGENT WORDS heard from the person just now, in Spanish; this is Andy's own check, not something they "
            f"said.] Say exactly this, calmly, and nothing else: {SAY_ES}")


def frame_for(text: str) -> str:
    return FRAME_ES if len(SPANISH.findall(str(text).lower())) >= 2 else FRAME


def is_urgent(text: str) -> bool:
    value = " ".join(str(text).lower().replace("’", "'").split())
    for pattern in URGENT:
        for m in re.finditer(pattern, value):
            if not NEGATION.search(value[:m.start()]):
                return True
    return False


# Words a Spanish 911 sentence has and an English one does not, to hear which language Andy used.
SPANISH_REPLY = re.compile(r"\b(llame|llamar|llama|ahora|usted|alguien|cercano|ayuda|emergencias|ambulancia|"
                           r"m[eé]dico|por favor)\b", re.I)


def needs_followup(reply: str, frame: str = FRAME) -> bool:
    """True unless Andy's reply already named 911, in Spanish when the person spoke Spanish."""
    reply = str(reply)
    if not SAID_911.search(reply):
        return True
    return frame == FRAME_ES and not SPANISH_REPLY.search(reply)


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
