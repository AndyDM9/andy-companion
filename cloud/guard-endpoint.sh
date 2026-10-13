#!/usr/bin/env bash
# Andy's second look at the person's words: NVIDIA Nemotron 3.5 Content Safety (4B, English and
# Spanish among 12 languages) served by vLLM on one L40S, as a Nebius Serverless Endpoint
# (src/andy_companion/guard.py). As for the eyes, the same token is required twice: by Nebius at the
# HTTPS address and by vLLM itself. vLLM 0.20.2 is the newest the model card supports; it does not
# log request text unless --enable-log-requests is given (checked in its source, 2026-10-13).
#
#   cloud/guard-endpoint.sh create     create it (saves the token; 'status' saves the URL)
#   cloud/guard-endpoint.sh start|stop  stopped endpoints are not charged for compute
#   cloud/guard-endpoint.sh status|delete
#
# Needs the Nebius CLI with a profile for an eu-north1 project (L40S is offered there).
set -euo pipefail
NAME="${ANDY_GUARD_NAME:-andy-guard}"
ENV_FILE="${ANDY_ENV_FILE:-$HOME/.config/companion-hackathon/.env}"
MODEL="nvidia/Nemotron-3.5-Content-Safety"
IMAGE="vllm/vllm-openai:v0.20.2"
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
      --args "--model $MODEL --served-model-name nemotron-guard --max-model-len 4096 --port 8000 --api-key $TOKEN" \
      --container-port 8000 \
      --platform gpu-l40s-a --preset 1gpu-8vcpu-32gb \
      --disk-size 100Gi --shm-size 8Gi \
      --public --on-demand \
      --auth token --token "$TOKEN"
    [ -n "${DRY_RUN:-}" ] && exit 0
    save ANDY_GUARD_TOKEN "$TOKEN"
    echo "Created. Run '$0 status' until it is RUNNING; the URL is saved when it is."
    ;;
  status)
    nebius ai endpoint get-by-name --name "$NAME" --format json | python3 -c '
import json, sys
d = json.load(sys.stdin); s = d.get("status", {})
https = [e for e in s.get("public_endpoints", []) if e.startswith("https://")]
print("state:", s.get("state"), "| url:", (https or ["-"])[0])'
    # Only the managed HTTPS address: the plain IP:port one would send the token and words unencrypted.
    URL="$(nebius ai endpoint get-by-name --name "$NAME" --format json | python3 -c 'import json,sys; s=json.load(sys.stdin).get("status",{}); print(next((e for e in s.get("public_endpoints", []) if e.startswith("https://")), ""))')"
    [ -n "$URL" ] && save ANDY_GUARD_URL "$URL" || true
    ;;
  start|stop|delete) nebius ai endpoint "$1" --id "$(id_of)" ;;
  *) echo "usage: $0 create|start|stop|status|delete" >&2; exit 2 ;;
esac
