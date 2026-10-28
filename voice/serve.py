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

Nemotron sometimes writes a tool call out as text instead of making it: on 2026-10-28, in the suite run as a
Nebius Serverless Job, a letter case's whole reply was "<tool_call> <function=read_letter </function>". The
speech package speaks any text it is given, so `unspoken_tool_markup` takes such markup out of each sentence
before it is spoken (wrapping the package's own remove_markdown, which every spoken sentence goes through).
Only how many characters were left out is logged, never the text.

Andy speaks English and Spanish. Parakeet hears 25 languages and writes what it thinks it heard: on 2026-10-28 two
turns on the robot, an accented one and a muffled one, came out in Cyrillic (detected as Ukrainian and Russian),
and Andy answered one in Russian. `only_our_languages` takes a transcript in another alphabet as unclear (Andy asks
again, in its language) and keeps the turn's language English or Spanish. Latin-script words pass untouched.
Only the detected language code is logged, never the words.

The Token Factory key comes from the environment (NEBIUS_API_KEY, from run.sh's private .env file), never
the command line: any process on this shared computer can read a command line (`ps`), but only this user
can read a process's environment. `key_from_environment` adds it to the arguments inside this process.
"""

from __future__ import annotations

import logging
import os
import re
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


TOOL_MARKUP = re.compile(r"<tool_call>.*?(?:</tool_call>|\Z)|</?tool_call>|<function=.*?(?:</function>|\Z)"
                         r"|</?function>|</?parameter(?:=[^>]*)?>"
                         # A sentence that starts with a tool's own name ("set_volume louder", the whole reply once in
                         # the suite's 291 turns on 2026-10-28): words joined by underscores are never speech.
                         r"|(?:^|(?<=[.!?]\s))[a-z]+(?:_[a-z0-9]+)+\b[^.!?\n]*[.!?]?", re.S)


def unspoken_tool_markup(text: str) -> str:
    """The text without any tool call the model wrote out instead of making it."""
    kept = TOOL_MARKUP.sub(" ", text)
    if kept == text:
        return text
    logger.info("voice: a tool call written as text was not spoken (%d characters)", len(text) - len(kept.strip()))
    return " ".join(kept.split())


def no_tool_markup_spoken(modules) -> None:
    """Every module's remove_markdown (each spoken sentence goes through it) first takes out tool-call markup."""
    for module in modules:
        original = module.remove_markdown
        if getattr(original, "_andy_no_tool_markup", False):
            continue

        def remove_markdown(text, *args, _original=original, **kwargs):
            return _original(unspoken_tool_markup(text), *args, **kwargs)

        remove_markdown._andy_no_tool_markup = True
        module.remove_markdown = remove_markdown


OUR_LANGUAGES = ("en", "es")
# Worded so the model asks again: tried on Nemotron 3.5 Lightning with Andy's profile, 6 of 6 in each language,
# at the start of a conversation and after it; a plainer "[The words could not be made out.]" set off random tools.
UNCLEAR = {"en": "[Andy couldn't make out these words: ask the person to say it again.]",
           "es": "[Andy no entendió estas palabras: pídale a la persona que lo repita.]"}
OTHER_ALPHABET = re.compile(r"[\u0370-\u03ff\u0400-\u052f]")     # Greek and Cyrillic: Parakeet's non-Latin ones


def our_language(text: str, language, last) -> tuple:
    """(text, language) kept to Andy's languages: another alphabet is a mishearing, said as unclear."""
    keep = language if language in OUR_LANGUAGES else last if last in OUR_LANGUAGES else "en"
    if text and OTHER_ALPHABET.search(text):
        logger.info("voice: a turn heard as %s was taken as unclear", language if isinstance(language, str) else "?")
        return UNCLEAR[keep], keep
    return text, keep


def only_our_languages(handler_class) -> None:
    """The speech-to-text handler's final transcripts, kept to English and Spanish (our_language)."""
    for name in ("_process_nano_parakeet", "_process_mlx_final"):
        original = getattr(handler_class, name, None)
        if original is None or getattr(original, "_andy_languages", False):
            continue

        def final(self, audio_input, _original=original):
            text, language = _original(self, audio_input)
            return our_language(text, language, getattr(self, "last_language", "en"))

        final._andy_languages = True
        setattr(handler_class, name, final)


def key_from_environment(argv: list, environ=os.environ) -> list:
    """The arguments with the model key added from NEBIUS_API_KEY, unless one was given already."""
    if any(a == "--responses_api_api_key" or a.startswith("--responses_api_api_key=") for a in argv):
        return argv
    key = environ.get("NEBIUS_API_KEY", "")
    return argv + ["--responses_api_api_key", key] if key else argv


if __name__ == "__main__":
    from rich.console import Console

    quiet_consoles(Console)
    from speech_to_speech.VAD.vad_handler import VADHandler

    cap_turns(VADHandler)
    from speech_to_speech.LLM import base_openai_compatible_language_model, language_model

    no_tool_markup_spoken([base_openai_compatible_language_model, language_model])
    from speech_to_speech.STT.parakeet_tdt_handler import ParakeetTDTSTTHandler

    only_our_languages(ParakeetTDTSTTHandler)
    from speech_to_speech.cli import main

    sys.argv[0] = "speech-to-speech"
    sys.argv = key_from_environment(sys.argv)
    sys.exit(main())
