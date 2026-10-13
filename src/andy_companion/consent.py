"""Andy saves something about the person only when they asked, checked in code.

The profile says to remember only what the person asks to remember, and to ask "Shall I remember
that?" before keeping a moment. On 2026-10-13 Pollen's own `remember` tool still saved two facts
from ordinary conversation. So saving tools are gated where every tool call passes: `remember` and
`remember_moment` run only if the person's last words asked for it ("remember that…", "don't
forget…") or said yes ("yes", "please do", "sí"). The last words are held in memory for this check
only; they are never written down or logged.
"""

from __future__ import annotations

import re
from functools import wraps
from typing import Any, Dict

SAVING = ("remember", "remember_moment")
ASKED = re.compile(
    r"\b(remember|don'?t forget|do not forget|keep (that|this) in mind|make a note|note that|"
    r"yes|yeah|yep|yup|sure|of course|please do|please|ok|okay|go ahead|that'?s right|correct|"
    r"recuerda|recu[eé]rdalo|recu[eé]rdelo|no (te )?olvides|no se olvide|apunta|an[oó]talo|"
    r"s[ií]|claro|vale|por favor|de acuerdo|perfecto)\b", re.I)
NOT_SAVED = {"saved": False,
             "say": "Not saved: the person has not asked. Ask \"Shall I remember that?\" and save only after they say yes."}

_last: Dict[str, str] = {"words": ""}


def heard(words: str) -> None:
    _last["words"] = " ".join(str(words or "").split())[:400]


def asked(words: str = None) -> bool:
    text = _last["words"] if words is None else str(words)
    return bool(ASKED.search(text.replace("’", "'")))


def install(handler_class=None, routine_class=None) -> bool:
    if handler_class is None:
        from reachy_mini_conversation_app.conversation_handler import ConversationHandler

        handler_class = ConversationHandler
    if routine_class is None:
        from reachy_mini_conversation_app.tools.background_tool_manager import ToolCallRoutine

        routine_class = ToolCallRoutine
    previous = handler_class._emit_transcript
    if getattr(previous, "_andy_consent", False):
        return False

    @wraps(previous)
    def emit(self, role: str, text: str, final: bool = True):
        previous(self, role, text, final)
        if role == "user" and final:
            heard(text)

    emit._andy_consent = True
    handler_class._emit_transcript = emit

    run = routine_class.__call__

    @wraps(run)
    async def gated(self, *args, **kwargs) -> Any:
        if getattr(self, "tool_name", "") in SAVING and not asked():
            return dict(NOT_SAVED)
        return await run(self, *args, **kwargs)

    routine_class.__call__ = gated
    return True
