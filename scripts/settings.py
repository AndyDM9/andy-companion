"""Set Andy up for a home: where it is, and which local news and event pages to prefer.

    python3 scripts/settings.py show
    python3 scripts/settings.py place "Springfield, Illinois"
    python3 scripts/settings.py news add sj-r.com          (a local paper's site)
    python3 scripts/settings.py events add https://library.example.org/events
    python3 scripts/settings.py links                     (the screen, family, under-the-hood and settings addresses)
    python3 scripts/settings.py new-family-link           (the old family link stops working)
    python3 scripts/settings.py sample-photos             (six sample landscapes for the idle screen)
    python3 scripts/settings.py remove-sample-photos

Kept in Andy's own owner-only settings file on this computer, never in the repository.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from andy_companion import board, settings  # noqa: E402


SAMPLES = [(1016, "Philippe Wuyts"), (1018, "Andrew Ridley"), (1036, "Wolfgang Lutz"), (1039, "Andrew Coelho"),
           (1043, "Christian Joudrey"), (1050, "Joseph Barrientos")]


def main(argv: list[str]) -> int:
    if {"-h", "--help"} & set(argv):     # the description, and nothing else run
        print(__doc__)
        return 0
    if not argv or argv[0] == "show":
        print(json.dumps({k: v for k, v in settings.get().items() if k != "last_morning"}, indent=2))
        return 0
    if argv[0] in ("links", "new-family-link"):
        import os

        from andy_companion import screen_server

        if argv[0] == "new-family-link":
            board.new_family_link()
        t = board.tokens()
        port = os.environ.get("ANDY_SCREEN_PORT", "8090")
        host = screen_server.lan_host()          # the same address the TV's settings code uses
        print(f"Screen (TV beside Andy): http://{host}:{port}/screen?t={t['screen']}")
        print(f"Family page:             http://{host}:{port}/family?k={t['family']}")
        print(f"Under the hood:          http://{host}:{port}/hood?t={t['hood']}")
        print(f"Andy's settings:        http://{host}:{port}/setup?s={t['setup']}")
        return 0
    if argv[0] == "sample-photos":
        # Landscapes from Lorem Picsum (Unsplash photos, free to use), with no people in them.
        import urllib.request

        for pid, author in SAMPLES:
            with urllib.request.urlopen(f"https://picsum.photos/id/{pid}/1600/1067", timeout=30) as r:
                board.add_sample_photo(r.read(), f"Sample photo by {author}, Unsplash")
        print(f"Added {len(SAMPLES)} sample photos; they show when Andy is idle. Remove: settings.py remove-sample-photos")
        return 0
    if argv[0] == "remove-sample-photos":
        print(f"Removed {board.remove_sample_photos()} sample photos.")
        return 0
    if argv[0] == "place" and len(argv) == 2:
        settings.update(place=argv[1].strip()[:120])
    elif argv[0] in ("news", "events") and len(argv) == 3 and argv[1] in ("add", "remove"):
        key = "news_sources" if argv[0] == "news" else "events_pages"
        items = [i for i in settings.get()[key] if i != argv[2]]
        if argv[1] == "add":
            items.append(argv[2].strip())
        settings.update(**{key: items[:20]})
    else:
        print(__doc__)
        return 2
    return main(["show"])


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
