"""The hood page's health tiles: one glance at everything Andy depends on.

Each tile is {"name", "status": "ok" | "off" | "warn" | "unknown", "detail"}: words as well as a colour.
Local checks (the robot's daemon, the voice server, Andy's app, quiet or asleep) refresh every 30
seconds; the Nebius endpoints every five minutes, because they cost money while running and someone
should see that at a glance. Everything runs in the background; a page never waits for a check.
Nothing here reads a key or a word: only states.
"""

from __future__ import annotations

import json
import shutil
import socket
import subprocess
import threading
import time
import urllib.request
from typing import Any, Callable, Dict, List, Optional

LOCAL_EVERY_S = 30
CLOUD_EVERY_S = 300
ENDPOINTS = (("eyes", "Eyes on Nebius", "andy-vision"), ("guard", "Second look on Nebius", "andy-guard"))

_cache: Dict[str, Any] = {"local": [], "cloud": [], "local_at": 0.0, "cloud_at": 0.0, "busy": False}


def tile(name: str, status: str, detail: str) -> Dict[str, str]:
    return {"name": name, "status": status, "detail": detail}


def daemon(opener: Optional[Callable] = None) -> Dict[str, str]:
    try:
        with (opener or urllib.request.urlopen)("http://127.0.0.1:8000/api/daemon/status", timeout=1.5) as r:
            data = json.loads(r.read())
    except Exception:
        return tile("Robot", "warn", "The robot's daemon does not answer")
    state = str(data.get("state", ""))
    if data.get("error"):
        return tile("Robot", "warn", f"Daemon {state}, with an error")
    return tile("Robot", "ok" if state == "running" else "warn", f"Daemon {state}, version {data.get('version', '?')}")


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def voice() -> Dict[str, str]:
    return (tile("Voice", "ok", "Parakeet and Qwen3-TTS ready, on this computer") if port_open(8765)
            else tile("Voice", "warn", "The voice server is not running"))


def mode_and_app(live_at: float, now: float) -> List[Dict[str, str]]:
    from andy_companion import state

    mode = state.current()
    if mode.get("unreadable"):
        return [tile("Andy", "warn", "Saved sleep/quiet mode unreadable; explicit wake or mode change needed")]
    if mode["mode"] == "quiet":
        return [tile("Andy", "off", "Quiet; the wake listener waits for “Andy, wake up”")]
    if mode["mode"] == "asleep":
        return [tile("Andy", "off", "Asleep; the wake listener waits for a wake phrase")]
    fresh = now - live_at <= 12
    return [tile("Andy", "ok" if fresh else "warn", "Awake and listening" if fresh else "Awake, but the app is silent")]


def endpoint_state(name: str, run: Callable = subprocess.run) -> Optional[str]:
    if not shutil.which("nebius"):
        return None
    try:
        out = run(["nebius", "ai", "endpoint", "get-by-name", "--name", name, "--format", "json"],
                  capture_output=True, text=True, timeout=20)
        return str(json.loads(out.stdout).get("status", {}).get("state", "")) or None
    except Exception:
        return None


def cloud(run: Callable = subprocess.run) -> List[Dict[str, str]]:
    tiles = []
    for _key, label, name in ENDPOINTS:
        state = endpoint_state(name, run)
        if state is None:
            tiles.append(tile(label, "unknown", "Not checked (no Nebius command line here)"))
        elif state == "RUNNING":
            tiles.append(tile(label, "ok", "Running (it costs while on)"))
        elif state in ("STOPPED", "STOPPING"):
            tiles.append(tile(label, "off", "Stopped (no cost)"))
        else:
            tiles.append(tile(label, "warn", state.replace("_", " ").capitalize()))
    return tiles


def _refresh(live_at: float, weather: Optional[Dict], tavily: Dict, cloud_due: bool) -> None:
    try:
        now = time.time()
        local = [daemon(), voice(), *mode_and_app(live_at, now)]
        local.append(tile("Weather", "ok", "National Weather Service, refreshed every 30 minutes") if weather
                     else tile("Weather", "unknown", "No town set, or not fetched yet"))
        if tavily and tavily.get("used") is not None:
            used, limit, paygo = tavily["used"], tavily.get("limit"), tavily.get("paygo")
            # Past the plan's credits, pay as you go carries on (2026-10-28 on the robot: "4964 of 1000" read as a fault).
            near = bool(limit) and used > 0.9 * limit and not paygo
            local.append(tile("Tavily", "warn" if near else "ok",
                              f"{used:,} credits this month, {limit:,} in the plan and {paygo:,} pay as you go" if paygo and limit
                              else f"{used:,} of {limit:,} credits this month" if limit else f"{used:,} credits this month"))
        else:
            local.append(tile("Tavily", "unknown", "Credits not reported yet"))
        _cache.update(local=local, local_at=now)
        if cloud_due:
            _cache.update(cloud=cloud(), cloud_at=now)
    finally:
        _cache["busy"] = False


def tiles(live_at: float, weather: Optional[Dict], tavily: Dict, now: Optional[float] = None) -> List[Dict[str, str]]:
    """The latest tiles; starts a refresh in the background when one is due."""
    now = time.time() if now is None else now
    local_due = now - _cache["local_at"] >= LOCAL_EVERY_S
    cloud_due = now - _cache["cloud_at"] >= CLOUD_EVERY_S
    if (local_due or cloud_due) and not _cache["busy"]:
        _cache["busy"] = True
        threading.Thread(target=_refresh, args=(live_at, weather, dict(tavily or {}), cloud_due),
                         name="andy-health", daemon=True).start()
    return list(_cache["local"]) + list(_cache["cloud"])
