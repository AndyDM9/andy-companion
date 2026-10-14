"""Record the urgent-words net's fixed sentences in Andy's own voice, so they can be played without the model.

The net (urgent.py) asks the model to say one exact sentence; when the model is unreachable it plays
these instead. They are made with the voice server's own text-to-speech (Qwen3-TTS, speaker "Aiden",
the conversation app's default voice), as 16 kHz mono WAVs, and `recordings.json` notes the sentence
each one holds, so a test fails when a sentence changes and its recording does not.

Run it in the voice server's environment, on a free GPU, after changing a sentence in urgent.py:

    cd voice && CUDA_VISIBLE_DEVICES=1 HF_HUB_OFFLINE=1 .venv/bin/python \\
        ../src/andy_companion/urgent_audio/regenerate.py

Name files to make only those again, and give another --seed when one comes out wrong (the model
samples, so a take can stumble). Check each take by ear, or with Parakeet, before committing it.
The takes here (2026-10-14): seed 7, except crisis_en.wav, seed 11 (seed 7 added a "one" after 911).
It loads its own copy of the model in its own process and leaves a running voice server alone.
"""

from __future__ import annotations

import json
import re
import sys
import wave
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from andy_companion import urgent  # noqa: E402

RATE = 16000
MODEL = "Qwen/Qwen3-TTS-12Hz-1.7B-CustomVoice"
SPEAKER = "Aiden"
# Digits are spelled out, so 911 is never read as "nine hundred and eleven".
SPOKEN = {"english": {"911": "nine one one", "988": "nine eight eight"},
          "spanish": {"911": "nueve uno uno", "988": "nueve ocho ocho"}}


def spoken(text: str, language: str) -> str:
    return re.sub(r"\b(911|988)\b", lambda m: SPOKEN[language][m.group(1)], text)


def write_wav(path: Path, samples, rate: int) -> None:
    import numpy as np

    audio = np.asarray(samples, dtype=np.float32).reshape(-1)
    if rate != RATE:   # linear resampling is plenty for speech going to a small speaker
        positions = np.arange(int(len(audio) * RATE / rate)) * (rate / RATE)
        audio = np.interp(positions, np.arange(len(audio)), audio).astype(np.float32)
    peak = float(np.max(np.abs(audio))) or 1.0
    audio = audio * (0.7 / peak)          # the same loudness for every sentence
    with wave.open(str(path), "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(RATE)
        w.writeframes((audio * 32767).astype("<i2").tobytes())


def main(argv: list) -> None:
    import argparse

    import numpy as np
    import torch
    from faster_qwen3_tts import FasterQwen3TTS

    parser = argparse.ArgumentParser(description="Record the urgent-words sentences.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("names", nargs="*", help="only these files, e.g. crisis_en.wav")
    args = parser.parse_args(argv)
    torch.manual_seed(args.seed)
    model = FasterQwen3TTS.from_pretrained(MODEL, device="cuda", dtype=torch.bfloat16,
                                           attn_implementation="eager", backend="ggml", quant="BF16")
    try:
        manifest = json.loads((HERE / "recordings.json").read_text())
    except (OSError, ValueError):
        manifest = {}
    for sentence, name in urgent.RECORDINGS.items():
        if args.names and name not in args.names:
            continue
        language = "spanish" if name.endswith("_es.wav") else "english"
        chunks, rate = model.generate_custom_voice(text=spoken(sentence, language), speaker=SPEAKER,
                                                   language=language, max_new_tokens=1024)
        write_wav(HERE / name, np.concatenate([np.asarray(c).reshape(-1) for c in chunks]), rate)
        manifest[name] = sentence
        print(f"{name}: {(HERE / name).stat().st_size // 1024} KB")
    (HERE / "recordings.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main(sys.argv[1:])
