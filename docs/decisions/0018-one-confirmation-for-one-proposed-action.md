# 0018: One confirmation authorizes one proposed action

**Date:** 2026-10-26. **Status:** accepted.

## Context

The October 26 review found that unrelated sentences containing "tell", "send" or "with my family"
passed the sharing gate. A bare yes also opened every saving and sharing tool, without reference to
what Andy had asked. The profile's wording could not guarantee that the right note was shared.

## Options

1. Narrow the expressions, retaining a conversation-wide yes.
2. Bind a yes to one exact tool and argument payload, read back before the person agrees.
3. Add accounts and confirmations on the phone, removing a voice-only interaction.

## Decision

Option 2. Each conversation's tool dependencies own a memory-only confirmation. The first saving or
sharing attempt prepares the exact proposed content and returns a question without running the tool.
After Andy says that question, a fresh yes authorizes the same tool with the same arguments once,
within two minutes. A different topic, a refusal, expiry or a different payload cannot use it.
Explicit requests to remember can save one item directly. Sharing always uses the readback and yes.
Andy's own `remember` tool replaces the upstream tool's instruction to save silently.

## Why

Tests cover the original false positives, a changed payload, another tool, another conversation,
expiry, a missing readback and reuse. A test with Pollen's installed dispatcher actually writes one
invented shared note, only after its confirmation. No robot is connected by that test.

## Consequences

The tools and profile describe preparing and confirming separately. A generic yes without a pending
proposal cannot publish a note. The text suite now executes the real confirmation gate around its
synthetic tool results and distinguishes a proposal from a completed write. Prior scorecards predate
this change; current scores and failures must be reported separately.

## Revisit when

- Testing on the robot shows the model paraphrasing the readback or changing confirmed arguments.
- Multiple people need separate permission within one shared conversation.
