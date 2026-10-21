"""How fast and how right are Andy's eyes, on each choice (PLAN B32)? A desk check, before the robot's own tries.

    uv run python evals/eyes_check.py PICTURE "glasses" token-factory [endpoint]

Two things, three times each, for each of the eyes named (vision.eyes; the endpoint must be started first):
- describing Andy's own TV screenshot (docs/images/tv-letter.png), as "what do you see?";
- finding the named thing in PICTURE cut into four views (left and right halves, top and bottom halves), asked
  all at once as the finder did before decision 0012 (it now reads each view as six zoomed tiles; zoom_check.py
  measures that), with what each view said.
PICTURE is any picture you may use with the thing in it; the scorecard keeps only its file name, the times and the
answers. The finder's real measure is the robot's own tries (evals/finder_eval.py compare).
"""

from __future__ import annotations

import json
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "src"))

from andy_companion import finder, vision  # noqa: E402
from andy_companion.measure import percentile  # noqa: E402


def views(picture):
    h, w = picture.shape[:2]
    return [picture[:, : w // 2], picture[:, w // 2:], picture[: h // 2], picture[h // 2:]]


def check(eyes: str, picture, what: str, runs: int = 3) -> dict:
    import cv2

    os.environ["ANDY_VISION"] = eyes
    screen = cv2.imread(str(HERE.parent / "docs/images/tv-letter.png"))
    out = {"model": vision.name(), "describe_s": [], "find_s": [], "said": "", "views": []}
    for _ in range(runs):
        t = time.monotonic()
        out["said"] = vision.describe(screen, "What do you see?")
        out["describe_s"].append(round(time.monotonic() - t, 2))
        t = time.monotonic()
        with ThreadPoolExecutor(4) as pool:
            out["views"] = list(pool.map(lambda v: finder.ask(v, what), views(picture)))
        out["find_s"].append(round(time.monotonic() - t, 2))
    out["describe_p50_s"], out["find_p50_s"] = percentile(out["describe_s"], 50), percentile(out["find_s"], 50)
    return out


def main() -> int:
    if {"-h", "--help"} & set(sys.argv[1:]):     # the description, and nothing else run
        print(__doc__)
        return 0
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    import cv2

    picture = cv2.imread(sys.argv[1])
    if picture is None:
        print("Couldn't read that picture.")
        return 2
    card = {"ran": datetime.now().astimezone().isoformat(timespec="seconds"), "picture": Path(sys.argv[1]).name,
            "what": sys.argv[2], "views": ["left half", "right half", "top half", "bottom half"],
            "eyes": {e: check(e, picture, sys.argv[2]) for e in sys.argv[3:]}}
    for e, c in card["eyes"].items():
        seen = ["seen" if v["seen"] else "not seen" for v in c["views"]]
        print(f"{e} ({c['model']}): describe {c['describe_s']} s, find four views {c['find_s']} s; views: {seen}")
    out = HERE / "results" / f"eyes-check-{datetime.now():%Y-%m-%d-%H%M}.json"
    out.write_text(json.dumps(card, indent=1, ensure_ascii=False) + "\n")
    print(f"Scorecard: {out.relative_to(HERE.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
