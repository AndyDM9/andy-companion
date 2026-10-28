"""2026-10-28: two first replies in the suite's final Serverless Job were tool calls Nemotron wrote out as text. The
voice server and the suite now make such a call (andy_companion.tool_text), but only one that fits a tool Andy has."""

import json
from pathlib import Path

import pytest

from andy_companion import tool_text

ROOT = Path(__file__).resolve().parents[1]
TOOLS = tool_text.schemas({"type": "function", "function": {"name": t["name"], "parameters": t["parameters"]}}
                          for t in json.loads((ROOT / "evals" / "tools.json").read_text()))


@pytest.mark.parametrize("written, made", [
    # The replies seen: the final Job (2026-10-28), the Job before it, and the memory-offer check (2026-10-27).
    ("<tool_call> <function=set_reminder> <parameter=what> tea dance with a live band </parameter> <parameter=minutes> "
     "1440 </parameter> </function=set_reminder> <par", [("set_reminder", {"what": "tea dance with a live band",
                                                                           "minutes": 1440})]),
    ("<tool_call> <function=get_today> <parameter=> {} </parameter> </function> </tool_call>", [("get_today", {})]),
    ("<tool_call> <function=read_letter </function>", [("read_letter", {})]),
    ("Qué bonito.\n<function=remember_fact>\n<parameter=fact>\nFuimos al parque con mi prima.\n</parameter>\n"
     "</function>\n</tool_call>\n", [("remember_fact", {"fact": "Fuimos al parque con mi prima."})]),
    ('<tool_call>{"name": "set_volume", "arguments": {"change": "louder"}}</tool_call>',
     [("set_volume", {"change": "louder"})]),
    ('<tool_call>{"name": "get_today", "arguments": "{}"}</tool_call>', [("get_today", {})]),
    # 2026-10-13's reply, its minutes in a broken tag: made with what it has, and the tool asks when (minutes is
    # not required: a reminder may be given a clock time instead).
    ("<tool_call> <function=set_reminder> <parameter=what> tea dance with a live band </parameter> <minute> 60 "
     "</parameter> </function> </tool_call>", [("set_reminder", {"what": "tea dance with a live band"})]),
])
def test_a_call_written_as_text_is_read_back_as_the_call(written, made):
    assert [(name, json.loads(args)) for name, args in tool_text.calls_in(written, TOOLS)] == made


@pytest.mark.parametrize("written", [
    "<tool_call> <function=open_the_door> </function> </tool_call>",                   # no such tool
    "<function=remember_fact><parameter=what>Likes tea</parameter></function>",       # its required fact missing
    "<function=set_reminder><parameter=what>tea</parameter><parameter=minutes>soon</parameter></function>",  # not a number
    "<tool_call>{not json}</tool_call>",
    "set_volume louder",                                                                 # never spoken, never made
    "It's on the table, by the lamp.",
    "Three is less than five: 3 < 5.",
])
def test_a_call_that_does_not_fit_is_not_made(written):
    assert tool_text.calls_in(written, TOOLS) == []


def test_a_parameter_the_tool_does_not_have_is_left_out():
    written = "<function=remember_fact><parameter=fact>Likes tea</parameter><parameter=save_now>yes</parameter></function>"
    assert tool_text.calls_in(written, TOOLS) == [("remember_fact", '{"fact": "Likes tea"}')]


def test_the_same_call_twice_is_made_once_and_never_more_than_three():
    once = "<function=get_today></function>"
    assert tool_text.calls_in(once * 2, TOOLS) == [("get_today", "{}")]
    many = "".join(f"<function=remember_fact><parameter=fact>fact {i}</parameter></function>" for i in range(5))
    assert len(tool_text.calls_in(many, TOOLS)) == tool_text.MAX_CALLS


@pytest.mark.parametrize("arriving, held", [
    ("Let me check. <tool_call> <function=get", 14),
    ("Let me check. <tool_", 14),                     # may be the start of one: held back until it is clear
    ("Let me check. <func", 14),
    ("It's 3 < 5", 10),                               # not the start of one: passed on
    ("All done.", 9),
])
def test_a_reply_still_arriving_is_held_back_only_from_a_possible_call(arriving, held):
    assert tool_text.held_from(arriving) == held


def test_tools_are_read_in_either_form_the_model_is_given_them():
    chat = [{"type": "function", "function": {"name": "get_today", "parameters": {"type": "object", "properties": {}}}}]
    realtime = [{"type": "function", "name": "get_today", "parameters": {"type": "object", "properties": {}}}]
    assert tool_text.schemas(chat) == tool_text.schemas(realtime) == {"get_today": {"type": "object", "properties": {}}}


def test_the_suite_hears_and_calls_as_the_robot_does():
    import importlib.util

    spec = importlib.util.spec_from_file_location("andy_run_suite_written", ROOT / "evals" / "run_suite.py")
    suite = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(suite)
    made = suite.as_on_the_robot({"content": "One moment. <tool_call> <function=get_today> </function> </tool_call>"})
    assert made["content"] == "One moment."
    assert [(c["function"]["name"], c["function"]["arguments"]) for c in made["tool_calls"]] == [("get_today", "{}")]
    real = {"content": "Sure. set_volume louder", "tool_calls": [{"id": "a", "function": {"name": "set_volume"}}]}
    assert suite.as_on_the_robot(real)["tool_calls"] == real["tool_calls"]          # a real call: nothing added
    assert suite.as_on_the_robot({"content": "Hello."}) == {"content": "Hello."}
