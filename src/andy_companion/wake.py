"""Wake Andy by voice while it sleeps, entirely on this computer.

The supervisor runs this only while Andy is asleep or quiet, so it never competes with the
conversation for the microphones. It listens with Vosk (offline, Apache-2.0), limited to a few
wake phrases, in English and, when its model is here (it is fetched for a Spanish speaker), in Spanish:
"Andy, despierta". Nothing is sent anywhere, stored or logged except "wake phrase heard".
"""

from __future__ import annotations

import hashlib
import io
import os
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
WAKE_UP = ("andy wake up", "wake up andy", "hey andy wake up", "andy time to wake up")
# Greetings wake Andy from sleep, where they are natural, but never end a quiet spell the person
# asked for: "Good morning, Andy" said to someone else called Andy (on 2026-10-13, very likely the
# founder, in a meeting near the robot) woke it 47 minutes early. Only "Andy, wake up" ends quiet.
GREETINGS = ("andy i'm back", "i'm back andy", "good morning andy", "andy good morning")
TRIGGERS = (*WAKE_UP, *GREETINGS)
GRAMMAR = [*TRIGGERS, "andy", "wake up", "good morning", "[unk]"]
# Spanish, with the same rule: only "despierta" ends a quiet spell; a greeting wakes Andy from sleep.
MODEL_ES = "vosk-model-small-es-0.42"
MODEL_ES_URL = f"https://alphacephei.com/vosk/models/{MODEL_ES}.zip"
MODEL_ES_SHA256 = "09b239888f633ef2f0b4e09736e3d9936acfd810bc65d53fad45261762c6511f"   # fetched 2026-10-14
WAKE_UP_ES = ("andy despierta", "despierta andy", "andy despiértate", "despiértate andy")
GREETINGS_ES = ("buenos días andy", "andy buenos días", "andy ya estoy aquí", "ya estoy aquí andy")
TRIGGERS_ES = (*WAKE_UP_ES, *GREETINGS_ES)
GRAMMAR_ES = [*TRIGGERS_ES, "andy", "despierta", "buenos días", "[unk]"]

RATE = 16000
CHUNK = RATE // 10 * 2  # 0.1 s of 16-bit mono


def is_trigger(text: str, triggers=TRIGGERS) -> bool:
    return " ".join(text.lower().split()) in triggers


def triggers_for(mode: str, language: str = "en"):
    """Asleep: any wake phrase. Quiet (the person asked for it): only an explicit wake-up."""
    if language == "es":
        return WAKE_UP_ES if mode == "quiet" else TRIGGERS_ES
    return WAKE_UP if mode == "quiet" else TRIGGERS


def mic_source(sim: Optional[bool] = None) -> Optional[str]:
    """The robot's microphones; without a robot (ANDY_SIM, scripts/andy-sim), this computer's default one."""
    try:                            # a hung sound server must not stop Andy waking for a reminder
        out = subprocess.run(["pactl", "list", "short", "sources"], capture_output=True, text=True, timeout=5).stdout
    except (OSError, subprocess.SubprocessError):
        out = ""
    for line in out.splitlines():
        parts = line.split("\t")
        if len(parts) > 1 and "Reachy_Mini_Audio" in parts[1] and not parts[1].endswith(".monitor"):
            return parts[1]
    if sim if sim is not None else os.environ.get("ANDY_SIM") == "1":
        return "@DEFAULT_SOURCE@"          # PulseAudio's (and PipeWire's) name for the default microphone
    return None


def ensure_model(language: str = "en") -> Path:
    """The model for a language, downloaded once and checked against its pinned checksum."""
    name, url, digest = (MODEL_ES, MODEL_ES_URL, MODEL_ES_SHA256) if language == "es" else \
        (MODEL_NAME, MODEL_URL, MODEL_SHA256)
    folder = MODEL_DIR.parent / name
    if folder.is_dir():
        return folder
    data = urllib.request.urlopen(url, timeout=120).read()
    if hashlib.sha256(data).hexdigest() != digest:
        raise RuntimeError("Vosk model checksum mismatch; not using it.")
    folder.parent.mkdir(parents=True, exist_ok=True)
    zipfile.ZipFile(io.BytesIO(data)).extractall(folder.parent)
    return folder


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


def heard(chunks: Iterator[bytes], recognizer, should_stop: Callable[[], bool], check_every: int = 10,
          triggers=TRIGGERS, also=()) -> Optional[str]:
    """Feed audio until a wake phrase is recognised ("phrase") or should_stop() says another reason
    to wake (or to stop listening) has come up (None). `also`: more (recognizer, triggers) pairs fed the
    same audio, such as the Spanish one."""
    listeners = [(recognizer, triggers), *also]
    for i, data in enumerate(chunks):
        if i % check_every == 0 and should_stop():
            return None
        for rec, words in listeners:
            if rec.AcceptWaveform(data) and is_trigger(json.loads(rec.Result()).get("text", ""), words):
                logger.info("Wake phrase heard")
                return "phrase"
    return None
