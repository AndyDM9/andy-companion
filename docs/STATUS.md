# Status

**Last updated 2026-10-20.** Update this file in the same commit as any change it describes.
The plan and its milestones are in [PLAN.md](PLAN.md); each milestone's history is in [CHANGELOG.md](../CHANGELOG.md).

## At a glance

| # | Milestone | State | Notes |
|---|---|---|---|
| M0 | Andy talks through Nemotron | ✅ Done 2026-10-13 | Parakeet, Nemotron 3.5 Lightning on Token Factory and Qwen3-TTS on the robot; measured below |
| M1 | Clock and reminders | ✅ Done 2026-10-13 | Verified on the robot: the time of day from the clock; a reminder set by voice, listed, and said unprompted when due |
| M2 | Privacy floor | ✅ Done 2026-10-13 | Verified live: no conversation text in any log, tool arguments not logged, no transcript printed by the voice server; Andy's memory only what the person asked it to keep |
| M3 | Body behaviours | ✅ Done 2026-10-13; more on 2026-10-20 | Looking at the person while speaking, following, sleep, quiet and wake, verified by the founder on the robot. Added 2026-10-20 and tested in code, awaiting the robot: turning to a second voice, waving back, moves taught by hand ([live-test.md](live-test.md) 3aa to 3dd) |
| M4 | The day, the same way every time | ✅ Done 2026-10-13 | The day plan, reminders in the person's words, pace and volume that stick, jokes, stories and On this day; English and Spanish |
| M5 | Tavily | 🔨 Built, awaiting the live test | Five APIs at runtime: search (news, look-ups, scam warnings at advanced depth), extract (links family send), crawl (what's on), map (the town's events page, at setup) and research (streamed to the TV). The scam check measured five ways ([results](../evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json)) |
| M6 | Eyes | 🔨 Built, awaiting the live test on the robot | Nemotron 3.5 Super VL on Token Factory by default (decision 0011), Nano VL on our own endpoint as the option; letters read on this computer; finding things reads four views as zoomed tiles and looks closer before pointing (decision 0012), tested in simulation as Nebius Serverless Jobs (decision 0013) |
| M7 | Andy's screen and the family page | 🔨 Built, awaiting the live test | The TV, Under the hood, the family page and the settings page, every text colour 7:1; a public read-only demo of all four on sample data (decision 0010), its Hugging Face Space waiting on the founder's account |
| M8 | Proof | 🔨 Built; final run before submitting | 94 spoken situations in 22 areas, Andy's real profile and its 38 tools, judged by Nemotron 3 Ultra: latest **92, 91, 94 of 94 as a Nebius Serverless Job** (2026-10-20). The scam check five ways, 54 real turns timed on the robot, the finder in simulation. Every run below and in [evals/results/](../evals/results/) |
| M9 | Ship | 🔨 In progress | The Reachy Mini app packaged and passing Pollen's checker; the doctor and user services; a fresh clone installs and passes, and every command a judge is told to run works without keys or says what it needs (audited 2026-10-20). Left: the name, the history rewrite, the repository public, the app and the Space published |
| M10 | Video and submission | 🔨 Prepared | The shot list ([video.md](video.md), 2:54 with a 72 s uncut take), the Devpost text ([submission.md](submission.md)) and the feedback ([feedback.md](feedback.md)) ready; filming 2026-10-24 to 10-26 |

## Accounts and keys

| What | State |
|---|---|
| Devpost registration | ✅ 2026-10-13 |
| Nebius Token Factory | ✅ Individual account, zero data retention on, key in `~/.config/companion-hackathon/.env` |
| Tavily | ✅ Key saved and tested; pay-as-you-go since 2026-10-14 (the free 1,000 monthly credits ran out on 2026-10-14) |

## Measurements

| Date | What | Result |
|---|---|---|
| 2026-10-20 19:25 | Judging without a robot (round 9): a fresh clone from GitHub, 855 tests; the robot's environment 862; the Space's image built and run in Docker (every page 200, writes 403, the film on the front page); the simulation's film made with live model calls (found, 1.4° from the duck) | The demo's front page plays `sim-search.mp4`; the TV demo's keys scene and the waving drawing checked in a browser |
| 2026-10-20 19:10 | The finder in simulation as two Nebius Serverless Jobs (`cloud/sim-job.sh`, decision 0013): Pollen's MuJoCo scene, a glasses-sized duck at random places, 30 trials each, software rendering | Zoomed in with the closer look: pointed 18 of 23 (58–90%), **false finds 0 of 7**, error median 0.76°; the old way: 19 of 23, **3 of 7**, 2.73°. On this computer's GPU: 21 of 23, 0 of 7, 0.8° against 23 of 23, 1 of 7, 1.5° |
| 2026-10-20 17:11 | Zooming in at the desk (`evals/zoom_check.py`): a real pair of reading glasses in a CC0 room photo, 9 frames with them, 9 painted out | Old way (768 px) **0 of 9**; six full-size tiles **9 of 9**, no false sighting; closer look confirmed 8 of 9, wrongly 0 of 9; 24 tiles at once 1.8 s |
| 2026-10-20 16:14 | The eyes side by side at the desk (`evals/eyes_check.py`, same pictures, three runs each) | Super VL on Token Factory: describe median 1.35 s, four views 2.08 s; Nano VL on our endpoint: 3.45 s and 2.28 s (3.69 s cold); both right on all four views; the endpoint stopped after |
| 2026-10-20 20:01 | Suite as a Nebius Serverless Job, 94 cases (version 2026-10-20c: photo stories, places, taught moves) | **92, 91, 94 of 94**; once each: act-2 and think-1 (no tool called), share-2 (shared without reading the message back), crisis-3 (no "someone you trust"), photo-4 (read as a letter); [scorecard](../evals/results/2026-10-20-nebius-job-andy-suite-20261020-195645.json). The bundle moved from gzip to xz to stay under the 64 KB limit |
| 2026-10-20 15:59 | Suite, 89 cases (version 2026-10-20a, photo stories added), Andy, on this computer | **87, 88, 86 of 89**; photo-1 to photo-4 12 of 12; once or twice each: share-2 (2), greet-1 (2), story-1, chat-2, all seen varying before |
| 2026-10-20 15:57 | The eyes at the desk, Nemotron 3.5 Super VL on Token Factory, reasoning off (`evals/eyes_check.py`): Andy's TV screenshot, and a public-domain still life cut into four views for "glasses" | Describe 1.46–1.51 s; four views at once 1.98–2.22 s; seen in the two views with the glasses, not in the two without, all three runs |
| 2026-10-20 15:52 | The scam check's no-model baseline: Andy's letter rules on the same 120 messages | **28 of 60 caught, 3 of 60 flagged** (held out: 6 of 20, 1 of 20); one check costs about $0.017 (Tavily $0.016, Nemotron $0.0006), measured on four messages |
| 2026-10-20 15:50 | Turn timings on the Reachy Mini from Andy's own log, 2026-10-14 to 10-18 (`evals/robot_timings.py`, numbers only) | 54 turns: first sound **median 1.06 s** after the words are understood, p90 1.88 s, p95 3.24 s, slowest 5.23 s; the reply started at a median 0.94 s (62 turns) |
| 2026-10-14 22:35 | Suite, 85 cases (version b), Andy, on this computer, after the fixes below | **84, 85, 83 of 85**; once each: crisis-3 (in Spanish, no "someone you trust", and *tú*), share-2 (asked what to say, a known flaky case), greet-1 (three sentences) |
| 2026-10-14 22:10 | Suite, 85 cases, Andy, on this computer, a regression check before the freeze | **82, 83, 82 of 85**; look-1 failed 3 of 3 (searched now as well as look_into), pace-2 2 of 3 (no set_volume for "I can't hear you"), money-5 read an instruction aloud. Fixed in the profile and look_into's description: the five cases then 15 of 15 |
| 2026-10-14 12:25 | Andy and the voice server as user services (`andy.service`, `andy-voice.service`, installed, not started at login) | Health check 16 of 18 (the two endpoints stopped on purpose); the voice server on GPU 1 with no key on its command line; no conversation text in the journal |
| 2026-10-14 12:00 | Scam check, 120 messages (40 held out), Tavily once per message, the models three times as four Nebius Serverless Jobs (`cloud/scam-job.sh`) | **Andy (Tavily + Ultra): 58 of 60 scams, 0 of 60 ordinary flagged**; Ultra alone 55.7, 0; Lightning alone 53.3, 0; Tavily + Lightning 60, but 24 flagged. Held out: 19 of 20 against 18. Source named in 170 of 174. Missed: a landlord's changed bank account, and a name-only text ("Margaret?"). 17 Ultra-alone answers stalled in its JSON (feedback) |
| 2026-10-13 23:03 | Suite as a Nebius Serverless Job, 81 cases (version x) | **79, 79, 79 of 81**; think-1 failed 3 of 3 (asked instead of calling think_it_through; called the person "Andy" unprompted), fixed: 4 of 4 after, with name-1 added |
| 2026-10-13 22:30 | Suite, 80 cases (jokes, stories, keeping company, on this day), Andy, on this computer | **77, 77, 77 of 80**; money-4 regressed (a question before the scam warning), fixed: money, sharing and company areas 15, 15, 15, 14 of 15 after. The final Nebius Serverless Job run comes before submitting |
| 2026-10-13 21:21 | Suite as a Nebius Serverless Job, 67 cases (three letter cases; tool cases judged on the reply; must-not-say words in code) | **64, 66, 66 of 67**; locally 64, 65, 67. share-2 failed 3 of 6 across both (Andy asked the person's name before sharing); after the profile said "theirs included", 1 failure in 11 runs. An example sentence in the profile was tried and removed: it made Andy offer to share unasked (share-1 failed 5 of 6) |
| 2026-10-13 | Lightning tool call by API (`set_reminder`) | Correct arguments, 0.63–0.76 s, no reasoning text |
| 2026-10-13 18:35 | On the robot, the founder: the new greeting, talking over Andy, the hood page | Greeting heard ("Good evening! I'm Andy, your robot companion…", 4.7 s of speech). Talked over Andy: he stopped and listened; the hood page counted 1 interruption, 1.6 s of reply cut. Median 1.04 s from the end of the words to Andy's first sound (2 turns, one with `day_plan`). The founder reported everything working |
| 2026-10-13 18:10 | Suite as a Nebius Serverless Job, 57 cases (files sent as one bundle) | **56, 56, 55 of 57**; the dizziness case passed 3 of 3 after a more concrete rule (the earlier job's scorecard file was saved empty and is removed, so its numbers aren't quoted) |
| 2026-10-13 | Nemotron 3.5 Content Safety on a Nebius Serverless Endpoint (L40S, vLLM 0.20.2), 32 written sentences | With our policy: tuning 8/8, **held-out 7/8 caught, 0/8 false alarms**; standard categories 5/8 and 5/8; median about 0.55 s from Florida; both addresses 401 without the token; stopped after the test |
| 2026-10-13 | Crisis cases (5), before and after the crisis rule and net | Before: "better off without me" got no crisis line 2 of 3, the Spanish case 3 of 3, and replies opened with "I can't keep you safe". After: **15 of 15**; grief and "dying to see" untouched. Full suite **57, 56, 56 of 57** |
| 2026-10-13 | Suite, 52 cases (web answers that become actions with a yes; what Andy remembers), Andy | **52, 52, 51 of 52**. Two more harness flaws found and fixed (words said with a tool call stopped the turn; a one-kind scam stand-in misled the lottery case). What Andy remembers is now in its instructions from the start |
| 2026-10-13 | Suite, 49 cases, the robot's real 27 tools, Andy | **49, 48, 48 of 49**. With the real tools the suite found: no camera claimed (fixed in the profile), a time invented (fixed), a harness flaw in remind-3 (fixed), and the net answering a Spanish speaker in English (fixed). A broad "always call the tool first" block was tried and removed: it made Andy speak as the person's son (3 of 3) |
| 2026-10-13 | Suite, 44 cases including 5 in Spanish, Andy | **44, 44, 44 of 44**. The harness now finishes tool turns as the robot does (up to three steps), so a reply after a tool is judged |
| 2026-10-13 | Nemotron Nano 12B v2 VL on a Nebius Serverless Endpoint (L40S) | 3.5 s per description, accurate on Andy's own screen and family page; weights 14.3 GB downloaded in 4.7 min; first start about 15 min; plain IP and HTTPS both 401 without the token |
| 2026-10-13 | Suite (39 cases, with consent-based moments), Andy | **39, 39, 39 of 39**; the judge now sees earlier turns; read_letter limited to paper held up |
| 2026-10-13 | Suite as a Nebius Serverless Job (cpu-d3, eu-west2) | 33, 35, 33 of 36 (model alone); chest pain failed once with no words at all |
| 2026-10-13 | Suite, Andy (model + net) after fixing the net's patterns | 34, 35, 34; chest pain passed 3 of 3 through the net. The run exposed a gap in the net: "my chest has been hurting" was not matched; fixed and tested |
| 2026-10-13 | Conversation suite, Nemotron 3.5 Lightning judged by Nemotron 3 Ultra | Baseline 27/36. After fixing 3 flawed test cases (recorded in the suite) and 6 profile weaknesses (money and PINs, emergencies, day plan, look-up versus events, quoted messages, repeating more simply): 35, 36, 36 over three runs; median reply 0.76 s |
| 2026-10-13 | Tavily calls, live | Local news 5.9 s (2 from a local public radio site); look-up 1.4 s; what's on 3.3 s; read a link 0.2 s; grandparent-scam message: 3 FTC and 1 AARP warnings. `safe_search` needs `basic` depth |
| 2026-10-13 | Reminder test on the robot | Set by voice, listed, said unprompted when due. Andy also chose a `dance` nod and an emotion to confirm, which moved the head hard: movement tools removed from the profile |
| 2026-10-13 | On the Reachy Mini Lite, 9 spoken turns | Parakeet 0.02–0.08 s; Lightning 0.62–0.83 s; first audio 0.10–0.33 s; no errors; interruptions handled; nod, remember and forget worked |

## Open problems

- The robot is named after the person most likely to be spoken to near it in this household (the founder). While quiet, only "Andy, wake up" ends it (fixed 2026-10-13); while awake, Andy still answers anyone in the room, so a call or meeting near the robot should be held with Andy quiet or asleep.

- The new way the endpoint scripts store their tokens (Nebius MysteryBox secrets, 2026-10-14) is tested
  against a stand-in for the Nebius CLI only; the next `cloud/vision-endpoint.sh create` proves it. The
  endpoints that exist were made the old way, with the token in their start arguments; recreating them
  clears that.
- The recorded 911 and crisis sentences (2026-10-14) have not yet been played on the robot (live test).
- **The robot itself (2026-10-20):** Pollen's daemon reported "Motor communication error! Check connections and
  power supply"; the founder reconnected the USB the same evening, the daemon is running again and Andy woke.
- Letters in Spanish need `tesseract-ocr-spa` installed (the founder's, with sudo).

- `scripts/andy-sim` (Andy without a robot, Pollen's `--mockup-sim`) is not verified: on this desktop the
  robot's own USB camera and microphone are plugged in, and the pretend robot's media server failed on them
  (2026-10-14, two tries, the real robot restored after each). It needs a try on a computer without the
  robot; until then the README calls it experimental.

The live test of everything built today is [live-test.md](live-test.md).
