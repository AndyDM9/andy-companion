# Andy's search, in simulation

Andy's own search for a lost thing (`src/andy_companion/finder.py`), run on Pollen's Reachy Mini MuJoCo scene instead
of a room: the scene's table with a rubber duck, a croissant and an apple placed at random, seen through a virtual
camera at the robot's eye, turned as the head turns. The same code as on the robot sweeps four views, reads each as six
zoomed tiles with NVIDIA Nemotron 3.5 Super VL on Nebius Token Factory, looks closer at the best sighting, and points;
each trial is scored against where the duck really is ([decision 0013](../docs/decisions/0013-the-finder-tested-in-simulation.md)).

| File | What it does |
|---|---|
| `finder_sim.py` | Many trials, a scorecard with intervals: found and pointed within 6°, no false find when the duck is out of sight, the pointing error |
| `replay.py` | One search filmed step by step, captioned (`docs/images/sim-search.mp4` and `.gif`) |
| `../cloud/sim-job.sh` | The trials as Nebius Serverless Jobs: software rendering in a CPU container, both ways (zoomed in, and the old way) |

**Run it** with a Token Factory key, no robot (the scene is fetched from PyPI once, checked against its checksum):

    cd sim && uv sync && cd ..
    NEBIUS_API_KEY=… MUJOCO_GL=egl uv run --project sim python sim/finder_sim.py --trials 10
    NEBIUS_API_KEY=… MUJOCO_GL=egl uv run --project sim python sim/replay.py

`MUJOCO_GL=osmesa` renders without a GPU. `--zoom off` runs the old way, one shrunk picture per view;
`--duck-scale 0.35` makes the duck about the size of a pair of glasses.

**Measured** (2026-10-20, 30 trials each as Nebius Serverless Jobs, the glasses-sized duck): zoomed in with the closer
look, pointed 18 of 23 times with **no false find in 7** (error 0.76°); the old way 19 of 23, with 3 false finds in 7
(error 2.73°) ([scorecards](../evals/results/README.md)).

**Its limit:** rendered pictures are cleaner than a room (no blur, no lens distortion, even light). It tests the
search's logic, geometry and the model; the rate in a real home comes from the robot's own tries.

It has its own environment (`sim/pyproject.toml`: MuJoCo 3.3.0, the version Pollen's package pins), so Andy's runtime
is untouched. Scorecards keep numbers, never pictures.
