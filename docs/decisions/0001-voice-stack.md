# 0001: The voice stack

**Date:** 2026-10-13. **Status:** accepted.

## Context

A spoken companion lives or dies on the time from the end of your words to its first sound, and on what happens to
those words. The robot's own app (Pollen's conversation app) expects an OpenAI-style realtime voice service; we
wanted NVIDIA's models in that loop, hearing and speaking on the home GPU so audio never leaves the house, and the
thinking on Nebius Token Factory.

## Decision

Run Hugging Face's `speech-to-speech` (Apache-2.0) in `serve` mode as the voice server:
- **speech-to-text:** NVIDIA Parakeet TDT 0.6B v3;
- **end of turn:** Smart Turn v3.2;
- **text-to-speech:** Qwen3-TTS;
- **brain:** NVIDIA Nemotron 3.5 Lightning on Nebius Token Factory, through the `chat-completions` backend with thinking off.

Pollen's Reachy Mini conversation app connects to it over the OpenAI Realtime protocol, unchanged.

## Why

- It is the protocol the Reachy Mini app already speaks, so the robot side needs no fork.
- Two NVIDIA models (Parakeet and Nemotron) and a real Token Factory runtime call.
- **Lightning is fast enough for speech.** Measured: 0.62–0.83 s per reply on the robot, against 1.0 s for Nemotron Super.
- **Its tool calls are correct.** Measured: a reminder with the right time.

## Alternatives

| Option | Why not |
|---|---|
| Pollen's hosted voice backend | Not Nebius, not NVIDIA |
| Nemotron Super as the main model | Slower; hard questions go to Nemotron 3 Ultra instead (`think_it_through`, `deeper.py`) |
| Our own audio pipeline | Weeks of work the existing server already does |

## Revisit when

- Lightning's tool calls fail on real turns.
- An NVIDIA text-to-speech model is easy to serve.
