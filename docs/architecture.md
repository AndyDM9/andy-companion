# Architecture

**Last updated 2026-10-26.** How Andy's parts fit together, for anyone reading or changing the code: the robot, the
home computer, Nebius and the web; what each module owns, and what it must not reach into.

![How Andy works](images/architecture.svg)

The text diagram below shows the voice path in detail.

```
            ┌──────────────────────── the home ────────────────────────┐
 person ──▶ │ Reachy Mini (mics, camera, head, antennas, body)         │
            │      │ audio                     ▲ moves                 │
            │      ▼                           │                       │
            │ Pollen conversation app + profiles/companion + tools/    │
            │   (scripts/run_andy.py attaches the reminder speaker and │
            │    body/: gaze, follow, seek, person, idle, glance)      │
            │      │ OpenAI Realtime protocol (ws://127.0.0.1:8765)    │
            │      ▼                                                   │
            │ voice/: speech-to-speech                                 │
            │   Silero VAD + Smart Turn (end of turn) →                │
            │   NVIDIA Parakeet (speech to text) → LLM client →        │
            │   Qwen3-TTS (text to speech)                             │
            └───────────────│──────────────────────────────────────────┘
                            ▼ HTTPS, zero data retention
              Nebius Token Factory: NVIDIA Nemotron 3.5 Lightning

 Also on this computer, offline: Vosk (the wake phrase, English and Spanish), Tesseract (reading a letter; only
 its text leaves), YuNet on ONNX Runtime in Pollen's software (finding a face to follow, never recognising it), and
 NVIDIA Cosmos Reason 2 (local vision; conversation still requires Token Factory). The full list, with what each is for and what we
 measured: the README's "Every model, and where it runs".

 tools/ (local_news, look_up, whats_on, read_link, check_message, look_into; setup: events page)
      ──▶ HTTPS ──▶ Tavily (search, extract, crawl, map, research); safe search on every search,
                    Spanish pages first for a Spanish speaker, credits reported for the screen
 check_message ──▶ Nemotron 3.5 Lightning (the message's own sign) + Nemotron 3 Ultra (each Tavily
                    warning: the same trick, not merely the same topic)
 find_object, describe_view, describe_photo ──▶ Nemotron 3.5 Super VL on Token Factory (ANDY_VISION; or Nano VL
                    on our own Serverless Endpoint, started on demand); describe_view sends the view at 1280 across
                    with its middle at full detail, find_object zoomed tiles and a closer look, turning the body
                    past the head's reach (decision 0016)
      └─ unreachable, with ANDY_VISION_FALLBACK=local ──▶ Cosmos Reason 2 (2B, or 8B on this desktop) on this computer
                    (local-eyes/run.sh, vLLM on 127.0.0.1:8095, the second GPU; or always, ANDY_VISION=local)
 guard ──▶ Nemotron 3.5 Content Safety on a Nebius Serverless Endpoint, beside each reply
 think_it_through ──▶ Nemotron 3 Ultra on Token Factory
```

## Running

On the desktop both halves run as user services (`scripts/install-services.sh`: `andy-voice.service` runs
`voice/run.sh`, `andy.service` runs `scripts/andy`, and `andy-eyes.service`, once `local-eyes/` is set up, runs the
offline eyes), restarted on failure and not started at login unless
enabled. A stop goes to the supervisor only (`KillMode=mixed`), which lets the app put the robot to sleep
first. `systemctl --user stop andy andy-voice` frees the computer for other work.

`scripts/andy` starts `supervisor.py`, which runs the app (`scripts/run-robot.sh` →
`scripts/run_andy.py`) while Andy is awake. When Andy sleeps or is quiet, the app stops and the
supervisor listens for a wake phrase (Vosk, offline), and wakes Andy when one is heard, when the
quiet time ends, or when a reminder comes due. A reminder wakes Andy only until it has been said and the
talk is over (60 s with nobody speaking); then Andy goes back to sleep or to the rest of the quiet. For
10 minutes after "goodnight" or "be quiet", a reminder already due but not yet said waits. The supervisor
reads the Tavily key from the env file for the setup page's events finder (never the model key). A watchdog
in the app (`watchdog.py`) asks the supervisor for a restart when the microphone keeps dropping audio, notes
speech left unanswered, and writes counts only to `health.json`.

Two ways to run the same Andy, both through `andy_companion.app_mode.install()`: on a computer
under the supervisor (`scripts/andy`), or as a Reachy Mini dashboard app (`reachy_app/`, no
supervisor: no wake phrase; the dashboard starts and stops it; it reads the env file itself, and its
watchdog only logs).

Both app entry points load allowlisted settings with `app_mode.read_env` / `load_env` before
configuring the voice connection; the desktop shell does not parse keys. The doctor shares that
parser, existing environment values win, and the supervisor, app, doctor and link command use the
configured screen port (decision 0020). The link command reads only the port, never API keys.
The doctor probes the configured voice host/port, with `HF_REALTIME_WS_URL` taking precedence over
`ANDY_VOICE_URL`, as in the app. This is TCP availability, not audio or WebSocket authentication.
Its single-controller check fails when socket/process inspection is unavailable or ownership is hidden;
it never treats an unknown connection as proof that Andy is the only controller. Preflight results
remain separate from observing spoken tasks and motion on the robot.

The fact tool is `remember_fact`, a unique external name: Pollen rejects a module named `remember`
because it already has one (decision 0021). The dashboard defers Pollen's main import until Andy's
configuration is set. CI also loads the real SDK configuration in fresh processes, without hardware.
The runtime registry has 38 profile tools and the SDK's `task_status` / `task_cancel`; the text suite
covers the profile tools. The sample demo refuses imported or cached household modules before seeding
any data, and requires its own new temporary store; it must never replace a live household's links.

## Parts, and what each owns

| Part | Owns | Must not |
|---|---|---|
| `voice/` | Hearing, end-of-turn detection, the model call, speaking | Store audio or text; hold keys in the repository |
| `profiles/companion/` | Who Andy is, how it speaks, what it never does, which tools it may use | Contain any person's data |
| `tools/` + `src/andy_companion/` | The companion's own abilities: the clock, reminders and the speaker that says a due reminder unprompted | Move the robot except through the app's movement tools |
| `src/andy_companion/body/` | Where Andy looks and turns: following the person while speaking and listening, finding them by voice or by sight, calm idle moments, the antennas' thinking lean, a glance at the TV when something new shows on it (`glance.py`: only once the screen's place is set, never while the person speaks); what the head is turned to for the TV's line (`looking_at.py`: you, the screen, the room or pointing, set by each move for as long as it lasts) | Store any frame, image or identity; send a picture anywhere |
| `board.py`, `transient.py`, `screen_server.py`, `pages/` | Cards and research in server memory, reached by the app over authenticated loopback HTTP, never files (decision 0019); Andy's screen and the family page: what is shown, how it looks (the time of day's colours, glass or the calm screen), what the person shared, messages and looks from family; captions paged over the foot of the screen; how each web answer was found; the gear menu (the settings code, Under the hood); "Try asking" when the screen is quiet; a static English/Spanish spoken-example guide, opened locally without a tool call. Finder progress uses the same memory-only card flow, with a private per-search ID, allowlisted stages, captured-view counts and a renewable 45-second expiry; old progress/cleanup cannot replace a new card (decision 0025). Four private links, each with its own token: screen, family, settings, hood. `READ_ONLY` and `INDEX` exist only for the public demo (`scripts/demo_screen.py --public`, `space/`, decision 0010): every POST refused, a front page at `/` Served on the home network only: a client outside private, loopback, link-local or home-VPN (100.64/10) addresses is refused, the public demo excepted; family sends are limited to 20 a minute; a photo's size is read from its header before it is decoded (2026-10-25). | Show or share anything the person did not ask to share; log a URL or token; let the hood link reach the screen or the settings |
| `setup_page.py` (+ `/setup`) | What a helper may change from a phone (town, news sites, what's-on pages, language, pace, volume, captions), its checks, and telling the person who changed what | Change reminders, memories or what is shared; change anything without a name and a notice to the person |
| `live.py` | What Andy is doing right now (ready, hearing, thinking, working with the tool's name, speaking), and what its head is turned to (one of four names from `body/looking_at.py`), sent to the screen server on change | Send words or tool arguments |
| `kept.py` | Persistent items and pending messages/research, listed and deletable; delete everything also clears the card, captions and views | Delete without a name and a notice to the person |
| `consent.py` | Per-conversation, one-use permission bound to exact tool arguments and a spoken readback, expiring after two minutes (decision 0018). Explicit requests can save one item directly; sharing always requires confirmation. Before any memory proposal or dispatch, recognised labelled credential values are refused without repeating them, including explicit requests; all four memory-tool names share the check (decision 0029). This limited check does not classify unlabelled secrets or other write paths. The first offered save or share is only a proposal; its tool runs after the matching confirmation. The tool wrapper rejects changed content and reused permission. Before `read_letter`, it also checks the existing latest utterance for a narrow already-spoken/quoted-message pattern and returns a non-camera result before OCR can run (decision 0028); explicitly held/printed pages retain the camera path, with negated page cues and introduction-level camera refusals respected. | Keep or log the words beyond the check |
| `health.py` | The hood page's health tiles: daemon, voice server, Andy's mode, weather, Tavily credits, Nebius endpoints | Read keys or words; hold up a page while checking |
| `turns.py` | How long each turn and each tool took, for the `/hood` page | Keep or send a word, a tool argument or anything but numbers, tool names and which eyes answered (one of three names) |
| `reading.py` | Reading a page held up to the camera, on this computer | Send or keep the picture |
| `onthisday.py` | Today's date in years gone by from Wikipedia: gentle items only, by a word filter and then a Nemotron check (once a day, cached); credited on screen | Offer anything unchecked; send anything but the date |
| `fun.py` | Jokes and riddles from a chosen set, never repeated within a month (`fun.json` holds joke numbers and times only) | Make up a joke; keep anything the person says |
| `stories.py`, `story_texts.json` | Public-domain stories read a part at a time, with a bookmark for another day (`story.json`: which story, which part); a story about something in particular is the model's own, said to be made up | Recite a story from memory; keep anything the person says |
| `body/giggle.py` | After a joke's punchline, a one-second antenna wiggle once Andy's voice stops | Move the head; move while the person speaks |
| `letters.py` | The page as a large-print card on the screen: Nemotron 3.5 Lightning fills a fixed schema; code adds the warning from the page's own words, keeps a scam's demand off the to-do, shows no medicine dose and masks account and phone numbers | Act on the page's text; show a dose; show a number that identifies someone; keep the card past the screen's usual five minutes |
| `urgent.py`, `urgent_audio/` | The deterministic net: urgent medical words get 911, crisis words get 988, in English or Spanish, if Andy's reply missed it; a negation counts only when it governs the words; when the model can't be reached or still leaves the number out, the sentence plays from a recording on the robot | Keep or log the words; claim to watch over anyone |
| `guard.py` | The second look: the person's words checked by Nemotron 3.5 Content Safety on a Nebius endpoint, beside Andy's reply; 988 if self-harm was found and the reply missed it | Delay a reply; keep or log the words or the result; act on any category but self-harm |
| `looking.py` | "Look into it": Tavily research streamed in the background, each step on the screen, the answer left for Andy to say; one at a time, ten a day; stopped at once when asked (`look_into` with `stop`, or "be quiet"); never started again by its own answer (none within 30 s of an answer, nor the same question within 10 minutes) | Log the question; act on the answer without a yes; retry a stopped research |
| `weather.py` | The forecast and alerts for the town from the National Weather Service; the town's coordinates, looked up once; on the TV, the town as the card's title, one line a period, an alert as what and until when | Send anything but the town and its coordinates |
| `web.py` | Tavily calls; cleaning web text into information; scrubbing messages before a scam check | Log a query or result; send numbers, links or emails from a message |
| `dayplan.py`, `settings.py`, `volume.py`, `voice_controls.py` | Today's plan in fixed words; the person's pace and volume; exact spoken controls, in English and Spanish | Keep any transcript; let the model reword the plan |
| `speaker.py` | Saying what is due at a quiet moment: reminders, the morning plan, family messages (with a note on the TV), a family suggestion of a reminder ("Shall I set it?", set only after a yes; the answer never goes back to the family), research answers | Speak while the person is speaking; set anything without a yes |
| `supervisor.py`, `state.py`, `wake.py`, `chimes.py` | Awake, asleep and quiet; waking by phrase, time or due reminder; soft cues | Listen while the app is running; send or keep any audio |
| `watchdog.py` | Noticing when Andy has stopped hearing well (audio drops), asking the supervisor for a restart, and counts for the hood page | Keep or log words; restart without a supervisor to bring Andy back (the dashboard app only logs) |
| `scamcheck.py`, `tools/check_message.py` | Whether a message read aloud shows a known scam's sign (Lightning, quoting the message) or uses the trick a Tavily warning describes (Ultra); the TV's receipt (what to do first, then three steps: the sign, the warning and its site, linked to the warning's page, why they match); saying plainly when the warnings couldn't be checked | Send the message's numbers, links or emails to Tavily; say "no sign" when the lookup failed |
| `finder.py`, `vision.py` | Choosing the eyes (`vision.eyes`: Nemotron 3.5 Super VL on Token Factory by default, Nano VL on our endpoint with `ANDY_VISION=endpoint`, Cosmos Reason 2 2B on this computer with `ANDY_VISION=local`, or off; decision 0011); every picture through `vision.answer`, which falls back to Cosmos here when the eyes can't be reached and `ANDY_VISION_FALLBACK=local` (never on a refusal), and records which eyes answered for the hood (decision 0015; a turn that used the eyes carries the name, one of three, to the screen server in the supervisor's process); a family photo with how to talk about it (one open question, a story kept only after a yes); sweeping the room, reading each of four views as six zoomed tiles at once, turning to look closer at the best sighting within the head's reach and checking a close-up, then pointing with the head (decision 0012); the four views (480 px) in the screen server's memory for two minutes (`POST /api/views` from this computer, `GET /view` for the TV, screen token), shown as "what Andy looked at" with the chosen one marked, also when nothing was found; failing in seconds when the endpoint is stopped; keeping tries for scoring only when `ANDY_FINDER_RECORD` is set | Keep a view on disk or in a log; describe people |
| `places.py`, `tools/remember_place.py`, `tools/forget_place.py` | Where the person's things are, kept only after a yes (consent gate): the thing, the head's direction, Andy's words, the time; a find remembered in memory only for six hours; `finder.find` looks there first | Keep a picture; keep anything without a yes |
| `gestures.py`, `tools/gesture.py` | Moves taught by hand with the antennas: limp antenna motors for six seconds, the movement trimmed, smoothed and capped at 1.8 rad/s, kept by name, played back; the motors come back on under a move that starts where the hand left them | Turn the head's motors off; move faster than the antennas' limit |
| `body/wave.py` | A wave beside the tracked face (OpenCV picture differences, 8 a second), answered by the antennas | Keep or send any picture; act while anyone speaks or during a search |
| `body/hold.py` | During a search, the head is the search's alone: seek, face following, the glance and idle hand-back stand down | — |
| `body/seek.py` (second speaker) | A voice well to the side of the face Andy follows turns the head to it; nobody there, back | Turn while Andy speaks; turn twice to the same empty direction within a minute |
| `sim/finder_sim.py`, `cloud/sim-job.sh` | The finder in Pollen's MuJoCo scene from a virtual eye, many trials, locally or as Nebius Serverless Jobs (decision 0013) | Run on the robot; keep pictures |
| `deeper.py` | "Think it through": a hard question handed to Nemotron 3 Ultra | Decide for the person |
| `captions.py` | Andy's own words to the screen as captions | Send the person's words |
| `scripts/demo_screen.py`, `space/`, `scripts/space.sh` | The screens on sample data, on this computer or as a public read-only Hugging Face Space (decision 0010) | Hold a key or a real person's data; take anything a visitor sends; run on the robot |
| Pollen's conversation app (dependency) | The robot connection, movement, tool calling | — (not forked, files unmodified; Andy hooks in at start through `app_mode.install`, wrapping a few of its methods) |

## Data

- Keys live in `~/.config/companion-hackathon/.env` (mode 600), outside the repository.
- Nebius Token Factory runs with zero data retention switched on.
- No recording or transcript is stored. Owner-only in `~/.local/share/andy-companion/`: what the person
  asks Andy to remember (`memory.json`, `moments.json`, moments for 7 days), their reminders
  (`reminders.json`), notes shared with family (`shared.json`), family messages
  waiting to be said (`inbox.json`), family photos (`photos/`, 7 days), settings (`settings.json`), the
  story bookmark (`story.json`) and joke numbers (`fun.json`). Cards and research questions and answers live only in the screen server's memory. The app uses authenticated loopback HTTP (`transient.py`, decision 0019), with no disk fallback. Old
  `screen.json` and old disk-backed research entries are removed on startup.
- Captions of Andy's own words live only in the screen server's memory, for three minutes (long enough to read a story's part along to the end), never on disk or in a log.
- Turn timings (numbers and tool names only) live only in the screen server's memory, last 40.
- The services' journal holds the same redacted log lines: timings, token counts and tool names, no words
  (checked 2026-10-14).
- Finder tries (the four views and close-ups at full size, what the model said, the head's angles, the times) are kept only when
  `ANDY_FINDER_RECORD` names a folder, for the founder's own test sessions, owner-only; deleted after
  scoring.

## Evaluation

- `scripts/check_video.py`: optional local production check using ffprobe metadata only. It checks
  container/video-track duration and track presence, without extracting frames, transcribing audio,
  changing media or uploading it. Audio padding and unknown video-track duration cannot pass as
  a minute of hardware video. A passing report always retains manual content/rights/visibility checks
  (decision 0024); this is not a robot or hosted-service dependency.
- `scripts/check_vision_recovery.py`: camera-only IPC reader with a process-local, unreachable loopback
  primary and local Cosmos fallback. It never instantiates a robot controller or loads provider keys;
  output contains status, source hash and timings, never the frame or description. The shared vision
  path checks fallback transport as well as primary transport; local modes require loopback. A stopped
  optional endpoint can bypass its failed network request, and its 404 can fail over; a Token Factory
  model-not-found response or refused request does not. This is independent of voice and hood verification.
- `scripts/devpost.py --ref hackathon-submission --final`: rejects a placeholder/non-video YouTube
  address, absent local release tag, app dependency still on main, or oversized form fields, then
  requires tracked files and the three export inputs to match the tag's snapshot before it
  checks public links. It reads repository metadata only; it does not submit anything or certify video
  rights, visibility, duration or hardware behavior. Judge access separates sample preview, optional
  own-key reproduction and author-funded robot testing (decision 0022).
- Guided judge inference (decision 0023) is a separate standard-library HTTP process and Docker Space.
  It loads the public companion profile, one allowlisted tool schema per example and the actual consent
  gate. Fixed challenge/choice IDs are its only inputs. Nemotron on Token Factory selects tools and replies;
  camera, OCR, search and family effects are simulated in isolated RAM. No household settings, store,
  SDK, camera or motor tool is loaded. Exact confirmation is displayed before a fresh Yes/No choice.
  Credentials stay in the Space secret; capped sessions expire even while idle. Concurrency, request size,
  token count, tool rounds and provider calls are bounded. The original screen Space stays read-only.
  The guided Space is `andydm/andy-companion-judge`; the screen preview links to it explicitly as a
  separate service, and public metadata exposes the model/profile/tools/prompt hashes, never credentials.
  Static GET routes ignore cosmetic query strings such as the host iframe's `__theme`; those values
  are never sent to the model. POST still accepts only the exact challenge endpoint and fixed ID/choice fields.
- `docs/judging.md`: the short testing path from the README, public demo and submission text.
  CI starts the real public demo in a separate process with throwaway sample data, probes pages,
  assets, tokens and write refusal, then checks cleanup. CI also builds a wheel and checks its
  pages, fonts, audio, profile and tools from an isolated installation with checkout imports disabled.
- `evals/run_suite.py`: 97 text-based conversation and tool-selection cases, the real profile, tool
  definitions, confirmation gate and urgent-words net, with synthetic tool results, judged by Nemotron
  3 Ultra. It does not run a microphone, camera or motors. Run locally or as a Nebius Serverless Job
  (`cloud/suite-job.sh run`); input and code hashes accompany new scorecards.
- `evals/physical_trials.py`: a fixed 30-attempt plan for the real finder; manual outcomes and timings,
  all attempts retained, confidence intervals, no speech or pictures. A score requires all 30.
- `evals/scam_eval.py`: the scam check five ways: word rules alone (`--word-rules`), and Lightning and Ultra each alone and with Tavily's warnings; Tavily fetched once
  per message and the models run three times as Nebius Serverless Jobs, two at a time
  (`cloud/scam-job.sh`; a job's request may hold 64 KB, so four parts).
- `evals/finder_eval.py`: the finder scored from recorded tries against the person's own labels.
- `evals/zoom_check.py`: the finder's own code on 18 frames of one room photo, the old way against zoomed tiles and
  the closer look (decision 0012).
- `sim/finder_sim.py` and `sim/replay.py`: Andy's search in Pollen's MuJoCo scene, scored against the scene's truth,
  as Nebius Serverless Jobs (`cloud/sim-job.sh run`, decision 0013); and the film of one search.
- `evals/eyes_check.py`: the two vision models side by side at the desk (decision 0011).
- `evals/robot_timings.py`: the robot's real turns, from Andy's own log, numbers only.
- `evals/guard_check.py`: the second look (Content Safety) on written sentences the word list misses.
- `evals/build_tools.py`: writes `evals/tools.json`, exactly the tools the robot gives the model.
- `scripts/doctor.py --live`: the health check before filming.
- No log line holds conversation text: `privacy.py` redacts the app's records as they are made,
  and `voice/serve.py` silences the transcript prints of every console in the voice server ("USER:",
  "ASSISTANT:" and, since 2026-10-25, "Live:"). The filter is not trusted alone: `scripts/doctor.py --live`
  reads the last day of the voice log and fails on any line that is not one of the kinds it may write
  (decision 0017).
- A reminder's words are kept as said, less a time at their end ("take a pill at eight" is kept as "take a
  pill", its time kept as the time); lists on the screens show them in sentence case.

Preflight (`scripts/doctor.py --live`, decision 0026) tests configured cloud-vision availability
with a fixed invented text-only request, at most eight output tokens and a 15-second timeout. It
reports status only; catalogue membership does not determine availability. It neither captures a
camera frame nor establishes visual quality. A camera-only local-fallback probe remains separate.

Requested camera-action response order (decisions 0027/0028): the profile/tools instruct the model to
dispatch the existing `find_object` or `read_letter` before preliminary speech. There is no separate keyword-driven movement path;
the same tool, camera checks, body ownership, transient progress and result flow remain in use.
