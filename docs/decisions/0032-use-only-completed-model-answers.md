# 0032: Use only completed, typed model answers in the non-streaming clients

**Date:** 2026-10-27. **Status:** accepted.

## Context

Synthetic provider fixtures reproduced an unfinished `<think>` draft returned by `deeper.think`,
and null vision content becoming the literal text “None”. Parseable JSON with missing/wrong fields
could also become an ordinary card or a no-sign result. These were injected tests, not a claim that
household content had been exposed.

[NVIDIA's model documentation](https://docs.nvidia.com/nim/large-language-models/2.0.10/get-started/advanced/get-started-nemotron-3.5-lightning.html)
describes token-budget exhaustion without a final answer and inline reasoning when a reasoning
parser is absent. Client validation must not rely on a successful HTTP status alone.

## Options

1. Coerce any content to a string and trust the provider's requested schema.
2. Attempt to salvage partial replies and infer missing fields.
3. Share a small reply validator and return the existing error path for incomplete/unusable results.

## Decision

Choose option 3 for `deeper`, `vision`, `letters` and `scamcheck`. A usable first-choice envelope needs
a message with non-empty string content and no refusal or unexpected tool call. An explicit
`finish_reason` must be `stop`; a missing field remains accepted for compatible legacy/local endpoints.
No automatic retry, model change or output-budget increase is added.

Plain-text clients use only the final suffix after a complete known reasoning wrapper; empty suffixes
and unfinished `<think>` markup are refused. Separate reasoning fields are never returned. Structured
callers keep literal tag strings for their own JSON parser rather than stripping strings inside JSON.

Letter/sign/warning-match replies must have exactly the required flat fields and their requested
string/boolean/integer-array types and enums. The helper covers these declared shapes, not general
JSON Schema. Missing or extra fields, wrong types and unknown enums produce errors, not ordinary
cards or “none” classifications. Existing grounding and page/message policies remain in their clients. When classification is unavailable
after a successful web lookup, the actual check tool explicitly marks it incomplete and shows an
incomplete-check card; generic warnings are not silently presented as a completed classification.

Malformed/refused replies are not transport outages and cannot invoke vision's fallback. The
standard-library helper is included in the scam and simulation job bundles and import-checked
without launching a job. The wheel and real SDK tool path are checked separately.

## Consequences

Rejected responses can require the person to ask again. A provider omitting finish metadata cannot
report truncation through that field; this check cannot infer every unmarked cutoff or factual error.
Known markup handling is not a general reasoning-channel or prompt-injection defence. The main
streaming voice engine and guided judge conversation have separate handlers and are outside this change.
No provider text, reasoning, question, camera picture or new conversation data is logged or retained.

## Revisit when

- A provider adds a verified completion convention or a legitimate reply is wrongly refused.
- A new client or response schema needs this boundary.
