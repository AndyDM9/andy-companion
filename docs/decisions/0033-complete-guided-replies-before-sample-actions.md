# 0033: Require completed guided replies before sample actions

**Date:** 2026-10-27. **Status:** accepted; extends 0023 and 0032.

## Context

The public judge playground discarded the completion envelope before interpreting the message.
Injected provider responses reproduced a `length` finish displayed as a completed answer and a
parseable but incomplete tool call preparing a confirmation. These were invented fault fixtures,
not household data or observed public provider incidents. The earlier four-client fix explicitly
excluded this separate handler.

## Options

1. Trust parseable messages and keep ignoring completion metadata.
2. Retry or enlarge the output budget when a response stops early.
3. Validate completion before any answer or simulated action, keeping existing limits and error paths.

## Decision

Choose option 3. The single hosted provider must explicitly finish with `stop` for text or
`tool_calls` for the one allowed tool call. Missing, null, contradictory or unfinished status is
rejected. Unlike the local/legacy clients in 0032, this dedicated hosted transport has no need to
accept missing finish metadata. Refusals, legacy function calls, wrong roles and malformed messages
are rejected. Closing replies cannot request another action.

Use the existing final-text validator to exclude known inline reasoning drafts. Tool-turn prose is
unused by the interface, so discard it and separate reasoning/metadata before the next request.
Existing challenge/name/argument/readback/choice checks remain authoritative for simulated actions.
If a closing answer fails after a completed action, keep the actual sample state visible with fixed
failure wording. Do not reverse that state or claim the closing answer completed.

The Space build manifest includes the standard-library helper and has an isolated cold-import check.
The injected chat seam now returns the same complete provider envelope as the HTTP transport.

## Why

HTTP success and parseable arguments do not establish completion. Refusing early avoids presenting
an unfinished answer or preparing/applying an incomplete action. No new retries, token budget,
model, tool schema, dependency, store or log are required.

## Consequences

A provider convention change can refuse legitimate examples until reviewed. Visitors can retry an
example within the existing allowance. This validates completion and supported response shapes;
it does not establish factual accuracy, general reasoning filtering or physical behavior. The
robot's streaming voice handler and memory-offer consistency remain outside this change.

## Revisit when

- The hosted provider changes its verified completion convention.
- A new challenge needs a different validated response shape.
