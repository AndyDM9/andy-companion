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
NAME="${ANDY_VISION_NAME:-andy-vision}"
ENV_FILE="${ANDY_ENV_FILE:-$HOME/.config/companion-hackathon/.env}"
MODEL="nvidia/NVIDIA-Nemotron-Nano-12B-v2-VL-FP8"
IMAGE="vllm/vllm-openai:v0.30.0"
id_of() { nebius ai endpoint get-by-name --name "$NAME" --format json 2>/dev/null | python3 -c 'import json,sys; print(json.load(sys.stdin)["metadata"]["id"])'; }
save() { # key value: replace or add one line in the private env file
  touch "$ENV_FILE"; chmod 600 "$ENV_FILE"
  grep -v "^$1=" "$ENV_FILE" > "$ENV_FILE.tmp" || true
  printf '%s=%s\n' "$1" "$2" >> "$ENV_FILE.tmp"; mv "$ENV_FILE.tmp" "$ENV_FILE"; chmod 600 "$ENV_FILE"
}
case "${1:-status}" in
  create)
    TOKEN="$(openssl rand -hex 32)"
    nebius ai endpoint create ${DRY_RUN:+--dry-run} --async \
      --name "$NAME" \
      --image "$IMAGE" \
      --container-command "python3 -m vllm.entrypoints.openai.api_server" \
      --args "--model $MODEL --served-model-name nemotron-vl --trust-remote-code --quantization modelopt --max-model-len 8192 --port 8000 --api-key $TOKEN" \
      --container-port 8000 \
      --platform gpu-l40s-a --preset 1gpu-8vcpu-32gb \
      --disk-size 100Gi --shm-size 8Gi \
      --public --on-demand \
      --auth token --token "$TOKEN"
    [ -n "${DRY_RUN:-}" ] && exit 0
    save ANDY_VISION_TOKEN "$TOKEN"
    echo "Created. Run '$0 status' until it is RUNNING; the URL is saved when it is."
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
  start|stop|delete) nebius ai endpoint "$1" --id "$(id_of)" ;;
  *) echo "usage: $0 create|start|stop|status|delete" >&2; exit 2 ;;
esac
