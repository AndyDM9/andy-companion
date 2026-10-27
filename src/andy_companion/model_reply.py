"""Final text from non-streaming model calls, without coercion or reasoning drafts.

No inputs, reasoning or rejected reply text are logged or retained. This validates the
transport envelope and reserved reasoning markup, not factual correctness or user intent.
"""
from __future__ import annotations

import json
import re
from typing import Any


class ModelReplyError(ValueError):
    pass


def final_text(payload: Any, *, structured: bool = False) -> str:
    try:
        choices = payload['choices']
        if not isinstance(choices, list) or not choices or not isinstance(choices[0], dict):
            raise TypeError
        choice = choices[0]
        message = choice['message']
        if not isinstance(message, dict):
            raise TypeError
    except (KeyError, TypeError):
        raise ModelReplyError('The model reply format was not usable.') from None
    # Some compatible local/legacy endpoints omit this field; an explicit non-stop
    # result is never presented as a completed answer.
    if 'finish_reason' in choice and choice['finish_reason'] != 'stop':
        raise ModelReplyError('The model did not finish its answer.')
    if message.get('refusal') or message.get('tool_calls') or message.get('function_call'):
        raise ModelReplyError('The model did not provide a final text answer.')
    content = message.get('content')
    if not isinstance(content, str):
        raise ModelReplyError('The model did not provide a text answer.')
    if not content.strip():
        raise ModelReplyError('The model gave no final answer.')
    if structured:
        # The caller decodes/validates JSON. Do not reinterpret tag strings inside
        # JSON values as a provider's reasoning wrapper.
        return content.strip()
    # Providers can put reasoning in a separate field, a <think> block, or a
    # prefix with only the closing marker. Only the final suffix is usable.
    closes = list(re.finditer(r'</think\s*>', content, re.I))
    answer = content[closes[-1].end():] if closes else content
    if re.search(r'</?think\b', answer, re.I):
        raise ModelReplyError('The model did not finish its answer.')
    answer = answer.strip()
    if not answer:
        raise ModelReplyError('The model gave no final answer.')
    return answer


def final_object(payload: Any, *, strings=(), booleans=(), integer_arrays=(), enums=None) -> dict:
    """The exact flat fields used by the letter/sign/warning-match clients, not a general schema validator."""
    try:
        value = json.loads(final_text(payload, structured=True))
    except (ValueError, RecursionError):
        raise ModelReplyError('The model did not provide the required answer fields.') from None
    fields = set(strings) | set(booleans) | set(integer_arrays)
    if (not isinstance(value, dict) or set(value) != fields
            or any(not isinstance(value[k], str) for k in strings)
            or any(type(value[k]) is not bool for k in booleans)
            or any(not isinstance(value[k], list) or any(type(i) is not int for i in value[k]) for k in integer_arrays)
            or any(value[k] not in allowed for k, allowed in (enums or {}).items())):
        raise ModelReplyError('The model did not provide the required answer fields.')
    return value
