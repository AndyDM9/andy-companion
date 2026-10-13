# Andy Companion

An open-source home companion robot for older adults who live at home, and the family who
help. It runs on a [Reachy Mini](https://huggingface.co/blog/reachy-mini), and its brain is
NVIDIA Nemotron on [Nebius Token Factory](https://tokenfactory.nebius.com/).

> Work in progress for the Nebius x NVIDIA Global AI Hackathon (Physical AI track), 2026.

## How it works

```
microphone ─▶ NVIDIA Parakeet (speech-to-text, local GPU)
          ─▶ NVIDIA Nemotron 3.5 Lightning on Nebius Token Factory (reasoning and tool calls)
          ─▶ text-to-speech (local GPU) ─▶ speaker
                         │
                         └─▶ tool calls ─▶ Reachy Mini head, antennas and body
```

- `voice/` runs [huggingface/speech-to-speech](https://github.com/huggingface/speech-to-speech)
  in `serve` mode, which speaks the OpenAI Realtime protocol on `127.0.0.1:8765`.
- `profiles/companion/` is the companion's profile for Pollen Robotics'
  [reachy_mini_conversation_app](https://github.com/pollen-robotics/reachy_mini_conversation_app).
- `tools/` holds the companion's own tools.

## What Andy does, and never does

- Reminders at the times you choose, in your words.
- Remembers what you ask it to, and forgets what you ask it to.
- Speaks at the pace and volume you choose.
- It is a robot, and it says so. It never speaks as, or imitates, a real person.
- It never gives medicine doses or medical advice, and never asks for money or passwords.

## Measured on a Reachy Mini Lite (2026-10-13)

| Step | Time |
|---|---|
| Parakeet speech-to-text | 0.02–0.08 s |
| Nemotron 3.5 Lightning on Token Factory (reply or tool call) | 0.62–0.83 s |
| Text-to-speech, first audio | 0.10–0.15 s |

## Setup

1. Keys in `~/.config/companion-hackathon/.env` (see `.env.example`), mode 600. Turn on zero
   data retention in your Token Factory organisation settings.
2. Voice server: `cd voice && uv sync && ./run.sh`
3. Robot: the Reachy Mini daemon running, then
   `ANDY_APP_PYTHON=/path/to/python-with-reachy-mini-conversation-app ./scripts/run-robot.sh --no-camera`

## Licence

Apache-2.0. See [LICENSE](LICENSE).
