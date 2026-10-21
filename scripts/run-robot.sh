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
export REALTIME_TRANSCRIPTION_LANGUAGE="${ANDY_LANGUAGE:-en}"   # a hint only: Parakeet detects the spoken language itself
cd "$ROOT"
# Only these reach the robot side: the web key, which eyes, the eyes' and the second look's endpoint addresses
# and tokens, and the Token Factory key, which the app itself uses for the scam check, letters, On this day
# and think_it_through. Nothing else in the env file is passed on.
ENV_FILE="${ANDY_ENV_FILE:-$HOME/.config/companion-hackathon/.env}"
if [ -f "$ENV_FILE" ]; then
  TAVILY_API_KEY="$(sed -n 's/^TAVILY_API_KEY=//p' "$ENV_FILE" | tail -1)"
  TAVILY_PROJECT="$(sed -n 's/^TAVILY_PROJECT=//p' "$ENV_FILE" | tail -1)"      # X-Project-ID; web.py's default if empty
  ANDY_VISION_URL="$(sed -n 's/^ANDY_VISION_URL=//p' "$ENV_FILE" | tail -1)"
  ANDY_VISION_TOKEN="$(sed -n 's/^ANDY_VISION_TOKEN=//p' "$ENV_FILE" | tail -1)"
  ANDY_GUARD_URL="$(sed -n 's/^ANDY_GUARD_URL=//p' "$ENV_FILE" | tail -1)"
  ANDY_GUARD_TOKEN="$(sed -n 's/^ANDY_GUARD_TOKEN=//p' "$ENV_FILE" | tail -1)"
  NEBIUS_API_KEY="$(sed -n 's/^NEBIUS_API_KEY=//p' "$ENV_FILE" | tail -1)"      # Ultra, the scam check, and the eyes on Token Factory
  ANDY_VISION="$(sed -n 's/^ANDY_VISION=//p' "$ENV_FILE" | tail -1)"              # token-factory (default), endpoint or off
  # Off unless the env file names a folder: the finder then keeps each try there for scoring (live test 3t2).
  ANDY_FINDER_RECORD="${ANDY_FINDER_RECORD:-$(sed -n 's/^ANDY_FINDER_RECORD=//p' "$ENV_FILE" | tail -1)}"
  export ANDY_FINDER_RECORD
  [ -n "$TAVILY_PROJECT" ] && export TAVILY_PROJECT
  export TAVILY_API_KEY ANDY_VISION ANDY_VISION_URL ANDY_VISION_TOKEN ANDY_GUARD_URL ANDY_GUARD_TOKEN NEBIUS_API_KEY
fi
export PYTHONPATH="$ROOT/src${PYTHONPATH:+:$PYTHONPATH}"
exec "$APP_PY" "$ROOT/scripts/run_andy.py" "$@"
