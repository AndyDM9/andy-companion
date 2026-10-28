# 0045: Tool results give the words to say, not the reasons

**Date:** 2026-10-28. **Status:** accepted.

## Context

Tool results told the model why ("the person has already supplied message words aloud, not a held-up page"), and
the model said it aloud ("Since this is spoken content, not a held-up letter…") in 4 of 6 replies, then claimed
"I've noted that". A joke's result gave the setup, the punchline and how to pace them; twice the pacing was said
("**Setup:** … (a moment of silence…)"). A longer instruction placed after fixed words was read out with them once.

## Options

1. **Explain better** in the result: more words for the model to repeat.
2. **Give the exact words to say,** with a short instruction, as the consent proposal already did ("Say 'say'
   exactly, then wait").

## Decision

Option 2: when what Andy says matters, the result carries `say` (in the person's language) and a few words of `how`,
never the reason. Applied to: a message read out that asks Andy itself to keep or share it, quoted words offered as a
yes (`consent.py`), jokes and riddles (`fun.py`), and family photos, which get their own prompt instead of the
camera's (`vision.PHOTO_PROMPT`). Where the model must word the reply itself, `how` says what to do, never why.

## Why

The nine permission cases went from 6, 5 and 7 of 9 to 9, 9 and 9; 50 more replies had no instruction said aloud;
jokes and riddles were clean in 26 of 26 tries and in every run after.

## Consequences

Some replies are now fixed sentences rather than the model's own wording; they are short, in English and Spanish,
and tested.

## Revisit when

- The model stops repeating its tool results' reasons.
