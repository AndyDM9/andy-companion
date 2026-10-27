#!/usr/bin/env bash
# Andy's finder tested in simulation as Nebius Serverless Jobs (PLAN B48): sim/finder_sim.py in a CPU container,
# Pollen's Reachy Mini MuJoCo scene rendered in software (OSMesa), the eyes on Token Factory. Two jobs, two at a time
# (a new account's quota): the search zoomed in, and the old way (one shrunk picture per view), on the same seed.
#
#   cloud/sim-job.sh run [trials, default 30] [duck scale, default 0.35]
#
# A job's request may hold 64 KB, so the code goes as one compressed bundle; the scene (24 MB) comes from PyPI
# inside the job (reachy-mini==1.12.0rc1, the robot's own version, without its dependencies).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
ENV_FILE="${ANDY_ENV_FILE:-$HOME/.config/companion-hackathon/.env}"
PROJECT="${NEBIUS_JOB_PROJECT:-${NEBIUS_PROJECT:-$(nebius config get parent-id 2>/dev/null || true)}}"
SECRET="andy-token-factory"
# Nothing starts without the word run, and anything but numbers after it (--help included) prints the usage:
# nothing is stored or started, so nothing is paid.
if [ "${1:-}" != run ]; then sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 2; fi
shift
TRIALS="${1:-30}"
SCALE="${2:-0.35}"
if ! [[ $TRIALS =~ ^[0-9]+$ && $SCALE =~ ^[0-9.]+$ ]]; then sed -n '2,9p' "$0" | sed 's/^# \{0,1\}//'; exit 2; fi
SEED="${ANDY_SIM_SEED:-21}"
STAMP="$(date +%Y%m%d-%H%M%S)"

# shellcheck source=cloud/secret.sh
. "$ROOT/cloud/secret.sh"
confirm_paid "Runs two Nebius Serverless Jobs ($TRIALS trials each): two 4-vCPU VMs for up to two hours, and the Token Factory calls."
KEY="$(sed -n 's/^NEBIUS_API_KEY=//p' "$ENV_FILE" | tail -1)"
[ -n "$KEY" ] || { echo "No NEBIUS_API_KEY in $ENV_FILE" >&2; exit 1; }
printf '%s' "$KEY" | store_secret "$SECRET" NEBIUS_API_KEY "Token Factory key for Andy's evaluations"
unset KEY

WORK="$(mktemp -d)"; trap 'rm -rf "$WORK"; jobs_left' EXIT; trap 'exit 130' INT TERM
mkdir -p "$WORK/b/sim" "$WORK/b/src/andy_companion"
cp "$ROOT/sim/finder_sim.py" "$WORK/b/sim/"
for f in __init__ finder vision reading measure model_reply; do cp "$ROOT/src/andy_companion/$f.py" "$WORK/b/src/andy_companion/"; done
tar -C "$WORK/b" -cf - sim src | xz -9e | base64 -w0 > "$WORK/bundle.b64"

launch() {   # zoom on|off → a job
  local zoom="$1" name="andy-sim-$STAMP-$1"
  cat > "$WORK/entry-$zoom.sh" <<SH
#!/bin/sh
set -e
apt-get update -qq >/dev/null && apt-get install -y -qq --no-install-recommends libosmesa6 libgl1 >/dev/null
pip install -q --no-cache-dir mujoco==3.3.0 numpy "opencv-python-headless>=4.10,<5" PyOpenGL >/dev/null
pip download -q --no-deps reachy-mini==1.12.0rc1 -d /tmp/wheel >/dev/null
cd /andy
python3 -c "import base64, io, tarfile, zipfile, glob; tarfile.open(fileobj=io.BytesIO(base64.b64decode(open('bundle.b64').read())), mode='r:xz').extractall(filter='data'); z = zipfile.ZipFile(glob.glob('/tmp/wheel/*.whl')[0]); [z.extract(n, '/andy/pkg') for n in z.namelist() if '/descriptions/' in n]"
export ANDY_SIM_MJCF=/andy/pkg/reachy_mini/descriptions/reachy_mini/mjcf MUJOCO_GL=osmesa PYOPENGL_PLATFORM=osmesa
export ANDY_SIM_WHERE="Nebius Serverless Job, cpu-d3 4vcpu-16gb"
exec python3 sim/finder_sim.py --trials $TRIALS --seed $SEED --zoom $zoom --duck-scale $SCALE --out -
SH
  nebius ai job create --async --name "$name" --parent-id "$PROJECT" \
    --image python:3.12-slim \
    --container-command "sh" --args "/andy/entry.sh" \
    --inject-file "$WORK/entry-$zoom.sh:/andy/entry.sh" \
    --inject-file "$WORK/bundle.b64:/andy/bundle.b64" \
    --env-secret "NEBIUS_API_KEY=$SECRET" \
    --platform cpu-d3 --preset 4vcpu-16gb --disk-size 20Gi \
    --timeout 2h --restart-policy never >/dev/null
  STARTED_JOBS+=("$name")
  echo "Zoom $zoom: job $name started ($(wc -c < "$WORK/bundle.b64") bytes of code)"
}

state() { nebius ai job get-by-name --name "$1" --parent-id "$PROJECT" --format json \
  | python3 -c 'import json,sys; print(json.load(sys.stdin).get("status",{}).get("state",""))'; }

finish() {   # zoom on|off → wait for its job, keep its scorecard
  local zoom="$1" name="andy-sim-$STAMP-$1" st id log out
  for _ in $(seq 1 480); do
    st="$(state "$name")"
    case "$st" in COMPLETED|SUCCEEDED|FAILED|ERROR|CANCELLED) break ;; esac
    sleep 15
  done
  echo "Zoom $zoom: $st"
  id="$(nebius ai job get-by-name --name "$name" --parent-id "$PROJECT" --format json | python3 -c 'import json,sys; print(json.load(sys.stdin)["metadata"]["id"])')"
  log="$WORK/$name.log"
  nebius ai job logs "$id" 2>/dev/null > "$log" || nebius ai job logs --id "$id" > "$log" || true
  out="$ROOT/evals/results/sim-finder-$STAMP-$zoom-small$SCALE-nebius-job.json"
  python3 -c '
import json, sys
line = [l for l in open(sys.argv[1]).read().splitlines() if l.startswith("SIM_SCORECARD ")][-1]
card = json.loads(line[len("SIM_SCORECARD "):]); card["job"] = sys.argv[2]
print(json.dumps(card, indent=1))' "$log" "$name" > "$out" 2>/dev/null \
    && python3 -c 'import json,sys; s=json.load(open(sys.argv[1]))["summary"]; print("  pointed", s["pointed"], "of", s["present"], s["pointed_95"], "false finds", s["false_finds"], "of", s["absent"], "error median", s["error_deg_median"], "deg")' "$out" \
    || { rm -f "$out"; echo "Zoom $zoom: no scorecard (log kept: $(cp "$log" "$ROOT/evals/results/" && echo "evals/results/$name.log"))"; }
}

launch on; launch off
finish on; finish off
JOBS_DONE=1
