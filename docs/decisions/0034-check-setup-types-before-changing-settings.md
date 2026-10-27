# 0034: Check setup value types before changing settings

**Date:** 2026-10-27. **Status:** accepted.

## Context

Invented setup inputs reproduced `captions="false"` becoming true, fractional hours and volume
silently truncating, and non-object settings being treated as an empty request. Non-finite direction
and wrong site-list types raised low-level exceptions; the HTTP wrapper already converted several
of these to a generic 400. These are injected cases, not observed household changes.

## Options

1. Keep Python truthiness and numeric coercion for flexible inputs.
2. Try to interpret malformed values as the person's intent.
3. Validate the supported shapes before saving any part of a setup request.

## Decision

Choose option 3. Settings must be an object; omission remains an empty no-op, but explicit null,
arrays and scalars are rejected. Switches require actual booleans. Volume and night hours require
whole numbers; existing integer text and integral numeric values remain supported. The screen's
direction still supports rounding fractional degrees, but rejects non-finite values and booleans.
Site fields accept newline-separated text, a list of strings, or the existing null/empty clear form.
Names/towns accept text or supported empty values; the helper name must be non-empty text.

The complete batch passes `clean` before settings persistence, announcements, volume changes or
background event lookups. Existing field ranges, unknown-field ignoring, tokens, network boundary
and owner-page behaviour remain. Return plain field-specific ValueErrors through the current HTTP
400 path; do not log submitted values.

## Why

The normal browser already sends these JSON types. Rejecting ambiguous forms preserves false and
whole-number choices without guessing. HTTP tests verify unchanged stored bytes and no announcement,
speaker call or background lookup when a mixed batch contains an invalid field.

## Consequences

Malformed integrations that relied on truthiness or fractional truncation must send valid types.
No model, profile, tool schema, storage format, migration or new package dependency changes.
This is a request boundary, not general persisted-settings validation or recovery. It does not
establish hardware movement, spoken delivery or a complete first-use user study.

## Revisit when

- A legitimate setup client needs another explicitly defined representation.
- A separate persisted-settings audit defines preservation and recovery behaviour.
