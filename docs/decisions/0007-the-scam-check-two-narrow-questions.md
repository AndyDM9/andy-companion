# 0007: The scam check asks two narrow questions, and the web's warnings are matched by a strong model

**Date:** 2026-10-14. **Status:** accepted.

## Context

Someone reads a suspicious message aloud and asks Andy whether it's a scam. A wrong "it's a scam" frightens
people off their own family's messages; a wrong "it's fine" is worse. On 2026-10-14, asked one broad
question with Tavily's consumer-protection warnings in hand, Nemotron took the warnings' topic as proof:
a grandchild's recital invitation became "computer access" (11 of 40 ordinary messages flagged).

## Decision

Two narrow questions, each with a strict schema (`src/andy_companion/scamcheck.py`):

1. **The message alone,** Nemotron 3.5 Lightning: which known scam's sign it shows, if any, quoting the
   message's words; code accepts the sign only if those words are in the message.
2. **Each Tavily warning,** Nemotron 3 Ultra: does the message use the same trick the warning describes,
   the same trick and not merely the same topic?

A message shows scam signs if either says so; the warning's source is what Andy names aloud. When the
web lookup fails, Andy says it couldn't check the warnings, never "no sign". Tavily gets the message with
numbers, links and emails removed.

## Why (measured, 2026-10-14)

120 messages read aloud, 40 of them written after this design was frozen; Tavily fetched once per message;
the models run three times as Nebius Serverless Jobs (`evals/scam_eval.py`, `cloud/scam-job.sh`):

| | Scams caught (of 60) | Ordinary flagged (of 60) |
|---|---|---|
| Lightning alone | 53.3 | 0 |
| Ultra alone, no web | 55.7 | 0 |
| Tavily's warnings matched by Lightning | 60 | 24 |
| **Tavily's warnings matched by Ultra (this design)** | **58** | **0** |

The web finds the trick; only the stronger model tells the trick from the topic. A bigger model without
the web does not get there.

## Revisit when

- A smaller model matches warnings without false alarms (rerun the four arms).
- The two misses recur in use: a landlord's "we've changed banks", and a name-only text.
