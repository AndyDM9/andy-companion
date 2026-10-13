"""Start speech-to-speech with its one unconditional transcript print silenced.

speech-to-speech logs transcripts only as their length unless --log_transcripts is given, but its
Qwen3-TTS handler prints each reply to the console ("ASSISTANT: ...") regardless. This wraps that
console so those lines are dropped; everything else prints as before.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from andy_companion.privacy import is_transcript_print  # noqa: E402


def quiet_console(module) -> None:
    console = getattr(module, "console", None)
    if console is None or getattr(console.print, "_andy_quiet", False):
        return
    original = console.print

    def print_unless_transcript(*args, **kwargs):
        if args and is_transcript_print(args[0]):
            return None
        return original(*args, **kwargs)

    print_unless_transcript._andy_quiet = True
    console.print = print_unless_transcript


if __name__ == "__main__":
    import importlib

    for name in ("speech_to_speech.TTS.qwen3_tts_handler", "speech_to_speech.STT.mlx_audio_whisper_handler"):
        try:
            quiet_console(importlib.import_module(name))
        except Exception:
            pass
    from speech_to_speech.cli import main

    sys.argv[0] = "speech-to-speech"
    sys.exit(main())
