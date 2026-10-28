# 0042: Outline only the confirmed screen copy using an optional local mask

**Date:** 2026-10-28. **Status:** accepted.

## Context

The founder requested an outline around the object in the finder picture. A border around a whole
view does not identify which item Andy meant. Existing Nemotron close-up confirmation and pointing
already work independently of a screen annotation; the shared robot is being used by another app.

## Options

1. Replace the finder with a new segmentation-driven robot pipeline.
2. Draw a guessed box/contour from the existing point, without a mask.
3. Optionally paint a local mask on the confirmed display copy, leaving decisions and movement alone.

## Decision

Choose option 3. Independently implement a loopback-only HTTP mask client, disabled unless
`ANDY_OUTLINE_URL` is set. It sends only the confirmed crop and object label to a separately operated
service. Existing Nemotron validation and angles remain authoritative. Only one qualifying mask
containing the confirmed point is drawn; ambiguous, unsupported or unavailable results use the
ordinary picture. Numeric polygon bounds, counts, reply size and transport timeouts are checked.
No proxy, redirect, external URL, provider markup, new dependency or automatic service startup.

The worker returns pixels only; cancellation while awaiting it cannot publish a late result.
Annotation occurs after the point is queued and recording has used unmodified pictures. The normal
two-minute authenticated in-memory screen-image route owns the annotated copy. No new store or
family-sharing path. Both fresh searches and remembered-place confirmation use the same helper.

## Why

This gives a concrete visual cue without making an optional service part of finding or pointing.
A local service can reuse an operator's existing licensed model without changing the brain, GPU
allocation, robot controller or hosted examples. A guessed outline would imply evidence we lack.

## Consequences

The normal installation has no outline; a compatible licensed server is an explicit prerequisite,
and its code/weights are not bundled here. SAM materials have their own licence. Additional local
inference may delay the spoken result; the socket timeout is per operation, not a total deadline.
Conservative matching may show no outline for a real object. Mask quality is not physical-finding
accuracy. Unit/loopback tests and a real service request on an own illustration do not complete
camera, pointing, crowded-scene or concurrent-deletion checks. Existing services/config stay untouched
while another app uses the hardware. Details: [object-outline.md](../object-outline.md).

## Revisit when

- Real staged trials show unacceptable contour alignment, latency or fallback behavior.
- A maintained service interface and independent GPU budget justify shipping a server separately.
