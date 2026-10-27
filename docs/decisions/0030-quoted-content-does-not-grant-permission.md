# 0030: Quoted content does not grant permission

**Date:** 2026-10-27. **Status:** accepted.

## Context

An invented request to read a message followed by “Please remember…” passed the explicit-save
test in English and Spanish. The phrase belonged to the message, rather than the person asking
Andy to keep it. The latest utterance was already held briefly in the confirmation state; no real
message or memory write was needed to reproduce the gap.

## Options

1. Rely on the model to distinguish the request from the message.
2. Reject every request containing a quote or colon, including explicit requests to keep a fact.
3. Check permission in the person's introduction, before the first colon or opening quote, while
   requiring a fresh yes to match the complete utterance.

## Decision

Choose option 3. Explicit save requests and requests to prepare family sharing are recognised only
in the introduction. The same rule applies to the public consent helpers and installed SDK wrapper.
All four memory-tool names are covered. A quote cannot create a save request or a fresh yes.
A recognised message/text/email/letter/note introduction with no actual request outside the payload
returns a fixed non-echoing result: no memory or sharing proposal is created. This also covers a
printed message for permission purposes; the separate camera-source rule is unchanged.

An explicit introduction such as “Please remember this fact: …” still authorises the usual one
save. The existing conservative refusal check still reads the complete utterance, so a refusal
after a delimiter or a time colon continues to win. Sharing still needs exact readback
and a fresh yes. Other non-explicit memory calls may prepare the existing consent question, but cannot
write without the subsequent matching confirmation. Credential-value refusal remains in force.

## Why

The permission check must apply to the person's request rather than treating message content as
authority. This changes neither the stored payload nor the exact-argument binding and expiry.
It adds no classifier, model call, store or log; the existing 400-character ephemeral input is used.

## Consequences

This is a limited punctuation-based boundary. Unmarked reported speech and every possible language
or paraphrase are not covered. It is not a general prompt-injection defence or factual validator.
An initially quoted request without a separate introduction needs the usual proposal/readback/yes
path. Tests also cover contractions, time colons and legitimate delimited requests.

## Revisit when

- A representative invented message bypasses the boundary, or an ordinary request is wrongly refused.
- A new tool or backend adds a permission or persistence path.
