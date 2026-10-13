# Architecture

**Last updated 2026-10-13.**

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
```

## Running

`scripts/andy` starts `supervisor.py`, which runs the app (`scripts/run-robot.sh` →
`scripts/run_andy.py`) while Andy is awake. When Andy sleeps or is quiet, the app stops and the
supervisor listens for a wake phrase (Vosk, offline), and wakes Andy when one is heard, when the
quiet time ends, or when a reminder comes due.

## Parts, and what each owns

| Part | Owns | Must not |
|---|---|---|
| `voice/` | Hearing, end-of-turn detection, the model call, speaking | Store audio or text; hold keys in the repository |
| `profiles/companion/` | Who Andy is, how it speaks, what it never does, which tools it may use | Contain any person's data |
| `tools/` + `src/andy_companion/` | The companion's own abilities: the clock, reminders and the speaker that says a due reminder unprompted | Move the robot except through the app's movement tools |
| `src/andy_companion/body/` | Where Andy looks and turns: following the person while speaking and listening, finding them by voice or by sight, calm idle moments | Store any frame, image or identity; send a picture anywhere |
| `supervisor.py`, `state.py`, `wake.py`, `chimes.py` | Awake, asleep and quiet; waking by phrase, time or due reminder; soft cues | Listen while the app is running; send or keep any audio |
| Pollen's conversation app (dependency) | The robot connection, movement, tool calling | — (unmodified) |

## Data

- Keys live in `~/.config/companion-hackathon/.env` (mode 600), outside the repository.
- Nebius Token Factory runs with zero data retention switched on.
- Nothing the person says is stored, except what they ask Andy to remember (`memory.json`) and
  the reminders they set (`reminders.json`), both owner-only in `~/.local/share/andy-companion/`.
- No log line holds conversation text: `privacy.py` redacts the app's records as they are made,
  and `voice/serve.py` silences the voice server's one transcript print.
