# Architecture

**Last updated 2026-10-28.** How Andy's parts fit together, for anyone reading or changing the code: the robot, the
home computer, Nebius and the web; what each module owns, and what it must not reach into.

**In short, three paths:**
- **A spoken turn:** the robot's microphones → NVIDIA Parakeet on this computer → NVIDIA Nemotron 3.5 Lightning on
  Nebius Token Factory, which answers or calls one of Andy's tools → Qwen3-TTS on this computer: a median 1.06 s from
  the words being understood to Andy's first sound, on the robot. The voice server speaks the OpenAI Realtime message
  format on this computer only; no OpenAI service is involved.
- **The eyes:** the robot's camera → NVIDIA Nemotron 3.5 Super VL on Token Factory (NVIDIA Cosmos Reason 2 on this
  computer if it can't be reached) → head angles → Andy turns, looks closer, checks and points.
- **The web:** a tool → Tavily → for a scam check, NVIDIA Nemotron 3 Ultra compares each warning with the message → a
  card on the TV that names its source.

**Decided in code, whatever the model says:** **Be careful** first on a risky letter; a letter's account, phone and
reference numbers never reach the model; one yes for one exact save or share; the 911 or 988 line on urgent words;
the date and time; going to sleep only when asked; when a memory offer is due (something coming up, a photo's
story) and that a time or date question asks the clock; a tool call the model wrote as text made as the call; and no conversation text in any log.

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
            │      │ Realtime-format WebSocket, local (127.0.0.1:8765) │
            │      ▼                                                   │
            │ voice/: speech-to-speech                                 │
            │   Silero VAD + Smart Turn (end of turn) →                │
            │   NVIDIA Parakeet (speech to text) → LLM client →        │
            │   Qwen3-TTS (text to speech)                             │
            └───────────────│──────────────────────────────────────────┘
                            ▼ HTTPS, zero data retention
              Nebius Token Factory: NVIDIA Nemotron 3.5 Lightning

 Also on this computer, offline: Vosk (the wake phrase in English, and in Spanish when Andy speaks Spanish), Tesseract (reading a letter; only
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

Under the desktop supervisor, an existing unreadable mode file pauses automatic wakes/restarts and
the current app stops through its normal control path (0040). Reads validate mode/deadline/return
metadata and leave the file intact; the offline listener requires an explicit wake, not a greeting.
A normal explicit mode change writes valid owner-only state atomically and restores operation.
Health/preflight show the problem, the status strip remains renderable, and no recovery copy or
payload log is created. A missing file retains the first-run awake default. This fault path can delay
reminders until corrected. Dashboard start/stop behavior remains manually controlled as below.

Two ways to run the same Andy, both through `andy_companion.app_mode.install()`: on a computer
under the supervisor (`scripts/andy`), or as a Reachy Mini dashboard app (`reachy_app/`, no
supervisor: no wake phrase; the dashboard starts and stops it; it reads the env file itself, and its
watchdog only logs).

Dashboard app startup writes a valid awake mode (0040), so a previous asleep/quiet state does not
mislabel the app the dashboard has just started. Supervised installation preserves the existing mode.

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

Optional display outline (0042): after the existing close-up confirmation and point are chosen,
`outline.py` can send that crop/label to an explicitly configured numeric-loopback mask service.
Validated numeric contours are painted on a separate screen copy; no SVG is rendered. Nemotron
confirmation/angles and the original recording frames are untouched. The annotated JPEG follows
the existing two-minute authenticated RAM-only view route; no new store/family path. The backend
is disabled by default, separately operated/licensed, and never started by Andy. The operator verifies
the backend's own local-processing/retention behavior; the client enforces its outbound loopback route.
Invalid, ambiguous
or unavailable masks leave the ordinary picture; cancellation while awaiting the worker prevents
late publication. It makes no physical-improvement claim. [Interface and limits](object-outline.md).

| Part | Owns | Must not |
|---|---|---|
| `voice/` | Hearing, end-of-turn detection, the model call, speaking | Store audio or text; hold keys in the repository |
| `profiles/companion/` | Who Andy is, how it speaks, what it never does, which tools it may use | Contain any person's data |
| `tools/` + `src/andy_companion/` | The companion's own abilities: the clock, reminders and the speaker that says a due reminder unprompted | Move the robot except through the app's movement tools |
| `src/andy_companion/body/` | Where Andy looks and turns: following the person while speaking and listening, finding them by voice or by sight, calm idle moments, the antennas' thinking lean, a glance at the TV when something new shows on it (`glance.py`: only once the screen's place is set, never while the person speaks); what the head is turned to for the TV's line (`looking_at.py`: you, the screen, the room, pointing, a voice, a wave, a closer look or a remembered place, set by each move for as long as it lasts) | Store any frame, image or identity; send a picture anywhere |
| `board.py`, `transient.py`, `screen_server.py`, `pages/` | Cards and research in server memory, reached by the app over authenticated loopback HTTP, never files (decision 0019); Andy's screen and the family page: what is shown, how it looks (the time of day's colours, glass or the calm screen), what the person shared, messages and looks from family; captions paged over the foot of the screen; how each web answer was found; the gear menu (the settings code, Under the hood); "Try asking" when the screen is quiet; a static English/Spanish spoken-example guide, opened locally without a tool call. Finder progress uses the same memory-only card flow, with a private per-search ID, allowlisted stages, captured-view counts and a renewable 45-second expiry; old progress/cleanup cannot replace a new card (decision 0025). Four private links, each with its own token: screen, family, settings, hood. `READ_ONLY` and `INDEX` exist only for the public demo (`scripts/demo_screen.py --public`, `space/`, decision 0010): every POST refused except the family page's look notice (accepted, kept nowhere), and a front page at `/`. Served on the home network only: a client outside private, loopback, link-local or home-VPN (100.64/10) addresses is refused, the public demo excepted; family sends are limited to 20 a minute; a photo's size is read from its header before it is decoded (2026-10-25). | Show or share anything the person did not ask to share; log a URL or token; let the hood link reach the screen or the settings |
| `setup_page.py` (+ `/setup`) | What a helper may change from a phone (town, news sites, what's-on pages, language, pace, volume, captions, family photos on the TV, the "Try asking" line, the night clock, the calm screen, where the TV is and glancing at it, afternoon offers, the welcome-back greeting and the person's name), its checks, and telling the person who changed what. Validate JSON shape/types for the whole batch before persistence, announcements, volume or background lookups (0034); preserve real false values, reject fractional integer controls and non-finite direction. | Change reminders, memories or what is shared; change anything without a name and a notice to the person; interpret malformed request values as consent to other settings |
| `settings.py`, `kept.py` | Validate saved settings and internal cache shapes under a shared reader/writer lock (0037). Preserve unreadable originals whole with unique owner-only filenames before returning defaults; failed preservation blocks replacement. The owner page explains default choices and lists metadata with existing authenticated single/all deletion and helper notices. Legacy partial files/integer-text volume remain readable; failed atomic saves clean up temporary copies. | Silently overwrite unreadable originals; display/log their contents; automatically restore them; claim all-store or semantic validation |
| `live.py` | What Andy is doing right now (ready, hearing, thinking, working with the tool's name, speaking), and what its head is turned to (one of eight names from `body/looking_at.py`), sent to the screen server on change | Send words or tool arguments |
| `kept.py` | Persistent items and pending messages/research, listed and deletable; delete everything also clears the card, captions and views | Delete without a name and a notice to the person |
| `consent.py` | Per-conversation, one-use permission bound to exact tool arguments and a spoken readback, expiring after two minutes (decision 0018). Explicit requests can save one item directly; sharing always requires confirmation. Before any memory proposal or dispatch, recognised labelled credential values are refused without repeating them, including explicit requests; all four memory-tool names share the check (decision 0029). This limited check does not classify unlabelled secrets or other write paths. The first offered save or share is only a proposal; its tool runs after the matching confirmation. The tool wrapper rejects changed content and reused permission. Explicit permission is recognised only before a colon/opening quote; a fresh yes must match the whole utterance (decision 0030). Recognised supplied message content without an actual request in its introduction produces neither a memory/sharing proposal nor a write; legitimate explicit delimited requests keep their existing path. Before `read_letter`, it also checks the existing latest utterance for a narrow already-spoken/quoted-message pattern and returns a non-camera result before OCR can run (decision 0028); explicitly held/printed pages retain the camera path, with negated page cues and introduction-level camera refusals respected. Its results say what to do, never why (worded as the reason, the model said the reason aloud); a message that itself asks to be kept or shared, and quoted words offered as permission, get fixed words to say, in English or Spanish. A memory question holding more than a sentence reads the words first and asks last, after "Thank you for telling me."; its language comes from Spanish words in what the person said (three small ones, or the household's language for a near miss; a name's ñ does not count). The fixed "that message asks me to…" words are only for a message that asks Andy itself, not one reminding the person. | Keep or log the words beyond the check |
| `health.py` | The hood page's health tiles: daemon, voice server, Andy's mode, weather, Tavily credits, Nebius endpoints | Read keys or words; hold up a page while checking |
| `turns.py` | How long each turn and each tool took, for the `/hood` page | Keep or send a word, a tool argument or anything but numbers, tool names and which eyes answered (one of three names) |
| `reading.py` | Reading a page held up to the camera, on this computer | Send or keep the picture |
| `onthisday.py` | Today's date in years gone by from Wikipedia: gentle items only, by a word filter and then a Nemotron check (once a day, cached); credited on screen | Offer anything unchecked; send anything but the date |
| `fun.py` | Jokes and riddles from a chosen set, never repeated within a month (`fun.json` holds joke numbers and times only), given to the model as the words to say, with no pacing to perform | Make up a joke; keep anything the person says |
| `stories.py`, `story_texts.json` | Public-domain stories read a part at a time, with a bookmark for another day (`story.json`: which story, which part); a story about something in particular is the model's own, said to be made up | Recite a story from memory; keep anything the person says |
| `body/giggle.py` | After a joke's punchline, a one-second antenna wiggle once Andy's voice stops | Move the head; move while the person speaks |
| `letters.py` | The page as a large-print card on the screen: Nemotron 3.5 Lightning fills a fixed schema; code adds the warning from the page's own words, keeps a scam's demand off the to-do, shows no medicine dose and masks account and phone numbers | Act on the page's text; show a dose; show a number that identifies someone; keep the card past the screen's usual five minutes |
| `urgent.py`, `urgent_audio/` | The deterministic net: urgent medical words get 911, crisis words get 988, in English or Spanish, if Andy's reply missed it; a negation counts only when it governs the words; when the model can't be reached or still leaves the number out, the sentence plays from a recording on the robot | Keep or log the words; claim to watch over anyone |
| `guard.py` | The second look: the person's words checked by Nemotron 3.5 Content Safety on a Nebius endpoint, beside Andy's reply; 988 if self-harm was found and the reply missed it | Delay a reply; keep or log the words or the result; act on any category but self-harm |
| `looking.py` | "Look into it": Tavily research streamed in the background, each step on the screen, the answer left for Andy to say; one at a time, ten a day; stopped at once when asked (`look_into` with `stop`, or "be quiet"); never started again by its own answer (none within 30 s of an answer, nor the same question within 10 minutes) | Log the question; act on the answer without a yes; retry a stopped research |
| `weather.py` | The forecast and alerts for the town from the National Weather Service; the town's coordinates, looked up once; on the TV, the town as the card's title, one line a period, an alert as what and until when | Send anything but the town and its coordinates |
| `web.py` | Tavily calls; cleaning web text into information; scrubbing messages before a scam check | Log a query or result; send numbers, links or emails from a message |
| `dayplan.py`, `settings.py`, `volume.py`, `voice_controls.py` | Today's plan in fixed words; the person's pace and volume; exact spoken controls, in English and Spanish, and sleep after Andy's own goodnight when the person asked for it | Keep any transcript; let the model reword the plan |
| `reminders.py`, `kept.py` | Exactly one time source per reminder, validated rows, shared file lock and bounded ID collision retries. Malformed stores are preserved whole under unique names; failed saves leave no temporary copies. Settings lists recovery metadata, marks those reminders inactive, and can delete one copy or all kept data (decision 0031). A failed preservation prevents a replacement write. | Silently choose between conflicting times; discard malformed rows; expose recovery contents in the page; retain a saved copy after its explicit deletion |
| `speaker.py` | Saying what is due at a quiet moment: reminders, the morning plan, family messages (with a note on the TV), a family suggestion of a reminder ("Shall I set it?", set only after a yes; the answer never goes back to the family), research answers | Speak while the person is speaking; set anything without a yes |
| `supervisor.py`, `state.py`, `wake.py`, `chimes.py` | Awake, asleep and quiet; waking by phrase, time or due reminder; soft cues | Listen while the app is running; send or keep any audio |
| `watchdog.py` | Noticing when Andy has stopped hearing well (audio drops), asking the supervisor for a restart, and counts for the hood page | Keep or log words; restart without a supervisor to bring Andy back (the dashboard app only logs) |
| `scamcheck.py`, `tools/check_message.py` | Whether a message read aloud shows a known scam's sign (Lightning, quoting the message) or uses the trick a Tavily warning describes (Ultra); the TV's receipt (what to do first, then three steps: the sign, the warning and its site, linked to the warning's page, why they match); saying plainly when the warnings couldn't be checked; "Checking this message" on the TV at once; the same message checked again within two minutes answered from the first check, in memory only | Send the message's numbers, links or emails to Tavily; say "no sign" when the lookup failed |
| `finder.py`, `vision.py` | Choosing the eyes (`vision.eyes`: Nemotron 3.5 Super VL on Token Factory by default, Nano VL on our endpoint with `ANDY_VISION=endpoint`, Cosmos Reason 2 2B on this computer with `ANDY_VISION=local`, or off; decision 0011); every picture through `vision.answer`, which falls back to Cosmos here when the eyes can't be reached and `ANDY_VISION_FALLBACK=local` (never on a refusal), and records which eyes answered for the hood (decision 0015; a turn that used the eyes carries the name, one of three, to the screen server in the supervisor's process); a family photo with how to talk about it (one open question, a story kept only after a yes); sweeping the room, reading each of four views as six zoomed tiles at once, turning to look closer at the best sighting, the body too when it is past the head's reach (decision 0016), and checking a close-up, then pointing with the head (decision 0012); the four views (480 px) in the screen server's memory for two minutes (`POST /api/views` from this computer, `GET /view` for the TV, screen token), shown as "what Andy looked at" with the chosen one marked, also when nothing was found; failing in seconds when the endpoint is stopped; keeping tries for scoring only when `ANDY_FINDER_RECORD` is set | Keep a view on disk or in a log; describe people |
| `places.py`, `tools/remember_place.py`, `tools/forget_place.py` | Where the person's things are, kept only when asked or after a yes (consent gate): the thing, the head's direction, Andy's words, the time; a find remembered in memory only for six hours; `finder.find` looks there first | Keep a picture; keep anything without a yes |
| `gestures.py`, `tools/gesture.py` | Moves taught by hand with the antennas: limp antenna motors for six seconds, the movement trimmed, smoothed and capped at 1.8 rad/s, kept by name, played back; the motors come back on under a move that starts where the hand left them | Turn the head's motors off; move faster than the antennas' limit |
| `body/person.py`, `body/presence.py` | Finding a person whose face isn't visible (YOLOX, OpenCV model zoo, about 1.4 a second on two CPU threads while following, less often when nobody is around) for following and for noticing someone is home; one in-memory timestamp of when someone was last seen or heard | Keep a frame, an image or an identity |
| `moments.py`, `recall.py`, `offers.py` | Dated moments kept after a yes and deleted a week after their date; what Andy remembers, given to it at the start of every conversation; what Andy may offer after a web answer, always with a yes | Keep anything without consent; offer to act without a yes |
| `clock.py`, `words.py` | The date and time in words, never guessed; fixed words in English and Spanish, never translated by the model | Let the model invent the day |
| `consent.py` (sleep) | `go_to_sleep` passes the tool gate only when the person's last words ask for sleep or goodbye, in English or Spanish | Put Andy to sleep on a misheard scrap |
| `turn_notes.py` | Andy's own note on the person's turn, added by the voice server (and the suite) to that request only: something coming up with its day, or a photo's story just told, gets a note to prepare the memory offer first; asking the time or the date gets a note to ask the clock (`get_today`) first. Questions, requests to Andy, quoted messages, a no, anything already asked for, and anything the urgent check fires on get none; a look at the room counts as a photo only when what was seen is one | Keep the note in the conversation; log the words; save anything (the offer still needs a yes); offer to remember crisis words |
| `tool_text.py` | A tool call the model wrote out as text, read back into the call it names, for the voice server and the suite: only a tool Andy has, with its own parameters, each of its declared type and every required one, at most three | Speak the markup; make a call Andy doesn't have; log the words |
| `words.py` (problems) | Every message the settings and family pages can show, in English and Spanish (`PROBLEMS_ES`); a replaced link answers JSON 410 with the expired page's words | Show a server error in the wrong language, or echo a token |
| `privacy.py`, `app_mode.py` | Redacting every log record of Pollen's app as it is made; everything Andy adds to Pollen's app, installed the same way by the desktop launcher and the dashboard app | Let a spoken turn or a tool's arguments reach a log |
| `measure.py`, `judge_playground.py` | Intervals and percentiles for every measured figure; the public guided examples with real inference and no household tool | Report a figure without its uncertainty; reach the camera, motors, stores or web from the public examples |
| `body/wave.py` | A wave beside the tracked face (OpenCV picture differences, 8 a second), answered by the antennas | Keep or send any picture; act while anyone speaks or during a search |
| `body/hold.py` | During a search, the head is the search's alone: seek, face following, the glance and idle hand-back stand down | — |
| `body/seek.py` (still things) | A "person" followed three times in ten minutes in one direction without a face ever showing (a coat, a lamp), or followed for a minute without one, is left alone there for ten minutes, or until a face is seen | Follow a shape that never had a face all evening; ignore a direction once a face was seen there |
| `body/seek.py` (second speaker) | A voice well to the side of the face Andy follows turns the head to it; nobody there, back | Turn while Andy speaks; turn twice to the same empty direction within a minute |
| `sim/finder_sim.py`, `cloud/sim-job.sh` | The finder in Pollen's MuJoCo scene from a virtual eye, many trials, locally or as Nebius Serverless Jobs (decision 0013) | Run on the robot; keep pictures |
| `model_reply.py` | Shared non-streaming answer boundary for deeper/vision/letter/scam clients (decision 0032). Reject unusable envelopes, explicit non-stop results, refusals, unexpected tool calls and non-string/empty content. Plain answers exclude known inline reasoning drafts; structured clients validate their exact flat fields/types/enums. Scam/simulation job bundles include the standard-library helper. | Treat malformed replies as ordinary answers or as an outage that warrants another model; log or retain provider content; claim to validate facts or the streaming voice engine |
| `deeper.py` | "Think it through": a hard question handed to Nemotron 3 Ultra | Decide for the person |
| `captions.py` | Andy's own words to the screen as captions | Send the person's words |
| `scripts/demo_screen.py`, `space/`, `scripts/space.sh` | The screens on sample data, on this computer or as a public read-only Hugging Face Space (decision 0010) | Hold a key or a real person's data; take anything a visitor sends; run on the robot |
| Pollen's conversation app (dependency) | The robot connection, movement, tool calling | — (not forked, files unmodified; Andy hooks in at start through `app_mode.install`, wrapping a few of its methods) |

The screen's main refresh and fast status poll each allow one pending request and use five-second
AbortController timeouts. Status requests pause while offline. Browser-local connection generations
are checked after status JSON decoding so late replies cannot overwrite a disconnected or newer
connection's state (0035). The existing ten-second offline indicator and independently running clock
remain. Without AbortController, the status guard caps requests but cannot cancel a hung fetch.

## Data

- Keys live in `~/.config/companion-hackathon/.env` (mode 600), outside the repository.
- Nebius Token Factory runs with zero data retention switched on.
- No recording or transcript is stored. Owner-only in `~/.local/share/andy-companion/`: what the person
  asks Andy to remember (`memory.json`, `moments.json`, moments for 7 days), their reminders
  (`reminders.json`), notes shared with family (`shared.json`), family messages
  waiting to be said (`inbox.json`), family photos (`photos/`, 7 days), settings (`settings.json`), the
  story bookmark (`story.json`), joke numbers (`fun.json`), where the person's things are (`places.json`) and moves taught
  by hand, by name (`gestures.json`); the settings page lists and deletes all but the settings, bookmark and joke numbers. Cards and research questions and answers live only in the screen server's memory. The app uses authenticated loopback HTTP (`transient.py`, decision 0019), with no disk fallback. Old
  `screen.json` and old disk-backed research entries are removed on startup.
- Unreadable reminder stores are preserved as `reminders.unreadable-*.json` in that same private directory. The owner page lists only copy metadata, not damaged contents; these reminders are inactive. Single-copy deletion and delete-everything remove the saved files. There is no automatic repair or restoration.
- Unreadable settings are likewise preserved as `settings.unreadable-*.json` (0037). The page shows metadata and explains that defaults apply to choices not set again; the original is inactive. Existing authenticated single/all deletion removes these copies too, without exposing their contents. Recovery copies are owner-only and never automatically restored.
- Captions of Andy's own words live only in the screen server's memory, for three minutes (long enough to read a story's part along to the end), never on disk or in a log.
- Turn timings (numbers and tool names only) live only in the screen server's memory, last 40.
- The services' journal holds the same redacted log lines: timings, token counts and tool names, no words
  (checked 2026-10-14).
- Finder tries (the four views and close-ups at full size, what the model said, the head's angles, the times), and
  "what do you see?" pictures with their descriptions (`vision.record_look`), are kept only when
  `ANDY_FINDER_RECORD` names a folder, for the founder's own test sessions, owner-only; deleted after
  scoring.

## Evaluation

- `.githooks/commit-msg` runs `scripts/check_commit_message.py` with the message file. Recognised
  private AI-session URLs/trailers are rejected with fixed wording and no echoed contents; author
  credits remain allowed. This complements the pre-commit tests/key check (0036). Neither hook runs
  the robot or loads household data. Audit name terms and private rollback history stay outside the repo.
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
  requires tracked files and the three export inputs to match the tag's snapshot. Anonymous bounded
  GETs then resolve the exact public GitHub tag to the same commit (lightweight or up to five annotated
  objects) and compare the public Hugging Face app's package metadata byte for byte (0038). Only then
  do public citation checks run; no final fields are printed on a failed check. Metadata bodies are
  capped at 64 KiB, socket timeout five seconds, supplied object URLs ignored, fixed non-echoing errors.
  Draft output is unchanged. It reads public/repository metadata only, never provider settings, and
  does not publish/move tags, update the app, submit anything or certify video
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
  Before any answer or simulated action, its hosted transport requires explicit completed `stop`/
  `tool_calls` status and a supported message shape (0033). Text reuses `model_reply`; tool-turn prose
  and reasoning/metadata are dropped before the next request. Failed closing text preserves the
  already-applied sample state with fixed wording. The build manifest includes the helper and has a
  cold-import check. No corresponding change to the streaming robot voice handler.
- `docs/judging.md`: the short testing path from the README, public demo and submission text.
  The public request form distinguishes assisted demonstrations from organiser hardware-access
  requests. Physical access is agreed separately; a video call is not a confirmed substitute. Public
  software demos stay isolated from the Reachy Mini/supporting desktop; personal administrative
  logins and provider keys remain private. This clarification adds no remote-control connection.
  CI starts the real public demo in a separate process with throwaway sample data, probes pages,
  assets, tokens and write refusal, then checks cleanup. CI also builds a wheel and checks its
  pages, fonts, audio, profile and tools from an isolated installation with checkout imports disabled.
- `evals/run_suite.py`: 97 text-based conversation and tool-selection cases, the real profile, tool
  definitions, confirmation gate and urgent-words net, with synthetic tool results, judged by Nemotron
  3 Ultra. It does not run a microphone, camera or motors. Run locally or as a Nebius Serverless Job
  (`cloud/suite-job.sh run`); input and code hashes accompany new scorecards.
- `evals/physical_trials.py`: a fixed 30-attempt plan for the real finder; manual outcomes and timings,
  all attempts retained, confidence intervals, no speech or pictures. A score requires all 30. Exact
  row/key/type/label/time validation applies to reads and direct scoring (0039); unsupported notes/
  extra cells are refused and canonical rows copied. Correct-absent responses and errors per group
  are explicit. Complete owner-only temporary files precede atomic CSV replacement; new plans/
  reports never replace existing files/symlinks. Single operator, no concurrent-writer guarantee.
  Scoring-checkout provenance is labelled separately from unverified per-trial robot provenance.
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
  "ASSISTANT:" and, since 2026-10-25, "Live:"). Since 2026-10-28 it also takes out any tool call the model wrote
  as text (`<tool_call>`, `<function=…>`) before a sentence is spoken, logging only how many characters, and makes
  that call when the reply made none (`tool_text.py`: only a tool Andy has, with its own parameters, each of its
  declared type; logging only the tool's name). When the person mentions something coming up with its day, or tells
  a photo's story, it adds Andy's own note to that turn in the request only (`turn_notes.py`), logging only the note's
  kind. The suite (`evals/run_suite.py`) does both the same way. It also keeps
  what reaches the model to English and Spanish: a transcript mostly in another alphabet is passed on as unclear (a
  stray word in one, such as "Andy" written in Cyrillic, is read as "Andy" or left out), so Andy
  asks again, once: more such turns within 30 s are passed on empty and get no reply (decision 0048; only the
  detected language code is logged). The filter is not trusted alone: `scripts/doctor.py --live`
  reads the last day of the voice log and fails on any line that is not one of the kinds it may write
  (decision 0017).
- A reminder's words are kept as said, less a time at their end ("take a pill at eight" is kept as "take a
  pill", its time kept as the time); lists on the screens show them in sentence case.

Preflight (`scripts/doctor.py --live`, decision 0026) tests configured cloud-vision availability
with a fixed invented text-only request, at most eight output tokens and a 15-second timeout. It
reports status only; catalogue membership does not determine availability. It neither captures a
camera frame nor establishes visual quality. A camera-only local-fallback probe remains separate.
Both conversation/vision text probes now use the runtime final-text validator (0041); incomplete,
refused or unusable replies cannot pass on HTTP success alone. Conversation timing is monotonic.
Optional endpoint catalogues are labelled separately from inference. Required watchdog counts are
validated without modifying the file: missing/unsupported, stale (30 seconds) or future (over one
second, allowing timestamp rounding) records fail both audio and unanswered-speech verification.
No provider text or unsupported health fields are printed; no service is started or restarted.

Requested camera-action response order (decisions 0027/0028): the profile/tools instruct the model to
dispatch the existing `find_object` or `read_letter` before preliminary speech. There is no separate keyword-driven movement path;
the same tool, camera checks, body ownership, transient progress and result flow remain in use.
