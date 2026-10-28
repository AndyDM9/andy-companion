"""2026-10-28: in the suite run as a Nebius Serverless Job, a letter case's whole reply was a tool call written out
as text, "<tool_call> <function=read_letter </function>". The speech package would have said it aloud; voice/serve.py
now takes such markup out of every sentence before it is spoken, and logs only how much."""

import importlib.util
import logging
import types
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def serve():
    spec = importlib.util.spec_from_file_location("andy_voice_serve_markup", ROOT / "voice" / "serve.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize("said, spoken", [
    ("<tool_call> <function=read_letter </function>", ""),                       # the reply seen on 2026-10-28
    ("<tool_call>\n<function=read_letter>\n</function>\n</tool_call>", ""),
    ('<tool_call>{"name": "read_letter", "arguments": {}}</tool_call>', ""),
    ("Let me read it. <tool_call> <function=read_letter </function>", "Let me read it."),
    ("<function=find_glasses>\n<parameter=what>\nglasses\n</parameter>\n</function>", ""),
    ("</tool_call>", ""),                                                         # the end of one, in a later sentence
    ("It's on the table, by the lamp.", "It's on the table, by the lamp."),       # ordinary words untouched
    ("Three is less than five: 3 < 5, and 7 > 2.", "Three is less than five: 3 < 5, and 7 > 2."),
    ("set_volume louder", ""),                                                   # seen in the suite, 2026-10-28
    ("look_into the farmers market", ""),
    ("I've turned it up. set_volume louder", "I've turned it up."),
    ("I'll set a reminder for the tea dance on Thursday.", "I'll set a reminder for the tea dance on Thursday."),
    ("Write to me at andy dot example, not a snake.", "Write to me at andy dot example, not a snake."),
])
def test_tool_markup_is_never_spoken(serve, said, spoken):
    assert serve.unspoken_tool_markup(said) == spoken


def test_only_a_count_is_logged_never_the_text(serve, caplog):
    with caplog.at_level(logging.INFO, logger="andy.voice"):
        serve.unspoken_tool_markup("<tool_call> <function=read_letter </function>")
        serve.unspoken_tool_markup("Nothing to take out.")
    assert len(caplog.records) == 1
    message = caplog.records[0].getMessage()
    assert "characters" in message and "read_letter" not in message and "tool_call>" not in message


def test_each_modules_remove_markdown_is_wrapped_once(serve):
    calls = []
    a = types.SimpleNamespace(remove_markdown=lambda text: calls.append(text) or text.replace("**", ""))
    b = types.SimpleNamespace(remove_markdown=lambda text: text)
    serve.no_tool_markup_spoken([a, b])
    serve.no_tool_markup_spoken([a, b])                                         # again: still one wrapper
    assert a.remove_markdown("**Be careful.** <tool_call> <function=read_letter </function>") == "Be careful."
    assert calls == ["**Be careful.**"]
    assert b.remove_markdown("<function=x </function>") == ""


def test_the_installed_speech_package_still_has_what_we_wrap():
    pytest.importorskip("speech_to_speech", reason="the voice environment is not installed here")
    from speech_to_speech.LLM import base_openai_compatible_language_model, language_model
    assert callable(base_openai_compatible_language_model.remove_markdown)
    assert callable(language_model.remove_markdown)


class Kinds:
    """Stand-ins for the speech package's event classes (the last test checks the real ones)."""

    class TextDelta(types.SimpleNamespace):
        pass

    class ToolCall(types.SimpleNamespace):
        pass

    class Usage(types.SimpleNamespace):
        pass

    class Part(types.SimpleNamespace):
        def model_copy(self, update):
            return Kinds.Part(**{**vars(self), **update})

    class AssistantMessage(types.SimpleNamespace):
        pass


def make_calls(accum):
    return [Kinds.ToolCall(name=entry["name"], arguments=entry["args"]) for entry in accum.values()]


GET_TODAY = {"get_today": {"type": "object", "properties": {}}}


def reply(serve, text, step=5, extra=(), tools=GET_TODAY):
    events = [Kinds.TextDelta(text=text[i:i + step]) for i in range(0, len(text), step)]
    events += [*extra, Kinds.AssistantMessage(content=[Kinds.Part(type="output_text", text=text)]), Kinds.Usage(n=1)]
    return list(serve.with_written_calls(iter(events), tools, Kinds, make_calls))


def spoken(events):
    return "".join(e.text for e in events if isinstance(e, Kinds.TextDelta))


def test_a_call_written_as_text_is_made_and_never_spoken(serve, caplog):
    with caplog.at_level(logging.INFO, logger="andy.voice"):
        events = reply(serve, "Let me look. <tool_call> <function=get_today> </function> </tool_call>")
    assert spoken(events).strip() == "Let me look."
    assert [(e.name, e.arguments) for e in events if isinstance(e, Kinds.ToolCall)] == [("get_today", "{}")]
    kept = [e for e in events if isinstance(e, Kinds.AssistantMessage)]
    assert [p.text for p in kept[0].content] == ["Let me look."]                  # the conversation keeps no markup
    assert [r.getMessage() for r in caplog.records] == ["voice: a tool call written as text was made: get_today"]


def test_a_reply_that_is_only_a_written_call_keeps_nothing_but_the_call(serve):
    events = reply(serve, "<tool_call> <function=get_today> <parameter=> {} </parameter> </function> </tool_call>")
    assert spoken(events) == ""
    assert not [e for e in events if isinstance(e, Kinds.AssistantMessage)]
    assert [e.name for e in events if isinstance(e, Kinds.ToolCall)] == ["get_today"]


def test_no_second_call_when_the_reply_made_a_real_one(serve):
    events = reply(serve, "Sure. <function=get_today></function>", extra=[Kinds.ToolCall(name="get_today", arguments="{}")])
    assert [e.name for e in events if isinstance(e, Kinds.ToolCall)] == ["get_today"]


def test_a_call_to_a_tool_andy_does_not_have_is_neither_made_nor_spoken(serve):
    events = reply(serve, "<tool_call> <function=open_the_door> </function> </tool_call>")
    assert spoken(events) == "" and not [e for e in events if isinstance(e, Kinds.ToolCall)]


def test_ordinary_words_pass_on_whole_and_in_order(serve):
    text = "It's 3 < 5, and the lamp is <on> the table. See you soon."
    events = reply(serve, text, step=3)
    assert spoken(events) == text
    assert [type(e).__name__ for e in events][-2:] == ["AssistantMessage", "Usage"]


def test_the_installed_speech_package_has_what_written_calls_need():
    pytest.importorskip("speech_to_speech", reason="the voice environment is not installed here")
    from speech_to_speech.LLM import base_openai_compatible_language_model as base
    from speech_to_speech.LLM.chat_completions_language_model import ChatCompletionsApiModelHandler as handler
    for name in ("TextDelta", "ToolCall", "AssistantMessage"):
        assert hasattr(base, name)
    for name in ("_build_optional_kwargs", "_iter_stream_events", "_iter_response_events", "_tool_calls_from_accum"):
        assert callable(getattr(handler, name))
