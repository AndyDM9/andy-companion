# 0038: Final export checks the published release, not only the local tag

**Date:** 2026-10-27. **Status:** accepted.

## Context

In an invented local/bare-repository fixture, the published tag kept the first commit while the
local tag moved to newer committed files. The old final exporter returned success when page checks
were mocked as HTTP 200. A public tag at a different commit can still have working page URLs.
Likewise, pinning the repository's app metadata does not publish that metadata to Hugging Face.
The old final path also printed copy-ready fields before discovering broken citation links.
A string-valued dependency field could satisfy the pin's substring check despite being invalid
package metadata; other wrong project shapes could raise instead of reporting the missing pin.

## Options

1. Keep local snapshot checks and rely on successful page responses/manual publication review.
2. Require an exact published commit and matching public app package metadata before final export.
3. Automatically publish or move tags and update the app as part of the exporter.

## Decision

Choose option 2. Keep `final_problems` local and run it first. Only when those checks pass, use
anonymous, read-only GETs to the canonical GitHub reference endpoint. Require the exact tag name,
supported object types and this repository's 40-hex SHA-1 IDs. Resolve lightweight tags directly;
follow at most five annotated-tag objects, with cycle/object-identity checks. Construct endpoints
from validated IDs rather than following URLs supplied by responses. Compare the resulting commit
to the local tag's peeled commit.

Then require the public Reachy Mini app's `pyproject.toml` on Hugging Face to match the tested local
file byte for byte. Local checks already require that file and the other export inputs in the tag's
unchanged snapshot, and require the app dependency to use `hackathon-submission`.
The project/dependency containers must have supported shapes, with dependencies a list of strings;
a substring in a single string cannot satisfy that pin check.

Requests use five-second socket timeouts and read at most 65,537 bytes, accepting at most 65,536.
No provider settings, authorization headers, cookies or response/error contents are printed or
retained. Missing/mismatched/malformed/unavailable metadata stops final export with a fixed reason.
Final citation checks also run before printing any copy-ready submission fields. Ordinary draft
output and `--check` keep their existing behavior. No tag, app, submission or robot is changed.

## Why

HTTP success is insufficient to identify a release. Exact published identity and matching installer
metadata make the source and installation instructions reviewable together. Read-only checks keep
publication separate from validation and avoid silently changing the judged materials.

## Consequences

Final export needs anonymous GitHub/Hugging Face availability and can be blocked by rate limits,
timeouts or a tag chain beyond the supported bound. Fix publication/access and retry; draft export
remains available. This is an internal reproducibility control, not an additional hackathon rule.
It checks metadata at export time, not future immutability, every app asset or successful hardware
installation. Video visibility/rights/duration/footage, actual submission and hardware access remain
manual obligations. The deadline freeze still applies.

## Revisit when

- The repository adopts different Git object IDs or a different app publication host.
- A legitimate release needs a deeper tag chain or another supported packaging workflow.

Reference: GitHub's [reference](https://docs.github.com/en/rest/git/refs#get-a-reference) and
[annotated-tag](https://docs.github.com/en/rest/git/tags#get-a-tag) APIs.
