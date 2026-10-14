# Plan

**Goal:** win the Physical AI track of the Nebius x NVIDIA Global AI Hackathon, and Best Use of
Tavily, with a companion robot that a judge would want in their own parent's home.

**Deadline:** submissions close **2026-10-30, 10:00 PT**. We submit by **2026-10-27**.

**One sentence:** Andy is a small home robot for older adults who live at home, and the family
who help. It runs on a Reachy Mini, its brain is NVIDIA Nemotron on Nebius, and it keeps no recordings or transcripts of what
it hears.

Live progress is in [STATUS.md](STATUS.md). Every change is in [CHANGELOG.md](../CHANGELOG.md).
Decisions are in [decisions/](decisions/). What Devpost requires is in
[submission-checklist.md](submission-checklist.md).

## How we are judged, and what answers each criterion

Stage one is pass/fail: a genuine Physical AI project that really uses Nebius and an NVIDIA open
model. Stage two scores four criteria, equally weighted, 1 to 5.

| Criterion | What answers it |
|---|---|
| Technological implementation | Three or more NVIDIA models across three Nebius products (Token Factory, a Serverless Endpoint, a Serverless Job); sub-second replies measured on screen; tested tools; a safety layer between the model and the body |
| Design ("a complete product, not a proof of concept") | The person's side (voice and robot) **and** the family's side (a phone page); setup in a few commands; a published Reachy Mini app |
| Potential impact | A real person and a real problem: older adults living at home, and the family who help. Honest wording, nothing claimed that is not measured |
| Quality of the idea | A companion that says it is a robot, never imitates a person, never stores what it hears, and lets the person decide what family sees |

## Milestones

Each milestone is done only when its "done when" is true and STATUS.md and CHANGELOG.md say so.

| # | Milestone | Done when | Target |
|---|---|---|---|
| M0 | **Andy talks through Nemotron** | Voice server with Parakeet and Nemotron Lightning; Andy answers on the robot | 2026-10-13 ✅ · ✅ done 2026-10-13 |
| M1 | **Clock and reminders** | Andy knows the date and time; sets, lists and cancels reminders by voice; speaks a reminder when it is due, unprompted; tests pass | 2026-10-15 · ✅ done 2026-10-13 |
| M2 | **Privacy floor** | No conversation text in any log; Andy's memory in its own store; nothing stored except what the person asks | 2026-10-16 · ✅ done 2026-10-13 |
| M3 | **Body behaviours** | Andy keeps looking at the person while it speaks and while they move (gaze, body follow, seek, person finder), gentle idle moments, no confirmation moves, upward looks softened; chimes, quiet mode, wake word; each rewritten here from the earlier assistant's general-purpose modules, with tests | 2026-10-18 · ✅ done 2026-10-13 |
| M4 | **The day, the same way every time** | A day plan said on request and each morning; pace and volume settings that stick | 2026-10-19 · ✅ done 2026-10-13 |
| M5 | **Tavily** | Local news with sources named aloud; read a link a relative sends; what's on this week; look up a suspicious message; Tavily is the only web provider ([0002](decisions/0002-one-search-provider-tavily.md)) | 2026-10-20 · 🔶 built; live test, and Tavily credits (founder 6.3) |
| M6 | **Eyes** | A Nemotron vision model on a Nebius Serverless Endpoint describes the camera picture; **"Andy, read this letter for me"**: text read on the computer (Tesseract), then explained simply by Nemotron, with a Tavily lookup when a letter or message may be a scam | 2026-10-21 · 🔶 built, finding things tested on the live model; live test on the robot |
| M7 | **Andy's screen and the family page** | A screen beside Andy (TV or monitor) shows what Andy is talking about: the day, reminders, news with its source, a picture; and a phone page for family showing only what the person chose to share, with Andy saying who looked | 2026-10-22 · 🔶 built; live test |
| M8 | **Proof** | A conversation test suite run as a Nebius Serverless Job, judged by Nemotron Ultra; scorecard in the README | 2026-10-23 · 🔶 built; Nebius Job 79/79/79 of 81; final run 2026-10-23 |
| M9 | **Ship** | README with setup, architecture diagram, published Reachy Mini app, repository public | 2026-10-24 · 🔶 app ready; repository public about 2026-10-20 |
| M10 | **Video and submission** | Under three minutes, at least one minute of the robot live; Devpost form complete with the tool feedback | 2026-10-27 · 🔶 texts ready; filming 2026-10-24 to 10-26 |

## Road to October 30 (the deadline is 2026-10-30, 10:00 PT; a complete draft by 2026-10-22, final by 2026-10-27)

Planned 2026-10-14 from four reviews (a judge's-eye review, a claims audit, a code and privacy review,
innovation research) and the founder's test on the robot. The research is in [research.md](research.md).
**The rule for the last two weeks: reliability on camera comes before more features.** Feature freeze
2026-10-23; fixes only after.

### Build (Claude), in order

| # | Item | Why | Status |
|---|---|---|---|
| B1 | **A watchdog** in the supervisor: if one turn keeps reopening (a TV, a radio) or the microphone keeps dropping audio, restart Andy's app and log why; cap one turn's continuous speech | On 2026-10-13 Andy stopped answering in exactly these ways | ✅ 2026-10-14 (`watchdog.py`, `voice/serve.py` turn cap) |
| B2 | **A health check**, one command before filming or a demo: the voice server, the robot, both endpoints, Token Factory, Tavily, the screen, a test turn; green or red in plain words | Nothing should fail on camera that a minute's check would have caught | ✅ 2026-10-14 (`scripts/doctor.py --live`) |
| B3 | **A scam-check evaluation with real Tavily calls**: about 30 scam messages and 30 genuine ones, warnings found with and without Tavily, run as a Nebius Job; published | Makes the Tavily bonus undeniable (the review's ask) | 🔶 built and run (80 messages; `evals/scam_eval.py`, `scamcheck.py`); the final clean run waits for Tavily credits (founder action 6.3: the Builder Program's $25) |
| B4 | **Tavily `map` at setup**: find the town's events page from its website automatically | Tavily's fifth capability, in real use | 🔶 built and tested with stand-ins (`web.find_events_page`); the live check waits for Tavily credits, then the README and Devpost text name it |
| B5 | **Greeting on arrival**: "Welcome back" when someone is seen after a long absence, at most every few hours, a setting to turn it off; speech only, no head movement | ElliQ and Lovot's most-liked behaviour | ✅ 2026-10-14 (`speaker.welcome_back`; greet-1 4 of 4) |
| B6 | **The cost per household**, with dated prices, in the README and Devpost text | Potential impact: "what does it cost to run?" | ✅ 2026-10-14 ([cost.md](cost.md): about $2.30 a month) |
| B7 | **NVIDIA Magpie TTS**, evaluated beside Qwen3-TTS: time to first audio, the Spanish voice; switched only if as fast and the founder approves | Every model in the speech loop NVIDIA's | ✅ evaluated 2026-10-14: **not switched**; a short sentence takes 0.6 to 0.8 s before any sound (no streaming) against 0.10 to 0.33 s now. Samples in `voice/magpie-eval/out/` for the founder to hear |
| B8 | **The body language, safely**: test with the founder whether head motion during listening reaches the microphones; if so, move only while Andy speaks | Built and switched off on 2026-10-13 | ⬜ (needs the founder at the robot) |

### Cleanup (Claude)

| # | Item | Status |
|---|---|---|
| C1 | gitleaks over every commit; a fresh-clone install from GitHub once public | 🔶 gitleaks: 93 commits, no leaks (2026-10-14); the fresh clone from GitHub once public |
| C2 | Remove dead code (the review's three unused imports); mark finished milestones done in this file | ✅ 2026-10-14 (four unused imports removed; ruff's error and bug checks pass) |
| C3 | The final Nebius Job run on 2026-10-23; its numbers into the README, the Devpost text and the video script in one commit | ⬜ (10-23) |
| C4 | Pin the Reachy Mini app's `andy-companion` dependency to the `hackathon-submission` tag | ⬜ (10-27) |

### The founder

| When | What | Where |
|---|---|---|
| Now | The live test on the robot | [live-test.md](live-test.md) |
| Now | Photos and four 5-second clips of the real robot (the glance, following, finding glasses, the joke wiggle) | founder action 6.17 |
| About 2026-10-20 | The name; the repository public, licence in About; a Hugging Face account; Claude publishes the app | [submission-checklist.md](submission-checklist.md) |
| By 2026-10-22 | **A complete draft submitted** on Devpost (the early eligibility check) | [submission.md](submission.md), [feedback.md](feedback.md) |
| 2026-10-24 to 10-26 | Filming to the shot list; YouTube Public, "not made for kids", captions | [video.md](video.md) |
| 2026-10-27 | The live rules page re-read; the commit tagged `hackathon-submission`; submitted; posts | [rules-compliance.md](rules-compliance.md) |
| 2026-12-01 to 12-15 | Judging: the repository public at the tag; the robot ready if physical access is asked for | |

## The video (draft)

1. Morning: Andy wakes, greets, says the day and one local headline with its source.
2. A reminder Andy speaks on its own at the chosen time.
3. Andy remembers yesterday's mention of a granddaughter's recital and offers to send a note to
   the family, if the person wants.
4. A letter held up to Andy: read aloud, explained simply, and a suspicious one looked up
   together, "shall we ask your daughter?"
5. Boundaries: asked to be someone else, or for a medicine dose, it kindly declines.
6. Under the hood: the NVIDIA models and Nebius products named aloud, timings on screen.

## Words we use, and words we never use

We describe people by age and living situation: "older adults who live at home, and the family
who help". We never name a medical condition. We never say Andy keeps anyone safe, watches over
anyone, notices changes in a person, reduces loneliness, replaces a visit or a carer, or makes
sure anyone takes medicine. We never call people "seniors" or "the elderly". We show what Andy
does; we do not claim outcomes we have not measured.

## Risks

| Risk | What we do |
|---|---|
| Lightning's tool calls are weak on a hard turn | Fall back to Nemotron Super for that turn |
| Reasoning text spoken aloud | Thinking off; strip it in our wrapper if it ever appears |
| No NVIDIA vision model on serverless Token Factory | Self-host one on a Nebius Serverless Endpoint (M6) |
| The robot is shared with another app | Only one program drives the robot at a time; tests stop the other |
| Time | Milestones are in order of what the video needs; M6 and M8 can shrink without breaking the demo |
