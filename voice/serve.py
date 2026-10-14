"""Start speech-to-speech with its transcript prints silenced, and each turn capped in length.

speech-to-speech logs transcripts only as their length unless --log_transcripts is given, but its
speech-to-text and text-to-speech handlers print what was heard ("USER: ...") and each reply
("ASSISTANT: ...") to the console regardless, each through its own rich Console. This filters
print on the Console class itself, before any handler is imported, so every console in the
server drops those lines and prints everything else as before.

A turn is reopened when speech resumes within a moment of a pause and nothing has been answered, with
no limit on how long that goes on. On 2026-10-13, continuous speech near the robot grew one turn past
5,000 characters while Andy waited to answer (every answer it began was cancelled by the next words),
and each pause re-transcribed the whole turn. `cap_turns` stops reopening a turn once it holds
MAX_TURN_S of audio: new speech starts a new turn instead (ANDY_MAX_TURN_S; 0 turns the cap off).
"""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from andy_companion.privacy import is_transcript_print  # noqa: E402


def quiet_consoles(console_class) -> None:
    """Make every instance of console_class, existing or future, drop transcript prints."""
    original = console_class.print
    if getattr(original, "_andy_quiet", False):
        return

    def print_unless_transcript(self, *args, **kwargs):
        if args and is_transcript_print(args[0]):
            return None
        return original(self, *args, **kwargs)

    print_unless_transcript._andy_quiet = True
    console_class.print = print_unless_transcript


MAX_TURN_S = float(os.environ.get("ANDY_MAX_TURN_S", "40"))
logger = logging.getLogger("andy.voice")


def cap_turns(vad_class, max_turn_s: float = MAX_TURN_S) -> None:
    """A turn already holding max_turn_s of audio is never reopened; the next speech is a new turn."""
    original = vad_class._should_reopen_current_turn
    if getattr(original, "_andy_capped", False) or max_turn_s <= 0:
        return

    def should_reopen(self, audio_start_ms: int) -> bool:
        prefix = getattr(self, "_speculative_audio_prefix", None)
        if prefix is not None and len(prefix) / float(self.sample_rate) >= max_turn_s:
            logger.info("VAD: turn capped at %.0f s of audio; the next speech starts a new turn", max_turn_s)
            return False
        return original(self, audio_start_ms)

    should_reopen._andy_capped = True
    vad_class._should_reopen_current_turn = should_reopen


if __name__ == "__main__":
    from rich.console import Console

    quiet_consoles(Console)
    from speech_to_speech.VAD.vad_handler import VADHandler

    cap_turns(VADHandler)
    from speech_to_speech.cli import main

    sys.argv[0] = "speech-to-speech"
    sys.exit(main())
