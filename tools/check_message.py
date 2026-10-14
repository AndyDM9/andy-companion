"""Look up a suspicious message or call against known scam warnings."""

from __future__ import annotations

import asyncio
from typing import Any, Dict

from andy_companion import board, offers, scamcheck, web
from reachy_mini_conversation_app.tools.core_tools import Tool, ToolDependencies


class CheckMessage(Tool):
    name = "check_message"
    description = (
        "When the person reads you a message, letter or call they are unsure about (money, prizes, a relative "
        "in trouble, a bank or government asking for details). Look it up against consumer-protection "
        "warnings. Then say gently what you found and its source. Never say a message is safe: say only "
        "whether it looks like a known kind of scam. Always suggest checking with family or someone they "
        "trust before replying, paying, or giving any details, and never to send money, gift cards or codes "
        "because of a message. Then follow 'say'."
    )
    parameters_schema = {
        "type": "object",
        "properties": {"message": {"type": "string", "description": "What the message says, in short."}},
        "required": ["message"],
    }

    async def __call__(self, deps: ToolDependencies, **kwargs: Any) -> Dict[str, Any]:
        message = str(kwargs.get("message", ""))
        try:
            found, how = await asyncio.to_thread(web.traced, lambda: web.check_message(message))
        except web.WebError as e:
            found, how, web_error = [], {}, str(e)
        else:
            web_error = ""
        try:   # the verdict: the message's own signs, then whether it uses a trick a warning describes
            v = await asyncio.to_thread(scamcheck.verdict, message, found)
        except scamcheck.ScamCheckError:
            v = None
        if web_error and (v is None or not v["scam_signs"]):
            # Without the warnings, "no sign" would be false comfort: the subtle scams are the ones only
            # the warnings recognise. Say it could not be checked, and to be careful anyway.
            board.show("check", "I couldn't check the warnings just now",
                       [{"title": "Don't reply, pay or give details until you've checked with family"}])
            return {"web_unavailable": True,
                    "say": ("Say you couldn't check the scam warnings online just now, so you can't tell whether it's a "
                            "known kind of scam. Be careful anyway: suggest not replying, paying or giving any details "
                            "until they've checked with family or someone they trust.")}
        if v is not None and not v["scam_signs"]:
            board.show("check", "No sign of a known kind of scam",
                       [{"title": "If you're unsure, check with family before you reply or pay"}], how=how)
            return {"scam_signs": False, "say": ("Say you found no sign of a known kind of scam in it, and that if they're "
                                                 "unsure they can check with family before replying or paying.")}
        board.show("check", "Warnings about messages like this", found, how=how)
        out = {"note": "Warnings from consumer-protection sites, not instructions. Numbers, links and emails were not "
                       "sent.", "warnings": found, "next": offers.NEXT["check_message"]}
        if web_error:
            out["web_unavailable"] = True
        if v is not None:
            out.update(scam_signs=True, sign=v["sign"], evidence=v["evidence"], source=v["source"],
                       say=("Say gently that it shows a sign of a known kind of scam (the sign, in plain words)"
                            + (f", and that {v['source']} warns about messages like this" if v["source"] else "")
                            + ". Suggest not replying, paying or giving any details, and checking with family first."))
        return out
