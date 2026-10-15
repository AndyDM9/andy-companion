# 0009: Four private links, each with its own token

**Date:** 2026-10-14. **Status:** accepted.

## Context

Andy serves four pages on the home network: the screen (for the TV), the family page, the settings page
and Under the hood. Until 2026-10-14 the screen and the hood page shared one token. The hood page is meant
to be shown, in the video too, and a shown hood link could read the screen's data and ask for the settings
code, whose QR is the settings link: full control of Andy.

## Decision

`board.tokens()` holds four tokens, one per page: `screen`, `family`, `setup` and `hood`. The hood token
opens only `/hood`, `/api/hood` and the status strip; the screen learns the hood's address from
`/api/screen` (screen token). Each settings code shown makes a new settings link. Every route compares its
token in constant time; caption, turn and frame posts are local-only as well.

## Why

A link shown on camera or sent to the wrong person reveals only its own page.

## Revisit when

- Accounts replace links (the company product, not this entry).
