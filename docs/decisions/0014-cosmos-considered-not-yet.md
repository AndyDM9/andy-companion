# 0014: Cosmos Reason 2 considered for the finder, not added before submitting

**Date:** 2026-10-25. **Status:** accepted.

## Context

The Physical AI track names NVIDIA's Nemotron, Cosmos, GR00T and Sonic models. Andy uses Nemotron (with Parakeet).
Two outside reviews of the entry (2026-10-25) asked whether to add NVIDIA Cosmos Reason 2 2B, a small vision model
that reasons about the physical world, as an offline fallback for finding things (PLAN B39, a stretch item since
2026-10-20). Five days remain before the deadline, and the submission work (the repository public, the video, the
endpoints, the history rewrite) is not finished.

## Options

1. **Add Cosmos Reason 2 2B on this computer now,** as the finder's offline fallback: about 6 to 10 hours, new code
   in the robot's loop, and the gated model's licence accepted on the founder's Hugging Face account.
2. **Say plainly that it was considered, and why it isn't in yet,** in the README's Limitations and on Devpost; add
   it only if the submission work is done by Wednesday 2026-10-28.

## Decision

Option 2. The README's Limitations and the Devpost text say which of the track's models Andy uses and why the others
aren't in. Cosmos stays planned for the Jetson version (README, "What a Jetson version would need").

## Why

- **It would add a fallback, not a better finder.** Online, Nemotron 3.5 Super VL on Token Factory already finds
  things: 9 of 9 zoomed in at the desk ([zoom check](../../evals/results/zoom-check-2026-10-20-1711.json)), no false
  find in 7 in simulation (decision 0013). The finder's real weakness at home is the closer look at things beyond the
  head's reach ([scorecard](../../evals/results/finder-eval-2026-10-20-2037.json)), which a different model doesn't fix.
- **It doesn't fit beside the voice on the GPU we ask for.** Hearing and speaking use about 7.1 GB (measured
  2026-10-20) and the README asks for an 8 GB GPU; 2 billion parameters at 16 bits are about 4 GB of weights alone
  (arithmetic, not measured).
- **New code in the physical loop this close to the freeze** risks the one thing that can't be fixed after the
  deadline: the video and the robot working as shown.
- **GR00T and Sonic** are policies for robots with arms or legs; the Reachy Mini has a head, antennas and a turning
  body.

## Consequences

The track wording is met by what Andy is (an embodied agent in Pollen's conversation app, with Nemotron deciding),
not by naming every model. Offline Andy finds nothing until the Jetson version.

## Revisit when

- The submission work is done by 2026-10-28 and the founder accepts the model's licence on Hugging Face.
- The Jetson version is built: an offline fallback belongs there.
