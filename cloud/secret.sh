# shellcheck shell=bash
# Sourced by the cloud scripts: store a value in Nebius MysteryBox without it ever being on a command line,
# where any process on this shared computer could read it (`ps`, /proc). The value comes on stdin and
# reaches the Nebius CLI inside a request file only this user can read, removed as soon as the call ends.
#
#   printf '%s' "$VALUE" | store_secret NAME PAYLOAD_KEY "description" [keep|replace]
#
# keep (the default): leave an existing secret as it is. replace: give an existing secret a new primary
# version, so a new endpoint token takes over from the old one.

secret_parent() { echo "${PROJECT:-$(nebius config get parent-id 2>/dev/null || true)}"; }

store_secret() (     # a subshell: its clean-up trap never touches the calling script's
  local name="$1" key="$2" description="$3" mode="${4:-keep}" parent existing req
  parent="$(secret_parent)"
  existing="$(nebius mysterybox secret get-by-name --name "$name" --parent-id "$parent" --format json 2>/dev/null \
    | python3 -c 'import json,sys; print(json.load(sys.stdin)["metadata"]["id"])' 2>/dev/null || true)"
  if [ -n "$existing" ] && [ "$mode" = keep ]; then
    cat >/dev/null                      # the value is not needed; drain it so the writer never blocks
    echo "Secret $name already stored."
    return 0
  fi
  req="$(umask 077; mktemp)"
  # A failure part-way still removes the file.
  trap 'rm -f "$req"' EXIT
  # The value is read from stdin by Python itself; only names, ids and the file's path are arguments.
  python3 -c '
import json, sys
name, key, description, parent, existing, out = sys.argv[1:]
value = sys.stdin.read()
payload = [{"key": key, "string_value": value}]
if existing:
    request = {"metadata": {"parent_id": existing}, "spec": {"payload": payload, "set_primary": True}}
else:
    request = {"metadata": {"name": name, "parent_id": parent},
               "spec": {"description": description, "secret_version": {"payload": payload}}}
with open(out, "w") as f:
    json.dump(request, f)' "$name" "$key" "$description" "$parent" "$existing" "$req"
  if [ -n "$existing" ]; then
    nebius mysterybox secret-version create --file "$req" >/dev/null
  else
    nebius mysterybox secret create --file "$req" >/dev/null
  fi
  echo "Secret $name stored."
)

# Paid resources start only after a yes; ANDY_YES=1 answers it for a run nobody is watching.
confirm_paid() {   # what it starts and what it costs
  [ "${ANDY_YES:-}" = 1 ] && return 0
  local answer=""
  printf '%s\nStart it? [y/N] ' "$1" >&2
  read -r answer 2>/dev/null </dev/tty || true      # no terminal (a script, a service): no
  case "$answer" in y|Y|yes|Yes) return 0 ;; esac
  echo "Nothing started." >&2
  exit 1
}

# The jobs this run started. If it stops before the end (an error, Ctrl-C), each is named with how to cancel it;
# each also ends by itself at its --timeout. The scripts call jobs_left from their EXIT trap, JOBS_DONE=1 at the end.
STARTED_JOBS=()
JOBS_DONE=""
jobs_left() {
  [ -z "$JOBS_DONE" ] && [ "${#STARTED_JOBS[@]}" -gt 0 ] || return 0
  echo "Stopped before the end. These jobs may still be running (and billed) until they finish or time out:" >&2
  printf '  %s\n' "${STARTED_JOBS[@]}" >&2
  echo "Cancel one with: nebius ai job cancel --id <id>  (its id: nebius ai job get-by-name --name <name> --parent-id ${PROJECT:-<project>})" >&2
}
