"""Invented private references only; exercise the checker and an isolated Git commit hook."""
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]
CHECK = ROOT / "scripts/check_commit_message.py"


@pytest.mark.parametrize("message", [
    "Example change\n\nClaude-Session: https://example.invalid/invented-reference",
    "Example change\n\nCodex-Session: invented-reference",
    "Example https://claude.ai/code/session_invented-reference",
    "Example https://claude.ai/chat/invented-reference",
    "Example HTTPS://WWW.CLAUDE.AI/CHAT/invented-reference",
    "Example https://chatgpt.com/c/invented-reference",
    "Example https://chat.openai.com/c/invented-reference",
])
def test_private_reference_is_rejected_without_echoing_any_message(tmp_path, message):
    path = tmp_path / "message"
    path.write_text(message)
    result = subprocess.run([sys.executable, str(CHECK), str(path)], capture_output=True, text=True)
    assert result.returncode == 1 and not result.stdout
    assert "private AI-session" in result.stderr
    assert "invented-reference" not in result.stderr and "https://" not in result.stderr
    assert path.read_text() == message


@pytest.mark.parametrize("message", [
    "Example change\n\nCo-Authored-By: Example Contributor <example@example.invalid>\n",
    "Clarify model setup\n\nSee https://claude.ai/ and https://platform.openai.com/docs/\n",
    "Retain source attribution and evidence\n",
])
def test_ordinary_message_and_author_credits_are_allowed(tmp_path, message):
    path = tmp_path / "message"
    path.write_text(message)
    result = subprocess.run([sys.executable, str(CHECK), str(path)], capture_output=True, text=True)
    assert result.returncode == 0 and not result.stdout and not result.stderr


@pytest.mark.parametrize("kind", ["missing", "invalid-utf8"])
def test_unreadable_message_fails_without_content_or_path_in_error(tmp_path, kind):
    path = tmp_path / "invented-private-file"
    if kind == "invalid-utf8":
        path.write_bytes(b"\xffinvented-reference")
    result = subprocess.run([sys.executable, str(CHECK), str(path)], capture_output=True, text=True)
    assert result.returncode == 2 and "UTF-8" in result.stderr
    assert "invented" not in result.stderr and not result.stdout


def test_actual_git_hook_rejects_private_trailer_and_allows_public_credit(tmp_path):
    def git(*args):
        return subprocess.run(["git", "-C", str(tmp_path), *args], capture_output=True, text=True)

    assert git("init", "--initial-branch=main").returncode == 0
    assert git("config", "user.name", "Example Contributor").returncode == 0
    assert git("config", "user.email", "example@example.invalid").returncode == 0
    assert git("config", "core.hooksPath", ".githooks").returncode == 0
    (tmp_path / ".githooks").mkdir()
    (tmp_path / "scripts").mkdir()
    hook = tmp_path / ".githooks/commit-msg"
    shutil.copyfile(ROOT / ".githooks/commit-msg", hook)
    hook.chmod(0o755)
    shutil.copyfile(CHECK, tmp_path / "scripts/check_commit_message.py")
    (tmp_path / "README.md").write_text("Invented hook fixture\n")
    assert git("add", ".").returncode == 0
    message = tmp_path / ".git/message"
    message.write_text("Example change\n\nClaude-Session: invented-reference\n")
    rejected = git("commit", "--file", str(message))
    assert rejected.returncode != 0 and "private AI-session" in rejected.stderr
    assert "invented-reference" not in rejected.stderr + rejected.stdout
    assert git("rev-parse", "--verify", "HEAD").returncode != 0
    message.write_text("Example change\n\nCo-Authored-By: Example Contributor <example@example.invalid>\n")
    accepted = git("commit", "--file", str(message))
    assert accepted.returncode == 0
    assert "Co-Authored-By:" in git("log", "-1", "--format=%B").stdout
