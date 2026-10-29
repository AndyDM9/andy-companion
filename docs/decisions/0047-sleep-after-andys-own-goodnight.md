# 0047: Andy goes to sleep after its own goodnight, when the person asked for sleep

**Date:** 2026-10-29. **Status:** accepted.

## Context

On the robot, asked to go to sleep in words that were not one of the exact spoken controls (`voice_controls.py`), the
model answered "Good night! See you tomorrow." and called no tool; Andy stayed awake. The sleep guard
(`consent.sleep_asked`) only stops a call the person did not ask for; nothing made a call the model left out.

## Options

1. **More exact phrases** only: each new wording needs adding, and the person can't know which ones work.
2. **A note on the turn** telling the model to call `go_to_sleep` (as in decision 0044): the sleep words ("bye",
   "rest", "see you", "bed") come up in many turns that are not a goodnight.
3. **Follow Andy's own goodnight:** when the person's turn asked for sleep and Andy's reply is a short goodnight, not
   a question, go to sleep once the words are out, unless the model's call already did.

## Decision

Options 1 and 3, in `voice_controls.py`. A few more exact phrases ("time to go to sleep", "time for bed", with
"okay" before them). For the rest: the person's final turn sets a yes or no (sleep asked, by the guard's own
pattern), never the words; an assistant reply of at most 120 characters, without a question mark, with "good night",
"sleep well", "sweet dreams", "see you tomorrow" or their Spanish, starts `go_to_sleep` after 2 s if Andy is still
awake.

## Why

Two signals together, the person's and Andy's own, are rarer than either alone; the model already decided it was a
goodnight, so only the call it forgot is made.

## Consequences

A goodnight Andy says to a "bye, see you tomorrow" now ends the conversation, as the profile asks for goodnight and
goodbye. Andy's reply is looked at for those words and dropped; nothing of it is kept or logged.

## Revisit when

- The model calls `go_to_sleep` reliably after a goodnight, or a goodnight the person did not want ends a talk.
