"""Exact spoken controls that work even if the model does not call the tool.

"Goodnight" and "be quiet for twenty minutes" are too important to leave to the model's choice.
Only a whole, completed utterance counts: not a question, a negation or a quoted example. The
transcript is looked at and dropped; it is never kept or logged.
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
         "buenas noches", "buenas noches andy", "a dormir", "vete a dormir", "a dormir andy"}
QUIET = {"be quiet", "stay quiet", "quiet please", "quiet", "silencio", "silencio por favor", "quédate callado",
         "quédate en silencio"}


def parse(text: str) -> Optional[Tuple[str, dict]]:
    if not isinstance(text, str) or len(text) > 160 or any(c in text for c in '?"“”'):
        return None
    value = " ".join(text.lower().replace("’", "'").split()).strip(" .!,")
    value = re.sub(r"^(?:hey )?andy[, ]+", "", value)
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

    @wraps(previous)
    def emit(self, role: str, text: str, final: bool = True):
        previous(self, role, text, final)
        command = parse(text) if role == "user" and final else None
        if command is None:
            return
        task = getattr(self, "_andy_control_task", None)
        if task is not None and not task.done():
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        self._andy_control_task = loop.create_task(execute(self, *command))

    emit._andy_voice_controls = True
    handler_class._emit_transcript = emit
    return True
