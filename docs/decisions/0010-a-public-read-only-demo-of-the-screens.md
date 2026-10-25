# 0010: A public, read-only demo of the screens, as a Hugging Face Space

**Date:** 2026-10-20. **Status:** accepted; the Space itself waits on the founder's account.

## Context

In Devpost's judging session (2026-10-20), every project the judges reviewed had a link they opened and
clicked through, typing their own examples; most of their feedback came from that. Andy's screens could be
seen only with `uv sync` and `scripts/demo_screen.py` on the judge's own computer. The robot itself can't be
put online, but its four pages run on sample data with no robot, model or keys.

Options:
1. **Screenshots and a GIF only.** Nothing to click.
2. **A static copy of the pages** (GitHub Pages, Cloudflare Pages) with the server's answers faked in the
   browser. A second copy of the pages to keep in step, and not the real server.
3. **The real demo server, hosted, writable.** Anything one visitor typed on the family page would appear on
   every visitor's TV: a page anyone can write on, shown to strangers.
4. **The real demo server, hosted, read-only,** on a Hugging Face Space (Docker), the home of Reachy Mini
   apps, free on its CPU tier.

## Decision

Option 4. `scripts/demo_screen.py --public` serves the same pages from the same server, with
`screen_server.READ_ONLY` set: every POST answers 403 with "This is a public demo with sample data: nothing
you send is kept or shown to anyone.", and each page shows that sentence where it would show a saved
change. The night clock is off (visitors come at any hour), the server keeps New York time, and only
huggingface.co may frame the pages. A front page at `/` says what Andy is and what each page shows.
`scripts/space.sh build` puts together only what the demo needs (the source, the demo script, the lock
file, the licence, `space/Dockerfile` and `space/README.md`); no keys, tests, evaluations or robot code.

## Why

The judges see Andy's real pages working, in their own browser, in seconds. Read-only means nothing a
visitor types reaches another visitor, so the page needs no moderation. It is the same code as on the robot,
so it can't drift from it.

## Revisit when

- Visitors should try a write (send a note, suggest a reminder): give each visitor their own sample
  household instead of turning writes on.

## Amended 2026-10-25: a Docker Space needs Hugging Face PRO

Creating the Space was refused (402): Hugging Face now hosts Docker and Gradio Spaces on its free CPU only for PRO
subscribers; static Spaces stay free. The founder chose PRO (about $9 a month, through judging to 2026-12-15) over a
static snapshot of the pages (free, but hours of new work in the last week, and a recording instead of the real
server) or no Space. The Space is uploaded private first, for the founder to check, and made public with the
repository. The Reachy Mini app is a static Space, so it needs no subscription.
