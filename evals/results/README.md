# Scorecards

Every run we made is kept, failures included, so the history can be checked. One redaction: where a recorded reply
named the founder's real town (a suite case about local buses), the town was renamed to the fictional "Harbor Bay"
on 2026-10-20, as everywhere else in the repository; nothing else in any scorecard was changed. Which one to read:

| Question | The scorecard to read |
|---|---|
| How does Andy do in conversation? | [2026-10-20-nebius-job-andy-suite-20261020-195645.json](2026-10-20-nebius-job-andy-suite-20261020-195645.json): the latest suite run, as a Nebius Serverless Job: 92, 91 and 94 of 94, five cases failing once each, with the judge's reasons. A final run comes before submitting |
| Does the scam check work, and what does Tavily add? | [scam-eval-2026-10-14-1200-nebius-jobs.json](scam-eval-2026-10-14-1200-nebius-jobs.json): 120 messages, each model alone and with Tavily's warnings (with the word rules below, five ways), three runs, four Nebius Serverless Jobs ([decision 0007](../../docs/decisions/0007-the-scam-check-two-narrow-questions.md)) |
| What would no model at all do? | [scam-word-rules-2026-10-20-1552.json](scam-word-rules-2026-10-20-1552.json): Andy's own letter rules on the same 120 messages (28 of 60 caught, 3 of 60 flagged), and the cost of one check |
| How fast is Andy on the robot? | [robot-timings-2026-10-20-1550.json](robot-timings-2026-10-20-1550.json): 54 real turns from Andy's log (numbers only), median 1.06 s from the words understood to the first sound |
| How fast and right are the eyes on each model? | `eyes-check-2026-10-20-*.json`: a desk check of Nemotron 3.5 Super VL on Token Factory and Nano VL on our endpoint (decision 0011); the finder's real measure is the robot's own tries (`finder_eval.py compare`) |
| Does the search work in simulation, many times over? | `sim-finder-20261020-185613-on-small0.35-nebius-job.json` and `…-off-…`: two Nebius Serverless Jobs, 30 trials each in Pollen's MuJoCo scene (decision 0013); the `sim-finder-2026-10-20-*` files are the same on this computer's GPU |
| Does zooming in find small things? | [zoom-check-2026-10-20-1711.json](zoom-check-2026-10-20-1711.json): the finder's own code on 18 frames of one CC0 room photo (decision 0012): the old way 0 of 9, zoomed in 9 of 9, no false sighting; the closer look 8 of 9, none wrong |
| What did Tavily return for each message? | [scam-warnings-2026-10-14-1144.json](scam-warnings-2026-10-14-1144.json): fetched once, used by every scam run above; rerun the models against it with only a Token Factory key |
| Does the second look catch what the word list misses? | [2026-10-13-guard-content-safety.json](2026-10-13-guard-content-safety.json) |
| Is NVIDIA Magpie TTS fast enough to be Andy's voice? | [magpie-eval-2026-10-14-0932.json](magpie-eval-2026-10-14-0932.json): not yet (whole sentences, no streaming) |

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
