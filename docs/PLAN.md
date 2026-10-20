# Plan

**Goal:** win the Nebius x NVIDIA Global AI Hackathon with a companion robot that a judge would want in
their own parent's home. A project wins one Overall award, or one track award and one bonus award, never
both (rules, section 8), so we aim for the Grand Prize, and the same work serves the Physical AI track with
Best Use of Tavily.

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
| Technological implementation | Five NVIDIA models across three Nebius products (Token Factory, two Serverless Endpoints, Serverless Jobs); Nemotron answering in 0.6 to 0.8 s, each turn timed on screen; the conversation suite and the scam check measured as Nebius Jobs; tested tools; rules in code between the model and the body |
| Design ("a complete product, not a proof of concept") | The person's side (voice and robot) **and** the family's side (a phone page); setup in a few commands; a published Reachy Mini app |
| Potential impact | A real person and a real problem: older adults living at home, and the family who help. Honest wording, nothing claimed that is not measured |
| Quality of the idea | A companion that says it is a robot, never imitates a person, never stores what it hears, and lets the person decide what family sees; a language model that moves the robot to find things; a scam check where the web finds the trick and a strong model tells it from the topic, measured both ways |

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
| M8 | **Proof** | A conversation test suite run as a Nebius Serverless Job, judged by Nemotron Ultra; scorecard in the README | 2026-10-23 · 🔶 built; Nebius Job 79/79/79 of 81; the scam check four ways as Nebius Jobs (2026-10-14); final suite run 2026-10-23 |
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
| B3 | **A scam-check evaluation with real Tavily calls**: about 30 scam messages and 30 genuine ones, warnings found with and without Tavily, run as a Nebius Job; published | Makes the Tavily bonus undeniable (the review's ask) | ✅ 2026-10-14: with Tavily 39/40 scams (9/10 subtle, against 7 alone), 0/40 ordinary flagged, 38/39 sourced |
| B4 | **Tavily `map` at setup**: find the town's events page from its website automatically | Tavily's fifth capability, in real use | ✅ 2026-10-14: live, harborbayfl.gov/Parks-Recreation/Events found in 3.8 s (the site refuses crawlers, so a search within it) |
| B5 | **Greeting on arrival**: "Welcome back" when someone is seen after a long absence, at most every few hours, a setting to turn it off; speech only, no head movement | ElliQ and Lovot's most-liked behaviour | ✅ 2026-10-14 (`speaker.welcome_back`; greet-1 4 of 4) |
| B6 | **The cost per household**, with dated prices, in the README and Devpost text | Potential impact: "what does it cost to run?" | ✅ 2026-10-14 ([cost.md](cost.md): about $2.30 a month) |
| B7 | **NVIDIA Magpie TTS**, evaluated beside Qwen3-TTS: time to first audio, the Spanish voice; switched only if as fast and the founder approves | Every model in the speech loop NVIDIA's | ✅ evaluated 2026-10-14: **not switched**; a short sentence takes 0.6 to 0.8 s before any sound (no streaming) against 0.10 to 0.33 s now. Samples in `voice/magpie-eval/out/` for the founder to hear |
| B8 | **The body language, safely**: test with the founder whether head motion during listening reaches the microphones; if so, move only while Andy speaks | Built and switched off on 2026-10-13 | ⬜ (needs the founder at the robot) |

### Round 2 (Claude), from the audits and research of 2026-10-14

A code and integration audit, a submission audit against the rules and criteria, and new research
(competitors, judges, prizes) found what follows. One rule shapes the aim: a project wins **one Overall
award, or one track award and one bonus award**, never both, so we build for the Grand Prize and the
same work serves the Physical AI track and the Tavily bonus.

| # | Item | Why | Status |
|---|---|---|---|
| B9 | **The audit's fixes:** the events finder's key in the supervisor; "what's on" falling back when a crawl fails; the urgent-words net (negations, and a spoken fallback when the model is down); consent asked for properly; "forget" deleting only what was meant; Andy never starting to speak over the person; secrets off every command line; the hood page's own token; endpoints that fail fast when stopped; the dashboard app's settings | Each could fail on camera or for a judge | ✅ 2026-10-14 (130 more tests); the new Nebius secret calls are proved at the next endpoint `create` |
| B10 | **The scam evaluation, fair and repeated:** a third arm (Nemotron 3 Ultra without Tavily), three runs each as a Nebius Serverless Job, and about 20 new messages modelled on this month's consumer-protection alerts, where finding recent warnings should matter | Today's gain (39 against 36) mixes Tavily with a second model and is one run; a rival scam entry exists | ✅ 2026-10-14: four arms, 120 messages (40 held out), three runs as Nebius Jobs: Andy 58 of 60, 0 flagged; Ultra alone 55.7; Lightning 53.3; Tavily + Lightning 60 but 24 flagged |
| B11 | **The finder measured:** about 25 recorded sweeps with known answers, run as a Nebius Serverless Job; accuracy and time to point | Robotics judges ask "how well does it work?"; Nebius presents Serverless Jobs for physical AI | 🔨 built 2026-10-14 (`ANDY_FINDER_RECORD`, `evals/finder_eval.py`); the founder records about 25 tries (1.5 h). The frames are too big for a job's 64 KB, so it is scored on this computer |
| B12 | **"How Andy found this"** on the screen: which Tavily call, depth, credits and time under each web answer (the sources were already named) | Shows the Tavily judges the integration plainly | ✅ 2026-10-14 (look-ups, news, what's on, scam checks, research) |
| B13 | **Privacy in four plain answers** (where it's heard, what's kept, who sees it, how to delete) in the README, the Devpost text and the video's last shot | The question every review of a home robot asks | ✅ 2026-10-14 (README, Devpost text, the video's last shot) |
| B14 | **The Devpost text and video script rewritten:** the robot first, a dated problem line, "What's new here", finding the glasses as an uncut take, talking over Andy in the long take, Tavily named in the opening, Spanish moved to a social clip | The submission audit's weakest criterion was the idea's sharpness | ✅ 2026-10-14 |

Also done on 2026-10-14, after round 2:

| # | Item | Status |
|---|---|---|
| B15 | Andy and the voice server as user services on the desktop (restart on failure; the stop through the supervisor) | ✅ |
| B16 | Spanish: spoken controls, saved days, Spanish pages first for news and events, letters in Spanish once `tesseract-ocr-spa` is installed | ✅ (waking from sleep stays English) |
| B17 | Ready for the clips and the final cut: draft captions with Parakeet (Spanish put into English, marked to check) and GIFs | ✅ |
| B18 | A fresh clone installs and passes as the README says; the keyless demo screen runs with an empty home folder | ✅ |

### Round 3 (Claude), from the design review of all four pages (2026-10-14, late evening)

The review's high and medium findings were done the same night (B15 to B18 above, and the changelog). The
founder approved its ideas; these turn the physical and the web work into things a viewer can see:

| # | Item | Why | Status |
|---|---|---|---|
| B19 | **"What Andy looked at":** after a search for something, the TV shows the four views Nemotron Nano VL read, left to right as Andy turned, the chosen one marked, for two minutes, in memory only | Makes the robot's physical search visible in one glance: the Physical AI track's point | ✅ 2026-10-14 (tested in a browser on the demo; on the robot in the live test) |
| B20 | **The scam check's receipt:** under "Be careful", three steps on the TV: the sign Nemotron Lightning spotted (with the message's own words), the consumer-protection warning Tavily found (and its site), and why Nemotron Ultra judged it the same trick | Shows the Tavily judges, and anyone, why Andy said what it said | ✅ 2026-10-14 (tested in a browser on the demo; on the robot in the live test) |
| B21 | **A family suggestion the person accepts:** on the family page, "Suggest a reminder" (what, when); Andy says "Anna suggested: call the pharmacy at 3 pm. Shall I set it?", and sets it only after a yes | Family help without taking over: nothing is set behind the person's back | ✅ 2026-10-14 (tested in a browser on the demo; on the robot in the live test) |
| B22 | **Family notes on the TV:** when Andy passes on a family message, the TV shows it as a note with who sent it and when, for five minutes | What Nest Hub's Family Notes do, inside our rules (no presence shown back) | ✅ 2026-10-14 (tested in a browser on the demo; on the robot in the live test) |
| B23 | **The rest of the review's ideas:** Tavily research with a running count of sites read; "Andy is looking at…" on the TV from the head's pose | Smaller; done if B19 to B22 land cleanly | ✅ 2026-10-14 (tested in a browser on the demo; on the robot in live test 3w) |

### Round 4 (Claude), from Devpost's judging session (2026-10-20)

The judges, two of them our track's NVIDIA judges, said what they look for: a live link they can click,
the aha in under two minutes, onboarding, a baseline beside every number, local models in physical AI,
limits published (they called it rigour), accessibility called out up front, one story rather than many
integrations, and real users. The notes are kept privately. Code before the freeze on 2026-10-22; words
until submission.

| # | Item | Why | Status |
|---|---|---|---|
| B24 | **The scam receipt says what to do first:** "Don't reply, pay or give any details. Check with family first." above the three steps | The judges' main note on a scam checker they reviewed: the action was below the evidence | ✅ 2026-10-20 (tested in a browser on the demo; on the robot in live test 3x) |
| B25 | **"Try asking…" on the TV:** when nothing is showing in the day, one thing to ask Andy at a time ("Where did I leave my glasses?"), in the household's language; settings can turn it off | Onboarding: a person, a relative or a judge sees what Andy can do without being told | ✅ 2026-10-20 (tested in a browser on the demo; on the robot in live test 3x) |
| B26 | **A public demo of the screens:** `demo_screen.py --public` serves the four pages read-only (nothing a visitor types reaches anyone else), with a Dockerfile for a Hugging Face Space | Every project the judges reviewed had a link they clicked through; ours needed `uv sync` | ✅ 2026-10-20 (the image built and run in Docker, writes refused; the Space itself is the founder's, 6.18) |
| B27 | **Accessibility, up front:** a section in the README and on Devpost | The judges: it counts if it is called out, and it gets missed otherwise | ✅ 2026-10-20 (README and Devpost text) |
| B28 | **What doesn't work yet:** the limits, in one section of the README and on Devpost | The judges: published limits read as rigour | ✅ 2026-10-20 (README and Devpost text) |
| B29 | **What runs where, and why that model:** this computer (hearing, speaking, waking, reading, following, with GPU memory and timings) and Nebius (each model, why that size, the number behind it) | The NVIDIA judges look for local models in physical AI and trade-offs between model sizes | ✅ 2026-10-20 (README and Devpost text; GPU memory measured) |
| B30 | **A chart of the scam check four ways** (scams caught, ordinary messages flagged), drawn from the scorecard, for the README and the Devpost gallery | A number reads as real against its baseline | ✅ 2026-10-20 (`scripts/make_charts.py`; SVG in the README, PNG for the gallery) |
| B31 | **The Devpost text, one story:** three moments first, the rest in one short list; "what we learned about the problem"; how Andy differs from a paste-in checker (you say it or hold it up; measured on ordinary messages); shorter sentences | The judges warned against many integrations without one story, and against "AI slop" | ✅ 2026-10-20 (the founder reads it before the draft goes in, 10-22) |

### Cleanup (Claude)

| # | Item | Status |
|---|---|---|
| C1 | gitleaks over every commit; a fresh-clone install from GitHub once public | 🔶 gitleaks: 108 commits, no leaks (2026-10-14); a fresh clone of the private repository installs and passes (2026-10-14); again once public |
| C2 | Remove dead code (the review's three unused imports); mark finished milestones done in this file | ✅ 2026-10-14 (four unused imports removed; ruff's error and bug checks pass) |
| C3 | The final Nebius Job run on 2026-10-23; its numbers into the README, the Devpost text and the video script in one commit | ⬜ (10-23) |
| C4 | Pin the Reachy Mini app's `andy-companion` dependency to the `hackathon-submission` tag | ⬜ (10-27) |

### The founder

| When | What | Where |
|---|---|---|
| Now | The live test on the robot | [live-test.md](live-test.md) |
| Now | **The body language test (B8)** with Claude watching the logs: the research says presence matters to at least one Physical AI judge | [live-test.md](live-test.md) 3u |
| This week | **One real session** with a relative who agrees to it in writing: about 20 unscripted minutes, one real moment for the video if they're willing, no claims about outcomes | founder action 6.17 |
| By 2026-10-23 | **Two or three short sessions with older adults** (a relative, a neighbour), each agreeing in writing: what they asked first, what confused them, what they'd change. Claude writes down only what they agree to, and what changed because of it. The judges' most repeated advice was to talk to real users | founder action 6.17 |
| After B26 | **The Hugging Face Space** for the public demo (the same account publishes the Reachy Mini app) | founder action 6.18 |
| This week | Say yes or no to B10's spend (about $3 to $6) | |
| Now | Photos and four 5-second clips of the real robot (the glance, following, finding glasses, the joke wiggle) | founder action 6.17 |
| About 2026-10-20 | The name; the repository public, licence in About; a Hugging Face account; Claude publishes the app | [submission-checklist.md](submission-checklist.md) |
| By 2026-10-22 | **A complete draft submitted** on Devpost (the early eligibility check) | [submission.md](submission.md), [feedback.md](feedback.md) |
| 2026-10-24 to 10-26 | Filming to the shot list; YouTube Public, "not made for kids", captions | [video.md](video.md) |
| 2026-10-27 | The live rules page re-read; the commit tagged `hackathon-submission`; submitted; posts | [rules-compliance.md](rules-compliance.md) |
| 2026-12-01 to 12-15 | Judging: the repository public at the tag; the robot ready if physical access is asked for | |

## The video

The shot list, rules and checklist are in [video.md](video.md) (rewritten 2026-10-14).

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
