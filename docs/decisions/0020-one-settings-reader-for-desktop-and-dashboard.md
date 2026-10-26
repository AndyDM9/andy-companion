# 0020: One settings reader for desktop and dashboard

**Date:** 2026-10-26. **Status:** accepted.

## Context

A fresh-setup audit found that `run-robot.sh` preloaded settings with `sed`, while the dashboard
used `app_mode.load_env`. The shell kept quote characters around keys, replaced existing environment
values and prefilled empty variables. It also fixed the voice address before the file's address was
read. The documented screen port, vision model and finder-turn setting were not consistently loaded.
The doctor parsed quoted settings differently again, and settings links ignored the file's screen port.

## Options

1. **Maintain the shell parser alongside Python:** duplicate quoting, allowlists and precedence rules
   across the launcher and app, with tests for each copy.
2. **Use the existing Python reader for both app entry points:** let `app_mode.install()` load its
   allowlisted settings before configuring the connection. Share the non-mutating parser with diagnostics.

## Decision

Choose option 2. The desktop launcher no longer parses the private env file or preselects the voice
address. Both app entry points use `read_env` through `load_env`; existing process variables win.
The doctor uses the same parser and precedence. The supervisor and app load the screen port;
the settings-link command loads that port only. The app also allows the documented vision-model
and finder-turn settings. Unrelated private values are never loaded.

## Why

The app already owns configuration and already runs first in `scripts/run_andy.py`. Reusing that
path removes a conflicting parser. Regression checks run the real desktop launcher with an invented
env file and a stand-in interpreter, so no robot, real credentials or services are used.

## Consequences

Quoted keys, custom voice addresses, shell overrides and non-default screen ports work consistently
in software checks. The robot-side launch still needs validation after USB reconnection. The voice
and local-eyes shell launchers retain their existing small allowlisted readers; this decision does
not make arbitrary env-file text executable or source the file as shell code.

## Revisit when

- Another app entry point or settings format is introduced.
