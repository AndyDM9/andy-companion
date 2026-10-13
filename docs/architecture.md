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
            │    body/: gaze, body follow, seek, person, idle)         │
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
| `src/andy_companion/body/` | Where Andy looks and turns: following the person while speaking and listening, finding them by voice or by sight, calm idle moments, the antennas' thinking lean | Store any frame, image or identity; send a picture anywhere |
| `board.py`, `screen_server.py`, `pages/` | Andy's screen and the family page: what is shown, what the person shared, messages and looks from family | Show or share anything the person did not ask to share; log a URL or token |
| `setup_page.py` (+ `/setup`) | What a helper may change from a phone (town, news sites, what's-on pages, language, pace, volume, captions), its checks, and telling the person who changed what | Change reminders, memories or what is shared; change anything without a name and a notice to the person |
| `turns.py` | How long each turn and each tool took, for the `/hood` page | Keep or send a word, a tool argument or anything but numbers and tool names |
| `reading.py` | Reading a page held up to the camera, on this computer | Send or keep the picture |
| `urgent.py` | The deterministic net: urgent medical words get 911, crisis words get 988, in English or Spanish, if Andy's reply missed it | Keep or log the words; claim to watch over anyone |
| `guard.py` | The second look: the person's words checked by Nemotron 3.5 Content Safety on a Nebius endpoint, beside Andy's reply; 988 if self-harm was found and the reply missed it | Delay a reply; keep or log the words or the result; act on any category but self-harm |
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
