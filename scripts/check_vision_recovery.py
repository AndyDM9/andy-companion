"""Check local-vision recovery with one real camera IPC frame; never save it or its description.

Run with robot/.venv/bin/python scripts/check_vision_recovery.py [--out metadata.json].
Only a camera reader is opened, not a robot controller. Andy may remain running.
The primary vision address is forced to closed loopback in this process only;
the frame can go only to local Cosmos. This does not test voice or pointing.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from andy_companion import app_mode, vision  # noqa: E402


@contextmanager
def isolated_settings():
    names = ("ANDY_LOCAL_EYES_URL", "ANDY_LOCAL_EYES_MODEL")
    settings = {k: v for k, v in app_mode.read_env(names).items() if k not in os.environ}
    settings.update(ANDY_VISION="endpoint", ANDY_VISION_FALLBACK="local",
                    ANDY_VISION_URL="https://127.0.0.1:1", ANDY_VISION_TOKEN="invented-local-probe")
    previous = {k: os.environ.get(k) for k in settings}
    try:
        os.environ.update(settings)
        yield
    finally:
        for k, value in previous.items():
            if value is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = value


def camera_reader():
    from reachy_mini.media.camera_constants import get_camera_specs_by_name
    from reachy_mini.media.camera_gstreamer import GStreamerCamera

    with urllib.request.urlopen("http://127.0.0.1:8000/api/camera/specs", timeout=3) as response:
        specs = json.load(response)
    return GStreamerCamera(log_level="CRITICAL", camera_specs=get_camera_specs_by_name(specs["name"]))


def probe(factory=camera_reader, describe=None, clock=time.monotonic, pause=time.sleep):
    if not vision.here(vision.local_eyes()["url"]):
        raise ValueError("local address required")
    if vision.reachable(vision.eyes()["url"]):
        raise RuntimeError("test primary must be unreachable")
    started = clock()
    camera = factory()
    try:
        camera.open()
        frame = None
        deadline = clock() + 3
        # open() consumes the first sample; read() is non-blocking, so wait for the next one.
        while frame is None and clock() < deadline:
            frame = camera.read()
            if frame is None:
                pause(0.03)
        if frame is None:
            raise TimeoutError("no camera frame")
    finally:
        camera.close()
    shape = list(frame.shape)
    ready_at = clock()
    reply = (describe or vision.describe)(frame, question="Briefly describe visible tabletop objects without describing people.")
    if not reply.strip() or vision.used() != "local":
        raise RuntimeError("local response not verified")
    result = {"ran": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "scope": "One real camera IPC frame to local fallback with an unreachable loopback primary; "
                       "no motor controller, voice/pointing test, saved image or saved description",
              "frame_shape": shape, "backend": vision.used(), "model_size": vision.local_size(),
              "reply_nonempty": True, "acquisition_seconds": round(ready_at - started, 3),
              "vision_seconds": round(clock() - ready_at, 3),
              "vision_source_sha256": hashlib.sha256(Path(vision.__file__).read_bytes()).hexdigest()}
    del frame, reply
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, help="optional numeric/status metadata only; no image or model text")
    args = parser.parse_args(argv)
    try:
        with isolated_settings():
            result = probe()
        if args.out:
            args.out.write_text(json.dumps(result, indent=2) + "\n")
    except Exception as error:
        print(json.dumps({"passed": False, "error_type": type(error).__name__}))
        return 1
    print(json.dumps(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
