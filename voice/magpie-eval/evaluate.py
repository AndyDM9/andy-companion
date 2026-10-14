"""Is NVIDIA Magpie TTS fast enough, and does it sound right, to be Andy's voice? (PLAN B7)

    CUDA_VISIBLE_DEVICES=0 voice/magpie-eval/.venv/bin/python voice/magpie-eval/evaluate.py

Andy speaks a reply sentence by sentence, so what matters is how long the first sentence takes to make:
Qwen3-TTS starts in 0.10-0.33 s, streaming (measured on the robot, 2026-10-13). Magpie makes a whole
sentence at once, so its time per sentence is the time to Andy's first sound. This times typical sentences
of Andy's in English and Spanish, for each voice, after a warm-up. It writes the audio to out/ (not in git)
for the founder to listen to, and the timings to evals/results/.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path

import soundfile as sf
import torch
from nemo.collections.tts.models import MagpieTTSModel

HERE = Path(__file__).resolve().parent
OUT = HERE / "out"
SPEAKERS = {"Aria": 0, "Jason": 1, "John": 2, "Leo": 3, "Sofia": 4}
SENTENCES = {
    "en": ["Good morning! I'm Andy, your robot companion, here to help with your day.",
           "It's time to call Rosa.",
           "I think I see your glasses, on the table by the lamp.",
           "Be careful: it asks for gift cards and threatens arrest. Real banks and agencies never do that. "
           "Don't call or pay yet; let's check with your daughter first."],
    "es": ["¡Buenos días! Soy Andy, su compañero robot, para ayudarle con su día.",
           "Es hora de llamar a Rosa.",
           "Según Wikipedia, un día como hoy se publicó el primer libro de Winnie the Pooh. ¿Cómo era aquella época para usted?"],
}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    device = "cuda" if torch.cuda.is_available() else "cpu"
    t = time.time()
    model = MagpieTTSModel.from_pretrained("nvidia/magpie_tts_multilingual_357m").to(device).eval()
    load_s = time.time() - t
    rate = int(getattr(model, "sample_rate", 22050))
    with torch.inference_mode():
        model.do_tts("Warming up.", language="en", apply_TN=False, speaker_index=4)   # first call is slow
        rows = []
        for speaker, idx in SPEAKERS.items():
            for lang, sentences in SENTENCES.items():
                for n, text in enumerate(sentences):
                    if device == "cuda":
                        torch.cuda.synchronize()
                    t = time.time()
                    audio, length = model.do_tts(text, language=lang, apply_TN=False, speaker_index=idx)
                    if device == "cuda":
                        torch.cuda.synchronize()
                    took = time.time() - t
                    samples = audio[0][: int(length[0])].float().cpu().numpy()
                    seconds = len(samples) / rate
                    sf.write(OUT / f"{speaker}-{lang}-{n}.wav", samples, rate)
                    rows.append({"speaker": speaker, "lang": lang, "n": n, "chars": len(text),
                                 "make_s": round(took, 3), "audio_s": round(seconds, 2),
                                 "real_time_factor": round(took / seconds, 3) if seconds else None})
                    print(f"{speaker:6} {lang} #{n}: {took:.2f} s to make {seconds:.1f} s of speech")
    first = [r["make_s"] for r in rows if r["chars"] < 80]
    card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"), "device": torch.cuda.get_device_name(0)
            if device == "cuda" else "cpu", "load_s": round(load_s, 1), "sample_rate": rate,
            "median_make_s_short_sentences": sorted(first)[len(first) // 2] if first else None, "rows": rows}
    out = HERE.parents[1] / "evals" / "results" / f"magpie-eval-{datetime.now():%Y-%m-%d-%H%M}.json"
    out.write_text(json.dumps(card, indent=1))
    print(f"\nMedian time to make a short sentence: {card['median_make_s_short_sentences']} s "
          f"(Qwen3-TTS starts in 0.10-0.33 s). Audio in {OUT}; timings in {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
