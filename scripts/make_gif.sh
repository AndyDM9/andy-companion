#!/usr/bin/env bash
# A short clip of the robot as a small looping GIF for the README and the Devpost gallery (PLAN, founder
# action 6.17). Two passes through ffmpeg with a palette made for this clip, so the colours stay clean.
#
#   scripts/make_gif.sh clip.mp4 docs/images/finding-glasses.gif [start_s] [seconds] [width]
set -euo pipefail
IN="${1:?usage: $0 clip.mp4 out.gif [start_s] [seconds] [width]}"
OUT="${2:?usage: $0 clip.mp4 out.gif [start_s] [seconds] [width]}"
START="${3:-0}"; LEN="${4:-5}"; WIDTH="${5:-640}"
PALETTE="$(mktemp --suffix=.png)"; trap 'rm -f "$PALETTE"' EXIT
FILTERS="fps=12,scale=${WIDTH}:-1:flags=lanczos"
ffmpeg -v error -y -ss "$START" -t "$LEN" -i "$IN" -vf "$FILTERS,palettegen=stats_mode=diff" "$PALETTE"
ffmpeg -v error -y -ss "$START" -t "$LEN" -i "$IN" -i "$PALETTE" \
  -lavfi "$FILTERS [x]; [x][1:v] paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" -loop 0 "$OUT"
echo "$OUT: $(du -h "$OUT" | cut -f1) (keep README GIFs under about 5 MB; shorten or narrow if larger)"
