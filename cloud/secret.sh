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

store_secret() {
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
  # A failure part-way still removes the file; the trap is cleared once it is gone.
  trap "rm -f '$req'" EXIT
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
  rm -f "$req"; trap - EXIT
  echo "Secret $name stored."
}
