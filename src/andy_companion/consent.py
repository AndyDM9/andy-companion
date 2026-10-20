"""Andy saves something about the person only when they asked, checked in code.

The profile says to remember only what the person asks to remember, and to ask "Shall I remember
that?" before keeping a moment. On 2026-10-13 Pollen's own `remember` tool still saved two facts
from ordinary conversation. So saving tools are gated where every tool call passes: `remember` and
`remember_moment` run only if the person's last words asked for it ("remember that…", "don't
forget…") or were a clear yes ("yes", "please do", "sí"), and said no "no" ("No, please do not
remember that"). A yes must open the answer and be the answer: "Yes please" and "Sí, claro" count,
"OK so my sister is coming Friday" does not, and "si" without its accent counts only on its own
("Si mañana llueve" is "if it rains tomorrow"). A word "remember" alone is not a request: "Do you
remember my sister's name?" and "I can't remember where I put them" are questions and worries. When
in doubt nothing is saved and Andy asks. The last words are held in memory for this check only; they
are never written down or logged.
"""

from __future__ import annotations

import re
from functools import wraps
from typing import Any, Dict

SAVING = ("remember", "remember_moment", "remember_place")
# An explicit request to keep something, said to Andy.
LEAD = r"(^|[.!?,;:]\s*)((please|andy|and|also|oh|ok|okay|so|now|yes|yeah|por favor|y|tambi[eé]n|s[ií])[,\s]+)*"
ASKED = re.compile(
    LEAD + r"(remember|recuerda|recu[eé]rde(lo)?|recu[eé]rdalo|apunta|ap[uú]ntalo|apunte|ap[uú]ntelo|anota|an[oó]talo|"
    r"anote|an[oó]telo|guarda|gu[aá]rdalo|guarde|gu[aá]rdelo|make a note|note (that|this|it) down|write (that|this|it) down|"
    r"keep (that|this|it) in mind|save (that|this|it))\b(?!\s+(when|how|what|who|where|why|if|whether|those|back|cuando|cómo|"
    r"qué|quién|dónde))"
    r"|\b(please|can you|could you|would you|will you|i want you to|i'?d like you to|i need you to|make sure (you|to)|"
    r"puedes|puede|podr[ií]as|podr[ií]a|quiero que) (remember|recordar|recuerdes|recuerde|apuntar|apuntes|apunte|anotar|"
    r"anotes|anote|guardar|guardes|guarde)\b(?!\s+(when|how|what|who|where|why|if|whether|cuando|cómo|qué|dónde))"
    r"|\b(remember (that|this|it) for me|don'?t forget|do not forget|no (te )?olvides|no se olvide|no lo olvides|"
    r"no lo olvide|keep (that|this) in mind|make a note|note that)\b")
# Asking Andy not to forget is a request; these phrases are taken out before looking for a "no".
KEEPING = re.compile(r"\b(don'?t forget|do not forget|never forget|no (te |lo )?olvides|no (se |lo )?olvide)\b")
REFUSED = re.compile(r"\b(no|nope|nah|not|don'?t|do not|never|rather not|better not|no thanks|nunca|tampoco|"
                     r"mejor no|forget (it|that|this|about it))\b|\bolv[ií]d(a|e)(lo|la)?\b")
# A clear yes opens the answer and is the answer: followed by nothing, or only by a short closer ("yes,
# please", "sure, go ahead", "sí, gracias"). Anything more is a new sentence, not consent: Parakeet
# writes commas, and "Okay, so my sister is coming Friday" must not save (2026-10-14 review).
# "si" without its accent counts only on its own ("si mañana llueve" is "if").
CLOSER = (r"please|please do|do|go ahead|you can|yes|thanks|thank you|that'?s fine|that'?s right|sure|of course|"
          r"andy|gracias|por favor|claro|vale|s[ií]")
YES = re.compile(r"^\W*(yes|yeah|yep|yup|sure|of course|please do|please|ok|okay|go ahead|that'?s right|correct|"
                 r"definitely|absolutely|s[ií] por favor|s[ií] claro|sí|claro|vale|por favor|de acuerdo|perfecto|"
                 r"bueno|dale)\b(\W*(" + CLOSER + r"))*\W*$")
BARE_SI = re.compile(r"^\W*si\W*($|[,.!]\s*(claro|por favor|gracias|vale)?\W*$)")
NOT_SAVED = {"saved": False,
             "say": "Not saved: the person has not asked. Ask \"Shall I remember that?\" and save only after they say yes."}

_last: Dict[str, str] = {"words": ""}


def heard(words: str) -> None:
    _last["words"] = " ".join(str(words or "").split())[:400]


def asked(words: str = None) -> bool:
    text = " ".join((_last["words"] if words is None else str(words)).replace("’", "'").lower().split())
    if not text or REFUSED.search(KEEPING.sub(" ", text)):
        return False
    return bool(ASKED.search(text) or YES.search(text) or BARE_SI.search(text))


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
