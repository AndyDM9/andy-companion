#!/usr/bin/env bash
# Install Andy as two systemd user services that start at login and restart on failure.
#   scripts/install-services.sh            install (not enabled)
#   scripts/install-services.sh --enable   install, enable and start now
# Only one program may drive the robot: stop any other robot app before enabling.
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST="$HOME/.config/systemd/user"
mkdir -p "$DEST"
for unit in andy-voice.service andy.service; do
  sed "s|@ROOT@|$ROOT|g" "$ROOT/systemd/$unit" > "$DEST/$unit"
done
systemctl --user daemon-reload
echo "Installed andy-voice.service and andy.service in $DEST"
if [ "${1:-}" = "--enable" ]; then
  systemctl --user enable --now andy-voice.service andy.service
  echo "Enabled and started. Logs: journalctl --user -u andy -f"
else
  echo "To start at login: $0 --enable   (stop any other robot app first)"
fi
