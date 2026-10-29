# 0048: Andy asks once about speech in another language, then leaves it alone

**Date:** 2026-10-29. **Status:** accepted.

## Context

A turn mostly in another alphabet reaches the model as "couldn't make out these words: ask again" (October 28,
`voice/serve.py`). On the robot, over four minutes of speech nearby in another language, 46 turns were taken as
unclear and Andy answered 21 of them, asking again each time over the people talking.

## Options

1. **Ask again every time,** as before: right for one misheard sentence, intrusive for a conversation or a video.
2. **Never answer** such a turn: a person whose sentence was misheard gets no reply at all.
3. **Ask once,** then leave further such turns unanswered until 30 s pass without one or a clear turn comes.

## Decision

Option 3, in `voice/serve.py` (`unclear_once`): a turn left unanswered becomes an empty transcript, which the speech
package passes to no model. Each unclear turn keeps the stretch going; only the gap in seconds is logged.

## Why

A sentence said to Andy and misheard gets the same "please say it again" as before. A stretch of talk in another
language near the robot costs one interruption instead of one every few seconds.

## Consequences

Someone misheard twice within 30 s gets no reply the second time; a clear turn, or a pause, resets it.

## Revisit when

- Speech-to-text can be held to English and Spanish, or a person is misheard more than once in a row.
