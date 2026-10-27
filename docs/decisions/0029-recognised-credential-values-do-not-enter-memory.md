# 0029: Recognised credential values do not enter memory through tool dispatch

**Date:** 2026-10-27. **Status:** accepted.

## Context

The profile and fact-tool description forbid keeping passwords or payment credentials. An invented
explicit request nevertheless passed the confirmation gate: consent alone released the tool. No
real credential was used or stored in this audit.

## Options

1. Rely on the model following its existing instruction.
2. Reject all account-related words, including ordinary reminders and object locations.
3. Reject narrowly recognised credential labels followed by value markers or numbers, before the
   existing confirmation or memory dispatch path.

## Decision

Choose option 3. `Confirmation.authorize` checks the arguments of all four memory-tool names,
including the compatibility alias. Recognised password, PIN, card-number/code and access-key/token
values return a fixed refusal without repeating the value or preparing a readback. A denial clears
any earlier proposal. An explicit request or subsequent yes cannot override it.

## Why

The check belongs before tools that can write, and before a proposal could repeat the credential.
Ordinary statements such as a password-reset appointment or a bank card's physical location keep
the existing consent path. No external classifier, new store, logging or extra model call.

## Consequences

This is a limited label-and-value check, not recognition of every secret, language or encoding.
It cannot identify an unlabelled secret or prevent a model from repeating one elsewhere. It does
not scrub existing memories, direct store calls, reminders or family messages. The policy against
asking for passwords remains in the profile. Tests use invented values and the installed SDK
dispatcher to verify that the underlying memory routine is never called for recognised cases.

## Revisit when

- A representative invented credential form bypasses this check or ordinary account talk is refused.
- The project adds another memory tool or exposes a direct memory-write path.
