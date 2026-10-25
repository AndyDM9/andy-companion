#!/usr/bin/env bash
# Andy's eyes on Nebius AI Cloud: NVIDIA Nemotron Nano 12B v2 VL (FP8) served by vLLM on one L40S,
# as a Nebius Serverless Endpoint. The same token is required twice: by Nebius at the HTTPS address,
# and by vLLM itself, so the endpoint's plain IP:port address is locked too.
#
#   cloud/vision-endpoint.sh create     create it (prints the URL; saves URL and token to the env file)
#   cloud/vision-endpoint.sh start|stop  stopped endpoints are not charged for compute
#   cloud/vision-endpoint.sh status|delete
#
# Needs the Nebius CLI with a profile for an eu-north1 project (L40S is offered there).
set -euo pipefail
# shellcheck source=cloud/secret.sh
. "$(cd "$(dirname "$0")" && pwd)/secret.sh"
NAME="${ANDY_VISION_NAME:-andy-vision}"
ENV_FILE="${ANDY_ENV_FILE:-$HOME/.config/companion-hackathon/.env}"
MODEL="nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-FP8"
IMAGE="vllm/vllm-openai:v0.30.0"
id_of() { nebius ai endpoint get-by-name --name "$NAME" --format json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["metadata"]["id"])'; }
save() ( # key value: replace or add one line in the private env file; every copy owner-only from the start
  umask 077
  mkdir -p "$(dirname "$ENV_FILE")"; touch "$ENV_FILE"; chmod 600 "$ENV_FILE"
  tmp="$(mktemp "$ENV_FILE.XXXXXX")"; trap 'rm -f "$tmp"' EXIT
  grep -v "^$1=" "$ENV_FILE" > "$tmp" || true
  printf '%s=%s\n' "$1" "$2" >> "$tmp"; mv "$tmp" "$ENV_FILE"
)
PRICE="one L40S GPU, billed by the hour while running (about \$1.55 an hour, cloud/README.md)"
STOP_NOTE="Billed by the hour from now until: $0 stop"
need_id() { local id; id="$(id_of || true)"; [ -n "$id" ] || { echo "No endpoint called $NAME." >&2; exit 1; }; echo "$id"; }
case "${1:-status}" in
  create)
    TOKEN="$(openssl rand -hex 32)"
    # The token never goes on a command line, where `ps` would show it: it is stored in MysteryBox (through
    # a pipe, secret.sh), and the endpoint reads it from there twice: --token-secret for Nebius's own check
    # at the HTTPS address, and VLLM_API_KEY, which vLLM reads in place of --api-key, for the plain IP:port.
    if [ -z "${DRY_RUN:-}" ]; then
      confirm_paid "Creates and starts the endpoint $NAME: $PRICE."
      # A new token replaces the stored one, so never while an endpoint of this name exists: it would keep
      # reading the old one, and the new one would be lost if create then failed (review, 2026-10-14).
      if [ -n "$(id_of || true)" ]; then
        echo "An endpoint called $NAME exists already: '$0 start' to use it, or '$0 delete' first." >&2
        exit 1
      fi
      # Kept here first, so this computer and the secret store always agree.
      save ANDY_VISION_TOKEN "$TOKEN"
      printf '%s' "$TOKEN" | store_secret "$NAME-auth" AUTH_TOKEN "Endpoint token for $NAME" replace
      printf '%s' "$TOKEN" | store_secret "$NAME-vllm" VLLM_API_KEY "vLLM key for $NAME" replace
    fi
    nebius ai endpoint create ${DRY_RUN:+--dry-run} --async \
      --name "$NAME" \
      --image "$IMAGE" \
      --container-command "python3 -m vllm.entrypoints.openai.api_server" \
      --args "--model $MODEL --served-model-name nemotron-vl --trust-remote-code --quantization modelopt --max-model-len 8192 --port 8000" \
      --container-port 8000 \
      --platform gpu-l40s-a --preset 1gpu-8vcpu-32gb \
      --disk-size 100Gi --shm-size 8Gi \
      --public --on-demand \
      --env-secret "VLLM_API_KEY=$NAME-vllm" \
      --auth token --token-secret "$NAME-auth"
    [ -n "${DRY_RUN:-}" ] && exit 0
    echo "Created. Run '$0 status' until it is RUNNING; the URL is saved when it is."
    echo "$STOP_NOTE"
    ;;
  status)
    nebius ai endpoint get-by-name --name "$NAME" --format json | python3 -c '
import json, sys
d = json.load(sys.stdin); s = d.get("status", {})
https = [e for e in s.get("public_endpoints", []) if e.startswith("https://")]
print("state:", s.get("state"), "| url:", (https or ["-"])[0])'
    # Only the managed HTTPS address: the plain IP:port one would send the token and pictures unencrypted.
    URL="$(nebius ai endpoint get-by-name --name "$NAME" --format json | python3 -c 'import json,sys; s=json.load(sys.stdin).get("status",{}); print(next((e for e in s.get("public_endpoints", []) if e.startswith("https://")), ""))')"
    [ -n "$URL" ] && save ANDY_VISION_URL "$URL" || true
    ;;
  start) ID="$(need_id)"; nebius ai endpoint start --id "$ID"; echo "$STOP_NOTE" ;;
  stop|delete) ID="$(need_id)"; nebius ai endpoint "$1" --id "$ID" ;;
  *) echo "usage: $0 create|start|stop|status|delete" >&2; exit 2 ;;
esac
