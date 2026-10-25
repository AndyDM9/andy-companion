#!/usr/bin/env bash
# The voice server: NVIDIA Parakeet speech-to-text on the local GPU, NVIDIA Nemotron on
# Nebius Token Factory as the brain, local text-to-speech. Serves the OpenAI Realtime
# protocol that Pollen's Reachy Mini conversation app speaks, on 127.0.0.1:8765.
set -euo pipefail
cd "$(dirname "$0")"
ENV_FILE="${ANDY_ENV_FILE:-$HOME/.config/companion-hackathon/.env}"
[ -r "$ENV_FILE" ] || { echo "No env file at $ENV_FILE: copy .env.example there, chmod 600 it, add NEBIUS_API_KEY" >&2; exit 1; }
# Only the settings this server uses come from the env file, never the whole file (it holds other keys); a name
# already set in the shell wins. Plain NAME=value lines; one pair of surrounding quotes is dropped.
setting() {
  local v
  v="$(sed -n "s/^$1=//p" "$ENV_FILE" | tail -1)"
  v="${v%\"}"; v="${v#\"}"; v="${v%\'}"; v="${v#\'}"
  printf '%s' "$v"
}
for name in NEBIUS_API_KEY NEBIUS_BASE_URL ANDY_MODEL ANDY_VOICE_GPU ANDY_MAX_TURN_S; do
  [ -n "${!name:-}" ] || printf -v "$name" '%s' "$(setting "$name")"
done
: "${NEBIUS_API_KEY:?NEBIUS_API_KEY is not set in $ENV_FILE}"
[ -z "$ANDY_MAX_TURN_S" ] || export ANDY_MAX_TURN_S            # read by serve.py
# The key reaches serve.py through the environment, never this command line, where `ps` would show it.
export NEBIUS_API_KEY
# The first GPU unless ANDY_VOICE_GPU (in the env file or the shell) picks another: a computer with one
# GPU has only GPU 0, and asking for 1 there leaves the voice server with none.
export CUDA_VISIBLE_DEVICES="${ANDY_VOICE_GPU:-0}"
exec .venv/bin/python serve.py serve \
  --llm_backend chat-completions \
  --model_name "${ANDY_MODEL:-nvidia/Nemotron-3_5-Lightning}" \
  --responses_api_base_url "${NEBIUS_BASE_URL:-https://api.tokenfactory.nebius.com/v1/}" \
  --responses_api_stream \
  "$@"
