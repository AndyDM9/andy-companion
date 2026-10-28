"""Check every part Andy needs, and say plainly what to fix.

    uv run python scripts/doctor.py           the setup
    uv run python scripts/doctor.py --live    and, before filming or a demo, that everything answers now

Reads the keys from the private env file without printing them. Makes one tiny request to Token
Factory and to Tavily to prove the keys work (a fraction of a cent). --live also checks configured Nebius
endpoint catalogues, validates/times short text replies from Nemotron and the configured Token Factory
vision model, and reads Andy's own health file
(andy_companion.watchdog: audio drops, unanswered speech; counts only), because on 2026-10-13 Andy
stopped answering in ways a minute's check would have shown.
"""

from __future__ import annotations

import json
import math
import os
import re
import shutil
import socket
import stat
import subprocess
import sys
import urllib.request
from urllib.parse import urlsplit
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
    from andy_companion import app_mode

    names = (*app_mode.APP_KEYS, "ANDY_LOCAL_EYES_PORT")
    out = app_mode.read_env(names, ENV_FILE)
    out.update({name: os.environ[name] for name in names if name in os.environ})
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


def model_probe(url: str, token: str, model: str) -> tuple[bool, str]:
    """Require usable final text, not HTTP success or a catalogue entry. No household input.

    This is a tiny text-only inference: it proves the model answers, not vision quality or robot motion.
    Never return provider text, URLs or exception messages: they can contain credentials or payloads.
    """
    from andy_companion.model_reply import ModelReplyError, final_text

    body = {"model": model, "max_tokens": 8, "temperature": 0,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "user", "content": "Say: ready."}]}
    try:
        code, raw = http(url, body,
                         {"Authorization": f"Bearer {token}",
                          "Content-Type": "application/json"}, timeout=15)
        if code != 200:
            return False, f"HTTP {code}"
        final_text(json.loads(raw))
        return True, "model returned final text (text-only probe)"
    except ModelReplyError:
        return False, "unusable final reply"
    except Exception as err:
        code = getattr(err, "code", None)
        return False, f"HTTP {code}" if isinstance(code, int) else type(err).__name__


def vision_model_probe(e: dict) -> tuple[bool, str]:
    base = e.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/").rstrip("/")
    return model_probe(base + "/chat/completions", e.get("NEBIUS_API_KEY", ""),
                       e.get("ANDY_VISION_MODEL", "nvidia/Nemotron-3.5-Super-VL"))


def audio_health(path: Path) -> dict | None:
    """Read counts only. Unsupported/missing fields are unknown, never zero by default."""
    try:
        h = json.loads(path.read_text())
        if not isinstance(h, dict):
            return None
        at, drops, unanswered = h['at'], h['drops_last_min'], h['unanswered_s']
        if type(at) not in (int, float) or not math.isfinite(at) or at < 0:
            return None
        if type(drops) is not int or drops < 0:
            return None
        if unanswered is not None and (type(unanswered) not in (int, float)
                                      or not math.isfinite(unanswered) or unanswered < 0):
            return None
        return {'at': at, 'drops_last_min': drops, 'unanswered_s': unanswered}
    except (OSError, ValueError, KeyError, OverflowError, RecursionError):
        return None


def voice_reachable(e: dict) -> bool:
    """Probe the app's configured voice address without printing its URL or credentials.

    This checks TCP availability, not a spoken turn or WebSocket authentication.
    The upstream override takes precedence just as in app_mode.configure_env().
    """
    url = os.environ.get("HF_REALTIME_WS_URL", e.get("ANDY_VOICE_URL", "ws://127.0.0.1:8765/v1/realtime"))
    try:
        address = urlsplit(url)
        if address.scheme not in ("ws", "wss") or not address.hostname:
            return False
        port = address.port or (443 if address.scheme == "wss" else 80)
        with socket.create_connection((address.hostname, port), timeout=3):
            return True
    except (OSError, ValueError):
        return False


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
            listed = "nvidia/Nemotron-3_5-Lightning" in ids
            check("Nebius Token Factory key", listed,
                  "Nemotron 3.5 Lightning listed" if listed else "required model not listed")
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

    voice_up = voice_reachable(e)
    others = others_on_port(voice_port(e), ANDYS_VOICE) if voice_up else []
    if others:
        check("Voice server", False, f"Andy's voice port is held by {', '.join(others)}",
              "stop that program first (only one program can listen there), then start andy-voice")
    else:
        check("Voice server", voice_up, "configured TCP address reachable; spoken turn not tested" if voice_up else
              "configured address invalid or unreachable",
              "check ANDY_VOICE_URL / HF_REALTIME_WS_URL and start the voice server")
    try:
        code, body = http("http://127.0.0.1:8000/api/daemon/status", timeout=3)
        state = json.loads(body).get("state")
        check("Reachy Mini daemon", state == "running", f"state {state}")
    except Exception:
        check("Reachy Mini daemon", False, "not reachable on 127.0.0.1:8000", "start Pollen's Reachy Mini daemon")
    check("Robot environment", (ROOT / "robot/.venv/bin/python").exists(), "", "cd robot && uv sync")
    check("Tesseract (reading letters)", bool(shutil.which("tesseract")), "", "sudo apt install tesseract-ocr")
    screen_port = int(e.get("ANDY_SCREEN_PORT") or "8090")
    others = others_on_port(screen_port, ANDYS_SCREEN) if port_open(screen_port) else []
    if others:
        check("Screen and family page", False, f"Andy's screen port is held by {', '.join(others)}",
              "stop that program first (only one program can listen there), then start andy")
    else:
        check("Screen and family page", port_open(screen_port), "", "they start with ./scripts/andy")

    from andy_companion import state
    s = state.current()
    print(f"• Andy's last state: {s['mode']}" + (" (until a set time)" if s.get("until") else "")
          + " (information, not a check; --live checks the app is running)")

    eyes = (e.get("ANDY_VISION") or "token-factory").strip().lower().replace("_", "-")
    # Cosmos Reason 2 on this computer (decision 0015): needed when chosen, a fallback otherwise.
    here = port_open(int(e.get("ANDY_LOCAL_EYES_PORT", "8095")))
    cosmos = "Cosmos Reason 2 8B" if "8b" in e.get("ANDY_LOCAL_EYES_MODEL", "").lower() else "Cosmos Reason 2 2B"
    if eyes == "local":
        check(f"Eyes ({cosmos}, this computer)", here, "answering" if here else "not running",
              "local-eyes/run.sh (cd local-eyes && uv sync, once)")
    elif (e.get("ANDY_VISION_FALLBACK") or "").strip().lower() == "local":
        check(f"Offline eyes ({cosmos}, the fallback)", True,
              "running" if here else "not running, so no fallback: local-eyes/run.sh")
    if eyes not in ("endpoint", "off", "local"):
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
        print("Preflight passed; verify spoken tasks and motion before filming." if not bad else "Preflight has failures.")
    return 1 if bad else 0


def live(e: dict) -> None:
    """Everything answering now: the checks to run a few minutes before filming or a demo."""
    import time

    print("\nLive:")
    eyes = (e.get("ANDY_VISION") or "token-factory").strip().lower().replace("_", "-")
    endpoints = [("Second look endpoint catalogue", "ANDY_GUARD_URL", "ANDY_GUARD_TOKEN", "cloud/guard-endpoint.sh start")]
    if eyes == "endpoint":
        endpoints.insert(0, ("Eyes endpoint catalogue", "ANDY_VISION_URL", "ANDY_VISION_TOKEN",
                             "cloud/vision-endpoint.sh start; the model loads about 8 minutes after RUNNING"))
    for name, url_key, token_key, fix in endpoints:
        url, token = e.get(url_key, ""), e.get(token_key, "")
        if not url:
            check(name, True, "not set up (optional)")
            continue
        try:
            code, _ = http(url.rstrip("/") + "/v1/models", headers={"Authorization": f"Bearer {token}"}, timeout=8)
            check(name, code == 200, "model catalogue reachable; inference not tested")
        except Exception as err:
            check(name, False, getattr(err, "code", type(err).__name__), fix)

    key = e.get("NEBIUS_API_KEY", "")
    if key:
        base = e.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/").rstrip("/")
        t = time.monotonic()
        ok, detail = model_probe(base + "/chat/completions", key, "nvidia/Nemotron-3_5-Lightning")
        took = time.monotonic() - t
        check("Nemotron replies quickly", ok and took < 1.5,
              f"{took:.2f} s for usable final text (text-only probe)" if ok else detail,
              "check the key, network and model reply; retry if Token Factory is slow")
        if eyes not in ("endpoint", "off", "local"):
            model = e.get("ANDY_VISION_MODEL", "nvidia/Nemotron-3.5-Super-VL")
            available, detail = vision_model_probe(e)
            check("Eyes on Token Factory", available, f"{model}; {detail}",
                  "check the configured model, key and network; catalogue membership is not an inference test")

    from andy_companion import settings, state, watchdog
    check("Saved sleep/quiet mode", not state.current().get("unreadable"), "",
          "the mode file needs review; an explicit wake or mode change replaces it with a valid state")
    running = subprocess.run(["pgrep", "-f", "scripts/run_andy.py"], capture_output=True).returncode == 0
    check("Andy's app running", running, "", "say \"Andy, wake up\" through the existing supervisor; check systemctl --user status andy")
    others = other_robot_apps()
    check("Only Andy drives the robot", others == [],
          "could not identify every robot connection" if others is None else ", ".join(others),
          "check ss access and process visibility" if others is None else
          "stop the other app (systemctl --user stop <its service>), and anything that starts it, such as its own "
          "wake word; two apps moving the head at once make it and the antennas shake")
    h = audio_health(watchdog.HEALTH)
    if h is not None:
        age = time.time() - h.get("at", 0)
        fresh = -1 <= age < 30  # watchdog rounds its wall-clock timestamp to the nearest second
        check("Microphone audio", fresh and h.get("drops_last_min", 0) == 0,
              f"{h.get('drops_last_min', 0)} drops in the last minute" + ("" if fresh else f" (health {age:.0f} s old)"),
              "check the existing service and system clock" if not fresh else
              "close heavy programs on this computer, then systemctl --user restart andy")
        check("Nothing talking over Andy", fresh and not h.get("unanswered_s"),
              "health is not current; unanswered speech not verified" if not fresh else
              ("" if not h.get("unanswered_s") else f"speech without an answer for {h['unanswered_s']} s"),
              "check the existing service and system clock" if not fresh else
              "turn off a TV, radio or video near the robot")
    else:
        check("Microphone audio", False, "audio health counts unavailable or unreadable",
              "check the existing andy service and wait for fresh watchdog counts")
        check("Nothing talking over Andy", False, "unanswered speech not verified",
              "check the existing andy service and wait for fresh watchdog counts")

    load = os.getloadavg()[0]
    cores = os.cpu_count() or 1
    check("Computer not overloaded", load < cores * 0.6, f"load {load:.1f} on {cores} cores",
          "close or pause heavy programs before filming (on 2026-10-13 a busy computer made the microphone drop audio)")
    check("Screen's place set (the glance)", settings.get().get("tv_yaw") is not None, "",
          "settings page → Where the screen is → Save and show me")
    log = voice_log()
    worded = lines_with_words(log) if log is not None else None
    check("No words in the voice log", worded == 0,
          "Could not read the voice journal" if worded is None else f"{worded} lines in the last day that may hold what was heard",
          "check journalctl access and that the voice service has produced a readable journal" if worded is None else
          "inspect the speech package's output filter and restart andy-voice; do not print or copy transcript lines")
    recording = finder_recording(e)
    check("Finder tries not kept", not recording, f"each search's and look's pictures go to {recording}" if recording else "",
          "the room and anyone filmed would be kept: remove the ANDY_FINDER_RECORD line from the env file, "
          "then systemctl --user restart andy")


# What the voice server may write: its loggers' lines and a few fixed notices at start and stop. Any other line
# could be words it heard, as its "Live:" prints were from 2026-10-15 to 10-25 (a long one over several lines).
VOICE_LOG_OK = re.compile(
    r"^(?:\d{4}-\d\d-\d\d \d\d:\d\d:\d\d,\d+ - |INFO: |Language: [a-z]{2}$|\[nltk_data\]|Using cache found in |"
    r"Started |Stopping |Stopped |andy-voice\.service: |✓ Pipeline stopped|Shutting down gracefully|"
    r"DeepFilterNet not available|/\S+\.py:\d+: \w*Warning: |\s+result = |\s*$)")


def voice_log(since: str = "-24h") -> str | None:
    try:
        result = subprocess.run(["journalctl", "--user", "-u", "andy-voice", "--since", since, "--no-pager", "-o", "cat"],
                                capture_output=True, text=True, timeout=30)
        if result.returncode or result.stderr.strip():
            return None
        return result.stdout
    except (OSError, subprocess.SubprocessError):
        return None


def lines_with_words(log: str) -> int:
    """How many lines of the voice server's log are not one of the kinds it may write (never what they say)."""
    return sum(1 for line in log.splitlines() if not VOICE_LOG_OK.match(line) or
               re.search(r"(?:^|\s)(?:USER|ASSISTANT|Live):", line))


def voice_port(e: dict) -> int | None:
    """The local port of the configured voice address, or None when it is not on this computer."""
    url = os.environ.get("HF_REALTIME_WS_URL", e.get("ANDY_VOICE_URL", "ws://127.0.0.1:8765/v1/realtime"))
    try:
        address = urlsplit(url)
        if address.hostname not in ("127.0.0.1", "localhost", "::1"):
            return None
        return address.port or (443 if address.scheme == "wss" else 80)
    except ValueError:
        return None


# Whether a listening program is Andy's own, from its service and command line.
ANDYS_VOICE = lambda unit, cmd: unit == "andy-voice.service" or "serve.py serve" in cmd   # noqa: E731
ANDYS_SCREEN = lambda unit, cmd: (unit == "andy.service" or "scripts/run_andy.py" in cmd    # noqa: E731
                                  or "andy_companion.supervisor" in cmd or "scripts/demo_screen.py" in cmd)


def others_on_port(port: int | None, mine, listing: str | None = None, read=None) -> list:
    """The programs other than Andy's listening on 127.0.0.1:port (2026-10-28: another project's voice and mask
    servers held Andy's voice and screen ports, and an open port alone read as Andy's own). Empty when only Andy's,
    or when it cannot be told: the open-port check stands then, as before."""
    if port is None:
        return []
    if listing is None:
        try:
            result = subprocess.run(["ss", "-tlnpH", f"( sport = :{port} )"], capture_output=True, text=True, timeout=5)
            if result.returncode or (result.stderr or "").strip():
                return []
            listing = result.stdout or ""
        except (OSError, subprocess.SubprocessError):
            return []
    read = read or _process
    found = []
    for pid in sorted({int(x) for x in re.findall(r"pid=(\d+)", listing)}):
        unit, cmd = read(pid)
        if not mine(unit, cmd):
            name = unit or _command_name(cmd) or f"process {pid}"
            if name not in found:
                found.append(name)
    return found


def _process(pid: int) -> tuple:
    """(its service or "", its command line or "")."""
    proc = Path("/proc") / str(pid)
    try:
        cmd = proc.joinpath("cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        groups = proc.joinpath("cgroup").read_text()
    except OSError:
        return "", ""
    return next((part for part in reversed(groups.strip().split("/")) if part.endswith(".service")), ""), cmd


def _command_name(cmd: str) -> str:
    """A program's short name: a Python module or script rather than "python"."""
    words = cmd.split()
    if not words:
        return ""
    if "python" in words[0].rsplit("/", 1)[-1]:
        rest = [w for w in words[1:] if not w.startswith("-") or w == "-m"]
        if rest[:1] == ["-m"] and len(rest) > 1:
            return rest[1]
        if rest:
            return rest[0].rsplit("/", 1)[-1]
    return words[0].rsplit("/", 1)[-1]


def other_robot_apps(listing: str | None = None, who=None) -> list | None:
    """Programs other than Andy connected to the robot's daemon (127.0.0.1:8000), each by its service or name.
    Two apps commanding the head at once make the head and antennas shake: on 2026-10-25 another conversation app,
    started by its own wake word when Andy said its name, did that. None means ownership could not be checked."""
    if listing is None:
        try:
            result = subprocess.run(["ss", "-tnpH", "state", "established", "( dport = :8000 )"],
                                    capture_output=True, text=True, timeout=5)
            if result.returncode or result.stderr.strip():
                return None
            listing = result.stdout
        except (OSError, subprocess.SubprocessError):
            return None
    if any(line.strip() and not re.search(r"pid=\d+", line) for line in listing.splitlines()):
        return None
    who = who or _program
    found = []
    for pid in sorted({int(x) for x in re.findall(r"pid=(\d+)", listing)}):
        name, andy = who(pid)
        if not andy and name not in found:
            found.append(name)
    return found


def _program(pid: int) -> tuple:
    """(its service, else its command's name; whether it is Andy's own)."""
    proc = Path("/proc") / str(pid)
    try:
        cmd = proc.joinpath("cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace")
        groups = proc.joinpath("cgroup").read_text()
    except OSError:
        return f"process {pid}", False
    unit = next((part for part in reversed(groups.strip().split("/")) if part.endswith(".service")), "")
    andy = unit == "andy.service" or "scripts/run_andy.py" in cmd or "andy_companion.supervisor" in cmd
    return unit or (cmd.split()[0].rsplit("/", 1)[-1] if cmd.strip() else f"process {pid}"), andy


def finder_recording(e: dict) -> str:
    """The folder finder tries are kept in, or "" (andy_companion.finder.record, PLAN B11)."""
    return (os.environ.get("ANDY_FINDER_RECORD") or e.get("ANDY_FINDER_RECORD", "")).strip()


if __name__ == "__main__":
    sys.exit(main())
