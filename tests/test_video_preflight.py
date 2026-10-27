"""Mechanical video checks do not certify footage content or actual submission."""
import importlib.util
import json
from pathlib import Path
import subprocess

import pytest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("video_preflight", ROOT / "scripts/check_video.py")
video = importlib.util.module_from_spec(spec)
spec.loader.exec_module(video)


def clip(seconds, *, audio=True, video_track=True, container=None):
    return {"container_seconds": seconds if container is None else container, "video_seconds": seconds,
            "has_video": video_track, "has_audio": audio}


@pytest.mark.parametrize("final_seconds,hardware_seconds,passed", [
    (176, 72, True), (179.999, 60, True), (180, 60, False), (176, 59.999, False),
    (59, 60, False),
])
def test_duration_boundaries(final_seconds, hardware_seconds, passed):
    assert video.check(clip(final_seconds), clip(hardware_seconds))["metadata_checks_passed"] is passed


def test_audio_padding_cannot_replace_a_minute_of_video():
    report = video.check(clip(176), clip(12, container=72))
    assert not report["metadata_checks_passed"]
    assert not report["checks"]["hardware_video_at_least_60_seconds"]
    assert not video.check(clip(20, container=176), clip(72))["metadata_checks_passed"]


@pytest.mark.parametrize("change", [{"has_video": False}, {"has_audio": False}, {"video_seconds": None}])
def test_final_track_requirements_and_unknown_duration_fail(change):
    final = {**clip(176), **change}
    assert not video.check(final, clip(72))["metadata_checks_passed"]


def test_passing_metadata_keeps_content_and_rights_checks_manual():
    report = video.check(clip(176), clip(72))
    assert report["metadata_checks_passed"]
    assert "actual hardware operating in the clip" in report["manual_checks_still_required"]
    assert "metadata only" in report["scope"]


def test_ffprobe_is_local_only_and_drops_metadata_text(tmp_path, monkeypatch):
    path = tmp_path / "invented video.mp4"
    path.write_bytes(b"synthetic fixture")
    monkeypatch.setattr(video.shutil, "which", lambda name: "/tools/ffprobe")
    def runner(args, **kwargs):
        assert args[args.index("-protocol_whitelist") + 1] == "file,pipe"
        assert args[-1] == str(path.resolve()) and kwargs["capture_output"] and kwargs["timeout"] == 20
        data = {"format": {"duration": "176", "tags": {"comment": "invented private words"}},
                "streams": [{"codec_type": "video", "duration": "175.9"}, {"codec_type": "audio"}]}
        return subprocess.CompletedProcess(args, 0, json.dumps(data).encode())
    result = video.metadata(path, runner)
    assert result == clip(175.9, container=176)
    assert "private words" not in json.dumps(result)


@pytest.mark.parametrize("duration", ["NaN", "inf", "-1", "0", "not a duration"])
def test_invalid_durations_are_refused(tmp_path, monkeypatch, duration):
    path = tmp_path / "fixture.mp4"
    path.touch()
    monkeypatch.setattr(video.shutil, "which", lambda name: "ffprobe")
    def runner(*args, **kwargs):
        return subprocess.CompletedProcess([], 0, json.dumps({"format": {"duration": duration}, "streams": []}).encode())
    with pytest.raises(ValueError):
        video.metadata(path, runner)


def test_cli_never_echoes_filename_or_external_error_text(tmp_path, monkeypatch, capsys):
    def bad(path):
        raise RuntimeError("invented private metadata")
    monkeypatch.setattr(video, "metadata", bad)
    assert video.main([str(tmp_path / "private-name.mp4"), "--hardware-clip", "raw.mp4"]) == 2
    out = capsys.readouterr().out
    assert "private-name" not in out and "private metadata" not in out
    assert json.loads(out)["metadata_checks_passed"] is False
