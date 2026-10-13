#!/usr/bin/env bash
# Run Andy's conversation suite as a Nebius Serverless Job: a plain Python container on a small CPU
# VM, the suite and Andy's real profile injected as files, the Token Factory key from Nebius's
# secret store (never in the job's settings). Prints the scorecard from the job's logs.
#
#   cloud/safety-job.sh run      create the job, wait for it, print and save the scorecard
#   cloud/safety-job.sh secret   store or refresh the Token Factory key in the secret store
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ANDY_ENV_FILE:-$HOME/.config/companion-hackathon/.env}"
# Any project whose region allows CPU VMs (new accounts often have no CPU quota in eu-north1).
PROJECT="${NEBIUS_JOB_PROJECT:-${NEBIUS_PROJECT:-$(nebius config get parent-id 2>/dev/null || true)}}"
SECRET="andy-token-factory"
RUNS="${ANDY_SUITE_RUNS:-3}"

secret() {
  KEY="$(sed -n 's/^NEBIUS_API_KEY=//p' "$ENV_FILE" | tail -1)"
  [ -n "$KEY" ] || { echo "No NEBIUS_API_KEY in $ENV_FILE" >&2; exit 1; }
  PAYLOAD="$(python3 -c 'import json,sys; print(json.dumps([{"key": "NEBIUS_API_KEY", "string_value": sys.argv[1]}]))' "$KEY")"
  if nebius mysterybox secret get-by-name --name "$SECRET" --parent-id "$PROJECT" >/dev/null 2>&1; then
    echo "Secret $SECRET already stored."
  else
    nebius mysterybox secret create --name "$SECRET" --parent-id "$PROJECT" \
      --description "Token Factory key for Andy's conversation suite" \
      --secret-version-payload "$PAYLOAD" >/dev/null
    echo "Secret $SECRET stored."
  fi
}

run() {
  secret
  NAME="andy-suite-$(date +%Y%m%d-%H%M%S)"
  nebius ai job create --async --name "$NAME" --parent-id "$PROJECT" \
    --image python:3.12-slim \
    --container-command "python3" \
    --args "/andy/evals/run_suite.py --runs $RUNS" \
    --inject-file "$ROOT/evals/run_suite.py:/andy/evals/run_suite.py" \
    --inject-file "$ROOT/evals/suite.json:/andy/evals/suite.json" \
    --inject-file "$ROOT/profiles/companion/profile.md:/andy/profiles/companion/profile.md" \
    --env-secret "NEBIUS_API_KEY=$SECRET" \
    --platform cpu-d3 --preset 2vcpu-8gb --disk-size 20Gi \
    --timeout 1h --restart-policy never >/dev/null
  echo "Job $NAME started; waiting for it to finish…"
  for _ in $(seq 1 120); do
    STATE="$(nebius ai job get-by-name --name "$NAME" --parent-id "$PROJECT" --format json | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status",{}).get("state",""))')"
    case "$STATE" in COMPLETED|SUCCEEDED|FAILED|ERROR|CANCELLED) break ;; esac
    sleep 15
  done
  echo "Job state: $STATE"
  ID="$(nebius ai job get-by-name --name "$NAME" --parent-id "$PROJECT" --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["metadata"]["id"])')"
  mkdir -p "$ROOT/evals/results"
  nebius ai job logs "$ID" 2>/dev/null > "$ROOT/evals/results/.job.log" || nebius ai job logs --id "$ID" > "$ROOT/evals/results/.job.log"
  grep -v '^SCORECARD_JSON' "$ROOT/evals/results/.job.log" | grep -vE '^\s*$' | tail -25
  OUT="$ROOT/evals/results/$(date +%Y-%m-%d)-nebius-job-$NAME.json"
  grep -o 'SCORECARD_JSON .*' "$ROOT/evals/results/.job.log" | tail -1 | sed 's/^SCORECARD_JSON //' | python3 -c '
import json, sys
card = json.loads(sys.stdin.read()); card["ran_on"] = "Nebius Serverless Job, cpu-d3 2vcpu-8gb"; card["job"] = sys.argv[1]
print(json.dumps(card, indent=2))' "$NAME" > "$OUT" && echo "Scorecard saved: ${OUT#$ROOT/}"
  rm -f "$ROOT/evals/results/.job.log"
}

case "${1:-run}" in run) run ;; secret) secret ;; *) echo "usage: $0 run|secret" >&2; exit 2 ;; esac
