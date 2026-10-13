"""Set Andy up for a home: where it is, and which local news and event pages to prefer.

    python scripts/settings.py show
    python scripts/settings.py place "Springfield, Illinois"
    python scripts/settings.py news add sj-r.com          (a local paper's site)
    python scripts/settings.py events add https://library.example.org/events

Kept in Andy's own owner-only settings file on this computer, never in the repository.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from andy_companion import settings  # noqa: E402


def main(argv: list[str]) -> int:
    if not argv or argv[0] == "show":
        print(json.dumps({k: v for k, v in settings.get().items() if k != "last_morning"}, indent=2))
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
