# 0046: The Spanish wake listener runs only when Andy speaks Spanish

**Date:** 2026-10-29. **Status:** accepted.

## Context

While Andy slept, a video playing nearby woke it: the supervisor logged "wake phrase heard" though no one had said
one. The Spanish listener ran in every home where its model had been fetched once, as it had been here, on 2026-10-14.
Measured on 22 minutes of read English (LibriSpeech samples, whole sentences and the same speech cut into short
phrases): the English listener never chose a wake phrase; the Spanish one chose "Andy, buenos días" once and
"Buenos días, Andy" once, the second at full confidence on every word.

## Options

1. **A confidence floor** on the words of a wake phrase: the second false match scored 1.0 on all three words.
2. **A second pass** with a free-vocabulary recognizer over the same audio: more code and more to tune on the day of
   filming.
3. **Listen in Spanish only when Andy's language is Spanish** (`settings` "language", set by `set_language` or on the
   settings page): one line.

## Decision

Option 3, in `supervisor.listens_in_spanish()`, read each time Andy goes to sleep or quiet. The English listener runs
as before. Nothing is logged but "wake phrase heard".

## Why

Option 1 would not have stopped the match measured; option 3 removes it in an English home and keeps Spanish wake
phrases for a Spanish speaker.

## Consequences

In an English home, "Andy, despierta" no longer wakes Andy. A Spanish home with English speech nearby (a television)
can still be woken by the Spanish listener; that is an open problem in STATUS.

## Revisit when

- A false wake is seen with the Spanish listener off, or a Spanish speaker's home reports one.
