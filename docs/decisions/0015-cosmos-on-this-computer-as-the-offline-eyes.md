# 0015: NVIDIA Cosmos Reason 2 2B on this computer, as the offline eyes

**Date:** 2026-10-25. **Status:** accepted; amends 0014.

## Context

Decision 0014 (the same morning) kept Cosmos Reason 2 out until the submission work was done. The founder chose to
build it now: the licence was accepted on Hugging Face, and this desktop has two RTX 3090s, one of them free while the
voice server uses the other. The Physical AI track names Cosmos; Andy's eyes, Nemotron 3.5 Super VL on Token
Factory, need the network.

## Options

1. **Cosmos as the eyes:** replace Super VL with Cosmos Reason 2 on this computer.
2. **Cosmos as the fallback:** Super VL stays the eyes; when it can't be reached, the same question goes to Cosmos
   here, if it is running. `ANDY_VISION=local` uses Cosmos always, for anyone who wants nothing to leave the house.
3. **Cosmos Reason 2 8B instead of 2B:** about 17.5 GB of weights, which fits the free 3090 but no Jetson.

## Decision

Option 2, with the 2B model: `local-eyes/run.sh` serves `nvidia/Cosmos-Reason2-2B` with vLLM 0.32.0 on 127.0.0.1:8095
only (GPU 0 unless `ANDY_LOCAL_EYES_GPU`), `ANDY_VISION_FALLBACK=local` turns the fallback on, and `vision.answer`
sends both "what do you see?" and the finder's questions through it. Only an unreachable answer falls back (a network
error, a timeout, 502, 503 or 504), never a refusal (401, 400). The hood names the eyes that answered, so a fallback is
never passed off as Token Factory. Plain http is allowed only to this computer's own address, and the Token Factory
key is never sent to it. A third user service, `andy-eyes`, runs it.

## Why

Measured in Pollen's MuJoCo scene with the same 30 trials (seed 11, a glasses-sized duck, zoomed tiles and the closer
look), on this computer's GPU:

| Eyes | Pointed at it | False finds (absent) | Pointed elsewhere | Median error | Median time |
|---|---|---|---|---|---|
| Nemotron 3.5 Super VL, Token Factory (2026-10-20) | 21 of 23 (73–98%) | 0 of 7 | 0 | 0.78° | 3.24 s |
| Cosmos Reason 2 2B, this computer (2026-10-25) | 18 of 23 (58–90%) | 0 of 7 | 3 | 3.06° | 2.13 s |

([Super VL](../../evals/results/sim-finder-2026-10-20-1852-on-small0.35.json),
[Cosmos 2B](../../evals/results/sim-finder-2026-10-25-1506-on-small0.35.json).) Cosmos 2B is faster and claims nothing
when the thing isn't there, but points less precisely and three times at the wrong place: good enough to keep Andy's
eyes working offline, not better than Super VL. The 2B model is the one NVIDIA's Jetson design for the Reachy Mini
runs, so the fallback is also the Jetson version's eyes. A description of Andy's TV screen took about 0.5 s and was
right.

## Consequences

- Andy keeps its eyes when the network is down, on this desktop; with `ANDY_VISION=local`, no picture leaves the house.
- A second GPU (or a 24 GB one) is needed for it beside the voice server; the 8 GB minimum in the README is for Andy
  without it.
- The 8B model is untested: its licence is separate, and it is worth measuring the same way before choosing it.
- New code in the robot's loop five days before the deadline: the fallback is off unless set, and tested
  (`tests/test_local_eyes.py`). It has not yet been tried on the robot.

## Revisit when

- Cosmos Reason 2 8B is measured on the same trials.
- The fallback is tried on the robot with the network unplugged.
