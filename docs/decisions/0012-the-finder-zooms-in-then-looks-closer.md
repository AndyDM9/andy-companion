# 0012: The finder zooms in, then looks closer

**Date:** 2026-10-20. **Status:** accepted; amended by 0016. **Changes:** how `find_object` reads its views (finder.py).

## Context

At home, Andy found the founder's glasses some times and not others. Each 1920x1080 camera frame was shrunk to
768 pixels before the vision model saw it; glasses across a room are 50 to 80 pixels wide at 1080p and 20 to 30
after shrinking, and Nemotron 3.5 Super VL reads an image at the size it is sent. The founder asked for zooming in,
cropping and enhancing. The research is in [research.md](../research.md#finding-small-things-zoom-in-then-look-closer-researched-2026-10-20).

Options:
1. **Send each frame at full size.** One call per view; at the desk it found the near glasses but not the far ones.
2. **Tiles:** each view as overlapping crops at full size (2x2 or 3x2), read at once.
3. **Tiles, then a closer look:** turn the head at the best sighting and check a close-up before pointing.
4. **Enhancement** (sharpening, contrast, super-resolution): no evidence it helps these models.
5. **A local detector first** (OWLv2, Grounding DINO, NanoOWL), the cloud model to confirm.
6. **The camera's 4K mode:** the daemon sets the resolution once when it starts.

## Decision

Option 3. Each view is six tiles (3 across, 2 down, 15% overlap) at full resolution, the four views' 24 tiles read at
once; a thing seen in two overlapping tiles is one sighting (the tile that sees it whole gives its place), and
sightings from neighbouring views within 6 degrees are one place. Andy turns its head at the best place (the most
tiles, then the most central), holds still, and asks about the middle half of a fresh frame; only a plain "yes"
counts, and a "no" moves to the next place (two at most). Then it points, using where the thing sits in the close-up,
and the TV shows the close-up in place of the wide view. `ANDY_FINDER_ZOOM=off` keeps the old way, for comparisons.

## Why

At the desk (`evals/zoom_check.py`, [scorecard](../../evals/results/zoom-check-2026-10-20-1711.json); 9 frames with a
real pair of reading glasses, 9 with them painted out): the old way 0 of 9; full-size frames 6 of 9 (none of the
three far ones, in the exploration before this decision); 3x2 tiles 9 of 9 with no false sighting; the closer look
confirmed 8 of 9 and said yes to none of the 9 painted-out spots. The 24 tiles take about 1.8 s together, as one
view did; the closer look adds about 2.5 s, and is something a viewer can see the robot do. About $0.005 a search, measured ([cost](../cost.md)).

## Measured at home (2026-10-20)

Nine tries on the robot in the founder's home, with the pair he hid ([scorecard](../../evals/results/finder-eval-2026-10-20-2037.json)): pointed at
them 3 times (95% interval 12 to 65%), never at a wrong place, missed 6, all on a chair. In 5 of the 6 the sweep
saw them and the closer look said no. The same saved views read again with today's tiles
([compare](../../evals/results/finder-compare-2026-10-20-2037.json)): the sweep's best view holds glasses in 7 of 9, and a wrong view in 2, which the closer look is there to stop. So the zoomed sweep works in a real
room, and the closer look loses a chair beyond the head's reach: the chair sits about 74 degrees to the side, past
the 60 the head turns, so the close-up is cut where the thing should be from a head that can't face it, and that
guess is furthest off there.

## Revisit when

- The closer look beyond reach (above): a larger close-up when the sighting is past the head's reach, or the body
  turning to face it; measured on the same kind of tries before trusting it.

- The robot's recorded tries (`finder_eval.py compare`) show where it still misses: then a second, lower row of
  views, 4K stills, or a local detector first (option 5, with NanoOWL as the Jetson path).
