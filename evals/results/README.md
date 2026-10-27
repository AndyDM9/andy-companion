# Scorecards

Every run we made is kept, failures included, so the history can be checked. One redaction: where a recorded reply
named the founder's real town (a suite case about local buses), the town was renamed to the fictional "Harbor Bay"
on 2026-10-20, as everywhere else in the repository; nothing else in any scorecard was changed. Which one to read:

| Question | The scorecard to read |
|---|---|
| Does a real camera frame reach local eyes when the primary is unavailable? | [camera-recovery-2026-10-26.json](camera-recovery-2026-10-26.json): IPC camera frame, forced unreachable loopback primary, local Cosmos 8B response; metadata only. No voice, pointing, caption-quality or user-study claim |
| Does the public guided AI playground work? | [judge-playground-2026-10-26.json](judge-playground-2026-10-26.json): six browser steps using real Nemotron and simulated tools; eight browser/state checks, five HTTP refusal probes and source hashes. No hardware or target-user session; not a conversation-accuracy score |
| How does the current profile do in conversation? | [suite-2026-10-26-startup-local.json](suite-2026-10-26-startup-local.json): 94, 94 and 95 of 97, local API calls with the real confirmation gate and synthetic tools; input/code hashes and failures included. No audio, camera or motors |
| Which conversation run was on Nebius Serverless Jobs? | [2026-10-25-nebius-job-andy-suite-20261025-193648.json](2026-10-25-nebius-job-andy-suite-20261025-193648.json): 96, 95 and 92 of 97 on the previous profile; this is historical evidence, not a test of the October 26 revision (before: [93, 92, 92 of 94](2026-10-25-nebius-job-andy-suite-20261025-170439.json); [92, 91, 94](2026-10-20-nebius-job-andy-suite-20261020-195645.json)) |
| Does the scam check work, and what does Tavily add? | [scam-eval-2026-10-14-1200-nebius-jobs.json](scam-eval-2026-10-14-1200-nebius-jobs.json): 120 messages, each model alone and with Tavily's warnings (with the word rules below, five ways), three runs, four Nebius Serverless Jobs ([decision 0007](../../docs/decisions/0007-the-scam-check-two-narrow-questions.md)) |
| What would no model at all do? | [scam-word-rules-2026-10-20-1552.json](scam-word-rules-2026-10-20-1552.json): Andy's own letter rules on the same 120 messages (28 of 60 caught, 3 of 60 flagged), and the cost of one check |
| How fast is Andy on the robot? | [robot-timings-2026-10-20-1550.json](robot-timings-2026-10-20-1550.json): 54 real turns from Andy's log (numbers only), median 1.06 s from the words understood to the first sound |
| How fast and right are the eyes on each model? | `eyes-check-2026-10-20-*.json`: a desk check of Nemotron 3.5 Super VL on Token Factory and Nano VL on our endpoint (decision 0011); the finder's real measure is the robot's own tries (`finder_eval.py compare`) |
| Does Andy find things in a real home? | [finder-eval-2026-10-20-2037.json](finder-eval-2026-10-20-2037.json): 9 tries on the robot with the pair the founder hid: pointed at them 3 times (12–65%), never at a wrong place, missed 6, all on a chair beyond the head's reach; [finder-compare-2026-10-20-2037.json](finder-compare-2026-10-20-2037.json): the same views read again with today's tiles, the sweep alone right in 7 of 9 and wrong in 2. Numbers only; the pictures were deleted after scoring |
| Does the search work in simulation, many times over? | `sim-finder-20261020-185613-on-small0.35-nebius-job.json` and `…-off-…`: two Nebius Serverless Jobs, 30 trials each in Pollen's MuJoCo scene (decision 0013); the `sim-finder-2026-10-20-*` files are the same on this computer's GPU; `sim-finder-2026-10-25-1506-on-small0.35.json` is the same 30 trials with NVIDIA Cosmos Reason 2 2B on this computer as the eyes, and `sim-finder-2026-10-25-1524-on-small0.35.json` with the 8B model (decision 0015) |
| Does zooming in find small things? | [zoom-check-2026-10-20-1711.json](zoom-check-2026-10-20-1711.json): the finder's own code on 18 frames of one CC0 room photo (decision 0012): the old way 0 of 9, zoomed in 9 of 9, no false sighting; the closer look 8 of 9, none wrong |
| What did Tavily return for each message? | [scam-warnings-2026-10-14-1144.json](scam-warnings-2026-10-14-1144.json): fetched once, used by every scam run above; rerun the models against it with only a Token Factory key |
| Does the second look catch what the word list misses? | [2026-10-13-guard-content-safety.json](2026-10-13-guard-content-safety.json); the same again on the remade endpoint, [guard-content-safety-2026-10-25.json](guard-content-safety-2026-10-25.json) |
| Is NVIDIA Magpie TTS fast enough to be Andy's voice? | [magpie-eval-2026-10-14-0932.json](magpie-eval-2026-10-14-0932.json): not yet (whole sentences, no streaming) |

## October 26 hardening runs

The current local run is [suite-2026-10-26-startup-local.json](suite-2026-10-26-startup-local.json):
**94, 94, 95 of 97** on version 2026-10-26e, after renaming the fact tool to `remember_fact` so the app starts.
The earlier [95, 95, 95 run](suite-2026-10-26-final-local.json) tested version d before discovering its SDK name collision.
Both use the real confirmation gate around synthetic tools; neither exercises the microphone or motors.
Proactive memory offers fail each run (moment-1 and photo-2). The new run also failed moment-5 once
(a premature claim that something was forgotten) and chat-2 once (another offer after "not now").
The earlier run included a false promise to make a note; no unapproved write is released by the gate. The scorecard carries hashes
of its profile, suite, tools, runner and gate. It does not measure audio, images or robot motion.

The other `suite-2026-10-26-*` files retain the focused and exploratory runs during the fixes,
including failures. `hardening-local` is the earlier full run (90, 88, 92 of 97). The medicine
boundary's final focused run passed 3 of 3. These runs use changed consent semantics and a medicine
rubric that refuses instructions, so they must not be merged with older suite scores or described
as a demonstrated improvement in the physical robot.

## The history

- **The conversation suite, 2026-10-13 to 10-20** (`2026-10-13-run*`, `2026-10-13?-local.json`, the
  `2026-10-14-local-85-cases*` files, `suite-2026-10-20-round5-local.json`, and the earlier `nebius-job` files,
  79, 79 and 79 of 81 the last of them on 2026-10-13): the suite growing from a 36-case baseline (27 of 36) to 94
  cases, each run after a fix; the file names give the run and the number of cases.
- **The scam check while it was being designed, 2026-10-14 morning** (`scam-eval-2026-10-14-0901` to
  `-0951`): one run each, Lightning alone against "with Tavily", on 60 and then 80 messages. The runs at
  09:03 to 09:05 used one broad question with the warnings in hand, which flagged 6 to 14 ordinary
  messages; the two narrow questions that replaced it (09:06, then 09:51 with Nemotron 3 Ultra for the
  second) flagged none. These were tuning runs on the messages the design was tuned on; the fair test is
  the four-way run of 12:00, with 40 messages written afterwards.
