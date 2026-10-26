#!/usr/bin/env bash
# The robot side: Pollen's conversation app with this repo's companion profile and tools,
# pointed at the local voice server. Needs the Reachy Mini daemon running.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_PY="${ANDY_APP_PYTHON:-$ROOT/robot/.venv/bin/python}"   # cd robot && uv sync
[ -x "$APP_PY" ] || { echo "First: (cd robot && uv sync)" >&2; exit 1; }
export REACHY_MINI_CUSTOM_PROFILE=companion
export REACHY_MINI_EXTERNAL_PROFILES_DIRECTORY="$ROOT/profiles"
export REACHY_MINI_EXTERNAL_TOOLS_DIRECTORY="$ROOT/tools"
export REALTIME_TRANSCRIPTION_LANGUAGE="${ANDY_LANGUAGE:-en}"   # a hint only: Parakeet detects the spoken language itself
cd "$ROOT"
# run_andy.py calls app_mode.install(): the same allowlisted env reader as the dashboard app.
# Do not prefill empty variables or duplicate quote parsing here: that would mask the reader's settings.
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$APP_PY" "$ROOT/scripts/run_andy.py" "$@"
