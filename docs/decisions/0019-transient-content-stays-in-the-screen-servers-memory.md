# 0019: Transient content stays in the screen server's memory

**Date:** 2026-10-26. **Status:** accepted; amends the data flow in 0009 and 0010.

## Context

The screen card was written to `screen.json`. A scam receipt could include words the person had read
aloud. Research topics and answers were written into `inbox.json`, and deleting everything left the
current card behind. Expiring a file after five minutes still writes its contents to disk.

## Options

1. Keep the files and describe them as temporary storage.
2. Put cards and research answers in shared memory through the existing local screen server.
3. Merge the supervisor and conversation app into one process to share Python objects.

## Decision

Option 2. The screen server owns cards and pending research answers in memory. The conversation app
uses `transient.py` over loopback HTTP. The endpoint requires the screen token and a loopback client;
it is refused in the public read-only demo. There is no disk fallback. The previous screen file and
old research entries are removed on startup without printing their contents.

Family notes, suggestions and photos retain their existing owner-only storage. Pending items appear
on the settings page and can be deleted individually. Delete everything also clears the card,
captions, views and pending research, while retaining notices of who changed settings. A generation
change prevents a running research from posting its answer after deletion.

## Why

A regression test starts the real screen server and sends cards and research from another Python
process. The server and client see the same state, neither writes the words to disk, and a wrong token
cannot clear the card. Tests also cover deletion, pending-item visibility and medicine-page content.

## Consequences

Restarting the screen server forgets transient content. If the server is unavailable, cards and
research delivery cannot fall back to a file. Reminders, explicitly remembered facts and shared notes
remain persistent. The public demo uses the same memory-backed server with invented data.

## Revisit when

- The processes move to different computers or another transport is needed.
- Product testing finds a need to resume a research after a restart: explicit permission would be needed
  before adding persistent conversation-derived state.
