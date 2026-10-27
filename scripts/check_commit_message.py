"""Reject private AI-session references in a public commit message, without echoing its contents.

Usage: python3 scripts/check_commit_message.py <message-file>
The configured commit-msg hook invokes this automatically; author credits remain supported.
"""
from __future__ import annotations

from pathlib import Path
import re
import sys

SESSION = re.compile(
    r"^\s*(?:Claude|Codex)-Session\s*:|"
    r"https?://(?:www\.)?(?:claude\.ai/(?:code/)?(?:session(?:_|/)|chat/)|"
    r"(?:chatgpt\.com|chat\.openai\.com)/c/)", re.I | re.M,
)


def main(argv: list[str]) -> int:
    if len(argv) != 1:
        print("Usage: python3 scripts/check_commit_message.py <message-file>", file=sys.stderr)
        return 2
    try:
        message = Path(argv[0]).read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        print("commit-msg: the message file could not be read as UTF-8.", file=sys.stderr)
        return 2
    if SESSION.search(message):
        print("commit-msg: remove private AI-session links or session trailers before publishing. "
              "Author credits can remain.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
