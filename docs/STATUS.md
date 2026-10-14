# Status

**Last updated 2026-10-13.** Update this file in the same commit as any change it describes.
The plan and its milestones are in [PLAN.md](PLAN.md).

## At a glance

| # | Milestone | State | Notes |
|---|---|---|---|
| M0 | Andy talks through Nemotron | ✅ Done 2026-10-13 | Measured below |
| M1 | Clock and reminders | ✅ Done 2026-10-13 | Verified on the robot: "Good afternoon" from the clock; a reminder set by voice, listed, and said unprompted when due |
| M2 | Privacy floor | ✅ Done 2026-10-13 | Verified live: 0 conversation lines in the app log, tool arguments `[not logged]`, 0 transcript prints from the voice server (heard words included since 2026-10-13: every console in it is filtered, after a gap for Parakeet's own console was found and fixed); remember/forget write Andy's own owner-only `memory.json`. Tests: `tests/test_privacy.py` |
| M3 | Body behaviours | ✅ Done 2026-10-13 | Verified by the founder on the robot: looking at the person while speaking, following when they move; sleep, quiet and wake; a due reminder wakes Andy. Added 2026-10-13, awaiting the robot: the antennas lean while Andy thinks or a tool runs; Andy glances at the TV when something new shows on it (the screen's place set on the settings page, with a "Save and show me" check; verified by the founder on the robot 2026-10-13: 60° to the right was too far, 35° looked right at the monitor) |
| M4 | The day, the same way every time | ✅ Done 2026-10-13 (moments and Spanish day plan added, awaiting live test) | Added 2026-10-13: the plan is on the TV too, as a "Today" card (what is still to come, then today's moments), with the morning plan and "what's on today". Verified on the robot: today's plan, slow pace and louder volume remembered, exact spoken controls |
| M5 | Tavily | 🔨 Built, awaiting the live test | `local_news` (chosen local papers first, source named), `look_up`, `whats_on` (the city's calendar page, then a dated search), `read_link`, `check_message` (consumer-protection sites only; numbers, links and emails never sent). Live: news 5.9 s, look-up 1.4 s, events 3.3 s, link 0.2 s, scam check found FTC and AARP warnings. 140 tests. Added 2026-10-13: `look_into` (Tavily research, streamed; each step on the TV; the answer spoken later with sources: live 46 s, a dated answer from harborbayfl.gov), scam checks at advanced depth (basic found nothing on a prize scam, advanced found four AARP/FTC warnings), `X-Project-ID` on every request and this month's credits on `/hood` |
| M6 | Eyes | 🔨 Built, awaiting the live test on the robot | Added 2026-10-13: a letter read becomes a large-print card on the TV (`letters.py`; Lightning with a strict schema, 0.73–0.97 s live on five sample pages; warnings, no dose, numbers masked, in code). Vision endpoint on Nebius (L40S, eu-north1, vLLM 0.30.0, Nemotron Nano 12B v2 VL FP8): accurate descriptions in 3.5 s; both addresses refuse requests without the token (401). Stopped when idle (`cloud/vision-endpoint.sh start` before a test or filming, `stop` after). `describe_view`, `describe_photo` and `read_letter` (sharpest of three frames, Tesseract on this computer, only the text reaches the model) built and tested |
| M7 | Andy's screen and the family page | 🔨 Built, awaiting the live test (photos from family added) | The screen (a day clock that takes the colour of the time of day; today's reminders, the next in green; what Andy is showing, with sources; fits a TV without scrolling) and the family page (only what the person shared; send Andy a message or a link; the person hears who looked). Private links with tokens; screenshots in `docs/images/`. 159 tests. Added 2026-10-13: the setup page from a phone, with Andy telling the person who changed what. Redesigned 2026-10-13 from research (Echo Show, Nest Hub, ElliQ, MagicMirror², WAI): a live state strip, Next with a countdown, the weather in view, one found card with sources, two-line captions, family photos when idle, a calm night clock, every colour 7:1; the settings hub on a phone (what Andy keeps, deletable; the settings code on the TV); the hood page's live pipeline and health tiles. "Andy Glass" the same day: frosted glass panels over slow drifting light, a state orb that breathes and rings, cards that rise in, a calm setting with no motion or see-through; contrast tested against the worst glow and photo behind each panel |
| M8 | Proof | 🔨 Built; final run near submission | `evals/`: 57 spoken situations in 17 areas (5 said in Spanish), Andy's real profile, exactly the robot's 27 tools (`evals/tools.json`) and the urgent-words net, judged by Nemotron 3 Ultra. Baseline 27/36; now 56, 56, 55 of 57 as a Nebius Serverless Job (eu-west2, 2026-10-13 18:10) and 57, 56, 56 on this computer (`evals/results/`). Live timings of every turn on the screen server's `/hood` page (built 2026-10-13, awaiting the live test). Known variation: about one different case fails per run (money-2, share-2, act-2, crisis-2 once each); Andy once saved a moment without asking in crisis-5, which that case does not judge. To do: the final rerun as a job before submitting |
| M9 | Ship | 🔨 In progress | Reachy Mini app packaged (`reachy_app/`; publish needs a Hugging Face account and a public repository). Doctor (10/10) and start-at-login services added. Andy runs in its own robot environment (`robot/`, Pollen's app 1.0.1, no longer the earlier assistant's); README rewritten for judges (features, NVIDIA and Nebius use, measurements, privacy, setup). To do: fresh-clone setup check, history scan for keys, Reachy Mini app packaging, make the repository public after the name decision |
| M10 | Video and submission | 🔨 Prepared | Registered on Devpost 2026-10-13. Shot list in `docs/video.md` (ten live shots, 2:45, words checked); draft Devpost texts in `docs/submission.md` |

## Accounts and keys

| What | State |
|---|---|
| Devpost registration | ✅ 2026-10-13 |
| Nebius Token Factory | ✅ Individual account, zero data retention on, key in `~/.config/companion-hackathon/.env` |
| Nebius Builder Program | Applied 2026-10-13; email verification pending |
| Hackathon Token Factory credit | Form sent 2026-10-13; code arrives by email |
| Tavily | ✅ Free plan, key saved and tested |

## Measurements

| Date | What | Result |
|---|---|---|
| 2026-10-13 | Lightning tool call by API (`set_reminder`) | Correct arguments, 0.63–0.76 s, no reasoning text |
| 2026-10-13 18:35 | On the robot, the founder: the new greeting, talking over Andy, the hood page | Greeting heard ("Good evening! I'm Andy, your robot companion…", 4.7 s of speech). Talked over Andy: he stopped and listened; the hood page counted 1 interruption, 1.6 s of reply cut. Median 1.04 s from the end of the words to Andy's first sound (2 turns, one with `day_plan`). Founder: "all working" |
| 2026-10-13 18:10 | Suite as a Nebius Serverless Job, 57 cases (files sent as one bundle) | **56, 56, 55 of 57**; the dizziness case, which had failed 3 of 3 on the job an hour earlier (54, 56, 56), passed 3 of 3 after a more concrete rule |
| 2026-10-13 | Nemotron 3.5 Content Safety on a Nebius Serverless Endpoint (L40S, vLLM 0.20.2), 32 written sentences | With our policy: tuning 8/8, **held-out 7/8 caught, 0/8 false alarms**; standard categories 5/8 and 5/8; median about 0.55 s from Miami; both addresses 401 without the token; stopped after the test |
| 2026-10-13 | Crisis cases (5), before and after the crisis rule and net | Before: "better off without me" got no crisis line 2 of 3, the Spanish case 3 of 3, and replies opened with "I can't keep you safe". After: **15 of 15**; grief and "dying to see" untouched. Full suite **57, 56, 56 of 57** |
| 2026-10-13 | Suite, 52 cases (web answers that become actions with a yes; what Andy remembers), Andy | **52, 52, 51 of 52**. Two more harness flaws found and fixed (words said with a tool call stopped the turn; a one-kind scam stand-in misled the lottery case). What Andy remembers is now in its instructions from the start |
| 2026-10-13 | Suite, 49 cases, the robot's real 27 tools, Andy | **49, 48, 48 of 49**. With the real tools the suite found: no camera claimed (fixed in the profile), a time invented (fixed), a harness flaw in remind-3 (fixed), and the net answering a Spanish speaker in English (fixed). A broad "always call the tool first" block was tried and removed: it made Andy speak as the person's son (3 of 3) |
| 2026-10-13 | Suite, 44 cases including 5 in Spanish, Andy | **44, 44, 44 of 44**. The harness now finishes tool turns as the robot does (up to three steps), so a reply after a tool is judged |
| 2026-10-13 | Nemotron Nano 12B v2 VL on a Nebius Serverless Endpoint (L40S) | 3.5 s per description, accurate on Andy's own screen and family page; weights 14.3 GB downloaded in 4.7 min; first start about 15 min; plain IP and HTTPS both 401 without the token |
| 2026-10-13 | Suite (39 cases, with consent-based moments), Andy | **39, 39, 39 of 39**; the judge now sees earlier turns; read_letter limited to paper held up |
| 2026-10-13 | Suite as a Nebius Serverless Job (cpu-d3, eu-west2) | 33, 35, 33 of 36 (model alone); chest pain failed once with no words at all |
| 2026-10-13 | Suite, Andy (model + net) after fixing the net's patterns | 34, 35, 34; chest pain passed 3 of 3 through the net. The run exposed a gap in the net: "my chest has been hurting" was not matched; fixed and tested |
| 2026-10-13 | Conversation suite, Nemotron 3.5 Lightning judged by Nemotron 3 Ultra | Baseline 27/36. After fixing 3 flawed test cases (recorded in the suite) and 6 profile weaknesses (money and PINs, emergencies, day plan, look-up versus events, quoted messages, repeating more simply): 35, 36, 36 over three runs; median reply 0.76 s |
| 2026-10-13 | Tavily calls, live | Local news 5.9 s (2 from wlrn.org); look-up 1.4 s; what's on 3.3 s; read a link 0.2 s; grandparent-scam message: 3 FTC and 1 AARP warnings. `safe_search` needs `basic` depth |
| 2026-10-13 | Reminder test on the robot | Set by voice, listed, said unprompted when due. Andy also chose a `dance` nod and an emotion to confirm, which moved the head hard: movement tools removed from the profile |
| 2026-10-13 | On the Reachy Mini Lite, 9 spoken turns | Parakeet 0.02–0.08 s; Lightning 0.62–0.83 s; first audio 0.10–0.33 s; no errors; interruptions handled; nod, remember and forget worked |

## Open problems

- The robot is named after the person most likely to be spoken to near it in this household (the founder). While quiet, only "Andy, wake up" ends it (fixed 2026-10-13); while awake, Andy still answers anyone in the room, so a call or meeting near the robot should be held with Andy quiet or asleep.

The live test of everything built today is [live-test.md](live-test.md).


- None open.
