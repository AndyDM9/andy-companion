#!/usr/bin/env bash
# Put together the public demo of Andy's screens for a Hugging Face Space (PLAN B26).
#
#   scripts/space.sh build [folder]     the Space's files in a fresh folder (default: ~/andy-space)
#
# Only what the demo needs goes in: the package's source, the demo script, the lock file and the licence,
# with space/Dockerfile and space/README.md (the Space's card). No keys, tests, evaluations or robot code.
# Then, from the folder, push it to a Space you made on huggingface.co (SDK: Docker), for example:
#   git init -b main && git add . && git commit -m "Andy's screens on sample data"
#   git remote add origin https://huggingface.co/spaces/<you>/<name> && git push -u origin main
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
[ "${1:-}" = "build" ] || { sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//' >&2; exit 2; }
OUT="${2:-$HOME/andy-space}"
if [ -e "$OUT" ] && [ -n "$(ls -A "$OUT" 2>/dev/null)" ]; then
  echo "$OUT is not empty; choose a new folder." >&2
  exit 1
fi
mkdir -p "$OUT/scripts"
cp "$ROOT/space/Dockerfile" "$ROOT/space/README.md" "$ROOT/pyproject.toml" "$ROOT/uv.lock" "$ROOT/LICENSE" "$OUT/"
cp "$ROOT/scripts/demo_screen.py" "$OUT/scripts/"
cp "$ROOT/docs/images/sim-search.mp4" "$OUT/"       # the simulated search's film, on the front page
# The source as git has it: nothing ignored, no caches.
git -C "$ROOT" archive HEAD src | tar -x -C "$OUT"
echo "The Space's files are in $OUT (from commit $(git -C "$ROOT" rev-parse --short HEAD))."
