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
- The 8B model was measured the same afternoon (below).
- New code in the robot's loop five days before the deadline: the fallback is off unless set, and tested
  (`tests/test_local_eyes.py`). Tried end to end on this computer with Token Factory unreachable (2026-10-25, after
  fixing the settings Andy loads and how the hood, in the supervisor's process, learns which eyes answered); not yet
  on the robot.

## Revisit when

- The fallback is tried on the robot with the network unplugged.

## Amended 2026-10-25: the 8B model measured

The founder accepted the 8B licence the same afternoon. On the same 30 trials, with the whole of GPU 0
(`ANDY_LOCAL_EYES_MEMORY=0.92`, a 12,288-token context so its cache fits; about 21 GB in use):

| Eyes | Pointed at it | False finds (absent) | Pointed elsewhere | Median error | Median time |
|---|---|---|---|---|---|
| Nemotron 3.5 Super VL, Token Factory | 21 of 23 (73–98%) | 0 of 7 | 0 | 0.78° | 3.24 s |
| Cosmos Reason 2 2B, this computer | 18 of 23 (58–90%) | 0 of 7 | 3 | 3.06° | 2.13 s |
| Cosmos Reason 2 8B, this computer | 22 of 23 (79–99%) | 0 of 7 | 0 | 1.95° | 4.80 s |

([8B](../../evals/results/sim-finder-2026-10-25-1524-on-small0.35.json).) The 8B model never pointed at the wrong place and found as
often as Super VL (22 against 21 is inside the intervals, so no claim that it finds more); it is less precise than Super VL and slower.
**On a computer with a whole 24 GB GPU free, such as this desktop, the 8B model is the offline eyes**
(`ANDY_LOCAL_EYES_MODEL=nvidia/Cosmos-Reason2-8B` in the env file, read by `local-eyes/run.sh` and by Andy); 2B stays
the default, for one GPU beside the voice server or a Jetson.

## Clarified 2026-10-26: local vision is not an offline conversation

The fallback is inside `vision.answer`. Tool selection and ordinary replies still use Nemotron on
Token Factory. A total network outage prevents a new voice request from reaching that tool. The
next robot check therefore blocks the primary vision service while leaving conversation reachable,
then verifies the local eyes and the name shown on the hood. A completely offline voice assistant
is future work. The previous desktop test proved a vision call, not offline voice interaction.

## Corrected 2026-10-26: every fallback follows the same boundary

Stopped optional endpoints must not prevent a ready local fallback from running. Readiness now checks
the fallback too, and `answer` skips a known-unreachable optional primary. A stopped endpoint's 404
may fall back; a missing Token Factory model or an authentication refusal does not. The fallback
receives the same transport checks as primary eyes, closing an unchecked plain-HTTP path. A backend
labelled local must point to loopback even over HTTPS, consistent with this decision's on-computer claim.

The repeatable camera-only probe uses an unreachable loopback primary in its own process. A real
1920×1080 IPC frame produced a local 8B response in 2.874 s, with no image or generated description
saved. It does not verify the spoken conversation, what the person heard, the hood UI or motor pointing.
