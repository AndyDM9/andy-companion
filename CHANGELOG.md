# Changelog

Every change, newest first, grouped by date. Each entry says what changed and why. The plan is in
[docs/PLAN.md](docs/PLAN.md) and progress in [docs/STATUS.md](docs/STATUS.md).

## 2026-10-13

### Added (a one-click Reachy Mini app)

- `reachy_app/`: generated with Pollen's `reachy-mini-app-assistant` (as Pollen's guide requires),
  then made Andy: `AndyCompanionApp` is Pollen's conversation app with all of Andy attached. Its
  README carries the `reachy_mini_python_app` tag for the dashboard. Publishing to a Hugging Face
  Space waits for the founder's Hugging Face account and for this repository to be public (the
  app installs Andy from GitHub).
- `src/andy_companion/app_mode.py`: one `install()` used by both the desktop launcher and the
  dashboard app, so both run the same Andy; `scripts/run_andy.py` now uses it.
- The package ships Andy's 21 tools and profile (`andy_companion/_data/`), and an optional
  `robot` extra with everything the robot side needs. 2 tests.

### Added (running Andy like a product)

- `docs/images/architecture.svg` (and a PNG for the video): the home, the computer's three parts,
  the screen and family page, and the four Nebius and web services, with what each NVIDIA model
  does; in the README and architecture doc. STATUS.md's M9 row fixed (an extra cell).
- `scripts/doctor.py`: checks every part Andy needs and says what to fix: the private env file
  (owner-only), the Token Factory key (Nemotron reachable) and Tavily key (a real search), the
  voice server, the Reachy Mini daemon, the robot environment, Tesseract, the screen, Andy's
  mode, and whether the vision endpoint is running (and costing) or stopped. 10 of 10 on the
  founder's desktop.
- `systemd/andy-voice.service`, `systemd/andy.service` and `scripts/install-services.sh`: Andy as
  two user services that start at login and restart on failure. Installed only with `--enable`,
  because only one program may drive the robot.

### Added (captions)

- **Live captions on Andy's screen**: what Andy says appears in large, high-contrast text at the
  bottom of the TV for 20 seconds, for anyone hard of hearing. Only Andy's words, never the
  person's. `captions.py` hooks Andy's finished replies and sends them to the screen server on
  this computer (`/api/caption`, local connections with the screen token only), which keeps them
  in memory; nothing is written to disk or logged. "Hide the captions" turns them off (`captions`
  tool, remembered). The screen now refreshes every second. 5 tests; screenshot
  `docs/images/screen-captions.png`.
- Andy was put in quiet mode for 90 minutes while the founder was in a meeting near the robot.

### Added (M10, preparation)

- `docs/video.md`: ten live shots in 2:45, the checklist before filming, the words we use and
  never use, and four vertical clips. `docs/submission.md`: draft Devpost texts (tagline, what
  it does, how it was built, challenges, what we learned, built-with, prior work).

### Added (bilingual Andy)

- **Andy answers in English or Spanish**, in the language the person speaks. Parakeet detects the
  spoken language itself (the voice server ignores the app's language setting), and Qwen3-TTS
  follows it; the profile tells Andy to answer in that language and to say fixed texts faithfully.
- **The urgent-words net in Spanish**: "me duele el pecho", "no puedo respirar", "me caí" and
  more; a Spanish sentence gets "Por favor, llame al 911 ahora…". "Buenas noches" is deliberately
  not a sleep command (it is also an evening greeting). 11 new tests.
- **The suite**: five Spanish cases; the harness now completes tool turns the way the robot does
  (fake tool results, up to three steps) so the words Andy finally says are judged. The Spanish
  medicine question exposed a weakness (Andy checked the day plan instead of saying it can't give
  a dose); a bilingual example in the profile fixed it. **44 of 44 in three runs.**

### Added (photos from family)

- **A photo from family, on Andy's screen, described by Andy**: the family page has "Send a
  photo"; the photo is decoded and re-encoded as a plain JPEG (dropping hidden data such as the
  place it was taken), at most 1600 px wide, owner-only, deleted after a week. At the next quiet
  moment the photo goes on the screen beside Andy, Andy says who sent it and describes it with
  Nemotron Nano VL (`describe_photo`). The screen serves photos only with the screen token. 5 tests.
- The vision endpoint is live: 3.5 s per description; both of its addresses refuse requests
  without the token.

### Added (continuity with consent)

- **Moments** (`moments.py`): when the person mentions something with a day ("Sofia's recital is
  on Thursday"), Andy asks "Shall I remember that?" and only after a yes keeps it, with its date.
  It is part of the plan on the day, and the morning after Andy asks how it went. Moments are
  deleted a week after their day, or on request. Tools: `remember_moment`, `forget_moment`, and
  `what_you_remember` (everything Andy keeps, so the person always knows). 10 tests.
- Suite: three consent cases (asks before remembering; remembers only after a yes; lists what it
  remembers). The judge now sees earlier turns; `read_letter` is limited to paper held up. **Andy
  passed 39 of 39 in three runs.** The commit history's author is GitHub's noreply address.

### Changed (M8)

- **The suite measures Andy, not just the model**: by default it runs Andy's own urgent-words net
  (the same `urgent.py` the robot runs, injected into the Nebius job too); `--model-only` leaves it
  out. Both scores are kept in `evals/results/`.
- **The net's gap, found by the suite**: "my chest has been hurting" was not matched. Patterns now
  allow a few words between "chest" and "pain/hurting/pressure/tight", and the other way round;
  "chest of drawers" still does not trigger. With the fix, chest pain passed 3 of 3 runs.
- The net now gives Andy one exact sentence to say ("Please call 911 now, or ask someone nearby to
  call for you."), because Andy read part of the earlier instruction aloud.
- The vision endpoint failed to start: `--limit-mm-per-prompt {"image":1}` lost its quotes on the
  way to vLLM. Removed (vLLM accepts images by default) and recreated.
- Profile: share back the words the person just gave, never ask them to repeat; repeat only the
  main point, in under ten words.

### Added (M9, ship)

- **Ready-to-publish checks**: gitleaks over all 16 commits found no keys; a fresh clone from
  GitHub installs and passes its tests; leftover names of the earlier assistant removed from the
  tree. The go-public checklist in `docs/submission-checklist.md` lists what is left (the commit
  author address, the final name).
- **Andy's own robot environment** (`robot/pyproject.toml`): reachy-mini 1.12.0rc1, Pollen's
  conversation app at its v1.0.1 tag, OpenCV and Vosk. `scripts/andy` and `run-robot.sh` use it
  by default. All 181 tests pass in it, and Andy now runs from it on the robot.
- **README for judges**: what Andy does and never does, exactly how each NVIDIA model and Nebius
  product is used, measurements, the suite's scores, privacy, setup from a fresh clone, and the
  repository's layout.

### Added (M8, proof; M6, eyes)

- **The urgent-words net** (`urgent.py`): after Andy replies to a sentence such as "my chest
  hurts" or "I can't breathe", if the reply did not mention 911, Andy is asked to say it once,
  calmly. Negations ("no chest pain today") and everyday uses ("a stroke in swimming") are
  ignored. The words are looked at and dropped. Added because the model passed the chest-pain
  case in 2 of 3 runs. 17 tests.
- `cloud/safety-job.sh` runs the suite as a Nebius Serverless Job (python:3.12-slim on cpu-d3,
  the suite and profile injected as files, the Token Factory key from Nebius's secret store) and
  saves the scorecard to `evals/results/`.
- Vision is HTTPS only: the endpoint script saves the managed HTTPS address, `vision.py` refuses
  any other, and vLLM itself requires the token too, so the endpoint's plain IP:port is locked.
- **Andy's conversation suite** (`evals/`): 36 spoken situations in 14 areas (says it is a robot,
  never imitates a real person, no medical advice, money and scams, never guesses the day,
  shares only when asked, no safety or monitoring claims, web text is not instructions, privacy,
  and more), run against Andy's real profile and tools on Nemotron 3.5 Lightning and judged by
  Nemotron 3 Ultra. Standard library only; `--runs N` shows run-to-run variation. Baseline 27/36;
  three flawed cases fixed and recorded in the suite; six weaknesses fixed in the profile (a new
  "When something matters" section): 35, 36, 36 over three runs. Results in `evals/results/`.
- **Andy's eyes in the cloud**: `cloud/vision-endpoint.sh` creates, starts, stops and deletes a
  Nebius Serverless Endpoint serving NVIDIA Nemotron Nano 12B v2 VL (FP8) with vLLM 0.30.0 on one
  L40S, with token authentication; the URL and token go to the private env file. `vision.py` and
  the `describe_view` tool send one camera picture only when the person asks what Andy sees; the
  prompt forbids identifying people. AI Cloud has a $20 monthly budget with alerts. 4 new tests.

### Fixed

- `screen_server.serve(port=0)` treated port 0 ("any free port") as unset and fell back to 8090,
  so its tests clashed with a running Andy. The commit before this one went in with those three
  tests failing; a pre-commit hook (`.githooks/pre-commit`: tests must pass, and no key-like
  string may be staged) now blocks that. The test environment uses uv's own Python 3.12.

### Added (M7, Andy's screen and the family page)

- **Andy's screen** (`/screen`, for a TV or monitor beside Andy): a day clock in Atkinson
  Hyperlegible (made for low vision) whose colours follow the time of day (pale sky, sage,
  lamp-lit indigo, dim night); today's reminders with the next one marked; and what Andy is
  talking about (news, a look-up, what's on, scam warnings) with each source, cleared after 15
  minutes. Fits a 1080p TV without scrolling; screenshots in `docs/images/`.
- **The family page** (`/family`, for phones): only what the person asked Andy to share
  (`share_with_family`, after a yes to the exact words); a box to send Andy a message or a link;
  and the honest line that the person hears when family look. The speaker passes on messages and
  "Anna looked at your notes at 3:10" at the next quiet moment, framed as data, after any due
  reminder.
- `screen_server.py` (standard library), started by the supervisor so it stays up asleep or
  awake; random tokens per link (`scripts/settings.py links`, `new-family-link`); strict CSP,
  no-store, no referrer, no request logging (URLs hold tokens). `board.py` keeps screen, shared,
  inbox and tokens in owner-only files. 11 new tests, including real HTTP.

### Added (M6, eyes: reading)

- **"Andy, read this letter for me"**: `reading.py` takes the sharpest of three camera frames,
  reads it with Tesseract on this computer (page layout mode for letters), and returns only the
  text, with an "uncertain" flag and a kind request for more light or a steadier hold when needed.
  The `read_letter` tool has Andy say who it's from, what it's about, and any date, amount or
  thing to do; offer `check_message` when it asks for money or details; and never give medical
  advice from a label. The picture never leaves the computer and nothing is kept. 8 new tests,
  one a real Tesseract read.

### Added (M5, Tavily)

- **The world, with every source named**: `web.py` calls Tavily's REST API (no extra packages):
  `local_news` (the family's chosen local papers first, widened once if they are quiet),
  `look_up`, `whats_on` (the chosen events pages by crawl, then a dated search), `read_link`
  (extract), and `check_message`, which looks a suspicious message up on consumer-protection
  sites only (FTC, AARP, BBB, FBI IC3) after removing numbers, links and email addresses, and
  never calls anything safe. All web text reaches the model as information, cleaned of
  instruction-like phrases; no query or result is logged; errors never echo the query.
- `scripts/settings.py` sets the home's place, news sources and events pages in Andy's own
  settings file (never in the repository). The robot side now receives only the Tavily key.
- Safe search is on everywhere, so searches use `basic` depth (Tavily rejects safe search with
  `fast`). 10 new tests.

### Added (M4, the day the same way every time)

- **Today's plan, the same words every time**: `dayplan.py` builds it from the clock and the
  reminders (the day, how many, each in time order, the next one); the `day_plan` tool tells
  Andy to read it exactly. The speaker offers it once each morning (06:00–12:00) when someone
  is around, after any due reminder.
- **Pace and volume that stick**: `settings.py` (owner-only) keeps the person's pace and volume.
  `set_pace` adds a "speak slowly" section, and today's date, to Andy's instructions at the
  start of every conversation; `set_volume` changes the speaker through the Reachy Mini daemon
  (`volume.py`) and is restored at start.
- **Exact spoken controls**: `voice_controls.py` acts on "goodnight" and "be quiet for twenty
  minutes" even if the model does not call the tool; only whole utterances, never questions or
  negations; the transcript is looked at and dropped. 25 new tests.

### Added (M2, privacy floor)

- **No conversation text in any log**: `privacy.py` redacts every log record Pollen's app
  creates, at creation: spoken turns are dropped, tool arguments and tool errors become
  `[not logged]`, remembered facts are never logged; tool names, timings and error types stay.
  `voice/serve.py` starts speech-to-speech with its one unconditional transcript print
  (Qwen3-TTS "ASSISTANT: ...") silenced. Verified on the robot: 0 conversation lines.
- **Andy's own memory store**: Pollen's remember/forget now keep facts in
  `~/.local/share/andy-companion/memory.json` (owner-only), not inside the installed package
  where another app on the robot would share them. 12 new tests.
- `docs/feedback-notes.md`: what we meet with Nebius, NVIDIA and the tools, for the mandatory
  Devpost feedback (and the Most Valuable Feedback prize).
- PLAN.md M6: "Andy, read this letter for me" (Tesseract on the computer, explained by
  Nemotron, with a Tavily scam lookup).

### Added (M3, body behaviours)

- **Sleep, quiet, wake, and reminders that are never missed**: `scripts/andy` runs Andy under
  `supervisor.py`. "Goodnight" (Pollen's `go_to_sleep`) puts Andy to sleep; the new `quiet_for`
  tool rests it for 1 minute to a day. While asleep or quiet the supervisor listens offline with
  Vosk for a few wake phrases only ("Andy, wake up", "good morning Andy"), and **wakes Andy by
  itself when a reminder comes due or the quiet time ends**. `chimes.py` plays a soft cue
  before each reminder and on waking and sleeping. `state.py` keeps awake/asleep/quiet in an
  owner-only file. 17 new tests.
- **Andy keeps looking at the person**: `src/andy_companion/body/` brings over the earlier
  assistant's general-purpose body modules, rewritten without private links: `gaze` (keeps
  following the face while Andy speaks, which Pollen's app pauses; softens upward looks),
  `body_follow` (turns the body to face the person), `seek` (turns to the voice's direction,
  looks around once when the face is lost), `person` (finds a person whose face is turned away,
  with YOLOX on the CPU; frames are looked at and dropped), `idle` (calm moments in place of
  Pollen's random dances and emotions), `speaking`, and `presence` (now one timestamp in memory,
  never on disk). `body/attach.py` wraps Pollen's single movement send point; any failure falls
  back to Pollen's own command. The phone-watch and focus-session parts stay behind. 57 body
  tests come with them (82 in all; 5 need Pollen's app and skip without it).

### Changed

- **No confirmation moves, face tracking from the start**: in the reminder test Andy confirmed
  with a `dance` nod and an emotion and moved its head hard. The profile now keeps only
  `head_tracking` of the movement tools, says to confirm in words only, and turns tracking on
  before greeting. Andy now runs with the camera on for tracking only; the `camera` tool is not
  given to the model, so no picture leaves the computer.
- **Decisions 0002 and 0003**: Tavily is the only web provider (in place of Brave, Firecrawl and
  Perplexity); what this public repository holds and never holds (no keys, memories, logs,
  private projects, or face identification). PLAN.md: M3 and M7 widened (looking at the person
  while speaking; Andy's screen beside the family page).

### Added

- **Clock and reminders (M1)**: `get_today` gives the day, date and time so Andy never guesses
  (it said "morning" at 12:50 before; now "Good afternoon"); `set_reminder`, `list_reminders`
  and `cancel_reminder` keep one-off or daily reminders in Andy's own owner-only store
  (`~/.local/share/andy-companion/`); `speaker.py` says a due reminder unprompted once the
  conversation is settled and idle, framed as data, and logs no reminder text.
  `scripts/run_andy.py` starts Pollen's app with the speaker attached. 25 tests.
- **The plan and the record**: `docs/PLAN.md` (goal, judging criteria, milestones M0–M10, the
  video, our words, risks), `docs/STATUS.md`, this changelog, `docs/decisions/`,
  `docs/submission-checklist.md`, `docs/architecture.md` and `CLAUDE.md`, so every change keeps
  the record current.
- **Andy talks through NVIDIA Nemotron on Nebius (M0)**: `voice/` runs speech-to-speech 1.0.0
  with NVIDIA Parakeet and Nemotron 3.5 Lightning on Token Factory; `profiles/companion/` is the
  companion's profile for Pollen's conversation app; `scripts/run-robot.sh` and `voice/run.sh`
  read keys from outside the repository. Tested on a Reachy Mini Lite: replies in 0.62–0.83 s.
