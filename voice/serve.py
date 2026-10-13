"""Start speech-to-speech with its transcript prints silenced.

speech-to-speech logs transcripts only as their length unless --log_transcripts is given, but its
speech-to-text and text-to-speech handlers print what was heard ("USER: ...") and each reply
("ASSISTANT: ...") to the console regardless, each through its own rich Console. This filters
print on the Console class itself, before any handler is imported, so every console in the
server drops those lines and prints everything else as before.
"""

from __future__ import annotations

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


if __name__ == "__main__":
    from rich.console import Console

    quiet_consoles(Console)
    from speech_to_speech.cli import main

    sys.argv[0] = "speech-to-speech"
    sys.exit(main())
