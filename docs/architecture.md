# Architecture

**Last updated 2026-10-13.**

```
            ┌──────────────────────── the home ────────────────────────┐
 person ──▶ │ Reachy Mini (mics, camera, head, antennas, body)         │
            │      │ audio                     ▲ moves                 │
            │      ▼                           │                       │
            │ Pollen conversation app + profiles/companion + tools/    │
            │      │ OpenAI Realtime protocol (ws://127.0.0.1:8765)    │
            │      ▼                                                   │
            │ voice/: speech-to-speech                                 │
            │   Smart Turn (end of turn) → NVIDIA Parakeet (speech to  │
            │   text) → LLM client → Qwen3-TTS (text to speech)        │
            └───────────────│──────────────────────────────────────────┘
                            ▼ HTTPS, zero data retention
              Nebius Token Factory: NVIDIA Nemotron 3.5 Lightning
```

## Parts, and what each owns

| Part | Owns | Must not |
|---|---|---|
| `voice/` | Hearing, end-of-turn detection, the model call, speaking | Store audio or text; hold keys in the repository |
| `profiles/companion/` | Who Andy is, how it speaks, what it never does, which tools it may use | Contain any person's data |
| `tools/` | The companion's own abilities (clock, reminders, …) | Move the robot except through the app's movement tools |
| Pollen's conversation app (dependency) | The robot connection, movement, tool calling | — (unmodified) |

## Data

- Keys live in `~/.config/companion-hackathon/.env` (mode 600), outside the repository.
- Nebius Token Factory runs with zero data retention switched on.
- Nothing the person says is stored, except what they ask Andy to remember (and reminders they
  set), in Andy's own store on the robot's computer. (M2 makes this true; see STATUS.md.)
