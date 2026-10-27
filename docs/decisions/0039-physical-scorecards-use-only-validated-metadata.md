# 0039: Physical scorecards use only validated metadata and preserve prior files

**Date:** 2026-10-27. **Status:** accepted.

## Context

The fixed 30-trial scorer is intended to retain labels, outcomes and times without speech or pictures.
An invented extra CSV cell became an unexpected dictionary key and passed through to the scorecard.
Direct calls to `score` also bypassed plan/type validation. File updates truncated in place, and
`score --out` could replace its input or an earlier scorecard. A zero false-find count alone did not
distinguish correct absent responses from errors in all absent trials.

## Options

1. Trust the CLI/input sheet and export all dictionaries unchanged.
2. Silently drop extra cells/notes and continue with the remainder.
3. Require the fixed schema at reading/scoring, reject unsupported data, and preserve earlier files.

## Decision

Choose option 3. Validate the exact 30 planned rows, seven keys, string cells, fixed planned labels,
allowed outcomes and finite elapsed-time bounds for file reads and direct scoring. Reject extra/
missing cells or keys with fixed errors that do not echo values. Copy only validated canonical
fields into a scorecard so later caller mutations cannot introduce notes.

Serialize before touching the destination. Write a complete same-directory owner-only temporary
file, then replace the intended CSV update atomically. New plans and scorecards use atomic
no-clobber publication with a hard link; an existing file or symlink is preserved. Clean temporary
files after success/failure. This supports the project's Linux filesystem; unsupported publication
fails rather than overwriting old data. Use one operator/writer for the series; no read/modify/write
concurrency guarantee or power-loss durability guarantee is added.

Keep all attempts in the fixed denominators. Add correct-absent counts/intervals and errors per
presence group, retaining the total error count and existing metrics. The `commit` metadata still
identifies the scoring checkout; a fixed `commit_scope` explicitly says it does not automatically
identify the robot's revision during each attempt. Keep the robot revision unchanged and verify
that association manually before publication.

## Why

Strict schema checks uphold the no-free-text measurement design. Preserving the original sheet
and existing reports protects work already collected. Separating correct rejections and errors
makes the evidence easier to assess without hiding failed attempts.

## Consequences

Use a new output filename to score again. Existing valid fixed-plan sheets remain usable; malformed
or extended ones require review. The tool cannot prove human-entered results are true or replace
physical observation, footage or a user study. Invented test files stay separate from real evidence;
no actual physical trial or improved success rate is claimed by this change.

## Revisit when

- A new measurement protocol needs different tasks/labels; version it separately.
- Multiple operators, another filesystem or automatic per-trial robot provenance are required.
