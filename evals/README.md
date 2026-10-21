# Measuring Andy

Every claim in the README comes from one of these, and every run is kept in [`results/`](results/README.md),
failures included.

| Script | The question | Runs |
|---|---|---|
| `run_suite.py` | Does Andy behave in conversation? 94 spoken situations in 22 areas, English and Spanish, with Andy's real profile and exactly the robot's tools (`tools.json`, written by `build_tools.py`), judged by NVIDIA Nemotron 3 Ultra; words that must never be said are checked in code | here, or as a Nebius Serverless Job (`cloud/suite-job.sh`) |
| `scam_eval.py` | Does Tavily make the scam check better, or is it the bigger model? 120 messages, five ways (word rules alone, two models alone, Tavily's warnings with each), three runs, 95% intervals | `--word-rules` here with no key; the models as Jobs (`cloud/scam-job.sh`) |
| `finder_eval.py` | How well does Andy find things at home? Scores the robot's recorded tries against labels, and reads the same tries again with each vision model | here |
| `zoom_check.py` | Does zooming in find small things? The finder's own code on labelled frames, zoom off against on | here |
| `eyes_check.py` | How fast and right is each vision model? | here |
| `robot_timings.py` | How fast does Andy answer on the robot? Every real turn's timing from Andy's own log, numbers only | here, on the robot's computer |
| `guard_check.py` | Does the second look (Content Safety) catch what the word list misses? | here, with the endpoint running |

Each prints `--help`. Andy's search in simulation is in [`sim/`](../sim/README.md).
