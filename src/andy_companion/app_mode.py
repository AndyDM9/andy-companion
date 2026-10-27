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


# What the app needs from the private env file, for both desktop and dashboard launches.
APP_KEYS = ("TAVILY_API_KEY", "TAVILY_PROJECT", "NEBIUS_API_KEY", "NEBIUS_BASE_URL", "ANDY_VISION",
            "ANDY_VISION_URL", "ANDY_VISION_TOKEN", "ANDY_FINDER_RECORD", "ANDY_GUARD_URL", "ANDY_GUARD_TOKEN", "ANDY_VOICE_URL",
            "ANDY_VISION_FALLBACK", "ANDY_LOCAL_EYES_URL", "ANDY_LOCAL_EYES_MODEL", "ANDY_WAVE_DEBUG",
            "ANDY_SCREEN_PORT", "ANDY_VISION_MODEL", "ANDY_FINDER_TURN")
# What the supervisor's own process needs: it hosts the screen server, whose setup page finds the town's
# events calendar with Tavily (setup_page.suggest_events_page), and which eyes are chosen and which Cosmos runs
# here (no key), for the hood page's "where it ran". The weather and the health tiles need no key.
SUPERVISOR_KEYS = ("TAVILY_API_KEY", "TAVILY_PROJECT", "ANDY_VISION", "ANDY_LOCAL_EYES_MODEL", "ANDY_SCREEN_PORT")


def env_file() -> Path:
    return Path(os.environ.get("ANDY_ENV_FILE") or Path.home() / ".config" / "companion-hackathon" / ".env")


def read_env(names, path=None) -> dict:
    """Read only allowlisted settings, without executing shell text or changing the environment."""
    path = Path(path) if path is not None else env_file()
    try:
        lines = path.read_text().splitlines()
    except (OSError, UnicodeDecodeError):
        return {}
    found = {}
    for line in lines:
        line = line.strip()
        if line.startswith("export "):
            line = line[len("export "):].lstrip()
        name, eq, value = line.partition("=")
        if not eq or name not in names:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
            value = value[1:-1]
        found[name] = value                  # the last line wins
    return found


def load_env(names, path=None) -> list:
    """Load named settings without replacing an existing environment variable. Return names only;
    values are never logged. A missing or unreadable file loads nothing."""
    found = read_env(names, path)
    loaded = [n for n, v in found.items() if v and n not in os.environ]
    for n in loaded:
        os.environ[n] = found[n]
    return loaded


def configure_env() -> None:
    os.environ.setdefault("REACHY_MINI_CUSTOM_PROFILE", "companion")
    os.environ.setdefault("REACHY_MINI_EXTERNAL_PROFILES_DIRECTORY", str(data_dir("profiles")))
    os.environ.setdefault("REACHY_MINI_EXTERNAL_TOOLS_DIRECTORY", str(data_dir("tools")))
    os.environ.setdefault("HF_REALTIME_CONNECTION_MODE", "local")
    os.environ.setdefault("HF_REALTIME_WS_URL", os.environ.get("ANDY_VOICE_URL", "ws://127.0.0.1:8765/v1/realtime"))


def install(screen: bool = False) -> None:
    """Attach Andy's additions. With screen=True also serve the screen and family page here
    (the dashboard app has no supervisor to do it). screen=True is how the dashboard app is told apart:
    there is no supervisor there, so the watchdog only logs instead of asking for a restart."""
    from andy_companion import captions, consent, guard, privacy, settings, speaker, turns, urgent, voice_controls, volume
    from andy_companion.body import attach as body

    load_env(APP_KEYS)        # before configure_env, which reads ANDY_VOICE_URL
    configure_env()
    privacy.install()
    body.install()
    speaker.attach()
    settings.install()
    voice_controls.install()
    urgent.install()
    guard.install()
    consent.install()
    captions.install()
    turns.install()
    volume.apply_saved()
    from andy_companion import state

    state.install_sleep_tool()
    if screen:
        state.awake()  # the dashboard has started this app; stale supervisor mode must not describe it as asleep
    from andy_companion import watchdog

    watchdog.install(supervised=not screen)
    import threading

    from andy_companion import live

    threading.Thread(target=live.report_loop, name="andy-live", daemon=True).start()
    if os.environ.get("TAVILY_API_KEY"):
        threading.Thread(target=turns.tavily_usage_loop, name="andy-tavily-usage", daemon=True).start()
    if screen:
        from andy_companion import screen_server
        try:
            screen_server.serve()
        except OSError:
            pass
