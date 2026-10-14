"""Read a letter, bill, card or label held up to Andy's camera, on this computer.

The sharpest of three camera frames is read with Tesseract (offline). Only the recognised text
reaches the model, which explains it in plain words; the picture never leaves the computer and
nothing is saved. Poor light or blur becomes a kind request to hold it closer or steadier.
"""

from __future__ import annotations

import csv
import io
import math
import functools
import os
import shutil
import subprocess
import time
from typing import Any, Callable, Dict, List, Optional

import numpy as np

OCR_TIMEOUT_S = 20
MAX_WORDS = 600
MAX_TEXT = 4000
MAX_PIXELS = 4096 * 4096


def valid_frame(frame: Any) -> bool:
    return (isinstance(frame, np.ndarray) and frame.dtype == np.uint8 and frame.ndim == 3 and frame.shape[2] == 3
            and min(frame.shape[:2]) >= 32 and frame.shape[0] * frame.shape[1] <= MAX_PIXELS)


def quality(frame: np.ndarray) -> Dict[str, Any]:
    import cv2

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    scale = min(1.0, 640 / gray.shape[1])
    small = cv2.resize(gray, (max(1, int(gray.shape[1] * scale)), max(1, int(gray.shape[0] * scale))))
    sharpness = float(cv2.Laplacian(small, cv2.CV_64F).var())
    brightness = float(gray.mean())
    problems = []
    if sharpness < 25:
        problems.append("blurry")
    if brightness < 40:
        problems.append("dark")
    return {"sharpness": round(sharpness, 1), "brightness": round(brightness, 1), "problems": problems}


def best_frame(get_frame: Callable[[], Any], tries: int = 3, sleep: Callable[[float], None] = time.sleep) -> Optional[np.ndarray]:
    samples = []
    for i in range(tries):
        if i:
            sleep(0.15)
        frame = get_frame()
        if valid_frame(frame):
            samples.append((quality(frame)["sharpness"], frame.copy()))
    return max(samples, key=lambda s: s[0])[1] if samples else None


def parse_tsv(text: str) -> Dict[str, Any]:
    words: List[Dict[str, Any]] = []
    lines: Dict[tuple, List[str]] = {}
    chars, partial = 0, False
    try:
        rows = csv.DictReader(io.StringIO(text), delimiter="\t", quoting=csv.QUOTE_NONE)
        if not {"text", "conf", "block_num", "par_num", "line_num", "level"} <= set(rows.fieldnames or []):
            raise ValueError
        for row in rows:
            if row["level"] != "5" or not row["text"].strip():
                continue
            confidence = float(row["conf"])
            if not math.isfinite(confidence):
                raise ValueError
            word = row["text"].strip()
            if len(words) >= MAX_WORDS or chars + len(word) + 1 > MAX_TEXT:
                partial = True
                break
            words.append({"text": word, "confidence": confidence})
            lines.setdefault((row["block_num"], row["par_num"], row["line_num"]), []).append(word)
            chars += len(word) + 1
    except (ValueError, TypeError, KeyError):
        return {"error": "The text could not be read properly."}
    good = [w for w in words if w["confidence"] >= 60]
    return {"text": "\n".join(" ".join(line) for line in lines.values()), "words": len(words),
            "partial": partial, "uncertain": not words or partial or len(good) < 0.8 * len(words)}



@functools.lru_cache(maxsize=4)
def languages(program: str) -> str:
    """English, and Spanish too when its Tesseract data is installed (tesseract-ocr-spa): a letter in Spanish
    reads properly, and English pages read the same."""
    try:
        listed = subprocess.run([program, "--list-langs"], capture_output=True, timeout=10).stdout.decode()
    except (OSError, subprocess.TimeoutExpired):
        return "eng"
    return "eng+spa" if "spa" in listed.split() else "eng"

def ocr(frame: np.ndarray, runner: Callable = subprocess.run) -> Dict[str, Any]:
    import cv2

    program = shutil.which("tesseract")
    if not program:
        return {"error": "Reading is not set up on this computer (Tesseract is missing)."}
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    scale = min(2.0, 2400 / max(gray.shape))
    gray = cv2.resize(gray, None, fx=scale, fy=scale, interpolation=cv2.INTER_CUBIC if scale > 1 else cv2.INTER_AREA)
    ok, encoded = cv2.imencode(".png", gray)
    if not ok:
        return {"error": "The picture could not be prepared for reading."}
    try:
        done = runner([program, "stdin", "stdout", "-l", languages(program), "--psm", "4", "tsv"], input=encoded.tobytes(),
                      capture_output=True, timeout=OCR_TIMEOUT_S, env={**os.environ, "OMP_THREAD_LIMIT": "2"})
    except (OSError, subprocess.TimeoutExpired):
        return {"error": "Reading took too long. Try holding it closer and steadier."}
    if done.returncode:
        return {"error": "Reading failed on this computer."}
    return parse_tsv(done.stdout.decode("utf-8", errors="replace"))


def read(get_frame: Callable[[], Any], runner: Callable = subprocess.run, sleep: Callable[[float], None] = time.sleep) -> Dict[str, Any]:
    frame = best_frame(get_frame, sleep=sleep)
    if frame is None:
        return {"error": "The camera did not give a picture. Try again in a moment."}
    q = quality(frame)
    result = ocr(frame, runner=runner)
    if "error" in result:
        return result
    if not result["text"].strip():
        ask = "It's a bit dark; more light would help." if "dark" in q["problems"] else \
              "Hold it a little closer to my eyes and keep it still." if "blurry" in q["problems"] else \
              "I couldn't find any writing. Hold the page facing me, a little closer."
        return {"text": "", "ask": ask}
    if q["problems"]:
        result["ask"] = "Some words may be wrong; more light or holding it steadier would help."
    return result
