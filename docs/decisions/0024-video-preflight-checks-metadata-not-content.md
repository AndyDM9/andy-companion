# 0024: Video preflight checks metadata and keeps content review manual

**Date:** 2026-10-26. **Status:** accepted.

## Context

The final exporter validates a video-shaped URL and release metadata, not the movie itself.
Filming is still planned for October 27. The official rules call for a video under three minutes
and at least a minute of physical hardware operating; our shot plan adds an uncut 72-second take.
An audio track is part of our narrated demo plan, not a new interpretation of the hardware rule.

## Options

1. Review every technical property manually in an editor.
2. Check local file metadata, then review actual content, rights and publication manually.
3. Ask a model to grade video content; that adds media handling and could wrongly certify authenticity or rights.

## Decision

Choose option 2. `scripts/check_video.py` reads duration and audio/video-track metadata through ffprobe,
using local files and a file/pipe protocol allowlist. It does not transcribe, extract frames, modify
the movie or upload anything. It reports no filenames, tags or external error text.

The final container and video track must be under 180 seconds, an audio track must exist, and a
separate raw hardware video track must be at least 60 seconds and fit within the final video track.
Audio padding cannot stand in for a minute of video. Unknown video-track duration fails this
conservative check; export a file with measurable track durations or review it manually.

## Why

Cheap mechanical checks catch common packaging errors without processing conversation content.
Even a black movie can pass metadata checks. A passing report always retains manual checks for
actual hardware operation, the uncut clip's inclusion, English translation, rights, privacy,
public YouTube visibility and the actual submission. No official requirement is ticked from this tool alone.

## Consequences

FFmpeg/ffprobe is an optional local production dependency, not a new robot or hosted-service dependency.
The checker cannot establish that the two files contain the same footage or that a device really worked.

## Revisit when

- The final footage is available, or the organiser's published video requirements change.
