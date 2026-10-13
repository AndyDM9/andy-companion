"""Wake Andy by voice while it sleeps, entirely on this computer.

The supervisor runs this only while Andy is asleep or quiet, so it never competes with the
conversation for the microphones. It listens with Vosk (offline, Apache-2.0), limited to a few
wake phrases. Nothing is sent anywhere, stored or logged except "wake phrase heard".
"""

from __future__ import annotations

import hashlib
import io
import json
import logging
import subprocess
import urllib.request
import zipfile
from pathlib import Path
from typing import Callable, Iterator, Optional

from andy_companion.reminders import DATA_DIR

logger = logging.getLogger("andy.wake")

MODEL_NAME = "vosk-model-small-en-us-0.15"
MODEL_URL = f"https://alphacephei.com/vosk/models/{MODEL_NAME}.zip"
MODEL_SHA256 = "30f26242c4eb449f948e42cb302dd7a686cb29a3423a8367f99ff41780942498"
MODEL_DIR = DATA_DIR / "models" / MODEL_NAME

# The recogniser may only choose between these (or "[unk]"), so ordinary speech can't be
# mistaken for a free-form match.
TRIGGERS = ("andy wake up", "wake up andy", "hey andy wake up", "andy time to wake up",
            "andy i'm back", "i'm back andy", "good morning andy", "andy good morning")
GRAMMAR = [*TRIGGERS, "andy", "wake up", "good morning", "[unk]"]

RATE = 16000
CHUNK = RATE // 10 * 2  # 0.1 s of 16-bit mono


def is_trigger(text: str) -> bool:
    return " ".join(text.lower().split()) in TRIGGERS


def mic_source() -> Optional[str]:
    out = subprocess.run(["pactl", "list", "short", "sources"], capture_output=True, text=True).stdout
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) > 1 and "Reachy_Mini_Audio" in parts[1] and not parts[1].endswith(".monitor"):
            return parts[1]
    return None


def ensure_model() -> Path:
    """The model, downloaded once and checked against its pinned checksum."""
    if MODEL_DIR.is_dir():
        return MODEL_DIR
    data = urllib.request.urlopen(MODEL_URL, timeout=120).read()
    if hashlib.sha256(data).hexdigest() != MODEL_SHA256:
        raise RuntimeError("Vosk model checksum mismatch; not using it.")
    MODEL_DIR.parent.mkdir(parents=True, exist_ok=True)
    zipfile.ZipFile(io.BytesIO(data)).extractall(MODEL_DIR.parent)
    return MODEL_DIR


def mic_chunks(source: str) -> Iterator[bytes]:
    """Raw 16 kHz mono audio from the robot's microphones, 0.1 s at a time."""
    proc = subprocess.Popen(
        ["parec", f"--device={source}", "--format=s16le", f"--rate={RATE}", "--channels=1", "--raw",
         "--latency-msec=100"],
        stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
    )
    try:
        while True:
            data = proc.stdout.read(CHUNK)
            if not data:
                return
            yield data
    finally:
        proc.terminate()
        proc.wait(timeout=5)


def heard(chunks: Iterator[bytes], recognizer, should_stop: Callable[[], bool], check_every: int = 10) -> Optional[str]:
    """Feed audio until a wake phrase is recognised ("phrase") or should_stop() says another reason
    to wake (or to stop listening) has come up (None)."""
    for i, data in enumerate(chunks):
        if i % check_every == 0 and should_stop():
            return None
        if recognizer.AcceptWaveform(data) and is_trigger(json.loads(recognizer.Result()).get("text", "")):
            logger.info("Wake phrase heard")
            return "phrase"
    return None
