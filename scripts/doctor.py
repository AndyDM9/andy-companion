"""Check every part Andy needs, and say plainly what to fix.

    python scripts/doctor.py           the setup
    python scripts/doctor.py --live    and, before filming or a demo, that everything answers now

Reads the keys from the private env file without printing them. Makes one tiny request to Token
Factory and to Tavily to prove the keys work (a fraction of a cent). --live also asks both Nebius
endpoints' models to answer, times one short reply from Nemotron, and reads Andy's own health file
(andy_companion.watchdog: audio drops, unanswered speech; counts only), because on 2026-10-13 Andy
stopped answering in ways a minute's check would have shown.
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import stat
import subprocess
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
ENV_FILE = Path(os.environ.get("ANDY_ENV_FILE", Path.home() / ".config" / "companion-hackathon" / ".env"))
results = []


def check(name: str, ok: bool, detail: str = "", fix: str = "") -> None:
    results.append((name, ok, detail, fix))
    mark = "✓" if ok else "✗"
    print(f"{mark} {name}" + (f": {detail}" if detail else ""))
    if not ok and fix:
        print(f"    → {fix}")


def env() -> dict:
    out = {}
    try:
        for line in ENV_FILE.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                k, v = line.split("=", 1)
                out[k.strip()] = v.strip()
    except OSError:
        pass
    return out


def http(url: str, body=None, headers=None, timeout=10):
    req = urllib.request.Request(url, data=json.dumps(body).encode() if body is not None else None,
                                 method="POST" if body is not None else "GET", headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read()


def port_open(port: int) -> bool:
    with socket.socket() as s:
        s.settimeout(1)
        return s.connect_ex(("127.0.0.1", port)) == 0


def main() -> int:
    if {"-h", "--help"} & set(sys.argv[1:]):     # the description, and nothing else run
        print(__doc__)
        return 0
    e = env()
    mode = stat.S_IMODE(ENV_FILE.stat().st_mode) if ENV_FILE.exists() else None
    check("Private env file", mode == 0o600, str(ENV_FILE) if mode else "missing",
          f"copy .env.example to {ENV_FILE} and run chmod 600 on it")

    key = e.get("NEBIUS_API_KEY", "")
    if key:
        try:
            base = e.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/").rstrip("/")
            code, body = http(base + "/models", headers={"Authorization": f"Bearer {key}"})
            ids = [m["id"] for m in json.loads(body).get("data", [])]
            check("Nebius Token Factory key", "nvidia/Nemotron-3_5-Lightning" in ids, "Nemotron 3.5 Lightning reachable")
        except Exception as err:
            check("Nebius Token Factory key", False, type(err).__name__, "check NEBIUS_API_KEY")
    else:
        check("Nebius Token Factory key", False, "missing", "add NEBIUS_API_KEY to the env file")
    print("  (remember: zero data retention must be on in Token Factory → Organization → Settings)")

    tkey = e.get("TAVILY_API_KEY", "")
    if tkey:
        try:
            http("https://api.tavily.com/search", {"query": "test", "max_results": 1},
                 {"Authorization": f"Bearer {tkey}", "Content-Type": "application/json"})
            check("Tavily key", True, "search works")
        except Exception as err:
            check("Tavily key", False, type(err).__name__, "check TAVILY_API_KEY")
    else:
        check("Tavily key", False, "missing", "add TAVILY_API_KEY to the env file")

    check("Voice server", port_open(8765), "listening on 127.0.0.1:8765" if port_open(8765) else "not running",
          "cd voice && uv sync && ./run.sh")
    try:
        code, body = http("http://127.0.0.1:8000/api/daemon/status", timeout=3)
        state = json.loads(body).get("state")
        check("Reachy Mini daemon", state == "running", f"state {state}")
    except Exception:
        check("Reachy Mini daemon", False, "not reachable on 127.0.0.1:8000", "start Pollen's Reachy Mini daemon")
    check("Robot environment", (ROOT / "robot/.venv/bin/python").exists(), "", "cd robot && uv sync")
    check("Tesseract (reading letters)", bool(shutil.which("tesseract")), "", "sudo apt install tesseract-ocr")
    check("Screen and family page", port_open(int(os.environ.get("ANDY_SCREEN_PORT", "8090"))), "",
          "they start with ./scripts/andy")

    from andy_companion import state
    s = state.current()
    print(f"• Andy's last state: {s['mode']}" + (" (until a set time)" if s.get("until") else "")
          + " (information, not a check; --live checks the app is running)")

    eyes = (e.get("ANDY_VISION") or "token-factory").strip().lower().replace("_", "-")
    if eyes not in ("endpoint", "off"):
        check("Eyes (Nemotron 3.5 Super VL, Token Factory)", bool(e.get("NEBIUS_API_KEY")),
              "always on, nothing to start" if e.get("NEBIUS_API_KEY") else "no Token Factory key",
              "add NEBIUS_API_KEY to the env file")
    elif eyes == "off":
        check("Eyes", True, "switched off (ANDY_VISION=off)")
    elif e.get("ANDY_VISION_URL"):
        if shutil.which("nebius"):
            out = subprocess.run([str(ROOT / "cloud/vision-endpoint.sh"), "status"], capture_output=True, text=True).stdout
            running = "RUNNING" in out
            check("Eyes (Nebius endpoint)", True, "running, costs while on" if running else "stopped (no compute cost)")
        else:
            check("Eyes (Nebius endpoint)", True, "configured; Nebius CLI not installed here to check")
    else:
        check("Eyes (Nebius endpoint)", True, "not set up (optional): cloud/vision-endpoint.sh create")

    if "--live" in sys.argv:
        live(e)

    bad = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(bad)} of {len(results)} checks passed." + ("" if not bad else " Fix the ✗ lines above."))
    if "--live" in sys.argv:
        print("Ready to film." if not bad else "Not ready to film yet.")
    return 1 if bad else 0


def live(e: dict) -> None:
    """Everything answering now: the checks to run a few minutes before filming or a demo."""
    import time

    print("\nLive:")
    eyes = (e.get("ANDY_VISION") or "token-factory").strip().lower().replace("_", "-")
    endpoints = [("Second look answers", "ANDY_GUARD_URL", "ANDY_GUARD_TOKEN", "cloud/guard-endpoint.sh start")]
    if eyes == "endpoint":
        endpoints.insert(0, ("Eyes answer", "ANDY_VISION_URL", "ANDY_VISION_TOKEN",
                             "cloud/vision-endpoint.sh start; the model loads about 8 minutes after RUNNING"))
    for name, url_key, token_key, fix in endpoints:
        url, token = e.get(url_key, ""), e.get(token_key, "")
        if not url:
            check(name, True, "not set up (optional)")
            continue
        try:
            code, _ = http(url.rstrip("/") + "/v1/models", headers={"Authorization": f"Bearer {token}"}, timeout=8)
            check(name, code == 200, "the model answers")
        except Exception as err:
            check(name, False, getattr(err, "code", type(err).__name__), fix)

    key = e.get("NEBIUS_API_KEY", "")
    if key:
        base = e.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/").rstrip("/")
        body = {"model": "nvidia/Nemotron-3_5-Lightning", "max_tokens": 8, "temperature": 0,
                "chat_template_kwargs": {"enable_thinking": False},
                "messages": [{"role": "user", "content": "Say: ready."}]}
        t = time.time()
        try:
            http(base + "/chat/completions", body, {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}, timeout=15)
            took = time.time() - t
            check("Nemotron replies quickly", took < 1.5, f"{took:.2f} s for a short reply",
                  "Token Factory is slow right now; try again in a few minutes")
        except Exception as err:
            check("Nemotron replies quickly", False, type(err).__name__, "check the key and the network")
        if eyes not in ("endpoint", "off"):   # the eyes on Token Factory: the model is listed for this key
            model = e.get("ANDY_VISION_MODEL", "nvidia/Nemotron-3.5-Super-VL")
            try:
                code, listing = http(base + "/models", headers={"Authorization": f"Bearer {key}"}, timeout=10)
                ids = {m.get("id") for m in json.loads(listing).get("data", [])}
                check("Eyes on Token Factory", model in ids, model, "set ANDY_VISION=endpoint and start the endpoint")
            except Exception as err:
                check("Eyes on Token Factory", False, type(err).__name__, "check the key and the network")

    from andy_companion import settings, watchdog
    running = subprocess.run(["pgrep", "-f", "scripts/run_andy.py"], capture_output=True).returncode == 0
    check("Andy's app running", running, "", "./scripts/andy, and say \"Andy, wake up\" if it is asleep")
    try:
        h = json.loads(watchdog.HEALTH.read_text())
        age = time.time() - h.get("at", 0)
        fresh = age < 30
        check("Microphone audio", fresh and h.get("drops_last_min", 0) == 0,
              f"{h.get('drops_last_min', 0)} drops in the last minute" + ("" if fresh else f" (health {age:.0f} s old)"),
              "close heavy programs on this computer, then restart Andy")
        check("Nothing talking over Andy", not h.get("unanswered_s"),
              "" if not h.get("unanswered_s") else f"speech without an answer for {h['unanswered_s']} s",
              "turn off a TV, radio or video near the robot")
    except (OSError, ValueError):
        check("Microphone audio", False, "no health file yet", "start Andy (./scripts/andy) and wait a few seconds")

    load = os.getloadavg()[0]
    cores = os.cpu_count() or 1
    check("Computer not overloaded", load < cores * 0.6, f"load {load:.1f} on {cores} cores",
          "close or pause heavy programs before filming (on 2026-10-13 a busy computer made the microphone drop audio)")
    check("Screen's place set (the glance)", settings.get().get("tv_yaw") is not None, "",
          "settings page → Where the screen is → Save and show me")
    recording = finder_recording(e)
    check("Finder tries not kept", not recording, f"each search's pictures go to {recording}" if recording else "",
          "the room and anyone filmed would be kept: remove the ANDY_FINDER_RECORD line from the env file, "
          "then systemctl --user restart andy")


def finder_recording(e: dict) -> str:
    """The folder finder tries are kept in, or "" (andy_companion.finder.record, PLAN B11)."""
    return (os.environ.get("ANDY_FINDER_RECORD") or e.get("ANDY_FINDER_RECORD", "")).strip()


if __name__ == "__main__":
    sys.exit(main())
