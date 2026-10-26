"""Nothing the person says reaches a log, and Andy's memory lives in Andy's own folder.

Pollen's conversation app logs every spoken turn at INFO ("role=user content=..."), the arguments
of every tool call (a reminder's words, a fact to remember), and what remember/forget stored.
`install()` redacts all of that at the moment each log record is created, for every logger in the
app, so no handler, file or crash report ever sees it. Tool names, timings and errors stay.

It also points Pollen's `remember`/`forget` store at Andy's own owner-only folder, instead of a
file inside the installed package that any other app on the robot would share.
"""

from __future__ import annotations

import logging
import os
import traceback
from pathlib import Path

from andy_companion.reminders import DATA_DIR

REDACTED = "[not logged]"
APP_NAMESPACE = "reachy_mini_conversation_app"
MEMORY_FILE = DATA_DIR / "memory.json"

# The whole record goes: it is nothing but what was said or stored.
DROP_PREFIXES = ("role=", "Tool call: remember fact=", "Tool call: forget query=")
# Messages built with f-strings: the text is in the message itself.
REDACT_TEXT = ("User partial transcript:", "Debounced partial emitted:", "Assistant transcript:", "User transcript:")
# Messages whose arguments carry what was said: the argument positions to replace (None = all).
REDACT_ARGS = {
    "Tool call received": (-1,),                 # args=
    "Invalid tool call": (2,),                   # args=
    "Tool call: camera question=": None,
    "bad args_json=": None,
    "Tool '%s' (id=%s) failed with error": (-1,),  # errors often quote the person
    "Tool error in": (-1,),
    "Tool call: idle_do_nothing reason=": None,
}


def redact(record: logging.LogRecord) -> bool:
    """Strip speech from a record in place; False if the whole record should go."""
    msg = str(record.msg)
    if msg.startswith(DROP_PREFIXES):
        return False
    for prefix in REDACT_TEXT:
        if msg.startswith(prefix):
            record.msg, record.args = f"{prefix} {REDACTED}", ()
            return True
    for prefix, positions in REDACT_ARGS.items():
        if msg.startswith(prefix) and isinstance(record.args, tuple) and record.args:
            args = list(record.args)
            for i in (range(len(args)) if positions is None else positions):
                if -len(args) <= i < len(args):
                    args[i] = REDACTED
            record.args = tuple(args)
            if record.exc_info and record.exc_info[0] is not None:
                kind, _, tb = record.exc_info
                record.exc_info = None
                record.exc_text = ("Traceback (most recent call last):\n" + "".join(traceback.format_tb(tb))
                                   + f"{kind.__name__}: {REDACTED}")
    return True


def redact_records() -> None:
    """Redact every record the app creates, whichever of its loggers made it (a filter on one
    logger does not see its children's records)."""
    previous = logging.getLogRecordFactory()
    if getattr(previous, "_andy_redacts", False):
        return

    def factory(*args, **kwargs):
        record = previous(*args, **kwargs)
        if record.name.startswith(APP_NAMESPACE) and not redact(record):
            record.msg, record.args = REDACTED, ()
        return record

    factory._andy_redacts = True
    logging.setLogRecordFactory(factory)


def own_memory_store() -> None:
    """Pollen's remember/forget keep their facts in Andy's own owner-only file."""
    from reachy_mini_conversation_app import memory

    if getattr(memory.memory_path_for_instance, "_andy_store", False):
        return
    MEMORY_FILE.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    os.chmod(MEMORY_FILE.parent, 0o700)

    def andy_memory_path(instance_path=None) -> Path:
        return MEMORY_FILE

    andy_memory_path._andy_store = True
    memory.memory_path_for_instance = andy_memory_path


def owner_only_files() -> None:
    """Every file this process creates is the owner's alone, Pollen's included (its remember tool made memory.json
    readable by others, inside Andy's owner-only folder; 2026-10-25 review), and the memory file is made so now."""
    os.umask(0o077)
    if MEMORY_FILE.exists():
        os.chmod(MEMORY_FILE, 0o600)


def install() -> None:
    owner_only_files()
    redact_records()
    own_memory_store()


# speech-to-speech logs transcripts as their length by default, but its Qwen3-TTS handler prints
# every reply to the console ("ASSISTANT: ...") regardless. voice/serve.py drops those lines. Its Parakeet
# handler also prints the words as they are heard ("Live: ..."), a line printed as rich Text, not a string:
# that one reached the journal from 2026-10-15 until 2026-10-25, when it was found and added here.
TRANSCRIPT_PRINTS = ("ASSISTANT:", "USER:", "Live:")


def is_transcript_print(text: object) -> bool:
    plain = str(text)
    while plain.startswith("["):              # rich markup such as "[green]"
        end = plain.find("]")
        if end < 0:
            break
        plain = plain[end + 1:]
    return plain.lstrip().startswith(TRANSCRIPT_PRINTS)
