"""Exact spoken controls that work even if the model does not call the tool.

"Goodnight" and "be quiet for twenty minutes" are too important to leave to the model's choice.
Only a whole, completed utterance counts: not a question, a negation or a quoted example. The
transcript is looked at and dropped; it is never kept or logged.

Any other way of asking for sleep is the model's to understand; if it then says goodnight without
calling go_to_sleep, Andy goes to sleep once the words are out.
"""

from __future__ import annotations

import asyncio
import logging
import re
from functools import wraps
from typing import Optional, Tuple

logger = logging.getLogger("andy.voice_controls")

NUMBERS = {"one": 1, "two": 2, "three": 3, "five": 5, "ten": 10, "fifteen": 15, "twenty": 20,
           "thirty": 30, "forty five": 45, "sixty": 60, "an": 1, "a": 1, "half an": 0.5,
           # Spanish, as Parakeet writes it ("media hora" is half an hour)
           "un": 1, "una": 1, "dos": 2, "tres": 3, "cinco": 5, "diez": 10, "quince": 15, "veinte": 20,
           "treinta": 30, "cuarenta y cinco": 45, "sesenta": 60, "media": 0.5}
SLEEP = {"goodnight", "good night", "go to sleep", "go to sleep now", "goodnight andy", "good night andy",
         "time to sleep", "time to go to sleep", "time for bed", "go to bed", "go to bed now",
         "buenas noches", "buenas noches andy", "a dormir", "vete a dormir", "a dormir andy", "vete a la cama"}
QUIET = {"be quiet", "stay quiet", "quiet please", "quiet", "silencio", "silencio por favor", "quédate callado",
         "quédate en silencio"}
# Andy's own short goodnight, said after the person asked for sleep. On 2026-10-29 the model answered a request to
# sleep with "Good night! See you tomorrow." and no go_to_sleep, and Andy stayed awake.
GOODNIGHT = re.compile(r"\b(?:good ?night|sleep well|sweet dreams|see you tomorrow|buenas noches|que descanses|"
                       r"dulces sueños|hasta mañana)\b", re.I)
AFTER_GOODNIGHT_S = 2.0      # the model's own call, if it made one, has put Andy to sleep by then


def parse(text: str) -> Optional[Tuple[str, dict]]:
    if not isinstance(text, str) or len(text) > 160 or any(c in text for c in '?"“”'):
        return None
    value = " ".join(text.lower().replace("’", "'").split()).strip(" .!,")
    for _ in range(2):                                               # "Okay Andy, …" / "Andy, okay, …"
        value = re.sub(r"^(?:hey )?andy[, ]+", "", value)
        value = re.sub(r"^(?:ok(?:ay)?|alright|all right|vale)[, ]+", "", value)
    value = re.sub(r"^(?:please|por favor) ", "", value)
    value = re.sub(r",? (?:please|por favor)$", "", value).strip(" .!,¡")
    value = re.sub(r",? andy$", "", value).strip(" .!,¡")       # "Goodnight, Andy" / "Buenas noches, Andy"
    if value in SLEEP:
        return "go_to_sleep", {}
    if value in QUIET:
        return "quiet_for", {"minutes": 60}
    match = (re.fullmatch(r"(?:be quiet|stay quiet|quiet) for (\d+|half an|forty five|[a-z]+) (minutes?|hours?)", value)
             or re.fullmatch(r"(?:silencio|quédate callado|quédate en silencio) (?:por|durante) "
                             r"(\d+|cuarenta y cinco|[a-z]+) (minutos?|horas?)", value)
             or re.fullmatch(r"(?:silencio|quédate callado|quédate en silencio) (?:por|durante) (media) (hora)", value))
    if not match:
        return None
    number, unit = match.groups()
    amount = float(number) if number.isdigit() else NUMBERS.get(number)
    if amount is None:
        return None
    minutes = int(amount * (60 if unit.startswith(("hour", "hora")) else 1))
    return ("quiet_for", {"minutes": minutes}) if 1 <= minutes <= 24 * 60 else None


def says_goodnight(reply: str) -> bool:
    """Andy's reply is a short goodnight, not a question."""
    return (isinstance(reply, str) and len(reply) <= 120 and not any(c in reply for c in "?¿")
            and bool(GOODNIGHT.search(reply)))


async def sleep_after_goodnight(handler) -> None:
    """Asked for sleep, the model said goodnight but did not call go_to_sleep: once the words are out, sleep."""
    from andy_companion import state

    await asyncio.sleep(AFTER_GOODNIGHT_S)
    if state.current()["mode"] != "awake":      # the model's call already did it (or Andy is quiet)
        return
    logger.info("Goodnight said without go_to_sleep; going to sleep")
    await execute(handler, "go_to_sleep", {})


async def execute(handler, name: str, arguments: dict) -> None:
    from reachy_mini_conversation_app.tools import core_tools

    try:
        tool = core_tools.get_tools().get(name)
        if tool is None:
            raise RuntimeError("control tool unavailable")
        logger.info("Spoken control: %s", name)
        await tool(handler.deps, **arguments)
    except asyncio.CancelledError:
        raise
    except Exception as error:   # errors can quote speech: keep only the type and the action
        logger.error("Spoken control %s failed: %s", name, type(error).__name__)


def install(handler_class=None) -> bool:
    if handler_class is None:
        from reachy_mini_conversation_app.conversation_handler import ConversationHandler

        handler_class = ConversationHandler
    previous = handler_class._emit_transcript
    if getattr(previous, "_andy_voice_controls", False):
        return False

    from andy_companion.consent import sleep_asked

    @wraps(previous)
    def emit(self, role: str, text: str, final: bool = True):
        previous(self, role, text, final)
        if not final:
            return
        if role == "user":
            command = parse(text)
            self._andy_sleep_asked = command is None and sleep_asked(text)     # a yes or no, never the words
            if command is None:
                return
            work = execute(self, *command)
        elif role == "assistant" and getattr(self, "_andy_sleep_asked", False) and says_goodnight(text):
            self._andy_sleep_asked = False
            work = sleep_after_goodnight(self)
        else:
            return
        task = getattr(self, "_andy_control_task", None)
        if task is not None and not task.done():
            work.close()
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            work.close()
            return
        self._andy_control_task = loop.create_task(work)

    emit._andy_voice_controls = True
    handler_class._emit_transcript = emit
    return True
