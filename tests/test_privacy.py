"""Nothing the person says reaches a log line."""

import logging
from pathlib import Path

import pytest

from andy_companion import privacy

ROOT = Path(__file__).resolve().parents[1]
SECRET = "my daughter Sofia and my bank PIN"


@pytest.fixture
def captured():
    privacy.redact_records()
    logger = logging.getLogger("reachy_mini_conversation_app.console")
    tool_logger = logging.getLogger("reachy_mini_conversation_app.tools.remember")
    records = []

    class Keep(logging.Handler):
        def emit(self, record):
            records.append(self.format(record))

    h = Keep(level=logging.DEBUG)
    for lg in (logger, tool_logger, logging.getLogger("reachy_mini_conversation_app.huggingface_realtime")):
        lg.addHandler(h)
        lg.setLevel(logging.DEBUG)
    yield records
    for lg in (logger, tool_logger, logging.getLogger("reachy_mini_conversation_app.huggingface_realtime")):
        lg.removeHandler(h)


def test_spoken_turns_never_reach_a_log(captured):
    logging.getLogger("reachy_mini_conversation_app.console").info("role=%s content=%s", "user", SECRET)
    assert all(SECRET not in line for line in captured)


def test_tool_arguments_are_redacted_but_the_tool_name_stays(captured):
    logging.getLogger("reachy_mini_conversation_app.huggingface_realtime").info(
        "Tool call received — tool_name=%r, call_id=%s, args=%s", "set_reminder", "c1", {"what": SECRET})
    (line,) = captured
    assert "set_reminder" in line and SECRET not in line and privacy.REDACTED in line


def test_remembered_facts_are_not_logged(captured):
    logging.getLogger("reachy_mini_conversation_app.tools.remember").info("Tool call: remember fact=%s", SECRET)
    assert all(SECRET not in line for line in captured)


def test_transcripts_in_f_strings_are_redacted(captured):
    logging.getLogger("reachy_mini_conversation_app.huggingface_realtime").debug(f"User transcript: {SECRET}")
    assert captured and all(SECRET not in line for line in captured)


def test_tool_errors_lose_their_text_but_keep_their_type(captured):
    try:
        raise ValueError(SECRET)
    except ValueError:
        logging.getLogger("reachy_mini_conversation_app.huggingface_realtime").exception(
            "Tool '%s' (id=%s) failed with error: %s", "set_reminder", "c1", SECRET)
    text = "\n".join(captured)
    assert "ValueError" in text and SECRET not in text


def test_other_loggers_are_untouched():
    record = logging.LogRecord("someone.else", logging.INFO, "f", 1, "role=%s", ("x",), None)
    assert privacy.redact(record) is False  # the rule itself would drop it...
    privacy.redact_records()
    made = logging.getLogRecordFactory()("someone.else", logging.INFO, "f", 1, "role=%s", ("x",), None)
    assert made.msg == "role=%s"            # ...but the factory only applies it to the app's loggers


def test_the_memory_store_is_andys_own_file(tmp_path, monkeypatch):
    pytest.importorskip("reachy_mini_conversation_app")
    from reachy_mini_conversation_app import memory

    monkeypatch.setattr(privacy, "MEMORY_FILE", tmp_path / "andy" / "memory.json")
    original = memory.memory_path_for_instance
    try:
        privacy.own_memory_store()
        assert memory.memory_path_for_instance("/somewhere/else") == tmp_path / "andy" / "memory.json"
    finally:
        memory.memory_path_for_instance = original


@pytest.mark.parametrize("line, dropped", [
    (f"[green]ASSISTANT: {SECRET}", True),
    (f"[yellow]USER: {SECRET}", True),
    ("ASSISTANT: hi", True),
    ("[green]✓ Pipeline stopped successfully[/green]", False),
    ("Shutting down gracefully...", False),
])
def test_voice_server_transcript_prints_are_recognised(line, dropped):
    assert privacy.is_transcript_print(line) is dropped


def _serve_module():
    import importlib.util

    spec = importlib.util.spec_from_file_location("andy_voice_serve", ROOT / "voice" / "serve.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_every_console_in_the_voice_server_drops_what_was_heard():
    """The Parakeet handler has its own Console; a fix for two named modules missed it."""
    printed = []

    class Console:                      # stands in for rich.console.Console
        def print(self, *args, **kwargs):
            printed.append(args[0])

    serve = _serve_module()
    existing = Console()
    serve.quiet_consoles(Console)
    serve.quiet_consoles(Console)       # twice is harmless
    later = Console()
    for console in (existing, later):
        console.print(f"[yellow]USER: {SECRET}")
        console.print(f"[green]ASSISTANT: {SECRET}")
        console.print("[green]Pipeline ready[/green]")
    assert printed == ["[green]Pipeline ready[/green]"] * 2


def test_files_andy_creates_are_the_owners_alone(tmp_path, monkeypatch):
    import os
    import stat

    from andy_companion import privacy
    memory = tmp_path / "memory.json"
    memory.write_text("{}")
    os.chmod(memory, 0o664)                                  # as Pollen's remember left it
    monkeypatch.setattr(privacy, "MEMORY_FILE", memory)
    before = os.umask(0o022)
    try:
        privacy.owner_only_files()
        (tmp_path / "new.json").write_text("{}")
        assert stat.S_IMODE(os.stat(tmp_path / "new.json").st_mode) == 0o600
        assert stat.S_IMODE(os.stat(memory).st_mode) == 0o600
    finally:
        os.umask(before)
