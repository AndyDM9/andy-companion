"""Draft English captions (an SRT file) for the demo video, for the founder to check before uploading.

    CUDA_VISIBLE_DEVICES=1 voice/.venv/bin/python scripts/draft_captions.py final-cut.mp4 [--translate]

The rules ask for captions in English, and English subtitles for anything said in another language
(docs/video.md). This splits the video's sound at its pauses (ffmpeg's silencedetect), transcribes each part
with NVIDIA Parakeet on this computer (the same model as Andy's ears, through nano_parakeet, as the voice
server loads it), and writes short caption lines: at most two lines of 42 characters, at most 7 seconds each.
Parts in Spanish are marked "[ES]"; with --translate they are also put into English by Nemotron 3.5
Lightning on Token Factory (needs NEBIUS_API_KEY), marked "[ES→EN, check]". Nothing is uploaded anywhere
else, and the draft is only a start: read every line against the video before uploading it.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
import urllib.request
from pathlib import Path

RATE = 16000
MIN_SILENCE_S = 0.45
MAX_CUE_S = 7.0
LINE = 42


def audio(video: Path):
    import numpy as np

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(video), "-ac", "1", "-ar", str(RATE), "-f", "s16le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0


def speech_parts(video: Path, total_s: float) -> list:
    """(start, end) of each stretch between pauses."""
    log = subprocess.run(["ffmpeg", "-v", "info", "-i", str(video), "-af",
                          f"silencedetect=noise=-35dB:d={MIN_SILENCE_S}", "-f", "null", "-"],
                         capture_output=True, text=True).stderr
    starts = [float(x) for x in re.findall(r"silence_start: ([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"silence_end: ([\d.]+)", log)]
    parts, cursor = [], 0.0
    for s, e in zip(starts, ends + [total_s] * (len(starts) - len(ends)), strict=True):
        if s - cursor > 0.3:
            parts.append((cursor, s))
        cursor = e
    if total_s - cursor > 0.3:
        parts.append((cursor, total_s))
    return parts


def cues(text: str, start: float, end: float) -> list:
    """One part's words as caption cues: two lines of LINE characters at most, time shared by length."""
    lines = textwrap.wrap(text, LINE) or [""]
    blocks = [" ".join(lines[i:i + 2]) for i in range(0, len(lines), 2)]
    total = sum(len(b) for b in blocks) or 1
    out, t = [], start
    for b in blocks:              # two lines are about 84 characters: under MAX_CUE_S at speaking pace
        d = (end - start) * len(b) / total
        out.append((t, t + min(d, MAX_CUE_S), "\n".join(textwrap.wrap(b, LINE)[:2])))
        t += d
    return out


def stamp(t: float) -> str:
    ms = int(round(t * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def spanish(text: str) -> bool:
    words = re.findall(r"[a-záéíóúñü]+", text.lower())
    marks = {"el", "la", "que", "de", "y", "en", "un", "una", "es", "por", "usted", "qué", "cómo", "está"}
    return bool(words) and (sum(w in marks for w in words) / len(words) > 0.18 or bool(re.search(r"[ñ¿¡áéíóú]", text)))


def translate(text: str) -> str:
    base = os.environ.get("NEBIUS_BASE_URL", "https://api.tokenfactory.nebius.com/v1/").rstrip("/")
    body = {"model": "nvidia/Nemotron-3_5-Lightning", "temperature": 0, "max_tokens": 200,
            "chat_template_kwargs": {"enable_thinking": False},
            "messages": [{"role": "system", "content": "Translate this spoken Spanish into plain spoken English for a "
                          "subtitle. Reply with the translation only."}, {"role": "user", "content": text}]}
    req = urllib.request.Request(base + "/chat/completions", method="POST", data=json.dumps(body).encode(),
                                 headers={"Authorization": f"Bearer {os.environ['NEBIUS_API_KEY']}",
                                          "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read())["choices"][0]["message"]["content"].strip()


def main() -> int:
    if {"-h", "--help"} & set(sys.argv[1:]):     # the description, and nothing else run
        print(__doc__)
        return 0
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    video = Path(sys.argv[1])
    sound = audio(video)
    total = len(sound) / RATE
    parts = speech_parts(video, total)
    from nano_parakeet import from_pretrained

    model = from_pretrained(model_name="nvidia/parakeet-tdt-0.6b-v3", device="cuda")
    entries = []
    for start, end in parts:
        piece = sound[int(start * RATE):int(end * RATE)]
        text = " ".join(str(model.transcribe(piece)).split())
        if not text:
            continue
        if spanish(text):
            text = f"[ES→EN, check] {translate(text)}" if "--translate" in sys.argv else f"[ES] {text}"
        entries.extend(cues(text, start, end))
    out = video.with_suffix(".draft.srt")
    out.write_text("\n".join(f"{i}\n{stamp(s)} --> {stamp(e)}\n{t}\n" for i, (s, e, t) in enumerate(entries, 1)))
    print(f"{len(entries)} captions over {total:.0f} s: {out}. Check every line before uploading.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
