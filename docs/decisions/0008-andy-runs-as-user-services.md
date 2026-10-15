# 0008: On the desktop, Andy and its voice server run as user services

**Date:** 2026-10-14. **Status:** accepted.

## Context

Until 2026-10-14 the voice server ran in a terminal tab and Andy under a shell started by hand. The
desktop is shared with other work; a terminal closed, a session ended or a crash left Andy silent, and the
voice server's command line showed the model key to every process (`ps`).

## Decision

Two systemd user services (`systemd/`, installed by `scripts/install-services.sh`):
`andy-voice.service` runs `voice/run.sh` and `andy.service` runs `scripts/andy`, both restarted on failure.
They are **not** started at login unless enabled, because only one program may drive the robot and the
earlier assistant's services are still enabled at login. A stop goes to the supervisor only
(`KillMode=mixed`), which lets the app put the robot to sleep and shut down; a stop is a clean exit, not a
failure. The model key reaches the voice server through its environment, never its command line.

## Why

- Andy keeps running whoever started it, and comes back after a crash.
- `systemctl --user stop andy andy-voice` frees the computer in one command.
- The journal holds only the redacted log lines (checked 2026-10-14: no words).

## Revisit when

- Andy runs on its own computer: then enable at login.
