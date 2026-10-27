# 0025: Make voice examples discoverable and show actual search progress

**Date:** 2026-10-26. **Status:** accepted.

## Context

The founder explicitly reopened useful feature and screen work after the earlier freeze. The TV
suggested one command at a time and showed the result of a search, but offered no browsable guide or
explanation of the wait during a search. The [product comparison](../research.md) supports improving
discoverability and feedback. It does not establish that other products lack these features.

## Options

1. Keep the freeze and the existing rotating hint only.
2. Add touch actions that initiate model/tool calls, or broad new communication features.
3. Add a passive spoken-command guide and event-driven feedback to the existing finder.

## Decision

Choose option 3. The guide is local static content in English/Spanish and opens by mouse, keyboard
or TV remote. It gives examples, never fabricated utterances or tool calls. Back closes it and restores
focus; a small display scrolls with remote arrows. It does not open automatically.

The finder starts a memory-only search card over the existing authenticated loopback boundary.
Its private random identifier scopes stage/count updates and cleanup to that card. Another card,
a clear or a newer search invalidates those updates. The identifier is omitted from screen reads.
Only four fixed stage names and a captured-view count from zero to four cross this new flow;
no target words, images or conversation text are added. Each real stage renews a 45-second expiry;
expired progress cannot be revived. Success/absence uses the existing result cards and image limits.
Errors and cancellation clear progress. Screen failure remains nonfatal to the finder.

## Why

This improves the existing physical interaction without another model, provider, tool, stored record
or public write route. Captured-view counts describe acquisition, not recognition progress or
confidence. The earlier-place check has no four-view counter because it precedes the room sweep.
The original clock size, contrast palette, captions, photos and reduced-motion choices remain.

## Revisit when

Consenting participants cannot discover the voice examples or understand the stages; the finder
changes its view count; or physical trials show that screen feedback distracts from the robot.
Browser/synthetic checks are not evidence of physical accuracy or usability with the intended audience.
