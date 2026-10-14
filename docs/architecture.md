# Architecture

**Last updated 2026-10-13.**

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
            │   Smart Turn (end of turn) → NVIDIA Parakeet (speech to  │
            │   text) → LLM client → Qwen3-TTS (text to speech)        │
            └───────────────│──────────────────────────────────────────┘
                            ▼ HTTPS, zero data retention
              Nebius Token Factory: NVIDIA Nemotron 3.5 Lightning

 tools/ (local_news, look_up, whats_on, read_link, check_message)
      ──▶ HTTPS ──▶ Tavily (search, extract, crawl); safe search on
```

## Running

`scripts/andy` starts `supervisor.py`, which runs the app (`scripts/run-robot.sh` →
`scripts/run_andy.py`) while Andy is awake. When Andy sleeps or is quiet, the app stops and the
supervisor listens for a wake phrase (Vosk, offline), and wakes Andy when one is heard, when the
quiet time ends, or when a reminder comes due.

Two ways to run the same Andy, both through `andy_companion.app_mode.install()`: on a computer
under the supervisor (`scripts/andy`), or as a Reachy Mini dashboard app (`reachy_app/`, no
supervisor: no wake phrase; the dashboard starts and stops it).

## Parts, and what each owns

| Part | Owns | Must not |
|---|---|---|
| `voice/` | Hearing, end-of-turn detection, the model call, speaking | Store audio or text; hold keys in the repository |
| `profiles/companion/` | Who Andy is, how it speaks, what it never does, which tools it may use | Contain any person's data |
| `tools/` + `src/andy_companion/` | The companion's own abilities: the clock, reminders and the speaker that says a due reminder unprompted | Move the robot except through the app's movement tools |
| `src/andy_companion/body/` | Where Andy looks and turns: following the person while speaking and listening, finding them by voice or by sight, calm idle moments, the antennas' thinking lean, a glance at the TV when something new shows on it (`glance.py`: only once the screen's place is set, never while the person speaks) | Store any frame, image or identity; send a picture anywhere |
| `board.py`, `screen_server.py`, `pages/` | Andy's screen and the family page: what is shown, how it looks (the time of day's colours, glass or the calm screen), what the person shared, messages and looks from family | Show or share anything the person did not ask to share; log a URL or token |
| `setup_page.py` (+ `/setup`) | What a helper may change from a phone (town, news sites, what's-on pages, language, pace, volume, captions), its checks, and telling the person who changed what | Change reminders, memories or what is shared; change anything without a name and a notice to the person |
| `live.py` | What Andy is doing right now (ready, hearing, thinking, working with the tool's name, speaking), sent to the screen server on change | Send words or tool arguments |
| `kept.py` | Everything Andy keeps about the person, listed and deletable from the settings page | Delete without a name and a notice to the person |
| `consent.py` | Saving tools (`remember`, `remember_moment`) run only when the person's last words asked or said yes | Keep or log the words beyond the check |
| `health.py` | The hood page's health tiles: daemon, voice server, Andy's mode, weather, Tavily credits, Nebius endpoints | Read keys or words; hold up a page while checking |
| `turns.py` | How long each turn and each tool took, for the `/hood` page | Keep or send a word, a tool argument or anything but numbers and tool names |
| `reading.py` | Reading a page held up to the camera, on this computer | Send or keep the picture |
| `fun.py` | Jokes and riddles from a chosen set, never repeated within a month (`fun.json` holds joke numbers and times only) | Make up a joke; keep anything the person says |
| `stories.py`, `story_texts.json` | Public-domain stories read a part at a time, with a bookmark for another day (`story.json`: which story, which part); a story about something in particular is the model's own, said to be made up | Recite a story from memory; keep anything the person says |
| `body/giggle.py` | After a joke's punchline, a one-second antenna wiggle once Andy's voice stops | Move the head; move while the person speaks |
| `letters.py` | The page as a large-print card on the screen: Nemotron Lightning fills a fixed schema; code adds the warning from the page's own words, keeps a scam's demand off the to-do, shows no medicine dose and masks account and phone numbers | Act on the page's text; show a dose; show a number that identifies someone; keep the card past the screen's usual 15 minutes |
| `urgent.py` | The deterministic net: urgent medical words get 911, crisis words get 988, in English or Spanish, if Andy's reply missed it | Keep or log the words; claim to watch over anyone |
| `guard.py` | The second look: the person's words checked by Nemotron 3.5 Content Safety on a Nebius endpoint, beside Andy's reply; 988 if self-harm was found and the reply missed it | Delay a reply; keep or log the words or the result; act on any category but self-harm |
| `looking.py` | "Look into it": Tavily research streamed in the background, each step on the screen, the answer left for Andy to say; one at a time, ten a day | Log the question; act on the answer without a yes |
| `weather.py` | The forecast and alerts for the town from the National Weather Service; the town's coordinates, looked up once | Send anything but the town and its coordinates |
| `web.py` | Tavily calls; cleaning web text into information; scrubbing messages before a scam check | Log a query or result; send numbers, links or emails from a message |
| `dayplan.py`, `settings.py`, `volume.py`, `voice_controls.py` | Today's plan in fixed words; the person's pace and volume; exact spoken controls | Keep any transcript; let the model reword the plan |
| `supervisor.py`, `state.py`, `wake.py`, `chimes.py` | Awake, asleep and quiet; waking by phrase, time or due reminder; soft cues | Listen while the app is running; send or keep any audio |
| Pollen's conversation app (dependency) | The robot connection, movement, tool calling | — (unmodified) |

## Data

- Keys live in `~/.config/companion-hackathon/.env` (mode 600), outside the repository.
- Nebius Token Factory runs with zero data retention switched on.
- Nothing the person says is stored, except what they ask Andy to remember (`memory.json`) and
  the reminders they set (`reminders.json`), and their pace and volume (`settings.json`), all owner-only in `~/.local/share/andy-companion/`.
- Captions of Andy's own words live only in the screen server's memory, for 20 seconds.
- Turn timings (numbers and tool names only) live only in the screen server's memory, last 40.
- No log line holds conversation text: `privacy.py` redacts the app's records as they are made,
  and `voice/serve.py` silences the transcript prints of every console in the voice server.
