# 0011: The eyes on Token Factory: Nemotron 3.5 Super VL, with our own endpoint as an option

**Date:** 2026-10-20. **Status:** accepted; amended by [0012](0012-the-finder-zooms-in-then-looks-closer.md) (the search reads zoomed tiles).

## Context

Andy's eyes ("what do you see?", family photos, finding the glasses) were NVIDIA Nemotron Nano 12B v2 VL on
our own Nebius Serverless Endpoint, one L40S, because Token Factory had no NVIDIA vision model for our key
(checked 2026-10-14). The endpoint takes about 15 minutes to start, costs about $1.55 an hour while on, and so
is stopped most of the time; then "where are my glasses?" fails in about 3 seconds with "my eyes are switched
off". On 2026-10-20 Token Factory's models API listed **NVIDIA Nemotron 3.5 Super VL** for our key (text and
image in, $0.30 and $0.90 per million tokens, us-north1).

Options:
1. **Keep the endpoint.** Measured with Andy since 2026-10-13; the smaller model on its own GPU; off most of
   the time.
2. **Super VL on Token Factory, always.** Always on, paid per picture; newer to Andy.
3. **Super VL by default, the endpoint as a setting,** both measured by the same scripts.

## Decision

Option 3. `ANDY_VISION` chooses: `token-factory` (the default), `endpoint`, or `off`
(`andy_companion.vision.eyes`). On Token Factory the request uses the conversation's key and turns reasoning
off (`enable_thinking: false`), which Super VL otherwise does first. The finder keeps its JSON schema; the
hood page and the doctor name the eyes in use.

## Why

Measured at the desk on 2026-10-20, three runs each, the same pictures
(`evals/eyes_check.py`, [scorecard](../../evals/results/eyes-check-2026-10-20-1614.json)):

| | Describe Andy's TV screen | Four views at once, for the glasses | Start |
|---|---|---|---|
| Nemotron 3.5 Super VL, Token Factory | median 1.35 s (1.34–1.51) | median 2.08 s (2.04–2.36); all four views right | none; about $0.0013 a search (before 0012's tiles; about $0.005 since) |
| Nemotron Nano 12B v2 VL, our endpoint | median 3.45 s (3.02–3.50) | median 2.28 s (2.27–3.69, the first one cold); all four views right | about 15 minutes (23 checks 20 s apart after RUNNING, plus the image pull); $1.55 an hour while on |

Both described the screen correctly; Super VL read its message word for word. One picture is not a measure of
how often each finds things in a real room: that is the robot's recorded tries, read by both.

The bigger model is faster here, it never has to be started, and a stopped endpoint was the most likely way
for the glasses moment to fail on camera. It is also the newest NVIDIA vision model, on the same service as the
conversation. The endpoint stays because it is the smaller model, on our own GPU: the comparison is the point.

## Revisit when

- The robot's own recorded tries (`evals/finder_eval.py compare … token-factory endpoint`) show Super VL finding
  less often than Nano VL.
- Token Factory's price or limits for Super VL change, or the model leaves the list.
