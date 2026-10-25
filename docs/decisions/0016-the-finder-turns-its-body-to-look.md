# 0016: The finder turns its body to look past the head's reach

**Date:** 2026-10-25. **Status:** accepted; amends 0012.

## Context

At home the finder pointed 3 of 9 times, never at the wrong place; all 6 misses were glasses on a chair about 74° to
the side ([scorecard](../../evals/results/finder-eval-2026-10-20-2037.json)). The sweep saw the chair in 5 of them
(its views reach about 95° each way), but the closer look and the point were clamped to 60°, the head's own reach,
so the glasses sat at the edge of the close-up and the strict yes/no said no. The founder asked that Andy turn and
look at the thing.

## Options

1. **Our own body move:** turn the base explicitly in the finder's moves, beside the head. New motion code, its own
   speed and limits, and a second owner of the body beside body-follow.
2. **Pollen's automatic body yaw:** send the head straight at the place, past 60°. Pollen's kinematics, with automatic
   body yaw on (the daemon's and the SDK's default), turn the base to keep the head within 65° of it, up to 160°.
3. **Leave it:** hide things within 60° for the video, and say so in the limits.

## Decision

Option 2. `finder.aim` sends the closer look and the point straight at a place up to `TURN_YAW_DEG` (110°, past all
the sweep sees) and pitch within 35° as before; the robot, the simulation and its film all aim through it.
`ANDY_FINDER_TURN=off` keeps the head's own 60°, for comparison or if it misbehaves on the day.

## Why

- Pollen's own inverse kinematics (the analytical solver the daemon runs), given the head at 74° and the body at 0:
  the body turns 9.5° and the head lands at 74.2°; at 86°, 21.1° and 86.0°; at 110°, 44.4° and 110.1°; the head never
  more than about 65° from the body (checked offline, 2026-10-25). The base turns within the limits Pollen set for it.
- It changes three angles, not the motion: the moves, their speed and the body-follow ownership stay as they are.

## Consequences

- Things beside Andy are looked at squarely, and Andy turns toward what it found, which reads on camera.
- Not yet tried on the robot: the base is heavier than the head, so a long turn may arrive later (the finder already
  waits up to 1.5 s for the head to say it has arrived). The live test's 3t3 tries it.
- Things behind Andy (past about 95°) are still out of the sweep.

## Revisit when

- The robot test shows the base lagging, overshooting or the head's picture blurred after a long turn.
- The sweep itself is widened behind Andy.
