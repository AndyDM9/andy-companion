# 0013: The finder tested in simulation, as Nebius Serverless Jobs

**Date:** 2026-10-20. **Status:** accepted.

## Context

The Physical AI track asks for "Nebius Serverless Jobs to run simulations, generate synthetic data, evaluate robot
policies". Andy's finder (decision 0012) had been measured at the desk on one photo, and on the robot only through the
founder's tries, a handful at a time. The search has geometry (where the head turns, how a sighting in a tile becomes a
direction, the closer look within the head's reach) that a photo can't test, and a robot can't test hundreds of times.

Options:
1. **Pollen's simulator daemon** (`reachy-mini-daemon --sim`): the whole robot in MuJoCo, Andy's app unchanged. The
   real robot's daemon already holds port 8000 and is another project's service; the simulated camera is streamed over
   UDP; heavy for a job.
2. **A virtual eye in Pollen's MuJoCo scene:** the scene's table, rubber duck, croissant and apple (reachy_mini
   1.12.0rc1, MuJoCo 3.3.0), rendered from a camera at the robot's eye camera, turned as the head would turn, with the
   finder's own camera model; the robot's body hidden. Andy's real search functions run on what it sees.
3. **No simulation:** only the robot's recorded tries.

## Decision

Option 2: `sim/finder_sim.py` (its own environment in `sim/`, so Andy's runtime is untouched) and `cloud/sim-job.sh`,
which runs it in a CPU container with software rendering (OSMesa), the scene fetched from PyPI inside the job and the
code sent as one compressed bundle under the 64 KB request limit. Each trial places the three things at random on the
table (a fifth of trials with the duck out of sight), runs the sweep, the zoomed tiles (Nemotron 3.5 Super VL on Token
Factory), `finder.merge_places`, and the closer look within reach, and scores the final direction against the scene's
truth: pointed within 6 degrees, a false find, the error in degrees. `--zoom off` runs the old way for comparison.

## What it showed (2026-10-20, scorecards in `evals/results/sim-finder-*`)

| Where | Duck | Zoomed in, closer look | The old way |
|---|---|---|---|
| This computer (GPU rendering) | full size, 30 trials | pointed 25 of 25, false finds 0 of 5, error 1.8° | 25 of 25, false finds 1 of 5, error 1.8° |
| This computer | a third (about glasses), 30 trials | pointed 21 of 23, 0 of 7, error 0.8° | 23 of 23, 1 of 7, error 1.5° |
| **Nebius Serverless Jobs** (software rendering) | a third, 30 trials each | **pointed 18 of 23 (58–90%), false finds 0 of 7, error 0.76°** | 19 of 23 (63–93%), 3 of 7, 2.73° |

Read plainly: on finding, the two ways are within chance of each other on rendered pictures (the desk photo, decision
0012, is where zooming in made the difference). What the closer look buys is clear in every run: no false find when the
duck isn't there (0 of 19 against 5 of 19), and pointing two to three times as precise. Software rendering in the jobs
draws a plainer picture than the GPU, and finds less.

## Limits

Rendered pictures are cleaner than a room: no motion blur, no lens distortion, even light. It tests the search's logic,
geometry and the model on rendered scenes, not the real rate, which comes from the robot's recorded tries.

## Revisit when

- A finder change (tiles, reach, close-up size) is made: rerun both ways before trusting it.
- Pollen's simulator can run beside the real robot's daemon: the whole app in simulation, the body included.
