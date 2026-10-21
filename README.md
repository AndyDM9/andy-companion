# Andy Companion

**A small home robot for older adults who live at home, and the family who help.** Andy runs on a
Pollen Robotics [Reachy Mini](https://huggingface.co/blog/reachy-mini). It hears with NVIDIA
Parakeet, talks with NVIDIA Nemotron on Nebius Token Factory (on the robot, a median of 1.06 s from your words to
its first sound), sees with Nemotron 3.5 Super VL, also on Token Factory, and looks things up with Tavily. It says it's a robot, and it keeps
no recordings or transcripts: only what you ask it to keep.

> Built for the Nebius x NVIDIA Global AI Hackathon 2026, Physical AI track.

**What's new here:**
- **A language model that moves a robot's head to find things in a room,** with nothing trained: it looks around,
  zooms in, looks closer and points, and it is tested in simulation as Nebius Serverless Jobs.
- **A scam check for where scams reach people at home:** the letter in your hand or the call you mention. Tavily's
  consumer-protection warnings, judged by Nemotron 3 Ultra, caught 58 of 60 scams and flagged none of 60 ordinary
  messages, measured beside word rules and each model alone.
- **Rules in code under the model:** **Be careful** on a risky letter whatever the model says, consent before
  anything is remembered, and no recordings or transcripts.

**Judging it without a robot** (you won't have a Reachy Mini; this is how to see the physical part anyway):
1. **Watch the video** (its link is the first thing below this list): everything on it is live, on the robot, with
   no cuts in the pauses.
2. **Watch Andy's search in simulation** (20 s, below): Pollen's own MuJoCo scene, Andy's own search code, live
   NVIDIA Nemotron 3.5 Super VL calls: it looks around, reads each view as six zoomed tiles, looks closer, points.
   Measured the same way over 30 trials as Nebius Serverless Jobs (no false find in 7 without the duck; pointing
   within 0.76° median). Run it yourself with a Token Factory key, no robot:
   `cd sim && uv sync && cd .. && NEBIUS_API_KEY=… MUJOCO_GL=egl uv run --project sim python sim/finder_sim.py --trials 10`
   (it fetches Pollen's scene from PyPI once; use `MUJOCO_GL=osmesa` without a GPU).
3. **See the screens with no keys at all:** `uv sync && uv run python scripts/demo_screen.py`, then open
   `http://127.0.0.1:8093/`: the TV, Under the hood, the family page and the settings page, on sample data
   (no robot, GPU or keys).
   <!-- Founder: once the Hugging Face Space is up (founder action 6.18), its link goes here as "or open it in your browser". -->
4. **Read the evidence:** the [conversation suite's scorecard](evals/results/2026-10-20-nebius-job-andy-suite-20261020-195645.json)
   (94 situations, a Nebius Serverless Job), the [scam check's](evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json)
   (each model alone and with Tavily's warnings, four Nebius Serverless Jobs, beside a [no-model baseline](evals/results/scam-word-rules-2026-10-20-1552.json)),
   and [54 real turns on the robot](evals/results/robot-timings-2026-10-20-1550.json); every failure is in them.
5. **Rerun the scam check yourself** with only a Token Factory key, against the Tavily warnings we saved:
   `NEBIUS_API_KEY=… uv run python evals/scam_eval.py --warnings evals/results/scam-warnings-2026-10-14-1144.json --runs 1`
   (a few minutes; Tavily isn't called).
6. **See the real robot live** on a video call, any time until 2026-12-15: ask, and we'll show it.
7. **The code that matters:** the scam check ([scamcheck.py](src/andy_companion/scamcheck.py)), finding things
   ([finder.py](src/andy_companion/finder.py)), letters ([letters.py](src/andy_companion/letters.py)), the
   urgent-words net ([urgent.py](src/andy_companion/urgent.py)), privacy ([privacy.py](src/andy_companion/privacy.py)),
   and why each choice was made ([decisions](docs/decisions/README.md)).

<!-- Founder: the video link and a photo or GIF of Andy beside the TV go here before submitting. -->

![Andy's own search for a rubber duck in Pollen's MuJoCo scene: on the left the room with an arrow for where Andy's eye points, on the right what it sees, with the zoomed tiles, the sighting, the close-up and the point](docs/images/sim-search.gif)

**Why a robot, not a smart speaker?** Andy looks at you while you talk and turns as you move. When it
shows you something on the TV it turns its head to the screen, so your eyes follow. It reads the letter
in your hand. Ask where your glasses are, and it looks around the room and points at them with its head.

## Three moments

**"Can you read this for me?"** You hold up a letter. Andy reads it on this computer and explains it,
and the TV shows it in large print. If the page asks for gift cards or rushes you, code (not the model)
puts **Be careful** first, and Andy never reads out the page's numbers.

![A letter on Andy's screen, with a warning (sample data)](docs/images/tv-letter.png)

**"Where did I leave my glasses?"** Andy looks around the room. NVIDIA Nemotron 3.5 Super VL on Token Factory
reads the four views zoomed in, each as six tiles at the camera's full resolution (24 at once, about 1.8 s). Then
Andy looks closer: it turns its head straight at what it saw, takes a close-up and checks it, and only then points
at them and says "I think I see your glasses, on the table…". At the desk, on nine versions of one room photo with a
real pair of reading glasses in it, the old way (one shrunk picture per view) found them in 0 of 9, zoomed in 9 of 9,
with no false sighting in the nine without them: a direction, not a rate
([how we measured](docs/research.md#finding-small-things-zoom-in-then-look-closer-researched-2026-10-20)). The TV shows the picture it saw them in, held in memory for two
minutes and never saved.

**"Could you look into whether the farmers market is on this Saturday?"** Andy starts Tavily's research
agent and carries on talking. The TV shows each step as it happens, and Andy tells you the dated answer
with its sources.

![Andy's screen: what it found, the next reminder, the weather, and its own words (sample data)](docs/images/tv-glass-found.png)

## What Andy does

- **Talks and keeps looking at you**, in English or Spanish, with body language from research: its
  antennas lift while you speak and lean while it thinks.
- **Notices the room by itself:** when someone else speaks from the side, Andy turns to them (and back if nobody is
  there, such as the TV); wave at it and its antennas wave back. The TV says what it noticed ("Turning to a voice",
  "Waving back").
- **Remembers where you put things, if you want:** "my keys are here" gets "Shall I remember where they are?";
  later "where are my keys?" turns straight to that spot and checks up close before looking around.
- **Learns a move by hand:** a grandchild moves Andy's antennas for six seconds, and "do Sofia's wave" plays it
  back, gently (its antennas only).
- **Your day:** the date (never guessed), reminders in your own words, the morning plan, and the weather
  from the National Weather Service.
- **Good company:** short turns and open questions about your life (never "Do you remember…?"), gentle
  jokes and riddles, public-domain stories read a part at a time, On this day from Wikipedia, and "help me
  think it through" with Nemotron 3 Ultra.
- **Scam checks, measured on Nebius** (120 messages read aloud, 60 scams and 60 ordinary; 40 of them
  written after the check was frozen, from this autumn's consumer-protection warnings; three runs as Nebius
  Serverless Jobs, 2026-10-14, [scorecard](evals/results/scam-eval-2026-10-14-1200-nebius-jobs.json); the
  word rules' [scorecard](evals/results/scam-word-rules-2026-10-20-1552.json)):

  ![The scam check five ways: scams caught and ordinary messages flagged, of 60 each, with 95% intervals](docs/images/scam-check-five-ways.svg)

  | | Scams caught (of 60) | Ordinary flagged (of 60) |
  |---|---|---|
  | Word rules alone (Andy's letter rules: gift cards, wire transfers, "act now"…; no model, no web) | 28 (35–59%) | 3 (2–14%) |
  | Nemotron 3.5 Lightning alone | 53.3 (78–95%) | 0 (0–6%) |
  | Nemotron 3 Ultra alone, no web | 55.7 (83–97%; of the 59.7 it answered) | 0 (0–6%; of the 54.7 it answered) |
  | Tavily's warnings, matched by Lightning | 60 (94–100%) | 24 (29–53%) |
  | **Andy: Tavily's warnings, matched by Ultra** | **58 (89–99%)** | **0 (0–6%)** |

  In brackets, the Wilson 95% interval over the 60 messages. Read plainly: on scams caught, Andy and the
  models alone overlap, so we don't claim Andy catches more. What Tavily plus a careful second question buys
  is warnings with a named source and **no false alarms, where Tavily with the fast model flags 40% of
  ordinary messages**: only a strong model tells the same trick from the same topic. One check costs about
  **$0.017** (an advanced Tavily search, 2 credits, plus about $0.0006 of Nemotron), so about **$17 per 1,000
  checks** at pay-as-you-go prices. Andy named the consumer-protection source it relied on in 170 of 174 scam verdicts; on the 20
  held-out scams it caught 19, against 18 for either model alone.
  17 of Ultra's answers on its own never finished their JSON (written up as feedback); they are left out of
  its totals, not counted as right.
- **The world, with sources:** local news from your own papers, look-ups, what's on, a link family sent,
  and scam checks, all through Tavily. Under each answer the TV says how it was found ("Found with Tavily:
  search (basic), 1.4 s, 1 credit"); a Spanish speaker gets Spanish pages first.
- **Family, on your terms:** family see only what you share, Andy tells you who looked, and a helper sets
  Andy up from a phone, with Andy telling you who changed what.
- **A screen beside it**, readable from across the room, with captions of Andy's own words and every
  text colour at 7:1 contrast, tested.

Everything, in full: [docs/features.md](docs/features.md).

**What Andy never does:** give medicine doses or medical advice, ask for money or passwords, claim to keep
anyone safe, speak as a real person, or keep recordings or transcripts.

**What it costs:** about **$2.30 a month** for one household's conversation, help and web lookups at an
active level of use (Token Factory's prices on 2026-10-14; the web within Tavily's free 1,000 credits), plus
the hardware once. The eyes are on Token Factory, paid per picture (a search for your glasses about half a cent), so nothing
runs while idle. The second look is not in that figure: it runs on a Nebius endpoint started when needed (about
$1.55 an hour while running). Every price and assumption: [docs/cost.md](docs/cost.md).

## Accessibility

Andy is used by voice, from across a room, by people of any eyesight or hearing, so access is the product:
- **Nothing to read, tap or install for the person.** Everything is said; the TV only shows what Andy
  says, and the family and settings pages are for helpers.
- **All of Andy's words as captions** on the TV, at reading pace, three lines at a time, on by default.
- **Readable from across the room:** large type in Atkinson Hyperlegible (made by the Braille Institute for
  low-vision readers), and every text colour at 7:1 contrast (WCAG AAA) against the worst glow or photo
  behind it, tested (`tests/test_screen_design.py`).
- **A calm screen** in the settings: no movement and no see-through panels; the TV also follows the
  system's reduced-motion setting.
- **The TV's remote:** arrows and OK reach Settings and Under the hood; Back closes the menu.
- **A letter in large print** on the TV, with what to do and by when.
- **Pace and volume by voice**, "slower", "louder", and they stick; talk over Andy and it stops at once.
- **English and Spanish**, with *usted*; the screen and pages switch too.
- **The phone pages** for family and helpers: 17 px text or larger, 48 px targets, 7:1 text.

## What runs where, and why that model

**On this computer, beside the robot:** hearing (NVIDIA Parakeet TDT 0.6B v3, 0.02 to 0.08 s an utterance)
and speaking (Qwen3-TTS, first audio in 0.10 to 0.33 s) on the GPU, about 7.1 GB of GPU memory together
(measured 2026-10-20); the wake phrase, offline, in English and Spanish (Vosk); reading a letter
(Tesseract: only its text leaves); following your face (Pollen's tracking); every body behaviour. When
Andy looks around for something, each frame is taken only after the head has stopped and settled
(0.6 s), so the model never reads a blurred view.

**On Nebius, each model for a reason we measured:**

| Model | Why this one |
|---|---|
| Nemotron 3.5 Lightning, Token Factory | Every turn: 0.6 to 0.8 s a reply with tool calls, at $0.06 per million input tokens |
| Nemotron 3 Ultra, Token Factory | Only where judgment matters: in the scam check, Ultra told the same trick from the same topic (0 ordinary messages flagged, against 24 with Lightning); hard decisions; the suite's judge |
| Nemotron 3.5 Super VL, Token Factory | Eyes: four views read at once as structured output in about 2.1 s, a description in about 1.35 s, against 2.3 s and 3.45 s for Nano VL on our own endpoint, both right on every view ([desk check](evals/results/eyes-check-2026-10-20-1614.json)); on Token Factory since October 2026, so always on, nothing to start and nothing paid while idle. Nemotron Nano 12B v2 VL on our own Serverless Endpoint stays as an option (`ANDY_VISION=endpoint`, [decision 0011](docs/decisions/0011-the-eyes-on-token-factory.md)) |
| Nemotron 3.5 Content Safety, Serverless Endpoint | A second look for signs of crisis, with our own policy: 7 of 8 held-out sentences caught, against 5 of 8 with its standard categories, in about 0.55 s |

### Beside NVIDIA's Reachy Mini Jetson assistant

NVIDIA's [Reachy Mini Jetson Assistant](https://www.jetson-ai-lab.com/tutorials/reachy-mini-jetson-assistant)
(Jetson AI Lab, read 2026-10-20) runs everything on the robot's own small computer. Andy makes different
choices, and says why:

| | The Jetson assistant | Andy |
|---|---|---|
| Computer | Jetson Orin Nano 8 GB, about 7.6 GB usable | A desktop with an NVIDIA GPU beside the robot; hearing and speaking use about 7.1 GB |
| Starting a turn | Push-to-talk in a web page; Silero VAD | A spoken wake phrase, offline (Vosk), English and Spanish; then natural turn-taking, and you can talk over Andy |
| Hearing | faster-whisper | NVIDIA Parakeet TDT 0.6B v3, on this computer |
| Thinking and seeing | Cosmos Reason 2 2B, 4-bit (about 2.2 GB), llama.cpp, on the Jetson | Nemotron 3.5 Lightning, Nemotron 3 Ultra and Nemotron 3.5 Super VL on Nebius Token Factory, zero data retention |
| Speaking | Kokoro | Qwen3-TTS, on this computer |
| Moving | One 100 Hz controller, so face tracking and speaking gestures never fight | The same idea in Pollen's movement manager: one loop at 60 Hz is the only thing that sets the motors; following your face is blended in, and glances at the TV, the finder's sweep and the antennas wait in its one queue |
| A picture for the model | Motion frozen briefly before the frame is chosen | The head stops and settles 0.6 s before each frame |
| Published speed | None given | Median 1.06 s from your words being understood to Andy's first sound, 54 real turns ([scorecard](evals/results/robot-timings-2026-10-20-1550.json)) |

**Why the difference:** the hard parts of Andy (telling a scam from an ordinary letter, judging a hard
question, finding glasses in a cluttered room) are where model size showed in our measurements, and Token
Factory runs the big models without a language model at home. The trade-off is that your words leave the house,
with zero data retention; the Jetson assistant keeps everything local.

**What a Jetson version would need** (a plan, not tried): hearing and speaking in well under 7.6 GB, so a
smaller voice than Qwen3-TTS; thinking and seeing staying on Token Factory, so the Jetson needs no language
model; and, for when the network is down, a small local model such as Cosmos Reason 2 2B to answer "where are my
glasses?" offline. Offline Andy should do less, never more.

## Built on what older adults have said they want

Each principle comes from published research, and each has something you can see Andy do.

| Principle | Source | What Andy does |
|---|---|---|
| Fast replies, clear turn-taking, controls the person can change | [International Psychogeriatrics, 2026](https://www.sciencedirect.com/science/article/pii/S1041610226000347) | Nemotron answers in 0.6 to 0.8 s; each turn's time, from when the voice server hears you finish to Andy's first sound, is shown live on the `/hood` page; you can talk over Andy and it stops at once; "slower", "louder", "be quiet for an hour" stick |
| Support human contact, never replace it | Same study | Passes on family messages and photos; encourages a call or a visit; never says it replaces anyone |
| Never present as human | [Berridge et al., 2023](https://pubmed.ncbi.nlm.nih.gov/36895732) | Says it is a robot whenever it matters; never speaks as anyone, even when asked (tested in the suite) |
| The older adult decides what is collected and shared | [University of Washington, 2023](https://www.washington.edu/news/2023/09/06/qa-older-adults-want-more-say-in-companion-robots-ai-and-data-collection) | Remembers only after "Shall I remember that?" (checked in code); shares only what you ask; tells you who looked and who changed a setting |
| No ageist assumptions, no talking down | [WHO, 2022](https://www.who.int/publications/i/item/9789240040793); research on patronising speech to older adults | Plain words, never "sweetie" or baby talk; *usted* in Spanish; no jokes about age, memory or health (tested) |

## How it uses NVIDIA and Nebius

![How Andy works](docs/images/architecture.svg)

| Part | Model or service | Where it runs |
|---|---|---|
| Conversation and tool calls | NVIDIA **Nemotron 3.5 Lightning** | **Nebius Token Factory** (zero data retention on) |
| Hearing | NVIDIA **Parakeet TDT 0.6B v3** | Local GPU, inside [speech-to-speech](https://github.com/huggingface/speech-to-speech) |
| Eyes: "what do you see?", family photos and finding things in the room | NVIDIA **Nemotron 3.5 Super VL**, structured output, reasoning off | **Nebius Token Factory**; or NVIDIA Nemotron Nano 12B v2 VL (FP8, vLLM 0.30.0) on our own **Nebius Serverless Endpoint**, one L40S ([cloud/vision-endpoint.sh](cloud/vision-endpoint.sh)), with `ANDY_VISION=endpoint` |
| A second look at the person's words, for signs of crisis | NVIDIA **Nemotron 3.5 Content Safety**, with a policy written for this, vLLM 0.20.2 | A second **Nebius Serverless Endpoint**, one L40S ([cloud/guard-endpoint.sh](cloud/guard-endpoint.sh)) |
| Thinking a hard question through ("help me think it through") and judging Andy's answers | NVIDIA **Nemotron 3 Ultra** | Nebius Token Factory |
| Large-print letter cards and vetting On this day | NVIDIA **Nemotron 3.5 Lightning**, structured output (strict JSON schema) | Nebius Token Factory |
| The conversation suite | 94 spoken situations, 22 areas, English and Spanish | **Nebius Serverless Job** ([cloud/suite-job.sh](cloud/suite-job.sh)) |
| The scam check, measured five ways | Word rules alone, Lightning, Ultra, and Tavily's warnings with each; 120 messages, three runs, 95% intervals | **Nebius Serverless Jobs**, four of them, two at a time ([cloud/scam-job.sh](cloud/scam-job.sh)); the word rules need no model |
| The web | **Tavily**: search (news, look-ups, scam checks at advanced depth), extract (links family send), crawl (what's on), **map** (the town's events calendar, at setup), and **research**, streamed, for "look into it for me"; safe search on every search; every search, extract, crawl and research request tagged `X-Project-ID`, and one conversation's requests share an `X-Session-Id`; credits shown on `/hood` | Tavily API |

### Where Token Factory sped us up

- **One key, every Nemotron model.** Andy talks with Nemotron 3.5 Lightning and the suite's judge is
  Nemotron 3 Ultra, both through the same Token Factory API: trying a model is changing its name, and
  the judge reads all 94 situations three times in a few minutes.
- **No language-model GPU at home.** The desktop's graphics cards keep hearing and speaking local
  (Parakeet, Qwen3-TTS); the thinking runs on Token Factory, 0.6 to 0.8 s per reply, measured on the
  robot.
- **Zero data retention**, switched on in Token Factory, so a household's conversation is not kept by
  the model service either.
- **The same suite runs on Nebius AI Cloud** as a Serverless Job, and so does the scam evaluation (the
  models three times against warnings Tavily fetched once, in about six minutes); the second look is a
  Serverless Endpoint we start when needed and stop after; stopped, it costs nothing for compute.
- **The newest NVIDIA vision model the week it arrived.** Nemotron 3.5 Super VL appeared on Token Factory in
  October 2026; Andy's eyes moved to it with one setting, and the same evaluation reads the robot's tries with
  either model.
- **The finder tested in simulation, as Serverless Jobs** ([decision 0013](docs/decisions/0013-the-finder-tested-in-simulation.md)):
  Pollen's MuJoCo scene with things placed at random, Andy's own search on what a virtual eye sees, scored against
  the scene's truth. Two jobs, 30 trials each, with a glasses-sized duck: zoomed in with the closer look, pointed at
  it 18 of 23 times with **no false find in 7** (error 0.76°); the old way 19 of 23, but **3 false finds in 7**
  (error 2.73°) ([on](evals/results/sim-finder-20261020-185613-on-small0.35-nebius-job.json),
  [off](evals/results/sim-finder-20261020-185613-off-small0.35-nebius-job.json)).

## Measured (Reachy Mini Lite)

| Step | Time |
|---|---|
| Parakeet speech-to-text | 0.02–0.08 s (2026-10-13) |
| Nemotron 3.5 Lightning reply or tool call | 0.62–0.83 s (2026-10-13) |
| Text-to-speech, first audio | 0.10–0.33 s (2026-10-13) |
| **The whole turn, 54 real turns** (2026-10-14 to 10-18): from your words being understood to Andy's first sound, tool turns included | **median 1.06 s**; 90% under 1.88 s, 95% under 3.24 s, slowest 5.23 s ([scorecard](evals/results/robot-timings-2026-10-20-1550.json), from Andy's own log, numbers only: `evals/robot_timings.py`) |

**Live, on the robot:** the screen server's `/hood` page shows each turn as it happens: the time from the
end of your words to Andy's first sound, then the turn laid out stage by stage (NVIDIA Parakeet on this
computer, Nemotron 3.5 Lightning on Nebius Token Factory, each tool with where it ran and how long it
took), a tally since Andy started, and the latest Nebius Serverless Job scorecard. Numbers and tool names
only, in memory; never the words. In English or Spanish, like the household.

![Under the hood (sample turns)](docs/images/hood.png)

**The conversation suite** ([evals/](evals/)): 94 spoken situations in 22 areas, English and Spanish,
judged by NVIDIA Nemotron 3 Ultra. The model gets exactly the robot's tools and their real descriptions
([evals/tools.json](evals/tools.json), written from the robot's code). Where a case needs a tool, what
Andy says with its answer is judged too; words that must never be said (a scam letter's phone number)
are checked in code, not by the judge.

- **Latest, as a Nebius Serverless Job: 92, 91 and 94 of 94** (2026-10-20, with photo stories, places and
  taught moves; [scorecard](evals/results/2026-10-20-nebius-job-andy-suite-20261020-195645.json)). Five cases failed once each, never twice: two calls that didn't
  happen (act-2, think-1), a share without reading the message back (share-2), a crisis reply without
  "someone you trust" (crisis-3), and a photo read as a letter (photo-4). The final Job run comes before
  submitting.
- **Before, as a Job:** 79, 79 and 79 of 81 (2026-10-13;
  [scorecard](evals/results/2026-10-13-nebius-job-andy-suite-20261013-230345.json)).
- **Baseline:** 27 of 36, before any fixes.
- **What the suite has found**, each fixed and recorded in [evals/suite.json](evals/suite.json):
  - Andy said it had no camera, and once invented a time;
  - no crisis line in 2 of 3 runs for "everyone would be better off without me" (15 of 15 after);
  - a judge that passed a reply reading out a scam's phone number, and a harness that never judged the
    rules of tool cases;
  - a story recited from the model's memory;
  - a scam warning delayed by a follow-up question.
- **Urgent words:** if someone says "my chest hurts" or "I don't want to be here anymore", a check in
  code sees the words. If Andy's reply misses 911 (or the 988 Suicide and Crisis Lifeline), Andy is told
  to say an exact sentence naming it, in English or Spanish. Grief and everyday phrases ("I'm dying to
  see my grandkids") are tested not to trigger it.
- **The second look** ([evals/guard_check.py](evals/guard_check.py)): on crisis phrasings the word list
  doesn't know, Nemotron 3.5 Content Safety with our policy caught **7 of 8 held-out sentences with no
  false alarms** in 8 ordinary ones that share their words ("my will", "the bridge", "sleeping tablets"),
  in about 0.55 s. With its standard categories it caught 5 of 8.

Every suite run's scorecard, each failure with the judge's reason, is in [evals/results/](evals/results/);
timings are dated measurements in [docs/STATUS.md](docs/STATUS.md).

## What doesn't work yet

- **No study with older adults yet.** Andy is built on published research and measured with our own tests;
  a pilot with an ethics review comes next.
- **The finder has no rate at home yet.** In a dozen tries during development (2026-10-19 and 20, the code
  changing between them) it found the glasses on a table and on the floor; on a dark chair it said several times
  that it couldn't see them, rather than guessing. Tries can be recorded and scored (`evals/finder_eval.py`). It
  finds things, not people. In simulation it is measured
  (decision 0013), but rendered pictures are cleaner than a room. From where Andy sits it can't look further than
  60 degrees to either side without turning its body, so a chair beside it can be out of reach.
- **Turning to a voice, waving back and moves taught by hand are new** (2026-10-20): tested in code and in the
  suite, not yet on camera with two people. The microphones can't tell a voice in front from one behind.
- **The scam check missed 2 of 60 scams.** It says a message looks like a known kind of scam, never that
  a message is safe, and always suggests checking with family first.
- **The suite isn't perfect:** about one different case fails each run, and every failure is in its
  scorecard.
- **Body language while thinking** (a glance away, a tilt as a question ends) is built but off until it has
  been tested with the robot (`ANDY_EXPRESSIVE=on`).
- **It needs a computer with an NVIDIA GPU** (8 GB or more) beside the robot. It doesn't run on a Jetson
  yet.
- **English and Spanish only.**
- **The second look** runs on a Nebius endpoint we start when needed. The eyes no longer do (they're on Token
  Factory), but Super VL is newer to Andy than Nano VL: it is checked at the desk and in the suite, and the
  finder's real measure is the recorded tries at home, read by both models.
- **The TV page** is tested in Chromium and has live regions for the state and the captions, but hasn't
  been tried with a screen reader.
- **Andy without a robot** (`scripts/andy-sim`) hasn't been tried on a computer with no robot attached.

## Privacy

**In four answers:**
- **Where is it heard?** Your voice becomes words on this computer and is never recorded; the words go to
  Nemotron on Nebius Token Factory, with zero data retention on.
- **What is kept?** Only what you ask Andy to keep (a reminder, a fact, a moment), on this computer.
- **Who sees it?** Family see only what you ask Andy to share; Andy tells you who looked.
- **How do I delete it?** Say "forget that", or a helper deletes anything from one page on a phone, and
  Andy tells you who deleted what.

- **No recordings or transcripts.** Andy's own log lines never contain what anyone says, and Pollen's
  app's log records are redacted as they are made, at the normal log level (`tests/test_privacy.py`).
- **What Andy keeps,** in owner-only files on its own computer: reminders, facts and moments you asked it
  to remember (moments for 7 days), notes you shared with family, messages and photos family sent
  (photos for 7 days), your settings, a story bookmark, and joke numbers. A question you asked Andy to
  look into is kept until Andy tells you the answer. A helper can see and delete everything on one
  page, and Andy tells you who deleted what.
- **What leaves the house,** only as each feature needs it:
  - your words to Nebius Token Factory (zero data retention on), and to your own Content Safety
    endpoint;
  - searches to Tavily, with scam-check messages' numbers and links removed first;
  - a camera picture to Nebius Token Factory (zero data retention on; or your own endpoint, if you choose it)
    only when you ask "what do you see?", ask Andy to find something, or a family photo is described; it is not
    kept there;
  - a letter is read on this computer, and only its text goes to Token Factory.
- **The TV and family pages** ask nothing of anyone outside the house: even the typeface is served by
  Andy itself.
- **Keys never enter this repository;** a pre-commit hook blocks key-like strings.

## Try it without a robot

- **The screen and pages, on sample data:** `uv sync && uv run python scripts/demo_screen.py`, then open
  the addresses it prints. No robot, GPU or keys. `--public` serves the same pages read-only for anyone
  to open; `scripts/space.sh build` puts them together as a Hugging Face Space (`space/`).
- **The conversation suite,** with only a Token Factory key: `uv run python evals/run_suite.py --runs 1`.
- **The scam evaluation,** with only a Token Factory key, against the saved Tavily warnings:
  `uv run python evals/scam_eval.py --warnings evals/results/scam-warnings-2026-10-14-1144.json --runs 1`.
- **Andy on your own computer, experimental:** `./scripts/andy-sim` runs Pollen's pretend robot
  (`--mockup-sim`) with your webcam, microphone and speakers, the voice server (an NVIDIA GPU) and Andy.
  Nothing moves, and finding things sees one view. On Linux, Pollen's daemon needs GStreamer with its WebRTC
  plugin ([Pollen's guide](https://huggingface.co/docs/reachy_mini/SDK/installation)). Not yet tried on a
  computer without a robot attached; the robot, on video, is the reference.
- **The real robot, live:** ask for a video call, any time until judging ends (2026-12-15).

## Setup

**You need:**
- Ubuntu 24.04 with an NVIDIA GPU (8 GB or more) for the voice server;
- a Reachy Mini with Pollen's daemon running ([Pollen's guide](https://huggingface.co/docs/reachy_mini));
- `tesseract-ocr` (and `tesseract-ocr-spa` for letters in Spanish), `pulseaudio-utils` (the wake listener
  uses `parec`), and [uv](https://docs.astral.sh/uv/);
- a Nebius Token Factory key and a Tavily key.

1. **Keys.** Copy `.env.example` to `~/.config/companion-hackathon/.env` and fill it in. Then
   `chmod 600` it. Turn on zero data retention in Token Factory's organisation settings.
2. **Voice server.** `cd voice && uv sync && ./run.sh`. It uses the first GPU; to use another, put
   `ANDY_VOICE_GPU=1` (its number) in the env file.
   The first start downloads the speech models (NVIDIA Parakeet, Qwen3-TTS, the turn detector) from
   Hugging Face, so it takes longer; later starts load them from the cache. To keep it running and
   restart it on failure: `scripts/install-services.sh`, then `systemctl --user start andy-voice andy`.
3. **Robot side.** `cd robot && uv sync`, then from the repository root run `./scripts/andy`.
4. **Your home.** `python scripts/settings.py links` prints four private addresses on your home
   network. Open **Set up Andy** on a phone to choose the town, local news sites, what's-on pages,
   language, pace, volume and captions. Open **the screen** on a TV, and send **the family page**
   to family. **Under the hood** has its own link, which opens only that page; the gear on the TV
   opens it too.
5. **Optional: eyes and the second look.** With the [Nebius CLI](https://docs.nebius.com/cli), run
   `cloud/vision-endpoint.sh create` (and `cloud/guard-endpoint.sh create`), then `status` until it is
   RUNNING. `create` keeps the endpoint's token in Nebius MysteryBox secrets, never on a command line.
   Run `stop` when you're done; a stopped endpoint costs nothing for compute.
6. **Check everything.** `robot/.venv/bin/python scripts/doctor.py` says what's missing.
   To start Andy at login: `scripts/install-services.sh --enable`.
7. **Optional: the suite on Nebius.** `cloud/suite-job.sh run`, or locally
   `set -a; . ~/.config/companion-hackathon/.env; set +a; uv run python evals/run_suite.py --runs 3`
   (it reads `NEBIUS_API_KEY` from the environment).

Tests: `uv run pytest`; every test, the robot-side ones included, in the robot's environment:
`uv run --project robot --with pytest python -m pytest tests`.

## Repository

| Path | What it is |
|---|---|
| `src/andy_companion/` | Andy's own code: clock, reminders, speaker, body behaviours, privacy, web, the scam check, reading, vision and the finder, the urgent-words net (with its recordings), screen, supervisor and watchdog |
| `tools/` | The voice tools Andy can call |
| `profiles/companion/` | Who Andy is and what it never does |
| `voice/` | The voice server (Parakeet, Nemotron on Token Factory, text-to-speech) |
| `robot/` | The robot-side environment (Pollen's conversation app 1.0.1) |
| `cloud/` | The Nebius Serverless Endpoint and Job scripts (and `secret.sh`: secrets never on a command line) |
| `evals/` | The conversation suite, the scam evaluation, the finder's scoring, and their scorecards |
| `scripts/` | Running Andy (`andy`, `install-services.sh`), the health check (`doctor.py`), settings links, the demo screen, captions and GIFs for the video |
| `systemd/` | The two user services: the voice server and Andy |
| `docs/` | [Plan](docs/PLAN.md), [status](docs/STATUS.md), [architecture](docs/architecture.md), [decisions](docs/decisions/) |

## Built during the hackathon

This project was created on 2026-10-13, inside the submission period (2026-08-26 to 2026-10-30).
It reuses, rewritten for this project, general-purpose robot behaviour code its author wrote earlier in
the same period (from 2026-10-05): looking at the person while speaking, turning toward a voice, the
offline wake phrase. Everything else, from the companion's tools and the rules in code to the screens, the
suite and the Nebius deployments, was written for this entry; the changelog has every step.
It builds on open source it does not copy: Pollen Robotics' conversation app (extended through its
profile, its tool folder and runtime hooks installed at start, `app_mode.install`; not forked, its files
unmodified) and Hugging Face's speech-to-speech server.

## Licences and credits

This repository is Apache-2.0 ([LICENSE](LICENSE)). It uses, under their own terms:

| What | Licence or terms | Credit |
|---|---|---|
| NVIDIA Parakeet TDT 0.6B v3 (hearing) | CC-BY-4.0 | NVIDIA, [model card](https://huggingface.co/nvidia/parakeet-tdt-0.6b-v3) |
| NVIDIA Nemotron 3.5 Lightning and Nemotron 3 Ultra | Used through Nebius Token Factory under its terms; NVIDIA's model licences | NVIDIA, Nebius |
| NVIDIA Nemotron 3.5 Super VL (eyes, since 2026-10-20) | Used through Nebius Token Factory under its terms; NVIDIA's model licence | NVIDIA, Nebius |
| NVIDIA Nemotron Nano 12B v2 VL FP8 (eyes on our own endpoint, the option) | NVIDIA's open model licence ([model card](https://huggingface.co/nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-FP8)) | NVIDIA |
| NVIDIA Nemotron 3.5 Content Safety (second look) | OpenMDW-1.1, Gemma Terms of Use and Prohibited Use Policy | NVIDIA, Google (Gemma) |
| Qwen3-TTS (speaking) | Apache-2.0 | Qwen team, Alibaba |
| Pollen Robotics' Reachy Mini SDK and conversation app | Apache-2.0 | Pollen Robotics |
| Pollen's MuJoCo scene for the Reachy Mini (`sim/`: fetched from the `reachy_mini` package on PyPI at run time, never stored in this repository) | Apache-2.0, with the package | Pollen Robotics |
| MuJoCo (the simulation) | Apache-2.0 | Google DeepMind |
| OpenCV (camera pictures, the wave) and Tesseract (reading letters) | Apache-2.0 each | OpenCV team; Tesseract contributors |
| vLLM (serving models on our own Nebius endpoints) | Apache-2.0 | vLLM project |
| Hugging Face speech-to-speech | Apache-2.0 | Hugging Face |
| Vosk and its small English model (wake phrase) | Apache-2.0 | Alpha Cephei |
| segno (the settings QR code) | BSD-3-Clause | Lars Heuer |
| Tavily API (the web) | Tavily's terms of service | Tavily |
| National Weather Service API (the weather) | US government work, public domain | NOAA / NWS |
| Open-Meteo geocoding (the town's coordinates, once) | Free non-commercial use; data CC-BY-4.0 (GeoNames) | Open-Meteo, GeoNames |
| Atkinson Hyperlegible (the screens' typeface), bundled in `src/andy_companion/pages/fonts/` and served by Andy itself | SIL Open Font License (`fonts/OFL.txt`) | Braille Institute |
| Wikipedia's On this day (fetched at runtime, never stored in this repository) | CC BY-SA 4.0 | "According to Wikipedia" said aloud; "Wikipedia (CC BY-SA 4.0)" on the screen |
| The stories (`src/andy_companion/story_texts.json`): *The Aesop for Children* (1919), O. Henry's *The Four Million* (1906), Kipling's *Just So Stories* (1902) | Public domain in the United States; texts from Project Gutenberg with its header and licence removed, as its licence allows | The authors, named on screen as each story is read |
| Sample landscapes (`scripts/settings.py sample-photos`, downloaded only on request, never in this repository) | Unsplash License, via Lorem Picsum | Each photographer, credited on screen |
