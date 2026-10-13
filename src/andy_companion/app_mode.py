"""Everything Andy adds to Pollen's conversation app, in one place.

Used by `scripts/run_andy.py` (the desktop launcher, under the supervisor) and by the Reachy Mini
dashboard app (`reachy_app/`), so both run exactly the same Andy.
"""

from __future__ import annotations

import os
from pathlib import Path

PACKAGE = Path(__file__).resolve().parent


def data_dir(name: str) -> Path:
    """tools/ or profiles/: shipped inside the installed package, or the repository's own in development."""
    shipped = PACKAGE / "_data" / name
    return shipped if shipped.is_dir() else PACKAGE.parents[1] / name


def configure_env() -> None:
    os.environ.setdefault("REACHY_MINI_CUSTOM_PROFILE", "companion")
    os.environ.setdefault("REACHY_MINI_EXTERNAL_PROFILES_DIRECTORY", str(data_dir("profiles")))
    os.environ.setdefault("REACHY_MINI_EXTERNAL_TOOLS_DIRECTORY", str(data_dir("tools")))
    os.environ.setdefault("HF_REALTIME_CONNECTION_MODE", "local")
    os.environ.setdefault("HF_REALTIME_WS_URL", os.environ.get("ANDY_VOICE_URL", "ws://127.0.0.1:8765/v1/realtime"))


def install(screen: bool = False) -> None:
    """Attach Andy's additions. With screen=True also serve the screen and family page here
    (the dashboard app has no supervisor to do it)."""
    from andy_companion import captions, guard, privacy, settings, speaker, turns, urgent, voice_controls, volume
    from andy_companion.body import attach as body

    configure_env()
    privacy.install()
    body.install()
    speaker.attach()
    settings.install()
    voice_controls.install()
    urgent.install()
    guard.install()
    captions.install()
    turns.install()
    volume.apply_saved()
    if screen:
        from andy_companion import screen_server
        try:
            screen_server.serve()
        except OSError:
            pass
