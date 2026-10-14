#!/usr/bin/env bash
# Run the scam-check evaluation's model runs (evals/scam_eval.py) as Nebius Serverless Jobs, against the
# Tavily warnings already fetched once (scam_eval.py --lookup --spend): no Tavily key leaves this computer.
#
# Two limits shape it (both met on 2026-10-14): a job's whole request may hold 64 KB ("plaintext must not
# exceed 65536 bytes", the files as base64), so the messages go in four parts; and a new account may run two
# VMs at once (quota compute.instance.count = 2), so the parts run two at a time. Each part's scorecard is kept
# in evals/results/scam-parts-<stamp>/, so a part that failed can be run again alone, and all are merged.
#
#   cloud/scam-job.sh evals/results/scam-warnings-<date>.json [runs, default 3]
#   ANDY_SCAM_STAMP=<stamp> ANDY_SCAM_ONLY="3 4" cloud/scam-job.sh …     run only the missing parts again
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ANDY_ENV_FILE:-$HOME/.config/companion-hackathon/.env}"
PROJECT="${NEBIUS_JOB_PROJECT:-${NEBIUS_PROJECT:-$(nebius config get parent-id 2>/dev/null || true)}}"
SECRET="andy-token-factory"
WARNINGS="${1:?usage: $0 evals/results/scam-warnings-<date>.json [runs]}"
RUNS="${2:-3}"
PARTS="${ANDY_SCAM_PARTS:-4}"
AT_ONCE="${ANDY_JOBS_AT_ONCE:-2}"
STAMP="${ANDY_SCAM_STAMP:-$(date +%Y%m%d-%H%M%S)}"
ONLY="${ANDY_SCAM_ONLY:-$(seq -s ' ' 1 "$PARTS")}"
KEEP="$ROOT/evals/results/scam-parts-$STAMP"
mkdir -p "$KEEP"

# shellcheck source=cloud/secret.sh
. "$ROOT/cloud/secret.sh"
KEY="$(sed -n 's/^NEBIUS_API_KEY=//p' "$ENV_FILE" | tail -1)"
[ -n "$KEY" ] || { echo "No NEBIUS_API_KEY in $ENV_FILE" >&2; exit 1; }
printf '%s' "$KEY" | store_secret "$SECRET" NEBIUS_API_KEY "Token Factory key for Andy's evaluations"
unset KEY

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"' EXIT

launch() {   # part number → a job running this part's messages
  local k="$1" name="andy-scam-$STAMP-$1"
  mkdir -p "$WORK/$k/evals/results" "$WORK/$k/src/andy_companion"
  # Only what the check reads: each message's warnings without their links, for this part's messages.
  python3 - "$ROOT/evals/scam_messages.json" "$ROOT/$WARNINGS" "$k" "$PARTS" "$WORK/$k/warnings.json" <<'PY'
import json, sys
msgs, wfile, k, n, out = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4]), sys.argv[5]
ids = {m["id"] for m in json.load(open(msgs))["messages"][k - 1::n]}
data = json.load(open(wfile))
keep = [{"id": m["id"], "warnings": [{x: w.get(x, "") for x in ("source", "title", "summary")} for w in m["warnings"]]}
        for m in data["messages"] if m["id"] in ids]
json.dump({"fetched": data.get("fetched", ""), "messages": keep}, open(out, "w"), separators=(",", ":"), ensure_ascii=False)
PY
  cp "$ROOT/evals/scam_eval.py" "$ROOT/evals/scam_messages.json" "$WORK/$k/evals/"
  cp "$ROOT/src/andy_companion/__init__.py" "$ROOT/src/andy_companion/scamcheck.py" "$WORK/$k/src/andy_companion/"
  tar -C "$WORK/$k" -cf - evals src warnings.json | xz -9e | base64 -w0 > "$WORK/bundle-$k.b64"
  # The container has Python but may lack xz: Python unpacks the bundle itself.
  cat > "$WORK/entry-$k.sh" <<SH
#!/bin/sh
set -e
cd /andy
python3 -c "import base64, io, tarfile; tarfile.open(fileobj=io.BytesIO(base64.b64decode(open('bundle.b64').read())), mode='r:xz').extractall()"
ANDY_IN_JOB=1 exec python3 evals/scam_eval.py --warnings warnings.json --runs $RUNS --part $k/$PARTS
SH
  nebius ai job create --async --name "$name" --parent-id "$PROJECT" \
    --image python:3.12-slim \
    --container-command "sh" --args "/andy/entry.sh" \
    --inject-file "$WORK/entry-$k.sh:/andy/entry.sh" \
    --inject-file "$WORK/bundle-$k.b64:/andy/bundle.b64" \
    --env-secret "NEBIUS_API_KEY=$SECRET" \
    --platform cpu-d3 --preset 2vcpu-8gb --disk-size 20Gi \
    --timeout 1h --restart-policy never >/dev/null
  echo "Part $k: job $name started ($(wc -c < "$WORK/bundle-$k.b64") bytes)"
}

state() { nebius ai job get-by-name --name "$1" --parent-id "$PROJECT" --format json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status",{}).get("state",""))'; }

finish() {   # part number → wait for its job, keep its scorecard
  local k="$1" name="andy-scam-$STAMP-$1" st id log
  for _ in $(seq 1 160); do
    st="$(state "$name")"
    case "$st" in COMPLETED|SUCCEEDED|FAILED|ERROR|CANCELLED) break ;; esac
    sleep 15
  done
  echo "Part $k: $st"
  id="$(nebius ai job get-by-name --name "$name" --parent-id "$PROJECT" --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["metadata"]["id"])')"
  log="$WORK/$name.log"
  nebius ai job logs "$id" 2>/dev/null > "$log" || nebius ai job logs --id "$id" > "$log" || true
  # The job's log cuts a line at 16,384 characters and may not keep lines in order (2026-10-14): the scorecard
  # comes as numbered chunks; an older log's single line is joined with the piece cut from it.
  python3 -c '
import itertools, json, re, sys
lines = open(sys.argv[3]).read().splitlines()
chunks = {}
for line in lines:
    m = re.match(r"SCORECARD_CHUNK (\d+)/(\d+) (.*)$", line)
    if m:
        chunks[int(m.group(1))] = m.group(3)
if chunks:
    card = json.loads("".join(chunks[i] for i in sorted(chunks)))
else:
    head = [l for l in lines if l.startswith("SCORECARD_JSON ")][-1][len("SCORECARD_JSON "):]
    # The pieces cut from it are the other lines holding JSON (the job prints no other double quotes).
    pieces = [l for l in lines if "\"" in l and not l.startswith("SCORECARD_JSON ")]
    for order in itertools.permutations(pieces):
        try:
            card = json.loads(head + "".join(order)); break
        except ValueError:
            continue
    else:
        raise SystemExit("no scorecard")
card["ran_on"] = "Nebius Serverless Job, cpu-d3 2vcpu-8gb"; card["job"] = sys.argv[1]
card["warnings_file"] = sys.argv[2]
print(json.dumps(card))' "$name" "$(basename "$WARNINGS")" "$log" > "$KEEP/part-$k.json" 2>/dev/null \
    || { rm -f "$KEEP/part-$k.json"; echo "Part $k: no scorecard; run it again with ANDY_SCAM_STAMP=$STAMP ANDY_SCAM_ONLY=\"$k\""; }
}

# A part already kept (a run again for the missing ones) is collected, not run again.
collect_only="${ANDY_SCAM_COLLECT:-}"
for k in $collect_only; do finish "$k"; done

set -- $ONLY
while [ $# -gt 0 ]; do
  batch=()
  for _ in $(seq 1 "$AT_ONCE"); do [ $# -gt 0 ] && { batch+=("$1"); shift; }; done
  for k in "${batch[@]}"; do launch "$k"; done
  for k in "${batch[@]}"; do finish "$k"; done
done

have="$(ls "$KEEP"/part-*.json 2>/dev/null | wc -l)"
if [ "$have" -eq "$PARTS" ]; then
  cd "$ROOT" && python3 evals/scam_eval.py --merge "$KEEP"/part-*.json
else
  echo "$have of $PARTS parts have scorecards in ${KEEP#$ROOT/}; run the missing ones again (see above)."
fi
