# Plan

The build plan, kept as a record: what was planned, why, and when it was done.
Key: M = milestone, B = plan item, C = a step near submission, round N = one day's batch of work.

**Goal:** a companion robot a family would want in their own parent's home, entered in the Nebius x NVIDIA
Global AI Hackathon: the Physical AI track, and Best Use of Tavily. A project wins one Overall award, or one
track award and one bonus award, never both (rules, section 8).

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
| Technological implementation | Six NVIDIA models (Parakeet, Nemotron 3.5 Lightning, Nemotron 3 Ultra, Nemotron 3.5 Super VL, Nemotron 3.5 Content Safety, and Nemotron Nano 12B v2 VL as an option) across Token Factory, Serverless Endpoints and Serverless Jobs; Nemotron answering in 0.6 to 0.8 s, each turn timed on screen; the conversation suite and the scam check measured as Nebius Serverless Jobs; tested tools; rules in code between the model and the body |
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
| M5 | **Tavily** | Local news with sources named aloud; read a link a relative sends; what's on this week; look up a suspicious message; Tavily is the only web provider ([0002](decisions/0002-one-search-provider-tavily.md)) | 2026-10-20 · 🔶 built; live test (Tavily pay-as-you-go since 2026-10-14) |
| M6 | **Eyes** | A Nemotron vision model on a Nebius Serverless Endpoint describes the camera picture; **"Andy, read this letter for me"**: text read on the computer (Tesseract), then explained simply by Nemotron, with a Tavily lookup when a letter or message may be a scam | 2026-10-21 · 🔶 built, finding things tested on the live model; live test on the robot |
| M7 | **Andy's screen and the family page** | A screen beside Andy (TV or monitor) shows what Andy is talking about: the day, reminders, news with its source, a picture; and a phone page for family showing only what the person chose to share, with Andy saying who looked | 2026-10-22 · 🔶 built; live test |
| M8 | **Proof** | A conversation test suite run as a Nebius Serverless Job, judged by Nemotron Ultra; scorecard in the README | 2026-10-23 · 🔶 built; latest as a Nebius Serverless Job 96, 95, 92 of 97 (2026-10-25, [scorecard](../evals/results/2026-10-25-nebius-job-andy-suite-20261025-193648.json)); the scam check five ways, as Nebius Serverless Jobs (2026-10-14); the final run at submission |
| M9 | **Ship** | README with setup, architecture diagram, published Reachy Mini app, repository public | 2026-10-24 · ✅ done 2026-10-25: public, the Space public, the Reachy Mini app published ([andy-companion-app](https://huggingface.co/spaces/andydm/andy-companion-app)) |
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
| B3 | **A scam-check evaluation with real Tavily calls**: about 30 scam messages and 30 genuine ones, warnings found with and without Tavily, run as a Nebius Serverless Job; published | Measures what Tavily adds, against the same checks without it (the review's ask) | ✅ 2026-10-14: with Tavily 39/40 scams (9/10 subtle, against 7 alone), 0/40 ordinary flagged, 38/39 sourced |
| B4 | **Tavily `map` at setup**: find the town's events page from its website automatically | Tavily's fifth capability, in real use | ✅ 2026-10-14: live, the town's own .gov events page (`/Parks-Recreation/Events`) found in 3.8 s (the site refuses crawlers, so a search within it) |
| B5 | **Greeting on arrival**: "Welcome back" when someone is seen after a long absence, at most every few hours, a setting to turn it off; speech only, no head movement | ElliQ and Lovot's most-liked behaviour | ✅ 2026-10-14 (`speaker.welcome_back`; greet-1 4 of 4) |
| B6 | **The cost per household**, with dated prices, in the README and Devpost text | Potential impact: "what does it cost to run?" | ✅ 2026-10-14 ([cost.md](cost.md): about $2.30 a month) |
| B7 | **NVIDIA Magpie TTS**, evaluated beside Qwen3-TTS: time to first audio, the Spanish voice; switched only if as fast and the founder approves | Every model in the speech loop NVIDIA's | ✅ evaluated 2026-10-14: **not switched**; a short sentence takes 0.6 to 0.8 s before any sound (no streaming) against 0.10 to 0.33 s now. Samples in `voice/magpie-eval/out/` (not committed) for the founder to hear |
| B8 | **The body language, safely**: test with the founder whether head motion during listening reaches the microphones; if so, move only while Andy speaks | Built and switched off on 2026-10-13 | ⬜ (needs the founder at the robot) |

### Round 2 (Claude), from the audits and research of 2026-10-14

A code and integration audit, a submission audit against the rules and criteria, and new research
(competitors, judges, prizes) found what follows. One rule shapes the aim: a project wins **one Overall
award, or one track award and one bonus award**, never both; the same work serves the
same work serves the Physical AI track and the Tavily bonus.

| # | Item | Why | Status |
|---|---|---|---|
| B9 | **The audit's fixes:** the events finder's key in the supervisor; "what's on" falling back when a crawl fails; the urgent-words net (negations, and a spoken fallback when the model is down); consent asked for properly; "forget" deleting only what was meant; Andy never starting to speak over the person; secrets off every command line; the hood page's own token; endpoints that fail fast when stopped; the dashboard app's settings | Each could fail on camera or for a judge | ✅ 2026-10-14 (130 more tests); the new Nebius secret calls are proved at the next endpoint `create` |
| B10 | **The scam evaluation, fair and repeated:** a third arm (Nemotron 3 Ultra without Tavily), three runs each as a Nebius Serverless Job, and about 20 new messages modelled on this month's consumer-protection alerts, where finding recent warnings should matter | Today's gain (39 against 36) mixes Tavily with a second model and is one run; a rival scam entry exists | ✅ 2026-10-14: four arms, 120 messages (40 held out), three runs as Nebius Serverless Jobs: Andy 58 of 60, 0 flagged; Ultra alone 55.7; Lightning 53.3; Tavily + Lightning 60 but 24 flagged |
| B11 | **The finder measured:** about 25 recorded sweeps with known answers, run as a Nebius Serverless Job; accuracy and time to point | Robotics judges ask "how well does it work?"; Nebius presents Serverless Jobs for physical AI | 🔨 built 2026-10-14 (`ANDY_FINDER_RECORD`, `evals/finder_eval.py`); the founder records about 25 tries (1.5 h). The frames are too big for a job's 64 KB, so it is scored on this computer |
| B12 | **"How Andy found this"** on the screen: which Tavily call, depth, credits and time under each web answer (the sources were already named) | Shows how each web answer was found, plainly | ✅ 2026-10-14 (look-ups, news, what's on, scam checks, research) |
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
| B19 | **"What Andy looked at":** after a search for something, the TV shows the four views Nemotron Nano VL read (Super VL since decision 0011), left to right as Andy turned, the chosen one marked, for two minutes, in memory only | Makes the robot's physical search visible in one glance: the Physical AI track's point | ✅ 2026-10-14 (tested in a browser on the demo; on the robot in the live test) |
| B20 | **The scam check's receipt:** under "Be careful", three steps on the TV: the sign Nemotron Lightning spotted (with the message's own words), the consumer-protection warning Tavily found (and its site), and why Nemotron Ultra judged it the same trick | Shows anyone why Andy said what it said | ✅ 2026-10-14 (tested in a browser on the demo; on the robot in the live test) |
| B21 | **A family suggestion the person accepts:** on the family page, "Suggest a reminder" (what, when); Andy says "Anna suggested: call the pharmacy at 3 pm. Shall I set it?", and sets it only after a yes | Family help without taking over: nothing is set behind the person's back | ✅ 2026-10-14 (tested in a browser on the demo; on the robot in the live test) |
| B22 | **Family notes on the TV:** when Andy passes on a family message, the TV shows it as a note with who sent it and when, for five minutes | What Nest Hub's Family Notes do, inside our rules (no presence shown back) | ✅ 2026-10-14 (tested in a browser on the demo; on the robot in the live test) |
| B23 | **The rest of the review's ideas:** Tavily research with a running count of sites read; "Andy is looking at…" on the TV from the head's pose | Smaller; done if B19 to B22 land cleanly | ✅ 2026-10-14 (tested in a browser on the demo; on the robot in live test 3w) |

### Round 4 (Claude), from Devpost's judging session (2026-10-20)

Devpost's public judging session said what judges look for: a live link they can click,
the aha in under two minutes, onboarding, a baseline beside every number, local models in physical AI,
limits published (they called it rigour), accessibility called out up front, one story rather than many
integrations, and real users. Code before the freeze on 2026-10-22; words
until submission.

| # | Item | Why | Status |
|---|---|---|---|
| B24 | **The scam receipt says what to do first:** "Don't reply, pay or give any details. Check with family first." above the three steps | The judges' main note on a scam checker they reviewed: the action was below the evidence | ✅ 2026-10-20 (tested in a browser on the demo; on the robot in live test 3x) |
| B25 | **"Try asking…" on the TV:** when nothing is showing in the day, one thing to ask Andy at a time ("Where did I leave my glasses?"), in the household's language; settings can turn it off | Onboarding: a person, a relative or a judge sees what Andy can do without being told | ✅ 2026-10-20 (tested in a browser on the demo; on the robot in live test 3x) |
| B26 | **A public demo of the screens:** `demo_screen.py --public` serves the four pages read-only (nothing a visitor types reaches anyone else), with a Dockerfile for a Hugging Face Space | Every project the judges reviewed had a link they clicked through; ours needed `uv sync` | ✅ 2026-10-20 (the image built and run in Docker, writes refused; the Space itself is the founder's) |
| B27 | **Accessibility, up front:** a section in the README and on Devpost | The judges: it counts if it is called out, and it gets missed otherwise | ✅ 2026-10-20 (README and Devpost text) |
| B28 | **What doesn't work yet:** the limits, in one section of the README and on Devpost | The judges: published limits read as rigour | ✅ 2026-10-20 (README and Devpost text) |
| B29 | **What runs where, and why that model:** this computer (hearing, speaking, waking, reading, following, with GPU memory and timings) and Nebius (each model, why that size, the number behind it) | Judges in Devpost's public session asked for local models in physical AI and trade-offs between model sizes | ✅ 2026-10-20 (README and Devpost text; GPU memory measured) |
| B30 | **A chart of the scam check four ways** (scams caught, ordinary messages flagged), drawn from the scorecard, for the README and the Devpost gallery | A number reads as real against its baseline | ✅ 2026-10-20 (`scripts/make_charts.py`; SVG in the README, PNG for the gallery) |
| B31 | **The Devpost text, one story:** three moments first, the rest in one short list; "what we learned about the problem"; how Andy differs from a paste-in checker (you say it or hold it up; measured on ordinary messages); shorter sentences | The judges warned against many integrations without one story, and against "AI slop" | ✅ 2026-10-20 (the founder reads it before the draft goes in, 10-22) |

### Round 5 (Claude), from the gap research of 2026-10-20 (approved by the founder the same day)

What is missing is mostly evidence a judge can see, not features: the rules let judges score on the text,
images and video alone, and the strongest Physical AI entries count real trials with intervals. Two
build findings: Nemotron 3.5 Super VL is now on serverless Token Factory (tried 2026-10-20: 2.2 s to
describe a screen, no endpoint to start), and our scam numbers need intervals, a no-model baseline and a
cost beside them. Code before the freeze on 2026-10-22.

| # | Item | Why | Status |
|---|---|---|---|
| B32 | **Eyes on serverless Token Factory:** Nemotron 3.5 Super VL for describing, photos and finding things, by default (`ANDY_VISION`); the Nano VL endpoint stays as an option, and both are measured side by side | Always on, so "find my glasses" never fails because an endpoint is stopped; the newest NVIDIA vision model; a size trade-off measured | ✅ 2026-10-20 ([decision 0011](decisions/0011-the-eyes-on-token-factory.md); `evals/eyes_check.py`: describe 1.35 s against 3.45 s for Nano VL, four views 2.08 s against 2.28 s, both right; the hood page and the doctor name the eyes in use) |
| B33 | **The scam numbers with rigour:** 95% intervals on every figure, a no-model baseline (keyword rules on the same 120 messages, no credits), the cost per 1,000 checks; the chart and texts redrawn; said plainly that the gain over the models alone is no false alarms, not more scams caught | A number reads as real beside its baseline and its uncertainty | ✅ 2026-10-20 (word rules 28 of 60 caught, 3 flagged; Andy 58 (89–99%), 0 (0–6%); about $17 per 1,000; the chart, README and Devpost text redrawn; `andy_companion.measure`) |
| B34 | **The robot measured:** timings recorded on the robot during the live test (numbers only, never words: end of words to first sound, p50 and p95), and the finder scored from the founder's recorded tries on both vision models, with intervals and time to point | The track's bar is real trials with intervals; ours are all from the desk so far | 🔶 timings ✅ 2026-10-20 from Andy's own log: 54 real turns, median 1.06 s, 95% under 3.24 s (`evals/robot_timings.py`); the finder's `compare` built and tested, waiting for the founder's ~20 recorded tries |
| B35 | **Photo stories:** when a photo comes from family or is held up, Andy asks one question about it; the story is kept only with a yes, and shared to family only with a second yes | Being remembered is what older adults value most in robot studies; it strengthens the family story without adding breadth | ✅ 2026-10-20 (profile and the photo tool's guidance; suite photo-1 to photo-4, 12 of 12 in a full run of 87, 88, 86 of 89; live test 3y). Sharing stays only-when-asked: an earlier try showed that offering made Andy share unasked |
| B36 | **The local design, side by side with NVIDIA's Reachy Mini Jetson assistant:** what matches (frames taken only when the head is still, measured GPU memory), what differs, and what a Jetson port would need, as a plan, never a claim | Judges in Devpost's public session asked for local models in physical AI | ✅ 2026-10-20 (README, "Beside NVIDIA's Reachy Mini Jetson assistant", with the table in [jetson-comparison.md](jetson-comparison.md) since 2026-10-21; Devpost "What's next") |
| B37 | **Tavily session headers** (`X-Session-Id` per conversation) | Uses Tavily's newer request features; cheap | ✅ 2026-10-20 (random, renewed after 30 quiet minutes; `X-Human-Id` not sent, since one robot is one household's key; tried live) |
| B38 | **The story leads with the robot and the family:** the video opens on a physical moment (the letter held up, the head turning to the glasses), the scam verdict one beat of three | Web-only scam checkers are many; a robot in a real home is not | ✅ 2026-10-20 in words (`docs/video.md`: the first caption leads with the letter and the robot; shot 5 a photo story); the filming is the founder's |
| B39 | Stretch, only if B32 to B38 land by 10-22: **Cosmos Reason 2 2B on this computer** as the finder's third model and its offline fallback | A local NVIDIA model in the physical loop; needs the gated model accepted on Hugging Face | ✅ 2026-10-25, after all (the founder accepted both licences): Cosmos Reason 2 on this computer as the offline eyes, 2B and 8B measured in simulation ([decision 0015](decisions/0015-cosmos-on-this-computer-as-the-offline-eyes.md)) |

Not taken: music and radio (no copyrighted music in the video; after the hackathon), quizzes and movement
to music (breadth), video calls (the person's camera to family), sending a scam's number or the letter
itself to Tavily, Pollen's app 1.1.0 (a transcript RPC; no upgrade before filming), a speech-to-text switch.

### Round 6 (Claude), the screen's design pass before filming (2026-10-20, asked for by the founder)

| # | Item | Why | Status |
|---|---|---|---|
| B40 | **Andy in the state pill:** a small drawing of the robot whose antennas do what the robot's do; "Looking at you" under the state; the same mark on the phone pages | The one memorable element: the robot's own body language, not a stock dot | ✅ 2026-10-20 |
| B41 | **Warnings that look like warnings:** a solid wash and "Be careful" on a solid band, 7:1 in every part of the day | The judges faulted a scam checker whose action sat under its evidence; ours must read from the sofa | ✅ 2026-10-20 (`tests/test_round6_screen.py`) |
| B42 | **The card is the thing to read:** a narrow day column, two-line captions beside a card, a bigger chosen view, the receipt never cut off or short of a step; the quiet screen centred | Step 3 (Nemotron Ultra) could drop and the evidence ended in "…" | ✅ 2026-10-20 (checked in a browser on the demo, day and evening) |
| B43 | **The demo for filming and screenshots:** `ANDY_DEMO_SCENE` holds one scene; the real coming Saturdays; new screenshots in the README, the app page and the gallery list | The gallery and README showed the old design; the demo's date was wrong | ✅ 2026-10-20 |

### Round 7 (Claude), finding small things (2026-10-20, from the founder's tries at home)

| # | Item | Why | Status |
|---|---|---|---|
| B44 | **Zoom in, then look closer:** six full-size tiles per view, read at once; the head turned at the best sighting for a close-up and a strict yes/no; the close-up on the TV (decision 0012) | The 768-pixel copy lost the glasses; the founder's tries didn't find them the first time | ✅ 2026-10-20 (desk: 0 of 9 before, 9 of 9 after; the robot's rate comes from the founder's recorded tries, 3t2) |

Not taken yet (decision 0012, revisit with the recorded tries): a second, lower row of views; the camera's 4K mode
(the daemon sets it once at start); a local detector first (OWLv2, or NanoOWL as the Jetson path); any "enhance" filter.

### Round 8 (Claude), Physical AI: reacting to the room (2026-10-20, approved by the founder)

From research on the track and the field: the track rewards hardware reacting live to the real
world, and "Serverless Jobs to run simulations … evaluate robot policies".

| # | Item | Why | Status |
|---|---|---|---|
| B45 | **Turn to whoever speaks:** a second voice well to the side turns the head; nobody there, back | Attention shown without words, and presence; NVIDIA's Reachy Mini Jetson assistant has no sound direction | ✅ 2026-10-20 (tests; on the robot in live test 3aa) |
| B46 | **Remember where I put it:** a place kept after a yes, looked at first when asked | Human–object interaction | ✅ 2026-10-20 (suite 18 of 18; live test 3bb) |
| B47 | **Teach Andy a move by hand** (antennas), kept by name, played back | Puppetry and demonstration data | ✅ 2026-10-20 (suite 12 of 12; live test 3cc) |
| B48 | **The finder in simulation, as Nebius Serverless Jobs** (decision 0013) | The track's text; the tie-break on technology | ✅ 2026-10-20 (two jobs: zoomed in 0 false finds in 7, error 0.76°; old way 3 in 7) |
| B49 | **Wave, and Andy waves back** with its antennas | Presence in a few seconds of video | ✅ 2026-10-20 (tests; live test 3dd) |
| B50 | **What Andy noticed**, on the TV and the hood page | The video shows the robot's reason, not only its move | ✅ 2026-10-20 |

Not taken: guided movement and reacting to falls or loud sounds (health and safety claims), Cosmos Reason 2 on an
endpoint, emotions and dances in the model's hands, full-head teaching (the head may drop with its motors off).

### Round 9 (Claude), judging without a robot (2026-10-20, the founder's question: how will judges see the physical part without a robot?)

| # | Item | Why | Status |
|---|---|---|---|
| B51 | **Andy's search in simulation, as a film** (`sim/replay.py`; `docs/images/sim-search.*`) | Judges see the physical reasoning in 20 s without a robot | ✅ 2026-10-20 |
| B52 | **The demo shows it:** the film on the front page and in the Space; the keys scene; the drawing waving | The link judges click carries the physical part too | ✅ 2026-10-20 (checked in a browser) |
| B53 | **A judge can run the simulation** with only a Token Factory key (the scene fetched from PyPI) | Reproducible evidence, the track's "run simulations" | ✅ 2026-10-20 |

### Round 10 (Claude), audits and packaging (2026-10-20 to 21, approved by the founder: "yes to all your recommendations")

No new features: reviews of how judges see the entry, and the fixes they found.

| # | Item | Why | Status |
|---|---|---|---|
| B54 | **An audit against the rules and a judge's first look:** the suite as a Nebius Job again (92, 91, 94 of 94), the demo's family page opening, the film readable, private matter out, the history rewrite prepared | Stage One checks and a judge's first ten minutes | ✅ 2026-10-20 |
| B55 | **A systems audit from a fresh clone:** `--help` safe in every script, clear messages without a key, tests 44 s to 13 s and no leftovers, `.env.example` complete | Everything a judge is told to run works | ✅ 2026-10-20 |
| B56 | **A documentation audit:** a map of the docs, a decision template, stale statements fixed, the founder's town out, READMEs for `cloud/`, `evals/`, `sim/` | Each document true, findable and current | ✅ 2026-10-21 |
| B57 | **The finder at home, measured** from the founder's tries: pointed 3 of 9, never wrong; recording off, pictures deleted | A real rate instead of "none yet" | ✅ 2026-10-20 |
| B58 | **The Devpost text and README, short and clear:** about 1,500 words on Devpost's headings, the README's first screen, the gallery planned real robot first with captions, narration timed to its shots | Judges have about five minutes a project | ✅ 2026-10-21 |

### Round 11 (Claude), found on the robot and its screen (2026-10-25 evening, the founder: "continue audit and verify")

| # | Item | Why | Status |
|---|---|---|---|
| B59 | **The TV's design at every size:** the found card side by side (numbers on the pictures, one-line labels), the resting cards never cut off, the day's cards clear of the caption, lists in sentence case, caption pages broken where a sentence pauses; checked in a browser on every scene at three sizes | The founder's screenshots: words over numbers, card tops cut off, words under the caption | ✅ 2026-10-25 |
| B60 | **The weather card:** the town as its title, one line a period, an alert as what and until when, the small card stepping aside | "Weather / Weather" and paragraphs cut at two lines, on the robot's screen | ✅ 2026-10-25 |
| B61 | **A reminder's words keep only what to do** (English and Spanish, 13 cases) | "take a pill at eight o'clock in the morning" beside its own time | ✅ 2026-10-25 |
| B62 | **A research never starts itself again, and can be stopped** ("stop looking", "never mind", "be quiet") | Seven researches in five minutes on the robot, and "stop searching" did nothing | ✅ 2026-10-25, to re-check on the robot |
| B63 | **No heard words in any log, checked:** the "Live:" prints filtered; the doctor reads the voice log; this desktop's copies cleared | Ten days of heard words in the journal (decision 0017) | ✅ 2026-10-25 |
| B64 | **A misheard name is checked, not refused** ("Depeche Mode, the band?") | Speech recognition mishears names said with an accent | ✅ 2026-10-25 (tried against the model twice) |
| B65 | **The Devpost draft filled and saved** (story, tags, links, every answer, thumbnail, five captioned images, contribution); not submitted | Packaging takes longer than expected (the judges' advice) | ✅ 2026-10-25; the video and robot photos to add |

### Cleanup (Claude)

| # | Item | Status |
|---|---|---|
| C1 | gitleaks over every commit; a fresh-clone install from GitHub once public | ✅ 2026-10-25: gitleaks clean over every commit after the history rewrite; an anonymous clone from public GitHub installs and passes |
| C2 | Remove dead code (the review's three unused imports); mark finished milestones done in this file | ✅ 2026-10-14 (four unused imports removed; ruff's error and bug checks pass) |
| C3 | The final Nebius Serverless Job run on 2026-10-23; its numbers into the README, the Devpost text and the video script in one commit | ✅ 2026-10-25: 93, 92, 92 of 94 |
| C4 | Pin the Reachy Mini app's `andy-companion` dependency to the `hackathon-submission` tag | ⬜ (10-27) |

### The founder

| When | What | Where |
|---|---|---|
| With the live test | **The new robot behaviours (B45 to B49):** a second person speaking from the side, a wave, "my keys are here", "let me teach you a move" | [live-test.md](live-test.md) 3aa to 3dd |
| Now | **The robot's power and USB:** on 2026-10-20 its daemon reported "Motor communication error! Check connections and power supply" | |
| Now | The live test on the robot | [live-test.md](live-test.md) |
| With the live test | **About 20 recorded "find my glasses" tries (B34)**, as live test 3t2 says: hide something, ask, repeat (glasses, keys, the remote; a few out of sight on purpose); then Claude scores them, and reads the same tries with both vision models | [live-test.md](live-test.md) 3t2 |
| Now | **The body language test (B8)** with Claude watching the logs: presence is what the track rewards, by research on the field | [live-test.md](live-test.md) 3u |
| This week | **One real session** with a relative who agrees to it in writing: about 20 unscripted minutes, one real moment for the video if they're willing, no claims about outcomes | (the founder's) |
| By 2026-10-23 | **Two or three short sessions with older adults** (a relative, a neighbour), each agreeing in writing: what they asked first, what confused them, what they'd change. Claude writes down only what they agree to, and what changed because of it. The judges' most repeated advice was to talk to real users. *Still to do before submitting (2026-10-25)* | (the founder's) |
| After B26 | **The Hugging Face Space** for the public demo (the same account publishes the Reachy Mini app) | (the founder's) |
| Now | Photos and four 5-second clips of the real robot (the glance, following, finding glasses, the joke wiggle) | (the founder's) |
| After the name decision | The name; the repository public (its history rewritten first), licence in About; a Hugging Face account; Claude publishes the app | [submission-checklist.md](submission-checklist.md) |
| By 2026-10-22 | **A complete draft submitted** on Devpost (the early eligibility check). *Missed; the draft was saved on 2026-10-25 (B65), to submit with the video* | [submission.md](submission.md), [feedback.md](feedback.md) |
| 2026-10-24 to 10-26 | Filming to the shot list; YouTube Public, "not made for kids", captions | [video.md](video.md) |
| 2026-10-27 | The live rules page re-read; the commit tagged `hackathon-submission`; submitted; posts | [rules-compliance.md](rules-compliance.md) |
| 2026-12-01 to 12-15 | Judging: the repository public at the tag; the robot ready if physical access is asked for | |

### Round 12 (Codex), the October 26 project review

The founder approved the review's recommendations and moved filming to October 27. Fixes and evidence
take priority over new features. The submission tag and app pin wait for the final tested revision.

| # | Item | Status |
|---|---|---|
| B66 | Bind each confirmation to one exact action and readback, with expiry and one-use permission | Built and regression-tested; decision 0018; robot check pending |
| B67 | Keep cards and research in server memory; complete pending-item visibility and deletion | Built and tested across processes; decision 0019; service checked; USB reconnection required for live validation |
| B68 | Fixed medicine-page response and a journal check that cannot pass on a read failure | Built and regression-tested; robot medicine-page check pending |
| B69 | CPU CI and accurate evaluation scope, real consent gate in the text suite, input/code hashes | Hosted CI passed on c3a3f12; current local text suite 95/97 three times; exploratory runs retained separately |
| B70 | Thirty planned real finder attempts, without speech or pictures; brief usability sessions | Recorder/scorer built; physical trials and sessions are the founder's |
| B71 | Reconcile claims, local-vision limits, API-cost scope, filming date and outstanding evidence | Updated October 26; video and real photos remain October 27 work |

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
| Lightning's tool calls are weak on a hard turn | Hand hard questions to Nemotron 3 Ultra (`think_it_through`) |
| Reasoning text spoken aloud | Thinking off; strip it in our wrapper if it ever appears |
| No NVIDIA vision model on serverless Token Factory | Resolved by decision 0011: Nemotron 3.5 Super VL on Token Factory since 2026-10-20; the Nano VL endpoint stays as an option |
| The robot is shared with another app | Only one program drives the robot at a time; tests stop the other |
| Time | Milestones are in order of what the video needs; M6 and M8 can shrink without breaking the demo |
