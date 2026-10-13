#!/usr/bin/env bash
# The voice server: NVIDIA Parakeet speech-to-text on the local GPU, NVIDIA Nemotron on
# Nebius Token Factory as the brain, local text-to-speech. Serves the OpenAI Realtime
# protocol that Pollen's Reachy Mini conversation app speaks, on 127.0.0.1:8765.
set -euo pipefail
cd "$(dirname "$0")"
ENV_FILE="${ANDY_ENV_FILE:-$HOME/.config/companion-hackathon/.env}"
set -a; . "$ENV_FILE"; set +a
: "${NEBIUS_API_KEY:?NEBIUS_API_KEY is not set in $ENV_FILE}"
export CUDA_VISIBLE_DEVICES="${ANDY_VOICE_GPU:-1}"
exec .venv/bin/speech-to-speech serve \
  --llm_backend chat-completions \
  --model_name "${ANDY_MODEL:-nvidia/Nemotron-3_5-Lightning}" \
  --responses_api_base_url "${NEBIUS_BASE_URL:-https://api.tokenfactory.nebius.com/v1/}" \
  --responses_api_api_key "$NEBIUS_API_KEY" \
  --responses_api_stream \
  "$@"
