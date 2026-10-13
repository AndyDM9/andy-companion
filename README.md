# Andy Companion

A small home robot for older adults who live at home, and the family who help. Andy runs on a
Pollen Robotics [Reachy Mini](https://huggingface.co/blog/reachy-mini). It hears with NVIDIA
Parakeet, thinks with NVIDIA Nemotron on Nebius Token Factory, and sees with a Nemotron vision
model on a Nebius Serverless Endpoint. It keeps nothing it hears.

> Built for the Nebius x NVIDIA Global AI Hackathon 2026, Physical AI track.

![Andy's screen in the afternoon](docs/images/screen-afternoon.png)

## What Andy does

- **Speaks English and Spanish**, in whichever you speak to it; the day plan and the screen
  switch too.
- **Talks, and keeps looking at you.** Andy follows your face while it speaks, turns its body
  when you move, and finds you by your voice if you're out of view. While it thinks or looks
  something up, its antennas lean slowly, so a pause never looks dead.
- **Says it's a robot.** It never pretends to be a person, and never speaks as someone you know.
- **Knows the day, and never guesses it.** "What's on today?" gets the same words every time,
  and each morning Andy offers the day's plan.
- **Reminders at the times you choose, in your words.** One-off or daily. A reminder wakes Andy
  if it is asleep, so none is missed.
- **Reads a letter you hold up.** It reads it on the computer, explains it simply, and offers to
  look it up if it asks for money or details.
- **Looks things up, and names the source.** Local news from papers you choose, opening hours,
  what's on this week, a link someone sent, and whether a message looks like a known scam.
- **Your pace and your volume.** "Please speak more slowly" and "speak up" stick.
- **Quiet when you want it.** "Be quiet for an hour", "goodnight", and "Andy, wake up".
- **A screen beside it.** A TV or monitor shows the day in large type, what's next, what Andy
  is talking about, and **live captions of what Andy says**. Its colours follow the time of day.
- **Family, on your terms.** Family see only what you ask Andy to share, can send Andy a message
  or a link, and Andy always tells you who looked.
- **Set up from a phone, never behind your back.** A helper sets the town, news sites, language
  and voice on a setup page; Andy tells you who changed what, and you can ask it to change
  anything back. Reminders, memories and what is shared stay yours, set by talking to Andy.

What Andy never does: give medicine doses or medical advice, ask for money or passwords, claim to
keep anyone safe, or keep recordings or transcripts.

## How it uses NVIDIA and Nebius

![How Andy works](docs/images/architecture.svg)

| Part | Model or service | Where it runs |
|---|---|---|
| Conversation and tool calls | NVIDIA **Nemotron 3.5 Lightning** | **Nebius Token Factory** (zero data retention on) |
| Hearing | NVIDIA **Parakeet TDT 0.6B v3** | Local GPU, inside [speech-to-speech](https://github.com/huggingface/speech-to-speech) |
| Eyes ("what do you see?") | NVIDIA **Nemotron Nano 12B v2 VL** (FP8), vLLM 0.30.0 | **Nebius Serverless Endpoint**, one L40S ([cloud/vision-endpoint.sh](cloud/vision-endpoint.sh)) |
| Judging Andy's answers | NVIDIA **Nemotron 3 Ultra** | Nebius Token Factory |
| The conversation suite | 52 spoken situations, 16 areas, English and Spanish | **Nebius Serverless Job** ([cloud/safety-job.sh](cloud/safety-job.sh)) |
| The web | Tavily search, extract, crawl (safe search on) | Tavily API |

## Measured (Reachy Mini Lite, 2026-10-13)

| Step | Time |
|---|---|
| Parakeet speech-to-text | 0.02–0.08 s |
| Nemotron 3.5 Lightning reply or tool call | 0.62–0.83 s |
| Text-to-speech, first audio | 0.10–0.33 s |

**Live, on the robot:** the screen server's `/hood` page shows every turn as it happens: from the
end of your words to Andy's first sound, split into hearing and reply, with each tool Andy used,
how long it took and where it ran. Numbers and tool names only, in memory; never the words.

![Under the hood (sample turns)](docs/images/hood.png)

**The conversation suite** ([evals/](evals/)): 52 spoken situations in English and Spanish, judged by Nemotron 3 Ultra. The model gets exactly the robot's 27 tools and their real descriptions ([evals/tools.json](evals/tools.json), written from the robot's code). **Latest: 52, 52 and 51 of 52 in three runs.**
- **Baseline:** 27/36.
- **After the fixes:** 35, 36 and 36 over three runs. The fixes were six profile weaknesses, plus three flawed cases fixed openly in the suite.
- **An honest correction:** earlier runs scored 44 of 44, but gave the model 17 tools with shortened descriptions. With the real 27, the suite found that Andy said it had no camera, once invented a time, and that one case could never pass (a harness flaw). All three are fixed and recorded in [evals/suite.json](evals/suite.json).
- **The urgent-words net:** a deterministic check under the model makes sure "my chest hurts" always gets "please call 911 now".

Scorecards are in [evals/results/](evals/results/).

## Privacy

- No audio or transcript is kept or logged. Log records are redacted as they are made, and tests prove it.
- Andy's only stored data are what you ask it to remember, your reminders and your settings, in owner-only files on the robot's computer.
- Pictures stay on the computer, except when you ask "what do you see?". Then one picture goes over HTTPS to your own Nebius endpoint and is not kept.
- Keys never enter this repository; a pre-commit hook blocks them.

## Setup

**You need:**
- Ubuntu 24.04 with an NVIDIA GPU (8 GB or more) for the voice server;
- a Reachy Mini with Pollen's daemon running ([Pollen's guide](https://huggingface.co/docs/reachy_mini));
- `tesseract-ocr`, and [uv](https://docs.astral.sh/uv/);
- a Nebius Token Factory key and a Tavily key.

1. **Keys.** Copy `.env.example` to `~/.config/companion-hackathon/.env` and fill it in. Then
   `chmod 600` it. Turn on zero data retention in Token Factory's organisation settings.
2. **Voice server.** `cd voice && uv sync && ./run.sh`
3. **Robot side.** `cd robot && uv sync`, then from the repository root run `./scripts/andy`.
4. **Your home.** `python scripts/settings.py links` prints four private addresses on your home
   network. Open **Set up Andy** on a phone to choose the town, local news sites, what's-on pages,
   language, pace, volume and captions. Open **the screen** on a TV, and send **the family page**
   to family.
5. **Optional: eyes.** With the [Nebius CLI](https://docs.nebius.com/cli), run
   `cloud/vision-endpoint.sh create`, then `status` until it is RUNNING. Run `stop` when you're
   done; a stopped endpoint costs nothing for compute.
6. **Check everything.** `robot/.venv/bin/python scripts/doctor.py` says what's missing.
   To start Andy at login: `scripts/install-services.sh --enable`.
7. **Optional: the suite on Nebius.** `cloud/safety-job.sh run`, or locally
   `uv run python evals/run_suite.py --runs 3`.

Tests: `uv run pytest`, plus the robot-side tests with `PYTHONPATH=src robot/.venv/bin/python -m pytest tests`.

## Repository

| Path | What it is |
|---|---|
| `src/andy_companion/` | Andy's own code: clock, reminders, speaker, body behaviours, privacy, web, reading, vision, screen, supervisor |
| `tools/` | The voice tools Andy can call |
| `profiles/companion/` | Who Andy is and what it never does |
| `voice/` | The voice server (Parakeet, Nemotron on Token Factory, text-to-speech) |
| `robot/` | The robot-side environment (Pollen's conversation app 1.0.1) |
| `cloud/` | The Nebius Serverless Endpoint and Job scripts |
| `evals/` | The conversation suite and its scorecards |
| `docs/` | [Plan](docs/PLAN.md), [status](docs/STATUS.md), [architecture](docs/architecture.md), [decisions](docs/decisions/) |

## Licence

Apache-2.0. See [LICENSE](LICENSE).
- Pollen's conversation app and Hugging Face's speech-to-speech are Apache-2.0.
- The NVIDIA models are under the NVIDIA Open Model License.
