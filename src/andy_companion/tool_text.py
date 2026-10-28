"""Tool calls the model writes out as text instead of making them.

Nemotron 3.5 Lightning sometimes writes the call it means to make as text, in its own markup, instead of making it.
In the suite's final Serverless Job on 2026-10-28, two first replies were such calls: "<tool_call> <function=get_today>
<parameter=> {} </parameter> </function> </tool_call>", and a set_reminder with its words and its minutes. The voice
server already left the markup unspoken, so the turn then did nothing. `calls_in` reads the markup back into the calls
it names, and the voice server (voice/serve.py) and the suite (evals/run_suite.py) make them as if the model had: only
tools the model was given, only with that tool's own parameters, each of its declared type, every required one there,
at most MAX_CALLS. A call that does not fit is dropped, as before. A save or a share made this way still needs the
person's yes (consent.py), like any other.

Standard library only: the suite runs as-is in a plain Python container. Nothing here logs or keeps the words.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List, Tuple

MAX_CALLS = 3
# What is never spoken: a <tool_call> block (or one cut off at the end), a <function=...> block, stray tags, and a
# sentence that starts with a tool's own name ("set_volume louder", the whole reply once in the suite's 291 turns on
# 2026-10-28): words joined by underscores are never speech.
MARKUP = re.compile(r"<tool_call>.*?(?:</tool_call>|\Z)|</?tool_call>|<function=.*?(?:</function>|\Z)"
                    r"|</?function>|</?parameter(?:=[^>]*)?>"
                    r"|(?:^|(?<=[.!?]\s))[a-z]+(?:_[a-z0-9]+)+\b[^.!?\n]*[.!?]?", re.S)
# The first sign of a written call, in a reply that is still arriving.
START = re.compile(r"<tool_call\b|<function=")
_STARTS = ("<tool_call", "<function=")
_FUNCTION = re.compile(r"<function=\s*([A-Za-z_]\w*)\s*>?(.*?)(?=</function|<function=|</tool_call>|\Z)", re.S)
_PARAMETER = re.compile(r"<parameter=\s*([A-Za-z_]\w*)\s*>(.*?)(?=</parameter>|<parameter=|</function|\Z)", re.S)
_JSON_CALL = re.compile(r"<tool_call>\s*(\{.*?\})\s*(?:</tool_call>|\Z)", re.S)


def unspoken(text: str) -> str:
    """The words with every written call taken out."""
    return " ".join(MARKUP.sub(" ", text).split())


def held_from(text: str) -> int:
    """Where a reply still arriving must be held back: from the start of a written call, or from a last '<' that
    may begin one; len(text) when all of it can be passed on."""
    found = START.search(text)
    if found:
        return found.start()
    last = text.rfind("<")
    if last >= 0 and any(start.startswith(text[last:]) for start in _STARTS):
        return last
    return len(text)


def schemas(tools: Iterable[Any]) -> Dict[str, Dict[str, Any]]:
    """{name: parameters} from the tools given to the model, in Chat Completions or Realtime form."""
    found: Dict[str, Dict[str, Any]] = {}
    for tool in tools or []:
        if not isinstance(tool, dict):
            tool = getattr(tool, "model_dump", lambda: {})() or {}
        spec = tool.get("function") if isinstance(tool.get("function"), dict) else tool
        if spec.get("name"):
            found[str(spec["name"])] = spec.get("parameters") or {}
    return found


def _typed(value: Any, kind: Any) -> Tuple[bool, Any]:
    """(fits, value) for one written value and its declared JSON type."""
    if isinstance(value, str):
        value = value.strip()
    if kind == "string":
        return (True, value) if isinstance(value, str) else (True, json.dumps(value, ensure_ascii=False))
    if kind in ("integer", "number"):
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False, None
        if number != number or number in (float("inf"), float("-inf")):
            return False, None
        if number.is_integer():
            return True, int(number)
        return (False, None) if kind == "integer" else (True, number)
    if kind == "boolean":
        word = str(value).lower()
        return (word in ("true", "false"), word == "true")
    if kind in ("array", "object"):
        try:
            loaded = json.loads(value) if isinstance(value, str) else value
        except ValueError:
            return False, None
        return isinstance(loaded, list if kind == "array" else dict), loaded
    return True, value                              # no declared type: as written


def _fitted(raw: Dict[str, Any], schema: Dict[str, Any]) -> "Dict[str, Any] | None":
    """The arguments as the tool declares them, or None when they don't fit."""
    properties = schema.get("properties") or {}
    arguments: Dict[str, Any] = {}
    for key, value in raw.items():
        if key not in properties:
            continue                                # a parameter the tool doesn't have is left out
        fits, typed = _typed(value, properties[key].get("type"))
        if not fits:
            return None
        arguments[key] = typed
    if any(key not in arguments for key in schema.get("required") or []):
        return None
    return arguments


def calls_in(text: str, tools: Dict[str, Dict[str, Any]]) -> List[Tuple[str, str]]:
    """The (name, arguments as JSON) of each call written in text that fits a tool in tools."""
    written: List[Tuple[str, Dict[str, Any]]] = []
    for block in _JSON_CALL.finditer(text or ""):
        try:
            data = json.loads(block.group(1))
            raw = data.get("arguments") or data.get("parameters") or {}
            raw = json.loads(raw) if isinstance(raw, str) else raw
        except (ValueError, AttributeError):
            continue
        if isinstance(data.get("name"), str) and isinstance(raw, dict):
            written.append((data["name"], raw))
    for function in _FUNCTION.finditer(text or ""):
        raw = {name: value for name, value in _PARAMETER.findall(function.group(2))}
        written.append((function.group(1), raw))
    calls: List[Tuple[str, str]] = []
    for name, raw in written:
        if name not in tools:
            continue
        arguments = _fitted(raw, tools[name])
        call = (name, json.dumps(arguments, ensure_ascii=False)) if arguments is not None else None
        if call and call not in calls:
            calls.append(call)
    return calls[:MAX_CALLS]
