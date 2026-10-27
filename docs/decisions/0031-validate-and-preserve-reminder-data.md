# 0031: Validate reminder times and preserve unreadable reminder data

**Date:** 2026-10-27. **Status:** accepted.

## Context

An invented daily reminder passed both `minutes=1` and `at="08:00"`. The old code chose minutes,
so a noon request became a daily 12:01 reminder. Syntactically valid JSON with malformed reminder
rows caused read/display exceptions. Two damaged files in the same second could overwrite one
recovery copy. Recovery copies were not listed or removed by “delete everything”.

## Options

1. Rely on model/tool schemas and JSON syntax alone.
2. Drop malformed rows and continue with the remainder.
3. Validate times and stored rows, preserve the complete unreadable file under a unique name,
   and make saved copies visible and deletable on the existing owner page.

## Decision

Choose option 3. A reminder takes one time source. Booleans, non-finite/non-numeric minutes and
invalid clock formats are refused before writing. Daily reminders require their clock time.
New IDs are checked under the file lock, with bounded retries on collision.

Stored rows require unique non-empty IDs, bounded text, representable finite timestamps and a
supported repeat value. Optional metadata may be absent for older one-off entries. A malformed
store is preserved whole; no rows are silently dropped or reinterpreted. A unique reserved recovery
destination prevents collisions. If preservation fails, no replacement store is written. Cooperating
readers and writers share the lock. Failed atomic saves clean up their temporary copies.

The existing Settings page lists metadata only under “Reminders needing review”, in English or
Spanish. It explains these reminders are inactive. A helper can delete one saved copy or use the
existing delete-everything action; both use the existing authenticated routes and named-helper notice.
Individual copy deletion accepts only a filename found in the reminder directory, never an arbitrary path.
An empty recovery category does not appear in the healthy page's empty-state list. Public writes remain refused.

## Why

Rejecting ambiguity is preferable to silently choosing the wrong daily time. Preserving the whole
file retains the evidence needed for manual review, while making the saved data visible and deletable
keeps the existing deletion promise meaningful. The fix adds no dependency, model, recording or log
of reminder words. Tests use temporary stores and invented data; the installed SDK dispatcher is exercised.

## Consequences

All reminders in a malformed store are inactive until reviewed; the page says so. This does not
automatically repair or restore the data. An unwritable store/recovery directory can still require
owner intervention; writes fail rather than discard the original. The existing reminder's timing
and speech behaviour otherwise retain their scope; no new physical, medical or outcome claim.

## Revisit when

- A future valid store format needs compatibility support or review shows a false rejection.
- The project adds a supported recovery/restoration workflow.
