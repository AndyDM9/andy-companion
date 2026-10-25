#!/usr/bin/env bash
# Install Andy as systemd user services that start at login and restart on failure: the voice server, Andy, and,
# when local-eyes/ has been set up (cd local-eyes && uv sync), the offline eyes (decision 0015).
#   scripts/install-services.sh            install (not enabled)
#   scripts/install-services.sh --enable   install, enable and start now
# Only one program may drive the robot: stop any other robot app before enabling.
set -euo pipefail
case "${1:-}" in
  ""|--enable) ;;
  *) sed -n '2,6p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2 ;;   # --help, a typo: the usage, nothing installed
esac
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
# The path goes into the units' ExecStart= lines and through sed: a space, | or & in it would break both.
case "$ROOT" in *[[:space:]\|\&]*) echo "The repository's path has a space, | or &: move it to a plain path first ($ROOT)." >&2; exit 1 ;; esac
DEST="$HOME/.config/systemd/user"
mkdir -p "$DEST"
UNITS="andy-voice.service andy.service"
[ -x "$ROOT/local-eyes/.venv/bin/vllm" ] && UNITS="andy-eyes.service $UNITS"
for unit in $UNITS; do
  sed "s|@ROOT@|$ROOT|g" "$ROOT/systemd/$unit" > "$DEST/$unit"
done
systemctl --user daemon-reload
echo "Installed $UNITS in $DEST"
if [ "${1:-}" = "--enable" ]; then
  # shellcheck disable=SC2086  # one word per unit
  systemctl --user enable --now $UNITS
  echo "Enabled and started. Logs: journalctl --user -u andy -f"
else
  echo "To start at login: $0 --enable   (stop any other robot app first)"
fi
