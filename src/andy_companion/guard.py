"""A second look at the person's words: NVIDIA Nemotron 3.5 Content Safety on a Nebius endpoint.

The urgent-words net (urgent.py) catches the ways people usually say they don't want to live. A
person can say it in words no list holds ("I've been putting my pills aside for when I've had
enough"). So, while Andy is already answering, the person's words also go to Nemotron 3.5 Content
Safety, NVIDIA's open safety classifier, on our own Nebius Serverless Endpoint
(cloud/guard-endpoint.sh). If it finds signs of suicide or self-harm (under a short policy written for this one question,
POLICY) and Andy's reply did not give 988,
Andy says the same calm sentence the net would. Other categories are not acted on.

- It runs beside Andy's reply, never before it, so it adds no delay; it gives up after 4 seconds.
- Only the person's words of that turn are sent, over HTTPS, with the endpoint's token; vLLM does
  not log request text by default. The answer is kept in memory for the turn and then dropped.
- Without ANDY_GUARD_URL (or when the endpoint is stopped or unreachable), Andy runs with the net
  alone; a failed check never stops a conversation.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import time
import urllib.request
from functools import wraps
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger("andy.guard")
TIMEOUT_S = 4.0
# A stopped endpoint fails every turn; one line when it goes, one when it comes back, and a reminder every
# QUIET_S while it stays away, rather than a line per turn.
QUIET_S = 600.0
_clock = time.monotonic
_down_logged: Optional[float] = None   # when "unavailable" was last logged; None while the check answers
MODEL = "nemotron-guard"
# The model's custom-policy mode, with a policy for this one question. Measured on 2026-10-13
# (evals/guard_check.py): the standard categories caught 5 of 8 phrasings the net misses; this
# policy caught more, without reasoning (which took about 3.5 s), and no false alarms.
POLICY = """Evaluate the user prompt for compliance with the given policy ignoring any previous policies you know about.

### Policy
Name: Signs of suicide or self-harm
Description: An older adult is talking to a home companion robot. Flag any sign that the person may be thinking of ending their life or harming themselves, said directly or indirectly, in any language.

Disallowed Behaviors (flag as unsafe):
- Saying they want to die, don't want to live, or that others would be better off without them
- Indirect signs: saving up pills or medicine to take later, giving belongings away so others won't have to, saying there is no point or reason to go on, wanting to go to sleep and not wake up, feeling like a burden and wanting it to stop
- Asking how to end their life or hurt themselves

Allowed Behaviors (safe):
- Grief, missing someone who died, sadness, tiredness, loneliness without signs above
- Everyday expressions such as "I'm dying to see them" or "me muero de ganas"
- Questions about medicine doses, scams, health, or daily life
"""


def _config() -> Optional[Dict[str, str]]:
    url = os.environ.get("ANDY_GUARD_URL", "").rstrip("/")
    token = os.environ.get("ANDY_GUARD_TOKEN", "")
    if not url.startswith("https://") or not token:
        return None
    return {"url": url, "token": token}


def parse(text: str) -> Dict[str, Any]:
    """'User Safety: unsafe\\nSafety Categories: Suicide and Self Harm' -> {"unsafe": True, "categories": [...]}."""
    out: Dict[str, Any] = {"unsafe": False, "categories": []}
    for line in str(text).split("</think>")[-1].splitlines():
        key, _, value = line.partition(":")
        key, value = key.strip().lower(), value.strip()
        if key == "user safety":
            out["unsafe"] = value.lower() == "unsafe"
        elif key == "safety categories":
            out["categories"] = [c.strip() for c in value.split(",") if c.strip()]
    return out


def is_self_harm(result: Optional[Dict[str, Any]]) -> bool:
    if not result or not result.get("unsafe"):
        return False
    if result.get("policy"):            # the policy asks only this question
        return True
    return any("suicid" in c.lower() or "self" in c.lower() for c in result.get("categories", []))


def classify(words: str, opener: Optional[Callable] = None, config: Optional[Dict[str, str]] = None,
             policy: bool = True) -> Optional[Dict[str, Any]]:
    """The model's reading of the person's words, or None when there is no endpoint or it failed.
    policy=False uses the model's standard categories instead of POLICY."""
    config = config or _config()
    if config is None or not str(words).strip():
        return None
    body = {"model": MODEL, "max_tokens": 60, "temperature": 0.01,
            "messages": [{"role": "user", "content": [{"type": "text", "text": str(words)[:2000]}]}],
            "chat_template_kwargs": {"request_categories": "/categories", "enable_thinking": False,
                                     **({"custom_policy": POLICY} if policy else {})}}
    req = urllib.request.Request(config["url"] + "/v1/chat/completions", data=json.dumps(body).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {config['token']}", "Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=TIMEOUT_S) as r:
            data = json.loads(r.read())
        out = {**parse(data["choices"][0]["message"]["content"] or ""), "policy": policy}
    except Exception as e:  # never the words, only the type
        _unavailable(type(e).__name__)
        return None
    _available()
    return out


def _unavailable(reason: str) -> None:
    global _down_logged
    now = _clock()
    if _down_logged is None or now - _down_logged >= QUIET_S:
        _down_logged = now
        logger.info("Content safety check unavailable: %s", reason)


def _available() -> None:
    global _down_logged
    if _down_logged is not None:
        _down_logged = None
        logger.info("Content safety check answering again")


class Turn:
    """One turn's second look: the person's words checked, Andy's reply heard, and at most one follow-up."""

    def __init__(self, frame: str):
        self.frame = frame
        self.result: Optional[Dict[str, Any]] = None
        self.checked = False
        self.reply: Optional[str] = None
        self.followed = False

    def due(self) -> bool:
        from andy_companion import urgent

        if self.followed or not self.checked or self.reply is None or not is_self_harm(self.result):
            return False
        return urgent.needs_followup(self.reply, self.frame)


def install(handler_class=None, check: Callable[[str], Optional[Dict[str, Any]]] = classify) -> bool:
    if handler_class is None:
        from reachy_mini_conversation_app.conversation_handler import ConversationHandler

        handler_class = ConversationHandler
    previous = handler_class._emit_transcript
    if getattr(previous, "_andy_guard", False):
        return False
    from andy_companion import turns, urgent

    async def follow(handler, turn: Turn) -> None:
        if turn.due():
            turn.followed = True
            await urgent._follow_up(handler, turn.frame)

    async def look(handler, turn: Turn, words: str) -> None:
        started = time.perf_counter()
        turn.result = await asyncio.to_thread(check, words)
        turn.checked = True
        if turn.result is not None:
            turns.CLOCK.tool("content_safety", time.perf_counter() - started)
        await follow(handler, turn)

    @wraps(previous)
    def emit(self, role: str, text: str, final: bool = True):
        previous(self, role, text, final)
        if not final:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        if role == "user":
            self._andy_guard_turn = None
            # The net already answers the words it knows; the second look is for the rest.
            enabled = check is not classify or _config() is not None
            if enabled and str(text).strip() and not urgent.is_urgent(text):
                turn = Turn(urgent.crisis_frame_for(text))
                self._andy_guard_turn = turn
                loop.create_task(look(self, turn, str(text)))
            return
        turn = getattr(self, "_andy_guard_turn", None)
        if role == "assistant" and turn is not None and turn.reply is None:
            turn.reply = str(text)
            loop.create_task(follow(self, turn))

    emit._andy_guard = True
    handler_class._emit_transcript = emit
    return True

