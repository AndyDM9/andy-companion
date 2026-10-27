# 0037: Validate and preserve unreadable saved settings

**Date:** 2026-10-27. **Status:** accepted.

## Context

An invented settings file containing `[]` raised AttributeError in every reader. Malformed JSON
silently became defaults, and the next update overwrote the original. Valid JSON with wrong field
types could break the weather cache, screen, greeting or startup volume. Request validation (0034)
does not protect reads of an existing file.

## Options

1. Treat unreadable data as empty and overwrite it at the next save.
2. Keep only individually valid values, silently discarding the rest.
3. Check the known stored schema, preserve the complete unreadable original and explicitly show
   that defaults are in use until choices are set again.

## Decision

Choose option 3, following reminder recovery (0031). Settings readers and writers share the existing
file lock. Known choices, boolean switches, numeric bounds, date/timestamp caches, site lists and
weather/events cache shapes are checked before use. Missing fields use independent defaults; unknown
stored fields remain ignored for compatibility. Legacy integer-text volume is accepted and read as
an integer, including zero. Reads do not rewrite valid files. Direct updates reject unsupported
fields/values before touching the original. The helper page retains its separate request rules.

An unreadable original is moved to a uniquely reserved owner-only `settings.unreadable-*.json` file
before defaults are returned. Failed preservation prevents replacement; failed atomic saves remove
their temporary files. Logs contain only a generated filename, never settings values or file contents.

Settings lists metadata under “Settings needing review” in English and Spanish, explains that the
unreadable original is inactive and defaults apply to choices not set again. The existing authenticated
two-tap single/delete-everything controls delete these copies, with the existing named-helper notice.
Deletion accepts only a matching generated basename in the settings directory, not arbitrary paths.

## Why

Continuing with explicit defaults avoids a malformed file breaking ordinary readers. Preserving
the whole original avoids silent loss and partial reinterpretation. Showing and deleting copies
keeps retained data visible without putting personal contents in the browser or logs.

## Consequences

All choices from a malformed file are inactive until set again; defaults can differ from the person's
previous preferences. Recovery is not automatic repair or restoration. An unwritable directory can
still require owner intervention. Validation concerns data shape and supported bounds, not the
truth of a cached location or the correctness of a web service. Other stores are outside this change.
No model, dependency, motor behaviour, API credentials or physical-test claim is added.

## Revisit when

- A new settings format or a valid older field needs compatibility support.
- A supported manual recovery/restoration workflow is added.
