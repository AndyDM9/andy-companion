"""One-use, action-bound confirmation for saving and sharing.

An explicit request can save one fact, moment or place. Sharing always requires a
proposal, its exact spoken readback, and a fresh yes. Other saves use that procedure
when offered. A confirmation expires in two minutes, belongs to one conversation,
and authorizes only the exact tool and arguments that were proposed. Words and
pending proposals live only in memory; none are logged or written down.
"""

from __future__ import annotations

import hashlib
import json
import re
import time
from functools import wraps
from typing import Any, Dict

SAVING = ("remember", "remember_fact", "remember_moment", "remember_place")
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
SHARING = ("share_with_family",)
# A plain request to pass something to family, said to Andy.
_FAMILY = r"(?:my|the|our|mi|la|nuestra)\s+(?:family|daughter|son|wife|husband|sister|brother|familia|hija|hijo|esposa|esposo|hermana|hermano)\b"
SHARE_ASKED = re.compile(
    LEAD + r"(?:share|send|tell|let|comparte|comp[aá]rtelo|env[ií]a|m[aá]ndalo|dile|d[ií]selo|d[ií]gale)\b"
    r"[^.!?]{0,220}\b" + _FAMILY +
    r"|\b(?:can you|could you|would you|will you|quiero que|puede|puedes)\s+"
    r"(?:share|send|tell|compartir|compartas|enviar|env[ií]es|decirle|digas)\b[^.!?]{0,220}\b" + _FAMILY)
NOT_SHARED = {"shared": False,
              "say": "Not shared: the person has not said yes. Say back what you would share and ask \"Shall I share that?\"; "
                     "share only after they say yes."}
NOT_SAVED = {"saved": False,
             "say": "Not saved: the person has not asked. Ask \"Shall I remember that?\" and save only after they say yes."}

_last: Dict[str, str] = {"words": ""}
CONFIRM_FOR_S = 120.0


def _normal(text: str) -> str:
    return " ".join(re.sub(r"[^\w\s]", " ", text.lower()).split())


def _yes_to(text: str, name: str) -> bool:
    if YES.fullmatch(text.lower()) or BARE_SI.fullmatch(text.lower()):
        return True
    verb = r"(?:share|send)" if name in SHARING else r"(?:keep|remember|save)"
    return bool(re.fullmatch(r"\W*(?:yes|yeah|sure)[,\s]+(?:please\s+)?" + verb +
                             r"\s+(?:it|that|this)(?:\s+please)?\W*", text.lower()))


class Confirmation:
    """One conversation's ephemeral, one-use permission. Nothing here is logged or saved."""

    def __init__(self, clock=time.monotonic):
        self.clock = clock
        self.words = ""
        self.pending = None
        self.confirmed = False
        self.used = False

    def hear(self, words: str) -> None:
        self.words = " ".join(str(words or "").split())[:400]
        self.used = False
        self.confirmed = bool(self.pending and self.pending["spoken"] and
                              self.clock() < self.pending["until"] and
                              _yes_to(self.words, self.pending["name"]))
        if not self.confirmed:
            self.pending = None

    def said(self, words: str) -> None:
        if self.pending and _normal(self.pending["question"]) == _normal(str(words)):
            self.pending["spoken"] = True

    def authorize(self, name: str, arguments: dict) -> dict | None:
        if self.used:
            return {"saved": False, "shared": False, "say": "That request was already handled. Do not repeat it."}
        canonical = json.dumps(arguments, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
        fingerprint = hashlib.sha256((name + canonical).encode()).hexdigest()
        text = self.words.lower().replace("’", "'")
        explicit = name in SAVING and asked(text) and bool(ASKED.search(text))
        matched = bool(self.confirmed and self.pending and self.pending["fingerprint"] == fingerprint and
                       self.clock() < self.pending["until"])
        if explicit or matched:
            self.used = True
            self.pending = None
            self.confirmed = False
            return None
        # The first call proposes the exact payload; it does not write anything. The
        # assistant must read this question before a fresh yes can release this call.
        fields = {"remember": ("fact",), "remember_fact": ("fact",), "remember_moment": ("what", "day"),
                  "remember_place": ("what", "said_where"), "share_with_family": ("note",)}
        pieces = [str(arguments.get(k, "")).strip() for k in fields[name]]
        content = "; ".join(p for p in pieces if p)
        if len(content) > 600:
            return {"error": "Keep the proposed content under 600 characters so the whole proposal can be read back."}
        if not content or REFUSED.search(KEEPING.sub(" ", text)):
            return dict(NOT_SHARED if name in SHARING else NOT_SAVED)
        if name in SHARING and not (SHARE_ASKED.search(text) or self.confirmed):
            return dict(NOT_SHARED)
        if not self.pending and (YES.fullmatch(text) or BARE_SI.fullmatch(text)):
            return dict(NOT_SHARED if name in SHARING else NOT_SAVED)
        spanish = bool(re.search(r"\b(s[ií]|familia|hija|hijo|recuerda|guarde|compartir)\b", text))
        verb = ("¿Quiere que comparta esto con su familia?" if name in SHARING else "¿Quiere que recuerde esto?") if spanish else (
            "Shall I share this with your family?" if name in SHARING else "Shall I remember this?")
        lead = ("Su nota dice" if spanish else "Your note says") if name in SHARING else (
            "Lo que recordaré" if spanish else "The memory would be")
        question = f"{lead}: “{content}”. {verb}"
        self.pending = {"name": name, "fingerprint": fingerprint, "question": question, "spoken": False,
                        "until": self.clock() + CONFIRM_FOR_S}
        self.confirmed = False
        return {"saved": False, "shared": False, "confirmation_needed": True,
                "say": question, "how": "Say 'say' exactly, then wait. Only after a fresh yes call this same tool with exactly the same arguments."}


_default = Confirmation()


def _session(obj):
    deps = getattr(obj, "deps", None)
    if deps is None:
        return _default
    if not hasattr(deps, "_andy_confirmation"):
        deps._andy_confirmation = Confirmation()
    return deps._andy_confirmation


def heard(words: str) -> None:
    _last["words"] = " ".join(str(words or "").split())[:400]
    _default.hear(words)


def asked(words: "str | None" = None) -> bool:
    text = " ".join((_last["words"] if words is None else str(words)).replace("’", "'").lower().split())
    if not text or REFUSED.search(KEEPING.sub(" ", text)):
        return False
    return bool(ASKED.search(text) or YES.search(text) or BARE_SI.search(text))


def asked_to_share(words: "str | None" = None) -> bool:
    """A clear yes, or a plain request to share, with no "no" in it."""
    text = " ".join((_last["words"] if words is None else str(words)).replace("’", "'").lower().split())
    if not text or REFUSED.search(text):
        return False
    return bool(YES.search(text) or BARE_SI.search(text) or SHARE_ASKED.search(text))


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
            _session(self).hear(text)
        elif role == "assistant" and final:
            _session(self).said(text)

    emit._andy_consent = True
    handler_class._emit_transcript = emit

    run = routine_class.__call__

    @wraps(run)
    async def gated(self, *args, **kwargs) -> Any:
        name = getattr(self, "tool_name", "")
        if name in SAVING + SHARING:
            try:
                arguments = json.loads(getattr(self, "args_json_str", "{}"))
            except (TypeError, ValueError):
                return {"error": "Invalid confirmation arguments."}
            if not isinstance(arguments, dict):
                return {"error": "Invalid confirmation arguments."}
            denied = _session(self).authorize(name, arguments)
            if denied is not None:
                return denied
        return await run(self, *args, **kwargs)

    routine_class.__call__ = gated
    return True
