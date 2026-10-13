"""What Andy remembers, given to it at the start of every conversation.

Asked "What do you remember about me?", Andy sometimes answered "nothing" without looking (the
suite, 2026-10-13). So the moments it keeps are now in its instructions from the start, and the
answer never depends on choosing to call a tool. Pollen's app already adds the remembered facts
the same way. Standard library only: the suite's Nebius job imports this file.
"""

from __future__ import annotations

from typing import Iterable, Tuple


def block(moments: Iterable[Tuple[str, str]]) -> str:
    """moments: (what, day in words) pairs, soonest first."""
    items = [f"- {what}, {day}" for what, day in moments]
    head = ("## WHAT YOU REMEMBER\nThe dated moments the person asked you to remember (any facts they asked "
            "you to remember are listed separately). If they ask what you remember, tell them all of it, "
            "plainly, and that they can ask you to forget any of it.")
    if not items:
        return head + "\nNo moments yet."
    return head + "\n" + "\n".join(items)
