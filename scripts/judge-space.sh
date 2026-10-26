#!/usr/bin/env bash
# Build the separate guided-inference Space from tracked files in HEAD only.
# Usage: scripts/judge-space.sh /tmp/a-new-empty-folder
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
OUT="${1:?Choose a fresh output folder}"
if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
  echo "Choose an empty output folder." >&2
  exit 1
fi
mkdir -p "$OUT"
git -C "$ROOT" archive HEAD \
  src/andy_companion/__init__.py src/andy_companion/consent.py src/andy_companion/judge_playground.py \
  src/andy_companion/pages/judge.html src/andy_companion/pages/judge.js src/andy_companion/pages/fonts \
  profiles/companion/profile.md evals/tools.json scripts/judge_playground.py \
  space-judge/Dockerfile space-judge/README.md LICENSE | tar -x -C "$OUT"
mv "$OUT/space-judge/Dockerfile" "$OUT/space-judge/README.md" "$OUT/"
rmdir "$OUT/space-judge"
echo "Built judge Space from $(git -C "$ROOT" rev-parse --short HEAD); add inference only through a server secret."
