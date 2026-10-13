#!/usr/bin/env bash
# The robot side: Pollen's conversation app with this repo's companion profile and tools,
# pointed at the local voice server. Needs the Reachy Mini daemon running.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_PY="${ANDY_APP_PYTHON:?set ANDY_APP_PYTHON to the python of an environment with reachy-mini-conversation-app 1.0.1}"
export REACHY_MINI_CUSTOM_PROFILE=companion
export REACHY_MINI_EXTERNAL_PROFILES_DIRECTORY="$ROOT/profiles"
export REACHY_MINI_EXTERNAL_TOOLS_DIRECTORY="$ROOT/tools"
export HF_REALTIME_CONNECTION_MODE=local
export HF_REALTIME_WS_URL="${ANDY_VOICE_URL:-ws://127.0.0.1:8765/v1/realtime}"
export REALTIME_TRANSCRIPTION_LANGUAGE=en
cd "$ROOT"
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$APP_PY" "$ROOT/scripts/run_andy.py" "$@"
