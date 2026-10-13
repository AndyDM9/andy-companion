# Status

**Last updated 2026-10-13.** Update this file in the same commit as any change it describes.
The plan and its milestones are in [PLAN.md](PLAN.md).

## At a glance

| # | Milestone | State | Notes |
|---|---|---|---|
| M0 | Andy talks through Nemotron | ✅ Done 2026-10-13 | Measured below |
| M1 | Clock and reminders | ✅ Done 2026-10-13 | Verified on the robot: "Good afternoon" from the clock; a reminder set by voice, listed, and said unprompted when due |
| M2 | Privacy floor | ✅ Done 2026-10-13 | Verified live: 0 conversation lines in the app log, tool arguments `[not logged]`, 0 transcript prints from the voice server; remember/forget write Andy's own owner-only `memory.json`. Tests: `tests/test_privacy.py` |
| M3 | Body behaviours | ✅ Done 2026-10-13 | Verified by the founder on the robot: looking at the person while speaking, following when they move; sleep, quiet and wake; a due reminder wakes Andy |
| M4 | The day, the same way every time | ✅ Done 2026-10-13 | Verified on the robot: today's plan, slow pace and louder volume remembered, exact spoken controls |
| M5 | Tavily | 🔨 Built, awaiting the live test | `local_news` (chosen local papers first, source named), `look_up`, `whats_on` (the city's calendar page, then a dated search), `read_link`, `check_message` (consumer-protection sites only; numbers, links and emails never sent). Live: news 5.9 s, look-up 1.4 s, events 3.3 s, link 0.2 s, scam check found FTC and AARP warnings. 140 tests |
| M6 | Eyes | 🔨 In progress | Vision endpoint created on Nebius (L40S, eu-north1, vLLM 0.30.0, Nemotron Nano 12B v2 VL FP8), starting; `describe_view` built and tested. Built, awaiting the live test: `read_letter` (sharpest of three frames, Tesseract on this computer, only the text reaches the model; a real Tesseract read passes in tests). To do: describing the camera picture with a Nemotron vision model on a Nebius Serverless Endpoint (needs a Nebius AI Cloud account) |
| M7 | Andy's screen and the family page | 🔨 Built, awaiting the live test | The screen (a day clock that takes the colour of the time of day; today's reminders, the next in green; what Andy is showing, with sources; fits a TV without scrolling) and the family page (only what the person shared; send Andy a message or a link; the person hears who looked). Private links with tokens; screenshots in `docs/images/`. 159 tests |
| M8 | Proof | 🔨 In progress | `evals/`: 36 spoken situations in 14 areas, Andy's real profile and tools, judged by Nemotron 3 Ultra. Baseline 27/36; after fixing 3 flawed cases and 6 profile weaknesses, 35, 36, 36 over three runs (`evals/results/`). To do: run it as a Nebius Serverless Job; a deterministic net for urgent words (chest pain passed 2 of 3) |
| M9 | Ship | 🔨 In progress | Andy runs in its own robot environment (`robot/`, Pollen's app 1.0.1, no longer the earlier assistant's); README rewritten for judges (features, NVIDIA and Nebius use, measurements, privacy, setup). To do: fresh-clone setup check, history scan for keys, Reachy Mini app packaging, make the repository public after the name decision |
| M10 | Video and submission | ⏳ | Registered on Devpost 2026-10-13 |

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
| 2026-10-13 | Conversation suite, Nemotron 3.5 Lightning judged by Nemotron 3 Ultra | Baseline 27/36. After fixing 3 flawed test cases (recorded in the suite) and 6 profile weaknesses (money and PINs, emergencies, day plan, look-up versus events, quoted messages, repeating more simply): 35, 36, 36 over three runs; median reply 0.76 s |
| 2026-10-13 | Tavily calls, live | Local news 5.9 s (2 from wlrn.org); look-up 1.4 s; what's on 3.3 s; read a link 0.2 s; grandparent-scam message: 3 FTC and 1 AARP warnings. `safe_search` needs `basic` depth |
| 2026-10-13 | Reminder test on the robot | Set by voice, listed, said unprompted when due. Andy also chose a `dance` nod and an emotion to confirm, which moved the head hard: movement tools removed from the profile |
| 2026-10-13 | On the Reachy Mini Lite, 9 spoken turns | Parakeet 0.02–0.08 s; Lightning 0.62–0.83 s; first audio 0.10–0.33 s; no errors; interruptions handled; nod, remember and forget worked |

## Open problems


- None open.
