# 0043: A tool call the model writes as text is made, when it fits a tool Andy has

**Date:** 2026-10-28. **Status:** accepted.

## Context

About one reply in 70, Nemotron 3.5 Lightning writes the call it means to make as text, in its own markup
(`<tool_call> <function=get_today> …`), instead of returning it as a tool call. Four such replies failed in the nine
Serverless Job runs of 2026-10-28's afternoon. The voice server already left the markup unspoken, so the turn said
and did nothing: a reminder accepted but not set, a time question unanswered.

## Options

1. **Leave the markup unspoken, as before:** safe, but the turn does nothing and the person repeats themselves.
2. **Ask the model again** when a reply is only markup: a second round trip (about a second more), and the same model
   may write the same markup.
3. **Read the markup back into the call it names** and make it, as if the model had: no extra model call.

## Decision

Option 3, in `src/andy_companion/tool_text.py`, used by the voice server (`voice/serve.py`, `written_calls_made`)
and the suite (`evals/run_suite.py`, `as_on_the_robot`) alike. A written call is made only for a tool the request
gave the model, only with that tool's own parameters, each of its declared type and every required one there, at
most three, and never when the reply also made a real call. The voice server holds the markup back from speech as
the reply streams and keeps it out of the conversation; it logs the tool's name only.

## Why

Every rule in code still applies to a call made this way (a save or share still needs the person's yes;
`consent.py`). After it: none of 36 evening runs failed on markup. Of 12 tries of one research request, 2 came as
written calls, both made.

## Consequences

The suite now measures what the robot does with a written call. A written call that names a parameter its tool
doesn't have is still dropped, and the turn says nothing (3 empty replies in 36 runs, cause not recorded).

## Revisit when

- Token Factory returns tool-call markup only as real calls, or the model stops writing it.
