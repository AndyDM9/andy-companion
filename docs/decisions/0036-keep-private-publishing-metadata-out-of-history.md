# 0036: Keep private publishing metadata out of history

**Date:** 2026-10-27. **Status:** accepted.

## Context

The founder requested an overall repository audit, including names from a public judging stream.
An anonymous mirror's 239 commits, 2,528 distinct blobs and commit metadata had no full-name matches
against the 23-person published roster. Surname candidates were an unrelated bibliography and binary
false positives. OCR checked 52 static image versions and three frames from each of four animated
assets, without matching names. This finite search and sampled OCR are not proof against every spelling
or visually encoded identity; the search terms and OCR text are not stored in this repository.

The audit did find 195 private AI-session trailers in commit messages and one retired screenshot
with an old private setup QR link. The QR token is not the current setup token. Earlier textual/key
scans did not cover these publication surfaces adequately.

## Options

1. Delete material only from today's tree, leaving it in the published history.
2. Replace the whole project history with a single snapshot, losing the development record.
3. Remove only the identified metadata and retired image object, retain the development record,
   verify the rewrite and prevent new private session trailers.

## Decision

Choose option 3, within the founder's requested history cleanup. Prepare and test an isolated rewrite
with git-filter-repo. Keep every commit, author/committer identity and date, including author credits.
Only the private session-trailer lines and the retired image object are removed. Verify each historical
file tree differs only by that image's removal, and the current tree remains identical. Keep an
owner-only rollback copy outside the project. Publish only with an explicit expected-old-head lease;
never overwrite an unexpected remote update.

The configured `commit-msg` hook runs a standard-library checker. It rejects private Claude/Codex
session trailers and recognised private AI-chat URL forms with a fixed, non-echoing error. Ordinary
author credits and public documentation links remain supported. It does not rewrite messages, inspect
conversation data or require a private name list. New tests use invented references only.

## Consequences

Rewritten commit IDs change. Other working copies must be freshly cloned or carefully resynchronised
without merging the old history back. Old evidence labels and CI runs retain their original measurement
scope; recorded file hashes remain valid because current application files are unchanged. A private
commit map is retained for tracing original IDs.

Git history cleanup cannot erase external clones, forks, provider caches or private rollback copies.
The published reachable history and a fresh anonymous clone must be checked separately. This is
publication hygiene, not a claim of comprehensive privacy detection or a new robot capability.

## Revisit when

- A new publication surface, private reference format or confirmed identity match is found.
- An organiser requests an exception to the submitted-material freeze.
