# 0044: Andy's own note on a turn, for a memory offer due and for the clock

**Date:** 2026-10-28. **Status:** accepted.

## Context

The profile asks three times for a memory offer when someone mentions something coming up with its day, or tells
a photo's story. Nemotron still answered "Sofia has her piano recital on Thursday" with "What was the recital like?"
in 6 of 12 runs, and once answered "What time is it?" with "The current time is 10:15 AM." without asking the clock.
More profile wording had not helped; the urgent-words net (`urgent.py`) only acts after the first reply.

## Options

1. **More profile wording:** tried; the offer stayed unreliable, and a warm sentence asked for before every memory
   question made the model claim "I'll remember…" first.
2. **A net after the reply,** like the urgent one: a second utterance after a wrong first one.
3. **Decide in code that the turn needs it,** and say so in a one-line note on the person's turn, in that request
   only, so the model's first reply already does it.

## Decision

Option 3, in `src/andy_companion/turn_notes.py`, added by the voice server (`notes_added`) and the suite alike:
- **Something coming up with its day** (an event word and a day, not past): prepare `remember_moment` first.
- **A photo's story** (after `describe_photo`, or `describe_view` whose description is a photo): prepare
  `remember_fact` first.
- **The time or the date asked:** call `get_today` first.

No note for urgent or crisis words (the urgent net's), questions (except about the time), requests to Andy, quoted
messages, a no, or anything already asked for. The note is never kept in the conversation; only its kind is logged.
Nothing is saved without the person's yes (`consent.py`).

## Why

The note is the most recent thing the model reads, and it worked where repetition in the profile had not: moment-1
missed in 1 of 33 runs after, 6 of 12 before; time questions asked the clock in 20 of 20 tries and in all nine final
runs. An independent review found the first version gave crisis words ("I am going to kill myself tomorrow") the
moment note, ahead of the urgent net; that, and four smaller misfires, were fixed before the final runs.

## Consequences

Whether a memory offer is due is now decided by patterns in English and Spanish, with their own tests; a phrasing
they miss gets no note and falls back to the profile. The photo story's offer is now always made through the
consent check, but the suite's judge still often wants a warmer word before the story is read back.

## Revisit when

- A model follows the profile's offer rule reliably without the note, or the patterns miss real speech.
