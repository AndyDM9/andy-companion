"""Check video-file metadata before uploading; never inspect or transcribe its content.

  uv run python scripts/check_video.py final-cut.mp4 --hardware-clip uncut-robot-take.mp4

Requires ffprobe (from FFmpeg). Passing checks duration/tracks only: a black video
can pass. Actual robot operation, use of the uncut clip, English translation,
rights, privacy, YouTube visibility and the final submission remain manual.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import shutil
import subprocess

MANUAL = ["actual hardware operating in the clip", "hardware clip included uncut in the final video",
          "English or checked English translation/subtitles", "rights to all people, images, music and marks",
          "no private links, credentials or personal details visible", "public YouTube upload and submitted URL"]


def metadata(path: Path, runner=subprocess.run):
    if not path.is_file():
        raise ValueError("video file missing")
    program = shutil.which("ffprobe")
    if not program:
        raise ValueError("ffprobe missing; install FFmpeg")
    # An explicit local path and protocol allowlist prevent playlist/network input.
    result = runner([program, "-v", "error", "-protocol_whitelist", "file,pipe", "-show_entries",
                     "format=duration:stream=codec_type,duration", "-of", "json", str(path.resolve())],
                    capture_output=True, timeout=20)
    if result.returncode:
        raise ValueError("video metadata could not be read")
    try:
        data = json.loads(result.stdout)
        duration = float(data["format"]["duration"])
        if not math.isfinite(duration) or duration <= 0:
            raise ValueError()
        streams = data["streams"]
        if not isinstance(streams, list):
            raise ValueError()
        video_durations = [float(s["duration"]) for s in streams if s.get("codec_type") == "video"
                           and s.get("duration") not in (None, "N/A")]
        if any(not math.isfinite(d) or d <= 0 for d in video_durations):
            raise ValueError()
        # A long audio track must not stand in for the hardware video track.
        video_seconds = max(video_durations) if video_durations else None
        return {"container_seconds": duration, "video_seconds": video_seconds,
                "has_video": any(s.get("codec_type") == "video" for s in streams),
                "has_audio": any(s.get("codec_type") == "audio" for s in streams)}
    except (ValueError, TypeError, KeyError, AttributeError):
        raise ValueError("video metadata invalid or incomplete") from None


def check(final, hardware):
    checks = {"final_has_video": final["has_video"], "final_has_audio": final["has_audio"],
              "final_under_180_seconds": final["container_seconds"] < 180,
              "final_video_under_180_seconds": final["video_seconds"] is not None and final["video_seconds"] < 180,
              "hardware_has_video": hardware["has_video"],
              "hardware_video_at_least_60_seconds": hardware["video_seconds"] is not None and hardware["video_seconds"] >= 60,
              "hardware_clip_fits_final": (hardware["video_seconds"] is not None and final["video_seconds"] is not None and
                                           hardware["video_seconds"] <= final["video_seconds"])}
    return {"metadata_checks_passed": all(checks.values()), "checks": checks, "final": final,
            "hardware_clip": hardware, "manual_checks_still_required": MANUAL,
            "scope": "Local file metadata only; not proof of hardware content, rights or submission readiness."}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("video", type=Path)
    parser.add_argument("--hardware-clip", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report = check(metadata(args.video), metadata(args.hardware_clip))
    except Exception as error:
        # ffprobe errors/metadata and filenames can contain private words: never echo them.
        print(json.dumps({"metadata_checks_passed": False, "error_type": type(error).__name__,
                          "fix": "Check local files, readable video-track duration and ffprobe installation.",
                          "manual_checks_still_required": MANUAL}))
        return 2
    print(json.dumps(report, indent=2))
    return 0 if report["metadata_checks_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
