#!/usr/bin/env bash
# The robot side: Pollen's conversation app with this repo's companion profile and tools,
# pointed at the local voice server. Needs the Reachy Mini daemon running.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
APP_PY="${ANDY_APP_PYTHON:-$ROOT/robot/.venv/bin/python}"   # cd robot && uv sync
export REACHY_MINI_CUSTOM_PROFILE=companion
export REACHY_MINI_EXTERNAL_PROFILES_DIRECTORY="$ROOT/profiles"
export REACHY_MINI_EXTERNAL_TOOLS_DIRECTORY="$ROOT/tools"
export HF_REALTIME_CONNECTION_MODE=local
export HF_REALTIME_WS_URL="${ANDY_VOICE_URL:-ws://127.0.0.1:8765/v1/realtime}"
export REALTIME_TRANSCRIPTION_LANGUAGE=en
cd "$ROOT"
# Only the web key and the vision endpoint's own token reach the robot side; the model key stays
# with the voice server.
ENV_FILE="${ANDY_ENV_FILE:-$HOME/.config/companion-hackathon/.env}"
if [ -f "$ENV_FILE" ]; then
  TAVILY_API_KEY="$(sed -n 's/^TAVILY_API_KEY=//p' "$ENV_FILE" | tail -1)"
  ANDY_VISION_URL="$(sed -n 's/^ANDY_VISION_URL=//p' "$ENV_FILE" | tail -1)"
  ANDY_VISION_TOKEN="$(sed -n 's/^ANDY_VISION_TOKEN=//p' "$ENV_FILE" | tail -1)"
  export TAVILY_API_KEY ANDY_VISION_URL ANDY_VISION_TOKEN
fi
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$APP_PY" "$ROOT/scripts/run_andy.py" "$@"
