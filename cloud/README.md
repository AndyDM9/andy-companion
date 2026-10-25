# Andy on Nebius AI Cloud

The scripts that run Andy's evaluations as **Nebius Serverless Jobs** and its optional models as **Nebius Serverless
Endpoints**. The conversation itself and the eyes need none of this: they call Nebius Token Factory directly.

| Script | What it runs | Measured |
|---|---|---|
| `suite-job.sh run` | The conversation suite (`evals/run_suite.py`, 94 spoken situations, judged by NVIDIA Nemotron 3 Ultra) in a small CPU container | 93, 92 and 92 of 94 (2026-10-25) |
| `scam-job.sh <warnings.json>` | The scam check's model runs against Tavily warnings fetched once, in four parts, two at a time | 58 of 60 scams caught, none of 60 ordinary messages flagged (2026-10-14) |
| `sim-job.sh run [trials] [scale]` | Andy's search in Pollen's MuJoCo scene (`sim/finder_sim.py`), software rendering, zoomed in and the old way | no false find in 7, 0.76° (2026-10-20) |
| `guard-endpoint.sh create\|start\|stop\|status` | NVIDIA Nemotron 3.5 Content Safety on one L40S (vLLM), the second look beside each reply | 7 of 8 held-out crisis phrasings, no false alarm |
| `vision-endpoint.sh create\|start\|stop\|status` | NVIDIA Nemotron Nano 12B v2 VL on one L40S, the optional eyes (`ANDY_VISION=endpoint`) | a description in 3.45 s against 1.35 s for Super VL on Token Factory |
| `secret.sh`, `job-entry.sh` | Helpers: a key into Nebius's secret store without ever being on a command line; the job's unpacking step | |

Each Job's code travels as one compressed bundle (a Job's request may hold 64 KB) and its Token Factory key comes from
the secret store, never from the Job's settings. The scorecards land in [`evals/results/`](../evals/results/README.md).
An endpoint costs about $1.55 an hour while running and nothing when stopped: `stop` it after use.

Needs the Nebius CLI signed in, and `NEBIUS_JOB_PROJECT` (or `NEBIUS_PROJECT`) set to a project whose region allows CPU
VMs for jobs. Nothing billed starts by accident:
- **The Job scripts need an explicit word:** `suite-job.sh run`, `sim-job.sh run [trials] [scale]`, `scam-job.sh
  <warnings.json>`. Run bare, or with arguments they can't use, they print their usage and start nothing.
- **Each asks before starting anything billed,** saying what it starts and for how long; `ANDY_YES=1` answers yes for
  a run nobody is watching.
- **If a Job script stops before the end** (an error, Ctrl-C), it names the jobs it started, which may still be
  running and billed until they finish or reach their timeout, and how to cancel each (`nebius ai job cancel --id`).
- **The endpoint scripts:** `create` asks first; `create` and `start` print the reminder that it is billed by the hour
  until `stop`. With no argument they show the endpoint's status.
