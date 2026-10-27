# 0027: Start an object search before announcing it

**Date:** 2026-10-26. **Status:** accepted.

## Context

A reported watch request received an announcement without a finder call. Recent numeric/tool-name
telemetry showed no search dispatch or finder exception; services were running with exclusive robot
control. Invented direct model requests selected the finder. These observations do not establish
exactly what speech recognition heard or whether generation was interrupted.

The profile and tool both required Andy to speak a preliminary announcement before calling the
finder. That creates a response that can sound like action before the action is dispatched.

## Options

1. Keep the announcement first and ask people to repeat failed requests.
2. Add a separate keyword-triggered motion path alongside model tool calls.
3. Ask the model to call the existing finder before speaking, and explicitly cover watch requests
   and follow-ups after an unfulfilled promise.

## Decision

Choose option 3. The model should immediately call the existing `find_object` for an explicit
object-search request, including a watch or wristwatch. It must not substitute a promise or general
advice. Results, uncertainty, camera prerequisites and existing movement ownership are unchanged.
Negations, an already-found object and watching a programme are not object-search requests.

## Why

This removes the instruction to speak before dispatch and keeps one tool/movement path. Adding a
second trigger could race or duplicate the model's search. The targeted streaming checks exercise
invented requests and follow-ups with real inference; mocked SDK tests verify watch dispatch and
prerequisite failures. Neither proves the person's next spoken request will succeed.

## Revisit when

A fresh spoken trial still announces without dispatch, or starts a search for a non-request. Capture
only counts/tool names and obtain a live retry; never retain household speech to diagnose it.

## Amended 2026-10-26: held-up page reading

The final audit found the same announcement-only failure for `read_letter`. The tool-first response
order now also applies to that existing camera/OCR tool. Decision 0028 records its separate spoken-text
source boundary; the physical letter retry remains separate from the founder-confirmed watch retry.
