#!/usr/bin/env bash
# Install Andy as systemd user services that start at login and restart on failure: the voice server, Andy, and,
# when local-eyes/ has been set up (cd local-eyes && uv sync), the offline eyes (decision 0015).
#   scripts/install-services.sh            install (not enabled)
#   scripts/install-services.sh --enable   install, enable and start now
# Only one program may drive the robot: stop any other robot app before enabling.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
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
  systemctl --user enable --now $UNITS
  echo "Enabled and started. Logs: journalctl --user -u andy -f"
else
  echo "To start at login: $0 --enable   (stop any other robot app first)"
fi
