# 0041: Preflight requires current audio counts and usable final model text

**Date:** 2026-10-27. **Status:** accepted.

## Context

The live doctor crashed on invented list/null health roots. Missing counts defaulted to zero, and
stale or future-dated metadata could leave the unanswered-speech check green. The fast conversation
probe accepted HTTP success without checking the reply, while the vision probe accepted truncated
or refused text. Endpoint catalogue requests were labelled as model answers.

## Options

1. Keep transport-only checks and explain every limitation to the operator.
2. Add separate manual reply parsing and default incomplete audio metadata to zero.
3. Reuse the existing final-text validator and treat unavailable/unsupported audio counts as unknown.

## Decision

Choose option 3. Both fixed text-only Token Factory probes use `model_reply.final_text`, without
printing or retaining provider text. Explicit non-stop finishes, refusals, tool calls, non-text,
empty final text and unfinished reasoning are rejected. The existing compatibility for omitted
finish metadata remains; this checks a usable transport reply, not its meaning or factual accuracy.
The conversation timing uses a monotonic clock and still requires less than 1.5 seconds.

The doctor reads the watchdog's required `at`, `drops_last_min` and `unanswered_s` fields without
changing the file. Numeric values must have supported types and be finite/nonnegative; drop counts
are integers, and unanswered duration may be null. Extra fields are ignored and never displayed.
Missing/unreadable/unsupported metadata fails both audio and unanswered-speech checks. Valid metadata
must be less than 30 seconds old and at most one second ahead, accommodating the watchdog's rounded
timestamp. Stale/future metadata cannot verify either check. Errors report fixed reasons, not contents.

Optional endpoint `/v1/models` checks explicitly say they test catalogue reachability, not inference.
A configured stopped endpoint remains a failure; this change does not conceal the known optional 404.

## Why

A preflight should distinguish verified counts and replies from unknown data. Reusing the runtime
validator avoids a weaker interpretation of completion/refusal metadata in diagnostics. Invented
faults and mocked replies reproduce the problems without recording household input or moving Andy.

## Consequences

Incomplete legacy health files now fail until the watchdog writes a current complete record. Clock
skew or a stopped app can fail both checks; neither is evidence that the person or microphone is at
fault. The doctor does not start/restart services, repair files or change models/endpoints. A healthy
text probe is not a camera, motor, audio, whole-conversation or availability measurement. A real spoken
task and movement check still precede filming. No hosted bundle or robot runtime change is required.

## Revisit when

- The watchdog schema, timestamp rounding or heartbeat interval changes.
- The model transport compatibility or diagnostic latency target changes.
