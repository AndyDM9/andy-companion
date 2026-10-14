"""Short, soft sounds: a gentle cue before a reminder, and on waking and going to sleep.

Made here as small WAV files and played by the robot's daemon (`/api/media/play_sound`). Never
while Andy is asleep or quiet.
"""

from __future__ import annotations

import io
import json
import urllib.request
import wave
from pathlib import Path
from typing import Dict, List, Tuple

import numpy as np

from andy_companion import state
from andy_companion.reminders import DATA_DIR

DIR = DATA_DIR / "sounds"
RATE = 16000
DAEMON = "http://127.0.0.1:8000"
TUNES: Dict[str, List[Tuple[float, float]]] = {      # (frequency Hz, seconds); 0 Hz is a pause
    "reminder": [(659.25, 0.12), (783.99, 0.12), (1046.5, 0.2)],
    "wake": [(523.25, 0.12), (783.99, 0.18)],
    "sleep": [(783.99, 0.14), (523.25, 0.22)],
}


def _tone(freq: float, seconds: float, volume: float = 0.22) -> np.ndarray:
    n = int(RATE * seconds)
    if freq <= 0:
        return np.zeros(n)
    t = np.arange(n) / RATE
    envelope = np.minimum(1.0, np.minimum(t, seconds - t) / 0.015)      # 15 ms fades: no clicks
    return volume * envelope * np.sin(2 * np.pi * freq * t)


def wav_bytes(name: str) -> bytes:
    samples = np.concatenate([_tone(f, s) for f, s in TUNES[name]])
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((samples * 32767).astype("<i2").tobytes())
    return buf.getvalue()


def path(name: str) -> Path:
    p = DIR / f"{name}.wav"
    data = wav_bytes(name)
    if not p.is_file() or p.read_bytes() != data:
        DIR.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
    return p


def play(name: str, opener=None, force: bool = False) -> bool:
    """Play one chime on the robot's speaker. False if unknown, Andy is not awake (unless `force`,
    for the wake and sleep chimes themselves), or the daemon is away."""
    if name not in TUNES or (not force and state.current()["mode"] != "awake"):
        return False
    return play_file(path(name), opener)


def play_file(file: Path, opener=None) -> bool:
    """Play a WAV on this computer on the robot's speaker, through the daemon (it reads the file by its
    path). Whatever Andy's mode: the urgent-words recordings (urgent.py) use it too. False if the
    daemon is away."""
    req = urllib.request.Request(DAEMON + "/api/media/play_sound", method="POST",
                                 data=json.dumps({"file": str(Path(file).resolve())}).encode(),
                                 headers={"Content-Type": "application/json"})
    try:
        with (opener or urllib.request.urlopen)(req, timeout=5):
            return True
    except Exception:
        return False
