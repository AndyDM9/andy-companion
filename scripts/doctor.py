"""Check every part Andy needs, and say plainly what to fix.

    python scripts/doctor.py

Reads the keys from the private env file without printing them. Makes one tiny request to Token
Factory and to Tavily to prove the keys work (a fraction of a cent).
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
    check("Andy", True, s["mode"] + (" (until a set time)" if s.get("until") else ""))

    if e.get("ANDY_VISION_URL"):
        if shutil.which("nebius"):
            out = subprocess.run([str(ROOT / "cloud/vision-endpoint.sh"), "status"], capture_output=True, text=True).stdout
            running = "RUNNING" in out
            check("Eyes (Nebius endpoint)", True, "running, costs while on" if running else "stopped (no compute cost)")
        else:
            check("Eyes (Nebius endpoint)", True, "configured; Nebius CLI not installed here to check")
    else:
        check("Eyes (Nebius endpoint)", True, "not set up (optional): cloud/vision-endpoint.sh create")

    bad = [r for r in results if not r[1]]
    print(f"\n{len(results) - len(bad)} of {len(results)} checks passed." + ("" if not bad else " Fix the ✗ lines above."))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
