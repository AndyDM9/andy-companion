# Security

## Reporting a problem

Please report a vulnerability privately, through GitHub's private vulnerability reporting on this repository
(the **Security** tab, then **Report a vulnerability**), not in a public issue. Say what you found, how to reproduce
it, and what it lets someone do. This is a small project kept by one person; expect an answer within a week.

## What's in scope

- **The screen server** (`src/andy_companion/screen_server.py`): the TV, family, settings and under-the-hood pages,
  served on the home network over plain HTTP. Each page has its own long random token, compared in constant time;
  the server refuses clients from outside private, loopback and link-local addresses; the endpoints that post
  captions, turns and views also require this computer itself.
- **Key handling:** the private env file (`~/.config/companion-hackathon/.env`, mode 600), what each program reads
  from it, and the cloud scripts (`cloud/`), which keep keys and endpoint tokens off command lines and in Nebius
  MysteryBox.
- **What Andy keeps** on its computer (`~/.local/share/andy-companion/`, owner-only files) and what leaves the
  house ([README, Privacy](README.md#privacy)).

The voice server (127.0.0.1:8765) and the offline eyes (127.0.0.1:8095) listen on this computer only.

The separate guided judge playground (`scripts/judge_playground.py`, decision 0023) accepts only
fixed challenge IDs and Yes/No choices. It uses a server-side provider secret, the public profile,
three allowlisted schemas and the actual confirmation gate, with simulated effects. It has no
household or SDK imports, camera/microphone input, arbitrary chat, file access route or remote motor
control. Sessions stay in RAM, are isolated and expire while idle; inbound workers, inference
concurrency, request/response sizes, output tokens and daily provider calls are bounded. The daily
allowance resets on a process restart and is not a provider-account spending limit. Host/platform
access metadata is separate from this application's policy of logging no request or model text.

## Known advisories in dependencies

Every environment's lock file is audited with `pip-audit`, and updated where a fix exists and nothing pins it. Not
yet fixed, and why:
- **The voice server:** Hugging Face's speech-to-speech 1.0.0 pins `nltk==3.10.0` and `torch==2.11.0` (which pins
  setuptools below 82), and pillow 13 is a major change to its speech pipeline, deferred. The voice server handles
  only audio and Andy's own reply text, loads only the published NVIDIA models, and listens on 127.0.0.1, so these
  advisories (untrusted images, untrusted model files, text parsing) don't reach it.
- **The offline eyes:** vLLM 0.32.0 pins its setuptools.
- **accelerate:** an advisory with no fixed release yet.
