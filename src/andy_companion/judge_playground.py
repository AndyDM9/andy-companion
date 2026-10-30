"""Fixed synthetic challenges with real inference, isolated from every household tool.

Only the confirmation gate is reused. No camera, motor, store, web search or SDK
is imported. Inputs are scenario IDs and yes/no buttons, never free text.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import secrets
import threading
import time
import urllib.request

from andy_companion.consent import Confirmation
from andy_companion.model_reply import final_text
from andy_companion.tool_text import unspoken

MODEL = "nvidia/Nemotron-3_5-Lightning"
ENDPOINT = "https://api.tokenfactory.nebius.com/v1/chat/completions"
NOTE = "I enjoyed the garden today."
CLOSING = {"role": "system", "content": "Now answer the person in plain words. Do not call or write any tool."}
CHALLENGES = {
    "letter": {"title": "Explain an invented bill", "tool": "read_letter",
               "prompt": "Can you read this letter for me? I'm holding it up.",
               "sample": "Made-up sender: Sunshine Coast Electric. Amount due: $86.40. Due: January 8, 2027. "
                         "Pay by your usual method. This company and bill are invented."},
    "choice": {"title": "You decide what family sees", "tool": "share_with_family",
               "prompt": "Share with my family that I enjoyed the garden today.",
               "sample": "An invented note: I enjoyed the garden today. Choose Yes or No after the exact note is shown."},
    "absent": {"title": "When the glasses are absent", "tool": "find_object",
               "prompt": "I can't find my reading glasses. Can you look for them?",
               "sample": "Simulated room: four views, no reading glasses present. No camera or motors are connected."},
}
BOUNDARY = """
## GUIDED SOFTWARE CHALLENGE
This is an isolated text demonstration with predefined invented inputs, not a live robot.
Only the current challenge's tool is available. Camera readings, object searches and
the family page are simulated; follow the tool result and do not invent a sighting.
The interface displays the exact confirmation from the code before its Yes/No buttons.
No personal data or real family is involved. Keep your answer to two short sentences.
Each example ends after one tool result. Do not promise another search or other work.
Describe these as sample results; never suggest this browser has a physical camera or robot.
"""
TTL = 300


class Unavailable(Exception):
    def __init__(self, code: str, status: int = 503):
        super().__init__(code)
        self.code, self.status = code, status


def _normal(text):
    return " ".join(re.sub(r"[^\w\s]", " ", str(text).lower()).split())


class Playground:
    def __init__(self, *, profile_path: Path, tools_path: Path, key: str = "", chat=None,
                 clock=time.monotonic, wall_clock=time.time, daily_limit: int = 120):
        self.key, self.chat = key, chat
        self.clock, self.wall_clock = clock, wall_clock
        self.daily_limit = daily_limit
        profile, tools = profile_path.read_bytes(), tools_path.read_bytes()
        text = profile.decode()
        self.prompt = (text.split("+++", 2)[2] if text.startswith("+++") else text).strip() + BOUNDARY
        names = {case["tool"] for case in CHALLENGES.values()}
        self.tools = {t["name"]: {"type": "function", "function": {k: t[k] for k in
                      ("name", "description", "parameters")}} for t in json.loads(tools) if t["name"] in names}
        if set(self.tools) != names:
            raise ValueError("challenge tool definitions missing")
        self.hashes = {"profile_sha256": hashlib.sha256(profile).hexdigest(),
                       "tools_sha256": hashlib.sha256(tools).hexdigest(),
                       "prompt_sha256": hashlib.sha256(self.prompt.encode()).hexdigest()}
        self.lock = threading.Lock()
        self.sessions = {}
        self.inflight = self.calls = 0
        self.day = int(self.wall_clock() // 86400)

    def metadata(self):
        return {"enabled": bool(self.key or self.chat), "model": MODEL, **self.hashes,
                "scope": "Real model replies; simulated tools; no connected robot or household.",
                "challenges": [{"id": k, **{field: c[field] for field in ("title", "prompt", "sample")}}
                               for k, c in CHALLENGES.items()]}

    def expire(self):
        """Also called by the HTTP server while idle, so expiry does not need another visitor."""
        with self.lock:
            now = self.clock()
            self.sessions = {k: s for k, s in self.sessions.items() if s["busy"] or now - s["at"] < TTL}

    def _message(self, messages, tool=None):
        with self.lock:
            day = int(self.wall_clock() // 86400)
            if day != self.day:
                self.day, self.calls = day, 0
            if self.calls >= self.daily_limit:
                raise Unavailable("public_allowance_reached", 429)
            self.calls += 1  # Failed calls count too; no automatic retry or unbounded tool loop.
        body = {"model": MODEL, "messages": messages, "max_tokens": 240, "temperature": 0.2,
                "chat_template_kwargs": {"enable_thinking": False}}
        if tool:
            body["tools"] = [self.tools[tool]]
            body["parallel_tool_calls"] = False
        try:
            if self.chat:
                payload = self.chat(body)
            else:
                request = urllib.request.Request(ENDPOINT, data=json.dumps(body).encode(), method="POST",
                                                headers={"Authorization": f"Bearer {self.key}",
                                                         "Content-Type": "application/json"})
                with urllib.request.urlopen(request, timeout=20) as response:
                    raw = response.read(262145)
                if len(raw) > 262144:
                    raise ValueError("response too large")
                payload = json.loads(raw)
        except Unavailable:
            raise
        except Exception:
            raise Unavailable("model_unavailable", 502) from None
        return self._completed_message(payload, tool)

    @staticmethod
    def _completed_message(payload, tool):
        """This hosted endpoint must explicitly finish before an answer or sample action is used."""
        try:
            choices = payload["choices"]
            if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
                raise ValueError()
            choice = choices[0]
            message = choice["message"]
            if (not isinstance(message, dict) or message.get("refusal") or message.get("function_call")
                    or message.get("role", "assistant") != "assistant"):
                raise ValueError()
            calls = message.get("tool_calls")
            if calls is None or calls == []:
                if choice.get("finish_reason") != "stop":
                    raise ValueError()
                return {"content": final_text(payload)[:1800]}
            if (not tool or choice.get("finish_reason") != "tool_calls" or not isinstance(calls, list)
                    or len(calls) != 1 or not isinstance(calls[0], dict)
                    or calls[0].get("type") != "function"
                    or (message.get("content") is not None and not isinstance(message["content"], str))):
                raise ValueError()
            # Tool-turn prose is not displayed and need not re-enter the next model request.
            # Keep only the call; discard any inline/separate reasoning and provider metadata.
            return {"content": "", "tool_calls": calls}
        except (KeyError, TypeError, ValueError):
            raise Unavailable("model_response_invalid", 502) from None

    def run(self, body: dict):
        if not isinstance(body, dict) or set(body) - {"challenge", "session", "choice"}:
            raise Unavailable("fixed_choices_only", 400)
        challenge, token, choice = body.get("challenge"), body.get("session"), body.get("choice")
        if not isinstance(challenge, str) or challenge not in CHALLENGES:
            raise Unavailable("unknown_challenge", 400)
        if token is not None and (not isinstance(token, str) or not re.fullmatch(r"[A-Za-z0-9_-]{32}", token)):
            raise Unavailable("invalid_session", 400)
        if choice not in (None, "yes", "no"):
            raise Unavailable("fixed_choices_only", 400)
        if not self.key and self.chat is None:
            raise Unavailable("not_configured")
        with self.lock:
            now = self.clock()
            self.sessions = {k: s for k, s in self.sessions.items() if s["busy"] or now - s["at"] < TTL}
            if self.inflight >= 2:
                raise Unavailable("busy", 429)
            if token:
                session = self.sessions.get(token)
                if not session or session["challenge"] != challenge:
                    raise Unavailable("session_expired", 410)
                if session["busy"] or not session["awaiting"] or choice is None:
                    raise Unavailable("step_already_handled", 409)
            else:
                if choice is not None:
                    raise Unavailable("start_before_choosing", 400)
                if len(self.sessions) >= 64:
                    raise Unavailable("busy", 429)
                token = secrets.token_urlsafe(24)
                session = {"challenge": challenge, "at": now, "busy": False, "awaiting": False,
                           "shared": False, "gate": Confirmation(clock=self.clock), "messages": [
                               {"role": "system", "content": self.prompt}]}
                self.sessions[token] = session
            session["busy"] = True
            session["awaiting"] = False
            self.inflight += 1
        started = self.clock()
        try:
            answer = self._turn(session, choice)
            return {"session": token, "challenge": challenge, "reply": answer[0], "reply_source": answer[1],
                    "tools": answer[2], "awaiting_choice": session["awaiting"],
                    "sample_family_shared": session["shared"], "seconds": round(self.clock() - started, 2),
                    "model": MODEL, "scope": "Software challenge; all tool effects are simulated."}
        finally:
            with self.lock:
                session["busy"] = False
                session["at"] = self.clock()
                self.inflight -= 1

    def _turn(self, session, choice):
        case = CHALLENGES[session["challenge"]]
        words = case["prompt"] if choice is None else ("Yes, please." if choice == "yes" else "No, thanks.")
        session["gate"].hear(words)
        session["messages"].append({"role": "user", "content": words})
        # A No is enforced in code and cannot be reinterpreted by the model.
        if choice == "no":
            return "Not shared. The sample family page is unchanged.", "code", []
        message = self._message(session["messages"], case["tool"])
        if not isinstance(message, dict):
            raise Unavailable("model_response_invalid", 502)
        calls = message.get("tool_calls") or []
        if not isinstance(calls, list) or len(calls) > 1:
            raise Unavailable("model_response_invalid", 502)
        if not calls:
            # A tool call written out as text is not a reply: the page never shows markup (the app speaks none,
            # tool_text). On 2026-10-30 a judge's check got "<tool_call><function=read_letter>..." as the reply.
            words = unspoken(message.get("content") or "")
            if not words:
                raise Unavailable("model_response_invalid", 502)
            return words, "model", []
        try:
            call = calls[0]
            fn = call["function"]
            name = fn["name"]
            arguments = json.loads(fn["arguments"])
            if (not isinstance(call.get("id"), str) or not call["id"] or name != case["tool"] or
                    not isinstance(arguments, dict) or len(str(fn["arguments"])) > 600):
                raise ValueError()
            result = self._tool(session, name, arguments)
        except (KeyError, TypeError, ValueError):
            raise Unavailable("model_action_rejected", 502) from None
        # Only keep the ordinary content/call fields; provider reasoning and metadata are dropped.
        session["messages"].append({"role": "assistant", "content": message.get("content") or "", "tool_calls": calls})
        session["messages"].append({"role": "tool", "tool_call_id": call["id"], "content": json.dumps(result)})
        trace = [{"name": name, "simulated": True, "confirmation_needed": bool(result.get("confirmation_needed"))}]
        if result.get("confirmation_needed"):
            # This web interface displays the gate's exact readback, then accepts a fresh button choice.
            session["gate"].said(result["say"])
            session["awaiting"] = True
            session["messages"].append({"role": "assistant", "content": result["say"]})
            return result["say"], "confirmation code", trace
        try:
            # Without this line Lightning wrote read_letter out again as text in 3 of 4 closing replies on 2026-10-30;
            # with it, 6 of 6 were words. It is sent only with this request and not kept in the conversation.
            reply = unspoken(self._message(session["messages"] + [CLOSING])["content"] or "")
        except Unavailable:
            reply = ""
        if not reply:
            # Preserve the result of an already-applied synthetic action even if the closing reply fails, or is only
            # a second tool call written out as text (no automatic retry: every call counts against the daily limit).
            return ("The model could not finish its reply. Check the sample-state result below.", "code", trace)
        session["messages"].append({"role": "assistant", "content": reply})
        return reply, "model", trace

    @staticmethod
    def _tool(session, name, arguments):
        if name == "share_with_family":
            if set(arguments) != {"note"} or _normal(arguments["note"]) != _normal(NOTE):
                raise ValueError()
            # Canonical payload: the only note this public demonstration can ever share.
            blocked = session["gate"].authorize(name, {"note": NOTE})
            if blocked:
                return blocked
            session["shared"] = True
            return {"shared": True, "note": NOTE, "how": "The invented note is now on this session's sample family page."}
        if name == "find_object":
            if set(arguments) != {"what"} or _normal(arguments["what"]) not in ("glasses", "reading glasses", "my reading glasses"):
                raise ValueError()
            return {"found": False, "looked": 4, "how": "In these simulated views the glasses were not found. "
                    "Say you couldn't see them, not that they do not exist. Never claim a sighting or a point."}
        if name == "read_letter" and arguments == {}:
            return {"kind": "bill", "sender": "Sunshine Coast Electric (invented)", "amount": "$86.40",
                    "by_when": "January 8, 2027", "about": "An invented electricity bill",
                    "to_do": "Pay by your usual method", "uncertain": False, "suspicious": False,
                    "how": "Explain the supplied sample bill in two short sentences. The camera/OCR result is simulated."}
        raise ValueError()
